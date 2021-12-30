# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Zmeter                       #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget
from fbs_runtime.application_context.PyQt5 import ApplicationContext


from UI.Ui_Login import Ui_Login



class MainLogin(QWidget, Ui_Login):
    def __init__(self):
        QWidget.__init__(self)
        # Inicialización de la ventana y propiedades
        self.setupUi(self)
   



if __name__ == "__main__":
    appctxt = ApplicationContext()     
    app = QApplication([])
    window = MainLogin()
    window.show()
    sys.exit(app.exec())
