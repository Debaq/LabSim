# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - ListWords                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import sys
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,QToolBox
from lib.helpers import Preferences


class_pref = Preferences()
list_words = class_pref.get("L_P")




class Ui_ListWords(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(292, 475)
        self.centralLayout = QVBoxLayout(Form)
        self.centralLayout.setObjectName(u"centralLayout")





class ListWords(QWidget, Ui_ListWords):
    def __init__(self):
        QWidget.__init__(self)
        # Inicialización de la ventana y propiedades
        self.setupUi(self)
        self.tabs = QTabWidget()
        self.tabs.setObjectName(u"tabs")



        names =  []
        pages = []
        buttons = []
        i = 0
        for key_i , val_i in list_words.items():
            for key_j, val_j in list_words[key_i].items():
                name = ("{} ({})".format(key_i, key_j))
                names.append([name])
                if 'page_temp'in locals():
                    pages.append(pages_temp)
                else:
                    pages_temp = []
                
                prev_page = ""
                for key_k, val_k in list_words[key_i][key_j].items():
                    page = "Lista {}".format(key_k)
                    pages_temp.append(page)

                    if 'buttons_temp' in locals():
                        buttons.append(buttons_temp)
                    else:
                        buttons_temp = []
                    #print(page)
                    if prev_page == page:
                        buttons_temp = []
                    prev_page = page
                    for l in list_words[key_i][key_j][key_k]:
                        buttons_temp.append(l)
                        
        #print(buttons)

   

    def createTabs(self, name, page, buttons):
        tab = QWidget()
        tab.setObjectName(u"{}".format(name))
        verticalLayout_2 = QVBoxLayout(tab)
        toolBox = QToolBox(tab)
            
