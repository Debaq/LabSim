# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CVC.ui'
##
## Created by: Qt User Interface Compiler version 6.2.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_CVC(object):
    def setupUi(self, CVC):
        if not CVC.objectName():
            CVC.setObjectName(u"CVC")
        CVC.resize(756, 608)
        self.verticalLayout_2 = QVBoxLayout(CVC)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.frame_central = QFrame(CVC)
        self.frame_central.setObjectName(u"frame_central")
        self.frame_central.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        self.frame_central.setFrameShape(QFrame.StyledPanel)
        self.frame_central.setFrameShadow(QFrame.Raised)
        self.layout_central = QVBoxLayout(self.frame_central)
        self.layout_central.setObjectName(u"layout_central")
        self.frame_menu = QFrame(self.frame_central)
        self.frame_menu.setObjectName(u"frame_menu")
        self.frame_menu.setMinimumSize(QSize(0, 30))
        self.frame_menu.setMaximumSize(QSize(16777215, 30))
        self.frame_menu.setStyleSheet(u"background-color: rgb(85, 170, 255);")
        self.layout_frame = QHBoxLayout(self.frame_menu)
        self.layout_frame.setObjectName(u"layout_frame")
        self.layout_frame.setContentsMargins(-1, 0, -1, 0)
        self.btn_profile = QPushButton(self.frame_menu)
        self.btn_profile.setObjectName(u"btn_profile")
        self.btn_profile.setFlat(True)

        self.layout_frame.addWidget(self.btn_profile)

        self.line_4 = QFrame(self.frame_menu)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.VLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.layout_frame.addWidget(self.line_4)

        self.btn_save = QPushButton(self.frame_menu)
        self.btn_save.setObjectName(u"btn_save")
        self.btn_save.setFlat(True)

        self.layout_frame.addWidget(self.btn_save)

        self.line_5 = QFrame(self.frame_menu)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.layout_frame.addWidget(self.line_5)

        self.btn_print = QPushButton(self.frame_menu)
        self.btn_print.setObjectName(u"btn_print")
        self.btn_print.setFlat(True)

        self.layout_frame.addWidget(self.btn_print)

        self.line_6 = QFrame(self.frame_menu)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.layout_frame.addWidget(self.line_6)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout_frame.addItem(self.horizontalSpacer_2)


        self.layout_central.addWidget(self.frame_menu)

        self.frame_data = QFrame(self.frame_central)
        self.frame_data.setObjectName(u"frame_data")
        self.frame_data.setMinimumSize(QSize(0, 60))
        self.frame_data.setMaximumSize(QSize(16777215, 60))
        self.layout_data = QHBoxLayout(self.frame_data)
        self.layout_data.setObjectName(u"layout_data")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.lbl_name = QLabel(self.frame_data)
        self.lbl_name.setObjectName(u"lbl_name")
        font = QFont()
        font.setPointSize(20)
        self.lbl_name.setFont(font)

        self.verticalLayout_4.addWidget(self.lbl_name)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lbl_sex = QLabel(self.frame_data)
        self.lbl_sex.setObjectName(u"lbl_sex")

        self.horizontalLayout_6.addWidget(self.lbl_sex)

        self.lbl_id = QLabel(self.frame_data)
        self.lbl_id.setObjectName(u"lbl_id")

        self.horizontalLayout_6.addWidget(self.lbl_id)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)


        self.layout_data.addLayout(self.verticalLayout_4)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.lbl_age = QLabel(self.frame_data)
        self.lbl_age.setObjectName(u"lbl_age")
        font1 = QFont()
        font1.setPointSize(15)
        self.lbl_age.setFont(font1)
        self.lbl_age.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_5.addWidget(self.lbl_age)

        self.lbl_birthday = QLabel(self.frame_data)
        self.lbl_birthday.setObjectName(u"lbl_birthday")
        self.lbl_birthday.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_5.addWidget(self.lbl_birthday)


        self.layout_data.addLayout(self.verticalLayout_5)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.lbl_test = QLabel(self.frame_data)
        self.lbl_test.setObjectName(u"lbl_test")
        self.lbl_test.setFont(font1)
        self.lbl_test.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_3.addWidget(self.lbl_test)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lbl_date_test = QLabel(self.frame_data)
        self.lbl_date_test.setObjectName(u"lbl_date_test")
        self.lbl_date_test.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.lbl_date_test)

        self.lbl_side_eye = QLabel(self.frame_data)
        self.lbl_side_eye.setObjectName(u"lbl_side_eye")
        font2 = QFont()
        font2.setPointSize(15)
        font2.setBold(True)
        self.lbl_side_eye.setFont(font2)
        self.lbl_side_eye.setStyleSheet(u"color: rgb(85, 170, 127);")
        self.lbl_side_eye.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.lbl_side_eye)


        self.verticalLayout_3.addLayout(self.horizontalLayout_7)


        self.layout_data.addLayout(self.verticalLayout_3)


        self.layout_central.addWidget(self.frame_data)

        self.line = QFrame(self.frame_central)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.layout_central.addWidget(self.line)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.layout_eye = QHBoxLayout()
        self.layout_eye.setObjectName(u"layout_eye")

        self.horizontalLayout_3.addLayout(self.layout_eye)

        self.layout_graph = QVBoxLayout()
        self.layout_graph.setObjectName(u"layout_graph")

        self.horizontalLayout_3.addLayout(self.layout_graph)

        self.verticalFrame = QFrame(self.frame_central)
        self.verticalFrame.setObjectName(u"verticalFrame")
        self.verticalFrame.setMaximumSize(QSize(150, 16777215))
        self.verticalLayout = QVBoxLayout(self.verticalFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btn_play_pause = QPushButton(self.verticalFrame)
        self.btn_play_pause.setObjectName(u"btn_play_pause")
        self.btn_play_pause.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_play_pause)

        self.btn_state = QPushButton(self.verticalFrame)
        self.btn_state.setObjectName(u"btn_state")
        self.btn_state.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_state)

        self.btn_param = QPushButton(self.verticalFrame)
        self.btn_param.setObjectName(u"btn_param")
        self.btn_param.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_param)

        self.btn_demo = QPushButton(self.verticalFrame)
        self.btn_demo.setObjectName(u"btn_demo")
        self.btn_demo.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_demo)

        self.btn_change_eye = QPushButton(self.verticalFrame)
        self.btn_change_eye.setObjectName(u"btn_change_eye")
        self.btn_change_eye.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_change_eye)

        self.btn_cancel = QPushButton(self.verticalFrame)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.verticalLayout.addWidget(self.btn_cancel)

        self.lbl_time = QLabel(self.verticalFrame)
        self.lbl_time.setObjectName(u"lbl_time")
        self.lbl_time.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_time)


        self.horizontalLayout_3.addWidget(self.verticalFrame)


        self.layout_central.addLayout(self.horizontalLayout_3)

        self.line_2 = QFrame(self.frame_central)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.layout_central.addWidget(self.line_2)

        self.horizontalFrame_3 = QFrame(self.frame_central)
        self.horizontalFrame_3.setObjectName(u"horizontalFrame_3")
        self.horizontalFrame_3.setMaximumSize(QSize(16777215, 60))
        self.horizontalLayout_4 = QHBoxLayout(self.horizontalFrame_3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.layout_graph_response = QHBoxLayout()
        self.layout_graph_response.setObjectName(u"layout_graph_response")

        self.horizontalLayout_4.addLayout(self.layout_graph_response)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.lbl_flase_positive = QLabel(self.horizontalFrame_3)
        self.lbl_flase_positive.setObjectName(u"lbl_flase_positive")

        self.verticalLayout_6.addWidget(self.lbl_flase_positive)

        self.lbl_lost_fixed = QLabel(self.horizontalFrame_3)
        self.lbl_lost_fixed.setObjectName(u"lbl_lost_fixed")

        self.verticalLayout_6.addWidget(self.lbl_lost_fixed)


        self.horizontalLayout_4.addLayout(self.verticalLayout_6)


        self.layout_central.addWidget(self.horizontalFrame_3)


        self.verticalLayout_2.addWidget(self.frame_central)

        self.horizontalFrame = QFrame(CVC)
        self.horizontalFrame.setObjectName(u"horizontalFrame")
        self.horizontalFrame.setMaximumSize(QSize(16777215, 120))
        self.horizontalLayout = QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, -1, 0, -1)
        self.btn_up = QPushButton(self.horizontalFrame)
        self.btn_up.setObjectName(u"btn_up")
        self.btn_up.setMinimumSize(QSize(0, 40))
        self.btn_up.setMaximumSize(QSize(40, 40))

        self.gridLayout.addWidget(self.btn_up, 0, 2, 1, 1)

        self.btn_left = QPushButton(self.horizontalFrame)
        self.btn_left.setObjectName(u"btn_left")
        self.btn_left.setMinimumSize(QSize(0, 40))
        self.btn_left.setMaximumSize(QSize(40, 40))

        self.gridLayout.addWidget(self.btn_left, 1, 1, 1, 1)

        self.btn_down = QPushButton(self.horizontalFrame)
        self.btn_down.setObjectName(u"btn_down")
        self.btn_down.setMinimumSize(QSize(0, 40))
        self.btn_down.setMaximumSize(QSize(40, 16777215))

        self.gridLayout.addWidget(self.btn_down, 2, 2, 1, 1)

        self.btn_right = QPushButton(self.horizontalFrame)
        self.btn_right.setObjectName(u"btn_right")
        self.btn_right.setMinimumSize(QSize(0, 40))
        self.btn_right.setMaximumSize(QSize(40, 40))

        self.gridLayout.addWidget(self.btn_right, 1, 3, 1, 1)


        self.horizontalLayout.addLayout(self.gridLayout)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addWidget(self.horizontalFrame)


        self.retranslateUi(CVC)

        QMetaObject.connectSlotsByName(CVC)
    # setupUi

    def retranslateUi(self, CVC):
        CVC.setWindowTitle(QCoreApplication.translate("CVC", u"CVC", None))
        self.btn_profile.setText(QCoreApplication.translate("CVC", u"Datos usuario", None))
        self.btn_save.setText(QCoreApplication.translate("CVC", u"Guardar", None))
        self.btn_print.setText(QCoreApplication.translate("CVC", u"Imprimir", None))
        self.lbl_name.setText(QCoreApplication.translate("CVC", u"Name, Name", None))
        self.lbl_sex.setText(QCoreApplication.translate("CVC", u"Sex", None))
        self.lbl_id.setText(QCoreApplication.translate("CVC", u"ID:000", None))
        self.lbl_age.setText(QCoreApplication.translate("CVC", u"20 a\u00f1os", None))
        self.lbl_birthday.setText(QCoreApplication.translate("CVC", u"Fecha de Nacimiento: 12/08/1986", None))
        self.lbl_test.setText(QCoreApplication.translate("CVC", u"TEST", None))
        self.lbl_date_test.setText(QCoreApplication.translate("CVC", u"Fecha test", None))
        self.lbl_side_eye.setText(QCoreApplication.translate("CVC", u"OD", None))
        self.btn_play_pause.setText(QCoreApplication.translate("CVC", u"Iniciar", None))
        self.btn_state.setText(QCoreApplication.translate("CVC", u"Mostrar estado", None))
        self.btn_param.setText(QCoreApplication.translate("CVC", u"Cambiar Par\u00e1metros", None))
        self.btn_demo.setText(QCoreApplication.translate("CVC", u"DEMOSTRACI\u00d3N", None))
        self.btn_change_eye.setText(QCoreApplication.translate("CVC", u"Examinar el otro ojo", None))
        self.btn_cancel.setText(QCoreApplication.translate("CVC", u"Cancelar prueba", None))
        self.lbl_time.setText(QCoreApplication.translate("CVC", u"Hora: 00:00", None))
        self.lbl_flase_positive.setText(QCoreApplication.translate("CVC", u"Falsos negativos : 00/00", None))
        self.lbl_lost_fixed.setText(QCoreApplication.translate("CVC", u"Perdidas de fijaci\u00f3n : 00/00", None))
        self.btn_up.setText(QCoreApplication.translate("CVC", u"up", None))
        self.btn_left.setText(QCoreApplication.translate("CVC", u"left", None))
        self.btn_down.setText(QCoreApplication.translate("CVC", u"down", None))
        self.btn_right.setText(QCoreApplication.translate("CVC", u"right", None))
    # retranslateUi

