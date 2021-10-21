# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                          VER. 0.7.5                           #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
#pip install https://build-system.fman.io/pro/12a9a98c-755b-4d95-9c60-a17ae1a74d6c/1.0.8#egg=fbs
#https://f002.backblazeb2.com/file/TMEduca/LabSim/LabSimSetup0.8.4.exe

__VERSION__ = 'v0.9.0'
import json
import sys
import time

import requests
from fbs_runtime.application_context.PyQt6 import ApplicationContext
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtWidgets import (QMainWindow, QMdiSubWindow, QMessageBox,
                             QPushButton, QWidget, QMdiArea, QMenu)
from PyQt6.QtGui import QPixmap, QPainter, QCursor


import ABR
import Audiometer
import ListWords
import login as Ui_login
import Z
from lib.helpers import Preferences, Storage
from UI.Ui_Main import Ui_MainWindow
from UI.Ui_command_voice_A import Ui_Form as commandVoiceA
from lib.h_win import FrameSubMdi, MoveWin

Preferences = Preferences()
APPS = Preferences.get("APP")
SECTORS = Preferences.get("SECTORS")
BOXS = Preferences.get("BOXS")
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")


    

class MdiArea(QMdiArea):
    def __init__(self):
        super(MdiArea, self).__init__()
        self.mousePressEvent = self.move_window
        self.documentMode = True
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.currentSubWindow() is None:
            # call the base implementation to draw the default colored background
            # create the painter *on the viewport*
            painter = QPainter(self.viewport())
            w = event.rect().width()
            h = event.rect().height()
            img = QPixmap(appctxt.get_resource("img/LogoBN.png"))
            img_x = w/2 - 200/2
            img_y = h/2 - 200/2
            painter.drawPixmap(int(img_x), int(img_y), 200, 200, img)
            painter.end()

    def move_window(self, e):
        if e.buttons() == Qt.RightButton:  
            contextMenu = QMenu(self)
            ordenar=contextMenu.addMenu("Ordenar")
            ordenar.addAction("Cascada", self.cascadeSubWindows)
            ordenar.addAction("Azulejos", self.tileSubWindows)
            ordenar.addAction("Cerrar todo", self.closeAll)
            contextMenu.exec_(self.mapToGlobal(e.pos()))

    def closeAll(self):
        i = self.parent().parent().parent()
        try:
            for j in i.Modules.length(True):
                if i.Modules.get(j) != None:
                    i.Modules.get(j).hide()
        except:
            pass


