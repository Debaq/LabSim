# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Audiometer.ui'
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
from PySide6.QtWidgets import (QApplication, QDial, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_Audiometer(object):
    def setupUi(self, Audiometer):
        if not Audiometer.objectName():
            Audiometer.setObjectName(u"Audiometer")
        Audiometer.resize(740, 504)
        Audiometer.setMinimumSize(QSize(740, 500))
        Audiometer.setMaximumSize(QSize(830, 504))
        self.horizontalLayout_7 = QHBoxLayout(Audiometer)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lateral_layout = QVBoxLayout()
        self.lateral_layout.setObjectName(u"lateral_layout")

        self.horizontalLayout_7.addLayout(self.lateral_layout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.display = QFrame(Audiometer)
        self.display.setObjectName(u"display")
        self.display.setMinimumSize(QSize(0, 120))
        self.display.setMaximumSize(QSize(16777215, 120))
        self.display.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        self.display.setFrameShape(QFrame.Box)
        self.horizontalLayout_2 = QHBoxLayout(self.display)
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.lbl_int_ch0 = QLabel(self.display)
        self.lbl_int_ch0.setObjectName(u"lbl_int_ch0")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.lbl_int_ch0.setFont(font)
        self.lbl_int_ch0.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.lbl_int_ch0)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lbl_trans_ch0 = QLabel(self.display)
        self.lbl_trans_ch0.setObjectName(u"lbl_trans_ch0")
        self.lbl_trans_ch0.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.lbl_trans_ch0)

        self.lbl_step_ch0 = QLabel(self.display)
        self.lbl_step_ch0.setObjectName(u"lbl_step_ch0")
        self.lbl_step_ch0.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.lbl_step_ch0)


        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.lbl_output_ch0 = QLabel(self.display)
        self.lbl_output_ch0.setObjectName(u"lbl_output_ch0")
        self.lbl_output_ch0.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.lbl_output_ch0)

        self.line_18 = QFrame(self.display)
        self.line_18.setObjectName(u"line_18")
        self.line_18.setFrameShape(QFrame.HLine)
        self.line_18.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line_18)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.lbl_stim_ch0 = QLabel(self.display)
        self.lbl_stim_ch0.setObjectName(u"lbl_stim_ch0")
        font1 = QFont()
        font1.setPointSize(8)
        self.lbl_stim_ch0.setFont(font1)
        self.lbl_stim_ch0.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_17.addWidget(self.lbl_stim_ch0)

        self.line_13 = QFrame(self.display)
        self.line_13.setObjectName(u"line_13")
        self.line_13.setFrameShape(QFrame.VLine)
        self.line_13.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_17.addWidget(self.line_13)

        self.lbl_contin_ch0 = QLabel(self.display)
        self.lbl_contin_ch0.setObjectName(u"lbl_contin_ch0")
        self.lbl_contin_ch0.setFont(font1)
        self.lbl_contin_ch0.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_17.addWidget(self.lbl_contin_ch0)

        self.line_14 = QFrame(self.display)
        self.line_14.setObjectName(u"line_14")
        self.line_14.setFrameShape(QFrame.VLine)
        self.line_14.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_17.addWidget(self.line_14)

        self.lbl_rev_ch0 = QLabel(self.display)
        self.lbl_rev_ch0.setObjectName(u"lbl_rev_ch0")
        self.lbl_rev_ch0.setFont(font1)
        self.lbl_rev_ch0.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_17.addWidget(self.lbl_rev_ch0)


        self.verticalLayout_4.addLayout(self.horizontalLayout_17)

        self.line_17 = QFrame(self.display)
        self.line_17.setObjectName(u"line_17")
        self.line_17.setFrameShape(QFrame.HLine)
        self.line_17.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line_17)

        self.lbl_warning_stim_der = QLabel(self.display)
        self.lbl_warning_stim_der.setObjectName(u"lbl_warning_stim_der")
        self.lbl_warning_stim_der.setAutoFillBackground(False)

        self.verticalLayout_4.addWidget(self.lbl_warning_stim_der)


        self.horizontalLayout_2.addLayout(self.verticalLayout_4)

        self.line_24 = QFrame(self.display)
        self.line_24.setObjectName(u"line_24")
        self.line_24.setFrameShape(QFrame.VLine)
        self.line_24.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line_24)

        self.horizontalFrame_2 = QFrame(self.display)
        self.horizontalFrame_2.setObjectName(u"horizontalFrame_2")
        self.horizontalFrame_2.setMinimumSize(QSize(18, 0))
        self.horizontalFrame_2.setMaximumSize(QSize(18, 16777215))
        self.horizontalLayout_20 = QHBoxLayout(self.horizontalFrame_2)
        self.horizontalLayout_20.setSpacing(0)
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalLayout_20.setContentsMargins(0, 0, 0, 0)
        self.vmeter_der = QProgressBar(self.horizontalFrame_2)
        self.vmeter_der.setObjectName(u"vmeter_der")
        self.vmeter_der.setMinimumSize(QSize(7, 0))
        self.vmeter_der.setMaximumSize(QSize(7, 16777215))
        self.vmeter_der.setFont(font1)
        self.vmeter_der.setStyleSheet(u"QProgressBar::chunk {\n"
"                background-color: #55ff7f;\n"
"            }")
        self.vmeter_der.setValue(0)
        self.vmeter_der.setAlignment(Qt.AlignCenter)
        self.vmeter_der.setOrientation(Qt.Vertical)

        self.horizontalLayout_20.addWidget(self.vmeter_der)

        self.verticalFrame = QFrame(self.horizontalFrame_2)
        self.verticalFrame.setObjectName(u"verticalFrame")
        self.verticalFrame.setMinimumSize(QSize(7, 0))
        self.verticalFrame.setMaximumSize(QSize(7, 16777215))
        self.verticalLayout_22 = QVBoxLayout(self.verticalFrame)
        self.verticalLayout_22.setSpacing(0)
        self.verticalLayout_22.setObjectName(u"verticalLayout_22")
        self.verticalLayout_22.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_22.setContentsMargins(0, 0, 0, 0)
        self.line_22 = QFrame(self.verticalFrame)
        self.line_22.setObjectName(u"line_22")
        self.line_22.setMinimumSize(QSize(5, 0))
        self.line_22.setMaximumSize(QSize(5, 16777215))
        self.line_22.setFrameShape(QFrame.HLine)
        self.line_22.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_22.addWidget(self.line_22)

        self.line_21 = QFrame(self.verticalFrame)
        self.line_21.setObjectName(u"line_21")
        self.line_21.setMinimumSize(QSize(5, 0))
        self.line_21.setMaximumSize(QSize(5, 16777215))
        self.line_21.setFrameShape(QFrame.HLine)
        self.line_21.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_22.addWidget(self.line_21)

        self.line_23 = QFrame(self.verticalFrame)
        self.line_23.setObjectName(u"line_23")
        self.line_23.setMinimumSize(QSize(5, 0))
        self.line_23.setMaximumSize(QSize(5, 16777215))
        self.line_23.setFrameShape(QFrame.HLine)
        self.line_23.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_22.addWidget(self.line_23)


        self.horizontalLayout_20.addWidget(self.verticalFrame)


        self.horizontalLayout_2.addWidget(self.horizontalFrame_2)

        self.line_6 = QFrame(self.display)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line_6)

        self.central = QFrame(self.display)
        self.central.setObjectName(u"central")
        self.central.setMinimumSize(QSize(270, 0))
        self.central.setMaximumSize(QSize(270, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.central)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.lbl_freq = QLabel(self.central)
        self.lbl_freq.setObjectName(u"lbl_freq")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_freq.sizePolicy().hasHeightForWidth())
        self.lbl_freq.setSizePolicy(sizePolicy)
        self.lbl_freq.setMinimumSize(QSize(0, 60))
        self.lbl_freq.setMaximumSize(QSize(16777215, 60))
        font2 = QFont()
        font2.setPointSize(20)
        font2.setBold(True)
        self.lbl_freq.setFont(font2)
        self.lbl_freq.setScaledContents(False)
        self.lbl_freq.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lbl_freq)

        self.lbl_prueba = QLabel(self.central)
        self.lbl_prueba.setObjectName(u"lbl_prueba")
        self.lbl_prueba.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lbl_prueba)

        self.lbl_time = QLabel(self.central)
        self.lbl_time.setObjectName(u"lbl_time")
        self.lbl_time.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lbl_time)

        self.lbl_response = QLabel(self.central)
        self.lbl_response.setObjectName(u"lbl_response")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbl_response.sizePolicy().hasHeightForWidth())
        self.lbl_response.setSizePolicy(sizePolicy1)
        font3 = QFont()
        font3.setPointSize(8)
        font3.setBold(True)
        self.lbl_response.setFont(font3)

        self.verticalLayout_3.addWidget(self.lbl_response)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setSpacing(0)
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.horizontalLayout_21.setContentsMargins(-1, 0, -1, -1)
        self.lbl_ext_der = QLabel(self.central)
        self.lbl_ext_der.setObjectName(u"lbl_ext_der")
        self.lbl_ext_der.setMinimumSize(QSize(90, 0))
        self.lbl_ext_der.setMaximumSize(QSize(90, 15))
        font4 = QFont()
        font4.setPointSize(9)
        self.lbl_ext_der.setFont(font4)

        self.horizontalLayout_21.addWidget(self.lbl_ext_der)

        self.lbl_warning_stim_cent = QLabel(self.central)
        self.lbl_warning_stim_cent.setObjectName(u"lbl_warning_stim_cent")
        self.lbl_warning_stim_cent.setMinimumSize(QSize(90, 0))
        self.lbl_warning_stim_cent.setMaximumSize(QSize(90, 15))
        self.lbl_warning_stim_cent.setFont(font4)

        self.horizontalLayout_21.addWidget(self.lbl_warning_stim_cent)

        self.lbl_ext_izq = QLabel(self.central)
        self.lbl_ext_izq.setObjectName(u"lbl_ext_izq")
        self.lbl_ext_izq.setMinimumSize(QSize(90, 0))
        self.lbl_ext_izq.setMaximumSize(QSize(90, 15))
        self.lbl_ext_izq.setFont(font4)
        self.lbl_ext_izq.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_21.addWidget(self.lbl_ext_izq)


        self.verticalLayout_3.addLayout(self.horizontalLayout_21)


        self.horizontalLayout_2.addWidget(self.central)

        self.line_7 = QFrame(self.display)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.VLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line_7)

        self.horizontalFrame = QFrame(self.display)
        self.horizontalFrame.setObjectName(u"horizontalFrame")
        self.horizontalFrame.setMinimumSize(QSize(18, 0))
        self.horizontalFrame.setMaximumSize(QSize(18, 16777215))
        self.horizontalLayout_19 = QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout_19.setSpacing(0)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.verticalFrame1 = QFrame(self.horizontalFrame)
        self.verticalFrame1.setObjectName(u"verticalFrame1")
        self.verticalFrame1.setMinimumSize(QSize(7, 0))
        self.verticalFrame1.setMaximumSize(QSize(7, 16777215))
        self.verticalLayout_23 = QVBoxLayout(self.verticalFrame1)
        self.verticalLayout_23.setSpacing(0)
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.verticalLayout_23.setContentsMargins(0, 0, 0, 0)
        self.line_25 = QFrame(self.verticalFrame1)
        self.line_25.setObjectName(u"line_25")
        self.line_25.setFrameShape(QFrame.HLine)
        self.line_25.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_23.addWidget(self.line_25)

        self.line_27 = QFrame(self.verticalFrame1)
        self.line_27.setObjectName(u"line_27")
        self.line_27.setFrameShape(QFrame.HLine)
        self.line_27.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_23.addWidget(self.line_27)

        self.line_26 = QFrame(self.verticalFrame1)
        self.line_26.setObjectName(u"line_26")
        self.line_26.setFrameShape(QFrame.HLine)
        self.line_26.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_23.addWidget(self.line_26)


        self.horizontalLayout_19.addWidget(self.verticalFrame1)

        self.vmeter_izq = QProgressBar(self.horizontalFrame)
        self.vmeter_izq.setObjectName(u"vmeter_izq")
        self.vmeter_izq.setMinimumSize(QSize(7, 0))
        self.vmeter_izq.setMaximumSize(QSize(7, 16777215))
        self.vmeter_izq.setStyleSheet(u"QProgressBar::chunk {\n"
"                background-color: #55ff7f;\n"
"            }")
        self.vmeter_izq.setValue(0)
        self.vmeter_izq.setOrientation(Qt.Vertical)

        self.horizontalLayout_19.addWidget(self.vmeter_izq)


        self.horizontalLayout_2.addWidget(self.horizontalFrame)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lbl_int_ch1 = QLabel(self.display)
        self.lbl_int_ch1.setObjectName(u"lbl_int_ch1")
        self.lbl_int_ch1.setFont(font)
        self.lbl_int_ch1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.lbl_int_ch1)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.lbl_trans_ch1 = QLabel(self.display)
        self.lbl_trans_ch1.setObjectName(u"lbl_trans_ch1")
        self.lbl_trans_ch1.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_12.addWidget(self.lbl_trans_ch1)

        self.lbl_step_ch1 = QLabel(self.display)
        self.lbl_step_ch1.setObjectName(u"lbl_step_ch1")
        self.lbl_step_ch1.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_12.addWidget(self.lbl_step_ch1)


        self.verticalLayout_2.addLayout(self.horizontalLayout_12)

        self.lbl_output_ch1 = QLabel(self.display)
        self.lbl_output_ch1.setObjectName(u"lbl_output_ch1")
        self.lbl_output_ch1.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.lbl_output_ch1)

        self.line_20 = QFrame(self.display)
        self.line_20.setObjectName(u"line_20")
        self.line_20.setFrameShape(QFrame.HLine)
        self.line_20.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_20)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.lbl_stim_ch1 = QLabel(self.display)
        self.lbl_stim_ch1.setObjectName(u"lbl_stim_ch1")
        self.lbl_stim_ch1.setFont(font1)
        self.lbl_stim_ch1.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_18.addWidget(self.lbl_stim_ch1)

        self.line_15 = QFrame(self.display)
        self.line_15.setObjectName(u"line_15")
        self.line_15.setFrameShape(QFrame.VLine)
        self.line_15.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_18.addWidget(self.line_15)

        self.lbl_contin_ch1 = QLabel(self.display)
        self.lbl_contin_ch1.setObjectName(u"lbl_contin_ch1")
        self.lbl_contin_ch1.setFont(font1)
        self.lbl_contin_ch1.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_18.addWidget(self.lbl_contin_ch1)

        self.line_16 = QFrame(self.display)
        self.line_16.setObjectName(u"line_16")
        self.line_16.setFrameShape(QFrame.VLine)
        self.line_16.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_18.addWidget(self.line_16)

        self.lbl_rev_ch1 = QLabel(self.display)
        self.lbl_rev_ch1.setObjectName(u"lbl_rev_ch1")
        self.lbl_rev_ch1.setFont(font1)
        self.lbl_rev_ch1.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_18.addWidget(self.lbl_rev_ch1)


        self.verticalLayout_2.addLayout(self.horizontalLayout_18)

        self.line_19 = QFrame(self.display)
        self.line_19.setObjectName(u"line_19")
        self.line_19.setFrameShape(QFrame.HLine)
        self.line_19.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_19)

        self.lbl_warning_stim_izq = QLabel(self.display)
        self.lbl_warning_stim_izq.setObjectName(u"lbl_warning_stim_izq")

        self.verticalLayout_2.addWidget(self.lbl_warning_stim_izq)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)


        self.verticalLayout.addWidget(self.display)

        self.line = QFrame(Audiometer)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.control = QVBoxLayout()
        self.control.setSpacing(4)
        self.control.setObjectName(u"control")
        self.control_btn_up = QHBoxLayout()
        self.control_btn_up.setSpacing(10)
        self.control_btn_up.setObjectName(u"control_btn_up")
        self.verticalLayout_21 = QVBoxLayout()
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setContentsMargins(0, -1, -1, -1)
        self.label_3 = QLabel(Audiometer)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font1)
        self.label_3.setAlignment(Qt.AlignCenter)

        self.verticalLayout_21.addWidget(self.label_3)

        self.dial_monitor_ch1 = QDial(Audiometer)
        self.dial_monitor_ch1.setObjectName(u"dial_monitor_ch1")
        self.dial_monitor_ch1.setMinimumSize(QSize(45, 45))
        self.dial_monitor_ch1.setMaximumSize(QSize(45, 45))
        self.dial_monitor_ch1.setMaximum(20)
        self.dial_monitor_ch1.setValue(2)
        self.dial_monitor_ch1.setOrientation(Qt.Horizontal)
        self.dial_monitor_ch1.setInvertedAppearance(False)
        self.dial_monitor_ch1.setInvertedControls(False)
        self.dial_monitor_ch1.setWrapping(False)
        self.dial_monitor_ch1.setNotchesVisible(True)

        self.verticalLayout_21.addWidget(self.dial_monitor_ch1)

        self.label_4 = QLabel(Audiometer)
        self.label_4.setObjectName(u"label_4")
        font5 = QFont()
        font5.setPointSize(7)
        self.label_4.setFont(font5)
        self.label_4.setAlignment(Qt.AlignCenter)

        self.verticalLayout_21.addWidget(self.label_4)

        self.dial_monitor_ch2 = QDial(Audiometer)
        self.dial_monitor_ch2.setObjectName(u"dial_monitor_ch2")
        self.dial_monitor_ch2.setMinimumSize(QSize(45, 45))
        self.dial_monitor_ch2.setMaximumSize(QSize(45, 45))
        self.dial_monitor_ch2.setMaximum(20)
        self.dial_monitor_ch2.setValue(2)
        self.dial_monitor_ch2.setNotchesVisible(True)

        self.verticalLayout_21.addWidget(self.dial_monitor_ch2)

        self.label_5 = QLabel(Audiometer)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font5)
        self.label_5.setAlignment(Qt.AlignCenter)

        self.verticalLayout_21.addWidget(self.label_5)

        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_21.addItem(self.verticalSpacer_9)


        self.control_btn_up.addLayout(self.verticalLayout_21)

        self.line_12 = QFrame(Audiometer)
        self.line_12.setObjectName(u"line_12")
        self.line_12.setFrameShape(QFrame.VLine)
        self.line_12.setFrameShadow(QFrame.Sunken)

        self.control_btn_up.addWidget(self.line_12)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setSpacing(4)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, -1, -1, -1)
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.label_15 = QLabel(Audiometer)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setFont(font4)
        self.label_15.setAlignment(Qt.AlignCenter)

        self.verticalLayout_11.addWidget(self.label_15)

        self.btn_output_der_der = QPushButton(Audiometer)
        self.btn_output_der_der.setObjectName(u"btn_output_der_der")
        self.btn_output_der_der.setMaximumSize(QSize(16777215, 25))
        self.btn_output_der_der.setFont(font4)
        self.btn_output_der_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_11.addWidget(self.btn_output_der_der)

        self.btn_output_izq_der = QPushButton(Audiometer)
        self.btn_output_izq_der.setObjectName(u"btn_output_izq_der")
        self.btn_output_izq_der.setMaximumSize(QSize(16777215, 25))
        self.btn_output_izq_der.setFont(font4)
        self.btn_output_izq_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_11.addWidget(self.btn_output_izq_der)

        self.btn_output_sim_der = QPushButton(Audiometer)
        self.btn_output_sim_der.setObjectName(u"btn_output_sim_der")
        self.btn_output_sim_der.setMaximumSize(QSize(16777215, 25))
        self.btn_output_sim_der.setFont(font4)
        self.btn_output_sim_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_11.addWidget(self.btn_output_sim_der)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer)


        self.horizontalLayout_9.addLayout(self.verticalLayout_11)

        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(-1, -1, -1, 0)
        self.label_11 = QLabel(Audiometer)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font4)
        self.label_11.setAlignment(Qt.AlignCenter)

        self.verticalLayout_12.addWidget(self.label_11)

        self.btn_stim_tone_der = QPushButton(Audiometer)
        self.btn_stim_tone_der.setObjectName(u"btn_stim_tone_der")
        self.btn_stim_tone_der.setMaximumSize(QSize(16777215, 25))
        self.btn_stim_tone_der.setFont(font4)
        self.btn_stim_tone_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_12.addWidget(self.btn_stim_tone_der)

        self.btn_stim_fm_der = QPushButton(Audiometer)
        self.btn_stim_fm_der.setObjectName(u"btn_stim_fm_der")
        self.btn_stim_fm_der.setMaximumSize(QSize(16777215, 25))
        self.btn_stim_fm_der.setFont(font4)
        self.btn_stim_fm_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_12.addWidget(self.btn_stim_fm_der)

        self.btn_stim_speech_der = QPushButton(Audiometer)
        self.btn_stim_speech_der.setObjectName(u"btn_stim_speech_der")
        self.btn_stim_speech_der.setMaximumSize(QSize(16777215, 25))
        self.btn_stim_speech_der.setFont(font4)
        self.btn_stim_speech_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_12.addWidget(self.btn_stim_speech_der)

        self.verticalLayout_19 = QVBoxLayout()
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(0, 0, -1, -1)
        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setSpacing(0)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(-1, 0, -1, -1)
        self.btn_stim_wn_der = QPushButton(Audiometer)
        self.btn_stim_wn_der.setObjectName(u"btn_stim_wn_der")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.btn_stim_wn_der.sizePolicy().hasHeightForWidth())
        self.btn_stim_wn_der.setSizePolicy(sizePolicy2)
        self.btn_stim_wn_der.setMaximumSize(QSize(35, 25))
        self.btn_stim_wn_der.setFont(font1)
        self.btn_stim_wn_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_15.addWidget(self.btn_stim_wn_der)

        self.btn_stim_nbn_der = QPushButton(Audiometer)
        self.btn_stim_nbn_der.setObjectName(u"btn_stim_nbn_der")
        sizePolicy2.setHeightForWidth(self.btn_stim_nbn_der.sizePolicy().hasHeightForWidth())
        self.btn_stim_nbn_der.setSizePolicy(sizePolicy2)
        self.btn_stim_nbn_der.setMaximumSize(QSize(35, 25))
        self.btn_stim_nbn_der.setFont(font1)
        self.btn_stim_nbn_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_15.addWidget(self.btn_stim_nbn_der)


        self.verticalLayout_19.addLayout(self.horizontalLayout_15)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.btn_stim_pn_der = QPushButton(Audiometer)
        self.btn_stim_pn_der.setObjectName(u"btn_stim_pn_der")
        self.btn_stim_pn_der.setMaximumSize(QSize(35, 25))
        self.btn_stim_pn_der.setFont(font1)
        self.btn_stim_pn_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_3.addWidget(self.btn_stim_pn_der)

        self.btn_stim_sn_der = QPushButton(Audiometer)
        self.btn_stim_sn_der.setObjectName(u"btn_stim_sn_der")
        sizePolicy2.setHeightForWidth(self.btn_stim_sn_der.sizePolicy().hasHeightForWidth())
        self.btn_stim_sn_der.setSizePolicy(sizePolicy2)
        self.btn_stim_sn_der.setMaximumSize(QSize(35, 25))
        self.btn_stim_sn_der.setFont(font1)
        self.btn_stim_sn_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_3.addWidget(self.btn_stim_sn_der)


        self.verticalLayout_19.addLayout(self.horizontalLayout_3)


        self.verticalLayout_12.addLayout(self.verticalLayout_19)

        self.verticalSpacer_6 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_12.addItem(self.verticalSpacer_6)


        self.horizontalLayout_9.addLayout(self.verticalLayout_12)

        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.label_10 = QLabel(Audiometer)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font4)
        self.label_10.setAlignment(Qt.AlignCenter)

        self.verticalLayout_14.addWidget(self.label_10)

        self.btn_trans_aer_der = QPushButton(Audiometer)
        self.btn_trans_aer_der.setObjectName(u"btn_trans_aer_der")
        self.btn_trans_aer_der.setMaximumSize(QSize(16777215, 25))
        self.btn_trans_aer_der.setFont(font4)
        self.btn_trans_aer_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_14.addWidget(self.btn_trans_aer_der)

        self.btn_trans_ose_der = QPushButton(Audiometer)
        self.btn_trans_ose_der.setObjectName(u"btn_trans_ose_der")
        self.btn_trans_ose_der.setMaximumSize(QSize(16777215, 25))
        self.btn_trans_ose_der.setFont(font4)
        self.btn_trans_ose_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_14.addWidget(self.btn_trans_ose_der)

        self.btn_trans_cl_der = QPushButton(Audiometer)
        self.btn_trans_cl_der.setObjectName(u"btn_trans_cl_der")
        self.btn_trans_cl_der.setMaximumSize(QSize(16777215, 25))
        self.btn_trans_cl_der.setFont(font4)
        self.btn_trans_cl_der.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_14.addWidget(self.btn_trans_cl_der)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_14.addItem(self.verticalSpacer_2)


        self.horizontalLayout_9.addLayout(self.verticalLayout_14)


        self.control_btn_up.addLayout(self.horizontalLayout_9)

        self.line_8 = QFrame(Audiometer)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.VLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.control_btn_up.addWidget(self.line_8)

        self.verticalFrame2 = QFrame(Audiometer)
        self.verticalFrame2.setObjectName(u"verticalFrame2")
        self.verticalFrame2.setMaximumSize(QSize(90, 16777215))
        self.verticalLayout_5 = QVBoxLayout(self.verticalFrame2)
        self.verticalLayout_5.setSpacing(5)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_5)

        self.btn_alt_frec = QPushButton(self.verticalFrame2)
        self.btn_alt_frec.setObjectName(u"btn_alt_frec")
        self.btn_alt_frec.setMaximumSize(QSize(85, 25))
        self.btn_alt_frec.setFont(font4)
        self.btn_alt_frec.setCheckable(False)

        self.verticalLayout_5.addWidget(self.btn_alt_frec)

        self.line_10 = QFrame(self.verticalFrame2)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setFrameShape(QFrame.HLine)
        self.line_10.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_5.addWidget(self.line_10)

        self.groupBox_step = QGroupBox(self.verticalFrame2)
        self.groupBox_step.setObjectName(u"groupBox_step")
        self.groupBox_step.setFont(font1)
        self.groupBox_step.setAlignment(Qt.AlignCenter)
        self.groupBox_step.setCheckable(False)
        self.horizontalLayout_13 = QHBoxLayout(self.groupBox_step)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(1, 0, 1, 0)
        self.btn_step_1 = QPushButton(self.groupBox_step)
        self.btn_step_1.setObjectName(u"btn_step_1")
        self.btn_step_1.setMaximumSize(QSize(16777215, 25))
        self.btn_step_1.setFont(font1)
        self.btn_step_1.setCheckable(False)
        self.btn_step_1.setAutoExclusive(True)

        self.horizontalLayout_13.addWidget(self.btn_step_1)

        self.btn_step_3 = QPushButton(self.groupBox_step)
        self.btn_step_3.setObjectName(u"btn_step_3")
        self.btn_step_3.setMaximumSize(QSize(16777215, 25))
        self.btn_step_3.setFont(font1)
        self.btn_step_3.setCheckable(False)
        self.btn_step_3.setAutoExclusive(True)

        self.horizontalLayout_13.addWidget(self.btn_step_3)

        self.btn_step_5 = QPushButton(self.groupBox_step)
        self.btn_step_5.setObjectName(u"btn_step_5")
        self.btn_step_5.setMaximumSize(QSize(16777215, 25))
        self.btn_step_5.setFont(font1)
        self.btn_step_5.setCheckable(False)
        self.btn_step_5.setChecked(False)
        self.btn_step_5.setAutoExclusive(True)
        self.btn_step_5.setFlat(False)

        self.horizontalLayout_13.addWidget(self.btn_step_5)


        self.verticalLayout_5.addWidget(self.groupBox_step)

        self.line_9 = QFrame(self.verticalFrame2)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setFrameShape(QFrame.HLine)
        self.line_9.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_5.addWidget(self.line_9)

        self.btn_ext_range = QPushButton(self.verticalFrame2)
        self.btn_ext_range.setObjectName(u"btn_ext_range")
        self.btn_ext_range.setMaximumSize(QSize(85, 25))
        self.btn_ext_range.setFont(font4)
        self.btn_ext_range.setCheckable(False)

        self.verticalLayout_5.addWidget(self.btn_ext_range)


        self.control_btn_up.addWidget(self.verticalFrame2)

        self.line_2 = QFrame(Audiometer)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.control_btn_up.addWidget(self.line_2)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setSpacing(4)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.label_12 = QLabel(Audiometer)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font4)
        self.label_12.setAlignment(Qt.AlignCenter)

        self.verticalLayout_17.addWidget(self.label_12)

        self.btn_trans_aer_izq = QPushButton(Audiometer)
        self.btn_trans_aer_izq.setObjectName(u"btn_trans_aer_izq")
        self.btn_trans_aer_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_trans_aer_izq.setFont(font4)
        self.btn_trans_aer_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_17.addWidget(self.btn_trans_aer_izq)

        self.btn_trans_ose_izq = QPushButton(Audiometer)
        self.btn_trans_ose_izq.setObjectName(u"btn_trans_ose_izq")
        self.btn_trans_ose_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_trans_ose_izq.setFont(font4)
        self.btn_trans_ose_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_17.addWidget(self.btn_trans_ose_izq)

        self.btn_trans_cl_izq = QPushButton(Audiometer)
        self.btn_trans_cl_izq.setObjectName(u"btn_trans_cl_izq")
        self.btn_trans_cl_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_trans_cl_izq.setFont(font4)
        self.btn_trans_cl_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_17.addWidget(self.btn_trans_cl_izq)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_17.addItem(self.verticalSpacer_3)


        self.horizontalLayout_8.addLayout(self.verticalLayout_17)

        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(-1, -1, -1, 0)
        self.label_13 = QLabel(Audiometer)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font4)
        self.label_13.setAlignment(Qt.AlignCenter)

        self.verticalLayout_16.addWidget(self.label_13)

        self.btn_stim_tone_izq = QPushButton(Audiometer)
        self.btn_stim_tone_izq.setObjectName(u"btn_stim_tone_izq")
        self.btn_stim_tone_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_stim_tone_izq.setFont(font4)
        self.btn_stim_tone_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_16.addWidget(self.btn_stim_tone_izq)

        self.btn_stim_fm_izq = QPushButton(Audiometer)
        self.btn_stim_fm_izq.setObjectName(u"btn_stim_fm_izq")
        self.btn_stim_fm_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_stim_fm_izq.setFont(font4)
        self.btn_stim_fm_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_16.addWidget(self.btn_stim_fm_izq)

        self.btn_stim_speech_izq = QPushButton(Audiometer)
        self.btn_stim_speech_izq.setObjectName(u"btn_stim_speech_izq")
        self.btn_stim_speech_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_stim_speech_izq.setFont(font4)
        self.btn_stim_speech_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_16.addWidget(self.btn_stim_speech_izq)

        self.verticalLayout_18 = QVBoxLayout()
        self.verticalLayout_18.setSpacing(0)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_18.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setSpacing(0)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(-1, 0, -1, -1)
        self.btn_stim_wn_izq = QPushButton(Audiometer)
        self.btn_stim_wn_izq.setObjectName(u"btn_stim_wn_izq")
        sizePolicy2.setHeightForWidth(self.btn_stim_wn_izq.sizePolicy().hasHeightForWidth())
        self.btn_stim_wn_izq.setSizePolicy(sizePolicy2)
        self.btn_stim_wn_izq.setMaximumSize(QSize(35, 25))
        font6 = QFont()
        font6.setPointSize(8)
        font6.setBold(False)
        self.btn_stim_wn_izq.setFont(font6)
        self.btn_stim_wn_izq.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_stim_wn_izq.setAutoExclusive(False)

        self.horizontalLayout_14.addWidget(self.btn_stim_wn_izq)

        self.btn_stim_nbn_izq = QPushButton(Audiometer)
        self.btn_stim_nbn_izq.setObjectName(u"btn_stim_nbn_izq")
        self.btn_stim_nbn_izq.setMaximumSize(QSize(35, 25))
        self.btn_stim_nbn_izq.setFont(font6)
        self.btn_stim_nbn_izq.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_stim_nbn_izq.setCheckable(False)
        self.btn_stim_nbn_izq.setAutoExclusive(False)

        self.horizontalLayout_14.addWidget(self.btn_stim_nbn_izq)


        self.verticalLayout_18.addLayout(self.horizontalLayout_14)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setSpacing(0)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.btn_stim_pn_izq = QPushButton(Audiometer)
        self.btn_stim_pn_izq.setObjectName(u"btn_stim_pn_izq")
        self.btn_stim_pn_izq.setMaximumSize(QSize(35, 25))
        self.btn_stim_pn_izq.setFont(font1)
        self.btn_stim_pn_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_11.addWidget(self.btn_stim_pn_izq)

        self.btn_stim_sn_izq = QPushButton(Audiometer)
        self.btn_stim_sn_izq.setObjectName(u"btn_stim_sn_izq")
        sizePolicy2.setHeightForWidth(self.btn_stim_sn_izq.sizePolicy().hasHeightForWidth())
        self.btn_stim_sn_izq.setSizePolicy(sizePolicy2)
        self.btn_stim_sn_izq.setMaximumSize(QSize(35, 25))
        self.btn_stim_sn_izq.setFont(font6)
        self.btn_stim_sn_izq.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_stim_sn_izq.setAutoExclusive(False)

        self.horizontalLayout_11.addWidget(self.btn_stim_sn_izq)


        self.verticalLayout_18.addLayout(self.horizontalLayout_11)


        self.verticalLayout_16.addLayout(self.verticalLayout_18)

        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_16.addItem(self.verticalSpacer_7)


        self.horizontalLayout_8.addLayout(self.verticalLayout_16)

        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.label_14 = QLabel(Audiometer)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font4)
        self.label_14.setAlignment(Qt.AlignCenter)

        self.verticalLayout_15.addWidget(self.label_14)

        self.btn_output_der_izq = QPushButton(Audiometer)
        self.btn_output_der_izq.setObjectName(u"btn_output_der_izq")
        self.btn_output_der_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_output_der_izq.setFont(font4)
        self.btn_output_der_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_15.addWidget(self.btn_output_der_izq)

        self.btn_output_izq_izq = QPushButton(Audiometer)
        self.btn_output_izq_izq.setObjectName(u"btn_output_izq_izq")
        self.btn_output_izq_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_output_izq_izq.setFont(font4)
        self.btn_output_izq_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_15.addWidget(self.btn_output_izq_izq)

        self.btn_output_sim_izq = QPushButton(Audiometer)
        self.btn_output_sim_izq.setObjectName(u"btn_output_sim_izq")
        self.btn_output_sim_izq.setMaximumSize(QSize(16777215, 25))
        self.btn_output_sim_izq.setFont(font4)
        self.btn_output_sim_izq.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_15.addWidget(self.btn_output_sim_izq)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_15.addItem(self.verticalSpacer_4)


        self.horizontalLayout_8.addLayout(self.verticalLayout_15)


        self.control_btn_up.addLayout(self.horizontalLayout_8)

        self.line_11 = QFrame(Audiometer)
        self.line_11.setObjectName(u"line_11")
        self.line_11.setFrameShape(QFrame.VLine)
        self.line_11.setFrameShadow(QFrame.Sunken)

        self.control_btn_up.addWidget(self.line_11)

        self.verticalLayout_20 = QVBoxLayout()
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.label = QLabel(Audiometer)
        self.label.setObjectName(u"label")
        self.label.setFont(font1)

        self.verticalLayout_20.addWidget(self.label)

        self.dial_talkback = QDial(Audiometer)
        self.dial_talkback.setObjectName(u"dial_talkback")
        self.dial_talkback.setMinimumSize(QSize(45, 45))
        self.dial_talkback.setMaximumSize(QSize(45, 45))
        self.dial_talkback.setMaximum(100)
        self.dial_talkback.setValue(5)
        self.dial_talkback.setNotchesVisible(True)

        self.verticalLayout_20.addWidget(self.dial_talkback)

        self.verticalSpacer_8 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_20.addItem(self.verticalSpacer_8)


        self.control_btn_up.addLayout(self.verticalLayout_20)


        self.control.addLayout(self.control_btn_up)

        self.line_5 = QFrame(Audiometer)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.HLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.control.addWidget(self.line_5)

        self.control_dial_down = QHBoxLayout()
        self.control_dial_down.setSpacing(4)
        self.control_dial_down.setObjectName(u"control_dial_down")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.dial_der = QDial(Audiometer)
        self.dial_der.setObjectName(u"dial_der")
        self.dial_der.setCursor(QCursor(Qt.OpenHandCursor))
        self.dial_der.setLayoutDirection(Qt.LeftToRight)
        self.dial_der.setAutoFillBackground(False)
        self.dial_der.setStyleSheet(u"")
        self.dial_der.setMinimum(1)
        self.dial_der.setMaximum(20)
        self.dial_der.setSingleStep(1)
        self.dial_der.setPageStep(1)
        self.dial_der.setValue(10)
        self.dial_der.setInvertedAppearance(False)
        self.dial_der.setWrapping(True)
        self.dial_der.setNotchTarget(3.700000000000000)
        self.dial_der.setNotchesVisible(False)

        self.verticalLayout_7.addWidget(self.dial_der)


        self.horizontalLayout_5.addLayout(self.verticalLayout_7)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.btn_puls_der = QPushButton(Audiometer)
        self.btn_puls_der.setObjectName(u"btn_puls_der")
        self.btn_puls_der.setFont(font4)

        self.verticalLayout_8.addWidget(self.btn_puls_der)

        self.btn_rever_ch0 = QPushButton(Audiometer)
        self.btn_rever_ch0.setObjectName(u"btn_rever_ch0")
        self.btn_rever_ch0.setFont(font4)
        self.btn_rever_ch0.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_rever_ch0.setCheckable(False)
        self.btn_rever_ch0.setChecked(False)

        self.verticalLayout_8.addWidget(self.btn_rever_ch0)

        self.verticalSpacer_10 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_10)

        self.btn_stim_ch0 = QPushButton(Audiometer)
        self.btn_stim_ch0.setObjectName(u"btn_stim_ch0")
        self.btn_stim_ch0.setFont(font4)
        self.btn_stim_ch0.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_stim_ch0.setAutoRepeat(False)
        self.btn_stim_ch0.setAutoExclusive(False)
        self.btn_stim_ch0.setAutoDefault(False)
        self.btn_stim_ch0.setFlat(False)

        self.verticalLayout_8.addWidget(self.btn_stim_ch0)

        self.verticalSpacer_11 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_11)


        self.horizontalLayout_5.addLayout(self.verticalLayout_8)


        self.control_dial_down.addLayout(self.horizontalLayout_5)

        self.line_3 = QFrame(Audiometer)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.VLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.control_dial_down.addWidget(self.line_3)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.btn_time_start = QPushButton(Audiometer)
        self.btn_time_start.setObjectName(u"btn_time_start")
        self.btn_time_start.setFont(font4)
        self.btn_time_start.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_10.addWidget(self.btn_time_start)

        self.btn_time_stop = QPushButton(Audiometer)
        self.btn_time_stop.setObjectName(u"btn_time_stop")
        self.btn_time_stop.setFont(font4)
        self.btn_time_stop.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_10.addWidget(self.btn_time_stop)

        self.btn_time_clear = QPushButton(Audiometer)
        self.btn_time_clear.setObjectName(u"btn_time_clear")
        self.btn_time_clear.setFont(font4)
        self.btn_time_clear.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_10.addWidget(self.btn_time_clear)


        self.verticalLayout_6.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalLayout_16.setContentsMargins(-1, 0, -1, -1)
        self.btn_correcta = QPushButton(Audiometer)
        self.btn_correcta.setObjectName(u"btn_correcta")
        self.btn_correcta.setFont(font4)
        self.btn_correcta.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_16.addWidget(self.btn_correcta)

        self.btn_borrar = QPushButton(Audiometer)
        self.btn_borrar.setObjectName(u"btn_borrar")
        self.btn_borrar.setFont(font4)
        self.btn_borrar.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_16.addWidget(self.btn_borrar)

        self.btn_incorrecta = QPushButton(Audiometer)
        self.btn_incorrecta.setObjectName(u"btn_incorrecta")
        self.btn_incorrecta.setFont(font4)
        self.btn_incorrecta.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_16.addWidget(self.btn_incorrecta)


        self.verticalLayout_6.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.btn_talkback = QPushButton(Audiometer)
        self.btn_talkback.setObjectName(u"btn_talkback")
        self.btn_talkback.setFont(font4)
        self.btn_talkback.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_22.addWidget(self.btn_talkback)

        self.btn_alternado = QPushButton(Audiometer)
        self.btn_alternado.setObjectName(u"btn_alternado")
        self.btn_alternado.setFont(font4)
        self.btn_alternado.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_alternado.setCheckable(False)

        self.horizontalLayout_22.addWidget(self.btn_alternado)


        self.verticalLayout_6.addLayout(self.horizontalLayout_22)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, 0, -1, -1)
        self.btn_freq_minus = QPushButton(Audiometer)
        self.btn_freq_minus.setObjectName(u"btn_freq_minus")
        self.btn_freq_minus.setFont(font4)
        self.btn_freq_minus.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_6.addWidget(self.btn_freq_minus)

        self.label_2 = QLabel(Audiometer)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font4)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.label_2)

        self.btn_freq_plus = QPushButton(Audiometer)
        self.btn_freq_plus.setObjectName(u"btn_freq_plus")
        self.btn_freq_plus.setFont(font4)
        self.btn_freq_plus.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_6.addWidget(self.btn_freq_plus)


        self.verticalLayout_6.addLayout(self.horizontalLayout_6)


        self.control_dial_down.addLayout(self.verticalLayout_6)

        self.line_4 = QFrame(Audiometer)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.VLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.control_dial_down.addWidget(self.line_4)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.btn_puls_izq = QPushButton(Audiometer)
        self.btn_puls_izq.setObjectName(u"btn_puls_izq")
        self.btn_puls_izq.setFont(font4)

        self.verticalLayout_10.addWidget(self.btn_puls_izq)

        self.btn_rever_ch1 = QPushButton(Audiometer)
        self.btn_rever_ch1.setObjectName(u"btn_rever_ch1")
        self.btn_rever_ch1.setFont(font4)
        self.btn_rever_ch1.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_rever_ch1.setCheckable(False)

        self.verticalLayout_10.addWidget(self.btn_rever_ch1)

        self.verticalSpacer_12 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_12)

        self.btn_stim_ch1 = QPushButton(Audiometer)
        self.btn_stim_ch1.setObjectName(u"btn_stim_ch1")
        self.btn_stim_ch1.setFont(font4)
        self.btn_stim_ch1.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout_10.addWidget(self.btn_stim_ch1)

        self.verticalSpacer_13 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_13)


        self.horizontalLayout_4.addLayout(self.verticalLayout_10)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.dial_izq = QDial(Audiometer)
        self.dial_izq.setObjectName(u"dial_izq")
        self.dial_izq.setCursor(QCursor(Qt.OpenHandCursor))
        self.dial_izq.setMinimum(1)
        self.dial_izq.setMaximum(20)
        self.dial_izq.setSingleStep(1)
        self.dial_izq.setPageStep(1)
        self.dial_izq.setValue(10)
        self.dial_izq.setWrapping(True)

        self.verticalLayout_9.addWidget(self.dial_izq)


        self.horizontalLayout_4.addLayout(self.verticalLayout_9)


        self.control_dial_down.addLayout(self.horizontalLayout_4)


        self.control.addLayout(self.control_dial_down)


        self.verticalLayout.addLayout(self.control)


        self.horizontalLayout_7.addLayout(self.verticalLayout)


        self.retranslateUi(Audiometer)

        self.btn_step_5.setDefault(False)
        self.btn_stim_ch0.setDefault(False)


        QMetaObject.connectSlotsByName(Audiometer)
    # setupUi

    def retranslateUi(self, Audiometer):
        Audiometer.setWindowTitle(QCoreApplication.translate("Audiometer", u"Audi\u00f3metro - Audiosim", None))
        self.lbl_int_ch0.setText(QCoreApplication.translate("Audiometer", u"20 dB HL", None))
        self.lbl_trans_ch0.setText(QCoreApplication.translate("Audiometer", u"Aerea", None))
        self.lbl_step_ch0.setText(QCoreApplication.translate("Audiometer", u"Pasos : 5 dB ", None))
        self.lbl_output_ch0.setText(QCoreApplication.translate("Audiometer", u"Derecha", None))
        self.lbl_stim_ch0.setText(QCoreApplication.translate("Audiometer", u"Tono", None))
        self.lbl_contin_ch0.setText(QCoreApplication.translate("Audiometer", u"Continuo", None))
        self.lbl_rev_ch0.setText(QCoreApplication.translate("Audiometer", u"Normal", None))
        self.lbl_warning_stim_der.setText("")
        self.vmeter_der.setFormat("")
        self.lbl_freq.setText(QCoreApplication.translate("Audiometer", u"1000 Hz", None))
        self.lbl_prueba.setText(QCoreApplication.translate("Audiometer", u"Umbrales", None))
        self.lbl_time.setText(QCoreApplication.translate("Audiometer", u"0:0", None))
        self.lbl_response.setText("")
        self.lbl_ext_der.setText("")
        self.lbl_warning_stim_cent.setText("")
        self.lbl_ext_izq.setText("")
        self.vmeter_izq.setFormat("")
        self.lbl_int_ch1.setText(QCoreApplication.translate("Audiometer", u"20 dB HL", None))
        self.lbl_trans_ch1.setText(QCoreApplication.translate("Audiometer", u"Aerea", None))
        self.lbl_step_ch1.setText(QCoreApplication.translate("Audiometer", u"Pasos : 5 dB ", None))
        self.lbl_output_ch1.setText(QCoreApplication.translate("Audiometer", u"Izquierda", None))
        self.lbl_stim_ch1.setText(QCoreApplication.translate("Audiometer", u"Narrow Band Noise", None))
        self.lbl_contin_ch1.setText(QCoreApplication.translate("Audiometer", u"Continuo", None))
        self.lbl_rev_ch1.setText(QCoreApplication.translate("Audiometer", u"Normal", None))
        self.lbl_warning_stim_izq.setText("")
        self.label_3.setText(QCoreApplication.translate("Audiometer", u"Monitor", None))
        self.label_4.setText(QCoreApplication.translate("Audiometer", u"ch1", None))
        self.label_5.setText(QCoreApplication.translate("Audiometer", u"ch2", None))
        self.label_15.setText(QCoreApplication.translate("Audiometer", u"Salida", None))
        self.btn_output_der_der.setText(QCoreApplication.translate("Audiometer", u"Derecha", None))
        self.btn_output_izq_der.setText(QCoreApplication.translate("Audiometer", u"Izquierda", None))
        self.btn_output_sim_der.setText(QCoreApplication.translate("Audiometer", u"Simult\u00e1neo", None))
        self.label_11.setText(QCoreApplication.translate("Audiometer", u"Est\u00edmulo", None))
        self.btn_stim_tone_der.setText(QCoreApplication.translate("Audiometer", u"Tono", None))
        self.btn_stim_fm_der.setText(QCoreApplication.translate("Audiometer", u"FM", None))
        self.btn_stim_speech_der.setText(QCoreApplication.translate("Audiometer", u"Habla", None))
        self.btn_stim_wn_der.setText(QCoreApplication.translate("Audiometer", u"WN", None))
        self.btn_stim_nbn_der.setText(QCoreApplication.translate("Audiometer", u"NBN", None))
        self.btn_stim_pn_der.setText(QCoreApplication.translate("Audiometer", u"PN", None))
        self.btn_stim_sn_der.setText(QCoreApplication.translate("Audiometer", u"SN", None))
        self.label_10.setText(QCoreApplication.translate("Audiometer", u"Transductor", None))
        self.btn_trans_aer_der.setText(QCoreApplication.translate("Audiometer", u"A\u00e9reo", None))
        self.btn_trans_ose_der.setText(QCoreApplication.translate("Audiometer", u"Osea", None))
        self.btn_trans_cl_der.setText(QCoreApplication.translate("Audiometer", u"C. libre", None))
        self.btn_alt_frec.setText(QCoreApplication.translate("Audiometer", u"Alta frec.", None))
        self.groupBox_step.setTitle(QCoreApplication.translate("Audiometer", u"Pasos", None))
        self.btn_step_1.setText(QCoreApplication.translate("Audiometer", u"1", None))
