# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                          VER. 0.7.5                           #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
# pip install https://build-system.fman.io/pro/12a9a98c-755b-4d95-9c60-a17ae1a74d6c/1.0.7#egg=fbs
#https://f002.backblazeb2.com/file/TMEduca/LabSim/LabSimSetup0.8.4.exe

__VERSION__ = 'v0.8.42'

import json
import sys
import time

import requests
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMdiSubWindow, QMessageBox,
                             QPushButton, QGroupBox, QHBoxLayout, QWidget, QMdiArea, QMenu, QAction)
from PyQt5.QtGui import QPixmap, QPainter


import ABR
import Audiometer
import ListWords
import login as Ui_login
import Z
from lib.helpers import Preferences, Storage
from UI.Ui_Main import Ui_MainWindow
from UI.Ui_frameSubMdi import Ui_Form as UI_frameSubMdi
from UI.Ui_command_voice_A import Ui_Form as commandVoiceA

Preferences = Preferences()
APPS = Preferences.get("APP")
SECTORS = Preferences.get("SECTORS")
BOXS = Preferences.get("BOXS")
STYLES = Preferences.get("styles")
LANGUAJE = Preferences.get("lang")


class frameSubMdi(QWidget, UI_frameSubMdi):
    def __init__(self, UI, name="Test"):
        super(frameSubMdi, self).__init__()
        self.setupUi(self)
        self.ui = UI
        self.layout_content.addWidget(self.ui)
        self.clickPosition=QPoint()
        self.barra.mouseMoveEvent = self.moveWindow

    def moveWindow(self, e):
            if e.buttons() == Qt.LeftButton:  
                #Move window 
                x = e.x()
                y = e.y()
                i = self.parent()
                #print("{} , {} , {}, {}".format(x, y, self.clickPosition, i.pos()))
                #print(e.globalPos()+ self.clickPosition)
                x = e.windowPos().toPoint().x()
                y = e.windowPos().toPoint().y()
                x= int(x)
                y= int(y)
                i.move(x-1,y-88)
                self.clickPosition = e.globalPos()
                e.accept()

