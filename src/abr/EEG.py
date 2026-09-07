"""Monitor de EEG crudo (los dos canales, sin promediar).

Antes esto era un cascaron: dibujaba los ejes, el titulo y las letras R/L y
nada mas -- nadie le pasaba datos nunca. El problema pedagogico es que sin
monitor crudo la impedancia y la tierra recien se manifiestan cuando el
alumno ya promedio 2000 barridos, o sea tarde: en un equipo real el 50 Hz y
el EMG de un paciente tenso se ven ANTES de apretar promediar, y por eso se
arreglan antes.

El trazo lo genera ABR_generator.raw_eeg (mismo modelo de impedancias,
tierra y red que la curva promediada) y lo empuja AbrMainWindow por timer.
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from pyqtgraph import GraphicsLayoutWidget

# Ventana visible del monitor (s) y muestreo del display. 500 Hz alcanza
# de sobra para ver 50 Hz y EMG; el fs del promediador (41.6 kHz) aca no
# aporta nada y solo cuesta CPU.
WINDOW_S = 3.0
FS = 500.0
# Separacion entre los dos canales, en uV, y rango visible. Un EEG
# relajado (10-15 uV RMS) ocupa un tercio del carril de su canal y deja
# lugar para que un paciente tenso o un electrodo malo se salgan de
# verdad; el margen que sobra arriba y abajo es para los rotulos.
CHANNEL_OFFSET = 30.0
RANGE_UV = 90.0


class EEG(GraphicsLayoutWidget):
    def __init__(self):
        GraphicsLayoutWidget.__init__(self)
        color_background = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        self.setBackground(color_background)
        self.pw = self.addPlot(row=0, col=0)
        self.n = int(WINDOW_S * FS)
        self.x = np.linspace(0, WINDOW_S, self.n)
        self.pw.setRange(yRange=(-RANGE_UV, RANGE_UV), xRange=(0, WINDOW_S),
                         disableAutoRange=True)
        self.pw.showGrid(x=False, y=False)
        self.pw.setMouseEnabled(x=False, y=False)
        self.pw.setMenuEnabled(False)
        self.pw.hideButtons()
        ax = self.pw.getAxis('bottom')
        ay = self.pw.getAxis('left')
        ax.setStyle(showValues=False)
        ay.setStyle(showValues=False)
        ax.setPen(self.color_pen)
        ay.setPen(self.color_pen)

        self.buffers = {'R': np.zeros(self.n), 'L': np.zeros(self.n)}
        self.offsets = {'R': CHANNEL_OFFSET, 'L': -CHANNEL_OFFSET}
        self.colors = {'R': pg.mkColor(192, 57, 43), 'L': pg.mkColor(41, 128, 185)}
        self.curves = {}
        self.reject_lines = {}
        self.state_text = {}
        for canal in ('R', 'L'):
            self.curves[canal] = self.pw.plot(
                self.x, self.buffers[canal] + self.offsets[canal],
                pen=pg.mkPen(self.colors[canal], width=1))
            # Barras de rechazo de artefacto: el barrido que las toca se
            # descarta. Es la forma de mostrar por que el promedio no avanza.
            self.reject_lines[canal] = [
                self._reject_line(canal, 1), self._reject_line(canal, -1)]
            # En los bordes de arriba y de abajo, fuera del carril de cada
            # canal: el panel es muy bajo para meter texto al lado del trazo.
            arriba = canal == 'R'
            # anchor 0 = borde superior del rotulo: el de arriba cuelga
            # hacia abajo y el de abajo hacia arriba, los dos adentro.
            texto = pg.TextItem(text='', color=self.colors[canal],
                                anchor=(1, 0 if arriba else 1))
            texto.setPos(WINDOW_S * 0.99,
                         RANGE_UV * (0.92 if arriba else -0.92))
            self.pw.addItem(texto)
            self.state_text[canal] = texto
        self.title()
        self.side_text()
        self.reject_uv = 0.0

    def _reject_line(self, canal, signo):
        linea = pg.InfiniteLine(
            pos=self.offsets[canal], angle=0,
            pen=pg.mkPen(150, 150, 150, 160, width=1,
                         style=Qt.PenStyle.DashLine))
        linea.setVisible(False)
        linea.signo = signo
        self.pw.addItem(linea)
        return linea

    def title(self):
        text = pg.TextItem(text='EEG', color=(0, 0, 0), anchor=(0, 0))
        # Arriba a la izquierda, igual que el titulo del FSP, y adentro del
        # area de dibujo: pegado al borde quedaba cortado.
        text.setPos(WINDOW_S * 0.01, RANGE_UV * 0.99)
        self.pw.addItem(text)

    def side_text(self):
        for canal in ('R', 'L'):
            text = pg.TextItem(text=canal, color=self.colors[canal], anchor=(0, 0.5))
            text.setPos(0, self.offsets[canal])
            self.pw.addItem(text)

    # ------------------------------------------------------------- datos
    def set_reject(self, reject_uv):
        """Umbral de rechazo de artefacto del equipo (uV, 0 = desactivado)."""
        self.reject_uv = float(reject_uv or 0.0)
        for canal, lineas in self.reject_lines.items():
            for linea in lineas:
                if self.reject_uv:
                    linea.setPos(self.offsets[canal] + linea.signo * self.reject_uv)
                linea.setVisible(bool(self.reject_uv))

    def push(self, data):
        """Agrega el trozo nuevo de EEG y corre la ventana.

        `data` es lo que devuelve ABR_generator.raw_eeg: canal en None
        significa electrodo desconectado, y eso se dibuja como lo que es --
        una linea plana, no un EEG limpio.
        """
        for canal in ('R', 'L'):
            trozo = data.get(canal)
            if trozo is None:
                self.buffers[canal][:] = 0.0
                self.state_text[canal].setText('sin electrodo')
            else:
                trozo = np.asarray(trozo, dtype=float)
                largo = min(len(trozo), self.n)
                self.buffers[canal] = np.roll(self.buffers[canal], -largo)
                self.buffers[canal][-largo:] = trozo[-largo:]
                rms = data.get(f'rms_{canal}', float(np.std(trozo)))
                marca = ' ⚠ rechazo' if data.get(f'rejected_{canal}') else ''
                self.state_text[canal].setText(f'{rms:.0f} µV RMS{marca}')
            self.curves[canal].setData(
                self.x, self.buffers[canal] + self.offsets[canal])

    def clear_trace(self):
        for canal in ('R', 'L'):
            self.buffers[canal][:] = 0.0
            self.curves[canal].setData(self.x, self.buffers[canal] + self.offsets[canal])
            self.state_text[canal].setText('')