class ComandVoiceA(QWidget, commandVoiceA):
    btn_checked = pyqtSignal(str)
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


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("LabSim {}".format(__VERSION__))
        self.lbl_title.setText("LabSim {}".format(__VERSION__))
        #Create MdiArea
        self.mdi_area = MdiArea()
        self.horizontalLayout.addWidget(self.mdi_area)
        #Load  pred
        self.configure_btn()
        self.create_stores()
        self.set_movewindow()
        self.subw_a = None
        self.subw_z = None
        self.subw_w = None
        self.subw_abr = None
        self.subw_voice = None
        
    def configure_btn(self):
        #BTNS
        self.btn_salir.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggle_MaxMin)
        self.btn_login.clicked.connect(self.activate_login)

    def create_stores(self):
        #Create Stores and variables
        self.var_list_word = Storage(2)
        self.new_login = False
        self.apps = APPS
        self.boxs = BOXS
        self.sectors_lbl = SECTORS
        self.modules = Storage(len(self.apps))
        self.prev_patient = str()

    def set_movewindow(self):
        #set movement window
        self.showMaximized()
        self.setMouseTracking(True)
        self.barra.mouseMoveEvent = self.move_window

    ## Funciones de la ventana
    def move_window(self, e):
        move = False
        if self.isMaximized(): #Not maximized
            self.toggle_MaxMin()
            move=True
        if not self.isMaximized(): #Not maximized
            move = True
        if move and e.buttons() == Qt.MouseButton.LeftButton:
            #Move window
            g_xy = e.globalPosition().toPoint()
            self.move(g_xy)
            e.accept()

    def toggle_MaxMin(self):
        if self.isMaximized():
            self.showNormal()
            self.resize(800,600)
        else:
            self.showMaximized()

    ## Funciones para el toolbar
    def btns_seccion(self):
        active = str()
        for iter_btn, i in enumerate(self.boxs):
            if self.boxs[i][0]:
                btn = QPushButton()
                btn.setObjectName(i)
                btn.setText(self.boxs[i][2])
                btn.clicked.connect(self.changeArea)
                btn.setMinimumHeight(30)
                btn.setCheckable(True)
                btn.setAutoExclusive(True)
                self.horizontalLayout_5.addWidget(btn)
                if iter_btn == 1:
                    active = i
        btn_selec = self.frame_sec.findChild(QPushButton,active)
        btn_selec.setChecked(True)
        self.chargeBtnsArea(active)
        self.btns_actions()

    def changeArea(self):
        for i in reversed(range( self.layoutTest.count())):
            self.layoutTest.itemAt(i).widget().deleteLater()
        widget = self.sender()
        obj_name = widget.objectName()
        self.chargeBtnsArea(obj_name)

    def chargeBtnsArea(self, area):
        for i in self.boxs[area][1]:
            btn = QPushButton('{}'.format(i))
            btn.setObjectName(i)
            btn.clicked.connect(self.activate_soft)
            tooltip = self.apps[i][1]
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            self.layoutTest.addWidget(btn)
            btn.setDisabled(True)
            btn.setMaximumHeight(25)
            btn.setMaximumWidth(40)
            #parent = self.frameAction.findChild(QHBoxLayout,area)
            #parent.addWidget(btn)

    def btns_actions(self):
        #command
        self.btn_cmd_voice = QPushButton("comandos de voz")
        self.btn_cmd_voice.clicked.connect(self.activate_Cvoice)
        self.layoutAction.addWidget(self.btn_cmd_voice)

    def activate_soft(self):
        widget = self.sender()
        objName = widget.objectName()
        m = globals()['MainWindow']
        print(m.__dict__.values())
        #print(dir(self.createInsWidegt))

        sub = getattr(m, 'subw_{}'.format(objName.lower()))
        self.activate_subwindow(objName, sub)
        #func(self)

    def changeStateBtnAreas(self, b):
        box = self.boxs[b]
        for area in box[1]:
            for i in self.frameAction.findChildren(QPushButton):
                if i.objectName() == area and self.apps[area][5] != "development":
                    i.setDisabled(False)

    def clearToolbar(self):
        for i in reversed(range( self.layoutTest.count())):
            self.layoutTest.itemAt(i).widget().deleteLater()
        for i in reversed(range( self.horizontalLayout_5.count())):
            self.horizontalLayout_5.itemAt(i).widget().deleteLater()
        for i in reversed(range( self.layoutAction.count())):
            self.layoutAction.itemAt(i).widget().deleteLater()

    ##Funciones para las SubWindows
    def flags(self, var):
        var.setWindowFlags(Qt.WindowType.Window |
                            Qt.WindowType.CustomizeWindowHint |
                            Qt.WindowType.WindowTitleHint |
                            Qt.WindowType.FramelessWindowHint|
                            Qt.WindowType.WindowCloseButtonHint |
                            Qt.WindowType.WindowStaysOnTopHint)


    def showHide(self, pos):
        if self.modules.get(pos).isHidden():
            self.modules.get(pos).show()
        else:
            self.modules.get(pos).hide()

    def createInsWidegt(self, data):
        self.data = data
        self.subw_a = FrameSubMdi(Audiometer.Audiometer(self.data))
        self.subw_a.ui_ui.signal_speech.connect(self.speechlist_mode)
        self.subw_z = FrameSubMdi(Z.ZControl())
        self.subw_w = FrameSubMdi(ListWords.ListWords(self.data))
        self.subw_abr = FrameSubMdi(ABR.MainWindow())
        self.subw_voice = FrameSubMdi(ComandVoiceA())
        self.subw_voice.ui_ui.btn_checked.connect(self.subw_a.ui_ui.supra)
        self.subw = {"A": self.subw_a, 
                    "Z":self.subw_z, 
                    "W": self.subw_w, 
                    "ABR": self.subw_abr,
                    "cVoice": self.subw_voice}

    def create_sub_window(self, widg, name, pos_z, fix=(True, True),
                        size=(740,560), position=(0,0)):
        if self.modules.isFull(pos_z):
            self.showHide(pos_z)
        else:
            sub = QMdiSubWindow()
            sub.setWidget(widg)
            widg.lbl_title.setText(name)
            self.mdi_area.addSubWindow(sub)
            if position != [0,0]:
                x,y = int(position[0]), int(position[1])
                sub.move(x,y-220)
            self.flags(sub)
            if fix[0]:
                sub.setMaximumSize(size[0], size[1])
            if fix[1]:
                sub.setMinimumSize(size[0], size[1])
                sub.resize(size[0], size[1])
            sub.show()
            list_wi = self.mdi_area.subWindowList()
            self.modules.set(pos_z, list_wi[-1])

    ##Conexión al Servidor
    def thread_data_clicked(self):
        self.thread_data = ReadThread()
        self.thread_data.name = self.subw_login.ui_ui.Le_name.text()
        self.thread_data.passw = self.subw_login.ui_ui.Le_passw.text()
        self.thread_data.start()
        self.thread_data.data_signal.connect(self.refresh_data)

    def refresh_data(self, data):
        self.data = data
        if self.new_login:
            self.createInsWidegt(self.data)
            print("creados")
            self.btns_seccion()
            self.new_login = False
        self.changeStateBtnAreas(self.data["box"])
        if self.data['result'] == 0:
            text = "conexión exitosa"
        else:
            text = self.sectors_lbl[data['sector']]
            if self.prev_patient != self.data['sector']:
                self.subw_a.ui_ui.la_super(self.data)
                self.subw_w.ui_ui.la_super(self.data)
                self.subw_z.ui_ui.laSuper(self.data)
                self.prev_patient = self.data['sector']
            self.subw_abr.ui_ui.laSuper(self.data)
        self.statusbar.showMessage(text)
        # log off external
        if self.data['state_login'] == "0":
            self.logout()
            QMessageBox.critical(self, "sesión", "Sesión terminada")

    def login(self):
        button_login = self.subw_login.ui_ui.btn_login.text()
        name = self.subw_login.ui_ui.Le_name.text()
        passw = self.subw_login.ui_ui.Le_passw.text()
        #print("{} : {} -- {}".format(name,passw, button_login))
        if button_login == "Salir":
            self.logout()
        else:
            data = {'user': name, 'password': passw, 'request': 'login'}
            result = request_API(data)
            if result == "ok":
                self._extracted_from_login_12(name)
            else:
                QMessageBox.critical(self, "Ingreso", "Error de credenciales")

    # TODO Rename this here and in `login`
    def _extracted_from_login_12(self, name):
        self.subw_login.ui_ui.Le_name.setDisabled(True)
        self.subw_login.ui_ui.Le_passw.setDisabled(True)
        self.thread_data_clicked()
        self.subw_login.ui_ui.btn_login.setText("Salir")
        self.btn_login.setText("Salir")
        self.showHide(0)
        text = "{}".format(name)
        self.lbl_name.setText(text)
        self.statusbar.showMessage(text)
        self.new_login = True

    def logout(self):
        name = self.subw_login.ui_ui.Le_name.text()
        passw = self.subw_login.ui_ui.Le_passw.text()
        self.thread_data.terminate()
        data = {'user': name, 'password': passw, 'request': 'logout'}
        request_API(data)
        self.subw_login.ui_ui.Le_name.setDisabled(False)
        self.subw_login.ui_ui.Le_passw.setDisabled(False)
        self.subw_login.ui_ui.Le_name.setText("")
        self.subw_login.ui_ui.Le_passw.setText("")
        self.subw_login.ui_ui.btn_login.setText("Ingresar")
        self.btn_login.setText("Ingresar")
        self.lbl_name.setText("Desconectado")
        self.mdi_area.closeAll()
        self.clearToolbar()
        #self.close()