class MdiArea(QMdiArea):
    def __init__(self):
        super(MdiArea, self).__init__()
        self.mousePressEvent = self.moveWindow
        self.documentMode = True
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.currentSubWindow() == None:
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

    def moveWindow(self, e):
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
        super(ComandVoiceA, self).__init__()
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
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("LabSim {}".format(__VERSION__))
        self.lbl_title.setText("LabSim {}".format(__VERSION__))
        #BTNS
        self.btn_salir.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggle_MaxMin)
        self.btn_login.clicked.connect(self.activate_login)
        #Create MdiArea
        self.mdiArea = MdiArea()
        self.horizontalLayout.addWidget(self.mdiArea)
        #Create Stores and variables
        self.var_listWord = Storage(2)
        self.newLogin = False
        self.apps = APPS
        self.Boxs = BOXS
        self.sectors_lbl = SECTORS
        self.Modules = Storage(len(self.apps))
        self.prevPatient = str()
        #set movement window
        self.showMaximized()
        self.setMouseTracking(True)
        self.clickPosition=QPoint()
        self.barra.mouseMoveEvent = self.moveWindow
       

    ## Funciones de la ventana
    def sizebtn(self):
        width = (self.size().width())/2
        height = (self.size().height())/2
        #print("width:{} , height:{}".format(width, height))
        self.activate_login()
    
    def moveWindow(self, e):
            move = False
            if self.isMaximized(): #Not maximized
                self.toggle_MaxMin()
                move=True
            if self.isMaximized() == False: #Not maximized
                move = True
            if move:
                if e.buttons() == Qt.LeftButton:  
                    #Move window 
                    x = e.x()
                    y = e.y()
                    gx = e.globalX()
                    gy = e.globalY()
                    #print(e.globalPost())
                    #self.move(self.pos() + e.globalPos() - self.clickPosition)
                    #self.move(e.globalPos())
                    self.move(gx, gy)
                    self.clickPosition = e.globalPos()
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
        j = 0
        for i in self.Boxs:
            if self.Boxs[i][0]:
                btn = QPushButton()
                btn.setObjectName(i)
                btn.setText(self.Boxs[i][2])
                btn.clicked.connect(self.changeArea)
                btn.setMinimumHeight(30)
                btn.setCheckable(True)
                btn.setAutoExclusive(True)
                self.horizontalLayout_5.addWidget(btn)
                if j == 1:
                    active = i
            j = j + 1
        btn_selec = self.frame_sec.findChild(QPushButton,active)
        btn_selec.setChecked(True)
        self.chargeBtnsArea(active)
        self.btns_actions()
        
    def changeArea(self):
        for i in reversed(range( self.layoutTest.count())): 
             self.layoutTest.itemAt(i).widget().deleteLater()
        widget = self.sender()
        objName = widget.objectName()
        self.chargeBtnsArea(objName)

    def chargeBtnsArea(self, area):
        for i in self.Boxs[area][1]:
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
        self.btn_commandVoice = QPushButton("comandos de voz")
        self.btn_commandVoice.clicked.connect(self.activate_Cvoice)
        self.layoutAction.addWidget(self.btn_commandVoice)

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

    def clearToolbar(self):
        for i in reversed(range( self.layoutTest.count())): 
             self.layoutTest.itemAt(i).widget().deleteLater()
        for i in reversed(range( self.horizontalLayout_5.count())): 
             self.horizontalLayout_5.itemAt(i).widget().deleteLater()
        for i in reversed(range( self.layoutAction.count())): 
             self.layoutAction.itemAt(i).widget().deleteLater()

    ##Funciones para las SubWindows
    def flags(self, var, t=True):
        if t == True:
            var.setWindowFlags(Qt.Window |
                               Qt.CustomizeWindowHint |
                               Qt.WindowTitleHint |
                               Qt.FramelessWindowHint|
                               Qt.WindowCloseButtonHint |
                               Qt.WindowStaysOnTopHint)
        else:
            var.setWindowFlags(Qt.Window |
                               Qt.CustomizeWindowHint |
                               Qt.WindowTitleHint |
                               Qt.FramelessWindowHint|
                               Qt.WindowMaximizeButtonHint |
                               Qt.WindowCloseButtonHint |
                               Qt.WindowStaysOnTopHint)

    def showHide(self, pos):
        if self.Modules.get(pos).isHidden():
            self.Modules.get(pos).show()
        else:
            self.Modules.get(pos).hide()

    def createInsWidegt(self, data):
        self.data = data
        self.A = frameSubMdi(Audiometer.Audiometer(self.data))
        self.A.ui.signal_speech.connect(self.speechlist_mode)
        self.Z = frameSubMdi(Z.ZControl())
        self.W = frameSubMdi(ListWords.ListWords(self.data))
        self.ABR = frameSubMdi(ABR.MainWindow())
        self.cVoice = frameSubMdi(ComandVoiceA())
        self.cVoice.ui.btn_checked.connect(self.A.ui.supra)

    def createSubWindow(self, widg, name, Z, fix=[True, True], size=[740,560], flags=True, position=[0,0]):
        if self.Modules.isFull(Z):
            self.showHide(Z)
        else:   
            sub = QMdiSubWindow()
            sub.setWidget(widg)
            #sub.setObjectName("Test")
            widg.lbl_title.setText(name)
            self.mdiArea.addSubWindow(sub)
            if position != [0,0]:
                x,y = int(position[0]), int(position[1])
                sub.move(x,y-220)
            #sub.setWindowTitle(name)
            self.flags(sub, flags)
            if fix[0] == True or fix[1] == True:
                if fix[0] == True:
                    sub.setMaximumSize(size[0], size[1])
                if fix[1] == True:
                    sub.setMinimumSize(size[0], size[1])
                    sub.resize(size[0], size[1])
            sub.show()
            list_wi = self.mdiArea.subWindowList()
            self.Modules.set(Z, list_wi[-1])

    ##Conexión al Servidor
    def thread_data_clicked(self):
        self.thread_data = ReadThread()
        self.thread_data.name = self.loginWin.ui.Le_name.text()
        self.thread_data.passw = self.loginWin.ui.Le_passw.text()
        self.thread_data.start()
        self.thread_data.data_signal.connect(self.refresh_data)

    def refresh_data(self, data):
        self.data = data
        if self.newLogin:
            self.createInsWidegt(self.data)
            self.btns_seccion()

            self.newLogin = False
        self.changeStateBtnAreas(self.data["box"])
        if self.data['result'] == 0:
            text = "conexión exitosa"
        else:
            text = self.sectors_lbl[data['sector']]
            if self.prevPatient != self.data['sector']:
                self.A.ui.laSuper(self.data)
                self.W.ui.laSuper(self.data)
                self.Z.ui.laSuper(self.data)
                self.prevPatient = self.data['sector']
            self.ABR.ui.laSuper(self.data)
        self.statusbar.showMessage(text)
        # log off external
        if self.data['state_login'] == "0":
            self.logout()
            QMessageBox.critical(self, "sesión", "Sesión terminada")

    def login(self):
        button_login = self.loginWin.ui.btn_login.text()
        name = self.loginWin.ui.Le_name.text()
        passw = self.loginWin.ui.Le_passw.text()
        #print("{} : {} -- {}".format(name,passw, button_login))
        if button_login == "Salir":
            self.logout()
        else:
            data = {'user': name, 'password': passw, 'request': 'login'}
            result = request_API(data)
            if result == "ok":
                self.loginWin.ui.Le_name.setDisabled(True)
                self.loginWin.ui.Le_passw.setDisabled(True)
                self.thread_data_clicked()
                self.loginWin.ui.btn_login.setText("Salir")
                self.btn_login.setText("Salir")
                self.showHide(0)
                text = "{}".format(name)
                self.lbl_name.setText(text)
                self.statusbar.showMessage(text)
                self.newLogin = True
            else:
                QMessageBox.critical(self, "Ingreso", "Error de credenciales")

    def logout(self):
        name = self.loginWin.ui.Le_name.text()
        passw = self.loginWin.ui.Le_passw.text()
        self.thread_data.terminate()
        data = {'user': name, 'password': passw, 'request': 'logout'}
        request_API(data)
        self.loginWin.ui.Le_name.setDisabled(False)
        self.loginWin.ui.Le_passw.setDisabled(False)
        self.loginWin.ui.Le_name.setText("")
        self.loginWin.ui.Le_passw.setText("")
        self.loginWin.ui.btn_login.setText("Ingresar")
        self.btn_login.setText("Ingresar")
        self.lbl_name.setText("Desconectado")
        self.mdiArea.closeAll()
        self.clearToolbar()
        #self.close()

