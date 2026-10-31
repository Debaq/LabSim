"""
Ventana de equipo a pantalla completa con reparto 1:3:1: un lateral, el
equipo al centro y otro lateral. Cada lateral es un quinto del ancho y el
equipo tres quintos, siempre al centro. El equipo es lo principal: se
agranda o achica entero (texto, perillas y botones, como un zoom) hasta
llenar su parte y va al medio en vertical. Estirar sus layouts solo abría
huecos entre los controles; por eso va dentro de un QGraphicsView (ver
Escalado). Nada se pliega ni se esconde: los paneles reacomodan sus
columnas al ancho que les toca.

Lo usan el audiómetro (audiometria/ventana.py) y el impedanciómetro
(impedanciometria/ventana.py).
"""
import shiboken6
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QTransform
from PySide6.QtWidgets import (QFrame, QGraphicsScene, QGraphicsView, QHBoxLayout, QSizePolicy,
                               QVBoxLayout, QWidget)

# Partes del ancho: lateral, equipo, lateral.
PARTES = (1, 3, 1)
# Zoom del equipo: más chico se lee mal; más grande, en una pantalla
# enorme, ya no aporta.
ESCALA_MINIMA = 0.6
ESCALA_MAXIMA = 2.2
MARGEN = 6


class Reparto(QWidget):
    """Los tres: `col_izq` y `col_der` (QVBoxLayout en `izq` y `der`) y el
    equipo escalado al centro (`escalado`)."""

    def __init__(self, equipo):
        super().__init__()
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(MARGEN, MARGEN, MARGEN, MARGEN)
        raiz.setSpacing(MARGEN)
        self.escalado = Escalado(equipo)
        self.col_izq, self.izq = _columna()
        self.col_der, self.der = _columna()
        raiz.addWidget(self.col_izq, PARTES[0])
        raiz.addWidget(self.escalado, PARTES[1])
        raiz.addWidget(self.col_der, PARTES[2])

    def resizeEvent(self, event):
        # Cada lateral topado en su quinto; con el estiramiento 1:3:1 el
        # resto es del equipo. Tope y no ancho fijo: un ancho fijo sería
        # también un mínimo, y el MDI ya no dejaría achicar la ventana.
        util = self.width() - 4 * MARGEN
        lateral = util * PARTES[0] // sum(PARTES)
        self.col_izq.setMaximumWidth(lateral)
        self.col_der.setMaximumWidth(lateral)
        super().resizeEvent(event)


def _columna():
    """Un lateral: sin mínimo propio, para que mande el reparto 1:3:1."""
    col = QWidget()
    col.setMinimumWidth(1)
    lay = QVBoxLayout(col)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(MARGEN)
    return col, lay


class Escalado(QGraphicsView):
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

    # El equipo se muestra y se esconde con la ventana: al esconderse corta
    # el sonido (Audiometer.hideEvent, por ejemplo). Dentro de la escena no
    # se enteraría solo. Al cerrar la app la escena lo borra antes de que
    # la vista se esconda: de ahí el isValid.
    def showEvent(self, event):
        super().showEvent(event)
        if shiboken6.isValid(self._widget):
            self._widget.show()

    def hideEvent(self, event):
        super().hideEvent(event)
        if shiboken6.isValid(self._widget):
            self._widget.hide()
