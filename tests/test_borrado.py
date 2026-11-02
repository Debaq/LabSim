"""core/borrado.py: cada deleteLater deja una línea en el registro antes."""
import contextlib
import io
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import QCoreApplication, QEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QMdiArea, QWidget  # noqa: E402

from core.borrado import borrar_luego  # noqa: E402

APP = QApplication.instance() or QApplication(sys.argv)


class _Modulo(QWidget):
    pass


class _Marco(QWidget):
    """Como FrameSubMdi: el módulo va en .obj."""
    def __init__(self):
        super().__init__()
        self.obj = _Modulo(self)


def _salida(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn()
    return buf.getvalue()


def test_anota_que_y_donde_y_borra():
    padre = QWidget()
    a, b, c = QLabel(padre), QLabel(padre), QFrame(padre)
    c.setObjectName("fila")
    texto = _salida(lambda: borrar_luego([a, None, b, c], "prueba"))
    assert texto.strip() == "borrar luego (prueba): QLabel ×2, QFrame 'fila'", texto
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert padre.children() == []


def test_subventana_dice_el_modulo():
    mdi = QMdiArea()
    sub = mdi.addSubWindow(_Marco())
    texto = _salida(lambda: borrar_luego([sub], "cerrar subventanas"))
    assert "QMdiSubWindow[_Modulo]" in texto, texto
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_nada_que_borrar_no_anota():
    assert _salida(lambda: borrar_luego([None], "vacío")) == ""


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
