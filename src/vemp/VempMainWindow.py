"""
VempMainWindow - Orquestador MDI del módulo VEMP.

Mismo ciclo que AbrMainWindow: sin cronómetro propio, reacciona a la
atención abierta en LabSim vía la_super(data_current, appointment_id), y el
alumno promedia con el botón del panel de control. Cada paciente trae su
definición en cases.data['VEMP']['OD'/'OI'] (ver CaseForm::parseVemp).

Lo que cambió respecto de la primera versión, y por qué:

- El examen ES MONOAURAL. Antes cada captura generaba las dos curvas (OD y
  OI) a la vez con la misma intensidad; eso no es un VEMP. Ahora se
  registra el oído del panel de control, uno por vez.
- La curva CRECE MIENTRAS SE PROMEDIA. Antes el timer contaba ticks sin
  dibujar nada y al terminar aparecía la curva final: la promediación no se
  veía y daba lo mismo pedir 60 barridos que 600.
- Se PUEDEN MARCAR LOS PICOS. Antes la tabla emitía una señal que no hacía
  nada (`_on_request_value` era un `pass`), así que no había manera de
  medir, ni de llenar la lat-int, ni de informar amplitudes.
- El caso se lee con el SHAPE NUEVO (cases.data['VEMP'][lado]['subtipos']
  [subtipo]), con compatibilidad hacia los casos viejos -- ver
  VEMP_generator_v1.case_for_subtipo.
- El SUBTIPO NO SE PRESELECCIONA desde el caso. Elegir qué VEMP corresponde
  es la decisión clínica del examen y la toma el alumno; el caso trae los
  tres armados justamente para que pueda elegir mal.
"""

import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMainWindow, QTabWidget,
                               QVBoxLayout, QWidget)

from backend.client import BackendClient
from core.base import context
from core.helpers import Preferences
from vemp.VempControl import VempControl, SUBTIPO_LABELS
from vemp.VempEmg import VempEmg
from vemp.VempGraph import VempGraph
from vemp.VempLatIntGraph import VempLatIntGraph
from vemp.VempReport import VempReport
from vemp.VempTable import VempTable
from vemp.VEMP_generator_v1 import (SUBTIPO_PEAKS, SUBTIPOS, VEMP_Curve,
                                    VEMPGeneratorV1, case_for_subtipo,
                                    emg_de_maniobra, select_population)

# Un tick de promediación (ms). Mismo valor que el ABR: es el ritmo al que
# la curva se ve crecer.
TIEMPO_ENTR_PROM = 300
# Refresco del monitor de EMG: corre siempre que haya paciente, promediando
# o no -- ahí se ve si el paciente está contrayendo antes de gastar
# barridos en descubrirlo.
TIEMPO_EMG = 300


