"""Panel SFOAE - corrida única animada: barrido de supresor + curva de sintonía.

La prueba es lineal (se mide el barrido de supresor en la frecuencia probe y
después se recorre la sintonía en frecuencia), así que va con UN solo botón
"Iniciar": antes había que apretar "Iniciar" y luego "Curva de sintonía", y
el alumno podía quedarse con media prueba. La corrida se anima punto a punto
como TEOAE/DPOAE -- el generador entrega promedios parciales por punto.
"""
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
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

from oae.generators.base import oae_probe_fit
from oae.generators.sfoae import SfoaeGenerator
from oae.widgets.probe_check import ProbeCheckWidget
from oae.widgets.plot_style import style_plot, black_title


class SfoaePanel(QWidget):
    """Tab SFOAE: barrido de supresor + curva de sintonía, en una corrida."""

    PROBE_CHECK_MS = 2000
    ANIM_TICK_MS = 80
    # La sintonía son 24 frecuencias: con todos los promedios de cada una la
    # corrida se hace larga sin agregar información, así que se saltean
    # frames intermedios (mismo criterio que la I/O del panel DPOAE).
    TUNING_FRAME_STEP = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = SfoaeGenerator()
        self.case_od = None
        self.case_oi = None
        self._pending = None
        self._steps = []
        self._step_idx = 0
        self._anim_ear = None
        self._result = None
        self._tuning = None
        self._sup_committed = []
        self._tun_committed = []
        # Resumen + captura por oído para el informe (ver report_summary()).
        self._report = {}
        self._shots = {}
        self._build_ui()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
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

        # Lectura en vivo del punto que se está midiendo: en el equipo real
        # el operador ve el valor del punto actual mientras promedia.
        live_box = QGroupBox("Punto en curso")
        live_form = QFormLayout(live_box)
        self.lbl_live_point = QLabel("--")
        live_form.addRow("Supresor / probe:", self.lbl_live_point)
        self.lbl_live_mag = QLabel("--")
        live_form.addRow("Magnitud:", self.lbl_live_mag)
        self.lbl_live_avg = QLabel("--")
        live_form.addRow("Promedios:", self.lbl_live_avg)
        left_layout.addWidget(live_box)
        left_layout.addStretch(1)

        # Derecha
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground((255, 255, 255))
        self.p_mag = self.glw.addPlot(row=0, col=0, title=black_title("Magnitud SFOAE vs nivel supresor"))
        self.p_mag.setLabel("left", "Magnitud", units="dB")
        self.p_mag.setLabel("bottom", "Nivel supresor", units="dB SPL")
        self.p_mag.setMouseEnabled(x=False, y=False)
        style_plot(self.p_mag)
        self.curve_mag = self.p_mag.plot(pen=pg.mkPen((41, 128, 185), width=2),
                                          symbol="o", symbolSize=6)
        self.live_mag = self.p_mag.plot(
            pen=None, symbol="o", symbolSize=11,
            symbolBrush=(41, 128, 185, 70), symbolPen=pg.mkPen((41, 128, 185), width=1))
        # Piso de ruido del registro: sin él la magnitud no se puede leer
        # (una SFOAE de 0.4 dB parece "presente" hasta que se ve dónde está
        # el ruido). El veredicto es por SNR sobre esta línea.
        self.noise_mag = pg.InfiniteLine(
            angle=0, pen=pg.mkPen((150, 150, 150), width=1, style=Qt.DashLine),
            label="ruido", labelOpts={"position": 0.05, "color": (120, 120, 120)})
        self.noise_mag.setVisible(False)
        self.p_mag.addItem(self.noise_mag)

        self.p_phase = self.glw.addPlot(row=1, col=0, title=black_title("Fase SFOAE vs nivel supresor"))
        self.p_phase.setLabel("left", "Fase", units="°")
        self.p_phase.setLabel("bottom", "Nivel supresor", units="dB SPL")
        self.p_phase.setMouseEnabled(x=False, y=False)
        style_plot(self.p_phase)
        self.curve_phase = self.p_phase.plot(pen=pg.mkPen((192, 57, 43), width=2),
                                             symbol="s", symbolSize=6)
        self.live_phase = self.p_phase.plot(
            pen=None, symbol="s", symbolSize=11,
            symbolBrush=(192, 57, 43, 70), symbolPen=pg.mkPen((192, 57, 43), width=1))

        self.p_tuning = self.glw.addPlot(row=2, col=0, title=black_title("Curva de sintonía (magnitud esperada vs frecuencia probe)"))
        self.p_tuning.setLabel("left", "Magnitud", units="dB")
        self.p_tuning.setLabel("bottom", "Frecuencia probe", units="Hz")
        self.p_tuning.setMouseEnabled(x=False, y=False)
        self.p_tuning.setLogMode(x=True, y=False)
        style_plot(self.p_tuning)
        self.curve_tuning = self.p_tuning.plot(pen=pg.mkPen((39, 174, 96), width=2))
        self.live_tuning = self.p_tuning.plot(
            pen=None, symbol="o", symbolSize=11,
            symbolBrush=(39, 174, 96, 70), symbolPen=pg.mkPen((39, 174, 96), width=1))
        self.noise_tuning = pg.InfiniteLine(
            angle=0, pen=pg.mkPen((150, 150, 150), width=1, style=Qt.DashLine),
            label="ruido", labelOpts={"position": 0.05, "color": (120, 120, 120)})
        self.noise_tuning.setVisible(False)
        self.p_tuning.addItem(self.noise_tuning)
        self.probe_freq_marker = pg.InfiniteLine(
            angle=90, pen=pg.mkPen((150, 150, 150), width=1, style=Qt.DotLine)
        )
        self.p_tuning.addItem(self.probe_freq_marker)

        self.lbl_summary = QLabel("Pulse 'Iniciar': barrido de supresor y curva de sintonía.")
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
        self.btn_stop.clicked.connect(self._on_stop)
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
        self.btn_start.setEnabled(available and not self._anim_timer.isActive())
        if not available:
            self.lbl_status.setText(f"Sin atención abierta o EOA no configurado para {ear}.")

    # ------------------------------------------------------------------
    # Corrida
    # ------------------------------------------------------------------
    def _on_start(self):
        ear, case = self._current_case()
        if case is None:
            return
        # El widget de chequeo de sonda corre con su propio QTimer: si se
        # genera la captura en la misma vuelta del event loop no alcanza a
        # pintar un frame (mismo patrón que TEOAE/DPOAE).
        self._pending = (ear, case)
        self.lbl_status.setText("Chequeando sonda...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.probe.start(self.spn_level.value(), oae_probe_fit(case))
        QTimer.singleShot(self.PROBE_CHECK_MS, self._run_capture)

    def _run_capture(self):
        if self._pending is None:
            return
        ear, case = self._pending
        self._pending = None
        self.probe.stop()
        freq = self.spn_freq.value()
        level = self.spn_level.value()

        self._result = self.generator.generate(
            freq_hz=freq, level_db=level, ear=ear, case=case)
        self._tuning = self.generator.tuning_curve(ear=ear, case=case)
        self._anim_ear = ear
        self._sup_committed = []
        self._tun_committed = []
        self.curve_mag.clear()
        self.curve_phase.clear()
        self.curve_tuning.clear()
        self.probe_freq_marker.setPos(np.log10(freq))
        for line, result in ((self.noise_mag, self._result),
                             (self.noise_tuning, self._tuning)):
            line.setPos(result["noise_floor_db"])
            line.setVisible(True)
        self.lbl_summary.setText("")

        # Cola de pasos: primero el barrido de supresor en la frecuencia
        # probe, después la sintonía en frecuencia. Una sola corrida.
        steps = []
        for point in self._result["points"]:
            for frame in point["frames"]:
                steps.append(("sup_frame", point, frame))
            steps.append(("sup_commit", point, None))
        for point in self._tuning["points"]:
            for frame in point["frames"][::self.TUNING_FRAME_STEP]:
                steps.append(("tun_frame", point, frame))
            steps.append(("tun_commit", point, None))
        self._steps = steps
        self._step_idx = 0
        self._anim_timer.start(self.ANIM_TICK_MS)
        self._anim_tick()

    def _anim_tick(self):
        if self._step_idx >= len(self._steps):
            self._anim_timer.stop()
            self._finish("Captura completa")
            return
        kind, point, frame = self._steps[self._step_idx]
        self._step_idx += 1
        if kind == "sup_frame":
            self._render_sup_frame(point, frame)
        elif kind == "sup_commit":
            self._commit_sup_point(point)
        elif kind == "tun_frame":
            self._render_tun_frame(point, frame)
        elif kind == "tun_commit":
            self._commit_tun_point(point)

    def _on_stop(self):
        self._pending = None
        self._anim_timer.stop()
        self.probe.stop()
        self._finish("Detenido")

    def _finish(self, status_text):
        """Cierra la corrida con lo que haya quedado medido.

        Un equipo real también entrega los puntos ya fijados si se corta la
        prueba a la mitad, no descarta la captura entera.
        """
        self.btn_stop.setEnabled(False)
        self._update_case_gate()
        self.lbl_status.setText(status_text)
        self.live_mag.clear()
        self.live_phase.clear()
        self.live_tuning.clear()
        self.lbl_live_point.setText("--")
        self.lbl_live_mag.setText("--")
        self.lbl_live_avg.setText("--")
        if not self._sup_committed:
            return
        ear = self._anim_ear
        freq = self._result["freq_hz"]
        max_mag = max(p["magnitude_db"] for p in self._sup_committed)
        noise = self._result["noise_floor_db"]
        min_snr = self._result["min_snr_db"]
        snr = max_mag - noise
        verdict = "PRESENTE" if snr >= min_snr else "AUSENTE"
        color = "#27ae60" if verdict == "PRESENTE" else "#c0392b"
        tun_txt = ""
        if self._tun_committed:
            best = max(self._tun_committed, key=lambda p: p["magnitude_db"])
            tun_txt = (f"  |  sintonía: máximo {best['magnitude_db']:.1f} dB @ "
                       f"{best['freq_hz']:.0f} Hz ({len(self._tun_committed)}/"
                       f"{len(self._tuning['points'])} frecuencias)")
        self.lbl_summary.setText(
            f"<b>{ear}</b> | <b style='color:{color}'>{verdict}</b> | "
            f"SFOAE @ {freq:.0f} Hz: magnitud máx {max_mag:.1f} dB sobre un "
            f"piso de {noise:.1f} dB (SNR {snr:.1f} dB, criterio {min_snr:.0f} dB)"
            f"{tun_txt}"
        )
        self._store_report(ear, max_mag, noise, snr, min_snr, verdict,
                           partial=status_text == "Detenido")

    # ------------------------------------------------------------------
    # Informe
    # ------------------------------------------------------------------
    def _store_report(self, ear, max_mag, noise, snr, min_snr, verdict,
                      partial=False):
        best_tun = (max(self._tun_committed, key=lambda p: p["magnitude_db"])
                    if self._tun_committed else None)
        self._report[ear] = {
            "freq_probe_hz": round(float(self._result["freq_hz"]), 0),
            "nivel_probe_db_spl": round(float(self._result["level_db_spl"]), 1),
            "magnitud_max_db": round(float(max_mag), 1),
            "piso_db": round(float(noise), 1),
            "snr_db": round(float(snr), 1),
            "criterio_snr_db": round(float(min_snr), 1),
            "veredicto": verdict,
            "supresion": [
                {
                    "supresor_db_spl": round(float(pt["suppressor_db"]), 0),
                    "magnitud_db": round(float(pt["magnitude_db"]), 1),
                    "fase_deg": round(float(pt["phase_deg"]), 1),
                }
                for pt in self._sup_committed
            ],
            "sintonia_max_db": round(float(best_tun["magnitude_db"]), 1) if best_tun else None,
            "sintonia_freq_hz": round(float(best_tun["freq_hz"]), 0) if best_tun else None,
            "sintonia_puntos": len(self._tun_committed),
            "parcial": bool(partial),
        }
        self._shots[ear] = self.glw.grab()

    def reset_all(self):
        """Descarta capturas y datos de informe (cambio de paciente).

        Sin esto, las capturas de un paciente seguían en pantalla -- y en el
        payload del informe -- al abrir la atención del siguiente.
        """
        self._report.clear()
        self._shots.clear()
        self._on_clear()

    def report_summary(self):
        """Dict {oído: resumen} de lo capturado (para el informe)."""
        return dict(self._report)

    def report_shots(self):
        """Dict {oído: QPixmap} con la captura de los gráficos por oído."""
        return dict(self._shots)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def _render_sup_frame(self, point, frame):
        self.live_mag.setData([point["suppressor_db"]], [frame["magnitude_db"]])
        self.live_phase.setData([point["suppressor_db"]], [frame["phase_deg"]])
        self.lbl_live_point.setText(
            f"{point['suppressor_db']:.0f} dB SPL @ {self._result['freq_hz']:.0f} Hz")
        self.lbl_live_mag.setText(f"{frame['magnitude_db']:.1f} dB")
        self.lbl_live_avg.setText(str(frame["n_avg"]))
        self.lbl_status.setText(
            f"Barrido de supresor: {len(self._sup_committed) + 1}/"
            f"{len(self._result['points'])} niveles...")

    def _commit_sup_point(self, point):
        self._sup_committed.append(point)
        xs = [p["suppressor_db"] for p in self._sup_committed]
        self.curve_mag.setData(xs, [p["magnitude_db"] for p in self._sup_committed])
        self.curve_phase.setData(xs, [p["phase_deg"] for p in self._sup_committed])

    def _render_tun_frame(self, point, frame):
        self.live_tuning.setData([point["freq_hz"]], [frame["magnitude_db"]])
        self.lbl_live_point.setText(f"probe {point['freq_hz']:.0f} Hz")
        self.lbl_live_mag.setText(f"{frame['magnitude_db']:.1f} dB")
        self.lbl_live_avg.setText(str(frame["n_avg"]))
        self.lbl_status.setText(
            f"Curva de sintonía: {len(self._tun_committed) + 1}/"
            f"{len(self._tuning['points'])} frecuencias...")

    def _commit_tun_point(self, point):
        self._tun_committed.append(point)
        self.curve_tuning.setData(
            [p["freq_hz"] for p in self._tun_committed],
            [p["magnitude_db"] for p in self._tun_committed])

    def _on_clear(self):
        ear, _case = self._current_case()
        self._report.pop(ear, None)
        self._shots.pop(ear, None)
        self._pending = None
        self._anim_timer.stop()
        self.probe.stop()
        self._steps = []
        self._step_idx = 0
        self._sup_committed = []
        self._tun_committed = []
        self.btn_stop.setEnabled(False)
        self._update_case_gate()
        self.curve_mag.clear()
        self.curve_phase.clear()
        self.curve_tuning.clear()
        self.live_mag.clear()
        self.live_phase.clear()
        self.live_tuning.clear()
        self.noise_mag.setVisible(False)
        self.noise_tuning.setVisible(False)
        self.lbl_live_point.setText("--")
        self.lbl_live_mag.setText("--")
        self.lbl_live_avg.setText("--")
        self.lbl_summary.setText("Pulse 'Iniciar': barrido de supresor y curva de sintonía.")
        self.lbl_status.setText("Listo")
