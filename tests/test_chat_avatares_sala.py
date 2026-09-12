"""
Caras del chat con acompañantes (agenda/ChatPaciente.py).

El paciente es `p1` en la sala (ver Sala.php) pero su foto se guarda con la
clave histórica del caso -- el case_id pelado, persona vacía (ver
PatientPhoto::key). Al pedirla como `p1` el backend devolvía 404 y el
paciente quedaba con el círculo de iniciales aunque tuviera foto subida,
que es lo que se notaba en los chats con más de un interlocutor: los
acompañantes con su cara y el paciente sin la suya.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtGui import QColor, QPixmap

from core.base import context  # crea la QApplication
from agenda.ChatPaciente import ChatPacienteWidget

SALA = [
    {"id": "p1", "nombre": "Juan", "rol": "paciente", "etiqueta": "Juan", "es_paciente": True, "informante": False},
    {"id": "p2", "nombre": "Rosa", "rol": "madre", "etiqueta": "Rosa (Madre)", "es_paciente": False, "informante": True},
]


def _widget():
    w = ChatPacienteWidget(usuario_nombre="Alumno")
    w._case_id = "caso1"
    return w


def test_foto_key_paciente_es_la_clave_historica():
    w = _widget()
    w._aplicar_sala(SALA)
    assert w._foto_key("p1") == ""
    assert w._foto_key("p2") == "p2"
    assert w._foto_key(ChatPacienteWidget._PACIENTE_ID) == ""


def test_foto_key_sin_sala_usa_el_respaldo():
    """Si la sala no se pudo traer, la burbuja llega igual: el respaldo
    __paciente__ tiene que seguir apuntando a la clave del caso."""
    w = _widget()
    assert w._foto_key(ChatPacienteWidget._PACIENTE_ID) == ""
    assert w._foto_key("p2") == "p2"


def test_la_foto_del_paciente_se_reusa_al_llegar_la_sala():
    """El paciente se pinta dos veces (respaldo __paciente__ y después p1).
    La segunda no vuelve a la red ni pasa por las iniciales."""
    w = _widget()
    pm = QPixmap(8, 8)
    pm.fill(QColor("#ff0000"))
    w._fotos[""] = pm
    pedidos = []
    w._pedir_avatar = lambda pid: pedidos.append(pid)

    w._asegurar_avatar(ChatPacienteWidget._PACIENTE_ID, "Juan")
    w._aplicar_sala(SALA)
    w._asegurar_avatar("p1", "Juan")
    w._asegurar_avatar("p2", "Rosa (Madre)")

    assert pedidos == ["p2"]  # el paciente ya tenía su foto en memoria
