"""El paciente de la rinomanometría, de frente: la máscara oronasal con el
neumotacógrafo y el adaptador con el tubo de presión en una narina.

Es la cara de la rinoscopía (resources/rinoscopia, cuadro recto,
nasal/RinoscopiaWindow.cara()), recortada de los ojos al mentón, con la
máscara y el adaptador dibujados encima. Lo que el alumno puede ver lo ve
aquí, sin carteles: la boca abierta se ve por la máscara transparente, la
máscara mal puesta queda chueca y el adaptador sin sellar asoma fuera de la
narina. La máscara se empaña al espirar.

Un clic en una narina pide poner ahí el adaptador (`narina`); quien decide
si se puede es la ventana del equipo.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

from nasal.RinoscopiaWindow import cara

# Lo que se muestra del cuadro de 600 px: de los ojos al mentón.
RECORTE = QRectF(165, 190, 270, 270)
# La máscara en px del cuadro: del dorso de la nariz a bajo el labio.
CONTORNO_MASCARA = [(300, 258), (334, 278), (356, 330), (362, 385), (344, 424), (300, 438),
                    (256, 424), (238, 385), (244, 330), (266, 278)]
CONECTOR = (300, 414)        # el neumotacógrafo, hacia el que mira
BOCA = (300, 373)
RADIO_NARINA = 11            # px del cuadro: dónde cuenta el clic
CHUECA_GRADOS = 9            # la máscara con fuga
ESPUMA = '#EDE3BF'
TUBO = '#6E9CC2'
COJIN = QColor(132, 160, 178, 225)


def _suave(puntos):
    """Contorno cerrado y suave por los puntos (Catmull-Rom a Bézier)."""
    n = len(puntos)
    camino = QPainterPath(QPointF(*puntos[0]))
    for i in range(n):
        p0, p1, p2, p3 = (QPointF(*puntos[(i + j) % n]) for j in (-1, 0, 1, 2))
        camino.cubicTo(p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6, p2)
    camino.closeSubpath()
    return camino


class PacienteRM(QWidget):
    narina = Signal(str)        # clic en la narina 'D' o 'I'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.activo = False
        self.sonda = None       # narina con el adaptador: 'D', 'I' o None
        self.mascara = False
        self.boca = False       # respira por la boca
        self.fuga = False       # máscara mal puesta
        self.suelto = False     # adaptador sin sellar
        self.empanado = 0.0     # 0-1, cuánto vaho hay en la máscara
        self._foto = None
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMouseTracking(True)

    def heightForWidth(self, ancho):
        return ancho

    def hasHeightForWidth(self):
        return True

    def sizeHint(self):
        return self.minimumSize()

    def _pixmap(self):
        if self._foto is None:
            d = cara()
            ini, largo = d['indice']['0']
            self._foto = QPixmap.fromImage(QImage.fromData(d['bin'][ini:ini + largo], 'WEBP'))
        return self._foto

    def _escala(self):
        lado = min(self.width(), self.height())
        k = lado / RECORTE.width()
        x0 = (self.width() - lado) / 2 - RECORTE.x() * k
        y0 = (self.height() - lado) / 2 - RECORTE.y() * k
        return x0, y0, k

    def _a_pantalla(self, x, y):
        x0, y0, k = self._escala()
        return QPointF(x0 + x * k, y0 + y * k)

    def _narinas(self):
        fila = cara()['cuadros']['0']
        return {l: fila[l] for l in ('D', 'I')}

    def _narina_en(self, pos):
        x0, y0, k = self._escala()
        x, y = (pos.x() - x0) / k, (pos.y() - y0) / k
        for lado, (nx, ny) in self._narinas().items():
            if (x - nx) ** 2 + (y - ny) ** 2 <= RADIO_NARINA ** 2:
                return lado
        return None

    def mouseMoveEvent(self, evento):
        sobre = self.activo and self._narina_en(evento.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if sobre else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(evento)

    def mousePressEvent(self, evento):
        lado = self._narina_en(evento.position()) if self.activo else None
        if lado and evento.button() == Qt.MouseButton.LeftButton:
            self.narina.emit(lado)
        super().mousePressEvent(evento)

    # --- Dibujo ---------------------------------------------------------

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor('#FFFFFF'))
        x0, y0, k = self._escala()
        lado = RECORTE.width() * k
        destino = QRectF((self.width() - lado) / 2, (self.height() - lado) / 2, lado, lado)
        p.drawPixmap(destino, self._pixmap(), RECORTE)
        if not self.activo:
            p.fillRect(destino, QColor(255, 255, 255, 150))
            p.end()
            return
        p.save()
        p.translate(x0, y0)
        p.scale(k, k)
        if self.boca:
            self._pintar_boca(p)
        if self.sonda:
            self._pintar_adaptador(p)
        if self.mascara:
            self._pintar_mascara(p)
        p.restore()
        p.end()

    def _pintar_boca(self, p):
        x, y = BOCA
        p.setPen(QPen(QColor(150, 84, 84), 3))
        p.setBrush(QColor(46, 20, 24, 240))
        p.drawEllipse(QPointF(x, y + 3), 21, 11)
        # Los dientes de arriba asoman.
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(236, 230, 214))
        p.drawRoundedRect(QRectF(x - 11, y - 7, 22, 5), 2, 2)

    def _pintar_adaptador(self, p):
        nx, ny = self._narinas()[self.sonda]
        hacia = -1 if self.sonda == 'D' else 1          # D queda a la izquierda de la imagen
        # El tubo baja por el costado de la máscara y sale del cuadro.
        tubo = QPainterPath(QPointF(nx, ny + 6))
        tubo.cubicTo(nx + hacia * 4, ny + 40, nx + hacia * 52, ny + 60, nx + hacia * 70, ny + 140)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(TUBO).darker(130), 4.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(tubo)
        p.setPen(QPen(QColor(TUBO).lighter(125), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(tubo)
        # La oliva de espuma: metida en la narina, o asomando si no sella.
        dy, alto = (5, 8) if self.suelto else (1, 10)
        p.setPen(QPen(QColor(ESPUMA).darker(135), 1.2))
        p.setBrush(QColor(ESPUMA))
        p.drawEllipse(QPointF(nx + hacia * (1.5 if self.suelto else 0), ny + dy), 7.5, alto / 2)

    def _pintar_mascara(self, p):
        p.save()
        if self.fuga:
            p.translate(300, 300)
            p.rotate(CHUECA_GRADOS)
            p.translate(-300 + 7, -300 - 4)
        forma = _suave(CONTORNO_MASCARA)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(228, 240, 246, 45 + int(85 * self.empanado)))
        p.drawPath(forma)
        # El cojín que apoya en la cara.
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(COJIN, 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(forma)
        p.setPen(QPen(QColor(255, 255, 255, 140), 1.4))
        p.drawPath(forma)
        # El neumotacógrafo, de frente: un tubo que viene hacia el que mira.
        cx, cy = CONECTOR
        p.setPen(QPen(QColor('#7D838C'), 2))
        p.setBrush(QColor(196, 202, 210, 235))
        p.drawEllipse(QPointF(cx, cy), 15, 15)
        p.setBrush(QColor(92, 98, 108, 235))
        p.drawEllipse(QPointF(cx, cy), 9, 9)
        p.setPen(QPen(QColor(220, 225, 230), 1))
        for dx in (-5, 0, 5):            # la malla del neumotacógrafo
            p.drawLine(QPointF(cx + dx, cy - 7), QPointF(cx + dx, cy + 7))
        p.restore()
