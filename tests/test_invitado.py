"""
Modo invitado (core/invitado.py): practicar con los pacientes del libro sin
cuenta. No hay token ni API: todo sale del catálogo de la app, no se usa la
sesión que haya quedado en el equipo y no se deja registro.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import requests  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from backend import client as backend_client  # noqa: E402
from backend.client import BackendClient  # noqa: E402
from backend.log_queue import LocalLogQueue  # noqa: E402
from core import helpers, invitado  # noqa: E402


def _con_invitado(fn):
    invitado.activar()
    try:
        return fn()
    finally:
        invitado.desactivar()


def test_el_catalogo_trae_la_practica_libre_del_libro():
    """Las mismas carpetas y pacientes que la práctica libre del backend."""
    cat = invitado.catalogo()
    assert len(cat["items"]) == 145 and len(cat["casos"]) == 112
    raul = next(it for it in invitado.items_practica() if it["case_id"] == "119")
    assert raul["procedimiento"] == "VEMP" and raul["carpeta"] == "Cap. 20 · VEMP"
    assert raul["intentos"] == 0 and raul["abierto"] is None
    assert "case:119" in invitado.agenda()["agenda_1"]


def test_sin_api_no_lee_la_sesion_del_equipo_ni_hace_pedidos():
    """session.json puede tener el token del último alumno que entró."""
    carpeta = Path(tempfile.mkdtemp())
    sesion = carpeta / "session.json"
    sesion.write_text(json.dumps({"token": "token-de-otro", "user": {"id": 7, "username": "ana"}}))

    def probar():
        c = BackendClient("https://ejemplo.invalid", sesion)
        assert c.token is None and c.user is None, "no hereda la sesión de otro"
        for pedido in (lambda: c.get_sync("1970-01-01"), lambda: c.get_practica(),
                       lambda: c.llm_chat("1", "x", 1, "", [], "hola")):
            try:
                pedido()
            except requests.ConnectionError as exc:
                assert "invitado" in str(exc)
            else:
                raise AssertionError("salió un pedido a la API")
    _con_invitado(probar)
    assert BackendClient("https://ejemplo.invalid", sesion).token == "token-de-otro", \
        "fuera del modo invitado, la sesión vuelve a contar"


def test_el_invitado_no_deja_eventos_en_la_cola():
    """Quedarían sin dueño y el próximo alumno los subiría a su nombre."""
    cola = LocalLogQueue(Path(tempfile.mkdtemp()) / "logs.db")
    _con_invitado(lambda: cola.push("audio_stim_button", {"f": 1000}))
    assert cola.pop_batch() == []
    cola.push("audio_stim_button", {"f": 1000})
    assert len(cola.pop_batch()) == 1


def test_la_agenda_los_casos_y_las_fotos_salen_de_la_app():
    def probar():
        assert helpers.Shedule().get()["agenda_1"]["case:119"].nombre == "Raúl Enrique"
        assert helpers.CasesOffline().get_cases()["119"]["Anamnesis"]["otros"].startswith("Tiene 45 años")
        assert helpers.CasesOffline.en_memoria("119") is not None
        assert len(helpers.lista_practica()) == 145
        assert helpers.foto_otoscopia("119", "od")[:2] == b"\xff\xd8", "la foto del libro, en JPEG"
        assert helpers.sesion_es_docente() is False
    _con_invitado(probar)
    assert backend_client.sin_api is False and invitado.activo is False


def test_la_ficha_del_invitado_cuenta_lo_que_diria_el_paciente_y_trae_los_informes():
    """Sin chat: el relato va escrito y los informes salen desde el principio."""
    from types import SimpleNamespace
    from core import ficha

    def probar():
        caso = invitado.casos()["119"]
        snap = caso["paciente_snapshot"]
        row = SimpleNamespace(fecha="", hora="", rut=snap["rut"], nombre=snap["nombre"],
                              apellido=snap["apellido"], fecha_nac=snap["fecha_nac"], procedimiento="VEMP",
                              atencion={}, case_id="119", practice_id=1)
        html = ficha.render_ficha_html(row, caso, {"agenda_1": {}}, invitado.USUARIO, False)
        assert "LO QUE CUENTA EL PACIENTE" in html and "chofer de buses" in html
        assert "Trae los informes." in html and "previo:119/" in html
    _con_invitado(probar)


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