#if QT_CONFIG(shortcut)
        self.btn_step_1.setShortcut(QCoreApplication.translate("Audiometer", u"1", None))
#endif // QT_CONFIG(shortcut)
        self.btn_step_3.setText(QCoreApplication.translate("Audiometer", u"3", None))
#if QT_CONFIG(shortcut)
        self.btn_step_3.setShortcut(QCoreApplication.translate("Audiometer", u"3", None))
#endif // QT_CONFIG(shortcut)
        self.btn_step_5.setText(QCoreApplication.translate("Audiometer", u"5", None))
#if QT_CONFIG(shortcut)
        self.btn_step_5.setShortcut(QCoreApplication.translate("Audiometer", u"5", None))
#endif // QT_CONFIG(shortcut)
        self.btn_ext_range.setText(QCoreApplication.translate("Audiometer", u"Ext. Rango", None))
#if QT_CONFIG(shortcut)
        self.btn_ext_range.setShortcut(QCoreApplication.translate("Audiometer", u"E", None))
#endif // QT_CONFIG(shortcut)
        self.label_12.setText(QCoreApplication.translate("Audiometer", u"Transductor", None))
        self.btn_trans_aer_izq.setText(QCoreApplication.translate("Audiometer", u"A\u00e9reo", None))
        self.btn_trans_ose_izq.setText(QCoreApplication.translate("Audiometer", u"Osea", None))
        self.btn_trans_cl_izq.setText(QCoreApplication.translate("Audiometer", u"C. libre", None))
        self.label_13.setText(QCoreApplication.translate("Audiometer", u"Est\u00edmulo", None))
        self.btn_stim_tone_izq.setText(QCoreApplication.translate("Audiometer", u"Tono", None))
        self.btn_stim_fm_izq.setText(QCoreApplication.translate("Audiometer", u"FM", None))
        self.btn_stim_speech_izq.setText(QCoreApplication.translate("Audiometer", u"Habla", None))
        self.btn_stim_wn_izq.setText(QCoreApplication.translate("Audiometer", u"WN", None))
        self.btn_stim_nbn_izq.setText(QCoreApplication.translate("Audiometer", u"NBN", None))
        self.btn_stim_pn_izq.setText(QCoreApplication.translate("Audiometer", u"PN", None))
        self.btn_stim_sn_izq.setText(QCoreApplication.translate("Audiometer", u"SN", None))
        self.label_14.setText(QCoreApplication.translate("Audiometer", u"Salida", None))
        self.btn_output_der_izq.setText(QCoreApplication.translate("Audiometer", u"Derecha", None))
        self.btn_output_izq_izq.setText(QCoreApplication.translate("Audiometer", u"Izquierda", None))
        self.btn_output_sim_izq.setText(QCoreApplication.translate("Audiometer", u"Simult\u00e1neo", None))
        self.label.setText(QCoreApplication.translate("Audiometer", u"Talkback", None))
        self.btn_puls_der.setText(QCoreApplication.translate("Audiometer", u"Pulsado", None))
        self.btn_rever_ch0.setText(QCoreApplication.translate("Audiometer", u"Invertir", None))
