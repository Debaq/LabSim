"""
Elección del instalador en Windows (core/updater.py).

En Windows el update ES el instalador Inno de una release, y ese .exe lo
compila un runner aparte (build-windows.yml): puede faltar en la release más
nueva porque el workflow falló o porque se publicó con SKIP_WINDOWS=1. Antes
se miraba solo la última y esas releases dejaban a Windows sin actualización
y sin aviso, aunque la anterior sí servía para ponerlos al día.
"""

import hashlib
import json
import os
import socket
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import updater


def release(build_id, assets, fecha):
    return {
        "tag_name": f"pyinstaller-v{build_id}",
        "created_at": fecha,
        "body": "",
        "assets": [
            {"name": n, "browser_download_url": f"https://x/{build_id}/{n}"} for n in assets
        ],
    }


SETUP = updater.SETUP_ASSET_NAME
FULL = updater.FULL_ASSET_NAME
UPDATE = updater.UPDATE_ASSET_NAME


def buscar(releases, local="0.9.8", windows=True):
    """check_for_update() contra una lista de releases de mentira, como si
    corriera en Windows (o en Linux con windows=False)."""
    original = (updater._fetch_releases, updater.IS_WINDOWS, updater.local_build_id,
                updater._ultimo_build_feed)
    updater._fetch_releases = lambda: releases
    updater._ultimo_build_feed = lambda: None     # sin atajo: va a la API
    updater.IS_WINDOWS = windows
    updater.local_build_id = lambda _v: local
    try:
        return updater.check_for_update("v0.9.8")
    finally:
        (updater._fetch_releases, updater.IS_WINDOWS, updater.local_build_id,
         updater._ultimo_build_feed) = original


def test_toma_el_instalador_de_la_mas_nueva():
    r = buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, SETUP], "2026-09-02T00:00:00Z"),
    ])
    assert r["mode"] == "setup"
    assert r["tag"] == "pyinstaller-v0.9.9"


def test_si_a_la_mas_nueva_le_falta_el_exe_cae_a_la_anterior():
    """El build de Windows falló en la última: la 0.9.9 igual los pone al día."""
    r = buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, SETUP], "2026-09-02T00:00:00Z"),
        release("1.0.0", [FULL], "2026-09-03T00:00:00Z"),
    ])
    assert r["tag"] == "pyinstaller-v0.9.9"
    assert r["url"].endswith(SETUP)


def test_sin_ningun_instalador_nuevo_no_ofrece_nada():
    """Nada que instalar es distinto de instalar algo viejo: no se retrocede
    a una release anterior a la que ya corre."""
    assert buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL], "2026-09-02T00:00:00Z"),
    ]) is None


def test_sin_releases_nuevas_no_ofrece_nada():
    assert buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
    ]) is None


def test_en_linux_el_instalador_no_cuenta():
    """La release nueva no trae paquete update, así que Linux baja el full;
    que tenga o no .exe de Windows no cambia nada."""
    r = buscar([
        release("0.9.8", [FULL, UPDATE], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL], "2026-09-02T00:00:00Z"),
    ], windows=False)
    assert r["mode"] == "full"
    assert r["tag"] == "pyinstaller-v0.9.9"


WUPD = updater.WIN_UPDATE_ASSET_NAME


def test_con_la_cadena_de_deltas_entera_va_por_deltas():
    r = buscar([
        release("0.9.8", [FULL, SETUP, WUPD], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, WUPD], "2026-09-02T00:00:00Z"),
        release("1.0.0", [FULL, SETUP, WUPD], "2026-09-03T00:00:00Z"),
    ])
    assert r["mode"] == "chain" and r["instalador"]
    assert [tag for tag, _ in r["hops"]] == ["pyinstaller-v0.9.9", "pyinstaller-v1.0.0"]
    assert r["hops"][-1][1].endswith(WUPD)


