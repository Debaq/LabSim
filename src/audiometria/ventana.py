"""
El audiómetro en una sola ventana a pantalla completa, con sus accesorios a
la vista: los comandos de voz a la izquierda, el equipo al centro y, a la
derecha, las listas de palabras cuando la prueba es Logoaudiometría. Antes
eran tres subventanas que se abrían con botones fuera del equipo, y los
alumnos se perdían buscándolas.

Reparto 1:3:1 en cualquier pantalla: cada lateral un quinto del ancho y el
audiómetro tres quintos, siempre al centro. El audiómetro es lo principal:
se agranda o achica entero (texto, perillas y botones, como un zoom) hasta
llenar su parte y va al medio en vertical. Estirar sus layouts solo abría
huecos entre los controles; por eso va dentro de un QGraphicsView (ver
_Escalado). Nada se pliega ni se esconde: los paneles reacomodan sus
columnas al ancho que les toca.

Cada panel sigue siendo un módulo del curso (CVOICE y W en Layout.php):
sin el permiso, su panel no aparece y su quinto queda vacío.
"""
import shiboken6
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QTransform
from PySide6.QtWidgets import (QFrame, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel,
                               QSizePolicy, QStackedLayout, QVBoxLayout, QWidget)

from audiometria.Audiometer import Audiometer, test_list
from audiometria.ListWords import ListWords
from audiometria.comandos_voz import ComandosVoz
from audiometria import no_realizable
from core import iconos, tema

LOGO = test_list[1]
# Partes del ancho: lateral, audiómetro, lateral.
PARTES = (1, 3, 1)
# Zoom del audiómetro: más chico se lee mal; más grande, en una pantalla
# enorme, ya no aporta.
ESCALA_MINIMA = 0.6
ESCALA_MAXIMA = 2.2
MARGEN = 6


class AudiometriaWindow(QWidget):

    def __init__(self, data, comandos=True, listas=True):
        super().__init__()
        tema.aplicar_estilo(self)
        self.audiometro = Audiometer(data)
        self.comandos = ComandosVoz()
        self.listas = ListWords(data)
        self.aviso_listas = _aviso_listas()
        self._con_comandos = comandos
        self._con_listas = listas
        self._logo = self.audiometro.lbl_prueba.text() == LOGO
        self.escalado = _Escalado(self.audiometro)
        # Con un bebé, en lugar del equipo va el aviso (ver no_realizable)
        self.aviso_bebe = no_realizable.AvisoNoRealizable("Audiometría no realizable")
        self._bebe_registrado = None   # caso cuyo intento ya quedó en el registro

        self.equipo = QWidget()
        raiz = QHBoxLayout(self.equipo)
        raiz.setContentsMargins(MARGEN, MARGEN, MARGEN, MARGEN)
        raiz.setSpacing(MARGEN)
        self.col_izq, izq = _columna()
        self.col_der, der = _columna()
        izq.addWidget(self.comandos)
        der.addWidget(self.listas)
        der.addWidget(self.aviso_listas)
        raiz.addWidget(self.col_izq, PARTES[0])
        raiz.addWidget(self.escalado, PARTES[1])
        raiz.addWidget(self.col_der, PARTES[2])
        self.pila = QStackedLayout(self)
        self.pila.addWidget(self.equipo)
        self.pila.addWidget(self.aviso_bebe)

        # Lo que antes conectaba main.connect_signals entre las tres ventanas.
        self.comandos.btn_checked.connect(self.audiometro.supra)
        self.audiometro.signal_speech.connect(self.listas.update_state)
        self.listas.level_changed.connect(
            lambda level: self.audiometro._on_player_level(self.listas.channel, level))
        self.audiometro.prueba_cambio.connect(self._al_cambiar_prueba)

        self._visibles()
        self._data = None
        self._revisar_edad(data)

    def la_super(self, data, appointment_id=None):
        self.audiometro.la_super(data, appointment_id)
        self.listas.la_super(data, appointment_id)
        self._revisar_edad(data)

    def _revisar_edad(self, data):
        self._data = data
        motivo = no_realizable.motivo(data, "audiometría")
        if motivo:
            self.aviso_bebe.texto.setText(motivo)
        self.pila.setCurrentWidget(self.aviso_bebe if motivo else self.equipo)
        if motivo:
            # dentro de la escena el audiómetro no se entera de que su página
            # se tapó: escondido suelta las teclas y corta el sonido
            # (Audiometer.hideEvent); _Escalado lo vuelve a mostrar
            self.audiometro.hide()
        elif self.escalado.isVisible():
            self.audiometro.show()
        if self.isVisible():
            self._registrar_bebe()

    def showEvent(self, event):
        super().showEvent(event)
        self._registrar_bebe()

    def _registrar_bebe(self):
        """Abrir el audiómetro con un bebé queda en el registro, una vez por
        caso: el docente ve que se intentó."""
        data = self._data
        if not no_realizable.es_bebe(data) or self._bebe_registrado is data:
            return
        self._bebe_registrado = data
        self.audiometro._log("audio_no_realizable", motivo="bebe",
                             edad=data.get("edad"), edad_horas=data.get("edad_horas"))

    def _al_cambiar_prueba(self, prueba):
        self._logo = prueba == LOGO
        self._visibles()

    def resizeEvent(self, event):
        # Cada lateral topado en su quinto; con el estiramiento 1:3:1 el
        # resto es del audiómetro. Tope y no ancho fijo: un ancho fijo sería
        # también un mínimo, y el MDI ya no dejaría achicar la ventana.
        util = self.width() - 4 * MARGEN
        lateral = util * PARTES[0] // sum(PARTES)
        self.col_izq.setMaximumWidth(lateral)
        self.col_der.setMaximumWidth(lateral)
        super().resizeEvent(event)

    def _visibles(self):
        self.comandos.setVisible(self._con_comandos)
        self.listas.setVisible(self._con_listas and self._logo)
        self.aviso_listas.setVisible(self._con_listas and not self._logo)