#if QT_CONFIG(tooltip)
        self.btn_stim_ch0.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.btn_stim_ch0.setText(QCoreApplication.translate("Audiometer", u"Est\u00edmulo", None))
        self.btn_time_start.setText(QCoreApplication.translate("Audiometer", u"Iniciar", None))
        self.btn_time_stop.setText(QCoreApplication.translate("Audiometer", u"Detener", None))
        self.btn_time_clear.setText(QCoreApplication.translate("Audiometer", u"Borrar", None))
        self.btn_correcta.setText(QCoreApplication.translate("Audiometer", u"+1", None))
        self.btn_borrar.setText(QCoreApplication.translate("Audiometer", u"Limpiar", None))
        self.btn_incorrecta.setText(QCoreApplication.translate("Audiometer", u"-1", None))
        self.btn_talkback.setText(QCoreApplication.translate("Audiometer", u"Talkback", None))
        self.btn_alternado.setText(QCoreApplication.translate("Audiometer", u"Alternado", None))
        self.btn_freq_minus.setText(QCoreApplication.translate("Audiometer", u"<", None))
#if QT_CONFIG(shortcut)
        self.btn_freq_minus.setShortcut(QCoreApplication.translate("Audiometer", u"A", None))
#endif // QT_CONFIG(shortcut)
        self.label_2.setText(QCoreApplication.translate("Audiometer", u"Frecuencia", None))
        self.btn_freq_plus.setText(QCoreApplication.translate("Audiometer", u">", None))
#if QT_CONFIG(shortcut)
        self.btn_freq_plus.setShortcut(QCoreApplication.translate("Audiometer", u"D", None))
#endif // QT_CONFIG(shortcut)
        self.btn_puls_izq.setText(QCoreApplication.translate("Audiometer", u"Pulsado", None))
        self.btn_rever_ch1.setText(QCoreApplication.translate("Audiometer", u"Invertir", None))
        self.btn_stim_ch1.setText(QCoreApplication.translate("Audiometer", u"Est\u00edmulo", None))
    # retranslateUi

