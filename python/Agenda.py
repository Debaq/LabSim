# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 0.9 - Audiometro                   #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QTableWidgetItem, QAbstractItemView
from UI.Ui_agenda import Ui_Form
from lib.helpers import Shedule



class Agenda(QWidget, Ui_Form):
    def __init__(self, permissions, obj):
        # Inicialización de la ventana y propiedades
        #super(Audiometer, self).__init__()
        super().__init__()
        self.setupUi(self)

        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.read_shedule()
        #self.populate_shedule()
        
        if permissions == 777:
            self.pushButton.setEnabled(False)
            self.pushButton.clicked.connect(lambda:self.create_case(obj))
        
    def create_case(self,obj):
        obj.activate_auto("CREATE_A")

        
    def read_shedule(self):
        shedule = Shedule()
        self.shedule = shedule.get()
        
    def populate_shedule(self, agenda="agenda_1"):
        
        self.tableWidget.setRowCount(len(self.shedule[agenda]))
        for i in self.shedule[agenda]:
            for idx_user in range(len(self.shedule[agenda][i])):
                user = self.shedule[agenda][i][idx_user]
                #print(f"data:{user} idx:{idx_user} i:{i}")
                item = QTableWidgetItem(user)
                self.tableWidget.setItem(int(i),idx_user,item)
        