"""La pieza del laboratorio de sueño vista desde la sala de control.

Dos vistas: la ventanilla (grande) y la cámara infrarroja del techo (chica, en una esquina). Un clic en la
chica las intercambia; doble clic en la grande pide verla ampliada (señal `ampliar`).

Son fotos (resources/psg_pieza, hechas con scripts/psg_pieza: MakeHuman + Blender), no 3D: para cada
pose, dormido/despierto y nivel de respiración hay un recorte de la cama sobre una base de la pieza. El
paciente respira (se funden los niveles vecinos). Por la ventanilla hay cinco puntos de vista: al mover el
mouse se pasa de uno a otro y el marco se corre más que la cama, como al mover la cabeza frente a un
vidrio; el reflejo del vidrio se corre al revés.
"""

import json
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QSizePolicy, QWidget

from core import tema
from core.base import context

TIC_MS = 50
# Ciclo respiratorio (s): dormido más lento y regular que despierto.
CICLO = {False: 4.4, True: 3.4}


class Paquete:
    """resources/psg_pieza: se lee una vez; las imágenes se decodifican al pedirlas."""
    _uno = None

    @classmethod
    def cargar(cls):
        if cls._uno is None:
            cls._uno = cls()
        return cls._uno if cls._uno.ok else None

    def __init__(self):
        self.ok = False
        self._img = {}
        try:
            with open(context.get_resource('psg_pieza/pieza.json'), encoding='utf-8') as f:
                self.info = json.load(f)
            with open(context.get_resource('psg_pieza/pieza.bin'), 'rb') as f:
                self.bin = f.read()
        except OSError:
            return
        self.ok = True
        self.respira = self.info['respira']
        self.vistas = self.info['ventanilla']['vistas']
        self.techo = self.info['techo']

    def imagen(self, ref):
        clave = tuple(ref)
        im = self._img.get(clave)
        if im is None:
            ini, largo = ref
            im = QImage.fromData(self.bin[ini:ini + largo], 'WEBP')
            self._img[clave] = im
        return im


