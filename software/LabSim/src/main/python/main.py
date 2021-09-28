# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                          VER. 0.7.5                           #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################

import json
import sys
import time

import requests
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase, QGuiApplication
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMdiSubWindow,
                             QMessageBox, QPushButton, QWidget, QGroupBox, QFrame)

import ABR
import Z
import login as Ui_login
import Audiometer
import ListWords

from lib.h_audio import CalculateLogo
from UI.Ui_Main import Ui_MainWindow

app_active = {
    'A':[True, "Audiómetro",1], 'Z':[True, "Impedanciómetro",2], 
    'ABR':[True, "Potencial evocado auditivo de tronco cerebral",3],
    'VEMP':[False, "Potenciales evocados vestibulares miogénicos",4],
    'EOAs':[False, "Emisor Otoacústico de Screening",5], 
    'EOAc':[False, "Emisor Otoacústico Clínico",6], 'VNG':[False, "Videonistagmografía",7], 
    'vHit':[False, "Video Head Impulse Test",8], 'POS':[False, "Posturografía",9]}

sectors_lbl = {'Camara_sono' : 'Usuario en cámara sonoamortiguada',
                'Z_OD' : 'Usuario con oliva en OD',
                'Z_OI': 'Usuario con oliva en OI'}


threshold_basic =  [[130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130]]

