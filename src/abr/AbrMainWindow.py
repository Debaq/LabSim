"""Módulo ABR (Potencial Evocado Auditivo de Tronco Cerebral).

Migrado desde simPEATC (Debaq/simPEATC, rama cleanup/fbs-remove) para
montarse como subventana MDI en LabSim (botón "ABR"). El modo OSCE, el
chequeo de licencia standalone, el timer/ciclo de examen propio (heredado
de cuando simPEATC corría solo con 2 casos random por sesión) y el banco
de 30 patologías hardcodeadas (antes en abr/conbinaciones.py) se sacaron
-- este módulo ahora sigue el mismo patrón que Audiometer/Z: sin
cronómetro propio, reacciona a la atención abierta en LabSim vía
la_super(data_current, appointment_id). Cada paciente trae su propia
definición ABR en cases.data['ABR']['OD'/'OI'] (ver CaseBuilder.php).
"""
import os

from abr.ABR_generator_v3 import ABR_Curve
from abr.AbrControl import AbrControl
from abr.AbrDetail import AbrDetail
from abr.AbrDetailAllCurves import AbrDetailAllCurves
from abr.AbrGraph import AbrGraph
from abr.AbrLatIntGraph import GraphLatInt
from abr.AbrReport import AbrReport
from abr.AbrTable import AbrTable
from abr.EEG import EEG
from abr.FSP import FSP
from abr.UI.AbrAdvanceSettings_ui import Ui_AdvanceSettings
from abr.UI.AbrMain_ui import Ui_MainWindow
from backend.client import BackendClient
from core.base import context
from core.helpers import Preferences
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QDialog, QMainWindow, QSizePolicy, QSpacerItem

tr = QCoreApplication.translate

TIEMPO_ENTR_PROM = 300

# Patología de respaldo si el caso del paciente no trae ABR configurado
# (caso viejo sin actualizar, o mientras no hay atención abierta).
DEFAULT_ABR_CASE = {
    'type': 'normal',
    'repro': True,
    'repro_var': 0.2,
    'umbral': 20,
    'average_objetivo': 2000,
    'desviaciones': {},
    'fsp_puntos': {'800': 2.3, '2000': 2.8, 'objetivo': 3.0},
}


class AbrMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, data_login=None) -> None:
        QMainWindow.__init__(self)
        self.setupUi(self)
        # data_login: dict de la sesión de LabSim (user/name/permission), lo
        # entrega la ventana principal al montar esta subventana MDI.
        self.data_login = data_login
        self.setWindowTitle("ABR")
        self.data_current = None
        self.appointment_id = None
        self.abr_od = dict(DEFAULT_ABR_CASE)
        self.abr_oi = dict(DEFAULT_ABR_CASE)

        self.control = AbrControl()
        self.detail = AbrDetail()
        self.report = AbrReport()
        self.table_l = AbrTable(1)
        self.table_r = AbrTable(0)
        self.eeg = EEG()
        self.fmp = FSP()
        self.detail_all = AbrDetailAllCurves()
        self.graph_r = AbrGraph(0)
        self.graph_l = AbrGraph(1)
        self.graph_lat_int = GraphLatInt()

        # "exam" haría que open_save_as_dialog use self.report.case, que ya
        # no existe (el caso viene de data_current, no de un índice propio).
        self.report.type_use = "custom"
        self.report.set_le_eva(self.data_login.get("name", "") if self.data_login else "")

        self.layout_abr.addWidget(self.graph_r)
        self.layout_abr.addWidget(self.graph_l)
        self.layout_lat_int.addWidget(self.graph_lat_int)
        self.layout_report.addWidget(self.report)
        self.detail.layout_tab1_secction1.addWidget(self.eeg)
        self.detail.layout_tab1_secction2.addWidget(self.fmp)
        self.detail.layout_tab2.addWidget(self.detail_all)
        self.layout_dock_parameter_content.addWidget(self.control)
        self.layout_dock_test_contents.addWidget(self.detail)
        self.layout_dock_values_contents.addWidget(self.table_r)
        self.layout_dock_values_contents.addWidget(self.table_l)
        self.layout_dock_values_contents.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        ########Conexiones de slots
        self.actionP_rametros_Avanzados.triggered.connect(self.active_advance_setting)
        # "Cambiar Caso" ya no aplica (el caso lo trae el paciente en
        # atención, ver la_super) -- el menú queda sin acción conectada.
        self.table_r.sig_measure_value.connect(self.measure_action)
        self.table_l.sig_measure_value.connect(self.measure_action)
        self.graph_r.sig_data_info.connect(self.measure_data)
        self.graph_l.sig_data_info.connect(self.measure_data)
        self.graph_r.sig_change_value_mark.connect(self.table_r.change_value_lat)
        self.graph_l.sig_change_value_mark.connect(self.table_l.change_value_lat)
        # CRÍTICO: También conectar las marcas del gráfico para actualizar la memoria
        self.graph_r.sig_change_value_mark.connect(self.update_memory_from_graph_mark)
        self.graph_l.sig_change_value_mark.connect(self.update_memory_from_graph_mark)
        self.graph_r.sig_curve_selected.connect(self.curve_selected)
        self.graph_l.sig_curve_selected.connect(self.curve_selected)
        self.graph_r.sig_del_curve.connect(self.update_delete_curve)
        self.graph_l.sig_del_curve.connect(self.update_delete_curve)

        self.tabWidget.currentChanged.connect(self.tab_change)
        self.detail_all.sig_selected_curve.connect(self.selected_)
        self.btn_scale_minus.clicked.connect(self.scale_graph)
        self.btn_scale_plus.clicked.connect(self.scale_graph)
        self.btn_next_case.hide()  # sin ciclo de casos propio, no aplica

        ######Variables de Estado
        self.control.capture.connect(self.capture_state)
        self.state_capture = "stopped"
        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self.capture)

        ######Variables de almacenamiento
        self.setting_current = {}
        self.curves_R = []
        self.curves_L = []
        self.current_capture_curve = ""
        self.current_curve_r = ""
        self.current_curve_l = ""
        self.current_setting = {}
        self.total_averages = 20
        self.current_measuring = [None, None]
        self.memory = {}
        self.donde = False
        self.count_averages = 0

    def la_super(self, data, appointment_id=None):
        """Recibe el caso del paciente en atención (o None al cerrarla/
        deshidratar), mismo patrón que Audiometer.la_super/Z.la_super."""
        self.appointment_id = appointment_id
        abr_data = (data or {}).get('ABR') or {}
        self.abr_od = abr_data.get('OD') or dict(DEFAULT_ABR_CASE)
        self.abr_oi = abr_data.get('OI') or dict(DEFAULT_ABR_CASE)
        self.data_current = data
        self.reset()

    def submit_report(self):
        """Sube el informe (curvas marcadas + hallazgos/conclusión + JPEG de
        los gráficos) al backend -- ver BackendClient.upload_report() /
        report_upload.php. Se llama al cerrar la atención (main.py::
        _cerrar_atencion_real), ANTES de que _hydrate_modules() nos saque
        appointment_id/data_login vía la_super(None).

        Best-effort a propósito: sin conexión, o si la fila 'atendiendo' de
        attendances todavía no sincronizó desde el cliente (offline-first),
        esto falla en silencio -- no debe romper el cierre de la atención,
        que ya se guardó local igual. El alumno no pierde el informe: sigue
        en pantalla, puede reintentar (ej. reabriendo la atención) o el
        docente puede pedir que se revise a mano.
        """
        if not self.data_login or not self.memory:
            return
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return

        temp_dir = context.get_resource("local_cache/abr/temp")
        exporters = {'0': self.graph_r, '1': self.graph_l, 'lat_int': self.graph_lat_int}
        images = {}
        for suffix, exporter in exporters.items():
            path = os.path.join(temp_dir, f'upload_{suffix}.jpg')
            try:
                exporter.export_jpg(path)
            except Exception as exc:
                print(f"ABR: no se pudo exportar {suffix} para el informe: {exc}")
                continue
            images[suffix] = path

        data = {
            'curvas': self.memory,
            'hallazgos': self.report.text_edit_1.toPlainText(),
            'conclusion': self.report.text_edit_2.toPlainText(),
        }

        client = BackendClient(Preferences().get("BACKEND_URL"), context.get_resource('json/session.json'))
        if not client.is_logged_in():
            return
        try:
            client.upload_report(appointment_id, 'ABR', data, images)
        except Exception as exc:
            print(f"ABR: no se pudo subir el informe: {exc}")

    def reset(self):
        """Limpia completamente los gráficos y la memoria de curvas"""
        print("\n🔄 RESET: Limpiando gráficos y memoria...")

        # Limpiar completamente ambos gráficos usando el nuevo método
        self.graph_r.limpiar_todo()
        self.graph_l.limpiar_todo()

        # Limpiar listas de curvas
        self.curves_R = []
        self.curves_L = []

        # Limpiar memoria
        self.memory = {}

        # Limpiar tablas
        self.table_r.clear_all()
        self.table_l.clear_all()
        self.detail_all.clear_all()

        print("   ✓ Reset completado\n")

    def update_delete_curve(self, curve):
        if curve in self.memory:
            table_letter = 'r' if curve[0] == 'R' else 'l'
            table = f'table_{table_letter}'
            getattr(self, table).clear_all()
            self.detail_all.delete_row_by_header(curve)
            del self.memory[curve]

    def curve_selected(self, curve):
        table_letter = 'r' if curve[0] == 'R' else 'l'
        try:
            table = f'table_{table_letter}'
            data = self.memory[curve]
            getattr(self, table).update_latamp_table(data)
        except KeyError:
            pass

    def scale_graph(self):
        _,_,direction = self.sender().objectName().split('_')
        value = self.graph_r.scale(direction)
        self.graph_l.scale(direction)
        value = int(round(value,0))
        value = f"{value}µV"
        self.lbl_scale.setText(value)

    def selected_(self, curve):
        letter = 'r' if curve[0] == 'R' else 'l'
        graph = f'graph_{letter}'
        getattr(self, graph).active_curve(curve)

    def tab_change(self, sender):
        if sender == 1:
            self.dock_values.setVisible(False)
            self.dock_parameter.setVisible(False)
            self.detail.tabWidget.setCurrentIndex(1)
            self.dock_test.setFixedHeight(400)
            self.graph_lat_int.clear_graph()
            self.graph_lat_int.plot_data(self.memory)
        elif sender == 2:
            self.dock_values.setVisible(False)
            self.dock_parameter.setVisible(False)
            self.detail.tabWidget.setCurrentIndex(1)
            self.dock_test.setFixedHeight(300)
            self.report_svg()

        else:
            self.dock_values.setVisible(True)
            self.dock_parameter.setVisible(True)
            self.detail.tabWidget.setCurrentIndex(0)
            self.dock_test.setFixedHeight(150)
            self.graph_lat_int.clear_graph()


    def capture_state(self, state:str) -> None:
        if state == 'record':
            self.state_capture = state
            self.current_setting = self.control.get_data()
            self.total_averages = self.fake_averages(self.current_setting["average"])
            self.capture_timer.start(TIEMPO_ENTR_PROM)
        elif state == 'stopped':
            self.state_capture = state
            self.capture_timer.stop()
            print('me detuve')
        else:
            self.state_capture = state

    def capture(self) -> None:
        if self.state_capture == 'record':
            side = self.current_setting["side"]
            self.graph(side)
            self.memory_curves()
        elif self.state_capture == 'pause':
            print("detenido")

    def get_curve(self, presets):
        pass

    def new_curve(self, side:str) -> str:
        side_letter = 'R' if side == 'OD' else 'L'
        side = f'curves_{side_letter}'
        db_curves = getattr(self, side)
        if not db_curves:
            curve = f'{side_letter}1'
        else:
            number_last_curve = int(db_curves[-1].strip(side_letter))
            curve =  f'{side_letter}{number_last_curve+1}'
        getattr(self, side).append(curve)
        table=f"table_{side_letter.lower()}"
        getattr(self, table).clear_all()
        self.selected_(curve)
        self.current_capture_curve = curve
        return curve

    def graph(self, side):
        self.done = False
        if self.count_averages == 0:
            self.new_curve(side)
            self.count_averages = 1
        elif self.count_averages < self.total_averages:
            self.count_averages +=1
        else:
            self.done = True
            self.count_averages = 0
            self.control.stop_capture()
        i_xy, c_xy, a, b, repro = self.test_test(side)
        intencity = self.current_setting['int']

        data_line = {self.current_capture_curve:{"ipsi_xy":i_xy,"contra_xy":c_xy, "a":a, "b":b, "gap":1.8,
                                                 "repro" : repro, "intencity":intencity, "done" : self.done}}
        side_letter = 'r' if side == 'OD' else 'l'
        graph = f'graph_{side_letter}'
        getattr(self, graph).create_line(data_line, intencity)

    def fake_averages(self, averages, fake = True, express = False):
        if isinstance(averages , str):
            averages = int(averages)
        if not express:
            if fake:
                # b > 1: superlineal a propósito -- pedir más promediaciones
                # (caso difícil / mucho ruido) debe sentirse notoriamente
                # más largo, no solo un poco más. Ancla en 2000 = ~28 ticks
                # (~8.4s), igual que la calibración vieja (b=0.522).
                a = 0.0014339
                b = 1.3
                return a * (averages**b)
            self.total_averages = averages
        else:
            return 1

    def measure_action(self, data):
        side =  list(data.keys())[0]
        side_letter = 'r' if side == '0' else 'l'
        request = list(data[side].keys())[0]
        mark,command = request.split('_')
        side = int(side)
        if command == 'L':
            value = self.current_measuring[side]['lat_A']
        elif command == 'A':
            value = self.current_measuring[side]['amp_AB']
        self.memory_curves((mark,command,value), side_letter)
        data[str(side)][request] = value
        table = f'table_{side_letter}'
        graph = f'graph_{side_letter}'
        getattr(self, table).set_data(data)
        getattr(self, graph).create_marks(mark)

    def measure_data(self, data):
        side = data["curve"][0]
        side = 0 if side == 'R' else 1
        side_letter = 'r' if side == 0 else 'l'
        self.current_measuring[side] = data['data']
        label = f"lbl_coord_{side_letter}"

        for key in data['data']:
            if isinstance(data['data'][key], float):  # Solo redondear si el valor es un flotante
                data['data'][key] = round(data['data'][key], 1)

        getattr(self,label).setText(f'{data}')

    def update_memory_from_graph_mark(self, data):
        """
        Actualiza la memoria cuando se marca una onda directamente en el gráfico

        Args:
            data: dict con formato {curva: {onda: [x, y]}} o {curva: {onda: None}}
        """
        for curve_name, marks_dict in data.items():
            # Verificar que la curva existe en memoria
            if curve_name not in self.memory:
                return

            # Asegurar que existe la estructura LatAmp
            if 'LatAmp' not in self.memory[curve_name]:
                self.memory[curve_name]['LatAmp'] = {
                    'I': [None, None],
                    'II': [None, None],
                    'III': [None, None],
                    'IV': [None, None],
                    'V': [None, None]
                }

            # Actualizar cada marca
            for wave, coords in marks_dict.items():
                if coords is None:
                    # Marca eliminada
                    self.memory[curve_name]['LatAmp'][wave] = [None, None]
                    print(f"   🗑️  Marca eliminada: {curve_name} - Onda {wave}")
                else:
                    # Marca creada/actualizada
                    latencia, amplitud = coords
                    self.memory[curve_name]['LatAmp'][wave] = [latencia, amplitud]
                    print(f"   ✓ Marca guardada: {curve_name} - Onda {wave}: Lat={latencia:.2f}ms, Amp={amplitud:.2f}μV")

            # Actualizar la tabla de detalle de todas las curvas
            self.detail_all.process_and_fill_data(self.memory)

    def active_advance_setting(self):
        self.dialog = QDialog(self)
        self.ui = Ui_AdvanceSettings()
        self.ui.setupUi(self.dialog)
        self.dialog.exec()

