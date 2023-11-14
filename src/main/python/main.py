#-*- coding: utf-8 -*-
"""
LabSim: LabSim is a simulation environment for practical
"""
__VERSION__ = 'v0.9.8'
# pylint: disable=no-name-in-module
import sys

from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton

import Audiometer
import create_a
import Agenda
import login as Ui_login
from base import context
from lib.h_win import FrameSubMdi, MdiArea
from lib.helpers import Preferences, Storage, CreatePatient
from lib.main.func_users import XLSReader
from lib.ui_helpers import ToolBar, show_hide, MoveWindow, toggle_max_min
from UI.Ui_Main import Ui_MainWindow
from UI.Ui_CVC import Ui_CVC
from UI.Ui_command_voice_A import Ui_Form as commandVoiceA
import contextlib
import ListWords

Preferences = Preferences()
APPS = Preferences.get("APP")
SECTORS = Preferences.get("SECTORS")
BOXS = Preferences.get("BOXS")
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")
if Preferences.get("test"):
    ONLINE = "development"
else:
    ONLINE = Preferences.get("online")
#name = CreatePatient()
#print(name.generar_nombre("men", social_name=True))


# Uso
#file_path = "cases/NominaAlumnos.xls"
#reader = XLSReader(file_path)
#reader.read_xls()
#data = reader.get_data()
#print(data)



class CVC (Ui_CVC):
    def __init__(self) -> None:
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
        text = btn.text()
        text = text.replace(" ", "_")
        text = text.replace("?", "")
        text = text.replace("¿", "")
        text = text.lower()
        self.btn_checked.emit(text)

