# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                          VER. 0.7.5                           #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
# pip install https://build-system.fman.io/pro/12a9a98c-755b-4d95-9c60-a17ae1a74d6c/1.0.7#egg=fbs
__VERSION__ = 'v0.8.4'

import json
import sys
import time

import requests
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase, QGuiApplication
from PyQt5.QtWidgets import (QMainWindow, QMdiSubWindow, QMessageBox,
                             QPushButton, QGroupBox, QHBoxLayout)

import ABR
import Audiometer
import ListWords
import login as Ui_login
import Z
from lib.helpers import Preferences, Storage
from UI.Ui_Main import Ui_MainWindow

Preferences = Preferences()
APPS = Preferences.get("APP")
SECTORS = Preferences.get("SECTORS")
BOXS = Preferences.get("BOXS")
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        QFontDatabase.addApplicationFont(appctxt.get_resource('font/OpenSans-Regular.ttf'))
        font = QFont("OpenSans")
        font.setPointSize(8)
        QGuiApplication.setFont(font)
        self.setWindowTitle("LabSim {}".format(__VERSION__))
        self.setMinimumSize(1200, 768)
        #self.actionLogin.triggered.connect(self.activate_login)
        self.btn_salir.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.showNormal)
        self.actionCascada.triggered.connect(self.cascade)
        self.actionTiles.triggered.connect(self.tile)
        self.actionCerrar_todas.triggered.connect(self.closeAll)
        self.mdiArea.documentMode = True
        
        self.var_listWord = Storage(2)
        self.newLogin = False
        self.apps = APPS
        self.Boxs = BOXS
        self.sectors_lbl = SECTORS
        self.Modules = Storage(len(self.apps))
        self.prevPatient = str()

        self.areas()
        self.activate_login()
        self.showMaximized()

    def areas(self):
        for i in self.Boxs:
            if self.Boxs[i][0]:
                gbtns = QGroupBox()
                name = "frame_{}".format(i)
                gbtns.setObjectName(name)
                gbtns.setTitle(self.Boxs[i][2])
                gbtns.setFlat(False)
                layout = QHBoxLayout(gbtns)
                layout.setObjectName(i)

                self.layoutTest.addWidget(gbtns)
                self.btns_areas(i, self.Boxs[i][1])


    def btns_areas(self, area, setBtns):
        for i in setBtns:
            btn = QPushButton('{}'.format(i))
            btn.setObjectName(i)
            btn.clicked.connect(self.activate_soft)
            tooltip = self.apps[i][1]
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            #self.layoutTest.addWidget(btn)
            btn.setDisabled(True)
            btn.setMaximumHeight(25)
            btn.setMaximumWidth(35)
            font = QFont()
            font.setPointSize(8)
            btn.setFont(font)
            parent = self.frameAction.findChild(QHBoxLayout,area)
            parent.addWidget(btn)
        rec = self.widget_Mdi.frameSize()
        print(rec)


        """
        for i in self.apps:
            btn = QPushButton('{}'.format(i))
            btn.setObjectName(i)
            btn.clicked.connect(self.activate_soft)
            tooltip = self.apps[i][1]
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            self.layoutTest.addWidget(btn)
            btn.setDisabled(True)
            btn.setMaximumHeight(25)
            btn.setMaximumWidth(35)
            font = QFont()
            font.setPointSize(8)
            btn.setFont(font)
        """
    def activate_soft(self):
        widget = self.sender()
        objName = widget.objectName()
        m = globals()['MainWindow']
        func = getattr(m, 'activate_{}'.format(objName.lower()))
        func(self)

    def changeStateBtnAreas(self, b):
        box = self.Boxs[b]
        for area in box[1]:
            for i in self.frameAction.findChildren(QPushButton):
                if i.objectName() == area:
                    if self.apps[area][5] != "development":
                        i.setDisabled(False)

    def flags(self, var, t=True):
        if t == True:
            var.setWindowFlags(Qt.Window |
                               Qt.CustomizeWindowHint |
                               Qt.WindowTitleHint |
                               Qt.WindowCloseButtonHint |
                               Qt.WindowStaysOnTopHint)
        else:
            var.setWindowFlags(Qt.Window |
                               Qt.CustomizeWindowHint |
                               Qt.WindowTitleHint |
                               Qt.WindowMaximizeButtonHint |
                               Qt.WindowCloseButtonHint |
                               Qt.WindowStaysOnTopHint)

    def closeAll(self):
        for i in self.Modules.length(True):
            if self.Modules.get(i) != None:
                self.Modules.get(i).hide()

    def cascade(self):
        self.mdiArea.cascadeSubWindows()

    def tile(self):
        self.mdiArea.tileSubWindows()

    def showHide(self, pos):
        if self.Modules.get(pos).isHidden():
            self.Modules.get(pos).show()
        else:
            self.Modules.get(pos).hide()

    def createInsWidegt(self, data):
        self.data = data
        self.A = Audiometer.Audiometer(self.data)
        self.A.signal_speech.connect(self.speechlist_mode)
        self.Z = Z.ZControl()
        self.W = ListWords.ListWords(self.data)
        self.ABR = ABR.MainWindow()

    def createSubWindow(self, widg, name, pos, fix=[True, True], size=[740,560], flags=True):
        if self.Modules.isFull(pos):
            self.showHide(pos)
        else:   
            sub = QMdiSubWindow()
            sub.setWidget(widg)
            self.mdiArea.addSubWindow(sub)
            sub.setWindowTitle(name)
            self.flags(sub, flags)
            if fix[0] == True or fix[1] == True:
                if fix[0] == True:
                    sub.setMaximumSize(size[0], size[1])
                if fix[1] == True:
                    sub.setMinimumSize(size[0], size[1])
                    sub.resize(size[0], size[1])
            sub.show()
            list_wi = self.mdiArea.subWindowList()
            self.Modules.set(pos, list_wi[-1])

    
    def thread_data_clicked(self):
        self.thread_data = ReadThread()
        self.thread_data.name = self.loginWin.Le_name.text()
        self.thread_data.passw = self.loginWin.Le_passw.text()
        self.thread_data.start()
        self.thread_data.data_signal.connect(self.refresh_data)

    def refresh_data(self, data):
        self.data = data
        if self.newLogin:
            self.createInsWidegt(self.data)
            self.newLogin = False
        self.changeStateBtnAreas(self.data["box"])
        if self.data['result'] == 0:
            text = "conexión exitosa"
        else:
            text = self.sectors_lbl[data['sector']]
            if self.prevPatient != self.data['sector']:
                self.A.laSuper(self.data)
                self.W.laSuper(self.data)
                self.Z.laSuper(self.data)
                self.prevPatient = self.data['sector']
            self.ABR.laSuper(self.data)

        self.statusbar.showMessage(text)
        # log off external
        if self.data['state_login'] == "0":
            self.logout()
            QMessageBox.critical(self, "sesión", "Sesión terminada")

    def login(self):
        button_login = self.loginWin.btn_login.text()
        name = self.loginWin.Le_name.text()
        passw = self.loginWin.Le_passw.text()
        if button_login == "Salir":
            self.logout()
        else:
            data = {'user': name, 'password': passw, 'request': 'login'}
            result = request_API(data)
            if result == "ok":
                self.loginWin.Le_name.setDisabled(True)
                self.loginWin.Le_passw.setDisabled(True)
                self.thread_data_clicked()
                self.loginWin.btn_login.setText("Salir")
                self.showHide(0)
                text = "Conectado : {}".format(name)
                self.lbl_name.setText(text)
                self.statusbar.showMessage(text)
                self.newLogin = True
            else:
                QMessageBox.critical(self, "Ingreso", "Error de credenciales")

    def logout(self):
        name = self.loginWin.Le_name.text()
        passw = self.loginWin.Le_passw.text()
        self.thread_data.terminate()
        data = {'user': name, 'password': passw, 'request': 'logout'}
        request_API(data)
        self.loginWin.Le_name.setDisabled(False)
        self.loginWin.Le_passw.setDisabled(False)
        self.loginWin.Le_name.setText("")
        self.loginWin.Le_passw.setText("")
        self.loginWin.btn_login.setText("Ingresar")
        self.lbl_name.setText("Desconectado")


    def activate_login(self):
        name = self.apps["Login"][1]
        pos = self.apps["Login"][2]
        size = self.apps["Login"][4]
        self.loginWin = Ui_login.MainLogin()
        self.loginWin.btn_login.clicked.connect(self.login)
        self.createSubWindow(self.loginWin, name, pos, size=size)

    def activate_a(self):
        name = self.apps["A"][1]
        pos = self.apps["A"][2]

        self.createSubWindow(self.A, name, pos)

    def activate_z(self):
        name = self.apps["Z"][1]
        pos = self.apps["Z"][2]
        self.createSubWindow(self.Z, name, pos)

    def activate_abr(self):
        name = self.apps["ABR"][1]
        pos = self.apps["ABR"][2]
        fix = self.apps["ABR"][3]
        size = self.apps["ABR"][4]
        self.createSubWindow(self.ABR, name, pos, fix=fix, size=size, flags=False)

    def activate_listWords(self):
        name = self.apps["W"][1]
        pos = self.apps["W"][2]
        size = self.apps["W"][4]
        if self.var_listWord.get(0):
            if self.Modules.isFull(pos):
                self.Modules.get(pos).show()
            else:
                self.createSubWindow(self.W, name, pos, size=size)
        else:
            self.Modules.get(pos).hide()

    def speechlist_mode(self, state):
        print(state)
        self.var_listWord.getAll(True)
        self.var_listWord.listSet(state, False)
        self.var_listWord.getAll(True)
        self.activate_listWords()
        self.W.playable[1] = state[2]
        self.W.playable[2] = state[3]
        if state[1]:
            self.W.playable[0] = True
        else:
            self.W.playable[0] = False

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
            if type(request_data) == type(1):
                response = {"result": request_data}
            else:
                response = request_data
                response['result'] = 1
            self.data_signal.emit(response)


if __name__ == '__main__':
    # app = QApplication(sys.argv)
    appctxt = ApplicationContext()
    window = MainWindow()
    Preferences.getStyle(window)
    # window.show()
    exit_code = appctxt.app.exec_()
    button_login = window.loginWin.btn_login.text()
    if button_login == "Salir":
        window.logout()
    sys.exit(exit_code)
    # sys.exit(app.exec_())
