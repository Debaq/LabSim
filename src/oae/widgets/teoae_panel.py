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

    # Chequeo de sonda antes de empezar a promediar.
    PROBE_CHECK_MS = 2400
    # Un equipo TEOAE real presenta ~50 clicks/s, así que la captura dura
    # n_sweeps/50 segundos (260 barridos ≈ 5 s). Antes la animación era fija
    # (~24 frames x 90 ms ≈ 2 s) independiente de # promedios: terminaba casi
    # al instante y no se parecía a una captura real.
    SWEEP_RATE_HZ = 50.0
    ANIM_TICK_MS = 70
    MAX_ANIM_S = 25.0
    SPEC_Y_MIN = -45.0
    SPEC_Y_MAX = 15.0
    SNR_Y_MIN = -14.0
    SNR_Y_MAX = 30.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = TeoaeGenerator()
        self._last_result = None
        self._pending = None
        self._frames = []
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
        self.p_response.setLabel("left", "Amplitud (µPa)")
        self.p_response.setLabel("bottom", "Tiempo", units="ms")
        self.p_response.setMouseEnabled(x=False, y=False)
        style_plot(self.p_response)
        self.curve_response = self.p_response.plot(pen=pg.mkPen((0, 0, 0), width=2))

        # (0,1): split buffer A/B con sus dos derivadas, como en ILO/Otoport:
        #   A, B      -> los dos promedios independientes (repro visual)
        #   A+B = (A+B)/2 -> la respuesta promediada (lo común a ambos)
        #   A-B = (A-B)/2 -> el ruido residual (la señal se cancela)
        # Ver de golpe cuánto queda en A-B contra cuánto hay en A+B es la
        # lectura clínica de si la captura sirve.
        self.p_wave = self.glw.addPlot(row=0, col=1, title=black_title("A / B"))
        self.p_wave.setLabel("bottom", "Tiempo", units="ms")
        self.p_wave.setMouseEnabled(x=False, y=False)
        style_plot(self.p_wave)
        # Apilados, no superpuestos: cada trazo va con su propio offset
        # vertical y el eje izquierdo rotula cuál es cada uno (los valores en
        # µPa no sirven de rótulo acá porque cada fila está desplazada).
        self.curve_a = self.p_wave.plot(pen=pg.mkPen((192, 57, 43), width=1))
        self.curve_b = self.p_wave.plot(
            pen=pg.mkPen((41, 128, 185), width=1, style=Qt.DashLine))
        self.curve_sum = self.p_wave.plot(pen=pg.mkPen((0, 0, 0), width=2))
        self.curve_diff = self.p_wave.plot(pen=pg.mkPen((130, 130, 130), width=1))
        # Fila (de arriba a abajo) de cada trazo y su rótulo.
        self._wave_rows = [
            (self.curve_a, 3, "A"),
            (self.curve_b, 2, "B"),
            (self.curve_sum, 1, "A+B"),
            (self.curve_diff, 0, "A-B"),
        ]
        # Línea de cero de cada fila, para leer la amplitud de cada trazo.
        self._wave_baselines = []
        for _curve, row, _name in self._wave_rows:
            base = pg.InfiniteLine(pos=0, angle=0,
                                   pen=pg.mkPen((200, 200, 200), width=1))
            base.setZValue(-10)
            self.p_wave.addItem(base)
            self._wave_baselines.append((base, row))
        self._wave_step = None

        # (0,2): Fourier -- espectro FFT de la respuesta + piso de ruido (A-B)
        self.p_spec = self.glw.addPlot(row=0, col=2, title=black_title("Fourier"))
        self.p_spec.setLabel("left", "Nivel", units="dB SPL")
        # Sin units="Hz": con logMode pyqtgraph reescala el rótulo a kHz pero
        # los ticks los ponemos nosotros en Hz -> quedaría "1k" bajo "(kHz)".
        self.p_spec.setLabel("bottom", "Frecuencia (Hz)")
        self.p_spec.setMouseEnabled(x=False, y=False)
        self.p_spec.setLogMode(x=True, y=False)
        style_plot(self.p_spec)
        # Ruido primero para que quede DEBAJO de la respuesta al superponerse.
        self.curve_noise = self.p_spec.plot(
            pen=pg.mkPen((150, 150, 150), width=1),
            fillLevel=self.SPEC_Y_MIN,
            brush=(150, 150, 150, 60),
        )
        self.curve_spec = self.p_spec.plot(pen=pg.mkPen((0, 0, 0), width=1))
        lo_hz = self.generator.normative["spectrum_low_hz"]
        hi_hz = self.generator.normative["spectrum_high_hz"]
        self.p_spec.setXRange(np.log10(lo_hz), np.log10(hi_hz), padding=0.02)
        self.p_spec.setYRange(self.SPEC_Y_MIN, self.SPEC_Y_MAX)
        # Con logMode el eje rotula 10^x: ilegible para un alumno. Ticks
        # explícitos en las frecuencias clínicas (coordenadas en log10).
        # Solo octavas: en log y con el plot angosto, 3000/4000/5000 se pisan
        # entre sí y el eje queda ilegible.
        ticks = [hz for hz in (250, 500, 1000, 2000, 4000, 8000)
                 if lo_hz <= hz <= hi_hz]
        self.p_spec.getAxis("bottom").setTicks([
            [(np.log10(hz), str(hz)) for hz in ticks]
        ])
        # Centros de las bandas analizadas. Van como líneas y no como regiones
        # sombreadas porque las bandas normativas son de una octava y se
        # solapan entre sí (1k..4k con ratio 0.707): sombrearlas pinta el
        # gráfico entero de azul y no se distingue ninguna.
        # Nota: p_spec está en logMode x=True -- curve_spec se autotransforma a
        # log10 (PlotDataItem), pero InfiniteLine/LinearRegionItem NO, y toman
        # sus coordenadas tal cual; hay que pasarles log10(Hz) o desbordan el
        # ViewBox y aplastan la curva contra el borde.
        for band_hz in self.generator.normative["bands_hz"]:
            line = pg.InfiniteLine(
                pos=np.log10(band_hz),
                angle=90,
                pen=pg.mkPen((41, 128, 185, 110), width=1, style=Qt.DashLine),
                movable=False,
            )
            line.setZValue(-10)
            self.p_spec.addItem(line)

        # (1, 0-1): SNR por banda
        self.p_snr = self.glw.addPlot(row=1, col=0, colspan=2, title=black_title("SNR por banda (umbral 6 dB)"))
        self.p_snr.setLabel("left", "SNR", units="dB")
        self.p_snr.setLabel("bottom", "Frecuencia", units="Hz")
        self.p_snr.setMouseEnabled(x=False, y=False)
        self.p_snr.setYRange(self.SNR_Y_MIN, self.SNR_Y_MAX)
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

    def _on_start(self):
        ear, case = self._current_case()
        if case is None:
            return
        self._pending = (ear, case, self.spn_level.value(), self.spn_n.value())
        self.lbl_status.setText("Chequeando sonda...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.probe.start(self.spn_level.value())
        # Chequeo de sonda animado real (QTimer del probe) antes de generar
        # la captura -- generate() es síncrono y bloquea el loop de eventos,
        # así que si se llama en la misma vuelta el timer del probe nunca
        # pinta un frame (la animación no se ve).
        QTimer.singleShot(self.PROBE_CHECK_MS, self._run_capture)

    def _run_capture(self):
        if self._pending is None:
            return
        ear, case, level, n = self._pending
        self._pending = None
        self.probe.stop()
        # Duración = # barridos / tasa de clicks, con tope para no dejar al
        # alumno mirando 40 s con 2000 promedios.
        duration_s = min(n / self.SWEEP_RATE_HZ, self.MAX_ANIM_S)
        n_frames = int(np.clip(duration_s * 1000 / self.ANIM_TICK_MS, 8, 400))
        result = self.generator.generate(
            level_db=level, n_sweeps=n, ear=ear, case=case, n_frames=n_frames
        )
        self._last_result = result
        self._anim_ear = ear
        self._frames = result["frames"]
        self._anim_idx = 0
        self._wave_step = None
        self._anim_timer.start(self.ANIM_TICK_MS)
        self._anim_tick()

    def _anim_tick(self):
        if self._anim_idx >= len(self._frames):
            self._anim_timer.stop()
            self._finish_capture(self._frames[-1] if self._frames else None,
                                 "Captura completa")
            return
        frame = self._frames[self._anim_idx]
        # Se actualizan TODOS los gráficos en cada frame (no solo la
        # respuesta): en el equipo real el espectro, el A/B, las barras de
        # SNR y las métricas se van armando durante la captura.
        self._render_frame(frame)
        self.text_pass.setText("...")
        self.text_pass.setColor((120, 120, 120))
        self.text_detail.setText(
            f"{self._anim_ear}  |  {frame['n_pass']}/{self._last_result['n_bands']} bandas"
        )
        self.lbl_status.setText(
            f"Promediando barridos: {frame['n_sweeps']}/"
            f"{self._last_result['n_sweeps_total']}..."
        )
        self._anim_idx += 1

    def _finish_capture(self, frame, status_text):
        """Cierra la captura mostrando el resultado del último frame pintado.

        Vale tanto para el final normal como para 'Detener': un equipo real
        también entrega el promedio parcial acumulado hasta el momento en que
        se corta, no descarta la captura.
        """
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText(status_text)
        if frame is None:
            return
        self._render_frame(frame)
        self._render_verdict(frame, self._anim_ear)

    def _on_stop(self):
        was_running = self._anim_timer.isActive()
        self._pending = None
        self._anim_timer.stop()
        self.probe.stop()
        frame = None
        if was_running and self._anim_idx > 0:
            frame = self._frames[self._anim_idx - 1]
            self._last_result = dict(self._last_result or {}, **frame)
        self._finish_capture(frame, "Detenido")

    def _on_clear(self):
        self._anim_timer.stop()
        self._frames = []
        self._anim_idx = 0
        self.curve_response.clear()
        for curve, _row, _name in self._wave_rows:
            curve.clear()
        self._wave_step = None
        self.curve_spec.clear()
        self.curve_noise.clear()
        self.bars_snr.setOpts(x=[], height=[], width=0.15)
        self.text_pass.setText("")
        self.text_detail.setText("")
        self.lbl_repro.setText("--")
        self.lbl_stability.setText("--")
        self.lbl_response.setText("--")
        self._last_result = None
        self.lbl_status.setText("Listo")

    def _render_frame(self, frame: dict):
        """Pinta un promedio parcial (o final): ondas, espectro, SNR y métricas.

        No toca el cartel PASS/REFER -- ese lo pone _render_verdict al cerrar
        la captura, porque durante el promediado el veredicto todavía no está
        tomado."""
        # Escalar a µPa (1 Pa = 1e6 µPa) para visualización
        t = self._last_result["time_ms"]
        a = frame["wave_a"] * 1e6
        b = frame["wave_b"] * 1e6
        self.curve_response.setData(t, frame["waveform"] * 1e6)
        self._render_stack(t, {"A": a, "B": b,
                               "A+B": (a + b) / 2, "A-B": (a - b) / 2})
        # Espectro de respuesta + piso de ruido estimado por A-B (el equipo
        # real muestra las dos: la banda gris de ruido es lo que permite leer
        # de un vistazo cuánta emisión hay por sobre el ruido).
        freqs = self._last_result["freqs"]
        self.curve_spec.setData(freqs, frame["spectrum_db"])
        self.curve_noise.setData(freqs, np.maximum(frame["noise_db"], self.SPEC_Y_MIN))
        # SNR bars
        snr = frame["snr_per_band"]
        centers = np.array(list(snr.keys()), dtype=float)
        heights = list(snr.values())
        brushes = [
            (39, 174, 96) if frame["pass_per_band"][c] else (192, 57, 43)
            for c in snr
        ]
        self.bars_snr.setOpts(x=centers, height=heights,
                              width=0.12 * centers, brushes=brushes)
        self.p_snr.setXRange(centers.min() * 0.7, centers.max() * 1.4)
        # Métricas de captura
        repro = frame["reproducibility_pct"]
        min_repro = self.generator.normative["min_reproducibility_pct"]
        self.lbl_repro.setText(f"{repro:.0f}%")
        self.lbl_repro.setStyleSheet(
            f"color: {'#27ae60' if repro >= min_repro else '#c0392b'};"
        )
        stability = frame["stability_pct"]
        min_stability = self.generator.normative["min_stability_pct"]
        self.lbl_stability.setText(f"{stability:.0f}%")
        self.lbl_stability.setStyleSheet(
            f"color: {'#27ae60' if stability >= min_stability else '#c0392b'};"
        )
        snr_total = frame["total_response_db"] - frame["total_noise_db"]
        self.lbl_response.setText(
            f"{frame['total_response_db']:.1f} / {frame['total_noise_db']:.1f} dB SPL "
            f"(SNR {snr_total:.1f} dB)"
        )

    def _render_stack(self, t, traces: dict):
        """Dibuja A, B, A+B y A-B apilados con offset vertical."""
        amp = float(np.percentile(np.abs(np.concatenate([traces["A"],
                                                         traces["B"]])), 99))
        step = max(amp * 2.4, 1.0)
        # El ruido baja durante la captura, así que el offset tiene que
        # seguirlo o al final los trazos quedan pegados al piso de su fila.
        # Solo se reescala ante cambios grandes: si se recalculara en cada
        # frame el eje bailaría todo el rato.
        if self._wave_step is None or abs(step - self._wave_step) > 0.2 * self._wave_step:
            self._wave_step = step
            self.p_wave.getAxis("left").setTicks([
                [(row * step, name) for _c, row, name in self._wave_rows]
            ])
            self.p_wave.setYRange(-0.7 * step, 3.7 * step, padding=0)
            for base, row in self._wave_baselines:
                base.setPos(row * step)
        step = self._wave_step
        for curve, row, name in self._wave_rows:
            curve.setData(t, traces[name] + row * step)

    def _render_verdict(self, frame: dict, ear: str):
        if frame["overall_pass"]:
            self.text_pass.setText("PASS")
            self.text_pass.setColor((39, 174, 96))
        else:
            self.text_pass.setText("REFER")
            self.text_pass.setColor((192, 57, 43))
        self.text_detail.setText(
            f"{ear}  |  {frame['n_pass']}/{self._last_result['n_bands']} bandas pasan"
            f"  |  {frame['n_sweeps']} barridos"
        )
