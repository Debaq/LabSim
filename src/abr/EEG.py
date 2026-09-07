"""Monitor del canal de registro (los dos lados, sin promediar).

Antes esto era un cascaron: dibujaba los ejes, el titulo y las letras R/L y
nada mas -- nadie le pasaba datos nunca. El problema pedagogico es que sin
monitor crudo la impedancia y la tierra recien se manifiestan cuando el
alumno ya promedio 2000 barridos, o sea tarde: en un equipo real el 50 Hz y
el EMG de un paciente tenso se ven ANTES de apretar promediar, y por eso se
arreglan antes.

El trazo lo genera ABR_generator.raw_eeg (mismo modelo de impedancias,
tierra, red, banda de registro y rechazo que la curva promediada) y lo
empuja AbrMainWindow por timer. Es el canal YA filtrado, que es lo que
muestra un equipo real: el EEG de banda ancha son ~12 uV RMS y cruzaria la
barra de rechazo todo el tiempo mientras el promedio avanza sin problema
-- monitor sucio con examen que registra, que es exactamente lo que no
tiene que pasar.

La escala sigue al umbral de rechazo: la barra queda siempre a la misma
altura de la pantalla, asi que "cuanto le falta al trazo para que lo
descarten" se lee de un vistazo en vez de depender de un rango fijo.
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from pyqtgraph import GraphicsLayoutWidget

from abr.ABR_generator import EEG_DISPLAY_FS

# Ventana visible del monitor (s). El muestreo sale del generador: 500 Hz
# no alcanzaba para la banda del ABR (Nyquist 250) -- el EMG que dispara el
# rechazo vive mas arriba.
WINDOW_S = 3.0
FS = EEG_DISPLAY_FS
# Carril de cada canal (uV de medio carril). Sale del umbral de rechazo:
# la barra queda siempre a REJECT_FRAC del borde, asi que "cuanto le falta
# al trazo para que lo descarten" se lee de un vistazo y dos estados del
# equipo se comparan mirando la misma escala. Un canal limpio (~2 uV RMS,
# picos de 8) ocupa un quinto del carril; uno con 8 kOhm lo desborda.
REJECT_FRAC = 0.7
DEFAULT_HALF_UV = 35.0
MIN_HALF_UV = 10.0
# Alto total en carriles: 2 son los dos canales, el resto es el margen
# donde van los rotulos.
LANE_HEADROOM = 2.5
# Cuanto del trazo tiene que ser zumbido de red para avisarlo en pantalla.
MAINS_SHARE = 0.35


class EEG(GraphicsLayoutWidget):
    def __init__(self):
        GraphicsLayoutWidget.__init__(self)
        color_background = pg.mkColor(255, 255, 255, 255)
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        self.setBackground(color_background)
        self.setAntialiasing(True)
        self.pw = self.addPlot(row=0, col=0)
        self.n = int(WINDOW_S * FS)
        self.x = np.linspace(0, WINDOW_S, self.n)
        self.reject_uv = 0.0
        self.half = DEFAULT_HALF_UV
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
        self.offsets = {'R': self.half, 'L': -self.half}
        self.colors = {'R': pg.mkColor(192, 57, 43), 'L': pg.mkColor(41, 128, 185)}
        self.curves = {}
        self.reject_lines = {}
        self.state_text = {}
        for canal in ('R', 'L'):
            # A 2 kHz de muestreo la ventana son miles de puntos: sin
            # downsampling el monitor se come la CPU dibujando pixeles
            # repetidos.
            self.curves[canal] = self.pw.plot(
                self.x, self.buffers[canal] + self.offsets[canal],
                pen=pg.mkPen(self.colors[canal], width=1),
                autoDownsample=True)
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
                                anchor=(1, 0 if arriba else 1),
                                fill=pg.mkBrush(255, 255, 255, 210))
            self.pw.addItem(texto)
            self.state_text[canal] = texto
        self.lbl_title = pg.TextItem(text='EEG', color=(0, 0, 0), anchor=(0, 0),
                                     fill=pg.mkBrush(255, 255, 255, 210))
        self.peaks = {'R': 0.0, 'L': 0.0}
        self.pw.addItem(self.lbl_title)
        self.side_labels = {}
        for canal in ('R', 'L'):
            texto = pg.TextItem(text=canal, color=self.colors[canal], anchor=(0, 0.5))
            self.pw.addItem(texto)
            self.side_labels[canal] = texto
        self._rescale()

    def _reject_line(self, canal, signo):
        linea = pg.InfiniteLine(
            pos=self.offsets[canal], angle=0,
            pen=pg.mkPen(150, 150, 150, 160, width=1,
                         style=Qt.PenStyle.DashLine))
        linea.setVisible(False)
        linea.signo = signo
        self.pw.addItem(linea)
        return linea

    # ------------------------------------------------------------ escala
    def _rescale(self):
        """Carril de cada canal a partir del umbral de rechazo del equipo."""
        if self.reject_uv:
            self.half = max(self.reject_uv / REJECT_FRAC, MIN_HALF_UV)
        else:
            self.half = DEFAULT_HALF_UV
        self.offsets = {'R': self.half, 'L': -self.half}
        # Un poco mas que los dos carriles: el margen de arriba y de abajo
        # es donde viven los rotulos, adentro del carril tapaban el trazo.
        rango = LANE_HEADROOM * self.half
        self.pw.setRange(yRange=(-rango, rango), xRange=(0, WINDOW_S),
                         disableAutoRange=True)
        self.lbl_title.setText(f'EEG  ±{self.half:.0f} µV')
        self.lbl_title.setPos(WINDOW_S * 0.01, rango * 0.99)
        for canal in ('R', 'L'):
            arriba = canal == 'R'
            self.state_text[canal].setPos(
                WINDOW_S * 0.99, rango * (0.97 if arriba else -0.97))
            self.side_labels[canal].setPos(0, self.offsets[canal])
            for linea in self.reject_lines[canal]:
                if self.reject_uv:
                    linea.setPos(self.offsets[canal] + linea.signo * self.reject_uv)
                linea.setVisible(bool(self.reject_uv))
            self.curves[canal].setData(
                self.x, self.buffers[canal] + self.offsets[canal])

    # ------------------------------------------------------------- datos
    def set_reject(self, reject_uv):
        """Umbral de rechazo de artefacto del equipo (uV, 0 = desactivado)."""
        self.reject_uv = float(reject_uv or 0.0)
        self._rescale()

    def push(self, data):
        """Agrega el trozo nuevo del canal y corre la ventana.

        `data` es lo que devuelve ABR_generator.raw_eeg: canal en None
        significa electrodo desconectado, y eso se dibuja como lo que es --
        una linea plana, no un EEG limpio.
        """
        for canal in ('R', 'L'):
            trozo = data.get(canal)
            if trozo is None:
                self.buffers[canal][:] = 0.0
                self.peaks[canal] = 0.0
                self.state_text[canal].setText('sin electrodo')
            else:
                trozo = np.asarray(trozo, dtype=float)
                largo = min(len(trozo), self.n)
                self.buffers[canal] = np.roll(self.buffers[canal], -largo)
                self.buffers[canal][-largo:] = trozo[-largo:]
                self.peaks[canal] = float(np.abs(self.buffers[canal]).max())
                rms = data.get(f'rms_{canal}', float(np.std(trozo)))
                # Rotulo corto: el panel es angosto y el titulo esta en la
                # otra punta de la misma linea.
                partes = [f'{rms:.1f} µV']
                # Distancia al rechazo en numeros: es lo que la barra no
                # puede decir cuando el trazo es chico y queda fuera de
                # escala.
                if self.reject_uv:
                    partes.append(f'pico {self.peaks[canal]:.0f}/'
                                  f'{self.reject_uv:.0f}')
                # El zumbido de red se nombra: es EL artefacto que el
                # alumno tiene que reconocer, y a esta ventana no se ve
                # como periodico.
                red = float(data.get(f'mains_{canal}') or 0.0)
                if red > MAINS_SHARE * max(rms, 1e-9):
                    partes.append('⚡50 Hz')
                if data.get(f'rejected_{canal}'):
                    tasa = data.get(f'reject_rate_{canal}') or 0.0
                    partes.append(f'⚠ rechazo {tasa * 100:.0f}%'
                                  if tasa else '⚠ rechazo')
                self.state_text[canal].setText(' · '.join(partes))
            self.curves[canal].setData(
                self.x, self.buffers[canal] + self.offsets[canal])

    def clear_trace(self):
        for canal in ('R', 'L'):
            self.buffers[canal][:] = 0.0
            self.curves[canal].setData(self.x, self.buffers[canal] + self.offsets[canal])
            self.state_text[canal].setText('')
