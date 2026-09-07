"""Panel TEOAE.

Izquierda: controles (nivel dB SPL, # promedios, oído OD/OI, botón Iniciar).
Derecha: GraphicsLayoutWidget 2x2 con:
  - TL: forma de onda promediada + split A/B
  - TR: espectro FFT con bandas marcadas
  - BL: barras SNR por banda + umbral 6 dB
  - BR: pass/refer + contador de bandas
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from oae.generators.teoae import TeoaeGenerator
from oae.widgets.probe_check import ProbeCheckWidget


class TeoaePanel(QWidget):
    """Tab TEOAE del módulo OAE clínico."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = TeoaeGenerator()
        self._last_result = None
        self.case_od = None
        self.case_oi = None
        self._build_ui()
        self._update_case_gate()

    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        # ---------- IZQUIERDA: controles ----------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(6, 6, 6, 6)

        # Probe check
        self.probe = ProbeCheckWidget()
        left_layout.addWidget(self.probe)

        # Parámetros
        params = QGroupBox("Parámetros")
        form = QFormLayout(params)
        self.spn_level = QDoubleSpinBox()
        self.spn_level.setRange(40.0, 90.0)
        self.spn_level.setValue(float(self.generator.normative["default_level_db_spl"]))
        self.spn_level.setSuffix(" dB SPL")
        self.spn_level.setSingleStep(1.0)
        form.addRow("Nivel click:", self.spn_level)

        self.spn_n = QSpinBox()
        self.spn_n.setRange(50, 2000)
        self.spn_n.setSingleStep(50)
        self.spn_n.setValue(int(self.generator.normative["default_n_sweeps"]))
        form.addRow("# Promedios:", self.spn_n)
        left_layout.addWidget(params)

        # Oído
        ear_box = QGroupBox("Oído")
        ear_layout = QHBoxLayout(ear_box)
        self.btn_od = QPushButton("OD")
        self.btn_oi = QPushButton("OI")
        self.btn_od.setCheckable(True)
        self.btn_oi.setCheckable(True)
        self.btn_od.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.btn_od)
        grp.addButton(self.btn_oi)
        grp.setExclusive(True)
        ear_layout.addWidget(self.btn_od)
        ear_layout.addWidget(self.btn_oi)
        left_layout.addWidget(ear_box)

        # Botones
        self.btn_start = QPushButton("Iniciar")
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setEnabled(False)
        self.btn_clear = QPushButton("Limpiar")
        btns = QHBoxLayout()
        btns.addWidget(self.btn_start)
        btns.addWidget(self.btn_stop)
        btns.addWidget(self.btn_clear)
        left_layout.addLayout(btns)

        self.lbl_status = QLabel("Listo")
        left_layout.addWidget(self.lbl_status)

        # Métricas clínicas estándar (equipo real tipo ILO/Otoport): estas
        # 3 son las que de verdad se miran para decidir si la captura es
        # válida, no solo el pass/refer por banda.
        metrics_box = QGroupBox("Métricas de captura")
        metrics_form = QFormLayout(metrics_box)
        self.lbl_repro = QLabel("--")
        metrics_form.addRow("Reproducibilidad:", self.lbl_repro)
        self.lbl_stability = QLabel("--")
        metrics_form.addRow("Estabilidad estímulo:", self.lbl_stability)
        self.lbl_response = QLabel("--")
        metrics_form.addRow("Respuesta / Ruido:", self.lbl_response)
        left_layout.addWidget(metrics_box)
        left_layout.addStretch(1)

        # ---------- DERECHA: plots 2x2 ----------
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground((255, 255, 255))

        # TL: waveform
        self.p_wave = self.glw.addPlot(row=0, col=0, title="Forma de onda promediada (A/B)")
        self.p_wave.setLabel("left", "Amplitud", units="Pa")
        self.p_wave.setLabel("bottom", "Tiempo", units="ms")
        self.p_wave.showGrid(x=True, y=True, alpha=0.3)
        self.p_wave.setMouseEnabled(x=False, y=False)
        self.curve_a = self.p_wave.plot(pen=pg.mkPen((192, 57, 43), width=2), name="A")
        self.curve_b = self.p_wave.plot(pen=pg.mkPen((41, 128, 185), width=2, style=Qt.DashLine), name="B")

        # TR: spectrum
        self.p_spec = self.glw.addPlot(row=0, col=1, title="Espectro FFT")
        self.p_spec.setLabel("left", "Nivel", units="dB SPL")
        self.p_spec.setLabel("bottom", "Frecuencia", units="Hz")
        self.p_spec.showGrid(x=True, y=True, alpha=0.3)
        self.p_spec.setMouseEnabled(x=False, y=False)
        self.p_spec.setLogMode(x=True, y=False)
        self.curve_spec = self.p_spec.plot(pen=pg.mkPen((0, 0, 0), width=1), name="spec")
        self.bands_regions = []

        # BL: SNR por banda
        self.p_snr = self.glw.addPlot(row=1, col=0, title="SNR por banda (umbral 6 dB)")
        self.p_snr.setLabel("left", "SNR", units="dB")
        self.p_snr.setLabel("bottom", "Frecuencia", units="Hz")
        self.p_snr.showGrid(x=True, y=True, alpha=0.3)
        self.p_snr.setMouseEnabled(x=False, y=False)
        self.p_snr.setLogMode(x=True, y=False)
        self.bars_snr = pg.BarGraphItem(x=[], height=[], width=0.15, brush=(41, 128, 185))
        self.p_snr.addItem(self.bars_snr)
        self.threshold_line = pg.InfiniteLine(
            pos=self.generator.normative["min_snr_db"],
            angle=0,
            pen=pg.mkPen((192, 57, 43), width=2, style=Qt.DashLine),
            label="umbral",
            labelOpts={"position": 0.05, "color": (192, 57, 43)},
        )
        self.p_snr.addItem(self.threshold_line)

        # BR: pass/refer
        self.p_result = self.glw.addPlot(row=1, col=1, title="Resultado")
        self.p_result.hideAxis("left")
        self.p_result.hideAxis("bottom")
        self.p_result.setMouseEnabled(x=False, y=False)
        self.text_pass = pg.TextItem(anchor=(0.5, 0.5), color=(0, 0, 0))
        font = QFont()
        font.setPixelSize(22)
        font.setBold(True)
        self.text_pass.setFont(font)
        self.p_result.addItem(self.text_pass)
        self.text_pass.setPos(0.5, 0.7)
        self.text_detail = pg.TextItem(anchor=(0.5, 0.5), color=(80, 80, 80))
        font2 = QFont()
        font2.setPixelSize(11)
        self.text_detail.setFont(font2)
        self.p_result.addItem(self.text_detail)
        self.text_detail.setPos(0.5, 0.3)
        self.p_result.setXRange(0, 1)
        self.p_result.setYRange(0, 1)

        splitter.addWidget(left)
        splitter.addWidget(self.glw)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 800])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(splitter)

        # Conexiones
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_od.toggled.connect(self._update_case_gate)
        self.btn_oi.toggled.connect(self._update_case_gate)

    def set_case(self, case_od, case_oi):
        """Recibe la patología por oído del caso activo (o None si no hay
        atención abierta / no está configurado EOA para ese oído)."""
        self.case_od = case_od
        self.case_oi = case_oi
        self._update_case_gate()

    def _current_case(self):
        ear = "OD" if self.btn_od.isChecked() else "OI"
        return ear, (self.case_od if ear == "OD" else self.case_oi)

    def _update_case_gate(self):
        ear, case = self._current_case()
        self.btn_start.setEnabled(case is not None)
        if case is None:
            self.lbl_status.setText(f"Sin atención abierta o EOA no configurado para {ear}.")

    def _on_start(self):
        ear, case = self._current_case()
        if case is None:
            return
        level = self.spn_level.value()
        n = self.spn_n.value()
        self.lbl_status.setText(f"Capturando: {ear}, {level:.0f} dB SPL, {n} promedios...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.probe.start()
        # Captura síncrona (sintético, sin audio device)
        result = self.generator.generate(level_db=level, n_sweeps=n, ear=ear, case=case)
        self._last_result = result
        self._render_result(result, ear)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.probe.stop()
        self.lbl_status.setText("Captura completa")

    def _on_stop(self):
        self.probe.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Detenido")

    def _on_clear(self):
        self.curve_a.clear()
        self.curve_b.clear()
        self.curve_spec.clear()
        for region in self.bands_regions:
            self.p_spec.removeItem(region)
        self.bands_regions.clear()
        self.bars_snr.setOpts(x=[], height=[], width=0.15)
        self.text_pass.setText("")
        self.text_detail.setText("")
        self.lbl_repro.setText("--")
        self.lbl_stability.setText("--")
        self.lbl_response.setText("--")
        self._last_result = None
        self.lbl_status.setText("Listo")

    def _render_result(self, result: dict, ear: str):
        # Waveform A/B
        t = result["time_ms"]
        a = result["wave_a"]
        b = result["wave_b"]
        # Escalar a µPa (1 Pa = 1e6 µPa) para visualización
        self.curve_a.setData(t, a * 1e6)
        self.curve_b.setData(t, b * 1e6)
        # Spectrum
        self.curve_spec.setData(result["freqs"], result["spectrum_db"])
        # Sombrear bandas TEOAE
        for region in self.bands_regions:
            self.p_spec.removeItem(region)
        self.bands_regions.clear()
        for band_hz in self.generator.normative["bands_hz"]:
            ratio = self.generator.normative["band_halfwidth_ratio"]
            region = pg.LinearRegionItem(
                values=[band_hz * ratio, band_hz / ratio],
                orientation="vertical",
                brush=(41, 128, 185, 30),
                pen=pg.mkPen((41, 128, 185, 80)),
                movable=False,
            )
            self.p_spec.addItem(region)
            self.bands_regions.append(region)
        # SNR bars
        snr = result["snr_per_band"]
        centers = list(snr.keys())
        heights = list(snr.values())
        # x positions log-spaced for BarGraphItem (use linear; setLogMode handles visual)
        x_positions = np.array(centers, dtype=float)
        brushes = [
            (39, 174, 96) if result["pass_per_band"][c] else (192, 57, 43)
            for c in centers
        ]
        self.bars_snr.setOpts(x=x_positions, height=heights, width=0.12 * np.array(centers), brushes=brushes)
        self.p_snr.setXRange(min(centers) * 0.7, max(centers) * 1.4)
        # Pass/Refer
        if result["overall_pass"]:
            self.text_pass.setText("PASS")
            self.text_pass.setColor((39, 174, 96))
        else:
            self.text_pass.setText("REFER")
            self.text_pass.setColor((192, 57, 43))
        self.text_detail.setText(
            f"{ear}  |  {result['n_pass']}/{result['n_bands']} bandas pasan"
        )
        # Métricas de captura
        repro = result["reproducibility_pct"]
        min_repro = self.generator.normative["min_reproducibility_pct"]
        self.lbl_repro.setText(f"{repro:.0f}%")
        self.lbl_repro.setStyleSheet(
            f"color: {'#27ae60' if repro >= min_repro else '#c0392b'};"
        )
        stability = result["stability_pct"]
        min_stability = self.generator.normative["min_stability_pct"]
        self.lbl_stability.setText(f"{stability:.0f}%")
        self.lbl_stability.setStyleSheet(
            f"color: {'#27ae60' if stability >= min_stability else '#c0392b'};"
        )
        snr_total = result["total_response_db"] - result["total_noise_db"]
        self.lbl_response.setText(
            f"{result['total_response_db']:.1f} / {result['total_noise_db']:.1f} dB SPL "
            f"(SNR {snr_total:.1f} dB)"
        )
