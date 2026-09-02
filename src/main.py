from pathlib import Path
import sys
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QMessageBox

from agenda import Agenda, create_a
from agenda.Agenda import ChatPacienteWidget
from audiometria import Audiometer, ListWords
from auth import login as Ui_login
from impedanciometria import Z
from core.base import context
from core.h_win import FrameSubMdi, MdiArea
from core.helpers import (CasesOffline, CreatePatient, Preferences, Shedule, Storage,
                          marcar_entry_atendiendo, marcar_entry_atendido, entry_esta_cancelada,
                          reset_backend_session)
from core.ui_helpers import MoveWindow, ToolBar, show_hide, toggle_max_min
from audiometria.UI.Ui_command_voice_A import Ui_Form as commandVoiceA
from cvc.UI.Ui_CVC import Ui_CVC
from core.UI.Ui_Main import Ui_MainWindow
from core.Logger import Logger
from backend.client import BackendClient
from backend.log_queue import LogUploaderThread, get_log_queue
from backend.sync_thread import SyncThread

# Definir la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'resources' / 'config' / 'config.json'
LOG_FILE = BASE_DIR / 'log_file.txt'

__VERSION__ = 'v0.9.8'
Preferences = Preferences()
APPS = Preferences.get("APP")
SECTORS = Preferences.get("SECTORS")
BOXS = Preferences.get("BOXS")
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")
ONLINE = "development" if Preferences.get("test") else Preferences.get("online")

# Cola local de logs de acciones (ver lib/backend/log_queue.py). Se crea
# siempre -- escribir en ella es solo un insert sqlite local, nunca toca
# la red -- pero solo se sube al backend si ONLINE == "backend" (ver
# MainWindow._data_login). En otros modos simplemente no se vacía nunca.
LOCAL_LOG_QUEUE = get_log_queue()
# Logger sin log_queue: stdout (prints de debug regados por todo el código)
# ya no se sube al backend -- era 87% del volumen y puro ruido interno
# ("cambio el sender", "True", [agenda_filter]...). Las acciones reales del
# alumno (audio_stim_button, z_dial_change, etc.) se suben aparte, con
# nombre propio, vía log_queue.push() explícito en Audiometer.py y Z.py.
sys.stdout = Logger(LOG_FILE)


class CVC(Ui_CVC):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class ComandVoiceA(QWidget, commandVoiceA):
    btn_checked = Signal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.buttonGroup.buttonClicked.connect(self.state)

    def state(self):
        btn = self.buttonGroup.checkedButton()
        text = btn.text().replace(" ", "_").replace("?", "").replace("¿", "").lower()
        self.btn_checked.emit(text)


