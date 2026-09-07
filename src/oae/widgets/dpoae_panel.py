"""Panel DPOAE - DP-gram (f2 vs nivel DP) + función I/O + tabla por punto."""
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from oae.generators.dpoae import DpoaeGenerator
from oae.widgets.probe_check import ProbeCheckWidget
from oae.widgets.plot_style import style_plot, black_title

_EAR_COLOR = {"OD": (192, 57, 43), "OI": (41, 128, 185)}


class DpoaePanel(QWidget):
    """Tab DPOAE: barrido f2 (DP-gram binaural) + función I/O + tabla por punto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = DpoaeGenerator()
        self.case_od = None
        self.case_oi = None
        self._results = {"OD": None, "OI": None}
        self._build_ui()
        self._update_case_gate()

    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        # Izquierda
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(6, 6, 6, 6)
        self.probe = ProbeCheckWidget()
        left_layout.addWidget(self.probe)

        params = QGroupBox("Parámetros")
        form = QFormLayout(params)
        self.spn_l1 = QDoubleSpinBox()
        self.spn_l1.setRange(40.0, 80.0)
        self.spn_l1.setValue(float(self.generator.normative["default_l1_db_spl"]))
        self.spn_l1.setSuffix(" dB SPL")
        form.addRow("Nivel L1:", self.spn_l1)
        self.spn_l2 = QDoubleSpinBox()
        self.spn_l2.setRange(40.0, 80.0)
        self.spn_l2.setValue(float(self.generator.normative["default_l2_db_spl"]))
        self.spn_l2.setSuffix(" dB SPL")
        form.addRow("Nivel L2:", self.spn_l2)
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

        self.btn_start = QPushButton("Iniciar barrido")
        self.btn_io = QPushButton("Función I/O")
        self.btn_clear = QPushButton("Limpiar")
        btns = QHBoxLayout()
        btns.addWidget(self.btn_start)
        btns.addWidget(self.btn_io)
        btns.addWidget(self.btn_clear)
        left_layout.addLayout(btns)
        self.lbl_status = QLabel("Listo")
        left_layout.addWidget(self.lbl_status)

        # Tabla por punto f2: análogo a lo que un equipo real imprime en
        # el reporte DPOAE (DP, NF, SNR y pass/refer por frecuencia, no
        # solo el veredicto agregado).
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["f2 (Hz)", "DP (dB)", "NF (dB)", "SNR (dB)", "Result"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.table, stretch=1)

        # Derecha: DP-gram arriba (binaural), función I/O abajo
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground((255, 255, 255))
        self.p_dp = self.glw.addPlot(row=0, col=0, title=black_title("DP-gram (f2 vs nivel DP) -- OD/OI superpuestos"))
        self.p_dp.setLabel("left", "Nivel DP / Noise floor", units="dB SPL")
        self.p_dp.setLabel("bottom", "f2", units="Hz")
        self.p_dp.setLogMode(x=True, y=False)
        self.p_dp.setMouseEnabled(x=False, y=False)
        style_plot(self.p_dp)
        self.p_dp.addLegend(offset=(10, 10))
        self.curves_dp = {}
        self.curves_nf = {}
        for ear, color in _EAR_COLOR.items():
            self.curves_dp[ear] = self.p_dp.plot(
                pen=pg.mkPen(color, width=2), symbol="o", symbolSize=7,
                symbolBrush=color, name=f"DP {ear}",
            )
            self.curves_nf[ear] = self.p_dp.plot(
                pen=pg.mkPen(color, width=1, style=Qt.DashLine), symbol="t", symbolSize=5,
                symbolBrush=color, name=f"NF {ear}",
            )
        self.threshold_line = pg.InfiniteLine(
            pos=self.generator.normative["min_dp_above_noise_db"],
            angle=0,
            pen=pg.mkPen((100, 100, 100), width=1, style=Qt.DotLine),
            label="umbral SNR",
            labelOpts={"position": 0.95, "color": (100, 100, 100)},
        )
        self.p_dp.addItem(self.threshold_line)

        self.p_io = self.glw.addPlot(row=1, col=0, title=black_title("Función I/O (crecimiento, f2 fijo @ pico)"))
        self.p_io.setLabel("left", "Nivel DP / NF", units="dB SPL")
        self.p_io.setLabel("bottom", "L2", units="dB SPL")
        self.p_io.setMouseEnabled(x=False, y=False)
        style_plot(self.p_io)
        self.curve_io_dp = self.p_io.plot(pen=pg.mkPen((192, 57, 43), width=2), symbol="o", symbolSize=6, name="DP")
        self.curve_io_nf = self.p_io.plot(
            pen=pg.mkPen((120, 120, 120), width=1, style=Qt.DashLine), symbol="t", symbolSize=5, name="NF"
        )

        self.lbl_summary = QLabel("Pulse 'Iniciar barrido' para generar el DP-gram.")
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.addWidget(self.glw, stretch=1)
        right_layout.addWidget(self.lbl_summary)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 800])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(splitter)

        self.btn_start.clicked.connect(self._on_start)
        self.btn_io.clicked.connect(self._on_io)
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
        self.btn_io.setEnabled(available)
        if not available:
            self.lbl_status.setText(f"Sin atención abierta o EOA no configurado para {ear}.")

    def _on_start(self):
        ear, case = self._current_case()
        if case is None:
            return
        l1 = self.spn_l1.value()
        l2 = self.spn_l2.value()
        self.lbl_status.setText(f"Generando DP-gram: {ear}, L1={l1:.0f}, L2={l2:.0f}...")
        result = self.generator.generate(l1_db=l1, l2_db=l2, ear=ear, case=case)
        self._results[ear] = result
        self.curves_dp[ear].setData(result["f2_list"], result["dp_levels_db_spl"])
        self.curves_nf[ear].setData(result["f2_list"], result["noise_floors_db_spl"])
        all_f2 = np.concatenate([r["f2_list"] for r in self._results.values() if r is not None])
        self.p_dp.setXRange(all_f2.min() * 0.8, all_f2.max() * 1.25)

        threshold = self.generator.normative["min_dp_above_noise_db"]
        snr = result["dp_levels_db_spl"] - result["noise_floors_db_spl"]
        n_pass = int(np.sum(snr >= threshold))
        n_total = len(result["f2_list"])
        verdict = "PASS" if n_pass >= n_total / 2 else "REFER"
        self.lbl_summary.setText(
            f"{ear} | {verdict} | {n_pass}/{n_total} puntos pasan (umbral SNR {threshold} dB)"
        )
        self._fill_table(result, threshold)
        self.lbl_status.setText("Listo")

    def _fill_table(self, result, threshold):
        f2_list = result["f2_list"]
        dp = result["dp_levels_db_spl"]
        nf = result["noise_floors_db_spl"]
        snr = dp - nf
        self.table.setRowCount(len(f2_list))
        for row, f2 in enumerate(f2_list):
            values = [f"{f2:.0f}", f"{dp[row]:.1f}", f"{nf[row]:.1f}", f"{snr[row]:.1f}"]
            passed = snr[row] >= threshold
            values.append("PASS" if passed else "REFER")
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                if col == 4:
                    item.setForeground(Qt.darkGreen if passed else Qt.red)
                self.table.setItem(row, col, item)

    def _on_io(self):
        ear, case = self._current_case()
        if case is None:
            return
        result = self.generator.generate_io(ear=ear, case=case)
        self.curve_io_dp.setData(result["l2_list"], result["dp_levels_db_spl"])
        self.curve_io_nf.setData(result["l2_list"], result["noise_floors_db_spl"])
        self.lbl_status.setText(f"Función I/O generada @ {result['f2_hz']:.0f} Hz ({ear}).")

    def _on_clear(self):
        for ear in _EAR_COLOR:
            self.curves_dp[ear].clear()
            self.curves_nf[ear].clear()
            self._results[ear] = None
        self.curve_io_dp.clear()
        self.curve_io_nf.clear()
        self.table.setRowCount(0)
        self.lbl_summary.setText("Pulse 'Iniciar barrido' para generar el DP-gram.")
        self.lbl_status.setText("Listo")