class MainWindow(QMainWindow, Ui_MainWindow, ToolBar):
    """Ventana Principal"""
    # pylint: disable=too-many-instance-attributes,attribute-defined-outside-init
    # Eight is reasonable in this case.

    def __init__(self) -> None:
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.create_variables() #Crea las variables
        self.set_mdi_area() #Configura el objeto mdi_area
        layout=(self.horizontalLayout_5, self.layoutTest)
        self.create_sub_windows() #Crea las subventanas

        ToolBar.__init__(self, self.sender,
                         BOXS, APPS, layout,
                         self.frame_sec,self.modules,
                         self.mdi_area, self.size,
                         self.subw) #Configura la barra de herramientas

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(f"LabSim {__VERSION__}")
        self.lbl_title.setText(f"LabSim {__VERSION__}")
        self.configure_btn() #Configura los botones
        MoveWindow(self).set_movewindow()#Configura el movimiento de la ventana con el mouse

    def configure_btn(self) -> None:
        """Se configuran los botones de la ventana"""
        self.btn_salir.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(lambda:toggle_max_min(self))
        self.btn_login.clicked.connect(self.activate_soft)

    def set_mdi_area(self) -> None:
        """crea el objeto mdi_area"""
        self.mdi_area = MdiArea()
        self.horizontalLayout.addWidget(self.mdi_area)

    def create_variables(self) -> None:
        """Crea las variables necesarias para el funcionamiento del programa"""
        self.data_login = None #Datos de login
        self.data_current = None #Datos del caso actual
        self.subw = None #Lista de subventanas
        self.sectors_lbl = SECTORS #Lista de sectores
        #Memorias
        self.modules = Storage(len(APPS)) #modulos
        self.var_list_word = Storage(2)

    def create_sub_windows(self) -> None:
        """Crea las subventanas"""
        self.create_sw_login()

    def create_sw_login(self) -> None:
        """crea la subventana login"""
        subw_login = FrameSubMdi(Ui_login.MainLogin(ONLINE))
        subw_login.obj.data_login_signal.connect(self._data_login)
        self.subw = {"LOGIN": subw_login}

    @Slot(dict)
    def _data_login(self, data:dict) -> None:
        """Slot Recibe el data de la subventana login

        Args:
            data (dict): data obtenida desde el login_data_login
        """
        #print(f"data in main: {data}")
        user = data["user"]
        if user is False:
            self.logout()
        else:
            show_hide(self.modules, 0)
            text = f"{data['user']}"
            self.lbl_name.setText(text)
            self.btn_login.setText("Cerrar Sesión")
            self.data_login = data
            self.combo_case()
            self.refresh_data()
            self.btns_actions() #este debo unirlo al toolbar


    def logout(self) -> None:
        """Cierra la sesion actual"""
        self.cmb_case.currentTextChanged.disconnect()
        self.cmb_case.clear()
        self.lbl_name.setText("")
        self.btn_login.setText("Ingresar")
        self.data_login = None
        self.data_current = None
    def combo_case(self) -> None:
        """Crea el combo de casos"""
        self.cmb_case.clear()
        self.cmb_case.currentTextChanged.connect(self.change_case)
        for i in self.data_login["cases"]:
            self.cmb_case.addItem(f"caso : {i}")

    def change_case(self, text:str) -> None:
        """ Change
        Args:
            text(str): string del combo
        """
        number_case = text.strip("caso : ")
        self.data_current = self.data_login["cases"][number_case]
        try:
            self.subw_a.obj.la_super(self.data_current)
        except AttributeError:
            pass

    def load_sub_windows(self) -> None:
        """Carga las subventanas"""
        self.subw_a = FrameSubMdi(Audiometer.Audiometer(self.data_current))
        subw_agenda = FrameSubMdi(Agenda.Agenda(self.data_login["permission"],self))
        subw_voice = FrameSubMdi(ComandVoiceA())
        subw_w = FrameSubMdi(ListWords.ListWords(self.data_current))

        if self.data_login["permission"] == 777:
            subw_create_a = FrameSubMdi(create_a.CreateA())
            self.subw["CREATE_A"]=subw_create_a
            
        self.subw["A"] = self.subw_a
        self.subw["AGENDA"]=subw_agenda
        self.subw["CVOICE"]=subw_voice
        self.subw["W"] = subw_w

        #self.subw_cvc = FrameSubMdi(CVC())
        self.connect_signals()
        
    def activate_listWords(self):
        if self.subw_a.obj.lbl_prueba.text() == "Logoaudiometría":
            self.activate_soft_("W")
        """

        if self.var_list_word.get(0):
            if self.modules.is_full(pos_z):
                self.modules.get(pos_z).show()
            else:
                self.create_sub_window(self.subw_w, name, pos_z, size=size)
        else:
            with contextlib.suppress(AttributeError):
                self.modules.get(pos_z).hide()
        """
    def speechlist_mode(self, state):
        #self.var_list_word.getAll(True)
        #self.var_list_word.list_set(state, False)
        #self.var_list_word.getAll(True)
        self.activate_listWords()
        self.subw["W"].obj.update_state(state)
        self.subw["W"].obj.playable[1] = state[2]
        self.subw["W"].obj.playable[2] = state[3]
        self.subw["W"].obj.playable[3] = state[4]
        self.subw["W"].obj.playable[0] = bool(state[1])

    def connect_signals(self):
        self.subw["CVOICE"].obj.btn_checked.connect(self.subw["A"].obj.supra)
        self.subw["A"].obj.signal_speech.connect(self.speechlist_mode)

    def refresh_data(self):
        self.load_sub_windows()
        self.btns_seccion()
        self.changeStateBtnAreas(self.frameAction, self.data_current["box"])
        
    #ESTE DEBO SACARLO CON LOS COMANDOS
    def btns_actions(self):
        #command
        self.btn_cmd_voice = QPushButton("comandos de voz")
        self.btn_cmd_voice.setObjectName("btn_CVOICE")
        self.btn_cmd_voice.clicked.connect(self.activate_soft)
        self.layoutAction.addWidget(self.btn_cmd_voice)
        self.btn_list_words = QPushButton("Listas de Palabras")
        self.btn_list_words.setObjectName("btn_W")
        self.btn_list_words.clicked.connect(self.activate_soft)
        self.layoutAction.addWidget(self.btn_list_words)





if __name__ == '__main__':
    window = MainWindow()
    Preferences.get_style(window)
    window.show()
    exit_code = context.app.exec()
    sys.exit(exit_code)
