"""Mouse para zurdos dentro de LabSim.

Intercambia los botones izquierdo y derecho solo en esta app. Lo normal es
hacerlo en el sistema operativo, pero en los computadores del laboratorio
la cuenta es compartida y el siguiente alumno lo encontraría al revés. Por
eso es una preferencia del alumno (viaja con su perfil, ver
core/preferencias.py) y se aplica SOLO en modo laboratorio
(LABSIM_KIOSKO=1, ver core/kiosko.py): en su propio computador lo tiene en
el sistema, y si LabSim lo invirtiera otra vez quedaría al derecho.

Cómo: un filtro en la QApplication recibe cada evento de mouse antes que
nadie, lo descarta y manda en su lugar uno igual con los botones
intercambiados. El menú contextual necesita un paso más: Qt lo genera a
partir del botón FÍSICO derecho, así que el que corresponde a ese botón se
descarta y se genera uno propio cuando el botón que "llega" es el derecho.
"""

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtGui import QContextMenuEvent, QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget

from core.kiosko import es_kiosko
from core.preferencias import preferencias

_IZQ = Qt.MouseButton.LeftButton
_DER = Qt.MouseButton.RightButton
_TIPOS = (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
          QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseMove)


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


def _tipo_que_abre_menu():
    """En Windows el menú contextual sale al SOLTAR el botón; en el resto,
    al apretarlo (igual que decide Qt)."""
    hints = QGuiApplication.styleHints()
    if hasattr(hints, "contextMenuTrigger"):
        if hints.contextMenuTrigger() == Qt.ContextMenuTrigger.Release:
            return QEvent.Type.MouseButtonRelease
        return QEvent.Type.MouseButtonPress
    import sys
    return QEvent.Type.MouseButtonRelease if sys.platform.startswith("win") \
        else QEvent.Type.MouseButtonPress


class InvertirBotones(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enviando = False
        self._menu_propio = False

    def eventFilter(self, obj, ev):
        tipo = ev.type()
        if tipo == QEvent.Type.ContextMenu:
            # El que genera Qt viene del botón físico derecho, que ahora es
            # el izquierdo: se descarta. El propio (abajo) pasa.
            return (not self._menu_propio
                    and ev.reason() == QContextMenuEvent.Reason.Mouse)
        if tipo not in _TIPOS or self._enviando:
            return False

        boton, botones = ev.button(), ev.buttons()
        nuevo_boton, nuevos_botones = _invertir(boton), _invertir_varios(botones)
        if nuevo_boton == boton and nuevos_botones == botones:
            return False  # rueda, botones laterales, movimiento sin apretar

        nuevo = QMouseEvent(tipo, ev.position(), ev.scenePosition(), ev.globalPosition(),
                            nuevo_boton, nuevos_botones, ev.modifiers(), ev.pointingDevice())
        self._enviando = True
        try:
            QCoreApplication.sendEvent(obj, nuevo)
        finally:
            self._enviando = False
        ev.setAccepted(nuevo.isAccepted())

        if (nuevo_boton == _DER and tipo == _tipo_que_abre_menu()
                and isinstance(obj, QWidget)):
            menu = QContextMenuEvent(QContextMenuEvent.Reason.Mouse,
                                     ev.position().toPoint(), ev.globalPosition().toPoint(),
                                     ev.modifiers())
            self._menu_propio = True
            try:
                QCoreApplication.sendEvent(obj, menu)
            finally:
                self._menu_propio = False
        return True


_filtro = None


def aplicar():
    """Instala o saca el filtro según el modo laboratorio y la preferencia
    del alumno logueado."""
    global _filtro
    app = QApplication.instance()
    activo = es_kiosko() and preferencias().mouse_zurdo()
    if activo and _filtro is None:
        _filtro = InvertirBotones(app)
        app.installEventFilter(_filtro)
    elif not activo and _filtro is not None:
        app.removeEventFilter(_filtro)
        _filtro.deleteLater()
        _filtro = None


def activo():
    return _filtro is not None


def conectar():
    """Se llama una vez al arrancar: sigue a la preferencia del alumno."""
    preferencias().cambiaron.connect(aplicar)
    aplicar()
