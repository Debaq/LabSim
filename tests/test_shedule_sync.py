"""
Filas "sin agendar" de la agenda: casos que existen en cases pero no tienen
ninguna cita en appointments (los que el panel muestra en admin/patients.php).

Se agregan a agenda_1 como filas sintéticas con key "case:<id>" para que el
docente las vea/pruebe, pero NO son citas: si el diff de subida las tratara
como tales, int("case:c3") reventaría y/o se crearían citas fantasma en el
backend en cada Shedule.set().
"""

import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from backend.shedule_sync import backend_state_to_shedule, diff_and_push_shedule


class _ClienteEspia:
    def __init__(self):
        self.llamadas = []

    def upsert_appointment(self, appointment_id, **fields):
        self.llamadas.append(("upsert", appointment_id))
        return {"appointment": {"id": 99}}

    def delete_appointment(self, appointment_id):
        self.llamadas.append(("delete", appointment_id))

    def post_attendance_action(self, appointment_id, estado, nota=""):
        self.llamadas.append(("attendance", appointment_id, estado))


def _state():
    return {
        "students": [],
        "attendances": [],
        "appointments": [
            {"id": 1, "fecha": "01-01-26", "hora": "10:00", "rut": "9",
             "nombre": "Ana", "apellido": "Paz", "case_id": "c1"},
        ],
        "cases": [
            {"id": "c1", "data": {}},
            {"id": "c2", "data": {}, "paciente_rut": "77",
             "paciente_nombre": "Sin", "paciente_apellido": "Agendar",
             "paciente_fecha_nac": "01-01-90"},
            {"id": "c3", "data": {"paciente_snapshot": {
                "rut": "55", "nombre": "Cita", "apellido": "Borrada"}}},
        ],
    }


def test_caso_sin_cita_entra_como_fila_sin_agendar():
    agenda = backend_state_to_shedule(_state(), 1, "doc")["agenda_1"]

    assert set(agenda) == {"1", "case:c2", "case:c3"}
    assert agenda["1"].sin_cita is False

    fila = agenda["case:c2"]
    assert (fila.sin_cita, fila.nombre, fila.apellido, fila.rut) == (True, "Sin", "Agendar", "77")
    assert fila.fecha == "" and fila.hora == ""


def test_identidad_cae_al_snapshot_si_el_caso_no_tiene_paciente():
    """Caso huérfano de una cita borrada: el nombre vive en cases.data."""
    agenda = backend_state_to_shedule(_state(), 1, "doc")["agenda_1"]
    fila = agenda["case:c3"]
    assert (fila.nombre, fila.apellido, fila.rut) == ("Cita", "Borrada", "55")


def test_las_filas_sin_cita_nunca_se_empujan_al_backend():
    shedule = backend_state_to_shedule(_state(), 1, "doc")
    cliente = _ClienteEspia()

    diff_and_push_shedule(cliente, shedule, deepcopy(shedule), "doc")
    assert cliente.llamadas == []

    # El caso se agendó desde el panel: la fila sintética desaparece, pero eso
    # no es una cita eliminada -- no se puede llamar delete_appointment con
    # "case:c2" (ni con ninguna otra cosa).
    nuevo = deepcopy(shedule)
    del nuevo["agenda_1"]["case:c2"]
    diff_and_push_shedule(cliente, nuevo, shedule, "doc")
    assert cliente.llamadas == []
