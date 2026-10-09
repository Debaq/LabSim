"""La agenda se arma con el delta del sync (core/helpers.aplicar_delta) en
vez de bajar todo cada ciclo (antes: sync desde 1970 cada 15 s por equipo).

El delta no avisa borrados ni reasignaciones: para eso el servidor manda
appointment_ids (las citas que hoy le tocan) y lo que no está se saca.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import helpers  # noqa: E402


class _Cliente:
    def __init__(self, role="student"):
        self.user = {"id": 1, "username": "alumno", "role": role}


def _cita(i, nombre="Ana", case_id="c1"):
    return {"id": i, "fecha": "09-10-26", "hora": "10:00", "rut": "9", "nombre": nombre,
            "apellido": "Paz", "fecha_nac": "", "procedimiento": "Audiometría",
            "case_id": case_id, "nota_admin": "", "practice_id": None}


def _preparar(role="student", citas=(1, 2)):
    helpers._backend_client = _Cliente(role)
    helpers._estado_agenda = helpers._indexar({
        "students": [],
        "appointments": [_cita(i) for i in citas],
        "cases": [{"id": "c1", "data": {}}],
        "attendances": [],
    })


def _delta(**kw):
    base = {"appointments": [], "cases": [], "attendances": [], "appointment_ids": [1, 2]}
    base.update(kw)
    return base


def test_sin_cambios_no_toca_la_agenda():
    _preparar()
    assert helpers.aplicar_delta(_delta()) == ("igual", None)


def test_una_cita_nueva_aparece_sin_bajar_todo():
    _preparar()
    que, data = helpers.aplicar_delta(_delta(appointments=[_cita(3, "Beto")],
                                              appointment_ids=[1, 2, 3]))
    assert que == "nuevo"
    assert sorted(data["agenda_1"]) == ["1", "2", "3"]
    assert data["agenda_1"]["3"].nombre == "Beto"
    assert helpers._shedule_snapshot == data   # el diff de subida queda al día
    assert helpers._shedule_snapshot is not data


def test_una_cita_editada_se_reemplaza():
    _preparar()
    _, data = helpers.aplicar_delta(_delta(appointments=[_cita(2, "Carla")]))
    assert data["agenda_1"]["2"].nombre == "Carla"


def test_mi_atencion_llega_en_el_delta():
    _preparar()
    att = {"id": 10, "appointment_id": 1, "student_id": 1, "estado": "atendiendo",
           "nota": "", "hora_real": "10:01:00"}
    _, data = helpers.aplicar_delta(_delta(attendances=[att]))
    assert data["agenda_1"]["1"].atencion["alumno"]["estado"] == "atendiendo"


def test_una_cita_borrada_o_reasignada_se_va():
    _preparar()
    que, data = helpers.aplicar_delta(_delta(appointment_ids=[1]))
    assert que == "nuevo"
    assert "2" not in data["agenda_1"] and "1" in data["agenda_1"]


def test_backend_sin_appointment_ids_baja_todo_si_cambio_algo():
    _preparar()
    sin_ids = {"appointments": [_cita(3)], "cases": [], "attendances": []}
    assert helpers.aplicar_delta(sin_ids) == ("completo", None)
    assert helpers.aplicar_delta({"appointments": []}) == ("igual", None)


def test_sin_agenda_bajada_pide_todo():
    helpers._estado_agenda = None
    assert helpers.aplicar_delta(_delta()) == ("completo", None)


def test_el_docente_baja_todo_si_atiende_un_alumno_que_no_conoce():
    _preparar(role="admin")
    att = {"id": 11, "appointment_id": 1, "student_id": 55, "estado": "atendido",
           "nota": "", "hora_real": ""}
    assert helpers.aplicar_delta(_delta(attendances=[att])) == ("completo", None)


def test_un_ciclo_se_despierta_con_ahora():
    import time
    from core import hilos

    pasos = []

    class _Lento(hilos.Ciclo):
        def paso(self):
            pasos.append(time.monotonic())

    ciclo = _Lento(60, "lento")
    ciclo.start()
    time.sleep(0.1)
    ciclo.ahora()
    fin = time.time() + 2
    while time.time() < fin and len(pasos) < 2:
        time.sleep(0.01)
    ciclo.stop()
    assert len(pasos) == 2, pasos           # no esperó los 60 s
    assert not ciclo.isRunning()


def test_sesion_vencida_avisa_una_vez_y_para_el_sync():
    import time
    import requests
    from core import hilos
    from core.base import context
    from backend.sync_thread import SyncThread

    class _Vencido:
        llamadas = 0

        def get_sync(self, since):
            _Vencido.llamadas += 1
            r = requests.Response()
            r.status_code = 401
            raise requests.HTTPError("Sesión vencida o revocada", response=r)

    avisos = []
    sync = SyncThread(_Vencido(), interval_s=0.01, al_vencer=lambda: avisos.append(1))
    sync.start()
    fin = time.time() + 3
    while time.time() < fin and (sync.isRunning() or not avisos):
        context.app.processEvents()
        time.sleep(0.01)
    assert avisos == [1], avisos
    assert not sync.isRunning() and _Vencido.llamadas == 1


def test_sin_red_el_sync_sigue_callado():
    import time
    import requests
    from backend.sync_thread import SyncThread

    class _SinRed:
        llamadas = 0

        def get_sync(self, since):
            _SinRed.llamadas += 1
            raise requests.ConnectionError("sin red")

    avisos = []
    sync = SyncThread(_SinRed(), interval_s=0.01, al_vencer=lambda: avisos.append(1))
    sync.start()
    time.sleep(0.2)
    sync.stop()
    assert avisos == [] and _SinRed.llamadas > 2


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
    sys.exit(1 if fallas else 0)
