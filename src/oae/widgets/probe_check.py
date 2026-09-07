"""Probe check widget - chequeo de ajuste de sonda en el canal.

Análogo al vúmetro de audio_player.py: muestra forma de onda en vivo y
nivel peak para que el alumno vea si la sonda está bien puesta. 100%
sintético, no requiere hardware.
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class ProbeCheckWidget(QWidget):
    """Forma de onda continua + barra de nivel peak."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("Chequeo de sonda (probe fit)"))
        self.plot = pg.PlotWidget()
        self.plot.setYRange(-1.0, 1.0)
        self.plot.setXRange(0, 200)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        self.curve = self.plot.plot(pen=pg.mkPen((41, 128, 185), width=2))
        layout.addWidget(self.plot)
        self.level_label = QLabel("Nivel peak:")
        layout.addWidget(self.level_label)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setValue(40)
        layout.addWidget(self.level)
        self.status_label = QLabel("Sonda: sin chequear")
        layout.addWidget(self.status_label)

        # Timer para animación (50ms tick)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.t = np.arange(200)
        self.phase = 0.0
        self._running = False

    def start(self):
        if not self._running:
            self.timer.start(50)
            self._running = True

    def stop(self):
        if self._running:
            self.timer.stop()
            self._running = False
            self.status_label.setText("Sonda: detenido")

    def _tick(self):
        self.phase += 0.25
        # Onda senoidal con modulación lenta (simula respiración/ruido ambiente)
        carrier = np.sin(self.t * 0.3 + self.phase)
        envelope = 0.55 + 0.35 * np.sin(self.phase * 0.4)
        y = carrier * envelope
        self.curve.setData(self.t, y)
        peak_pct = int(abs(envelope) * 100)
        self.level.setValue(peak_pct)
        if peak_pct < 30:
            status = "Sonda: floja / sin sello"
        elif peak_pct < 70:
            status = "Sonda: ajuste aceptable"
        else:
            status = "Sonda: ajuste bueno"
        self.status_label.setText(status)
