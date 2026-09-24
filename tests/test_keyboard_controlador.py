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


from core import atajos  # noqa: E402
from core.preferencias import preferencias  # noqa: E402


def test_con_controlador_s_sube():
    t = atajos.teclas(True)
    assert (t["a_ch1_subir"], t["a_ch1_bajar"]) == ("S", "W")
    assert (t["z_subir"], t["z_bajar"]) == ("S", "W")


def test_con_teclado_w_sube():
    t = atajos.teclas(False)
    assert (t["a_ch1_subir"], t["a_ch1_bajar"]) == ("W", "S")
    assert (t["a_ch2_subir"], t["a_ch2_bajar"]) == ("I", "K")


def test_los_atajos_del_alumno_solo_valen_sin_controlador():
    propios = {"a_ch1_subir": "Up", "a_ch1_bajar": "Down"}
    assert atajos.teclas(False, propios)["a_ch1_subir"] == "Up"
    assert atajos.teclas(True, propios)["a_ch1_subir"] == "S"   # el firmware manda


def test_atajos_repetidos_o_reservados():
    mapa = atajos.teclas(False, {"a_ch2_subir": "W", "a_freq_mas": "5"})
    errores = atajos.conflictos(mapa)
    assert any("repetida" in e for e in errores)
    assert any("«5»" in e for e in errores)
    assert atajos.conflictos(atajos.teclas(False)) == []
    # La misma tecla en módulos distintos sí vale (W en audiómetro y Z).
    assert atajos.teclas(False)["z_subir"] == atajos.teclas(False)["a_ch1_subir"]


class _Monitor:
    def __init__(self, conectado):
        self.conectado = conectado

    def is_connected(self):
        return self.conectado


def test_audiometro_cambia_al_enchufar():
    from audiometria.Audiometer import Audiometer
    from PySide6.QtWidgets import QPushButton
    a = types.SimpleNamespace(kb_monitor=_Monitor(False), btn_freq_minus=QPushButton(),
                              btn_freq_plus=QPushButton(), cycle_output=lambda c: None,
                              cycle_stim=lambda c: None, cycle_trans=lambda c: None)
    preferencias().cargar({})
    Audiometer._aplicar_atajos(a)
    assert a._dial_keys[Qt.Key_W] == (0, True) and a._dial_keys[Qt.Key_S] == (0, False)
    assert a._dial_keys[Qt.Key_I] == (1, True) and a._dial_keys[Qt.Key_K] == (1, False)
    assert a._stim_keys == {Qt.Key_V: 0, Qt.Key_B: 1}
    assert a.btn_freq_minus.shortcut() == QKeySequence("A")
    a.kb_monitor.conectado = True
    Audiometer._aplicar_atajos(a)
    assert a._dial_keys[Qt.Key_S] == (0, True) and a._dial_keys[Qt.Key_W] == (0, False)
    # Los del alumno, sin controlador.
    a.kb_monitor.conectado = False
    preferencias().cargar({"atajos": {"a_ch1_subir": "Up", "a_estimulo_ch1": "Space"}})
    Audiometer._aplicar_atajos(a)
    assert a._dial_keys[Qt.Key_Up] == (0, True)
    assert a._stim_keys[Qt.Key_Space] == 0
    preferencias().cargar({})


def test_impedanciometro_cambia_al_enchufar():
    from PySide6.QtGui import QShortcut
    from PySide6.QtWidgets import QWidget
    from impedanciometria.Z import ZControl
    w = QWidget()
    z = types.SimpleNamespace(kb_monitor=_Monitor(False), shortcut_dial_up=QShortcut(w),
                              shortcut_dial_down=QShortcut(w), shortcut_stimulus=QShortcut(w))
    preferencias().cargar({})
    ZControl._aplicar_atajos(z)
    assert z.shortcut_dial_up.key() == QKeySequence(Qt.Key_W)
    assert z.shortcut_dial_down.key() == QKeySequence(Qt.Key_S)
    z.kb_monitor.conectado = True
    ZControl._aplicar_atajos(z)
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
