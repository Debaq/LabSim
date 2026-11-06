"""El controlador leído directo del dispositivo (core/controlador_directo.py).

1. Los eventos de /dev/input se traducen a Qt.Key: apretar, soltar,
   repetición; lo que no es tecla o no se conoce se ignora.
2. Con el foco en un campo de texto de otra ventana ACTIVA (el caso que
   dejaba la consola sin efecto), las teclas del controlador igual mueven el
   audiómetro y el Z a la vista, y no se escriben en el campo.
3. Con el equipo cerrado no hace nada; el estímulo sigue apretar y soltar.
Un pipe hace de dispositivo (agregar_fd): sin permisos ni hardware.
"""
import os
import struct
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QMdiArea  # noqa: E402

from audiometria.ventana import AudiometriaWindow  # noqa: E402
from core import controlador_directo as CD  # noqa: E402
from impedanciometria.ventana import ImpedanciometriaWindow  # noqa: E402

KEY = {"S": 31, "W": 17, "V": 47, "1": 2}


def ev(codigo, valor, tipo=CD.EV_KEY):
    return struct.pack("llHHi", 0, 0, tipo, codigo, valor)


def _vueltas(n=6):
    for _ in range(n):
        QApplication.processEvents()


# --- 1 -----------------------------------------------------------------------

def test_decodificar():
    datos = ev(31, 1) + ev(0, 0, tipo=0) + ev(31, 2) + ev(31, 0) + ev(999, 1) + ev(47, 1)[:10]
    assert CD.decodificar(datos) == [(int(Qt.Key.Key_S), True, False),
                                     (int(Qt.Key.Key_S), True, True),
                                     (int(Qt.Key.Key_S), False, False)]
    assert CD.QT_DE_LINUX[2] == int(Qt.Key.Key_1) and CD.QT_DE_LINUX[11] == int(Qt.Key.Key_0)
    assert CD.QT_DE_LINUX[47] == int(Qt.Key.Key_V) and CD.QT_DE_LINUX[37] == int(Qt.Key.Key_K)


# --- 2 -----------------------------------------------------------------------

def _escena(equipo):
    """La ficha activa con su campo enfocado y el equipo abierto de fondo."""
    main = QMainWindow()
    mdi = QMdiArea()
    main.setCentralWidget(mdi)
    main.resize(1366, 768)
    sub_eq = mdi.addSubWindow(equipo)
    ficha = QLineEdit()
    sub_ficha = mdi.addSubWindow(ficha)
    main.show()
    sub_eq.show()
    sub_ficha.show()
    _vueltas()
    mdi.setActiveSubWindow(sub_ficha)
    ficha.setFocus()
    _vueltas()
    assert mdi.activeSubWindow() is sub_ficha and QApplication.focusWidget() is ficha
    return main, ficha, sub_eq


def _pipe():
    lee, escribe = os.pipe()
    os.set_blocking(lee, False)
    CD.controlador().agregar_fd(lee, "prueba")
    return lee, escribe


def _cerrar(lee, escribe):
    CD.controlador()._soltar(lee)
    os.close(escribe)


def test_audiometro_responde_con_el_foco_en_la_ficha():
    v = AudiometriaWindow(None)
    main, ficha, _sub = _escena(v)
    lee, escribe = _pipe()
    a = v.audiometro
    antes = a.dial_ch0.value()
    os.write(escribe, ev(KEY["S"], 1) + ev(KEY["S"], 0))   # encoder: subir canal 1
    _vueltas()
    assert a.dial_ch0.value() > antes, (antes, a.dial_ch0.value())
    # El estímulo sigue la tecla apretada y soltada.
    eventos = []
    a.btn_stims[0].pressed.connect(lambda: eventos.append("press"))
    a.btn_stims[0].released.connect(lambda: eventos.append("release"))
    os.write(escribe, ev(KEY["V"], 1) + ev(KEY["V"], 2) + ev(KEY["V"], 0))
    _vueltas()
    assert eventos == ["press", "release"], eventos
    assert ficha.text() == ""
    _cerrar(lee, escribe)
    main.close()


def test_z_responde_con_el_foco_en_la_ficha():
    v = ImpedanciometriaWindow()
    main, ficha, _sub = _escena(v)
    lee, escribe = _pipe()
    antes = v.z.dial.value()
    os.write(escribe, ev(KEY["S"], 1) + ev(KEY["S"], 0))   # con el controlador S sube
    _vueltas()
    assert v.z.dial.value() > antes, (antes, v.z.dial.value())
    assert ficha.text() == ""
    _cerrar(lee, escribe)
    main.close()


# --- 3 -----------------------------------------------------------------------

def test_con_el_equipo_cerrado_no_hace_nada():
    v = AudiometriaWindow(None)
    main, _ficha, sub = _escena(v)
    sub.hide()
    _vueltas()
    lee, escribe = _pipe()
    antes = v.audiometro.dial_ch0.value()
    os.write(escribe, ev(KEY["S"], 1) + ev(KEY["S"], 0))
    _vueltas()
    assert v.audiometro.dial_ch0.value() == antes
    _cerrar(lee, escribe)
    main.close()


def test_sin_dispositivo_no_esta_activo():
    c = CD.ControladorDirecto()
    assert not c.activo()
    c.cerrar()


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
