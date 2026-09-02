# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Audimetry_create_profile.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QSpinBox, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_generator_audio(object):
    def setupUi(self, generator_audio):
        if not generator_audio.objectName():
            generator_audio.setObjectName(u"generator_audio")
        generator_audio.resize(753, 778)
        self.verticalLayout = QVBoxLayout(generator_audio)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_64 = QLabel(generator_audio)
        self.label_64.setObjectName(u"label_64")

        self.horizontalLayout_7.addWidget(self.label_64)

        self.led_name = QLineEdit(generator_audio)
        self.led_name.setObjectName(u"led_name")
        self.led_name.setFrame(True)
        self.led_name.setReadOnly(True)

        self.horizontalLayout_7.addWidget(self.led_name)

        self.pushButton = QPushButton(generator_audio)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_7.addWidget(self.pushButton)


        self.verticalLayout.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setSpacing(30)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_65 = QLabel(generator_audio)
        self.label_65.setObjectName(u"label_65")
        self.label_65.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_9.addWidget(self.label_65)

        self.spinBox = QSpinBox(generator_audio)
        self.spinBox.setObjectName(u"spinBox")
        self.spinBox.setMinimum(1)

        self.horizontalLayout_9.addWidget(self.spinBox)


        self.horizontalLayout_8.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_66 = QLabel(generator_audio)
        self.label_66.setObjectName(u"label_66")
        self.label_66.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_10.addWidget(self.label_66)

        self.radioButton = QRadioButton(generator_audio)
        self.radioButton.setObjectName(u"radioButton")

        self.horizontalLayout_10.addWidget(self.radioButton)

        self.radioButton_2 = QRadioButton(generator_audio)
        self.radioButton_2.setObjectName(u"radioButton_2")
        self.radioButton_2.setChecked(True)

        self.horizontalLayout_10.addWidget(self.radioButton_2)


        self.horizontalLayout_8.addLayout(self.horizontalLayout_10)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.tabWidget = QTabWidget(generator_audio)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_audiometria = QWidget()
        self.tab_audiometria.setObjectName(u"tab_audiometria")
        self.verticalLayout_tab1 = QVBoxLayout(self.tab_audiometria)
        self.verticalLayout_tab1.setObjectName(u"verticalLayout_tab1")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.spbox_a_oi_1 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_1.setObjectName(u"spbox_a_oi_1")
        self.spbox_a_oi_1.setMaximum(120)
        self.spbox_a_oi_1.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_1, 2, 3, 1, 1)

        self.spbox_a_od_0 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_0.setObjectName(u"spbox_a_od_0")
        self.spbox_a_od_0.setMaximum(120)
        self.spbox_a_od_0.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_0, 1, 2, 1, 1)

        self.spbox_a_od_7 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_7.setObjectName(u"spbox_a_od_7")
        self.spbox_a_od_7.setMaximum(120)
        self.spbox_a_od_7.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_7, 1, 9, 1, 1)

        self.spbox_a_oi_6 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_6.setObjectName(u"spbox_a_oi_6")
        self.spbox_a_oi_6.setMaximum(120)
        self.spbox_a_oi_6.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_6, 2, 8, 1, 1)

        self.spbox_a_oi_8 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_8.setObjectName(u"spbox_a_oi_8")
        self.spbox_a_oi_8.setMaximum(120)
        self.spbox_a_oi_8.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_8, 2, 10, 1, 1)

        self.label_10 = QLabel(self.tab_audiometria)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout.addWidget(self.label_10, 0, 1, 1, 1)

        self.spbox_a_od_1 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_1.setObjectName(u"spbox_a_od_1")
        self.spbox_a_od_1.setMaximum(120)
        self.spbox_a_od_1.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_1, 1, 3, 1, 1)

        self.spbox_a_od_5 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_5.setObjectName(u"spbox_a_od_5")
        self.spbox_a_od_5.setMaximum(120)
        self.spbox_a_od_5.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_5, 1, 7, 1, 1)

        self.label_2 = QLabel(self.tab_audiometria)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 0, 3, 1, 1)

        self.label_11 = QLabel(self.tab_audiometria)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout.addWidget(self.label_11, 1, 1, 1, 1)

        self.label_8 = QLabel(self.tab_audiometria)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout.addWidget(self.label_8, 0, 9, 1, 1)

        self.spbox_a_oi_2 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_2.setObjectName(u"spbox_a_oi_2")
        self.spbox_a_oi_2.setMaximum(120)
        self.spbox_a_oi_2.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_2, 2, 4, 1, 1)

        self.spbox_a_od_8 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_8.setObjectName(u"spbox_a_od_8")
        self.spbox_a_od_8.setMaximum(120)
        self.spbox_a_od_8.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_8, 1, 10, 1, 1)

        self.label_9 = QLabel(self.tab_audiometria)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 0, 10, 1, 1)

        self.spbox_a_oi_5 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_5.setObjectName(u"spbox_a_oi_5")
        self.spbox_a_oi_5.setMaximum(120)
        self.spbox_a_oi_5.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_5, 2, 7, 1, 1)

        self.spbox_a_oi_3 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_3.setObjectName(u"spbox_a_oi_3")
        self.spbox_a_oi_3.setMaximum(120)
        self.spbox_a_oi_3.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_3, 2, 5, 1, 1)

        self.label_6 = QLabel(self.tab_audiometria)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 0, 7, 1, 1)

        self.spbox_a_od_3 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_3.setObjectName(u"spbox_a_od_3")
        self.spbox_a_od_3.setMaximum(120)
        self.spbox_a_od_3.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_3, 1, 5, 1, 1)

        self.label_13 = QLabel(self.tab_audiometria)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout.addWidget(self.label_13, 0, 0, 3, 1)

        self.spbox_a_od_4 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_4.setObjectName(u"spbox_a_od_4")
        self.spbox_a_od_4.setMaximum(120)
        self.spbox_a_od_4.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_4, 1, 6, 1, 1)

        self.label_12 = QLabel(self.tab_audiometria)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 2, 1, 1, 1)

        self.spbox_a_oi_0 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_0.setObjectName(u"spbox_a_oi_0")
        self.spbox_a_oi_0.setMaximum(120)
        self.spbox_a_oi_0.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_0, 2, 2, 1, 1)

        self.label = QLabel(self.tab_audiometria)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 2, 1, 1)

        self.label_7 = QLabel(self.tab_audiometria)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 0, 8, 1, 1)

        self.spbox_a_oi_7 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_7.setObjectName(u"spbox_a_oi_7")
        self.spbox_a_oi_7.setMaximum(120)
        self.spbox_a_oi_7.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_7, 2, 9, 1, 1)

        self.spbox_a_oi_4 = QSpinBox(self.tab_audiometria)
        self.spbox_a_oi_4.setObjectName(u"spbox_a_oi_4")
        self.spbox_a_oi_4.setMaximum(120)
        self.spbox_a_oi_4.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_4, 2, 6, 1, 1)

        self.label_5 = QLabel(self.tab_audiometria)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 6, 1, 1)

        self.label_4 = QLabel(self.tab_audiometria)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 0, 5, 1, 1)

        self.spbox_a_od_6 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_6.setObjectName(u"spbox_a_od_6")
        self.spbox_a_od_6.setMaximum(120)
        self.spbox_a_od_6.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_6, 1, 8, 1, 1)

        self.spbox_a_od_2 = QSpinBox(self.tab_audiometria)
        self.spbox_a_od_2.setObjectName(u"spbox_a_od_2")
        self.spbox_a_od_2.setMaximum(120)
        self.spbox_a_od_2.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_2, 1, 4, 1, 1)

        self.label_3 = QLabel(self.tab_audiometria)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 4, 1, 1)


        self.verticalLayout_tab1.addLayout(self.gridLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_41 = QLabel(self.tab_audiometria)
        self.label_41.setObjectName(u"label_41")

        self.horizontalLayout.addWidget(self.label_41)

        self.chbox_peg_od = QCheckBox(self.tab_audiometria)
        self.chbox_peg_od.setObjectName(u"chbox_peg_od")

        self.horizontalLayout.addWidget(self.chbox_peg_od)

        self.chbox_peg_oi = QCheckBox(self.tab_audiometria)
        self.chbox_peg_oi.setObjectName(u"chbox_peg_oi")

        self.horizontalLayout.addWidget(self.chbox_peg_oi)


        self.verticalLayout_tab1.addLayout(self.horizontalLayout)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_14 = QLabel(self.tab_audiometria)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_2.addWidget(self.label_14, 0, 5, 1, 1)

        self.label_15 = QLabel(self.tab_audiometria)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_2.addWidget(self.label_15, 0, 1, 1, 1)

        self.label_16 = QLabel(self.tab_audiometria)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_2.addWidget(self.label_16, 1, 1, 1, 1)

        self.label_17 = QLabel(self.tab_audiometria)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_2.addWidget(self.label_17, 0, 2, 1, 1)

        self.label_18 = QLabel(self.tab_audiometria)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_2.addWidget(self.label_18, 0, 6, 1, 1)

        self.label_19 = QLabel(self.tab_audiometria)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_2.addWidget(self.label_19, 0, 10, 1, 1)

        self.label_20 = QLabel(self.tab_audiometria)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_2.addWidget(self.label_20, 2, 1, 1, 1)

        self.label_21 = QLabel(self.tab_audiometria)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_2.addWidget(self.label_21, 0, 3, 1, 1)

        self.label_22 = QLabel(self.tab_audiometria)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_2.addWidget(self.label_22, 0, 7, 1, 1)

        self.label_23 = QLabel(self.tab_audiometria)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout_2.addWidget(self.label_23, 0, 4, 1, 1)

        self.label_24 = QLabel(self.tab_audiometria)
        self.label_24.setObjectName(u"label_24")

        self.gridLayout_2.addWidget(self.label_24, 0, 9, 1, 1)

        self.label_25 = QLabel(self.tab_audiometria)
        self.label_25.setObjectName(u"label_25")

        self.gridLayout_2.addWidget(self.label_25, 0, 8, 1, 1)

        self.label_26 = QLabel(self.tab_audiometria)
        self.label_26.setObjectName(u"label_26")

        self.gridLayout_2.addWidget(self.label_26, 0, 0, 3, 1)

        self.spbox_o_od_0 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_0.setObjectName(u"spbox_o_od_0")
        self.spbox_o_od_0.setMaximum(120)
        self.spbox_o_od_0.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_0, 1, 2, 1, 1)

        self.spbox_o_od_1 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_1.setObjectName(u"spbox_o_od_1")
        self.spbox_o_od_1.setMaximum(120)
        self.spbox_o_od_1.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_1, 1, 3, 1, 1)

        self.spbox_o_od_2 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_2.setObjectName(u"spbox_o_od_2")
        self.spbox_o_od_2.setMaximum(120)
        self.spbox_o_od_2.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_2, 1, 4, 1, 1)

        self.spbox_o_od_3 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_3.setObjectName(u"spbox_o_od_3")
        self.spbox_o_od_3.setMaximum(120)
        self.spbox_o_od_3.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_3, 1, 5, 1, 1)

        self.spbox_o_od_4 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_4.setObjectName(u"spbox_o_od_4")
        self.spbox_o_od_4.setMaximum(120)
        self.spbox_o_od_4.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_4, 1, 6, 1, 1)

        self.spbox_o_od_5 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_5.setObjectName(u"spbox_o_od_5")
        self.spbox_o_od_5.setMaximum(120)
        self.spbox_o_od_5.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_5, 1, 7, 1, 1)

        self.spbox_o_od_6 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_6.setObjectName(u"spbox_o_od_6")
        self.spbox_o_od_6.setMaximum(120)
        self.spbox_o_od_6.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_6, 1, 8, 1, 1)

        self.spbox_o_od_7 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_7.setObjectName(u"spbox_o_od_7")
        self.spbox_o_od_7.setMaximum(120)
        self.spbox_o_od_7.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_7, 1, 9, 1, 1)

        self.spbox_o_od_8 = QSpinBox(self.tab_audiometria)
        self.spbox_o_od_8.setObjectName(u"spbox_o_od_8")
        self.spbox_o_od_8.setMaximum(120)
        self.spbox_o_od_8.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_8, 1, 10, 1, 1)

        self.spbox_o_oi_6 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_6.setObjectName(u"spbox_o_oi_6")
        self.spbox_o_oi_6.setMaximum(120)
        self.spbox_o_oi_6.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_6, 2, 8, 1, 1)

        self.spbox_o_oi_7 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_7.setObjectName(u"spbox_o_oi_7")
        self.spbox_o_oi_7.setMaximum(120)
        self.spbox_o_oi_7.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_7, 2, 9, 1, 1)

        self.spbox_o_oi_8 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_8.setObjectName(u"spbox_o_oi_8")
        self.spbox_o_oi_8.setMaximum(120)
        self.spbox_o_oi_8.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_8, 2, 10, 1, 1)

        self.spbox_o_oi_0 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_0.setObjectName(u"spbox_o_oi_0")
        self.spbox_o_oi_0.setMaximum(120)
        self.spbox_o_oi_0.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_0, 2, 2, 1, 1)

        self.spbox_o_oi_1 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_1.setObjectName(u"spbox_o_oi_1")
        self.spbox_o_oi_1.setMaximum(120)
        self.spbox_o_oi_1.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_1, 2, 3, 1, 1)

        self.spbox_o_oi_2 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_2.setObjectName(u"spbox_o_oi_2")
        self.spbox_o_oi_2.setMaximum(120)
        self.spbox_o_oi_2.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_2, 2, 4, 1, 1)

        self.spbox_o_oi_3 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_3.setObjectName(u"spbox_o_oi_3")
        self.spbox_o_oi_3.setMaximum(120)
        self.spbox_o_oi_3.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_3, 2, 5, 1, 1)

        self.spbox_o_oi_4 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_4.setObjectName(u"spbox_o_oi_4")
        self.spbox_o_oi_4.setMaximum(120)
        self.spbox_o_oi_4.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_4, 2, 6, 1, 1)

        self.spbox_o_oi_5 = QSpinBox(self.tab_audiometria)
        self.spbox_o_oi_5.setObjectName(u"spbox_o_oi_5")
        self.spbox_o_oi_5.setMaximum(120)
        self.spbox_o_oi_5.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_5, 2, 7, 1, 1)


        self.verticalLayout_tab1.addLayout(self.gridLayout_2)

        self.line_3 = QFrame(self.tab_audiometria)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_tab1.addWidget(self.line_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_42 = QLabel(self.tab_audiometria)
        self.label_42.setObjectName(u"label_42")

        self.horizontalLayout_2.addWidget(self.label_42)

        self.chbox_ldl_od = QCheckBox(self.tab_audiometria)
        self.chbox_ldl_od.setObjectName(u"chbox_ldl_od")

        self.horizontalLayout_2.addWidget(self.chbox_ldl_od)

        self.chbox_ldl_oi = QCheckBox(self.tab_audiometria)
        self.chbox_ldl_oi.setObjectName(u"chbox_ldl_oi")

        self.horizontalLayout_2.addWidget(self.chbox_ldl_oi)


        self.verticalLayout_tab1.addLayout(self.horizontalLayout_2)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.spbox_ldl_od_4 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_4.setObjectName(u"spbox_ldl_od_4")
        self.spbox_ldl_od_4.setEnabled(False)
        self.spbox_ldl_od_4.setMaximum(130)
        self.spbox_ldl_od_4.setSingleStep(5)
        self.spbox_ldl_od_4.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_4, 1, 6, 1, 1)

        self.label_33 = QLabel(self.tab_audiometria)
        self.label_33.setObjectName(u"label_33")

        self.gridLayout_3.addWidget(self.label_33, 2, 1, 1, 1)

        self.spbox_ldl_oi_0 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_0.setObjectName(u"spbox_ldl_oi_0")
        self.spbox_ldl_oi_0.setEnabled(False)
        self.spbox_ldl_oi_0.setMaximum(130)
        self.spbox_ldl_oi_0.setSingleStep(5)
        self.spbox_ldl_oi_0.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_0, 2, 2, 1, 1)

        self.spbox_ldl_oi_8 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_8.setObjectName(u"spbox_ldl_oi_8")
        self.spbox_ldl_oi_8.setEnabled(False)
        self.spbox_ldl_oi_8.setMaximum(130)
        self.spbox_ldl_oi_8.setSingleStep(5)
        self.spbox_ldl_oi_8.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_8, 2, 10, 1, 1)

        self.label_35 = QLabel(self.tab_audiometria)
        self.label_35.setObjectName(u"label_35")

        self.gridLayout_3.addWidget(self.label_35, 0, 7, 1, 1)

        self.spbox_ldl_oi_7 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_7.setObjectName(u"spbox_ldl_oi_7")
        self.spbox_ldl_oi_7.setEnabled(False)
        self.spbox_ldl_oi_7.setMaximum(130)
        self.spbox_ldl_oi_7.setSingleStep(5)
        self.spbox_ldl_oi_7.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_7, 2, 9, 1, 1)

        self.spbox_ldl_od_3 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_3.setObjectName(u"spbox_ldl_od_3")
        self.spbox_ldl_od_3.setEnabled(False)
        self.spbox_ldl_od_3.setMaximum(130)
        self.spbox_ldl_od_3.setSingleStep(5)
        self.spbox_ldl_od_3.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_3, 1, 5, 1, 1)

        self.spbox_ldl_od_7 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_7.setObjectName(u"spbox_ldl_od_7")
        self.spbox_ldl_od_7.setEnabled(False)
        self.spbox_ldl_od_7.setMaximum(130)
        self.spbox_ldl_od_7.setSingleStep(5)
        self.spbox_ldl_od_7.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_7, 1, 9, 1, 1)

        self.spbox_ldl_od_8 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_8.setObjectName(u"spbox_ldl_od_8")
        self.spbox_ldl_od_8.setEnabled(False)
        self.spbox_ldl_od_8.setMaximum(130)
        self.spbox_ldl_od_8.setSingleStep(5)
        self.spbox_ldl_od_8.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_8, 1, 10, 1, 1)

        self.label_27 = QLabel(self.tab_audiometria)
        self.label_27.setObjectName(u"label_27")

        self.gridLayout_3.addWidget(self.label_27, 0, 5, 1, 1)

        self.label_30 = QLabel(self.tab_audiometria)
        self.label_30.setObjectName(u"label_30")

        self.gridLayout_3.addWidget(self.label_30, 0, 2, 1, 1)

        self.spbox_ldl_od_1 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_1.setObjectName(u"spbox_ldl_od_1")
        self.spbox_ldl_od_1.setEnabled(False)
        self.spbox_ldl_od_1.setMaximum(130)
        self.spbox_ldl_od_1.setSingleStep(5)
        self.spbox_ldl_od_1.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_1, 1, 3, 1, 1)

        self.spbox_ldl_oi_5 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_5.setObjectName(u"spbox_ldl_oi_5")
        self.spbox_ldl_oi_5.setEnabled(False)
        self.spbox_ldl_oi_5.setMaximum(130)
        self.spbox_ldl_oi_5.setSingleStep(5)
        self.spbox_ldl_oi_5.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_5, 2, 7, 1, 1)

        self.label_38 = QLabel(self.tab_audiometria)
        self.label_38.setObjectName(u"label_38")

        self.gridLayout_3.addWidget(self.label_38, 0, 8, 1, 1)

        self.spbox_ldl_od_5 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_5.setObjectName(u"spbox_ldl_od_5")
        self.spbox_ldl_od_5.setEnabled(False)
        self.spbox_ldl_od_5.setMaximum(130)
        self.spbox_ldl_od_5.setSingleStep(5)
        self.spbox_ldl_od_5.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_5, 1, 7, 1, 1)

        self.spbox_ldl_oi_2 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_2.setObjectName(u"spbox_ldl_oi_2")
        self.spbox_ldl_oi_2.setEnabled(False)
        self.spbox_ldl_oi_2.setMaximum(130)
        self.spbox_ldl_oi_2.setSingleStep(5)
        self.spbox_ldl_oi_2.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_2, 2, 4, 1, 1)

        self.label_29 = QLabel(self.tab_audiometria)
        self.label_29.setObjectName(u"label_29")

        self.gridLayout_3.addWidget(self.label_29, 1, 1, 1, 1)

        self.spbox_ldl_od_0 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_0.setObjectName(u"spbox_ldl_od_0")
        self.spbox_ldl_od_0.setEnabled(False)
        self.spbox_ldl_od_0.setMaximum(130)
        self.spbox_ldl_od_0.setSingleStep(5)
        self.spbox_ldl_od_0.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_0, 1, 2, 1, 1)

        self.label_37 = QLabel(self.tab_audiometria)
        self.label_37.setObjectName(u"label_37")

        self.gridLayout_3.addWidget(self.label_37, 0, 9, 1, 1)

        self.spbox_ldl_oi_1 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_1.setObjectName(u"spbox_ldl_oi_1")
        self.spbox_ldl_oi_1.setEnabled(False)
        self.spbox_ldl_oi_1.setMaximum(130)
        self.spbox_ldl_oi_1.setSingleStep(5)
        self.spbox_ldl_oi_1.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_1, 2, 3, 1, 1)

        self.label_34 = QLabel(self.tab_audiometria)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout_3.addWidget(self.label_34, 0, 3, 1, 1)

        self.label_32 = QLabel(self.tab_audiometria)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout_3.addWidget(self.label_32, 0, 10, 1, 1)

        self.label_39 = QLabel(self.tab_audiometria)
        self.label_39.setObjectName(u"label_39")

        self.gridLayout_3.addWidget(self.label_39, 0, 0, 3, 1)

        self.spbox_ldl_od_6 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_6.setObjectName(u"spbox_ldl_od_6")
        self.spbox_ldl_od_6.setEnabled(False)
        self.spbox_ldl_od_6.setMaximum(130)
        self.spbox_ldl_od_6.setSingleStep(5)
        self.spbox_ldl_od_6.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_6, 1, 8, 1, 1)

        self.spbox_ldl_oi_4 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_4.setObjectName(u"spbox_ldl_oi_4")
        self.spbox_ldl_oi_4.setEnabled(False)
        self.spbox_ldl_oi_4.setMaximum(130)
        self.spbox_ldl_oi_4.setSingleStep(5)
        self.spbox_ldl_oi_4.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_4, 2, 6, 1, 1)

        self.spbox_ldl_od_2 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_od_2.setObjectName(u"spbox_ldl_od_2")
        self.spbox_ldl_od_2.setEnabled(False)
        self.spbox_ldl_od_2.setMaximum(130)
        self.spbox_ldl_od_2.setSingleStep(5)
        self.spbox_ldl_od_2.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_2, 1, 4, 1, 1)

        self.label_31 = QLabel(self.tab_audiometria)
        self.label_31.setObjectName(u"label_31")

        self.gridLayout_3.addWidget(self.label_31, 0, 6, 1, 1)

        self.label_36 = QLabel(self.tab_audiometria)
        self.label_36.setObjectName(u"label_36")

        self.gridLayout_3.addWidget(self.label_36, 0, 4, 1, 1)

        self.spbox_ldl_oi_3 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_3.setObjectName(u"spbox_ldl_oi_3")
        self.spbox_ldl_oi_3.setEnabled(False)
        self.spbox_ldl_oi_3.setMaximum(130)
        self.spbox_ldl_oi_3.setSingleStep(5)
        self.spbox_ldl_oi_3.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_3, 2, 5, 1, 1)

        self.spbox_ldl_oi_6 = QSpinBox(self.tab_audiometria)
        self.spbox_ldl_oi_6.setObjectName(u"spbox_ldl_oi_6")
        self.spbox_ldl_oi_6.setEnabled(False)
        self.spbox_ldl_oi_6.setMaximum(130)
        self.spbox_ldl_oi_6.setSingleStep(5)
        self.spbox_ldl_oi_6.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_6, 2, 8, 1, 1)

        self.label_28 = QLabel(self.tab_audiometria)
        self.label_28.setObjectName(u"label_28")

        self.gridLayout_3.addWidget(self.label_28, 0, 1, 1, 1)


        self.verticalLayout_tab1.addLayout(self.gridLayout_3)

        self.label_40 = QLabel(self.tab_audiometria)
        self.label_40.setObjectName(u"label_40")

        self.verticalLayout_tab1.addWidget(self.label_40)

        self.line_2 = QFrame(self.tab_audiometria)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_tab1.addWidget(self.line_2)

        self.tabWidget.addTab(self.tab_audiometria, "")
        self.tab_otras = QWidget()
        self.tab_otras.setObjectName(u"tab_otras")
        self.verticalLayout_tab2 = QVBoxLayout(self.tab_otras)
        self.verticalLayout_tab2.setObjectName(u"verticalLayout_tab2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_43 = QLabel(self.tab_otras)
        self.label_43.setObjectName(u"label_43")
        self.label_43.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_43)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_51 = QLabel(self.tab_otras)
        self.label_51.setObjectName(u"label_51")

        self.gridLayout_4.addWidget(self.label_51, 1, 2, 1, 1)

        self.label_47 = QLabel(self.tab_otras)
        self.label_47.setObjectName(u"label_47")

        self.gridLayout_4.addWidget(self.label_47, 4, 0, 1, 1)

        self.label_45 = QLabel(self.tab_otras)
        self.label_45.setObjectName(u"label_45")

        self.gridLayout_4.addWidget(self.label_45, 2, 0, 1, 1)

        self.label_49 = QLabel(self.tab_otras)
        self.label_49.setObjectName(u"label_49")

        self.gridLayout_4.addWidget(self.label_49, 0, 4, 1, 1)

        self.label_50 = QLabel(self.tab_otras)
        self.label_50.setObjectName(u"label_50")

        self.gridLayout_4.addWidget(self.label_50, 0, 1, 1, 2)

        self.label_46 = QLabel(self.tab_otras)
        self.label_46.setObjectName(u"label_46")

        self.gridLayout_4.addWidget(self.label_46, 3, 0, 1, 1)

        self.label_48 = QLabel(self.tab_otras)
        self.label_48.setObjectName(u"label_48")

        self.gridLayout_4.addWidget(self.label_48, 1, 1, 1, 1)

        self.label_52 = QLabel(self.tab_otras)
        self.label_52.setObjectName(u"label_52")

        self.gridLayout_4.addWidget(self.label_52, 1, 3, 1, 1)

        self.label_53 = QLabel(self.tab_otras)
        self.label_53.setObjectName(u"label_53")

        self.gridLayout_4.addWidget(self.label_53, 1, 4, 1, 1)

        self.label_54 = QLabel(self.tab_otras)
        self.label_54.setObjectName(u"label_54")

        self.gridLayout_4.addWidget(self.label_54, 3, 2, 1, 1)

        self.label_55 = QLabel(self.tab_otras)
        self.label_55.setObjectName(u"label_55")

        self.gridLayout_4.addWidget(self.label_55, 3, 4, 1, 1)

        self.label_56 = QLabel(self.tab_otras)
        self.label_56.setObjectName(u"label_56")

        self.gridLayout_4.addWidget(self.label_56, 2, 2, 1, 1)

        self.label_57 = QLabel(self.tab_otras)
        self.label_57.setObjectName(u"label_57")

        self.gridLayout_4.addWidget(self.label_57, 2, 4, 1, 1)

        self.spbox_sdt_od_0 = QSpinBox(self.tab_otras)
        self.spbox_sdt_od_0.setObjectName(u"spbox_sdt_od_0")
        self.spbox_sdt_od_0.setMaximum(130)
        self.spbox_sdt_od_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_sdt_od_0, 2, 1, 1, 1)

        self.spbox_srt_od_0 = QSpinBox(self.tab_otras)
        self.spbox_srt_od_0.setObjectName(u"spbox_srt_od_0")
        self.spbox_srt_od_0.setMaximum(130)
        self.spbox_srt_od_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_srt_od_0, 3, 1, 1, 1)

        self.spbox_umd_od_0 = QSpinBox(self.tab_otras)
        self.spbox_umd_od_0.setObjectName(u"spbox_umd_od_0")
        self.spbox_umd_od_0.setMaximum(130)
        self.spbox_umd_od_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_umd_od_0, 4, 1, 1, 1)

        self.spbox_umd_od_1 = QSpinBox(self.tab_otras)
        self.spbox_umd_od_1.setObjectName(u"spbox_umd_od_1")
        self.spbox_umd_od_1.setMaximum(100)
        self.spbox_umd_od_1.setSingleStep(4)

        self.gridLayout_4.addWidget(self.spbox_umd_od_1, 4, 2, 1, 1)

        self.spbox_umd_oi_0 = QSpinBox(self.tab_otras)
        self.spbox_umd_oi_0.setObjectName(u"spbox_umd_oi_0")
        self.spbox_umd_oi_0.setMaximum(130)
        self.spbox_umd_oi_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_umd_oi_0, 4, 3, 1, 1)

        self.spbox_umd_oi_1 = QSpinBox(self.tab_otras)
        self.spbox_umd_oi_1.setObjectName(u"spbox_umd_oi_1")
        self.spbox_umd_oi_1.setMaximum(100)
        self.spbox_umd_oi_1.setSingleStep(4)

        self.gridLayout_4.addWidget(self.spbox_umd_oi_1, 4, 4, 1, 1)

        self.spbox_srt_oi_0 = QSpinBox(self.tab_otras)
        self.spbox_srt_oi_0.setObjectName(u"spbox_srt_oi_0")
        self.spbox_srt_oi_0.setMaximum(130)
        self.spbox_srt_oi_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_srt_oi_0, 3, 3, 1, 1)

        self.spbox_sdt_oi_0 = QSpinBox(self.tab_otras)
        self.spbox_sdt_oi_0.setObjectName(u"spbox_sdt_oi_0")
        self.spbox_sdt_oi_0.setMaximum(130)
        self.spbox_sdt_oi_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_sdt_oi_0, 2, 3, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout_4)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        self.line = QFrame(self.tab_otras)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_3.addWidget(self.line)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.label_44 = QLabel(self.tab_otras)
        self.label_44.setObjectName(u"label_44")
        self.label_44.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_44)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_58 = QLabel(self.tab_otras)
        self.label_58.setObjectName(u"label_58")

        self.horizontalLayout_5.addWidget(self.label_58)

        self.chbox_recrut_od = QCheckBox(self.tab_otras)
        self.chbox_recrut_od.setObjectName(u"chbox_recrut_od")

        self.horizontalLayout_5.addWidget(self.chbox_recrut_od)

        self.chbox_recrut_oi = QCheckBox(self.tab_otras)
        self.chbox_recrut_oi.setObjectName(u"chbox_recrut_oi")

        self.horizontalLayout_5.addWidget(self.chbox_recrut_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_59 = QLabel(self.tab_otras)
        self.label_59.setObjectName(u"label_59")

        self.horizontalLayout_4.addWidget(self.label_59)

        self.chbox_det_od = QCheckBox(self.tab_otras)
        self.chbox_det_od.setObjectName(u"chbox_det_od")

        self.horizontalLayout_4.addWidget(self.chbox_det_od)

        self.chbox_det_oi = QCheckBox(self.tab_otras)
        self.chbox_det_oi.setObjectName(u"chbox_det_oi")

        self.horizontalLayout_4.addWidget(self.chbox_det_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_60 = QLabel(self.tab_otras)
        self.label_60.setObjectName(u"label_60")

        self.horizontalLayout_6.addWidget(self.label_60)

        self.label_61 = QLabel(self.tab_otras)
        self.label_61.setObjectName(u"label_61")
        self.label_61.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_61)

        self.cb_z_od = QComboBox(self.tab_otras)
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.setObjectName(u"cb_z_od")

        self.horizontalLayout_6.addWidget(self.cb_z_od)

        self.label_62 = QLabel(self.tab_otras)
        self.label_62.setObjectName(u"label_62")
        self.label_62.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_62)

        self.cb_z_oi = QComboBox(self.tab_otras)
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.setObjectName(u"cb_z_oi")

        self.horizontalLayout_6.addWidget(self.cb_z_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_fowler = QHBoxLayout()
        self.horizontalLayout_fowler.setObjectName(u"horizontalLayout_fowler")
        self.label_64 = QLabel(self.tab_otras)
        self.label_64.setObjectName(u"label_64")

        self.horizontalLayout_fowler.addWidget(self.label_64)

        self.cb_fowler_freq = QComboBox(self.tab_otras)
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.addItem("")
        self.cb_fowler_freq.setObjectName(u"cb_fowler_freq")

        self.horizontalLayout_fowler.addWidget(self.cb_fowler_freq)

        self.label_65 = QLabel(self.tab_otras)
        self.label_65.setObjectName(u"label_65")

        self.horizontalLayout_fowler.addWidget(self.label_65)

        self.spbox_fowler_cut_1 = QSpinBox(self.tab_otras)
        self.spbox_fowler_cut_1.setObjectName(u"spbox_fowler_cut_1")
        self.spbox_fowler_cut_1.setMaximum(90)
        self.spbox_fowler_cut_1.setSingleStep(5)
        self.spbox_fowler_cut_1.setValue(15)

        self.horizontalLayout_fowler.addWidget(self.spbox_fowler_cut_1)

        self.spbox_fowler_cut_2 = QSpinBox(self.tab_otras)
        self.spbox_fowler_cut_2.setObjectName(u"spbox_fowler_cut_2")
        self.spbox_fowler_cut_2.setMaximum(90)
        self.spbox_fowler_cut_2.setSingleStep(5)
        self.spbox_fowler_cut_2.setValue(30)

        self.horizontalLayout_fowler.addWidget(self.spbox_fowler_cut_2)

        self.spbox_fowler_cut_3 = QSpinBox(self.tab_otras)
        self.spbox_fowler_cut_3.setObjectName(u"spbox_fowler_cut_3")
        self.spbox_fowler_cut_3.setMaximum(90)
        self.spbox_fowler_cut_3.setSingleStep(5)
        self.spbox_fowler_cut_3.setValue(50)

        self.horizontalLayout_fowler.addWidget(self.spbox_fowler_cut_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_fowler)

        self.horizontalLayout_stenger = QHBoxLayout()
        self.horizontalLayout_stenger.setObjectName(u"horizontalLayout_stenger")
        self.label_66 = QLabel(self.tab_otras)
        self.label_66.setObjectName(u"label_66")

        self.horizontalLayout_stenger.addWidget(self.label_66)

        self.chbox_stenger_od = QCheckBox(self.tab_otras)
        self.chbox_stenger_od.setObjectName(u"chbox_stenger_od")

        self.horizontalLayout_stenger.addWidget(self.chbox_stenger_od)

        self.chbox_stenger_oi = QCheckBox(self.tab_otras)
        self.chbox_stenger_oi.setObjectName(u"chbox_stenger_oi")

        self.horizontalLayout_stenger.addWidget(self.chbox_stenger_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_stenger)

        self.horizontalLayout_sisi = QHBoxLayout()
        self.horizontalLayout_sisi.setObjectName(u"horizontalLayout_sisi")
        self.label_67 = QLabel(self.tab_otras)
        self.label_67.setObjectName(u"label_67")

        self.horizontalLayout_sisi.addWidget(self.label_67)

        self.label_68 = QLabel(self.tab_otras)
        self.label_68.setObjectName(u"label_68")

        self.horizontalLayout_sisi.addWidget(self.label_68)

        self.spbox_sisi_od = QSpinBox(self.tab_otras)
        self.spbox_sisi_od.setObjectName(u"spbox_sisi_od")
        self.spbox_sisi_od.setMaximum(100)
        self.spbox_sisi_od.setSingleStep(5)

        self.horizontalLayout_sisi.addWidget(self.spbox_sisi_od)

        self.label_69 = QLabel(self.tab_otras)
        self.label_69.setObjectName(u"label_69")

        self.horizontalLayout_sisi.addWidget(self.label_69)

        self.spbox_sisi_oi = QSpinBox(self.tab_otras)
        self.spbox_sisi_oi.setObjectName(u"spbox_sisi_oi")
        self.spbox_sisi_oi.setMaximum(100)
        self.spbox_sisi_oi.setSingleStep(5)

        self.horizontalLayout_sisi.addWidget(self.spbox_sisi_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_sisi)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)


        self.verticalLayout_tab2.addLayout(self.horizontalLayout_3)

        self.label_63 = QLabel(self.tab_otras)
        self.label_63.setObjectName(u"label_63")
        self.label_63.setTextFormat(Qt.AutoText)
        self.label_63.setWordWrap(True)

        self.verticalLayout_tab2.addWidget(self.label_63)

        self.tabWidget.addTab(self.tab_otras, "")
        self.tab_reflejos = QWidget()
        self.tab_reflejos.setObjectName(u"tab_reflejos")
        self.verticalLayout_tab3 = QVBoxLayout(self.tab_reflejos)
        self.verticalLayout_tab3.setObjectName(u"verticalLayout_tab3")
        self.label_reflex_title = QLabel(self.tab_reflejos)
        self.label_reflex_title.setObjectName(u"label_reflex_title")
        self.label_reflex_title.setAlignment(Qt.AlignCenter)

        self.verticalLayout_tab3.addWidget(self.label_reflex_title)

        self.gridLayout_reflex = QGridLayout()
        self.gridLayout_reflex.setObjectName(u"gridLayout_reflex")
        self.label_reflex_od = QLabel(self.tab_reflejos)
        self.label_reflex_od.setObjectName(u"label_reflex_od")
        self.label_reflex_od.setAlignment(Qt.AlignCenter)

        self.gridLayout_reflex.addWidget(self.label_reflex_od, 0, 1, 1, 2)

        self.label_reflex_oi = QLabel(self.tab_reflejos)
        self.label_reflex_oi.setObjectName(u"label_reflex_oi")
        self.label_reflex_oi.setAlignment(Qt.AlignCenter)

        self.gridLayout_reflex.addWidget(self.label_reflex_oi, 0, 3, 1, 2)

        self.label_reflex_freq_header = QLabel(self.tab_reflejos)
        self.label_reflex_freq_header.setObjectName(u"label_reflex_freq_header")

        self.gridLayout_reflex.addWidget(self.label_reflex_freq_header, 1, 0, 1, 1)

        self.label_reflex_ipsi_od = QLabel(self.tab_reflejos)
        self.label_reflex_ipsi_od.setObjectName(u"label_reflex_ipsi_od")
        self.label_reflex_ipsi_od.setAlignment(Qt.AlignCenter)

        self.gridLayout_reflex.addWidget(self.label_reflex_ipsi_od, 1, 1, 1, 1)

        self.label_reflex_contra_od = QLabel(self.tab_reflejos)
        self.label_reflex_contra_od.setObjectName(u"label_reflex_contra_od")
        self.label_reflex_contra_od.setAlignment(Qt.AlignCenter)

        self.gridLayout_reflex.addWidget(self.label_reflex_contra_od, 1, 2, 1, 1)

        self.label_reflex_ipsi_oi = QLabel(self.tab_reflejos)
        self.label_reflex_ipsi_oi.setObjectName(u"label_reflex_ipsi_oi")
        self.label_reflex_ipsi_oi.setAlignment(Qt.AlignCenter)

        self.gridLayout_reflex.addWidget(self.label_reflex_ipsi_oi, 1, 3, 1, 1)

        self.label_reflex_contra_oi = QLabel(self.tab_reflejos)
        self.label_reflex_contra_oi.setObjectName(u"label_reflex_contra_oi")
        self.label_reflex_contra_oi.setAlignment(Qt.AlignCenter)

        self.gridLayout_reflex.addWidget(self.label_reflex_contra_oi, 1, 4, 1, 1)

        self.label_reflex_f500 = QLabel(self.tab_reflejos)
        self.label_reflex_f500.setObjectName(u"label_reflex_f500")

        self.gridLayout_reflex.addWidget(self.label_reflex_f500, 2, 0, 1, 1)

        self.spbox_reflex_ipsi_od_0 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_od_0.setObjectName(u"spbox_reflex_ipsi_od_0")
        self.spbox_reflex_ipsi_od_0.setMaximum(130)
        self.spbox_reflex_ipsi_od_0.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_od_0, 2, 1, 1, 1)

        self.spbox_reflex_contra_od_0 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_od_0.setObjectName(u"spbox_reflex_contra_od_0")
        self.spbox_reflex_contra_od_0.setMaximum(130)
        self.spbox_reflex_contra_od_0.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_od_0, 2, 2, 1, 1)

        self.spbox_reflex_ipsi_oi_0 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_oi_0.setObjectName(u"spbox_reflex_ipsi_oi_0")
        self.spbox_reflex_ipsi_oi_0.setMaximum(130)
        self.spbox_reflex_ipsi_oi_0.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_oi_0, 2, 3, 1, 1)

        self.spbox_reflex_contra_oi_0 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_oi_0.setObjectName(u"spbox_reflex_contra_oi_0")
        self.spbox_reflex_contra_oi_0.setMaximum(130)
        self.spbox_reflex_contra_oi_0.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_oi_0, 2, 4, 1, 1)

        self.label_reflex_f1000 = QLabel(self.tab_reflejos)
        self.label_reflex_f1000.setObjectName(u"label_reflex_f1000")

        self.gridLayout_reflex.addWidget(self.label_reflex_f1000, 3, 0, 1, 1)

        self.spbox_reflex_ipsi_od_1 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_od_1.setObjectName(u"spbox_reflex_ipsi_od_1")
        self.spbox_reflex_ipsi_od_1.setMaximum(130)
        self.spbox_reflex_ipsi_od_1.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_od_1, 3, 1, 1, 1)

        self.spbox_reflex_contra_od_1 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_od_1.setObjectName(u"spbox_reflex_contra_od_1")
        self.spbox_reflex_contra_od_1.setMaximum(130)
        self.spbox_reflex_contra_od_1.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_od_1, 3, 2, 1, 1)

        self.spbox_reflex_ipsi_oi_1 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_oi_1.setObjectName(u"spbox_reflex_ipsi_oi_1")
        self.spbox_reflex_ipsi_oi_1.setMaximum(130)
        self.spbox_reflex_ipsi_oi_1.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_oi_1, 3, 3, 1, 1)

        self.spbox_reflex_contra_oi_1 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_oi_1.setObjectName(u"spbox_reflex_contra_oi_1")
        self.spbox_reflex_contra_oi_1.setMaximum(130)
        self.spbox_reflex_contra_oi_1.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_oi_1, 3, 4, 1, 1)

        self.label_reflex_f2000 = QLabel(self.tab_reflejos)
        self.label_reflex_f2000.setObjectName(u"label_reflex_f2000")

        self.gridLayout_reflex.addWidget(self.label_reflex_f2000, 4, 0, 1, 1)

        self.spbox_reflex_ipsi_od_2 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_od_2.setObjectName(u"spbox_reflex_ipsi_od_2")
        self.spbox_reflex_ipsi_od_2.setMaximum(130)
        self.spbox_reflex_ipsi_od_2.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_od_2, 4, 1, 1, 1)

        self.spbox_reflex_contra_od_2 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_od_2.setObjectName(u"spbox_reflex_contra_od_2")
        self.spbox_reflex_contra_od_2.setMaximum(130)
        self.spbox_reflex_contra_od_2.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_od_2, 4, 2, 1, 1)

        self.spbox_reflex_ipsi_oi_2 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_oi_2.setObjectName(u"spbox_reflex_ipsi_oi_2")
        self.spbox_reflex_ipsi_oi_2.setMaximum(130)
        self.spbox_reflex_ipsi_oi_2.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_oi_2, 4, 3, 1, 1)

        self.spbox_reflex_contra_oi_2 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_oi_2.setObjectName(u"spbox_reflex_contra_oi_2")
        self.spbox_reflex_contra_oi_2.setMaximum(130)
        self.spbox_reflex_contra_oi_2.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_oi_2, 4, 4, 1, 1)

        self.label_reflex_f4000 = QLabel(self.tab_reflejos)
        self.label_reflex_f4000.setObjectName(u"label_reflex_f4000")

        self.gridLayout_reflex.addWidget(self.label_reflex_f4000, 5, 0, 1, 1)

        self.spbox_reflex_ipsi_od_3 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_od_3.setObjectName(u"spbox_reflex_ipsi_od_3")
        self.spbox_reflex_ipsi_od_3.setMaximum(130)
        self.spbox_reflex_ipsi_od_3.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_od_3, 5, 1, 1, 1)

        self.spbox_reflex_contra_od_3 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_od_3.setObjectName(u"spbox_reflex_contra_od_3")
        self.spbox_reflex_contra_od_3.setMaximum(130)
        self.spbox_reflex_contra_od_3.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_od_3, 5, 2, 1, 1)

        self.spbox_reflex_ipsi_oi_3 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_ipsi_oi_3.setObjectName(u"spbox_reflex_ipsi_oi_3")
        self.spbox_reflex_ipsi_oi_3.setMaximum(130)
        self.spbox_reflex_ipsi_oi_3.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_ipsi_oi_3, 5, 3, 1, 1)

        self.spbox_reflex_contra_oi_3 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_oi_3.setObjectName(u"spbox_reflex_contra_oi_3")
        self.spbox_reflex_contra_oi_3.setMaximum(130)
        self.spbox_reflex_contra_oi_3.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_oi_3, 5, 4, 1, 1)

        self.label_reflex_wn = QLabel(self.tab_reflejos)
        self.label_reflex_wn.setObjectName(u"label_reflex_wn")

        self.gridLayout_reflex.addWidget(self.label_reflex_wn, 6, 0, 1, 1)

        self.spbox_reflex_contra_od_4 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_od_4.setObjectName(u"spbox_reflex_contra_od_4")
        self.spbox_reflex_contra_od_4.setMaximum(130)
        self.spbox_reflex_contra_od_4.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_od_4, 6, 2, 1, 1)

        self.spbox_reflex_contra_oi_4 = QSpinBox(self.tab_reflejos)
        self.spbox_reflex_contra_oi_4.setObjectName(u"spbox_reflex_contra_oi_4")
        self.spbox_reflex_contra_oi_4.setMaximum(130)
        self.spbox_reflex_contra_oi_4.setSingleStep(5)

        self.gridLayout_reflex.addWidget(self.spbox_reflex_contra_oi_4, 6, 4, 1, 1)


        self.verticalLayout_tab3.addLayout(self.gridLayout_reflex)

        self.verticalSpacer_reflex = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_tab3.addItem(self.verticalSpacer_reflex)

        self.tabWidget.addTab(self.tab_reflejos, "")
        self.tab_etf = QWidget()
        self.tab_etf.setObjectName(u"tab_etf")
        self.verticalLayout_tab4 = QVBoxLayout(self.tab_etf)
        self.verticalLayout_tab4.setObjectName(u"verticalLayout_tab4")
        self.label_etf_title = QLabel(self.tab_etf)
        self.label_etf_title.setObjectName(u"label_etf_title")
        self.label_etf_title.setAlignment(Qt.AlignCenter)

        self.verticalLayout_tab4.addWidget(self.label_etf_title)

        self.horizontalLayout_etf_od = QHBoxLayout()
        self.horizontalLayout_etf_od.setObjectName(u"horizontalLayout_etf_od")
        self.label_etf_od = QLabel(self.tab_etf)
        self.label_etf_od.setObjectName(u"label_etf_od")

        self.horizontalLayout_etf_od.addWidget(self.label_etf_od)

        self.cb_etf_od = QComboBox(self.tab_etf)
        self.cb_etf_od.addItem("")
        self.cb_etf_od.addItem("")
        self.cb_etf_od.addItem("")
        self.cb_etf_od.addItem("")
        self.cb_etf_od.setObjectName(u"cb_etf_od")

        self.horizontalLayout_etf_od.addWidget(self.cb_etf_od)


        self.verticalLayout_tab4.addLayout(self.horizontalLayout_etf_od)

        self.horizontalLayout_etf_oi = QHBoxLayout()
        self.horizontalLayout_etf_oi.setObjectName(u"horizontalLayout_etf_oi")
        self.label_etf_oi = QLabel(self.tab_etf)
        self.label_etf_oi.setObjectName(u"label_etf_oi")

        self.horizontalLayout_etf_oi.addWidget(self.label_etf_oi)

        self.cb_etf_oi = QComboBox(self.tab_etf)
        self.cb_etf_oi.addItem("")
        self.cb_etf_oi.addItem("")
        self.cb_etf_oi.addItem("")
        self.cb_etf_oi.addItem("")
        self.cb_etf_oi.setObjectName(u"cb_etf_oi")

        self.horizontalLayout_etf_oi.addWidget(self.cb_etf_oi)


        self.verticalLayout_tab4.addLayout(self.horizontalLayout_etf_oi)

        self.verticalSpacer_etf = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_tab4.addItem(self.verticalSpacer_etf)

        self.tabWidget.addTab(self.tab_etf, "")
        self.tab_historia = QWidget()
        self.tab_historia.setObjectName(u"tab_historia")
        self.verticalLayout_tab5 = QVBoxLayout(self.tab_historia)
        self.verticalLayout_tab5.setObjectName(u"verticalLayout_tab5")
        self.label_historia_title = QLabel(self.tab_historia)
        self.label_historia_title.setObjectName(u"label_historia_title")
        self.label_historia_title.setAlignment(Qt.AlignCenter)

        self.verticalLayout_tab5.addWidget(self.label_historia_title)

        self.gridLayout_historia = QGridLayout()
        self.gridLayout_historia.setObjectName(u"gridLayout_historia")
        self.chbox_hist_hipoacusia_familiar = QCheckBox(self.tab_historia)
        self.chbox_hist_hipoacusia_familiar.setObjectName(u"chbox_hist_hipoacusia_familiar")

        self.gridLayout_historia.addWidget(self.chbox_hist_hipoacusia_familiar, 0, 0, 1, 1)

        self.chbox_hist_ototoxicos = QCheckBox(self.tab_historia)
        self.chbox_hist_ototoxicos.setObjectName(u"chbox_hist_ototoxicos")

        self.gridLayout_historia.addWidget(self.chbox_hist_ototoxicos, 0, 1, 1, 1)

        self.chbox_hist_trauma_acustico = QCheckBox(self.tab_historia)
        self.chbox_hist_trauma_acustico.setObjectName(u"chbox_hist_trauma_acustico")

        self.gridLayout_historia.addWidget(self.chbox_hist_trauma_acustico, 1, 0, 1, 1)

        self.chbox_hist_otitis = QCheckBox(self.tab_historia)
        self.chbox_hist_otitis.setObjectName(u"chbox_hist_otitis")

        self.gridLayout_historia.addWidget(self.chbox_hist_otitis, 1, 1, 1, 1)

        self.chbox_hist_meningitis = QCheckBox(self.tab_historia)
        self.chbox_hist_meningitis.setObjectName(u"chbox_hist_meningitis")

        self.gridLayout_historia.addWidget(self.chbox_hist_meningitis, 2, 0, 1, 1)

        self.chbox_hist_tce = QCheckBox(self.tab_historia)
        self.chbox_hist_tce.setObjectName(u"chbox_hist_tce")

        self.gridLayout_historia.addWidget(self.chbox_hist_tce, 2, 1, 1, 1)

        self.chbox_hist_diabetes = QCheckBox(self.tab_historia)
        self.chbox_hist_diabetes.setObjectName(u"chbox_hist_diabetes")

        self.gridLayout_historia.addWidget(self.chbox_hist_diabetes, 3, 0, 1, 1)

        self.chbox_hist_hta = QCheckBox(self.tab_historia)
        self.chbox_hist_hta.setObjectName(u"chbox_hist_hta")

        self.gridLayout_historia.addWidget(self.chbox_hist_hta, 3, 1, 1, 1)


        self.verticalLayout_tab5.addLayout(self.gridLayout_historia)

        self.horizontalLayout_medicamentos = QHBoxLayout()
        self.horizontalLayout_medicamentos.setObjectName(u"horizontalLayout_medicamentos")
        self.label_medicamentos = QLabel(self.tab_historia)
        self.label_medicamentos.setObjectName(u"label_medicamentos")

        self.horizontalLayout_medicamentos.addWidget(self.label_medicamentos)

        self.led_medicamentos = QLineEdit(self.tab_historia)
        self.led_medicamentos.setObjectName(u"led_medicamentos")

        self.horizontalLayout_medicamentos.addWidget(self.led_medicamentos)


        self.verticalLayout_tab5.addLayout(self.horizontalLayout_medicamentos)

        self.horizontalLayout_cirugias = QHBoxLayout()
        self.horizontalLayout_cirugias.setObjectName(u"horizontalLayout_cirugias")
        self.label_cirugias = QLabel(self.tab_historia)
        self.label_cirugias.setObjectName(u"label_cirugias")

        self.horizontalLayout_cirugias.addWidget(self.label_cirugias)

        self.led_cirugias = QLineEdit(self.tab_historia)
        self.led_cirugias.setObjectName(u"led_cirugias")

        self.horizontalLayout_cirugias.addWidget(self.led_cirugias)


        self.verticalLayout_tab5.addLayout(self.horizontalLayout_cirugias)

        self.label_otros_antecedentes = QLabel(self.tab_historia)
        self.label_otros_antecedentes.setObjectName(u"label_otros_antecedentes")

        self.verticalLayout_tab5.addWidget(self.label_otros_antecedentes)

        self.txt_otros_antecedentes = QTextEdit(self.tab_historia)
        self.txt_otros_antecedentes.setObjectName(u"txt_otros_antecedentes")

        self.verticalLayout_tab5.addWidget(self.txt_otros_antecedentes)

        self.tabWidget.addTab(self.tab_historia, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer)

        self.btn_cancel = QPushButton(generator_audio)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.horizontalLayout_11.addWidget(self.btn_cancel)

        self.btn_create = QPushButton(generator_audio)
        self.btn_create.setObjectName(u"btn_create")

        self.horizontalLayout_11.addWidget(self.btn_create)


        self.verticalLayout.addLayout(self.horizontalLayout_11)

        QWidget.setTabOrder(self.spbox_a_od_0, self.spbox_a_od_1)
        QWidget.setTabOrder(self.spbox_a_od_1, self.spbox_a_od_2)
        QWidget.setTabOrder(self.spbox_a_od_2, self.spbox_a_od_3)
        QWidget.setTabOrder(self.spbox_a_od_3, self.spbox_a_od_4)
        QWidget.setTabOrder(self.spbox_a_od_4, self.spbox_a_od_5)
        QWidget.setTabOrder(self.spbox_a_od_5, self.spbox_a_od_6)
        QWidget.setTabOrder(self.spbox_a_od_6, self.spbox_a_od_7)
        QWidget.setTabOrder(self.spbox_a_od_7, self.spbox_a_od_8)
        QWidget.setTabOrder(self.spbox_a_od_8, self.spbox_a_oi_0)
        QWidget.setTabOrder(self.spbox_a_oi_0, self.spbox_a_oi_1)
        QWidget.setTabOrder(self.spbox_a_oi_1, self.spbox_a_oi_2)
        QWidget.setTabOrder(self.spbox_a_oi_2, self.spbox_a_oi_3)
        QWidget.setTabOrder(self.spbox_a_oi_3, self.spbox_a_oi_4)
        QWidget.setTabOrder(self.spbox_a_oi_4, self.spbox_a_oi_5)
        QWidget.setTabOrder(self.spbox_a_oi_5, self.spbox_a_oi_6)
        QWidget.setTabOrder(self.spbox_a_oi_6, self.spbox_a_oi_7)
        QWidget.setTabOrder(self.spbox_a_oi_7, self.spbox_a_oi_8)
        QWidget.setTabOrder(self.spbox_a_oi_8, self.chbox_peg_od)
        QWidget.setTabOrder(self.chbox_peg_od, self.chbox_peg_oi)
        QWidget.setTabOrder(self.chbox_peg_oi, self.spbox_o_od_0)
        QWidget.setTabOrder(self.spbox_o_od_0, self.spbox_o_od_1)
        QWidget.setTabOrder(self.spbox_o_od_1, self.spbox_o_od_2)
        QWidget.setTabOrder(self.spbox_o_od_2, self.spbox_o_od_3)
        QWidget.setTabOrder(self.spbox_o_od_3, self.spbox_o_od_4)
        QWidget.setTabOrder(self.spbox_o_od_4, self.spbox_o_od_5)
        QWidget.setTabOrder(self.spbox_o_od_5, self.spbox_o_od_6)
        QWidget.setTabOrder(self.spbox_o_od_6, self.spbox_o_od_7)
        QWidget.setTabOrder(self.spbox_o_od_7, self.spbox_o_od_8)
        QWidget.setTabOrder(self.spbox_o_od_8, self.spbox_o_oi_0)
        QWidget.setTabOrder(self.spbox_o_oi_0, self.spbox_o_oi_1)
        QWidget.setTabOrder(self.spbox_o_oi_1, self.spbox_o_oi_2)
        QWidget.setTabOrder(self.spbox_o_oi_2, self.spbox_o_oi_3)
        QWidget.setTabOrder(self.spbox_o_oi_3, self.spbox_o_oi_4)
        QWidget.setTabOrder(self.spbox_o_oi_4, self.spbox_o_oi_5)
        QWidget.setTabOrder(self.spbox_o_oi_5, self.spbox_o_oi_6)
        QWidget.setTabOrder(self.spbox_o_oi_6, self.spbox_o_oi_7)
        QWidget.setTabOrder(self.spbox_o_oi_7, self.spbox_o_oi_8)
        QWidget.setTabOrder(self.spbox_o_oi_8, self.chbox_ldl_od)
        QWidget.setTabOrder(self.chbox_ldl_od, self.chbox_ldl_oi)
        QWidget.setTabOrder(self.chbox_ldl_oi, self.spbox_ldl_od_0)
        QWidget.setTabOrder(self.spbox_ldl_od_0, self.spbox_ldl_od_1)
        QWidget.setTabOrder(self.spbox_ldl_od_1, self.spbox_ldl_od_2)
        QWidget.setTabOrder(self.spbox_ldl_od_2, self.spbox_ldl_od_3)
        QWidget.setTabOrder(self.spbox_ldl_od_3, self.spbox_ldl_od_4)
        QWidget.setTabOrder(self.spbox_ldl_od_4, self.spbox_ldl_od_5)
        QWidget.setTabOrder(self.spbox_ldl_od_5, self.spbox_ldl_od_6)
        QWidget.setTabOrder(self.spbox_ldl_od_6, self.spbox_ldl_od_7)
        QWidget.setTabOrder(self.spbox_ldl_od_7, self.spbox_ldl_od_8)
        QWidget.setTabOrder(self.spbox_ldl_od_8, self.spbox_ldl_oi_0)
        QWidget.setTabOrder(self.spbox_ldl_oi_0, self.spbox_ldl_oi_1)
        QWidget.setTabOrder(self.spbox_ldl_oi_1, self.spbox_ldl_oi_2)
        QWidget.setTabOrder(self.spbox_ldl_oi_2, self.spbox_ldl_oi_3)
        QWidget.setTabOrder(self.spbox_ldl_oi_3, self.spbox_ldl_oi_4)
        QWidget.setTabOrder(self.spbox_ldl_oi_4, self.spbox_ldl_oi_5)
        QWidget.setTabOrder(self.spbox_ldl_oi_5, self.spbox_ldl_oi_6)
        QWidget.setTabOrder(self.spbox_ldl_oi_6, self.spbox_ldl_oi_7)
        QWidget.setTabOrder(self.spbox_ldl_oi_7, self.spbox_ldl_oi_8)
        QWidget.setTabOrder(self.spbox_ldl_oi_8, self.spbox_sdt_od_0)
        QWidget.setTabOrder(self.spbox_sdt_od_0, self.spbox_srt_od_0)
        QWidget.setTabOrder(self.spbox_srt_od_0, self.spbox_umd_od_0)
        QWidget.setTabOrder(self.spbox_umd_od_0, self.spbox_umd_od_1)
        QWidget.setTabOrder(self.spbox_umd_od_1, self.spbox_sdt_oi_0)
        QWidget.setTabOrder(self.spbox_sdt_oi_0, self.spbox_srt_oi_0)
        QWidget.setTabOrder(self.spbox_srt_oi_0, self.spbox_umd_oi_0)
        QWidget.setTabOrder(self.spbox_umd_oi_0, self.spbox_umd_oi_1)
        QWidget.setTabOrder(self.spbox_umd_oi_1, self.spbox_reflex_ipsi_od_0)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_od_0, self.spbox_reflex_ipsi_od_1)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_od_1, self.spbox_reflex_ipsi_od_2)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_od_2, self.spbox_reflex_ipsi_od_3)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_od_3, self.spbox_reflex_contra_od_0)
        QWidget.setTabOrder(self.spbox_reflex_contra_od_0, self.spbox_reflex_contra_od_1)
        QWidget.setTabOrder(self.spbox_reflex_contra_od_1, self.spbox_reflex_contra_od_2)
        QWidget.setTabOrder(self.spbox_reflex_contra_od_2, self.spbox_reflex_contra_od_3)
        QWidget.setTabOrder(self.spbox_reflex_contra_od_3, self.spbox_reflex_ipsi_oi_0)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_oi_0, self.spbox_reflex_ipsi_oi_1)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_oi_1, self.spbox_reflex_ipsi_oi_2)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_oi_2, self.spbox_reflex_ipsi_oi_3)
        QWidget.setTabOrder(self.spbox_reflex_ipsi_oi_3, self.spbox_reflex_contra_oi_0)
        QWidget.setTabOrder(self.spbox_reflex_contra_oi_0, self.spbox_reflex_contra_oi_1)
        QWidget.setTabOrder(self.spbox_reflex_contra_oi_1, self.spbox_reflex_contra_oi_2)
        QWidget.setTabOrder(self.spbox_reflex_contra_oi_2, self.spbox_reflex_contra_oi_3)
        QWidget.setTabOrder(self.spbox_reflex_contra_oi_3, self.cb_etf_od)
        QWidget.setTabOrder(self.cb_etf_od, self.cb_etf_oi)
        QWidget.setTabOrder(self.cb_etf_oi, self.spbox_reflex_contra_od_4)
        QWidget.setTabOrder(self.spbox_reflex_contra_od_4, self.spbox_reflex_contra_oi_4)
        QWidget.setTabOrder(self.spbox_reflex_contra_oi_4, self.chbox_hist_hipoacusia_familiar)
        QWidget.setTabOrder(self.chbox_hist_hipoacusia_familiar, self.chbox_hist_ototoxicos)
        QWidget.setTabOrder(self.chbox_hist_ototoxicos, self.chbox_hist_trauma_acustico)
        QWidget.setTabOrder(self.chbox_hist_trauma_acustico, self.chbox_hist_otitis)
        QWidget.setTabOrder(self.chbox_hist_otitis, self.chbox_hist_meningitis)
        QWidget.setTabOrder(self.chbox_hist_meningitis, self.chbox_hist_tce)
        QWidget.setTabOrder(self.chbox_hist_tce, self.chbox_hist_diabetes)
        QWidget.setTabOrder(self.chbox_hist_diabetes, self.chbox_hist_hta)
        QWidget.setTabOrder(self.chbox_hist_hta, self.led_medicamentos)
        QWidget.setTabOrder(self.led_medicamentos, self.led_cirugias)
        QWidget.setTabOrder(self.led_cirugias, self.txt_otros_antecedentes)

        self.retranslateUi(generator_audio)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(generator_audio)
    # setupUi

    def retranslateUi(self, generator_audio):
        generator_audio.setWindowTitle(QCoreApplication.translate("generator_audio", u"Form", None))
        self.label_64.setText(QCoreApplication.translate("generator_audio", u"Nombre:", None))
        self.pushButton.setText(QCoreApplication.translate("generator_audio", u"Generar", None))
        self.label_65.setText(QCoreApplication.translate("generator_audio", u"Edad", None))
        self.label_66.setText(QCoreApplication.translate("generator_audio", u"Sexo", None))
        self.radioButton.setText(QCoreApplication.translate("generator_audio", u"Masculino", None))
        self.radioButton_2.setText(QCoreApplication.translate("generator_audio", u"Femenino", None))
        self.label_10.setText(QCoreApplication.translate("generator_audio", u"Frecuencia", None))
        self.label_2.setText(QCoreApplication.translate("generator_audio", u"250", None))
        self.label_11.setText(QCoreApplication.translate("generator_audio", u"Umbral OD", None))
        self.label_8.setText(QCoreApplication.translate("generator_audio", u"6000", None))
        self.label_9.setText(QCoreApplication.translate("generator_audio", u"8000", None))
        self.label_6.setText(QCoreApplication.translate("generator_audio", u"3000", None))
        self.label_13.setText(QCoreApplication.translate("generator_audio", u"A\u00e9rea", None))
        self.label_12.setText(QCoreApplication.translate("generator_audio", u"Umbral OI", None))
        self.label.setText(QCoreApplication.translate("generator_audio", u"125", None))
        self.label_7.setText(QCoreApplication.translate("generator_audio", u"4000", None))
        self.label_5.setText(QCoreApplication.translate("generator_audio", u"2000", None))
        self.label_4.setText(QCoreApplication.translate("generator_audio", u"1000", None))
        self.label_3.setText(QCoreApplication.translate("generator_audio", u"500", None))
        self.label_41.setText(QCoreApplication.translate("generator_audio", u"\u00d3seas pegadas a A\u00e9reas:", None))
        self.chbox_peg_od.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.chbox_peg_oi.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.label_14.setText(QCoreApplication.translate("generator_audio", u"1000", None))
        self.label_15.setText(QCoreApplication.translate("generator_audio", u"Frecuencia", None))
        self.label_16.setText(QCoreApplication.translate("generator_audio", u"Umbral OD", None))
        self.label_17.setText(QCoreApplication.translate("generator_audio", u"125", None))
        self.label_18.setText(QCoreApplication.translate("generator_audio", u"2000", None))
        self.label_19.setText(QCoreApplication.translate("generator_audio", u"8000", None))
        self.label_20.setText(QCoreApplication.translate("generator_audio", u"Umbral OI", None))
        self.label_21.setText(QCoreApplication.translate("generator_audio", u"250", None))
        self.label_22.setText(QCoreApplication.translate("generator_audio", u"3000", None))
        self.label_23.setText(QCoreApplication.translate("generator_audio", u"500", None))
        self.label_24.setText(QCoreApplication.translate("generator_audio", u"6000", None))
        self.label_25.setText(QCoreApplication.translate("generator_audio", u"4000", None))
        self.label_26.setText(QCoreApplication.translate("generator_audio", u"\u00d3sea", None))
        self.label_42.setText(QCoreApplication.translate("generator_audio", u"Posee LDL en:", None))
        self.chbox_ldl_od.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.chbox_ldl_oi.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.label_33.setText(QCoreApplication.translate("generator_audio", u"Umbral OI", None))
        self.label_35.setText(QCoreApplication.translate("generator_audio", u"3000", None))
        self.label_27.setText(QCoreApplication.translate("generator_audio", u"1000", None))
        self.label_30.setText(QCoreApplication.translate("generator_audio", u"125", None))
        self.label_38.setText(QCoreApplication.translate("generator_audio", u"4000", None))
        self.label_29.setText(QCoreApplication.translate("generator_audio", u"Umbral OD", None))
        self.label_37.setText(QCoreApplication.translate("generator_audio", u"6000", None))
        self.label_34.setText(QCoreApplication.translate("generator_audio", u"250", None))
        self.label_32.setText(QCoreApplication.translate("generator_audio", u"8000", None))
        self.label_39.setText(QCoreApplication.translate("generator_audio", u"LDL", None))
        self.label_31.setText(QCoreApplication.translate("generator_audio", u"2000", None))
        self.label_36.setText(QCoreApplication.translate("generator_audio", u"500", None))
        self.label_28.setText(QCoreApplication.translate("generator_audio", u"Frecuencia", None))
        self.label_40.setText(QCoreApplication.translate("generator_audio", u"Nota: Todos los datos deben ser llenados, si un umbral no se toma o no existe debe poner 130", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_audiometria), QCoreApplication.translate("generator_audio", u"Audiometr\u00eda", None))
        self.label_43.setText(QCoreApplication.translate("generator_audio", u"LogoAudiometr\u00eda", None))
        self.label_51.setText(QCoreApplication.translate("generator_audio", u"%", None))
        self.label_47.setText(QCoreApplication.translate("generator_audio", u"UMD (max)", None))
        self.label_45.setText(QCoreApplication.translate("generator_audio", u"SDT", None))
        self.label_49.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.label_50.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.label_46.setText(QCoreApplication.translate("generator_audio", u"SRT", None))
        self.label_48.setText(QCoreApplication.translate("generator_audio", u"dB", None))
        self.label_52.setText(QCoreApplication.translate("generator_audio", u"dB", None))
        self.label_53.setText(QCoreApplication.translate("generator_audio", u"%", None))
        self.label_54.setText(QCoreApplication.translate("generator_audio", u"50", None))
        self.label_55.setText(QCoreApplication.translate("generator_audio", u"50", None))
        self.label_56.setText(QCoreApplication.translate("generator_audio", u"0", None))
        self.label_57.setText(QCoreApplication.translate("generator_audio", u"0", None))
        self.label_44.setText(QCoreApplication.translate("generator_audio", u"Otras Pruebas", None))
        self.label_58.setText(QCoreApplication.translate("generator_audio", u"Reclutamiento", None))
        self.chbox_recrut_od.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.chbox_recrut_oi.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.label_59.setText(QCoreApplication.translate("generator_audio", u"Deterioro", None))
        self.chbox_det_od.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.chbox_det_oi.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.label_60.setText(QCoreApplication.translate("generator_audio", u"Z", None))
        self.label_61.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.cb_z_od.setItemText(0, QCoreApplication.translate("generator_audio", u"A", None))
        self.cb_z_od.setItemText(1, QCoreApplication.translate("generator_audio", u"As", None))
        self.cb_z_od.setItemText(2, QCoreApplication.translate("generator_audio", u"Ad", None))
        self.cb_z_od.setItemText(3, QCoreApplication.translate("generator_audio", u"C", None))
        self.cb_z_od.setItemText(4, QCoreApplication.translate("generator_audio", u"Cs", None))
        self.cb_z_od.setItemText(5, QCoreApplication.translate("generator_audio", u"B", None))

        self.label_62.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.cb_z_oi.setItemText(0, QCoreApplication.translate("generator_audio", u"A", None))
        self.cb_z_oi.setItemText(1, QCoreApplication.translate("generator_audio", u"As", None))
        self.cb_z_oi.setItemText(2, QCoreApplication.translate("generator_audio", u"Ad", None))
        self.cb_z_oi.setItemText(3, QCoreApplication.translate("generator_audio", u"C", None))
        self.cb_z_oi.setItemText(4, QCoreApplication.translate("generator_audio", u"Cs", None))
        self.cb_z_oi.setItemText(5, QCoreApplication.translate("generator_audio", u"B", None))
        self.label_64.setText(QCoreApplication.translate("generator_audio", u"Fowler", None))
        self.cb_fowler_freq.setItemText(0, QCoreApplication.translate("generator_audio", u"125", None))
        self.cb_fowler_freq.setItemText(1, QCoreApplication.translate("generator_audio", u"250", None))
        self.cb_fowler_freq.setItemText(2, QCoreApplication.translate("generator_audio", u"500", None))
        self.cb_fowler_freq.setItemText(3, QCoreApplication.translate("generator_audio", u"1000", None))
        self.cb_fowler_freq.setItemText(4, QCoreApplication.translate("generator_audio", u"2000", None))
        self.cb_fowler_freq.setItemText(5, QCoreApplication.translate("generator_audio", u"3000", None))
        self.cb_fowler_freq.setItemText(6, QCoreApplication.translate("generator_audio", u"4000", None))
        self.cb_fowler_freq.setItemText(7, QCoreApplication.translate("generator_audio", u"6000", None))
        self.cb_fowler_freq.setItemText(8, QCoreApplication.translate("generator_audio", u"8000", None))
        self.label_65.setText(QCoreApplication.translate("generator_audio", u"Cortes", None))
        self.label_66.setText(QCoreApplication.translate("generator_audio", u"Stenger", None))
        self.chbox_stenger_od.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.chbox_stenger_oi.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.label_67.setText(QCoreApplication.translate("generator_audio", u"SISI %", None))
        self.label_68.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.label_69.setText(QCoreApplication.translate("generator_audio", u"OI", None))

        self.label_63.setText(QCoreApplication.translate("generator_audio", u"Nota: todos los valores deben ser rellenados si alguno no existe en db poner 130 y al porcentaje 0, en el caso de UMD solo poner el valor maximo de discriminaci\u00f3n", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_otras), QCoreApplication.translate("generator_audio", u"Otras Pruebas", None))
        self.label_reflex_title.setText(QCoreApplication.translate("generator_audio", u"Reflejos Ac\u00fasticos (dB HL) - dejar en 130 si est\u00e1 ausente. WN (ruido blanco) solo se toma en contralateral", None))
        self.label_reflex_od.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.label_reflex_oi.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.label_reflex_freq_header.setText(QCoreApplication.translate("generator_audio", u"Frecuencia (Hz)", None))
        self.label_reflex_ipsi_od.setText(QCoreApplication.translate("generator_audio", u"Ipsi", None))
        self.label_reflex_contra_od.setText(QCoreApplication.translate("generator_audio", u"Contra", None))
        self.label_reflex_ipsi_oi.setText(QCoreApplication.translate("generator_audio", u"Ipsi", None))
        self.label_reflex_contra_oi.setText(QCoreApplication.translate("generator_audio", u"Contra", None))
        self.label_reflex_f500.setText(QCoreApplication.translate("generator_audio", u"500", None))
        self.label_reflex_f1000.setText(QCoreApplication.translate("generator_audio", u"1000", None))
        self.label_reflex_f2000.setText(QCoreApplication.translate("generator_audio", u"2000", None))
        self.label_reflex_f4000.setText(QCoreApplication.translate("generator_audio", u"4000", None))
        self.label_reflex_wn.setText(QCoreApplication.translate("generator_audio", u"WN", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_reflejos), QCoreApplication.translate("generator_audio", u"Reflejos Ac\u00fasticos", None))
        self.label_etf_title.setText(QCoreApplication.translate("generator_audio", u"Funci\u00f3n Tubaria: Normal/Disfunci\u00f3n tubaria (membrana indemne, Valsalva/Toynbee) o Permeable/No permeable (membrana perforada, manometr\u00eda directa)", None))
        self.label_etf_od.setText(QCoreApplication.translate("generator_audio", u"OD", None))
        self.cb_etf_od.setItemText(0, QCoreApplication.translate("generator_audio", u"Normal", None))
        self.cb_etf_od.setItemText(1, QCoreApplication.translate("generator_audio", u"Disfunci\u00f3n tubaria", None))
        self.cb_etf_od.setItemText(2, QCoreApplication.translate("generator_audio", u"Permeable", None))
        self.cb_etf_od.setItemText(3, QCoreApplication.translate("generator_audio", u"No permeable", None))

        self.label_etf_oi.setText(QCoreApplication.translate("generator_audio", u"OI", None))
        self.cb_etf_oi.setItemText(0, QCoreApplication.translate("generator_audio", u"Normal", None))
        self.cb_etf_oi.setItemText(1, QCoreApplication.translate("generator_audio", u"Disfunci\u00f3n tubaria", None))
        self.cb_etf_oi.setItemText(2, QCoreApplication.translate("generator_audio", u"Permeable", None))
        self.cb_etf_oi.setItemText(3, QCoreApplication.translate("generator_audio", u"No permeable", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_etf), QCoreApplication.translate("generator_audio", u"Funci\u00f3n Tubaria", None))
        self.label_historia_title.setText(QCoreApplication.translate("generator_audio", u"Antecedentes relevantes para la anamnesis", None))
        self.chbox_hist_hipoacusia_familiar.setText(QCoreApplication.translate("generator_audio", u"Hipoacusia familiar", None))
        self.chbox_hist_ototoxicos.setText(QCoreApplication.translate("generator_audio", u"Exposici\u00f3n a otot\u00f3xicos", None))
        self.chbox_hist_trauma_acustico.setText(QCoreApplication.translate("generator_audio", u"Exposici\u00f3n a ruido / trauma ac\u00fastico", None))
        self.chbox_hist_otitis.setText(QCoreApplication.translate("generator_audio", u"Otitis media a repetici\u00f3n", None))
        self.chbox_hist_meningitis.setText(QCoreApplication.translate("generator_audio", u"Meningitis", None))
        self.chbox_hist_tce.setText(QCoreApplication.translate("generator_audio", u"Traumatismo craneoencef\u00e1lico", None))
        self.chbox_hist_diabetes.setText(QCoreApplication.translate("generator_audio", u"Diabetes", None))
        self.chbox_hist_hta.setText(QCoreApplication.translate("generator_audio", u"Hipertensi\u00f3n arterial", None))
        self.label_medicamentos.setText(QCoreApplication.translate("generator_audio", u"Medicamentos:", None))
        self.label_cirugias.setText(QCoreApplication.translate("generator_audio", u"Cirug\u00edas previas:", None))
        self.label_otros_antecedentes.setText(QCoreApplication.translate("generator_audio", u"Otros antecedentes relevantes:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_historia), QCoreApplication.translate("generator_audio", u"Historia Cl\u00ednica", None))
        self.btn_cancel.setText(QCoreApplication.translate("generator_audio", u"Cancelar", None))
        self.btn_create.setText(QCoreApplication.translate("generator_audio", u"Crear", None))
    # retranslateUi

