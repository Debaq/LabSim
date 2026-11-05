"""core/h_win.MdiArea: el aviso de show/hide de subventanas no pasa por
ningún eventFilter en Python (tickets 35, 36, 43 del 2026-11-05), sino por
la señal visibility_changed del FrameSubMdi. Y core/recolector: el GC corre
solo desde el hilo de la ventana (ticket 33)."""
import gc
import os
import sys
import weakref

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QMdiArea, QMdiSubWindow, QWidget  # noqa: E402

from core import h_win  # noqa: E402  (core.base crea la QApplication)
from core.h_win import FrameSubMdi, MdiArea  # noqa: E402

APP = QApplication.instance()


def _vueltas():
    for _ in range(3):
        QCoreApplication.processEvents()


def _mdi():
    mdi = MdiArea()
    mdi.resize(600, 400)
    mdi.show()
    _vueltas()
    return mdi


def _sub(mdi, w=200, h=150):
    sub = QMdiSubWindow()
    sub.setWidget(FrameSubMdi(QWidget()))
    mdi.addSubWindow(sub)
    sub.resize(w, h)
    sub.show()
    _vueltas()
    return sub


def _borrar(*objs):
    for o in objs:
        o.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_ningun_eventfilter_en_python():
    assert MdiArea.eventFilter is QMdiArea.eventFilter
    assert not hasattr(h_win, "_VigiaSubventanas")


def test_avisa_al_esconder_mostrar_y_sacar():
    mdi = _mdi()
    avisos = []
    mdi.ventanas_cambiaron.connect(lambda: avisos.append(1))
    sub = _sub(mdi)
    otra = _sub(mdi)   # la activa es `otra`: esconder `sub` no la activa
    avisos.clear()
    sub.hide()
    _vueltas()
    assert avisos, "esconder una subventana no avisó"
    avisos.clear()
    sub.show()
    _vueltas()
    assert avisos, "mostrar una subventana no avisó"
    avisos.clear()
    mdi.removeSubWindow(otra)
    _vueltas()
    assert avisos, "sacar una subventana no avisó"
    _borrar(otra, sub, mdi)


def test_conecta_una_sola_vez():
    mdi = _mdi()
    sub = _sub(mdi)
    mdi.removeSubWindow(sub)
    mdi.addSubWindow(sub)
    assert sub.widget()._avisa_al_mdi
    _borrar(sub, mdi)


def test_frame_sin_ciclo_con_su_barra():
    estaba = gc.isenabled()
    gc.disable()
    try:
        frame = FrameSubMdi(QWidget())
        ref = weakref.ref(frame)
        del frame
        assert ref() is None, "FrameSubMdi quedó vivo: hay un ciclo de referencias"
    finally:
        if estaba:
            gc.enable()


def _mouse(tipo, x, y, botones):
    boton = (Qt.MouseButton.NoButton if tipo == QEvent.Type.MouseMove
             else Qt.MouseButton.LeftButton)
    p = QPointF(x, y)
    return QMouseEvent(tipo, p, p, p, boton, botones, Qt.KeyboardModifier.NoModifier)


def test_arrastre_solo_con_boton_izquierdo():
    mdi = _mdi()
    sub = _sub(mdi)
    sub.move(10, 10)
    barra = sub.widget().barra
    izq, nada = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
    barra.mousePressEvent(_mouse(QEvent.Type.MouseButtonPress, 100, 100, izq))
    barra.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, 150, 130, izq))
    assert sub.pos() == QPoint(60, 40), sub.pos()
    # Se perdió el release: moverse sin el botón izquierdo no arrastra.
    barra.mouseMoveEvent(_mouse(QEvent.Type.MouseMove, 200, 200, Qt.MouseButton.RightButton))
    assert sub.pos() == QPoint(60, 40), sub.pos()
    barra.mouseReleaseEvent(_mouse(QEvent.Type.MouseButtonRelease, 200, 200, nada))
    _borrar(sub, mdi)


def test_keep_inside_achica_y_devuelve_el_tamano():
    mdi = _mdi()
    sub = _sub(mdi, 400, 300)
    sub.setMinimumSize(400, 300)
    sub.move(150, 80)
    mdi.resize(300, 200)
    _vueltas()
    vp = mdi.viewport().size()
    assert sub.width() <= vp.width() and sub.height() <= vp.height()
    assert sub.x() >= 0 and sub.y() >= 0
    mdi.resize(800, 600)
    _vueltas()
    assert (sub.width(), sub.height()) == (400, 300)
    assert (sub.minimumWidth(), sub.minimumHeight()) == (400, 300)
    _borrar(sub, mdi)


def test_keep_inside_nunca_deja_la_barra_afuera():
    mdi = _mdi()
    sub = _sub(mdi)
    # Más grande que el viewport y sin poder achicarse (mínimo forzado
    # después): la esquina con la barra queda a la vista.
    sub.resize(900, 700)
    sub.setMinimumSize(900, 700)
    sub.move(-50, -50)
    sub.setMinimumSize(900, 700)
    mdi.keep_inside(sub)
    assert sub.x() >= 0 and sub.y() >= 0, sub.pos()
    _borrar(sub, mdi)


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
