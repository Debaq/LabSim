"""
VempMainWindow - Orquestador MDI del módulo VEMP.

Replica la estructura de AbrMainWindow pero simplificada:
- Sin ciclo de examen propio (TIEMPO_TEST, QTimer de captura por curva)
  -- el alumno decide cuándo capturar usando el botón start/stop del
  control, y cada "capture" genera UNA curva con VEMP_Curve(). Se eliminó
  el timer interno que tenía simPEATC cuando corría standalone.
- Subtipo (CVEMP/OVEMP/MVEMP) lo elige el alumno desde el dropdown del
  control; al cambiarlo, se actualizan peak_labels en gráficos + tabla.
- Sin lat-int automática (la llena el alumno al ir a la pestaña 2 con
  curvas capturadas). Sin detail_all (demasiado para v1).
- submit_report exporta 3 JPEGs (OD, OI, lat-int) + el waves list al
  backend via BackendClient.upload_report(appointment_id, 'VEMP', ...).
"""

import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QTabWidget, QSplitter,
)

from core.base import context
from backend.client import BackendClient
from core.helpers import Preferences

from vemp.VempControl import VempControl, SUBTIPOS
from vemp.VempGraph import VempGraph
from vemp.VempLatIntGraph import VempLatIntGraph
from vemp.VempTable import VempTable
from vemp.VempReport import VempReport
from vemp.VEMP_generator_v1 import VEMP_Curve, SUBTIPO_PEAKS


