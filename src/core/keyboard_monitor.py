"""Detección de conexión/desconexión del keyboard LabSim (STM32) por USB.

El firmware (firmware/labsim_keyboard) usa el core USB HID default de
Arduino_Core_STM32 sin VID/PID propio, así que se identifica por el ID de
fábrica de ST (0483:5740, demo Virtual COM Port). Con varias unidades en
uso no se filtra por número de serie: cualquier dispositivo con ese
VID:PID cuenta como "el keyboard LabSim" conectado.
"""

import pyudev
from PySide6.QtCore import QObject, Signal

LABSIM_KEYBOARD_VID = "0483"
LABSIM_KEYBOARD_PID = "5740"


class KeyboardMonitor(QObject):

    connection_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._context = pyudev.Context()
        self._connected = False
        self._serial = None
        monitor = pyudev.Monitor.from_netlink(self._context)
        monitor.filter_by(subsystem="usb", device_type="usb_device")
        self._observer = pyudev.MonitorObserver(monitor, callback=self._on_udev_event)

    def start(self):
        self._connected = self._scan_present()
        self._observer.start()
        return self._connected

    def stop(self):
        self._observer.stop()

    def is_connected(self):
        return self._connected

    def serial(self):
        return self._serial

    def _scan_present(self):
        for device in self._context.list_devices(subsystem="usb", DEVTYPE="usb_device"):
            if self._matches(device):
                self._serial = self._read_serial(device)
                return True
        return False

    def _on_udev_event(self, device):
        if not self._matches(device):
            return
        if device.action == "add":
            self._serial = self._read_serial(device)
            self._set_connected(True)
        elif device.action == "remove":
            self._serial = None
            self._set_connected(False)

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
