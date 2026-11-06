"""El controlador LabSim leído directo del dispositivo, sin pasar por el foco.

El controlador (firmware/labsim_keyboard) es un teclado USB más: manda
letras comunes (S, W, V, 1…). Por X esas teclas van al widget con foco, y
si el foco quedaba en un campo de texto (la ficha, el chat) el audiómetro
no respondía y las letras se escribían donde no iban. El alumno no tiene
por qué saber del foco (2026-11-06).

Aquí, en Linux, se abren los nodos /dev/input/event* del controlador
(VID:PID 0483:5740, ver core/keyboard_monitor.py) y se toman en exclusiva
(EVIOCGRAB): X deja de recibir sus teclas y LabSim se las entrega al equipo
que esté a la vista (audiómetro o impedanciómetro), tenga el foco quien lo
tenga. Los eventos se leen en el hilo de Qt con QSocketNotifier (sin hilos,
ver core/hilos.py).

Si no se puede abrir (falta el permiso: la regla udev del kiosko, en
archcraft-postinstall, modules/70-kiosko.sh; o no es Linux), no pasa nada:
las teclas siguen llegando por X como antes. Al salir la app (o caerse) el
sistema suelta el dispositivo solo.
"""

import errno
import os
import struct
import sys

from PySide6.QtCore import QObject, QSocketNotifier, Qt, QTimer, Signal

from core import keyboard_monitor

_ES_LINUX = sys.platform.startswith("linux")

# struct input_event en 64 bits: timeval (dos long), type, code, value.
_EVENTO = struct.Struct("llHHi")
EV_KEY = 1
# _IOW('E', 0x90, int)
EVIOCGRAB = 0x40044590

# Código de tecla de Linux (input-event-codes.h) -> Qt.Key. Solo lo que el
# firmware puede mandar: letras, números y flechas.
_FILAS = ((2, "1234567890"), (16, "QWERTYUIOP"), (30, "ASDFGHJKL"), (44, "ZXCVBNM"))
QT_DE_LINUX = {}
for _inicio, _letras in _FILAS:
    for _i, _c in enumerate(_letras):
        QT_DE_LINUX[_inicio + _i] = int(getattr(Qt.Key, f"Key_{_c}"))
QT_DE_LINUX.update({103: int(Qt.Key.Key_Up), 108: int(Qt.Key.Key_Down),
                    105: int(Qt.Key.Key_Left), 106: int(Qt.Key.Key_Right),
                    57: int(Qt.Key.Key_Space)})

# Al enchufarlo, el nodo event* aparece un poco después del aviso USB.
REINTENTOS = 10
REINTENTO_MS = 300


def decodificar(datos):
    """Bytes leídos -> [(qt_key, apretada, repetida)] de las teclas
    conocidas (value 1 = apretó, 0 = soltó, 2 = repetición del sistema)."""
    out = []
    n = len(datos) - len(datos) % _EVENTO.size
    for _s, _us, tipo, codigo, valor in _EVENTO.iter_unpack(datos[:n]):
        if tipo != EV_KEY or codigo not in QT_DE_LINUX or valor not in (0, 1, 2):
            continue
        out.append((QT_DE_LINUX[codigo], valor != 0, valor == 2))
    return out


def nodos_del_controlador():
    """Los /dev/input/event* del controlador conectado (puede traer más de
    uno: teclado y control de consumo)."""
    if not _ES_LINUX:
        return []
    try:
        import pyudev
    except ImportError:
        return []
    nodos = []
    for dev in pyudev.Context().list_devices(subsystem="input"):
        nodo = dev.device_node
        if not nodo or not os.path.basename(nodo).startswith("event"):
            continue
        usb = dev.find_parent("usb", "usb_device")
        if usb is not None and keyboard_monitor.KeyboardMonitor._matches(usb):
            nodos.append(nodo)
    return sorted(nodos)


