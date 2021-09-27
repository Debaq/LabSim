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

from UI.Ui_Main_new import Ui_MainWindow



app_active = {
    'A':[True, "Audiómetro"], 'Z':[True, "Impedanciómetro"], 
    'ABR':[False, "Potencial evocado auditivo de tronco cerebral"],
    'VEMP':[False, "Potenciales evocados vestibulares miogénicos"],
    'EOAs':[False, "Emisor Otoacústico de Screening"], 
    'EOAc':[False, "Emisor Otoacústico Clínico"], 'VNG':[False, "Videonistagmografía"], 
    'vHit':[False, "Video Head Impulse Test"], 'POS':[False, "Posturografía"]}

flags = [Qt.Window, Qt.CustomizeWindowHint, Qt.WindowTitleHint, 
        Qt.WindowMaximizeButtonHint, Qt.WindowCloseButtonHint,
        Qt.WindowStaysOnTopHint]

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


class CalculateLogo():
    def __init__(self, thr = data_basic):
        self.thr = thr
        self.sdt = self.sdt_calcule(self.thr)
        self.srt = [self.thr["Aérea"][4][0],self.thr["Aérea"][4][1]]
        if self.srt[0] == self.sdt[0]:
            self.srt[0] = self.srt[0]+10
        if self.srt[1] == self.sdt[1]:
            self.srt[1]=self.srt[1]+10
        self.umd = [self.srt[0]+25, self.srt[1]+25]
        #self.porcentajes_logo = [[0,0],[5,24],[10,52],[15,64],[20,76],[25,84],[30,96],[35,100]]
        self.porcentajes_logo = [0,24,52,64,76,84,96,100]
        self.curve_normal = [0,5,10,15,20,25,30,35]
        self.data = self.calculate_result()
        


    def sdt_calcule(self, data):
        od = [data["Aérea"][1][0],data["Aérea"][2][0],data["Aérea"][3][0],data["Aérea"][4][0],data["Aérea"][5][0],data["Aérea"][6][0]]
        oi = [data["Aérea"][1][1],data["Aérea"][2][1],data["Aérea"][3][1],data["Aérea"][4][1],data["Aérea"][5][1],data["Aérea"][6][1]]
        od.sort()
        oi.sort()
        def prom(x):
            result = sum(x)/len(x)
            return result

        prom_od = prom([od[0], od[1]])
        prom_oi = prom([oi[0], oi[1]])

        result_prev = [prom_od, prom_oi]
        result = [int(result_prev[0]/5)*5,int(result_prev[1]/5)*5 ]
        return result
    
    def calculate_result(self):
        def generate(sdt , srt, umd, por):
            temp = {}
            idx_sdt = 0
            idx_srt = 2
            idx_umd = 7
            temp[str(sdt)] = int(por[idx_sdt]/4)
            temp[str(sdt+5)] = int(por[1]/4)
            temp[str(srt)] = int(por[idx_srt]/4)
            temp[str(sdt+5)] = int(por[3]/4)
            temp[str(sdt+10)] = int(por[4]/4)
            temp[str(sdt+15)] = int(por[5]/4)
            temp[str(sdt+20)] = int(por[6]/4)
            temp[str(sdt+25)] = int(por[6]/4)

            temp[str(umd)] = int(por[idx_umd]/4)
            return temp
    
        od = generate(self.sdt[0], self.srt[0], self.umd[0], self.porcentajes_logo )
        oi = generate(self.sdt[1], self.srt[1], self.umd[1], self.porcentajes_logo )
        data = [od, oi]
        return data
    
    def get(self):
        return self.data



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        #QMainWindow.__init__(self)
        super(MainWindow, self).__init__()

        self.setupUi(self)
        QFontDatabase.addApplicationFont(appctxt.get_resource('font/OpenSans-Regular.ttf'))
        font = QFont("OpenSans")
        QGuiApplication.setFont(font)
        self.showMaximized()
        self.setWindowTitle("LabSim")
        self.actionLogin.triggered.connect(self.login_win)
  
        self.actionCascada.triggered.connect(self.cascade)
        self.actionTiles.triggered.connect(self.tile)
        self.actionCerrar_todas.triggered.connect(self.closeAll)
        self.mdiArea.documentMode = False
        self.Z_O = 3
        self.lisModuleActive = [None, None,None,None]
        self.var_listWord = [None, None]
        self.lateral_btn()

        logo = CalculateLogo() 
        self.logo_data = logo.get()
        self.data = data_basic


    def lateral_btn(self):
        #self.groupBox = QGroupBox(self.layout_test)
        for i in app_active:
            btn = QPushButton('{}'.format(i))
            text = btn.text()
            btn.setObjectName(i)
            btn.clicked.connect(lambda ch, text=text: self.activate_soft(text))
            tooltip= app_active[i][1]
            btn.setToolTip(tooltip)
            self.layout_test.addWidget(btn)
            if app_active[i][0] == False:
                btn.setDisabled(True)
            
    def speechlist_mode(self, state):
        print(state)
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

    def login_win(self):
        sub_Login = QMdiSubWindow()
        self.loginWin = Ui_login.MainLogin()
        sub_Login.setWidget(self.loginWin)
        self.loginWin.btn_login.clicked.connect(self.login)
        self.mdiArea.addSubWindow(sub_Login)
        self.flags(sub_Login)
        sub_Login.show()

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

    def activate_a(self):
        pos = 0
        if self.lisModuleActive[pos] != None:
            if self.lisModuleActive[pos].isHidden():
                self.lisModuleActive[pos].show()
            else:
                self.lisModuleActive[pos].hide()
        else:
            sub_A = QMdiSubWindow()
            self.A = Audiometer.Audiometer(self.data)
            self.A.signal_speech.connect(self.speechlist_mode)

            sub_A.setWidget(self.A)
            self.mdiArea.addSubWindow(sub_A)
            sub_A.setWindowTitle("Audiometro")
            self.flags(sub_A)
            sub_A.setMaximumSize(740,560)
            sub_A.setMinimumSize(740,560)
            sub_A.show()
            list_wi = self.mdiArea.subWindowList()
            self.lisModuleActive[pos] = list_wi[-1]

    def activate_z(self):
        pos = 1
        if self.lisModuleActive[pos] != None:
            if self.lisModuleActive[pos].isHidden():
                self.lisModuleActive[pos].show()
            else:
                self.lisModuleActive[pos].hide()
        else:
            sub_Z = QMdiSubWindow()
            self.Z = Z.ZControl(self.data, self.Z_O)
            sub_Z.setWidget(self.Z)
            self.mdiArea.addSubWindow(sub_Z)
            sub_Z.setWindowTitle("Impedanciómetro")
            self.flags(sub_Z)
            sub_Z.setMaximumSize(740,560)
            sub_Z.setMinimumSize(740,560)
            sub_Z.show()
            list_wi = self.mdiArea.subWindowList()
            self.lisModuleActive[pos] = list_wi[-1]

    def activate_abr(self):
        pos = [2]
        if self.lisModuleActive[pos] != None:
            if self.lisModuleActive[pos].isHidden():
                self.lisModuleActive[pos].show()
            else:
                self.lisModuleActive[pos].hide()
        else:
            sub_ABR = QMdiSubWindow()
            sub_ABR.setWidget(ABR.MainWindow())
            self.mdiArea.addSubWindow(sub_ABR)
            sub_ABR.setWindowTitle("Potenciales Evocados")
            self.flags(sub_ABR)
            sub_ABR.show()
            list_wi = self.mdiArea.subWindowList()
            self.lisModuleActive[pos] = list_wi[-1]

  
    def activate_listWords(self):
        pos = 3        
        if self.var_listWord[0]:
            if self.lisModuleActive[pos] != None:
                self.lisModuleActive[pos].show()
            else:
                sub_W = QMdiSubWindow()
                
                self.W = ListWords.ListWords(self.data)
                sub_W.setWidget(self.W)
                self.mdiArea.addSubWindow(sub_W)
                sub_W.setWindowTitle("Lista de Palabras")
                self.flags(sub_W)
                sub_W.setMaximumSize(270,650)
                sub_W.setMinimumSize(270,650)

                sub_W.show()
                list_wi = self.mdiArea.subWindowList()
                self.lisModuleActive[pos] = list_wi[-1]
        else:
            self.lisModuleActive[pos].hide()



    def thread_data_clicked(self):
        self.thread_data = ReadThread()
        self.thread_data.name = self.loginWin.Le_name.text()
        self.thread_data.passw = self.loginWin.Le_passw.text()
        self.thread_data.start()
        self.thread_data.data_signal.connect(self.refresh_data)

    def refresh_data(self, data):
        #print(data)
        text= ''
        if data['result'] == 0:
            text = "conexión exitosa"
        else:
            try:
                if data['sector'] == 'Camara_sono':
                    text = 'usuario en cámara sonoamortiguada'
                    self.A.laSuper(data)
                    self.W.laSuper(data)
           
                self.Z.laSuper(data)
                
            except:
                pass

        name = self.loginWin.Le_name.text()
        passw = self.loginWin.Le_passw.text()
        self.loginWin.lbl_infoLogin.setText(text)

        data_2 = {'user': name, 'password': passw, 'request': 'state_login'}
        result = request_API(data_2)
        if result == "0":
            QMessageBox.critical(self, "sesión", "Sesión terminada")
            self.logout()

    def login(self):
        button_login = self.loginWin.btn_login.text()
        name = self.loginWin.Le_name.text()
        passw = self.loginWin.Le_passw.text()
        if button_login == "Salir":
            data = {'user': name, 'password': passw, 'request': 'logout'}
            result = request_API(data)
            self.logout()

        else:
            data = {'user': name, 'password': passw, 'request': 'login'}
            result = request_API(data)
            if result == "ok":
                self.loginWin.Le_name.setDisabled(True)
                self.loginWin.Le_passw.setDisabled(True)
                #self.btn_a.setDisabled(False)
                #self.btn_z.setDisabled(False)
                self.thread_data_clicked()
                self.loginWin.btn_login.setText("Salir")
            else:
                QMessageBox.critical(self, "Ingreso", "Error de credenciales")

    def logout(self):
        self.loginWin.Le_name.setDisabled(False)
        self.loginWin.Le_passw.setDisabled(False)
        self.loginWin.lbl_infoLogin.setText("")

        self.loginWin.Le_name.setText("")
        self.loginWin.Le_passw.setText("")
        self.loginWin.btn_login.setText("Ingresar")

        #print("terminando")
        self.thread_data.terminate()
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
        i = 0
        while True:
            i += 1
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
    #print("adiós")

    sys.exit(exit_code)
    #sys.exit(app.exec_())