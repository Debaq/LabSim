"""
Medidor de EMG: la mitad del examen que no se ve en la traza.

La amplitud cruda del VEMP escala con cuánto está contrayendo el paciente el
músculo del que se registra. Sin ver ese EMG, una traza plana puede ser una
respuesta ausente o un paciente que soltó la cabeza, y las dos se dibujan
igual. Este medidor muestra, en vivo:

- el EMG rectificado del momento, en µV;
- la BANDA en la que el equipo acepta los barridos (fuera de ella los tira);
- la historia reciente, para ver la fatiga: el paciente que arranca en 90 µV
  y termina en 50 no contrajo igual todo el registro, y esa es la razón por
  la que la amplitud que se informa es la corregida.

Pintado a mano y no con pyqtgraph: es un instrumento, no un gráfico de
datos, y con QPainter entra en 110 px sin ejes ni leyenda.
"""

from collections import deque

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from vemp import protocol, theme

N_HISTORIA = 90


class MedidorEmg(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.subtipo = protocol.CVEMP
        self.nivel = 0.0
        self.activo = False
        self.historia = deque([0.0] * N_HISTORIA, maxlen=N_HISTORIA)
        self.setMinimumHeight(118)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def set_subtipo(self, subtipo):
        self.subtipo = subtipo if subtipo in protocol.EMG_BANDA else protocol.CVEMP
        self.update()

    def push(self, nivel):
        self.nivel = float(nivel)
        self.historia.append(self.nivel)
        self.update()

    def set_activo(self, activo):
        self.activo = bool(activo)
        if not activo:
            self.nivel = 0.0
            self.historia = deque([0.0] * N_HISTORIA, maxlen=N_HISTORIA)
        self.update()

    @property
    def estado(self):
        return protocol.estado_emg(self.subtipo, self.nivel)

    # ------------------------------------------------------------------
    # Pintura
    # ------------------------------------------------------------------

    def paintEvent(self, _event):
        lo, hi = protocol.EMG_BANDA[self.subtipo]
        tope = hi * 1.35
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        ancho = self.width()
        alto = self.height()
        margen = 10
        util = ancho - 2 * margen

        # --- Rótulo y lectura -----------------------------------------
        p.setPen(QColor(theme.TEXTO_TENUE))
        fuente = QFont(self.font())
        fuente.setPointSizeF(7.5)
        fuente.setBold(True)
        p.setFont(fuente)
        p.drawText(margen, 14, 'EMG RECTIFICADO')

        color = self._color_estado()
        fuente.setPointSizeF(13.0)
        p.setFont(fuente)
        p.setPen(QColor(color))
        texto = '--' if not self.activo else f'{self.nivel:.0f}'
        p.drawText(QRectF(margen, 18, util, 22),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, texto)

        fuente.setPointSizeF(7.5)
        fuente.setBold(False)
        p.setFont(fuente)
        p.setPen(QColor(theme.TEXTO_SUAVE))
        p.drawText(QRectF(margen + 34, 18, util - 34, 22),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f'µV   ·   banda {lo:.0f}–{hi:.0f}')
        p.setPen(QColor(color))
        p.drawText(QRectF(margen, 18, util, 22),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   self._texto_estado())

        # --- Barra con la banda objetivo -------------------------------
        y_barra = 46
        h_barra = 16
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(theme.TARJETA_ALT)))
        p.drawRoundedRect(QRectF(margen, y_barra, util, h_barra), 4, 4)

        x_lo = margen + util * (lo / tope)
        x_hi = margen + util * (min(hi, tope) / tope)
        p.setBrush(QBrush(QColor(27, 138, 90, 38)))
        p.drawRect(QRectF(x_lo, y_barra, x_hi - x_lo, h_barra))
        p.setPen(QPen(QColor(theme.OK), 1, Qt.PenStyle.DashLine))
        p.drawLine(int(x_lo), y_barra, int(x_lo), y_barra + h_barra)
        p.drawLine(int(x_hi), y_barra, int(x_hi), y_barra + h_barra)

        if self.activo and self.nivel > 0:
            ancho_nivel = util * min(self.nivel / tope, 1.0)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(color)))
            p.drawRoundedRect(QRectF(margen, y_barra + 3, ancho_nivel, h_barra - 6), 3, 3)

        # --- Historia --------------------------------------------------
        y_top = y_barra + h_barra + 8
        h_hist = max(alto - y_top - 6, 12)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(theme.TARJETA_ALT)))
        p.drawRoundedRect(QRectF(margen, y_top, util, h_hist), 4, 4)

        # La banda también en la historia: así se ve el momento en el que la
        # contracción se cayó por debajo de lo aceptable.
        y_de = lambda v: y_top + h_hist - h_hist * min(v / tope, 1.0)
        p.setBrush(QBrush(QColor(27, 138, 90, 26)))
        p.drawRect(QRectF(margen, y_de(hi), util, y_de(lo) - y_de(hi)))

        if self.activo:
            p.setPen(QPen(QColor(theme.TEXTO_SUAVE), 1.4))
            paso = util / max(len(self.historia) - 1, 1)
            anterior = None
            for i, valor in enumerate(self.historia):
                punto = (margen + i * paso, y_de(valor))
                if anterior is not None:
                    p.drawLine(int(anterior[0]), int(anterior[1]),
                               int(punto[0]), int(punto[1]))
                anterior = punto
        p.end()

    def _color_estado(self):
        if not self.activo or self.nivel <= 0:
            return theme.TEXTO_TENUE
        return {'ok': theme.OK, 'insuficiente': theme.AVISO,
                'excesivo': theme.ALERTA}[self.estado]

    def _texto_estado(self):
        if not self.activo or self.nivel <= 0:
            return 'sin paciente'
        return {'ok': 'en banda',
                'insuficiente': 'contracción insuficiente',
                'excesivo': 'contracción excesiva'}[self.estado]
