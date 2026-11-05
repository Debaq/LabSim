"""Mouse para zurdos dentro de LabSim.

Intercambia los botones izquierdo y derecho solo en esta app. Lo normal es
hacerlo en el sistema operativo, pero en los computadores del laboratorio
la cuenta es compartida y el siguiente alumno lo encontraría al revés. Por
eso es una preferencia del alumno (viaja con su perfil, ver
core/preferencias.py) y se aplica SOLO en modo laboratorio
(LABSIM_KIOSKO=1, ver core/kiosko.py): en su propio computador lo tiene en
el sistema, y si LabSim lo invirtiera otra vez quedaría al derecho.

Cómo: un filtro en cada ventana NATIVA (QWindow) de la app recibe el evento
de mouse del sistema antes de que Qt lo reparta a los widgets, lo descarta
y le manda a la misma ventana uno igual con los botones intercambiados. Qt
lo reparte como si fuera el original, menú contextual incluido (lo genera
del botón derecho ya invertido).

No va en QApplication (2026-11-05): ahí cada evento de cada objeto de la
app pasaba por Python, también los de objetos a medio destruir, el mismo
mal que tumbaba el MDI (tickets 35, 36, 43). Las ventanas nativas son pocas
y duran; a las que aparecen después (diálogos, menús, la lista de un
combo) se les pone el filtro al aparecer (ver _cubrir).
"""

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


def aplicar():
    """Instala o saca el filtro según el modo laboratorio y la preferencia
    del alumno logueado."""
    global _filtro
    app = QApplication.instance()
    activo = es_kiosko() and preferencias().mouse_zurdo()
    if activo and _filtro is None:
        _filtro = InvertirBotones(app)
        _filtro.empezar()
    elif not activo and _filtro is not None:
        _filtro.terminar()
        _filtro.deleteLater()
        _filtro = None


def activo():
    return _filtro is not None


def conectar():
    """Se llama una vez al arrancar: sigue a la preferencia del alumno."""
    preferencias().cambiaron.connect(aplicar)
    aplicar()
