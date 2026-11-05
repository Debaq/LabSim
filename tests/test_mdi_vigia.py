"""core/h_win.MdiArea: el aviso de show/hide de subventanas no pasa por
QMdiArea.eventFilter y se suelta antes de que Qt destruya la subventana
(tickets 35, 36, 43 del 2026-11-05). Y core/recolector: el GC corre solo
desde el hilo de la ventana (ticket 33)."""
import gc
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import QCoreApplication, QEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QMdiArea, QMdiSubWindow, QWidget  # noqa: E402

from core.h_win import MdiArea, _VigiaSubventanas  # noqa: E402  (crea la QApplication)

APP = QApplication.instance()


def _vueltas():
    for _ in range(3):
        QCoreApplication.processEvents()


def test_no_sobrescribe_eventfilter_de_qmdiarea():
    assert MdiArea.eventFilter is QMdiArea.eventFilter


class _Espia(_VigiaSubventanas):
    def __init__(self, avisar, parent):
        super().__init__(avisar, parent)
        self.vistos = []

    def eventFilter(self, obj, event):
        self.vistos.append(event.type())
        return super().eventFilter(obj, event)


def test_avisa_al_esconder_y_se_suelta_al_borrar():
    mdi = MdiArea()
    mdi._vigia = espia = _Espia(mdi._avisar_cambio, mdi)
    mdi.resize(600, 400)
    mdi.show()
    avisos = []
    mdi.ventanas_cambiaron.connect(lambda: avisos.append(1))
    sub = QMdiSubWindow()
    sub.setWidget(QWidget())
    mdi.addSubWindow(sub)
    sub.show()
    _vueltas()
    avisos.clear()
    sub.hide()
    _vueltas()
    assert avisos, "esconder una subventana no avisó"

    espia.vistos.clear()
    sub.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _vueltas()
    # Lo último que vio el filtro fue el DeferredDelete: nada de la
    # destrucción (ChildRemoved, Leave, Destroy) pasó por Python.
    assert espia.vistos == [QEvent.Type.DeferredDelete], espia.vistos
    assert mdi.subWindowList() == []
    mdi.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_recolector_apaga_el_automatico_y_recolecta():
    from core import recolector
    estaba = gc.isenabled()
    try:
        recolector.iniciar()
        assert not gc.isenabled()
        assert recolector._timer.isActive()
        recolector._ultima_completa = 0.0
        recolector._pasada()  # completa, sin romper
    finally:
        recolector._timer.stop()
        recolector._timer = None
        if estaba:
            gc.enable()


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
