"""
Atender a un paciente con otro abierto (main.MainWindow._otra_atencion_abierta).

Con una atención real se pide cerrarla primero. En la prueba del docente
cambiaba de paciente sin decir nada; ahora pregunta, y si dice que no sigue
con el que tenía.
"""

import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtWidgets import QMessageBox, QWidget  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import main  # noqa: E402


class _Main(QWidget):
    """Lo que _otra_atencion_abierta le pide a la ventana."""

    def __init__(self, appointment_id):
        super().__init__()
        self.data_current_key = "10"
        self.paciente_actual = {"nombre": "Lourdes", "appointment_id": appointment_id}
        self.cerradas = []

    def cerrar_atencion_prueba(self, nota):
        self.cerradas.append(nota)
        self.data_current_key = None


def _con_respuesta(boton, fn):
    """Corre fn con el diálogo contestado solo (sin ventana que bloquee)."""
    vistos = []
    original = QMessageBox.exec

    def contestar(dlg):
        vistos.append(dlg.text())
        return boton

    QMessageBox.exec = contestar
    try:
        return fn(), vistos
    finally:
        QMessageBox.exec = original


def _otra(m, key):
    return main.MainWindow._otra_atencion_abierta(m, key)


def test_en_prueba_pregunta_y_si_dice_que_no_sigue_con_el_que_tenia():
    m = _Main(None)
    bloquea, vistos = _con_respuesta(QMessageBox.StandardButton.No, lambda: _otra(m, "11"))
    assert bloquea and "Lourdes" in vistos[0] and "prueba" in vistos[0]
    assert m.cerradas == [] and m.data_current_key == "10"


def test_en_prueba_si_dice_que_si_cierra_la_prueba_y_deja_pasar():
    m = _Main(None)
    bloquea, _ = _con_respuesta(QMessageBox.StandardButton.Yes, lambda: _otra(m, "11"))
    assert not bloquea and m.cerradas and m.data_current_key is None


def test_con_una_atencion_real_hay_que_cerrarla_primero():
    m = _Main(55)
    bloquea, vistos = _con_respuesta(QMessageBox.StandardButton.Ok, lambda: _otra(m, "11"))
    assert bloquea and "Ciérrala primero" in vistos[0]


def test_el_mismo_paciente_o_ninguno_abierto_no_avisa():
    m = _Main(None)
    assert _con_respuesta(QMessageBox.StandardButton.No, lambda: _otra(m, "10")) == (False, [])
    m.data_current_key = None
    assert _con_respuesta(QMessageBox.StandardButton.No, lambda: _otra(m, "11")) == (False, [])


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
