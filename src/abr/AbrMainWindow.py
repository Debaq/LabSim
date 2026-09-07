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

from abr.ABR_generator import (ABR_Curve, ABRGenerator, agitation_factor,
                               case_quality, latency_intensity_band,
                               normative_limits, raw_eeg)
from abr.AbrAdvanceSettings import (MONTAGES, TRANSDUCERS, AbrAdvanceSettings,
                                    default_settings)
from abr.AbrControl import AbrControl
from abr.AbrDetail import AbrDetail
from abr.AbrDetailAllCurves import AbrDetailAllCurves
from abr.AbrGraph import AbrGraph
from abr.AbrLatIntGraph import GraphLatInt
from abr.AbrReport import AbrReport
from abr.AbrTable import AbrTable
from abr.EEG import EEG
from abr.FSP import FSP
from abr.UI.AbrMain_ui import Ui_MainWindow
from backend.client import BackendClient
from core.base import context
from core.helpers import Preferences
from core.rng import stable_seed
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QMainWindow, QSizePolicy, QSpacerItem

tr = QCoreApplication.translate

TIEMPO_ENTR_PROM = 300
# Refresco del monitor de EEG crudo. Es el trazo que corre SIEMPRE que hay
# un paciente cargado, promediando o no: ahi se ve el 50 Hz y la tension
# antes de gastar 2000 barridos en descubrirlos.
TIEMPO_EEG = 300
# Alto del dock de detalle con el monitor abierto. Eran 150 px cuando los
# dos graficos estaban vacios; con el EEG crudo y el FSP dibujando de
# verdad, a esa altura no se lee ninguno de los dos.
ALTO_DOCK_DETALLE = 220


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
        # None = sin datos reales para ese oído (sin atención abierta, o
        # paciente sin ABR configurado en ese lado) -- no hay fallback
        # sintético, ver graph() para el guard antes de capturar.
        self.abr_od = None
        self.abr_oi = None

        self.control = AbrControl()
        # Sin atención abierta al crear la ventana (recién montada, antes
        # de cualquier la_super real) -- sin esto se podía capturar sin
        # ningún paciente cargado.
        self.control.setEnabled(False)
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
        self.btn_toggle_sub.toggled.connect(self.toggle_sub)
        self.btn_toggle_contra.toggled.connect(self.toggle_contra)
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
        # FSP por curva: el grafico del dock muestra el de la curva
        # seleccionada, no solo el de la ultima promediacion.
        self.fsp_tracks = {}
        self.fsp_shown = None
        self.donde = False
        self.count_averages = 0
        # Equipo (transductor, ventana, montaje, electrodos, rechazo de
        # artefacto...). Arranca en el montaje de rutina del protocolo y lo
        # edita el alumno en Parametros Avanzados. Antes el dialogo se abria
        # y se descartaba: el generador quedaba fijo en fono de insercion,
        # impedancia 3 kOhm y ventana de 12 ms.
        self.technical = default_settings(self.control.cb_test.currentText())
        self.control.cb_test.currentTextChanged.connect(self.test_changed)
        # Los rangos normativos de la tabla dependen de la intensidad y del
        # estimulo con que se registro, asi que siguen al panel de control.
        self.control.sb_intencity.valueChanged.connect(self.apply_norms)
        self.control.cb_stim.currentTextChanged.connect(self.apply_norms)
        self.control.apply_protocol(self.control.cb_test.currentText())

        # Monitor de EEG crudo: corre siempre que haya paciente, no solo
        # promediando. self.eeg_tick avanza el trazo (no se repite) y
        # self.quality es cuanto ruido trae ESTE paciente.
        self.eeg_tick = 0
        self.quality = 1.0
        self.eeg_timer = QTimer(self)
        self.eeg_timer.timeout.connect(self.refresh_eeg)
        # Ultima metadata que devolvio el generador: barridos aceptados,
        # rechazo, FSP, ruido residual, replicabilidad. Antes se calculaba
        # todo esto y se tiraba (ABR_Curve devolvia solo las curvas).
        self.last_metadata = {}
        self.blink = False
        self.lbl_scale.setText(f"{int(round(self.graph_r.get_scale()))}µV")
        self.apply_window()
        self.eeg.set_reject(self.technical.get('artifact_reject_uv'))
        self.dock_test.setFixedHeight(ALTO_DOCK_DETALLE)

    def la_super(self, data, appointment_id=None):
        """Recibe el caso del paciente en atención (o None al cerrarla/
        deshidratar), mismo patrón que Audiometer.la_super/Z.la_super.

        Sin datos reales no hay curva -- ni con atención abierta pero sin
        ABR configurado en ese caso, ni sin atención. self.abr_od/oi quedan
        en None en ambos casos (sin fallback sintético); graph() corta antes
        de generar nada si el lado activo no tiene datos."""
        self.appointment_id = appointment_id
        self.data_current = data
        self.control.setEnabled(data is not None)
        abr_data = (data or {}).get('ABR') or {}
        self.abr_od = abr_data.get('OD')
        self.abr_oi = abr_data.get('OI')
        # Cuanto ruido trae este paciente: lo mismo que usa el generador
        # para la curva promediada, para que el EEG crudo y el promedio
        # cuenten la misma historia.
        self.quality = case_quality(self.abr_od or self.abr_oi or {})
        self.reset()
        # La banda normativa del grafico latencia-intensidad sigue a la
        # poblacion del paciente: con la banda de adulto, un neonato queda
        # fuera de norma siempre.
        self.apply_norms()
        if data is None:
            self.eeg_timer.stop()
            self.eeg.clear_trace()
        else:
            self.eeg.set_reject(self.technical.get('artifact_reject_uv'))
            self.eeg_timer.start(TIEMPO_EEG)

    def recording_conditions(self):
        """Como se esta registrando: equipo + lo que el equipo midio.

        Es la mitad del informe que faltaba. Con solo curvas y conclusion,
        el docente evalua el resultado pero no el procedimiento: no puede
        distinguir un informe bien hecho de uno tomado con los electrodos a
        8 kOhm, sin tierra o con el rechazo apagado.
        """
        tec = self.technical
        meta = self.last_metadata
        peor, desbalance, ok = ABRGenerator.impedance_report(tec)
        etiqueta = {v: k for k, v in TRANSDUCERS.items()}
        montaje = {v: k for k, v in MONTAGES.items()}
        datos = {
            'transductor': etiqueta.get(tec.get('transducer'), tec.get('transducer')),
            'montaje': montaje.get(tec.get('montage'), tec.get('montage')),
            'ventana_ms': tec.get('window_ms'),
            'electrodos': dict(tec.get('electrodes') or {}),
            'impedancias_kohm': dict(tec.get('impedance') or {}),
            'impedancia_max_kohm': round(float(peor), 1),
            'impedancia_desbalance_kohm': round(float(desbalance), 1),
            'impedancia_en_norma': bool(ok),
            'rechazo_artefacto_uv': tec.get('artifact_reject_uv'),
            'ruido_residual_objetivo_nv': tec.get('residual_noise_nv'),
            'criterio_fsp': tec.get('fsp_criterion'),
        }
        if meta:
            datos.update({
                'barridos_presentados': int(meta.get('current_avg') or 0),
                'barridos_aceptados': int(meta.get('accepted_sweeps') or 0),
                'barridos_rechazados': int(meta.get('rejected_sweeps') or 0),
                'fsp': round(float(meta.get('fsp') or 0), 2),
                'ruido_residual_nv': round(float(meta.get('residual_noise_nv') or 0), 1),
                'replicabilidad': round(float(meta.get('repro_index') or 0), 2),
                'canal_contralateral': bool(meta.get('contra') is not None),
                'interferencia_red': bool(meta.get('mains')),
            })
        return datos

    def apply_norms(self, *_):
        """Banda normativa y rangos de la tabla, para ESTE paciente."""
        if self.data_current is None:
            return
        stim = self.control.cb_stim.currentText()
        try:
            x, lo, hi = latency_intensity_band(self.data_current, 'V', stim)
        except Exception as exc:      # normativa incompleta para ese estimulo
            print(f"ABR: sin banda normativa ({exc})")
            return
        edad = self.data_current.get('edad')
        etiqueta = f"Onda V ±2 DE ({edad} años)" if edad is not None else "Onda V ±2 DE"
        self.graph_lat_int.set_band(x, lo, hi, etiqueta)
        intensidad = self.control.sb_intencity.value()
        for tabla in (self.table_r, self.table_l):
            tabla.set_norms(normative_limits(self.data_current, intensidad, stim))

    def refresh_eeg(self):
        """Un trozo nuevo de EEG crudo en el monitor de los dos canales."""
        if self.data_current is None:
            return
        self.eeg_tick += 1
        # stable_seed y no hash(): el trazo del mismo paciente arranca
        # igual en cualquier proceso (ver core.rng).
        semilla = stable_seed(self.appointment_id)
        try:
            # La banda de registro y el rate salen del panel de control:
            # el monitor tiene que mostrar la MISMA banda que se promedia,
            # o el alumno mueve los filtros y no ve nada cambiar.
            datos = raw_eeg(self.technical,
                            quality=self.quality * self.agitation_now(),
                            seed=semilla,
                            tick=self.eeg_tick, duration_ms=TIEMPO_EEG,
                            test=self.control.cb_test.currentText(),
                            setting=self.control.get_data())
        except Exception as exc:
            print(f"ABR: no se pudo generar el EEG crudo: {exc}")
            self.eeg_timer.stop()
            return
        self.eeg.push(datos)

    def agitation_now(self):
        """Cuanto se esta moviendo el paciente en este momento.

        Durante la captura el indice es el bloque de promediado que trae la
        metadata, para que el monitor se ensucie en el MISMO tramo en que
        el equipo esta descartando barridos. Fuera de la captura el
        paciente se sigue moviendo igual, asi que el indice es el tick del
        monitor: quien mira antes de apretar promediar ve con que se va a
        encontrar.
        """
        case = self.abr_od or self.abr_oi or {}
        if not float(case.get('inquietud') or 0):
            return 1.0
        if self.state_capture == 'record' and self.last_metadata:
            bloque = int(self.last_metadata.get('noise_blocks') or 0)
        else:
            bloque = self.eeg_tick
        return agitation_factor(case, bloque)

    def update_capture_info(self, metadata):
        """Estado de la captura en curso, como lo muestra un equipo real.

        Barridos presentados vs aceptados (el equipo cuenta los
        presentados, el promedio avanza con los aceptados), FSP, ruido
        residual y replicabilidad A/B. Todo esto lo calculaba el generador
        y no salia de ahi.
        """
        presentados = metadata.get('current_avg') or 0
        aceptados = metadata.get('accepted_sweeps') or 0
        rechazo = 1.0 - (metadata.get('artifact_acceptance') or 1.0)
        rate = float(self.current_setting.get('rate') or 21.1)
        segundos = int(presentados / rate) if rate else 0
        self.lbl_time.setText(f"{segundos // 60:02d}:{segundos % 60:02d}")

        partes = [f"{self.current_capture_curve}",
                  f"{self.current_setting.get('int')} dBnHL {self.current_setting.get('side')}",
                  f"{int(presentados)}/{int(self.current_setting.get('average') or 0)} barridos",
                  f"aceptados {int(aceptados)}",
                  f"FSP {metadata.get('fsp', 0):.1f}",
                  f"ruido {metadata.get('residual_noise_nv', 0):.0f} nV",
                  f"repro {metadata.get('repro_index', 0):.2f}"]
        if metadata.get('fsp_criterion') and metadata.get('fsp_pass'):
            partes.append("respuesta presente")
        if not metadata.get('recording', True):
            partes.append("SIN REGISTRO (electrodo desconectado)")
        if metadata.get('mains'):
            partes.append("50 Hz")
        # El equipo real parpadea mientras descarta barridos: sin eso, el
        # alumno ve el promedio avanzar lento y no sabe por que.
        if rechazo > 0.01:
            self.blink = not self.blink
            marca = "⛔ RECHAZO" if self.blink else "   RECHAZO"
            partes.append(f"{marca} {rechazo * 100:.0f}%")
        self.lbl_info.setText("  ·  ".join(str(p) for p in partes))

    def update_detail_info(self, setting):
        """Panel de detalle: como se registro la curva que se esta mirando.

        Los lbl_info_* estaban en el .ui desde siempre y nadie les escribia
        nunca.
        """
        if not setting:
            for nombre in ('estim', 'pol', 'int', 'mkg', 'rate', 'filter',
                           'aver', 'side'):
                getattr(self.detail, f'lbl_info_{nombre}').setText('')
            return
        self.detail.lbl_info_estim.setText(str(setting.get('stim', '')))
        self.detail.lbl_info_pol.setText(str(setting.get('pol', '')))
        self.detail.lbl_info_int.setText(f"{setting.get('int', '')} dBnHL")
        self.detail.lbl_info_mkg.setText(f"{setting.get('mkg', '')} dB")
        self.detail.lbl_info_rate.setText(f"{setting.get('rate', '')}/s")
        self.detail.lbl_info_filter.setText(
            f"{setting.get('filter_passhigh', '')}-{setting.get('filter_down', '')} Hz")
        self.detail.lbl_info_aver.setText(str(setting.get('average', '')))
        self.detail.lbl_info_side.setText(str(setting.get('side', '')))

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
            # Condiciones de registro: sin esto el informe dice QUE se
            # obtuvo pero no COMO, y el procedimiento no se puede evaluar.
            # Cada curva ademas lleva las suyas (memory[curva]['tecnica']),
            # porque el alumno puede cambiar el equipo a mitad del examen.
            'tecnica': self.recording_conditions(),
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
        # Limpiar completamente ambos gráficos usando el nuevo método
        self.graph_r.limpiar_todo()
        self.graph_l.limpiar_todo()

        # Limpiar listas de curvas
        self.curves_R = []
        self.curves_L = []

        # Limpiar memoria
        self.memory = {}
        self.fsp_tracks = {}
        self.fsp_shown = None

        # Limpiar tablas
        self.table_r.clear_all()
        self.table_l.clear_all()
        self.detail_all.clear_all()

        # Limpiar panel de detalle y estado de captura
        self.fmp.clear_curve()
        self.update_detail_info(None)
        self.last_metadata = {}
        self.lbl_info.setText("")
        self.lbl_time.setText("")

    def update_delete_curve(self, curve):
        if curve in self.memory:
            table_letter = 'r' if curve[0] == 'R' else 'l'
            table = f'table_{table_letter}'
            getattr(self, table).clear_all()
            self.detail_all.delete_row_by_header(curve)
            del self.memory[curve]
            self.fsp_tracks.pop(curve, None)
            if self.fsp_shown == curve:
                self.fsp_shown = None
                self.fmp.set_track(None)

    def curve_selected(self, curve):
        table_letter = 'r' if curve[0] == 'R' else 'l'
        # El FSP es de la curva: al seleccionarla se dibuja el suyo (con
        # cuantos barridos cruzo el criterio ESA). Si es la que se esta
        # registrando ahora, sigue creciendo en vivo -- ver push_fsp. Va
        # ANTES del lookup en memory: la curva recien creada todavia no
        # esta ahi (memory_curves corre despues de graph()) y el FSP en
        # vivo se quedaba dibujando en la curva anterior.
        self.fsp_shown = curve
        self.fmp.set_track(self.fsp_tracks.get(curve))
        try:
            table = f'table_{table_letter}'
            data = self.memory[curve]
        except KeyError:
            return
        # Los rangos normativos dependen de la intensidad de ESA curva: una
        # onda V de 6.4 ms a 40 dB es normal y a 80 dB no.
        if self.data_current is not None:
            getattr(self, table).set_norms(normative_limits(
                self.data_current, data.get('int', 80), data.get('stim', 'Click')))
        getattr(self, table).update_latamp_table(data)
        self.update_detail_info(data)

    def scale_graph(self):
        _,_,direction = self.sender().objectName().split('_')
        value = self.graph_r.scale(direction)
        self.graph_l.scale(direction)
        value = int(round(value,0))
        value = f"{value}µV"
        self.lbl_scale.setText(value)

    def toggle_sub(self, visible):
        """Subpromedios A/B a la vista en los dos oidos a la vez."""
        self.graph_r.set_sub_visible(visible)
        self.graph_l.set_sub_visible(visible)

    def toggle_contra(self, visible):
        self.graph_r.set_contra_visible(visible)
        self.graph_l.set_contra_visible(visible)

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
            self.dock_test.setFixedHeight(ALTO_DOCK_DETALLE)
            self.graph_lat_int.clear_graph()


    def capture_state(self, state:str) -> None:
        if state == 'record':
            self.state_capture = state
            self.current_setting = self.control.get_data()
            self.total_averages = self.fake_averages(self.current_setting["average"])
            # El FSP arranca de cero en cada captura y contra las
            # promediaciones que se pidieron, con el criterio de deteccion
            # que quedo en Parametros Avanzados.
            if self.count_averages == 0:
                self.fmp.clear_curve()
            self.fmp.set_mean(self.current_setting["average"])
            self.fmp.set_criterion(self.technical.get('fsp_criterion'))
            self.capture_timer.start(TIEMPO_ENTR_PROM)
        elif state == 'stopped':
            self.state_capture = state
            self.capture_timer.stop()
        else:
            self.state_capture = state

    def capture(self) -> None:
        if self.state_capture == 'record':
            # El tubo se pinza EN PLENA promediacion (ese es el punto de la
            # maniobra: ver si lo que esta en pantalla se cae o no), asi
            # que este flag se relee en cada tick aunque el resto del
            # setting quede congelado al iniciar la captura.
            self.current_setting['clamp'] = self.control.ch_clamp.isChecked()
            side = self.current_setting["side"]
            self.graph(side)
            self.memory_curves()
        elif self.state_capture == 'pause':
            pass

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
        case = self.abr_od if side == "OD" else self.abr_oi
        if case is None:
            # Paciente sin ABR configurado en este oído (o sin atención --
            # aunque eso ya lo bloquea self.control.setEnabled en la_super).
            # Sin datos reales no se genera nada, ni un ejemplo sintético.
            self.control.stop_capture()
            return
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
        i_xy, c_xy, repro, metadata = self.test_test(side)
        intencity = self.current_setting['int']
        self.last_metadata = metadata

        data_line = {self.current_capture_curve: {
            "ipsi_xy": i_xy,
            # Canal contralateral: None si ese electrodo esta desconectado.
            "contra_xy": c_xy,
            # Subpromedios A/B (pares e impares): la replicabilidad EN VIVO.
            "sub_a": (i_xy[0], metadata['sub_a']),
            "sub_b": (i_xy[0], metadata['sub_b']),
            "repro": repro, "intencity": intencity, "done": self.done}}
        side_letter = 'r' if side == 'OD' else 'l'
        graph = f'graph_{side_letter}'
        getattr(self, graph).create_line(data_line, intencity)
        self.push_fsp(self.current_capture_curve, metadata)
        self.update_capture_info(metadata)
        self.update_detail_info(self.current_setting)

    def push_fsp(self, curve, metadata):
        """Un punto de FSP para ESA curva, y al grafico si es la que se mira.

        La serie la lleva la ventana y no el widget: mientras se promedia
        R2 el alumno puede volver a mirar el FSP de R1 sin cortar nada, y
        si la curva que mira es la que se esta registrando la ve crecer en
        vivo, punto a punto.
        """
        track = self.fsp_tracks.get(curve)
        if track is None:
            track = {'sweeps': [], 'fsp': [], 'noise': [],
                     'mean': int(self.current_setting.get('average') or 0) or None,
                     'criterion': self.technical.get('fsp_criterion'),
                     'crossed_at': None}
            self.fsp_tracks[curve] = track
        track['sweeps'].append(float(metadata.get('current_avg') or 0))
        track['fsp'].append(float(metadata.get('fsp') or 0))
        track['noise'].append(float(metadata.get('residual_noise_nv') or 0))
        criterio = track.get('criterion')
        if (criterio and track['crossed_at'] is None
                and track['fsp'][-1] >= float(criterio)):
            track['crossed_at'] = track['sweeps'][-1]
        if self.fsp_shown in (None, curve):
            self.fsp_shown = curve
            self.fmp.set_track(track)

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
                else:
                    # Marca creada/actualizada
                    self.memory[curve_name]['LatAmp'][wave] = list(coords)

            # Actualizar la tabla de detalle de todas las curvas
            self.detail_all.process_and_fill_data(self.memory)

    def active_advance_setting(self):
        """Parametros Avanzados: configuracion del EQUIPO, no del paciente.

        Lo que se acepte aca entra en la proxima captura (ver test_test);
        las curvas ya tomadas no se recalculan, igual que en un equipo real.
        """
        dialog = AbrAdvanceSettings(self.technical,
                                    self.control.cb_test.currentText(), self)
        if dialog.exec():
            self.technical = dialog.get_data()
            self.apply_window()
            # El monitor de EEG tiene que mostrar de inmediato las barras
            # de rechazo nuevas: es donde el alumno ve el efecto de lo que
            # acaba de tocar, sin esperar a promediar.
            self.eeg.set_reject(self.technical.get('artifact_reject_uv'))

    def test_changed(self, test):
        """Cambio de prueba en el combo: cada potencial trae su protocolo.

        Solo se reajusta el equipo (ventana de registro, montaje) y los
        estimulos con sentido clinico. Tasa y promediaciones NO se tocan a
        proposito: son los controles que el alumno tiene que aprender a
        configurar (ver AbrControl.randomize_initial_values).
        """
        self.technical = default_settings(test)
        self.control.apply_protocol(test)
        self.apply_window()
        self.eeg.set_reject(self.technical.get('artifact_reject_uv'))

    def apply_window(self):
        """Los gráficos siguen la ventana de registro del equipo."""
        ventana = self.technical.get('window_ms', 12)
        self.graph_r.set_windows(ventana)
        self.graph_l.set_windows(ventana)

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
            # Se guarda tambien COMO se registro: equipo, impedancias,
            # rechazo, barridos aceptados. Sin eso el informe cuenta el
            # resultado pero no el procedimiento (ver submit_report).
            self.memory[name_curve] = dict(sett, **model)
            self.memory[name_curve]['tecnica'] = self.recording_conditions()
            # Va tambien al informe: el FSP es la evidencia de por que se
            # corto el promedio en esa curva.
            self.memory[name_curve]['fsp_track'] = self.fsp_tracks.get(name_curve, {})
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
        # Oido no evaluado: el generador lo necesita para la curva sombra
        # (estimulo que cruza el craneo por sobre la atenuacion interaural
        # y hace responder a la otra coclea si no esta enmascarada).
        contra = self.abr_oi if side_idx == 0 else self.abr_od

        if case.get("repro", True) == False:
            side_letter = 'r' if side_idx == 0 else 'l'
            graph = f"graph_{side_letter}"
            repro_prev = getattr(self, graph).get_data(self.current_setting["int"])
            if repro_prev == None:
                repro_prev = 0
        else:
            repro_prev = 0


        x, y, dx, dy, repro, metadata = ABR_Curve(
            self.current_setting["int"], self.current_setting, case, repro_prev,
            [(self.count_averages * self.total_averages) * 2.5, self.current_setting['average']],
            done=self.done,
            # data_current trae 'edad' y 'gender' del paciente (ver
            # CaseBuilder.buildCaseData): con eso el generador elige la
            # poblacion normativa en vez de asumir siempre mujer adulta.
            patient=self.data_current,
            contra=contra,
            capture_id=self.current_capture_curve,
            technical=self.technical,
        )

        contra = (dx, dy) if dy is not None else None
        return (x, y), contra, repro, metadata

    #########EVENTS
    def closeEvent(self, event):
        event.accept()
