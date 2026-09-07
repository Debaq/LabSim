"""Panel SFOAE - barrido de supresor + curva de sintonía por frecuencia."""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from oae.generators.sfoae import SfoaeGenerator
from oae.widgets.probe_check import ProbeCheckWidget


class SfoaePanel(QWidget):
    """Tab SFOAE: barrido de supresor + curva de sintonía."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = SfoaeGenerator()
        self.case_od = None
        self.case_oi = None
        self._build_ui()
        self._update_case_gate()

    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(6, 6, 6, 6)
        self.probe = ProbeCheckWidget()
        left_layout.addWidget(self.probe)

        params = QGroupBox("Parámetros")
        form = QFormLayout(params)
        self.spn_freq = QDoubleSpinBox()
        self.spn_freq.setRange(500.0, 4000.0)
        self.spn_freq.setValue(float(self.generator.normative["default_freq_hz"]))
        self.spn_freq.setSuffix(" Hz")
        form.addRow("Frecuencia probe:", self.spn_freq)
        self.spn_level = QDoubleSpinBox()
        self.spn_level.setRange(0.0, 80.0)
        self.spn_level.setValue(float(self.generator.normative["default_level_db_spl"]))
        self.spn_level.setSuffix(" dB SPL")
        form.addRow("Nivel probe:", self.spn_level)
        left_layout.addWidget(params)

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

        self.btn_start = QPushButton("Iniciar")
        self.btn_tuning = QPushButton("Curva de sintonía")
        self.btn_clear = QPushButton("Limpiar")
        btns = QHBoxLayout()
        btns.addWidget(self.btn_start)
        btns.addWidget(self.btn_tuning)
        btns.addWidget(self.btn_clear)
        left_layout.addLayout(btns)
        self.lbl_status = QLabel("Listo")
        left_layout.addWidget(self.lbl_status)
        left_layout.addStretch(1)

        # Derecha
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground((255, 255, 255))
        self.p_mag = self.glw.addPlot(row=0, col=0, title="Magnitud SFOAE vs nivel supresor")
        self.p_mag.setLabel("left", "Magnitud", units="dB")
        self.p_mag.setLabel("bottom", "Nivel supresor", units="dB SPL")
        self.p_mag.showGrid(x=True, y=True, alpha=0.3)
        self.p_mag.setMouseEnabled(x=False, y=False)
        self.curve_mag = self.p_mag.plot(pen=pg.mkPen((41, 128, 185), width=2),
                                          symbol="o", symbolSize=6)

        self.p_phase = self.glw.addPlot(row=1, col=0, title="Fase SFOAE vs nivel supresor")
        self.p_phase.setLabel("left", "Fase", units="°")
        self.p_phase.setLabel("bottom", "Nivel supresor", units="dB SPL")
        self.p_phase.showGrid(x=True, y=True, alpha=0.3)
        self.p_phase.setMouseEnabled(x=False, y=False)
        self.curve_phase = self.p_phase.plot(pen=pg.mkPen((192, 57, 43), width=2),
                                             symbol="s", symbolSize=6)

        self.p_tuning = self.glw.addPlot(row=2, col=0, title="Curva de sintonía (magnitud esperada vs frecuencia probe)")
        self.p_tuning.setLabel("left", "Magnitud", units="dB")
        self.p_tuning.setLabel("bottom", "Frecuencia probe", units="Hz")
        self.p_tuning.showGrid(x=True, y=True, alpha=0.3)
        self.p_tuning.setMouseEnabled(x=False, y=False)
        self.p_tuning.setLogMode(x=True, y=False)
        self.curve_tuning = self.p_tuning.plot(pen=pg.mkPen((39, 174, 96), width=2))
        self.probe_freq_marker = pg.InfiniteLine(
            angle=90, pen=pg.mkPen((150, 150, 150), width=1, style=Qt.DotLine)
        )
        self.p_tuning.addItem(self.probe_freq_marker)

        self.lbl_summary = QLabel("Pulse 'Iniciar' para barrido de supresor.")
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.addWidget(self.glw, stretch=1)
        right_layout.addWidget(self.lbl_summary)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 800])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(splitter)

        self.btn_start.clicked.connect(self._on_start)
        self.btn_tuning.clicked.connect(self._on_tuning)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_od.toggled.connect(self._update_case_gate)
        self.btn_oi.toggled.connect(self._update_case_gate)

    def set_case(self, case_od, case_oi):
        self.case_od = case_od
        self.case_oi = case_oi
        self._update_case_gate()

    def _current_case(self):
        ear = "OD" if self.btn_od.isChecked() else "OI"
        return ear, (self.case_od if ear == "OD" else self.case_oi)

    def _update_case_gate(self):
        ear, case = self._current_case()
        available = case is not None
        self.btn_start.setEnabled(available)
        self.btn_tuning.setEnabled(available)
        if not available:
            self.lbl_status.setText(f"Sin atención abierta o EOA no configurado para {ear}.")

    def _on_start(self):
        ear, case = self._current_case()
        if case is None:
            return
        freq = self.spn_freq.value()
        level = self.spn_level.value()
        self.lbl_status.setText(f"Generando SFOAE: {ear}, {freq:.0f} Hz, {level:.0f} dB SPL...")
        result = self.generator.generate(freq_hz=freq, level_db=level, ear=ear, case=case)
        self.curve_mag.setData(result["suppressor_levels"], result["magnitude_db"])
        self.curve_phase.setData(result["suppressor_levels"], result["phase_deg"])
        self.probe_freq_marker.setPos(np.log10(freq))
        # Resumen
        max_mag = float(np.max(result["magnitude_db"]))
        threshold = self.generator.normative["min_magnitude_db"]
        verdict = "PRESENTE" if max_mag >= threshold else "AUSENTE"
        self.lbl_summary.setText(
            f"{ear} | {verdict} | SFOAE @ {freq:.0f} Hz: magnitud máx {max_mag:.1f} dB "
            f"(umbral {threshold} dB, base sin supresor {result['base_magnitude_db']:.1f} dB)"
        )
        self.lbl_status.setText("Listo")

    def _on_tuning(self):
        ear, case = self._current_case()
        if case is None:
            return
        result = self.generator.tuning_curve(ear=ear, case=case)
        self.curve_tuning.setData(result["freqs"], result["magnitude_db"])
        self.lbl_status.setText(f"Curva de sintonía generada ({ear}).")

    def _on_clear(self):
        self.curve_mag.clear()
        self.curve_phase.clear()
        self.curve_tuning.clear()
        self.lbl_summary.setText("Pulse 'Iniciar' para barrido de supresor.")
        self.lbl_status.setText("Listo")
