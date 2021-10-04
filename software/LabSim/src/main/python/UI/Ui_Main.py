# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/UI/Main.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(933, 600)
        MainWindow.setStyleSheet("QPushbutton#btn_max {\n"
"  color: rgb(220, 220, 220);\n"
"\n"
"}")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.barra = QtWidgets.QFrame(self.centralwidget)
        self.barra.setMaximumSize(QtCore.QSize(16777215, 30))
        self.barra.setObjectName("barra")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.barra)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(6, -1, -1, -1)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.lbl_title = QtWidgets.QLabel(self.barra)
        self.lbl_title.setObjectName("lbl_title")
        self.horizontalLayout_4.addWidget(self.lbl_title)
        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.frame_sec = QtWidgets.QFrame(self.barra)
        self.frame_sec.setObjectName("frame_sec")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.frame_sec)
        self.horizontalLayout_5.setContentsMargins(20, -1, -1, -1)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.horizontalLayout_2.addWidget(self.frame_sec)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.lbl_name = QtWidgets.QLabel(self.barra)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.lbl_name.setFont(font)
        self.lbl_name.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lbl_name.setObjectName("lbl_name")
        self.horizontalLayout_2.addWidget(self.lbl_name)
        self.btn_login = QtWidgets.QPushButton(self.barra)
        self.btn_login.setMinimumSize(QtCore.QSize(0, 20))
        self.btn_login.setMaximumSize(QtCore.QSize(60, 25))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.btn_login.setFont(font)
        self.btn_login.setAutoFillBackground(False)
        self.btn_login.setObjectName("btn_login")
        self.horizontalLayout_2.addWidget(self.btn_login)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalGroupBox = QtWidgets.QGroupBox(self.barra)
        self.horizontalGroupBox.setMinimumSize(QtCore.QSize(0, 30))
        self.horizontalGroupBox.setFlat(True)
        self.horizontalGroupBox.setObjectName("horizontalGroupBox")
        self.control_win = QtWidgets.QHBoxLayout(self.horizontalGroupBox)
        self.control_win.setContentsMargins(0, 0, 0, 0)
        self.control_win.setSpacing(0)
        self.control_win.setObjectName("control_win")
        self.btn_min = QtWidgets.QPushButton(self.horizontalGroupBox)
        self.btn_min.setMinimumSize(QtCore.QSize(10, 0))
        self.btn_min.setMaximumSize(QtCore.QSize(20, 20))
        self.btn_min.setStyleSheet("color: rgb(255, 255, 255);")
        self.btn_min.setFlat(True)
        self.btn_min.setObjectName("btn_min")
        self.control_win.addWidget(self.btn_min)
        self.btn_max = QtWidgets.QPushButton(self.horizontalGroupBox)
        self.btn_max.setMaximumSize(QtCore.QSize(20, 20))
        self.btn_max.setStyleSheet("color: rgb(255, 255, 255);")
        self.btn_max.setFlat(True)
        self.btn_max.setObjectName("btn_max")
        self.control_win.addWidget(self.btn_max)
        self.btn_salir = QtWidgets.QPushButton(self.horizontalGroupBox)
        self.btn_salir.setMaximumSize(QtCore.QSize(20, 20))
        self.btn_salir.setStyleSheet("color: rgb(255, 255, 255);")
        self.btn_salir.setFlat(True)
        self.btn_salir.setObjectName("btn_salir")
        self.control_win.addWidget(self.btn_salir)
        self.horizontalLayout_3.addWidget(self.horizontalGroupBox)
        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)
        self.verticalLayout_3.addWidget(self.barra)
        self.tool = QtWidgets.QFrame(self.centralwidget)
        self.tool.setEnabled(True)
        self.tool.setObjectName("tool")
        self.layout_bar = QtWidgets.QHBoxLayout(self.tool)
        self.layout_bar.setContentsMargins(-1, 3, 6, 3)
        self.layout_bar.setObjectName("layout_bar")
        self.frameAction = QtWidgets.QFrame(self.tool)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.frameAction.setFont(font)
        self.frameAction.setObjectName("frameAction")
        self.layoutTest = QtWidgets.QHBoxLayout(self.frameAction)
        self.layoutTest.setContentsMargins(-1, 0, -1, 0)
        self.layoutTest.setObjectName("layoutTest")
        self.layout_bar.addWidget(self.frameAction)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.layout_bar.addItem(spacerItem2)
        self.layoutAction = QtWidgets.QHBoxLayout()
        self.layoutAction.setContentsMargins(-1, -1, 0, -1)
        self.layoutAction.setObjectName("layoutAction")
        self.layout_bar.addLayout(self.layoutAction)
        self.verticalLayout_3.addWidget(self.tool)
        self.mdiArea = QtWidgets.QMdiArea(self.centralwidget)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        brush = QtGui.QBrush(QtGui.QColor(136, 142, 147))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.mdiArea.setBackground(brush)
        self.mdiArea.setViewMode(QtWidgets.QMdiArea.SubWindowView)
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.setObjectName("mdiArea")
        self.verticalLayout_3.addWidget(self.mdiArea)
        self.verticalLayout.addLayout(self.verticalLayout_3)
        self.widget_Mdi = QtWidgets.QWidget(self.centralwidget)
        self.widget_Mdi.setObjectName("widget_Mdi")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget_Mdi)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout.addWidget(self.widget_Mdi)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setMaximumSize(QtCore.QSize(16777215, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.statusbar.setFont(font)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionLogin = QtWidgets.QAction(MainWindow)
        self.actionLogin.setObjectName("actionLogin")
        self.actionSalir = QtWidgets.QAction(MainWindow)
        self.actionSalir.setObjectName("actionSalir")
        self.actionEnviar_un_ticket = QtWidgets.QAction(MainWindow)
        self.actionEnviar_un_ticket.setObjectName("actionEnviar_un_ticket")
        self.actionAcerca_de = QtWidgets.QAction(MainWindow)
        self.actionAcerca_de.setObjectName("actionAcerca_de")
        self.actionCascada = QtWidgets.QAction(MainWindow)
        self.actionCascada.setObjectName("actionCascada")
        self.actionCerrar_todas = QtWidgets.QAction(MainWindow)
        self.actionCerrar_todas.setObjectName("actionCerrar_todas")
        self.actionTiles = QtWidgets.QAction(MainWindow)
        self.actionTiles.setObjectName("actionTiles")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.lbl_title.setText(_translate("MainWindow", "TextLabel"))
        self.lbl_name.setText(_translate("MainWindow", "Desconectado"))
        self.btn_login.setText(_translate("MainWindow", "Ingresar"))
        self.btn_min.setText(_translate("MainWindow", "_"))
        self.btn_max.setText(_translate("MainWindow", "O"))
        self.btn_salir.setText(_translate("MainWindow", "X"))
        self.actionLogin.setText(_translate("MainWindow", "Ingresar"))
        self.actionSalir.setText(_translate("MainWindow", "Salir"))
        self.actionEnviar_un_ticket.setText(_translate("MainWindow", "Enviar un ticket"))
        self.actionAcerca_de.setText(_translate("MainWindow", "Acerca de LabSim"))
        self.actionCascada.setText(_translate("MainWindow", "Cascada"))
        self.actionCerrar_todas.setText(_translate("MainWindow", "Cerrar todas"))
        self.actionTiles.setText(_translate("MainWindow", "Lozas"))
