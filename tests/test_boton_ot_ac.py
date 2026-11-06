"""Un solo botón para otoscopía y diapasones (2026-11-06).

El layout del servidor sigue mandando OT y AC por separado (para las
versiones anteriores); la app muestra un botón "OT/AC" que abre la ventana
de los dos (audiometria/ventana_ot_ac.py) si el curso tiene cualquiera.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from core.ui_helpers import ToolBar  # noqa: E402

APPS = {c: [False, c, i, [False, True], "max", "pre"] for i, c in enumerate(("OT", "AC", "A", "Z"), 1)}


class _Barra:
    chargeBtnsArea = ToolBar.chargeBtnsArea
    _module_visible = ToolBar._module_visible

    def __init__(self, modulos):
        self.boxs = {"Box_1": [True, ["OT", "AC", "A", "Z"], "Box Audiología"]}
        self.apps = APPS
        self._caja = QWidget()
        self.layouts = [None, QHBoxLayout(self._caja)]
        self.data_login = {"user": "x", "permission": 444, "modules": modulos}

    def activate_soft(self):
        pass

    def pintar_botones_modulos(self):
        pass

    def botones(self):
        lay = self.layouts[1]
        return [lay.itemAt(i).widget() for i in range(lay.count())
                if isinstance(lay.itemAt(i).widget(), QPushButton)]


def _nombres(modulos):
    barra = _Barra(modulos)
    barra.chargeBtnsArea("Box_1")
    return [(b.objectName(), b.text()) for b in barra.botones()]


def test_con_los_dos_hay_un_solo_boton():
    assert _nombres(["OT", "AC", "A", "Z"]) == [("btn_AC", "OT/AC"), ("btn_A", "A"), ("btn_Z", "Z")]


def test_con_solo_otoscopia_tambien_aparece():
    # Como el curso 2: tiene OT y no AC
    assert _nombres(["OT", "Z"]) == [("btn_AC", "OT/AC"), ("btn_Z", "Z")]


def test_con_solo_acumetria_aparece():
    assert _nombres(["AC"]) == [("btn_AC", "OT/AC")]


def test_sin_ninguno_no_aparece():
    assert _nombres(["A"]) == [("btn_A", "A")]


def test_la_ventana_se_abre_con_cualquiera_de_los_dos():
    from core.ui_helpers import VENTANA_DE
    solo_ot = _Barra(["OT", "Z"])
    assert any(solo_ot._module_visible(c) for c in VENTANA_DE["AC"])
    assert not solo_ot._module_visible("AC"), "pero sin la pestaña de diapasones"


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
