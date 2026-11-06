"""Abrir y cerrar atenciones sin red (core/acciones_pendientes.py) y la
práctica libre guardada en el equipo (invitado.descargar_catalogo).

Partes 2 y 3 de docs/roadmap_sin_servidor.md, 2026-11-06: el servidor
perdía paquetes en pleno práctico y abrir o cerrar una atención fallaba.
"""

import gzip
import json
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["LABSIM_DATA_DIR"] = tempfile.mkdtemp(prefix="labsim_datos_")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import requests  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from core import acciones_pendientes as ap, respaldo_informes, rutas  # noqa: E402
from core import report_autosave  # noqa: E402
from backend import client as cliente_mod  # noqa: E402


def _http(codigo):
    r = requests.Response()
    r.status_code = codigo
    return requests.HTTPError(str(codigo), response=r)


class Cliente:
    """BackendClient falso: anota lo que se le manda y falla como se le diga."""

    def __init__(self, uid=5, username="martin.soto", token="tok-5", fallas=()):
        self.user = {"id": uid, "username": username}
        self.token = token
        self.ajeno = False
        self.fallas = list(fallas)
        self.acciones = []

    def is_logged_in(self):
        return bool(self.token)

    def _fallar(self):
        if self.fallas:
            f = self.fallas.pop(0)
            if f == "red":
                raise requests.ConnectionError("sin red")
            if f is not None:
                raise _http(f)

    def post_attendance_action(self, cita, accion, nota=None):
        self._fallar()
        self.acciones.append((cita, accion, nota, self.token))
        return {}


def _limpiar():
    for archivo in rutas.carpeta("acciones_pendientes").glob("*.json"):
        archivo.unlink()


def test_sin_red_queda_en_cola_y_sale_en_orden_al_volver():
    _limpiar()
    c = Cliente(fallas=["red"])
    ap.encolar(c, 99, "atendiendo")
    ap.encolar(c, 99, "atendido", "evolución")
    assert ap.vaciar(c) == 2, "sin red no sale nada y no se pierde nada"
    assert c.acciones == []
    assert ap.vaciar(c) == 0
    assert [(a, b) for a, b, _, _ in c.acciones] == [(99, "atendiendo"), (99, "atendido")]
    assert not ap.hay_pendientes()


def test_la_agenda_muestra_lo_que_esta_en_cola():
    from backend.shedule_sync import AgendaEntry
    from core.helpers import con_pendientes
    _limpiar()
    c = Cliente()
    ap.encolar(c, 99, "atendido", "evolución")
    data = {"agenda_1": {"99": AgendaEntry(atencion={"martin.soto": {"estado": "atendiendo",
                                                                     "nota": "", "hora_real": "09:10:00"}}),
                         "100": AgendaEntry()}}
    con_pendientes(data, c.user)
    assert data["agenda_1"]["99"].atencion["martin.soto"] == {
        "estado": "atendido", "nota": "evolución", "hora_real": "09:10:00"}
    assert data["agenda_1"]["100"].atencion == {}
    _limpiar()


def test_antes_de_cerrar_suben_los_informes_del_equipo():
    _limpiar()
    orden = []
    c = Cliente()
    original = report_autosave.subir
    report_autosave.subir = lambda job, client=None: orden.append(("informe", job["tipo"]))
    c.post_attendance_action = lambda cita, accion, nota=None: orden.append((accion, cita))
    usuario = respaldo_informes.usuario_de(c)
    job = {"appointment_id": 99, "tipo": "ABR", "data": {"curvas": {"R1": 80}}}
    respaldo_informes.guardar(usuario, job, report_autosave.huella(job))
    try:
        ap.encolar(c, 99, "atendido", "nota")
        assert ap.vaciar(c) == 0
    finally:
        report_autosave.subir = original
    assert orden == [("informe", "ABR"), ("atendido", 99)], orden


def test_si_el_informe_no_sube_por_la_red_no_se_cierra():
    _limpiar()
    c = Cliente()
    original = report_autosave.subir

    def sin_red(job, client=None):
        raise requests.ConnectionError("sin red")

    report_autosave.subir = sin_red
    usuario = respaldo_informes.usuario_de(c)
    job = {"appointment_id": 98, "tipo": "VEMP", "data": {"x": 1}}
    respaldo_informes.guardar(usuario, job, report_autosave.huella(job))
    try:
        ap.encolar(c, 98, "atendido", "nota")
        assert ap.vaciar(c) == 1
    finally:
        report_autosave.subir = original
    assert c.acciones == [], "sin el informe no se marca atendido"
    _limpiar()


