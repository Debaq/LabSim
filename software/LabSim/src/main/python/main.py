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
                             QMessageBox, QPushButton, QWidget, QGroupBox)

import ABR
import Z
from Audiometer import Audiometer
from UI.Ui_Main_new import Ui_MainWindow

app_active = {
    'A':True, 'Z':True, 'ABR':True,
    'EOAs':False, 'EOAc':False, 'VNG':False, 
    'Vhit':False, 'POS':False}

threshold =  [[[130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130]],
                [[130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130]],
                [[130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130],[130,130],
                [130,130],[130,130],[130,130]]
                ]

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self)
        self.setupUi(self)
       # QFontDatabase.addApplicationFont(
            #appctxt.get_resource('font/OpenSans-Regular.ttf'))
        #self.font = QFont.setFamily('OpenSans-Bold')
        #font = QFont("OpenSans")
        #QGuiApplication.setFont(font)
        self.showMaximized()
        #self.actionAudiometro.triggered.connect(self.activate_a)
        #self.actionImpedanciometro.triggered.connect(self.activate_z)
        #self.actionCascada.triggered.connect(self.cascade)
        #self.actionTiles.triggered.connect(self.tile)
        #self.actionCerrar_todas.triggered.connect(self.closeAll)
        #self.actionABR.triggered.connect(self.activate_abr)
        #self.setWindowTitle("LabSim")
        self.mdiArea.documentMode = True
        #self.Z_O = 3
        #self.Z = Z.ZControl('C', 'C', self.Z_O)
        #self.A = Audiometer(threshold)
        self.lisModuleActive = [None,None,None]
        self.lateral_btn()


    def lateral_btn(self):
        #self.groupBox = QGroupBox(self.layout_test)
        for i in app_active:
            if app_active[i]:
                self.btn = QPushButton('{}'.format(i))
                text = self.btn.text()
                self.btn.clicked.connect(lambda ch, text=text: self.printer(text))
                #self.layout_test.addWidget(self.btn)

    def printer(self, n):
        print(n)

    def closeAll(self):
        #self.mdiArea.closeAllSubWindows()
        for i in range(len(self.lisModuleActive)):
            self.lisModuleActive[i].hide()


    def cascade(self):
        self.mdiArea.cascadeSubWindows()

    def tile(self):
        self.mdiArea.tileSubWindows()

    def activate_z(self):
        if self.lisModuleActive[1] != None:
            if self.lisModuleActive[1].isHidden():
                self.lisModuleActive[1].show()
            else:
                self.lisModuleActive[1].hide()
        else:
            sub_Z = QMdiSubWindow()
            sub_Z.setWidget(Z.ZControl('C', 'C', self.Z_O))
            self.mdiArea.addSubWindow(sub_Z)
            sub_Z.setWindowTitle("Impedanciómetro")
            sub_Z.setWindowFlags(
                Qt.Window |
                Qt.CustomizeWindowHint |
                Qt.WindowTitleHint |
                Qt.WindowMaximizeButtonHint |
                Qt.WindowCloseButtonHint |
                Qt.WindowStaysOnTopHint
                )
            sub_Z.show()
            list_wi = self.mdiArea.subWindowList()
            self.lisModuleActive[1] = list_wi[-1]

    def activate_abr(self):
        if self.lisModuleActive[2] != None:
            if self.lisModuleActive[2].isHidden():
                self.lisModuleActive[2].show()
            else:
                self.lisModuleActive[2].hide()
        else:
            sub_ABR = QMdiSubWindow()
            sub_ABR.setWidget(ABR.MainWindow())
            self.mdiArea.addSubWindow(sub_ABR)
            sub_ABR.setWindowTitle("Potenciales Evocados")
            sub_ABR.setWindowFlags(
                Qt.Window |
                Qt.CustomizeWindowHint |
                Qt.WindowTitleHint |
                Qt.WindowMaximizeButtonHint |
                Qt.WindowCloseButtonHint |
                Qt.WindowStaysOnTopHint
                )
            sub_ABR.show()
            list_wi = self.mdiArea.subWindowList()
            self.lisModuleActive[2] = list_wi[-1]


    def activate_a(self):
        if self.lisModuleActive[0] != None:
            if self.lisModuleActive[0].isHidden():
                self.lisModuleActive[0].show()
            else:
                self.lisModuleActive[0].hide()
        else:
            sub_A = QMdiSubWindow()
            sub_A.setWidget(Audiometer(threshold))
            self.mdiArea.addSubWindow(sub_A)
            sub_A.setWindowTitle("Audiometro")
            sub_A.setWindowFlags(
                Qt.Window |
                Qt.CustomizeWindowHint |
                Qt.WindowTitleHint |
                Qt.WindowMaximizeButtonHint |
                Qt.WindowCloseButtonHint |
                Qt.WindowStaysOnTopHint
                )
            sub_A.show()
            list_wi = self.mdiArea.subWindowList()
            self.lisModuleActive[0] = list_wi[-1]

    def thread_data_clicked(self):
        self.thread_data = ReadThread()
        self.thread_data.name = self.name.text()
        self.thread_data.passw = self.passw.text()
        self.thread_data.start()
        self.thread_data.data_signal.connect(self.refresh_data)

    def refresh_data(self, data):
        print(data)

        if data['result'] == 0:
            text = "conexión exitosa"
        else:
            if data['sector'] == 'Camara_sono':
                text = 'usuario en cámara sonoamortiguada'
            if data['sector'] == 'Z_OD':
                text = 'usuario con oliva en OD'
                self.Z.side_sonda = 0
                self.Z.data_OD.create_auto(data['Z_OD'])

            if data['sector'] == 'Z_OI':
                text = 'usuario con oliva en OI'
                self.Z.side_sonda = 1
                self.Z.data_OI.create_auto(data['Z_OI'])


        name = self.name.text()
        passw = self.passw.text()
        self.lbl_status.setText(text)

        data_2 = {'user': name, 'password': passw, 'request': 'state_login'}
        result = request_API(data_2)
        if result == "0":
            QMessageBox.critical(self, "sesión", "Sesión terminada")
            self.logout()

    def login(self):
        button_login = self.btn_login.text()
        name = self.name.text()
        passw = self.passw.text()
        if button_login == "Salir":
            data = {'user': name, 'password': passw, 'request': 'logout'}
            result = request_API(data)
            self.logout()

        else:
            data = {'user': name, 'password': passw, 'request': 'login'}
            result = request_API(data)
            if result == "ok":
                self.name.setDisabled(True)
                self.passw.setDisabled(True)
                self.btn_a.setDisabled(False)
                self.btn_z.setDisabled(False)
                self.thread_data_clicked()
                self.btn_login.setText("Salir")
            else:
                QMessageBox.critical(self, "Ingreso", "Error de credenciales")

    def logout(self):
        self.name.setDisabled(False)
        self.passw.setDisabled(False)
        self.btn_a.setDisabled(True)
        self.btn_z.setDisabled(True)
        self.lbl_status.setText("")
        self.name.setText("")
        self.passw.setText("")
        self.btn_login.setText("Ingresar")
        #self.read_data.terminate()


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
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = MainWindow()
    window.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