###Activate subwindows
    def activate_login(self):
        name = self.apps["Login"][1]
        Z = self.apps["Login"][2]
        size = self.apps["Login"][4]
        self.loginWin = frameSubMdi(Ui_login.MainLogin())
        #self.loginWin = Ui_login.MainLogin()
        self.loginWin.ui.btn_login.clicked.connect(self.login)
        width = (self.size().width())/2
        height = (self.size().height())/2
        w=size[0]/2
        h=size[1]/2
        #print("width:{} , height:{} , w:{} , h:{} ".format(width, height, w, h))
        pos = [width-w, height-h]
        self.createSubWindow(self.loginWin, name, Z, size=size, position=pos)

    def activate_a(self):
        name = self.apps["A"][1]
        Z = self.apps["A"][2]
        size = self.apps["A"][4]
        width = (self.size().width())/2
        height = (self.size().height())/2
        w=size[0]/2
        h=size[1]/2
        pos = [width-w, height-h]
        self.createSubWindow(self.A, name, Z, size= size, position=pos)

    def activate_z(self):
        name = self.apps["Z"][1]
        Z = self.apps["Z"][2]
        size = self.apps["Z"][4]
        width = (self.size().width())/2
        height = (self.size().height())/2
        w=size[0]/2
        h=size[1]/2
        pos = [width-w, height-h]
        self.createSubWindow(self.Z, name, Z, size= size, position=pos)

    def activate_abr(self):
        name = self.apps["ABR"][1]
        Z = self.apps["ABR"][2]
        fix = self.apps["ABR"][3]
        size = self.apps["ABR"][4]
        width = (self.size().width())/2
        height = (self.size().height())/2
        w=size[0]/2
        h=size[1]/2
        pos = [width-w, height-h]
        self.createSubWindow(self.ABR, name, Z, fix=fix, size=size,position=pos)

    def activate_Cvoice(self):
        name = self.apps["cVoice"][1]
        Z = self.apps["cVoice"][2]
        size = self.apps["cVoice"][4]
        self.createSubWindow(self.cVoice, name, Z, size=size)

    def activate_listWords(self):
        name = self.apps["W"][1]
        Z = self.apps["W"][2]
        size = self.apps["W"][4]
        if self.var_listWord.get(0):
            if self.Modules.isFull(Z):
                self.Modules.get(Z).show()
            else:
                self.createSubWindow(self.W, name, Z, size=size)
        else:
            self.Modules.get(Z).hide()

    def speechlist_mode(self, state):
        self.var_listWord.getAll(True)
        self.var_listWord.listSet(state, False)
        self.var_listWord.getAll(True)
        self.activate_listWords()
        self.W.ui.playable[1] = state[2]
        self.W.ui.playable[2] = state[3]
        self.W.ui.playable[3] = state[4]
        if state[1]:
            self.W.ui.playable[0] = True
        else:
            self.W.ui.playable[0] = False

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

    sys.exit(exit_code)
    # sys.exit(app.exec_())