def test_un_eslabon_sin_delta_cae_al_instalador_completo():
    """La 0.9.9 se publicó antes de los deltas: desde la 0.9.8 no hay cadena."""
    r = buscar([
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL], "2026-09-02T00:00:00Z"),
        release("1.0.0", [FULL, SETUP, WUPD], "2026-09-03T00:00:00Z"),
    ])
    assert r["mode"] == "setup" and r["url"].endswith("1.0.0/" + SETUP)


def test_la_cadena_no_pasa_de_la_ultima_con_instalador():
    """La 1.0.0 no trae nada de Windows (su build falló): la cadena llega
    hasta la 0.9.9, la misma que el instalador completo."""
    r = buscar([
        release("0.9.8", [FULL, SETUP, WUPD], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, SETUP, WUPD], "2026-09-02T00:00:00Z"),
        release("1.0.0", [FULL], "2026-09-03T00:00:00Z"),
    ])
    assert r["tag"] == "pyinstaller-v0.9.9"
    assert [tag for tag, _ in r["hops"]] == ["pyinstaller-v0.9.9"]


def test_build_desconocida_no_usa_deltas():
    """Sin saber en qué release está, ningún delta sirve de base."""
    r = buscar([
        release("0.9.8", [FULL, SETUP, WUPD], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, SETUP, WUPD], "2026-09-02T00:00:00Z"),
    ], local="0.9.8-rdev")
    assert r["mode"] == "setup"


def test_trae_tamano_y_sha256_para_verificar():
    rels = [
        release("0.9.8", [FULL, SETUP], "2026-09-01T00:00:00Z"),
        release("0.9.9", [FULL, SETUP], "2026-09-02T00:00:00Z"),
    ]
    for a in rels[1]["assets"]:
        a["size"] = 1234
        a["digest"] = "sha256:ABCD"
    r = buscar(rels)
    assert r["verificar"][r["url"]] == {"size": 1234, "sha256": "abcd"}


def test_script_windows_corre_en_fila_y_solo_el_ultimo_relanza():
    s = updater._script_windows(3)
    pasos = [l for l in s.split("\r\n") if l.startswith('start "" /wait')]
    assert len(pasos) == 3
    assert all("/SUPPRESSMSGBOXES" in p and "/LOG=" in p for p in pasos)
    assert ["/LAUNCH=1" in p for p in pasos] == [False, False, True]
    assert s.count("if errorlevel 1 goto fallo") == 3
    # Nada de rutas absolutas adentro: cmd lee el .cmd en OEM (ver docstring).
    assert ":\\" not in s
    s.encode("ascii")


def _con_dist(tmp, fn):
    original = (updater._dist_dir, updater.local_build_id)
    updater._dist_dir = lambda: Path(tmp)
    try:
        return fn()
    finally:
        updater._dist_dir, updater.local_build_id = original


def _pendiente(tmp, carpeta, instalador=True, hace=0):
    ruta = Path(tmp) / updater.PENDIENTE
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"esperado": "0.9.9", "desde": "0.9.8", "carpeta": str(carpeta),
                                "cuando": time.time() - hace, "instalador": instalador}))
    return ruta


def test_update_que_llego_borra_marca_y_descargas():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp) / "descarga"
        carpeta.mkdir()
        ruta = _pendiente(tmp, carpeta)

        def correr():
            updater.local_build_id = lambda _v: "0.9.9"
            return updater.revisar_update_anterior("v0.9.8")
        assert _con_dist(tmp, correr) is None
        assert not ruta.exists() and not carpeta.exists()


def test_update_que_no_llego_avisa_con_el_log():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp) / "descarga"
        carpeta.mkdir()
        (carpeta / "FALLO").write_text("1")
        (carpeta / "aplicar.log").write_text("paso 1 de 1\nFALLO 1\n")
        (carpeta / "paso1.log").write_text("Delta para 0.9.8, instalada: \"0.9.7\"\n")
        ruta = _pendiente(tmp, carpeta)

        def correr():
            updater.local_build_id = lambda _v: "0.9.8"
            return updater.revisar_update_anterior("v0.9.8")
        r = _con_dist(tmp, correr)
        assert r["esperado"] == "0.9.9" and r["actual"] == "0.9.8"
        assert "FALLO 1" in r["log"] and "instalada" in r["log"]
        assert not ruta.exists(), "se avisa una sola vez"