class VistaPieza(QWidget):
    ampliar = Signal()

    def __init__(self, parent=None, grande=False):
        super().__init__(parent)
        self.P = Paquete.cargar()
        self.grande = grande
        self.pos = None
        self.despierto = False
        self.hora = ''
        self.principal = 'ventanilla'
        self.fase = 0.0
        self.u = self.u_meta = 2.0     # punto de vista de la ventanilla (0..4, 2 = centro)
        self._t = time.monotonic()
        self._cache = {}               # (grupo, ref, ancho, alto) -> QPixmap escalado
        self.setMouseTracking(True)
        self.setMinimumSize(160, 100)
        sp = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        self.timer = QTimer(self)
        self.timer.setInterval(TIC_MS)
        self.timer.timeout.connect(self._tic)
        if not grande:
            self.setToolTip('Doble clic: ampliar. Clic en la cámara chica: cambiar de vista.')

    # --- estado ---------------------------------------------------------

    def poner(self, pos, despierto, hora=''):
        if (pos, despierto, hora) != (self.pos, self.despierto, self.hora):
            self.pos, self.despierto, self.hora = pos, despierto, hora
            self.update()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return round(w * 10 / 16)

    def showEvent(self, e):
        self._t = time.monotonic()
        self.timer.start()
        super().showEvent(e)

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def _tic(self):
        ahora = time.monotonic()
        dt, self._t = min(0.2, ahora - self._t), ahora
        self.fase = (self.fase + dt / CICLO[self.despierto]) % 1.0
        self.u += (self.u_meta - self.u) * min(1.0, dt * 6)
        if self.pos is not None and self.P:
            self.update()

    # --- mouse ----------------------------------------------------------

    def _rect_chica(self, area):
        """La vista chica: sobre la ventanilla, arriba a la izquierda (la puerta y la cortina; abajo a
        la derecha tapaba la cabeza del paciente); sobre la cámara, abajo a la derecha (el piso)."""
        w = area.width() * 0.32
        if self.principal == 'ventanilla':
            return QRectF(area.left() + 6, area.top() + 6, w, w * 3 / 4)
        h = w * 10 / 16
        return QRectF(area.right() - w - 6, area.bottom() - h - 6, w, h)

    def mouseMoveEvent(self, e):
        area = self._area()
        if self.principal == 'ventanilla' and area.width() > 0:
            x = (e.position().x() - area.left()) / area.width()
            # Mover el mouse a la derecha es correrse a la derecha frente al vidrio.
            self.u_meta = max(0.0, min(4.0, 4.0 * x))
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self.u_meta = 2.0
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._rect_chica(self._area()).contains(e.position()):
            self.principal = 'techo' if self.principal == 'ventanilla' else 'ventanilla'
            self.u_meta = self.u = 2.0
            self.update()
            return
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if not self._rect_chica(self._area()).contains(e.position()):
            self.ampliar.emit()
        super().mouseDoubleClickEvent(e)

    # --- dibujo ---------------------------------------------------------

    def _area(self):
        """El rectángulo de la imagen principal (16:10 o 4:3, centrado)."""
        prop = 16 / 10 if self.principal == 'ventanilla' else 4 / 3
        w, h = self.width(), self.height()
        if w / max(1, h) > prop:
            w = h * prop
        else:
            h = w / prop
        return QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)

    def _escalada(self, ref, w, h):
        clave = (tuple(ref), w, h)
        pm = self._cache.get(clave)
        if pm is None:
            if len(self._cache) > 400:
                self._cache.clear()
            im = self.P.imagen(ref)
            pm = QPixmap.fromImage(im.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
            self._cache[clave] = pm
        return pm

    def _componer(self, grupo, tam, w, h):
        """Base + recorte del estado (con los dos niveles de respiración vecinos fundidos)."""
        img = QPixmap(w, h)
        q = QPainter(img)
        q.drawPixmap(0, 0, self._escalada(grupo['base'], w, h))
        sx, sy = w / tam[0], h / tam[1]
        x, y, rw, rh = grupo['rect']
        destino = QRectF(x * sx, y * sy, rw * sx, rh * sy)
        pw, ph = max(1, round(rw * sx)), max(1, round(rh * sy))
        nivel = (1 - math.cos(2 * math.pi * self.fase)) / 2 * (self.P.respira - 1)
        r0 = int(nivel)
        r1 = min(self.P.respira - 1, r0 + 1)
        d = int(self.despierto)
        q.drawPixmap(destino, self._escalada(grupo['cuadros'][f'{self.pos}_{d}_{r0}'], pw, ph),
                     QRectF(0, 0, pw, ph))
        if r1 != r0 and nivel - r0 > 0.02:
            q.setOpacity(nivel - r0)
            q.drawPixmap(destino, self._escalada(grupo['cuadros'][f'{self.pos}_{d}_{r1}'], pw, ph),
                         QRectF(0, 0, pw, ph))
        q.end()
        return img

    def _ventanilla(self, q, area, u):
        w, h = round(area.width()), round(area.height())
        tam = self.P.info['ventanilla']['tam']
        k0 = int(math.floor(u))
        k1 = min(len(self.P.vistas) - 1, k0 + 1)
        t = u - k0
        q.drawPixmap(area.topLeft(), self._componer(self.P.vistas[k0], tam, w, h))
        if k1 != k0 and t > 0.03:
            q.setOpacity(t)
            q.drawPixmap(area.topLeft(), self._componer(self.P.vistas[k1], tam, w, h))
            q.setOpacity(1)
        # El reflejo del vidrio, dentro del vano (se corre al revés que la vista).
        sx, sy = area.width() / tam[0], area.height() / tam[1]
        v0, v1 = self.P.vistas[k0]['vano'], self.P.vistas[k1]['vano']
        vano = QPolygonF([QPointF(area.left() + ((1 - t) * a[0] + t * b[0]) * sx,
                                  area.top() + ((1 - t) * a[1] + t * b[1]) * sy) for a, b in zip(v0, v1)])
        caja = vano.boundingRect()
        corre = (2.0 - u) * 0.08 * caja.width()
        g = QLinearGradient(caja.left() + corre, caja.top(), caja.left() + corre + caja.width() * 0.7, caja.bottom())
        for pos, alfa in ((0.0, 0), (0.18, 26), (0.24, 8), (0.42, 0), (0.55, 18), (0.6, 4), (1.0, 0)):
            g.setColorAt(pos, QColor(200, 220, 255, alfa))
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(g)
        q.drawPolygon(vano)

    def _techo(self, q, area, chica=False):
        w, h = round(area.width()), round(area.height())
        q.drawPixmap(area.topLeft(), self._componer(self.P.techo, self.P.techo['tam'], w, h))
        if chica and area.width() < 140:
            return
        f = QFont(self.font())
        f.setPixelSize(max(9, round(area.height() * 0.045)))
        f.setFamily('monospace')
        q.setFont(f)
        q.setPen(QColor(235, 245, 235, 220))
        m = area.height() * 0.03
        q.drawText(QPointF(area.left() + m * 1.5, area.top() + m + f.pixelSize()), f'CAM 1  IR  {self.hora}')
        if int(time.monotonic() * 1.2) % 2:
            q.setBrush(QColor('#e0403a'))
            q.setPen(Qt.PenStyle.NoPen)
            r = f.pixelSize() * 0.35
            q.drawEllipse(QPointF(area.right() - m * 1.5 - r, area.top() + m + f.pixelSize() * 0.6), r, r)

    def paintEvent(self, _e):
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.fillRect(self.rect(), QColor('#16181b'))
        area = self._area()
        if not self.P or self.pos is None:
            q.setPen(QColor(tema.TEXTO_SUAVE))
            q.drawText(area, Qt.AlignmentFlag.AlignCenter,
                       'Sin imagen de la pieza' if not self.P else '')
            q.end()
            return
        if self.principal == 'ventanilla':
            self._ventanilla(q, area, self.u)
        else:
            self._techo(q, area)
        chica = self._rect_chica(area)
        q.setOpacity(1)
        if self.principal == 'ventanilla':
            self._techo(q, chica, chica=True)
        else:
            self._ventanilla(q, chica, 2.0)
        q.setBrush(Qt.BrushStyle.NoBrush)
        q.setPen(QPen(QColor(255, 255, 255, 170), 1.2))
        q.drawRect(chica)
        q.end()