class MainWindow(QMainWindow, Ui_MainWindow, ToolBar):
    """Ventana Principal"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cmb_case.setVisible(False)
        self.cmb_case.setEnabled(False)
        self.create_variables()
        self.set_mdi_area()
        self.create_sub_windows()
        layout = (self.horizontalLayout_5, self.layoutTest)

        ToolBar.__init__(self, self.sender, BOXS, APPS, layout, self.frame_sec, self.modules, self.mdi_area, self.size, self.subw)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(f"LabSim {__VERSION__}")
        self.lbl_title.setText(f"LabSim {__VERSION__}")
        self.configure_btn()
        MoveWindow(self).set_movewindow()

    def configure_btn(self):
        """Configura los botones de la ventana"""
        self.btn_salir.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(lambda: toggle_max_min(self))
        self.btn_login.clicked.connect(self.toggle_login)

    def set_mdi_area(self):
        """Crea el objeto mdi_area"""
        self.mdi_area = MdiArea()
        self.horizontalLayout.addWidget(self.mdi_area)

    def create_variables(self):
        """Crea las variables necesarias para el funcionamiento del programa"""
        self.data_login = None
        self.data_current = None
        self.data_current_key = None
        self.paciente_actual = None
        self.subw = None
        self.sectors_lbl = SECTORS
        self.modules = Storage(len(APPS))
        self.var_list_word = Storage(2)
        self.log_uploader = None
        self.sync_thread = None

    def create_sub_windows(self):
        """Crea las subventanas"""
        self.create_sw_login()

    def create_sw_login(self):
        """Crea la subventana login"""
        subw_login = FrameSubMdi(Ui_login.MainLogin(ONLINE))
        subw_login.obj.data_login_signal.connect(self._data_login)
        self.subw = {"LOGIN": subw_login}

    @Slot(dict)
    def _data_login(self, data):
        """Recibe el data de la subventana login"""
        user = data["user"]
        if not user:
            self.logout()
        else:
            reset_backend_session()
            show_hide(self.modules, 0)
            self.lbl_name.setText(f"{user}")
            self.btn_login.setText("Cerrar Sesión")
            self.data_login = data
            LOCAL_LOG_QUEUE.push("session_login", {
                "user": data.get("user"),
                "name": data.get("name"),
                "permission": data.get("permission"),
            })
            self.refresh_data()
            self.btns_actions()
            self._start_log_uploader()
            self._start_sync_thread()

    def _start_log_uploader(self):
        """Sube en lotes los logs de acciones acumulados (ver log_queue.py).
        Solo aplica en modo backend y si el login realmente dejó un token."""
        if ONLINE != "backend":
            return
        client = BackendClient(Preferences.get("BACKEND_URL"), context.get_resource('json/session.json'))
        if not client.is_logged_in():
            return
        self.log_uploader = LogUploaderThread(LOCAL_LOG_QUEUE, client)
        self.log_uploader.start()

    def _stop_log_uploader(self):
        if self.log_uploader is not None:
            self.log_uploader.stop()
            self.log_uploader = None

    def _start_sync_thread(self):
        """Poll periódico al backend (ver sync_thread.py): si el admin edita
        la agenda desde otra terminal, esta refresca sola en el próximo ciclo."""
        if ONLINE != "backend":
            return
        client = BackendClient(Preferences.get("BACKEND_URL"), context.get_resource('json/session.json'))
        if not client.is_logged_in():
            return
        self.sync_thread = SyncThread(client)
        self.sync_thread.sync_ok.connect(self._on_backend_sync)
        self.sync_thread.start()

    def _on_backend_sync(self, _delta):
        # refresh_async: este callback corre en cada ciclo de polling (15s);
        # refresh() normal dispara una consulta de red nueva y BLOQUEANTE
        # (Shedule() -> get_full_state), que con el backend caído congelaba
        # toda la ventana hasta 10s por ciclo (timeout SSL).
        agenda_win = self.subw.get("AGENDA") if self.subw else None
        if agenda_win is not None:
            agenda_win.obj.refresh_async()

    def _stop_sync_thread(self):
        if self.sync_thread is not None:
            self.sync_thread.stop()
            self.sync_thread = None

    def toggle_login(self):
        """Cierra sesión de inmediato si hay una activa, si no abre la ventana de login"""
        if self.data_login:
            self.logout()
        else:
            self.activate_subwindow(self.size, "LOGIN", self.subw["LOGIN"])

    def logout(self):
        """Cierra la sesión actual"""
        LOCAL_LOG_QUEUE.push("session_logout", {
            "user": self.data_login.get("user") if self.data_login else None,
        })
        if self.log_uploader is not None:
            # Sube ahora mismo: si esperamos al ciclo normal, este evento
            # queda en la cola local hasta el próximo login (el hilo se
            # detiene abajo).
            self.log_uploader.flush_now()
        self._stop_log_uploader()
        self._stop_sync_thread()
        self._close_sub_windows()
        login_subw = self.subw.get("LOGIN") if self.subw else None
        if login_subw is not None:
            # El login se logueó via toggle_login (btn "Cerrar Sesión"), no
            # via el btn "Salir" propio de la ventana de login -- por eso
            # login.py:logout() (que limpia y reactiva los campos) nunca se
            # ejecuta acá. Sin esto, la próxima vez que se abre la ventana
            # de login los campos quedan deshabilitados con el usuario
            # anterior escrito.
            login_subw.obj._enable_widgets()
        self.lbl_name.setText("")
        self.btn_login.setText("Ingresar")
        self.data_login = None
        self.data_current = None
        self.data_current_key = None
        self.paciente_actual = None

    def _close_sub_windows(self):
        """Cierra todas las subventanas abiertas (excepto LOGIN) y deshidrata sus datos"""
        login_pos_z = self.apps["LOGIN"][2]
        for pos_z in self.modules.length(True):
            if pos_z == login_pos_z:
                continue
            sub = self.modules.get(pos_z)
            if sub is not None:
                self.mdi_area.removeSubWindow(sub)
                sub.deleteLater()
                self.modules.set(pos_z, None)

        login_subw = self.subw.get("LOGIN") if self.subw else None
        self.subw = {"LOGIN": login_subw} if login_subw else None

        for attr in ("subw_a", "subw_w", "subw_z"):
            if hasattr(self, attr):
                delattr(self, attr)

    def atender_paciente(self, key):
        """
        Inicia o retoma la atención (estado 'atendiendo'), carga el caso e hidrata
        los módulos. Se llama tanto la primera vez como al retomar un paciente que
        ya estaba en atención (tras reabrir la app o al volver desde otro paciente).
        """
        if self.data_login["permission"] == 777:
            return  # el admin no atiende pacientes, para eso existe un usuario básico de prueba

        shedule = Shedule()
        agenda = shedule.data.setdefault("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            return
        if entry_esta_cancelada(entry):
            return  # el admin canceló la cita mientras estaba visible

        case_id = entry[7]
        marcar_entry_atendiendo(entry, self.data_login["user"])
        shedule.set(shedule.data)

        self.data_current = CasesOffline().get_cases()[case_id]
        self.data_current_key = key

        if self.subw and "AGENDA" in self.subw:
            self.subw["AGENDA"].obj.refresh()

        self._hydrate_modules()
        if self.data_current:
            self.changeStateBtnAreas(self.frameAction, self.data_current["box"])

        rut = entry[2] if len(entry) > 2 else ""
        fecha_nac = entry[5] if len(entry) > 5 else ""
        self.statusbar.showMessage(f"Estás atendiendo a: RUT {rut} — Fecha de nacimiento {fecha_nac}")

        nombre = f"{entry[3] if len(entry) > 3 else ''} {entry[4] if len(entry) > 4 else ''}".strip()
        procedimiento = entry[6] if len(entry) > 6 else ""
        try:
            edad, _, _ = CreatePatient().get_age_from_rut(int(rut))
        except (TypeError, ValueError):
            edad = 0
        try:
            appointment_id = int(key)
        except (TypeError, ValueError):
            appointment_id = None
        self.paciente_actual = {
            "case_id": case_id, "nombre": nombre or "el paciente",
            "edad": edad, "procedimiento": procedimiento, "appointment_id": appointment_id,
        }

    def atender_paciente_prueba(self, key):
        """
        Admin: carga el caso `key` en los módulos (audiómetro, chat con el
        paciente, etc.) para probarlo. A diferencia de atender_paciente(), NO
        marca "atendiendo" ni escribe en attendances/agenda -- no deja rastro
        en la base de datos, es solo para verificar que un caso funciona.
        """
        shedule = Shedule()
        agenda = shedule.data.get("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            return

        case_id = entry[7] if len(entry) > 7 else None
        if not case_id:
            return

        self.data_current = CasesOffline().get_cases()[case_id]
        self.data_current_key = key

        self._hydrate_modules()
        if self.data_current:
            self.changeStateBtnAreas(self.frameAction, self.data_current["box"])

        rut = entry[2] if len(entry) > 2 else ""
        nombre = f"{entry[3] if len(entry) > 3 else ''} {entry[4] if len(entry) > 4 else ''}".strip()
        procedimiento = entry[6] if len(entry) > 6 else ""
        try:
            edad, _, _ = CreatePatient().get_age_from_rut(int(rut))
        except (TypeError, ValueError):
            edad = 0
        self.paciente_actual = {
            "case_id": case_id, "nombre": nombre or "el paciente",
            "edad": edad, "procedimiento": procedimiento,
            "appointment_id": None,  # "prueba" -- nunca se guarda el chat de esto
        }
        self.statusbar.showMessage(f"[PRUEBA] Caso cargado: {nombre or case_id} (no se guarda atención)")

    def cerrar_atencion(self, key, nota):
        """Cierra la atención (estado 'atendido') guardando la nota de atención del estudiante"""
        if self.data_login["permission"] == 777:
            return  # el admin no atiende pacientes, para eso existe un usuario básico de prueba

        shedule = Shedule()
        agenda = shedule.data.setdefault("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            return

        marcar_entry_atendido(entry, self.data_login["user"], nota)
        shedule.set(shedule.data)

        if self.data_current_key == key:
            self.data_current_key = None
            self.data_current = None
            self.paciente_actual = None
            self._hydrate_modules()

        if self.subw and "AGENDA" in self.subw:
            self.subw["AGENDA"].obj.refresh()

        self.statusbar.clearMessage()

    def _hydrate_modules(self):
        """Carga self.data_current en los módulos ya construidos, o los
        deshidrata (data_current=None) para que dejen de loguear acciones
        bajo el caso/paciente ya cerrado."""
        for attr in ("subw_a", "subw_z", "subw_w"):
            try:
                getattr(self, attr).obj.la_super(self.data_current, self.data_current_key)
            except AttributeError:
                pass

    def load_sub_windows(self):
        """Carga las subventanas"""
        self.subw_a = FrameSubMdi(Audiometer.Audiometer(self.data_current))
        subw_agenda = FrameSubMdi(Agenda.Agenda(self.data_login["permission"], self))
        subw_voice = FrameSubMdi(ComandVoiceA())
        subw_chat = FrameSubMdi(ChatPacienteWidget())
        self.subw_w = FrameSubMdi(ListWords.ListWords(self.data_current))
        self.subw_z = FrameSubMdi(Z.ZControl())

        if self.data_login["permission"] in (555, 777):  # docente y admin, no alumno
            subw_create_a = FrameSubMdi(create_a.CreateA(self.data_login["user"], self))
            self.subw["CREATE_A"] = subw_create_a

        self.subw["A"] = self.subw_a
        self.subw["AGENDA"] = subw_agenda
        self.subw["CVOICE"] = subw_voice
        self.subw["CHAT"] = subw_chat
        self.subw["W"] = self.subw_w
        self.subw["Z"] = self.subw_z
        self._hydrate_modules()
        self.connect_signals()

    def activate_listWords(self):
        if self.subw_a.obj.lbl_prueba.text() == "Logoaudiometría":
            self.activate_auto("W")

    def speechlist_mode(self, state):
        self.subw["W"].obj.update_state(state)

    def connect_signals(self):
        self.subw["CVOICE"].obj.btn_checked.connect(self.subw["A"].obj.supra)
        self.subw["A"].obj.signal_speech.connect(self.speechlist_mode)
        self.subw["W"].obj.level_changed.connect(
            lambda level: self.subw["A"].obj._on_player_level(self.subw["W"].obj.channel, level))

    def refresh_data(self):
        self.load_sub_windows()
        self.btns_seccion()
        if self.data_current:
            self.changeStateBtnAreas(self.frameAction, self.data_current["box"])

    def btns_actions(self):
        for i in reversed(range(self.layoutAction.count())):
            widget = self.layoutAction.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.btn_chat_paciente = QPushButton("Hablar con el paciente")
        self.btn_chat_paciente.setObjectName("btn_chat_paciente")
        self.btn_chat_paciente.clicked.connect(self.abrir_chat_paciente)
        self.layoutAction.addWidget(self.btn_chat_paciente)
        self.btn_cmd_voice = QPushButton("Comandos de voz")
        self.btn_cmd_voice.setObjectName("btn_CVOICE")
        self.btn_cmd_voice.clicked.connect(self.activate_soft)
        self.layoutAction.addWidget(self.btn_cmd_voice)
        self.btn_list_words = QPushButton("Listas de Palabras")
        self.btn_list_words.setObjectName("btn_W")
        self.btn_list_words.clicked.connect(self.activate_listWords)
        self.layoutAction.addWidget(self.btn_list_words)

    def abrir_chat_con(self, case_id, nombre, edad, procedimiento, appointment_id=None):
        """Abre (o trae al frente) la subventana MDI de chat con el paciente,
        reapuntada al caso indicado. appointment_id=None = no se guarda el
        chat (ver ChatPacienteWidget.set_paciente)."""
        self.subw["CHAT"].obj.set_paciente(case_id, nombre, edad, procedimiento, appointment_id)
        self.activate_auto("CHAT")

    def abrir_chat_paciente(self):
        """Abre el chat con el paciente simulado por LLM del caso que se está atendiendo."""
        if not self.paciente_actual:
            QMessageBox.information(self, "Hablar con el paciente", "No estás atendiendo un paciente.")
            return
        p = self.paciente_actual
        self.abrir_chat_con(p["case_id"], p["nombre"], p["edad"], p["procedimiento"], p.get("appointment_id"))

    def closeEvent(self, event):
        self._stop_log_uploader()
        self._stop_sync_thread()
        super().closeEvent(event)


if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        from core.updater import apply_update_and_restart, check_for_update
        update = check_for_update(__VERSION__)
        if update is not None:
            tag, download_url = update
            resp = QMessageBox.question(
                None,
                "Actualización disponible",
                f"Hay una nueva versión disponible ({tag}).\n"
                "¿Actualizar ahora? La aplicación se cerrará y volverá a abrir sola.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if resp == QMessageBox.Yes:
                apply_update_and_restart(download_url)  # no vuelve

    window = MainWindow()
    Preferences.get_style(window)
    window.show()
    exit_code = context.app.exec()
    sys.exit(exit_code)
