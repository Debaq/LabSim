"""Probe check widget - chequeo de ajuste de sonda en el conducto.

Muestra lo mismo que la pantalla de "stimulus / probe fit" de un equipo
TEOAE real: el click de estímulo tal como lo recoge el micrófono de la sonda
dentro del conducto (eje en ms, un click cada 20 ms = 50 clicks/s), el nivel
que alcanza en dB peSPL y una barra de calidad de sello que se va estabilizando
mientras el operador acomoda la sonda. 100% sintético, no requiere hardware.
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from oae.widgets.plot_style import style_plot


class ProbeCheckWidget(QWidget):
    """Click de estímulo en el conducto + nivel + calidad de sello."""

    WINDOW_MS = 25.0          # ventana visible del "osciloscopio"
    CLICK_PERIOD_MS = 20.0    # 50 clicks/s, tasa típica de TEOAE
    RING_FREQ_HZ = 2200.0     # resonancia del conducto+sonda
    RING_DECAY_MS = 0.9
    N_POINTS = 600
    TICK_MS = 50
    SCROLL_MS = 1.6           # avance del trazo por tick

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("Chequeo de sonda (probe fit)"))
        self.plot = pg.PlotWidget()
        self.plot.setBackground((255, 255, 255))
        self.plot.setYRange(-1.15, 1.15)
        self.plot.setXRange(0, self.WINDOW_MS)
        self.plot.setLabel("bottom", "Tiempo", units="ms")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        self.plot.getPlotItem().hideAxis("left")
        style_plot(self.plot.getPlotItem(), grid_alpha=0.3)
        self.curve = self.plot.plot(pen=pg.mkPen((41, 128, 185), width=2))
        layout.addWidget(self.plot)
        self.level_label = QLabel("Estímulo: --")
        layout.addWidget(self.level_label)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setValue(0)
        self.level.setFormat("Sello %p%")
        layout.addWidget(self.level)
        self.status_label = QLabel("Sonda: sin chequear")
        layout.addWidget(self.status_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.t_ms = np.linspace(0.0, self.WINDOW_MS, self.N_POINTS)
        self.offset_ms = 0.0
        self.fit_quality = 0.3
        self.target_fit = 0.85
        self.level_db = 60.0
        self._running = False
        self._rng = np.random.default_rng()

    def start(self, level_db: float = 60.0, fit_target: float | None = None):
        """`fit_target` (0-1) es el sello que el docente configuró para ese
        oído en el caso (EOAS['sello_pct']). Sin caso configurado se sortea
        un sello bueno, como antes."""
        if self._running:
            return
        self.level_db = float(level_db)
        if fit_target is None:
            self.target_fit = float(self._rng.uniform(0.72, 0.95))
        else:
            # Variación chica alrededor del objetivo: dos inserciones del
            # mismo paciente no dan el mismo sello exacto.
            self.target_fit = float(np.clip(
                self._rng.normal(float(fit_target), 0.03), 0.05, 1.0))
        # El sello arranca flojo y se acomoda: el alumno ve el trazo crecer y
        # estabilizarse, que es lo que pasa al insertar la sonda de verdad.
        self.fit_quality = float(min(self._rng.uniform(0.2, 0.4),
                                     self.target_fit))
        self.timer.start(self.TICK_MS)
        self._running = True

    def stop(self):
        if self._running:
            self.timer.stop()
            self._running = False
        # Sin captura corriendo no hay señal que mostrar -- si no, queda
        # pegado en lo último que pintó _tick, como si la sonda siguiera
        # detectando algo.
        self.level.setValue(0)
        self.curve.clear()
        self.level_label.setText("Estímulo: --")
        self.status_label.setText("Sonda: sin chequear")

    def _click_train(self) -> np.ndarray:
        """Tren de clicks con la ringing del conducto, desplazándose en el
        tiempo (un click cada CLICK_PERIOD_MS)."""
        u = (self.t_ms + self.offset_ms) % self.CLICK_PERIOD_MS
        return np.sin(2 * np.pi * self.RING_FREQ_HZ * u * 1e-3) * np.exp(
            -u / self.RING_DECAY_MS
        )

    def _tick(self):
        self.offset_ms = (self.offset_ms + self.SCROLL_MS) % self.CLICK_PERIOD_MS
        # Convergencia al sello objetivo + micro-variación (respiración /
        # movimiento del paciente), no un random walk libre que puede terminar
        # en cualquier parte.
        self.fit_quality = float(np.clip(
            self.fit_quality
            + 0.18 * (self.target_fit - self.fit_quality)
            + self._rng.normal(0, 0.015),
            0.05, 1.0,
        ))
        noise = self._rng.normal(0, 0.02, size=self.t_ms.shape)
        self.curve.setData(self.t_ms, self._click_train() * self.fit_quality + noise)

        pct = int(round(self.fit_quality * 100))
        self.level.setValue(pct)
        # Pérdida de sello = pérdida de nivel en el conducto.
        db = self.level_db + 20 * np.log10(max(self.fit_quality, 0.05))
        self.level_label.setText(f"Estímulo: {db:.1f} dB peSPL")
        if pct < 30:
            status = "Sonda: floja / sin sello"
        elif pct < 70:
            status = "Sonda: ajuste aceptable"
        else:
            status = "Sonda: ajuste bueno"
        self.status_label.setText(status)
