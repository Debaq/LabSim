"""El dial se maneja distinto con el controlador LabSim y con el teclado.

El encoder del controlador manda 's' al girar a la derecha (subir) y 'w' a
la izquierda (bajar). En el teclado del computador lo intuitivo es lo
contrario: W arriba, S abajo. La app detecta el controlador por USB (ver
core/keyboard_monitor.py) y cambia las teclas al enchufarlo o sacarlo.
"""

import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QKeySequence  # noqa: E402

from core.base import context  # noqa: E402,F401
from core import keyboard_monitor as km  # noqa: E402


def test_con_controlador_s_sube():
    assert km.teclas_dial(True) == (Qt.Key_S, Qt.Key_W)


def test_con_teclado_w_sube():
    assert km.teclas_dial(False) == (Qt.Key_W, Qt.Key_S)


def test_audiometro_cambia_al_enchufar():
    from audiometria.Audiometer import Audiometer
    a = types.SimpleNamespace(_dial_keys={})
    Audiometer._aplicar_teclas_dial(a, False)
    assert a._dial_keys[Qt.Key_W] == (0, True) and a._dial_keys[Qt.Key_S] == (0, False)
    assert a._dial_keys[Qt.Key_I] == (1, True) and a._dial_keys[Qt.Key_K] == (1, False)
    Audiometer._aplicar_teclas_dial(a, True)
    assert a._dial_keys[Qt.Key_S] == (0, True) and a._dial_keys[Qt.Key_W] == (0, False)
    assert a._dial_keys[Qt.Key_I] == (1, True)   # el canal 2 no cambia


def test_impedanciometro_cambia_al_enchufar():
    from PySide6.QtGui import QShortcut
    from PySide6.QtWidgets import QWidget
    from impedanciometria.Z import ZControl
    w = QWidget()
    z = types.SimpleNamespace(shortcut_dial_up=QShortcut(w), shortcut_dial_down=QShortcut(w))
    ZControl._aplicar_teclas_dial(z, False)
    assert z.shortcut_dial_up.key() == QKeySequence(Qt.Key_W)
    assert z.shortcut_dial_down.key() == QKeySequence(Qt.Key_S)
    ZControl._aplicar_teclas_dial(z, True)
    assert z.shortcut_dial_up.key() == QKeySequence(Qt.Key_S)


def _windows_falso(instancias, presentes):
    """winreg + cfgmgr32 de mentira: `instancias` enchufadas alguna vez,
    `presentes` las que están ahora."""
    winreg = types.ModuleType("winreg")
    winreg.HKEY_LOCAL_MACHINE = 0

    def open_key(_raiz, ruta):
        if instancias is None:
            raise OSError("no existe")
        assert ruta.endswith(r"USB\VID_0483&PID_5740")
        return "clave"

    def enum_key(_clave, i):
        if i >= len(instancias):
            raise OSError("fin")
        return instancias[i]

    winreg.OpenKey, winreg.EnumKey, winreg.CloseKey = open_key, enum_key, lambda _c: None

    class Cfg:
        def CM_Locate_DevNodeW(self, _p, device_id, _flags):
            return 0 if device_id.value.rsplit("\\", 1)[1] in presentes else 13

    import ctypes
    sys.modules["winreg"] = winreg
    ctypes.WinDLL = lambda nombre: Cfg()


def test_windows_detecta_el_que_esta_enchufado():
    _windows_falso(["ABC", "XYZ"], {"XYZ"})
    assert km._presente_en_windows()


def test_windows_uno_que_se_enchufo_antes_no_cuenta():
    _windows_falso(["ABC"], set())
    assert not km._presente_en_windows()


def test_windows_nunca_enchufado():
    _windows_falso(None, set())
    assert not km._presente_en_windows()


def test_el_aviso_de_udev_llega_al_hilo_principal():
    """pyudev avisa desde otro hilo: el cambio se aplica encolado."""
    import threading
    from PySide6.QtCore import QCoreApplication
    mon = km.KeyboardMonitor.__new__(km.KeyboardMonitor)
    km.QObject.__init__(mon)
    mon._connected, mon._serial = False, None
    mon._udev_evento.connect(mon._aplicar_udev, Qt.ConnectionType.QueuedConnection)
    recibido = []
    mon.connection_changed.connect(lambda c: recibido.append((c, threading.current_thread().name)))
    hilo = threading.Thread(target=lambda: mon._udev_evento.emit("add", "S1"), name="udev")
    hilo.start()
    hilo.join()
    assert recibido == []          # todavía no: va encolado
    QCoreApplication.processEvents()
    assert recibido == [(True, threading.main_thread().name)]


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