def test_instalador_trabajando_no_es_falla():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp) / "descarga"
        carpeta.mkdir()
        ruta = _pendiente(tmp, carpeta, hace=60)

        def correr():
            updater.local_build_id = lambda _v: "0.9.8"
            return updater.revisar_update_anterior("v0.9.8")
        assert _con_dist(tmp, correr) == {"en_curso": True}
        assert ruta.exists()
        # Pasada la gracia, sin FALLO, ya no se espera más.
        _pendiente(tmp, carpeta, hace=updater.PENDIENTE_GRACIA_S + 1)
        assert _con_dist(tmp, correr)["esperado"] == "0.9.9"


def test_limpiar_temporales_respeta_recientes_y_la_pendiente():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as dist:
        original = tempfile.tempdir
        tempfile.tempdir = tmp
        try:
            vieja, reciente, pendiente, ajena = (Path(tmp) / n for n in (
                updater.TMP_PREFIX + "a", updater.TMP_PREFIX + "b", updater.TMP_PREFIX + "c", "otra_cosa"))
            for c in (vieja, reciente, pendiente, ajena):
                c.mkdir()
                (c / "paso1.exe").write_bytes(b"x")
            hace_dos_horas = time.time() - 7200
            for c in (vieja, pendiente, ajena):
                os.utime(c, (hace_dos_horas, hace_dos_horas))
            _pendiente(dist, pendiente)
            _con_dist(dist, updater.limpiar_temporales)
            assert not vieja.exists()
            assert reciente.exists() and pendiente.exists() and ajena.exists()
        finally:
            tempfile.tempdir = original


class _Servidor(BaseHTTPRequestHandler):
    """Sirve DATOS; la primera respuesta se corta a la mitad (como la red
    del laboratorio). Respeta Range."""
    cortar = True
    pedidos = []

    def do_GET(self):
        rango = self.headers.get("Range")
        _Servidor.pedidos.append(rango)
        desde = int(rango.split("=")[1].rstrip("-")) if rango else 0
        cuerpo = DATOS[desde:]
        self.send_response(206 if rango else 200)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if _Servidor.cortar:
            _Servidor.cortar = False
            self.wfile.write(cuerpo[:len(cuerpo) // 2])
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_RDWR)
            return
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass


DATOS = bytes(range(256)) * 4000


def _servir():
    srv = HTTPServer(("127.0.0.1", 0), _Servidor)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}/x"


def test_descarga_cortada_sigue_desde_donde_quedo():
    srv, url = _servir()
    original = updater.time.sleep
    updater.time.sleep = lambda _s: None
    _Servidor.cortar, _Servidor.pedidos = True, []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "paso1.exe"
            esperado = {"size": len(DATOS), "sha256": hashlib.sha256(DATOS).hexdigest()}
            updater._download(url, dest, lambda *_: None, esperado)
            assert dest.read_bytes() == DATOS
            assert not (Path(tmp) / "paso1.exe.part").exists()
            assert _Servidor.pedidos[0] is None and _Servidor.pedidos[1].startswith("bytes=")
    finally:
        updater.time.sleep = original
        srv.shutdown()


def test_descarga_que_no_coincide_no_queda_como_buena():
    srv, url = _servir()
    original = updater.time.sleep
    updater.time.sleep = lambda _s: None
    _Servidor.cortar = False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "paso1.exe"
            try:
                updater._download(url, dest, lambda *_: None, {"sha256": "0" * 64})
            except ValueError as exc:
                assert "no coincide" in str(exc)
            else:
                raise AssertionError("aceptó una descarga con otro sha256")
            assert not dest.exists() and not (Path(tmp) / "paso1.exe.part").exists()
    finally:
        updater.time.sleep = original
        srv.shutdown()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