class ControladorDirecto(QObject):
    """`tecla(qt_key, apretada, repetida)` por cada tecla del controlador
    mientras está tomado (`activo()`)."""

    tecla = Signal(int, bool, bool)
    activo_cambio = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fds = {}            # fd -> (nodo, QSocketNotifier)
        self._reintentos = 0
        self._ultimo_error = None

    def activo(self):
        return bool(self._fds)

    def nodos(self):
        return [n for n, _s in self._fds.values()]

    # -- abrir y cerrar ---------------------------------------------------

    def abrir(self):
        """Toma los nodos del controlador. True si quedó al menos uno."""
        antes = self.activo()
        abiertos = {n for n, _s in self._fds.values()}
        for nodo in nodos_del_controlador():
            if nodo in abiertos:
                continue
            try:
                fd = os.open(nodo, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
            except OSError as exc:
                self._avisar_error(f"no se puede abrir {nodo}: {exc.strerror}")
                continue
            try:
                import fcntl
                fcntl.ioctl(fd, EVIOCGRAB, 1)
            except OSError as exc:
                # Otro lo tiene tomado: leerlo igual duplicaría las teclas.
                os.close(fd)
                self._avisar_error(f"no se puede tomar {nodo}: {exc.strerror}")
                continue
            self.agregar_fd(fd, nodo)
            print(f"[controlador] leyendo directo de {nodo}")
        if self.activo() != antes:
            self.activo_cambio.emit(self.activo())
        return self.activo()

    def agregar_fd(self, fd, nodo):
        """Empieza a leer `fd` (también lo usan las pruebas, con un pipe)."""
        notif = QSocketNotifier(fd, QSocketNotifier.Type.Read, self)
        notif.activated.connect(lambda *_a, fd=fd: self._leer(fd))
        self._fds[fd] = (nodo, notif)

    def cerrar(self):
        antes = self.activo()
        for fd in list(self._fds):
            self._soltar(fd)
        if antes:
            self.activo_cambio.emit(False)

    def _soltar(self, fd):
        nodo, notif = self._fds.pop(fd, (None, None))
        if notif is not None:
            notif.setEnabled(False)
            notif.deleteLater()
        try:
            import fcntl
            fcntl.ioctl(fd, EVIOCGRAB, 0)
        except (OSError, ImportError):
            pass
        try:
            os.close(fd)
        except OSError:
            pass
        if nodo:
            print(f"[controlador] suelto {nodo}")

    def _avisar_error(self, texto):
        # Una vez por mensaje: sin permiso se reintenta a cada enchufe.
        if texto != self._ultimo_error:
            self._ultimo_error = texto
            print(f"[controlador] {texto}; sigue por el teclado normal")

    # -- leer ---------------------------------------------------------------

    def _leer(self, fd):
        datos = b""
        while True:
            try:
                trozo = os.read(fd, _EVENTO.size * 64)
            except BlockingIOError:
                break
            except OSError as exc:
                # ENODEV: se desenchufó.
                if exc.errno not in (errno.EAGAIN,):
                    self._soltar(fd)
                    if not self.activo():
                        self.activo_cambio.emit(False)
                break
            if not trozo:
                break
            datos += trozo
            if len(trozo) < _EVENTO.size * 64:
                break
        for qt_key, apretada, repetida in decodificar(datos):
            self.tecla.emit(qt_key, apretada, repetida)

    # -- enchufar y desenchufar --------------------------------------------

    def _al_cambiar_conexion(self, conectado):
        if conectado:
            self._reintentos = 0
            self._intentar()
        else:
            self.cerrar()

    def _intentar(self):
        if self.abrir() or self._reintentos >= REINTENTOS:
            return
        self._reintentos += 1
        QTimer.singleShot(REINTENTO_MS, self, self._intentar)


_compartido = None


def controlador():
    """El lector de toda la app, ya arrancado: lo comparten el audiómetro y
    el impedanciómetro. Sigue el enchufe del controlador."""
    global _compartido
    if _compartido is None:
        _compartido = ControladorDirecto()
        if _ES_LINUX:
            mon = keyboard_monitor.monitor()
            mon.connection_changed.connect(_compartido._al_cambiar_conexion)
            if mon.is_connected():
                _compartido._intentar()
    return _compartido
