"""Panel DPOAE - DP-grama animado + espectro FFT del punto + función I/O.

Un solo botón "Iniciar": la corrida reproduce lo que hace el equipo real,
en este orden y en la misma captura (antes la función I/O era un botón
aparte que dibujaba la curva entera de golpe):

  1. chequeo de sonda (probe fit),
  2. DP-grama: se mide f2 por f2; en cada punto se ve el espectro FFT con
     los primarios f1/f2 y el producto 2f1-f2 emergiendo sobre el ruido
     mientras se promedia, y recién ahí el punto queda fijado en la curva,
  3. función I/O: se construye punto a punto sobre el f2 de mejor SNR del
     DP-grama, y marca el umbral DP (L2 más bajo con SNR >= criterio).

El DP-grama lleva las áreas de lectura clínica: rango normal por
frecuencia (verde), zona de ruido (relleno bajo el noise floor) y la línea
de objetivo NF + criterio SNR por punto.
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
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from oae.generators.base import oae_probe_fit
from oae.generators.dpoae import DpoaeGenerator
from oae.widgets.probe_check import ProbeCheckWidget
from oae.widgets.plot_style import style_plot, black_title

_EAR_COLOR = {"OD": (192, 57, 43), "OI": (41, 128, 185)}


class DpoaePanel(QWidget):
    """Tab DPOAE: DP-grama binaural + espectro por punto + función I/O."""

    PROBE_CHECK_MS = 2200
    ANIM_TICK_MS = 80
    # Rango vertical del DP-grama: cubre el rango normal (hasta ~17 dB) y
    # deja ver el piso de ruido sin que la curva se pegue al borde.
    DP_Y_MIN = -30.0
    DP_Y_MAX = 30.0
    # Espectro: los primarios andan en 55-70 dB SPL, el DP en torno a 0-15.
    SPEC_Y_MIN = -40.0
    SPEC_Y_MAX = 80.0
    # La I/O se anima con menos frames por punto que el DP-grama: son 10
    # niveles de L2 y con los 6 promedios de cada uno la corrida se hace
    # larga sin agregar información.
    IO_FRAME_STEP = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = DpoaeGenerator()
        self.case_od = None
        self.case_oi = None
        self._results = {"OD": None, "OI": None}
        self._io_results = {"OD": None, "OI": None}
        self._steps = []
        self._step_idx = 0
        self._anim_ear = None
        self._pending = None
        self._committed = []
        self._io_committed = []
        # Resumen + captura por oído para el informe (ver report_summary()).
        self._report = {}
        self._shots = {}
        self._build_ui()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._update_case_gate()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)
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

        # Métricas del punto que se está midiendo, como el cabezal de un
        # equipo real (f1/f2/2f1-f2 y promedios acumulados).
        point_box = QGroupBox("Punto en medición")
        point_form = QFormLayout(point_box)
        self.lbl_pair = QLabel("--")
        point_form.addRow("f1 / f2:", self.lbl_pair)
        self.lbl_fdp = QLabel("--")
        point_form.addRow("2f1-f2:", self.lbl_fdp)
        self.lbl_avg = QLabel("--")
        point_form.addRow("Promedios:", self.lbl_avg)
        left_layout.addWidget(point_box)

        # Tabla por punto f2: análogo a lo que un equipo real imprime en
        # el reporte DPOAE (DP, NF, SNR y pass/refer por frecuencia, no
        # solo el veredicto agregado).
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["f2 (Hz)", "DP (dB)", "NF (dB)", "SNR (dB)", "Result"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.table, stretch=1)

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground((255, 255, 255))
        self._build_dpgram()
        self._build_spectrum()
        self._build_io()

        self.lbl_summary = QLabel("Pulse 'Iniciar' para correr el DP-grama.")
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
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_od.toggled.connect(self._update_case_gate)
        self.btn_oi.toggled.connect(self._update_case_gate)

    def _build_dpgram(self):
        self.p_dp = self.glw.addPlot(
            row=0, col=0, colspan=2,
            title=black_title("DP-grama (nivel DP vs f2) -- OD/OI superpuestos"),
        )
        self.p_dp.setLabel("left", "Nivel", units="dB SPL")
        # Sin units=: en logMode pyqtgraph reescalaría el rótulo y los ticks
        # los ponemos nosotros (mismo motivo que en el Fourier de TEOAE).
        self.p_dp.setLabel("bottom", "f2 (kHz)")
        self.p_dp.setLogMode(x=True, y=False)
        self.p_dp.setMouseEnabled(x=False, y=False)
        self.p_dp.setYRange(self.DP_Y_MIN, self.DP_Y_MAX)
        style_plot(self.p_dp)
        # labelTextColor explícito: la config global de pyqtgraph puede venir
        # con foreground='w' de otro módulo y la leyenda queda blanca sobre
        # blanco (mismo problema que resuelve plot_style para los ejes).
        legend = self.p_dp.addLegend(offset=(10, 10), labelTextColor="k",
                                     brush=pg.mkBrush(255, 255, 255, 200),
                                     pen=pg.mkPen(200, 200, 200))
        legend.setColumnCount(3)

        f2_list = self.generator.f2_list()
        # El eje va en log10(Hz): antes se llamaba a setXRange con Hz
        # lineales sobre un plot en logMode, así que el rango quedaba en
        # 800..7500 "log units" y toda la curva se aplastaba contra el
        # borde izquierdo -- de ahí que el DP-grama se viera vacío.
        self.p_dp.setXRange(np.log10(f2_list.min() * 0.88),
                            np.log10(f2_list.max() * 1.12), padding=0)
        self.p_dp.getAxis("bottom").setTicks([
            [(np.log10(f), f"{f / 1000:g}") for f in f2_list]
        ])

        # Área de normalidad: rango p5-p95 del nivel DP por frecuencia.
        # Las curvas borde van sin pen visible; lo que se ve es el relleno.
        band_low, band_high = self.generator.normal_band(f2_list)
        self._band_lo = self.p_dp.plot(f2_list, band_low, pen=pg.mkPen((39, 174, 96, 90), width=1))
        self._band_hi = self.p_dp.plot(f2_list, band_high, pen=pg.mkPen((39, 174, 96, 90), width=1))
        band = pg.FillBetweenItem(self._band_lo, self._band_hi,
                                  brush=pg.mkBrush(39, 174, 96, 45))
        band.setZValue(-20)
        self.p_dp.addItem(band)
        # Entrada de leyenda para el área (FillBetweenItem no va a la
        # leyenda por sí solo; un ítem vacío con el mismo brush sí).
        self.p_dp.plot([], [], pen=pg.mkPen((39, 174, 96), width=6), name="Rango normal")

        self.curves_dp = {}
        self.curves_nf = {}
        self.curves_target = {}
        self.live_dp = {}
        self.live_nf = {}
        for ear, color in _EAR_COLOR.items():
            # Zona de ruido: relleno bajo el noise floor -- todo lo que cae
            # ahí no es distinguible del ruido de fondo.
            self.curves_nf[ear] = self.p_dp.plot(
                pen=pg.mkPen(color, width=1, style=Qt.DashLine), symbol="t", symbolSize=5,
                symbolBrush=color, name=f"NF {ear}",
                fillLevel=self.DP_Y_MIN, brush=pg.mkBrush(color[0], color[1], color[2], 40),
            )
            # Nivel objetivo POR FRECUENCIA (noise floor + criterio SNR de
            # ese punto): lo que el DP tiene que superar ahí para pasar.
            # El criterio es relativo al ruido de cada punto, no un nivel
            # absoluto único.
            # Una sola entrada de leyenda para el objetivo (la línea es la
            # misma lectura en los dos oídos, solo cambia el color).
            target_name = (f"Objetivo (NF+{self.generator.normative['min_dp_above_noise_db']:g} dB)"
                           if ear == "OD" else None)
            self.curves_target[ear] = self.p_dp.plot(
                pen=pg.mkPen(color, width=1, style=Qt.DotLine), name=target_name,
            )
            self.curves_dp[ear] = self.p_dp.plot(
                pen=pg.mkPen(color, width=2), symbol="o", symbolSize=8,
                symbolBrush=color, name=f"DP {ear}",
            )
            # Punto "en vivo": el valor parcial del f2 que se está midiendo,
            # todavía no fijado en la curva (símbolo hueco).
            self.live_dp[ear] = self.p_dp.plot(
                pen=None, symbol="o", symbolSize=12, symbolBrush=None,
                symbolPen=pg.mkPen(color, width=2),
            )
            self.live_nf[ear] = self.p_dp.plot(
                pen=None, symbol="t", symbolSize=9, symbolBrush=None,
                symbolPen=pg.mkPen(color, width=1, style=Qt.DashLine),
            )

        # InfiniteLine NO se autotransforma en logMode (a diferencia de
        # PlotDataItem): hay que darle log10(Hz) o se va fuera del ViewBox.
        self.cursor_f2 = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen((120, 120, 120), width=1, style=Qt.DashLine))
        self.cursor_f2.setZValue(-5)
        self.cursor_f2.setVisible(False)
        self.p_dp.addItem(self.cursor_f2)

    def _build_spectrum(self):
        self.p_spec = self.glw.addPlot(
            row=1, col=0, title=black_title("Espectro del canal (punto en medición)"))
        self.p_spec.setLabel("left", "Nivel", units="dB SPL")
        self.p_spec.setLabel("bottom", "Frecuencia", units="Hz")
        # Eje lineal a propósito (el DP-grama sí va en log): es un análisis
        # FFT y así se ve la separación real entre f1, f2 y 2f1-f2, que es
        # lo que hay que aprender a leer. En log los bins de agudos se
        # apelotonan y el piso de ruido parece tener un escalón.
        self.p_spec.setMouseEnabled(x=False, y=False)
        self.p_spec.setYRange(self.SPEC_Y_MIN, self.SPEC_Y_MAX)
        self.p_spec.setXRange(self.generator.SPEC_LOW_HZ,
                              self.generator.SPEC_HIGH_HZ, padding=0.01)
        style_plot(self.p_spec)
        self.curve_spec = self.p_spec.plot(
            pen=pg.mkPen((60, 60, 60), width=1),
            fillLevel=self.SPEC_Y_MIN, brush=pg.mkBrush(120, 120, 120, 60),
        )
        # Marcadores del par primario y del producto de distorsión: son las
        # 3 frecuencias que el alumno tiene que aprender a ubicar.
        self.spec_lines = {}
        for name, color in (("f1", (120, 120, 120)), ("f2", (120, 120, 120)),
                            ("2f1-f2", (192, 57, 43))):
            line = pg.InfiniteLine(
                pos=0, angle=90, pen=pg.mkPen(color, width=1, style=Qt.DashLine),
                label=name, labelOpts={"position": 0.92, "color": color},
            )
            line.setVisible(False)
            self.p_spec.addItem(line)
            self.spec_lines[name] = line

    def _build_io(self):
        self.p_io = self.glw.addPlot(
            row=1, col=1, title=black_title("Función I/O (crecimiento a f2 de mejor SNR)"))
        self.p_io.setLabel("left", "Nivel DP", units="dB SPL")
        self.p_io.setLabel("bottom", "L2", units="dB SPL")
        self.p_io.setMouseEnabled(x=False, y=False)
        self.p_io.setYRange(self.DP_Y_MIN, self.DP_Y_MAX)
        self.p_io.setXRange(float(self.generator.normative["io_l2_min_db_spl"]) - 3,
                            float(self.generator.normative["io_l2_max_db_spl"]) + 3)
        style_plot(self.p_io)
        self.p_io.addLegend(offset=(10, 10), labelTextColor="k",
                            brush=pg.mkBrush(255, 255, 255, 200),
                            pen=pg.mkPen(200, 200, 200)).setColumnCount(3)
        self.curve_io_nf = self.p_io.plot(
            pen=pg.mkPen((120, 120, 120), width=1, style=Qt.DashLine), symbol="t",
            symbolSize=5, symbolBrush=(120, 120, 120), name="NF",
            fillLevel=self.DP_Y_MIN, brush=pg.mkBrush(120, 120, 120, 45),
        )
        self.curve_io_target = self.p_io.plot(
            pen=pg.mkPen((120, 120, 120), width=1, style=Qt.DotLine), name="Objetivo",
        )
        self.curve_io_dp = self.p_io.plot(
            pen=pg.mkPen(_EAR_COLOR["OD"], width=2), symbol="o", symbolSize=7, name="DP")
        self.live_io = self.p_io.plot(
            pen=None, symbol="o", symbolSize=12, symbolBrush=None,
            symbolPen=pg.mkPen((80, 80, 80), width=2))
        # Umbral DP: L2 más bajo que todavía deja SNR sobre el criterio.
        self.io_threshold = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen((39, 174, 96), width=2),
            label="umbral DP", labelOpts={"position": 0.08, "color": (39, 174, 96)},
        )
        self.io_threshold.setVisible(False)
        self.p_io.addItem(self.io_threshold)

    # ------------------------------------------------------------------
    # Caso clínico
    # ------------------------------------------------------------------
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
        self._pending = (ear, case, self.spn_l1.value(), self.spn_l2.value())
        self.lbl_status.setText("Chequeando sonda...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.probe.start(self.spn_l2.value(), oae_probe_fit(case))
        # El probe check corre con su propio QTimer: si generamos la captura
        # en esta misma vuelta del event loop, la animación de la sonda no
        # alcanza a pintar ni un frame (mismo patrón que TEOAE).
        QTimer.singleShot(self.PROBE_CHECK_MS, self._run_capture)

    def _run_capture(self):
        if self._pending is None:
            return
        ear, case, l1, l2 = self._pending
        self._pending = None
        self.probe.stop()

        result = self.generator.generate(l1_db=l1, l2_db=l2, ear=ear, case=case)
        # La I/O se corre en el f2 que dio mejor SNR en el DP-grama: es lo
        # que hace el operador (elegir la frecuencia con respuesta para
        # estudiar el crecimiento ahí), no un f2 fijo de fábrica.
        best = max(result["points"], key=lambda p: p["snr_db"])
        io = self.generator.generate_io(f2_hz=best["f2_hz"], ear=ear, case=case)

        self._results[ear] = result
        self._io_results[ear] = io
        self._anim_ear = ear
        self._committed = []
        self._io_committed = []
        self.table.setRowCount(0)
        self._clear_ear_curves(ear)
        self.curve_io_dp.clear()
        self.curve_io_nf.clear()
        self.curve_io_target.clear()
        self.io_threshold.setVisible(False)

        # Cola de pasos: frames de cada punto + su commit, primero el
        # DP-grama y después la I/O, todo en la misma corrida.
        steps = []
        for point in result["points"]:
            for frame in point["frames"]:
                steps.append(("dp_frame", point, frame))
            steps.append(("dp_commit", point, None))
        for point in io["points"]:
            for frame in point["frames"][::self.IO_FRAME_STEP]:
                steps.append(("io_frame", point, frame))
            steps.append(("io_commit", point, None))
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
        if kind == "dp_frame":
            self._render_dp_frame(point, frame)
        elif kind == "dp_commit":
            self._commit_dp_point(point)
        elif kind == "io_frame":
            self._render_io_frame(point, frame)
        elif kind == "io_commit":
            self._commit_io_point(point)

    def _on_stop(self):
        self._pending = None
        self._anim_timer.stop()
        self.probe.stop()
        self._finish("Detenido")

    def _finish(self, status_text):
        """Cierra la corrida con lo que haya quedado medido.

        Un equipo real también entrega los puntos ya fijados si se corta
        el examen a la mitad, no descarta la captura entera.
        """
        ear = self._anim_ear
        self.btn_stop.setEnabled(False)
        self._update_case_gate()
        self.lbl_status.setText(status_text)
        for e in _EAR_COLOR:
            self.live_dp[e].clear()
            self.live_nf[e].clear()
        self.live_io.clear()
        self.cursor_f2.setVisible(False)
        for line in self.spec_lines.values():
            line.setVisible(False)
        if ear is None or not self._committed:
            return
        threshold = self.generator.normative["min_dp_above_noise_db"]
        min_pass = int(self.generator.normative["pass_points_min"])
        n_pass = sum(1 for p in self._committed if p["passed"])
        n_total = len(self._committed)
        verdict = "PASS" if n_pass >= min_pass else "REFER"
        color = "#27ae60" if verdict == "PASS" else "#c0392b"
        io = self._io_results.get(ear) or {}
        thr_txt = ""
        if self._io_committed and io.get("threshold_l2") is not None:
            measured = [p["l2_db"] for p in self._io_committed if p["passed"]]
            if measured:
                thr_txt = (f"  |  umbral DP {min(measured):.0f} dB SPL @ "
                           f"{io['f2_hz']:.0f} Hz")
        self.lbl_summary.setText(
            f"<b>{ear}</b> | <b style='color:{color}'>{verdict}</b> | "
            f"{n_pass}/{n_total} puntos pasan (criterio SNR >= {threshold} dB, "
            f"mínimo {min_pass} puntos){thr_txt}"
        )
        self._store_report(ear, n_pass, n_total, verdict, io,
                           partial=status_text == "Detenido")

    # ------------------------------------------------------------------
    # Informe
    # ------------------------------------------------------------------
    def _store_report(self, ear, n_pass, n_total, verdict, io, partial=False):
        umbral_l2 = None
        if self._io_committed:
            measured = [p["l2_db"] for p in self._io_committed if p["passed"]]
            if measured:
                umbral_l2 = float(min(measured))
        self._report[ear] = {
            "l1_db": self.spn_l1.value(),
            "l2_db": self.spn_l2.value(),
            "puntos": [
                {
                    "f2_hz": round(float(p["f2_hz"]), 0),
                    "dp_db": round(float(p["dp_db"]), 1),
                    "nf_db": round(float(p["nf_db"]), 1),
                    "snr_db": round(float(p["snr_db"]), 1),
                    "pass": bool(p["passed"]),
                }
                for p in self._committed
            ],
            "n_pass": int(n_pass),
            "n_total": int(n_total),
            "veredicto": verdict,
            "io_f2_hz": round(float(io["f2_hz"]), 0) if io.get("f2_hz") else None,
            "io_umbral_l2_db": umbral_l2,
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
    def _render_dp_frame(self, point, frame):
        ear = self._anim_ear
        self.live_dp[ear].setData([point["f2_hz"]], [frame["dp_db"]])
        self.live_nf[ear].setData([point["f2_hz"]], [frame["nf_db"]])
        self.cursor_f2.setPos(np.log10(point["f2_hz"]))
        self.cursor_f2.setVisible(True)
        self._render_spectrum(point, frame)
        n_done = len(self._committed) + 1
        self.lbl_status.setText(
            f"DP-grama {ear}: punto {n_done}/{len(self._results[ear]['points'])} "
            f"-- f2 {point['f2_hz']:.0f} Hz"
        )

    def _render_spectrum(self, point, frame):
        self.curve_spec.setData(frame["spec_freqs"], frame["spec_db"])
        for name, freq in (("f1", point["f1_hz"]), ("f2", point["f2_hz"]),
                           ("2f1-f2", point["fdp_hz"])):
            line = self.spec_lines[name]
            # p_spec va en eje lineal: la línea toma Hz directo (a diferencia
            # del cursor del DP-grama, que necesita log10).
            line.setPos(freq)
            line.setVisible(True)
        self.lbl_pair.setText(f"{point['f1_hz']:.0f} / {point['f2_hz']:.0f} Hz")
        self.lbl_fdp.setText(f"{point['fdp_hz']:.0f} Hz -- {frame['dp_db']:.1f} dB SPL")
        self.lbl_avg.setText(f"{frame['n_avg']} (SNR {frame['snr_db']:.1f} dB)")

    def _commit_dp_point(self, point):
        ear = self._anim_ear
        self._committed.append(point)
        threshold = float(self.generator.normative["min_dp_above_noise_db"])
        f2 = np.array([p["f2_hz"] for p in self._committed])
        dp = np.array([p["dp_db"] for p in self._committed])
        nf = np.array([p["nf_db"] for p in self._committed])
        self.curves_dp[ear].setData(f2, dp)
        self.curves_nf[ear].setData(f2, nf)
        self.curves_target[ear].setData(f2, nf + threshold)
        self.live_dp[ear].clear()
        self.live_nf[ear].clear()
        self._append_table_row(point)

    def _append_table_row(self, point):
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [
            f"{point['f2_hz']:.0f}",
            f"{point['dp_db']:.1f}",
            f"{point['nf_db']:.1f}",
            f"{point['snr_db']:.1f}",
            "PASS" if point["passed"] else "REFER",
        ]
        for col, text in enumerate(values):
            item = QTableWidgetItem(text)
            if col == 4:
                item.setForeground(Qt.darkGreen if point["passed"] else Qt.red)
            self.table.setItem(row, col, item)
        self.table.scrollToBottom()

    def _render_io_frame(self, point, frame):
        self.live_io.setData([point["l2_db"]], [frame["dp_db"]])
        self._render_spectrum(point, frame)
        self.lbl_status.setText(
            f"Función I/O @ {point['f2_hz']:.0f} Hz -- L1/L2 "
            f"{point['l1_db']:.0f}/{point['l2_db']:.0f} dB SPL"
        )

    def _commit_io_point(self, point):
        self._io_committed.append(point)
        threshold = float(self.generator.normative["min_dp_above_noise_db"])
        l2 = np.array([p["l2_db"] for p in self._io_committed])
        dp = np.array([p["dp_db"] for p in self._io_committed])
        nf = np.array([p["nf_db"] for p in self._io_committed])
        self.curve_io_dp.setData(l2, dp)
        self.curve_io_nf.setData(l2, nf)
        self.curve_io_target.setData(l2, nf + threshold)
        self.live_io.clear()
        passing = [p["l2_db"] for p in self._io_committed if p["passed"]]
        if passing:
            self.io_threshold.setPos(min(passing))
            self.io_threshold.setVisible(True)

    # ------------------------------------------------------------------
    def _clear_ear_curves(self, ear):
        self.curves_dp[ear].clear()
        self.curves_nf[ear].clear()
        self.curves_target[ear].clear()
        self.live_dp[ear].clear()
        self.live_nf[ear].clear()

    def _on_clear(self):
        self._anim_timer.stop()
        self.probe.stop()
        self._pending = None
        self._steps = []
        self._step_idx = 0
        self._committed = []
        self._io_committed = []
        for ear in _EAR_COLOR:
            self._clear_ear_curves(ear)
            self._results[ear] = None
            self._io_results[ear] = None
            self._report.pop(ear, None)
            self._shots.pop(ear, None)
        self.curve_io_dp.clear()
        self.curve_io_nf.clear()
        self.curve_io_target.clear()
        self.live_io.clear()
        self.io_threshold.setVisible(False)
        self.curve_spec.clear()
        self.cursor_f2.setVisible(False)
        for line in self.spec_lines.values():
            line.setVisible(False)
        self.table.setRowCount(0)
        self.lbl_pair.setText("--")
        self.lbl_fdp.setText("--")
        self.lbl_avg.setText("--")
        self.lbl_summary.setText("Pulse 'Iniciar' para correr el DP-grama.")
        self.btn_stop.setEnabled(False)
        self._update_case_gate()
        self.lbl_status.setText("Listo")
