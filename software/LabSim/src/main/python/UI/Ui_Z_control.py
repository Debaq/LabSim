# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Z_control.ui'
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
from PySide6.QtWidgets import (QApplication, QDial, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Z_control(object):
    def setupUi(self, Z_control):
        if not Z_control.objectName():
            Z_control.setObjectName(u"Z_control")
        Z_control.resize(740, 540)
        Z_control.setMinimumSize(QSize(740, 540))
        Z_control.setMaximumSize(QSize(740, 540))
        self.verticalLayout = QVBoxLayout(Z_control)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 6, 6, 6)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer)

        self.frame_screen = QFrame(Z_control)
        self.frame_screen.setObjectName(u"frame_screen")
        self.frame_screen.setMinimumSize(QSize(600, 280))
        self.frame_screen.setMaximumSize(QSize(600, 300))
        self.frame_screen.setStyleSheet(u"background-color: rgb(85, 170, 255);")
        self.frame_screen.setFrameShape(QFrame.Box)
        self.frame_screen.setFrameShadow(QFrame.Sunken)
        self.frame_screen.setLineWidth(3)
        self.Screen_Layout = QHBoxLayout(self.frame_screen)
        self.Screen_Layout.setSpacing(0)
        self.Screen_Layout.setObjectName(u"Screen_Layout")
        self.Screen_Layout.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_6.addWidget(self.frame_screen)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.frame_btn_screen = QFrame(Z_control)
        self.frame_btn_screen.setObjectName(u"frame_btn_screen")
        self.frame_btn_screen.setMinimumSize(QSize(0, 31))
        self.frame_btn_screen.setMaximumSize(QSize(16777215, 31))
        self.layout_btn_screen = QHBoxLayout(self.frame_btn_screen)
        self.layout_btn_screen.setSpacing(30)
        self.layout_btn_screen.setObjectName(u"layout_btn_screen")
        self.layout_btn_screen.setContentsMargins(80, 0, 100, -1)
        self.btn_1 = QPushButton(self.frame_btn_screen)
        self.btn_1.setObjectName(u"btn_1")

        self.layout_btn_screen.addWidget(self.btn_1)

        self.btn_2 = QPushButton(self.frame_btn_screen)
        self.btn_2.setObjectName(u"btn_2")

        self.layout_btn_screen.addWidget(self.btn_2)

        self.btn_3 = QPushButton(self.frame_btn_screen)
        self.btn_3.setObjectName(u"btn_3")
        self.btn_3.setEnabled(False)

        self.layout_btn_screen.addWidget(self.btn_3)

        self.btn_4 = QPushButton(self.frame_btn_screen)
        self.btn_4.setObjectName(u"btn_4")
        self.btn_4.setEnabled(False)

        self.layout_btn_screen.addWidget(self.btn_4)

        self.btn_5 = QPushButton(self.frame_btn_screen)
        self.btn_5.setObjectName(u"btn_5")
        self.btn_5.setEnabled(False)

        self.layout_btn_screen.addWidget(self.btn_5)

        self.btn_6 = QPushButton(self.frame_btn_screen)
        self.btn_6.setObjectName(u"btn_6")
        self.btn_6.setEnabled(False)

        self.layout_btn_screen.addWidget(self.btn_6)


        self.verticalLayout.addWidget(self.frame_btn_screen)

        self.frame_control = QFrame(Z_control)
        self.frame_control.setObjectName(u"frame_control")
        self.frame_control.setMaximumSize(QSize(16777215, 200))
        self.horizontalLayout_3 = QHBoxLayout(self.frame_control)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.dial = QDial(self.frame_control)
        self.dial.setObjectName(u"dial")
        self.dial.setEnabled(False)
        self.dial.setMinimumSize(QSize(100, 100))
        self.dial.setMaximumSize(QSize(100, 100))
        font = QFont()
        font.setPointSize(8)
        self.dial.setFont(font)
        self.dial.setMinimum(1)
        self.dial.setMaximum(20)
        self.dial.setTracking(False)
        self.dial.setWrapping(True)

        self.verticalLayout_3.addWidget(self.dial)

        self.btn_stimulus = QPushButton(self.frame_control)
        self.btn_stimulus.setObjectName(u"btn_stimulus")
        self.btn_stimulus.setFont(font)

        self.verticalLayout_3.addWidget(self.btn_stimulus)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, -1, 6, -1)
        self.label_2 = QLabel(self.frame_control)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.label = QLabel(self.frame_control)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(30, 30))
        self.label.setStyleSheet(u"background-color: rgb(152, 152, 152);")

        self.horizontalLayout.addWidget(self.label)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.btn_up = QPushButton(self.frame_control)
        self.btn_up.setObjectName(u"btn_up")
        self.btn_up.setEnabled(False)
        self.btn_up.setFont(font)

        self.verticalLayout_6.addWidget(self.btn_up)


        self.verticalLayout_4.addLayout(self.verticalLayout_6)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.btn_down = QPushButton(self.frame_control)
        self.btn_down.setObjectName(u"btn_down")
        self.btn_down.setEnabled(False)
        self.btn_down.setFont(font)

        self.verticalLayout_8.addWidget(self.btn_down)


        self.verticalLayout_4.addLayout(self.verticalLayout_8)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.btn_release = QPushButton(self.frame_control)
        self.btn_release.setObjectName(u"btn_release")
        self.btn_release.setEnabled(False)
        self.btn_release.setFont(font)

        self.verticalLayout_7.addWidget(self.btn_release)


        self.verticalLayout_4.addLayout(self.verticalLayout_7)


        self.horizontalLayout_3.addLayout(self.verticalLayout_4)

        self.frame = QFrame(self.frame_control)
        self.frame.setObjectName(u"frame")
        self.frame.setMaximumSize(QSize(150, 16777215))
        self.frame.setFont(font)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_7 = QLabel(self.frame)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMaximumSize(QSize(16777215, 25))
        self.label_7.setFont(font)
        self.label_7.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_7)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(16777215, 25))
        font1 = QFont()
        font1.setPointSize(8)
        font1.setBold(False)
        self.label_3.setFont(font1)
        self.label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.label_3)

        self.btn_side = QPushButton(self.frame)
        self.btn_side.setObjectName(u"btn_side")
        self.btn_side.setMaximumSize(QSize(16777215, 25))
        self.btn_side.setFont(font1)

        self.horizontalLayout_4.addWidget(self.btn_side)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.btn_226 = QPushButton(self.frame)
        self.btn_226.setObjectName(u"btn_226")
        self.btn_226.setMaximumSize(QSize(16777215, 25))
        self.btn_226.setFont(font)

        self.horizontalLayout_7.addWidget(self.btn_226)

        self.btn_1000 = QPushButton(self.frame)
        self.btn_1000.setObjectName(u"btn_1000")
        self.btn_1000.setEnabled(False)
        self.btn_1000.setMaximumSize(QSize(16777215, 25))
        self.btn_1000.setFont(font)

        self.horizontalLayout_7.addWidget(self.btn_1000)


        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(16777215, 25))
        self.label_5.setFont(font)
        self.label_5.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_5)

        self.btn_reflex = QPushButton(self.frame)
        self.btn_reflex.setObjectName(u"btn_reflex")
        self.btn_reflex.setEnabled(False)
        self.btn_reflex.setMaximumSize(QSize(16777215, 25))
        self.btn_reflex.setFont(font)

        self.verticalLayout_2.addWidget(self.btn_reflex)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.btn_toneDecay = QPushButton(self.frame)
        self.btn_toneDecay.setObjectName(u"btn_toneDecay")
        self.btn_toneDecay.setEnabled(False)
        self.btn_toneDecay.setMaximumSize(QSize(16777215, 25))
        self.btn_toneDecay.setFont(font)

        self.horizontalLayout_5.addWidget(self.btn_toneDecay)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btn_print = QPushButton(self.frame)
        self.btn_print.setObjectName(u"btn_print")
        self.btn_print.setEnabled(True)
        self.btn_print.setMaximumSize(QSize(16777215, 25))
        self.btn_print.setFont(font)

        self.horizontalLayout_2.addWidget(self.btn_print)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_3)


        self.horizontalLayout_3.addWidget(self.frame)


        self.verticalLayout.addWidget(self.frame_control)


        self.retranslateUi(Z_control)

        QMetaObject.connectSlotsByName(Z_control)
    # setupUi

    def retranslateUi(self, Z_control):
        Z_control.setWindowTitle(QCoreApplication.translate("Z_control", u"Form", None))
        self.btn_1.setText("")
        self.btn_2.setText("")
        self.btn_3.setText("")
        self.btn_4.setText("")
        self.btn_5.setText("")
        self.btn_6.setText("")
        self.btn_stimulus.setText(QCoreApplication.translate("Z_control", u"stimulus", None))
        self.label_2.setText(QCoreApplication.translate("Z_control", u"Leak", None))
        self.label.setText("")
        self.btn_up.setText(QCoreApplication.translate("Z_control", u"up", None))
        self.btn_down.setText(QCoreApplication.translate("Z_control", u"down", None))
        self.btn_release.setText(QCoreApplication.translate("Z_control", u"Realease", None))
        self.label_7.setText(QCoreApplication.translate("Z_control", u"Control", None))
        self.label_3.setText(QCoreApplication.translate("Z_control", u"Side", None))
        self.btn_side.setText(QCoreApplication.translate("Z_control", u"OD/OI", None))
        self.btn_226.setText(QCoreApplication.translate("Z_control", u"226 Hz", None))
        self.btn_1000.setText(QCoreApplication.translate("Z_control", u"1000 Hz", None))
        self.label_5.setText(QCoreApplication.translate("Z_control", u"Reflex", None))
        self.btn_reflex.setText(QCoreApplication.translate("Z_control", u"IPSI/CONTRA", None))
        self.btn_toneDecay.setText(QCoreApplication.translate("Z_control", u"Tone Decay", None))
        self.btn_print.setText(QCoreApplication.translate("Z_control", u"Print", None))
    # retranslateUi