class VempMainWindow(QMainWindow):
    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.data_current = None
        self.appointment_id = None
        self.vemp_od = None
        self.vemp_oi = None
        self.subtipo = 'CVEMP'

        # Estado de captura
        self.state_capture = 'stopped'
        self.curves = []  # nombres de curvas en orden
        self.memory = {}  # curve_name -> dict completo (sett + LatAmp)
        self.capture_timer = QTimer()
        self.capture_timer.setInterval(200)  # ticks durante captura
        self.capture_timer.timeout.connect(self._tick_capture)
        self._capture_count = 0
        self._capture_target = 0

        self._build_ui()

        # Gate: arranca deshabilitado hasta que llegue la_super(data != None)
        self.control.setEnabled(False)

    # =====================================================================
    # UI
    # =====================================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # Panel izquierdo: control + tabla por oído
        left = QVBoxLayout()
        self.control = VempControl()
        self.control.cb_subtipo.currentTextChanged.connect(self._on_subtipo_changed)
        self.control.capture.connect(self._on_capture_state)
        left.addWidget(self.control)

        # Tablas OD / OI lado a lado
        tables = QHBoxLayout()
        self.table_r = VempTable(side=0)
        self.table_l = VempTable(side=1)
        self.table_r.sig_measure_value.connect(self._on_request_value)
        self.table_l.sig_measure_value.connect(self._on_request_value)
        tables.addWidget(self.table_r)
        tables.addWidget(self.table_l)
        left.addLayout(tables)

        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(360)
        root.addWidget(left_w)

        # Panel derecho: tabs (curvas, lat-int, informe)
        self.tabs = QTabWidget()

        # Tab 1: gráficos OD/OI lado a lado
        graphs = QHBoxLayout()
        self.graph_r = VempGraph(side=0, peak_labels=self._current_peaks())
        self.graph_l = VempGraph(side=1, peak_labels=self._current_peaks())
        graphs.addWidget(self.graph_r)
        graphs.addWidget(self.graph_l)
        tab_graphs = QWidget()
        tab_graphs.setLayout(graphs)
        self.tabs.addTab(tab_graphs, 'Curvas')

        # Tab 2: latencia-intensidad
        self.lat_int = VempLatIntGraph(peak_labels=self._current_peaks())
        self.tabs.addTab(self.lat_int, 'Lat-Int')

        # Tab 3: informe
        self.report = VempReport()
        if self.data_login.get('name'):
            self.report.set_le_eva(self.data_login['name'])
        self.tabs.addTab(self.report, 'Informe')

        root.addWidget(self.tabs, 1)

    def _current_peaks(self):
        return SUBTIPO_PEAKS.get(self.subtipo, ['p13', 'n23'])

    # =====================================================================
    # la_super / reset / submit_report (API que llama main.py)
    # =====================================================================

    def la_super(self, data, appointment_id=None):
        """Llamado por main.py cuando hay un paciente activo."""
        self.data_current = data
        self.appointment_id = appointment_id
        self.control.setEnabled(data is not None)
        vemp_data = (data or {}).get('VEMP') or {}
        # Si el caso trae subtipo configurado, usarlo como default; si no, dejar CVEMP.
        od_sub = (vemp_data.get('OD') or {}).get('subtipo')
        oi_sub = (vemp_data.get('OI') or {}).get('subtipo')
        chosen = od_sub or oi_sub or 'CVEMP'
        if chosen in SUBTIPOS:
            self.control.cb_subtipo.setCurrentText(chosen)
            self.subtipo = chosen
        self.vemp_od = vemp_data.get('OD')
        self.vemp_oi = vemp_data.get('OI')
        self.reset()

    def reset(self):
        self.curves = []
        self.memory = {}
        self.graph_r.limpiar_todo()
        self.graph_l.limpiar_todo()
        self.table_r.clear_all()
        self.table_l.clear_all()
        self.lat_int.clear_graph()

    def submit_report(self):
        """Sube el informe al cerrar la atención. Replica el patrón ABR."""
        if not self.data_login:
            return
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return
        if not self.memory:
            return

        temp_dir = context.get_resource('local_cache/vemp/temp')
        os.makedirs(temp_dir, exist_ok=True)
        images = {}
        for suffix, widget in [('0', self.graph_r), ('1', self.graph_l),
                               ('lat_int', self.lat_int)]:
            path = os.path.join(temp_dir, f'upload_{suffix}.jpg')
            try:
                widget.export_jpg(path)
                images[suffix] = path
            except Exception:
                continue

        data = {
            'curvas': self.memory,
            'hallazgos': self.report.text_edit_1.toPlainText(),
            'conclusion': self.report.text_edit_2.toPlainText(),
            'waves': self._current_peaks(),
        }
        client = BackendClient(
            Preferences().get('BACKEND_URL'),
            context.get_resource('json/session.json'),
        )
        if not client.is_logged_in():
            return
        try:
            client.upload_report(appointment_id, 'VEMP', data, images)
        except Exception:
            pass

    # =====================================================================
    # Subtipo change
    # =====================================================================

    def _on_subtipo_changed(self, subtipo):
        if subtipo not in SUBTIPOS:
            return
        self.subtipo = subtipo
        peaks = self._current_peaks()
        self.graph_r.set_peak_labels(peaks)
        self.graph_l.set_peak_labels(peaks)
        self.table_r.set_peak_labels(peaks)
        self.table_l.set_peak_labels(peaks)

    # =====================================================================
    # Captura (simplificada vs ABR)
    # =====================================================================

    def _on_capture_state(self, state):
        self.state_capture = state
        if state == 'record':
            self._start_capture()
        elif state == 'stopped':
            self._stop_capture()

    def _start_capture(self):
        control = self.control.get_data()
        # El lado es la curva actual del lado activo (alternativa: tomar de un selector).
        # Para v1 simplificado: capturamos ambas curvas (OD y OI) con la misma intensidad.
        # El alumno elegirá qué pico marcar en cada una.
        side = 'OD'
        # Nota: en una iteración futura se puede separar captura por lado.
        self._capture_target = control['average']
        self._capture_count = 0
        self.capture_timer.start()

    def _tick_capture(self):
        self._capture_count += 1
        if self._capture_count >= self._capture_target:
            self.capture_timer.stop()
            self._finalize_capture()

    def _finalize_capture(self):
        control = self.control.get_data()
        intensity = control['int']
        # Construir 'case' para VEMP_Curve (compat con la firma)
        case_od = self.vemp_od or {'type': 'normal', 'umbral': 60, 'repro': True,
                                   'repro_var': 0.2, 'average_objetivo': control['average'],
                                   'desviaciones': {}}
        case_oi = self.vemp_oi or case_od
        # Generar ambas curvas (OD, OI)
        for side_label, side_idx, case_side, graph, table in [
            ('OD', 0, case_od, self.graph_r, self.table_r),
            ('OI', 1, case_oi, self.graph_l, self.table_l),
        ]:
            name = f'{side_label[0]}{len(self.curves) // 2 + 1}'
            x, y, dx, dy, repro = VEMP_Curve(
                actual_intencity=intensity,
                control_setting={**control, 'subtipo': self.subtipo},
                case=case_side,
                repro_prev=0,
                prom=(self._capture_count, control['average']),
                done=True,
            )
            graph.create_line(name, x, y, intensity)
            table.clear_all()
            self.curves.append(name)
            self.memory[name] = {
                'side': side_label,
                'int': intensity,
                'subtipo': self.subtipo,
                'stim': control.get('subtipo', 'CVEMP'),
                'rate': control['rate'],
                'average': control['average'],
                'LatAmp': {p: [None, None] for p in self._current_peaks()},
                'waves': self._current_peaks(),
            }

    def _stop_capture(self):
        self.capture_timer.stop()

    def _on_request_value(self, data):
        """Alumno hace click en celda de tabla → pide medición al gráfico activo."""
        # En una iteración futura: implementar cursores A/A' para medir amp entre 2 puntos.
        # Por ahora solo se loguea: el alumno marca lat/amp arrastrando los labels de
        # pico directamente sobre el gráfico (set_mark).
        pass

    def closeEvent(self, event):
        self.capture_timer.stop()
        event.accept()