class VempMainWindow(QMainWindow):
    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.setWindowTitle('VEMP')
        self.data_current = None
        self.appointment_id = None
        # None = sin datos reales para ese oído (sin atención, o paciente sin
        # VEMP configurado). Sin datos no se genera nada, ni un ejemplo
        # sintético: graph() corta antes.
        self.vemp_od = None
        self.vemp_oi = None
        self.subtipo = 'CVEMP'

        # Estado de captura
        self.state_capture = 'stopped'
        self.current_setting = {}
        self.current_capture_curve = ''
        self.curves_R = []
        self.curves_L = []
        self.count_averages = 0
        self.total_averages = 20
        self.done = False
        self.memory = {}
        self.last_metadata = {}
        # Última lectura de los cursores por oído (la usa la tabla al pedir
        # un valor).
        self.current_measuring = [None, None]

        # La normativa se lee una vez: baseline_actual() la consulta cada
        # vez que cambia el subtipo o la pestaña.
        self._generador = None

        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self.capture)
        self.emg_timer = QTimer(self)
        self.emg_timer.timeout.connect(self.refresh_emg)

        self._build_ui()
        self._connect()
        self.control.setEnabled(False)
        self.apply_subtipo(self.control.get_subtipo())

    # =====================================================================
    # UI
    # =====================================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # --- Izquierda: control del equipo + monitor de EMG ---------------
        self.control = VempControl()
        self.emg = VempEmg()
        izquierda = QVBoxLayout()
        izquierda.addWidget(self.control)
        izquierda.addWidget(self.emg)
        izquierda.addStretch(1)
        panel_izq = QWidget()
        panel_izq.setLayout(izquierda)
        panel_izq.setFixedWidth(320)
        root.addWidget(panel_izq)

        # --- Centro: pestañas + línea de estado ---------------------------
        self.tabs = QTabWidget()

        self.graph_r = VempGraph(side=0, subtipo=self.subtipo)
        self.graph_l = VempGraph(side=1, subtipo=self.subtipo)
        graficos = QHBoxLayout()
        graficos.addWidget(self.graph_r)
        graficos.addWidget(self.graph_l)
        tab_graficos = QWidget()
        tab_graficos.setLayout(graficos)
        self.tabs.addTab(tab_graficos, 'Curvas')

        self.lat_int = VempLatIntGraph(peak_labels=SUBTIPO_PEAKS[self.subtipo])
        self.tabs.addTab(self.lat_int, 'Lat-Int / Amplitud')

        self.report = VempReport()
        if self.data_login.get('name'):
            self.report.set_le_eva(self.data_login['name'])
        self.tabs.addTab(self.report, 'Informe')

        self.lbl_info = QLabel('')
        centro = QVBoxLayout()
        centro.addWidget(self.tabs, 1)
        centro.addWidget(self.lbl_info)
        panel_centro = QWidget()
        panel_centro.setLayout(centro)
        root.addWidget(panel_centro, 1)

        # --- Derecha: tablas por oído -------------------------------------
        self.table_r = VempTable(side=0, peak_labels=SUBTIPO_PEAKS[self.subtipo])
        self.table_l = VempTable(side=1, peak_labels=SUBTIPO_PEAKS[self.subtipo])
        derecha = QVBoxLayout()
        derecha.addWidget(self.table_r)
        derecha.addWidget(self.table_l)
        derecha.addStretch(1)
        panel_der = QWidget()
        panel_der.setLayout(derecha)
        panel_der.setFixedWidth(280)
        root.addWidget(panel_der)

    def _connect(self):
        self.control.capture.connect(self.capture_state)
        self.control.sig_subtipo.connect(self.apply_subtipo)
        self.control.sig_maniobra.connect(lambda *_: self.refresh_emg())
        self.tabs.currentChanged.connect(self.tab_change)

        for grafico in (self.graph_r, self.graph_l):
            grafico.sig_data_info.connect(self.measure_data)
            grafico.sig_change_value_mark.connect(self.update_memory_from_graph_mark)
            grafico.sig_curve_selected.connect(self.curve_selected)
            grafico.sig_del_curve.connect(self.update_delete_curve)
        self.table_r.sig_measure_value.connect(self.measure_action)
        self.table_l.sig_measure_value.connect(self.measure_action)

    # =====================================================================
    # la_super / reset (API que llama main.py)
    # =====================================================================

    def la_super(self, data, appointment_id=None):
        """Recibe el caso del paciente en atención (o None al cerrarla)."""
        self.data_current = data
        self.appointment_id = appointment_id
        self.control.setEnabled(data is not None)
        vemp_data = (data or {}).get('VEMP') or {}
        self.vemp_od = vemp_data.get('OD')
        self.vemp_oi = vemp_data.get('OI')
        self.reset()
        self.apply_subtipo(self.control.get_subtipo())
        if data is None:
            self.emg_timer.stop()
            self.emg.clear_trace()
        else:
            self.emg_timer.start(TIEMPO_EMG)

    def reset(self):
        self.curves_R = []
        self.curves_L = []
        self.memory = {}
        self.count_averages = 0
        self.current_capture_curve = ''
        self.last_metadata = {}
        self.current_measuring = [None, None]
        self.graph_r.limpiar_todo()
        self.graph_l.limpiar_todo()
        self.table_r.clear_all()
        self.table_l.clear_all()
        self.lat_int.clear_graph()
        self.lbl_info.setText('')
        self.report.set_asimetria(self.subtipo)

    # =====================================================================
    # Subtipo
    # =====================================================================

    def apply_subtipo(self, subtipo):
        """Cambiar de VEMP cambia picos, escala, banda normativa y maniobras.

        Las curvas ya tomadas del otro subtipo no se borran: se ocultan y
        vuelven al cambiar el combo de nuevo (ver VempGraph.set_subtipo).
        """
        if subtipo not in SUBTIPOS:
            return
        self.subtipo = subtipo
        picos = SUBTIPO_PEAKS[subtipo]
        self.graph_r.set_subtipo(subtipo)
        self.graph_l.set_subtipo(subtipo)
        self.table_r.set_peak_labels(picos)
        self.table_l.set_peak_labels(picos)
        self.lat_int.set_subtipo(subtipo, self.baseline_actual(subtipo))
        self.emg.set_subtipo(subtipo)
        self.refresh_emg()
        self.refresh_asimetria()
        for tabla, grafico in ((self.table_r, self.graph_r),
                               (self.table_l, self.graph_l)):
            activa = grafico.get_active()
            if activa:
                self.curve_selected(activa)
            else:
                tabla.clear_all()

    def baseline_actual(self, subtipo):
        """Normativa de ESTE paciente para el subtipo: la misma que usa el
        generador, para que la banda de la lat-int y las curvas cuenten la
        misma historia."""
        if self._generador is None:
            try:
                self._generador = VEMPGeneratorV1()
            except Exception as exc:
                print(f'VEMP: no se pudo leer la normativa ({exc})')
                return {}
        generador = self._generador
        poblacion = select_population((self.data_current or {}).get('edad'),
                                      (self.data_current or {}).get('gender'))
        freq = self.control.cb_freq.currentText()
        return generador.get_baseline_values(poblacion, subtipo, freq=freq)

    # =====================================================================
    # Captura
    # =====================================================================

    def capture_state(self, state):
        if state == 'record':
            self.state_capture = state
            self.current_setting = self.control.get_data()
            self.total_averages = self.fake_averages(self.current_setting['average'])
            self.capture_timer.start(TIEMPO_ENTR_PROM)
        elif state == 'stopped':
            self.state_capture = state
            self.capture_timer.stop()
            self.count_averages = 0
        else:
            self.state_capture = state
            self.capture_timer.stop()

    def fake_averages(self, averages):
        """Cuántos ticks dura la promediación pedida.

        Superlineal a propósito (igual que el ABR): pedir 600 barridos tiene
        que sentirse mucho más largo que pedir 100, no un poco.
        """
        try:
            averages = int(averages)
        except (TypeError, ValueError):
            averages = 200
        return max(5, min(int(round(averages ** 1.1 / 25)), 90))

    def capture(self):
        if self.state_capture != 'record':
            return
        # La maniobra se relee en cada tick aunque el resto del setting quede
        # congelado al iniciar: el paciente se relaja EN PLENA promediación y
        # ver la respuesta caerse ahí es parte de lo que hay que aprender.
        self.current_setting['maniobra'] = self.control.get_maniobra()
        self.graph(self.current_setting['side'])

    def caso_del_lado(self, side):
        oido = self.vemp_od if side == 'OD' else self.vemp_oi
        return case_for_subtipo(oido, self.subtipo)

    def new_curve(self, side):
        letra_lado = 'R' if side == 'OD' else 'L'
        lista = self.curves_R if letra_lado == 'R' else self.curves_L
        # El nombre lleva el subtipo: un cVEMP y un oVEMP del mismo oído son
        # curvas distintas y conviven en la misma memoria/informe.
        prefijo = f'{self.subtipo[0]}{letra_lado}'
        # El número sale del máximo y no de la cuenta: borrar una curva del
        # medio no puede devolver un nombre que otra ya está usando.
        usados = [int(c[len(prefijo):]) for c in lista
                  if c.startswith(prefijo) and c[len(prefijo):].isdigit()]
        curva = f'{prefijo}{max(usados, default=0) + 1}'
        lista.append(curva)
        self.current_capture_curve = curva
        return curva

    def graph(self, side):
        case = self.caso_del_lado(side)
        if case is None:
            # Paciente sin VEMP configurado en este oído. Sin datos reales no
            # se genera nada.
            self.control.stop_capture()
            self.lbl_info.setText(
                f'{side}: este paciente no tiene VEMP configurado en ese oído.')
            return

        self.done = False
        if self.count_averages == 0:
            self.new_curve(side)
            self.count_averages = 1
        elif self.count_averages < self.total_averages:
            self.count_averages += 1
        else:
            self.done = True
            self.count_averages = 0
            self.control.stop_capture()

        intensidad = self.current_setting['int']
        x, y, _dx, _dy, _repro, metadata = VEMP_Curve(
            intensidad,
            {**self.current_setting, 'subtipo': self.subtipo},
            case,
            repro_prev=0,
            prom=[(self.count_averages / max(self.total_averages, 1)),
                  self.current_setting['average']],
            done=self.done,
            patient=self.data_current,
        )
        self.last_metadata = metadata

        grafico = self.graph_r if side == 'OD' else self.graph_l
        grafico.create_line(self.current_capture_curve, x, y, intensidad,
                            subtipo=self.subtipo, done=self.done)
        self.memory_curves(side)
        self.update_capture_info(metadata)

    def memory_curves(self, side):
        """Crea/actualiza la ficha de la curva en la memoria del examen."""
        curva = self.current_capture_curve
        if curva not in self.memory:
            self.memory[curva] = {
                **self.current_setting,
                'side': side,
                'subtipo': self.subtipo,
                'waves': list(SUBTIPO_PEAKS[self.subtipo]),
                'LatAmp': {p: [None, None] for p in SUBTIPO_PEAKS[self.subtipo]},
                'p2p': None,
            }
        # Cómo se registró: la maniobra y el EMG son las condiciones sin las
        # que el resultado no se puede evaluar (ver AbrMainWindow.
        # recording_conditions -- mismo criterio).
        self.memory[curva].update({
            'maniobra': self.current_setting.get('maniobra'),
            'emg_uv': round(float(self.last_metadata.get('emg_uv') or 0), 1),
            'emg_ok': bool(self.last_metadata.get('emg_ok')),
            'barridos': int(self.last_metadata.get('current_avg') or 0),
            'done': self.done,
        })

    def update_capture_info(self, metadata):
        """Estado de la captura, como lo muestra el equipo real.

        Los barridos que van, el EMG con el que se están registrando y el
        aviso cuando ese EMG no alcanza: sin eso, una curva plana por
        paciente relajado y una por respuesta ausente se ven igual.
        """
        setting = self.current_setting
        presentados = int(metadata.get('current_avg') or 0)
        pedidos = int(setting.get('average') or 0)
        rate = float(setting.get('rate') or 5.0)
        segundos = int(presentados / rate) if rate else 0
        partes = [
            self.current_capture_curve,
            f"{setting.get('int')} dB SPL {setting.get('side')}",
            f"{self.subtipo} {setting.get('freq', '500Hz')}",
            f"{presentados}/{pedidos} barridos",
            f"{segundos // 60:02d}:{segundos % 60:02d}",
            f"EMG {metadata.get('emg_uv', 0):.0f} µV",
        ]
        if not metadata.get('emg_ok'):
            partes.append('⛔ EMG FUERA DE RANGO -- revisá la maniobra')
        self.lbl_info.setText('  ·  '.join(str(p) for p in partes))

    # =====================================================================
    # Monitor de EMG
    # =====================================================================

    def refresh_emg(self):
        if self.data_current is None:
            return
        nivel = emg_de_maniobra(self.subtipo, self.control.get_maniobra())
        self.emg.push(nivel)

    # =====================================================================
    # Medición (cursores + tabla + marcas)
    # =====================================================================

    def measure_data(self, data):
        """Lectura de los cursores del gráfico, guardada por oído."""
        info = data.get('data') or {}
        side = int(info.get('side', 0))
        self.current_measuring[side] = info

    def measure_action(self, pedido):
        """Clic en una celda de la tabla: marca el pico donde está el cursor A.

        Las dos columnas hacen lo mismo a propósito: la marca ES un punto de
        la curva, así que latencia y amplitud salen juntas. Pedirlas por
        separado (como en el ABR, donde la amplitud es A-A') dejaba marcar
        una latencia sin amplitud y una amplitud sin latencia.
        """
        side = int(pedido.get('side', 0))
        pico = pedido.get('pico')
        medida = self.current_measuring[side]
        if not medida:
            self.lbl_info.setText(
                'Poné el cursor A sobre el pico en la curva antes de marcarlo.')
            return
        grafico = self.graph_r if side == 0 else self.graph_l
        if grafico.get_active() is None:
            return
        grafico.create_marks(pico)

    def update_memory_from_graph_mark(self, data):
        """Marca creada o borrada en el gráfico -> memoria + tabla + p2p."""
        for curva, marcas in data.items():
            ficha = self.memory.get(curva)
            if ficha is None:
                continue
            for pico, coords in marcas.items():
                if pico not in ficha['LatAmp']:
                    continue
                if coords is None:
                    ficha['LatAmp'][pico] = [None, None]
                else:
                    ficha['LatAmp'][pico] = [float(coords[0]), float(coords[1])]
            side = ficha.get('side', 'OD')
            tabla = self.table_r if side == 'OD' else self.table_l
            ficha['p2p'] = self.peak_to_peak(ficha)
            if (self.graph_r if side == 'OD' else self.graph_l).get_active() == curva:
                tabla.set_latamp(ficha['LatAmp'])
            self.refresh_asimetria()

    def peak_to_peak(self, ficha):
        """Amplitud pico-pico de la curva: resta CON SIGNO entre sus dos
        picos (P13 arriba, N23 abajo). Sale de los picos que registró ESA
        curva y no de los del subtipo activo, que puede ser otro."""
        latamp = ficha.get('LatAmp') or {}
        amps = []
        for pico in ficha.get('waves') or []:
            vals = latamp.get(pico)
            if not vals or vals[1] is None:
                return None
            amps.append(float(vals[1]))
        if len(amps) < 2:
            return None
        return abs(amps[0] - amps[1])

    def curve_selected(self, curva):
        ficha = self.memory.get(curva)
        if ficha is None:
            return
        tabla = self.table_r if ficha.get('side') == 'OD' else self.table_l
        tabla.set_titulo(curva, ficha.get('int'), ficha.get('subtipo'))
        tabla.set_latamp(ficha.get('LatAmp'))

    def update_delete_curve(self, curva):
        ficha = self.memory.pop(curva, None)
        if ficha is None:
            return
        if curva in self.curves_R:
            self.curves_R.remove(curva)
        if curva in self.curves_L:
            self.curves_L.remove(curva)
        tabla = self.table_r if ficha.get('side') == 'OD' else self.table_l
        tabla.clear_all()
        self.refresh_asimetria()

    # =====================================================================
    # Asimetría
    # =====================================================================

    def asimetria(self):
        """Razón de asimetría del subtipo activo, con las mayores amplitudes
        pico-pico marcadas en cada oído. Devuelve (od, oi, ratio_%)."""
        mejor = {'OD': None, 'OI': None}
        for ficha in self.memory.values():
            if ficha.get('subtipo') != self.subtipo:
                continue
            p2p = ficha.get('p2p')
            lado = ficha.get('side')
            if p2p is None or lado not in mejor:
                continue
            if mejor[lado] is None or p2p > mejor[lado]:
                mejor[lado] = p2p
        od, oi = mejor['OD'], mejor['OI']
        if od is None or oi is None or (od + oi) == 0:
            return od, oi, None
        return od, oi, abs(od - oi) / (od + oi) * 100

    def refresh_asimetria(self):
        od, oi, ratio = self.asimetria()
        self.report.set_asimetria(SUBTIPO_LABELS.get(self.subtipo, self.subtipo),
                                  od, oi, ratio)

    # =====================================================================
    # Pestañas
    # =====================================================================

    def tab_change(self, index):
        if index == 1:
            self.lat_int.set_subtipo(self.subtipo, self.baseline_actual(self.subtipo))
            self.lat_int.plot_data(self.memory, self.subtipo)
        elif index == 2:
            self.refresh_asimetria()

    # =====================================================================
    # Informe
    # =====================================================================

    def submit_report(self):
        """Sube el informe al cerrar la atención. Best-effort, igual que el
        ABR: sin conexión no debe romper el cierre de la atención."""
        if not self.data_login or not self.memory:
            return
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return

        temp_dir = context.get_resource('local_cache/vemp/temp')
        os.makedirs(temp_dir, exist_ok=True)
        images = {}
        for sufijo, widget in [('0', self.graph_r), ('1', self.graph_l),
                               ('lat_int', self.lat_int)]:
            path = os.path.join(temp_dir, f'upload_{sufijo}.jpg')
            try:
                widget.export_jpg(path)
            except Exception as exc:
                print(f'VEMP: no se pudo exportar {sufijo} para el informe: {exc}')
                continue
            images[sufijo] = path

        od, oi, ratio = self.asimetria()
        data = {
            'curvas': self.memory,
            'subtipo': self.subtipo,
            'asimetria': {'subtipo': self.subtipo, 'od': od, 'oi': oi,
                          'ratio': None if ratio is None else round(ratio, 1)},
            'hallazgos': self.report.text_edit_1.toPlainText(),
            'conclusion': self.report.text_edit_2.toPlainText(),
            'waves': list(SUBTIPO_PEAKS[self.subtipo]),
        }
        client = BackendClient(
            Preferences().get('BACKEND_URL'),
            context.get_resource('json/session.json'),
        )
        if not client.is_logged_in():
            return
        try:
            client.upload_report(appointment_id, 'VEMP', data, images)
        except Exception as exc:
            print(f'VEMP: no se pudo subir el informe: {exc}')

    def closeEvent(self, event):
        self.capture_timer.stop()
        self.emg_timer.stop()
        event.accept()
