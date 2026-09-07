"""Panel TEOAE.

Izquierda: controles (nivel dB SPL, # promedios, oído OD/OI, botón Iniciar).
Derecha: GraphicsLayoutWidget con 3 gráficos principales + 2 secundarios:
  - Respuesta: forma de onda promediada completa
  - A / B: buffers split para chequeo visual de reproducibilidad
  - Fourier: espectro FFT con bandas marcadas
  - SNR por banda + umbral, y resultado PASS/REFER
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
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
from oae.widgets.plot_style import style_plot, black_title


class TeoaePanel(QWidget):
    """Tab TEOAE del módulo OAE clínico."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = TeoaeGenerator()
        self._last_result = None
        self._pending = None
        self._anim_checkpoints = []
        self._anim_idx = 0
        self._anim_ear = None
        self.case_od = None
        self.case_oi = None
        self._build_ui()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
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

        # ---------- DERECHA: 3 gráficos principales (fila 0) + 2 secundarios (fila 1) ----------
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground((255, 255, 255))

        # (0,0): Respuesta -- forma de onda promediada completa (única curva)
        self.p_response = self.glw.addPlot(row=0, col=0, title=black_title("Respuesta"))
        self.p_response.setLabel("left", "Amplitud", units="Pa")
        self.p_response.setLabel("bottom", "Tiempo", units="ms")
        self.p_response.setMouseEnabled(x=False, y=False)
        style_plot(self.p_response)
        self.curve_response = self.p_response.plot(pen=pg.mkPen((0, 0, 0), width=2))

        # (0,1): A vs B -- split buffer, chequeo visual de reproducibilidad
        self.p_wave = self.glw.addPlot(row=0, col=1, title=black_title("A / B"))
        self.p_wave.setLabel("left", "Amplitud", units="Pa")
        self.p_wave.setLabel("bottom", "Tiempo", units="ms")
        self.p_wave.setMouseEnabled(x=False, y=False)
        style_plot(self.p_wave)
        self.curve_a = self.p_wave.plot(pen=pg.mkPen((192, 57, 43), width=2), name="A")
        self.curve_b = self.p_wave.plot(pen=pg.mkPen((41, 128, 185), width=2, style=Qt.DashLine), name="B")

        # (0,2): Fourier -- espectro FFT con bandas marcadas
        self.p_spec = self.glw.addPlot(row=0, col=2, title=black_title("Fourier"))
        self.p_spec.setLabel("left", "Nivel", units="dB SPL")
        self.p_spec.setLabel("bottom", "Frecuencia", units="Hz")
        self.p_spec.setMouseEnabled(x=False, y=False)
        self.p_spec.setLogMode(x=True, y=False)
        style_plot(self.p_spec)
        self.curve_spec = self.p_spec.plot(pen=pg.mkPen((0, 0, 0), width=1), name="spec")
        self.bands_regions = []

        # (1, 0-1): SNR por banda
        self.p_snr = self.glw.addPlot(row=1, col=0, colspan=2, title=black_title("SNR por banda (umbral 6 dB)"))
        self.p_snr.setLabel("left", "SNR", units="dB")
        self.p_snr.setLabel("bottom", "Frecuencia", units="Hz")
        self.p_snr.setMouseEnabled(x=False, y=False)
        # Sin setLogMode: BarGraphItem no se auto-transforma a log como sí
        # hace PlotDataItem (curve_spec), y setXRange más abajo pasa Hz
        # lineales -- mezclar ambos rompe el eje (rango absurdo, barras
        # invisibles). Bandas son pocas y discretas, lineal alcanza.
        style_plot(self.p_snr)
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

        # (1,2): pass/refer
        self.p_result = self.glw.addPlot(row=1, col=2, title=black_title("Resultado"))
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

    PROBE_CHECK_MS = 1800
    SWEEP_ANIM_MS = 90

    def _on_start(self):
        ear, case = self._current_case()
        if case is None:
            return
        self._pending = (ear, case, self.spn_level.value(), self.spn_n.value())
        self.lbl_status.setText("Chequeando sonda...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.probe.start()
        # Chequeo de sonda animado real (QTimer del probe) antes de generar
        # la captura -- antes generate() corría síncrono en la misma llamada
        # y bloqueaba el loop de eventos, así que el timer nunca pintaba un
        # frame (la animación jamás se veía).
        QTimer.singleShot(self.PROBE_CHECK_MS, self._run_capture)

    def _run_capture(self):
        if self._pending is None:
            return
        ear, case, level, n = self._pending
        self._pending = None
        self.probe.stop()
        result = self.generator.generate(level_db=level, n_sweeps=n, ear=ear, case=case)
        self._last_result = result
        self._anim_ear = ear
        self._anim_checkpoints = result["sweep_checkpoints"]
        self._anim_idx = 0
        self._anim_timer.start(self.SWEEP_ANIM_MS)
        self._anim_tick()

    def _anim_tick(self):
        checkpoints = self._anim_checkpoints
        result = self._last_result
        if self._anim_idx >= len(checkpoints):
            self._anim_timer.stop()
            self._render_result(result, self._anim_ear)
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.lbl_status.setText("Captura completa")
            return
        cp = checkpoints[self._anim_idx]
        self.curve_response.setData(result["time_ms"], cp["waveform"] * 1e6)
        self.lbl_status.setText(
            f"Promediando barridos: {cp['n_sweeps']}/{result['n_sweeps']}..."
        )
        self._anim_idx += 1

    def _on_stop(self):
        self._pending = None
        self._anim_timer.stop()
        self.probe.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Detenido")

    def _on_clear(self):
        self.curve_response.clear()
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
        # Respuesta + Waveform A/B
        t = result["time_ms"]
        a = result["wave_a"]
        b = result["wave_b"]
        # Escalar a µPa (1 Pa = 1e6 µPa) para visualización
        self.curve_response.setData(t, result["waveform"] * 1e6)
        self.curve_a.setData(t, a * 1e6)
        self.curve_b.setData(t, b * 1e6)
        # Spectrum. setXRange explícito en log10 (no confiar solo en
        # autoRange -- ver comentario en el shading de bandas más abajo
        # sobre por qué un item no-log-aware puede desbordarlo).
        self.curve_spec.setData(result["freqs"], result["spectrum_db"])
        self.p_spec.setXRange(
            np.log10(self.generator.normative["spectrum_low_hz"]),
            np.log10(self.generator.normative["spectrum_high_hz"]),
            padding=0.02,
        )
        # Sombrear bandas TEOAE
        for region in self.bands_regions:
            self.p_spec.removeItem(region)
        self.bands_regions.clear()
        for band_hz in self.generator.normative["bands_hz"]:
            ratio = self.generator.normative["band_halfwidth_ratio"]
            # p_spec está en logMode x=True: curve_spec se autotransforma a
            # log10 internamente (PlotDataItem), pero LinearRegionItem NO
            # tiene setLogMode y toma sus "values" tal cual como coordenadas
            # de la escena. Si le pasamos Hz lineales (350..5600), esos
            # límites lineales entran al cálculo de autoRange del ViewBox
            # junto a la curva ya-log (rango ~2.7..3.7) y el autoRange se
            # estira para cubrir ambos: la curva real queda aplastada en una
            # franja invisible contra el borde. Hay que pasarle los límites
            # ya en log10 para que coincidan con el sistema de coordenadas
            # real de la escena.
            region = pg.LinearRegionItem(
                values=[np.log10(band_hz * ratio), np.log10(band_hz / ratio)],
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
