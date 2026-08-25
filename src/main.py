from pathlib import Path
import sys
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton

import Agenda
import Audiometer
import create_a
import ListWords
import login as Ui_login
import Z
from base import context
from lib.h_win import FrameSubMdi, MdiArea
from lib.helpers import CasesOffline, CreatePatient, Preferences, Shedule, Storage, marcar_entry_atendido
from lib.ui_helpers import MoveWindow, ToolBar, show_hide, toggle_max_min
from UI.Ui_command_voice_A import Ui_Form as commandVoiceA
from UI.Ui_CVC import Ui_CVC
from UI.Ui_Main import Ui_MainWindow
from Logger import Logger

# Definir la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'resources' / 'config' / 'config.json'
LOG_FILE = BASE_DIR / 'log_file.txt'

sys.stdout = Logger(LOG_FILE)

__VERSION__ = 'v0.9.8'
Preferences = Preferences()
APPS = Preferences.get("APP")
SECTORS = Preferences.get("SECTORS")
BOXS = Preferences.get("BOXS")
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")
ONLINE = "development" if Preferences.get("test") else Preferences.get("online")


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
        self.btn_login.clicked.connect(self.activate_soft)

    def set_mdi_area(self):
        """Crea el objeto mdi_area"""
        self.mdi_area = MdiArea()
        self.horizontalLayout.addWidget(self.mdi_area)

    def create_variables(self):
        """Crea las variables necesarias para el funcionamiento del programa"""
        self.data_login = None
        self.data_current = None
        self.subw = None
        self.sectors_lbl = SECTORS
        self.modules = Storage(len(APPS))
        self.var_list_word = Storage(2)

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
            show_hide(self.modules, 0)
            self.lbl_name.setText(f"{user}")
            self.btn_login.setText("Cerrar Sesión")
            self.data_login = data
            self.refresh_data()
            self.btns_actions()

    def logout(self):
        """Cierra la sesión actual"""
        self._close_sub_windows()
        self.lbl_name.setText("")
        self.btn_login.setText("Ingresar")
        self.data_login = None
        self.data_current = None

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
        """Marca al paciente como atendido, carga su caso e hidrata los módulos"""
        shedule = Shedule()
        agenda = shedule.data.setdefault("agenda_1", {})
        entry = agenda.get(key)
        if entry is None:
            return

        case_id = entry[7]
        marcar_entry_atendido(entry, self.data_login["user"])
        shedule.set(shedule.data)

        self.data_current = CasesOffline().get_cases()[case_id]

        if self.subw and "AGENDA" in self.subw:
            self.subw["AGENDA"].obj.refresh()

        self._hydrate_modules()
        if self.data_current:
            self.changeStateBtnAreas(self.frameAction, self.data_current["box"])

    def _hydrate_modules(self):
        """Carga self.data_current en los módulos ya construidos"""
        if self.data_current is None:
            return
        try:
            self.subw_a.obj.la_super(self.data_current)
            self.subw_z.obj.la_super(self.data_current)
            self.subw_w.obj.la_super(self.data_current)
        except AttributeError:
            pass

    def load_sub_windows(self):
        """Carga las subventanas"""
        self.subw_a = FrameSubMdi(Audiometer.Audiometer(self.data_current))
        subw_agenda = FrameSubMdi(Agenda.Agenda(self.data_login["permission"], self))
        subw_voice = FrameSubMdi(ComandVoiceA())
        self.subw_w = FrameSubMdi(ListWords.ListWords(self.data_current))
        self.subw_z = FrameSubMdi(Z.ZControl())

        if self.data_login["permission"] == 777:
            subw_create_a = FrameSubMdi(create_a.CreateA(self.data_login["user"], self))
            self.subw["CREATE_A"] = subw_create_a

        self.subw["A"] = self.subw_a
        self.subw["AGENDA"] = subw_agenda
        self.subw["CVOICE"] = subw_voice
        self.subw["W"] = self.subw_w
        self.subw["Z"] = self.subw_z
        self._hydrate_modules()
        self.connect_signals()

    def activate_listWords(self):
        if self.subw_a.obj.lbl_prueba.text() == "Logoaudiometría":
            self.activate_soft("W")

    def speechlist_mode(self, state):
        self.subw["W"].obj.update_state(state)

    def connect_signals(self):
        self.subw["CVOICE"].obj.btn_checked.connect(self.subw["A"].obj.supra)
        self.subw["A"].obj.signal_speech.connect(self.speechlist_mode)

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
        self.btn_cmd_voice = QPushButton("Comandos de voz")
        self.btn_cmd_voice.setObjectName("btn_CVOICE")
        self.btn_cmd_voice.clicked.connect(self.activate_soft)
        self.layoutAction.addWidget(self.btn_cmd_voice)
        self.btn_list_words = QPushButton("Listas de Palabras")
        self.btn_list_words.setObjectName("btn_W")
        self.btn_list_words.clicked.connect(self.activate_listWords)
        self.layoutAction.addWidget(self.btn_list_words)


if __name__ == '__main__':
    window = MainWindow()
    Preferences.get_style(window)
    window.show()
    exit_code = context.app.exec()
    sys.exit(exit_code)
