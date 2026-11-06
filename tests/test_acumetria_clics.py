"""Los botones de Acumetría reciben el clic (2026-11-06).

Desde el rediseño del 2026-10-26 los QButtonGroup tenían de dueño un QWidget
suelto que después se metía en la pestaña sin layout: Qt lo mostraba de
640x480 en la esquina, encima del panel, y se tragaba todos los clics. Los
diapasones no respondían y no quedaba nada en el registro. QTest.mouseClick
sobre el botón no lo veía (le manda el evento directo): acá se pregunta qué
widget está de verdad bajo el centro de cada botón, como haría el mouse.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtWidgets import QTabWidget  # noqa: E402

from core.base import context  # noqa: E402  (crea la QApplication)
from core.h_win import FrameSubMdi  # noqa: E402
import audiometria.Acumetria as A  # noqa: E402

APP = context.app


def _bajo_el_mouse(win, boton):
    return win.childAt(boton.mapTo(win, boton.rect().center()))


def test_nada_tapa_los_botones_de_los_diapasones():
    w = A.Acumetria(None)
    marco = FrameSubMdi(w, expand=True)
    marco.resize(1100, 650)
    marco.show()
    w.la_super({"id": 79, "edad": 24, "Weber": {"500": "oi"}}, 102)
    APP.processEvents()
    win = marco.window()
    pestanas = w.findChildren(QTabWidget)[0]
    botones = {0: ("rinne_500", "rinne_1000", "rinne_od", "rinne_oi", "btn_mastoides", "btn_pabellon",
                   "btn_comparar"),
               1: ("weber_500", "weber_1000", "btn_frente")}
    for pestana, nombres in botones.items():
        pestanas.setCurrentIndex(pestana)
        APP.processEvents()
        for nombre in nombres:
            boton = getattr(w, nombre)
            bajo = _bajo_el_mouse(win, boton)
            assert bajo is boton or boton.isAncestorOf(bajo), \
                f"{nombre}: el clic lo recibe {type(bajo).__name__}"
    marco.close()


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
