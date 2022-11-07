#-*- coding: utf-8 -*-
"""
LabSim: LabSim is a simulation environment for practical
"""
__VERSION__ = 'v0.9.5'
# pylint: disable=no-name-in-module
import sys

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QMainWindow

import Audiometer
import Agenda
import login as Ui_login
from base import context
from lib.h_win import FrameSubMdi, MdiArea
from lib.helpers import Preferences, Storage
from lib.ui_helpers import ToolBar, show_hide, MoveWindow, toggle_max_min
from UI.Ui_Main import Ui_MainWindow
from UI.Ui_CVC import Ui_CVC

Preferences = Preferences()
APPS = Preferences.get("APP")
SECTORS = Preferences.get("SECTORS")
BOXS = Preferences.get("BOXS")
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")
ONLINE = Preferences.get("online")

class CVC (Ui_CVC):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

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

    def create_sub_windows(self) -> None:
        """Crea las subventanas"""
        self.create_sw_login()

    def create_sw_login(self) -> None:
        """crea la subventana login"""
        subw_login = FrameSubMdi(Ui_login.MainLogin(ONLINE))
        subw_login.ui_ui.data_login_signal.connect(self._data_login)
        self.subw = {"LOGIN": subw_login}

    @Slot(dict)
    def _data_login(self, data:dict) -> None:
        """Slot Recibe el data de la subventana login

        Args:
            data (dict): data obtenida desde el login
        """
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

    def load_sub_windows(self) -> None:
        """Carga las subventanas"""
        #self.subw_a = FrameSubMdi(Audiometer.Audiometer(self.data_current))
        #self.subw["A"] = self.subw_a
        subw_agenda = FrameSubMdi(Agenda.Agenda())
        self.subw["AGENDA"]=subw_agenda
        #self.subw_cvc = FrameSubMdi(CVC())
        #self.subw_a.ui_ui.signal_speech.connect(self.speechlist_mode)

    def refresh_data(self):
        self.load_sub_windows()
        self.btns_seccion()
        self.changeStateBtnAreas(self.frameAction, self.data_current["box"])



if __name__ == '__main__':
    window = MainWindow()
    Preferences.get_style(window)
    window.show()
    exit_code = context.app.exec()
    sys.exit(exit_code)
