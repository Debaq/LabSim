"""Mouse para zurdos en LabSim.

Intercambia los botones izquierdo y derecho. Lo normal es hacerlo en el
sistema operativo, pero en los computadores del laboratorio la cuenta es
compartida y el siguiente alumno lo encontraría al revés. Por eso es una
preferencia del alumno (viaja con su perfil, ver core/preferencias.py) y se
aplica SOLO en modo laboratorio (LABSIM_KIOSKO=1, ver core/kiosko.py): en
su propio computador lo tiene en el sistema, y si LabSim lo invirtiera otra
vez quedaría al derecho.

Dos maneras, en este orden:

1. **En el servidor X** (los kioskos: X11 + Openbox, ver el repo
   archcraft-postinstall). Con Xlib (`XSetPointerMapping`, por ctypes) se
   intercambian los botones 1 y 3 del puntero: LabSim no toca ningún
   evento, el sistema ya los entrega invertidos. Se pone al entrar un
   alumno zurdo y se saca al cerrar su sesión y al salir de LabSim. Si
   LabSim se cae con el mapeo puesto, al volver a abrir lo corrige (en el
   kiosko, sin zurdo, los botones 1 y 3 invertidos solo pueden ser
   nuestros), y al reiniciar el equipo X arranca de nuevo.
2. **Sin X11** (Wayland, Windows, las pruebas): un filtro en cada ventana
   nativa (QWindow) recibe el evento de mouse antes de que Qt lo reparta,
   lo descarta y le manda a la misma ventana uno igual con los botones
   intercambiados. No va en QApplication (2026-11-05): ahí cada evento de
   cada objeto pasaba por Python, también los de objetos a medio destruir,
   el mismo mal que tumbaba el MDI (tickets 35, 36, 43).

libX11 se carga del dist (va empaquetada, ver LabSim.spec) o por su nombre,
que con Qt en xcb ya está cargada: nunca con ctypes.util.find_library, que
devolvería la del sistema y mezclaría dos versiones (build encapsulado).
"""

import ctypes
import os
import sys

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QApplication

from core.kiosko import es_kiosko
from core.preferencias import preferencias

_IZQ = Qt.MouseButton.LeftButton
_DER = Qt.MouseButton.RightButton
_TIPOS = (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
          QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseMove)
# Propiedad dinámica que marca las ventanas que ya tienen el filtro.
_MARCA = "labsim_mouse_zurdo"
# Respaldo para ventanas que aparecen sin clic ni foco (un aviso que se
# abre solo): cada cuánto se revisan.
_REVISAR_MS = 500
# XSetPointerMapping responde "ocupado" si hay un botón apretado: se
# reintenta cada tanto, un rato.
_REINTENTO_MS = 200
_REINTENTOS = 25


# --- 1. En el servidor X -----------------------------------------------------

class MapeoX11:
    """Los botones del puntero en el servidor X (Xlib por ctypes)."""

    EXITO, OCUPADO = 0, 1   # MappingSuccess, MappingBusy

    def __init__(self, lib):
        self.lib = lib

    @classmethod
    def abrir(cls):
        """El mapeo del servidor X, o None si la app no corre en X11."""
        if not sys.platform.startswith("linux"):
            return None
        app = QGuiApplication.instance()
        if app is None or QGuiApplication.platformName() != "xcb":
            return None
        lib = _cargar_libx11()
        if lib is None:
            return None
        mapeo = cls(lib)
        return mapeo if mapeo.leer() else None

    def _con_display(self, hacer):
        dpy = self.lib.XOpenDisplay(None)
        if not dpy:
            return None
        try:
            return hacer(dpy)
        finally:
            self.lib.XCloseDisplay(dpy)

    def leer(self):
        """[botón lógico de cada botón físico], o [] si no se pudo."""
        def hacer(dpy):
            buf = (ctypes.c_ubyte * 256)()
            n = self.lib.XGetPointerMapping(dpy, buf, 256)
            return list(buf[:n])
        return self._con_display(hacer) or []

    def invertido(self):
        m = self.leer()
        return len(m) >= 3 and m[0] == 3 and m[2] == 1

    def poner(self, invertir):
        """'ok', 'ocupado' (un botón apretado: reintentar) o 'error'."""
        def hacer(dpy):
            buf = (ctypes.c_ubyte * 256)()
            n = self.lib.XGetPointerMapping(dpy, buf, 256)
            if n < 3:
                return 'error'
            buf[0], buf[2] = (3, 1) if invertir else (1, 3)
            r = self.lib.XSetPointerMapping(dpy, buf, n)
            return {self.EXITO: 'ok', self.OCUPADO: 'ocupado'}.get(r, 'error')
        return self._con_display(hacer) or 'error'


def _cargar_libx11():
    candidatos = []
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidatos.append(os.path.join(base, "libX11.so.6"))
    candidatos.append("libX11.so.6")
    for nombre in candidatos:
        if os.sep in nombre and not os.path.exists(nombre):
            continue
        try:
            lib = ctypes.CDLL(nombre)
        except OSError:
            continue
        lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
        lib.XOpenDisplay.restype = ctypes.c_void_p
        lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
        lib.XCloseDisplay.restype = ctypes.c_int
        for f in (lib.XGetPointerMapping, lib.XSetPointerMapping):
            f.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
            f.restype = ctypes.c_int
        return lib
    return None


# None: sin mirar todavía; False: no hay X11; si no, el MapeoX11.
_x11 = None
# Lo último que se pidió poner en X (para activo() y los reintentos).
_x11_invertido = False


