"""Mouse para zurdos dentro de LabSim (core/mouse_zurdo.py).

Solo con LABSIM_KIOSKO=1 y la preferencia del alumno activada: el botón
derecho hace lo que haría el izquierdo y al revés, menú contextual incluido.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QPushButton, QWidget  # noqa: E402

from core.base import context  # noqa: E402,F401
from core import mouse_zurdo  # noqa: E402
from core.preferencias import preferencias  # noqa: E402


class Lienzo(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(100, 100)
        self.menus = 0
        self.presiones = []

    def contextMenuEvent(self, ev):
        self.menus += 1

    def mousePressEvent(self, ev):
        self.presiones.append(ev.button())


def _zurdo(kiosko, pref):
    os.environ["LABSIM_KIOSKO"] = "1" if kiosko else "0"
    preferencias().cargar({"mouse_zurdo": pref})
    mouse_zurdo.aplicar()


def _clics(boton):
    b = QPushButton("x")
    b.resize(60, 30)
    b.show()
    veces = []
    b.clicked.connect(lambda: veces.append(1))
    QTest.mouseClick(b, boton)
    b.close()
    return len(veces)


def test_sin_kiosko_no_se_invierte():
    _zurdo(kiosko=False, pref=True)
    assert not mouse_zurdo.activo()
    assert _clics(Qt.LeftButton) == 1


def test_kiosko_y_zurdo_invierte_el_clic():
    _zurdo(kiosko=True, pref=True)
    assert mouse_zurdo.activo()
    assert _clics(Qt.LeftButton) == 0
    assert _clics(Qt.RightButton) == 1


def test_el_widget_ve_el_boton_invertido():
    _zurdo(kiosko=True, pref=True)
    w = Lienzo()
    w.show()
    QTest.mousePress(w, Qt.RightButton, pos=QPoint(10, 10))
    QTest.mouseRelease(w, Qt.RightButton, pos=QPoint(10, 10))
    assert w.presiones == [Qt.LeftButton]
    assert w.menus == 0          # el derecho físico ya no abre el menú
    w.close()


def test_el_menu_contextual_sale_con_el_izquierdo():
    _zurdo(kiosko=True, pref=True)
    w = Lienzo()
    w.show()
    QTest.mouseClick(w, Qt.LeftButton, pos=QPoint(10, 10))
    assert w.menus == 1
    w.close()


def test_preferencia_apagada_vuelve_a_lo_normal():
    _zurdo(kiosko=True, pref=True)
    _zurdo(kiosko=True, pref=False)
    assert not mouse_zurdo.activo()
    assert _clics(Qt.LeftButton) == 1


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
    _zurdo(kiosko=False, pref=False)
    sys.exit(1 if fallas else 0)
