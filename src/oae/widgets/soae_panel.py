"""Panel SOAE - emisiones otoacústicas espontáneas.

Reproduce la pantalla de un registro SOAE real: la sonda en el conducto en
SILENCIO (no hay estímulo, por eso no hay control de nivel) y un espectro
que se va promediando. Lo que el alumno tiene que ver es el mecanismo:
al promediar, el ruido deja de fluctuar (su nivel medio no baja, pero sí
su dispersión) mientras los picos espontáneos se quedan quietos, así que
los SOAE emergen y los picos espurios de los primeros segundos
desaparecen.

Criterio de detección (el del equipo, no "el pico más alto"): >= 3 dB
sobre el piso local Y reproducible en las dos mitades independientes del
registro -- el gráfico de detalle A/B de abajo es justamente esa lectura.
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
from oae.generators.soae import SoaeGenerator
from oae.widgets.probe_check import ProbeCheckWidget
from oae.widgets.plot_style import style_plot, black_title


class SoaePanel(QWidget):
    """Tab SOAE del módulo OAE clínico."""

    PROBE_CHECK_MS = 2000
    ANIM_TICK_MS = 110
    SPEC_Y_MIN = -25.0
    SPEC_Y_MAX = 25.0
    # Ancho de la ventana de zoom del gráfico de detalle A/B.
    DETAIL_HALFWIDTH_HZ = 60.0
    # Banda donde se mide el piso "de trabajo" que se informa al alumno
    # (los graves están siempre sucios y no definen la calidad del registro).
    FLOOR_BAND_HZ = (1000.0, 4000.0)
    MAX_PEAK_LABELS = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = SoaeGenerator()
        self.case_od = None
        self.case_oi = None
        self._result = None
        self._pending = None
        self._frames = []
        self._anim_idx = 0
        self._anim_ear = None
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
        self.spn_record = QDoubleSpinBox()
        self.spn_record.setRange(float(self.generator.normative["min_record_s"]),
                                 float(self.generator.normative["max_record_s"]))
        self.spn_record.setSingleStep(5.0)
        self.spn_record.setValue(float(self.generator.normative["default_record_s"]))
        self.spn_record.setSuffix(" s")
        form.addRow("Duración registro:", self.spn_record)
        # Sin nivel de estímulo: el registro es en silencio. Se muestra el
        # criterio para que el alumno sepa contra qué se está comparando.
        self.lbl_criterion = QLabel(
            f"≥ {self.generator.normative['min_snr_db']:.0f} dB sobre piso "
            f"local + A/B"
        )
        self.lbl_criterion.setWordWrap(True)
        form.addRow("Criterio:", self.lbl_criterion)
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

        metrics = QGroupBox("Registro")
        metrics_form = QFormLayout(metrics)
        self.lbl_elapsed = QLabel("--")
        metrics_form.addRow("Tiempo promediado:", self.lbl_elapsed)
        self.lbl_avg = QLabel("--")
        metrics_form.addRow("Promedios:", self.lbl_avg)
        self.lbl_floor = QLabel("--")
        metrics_form.addRow("Piso 1-4 kHz:", self.lbl_floor)
        self.lbl_resolution = QLabel("--")
        metrics_form.addRow("Resolución FFT:", self.lbl_resolution)
        left_layout.addWidget(metrics)

        # Tabla de picos: es el informe SOAE de un equipo real (frecuencia
        # con decimales, nivel de la emisión, piso y SNR por pico).
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Frec (Hz)", "Nivel (dB SPL)", "Piso (dB)", "SNR (dB)"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.table, stretch=1)

        # ---------- DERECHA ----------
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground((255, 255, 255))
        self._build_spectrum()
        self._build_detail()

        self.lbl_summary = QLabel("Pulse 'Iniciar' para registrar en silencio.")
        self.lbl_summary.setWordWrap(True)
        self.lbl_note = QLabel(
            "La ausencia de SOAE NO es patológica por sí sola: solo ~40-50% de "
            "los oídos normales los presentan. Su PRESENCIA sí indica células "
            "ciliadas externas funcionantes y umbrales mejores a ~30 dB HL en "
            "esa zona frecuencial."
        )
        self.lbl_note.setWordWrap(True)
        self.lbl_note.setStyleSheet("color: #555555;")

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.addWidget(self.glw, stretch=1)
        right_layout.addWidget(self.lbl_summary)
        right_layout.addWidget(self.lbl_note)

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

    def _build_spectrum(self):
        self.p_spec = self.glw.addPlot(
            row=0, col=0, title=black_title("Espectro del conducto (sin estímulo)"))
        self.p_spec.setLabel("left", "Nivel", units="dB SPL")
        # Sin units: en logMode pyqtgraph reescalaría el rótulo a kHz y los
        # ticks los ponemos nosotros en Hz (mismo motivo que en TEOAE).
        self.p_spec.setLabel("bottom", "Frecuencia (Hz)")
        self.p_spec.setMouseEnabled(x=False, y=False)
        self.p_spec.setLogMode(x=True, y=False)
        style_plot(self.p_spec)
        lo = float(self.generator.normative["spectrum_low_hz"])
        hi = float(self.generator.normative["spectrum_high_hz"])
        self.p_spec.setXRange(np.log10(lo), np.log10(hi), padding=0.02)
        self.p_spec.setYRange(self.SPEC_Y_MIN, self.SPEC_Y_MAX)
        ticks = [hz for hz in (500, 1000, 2000, 4000, 8000) if lo <= hz <= hi]
        self.p_spec.getAxis("bottom").setTicks(
            [[(np.log10(hz), str(hz)) for hz in ticks]])

        # Piso local primero para que quede DEBAJO del espectro.
        self.curve_floor = self.p_spec.plot(
            pen=pg.mkPen((150, 150, 150), width=1),
            fillLevel=self.SPEC_Y_MIN, brush=(150, 150, 150, 60))
        self.curve_criterion = self.p_spec.plot(
            pen=pg.mkPen((192, 57, 43), width=1, style=Qt.DashLine))
        self.curve_spec = self.p_spec.plot(pen=pg.mkPen((0, 0, 0), width=1))
        self.peak_marks = pg.ScatterPlotItem(
            symbol="t1", size=11, brush=(39, 174, 96), pen=pg.mkPen((0, 90, 40)))
        self.p_spec.addItem(self.peak_marks)
        # Pool fijo de etiquetas: crear/destruir TextItems en cada frame de
        # la animación deja items huérfanos en la escena.
        label_font = QFont()
        label_font.setPixelSize(10)
        self.peak_labels = []
        for _ in range(self.MAX_PEAK_LABELS):
            text = pg.TextItem(anchor=(0.5, 1.0), color=(39, 174, 96))
            text.setFont(label_font)
            text.setVisible(False)
            self.p_spec.addItem(text)
            self.peak_labels.append(text)

    def _build_detail(self):
        self.p_detail = self.glw.addPlot(
            row=1, col=0,
            title=black_title("Detalle del pico más fuerte -- mitades A / B del registro"))
        self.p_detail.setLabel("left", "Nivel", units="dB SPL")
        self.p_detail.setLabel("bottom", "Frecuencia", units="Hz")
        self.p_detail.setMouseEnabled(x=False, y=False)
        style_plot(self.p_detail)
        self.curve_a = self.p_detail.plot(
            pen=pg.mkPen((192, 57, 43), width=1), name="A")
        self.curve_b = self.p_detail.plot(
            pen=pg.mkPen((41, 128, 185), width=1, style=Qt.DashLine), name="B")
        self.curve_detail_floor = self.p_detail.plot(
            pen=pg.mkPen((150, 150, 150), width=1))
        legend = self.p_detail.addLegend(offset=(-10, 10),
                                         labelTextColor=(0, 0, 0))
        legend.addItem(self.curve_a, "A (1ª mitad)")
        legend.addItem(self.curve_b, "B (2ª mitad)")
        legend.addItem(self.curve_detail_floor, "piso local")
        self.glw.ci.layout.setRowStretchFactor(0, 3)
        self.glw.ci.layout.setRowStretchFactor(1, 2)

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
        self._pending = (ear, case, self.spn_record.value())
        self.lbl_status.setText("Chequeando sonda...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        # El nivel que se le pasa al probe check es solo el del click de
        # chequeo de sello: el registro SOAE en sí es en silencio.
        self.probe.start(60.0, oae_probe_fit(case))
        QTimer.singleShot(self.PROBE_CHECK_MS, self._run_capture)

    def _run_capture(self):
        if self._pending is None:
            return
        ear, case, record_s = self._pending
        self._pending = None
        self.probe.stop()
        self._result = self.generator.generate(ear=ear, case=case, record_s=record_s)
        # El eje se ajusta al piso esperado de ESTE oído: con un paciente
        # ruidoso todo el registro sube 10-15 dB y con rango fijo los picos
        # se salían del gráfico (o quedaban aplastados contra el borde).
        floor = self._result["expected_floor_db"]
        self.p_spec.setYRange(float(floor.min()) - 10.0,
                              float(floor.max()) + 18.0, padding=0)
        self._frames = self._result["frames"]
        self._anim_ear = ear
        self._anim_idx = 0
        self.lbl_resolution.setText(f"{self._result['bin_width_hz']:.1f} Hz/bin")
        self._anim_timer.start(self.ANIM_TICK_MS)
        self._anim_tick()

    def _anim_tick(self):
        if self._anim_idx >= len(self._frames):
            self._anim_timer.stop()
            self._finish(self._frames[-1] if self._frames else None,
                         "Registro completo")
            return
        frame = self._frames[self._anim_idx]
        self._render_frame(frame)
        self.lbl_status.setText(
            f"Registrando: {frame['elapsed_s']:.1f} / "
            f"{self._result['record_s']:.0f} s..."
        )
        self.lbl_summary.setText(
            f"{self._anim_ear}  |  promediando -- el ruido se aplana y los "
            f"picos que no son SOAE dejan de cumplir criterio "
            f"({len(frame['peaks'])} sobre criterio en este instante)."
        )
        self._anim_idx += 1

    def _on_stop(self):
        was_running = self._anim_timer.isActive()
        self._pending = None
        self._anim_timer.stop()
        self.probe.stop()
        frame = None
        if was_running and self._anim_idx > 0:
            frame = self._frames[self._anim_idx - 1]
        self._finish(frame, "Detenido", partial=True)

    def _finish(self, frame, status_text, partial: bool = False):
        """Cierra el registro con lo acumulado hasta ese momento.

        Igual que TEOAE/DPOAE: si se corta a la mitad se informa el
        promedio parcial, pero acá además se avisa que un registro corto
        no alcanza para descartar SOAE (el piso todavía está alto).
        """
        self.btn_stop.setEnabled(False)
        self._update_case_gate()
        self.lbl_status.setText(status_text)
        if frame is None:
            return
        self._render_frame(frame)
        self._render_verdict(frame, partial)

    def _on_clear(self):
        self._anim_timer.stop()
        self.probe.stop()
        self._frames = []
        self._anim_idx = 0
        self._result = None
        self.curve_spec.clear()
        self.curve_floor.clear()
        self.curve_criterion.clear()
        self.curve_a.clear()
        self.curve_b.clear()
        self.curve_detail_floor.clear()
        self.peak_marks.setData([], [])
        for label in self.peak_labels:
            label.setVisible(False)
        self.table.setRowCount(0)
        self.lbl_elapsed.setText("--")
        self.lbl_avg.setText("--")
        self.lbl_floor.setText("--")
        self.lbl_resolution.setText("--")
        self.lbl_summary.setText("Pulse 'Iniciar' para registrar en silencio.")
        self.lbl_status.setText("Listo")
        self._update_case_gate()

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def _mean_floor_db(self, frame) -> float:
        """Piso medio en la banda de trabajo (1-4 kHz)."""
        freqs = self._result["freqs"]
        lo, hi = self.FLOOR_BAND_HZ
        mask = (freqs >= lo) & (freqs <= hi)
        return float(np.mean(frame["floor_db"][mask]))

    def _render_frame(self, frame):
        freqs = self._result["freqs"]
        min_snr = float(self.generator.normative["min_snr_db"])
        # OJO: p_spec está en logMode x=True. Los PlotDataItem se
        # autotransforman (van en Hz), pero ScatterPlotItem y TextItem no
        # -- a esos hay que pasarles log10(Hz) a mano (mismo detalle que
        # las líneas de banda de TEOAE).
        self.curve_spec.setData(freqs, frame["spec_db"])
        self.curve_floor.setData(freqs, np.maximum(frame["floor_db"], self.SPEC_Y_MIN))
        self.curve_criterion.setData(freqs, frame["floor_db"] + min_snr)

        peaks = frame["peaks"]
        self.peak_marks.setData(
            [np.log10(p["freq_hz"]) for p in peaks],
            [p["bin_level_db_spl"] + 2.0 for p in peaks],
        )
        strongest = sorted(peaks, key=lambda p: -p["snr_db"])[:self.MAX_PEAK_LABELS]
        strongest.sort(key=lambda p: p["freq_hz"])
        for i, (label, peak) in enumerate(zip(self.peak_labels, strongest)):
            label.setText(f"{peak['freq_hz']:.0f} Hz\n{peak['level_db_spl']:.1f} dB")
            # Dos SOAE vecinos pueden estar a 100 Hz: las etiquetas se
            # alternan en altura para no pisarse.
            label.setPos(np.log10(peak["freq_hz"]),
                         peak["bin_level_db_spl"] + (3.5 if i % 2 == 0 else 9.5))
            label.setVisible(True)
        for label in self.peak_labels[len(strongest):]:
            label.setVisible(False)

        self._render_detail(frame, peaks)
        self._render_table(peaks)
        self.lbl_elapsed.setText(f"{frame['elapsed_s']:.1f} s")
        self.lbl_avg.setText(str(frame["n_avg"]))
        floor = self._mean_floor_db(frame)
        noisy = floor > float(self.generator.normative["valid_floor_max_db_spl"])
        self.lbl_floor.setText(f"{floor:.1f} dB SPL")
        self.lbl_floor.setStyleSheet(f"color: {'#c0392b' if noisy else '#27ae60'};")

    def _render_detail(self, frame, peaks):
        """Zoom A/B alrededor del pico más fuerte (o del centro de la zona
        SOAE si todavía no hay ninguno): es donde se ve si el pico se
        repite en las dos mitades o si fue ruido de una sola."""
        freqs = self._result["freqs"]
        if peaks:
            center = max(peaks, key=lambda p: p["snr_db"])["freq_hz"]
            self.p_detail.setTitle(black_title(
                f"Detalle {center:.0f} Hz -- mitades A / B del registro"))
        else:
            # Sin picos el zoom se queda en la zona donde más SOAE aparecen,
            # y el título lo dice para que no se lea como un pico real.
            center = float(self.generator.normative["peak_freq_center_hz"])
            self.p_detail.setTitle(black_title(
                f"Zona de búsqueda {center:.0f} Hz -- sin pico sobre criterio"))
        mask = np.abs(freqs - center) <= self.DETAIL_HALFWIDTH_HZ
        if not mask.any():
            return
        self.curve_a.setData(freqs[mask], frame["spec_a_db"][mask])
        self.curve_b.setData(freqs[mask], frame["spec_b_db"][mask])
        self.curve_detail_floor.setData(freqs[mask], frame["floor_db"][mask])
        self.p_detail.setXRange(center - self.DETAIL_HALFWIDTH_HZ,
                                center + self.DETAIL_HALFWIDTH_HZ, padding=0)

    def _render_table(self, peaks):
        self.table.setRowCount(len(peaks))
        for row, peak in enumerate(peaks):
            values = [
                f"{peak['freq_hz']:.1f}",
                f"{peak['level_db_spl']:.1f}",
                f"{peak['floor_db_spl']:.1f}",
                f"{peak['snr_db']:.1f}",
            ]
            for col, text in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(text))

    def _render_verdict(self, frame, partial: bool = False):
        ear = self._anim_ear
        # Un registro cortado a la mitad todavía tiene ruido fluctuando:
        # ahí un pico de 3-4 dB puede ser ruido, no un SOAE.
        aviso = ("  Registro incompleto: repetir los "
                 f"{self._result['record_s']:.0f} s completos antes de "
                 "informar." if partial else "")
        peaks = frame["peaks"]
        floor = self._mean_floor_db(frame)
        noisy = floor > float(self.generator.normative["valid_floor_max_db_spl"])
        if peaks:
            freqs_txt = ", ".join(f"{p['freq_hz']:.0f} Hz ({p['level_db_spl']:.1f} dB SPL"
                                  f", SNR {p['snr_db']:.1f} dB)" for p in peaks)
            self.lbl_summary.setText(
                f"{ear}  |  SOAE PRESENTES -- {len(peaks)} pico(s): "
                f"{freqs_txt}.{aviso}"
            )
            self.lbl_summary.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif noisy:
            # Distinguir "no hay SOAE" de "no se pueden ver": es el error
            # clínico clásico al leer un registro ruidoso.
            self.lbl_summary.setText(
                f"{ear}  |  REGISTRO NO CONCLUYENTE -- piso de ruido alto "
                f"({floor:.1f} dB SPL en 1-4 kHz). Repetir con el paciente "
                f"quieto / mejor sello antes de informar ausencia.{aviso}"
            )
            self.lbl_summary.setStyleSheet("color: #c0392b; font-weight: bold;")
        else:
            self.lbl_summary.setText(
                f"{ear}  |  SIN SOAE DETECTADAS en {frame['elapsed_s']:.0f} s de "
                f"registro (piso {floor:.1f} dB SPL, criterio "
                f"{self.generator.normative['min_snr_db']:.0f} dB). La ausencia "
                f"aislada no es diagnóstica: hay que leerla junto a TEOAE/DPOAE "
                f"de este oído.{aviso}"
            )
            self.lbl_summary.setStyleSheet("color: #444444; font-weight: bold;")
