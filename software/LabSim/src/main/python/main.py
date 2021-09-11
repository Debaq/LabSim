# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                          VER. 0.7.5                           #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFontDatabase, QFont,QGuiApplication
import requests
import sys
from UI.Ui_main_login import Ui_MainLogin
import Z
import json
import time
from Audiometer import *
from Audiometer import Audiometer
from UI.Ui_main_login import Ui_MainLogin

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

class MainWindow(QMainWindow, Ui_MainLogin):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self)
        QFontDatabase.addApplicationFont(
            appctxt.get_resource('font/OpenSans-Regular.ttf'))
        #self.font = QFont.setFamily('OpenSans-Bold')
        font = QFont("OpenSans")
        QGuiApplication.setFont(font)
        self.setupUi(self)
        self.btn_login.clicked.connect(self.login)
        # self.btn_login.clicked.connect(self.evt_btnStart_click)
        self.btn_z.clicked.connect(self.activate_z)
        self.btn_a.clicked.connect(self.activate_a)
        self.btn_z.setDisabled(True)
        self.btn_a.setDisabled(True)
        self.Z_O = 3
        self.Z = Z.ZControl('C', 'C', self.Z_O)
        self.A = Audiometer(threshold)


    def activate_z(self):
        self.Z.show()

    def activate_a(self):
        self.A.show()

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
