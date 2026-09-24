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

import numpy as np

from abr.ABR_generator import (ABR_Curve, ABRGenerator, agitation_factor,
                               case_quality, latency_intensity_band,
                               normative_limits, raw_eeg)
from abr.AbrAdvanceSettings import (MONTAGES, TRANSDUCERS, AbrAdvanceSettings,
                                    default_settings)
from abr.AbrControl import AbrControl
from abr.ECochG_generator import ECochG_Curve
from abr.AbrDetail import AbrDetail
from abr.AbrDetailAllCurves import AbrDetailAllCurves
from abr.AbrGraph import AbrGraph
from abr.AbrLatIntGraph import GraphLatInt
from abr.AbrReport import AbrReport
from abr.AbrSessions import (curve_order, editable_part, pack_trace,
                             session_label, unpack_trace)
from abr.AbrTable import AbrTable
from abr.EcochgTable import EcochgTable
from abr import ecochg
from abr.EEG import EEG
from abr.FSP import FSP
from abr.UI.AbrMain_ui import Ui_MainWindow
from backend.client import BackendClient
from core.base import context
from core.helpers import Preferences
from core.report_autosave import subir_ahora
from core.rng import stable_seed
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import (QComboBox, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QSizePolicy, QSpacerItem)

tr = QCoreApplication.translate