def test_lo_de_otro_alumno_sale_con_su_token_y_marcado_ajeno():
    _limpiar()
    antes = Cliente(uid=5, username="martin.soto", token="tok-soto")
    ap.encolar(antes, 99, "atendido", "nota")
    ahora = Cliente(uid=16, username="joan.pastenes", token="tok-pastenes")
    enviados = []
    original = cliente_mod.BackendClient.post_attendance_action

    def anotar(self, cita, accion, nota=None):
        enviados.append((cita, accion, self.token, self.ajeno, self._headers().get(cliente_mod.CABECERA_AJENO)))
        return {}

    cliente_mod.BackendClient.post_attendance_action = anotar
    try:
        assert ap.vaciar(ahora) == 0
    finally:
        cliente_mod.BackendClient.post_attendance_action = original
    assert enviados == [(99, "atendido", "tok-soto", True, "1")], enviados
    assert ahora.acciones == []


def test_un_401_con_token_ajeno_no_saca_a_quien_esta():
    avisos = []
    cliente_mod.al_perder_sesion = avisos.append
    try:
        resp = requests.Response()
        resp.status_code = 401
        resp.request = requests.Request("POST", "http://x", headers={
            "Authorization": "Bearer viejo", cliente_mod.CABECERA_AJENO: "1"}).prepare()
        cliente_mod._revisar_sesion(resp)
        assert avisos == []
        resp.request = requests.Request("POST", "http://x", headers={"Authorization": "Bearer mio"}).prepare()
        cliente_mod._revisar_sesion(resp)
        assert avisos == ["vencida"]
    finally:
        cliente_mod.al_perder_sesion = None


def test_lo_que_el_servidor_rechaza_se_bota_y_no_traba_lo_demas():
    _limpiar()
    c = Cliente(fallas=[404, None])
    ap.encolar(c, 7, "atendiendo")
    ap.encolar(c, 8, "atendiendo")
    assert ap.vaciar(c) == 0
    assert [a[0] for a in c.acciones] == [8]


def test_token_vencido_espera_a_que_vuelva_a_entrar():
    _limpiar()
    c = Cliente(fallas=[401])
    ap.encolar(c, 9, "atendido", "nota")
    assert ap.vaciar(c) == 1
    assert ap.vaciar(c) == 0 and c.acciones[0][:2] == (9, "atendido")


def test_la_practica_libre_queda_en_el_equipo_para_practicar_sin_cuenta():
    from core import invitado

    class ConPractica:
        def get_practica(self):
            return [{"id": 43, "folder_id": 11, "carpeta": "Cap. 11", "grupo": "Libro", "case_id": "79",
                     "orden": 2, "procedimiento": "PEATC", "nombre": "Víctor Pepe",
                     "apellido": "Cruz Arias", "rut": "21070440", "fecha_nac": "23-07-2002",
                     "intentos": 3},
                    {"id": 44, "folder_id": 11, "carpeta": "Cap. 11", "case_id": "999"}]  # sin caso: fuera

    estado = {"cases": [{"id": "79", "data": {"Rinne": {"500": {"od": "positivo"}}}}]}
    assert invitado.descargar_catalogo(ConPractica(), estado) == 1
    cat = json.loads(gzip.decompress((rutas.datos() / invitado.DESCARGADO).read_bytes()))
    assert [c["nombre"] for c in cat["carpetas"]] == ["Cap. 11"]
    assert cat["items"][0]["apellido"] == "Cruz Arias" and "intentos" not in cat["items"][0]
    assert invitado.catalogo()["casos"]["79"]["id"] == 79
    assert invitado.casos()["79"]["Rinne"] == {"500": {"od": "positivo"}}


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
            except Exception as exc:  # noqa: BLE001
                fallas += 1
                print(f"ERROR {nombre}: {type(exc).__name__}: {exc}")
    sys.exit(1 if fallas else 0)