def _columna():
    """Un lateral: sin mínimo propio, para que mande el reparto 1:3:1."""
    col = QWidget()
    col.setMinimumWidth(1)
    lay = QVBoxLayout(col)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(MARGEN)
    return col, lay


class _Escalado(QGraphicsView):
    """Muestra un widget escalado entero al espacio que tiene, centrado y
    sin deformarlo. El widget sigue siendo el mismo (clics, perillas y
    teclas andan igual); solo se dibuja con zoom."""

    def __init__(self, widget):
        super().__init__()
        self._widget = widget
        self.base = widget.minimumSizeHint()
        widget.resize(self.base)
        escena = QGraphicsScene(self)
        self._proxy = escena.addWidget(widget)
        self.setScene(escena)
        self.setSceneRect(self._proxy.boundingRect())
        self.setObjectName("escalado")
        self.setStyleSheet("QGraphicsView#escalado { background: transparent; border: none; }")
        self.viewport().setAutoFillBackground(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setRenderHints(QPainter.RenderHint.Antialiasing
                            | QPainter.RenderHint.TextAntialiasing
                            | QPainter.RenderHint.SmoothPixmapTransform)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.escala = 1.0

    def sizeHint(self):
        return self.base

    def minimumSizeHint(self):
        return QSize(0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        escala = min(self.width() / self.base.width(), self.height() / self.base.height())
        self.escala = max(ESCALA_MINIMA, min(ESCALA_MAXIMA, escala))
        self.setTransform(QTransform.fromScale(self.escala, self.escala))

    # El audiómetro se muestra y se esconde con la ventana: al esconderse
    # corta el sonido y suelta sus teclas (Audiometer.hideEvent). Dentro de
    # la escena no se enteraría solo. Al cerrar la app la escena lo borra
    # antes de que la vista se esconda: de ahí el isValid.
    def showEvent(self, event):
        super().showEvent(event)
        if shiboken6.isValid(self._widget):
            self._widget.show()

    def hideEvent(self, event):
        super().hideEvent(event)
        if shiboken6.isValid(self._widget):
            self._widget.hide()


def _aviso_listas():
    """El lado derecho sin logoaudiometría: dice qué va ahí y cuándo."""
    caja = QFrame()
    caja.setProperty("card", "true")
    col = QVBoxLayout(caja)
    col.setContentsMargins(18, 18, 18, 18)
    col.setSpacing(8)
    col.addStretch(1)
    icono = QLabel()
    icono.setPixmap(iconos.pixmap("lista", tema.TEXTO_TENUE, 32))
    icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
    titulo = QLabel("Listas de palabras")
    titulo.setProperty("role", "titulo")
    titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    titulo.setWordWrap(True)
    pista = QLabel("Aparecen aquí al poner Habla en un canal del audiómetro "
                   "(Logoaudiometría).")
    pista.setProperty("role", "hint")
    pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pista.setWordWrap(True)
    for w in (icono, titulo, pista):
        col.addWidget(w)
    col.addStretch(2)
    return caja
