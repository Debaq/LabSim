"""
Actualización obligatoria en el kiosko (core/actualizacion_kiosko.py).

En el laboratorio una versión vieja es una versión rota. Antes, si la
consulta a GitHub o la instalación fallaban, el kiosko abría la versión
vieja sin avisar. Ahora:

1. Al abrir no se sale de la pantalla de actualización hasta que GitHub
   confirma que no hay nada nuevo: una falla de red o de instalación se
   reintenta.
2. Con una versión nueva y un alumno atendiendo, se espera al cierre de
   sesión; sin sesión, se actualiza en el momento.
3. check_for_update(estricto=True) distingue "no hay nada" de "no se pudo
   consultar"; sin estricto sigue devolviendo None (fuera del kiosko no se
   bloquea a nadie).
4. La lista sale del backend (consulta a GitHub una vez cada 10 min por
   todo el laboratorio); si no responde, "¿estoy al día?" se pregunta al feed Atom (página web, sin el límite de
   60 consultas por hora de la API, que el laboratorio comparte por IP); la
   API solo cuando hay algo nuevo o falta verificar la instalación.
"""

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import actualizacion_kiosko as ak  # noqa: E402
from core import updater  # noqa: E402

ak.ESPERAS_S = (0,)          # sin esperas reales entre reintentos


def _chequear(feed, marca=None, api=None, estricto=False, backend=None):
    """check_for_update con backend, feed y API de mentira. `feed` es el
    build_id que trae el feed (o una excepción); `api` y `backend` la lista
    de releases (o una excepción; backend None = sin backend configurado).
    Devuelve (resultado, si se consultó la API)."""
    usada = []

    def backend_falso(_url):
        if isinstance(backend, Exception):
            raise backend
        return backend

    def feed_falso():
        if isinstance(feed, Exception):
            raise feed
        return feed

    def api_falsa():
        usada.append(True)
        if isinstance(api, Exception):
            raise api
        return api or []

    original = (updater._ultimo_build_feed, updater._fetch_releases,
                updater.local_build_id, updater._dist_dir,
                updater._fetch_releases_backend)
    with tempfile.TemporaryDirectory() as tmp:
        if marca is not None:
            m = Path(tmp) / updater.VERIFY_MARKER
            m.parent.mkdir(parents=True, exist_ok=True)
            m.write_text(marca, encoding="utf-8")
        updater._ultimo_build_feed = feed_falso
        updater._fetch_releases = api_falsa
        updater.local_build_id = lambda _v: "0.9.8-raaa"
        updater._dist_dir = lambda: Path(tmp)
        updater._fetch_releases_backend = backend_falso
        url = "https://backend" if backend is not None else None
        try:
            return (updater.check_for_update("v0.9.8", estricto=estricto, backend_url=url),
                    bool(usada))
        finally:
            (updater._ultimo_build_feed, updater._fetch_releases,
             updater.local_build_id, updater._dist_dir,
             updater._fetch_releases_backend) = original


def test_al_dia_segun_el_feed_no_gasta_la_api():
    assert _chequear("0.9.8-raaa", marca="0.9.8-raaa") == (None, False)


def test_sin_verificar_la_instalacion_va_a_la_api():
    assert _chequear("0.9.8-raaa")[1]


def test_version_nueva_en_el_feed_va_a_la_api():
    assert _chequear("0.9.8-rbbb", marca="0.9.8-raaa")[1]


def test_feed_caido_cae_a_la_api():
    assert _chequear(URLError("sin red"), marca="0.9.8-raaa")[1]


def _release(build_id, fecha):
    return {"tag_name": "pyinstaller-v" + build_id, "created_at": fecha, "body": "",
            "assets": [{"name": updater.FULL_ASSET_NAME,
                        "browser_download_url": "https://github.com/x/full.tar.gz"}]}


def test_con_backend_no_se_toca_github():
    lista = [_release("0.9.8-raaa", "2026-09-24"), _release("0.9.8-rbbb", "2026-09-25")]
    # feed y API explotarían si se usaran
    r, api = _chequear(RuntimeError("no"), api=RuntimeError("no"), backend=lista)
    assert r["build_id"] == "0.9.8-rbbb" and not api


def test_backend_caido_cae_a_github():
    assert _chequear("0.9.8-rbbb", marca="0.9.8-raaa", backend=URLError("caído"))[1]


def test_limite_de_github_no_se_confunde_con_al_dia():
    limite = HTTPError("https://api.github.com", 403, "rate limit", {}, None)
    assert _chequear("0.9.8-rbbb", api=limite) == (None, True)
    try:
        _chequear("0.9.8-rbbb", api=limite, estricto=True)
    except updater.UpdateCheckError:
        return
    raise AssertionError("estricto tenía que levantar UpdateCheckError")


def _simular(respuestas_check, fallas_apply=0, abortar=lambda: False):
    """Corre actualizar_o_bloquear con check/apply de mentira. Devuelve
    (llamadas a check, llamadas a apply, si terminó "reiniciando")."""
    cola = list(respuestas_check)
    llamadas = {"check": 0, "apply": 0}

    class Reinicio(BaseException):   # como os._exit: nada la atrapa
        pass

    def check(_version, estricto=False, backend_url=None):
        assert estricto
        llamadas["check"] += 1
        r = cola.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def apply(_update, on_progress=None):
        llamadas["apply"] += 1
        if llamadas["apply"] <= fallas_apply:
            raise OSError("descarga cortada")
        raise Reinicio()     # el real hace os._exit

    original = (ak.check_for_update, ak.apply_update_and_restart)
    ak.check_for_update, ak.apply_update_and_restart = check, apply
    reinicio = False
    try:
        ak.actualizar_o_bloquear("v0.9.8", abortar=abortar)
    except Reinicio:
        reinicio = True
    finally:
        ak.check_for_update, ak.apply_update_and_restart = original
    return llamadas["check"], llamadas["apply"], reinicio


def test_al_dia_abre():
    assert _simular([None]) == (1, 0, False)


def test_sin_red_reintenta_hasta_poder_consultar():
    sin_red = updater.UpdateCheckError("sin red")
    assert _simular([sin_red, sin_red, None]) == (3, 0, False)


def test_version_nueva_se_instala():
    assert _simular([{"mode": "full"}]) == (1, 1, True)


def test_instalacion_fallida_no_abre_la_vieja():
    # falla la primera instalación: vuelve a consultar e instala de nuevo
    nueva = {"mode": "full"}
    assert _simular([nueva, nueva], fallas_apply=1) == (2, 2, True)


def test_apagado_corta_la_espera():
    sin_red = updater.UpdateCheckError("sin red")
    assert _simular([sin_red] * 5, abortar=lambda: True) == (0, 0, False)


def test_con_alumno_atendiendo_espera_al_cierre_de_sesion():
    import main
    aplicadas = []
    ventana = SimpleNamespace(data_login={"user": "alumno"},
                              _update_pendiente=False,
                              _actualizar_ahora=lambda: aplicadas.append(1))
    main.MainWindow._on_update_disponible(ventana)
    assert ventana._update_pendiente and not aplicadas
    ventana.data_login = None
    main.MainWindow._on_update_disponible(ventana)
    assert aplicadas == [1]


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                sys.stderr.write(f"  {nombre} OK\n")
            except AssertionError as exc:
                fallos += 1
                sys.stderr.write(f"  {nombre} FALLÓ: {exc}\n")
    sys.stderr.write("TODOS LOS TESTS PASARON\n" if not fallos else f"{fallos} FALLARON\n")
    os._exit(1 if fallos else 0)
