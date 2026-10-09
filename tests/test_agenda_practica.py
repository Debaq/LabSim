"""
Práctica libre en la agenda del alumno (agenda/Agenda.py, ver
labsim_backend/src/Practica.php): la lista de práctica se ve aparte de la
agenda, los intentos no aparecen como citas, y el botón sigue el ciclo
Practicar -> (intento abierto) -> Cerrar/Evolucionar, o Retomar si la app se
cerró con el intento abierto.

Sin red: Shedule y la API de práctica se reemplazan por dobles.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import Qt

from core.base import context  # crea la QApplication
from backend.shedule_sync import AgendaEntry
import agenda.Agenda as mod

APP = context.app


def _agenda_estado():
    hoy = mod.QDate.currentDate().toString("dd-MM-yy")
    return {"agenda_1": {
        "10": AgendaEntry(fecha=hoy, hora="09:00", nombre="Cita", apellido="Normal", case_id="c1"),
        "11": AgendaEntry(fecha=hoy, hora="21:00", nombre="Intento", apellido="Viejo", case_id="c2",
                          practice_id=1, atencion={"alumno": {"estado": "atendido"}}),
    }}


class _SheduleFalso:
    def get(self):
        return _agenda_estado()


class _Main:
    def __init__(self):
        self.data_login = {"user": "alumno", "permission": 444}
        self.data_current_key = None
        self.atendidos = []
        self.evoluciones = []

    def atender_paciente(self, key):
        self.atendidos.append(key)
        self.data_current_key = key

    def abrir_evolucion(self, nombre, guardar, key=None):
        self.evoluciones.append((nombre, key))


ITEMS = [{"id": 1, "case_id": "c2", "procedimiento": "Audiometría", "show_study_sheet": True,
          "curso": "C1", "nombre": "Ana", "apellido": "Paz", "rut": "1-9", "fecha_nac": "",
          "intentos": 1, "ultimo": "2026-10-08 20:00:00", "ultimo_cerrado": 11, "abierto": None}]


def _armar(monkey_iniciar):
    mod.Shedule = _SheduleFalso
    mod.lista_practica = lambda: [dict(it) for it in ITEMS]
    mod.iniciar_practica = monkey_iniciar
    main = _Main()
    ag = mod.Agenda(444, main)
    # Sin hilo: se entrega la lista como lo haría _pedir_practica (hilos.en_fondo).
    ag._pedir_practica = lambda: ag._on_practica_fetched(mod.lista_practica())
    ag.refresh_async = ag._pedir_practica
    return ag, main


def _filas(ag):
    return [ag.tableWidget.item(r, 3).text() for r in range(ag.tableWidget.rowCount())]


def test_los_intentos_no_aparecen_en_la_agenda():
    ag, _ = _armar(lambda pid: {})
    assert _filas(ag) == ["Cita"], _filas(ag)


def test_practicar_abre_un_intento_y_despues_se_cierra():
    abiertos = []

    def iniciar(pid):
        abiertos.append(pid)
        return {"id": 42}

    ag, main = _armar(iniciar)
    ag.btn_practica.setChecked(True)
    assert _filas(ag) == ["Ana"], _filas(ag)
    ag.tableWidget.selectRow(0)
    assert ag.btn_atender.text() == "Practicar"
    assert ag.btn_ficha_estudio.isEnabled()
    assert not ag.btn_ver_ficha.isEnabled()

    ag.btn_atender.click()
    assert abiertos == [1] and main.atendidos == ["42"]
    assert ag.btn_atender.text() == "Cerrar/Evolucionar", ag.btn_atender.text()

    ag.btn_atender.click()
    assert main.evoluciones == [("Ana Paz", "42")]

    ag.btn_practica.setChecked(False)
    assert _filas(ag) == ["Cita"]


def test_intento_abierto_de_otra_vez_se_retoma():
    ag, main = _armar(lambda pid: (_ for _ in ()).throw(AssertionError("no debe crear otro")))
    ITEMS[0]["abierto"] = 77
    try:
        ag.btn_practica.setChecked(True)
        ag.tableWidget.selectRow(0)
        assert ag.btn_atender.text() == "Retomar"
        ag.btn_atender.click()
        assert main.atendidos == ["77"]
    finally:
        ITEMS[0]["abierto"] = None


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
