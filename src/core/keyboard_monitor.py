"""Detección de conexión/desconexión del keyboard LabSim (STM32) por USB.

El firmware (firmware/labsim_keyboard) usa el core USB HID default de
Arduino_Core_STM32 sin VID/PID propio, así que se identifica por el ID de
fábrica de ST (0483:5740). Con varias unidades en uso no se filtra por
número de serie: cualquier dispositivo con ese VID:PID cuenta como "el
keyboard LabSim" conectado.

Para qué se usa: el mismo dial se maneja distinto con el controlador y con
el teclado del computador (ver teclas_dial). El encoder del controlador
manda 's' al girar a la derecha (subir) y 'w' a la izquierda (bajar); en
un teclado lo intuitivo es lo contrario, W arriba y S abajo, como WASD.

- Linux: pyudev, con aviso inmediato al enchufar/desenchufar.
- Windows: el registro dice qué instancias de ese VID:PID se enchufaron
  alguna vez y cfgmgr32 cuál está presente ahora; se revisa cada
  POLL_MS (sin dependencias extra).
- Otro sistema: queda "no conectado" (teclado del computador).
"""

import sys

from PySide6.QtCore import QObject, QTimer, Qt, Signal

_ES_LINUX = sys.platform.startswith("linux")
_ES_WINDOWS = sys.platform.startswith("win")
if _ES_LINUX:
    try:
        import pyudev
    except ImportError:  # instalación sin pyudev: se asume teclado del PC
        _ES_LINUX = False

LABSIM_KEYBOARD_VID = "0483"
LABSIM_KEYBOARD_PID = "5740"
POLL_MS = 2000


def teclas_dial(conectado):
    """(subir, bajar) del dial del canal 1 del audiómetro y del dial de la
    impedanciometría, según haya controlador o no."""
    if conectado:
        return Qt.Key_S, Qt.Key_W     # encoder: derecha = 's' = subir
    return Qt.Key_W, Qt.Key_S         # teclado: W arriba, S abajo


def _presente_en_windows():
    """True si hay una instancia del VID:PID enchufada ahora mismo."""
    import ctypes
    import winreg

    ruta = rf"SYSTEM\CurrentControlSet\Enum\USB\VID_{LABSIM_KEYBOARD_VID}&PID_{LABSIM_KEYBOARD_PID}"
    try:
        clave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ruta)
    except OSError:
        return False  # nunca se enchufó en este equipo
    cfgmgr = ctypes.WinDLL("cfgmgr32")
    devinst = ctypes.c_uint32()
    try:
        i = 0
        while True:
            try:
                instancia = winreg.EnumKey(clave, i)
            except OSError:
                return False
            i += 1
            device_id = f"USB\\VID_{LABSIM_KEYBOARD_VID}&PID_{LABSIM_KEYBOARD_PID}\\{instancia}"
            # CM_LOCATE_DEVNODE_NORMAL (0) solo encuentra dispositivos
            # presentes: uno que se enchufó antes y ya no está falla.
            if cfgmgr.CM_Locate_DevNodeW(ctypes.byref(devinst), ctypes.c_wchar_p(device_id), 0) == 0:
                return True
    finally:
        winreg.CloseKey(clave)


class KeyboardMonitor(QObject):

    connection_changed = Signal(bool)
    # Interna: el observador de pyudev avisa desde su propio hilo; esta
    # señal lo trae al hilo principal antes de tocar nada de la interfaz.
    _udev_evento = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._serial = None
        self._context = None
        self._observer = None
        self._timer = None
        self._iniciado = False
        if _ES_LINUX:
            self._context = pyudev.Context()
            monitor = pyudev.Monitor.from_netlink(self._context)
            monitor.filter_by(subsystem="usb", device_type="usb_device")
            self._observer = pyudev.MonitorObserver(monitor, callback=self._on_udev_event)
            self._udev_evento.connect(self._aplicar_udev, Qt.ConnectionType.QueuedConnection)
        elif _ES_WINDOWS:
            self._timer = QTimer(self)
            self._timer.setInterval(POLL_MS)
            self._timer.timeout.connect(self._poll_windows)

    def start(self):
        if self._iniciado:
            return self._connected
        self._iniciado = True
        if _ES_LINUX:
            self._connected = self._scan_present()
            self._observer.start()
        elif _ES_WINDOWS:
            self._connected = self._leer_windows()
            self._timer.start()
        return self._connected

    def stop(self):
        if self._observer:
            self._observer.stop()
        if self._timer:
            self._timer.stop()

    def is_connected(self):
        return self._connected

    def serial(self):
        return self._serial

    # -- Linux -----------------------------------------------------------

    def _scan_present(self):
        for device in self._context.list_devices(subsystem="usb", DEVTYPE="usb_device"):
            if self._matches(device):
                self._serial = self._read_serial(device)
                return True
        return False

    def _on_udev_event(self, device):
        if self._matches(device):
            self._udev_evento.emit(device.action or "", self._read_serial(device) or "")

    def _aplicar_udev(self, accion, serial):
        if accion == "add":
            self._serial = serial or None
            self._set_connected(True)
        elif accion == "remove":
            self._serial = None
            self._set_connected(False)

    # -- Windows ---------------------------------------------------------

    @staticmethod
    def _leer_windows():
        try:
            return _presente_en_windows()
        except Exception:  # noqa: BLE001 -- sin permiso de lectura, etc.
            return False

    def _poll_windows(self):
        self._set_connected(self._leer_windows())

    # --------------------------------------------------------------------

    def _set_connected(self, connected):
        if connected != self._connected:
            self._connected = connected
            self.connection_changed.emit(connected)

    @staticmethod
    def _matches(device):
        try:
            vid = device.attributes.asstring("idVendor")
            pid = device.attributes.asstring("idProduct")
        except (KeyError, UnicodeDecodeError):
            return False
        return vid == LABSIM_KEYBOARD_VID and pid == LABSIM_KEYBOARD_PID

    @staticmethod
    def _read_serial(device):
        try:
            return device.attributes.asstring("serial")
        except (KeyError, UnicodeDecodeError):
            return None


_compartido = None


def monitor():
    """El detector de toda la app, ya arrancado. Uno solo: el audiómetro y
    la impedanciometría miran el mismo controlador."""
    global _compartido
    if _compartido is None:
        _compartido = KeyboardMonitor()
        _compartido.start()
    return _compartido
