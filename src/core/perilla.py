"""
Perilla de los equipos (impedanciómetro, audiómetro) con la paleta de LabSim.

Es un QDial: el valor, las señales, el teclado y el arrastre con el mouse
son los de Qt. Solo cambia el dibujo, que con el estilo del sistema era un
disco gris plano. El ángulo del indicador sale de la misma cuenta que usa
QDial para leer el mouse (QStyleHelper::angle), así que la marca queda
siempre bajo el dedo.

    Perilla()                 -> sin vuelta: arco de 300° con el recorrido
    Perilla(); setWrapping()  -> con vuelta: marcas alrededor, sin arco
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QDial

from core import tema


def _pluma(color, grosor):
    pen = QPen(QColor(color), grosor)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pen


class Perilla(QDial):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def _angulo(self):
        """Radianes, sentido matemático (0 = derecha, y hacia arriba)."""
        lo, hi = self.minimum(), self.maximum()
        if hi == lo:
            return math.pi / 2
        v = self.sliderPosition() - lo
        if self.wrapping():
            return math.pi * 3 / 2 - v * 2 * math.pi / (hi - lo)
        return (math.pi * 8 - v * 10 * math.pi / (hi - lo)) / 6

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        lado = min(self.width(), self.height())
        c = QPointF(self.width() / 2, self.height() / 2)
        r_pista = lado / 2 - 3
        r_cuerpo = r_pista * 0.74
        activo = self.isEnabled()
        acento = QColor(tema.ACENTO if activo else tema.TRAZO_INACTIVO)

        pista = QRectF(c.x() - r_pista, c.y() - r_pista, 2 * r_pista, 2 * r_pista)
        grosor = max(2.5, lado / 26)
        if self.wrapping():
            # Con vuelta (un encoder sin fin) no hay recorrido ni posición
            # fija: marcas todas iguales, ninguna destacada.
            p.setPen(_pluma(tema.BORDE_FUERTE, 1.4))
            for i in range(24):
                a = i * math.pi / 12
                r0 = r_pista - grosor
                p.drawLine(QPointF(c.x() + r0 * math.cos(a), c.y() - r0 * math.sin(a)),
                           QPointF(c.x() + r_pista * math.cos(a), c.y() - r_pista * math.sin(a)))
        else:
            # Pista de 300° (de 240° a -60°) y lo recorrido en el acento.
            p.setPen(_pluma(tema.GRILLA_FUERTE, grosor))
            p.drawArc(pista, 240 * 16, -300 * 16)
            barrido = math.degrees(self._angulo()) - 240
            if barrido:
                p.setPen(_pluma(acento, grosor))
                p.drawArc(pista, 240 * 16, int(barrido * 16))

        # Cuerpo: blanco con un degradé suave hacia el borde.
        cuerpo = QRectF(c.x() - r_cuerpo, c.y() - r_cuerpo, 2 * r_cuerpo, 2 * r_cuerpo)
        grad = QRadialGradient(c.x() - r_cuerpo * 0.3, c.y() - r_cuerpo * 0.35, r_cuerpo * 1.4)
        grad.setColorAt(0.0, QColor(tema.TARJETA))
        grad.setColorAt(1.0, QColor(tema.FONDO))
        p.setBrush(grad)
        p.setPen(QPen(QColor(tema.BORDE_FUERTE), 1.2))
        p.drawEllipse(cuerpo)

        # Indicador: una raya desde cerca del centro hasta el borde del cuerpo.
        a = self._angulo()
        dx, dy = math.cos(a), -math.sin(a)
        p.setPen(_pluma(acento, max(2.5, lado / 30)))
        p.drawLine(QPointF(c.x() + dx * r_cuerpo * 0.35, c.y() + dy * r_cuerpo * 0.35),
                   QPointF(c.x() + dx * r_cuerpo * 0.82, c.y() + dy * r_cuerpo * 0.82))
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(tema.ACENTO_SUAVE), 2))
            p.drawEllipse(cuerpo.adjusted(-2, -2, 2, 2))
        p.end()