###Activate subwindows
    def activate_login(self):
        name = self.apps["Login"][1]
        pos_z = self.apps["Login"][2]
        size = self.apps["Login"][4]
        self.subw_login = FrameSubMdi(Ui_login.MainLogin())
        #self.subw_login = Ui_login.MainLogin()
        self.subw_login.ui_ui.btn_login.clicked.connect(self.login)
        width = (self.size().width())/2
        height = (self.size().height())/2
        width_div2=size[0]/2
        height_div2=size[1]/2
        #print("width:{} , height:{} , w:{} , h:{} ".format(width, height, w, h))
        pos = [width-width_div2, height-height_div2]
        self.create_sub_window(self.subw_login, name, pos_z, size=size, position=pos)

    def activate_subwindow(self, app: str, submdi: FrameSubMdi) -> None:
        name = self.apps[app][1]
        pos_z = self.apps[app][2]
        fix = self.apps[app][3]
        size = self.apps[app][4]
        width = (self.size().width())/2
        height = (self.size().height())/2
        w_submdi=size[0]/2
        h_submdi=size[1]/2
        pos = [width-w_submdi, height-h_submdi]
        self.create_sub_window(submdi, name, pos_z=pos_z, fix=fix, size=size,position=pos)

    def activate_a(self):
        name = self.apps["A"][1]
        pos_z = self.apps["A"][2]
        size = self.apps["A"][4]
        width = (self.size().width())/2
        height = (self.size().height())/2
        w=size[0]/2
        h=size[1]/2
        pos = [width-w, height-h]
        self.create_sub_window(self.subw_a, name, pos_z, size= size, position=pos)

    def activate_z(self):
        name = self.apps["Z"][1]
        pos_z = self.apps["Z"][2]
        size = self.apps["Z"][4]
        width = (self.size().width())/2
        height = (self.size().height())/2
        w=size[0]/2
        h=size[1]/2
        pos = [width-w, height-h]
        self.create_sub_window(self.subw_z, name, pos_z, size= size, position=pos)

    def activate_abr(self):
        name = self.apps["ABR"][1]
        pos_z = self.apps["ABR"][2]
        fix = self.apps["ABR"][3]
        size = self.apps["ABR"][4]
        width = (self.size().width())/2
        height = (self.size().height())/2
        w=size[0]/2
        h=size[1]/2
        pos = [width-w, height-h]
        self.create_sub_window(self.subw_abr, name, pos_z, fix=fix, size=size,position=pos)

    def activate_Cvoice(self):
        name = self.apps["cVoice"][1]
        pos_z = self.apps["cVoice"][2]
        size = self.apps["cVoice"][4]
        self.create_sub_window(self.subw_voice, name, pos_z, size=size)

    def activate_listWords(self):
        name = self.apps["W"][1]
        pos_z = self.apps["W"][2]
        size = self.apps["W"][4]
        if self.var_list_word.get(0):
            if self.modules.isFull(pos_z):
                self.modules.get(pos_z).show()
            else:
                self.create_sub_window(self.subw_w, name, pos_z, size=size)
        else:
            self.modules.get(pos_z).hide()

    def speechlist_mode(self, state):
        self.var_list_word.getAll(True)
        self.var_list_word.listSet(state, False)
        self.var_list_word.getAll(True)
        self.activate_listWords()
        self.subw_w.ui_ui.playable[1] = state[2]
        self.subw_w.ui_ui.playable[2] = state[3]
        self.subw_w.ui_ui.playable[3] = state[4]
        self.subw_w.ui_ui.playable[0] = bool(state[1])

def request_API(data):
    URL = "https://tmeduca.cl/LabSim/module/API_v2.php"
    response = requests.post(URL, data=data)
    return response.text

class ReadThread(QThread):
    name = ""
    passw = ""
    data_signal = pyqtSignal(dict)

    def run(self):
        while True:
            time.sleep(1)
            name = self.name
            passw = self.passw
            data = {'user': name, passw: passw, 'request': 'state'}
            request_data = json.loads(request_API(data))
            if isinstance(request_data, int):
                response = {"result": request_data}
            else:
                response = request_data
                response['result'] = 1
            self.data_signal.emit(response)


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = MainWindow()
    Preferences.getStyle(window)
    window.show()
    exit_code = appctxt.app.exec()
    sys.exit(exit_code)
