"""El controlador físico responde apenas se abre el equipo (2026-11-06).

El audiómetro y el impedanciómetro son ventanas de fondo del MDI. Al
abrirlos con la ficha o el chat encima, la subventana no se activaba y el
foco quedaba en un campo de texto de la otra: el audiómetro no atendía las
teclas y en el Z se las comía el campo. Los alumnos no hacen clic en el
equipo para usar el controlador ni tienen por qué saber del foco.

1. Abrir el equipo con un campo de texto enfocado en otra ventana: las
   teclas del controlador mueven el dial (audiómetro y Z).
2. Un campo de texto con foco que ya no es la ventana activa no se queda
   con las teclas del audiómetro; el de la ventana activa sí (se escribe).
3. El buscador de frases no toma el foco solo, y lo suelta al elegir.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QMdiSubWindow  # noqa: E402

from audiometria.ventana import AudiometriaWindow  # noqa: E402
from core import atajos  # noqa: E402
from core.h_win import MdiArea  # noqa: E402
from core.h_win import FrameSubMdi  # noqa: E402
from core.ui_helpers import FULL_WINDOW_PROP, _flags, raise_window  # noqa: E402
from impedanciometria.ventana import ImpedanciometriaWindow  # noqa: E402


def _vueltas(n=8):
    for _ in range(n):
        QApplication.processEvents()


def _escena(equipo):
    """Ventana principal con MDI: la ficha (con un campo de texto enfocado)
    encima y el equipo de fondo, cerrado."""
    main = QMainWindow()
    mdi = MdiArea()
    main.setCentralWidget(mdi)
    main.resize(1366, 768)
    ficha = QLineEdit()
    sub_ficha = mdi.addSubWindow(ficha)
    # Como create_sub_window con size "max".
    frame = FrameSubMdi(equipo, expand=True)
    frame.barra.hide()
    sub_eq = QMdiSubWindow()
    sub_eq.setWidget(frame)
    mdi.addSubWindow(sub_eq)
    _flags(sub_eq)
    sub_eq.setProperty(FULL_WINDOW_PROP, True)
    sub_eq.hide()
    main.show()
    sub_ficha.show()
    mdi.setActiveSubWindow(sub_ficha)
    ficha.setFocus()
    _vueltas()
    assert QApplication.focusWidget() is ficha
    return main, mdi, sub_ficha, ficha, sub_eq


def _abrir(sub_eq):
    """Como main.py al tocar el botón del equipo."""
    sub_eq.show()
    raise_window(sub_eq)
    _vueltas()


def _tecla(main, accion):
    tecla = Qt.Key(atajos.qt_key(atajos.teclas(False)[accion]))
    QTest.keyClick(main.windowHandle(), tecla)
    _vueltas(3)


# --- 1 -----------------------------------------------------------------------

def test_abrir_el_audiometro_le_da_las_teclas():
    v = AudiometriaWindow(None)
    main, mdi, _sf, ficha, sub = _escena(v)
    _abrir(sub)
    assert mdi.activeSubWindow() is sub
    antes = v.audiometro.dial_ch0.value()
    _tecla(main, "a_ch1_subir")
    assert v.audiometro.dial_ch0.value() != antes
    assert ficha.text() == ""
    main.close()


def test_abrir_el_z_le_da_las_teclas():
    v = ImpedanciometriaWindow()
    main, mdi, _sf, ficha, sub = _escena(v)
    _abrir(sub)
    assert mdi.activeSubWindow() is sub
    antes = v.z.dial.value()
    _tecla(main, "z_subir")
    assert v.z.dial.value() != antes
    assert ficha.text() == ""
    main.close()


# --- 2 -----------------------------------------------------------------------

def test_campo_de_otra_ventana_no_se_queda_con_las_teclas():
    v = AudiometriaWindow(None)
    main, mdi, sub_ficha, ficha, sub = _escena(v)
    _abrir(sub)
    # El foco vuelve a quedar en la ficha, pero la ventana activa es el
    # audiómetro (p. ej. el foco se lo dio un aviso).
    ficha.setFocus()
    mdi.setActiveSubWindow(sub)
    _vueltas()
    if mdi.activeSubWindow() is sub and QApplication.focusWidget() is ficha:
        antes = v.audiometro.dial_ch0.value()
        _tecla(main, "a_ch1_subir")
        assert v.audiometro.dial_ch0.value() != antes
    # Escribiendo en la ficha (su ventana activa): las letras son de ella.
    mdi.setActiveSubWindow(sub_ficha)
    ficha.setFocus()
    _vueltas()
    antes = v.audiometro.dial_ch0.value()
    _tecla(main, "a_ch1_subir")
    assert v.audiometro.dial_ch0.value() == antes
    main.close()


# --- 3 -----------------------------------------------------------------------

def test_el_buscador_de_frases_no_toma_el_foco_solo():
    v = AudiometriaWindow(None)
    buscar = v.comandos.buscar
    assert buscar.focusPolicy() == Qt.FocusPolicy.ClickFocus
    buscar.setFocus()
    buscar.setText("mano")
    buscar.returnPressed.emit()
    assert not buscar.hasFocus()


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