# Cada cuanto se redibuja la curva mientras promedia. Estaba en 300 ms, o
# sea tres cuadros por segundo: la promediacion se veia a los saltos. Un
# tick cuesta ~30 ms de calculo, asi que hay lugar de sobra para tres veces
# mas cuadros; la DURACION de la captura no cambia, porque la cuenta de
# ticks se multiplico por lo mismo (ver fake_averages).
TIEMPO_ENTR_PROM = 100
CUADROS_POR_TICK_VIEJO = 3
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
        # Las tablas del ECochG viven al lado de las del ABR y se muestran
        # segun la prueba activa (ver apply_test_widgets): son dos examenes
        # que no comparten NI UNA medida --ondas I-V contra razon PS/PA--
        # asi que no hay una tabla que sirva para los dos.
        self.table_ec_r = EcochgTable(0)
        self.table_ec_l = EcochgTable(1)
        self.layout_dock_values_contents.addWidget(self.table_ec_r)
        self.layout_dock_values_contents.addWidget(self.table_ec_l)
        self.layout_dock_values_contents.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        ########Conexiones de slots
        self.actionP_rametros_Avanzados.triggered.connect(self.active_advance_setting)
        # "Cambiar Caso" ya no aplica (el caso lo trae el paciente en
        # atención, ver la_super) -- el menú queda sin acción conectada.
        self.table_r.sig_measure_value.connect(self.measure_action)
        self.table_l.sig_measure_value.connect(self.measure_action)
        self.table_ec_r.sig_arm_mark.connect(self.arm_ecochg_mark)
        self.table_ec_l.sig_arm_mark.connect(self.arm_ecochg_mark)
        self.table_ec_r.sig_auto_mark.connect(self.auto_ecochg_mark)
        self.table_ec_l.sig_auto_mark.connect(self.auto_ecochg_mark)
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
        self.btn_scale_plus.setToolTip("Agrandar las curvas (menos µV en la ventana)")
        self.btn_scale_minus.setToolTip("Achicar las curvas (más µV en la ventana)")
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
        self.setup_sessions_bar()
        # Equipo (transductor, ventana, montaje, electrodos, rechazo de
        # artefacto...). Arranca en el montaje de rutina del protocolo y lo
        # edita el alumno en Parametros Avanzados. Antes el dialogo se abria
        # y se descartaba: el generador quedaba fijo en fono de insercion,
        # impedancia 3 kOhm y ventana de 12 ms.
        self.test_actual = self.control.cb_test.currentText()
        self.technical = default_settings(self.test_actual)
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
        self.show_scale()
        self.apply_test_widgets(self.control.cb_test.currentText())
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
        self.clear_sessions()
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
            # Despues de pintar: es una consulta al backend y la atencion
            # no tiene por que esperarla.
            QTimer.singleShot(0, self.fetch_sessions)

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
        limites = normative_limits(self.data_current, intensidad, stim)
        for tabla in (self.table_r, self.table_l):
            tabla.set_norms(limites)
        # ECochG: el limite de cada razon depende del ELECTRODO (ver
        # ecochg.SP_AP_LIMIT), y la latencia del PA es la de la onda I --
        # es la misma descarga, registrada desde el otro extremo.
        norma_ec = ecochg.normative(self.technical.get('montage'),
                                    (limites.get('lat') or {}).get('I'))
        for tabla in (self.table_ec_r, self.table_ec_l):
            tabla.set_norms(norma_ec)

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
        if metadata.get('ecochg_sin_datos'):
            # No es un electrodo suelto: este caso no trae
            # electrococleografia. Decir "electrodo desconectado" mandaba
            # al alumno a revisar el montaje por algo que no es del equipo.
            partes.append("SIN REGISTRO (el caso no trae ECochG)")
        elif not metadata.get('recording', True):
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
        # El estimulo solo no dice como se registro: el mismo chirp por via
        # osea es otra curva (otro normativo, otro umbral). Se rotula al
        # lado del estimulo porque en el .ui no hay campo para la via.
        estim = str(setting.get('stim', ''))
        if setting.get('transducer') == 'bone_vibrator':
            estim = f"{estim} (óseo)"
        self.detail.lbl_info_estim.setText(estim)
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
        if self.session_idx is not None:
            # Se esta mirando una sesion anterior: lo que se sube es la de
            # esta atencion, asi que primero se vuelve a ella (y se ofrece
            # guardar lo que se haya cambiado en la otra).
            self.select_session(None, allow_cancel=False)
        job = self.report_job()
        if job is None:
            return
        client = BackendClient(Preferences().get("BACKEND_URL"), context.get_resource('json/session.json'))
        ok, error = subir_ahora(job, client)
        if not ok:
            print(f"ABR: no se pudo subir el informe: {error}")

    def report_job(self):
        """El informe tal como se sube (ver core/report_autosave.py), o None
        si no hay nada que subir.

        Mirando una sesion anterior no se sube nada: lo que esta en
        pantalla es otra atencion, y la actual se sube al volver a ella.
        """
        if self.session_idx is not None:
            return None
        if not self.data_login or not self.memory:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        # El tipo es el de la prueba con la que se registro: la tabla
        # `reports` ya distingue ELECTROCOCLEO de ABR, y el informe de un
        # ECochG no dice nada de ondas I-V. Cambiar de prueba borra las
        # curvas (ver test_changed), asi que no hay sesiones mezcladas que
        # puedan quedar mal rotuladas.
        return {"appointment_id": appointment_id, "tipo": self.report_tipo(),
                "data": self.session_payload(), "images": self.export_images}

    def report_tipo(self):
        return 'ELECTROCOCLEO' if self.es_ecochg() else 'ABR'

    def export_images(self):
        """JPEG de los graficos para el informe, tal como estan en pantalla."""
        temp_dir = context.get_resource("local_cache/abr/temp")
        # En la app instalada la carpeta no existe (local_cache no va en el
        # build): sin esto el JPEG no se escribia, sin error, y la subida
        # reventaba al abrir un archivo inexistente. El informe del ABR no
        # llegaba nunca al backend.
        os.makedirs(temp_dir, exist_ok=True)
        exporters = {'0': self.graph_r, '1': self.graph_l, 'lat_int': self.graph_lat_int}
        if self.es_ecochg():
            # El ECochG no se registra en serie descendente: se hace a
            # nivel alto, que es donde el potencial de sumacion es
            # medible. El grafico latencia-intensidad queda vacio y en el
            # informe seria un cuadro en blanco con un titulo.
            exporters.pop('lat_int')
        images = {}
        for suffix, exporter in exporters.items():
            path = os.path.join(temp_dir, f'upload_{suffix}.jpg')
            try:
                exporter.export_jpg(path)
            except Exception as exc:
                print(f"ABR: no se pudo exportar {suffix} para el informe: {exc}")
                continue
            if not os.path.isfile(path):
                # QImage.save falla en silencio: sin la imagen se sube igual
                # el resto del informe.
                print(f"ABR: no se pudo exportar {suffix} para el informe")
                continue
            images[suffix] = path
        return images

    def session_payload(self):
        """La sesion en pantalla, tal como se manda al backend.

        Cada curva lleva su trazo y sus marcas en el grafico (ver
        AbrSessions): con eso se vuelve a abrir tal cual, para mirarla o
        terminar de marcarla en otra atencion.
        """
        curvas = {}
        for nombre, entrada in self.memory.items():
            curva = dict(entrada)
            grafico = self.graph_r if nombre.startswith('R') else self.graph_l
            valores = grafico.data.get(nombre)
            if valores is not None:
                curva['traza'] = pack_trace(valores)
                curva['marcas_graf'] = {
                    etiqueta: [float(v) for v in xy]
                    for etiqueta, xy in grafico.marks.get(nombre, {}).items()}
            curvas[nombre] = curva
        data = {
            'prueba': self.test_actual,
            # El equipo tal cual (ventana, montaje...): con esto la sesion
            # se vuelve a dibujar con la misma ventana y escala.
            'equipo': dict(self.technical),
            'curvas': curvas,
            # Condiciones de registro: sin esto el informe dice QUE se
            # obtuvo pero no COMO, y el procedimiento no se puede evaluar.
            # Cada curva ademas lleva las suyas (memory[curva]['tecnica']),
            # porque el alumno puede cambiar el equipo a mitad del examen.
            'tecnica': self.recording_conditions(),
            'hallazgos': self.report.text_edit_1.toPlainText(),
            'conclusion': self.report.text_edit_2.toPlainText(),
        }
        if self.es_ecochg():
            # El corrimiento por tasa es una comparacion entre dos curvas,
            # asi que no vive en ninguna: va aparte, ya resuelto, igual que
            # la razon de asimetria del VEMP.
            for lado, clave in ((0, 'OD'), (1, 'OI')):
                shift = self.ecochg_rate_shift(lado)
                if shift:
                    data.setdefault('tasa', dict(shift, oido=clave))
        return data

    def draw_session(self, data):
        """Dibuja una sesion que vino del backend (o la actual, al volver a ella)."""
        self.reset()
        curvas = data.get('curvas') or {}
        prueba = data.get('prueba')
        if not prueba:
            primera = next(iter(curvas.values()), {})
            prueba = primera.get('test') or 'ABR'
        self.set_test_silently(prueba, data.get('equipo'))
        for nombre in sorted(curvas, key=curve_order):
            entrada = curvas[nombre]
            self.memory[nombre] = {k: v for k, v in entrada.items()
                                   if k not in ('traza', 'marcas_graf')}
            self.fsp_tracks[nombre] = entrada.get('fsp_track') or {}
            traza = entrada.get('traza')
            if not traza:
                # Informe de antes de guardar trazos: quedan los numeros.
                continue
            letra = nombre[:1]
            grafico = self.graph_r if letra == 'R' else self.graph_l
            grafico.load_curve(nombre, unpack_trace(traza, entrada.get('int')),
                               entrada.get('int'), entrada,
                               traza.get('gap', 0.0), entrada.get('marcas_graf'))
            getattr(self, f'curves_{letra}').append(nombre)
        if self.es_ecochg():
            for nombre in self.memory:
                self.refresh_ecochg(nombre)
        self.detail_all.process_and_fill_data(self.memory)
        self.report.text_edit_1.setPlainText(data.get('hallazgos', ''))
        self.report.text_edit_2.setPlainText(data.get('conclusion', ''))
        for lista in (self.curves_R, self.curves_L):
            if lista:
                self.selected_(lista[-1])

    def set_test_silently(self, test, equipo=None):
        """Pone la prueba de una sesion sin pasar por test_changed.

        test_changed borra las curvas y pregunta: aca se esta abriendo una
        sesion, no cambiando de prueba.
        """
        self.control.cb_test.blockSignals(True)
        self.control.cb_test.setCurrentText(test)
        self.control.cb_test.blockSignals(False)
        self.test_actual = test
        self.technical = dict(equipo) if equipo else default_settings(test)
        self.apply_test_widgets(test)
        self.apply_window()
        self.apply_norms()

    # ------------------------------------------------------------------
    # Sesiones anteriores del mismo paciente
    # ------------------------------------------------------------------

    def setup_sessions_bar(self):
        """Combo de sesiones en la barra de arriba, junto al estado.

        Al mismo paciente se le puede hacer mas de un ABR (uno por
        atencion). Desde aca se abre uno anterior para verlo o terminarlo:
        marcas y conclusiones, nunca curvas nuevas.
        """
        # Sin sesiones anteriores no hay nada que elegir: la barra aparece
        # recien cuando fetch_sessions encuentra alguna.
        self.sessions = []
        self.session_idx = None
        self.live_snapshot = None
        self.revision_baseline = None
        self.lbl_session = QLabel(tr("AbrMainWindow", "Sesión:"))
        self.cb_session = QComboBox()
        self.cb_session.setMinimumWidth(180)
        self.cb_session.currentIndexChanged.connect(self.on_session_combo)
        self.btn_save_session = QPushButton(tr("AbrMainWindow", "Guardar cambios"))
        self.btn_save_session.setStatusTip(tr(
            "AbrMainWindow", "Guardar marcas y conclusiones de esta sesión"))
        self.btn_save_session.clicked.connect(self.save_session)
        for widget in (self.lbl_session, self.cb_session, self.btn_save_session):
            self.horizontalLayout.addWidget(widget)
        self.fill_sessions([])

    def fill_sessions(self, reports):
        self.sessions = [r for r in reports if isinstance(r.get('data'), dict)]
        self.cb_session.blockSignals(True)
        self.cb_session.clear()
        self.cb_session.addItem(tr("AbrMainWindow", "Actual"))
        for report in self.sessions:
            self.cb_session.addItem(session_label(report))
        self.cb_session.setCurrentIndex(0)
        self.cb_session.blockSignals(False)
        hay = bool(self.sessions)
        self.lbl_session.setVisible(hay)
        self.cb_session.setVisible(hay)
        self.btn_save_session.setVisible(False)

    def fetch_sessions(self):
        """Pide al backend los ABR anteriores de este alumno con este paciente."""
        if self.data_current is None:
            return
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return
        client = None
        try:
            client = BackendClient(Preferences().get("BACKEND_URL"),
                                   context.get_resource('json/session.json'))
            if not client.is_logged_in():
                return
            reports = client.get_patient_reports(appointment_id)
        except Exception as exc:
            # Sin conexion se atiende igual: solo no se ven las anteriores.
            print(f"ABR: no se pudieron traer las sesiones anteriores: {exc}")
            reports = None
        if reports is not None and self.session_idx is None:
            self.fill_sessions(reports)
        if client is not None:
            self.restore_current(client, appointment_id)

    def restore_current(self, client, appointment_id):
        """Retomar la atencion: vuelve lo que ya se habia guardado de ella.

        El informe se guarda solo mientras se atiende (ver
        core/report_autosave.py). Si la app se cerro con la atencion
        abierta, las curvas estan en el servidor y no en memoria: se
        redibujan como estaban. Solo si el alumno todavia no registro nada
        en esta vuelta -- lo que esta en pantalla no se pisa.
        """
        if self.memory or self.session_idx is not None:
            return
        try:
            guardados = client.get_my_report(appointment_id, ['ABR', 'ELECTROCOCLEO'])
        except Exception as exc:
            print(f"ABR: no se pudo recuperar lo guardado de esta atencion: {exc}")
            return
        if self.memory or self.session_idx is not None:
            return  # empezo a registrar mientras se pedia
        for informe in guardados:
            data = informe.get('data')
            if isinstance(data, dict) and data.get('curvas'):
                self.draw_session(data)
                return

    def clear_sessions(self):
        """Cambio de paciente: la lista era del anterior."""
        if self.session_idx is not None and self.live_snapshot is not None:
            # La prueba en pantalla era la de la sesion anterior.
            self.set_test_silently(self.live_snapshot.get('prueba') or 'ABR',
                                   self.live_snapshot.get('equipo'))
        self.session_idx = None
        self.live_snapshot = None
        self.revision_baseline = None
        self.set_revision_mode(False)
        self.fill_sessions([])

    def on_session_combo(self, index):
        self.select_session(index - 1 if index > 0 else None)

    def select_session(self, idx, allow_cancel=True):
        """Abre una sesion anterior (idx) o vuelve a la actual (None).

        La actual no se pierde al ir a mirar otra: se guarda entera (curvas,
        marcas, informe escrito, prueba y equipo) y se restituye al volver.
        """
        if idx == self.session_idx:
            return
        if self.state_capture != 'stopped':
            self.control.stop_capture()
        if self.session_idx is not None:
            if not self.leave_revision(allow_cancel):
                self.cb_session.blockSignals(True)
                self.cb_session.setCurrentIndex(self.session_idx + 1)
                self.cb_session.blockSignals(False)
                return
        else:
            self.live_snapshot = self.session_payload()

        if idx is None:
            self.draw_session(self.live_snapshot)
            self.live_snapshot = None
            self.revision_baseline = None
        else:
            self.draw_session(self.sessions[idx]['data'])
            self.revision_baseline = editable_part(self.session_payload())
        self.session_idx = idx
        self.cb_session.blockSignals(True)
        self.cb_session.setCurrentIndex(0 if idx is None else idx + 1)
        self.cb_session.blockSignals(False)
        self.set_revision_mode(idx is not None)

    def set_revision_mode(self, on):
        """En una sesion anterior no se registra ni se borran curvas."""
        self.control.setEnabled(not on and self.data_current is not None)
        for grafico in (self.graph_r, self.graph_l):
            grafico.curves_locked = on
        self.btn_save_session.setVisible(on)
        if on:
            self.lbl_info.setText(tr(
                "AbrMainWindow",
                "Sesión anterior: solo se editan marcas y conclusiones"))

    def revision_dirty(self):
        return (self.revision_baseline is not None
                and editable_part(self.session_payload()) != self.revision_baseline)

    def leave_revision(self, allow_cancel=True):
        """Salir de una sesion anterior: si cambio algo, guardar o no."""
        if not self.revision_dirty():
            return True
        respuesta = self.ask_save_revision(allow_cancel)
        if respuesta == 'save':
            return self.save_session()
        return respuesta == 'discard'

    def ask_save_revision(self, allow_cancel=True):
        botones = QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
        if allow_cancel:
            botones |= QMessageBox.StandardButton.Cancel
        respuesta = QMessageBox.question(
            self, tr("AbrMainWindow", "Sesión anterior"),
            tr("AbrMainWindow",
               "Cambiaste marcas o conclusiones de esta sesión.\n\n"
               "¿Guardar los cambios?"),
            botones, QMessageBox.StandardButton.Save)
        return {QMessageBox.StandardButton.Save: 'save',
                QMessageBox.StandardButton.Discard: 'discard'}.get(respuesta, 'cancel')

    def save_session(self):
        """Sube marcas y conclusiones de la sesion anterior abierta.

        El backend toma solo eso (ver ReportRevision.php): los trazos y el
        setting de esa sesion quedan como se registraron.
        """
        if self.session_idx is None:
            return False
        report = self.sessions[self.session_idx]
        data = self.session_payload()
        try:
            client = BackendClient(Preferences().get("BACKEND_URL"),
                                   context.get_resource('json/session.json'))
            client.upload_report(int(report['appointment_id']), report['tipo'],
                                 data, self.export_images())
        except Exception as exc:
            QMessageBox.warning(
                self, tr("AbrMainWindow", "Sesión anterior"),
                tr("AbrMainWindow", "No se pudieron guardar los cambios:\n{0}").format(exc))
            return False
        report['data'] = data
        self.revision_baseline = editable_part(data)
        self.lbl_info.setText(tr("AbrMainWindow", "Cambios guardados"))
        return True

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
        # Una captura a medias no sobrevive al cambio de paciente.
        self.count_averages = 0

        # Limpiar tablas
        self.table_r.clear_all()
        self.table_l.clear_all()
        self.table_ec_r.clear_all()
        self.table_ec_l.clear_all()
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
            getattr(self, f'table_ec_{table_letter}').clear_all()
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
        if self.es_ecochg():
            # La tabla del ECochG muestra las medidas de la curva que se
            # esta mirando: son de la curva, no del oido.
            self.refresh_ecochg(curve)
            self.update_detail_info(data)
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
        self.graph_r.scale(direction)
        self.graph_l.scale(direction)
        self.show_scale()

    def show_scale(self):
        # Sin redondear a entero: la escala baja a 0.75 uV y el rotulo
        # decia "1µV".
        self.lbl_scale.setText(f"{round(self.graph_r.get_scale(), 2):g}µV")

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
        if state == 'record' and self.session_idx is not None:
            # Sesion anterior abierta: se mira y se marca, no se registra.
            self.control.stop_capture()
            return
        if state == 'record':
            self.state_capture = state
            self.current_setting = self.control.get_data()
            # La via la define el transductor (Parametros Avanzados), no el
            # combo de estimulos: viaja pegada al setting de la captura
            # para que el detalle diga con que se registro esa curva.
            self.current_setting['transducer'] = self.technical.get('transducer')
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
            if self.count_averages:
                self.close_cut_capture()
        else:
            self.state_capture = state

    def close_cut_capture(self) -> None:
        """Detener a mitad de camino cierra la curva con lo que lleva.

        Sin esto el contador quedaba donde se corto y el proximo Iniciar
        seguia promediando sobre la MISMA curva (con el setting nuevo),
        en vez de abrir otra. La curva cortada queda como terminada: su
        trazo es el de los barridos que alcanzo a promediar y la tecnica
        en memoria ya dice cuantos fueron (ver recording_conditions).
        """
        self.count_averages = 0
        curve = self.current_capture_curve
        graph = self.graph_r if curve.startswith('R') else self.graph_l
        if curve in graph.data:
            graph.data[curve]['done'] = True

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
        # El setting viaja con la curva: la etiqueta decide sola si hay
        # algun parametro que la distinga del resto de la pila.
        getattr(self, graph).create_line(data_line, intencity,
                                         self.current_setting)
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
                # más largo, no solo un poco más. Ancla en 2000 = ~84 ticks
                # de 100 ms (~8.4 s), la misma duración de siempre repartida
                # en el triple de cuadros.
                a = 0.0014339 * CUADROS_POR_TICK_VIEJO
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
        if self.es_ecochg():
            # Las marcas del ECochG no son ondas: no entran en LatAmp ni en
            # la tabla de todas las curvas, que esta armada sobre I-V.
            self.ecochg_mark_changed(data)
            return
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

    # ------------------------------------------------------------------
    # ECochG: la medicion es otra (ver abr/ecochg.py y EcochgTable)
    # ------------------------------------------------------------------

    def es_ecochg(self):
        return self.control.cb_test.currentText() == 'ECochG'

    def apply_test_widgets(self, test):
        """Muestra la tabla de la prueba activa y ajusta el marcado.

        En el ABR se marcan cinco ondas con los cursores y las celdas de la
        tabla; en el ECochG se marcan cuatro puntos haciendo clic sobre la
        curva. No es una preferencia de interfaz: son dos examenes que no
        comparten ninguna medida.
        """
        ecochg_on = test == 'ECochG'
        for tabla in (self.table_r, self.table_l):
            tabla.setVisible(not ecochg_on)
        for tabla in (self.table_ec_r, self.table_ec_l):
            tabla.setVisible(ecochg_on)
            tabla.disarm()
        for grafico in (self.graph_r, self.graph_l):
            if ecochg_on:
                # El PA se pega al pico; la base y el hombro del PS caen
                # donde el alumno decida, que es la parte que se evalua.
                grafico.set_marks_mode(ecochg.MARKS, snap=('PA',), notify=True)
            else:
                grafico.set_marks_mode(('I', 'II', 'III', 'IV', 'V'))

    def arm_ecochg_mark(self, side, mark):
        """Deja armada una marca en el grafico de ese oido.

        Solo una a la vez en toda la ventana: con dos armadas, un clic en
        el grafico del otro oido pondria la marca del que no se estaba
        mirando.
        """
        propio, otro = (0, 1) if side == 0 else (1, 0)
        graficos = (self.graph_r, self.graph_l)
        tablas = (self.table_ec_r, self.table_ec_l)
        if mark is not None:
            tablas[otro].disarm()
            graficos[otro].arm_mark(None)
        graficos[propio].arm_mark(mark)

    def auto_ecochg_mark(self, side):
        """Marcado automatico del equipo sobre la curva seleccionada.

        Lo hace el mismo detector que usaria un equipo real: mira el TRAZO
        y nada mas, no el caso ni lo que el modelo dibujo (ver
        ecochg.auto_marks). Con la banda mal puesta, el nivel bajo o el
        promedio a medias marca mal, y corregirlo a mano es parte del
        examen: las marcas quedan como cualquier otra.
        """
        grafico = self.graph_r if side == 0 else self.graph_l
        curva = grafico.get_active()
        if not curva or curva not in grafico.data:
            return
        x, y = grafico.data[curva]['ipsi_xy']
        marcas = ecochg.auto_marks(np.asarray(x), np.asarray(y))
        if not marcas:
            # No hay complejo donde deberia haberlo: no se inventa uno.
            return
        for marca in ecochg.MARKS:
            if marca not in marcas:
                continue
            grafico.current_lat = marcas[marca]
            grafico.create_marks(marca)

    def ecochg_mark_changed(self, data):
        """Una marca del ECochG se puso, se movio o se borro."""
        for curve, marcas in data.items():
            if curve not in self.memory:
                continue
            guardadas = self.memory[curve].setdefault('marcas', {})
            for marca, coords in marcas.items():
                if coords is None:
                    guardadas.pop(marca, None)
                else:
                    guardadas[marca] = list(coords)
            self.refresh_ecochg(curve)

    def refresh_ecochg(self, curve):
        """Recalcula las medidas de esa curva y las muestra."""
        if not curve or curve not in self.memory:
            return
        side = 0 if curve[0] == 'R' else 1
        grafico = self.graph_r if side == 0 else self.graph_l
        tabla = self.table_ec_r if side == 0 else self.table_ec_l
        datos = grafico.data.get(curve)
        if datos is None:
            return
        x, y = datos['ipsi_xy']
        medidas = ecochg.measure_complex(
            np.asarray(x), np.asarray(y),
            (self.memory[curve].get('marcas') or {}))
        self.memory[curve]['ECochG'] = medidas
        tabla.set_medidas(medidas)
        tabla.set_rate_shift(self.ecochg_rate_shift(side))
        # La marca ya esta puesta: se suelta para que el proximo clic no
        # la vuelva a mover sin querer.
        tabla.disarm()
        grafico.arm_mark(None)

    def ecochg_rate_shift(self, side):
        """Corrimiento del PA entre la curva mas lenta y la mas rapida.

        Se arma con TODAS las curvas medidas de ese oido, no con la
        seleccionada: es una comparacion entre dos registros y el alumno
        tiene que haberlos capturado.
        """
        letra = 'R' if side == 0 else 'L'
        curvas = []
        for nombre, datos in self.memory.items():
            if not nombre.startswith(letra):
                continue
            medidas = datos.get('ECochG') or {}
            curvas.append({'rate': datos.get('rate'),
                           'ap_lat': medidas.get('ap_lat'),
                           'ap_amp': medidas.get('ap_amp')})
        return ecochg.rate_shift(curvas)

    def test_changed(self, test):
        """Cambio de prueba en el combo: cada potencial trae su protocolo.

        Solo se reajusta el equipo (ventana de registro, montaje) y los
        estimulos con sentido clinico. Tasa y promediaciones NO se tocan a
        proposito: son los controles que el alumno tiene que aprender a
        configurar (ver AbrControl.randomize_initial_values).
        """
        # Cambiar de prueba empieza un registro nuevo: el ABR y el ECochG
        # no se pueden apilar en el mismo grafico (ventanas distintas, y el
        # ECochG tiene el PA hacia abajo porque el electrodo activo es el
        # del oido), y el informe se sube con UN tipo. Se pregunta porque
        # es destructivo y el combo esta a un clic de distancia.
        if self.memory and not self.confirm_test_change(test):
            self.control.cb_test.blockSignals(True)
            self.control.cb_test.setCurrentText(self.test_actual)
            self.control.cb_test.blockSignals(False)
            return
        self.test_actual = test
        self.technical = default_settings(test)
        self.control.apply_protocol(test)
        self.apply_test_widgets(test)
        self.apply_window()
        self.apply_norms()
        self.reset()
        self.eeg.set_reject(self.technical.get('artifact_reject_uv'))

    def confirm_test_change(self, test):
        """Avisa que cambiar de prueba borra lo registrado."""
        respuesta = QMessageBox.question(
            self, tr("AbrMainWindow", "Cambiar de prueba"),
            tr("AbrMainWindow",
               "Cambiar a {0} borra las curvas registradas y el informe "
               "escrito.\n\n¿Continuar?").format(test),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        return respuesta == QMessageBox.StandardButton.Yes

    ESCALA_ABR_UV = 6.0

    def apply_window(self):
        """Los graficos siguen la ventana y la escala del equipo.

        La escala no es una preferencia de dibujo: un ECochG timpanico
        tiene el PA en 3.5 uV y en la escala del ABR (6 uV de alto, para
        ondas de medio uV) se sale por abajo y se pisa con la curva de al
        lado. Sigue al ELECTRODO, que es lo que decide cuanta respuesta
        llega.
        """
        ventana = self.technical.get('window_ms', 12)
        if self.es_ecochg():
            escala = ecochg.display_scale_uv(self.technical.get('montage'))
        else:
            escala = self.ESCALA_ABR_UV
        for grafico in (self.graph_r, self.graph_l):
            grafico.set_windows(ventana)
            grafico.set_scale(escala)
        self.show_scale()

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


        # Cuanto se lleva promediado, como FRACCION de la captura. Era
        # `count * total * 2.5`, que crece con la cantidad de ticks: el
        # promedio llegaba al tope en el 40% de la captura y el resto de
        # los ticks dibujaban exactamente el mismo trazo. O sea que la
        # segunda mitad de cada promediacion era una animacion congelada,
        # y al subir los cuadros por segundo eso empeoraba en vez de
        # mejorar.
        prom = [min(self.count_averages / max(self.total_averages, 1), 1.0),
                self.current_setting['average']]
        if self.es_ecochg():
            # Otro examen, otro generador (ver abr/ECochG_generator.py). No
            # devuelve canal contralateral ni jitter de reproducibilidad:
            # el ECochG no los tiene.
            x, y, metadata = ECochG_Curve(
                self.current_setting["int"], self.current_setting, case, prom,
                done=self.done, patient=self.data_current,
                capture_id=self.current_capture_curve,
                technical=self.technical)
            return (x, y), None, 0, metadata

        x, y, dx, dy, repro, metadata = ABR_Curve(
            self.current_setting["int"], self.current_setting, case, repro_prev,
            prom,
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