data_basic = {
    'gender' : 0,
    'id'    :   1,
    'Aérea' : threshold_basic,
    'Ósea' : threshold_basic,
    'LDL' : threshold_basic,
    'Aérea_mkg' :threshold_basic,
    'Ósea_mkg' : threshold_basic,
    "Z_OD": "A",
    "Z_OI": "A",
    "sector": "Camara_sono",
    "volume" : [0,0,"N/D"]
}


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        #QMainWindow.__init__(self)
        super(MainWindow, self).__init__()
        self.setupUi(self)
        QFontDatabase.addApplicationFont(appctxt.get_resource('font/OpenSans-Regular.ttf'))
        font = QFont("OpenSans")
        font.setPointSize(5)
        QGuiApplication.setFont(font)
        self.showMaximized()
        self.setWindowTitle("LabSim")
        self.actionLogin.triggered.connect(self.login_win)
  
        self.actionCascada.triggered.connect(self.cascade)
        self.actionTiles.triggered.connect(self.tile)
        self.actionCerrar_todas.triggered.connect(self.closeAll)
        self.mdiArea.documentMode = False
        self.Z_O = 3
        self.lisModuleActive = [None,None,None,None,None]
        self.var_listWord = [None, None]
        self.lateral_btn()
        logo = CalculateLogo(data_basic) 
        self.logo_data = logo.get()
        self.data = data_basic
        self.login_win()

    def lateral_btn(self):
        for i in app_active:
            btn = QPushButton('{}'.format(i))
            text = btn.text()
            btn.setObjectName(i)
            btn.clicked.connect(lambda ch, text=text: self.activate_soft(text))
            tooltip= app_active[i][1]
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            self.layoutTest.addWidget(btn)
            if app_active[i][0] == False:
                btn.setDisabled(True)

    def speechlist_mode(self, state):
        self.var_listWord = state
        self.activate_listWords()
        self.W.playable[1] = state[2]
        self.W.playable[2] = state[3]
        if state[1]:
            self.W.playable[0] = True
        else:
            self.W.playable[0] = False


    def activate_soft(self, n):
        widget = self.sender()
        objName = widget.objectName()
        if objName == 'A':
            self.activate_a()
        if objName == 'Z':
            self.activate_z()
        if objName == 'ABR':
            self.activate_abr()
        if objName == 'Lista':
            self.activate_listWords()
        #for i in self.verticalFrame.findChildren(QPushButton):
        #    if i.objectName() == "Z":
        #        i.setDisabled(True)
        #print(widget.objectName())

    def flags(self,var):
         var.setWindowFlags(Qt.Window |
                Qt.CustomizeWindowHint |
                Qt.WindowTitleHint |
                Qt.WindowCloseButtonHint |
                Qt.WindowStaysOnTopHint)

    def closeAll(self):
        for i in range(len(self.lisModuleActive)):
            self.lisModuleActive[i].hide()

    def cascade(self):
        self.mdiArea.cascadeSubWindows()

    def tile(self):
        self.mdiArea.tileSubWindows()

    def showHide(self, pos):
        if self.lisModuleActive[pos].isHidden():
            self.lisModuleActive[pos].show()
        else:
            self.lisModuleActive[pos].hide()
    
    def createSubWindow(self, widg, name, pos, size = True, width=740, height=560):
        sub = QMdiSubWindow()
        sub.setWidget(widg)
        self.mdiArea.addSubWindow(sub)
        sub.setWindowTitle(name)
        self.flags(sub)
        if size:
            sub.setMaximumSize(width,height)
            sub.setMinimumSize(width,height)
        sub.show()
        list_wi = self.mdiArea.subWindowList()
        self.lisModuleActive[pos] = list_wi[-1]

    def login_win(self):
        pos = 0
        if self.lisModuleActive[pos] != None:
           self.showHide(pos)
        else:
            self.loginWin = Ui_login.MainLogin()
            self.loginWin.btn_login.clicked.connect(self.login)
            self.createSubWindow(self.loginWin, "Ingresar", pos, height=140, width=420)

    def activate_a(self):
        pos = 1
        if self.lisModuleActive[pos] != None:
            self.showHide(pos)
        else:
            self.A = Audiometer.Audiometer(self.data)
            self.A.signal_speech.connect(self.speechlist_mode)
            self.createSubWindow(self.A, "Audiometro", pos)

    def activate_z(self):
        pos = 2
        if self.lisModuleActive[pos] != None:
           self.showHide(pos)
        else:
            self.Z = Z.ZControl(self.data, self.Z_O)
            self.createSubWindow(self.Z, "Impedanciómetro", pos)

    def activate_abr(self):
        pos = 3
        if self.lisModuleActive[pos] != None:
           self.showHide(pos)
        else:
            self.ABR = ABR.MainWindow()
            self.createSubWindow(self.ABR, "Potenciales Evocados", pos, size=False)
  
    def activate_listWords(self):
        pos = 4        
        if self.var_listWord[0]:
            if self.lisModuleActive[pos] != None:
                self.lisModuleActive[pos].show()
            else:
                self.W = ListWords.ListWords(self.data)
                self.createSubWindow(self.W , "Lista de Palabras", pos,width=270, height=650)
        else:
            self.lisModuleActive[pos].hide()

    def thread_data_clicked(self):
        self.thread_data = ReadThread()
        self.thread_data.name = self.loginWin.Le_name.text()
        self.thread_data.passw = self.loginWin.Le_passw.text()
        self.thread_data.start()
        self.thread_data.data_signal.connect(self.refresh_data)

    def refresh_data(self, data):
        self.data = data
        if self.data['result'] == 0:
            text = "conexión exitosa"
        else:
            text = sectors_lbl[data['sector']]
            try:
                self.A.laSuper(self.data)
                self.W.laSuper(self.data)
                self.Z.laSuper(self.data)
            except:
                pass
        self.statusbar.showMessage(text)
        #log off external
        if data['state_login'] == "0":
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


def Splash(app):
    #app = QApplication(sys.argv)
    pixmap = QPixmap(appctxt.get_resource('img/Logo.png'))
    splash_img = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash_img.setEnabled(False)
    opaqueness = 0.0
    splash_img.setWindowOpacity(opaqueness)
    splash_img.setAttribute(Qt.WA_DeleteOnClose)
    splash_img.setMask(pixmap.mask())
    splash_img.show()
    for i in range(0, 2):
        time.sleep(0.1)
    splash_img.finish(app)


def request_API(data):
    URL = "https://tmeduca.cl/LabSim/module/API_v2.php"
    response = requests.post(URL, data=data)
    return response.text


class ReadThread(QThread):
    name = ""
    passw = ""
    data_signal = pyqtSignal(dict)
    def run(self):
        #i = 0
        while True:
            #i += 1
            time.sleep(1)
            #print("funcionando {}".format(i))
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
    #app = QApplication(sys.argv)
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = MainWindow()
    window.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    button_login = window.loginWin.btn_login.text()
    if button_login == "Salir":
        window.logout()
    sys.exit(exit_code)
    #sys.exit(app.exec_())