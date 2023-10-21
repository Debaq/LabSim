# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Main.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(933, 600)
        MainWindow.setStyleSheet(u"QPushbutton#btn_max {\n"
"  color: rgb(220, 220, 220);\n"
"\n"
"}")
        self.actionLogin = QAction(MainWindow)
        self.actionLogin.setObjectName(u"actionLogin")
        self.actionSalir = QAction(MainWindow)
        self.actionSalir.setObjectName(u"actionSalir")
        self.actionEnviar_un_ticket = QAction(MainWindow)
        self.actionEnviar_un_ticket.setObjectName(u"actionEnviar_un_ticket")
        self.actionAcerca_de = QAction(MainWindow)
        self.actionAcerca_de.setObjectName(u"actionAcerca_de")
        self.actionCascada = QAction(MainWindow)
        self.actionCascada.setObjectName(u"actionCascada")
        self.actionCerrar_todas = QAction(MainWindow)
        self.actionCerrar_todas.setObjectName(u"actionCerrar_todas")
        self.actionTiles = QAction(MainWindow)
        self.actionTiles.setObjectName(u"actionTiles")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.barra = QWidget(self.centralwidget)
        self.barra.setObjectName(u"barra")
        self.barra.setMaximumSize(QSize(16777215, 30))
        self.horizontalLayout_2 = QHBoxLayout(self.barra)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(6, -1, 6, -1)
        self.lbl_title = QLabel(self.barra)
        self.lbl_title.setObjectName(u"lbl_title")

        self.horizontalLayout_4.addWidget(self.lbl_title)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)

        self.frame_sec = QFrame(self.barra)
        self.frame_sec.setObjectName(u"frame_sec")
        self.horizontalLayout_5 = QHBoxLayout(self.frame_sec)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(20, -1, -1, -1)

        self.horizontalLayout_2.addWidget(self.frame_sec)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.cmb_case = QComboBox(self.barra)
        self.cmb_case.setObjectName(u"cmb_case")

        self.horizontalLayout_2.addWidget(self.cmb_case)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(10)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, -1, 6, -1)
        self.lbl_name = QLabel(self.barra)
        self.lbl_name.setObjectName(u"lbl_name")
        font = QFont()
        font.setPointSize(8)
        self.lbl_name.setFont(font)
        self.lbl_name.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.lbl_name)

        self.btn_login = QPushButton(self.barra)
        self.btn_login.setObjectName(u"btn_login")
        self.btn_login.setMinimumSize(QSize(0, 20))
        self.btn_login.setMaximumSize(QSize(60, 25))
        self.btn_login.setFont(font)
        self.btn_login.setAutoFillBackground(False)
        self.btn_login.setCheckable(False)

        self.horizontalLayout_6.addWidget(self.btn_login)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, -1, -1, -1)
        self.horizontalGroupBox = QGroupBox(self.barra)
        self.horizontalGroupBox.setObjectName(u"horizontalGroupBox")
        self.horizontalGroupBox.setMinimumSize(QSize(0, 30))
        self.horizontalGroupBox.setFlat(True)
        self.control_win = QHBoxLayout(self.horizontalGroupBox)
        self.control_win.setSpacing(0)
        self.control_win.setObjectName(u"control_win")
        self.control_win.setContentsMargins(0, 0, 0, 0)
        self.btn_min = QPushButton(self.horizontalGroupBox)
        self.btn_min.setObjectName(u"btn_min")
        self.btn_min.setMinimumSize(QSize(10, 0))
        self.btn_min.setMaximumSize(QSize(20, 20))
        self.btn_min.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.btn_min.setFlat(True)

        self.control_win.addWidget(self.btn_min)

        self.btn_max = QPushButton(self.horizontalGroupBox)
        self.btn_max.setObjectName(u"btn_max")
        self.btn_max.setMaximumSize(QSize(20, 20))
        self.btn_max.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.btn_max.setFlat(True)

        self.control_win.addWidget(self.btn_max)

        self.btn_salir = QPushButton(self.horizontalGroupBox)
        self.btn_salir.setObjectName(u"btn_salir")
        self.btn_salir.setMaximumSize(QSize(20, 20))
        self.btn_salir.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.btn_salir.setFlat(True)

        self.control_win.addWidget(self.btn_salir)


        self.horizontalLayout_3.addWidget(self.horizontalGroupBox)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)


        self.verticalLayout_3.addWidget(self.barra)

        self.tool = QFrame(self.centralwidget)
        self.tool.setObjectName(u"tool")
        self.tool.setEnabled(True)
        self.layout_bar = QHBoxLayout(self.tool)
        self.layout_bar.setObjectName(u"layout_bar")
        self.layout_bar.setContentsMargins(-1, 3, 6, 3)
        self.frameAction = QFrame(self.tool)
        self.frameAction.setObjectName(u"frameAction")
        self.frameAction.setFont(font)
        self.layoutTest = QHBoxLayout(self.frameAction)
        self.layoutTest.setObjectName(u"layoutTest")
        self.layoutTest.setContentsMargins(-1, 0, -1, 0)

        self.layout_bar.addWidget(self.frameAction)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_bar.addItem(self.horizontalSpacer)

        self.layoutAction = QHBoxLayout()
        self.layoutAction.setObjectName(u"layoutAction")
        self.layoutAction.setContentsMargins(-1, -1, 0, -1)

        self.layout_bar.addLayout(self.layoutAction)


        self.verticalLayout_3.addWidget(self.tool)


        self.verticalLayout.addLayout(self.verticalLayout_3)

        self.widget_Mdi = QWidget(self.centralwidget)
        self.widget_Mdi.setObjectName(u"widget_Mdi")
        self.horizontalLayout = QHBoxLayout(self.widget_Mdi)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.widget_Mdi)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setMaximumSize(QSize(16777215, 20))
        self.statusbar.setFont(font)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionLogin.setText(QCoreApplication.translate("MainWindow", u"Ingresar", None))
        self.actionSalir.setText(QCoreApplication.translate("MainWindow", u"Salir", None))
        self.actionEnviar_un_ticket.setText(QCoreApplication.translate("MainWindow", u"Enviar un ticket", None))
        self.actionAcerca_de.setText(QCoreApplication.translate("MainWindow", u"Acerca de LabSim", None))
        self.actionCascada.setText(QCoreApplication.translate("MainWindow", u"Cascada", None))
        self.actionCerrar_todas.setText(QCoreApplication.translate("MainWindow", u"Cerrar todas", None))
        self.actionTiles.setText(QCoreApplication.translate("MainWindow", u"Lozas", None))
        self.lbl_title.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.lbl_name.setText(QCoreApplication.translate("MainWindow", u"Desconectado", None))
        self.btn_login.setText(QCoreApplication.translate("MainWindow", u"Ingresar", None))
        self.btn_min.setText(QCoreApplication.translate("MainWindow", u"_", None))
        self.btn_max.setText(QCoreApplication.translate("MainWindow", u"O", None))
        self.btn_salir.setText(QCoreApplication.translate("MainWindow", u"X", None))
    # retranslateUi

