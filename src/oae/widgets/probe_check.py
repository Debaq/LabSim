"""Probe check widget - chequeo de ajuste de sonda en el canal.

Análogo al vúmetro de audio_player.py: muestra forma de onda en vivo y
nivel peak para que el alumno vea si la sonda está bien puesta. 100%
sintético, no requiere hardware.
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from oae.widgets.plot_style import style_plot


class ProbeCheckWidget(QWidget):
    """Forma de onda continua + barra de nivel peak."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("Chequeo de sonda (probe fit)"))
        self.plot = pg.PlotWidget()
        self.plot.setBackground((255, 255, 255))
        self.plot.setYRange(-1.0, 1.0)
        self.plot.setXRange(0, 200)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        style_plot(self.plot.getPlotItem(), grid_alpha=0.3)
        self.curve = self.plot.plot(pen=pg.mkPen((41, 128, 185), width=2))
        layout.addWidget(self.plot)
        self.level_label = QLabel("Nivel peak:")
        layout.addWidget(self.level_label)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setValue(0)
        layout.addWidget(self.level)
        self.status_label = QLabel("Sonda: sin chequear")
        layout.addWidget(self.status_label)

        # Timer para animación (50ms tick)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.t = np.arange(200)
        self.scroll = 0
        self.fit_quality = 0.6
        self._running = False
        self._rng = np.random.default_rng()

    def start(self):
        if not self._running:
            self.timer.start(50)
            self._running = True

    def stop(self):
        if self._running:
            self.timer.stop()
            self._running = False
        # Sin captura corriendo no hay señal que mostrar -- antes quedaba
        # pegado en lo último que haya marcado _tick (o en 40% "a mano" si
        # nunca había arrancado), como si la sonda siguiera detectando algo.
        self.level.setValue(0)
        self.curve.clear()
        self.status_label.setText("Sonda: sin chequear")

    def _tick(self):
        # TEOAE se evoca con clicks (transientes), no con un tono continuo:
        # el chequeo de sonda tiene que mostrar eso -- un tren de clicks
        # cortos que pasan en el tiempo (como un osciloscopio en vivo),
        # no una onda continua modulada tipo "respiración".
        period = 40
        click_width = 14
        self.scroll = (self.scroll + 5) % period
        phase_in_period = (self.t + self.scroll) % period
        carrier = np.where(
            phase_in_period < click_width,
            np.sin(2 * np.pi * phase_in_period / 6) * np.exp(-phase_in_period / 4.5),
            0.0,
        )
        # Sello de la sonda varía lento (random walk acotado), simula
        # ajuste real en el canal en vez de un valor fijo o sinusoidal.
        self.fit_quality = float(
            np.clip(self.fit_quality + self._rng.normal(0, 0.03), 0.1, 1.0)
        )
        noise = self._rng.normal(0, 0.03, size=self.t.shape)
        y = carrier * self.fit_quality + noise
        self.curve.setData(self.t, y)
        peak_pct = int(self.fit_quality * 100)
        self.level.setValue(peak_pct)
        if peak_pct < 30:
            status = "Sonda: floja / sin sello"
        elif peak_pct < 70:
            status = "Sonda: ajuste aceptable"
        else:
            status = "Sonda: ajuste bueno"
        self.status_label.setText(status)