################INTERCAMBIO
    def memory_curves(self, value=None, side=None):
        if isinstance(value, tuple):
            c,cmd,val = value
            key = 'LatAmp' if cmd == 'L' or cmd == 'A' else 'InterPeaks'
            column = 0 if cmd == 'L' else 1
        model = {'LatAmp':{'I':[None,None], 'II':[None,None],'III':[None,None],'IV':[None,None],'V':[None,None]}}
        if side:
            graph = f'graph_{side}'
            name_curve = getattr(self,graph).act_curve
            if value is not None:
                self.memory[name_curve][key][c][column] = val
        else:
            name_curve = self.current_capture_curve
            sett = self.current_setting
            self.memory[name_curve] = dict(sett, **model)
        self.detail_all.process_and_fill_data(self.memory)

################Report
    def report_svg(self):
        # Deshabilitado: el PDF ahora se genera en el backend (report_pdf.php)
        # al primer "descargar", no en el cliente. Ver commit 0ce3e30.
        return



    def test_test(self, side):

        """
        morfología : presencia de ondas I,III,V
        replicabilidad : +- 0.1 ms
        Latencias Absolutas a 75: +-0.2ms
            - I : 1.6 ms
            -III: 3.7 ms
            -V: 5.6 ms
        Interonda +-0.4 ms
            -I-III : 2.0ms
            -III-V : 1.8ms
            -I-V : 3.8 ms

        desviación de latencias sobre los 50dB: 0.3ms / 10dB
        desviación de latencia onda V en cambio de tasa: desde los 0.6 a 0.8
        Ratio V/I  : mayor a 1
        interaural diferencia : menor que 0.4

        """

        side_idx = 0 if side == "OD" else 1
        case = self.abr_od if side_idx == 0 else self.abr_oi

        if case.get("repro", True) == False:
            side_letter = 'r' if side_idx == 0 else 'l'
            graph = f"graph_{side_letter}"
            repro_prev = getattr(self, graph).get_data(self.current_setting["int"])
            if repro_prev == None:
                repro_prev = 0
        else:
            repro_prev = 0


        x,y, dx, dy, repro = ABR_Curve(self.current_setting["int"], self.current_setting, case, repro_prev, [(self.count_averages*self.total_averages)*2.5, self.current_setting['average']], done = self.done)

        return(x,y),(dx,dy),(0,0),(0,0), repro

    #########EVENTS
    def closeEvent(self, event):
        event.accept()