def _mapeo_x11():
    global _x11
    if _x11 is None:
        _x11 = MapeoX11.abrir() or False
    return _x11 or None


def _poner_en_x11(intento=0):
    """Deja el servidor X como pide la preferencia del alumno logueado."""
    global _x11_invertido
    x11 = _mapeo_x11()
    if x11 is None:
        return
    deseado = es_kiosko() and preferencias().mouse_zurdo()
    if x11.invertido() == deseado:
        _x11_invertido = deseado
        return
    r = x11.poner(deseado)
    if r == 'ok':
        _x11_invertido = deseado
        print(f"mouse zurdo: botones {'invertidos' if deseado else 'normales'} en X")
    elif r == 'ocupado' and intento < _REINTENTOS:
        QTimer.singleShot(_REINTENTO_MS, QCoreApplication.instance(),
                          lambda: _poner_en_x11(intento + 1))
    else:
        print(f"mouse zurdo: X no aceptó el cambio ({r})")


def _al_salir():
    """Al cerrar LabSim el mouse vuelve a lo normal para lo que siga."""
    x11 = _mapeo_x11() if es_kiosko() else None
    if x11 is not None and x11.invertido():
        x11.poner(False)


# --- 2. Sin X11: filtro en cada ventana nativa -------------------------------

def _invertir(boton):
    if boton == _IZQ:
        return _DER
    if boton == _DER:
        return _IZQ
    return boton


def _invertir_varios(botones):
    izq = bool(botones & _IZQ)
    der = bool(botones & _DER)
    resto = botones & ~(_IZQ | _DER)
    if izq:
        resto |= _DER
    if der:
        resto |= _IZQ
    return resto


class InvertirBotones(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        # Los eventos que mandó este filtro y siguen en camino. Se
        # reconocen por identidad, no con una bandera: si el clic abre un
        # diálogo modal (exec()), el reenvío no vuelve hasta cerrarlo, y con
        # una bandera puesta todos los clics del diálogo pasaban sin
        # invertir.
        self._en_camino = []
        self._revisar = QTimer(self)
        self._revisar.setInterval(_REVISAR_MS)
        self._revisar.timeout.connect(self.cubrir)

    def empezar(self):
        self.cubrir()
        QGuiApplication.instance().focusWindowChanged.connect(self.cubrir)
        self._revisar.start()

    def terminar(self):
        self._revisar.stop()
        try:
            QGuiApplication.instance().focusWindowChanged.disconnect(self.cubrir)
        except (RuntimeError, TypeError):
            pass
        for ventana in QGuiApplication.topLevelWindows():
            if ventana.property(_MARCA):
                ventana.removeEventFilter(self)
                ventana.setProperty(_MARCA, False)

    def cubrir(self, *_):
        """Pone el filtro en las ventanas nativas que todavía no lo tienen."""
        for ventana in QGuiApplication.topLevelWindows():
            if not ventana.property(_MARCA):
                ventana.installEventFilter(self)
                ventana.setProperty(_MARCA, True)

    def eventFilter(self, obj, ev):
        tipo = ev.type()
        if tipo not in _TIPOS:
            return False
        if any(ev is propio for propio in self._en_camino):
            return False

        boton, botones = ev.button(), ev.buttons()
        nuevo_boton, nuevos_botones = _invertir(boton), _invertir_varios(botones)
        if nuevo_boton == boton and nuevos_botones == botones:
            return False  # rueda, botones laterales, movimiento sin apretar

        if tipo == QEvent.Type.MouseButtonPress:
            # Un clic puede abrir un menú o la lista de un combo (ventanas
            # nativas nuevas): se cubren apenas el bucle de eventos gira,
            # también si el menú se abre con exec() dentro del reenvío.
            QTimer.singleShot(0, self, self.cubrir)

        nuevo = QMouseEvent(tipo, ev.position(), ev.scenePosition(), ev.globalPosition(),
                            nuevo_boton, nuevos_botones, ev.modifiers(), ev.pointingDevice())
        self._en_camino.append(nuevo)
        try:
            QCoreApplication.sendEvent(obj, nuevo)
        finally:
            self._en_camino = [e for e in self._en_camino if e is not nuevo]
        ev.setAccepted(nuevo.isAccepted())
        if tipo == QEvent.Type.MouseButtonPress:
            self.cubrir()
        return True


_filtro = None


def _sacar_filtro():
    global _filtro
    if _filtro is not None:
        _filtro.terminar()
        _filtro.deleteLater()
        _filtro = None


# --- Lo que usa el resto de la app -------------------------------------------

def aplicar():
    """Pone o saca la inversión según el modo laboratorio y la preferencia
    del alumno logueado."""
    global _filtro
    # Fuera del kiosko no se toca el servidor X: el mouse del computador
    # personal lo maneja su dueño (un zurdo ya lo tendría invertido ahí).
    if es_kiosko() and _mapeo_x11() is not None:
        _sacar_filtro()
        _poner_en_x11()
        return
    activo_ = es_kiosko() and preferencias().mouse_zurdo()
    if activo_ and _filtro is None:
        _filtro = InvertirBotones(QApplication.instance())
        _filtro.empezar()
    elif not activo_:
        _sacar_filtro()


def activo():
    return _filtro is not None or (_x11 not in (None, False) and _x11_invertido)


def conectar():
    """Se llama una vez al arrancar: sigue a la preferencia del alumno."""
    preferencias().cambiaron.connect(aplicar)
    app = QApplication.instance()
    if app is not None:
        app.aboutToQuit.connect(_al_salir)
    aplicar()
