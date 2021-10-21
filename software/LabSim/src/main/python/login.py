# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Zmeter                       #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from PyQt6.QtWidgets import QWidget


from UI.Ui_Login import Ui_Login



class MainLogin(QWidget, Ui_Login):
    def __init__(self):
        QWidget.__init__(self)
        # Inicialización de la ventana y propiedades
        self.setupUi(self)
   

if __name__ == "__main__":
    pass
