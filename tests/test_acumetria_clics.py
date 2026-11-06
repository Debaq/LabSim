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


from core.base import context  # noqa: E402  (crea la QApplication)
from core.h_win import FrameSubMdi  # noqa: E402
import audiometria.Acumetria as A  # noqa: E402

APP = context.app


def _bajo_el_mouse(win, boton):
    return win.childAt(boton.mapTo(win, boton.rect().center()))


def test_nada_tapa_los_botones_de_los_diapasones():
    from audiometria.Otoscopia import Otoscopia
    from audiometria.ventana_ot_ac import OtoscopiaAcumetriaWindow
    w = A.Acumetria(None)
    v = OtoscopiaAcumetriaWindow(Otoscopia(None), w)
    marco = FrameSubMdi(v, expand=True)
    marco.resize(1100, 650)
    marco.show()
    w.la_super({"id": 79, "edad": 24, "Rinne": {"500": {"od": "positivo"}}, "Weber": {"500": "oi"}}, 102)
    APP.processEvents()
    win = marco.window()
    controles = [w.botones_hz["500"], w.botones_hz["1000"], w.btn_golpear, w.btn_retirar, v.cabeza]
    controles += list(v.botones_herramienta.values())
    for control in controles:
        bajo = _bajo_el_mouse(win, control)
        assert bajo is control or control.isAncestorOf(bajo), \
            f"{type(control).__name__} {getattr(control, 'text', lambda: '')()}: el clic lo recibe {type(bajo).__name__}"
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
