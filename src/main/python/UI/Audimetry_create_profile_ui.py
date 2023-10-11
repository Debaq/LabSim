# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Audimetry_create_profile.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
    QSpinBox, QVBoxLayout, QWidget)

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
        self.radioButton.setEnabled(False)

        self.horizontalLayout_10.addWidget(self.radioButton)

        self.radioButton_2 = QRadioButton(generator_audio)
        self.radioButton_2.setObjectName(u"radioButton_2")
        self.radioButton_2.setChecked(True)

        self.horizontalLayout_10.addWidget(self.radioButton_2)


        self.horizontalLayout_8.addLayout(self.horizontalLayout_10)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.spbox_a_oi_1 = QSpinBox(generator_audio)
        self.spbox_a_oi_1.setObjectName(u"spbox_a_oi_1")
        self.spbox_a_oi_1.setMaximum(120)
        self.spbox_a_oi_1.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_1, 2, 3, 1, 1)

        self.spbox_a_od_0 = QSpinBox(generator_audio)
        self.spbox_a_od_0.setObjectName(u"spbox_a_od_0")
        self.spbox_a_od_0.setMaximum(120)
        self.spbox_a_od_0.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_0, 1, 2, 1, 1)

        self.spbox_a_od_7 = QSpinBox(generator_audio)
        self.spbox_a_od_7.setObjectName(u"spbox_a_od_7")
        self.spbox_a_od_7.setMaximum(120)
        self.spbox_a_od_7.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_7, 1, 9, 1, 1)

        self.spbox_a_oi_6 = QSpinBox(generator_audio)
        self.spbox_a_oi_6.setObjectName(u"spbox_a_oi_6")
        self.spbox_a_oi_6.setMaximum(120)
        self.spbox_a_oi_6.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_6, 2, 8, 1, 1)

        self.spbox_a_oi_8 = QSpinBox(generator_audio)
        self.spbox_a_oi_8.setObjectName(u"spbox_a_oi_8")
        self.spbox_a_oi_8.setMaximum(120)
        self.spbox_a_oi_8.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_8, 2, 10, 1, 1)

        self.label_10 = QLabel(generator_audio)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout.addWidget(self.label_10, 0, 1, 1, 1)

        self.spbox_a_od_1 = QSpinBox(generator_audio)
        self.spbox_a_od_1.setObjectName(u"spbox_a_od_1")
        self.spbox_a_od_1.setMaximum(120)
        self.spbox_a_od_1.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_1, 1, 3, 1, 1)

        self.spbox_a_od_5 = QSpinBox(generator_audio)
        self.spbox_a_od_5.setObjectName(u"spbox_a_od_5")
        self.spbox_a_od_5.setMaximum(120)
        self.spbox_a_od_5.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_5, 1, 7, 1, 1)

        self.label_2 = QLabel(generator_audio)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 0, 3, 1, 1)

        self.label_11 = QLabel(generator_audio)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout.addWidget(self.label_11, 1, 1, 1, 1)

        self.label_8 = QLabel(generator_audio)
        self.label_8.setObjectName(u"label_8")

        self.gridLayout.addWidget(self.label_8, 0, 9, 1, 1)

        self.spbox_a_oi_2 = QSpinBox(generator_audio)
        self.spbox_a_oi_2.setObjectName(u"spbox_a_oi_2")
        self.spbox_a_oi_2.setMaximum(120)
        self.spbox_a_oi_2.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_2, 2, 4, 1, 1)

        self.spbox_a_od_8 = QSpinBox(generator_audio)
        self.spbox_a_od_8.setObjectName(u"spbox_a_od_8")
        self.spbox_a_od_8.setMaximum(120)
        self.spbox_a_od_8.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_8, 1, 10, 1, 1)

        self.label_9 = QLabel(generator_audio)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout.addWidget(self.label_9, 0, 10, 1, 1)

        self.spbox_a_oi_5 = QSpinBox(generator_audio)
        self.spbox_a_oi_5.setObjectName(u"spbox_a_oi_5")
        self.spbox_a_oi_5.setMaximum(120)
        self.spbox_a_oi_5.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_5, 2, 7, 1, 1)

        self.spbox_a_oi_3 = QSpinBox(generator_audio)
        self.spbox_a_oi_3.setObjectName(u"spbox_a_oi_3")
        self.spbox_a_oi_3.setMaximum(120)
        self.spbox_a_oi_3.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_3, 2, 5, 1, 1)

        self.label_6 = QLabel(generator_audio)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 0, 7, 1, 1)

        self.spbox_a_od_3 = QSpinBox(generator_audio)
        self.spbox_a_od_3.setObjectName(u"spbox_a_od_3")
        self.spbox_a_od_3.setMaximum(120)
        self.spbox_a_od_3.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_3, 1, 5, 1, 1)

        self.label_13 = QLabel(generator_audio)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout.addWidget(self.label_13, 0, 0, 3, 1)

        self.spbox_a_od_4 = QSpinBox(generator_audio)
        self.spbox_a_od_4.setObjectName(u"spbox_a_od_4")
        self.spbox_a_od_4.setMaximum(120)
        self.spbox_a_od_4.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_4, 1, 6, 1, 1)

        self.label_12 = QLabel(generator_audio)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout.addWidget(self.label_12, 2, 1, 1, 1)

        self.spbox_a_oi_0 = QSpinBox(generator_audio)
        self.spbox_a_oi_0.setObjectName(u"spbox_a_oi_0")
        self.spbox_a_oi_0.setMaximum(120)
        self.spbox_a_oi_0.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_0, 2, 2, 1, 1)

        self.label = QLabel(generator_audio)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 2, 1, 1)

        self.label_7 = QLabel(generator_audio)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 0, 8, 1, 1)

        self.spbox_a_oi_7 = QSpinBox(generator_audio)
        self.spbox_a_oi_7.setObjectName(u"spbox_a_oi_7")
        self.spbox_a_oi_7.setMaximum(120)
        self.spbox_a_oi_7.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_7, 2, 9, 1, 1)

        self.spbox_a_oi_4 = QSpinBox(generator_audio)
        self.spbox_a_oi_4.setObjectName(u"spbox_a_oi_4")
        self.spbox_a_oi_4.setMaximum(120)
        self.spbox_a_oi_4.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_oi_4, 2, 6, 1, 1)

        self.label_5 = QLabel(generator_audio)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 6, 1, 1)

        self.label_4 = QLabel(generator_audio)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 0, 5, 1, 1)

        self.spbox_a_od_6 = QSpinBox(generator_audio)
        self.spbox_a_od_6.setObjectName(u"spbox_a_od_6")
        self.spbox_a_od_6.setMaximum(120)
        self.spbox_a_od_6.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_6, 1, 8, 1, 1)

        self.spbox_a_od_2 = QSpinBox(generator_audio)
        self.spbox_a_od_2.setObjectName(u"spbox_a_od_2")
        self.spbox_a_od_2.setMaximum(120)
        self.spbox_a_od_2.setSingleStep(5)

        self.gridLayout.addWidget(self.spbox_a_od_2, 1, 4, 1, 1)

        self.label_3 = QLabel(generator_audio)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 4, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_41 = QLabel(generator_audio)
        self.label_41.setObjectName(u"label_41")

        self.horizontalLayout.addWidget(self.label_41)

        self.chbox_peg_od = QCheckBox(generator_audio)
        self.chbox_peg_od.setObjectName(u"chbox_peg_od")

        self.horizontalLayout.addWidget(self.chbox_peg_od)

        self.chbox_peg_oi = QCheckBox(generator_audio)
        self.chbox_peg_oi.setObjectName(u"chbox_peg_oi")

        self.horizontalLayout.addWidget(self.chbox_peg_oi)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_14 = QLabel(generator_audio)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_2.addWidget(self.label_14, 0, 5, 1, 1)

        self.label_15 = QLabel(generator_audio)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_2.addWidget(self.label_15, 0, 1, 1, 1)

        self.label_16 = QLabel(generator_audio)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_2.addWidget(self.label_16, 1, 1, 1, 1)

        self.label_17 = QLabel(generator_audio)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_2.addWidget(self.label_17, 0, 2, 1, 1)

        self.label_18 = QLabel(generator_audio)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_2.addWidget(self.label_18, 0, 6, 1, 1)

        self.label_19 = QLabel(generator_audio)
        self.label_19.setObjectName(u"label_19")

        self.gridLayout_2.addWidget(self.label_19, 0, 10, 1, 1)

        self.label_20 = QLabel(generator_audio)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_2.addWidget(self.label_20, 2, 1, 1, 1)

        self.label_21 = QLabel(generator_audio)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_2.addWidget(self.label_21, 0, 3, 1, 1)

        self.label_22 = QLabel(generator_audio)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_2.addWidget(self.label_22, 0, 7, 1, 1)

        self.label_23 = QLabel(generator_audio)
        self.label_23.setObjectName(u"label_23")

        self.gridLayout_2.addWidget(self.label_23, 0, 4, 1, 1)

        self.label_24 = QLabel(generator_audio)
        self.label_24.setObjectName(u"label_24")

        self.gridLayout_2.addWidget(self.label_24, 0, 9, 1, 1)

        self.label_25 = QLabel(generator_audio)
        self.label_25.setObjectName(u"label_25")

        self.gridLayout_2.addWidget(self.label_25, 0, 8, 1, 1)

        self.label_26 = QLabel(generator_audio)
        self.label_26.setObjectName(u"label_26")

        self.gridLayout_2.addWidget(self.label_26, 0, 0, 3, 1)

        self.spbox_o_od_0 = QSpinBox(generator_audio)
        self.spbox_o_od_0.setObjectName(u"spbox_o_od_0")
        self.spbox_o_od_0.setMaximum(120)
        self.spbox_o_od_0.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_0, 1, 2, 1, 1)

        self.spbox_o_od_1 = QSpinBox(generator_audio)
        self.spbox_o_od_1.setObjectName(u"spbox_o_od_1")
        self.spbox_o_od_1.setMaximum(120)
        self.spbox_o_od_1.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_1, 1, 3, 1, 1)

        self.spbox_o_od_2 = QSpinBox(generator_audio)
        self.spbox_o_od_2.setObjectName(u"spbox_o_od_2")
        self.spbox_o_od_2.setMaximum(120)
        self.spbox_o_od_2.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_2, 1, 4, 1, 1)

        self.spbox_o_od_3 = QSpinBox(generator_audio)
        self.spbox_o_od_3.setObjectName(u"spbox_o_od_3")
        self.spbox_o_od_3.setMaximum(120)
        self.spbox_o_od_3.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_3, 1, 5, 1, 1)

        self.spbox_o_od_4 = QSpinBox(generator_audio)
        self.spbox_o_od_4.setObjectName(u"spbox_o_od_4")
        self.spbox_o_od_4.setMaximum(120)
        self.spbox_o_od_4.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_4, 1, 6, 1, 1)

        self.spbox_o_od_5 = QSpinBox(generator_audio)
        self.spbox_o_od_5.setObjectName(u"spbox_o_od_5")
        self.spbox_o_od_5.setMaximum(120)
        self.spbox_o_od_5.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_5, 1, 7, 1, 1)

        self.spbox_o_od_6 = QSpinBox(generator_audio)
        self.spbox_o_od_6.setObjectName(u"spbox_o_od_6")
        self.spbox_o_od_6.setMaximum(120)
        self.spbox_o_od_6.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_6, 1, 8, 1, 1)

        self.spbox_o_od_7 = QSpinBox(generator_audio)
        self.spbox_o_od_7.setObjectName(u"spbox_o_od_7")
        self.spbox_o_od_7.setMaximum(120)
        self.spbox_o_od_7.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_7, 1, 9, 1, 1)

        self.spbox_o_od_8 = QSpinBox(generator_audio)
        self.spbox_o_od_8.setObjectName(u"spbox_o_od_8")
        self.spbox_o_od_8.setMaximum(120)
        self.spbox_o_od_8.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_od_8, 1, 10, 1, 1)

        self.spbox_o_oi_6 = QSpinBox(generator_audio)
        self.spbox_o_oi_6.setObjectName(u"spbox_o_oi_6")
        self.spbox_o_oi_6.setMaximum(120)
        self.spbox_o_oi_6.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_6, 2, 8, 1, 1)

        self.spbox_o_oi_7 = QSpinBox(generator_audio)
        self.spbox_o_oi_7.setObjectName(u"spbox_o_oi_7")
        self.spbox_o_oi_7.setMaximum(120)
        self.spbox_o_oi_7.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_7, 2, 9, 1, 1)

        self.spbox_o_oi_8 = QSpinBox(generator_audio)
        self.spbox_o_oi_8.setObjectName(u"spbox_o_oi_8")
        self.spbox_o_oi_8.setMaximum(120)
        self.spbox_o_oi_8.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_8, 2, 10, 1, 1)

        self.spbox_o_oi_0 = QSpinBox(generator_audio)
        self.spbox_o_oi_0.setObjectName(u"spbox_o_oi_0")
        self.spbox_o_oi_0.setMaximum(120)
        self.spbox_o_oi_0.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_0, 2, 2, 1, 1)

        self.spbox_o_oi_1 = QSpinBox(generator_audio)
        self.spbox_o_oi_1.setObjectName(u"spbox_o_oi_1")
        self.spbox_o_oi_1.setMaximum(120)
        self.spbox_o_oi_1.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_1, 2, 3, 1, 1)

        self.spbox_o_oi_2 = QSpinBox(generator_audio)
        self.spbox_o_oi_2.setObjectName(u"spbox_o_oi_2")
        self.spbox_o_oi_2.setMaximum(120)
        self.spbox_o_oi_2.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_2, 2, 4, 1, 1)

        self.spbox_o_oi_3 = QSpinBox(generator_audio)
        self.spbox_o_oi_3.setObjectName(u"spbox_o_oi_3")
        self.spbox_o_oi_3.setMaximum(120)
        self.spbox_o_oi_3.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_3, 2, 5, 1, 1)

        self.spbox_o_oi_4 = QSpinBox(generator_audio)
        self.spbox_o_oi_4.setObjectName(u"spbox_o_oi_4")
        self.spbox_o_oi_4.setMaximum(120)
        self.spbox_o_oi_4.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_4, 2, 6, 1, 1)

        self.spbox_o_oi_5 = QSpinBox(generator_audio)
        self.spbox_o_oi_5.setObjectName(u"spbox_o_oi_5")
        self.spbox_o_oi_5.setMaximum(120)
        self.spbox_o_oi_5.setSingleStep(5)

        self.gridLayout_2.addWidget(self.spbox_o_oi_5, 2, 7, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)

        self.line_3 = QFrame(generator_audio)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_42 = QLabel(generator_audio)
        self.label_42.setObjectName(u"label_42")

        self.horizontalLayout_2.addWidget(self.label_42)

        self.chbox_ldl_od = QCheckBox(generator_audio)
        self.chbox_ldl_od.setObjectName(u"chbox_ldl_od")

        self.horizontalLayout_2.addWidget(self.chbox_ldl_od)

        self.chbox_ldl_oi = QCheckBox(generator_audio)
        self.chbox_ldl_oi.setObjectName(u"chbox_ldl_oi")

        self.horizontalLayout_2.addWidget(self.chbox_ldl_oi)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.spbox_ldl_od_4 = QSpinBox(generator_audio)
        self.spbox_ldl_od_4.setObjectName(u"spbox_ldl_od_4")
        self.spbox_ldl_od_4.setEnabled(False)
        self.spbox_ldl_od_4.setMaximum(130)
        self.spbox_ldl_od_4.setSingleStep(5)
        self.spbox_ldl_od_4.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_4, 1, 6, 1, 1)

        self.label_33 = QLabel(generator_audio)
        self.label_33.setObjectName(u"label_33")

        self.gridLayout_3.addWidget(self.label_33, 2, 1, 1, 1)

        self.spbox_ldl_oi_0 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_0.setObjectName(u"spbox_ldl_oi_0")
        self.spbox_ldl_oi_0.setEnabled(False)
        self.spbox_ldl_oi_0.setMaximum(130)
        self.spbox_ldl_oi_0.setSingleStep(5)
        self.spbox_ldl_oi_0.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_0, 2, 2, 1, 1)

        self.spbox_ldl_oi_8 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_8.setObjectName(u"spbox_ldl_oi_8")
        self.spbox_ldl_oi_8.setEnabled(False)
        self.spbox_ldl_oi_8.setMaximum(130)
        self.spbox_ldl_oi_8.setSingleStep(5)
        self.spbox_ldl_oi_8.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_8, 2, 10, 1, 1)

        self.label_35 = QLabel(generator_audio)
        self.label_35.setObjectName(u"label_35")

        self.gridLayout_3.addWidget(self.label_35, 0, 7, 1, 1)

        self.spbox_ldl_oi_7 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_7.setObjectName(u"spbox_ldl_oi_7")
        self.spbox_ldl_oi_7.setEnabled(False)
        self.spbox_ldl_oi_7.setMaximum(130)
        self.spbox_ldl_oi_7.setSingleStep(5)
        self.spbox_ldl_oi_7.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_7, 2, 9, 1, 1)

        self.spbox_ldl_od_3 = QSpinBox(generator_audio)
        self.spbox_ldl_od_3.setObjectName(u"spbox_ldl_od_3")
        self.spbox_ldl_od_3.setEnabled(False)
        self.spbox_ldl_od_3.setMaximum(130)
        self.spbox_ldl_od_3.setSingleStep(5)
        self.spbox_ldl_od_3.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_3, 1, 5, 1, 1)

        self.spbox_ldl_od_7 = QSpinBox(generator_audio)
        self.spbox_ldl_od_7.setObjectName(u"spbox_ldl_od_7")
        self.spbox_ldl_od_7.setEnabled(False)
        self.spbox_ldl_od_7.setMaximum(130)
        self.spbox_ldl_od_7.setSingleStep(5)
        self.spbox_ldl_od_7.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_7, 1, 9, 1, 1)

        self.spbox_ldl_od_8 = QSpinBox(generator_audio)
        self.spbox_ldl_od_8.setObjectName(u"spbox_ldl_od_8")
        self.spbox_ldl_od_8.setEnabled(False)
        self.spbox_ldl_od_8.setMaximum(130)
        self.spbox_ldl_od_8.setSingleStep(5)
        self.spbox_ldl_od_8.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_8, 1, 10, 1, 1)

        self.label_27 = QLabel(generator_audio)
        self.label_27.setObjectName(u"label_27")

        self.gridLayout_3.addWidget(self.label_27, 0, 5, 1, 1)

        self.label_30 = QLabel(generator_audio)
        self.label_30.setObjectName(u"label_30")

        self.gridLayout_3.addWidget(self.label_30, 0, 2, 1, 1)

        self.spbox_ldl_od_1 = QSpinBox(generator_audio)
        self.spbox_ldl_od_1.setObjectName(u"spbox_ldl_od_1")
        self.spbox_ldl_od_1.setEnabled(False)
        self.spbox_ldl_od_1.setMaximum(130)
        self.spbox_ldl_od_1.setSingleStep(5)
        self.spbox_ldl_od_1.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_1, 1, 3, 1, 1)

        self.spbox_ldl_oi_5 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_5.setObjectName(u"spbox_ldl_oi_5")
        self.spbox_ldl_oi_5.setEnabled(False)
        self.spbox_ldl_oi_5.setMaximum(130)
        self.spbox_ldl_oi_5.setSingleStep(5)
        self.spbox_ldl_oi_5.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_5, 2, 7, 1, 1)

        self.label_38 = QLabel(generator_audio)
        self.label_38.setObjectName(u"label_38")

        self.gridLayout_3.addWidget(self.label_38, 0, 8, 1, 1)

        self.spbox_ldl_od_5 = QSpinBox(generator_audio)
        self.spbox_ldl_od_5.setObjectName(u"spbox_ldl_od_5")
        self.spbox_ldl_od_5.setEnabled(False)
        self.spbox_ldl_od_5.setMaximum(130)
        self.spbox_ldl_od_5.setSingleStep(5)
        self.spbox_ldl_od_5.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_5, 1, 7, 1, 1)

        self.spbox_ldl_oi_2 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_2.setObjectName(u"spbox_ldl_oi_2")
        self.spbox_ldl_oi_2.setEnabled(False)
        self.spbox_ldl_oi_2.setMaximum(130)
        self.spbox_ldl_oi_2.setSingleStep(5)
        self.spbox_ldl_oi_2.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_2, 2, 4, 1, 1)

        self.label_29 = QLabel(generator_audio)
        self.label_29.setObjectName(u"label_29")

        self.gridLayout_3.addWidget(self.label_29, 1, 1, 1, 1)

        self.spbox_ldl_od_0 = QSpinBox(generator_audio)
        self.spbox_ldl_od_0.setObjectName(u"spbox_ldl_od_0")
        self.spbox_ldl_od_0.setEnabled(False)
        self.spbox_ldl_od_0.setMaximum(130)
        self.spbox_ldl_od_0.setSingleStep(5)
        self.spbox_ldl_od_0.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_0, 1, 2, 1, 1)

        self.label_37 = QLabel(generator_audio)
        self.label_37.setObjectName(u"label_37")

        self.gridLayout_3.addWidget(self.label_37, 0, 9, 1, 1)

        self.spbox_ldl_oi_1 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_1.setObjectName(u"spbox_ldl_oi_1")
        self.spbox_ldl_oi_1.setEnabled(False)
        self.spbox_ldl_oi_1.setMaximum(130)
        self.spbox_ldl_oi_1.setSingleStep(5)
        self.spbox_ldl_oi_1.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_1, 2, 3, 1, 1)

        self.label_34 = QLabel(generator_audio)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout_3.addWidget(self.label_34, 0, 3, 1, 1)

        self.label_32 = QLabel(generator_audio)
        self.label_32.setObjectName(u"label_32")

        self.gridLayout_3.addWidget(self.label_32, 0, 10, 1, 1)

        self.label_39 = QLabel(generator_audio)
        self.label_39.setObjectName(u"label_39")

        self.gridLayout_3.addWidget(self.label_39, 0, 0, 3, 1)

        self.spbox_ldl_od_6 = QSpinBox(generator_audio)
        self.spbox_ldl_od_6.setObjectName(u"spbox_ldl_od_6")
        self.spbox_ldl_od_6.setEnabled(False)
        self.spbox_ldl_od_6.setMaximum(130)
        self.spbox_ldl_od_6.setSingleStep(5)
        self.spbox_ldl_od_6.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_6, 1, 8, 1, 1)

        self.spbox_ldl_oi_4 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_4.setObjectName(u"spbox_ldl_oi_4")
        self.spbox_ldl_oi_4.setEnabled(False)
        self.spbox_ldl_oi_4.setMaximum(130)
        self.spbox_ldl_oi_4.setSingleStep(5)
        self.spbox_ldl_oi_4.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_4, 2, 6, 1, 1)

        self.spbox_ldl_od_2 = QSpinBox(generator_audio)
        self.spbox_ldl_od_2.setObjectName(u"spbox_ldl_od_2")
        self.spbox_ldl_od_2.setEnabled(False)
        self.spbox_ldl_od_2.setMaximum(130)
        self.spbox_ldl_od_2.setSingleStep(5)
        self.spbox_ldl_od_2.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_od_2, 1, 4, 1, 1)

        self.label_31 = QLabel(generator_audio)
        self.label_31.setObjectName(u"label_31")

        self.gridLayout_3.addWidget(self.label_31, 0, 6, 1, 1)

        self.label_36 = QLabel(generator_audio)
        self.label_36.setObjectName(u"label_36")

        self.gridLayout_3.addWidget(self.label_36, 0, 4, 1, 1)

        self.spbox_ldl_oi_3 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_3.setObjectName(u"spbox_ldl_oi_3")
        self.spbox_ldl_oi_3.setEnabled(False)
        self.spbox_ldl_oi_3.setMaximum(130)
        self.spbox_ldl_oi_3.setSingleStep(5)
        self.spbox_ldl_oi_3.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_3, 2, 5, 1, 1)

        self.spbox_ldl_oi_6 = QSpinBox(generator_audio)
        self.spbox_ldl_oi_6.setObjectName(u"spbox_ldl_oi_6")
        self.spbox_ldl_oi_6.setEnabled(False)
        self.spbox_ldl_oi_6.setMaximum(130)
        self.spbox_ldl_oi_6.setSingleStep(5)
        self.spbox_ldl_oi_6.setValue(130)

        self.gridLayout_3.addWidget(self.spbox_ldl_oi_6, 2, 8, 1, 1)

        self.label_28 = QLabel(generator_audio)
        self.label_28.setObjectName(u"label_28")

        self.gridLayout_3.addWidget(self.label_28, 0, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_3)

        self.label_40 = QLabel(generator_audio)
        self.label_40.setObjectName(u"label_40")

        self.verticalLayout.addWidget(self.label_40)

        self.line_2 = QFrame(generator_audio)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_43 = QLabel(generator_audio)
        self.label_43.setObjectName(u"label_43")
        self.label_43.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_43)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_51 = QLabel(generator_audio)
        self.label_51.setObjectName(u"label_51")

        self.gridLayout_4.addWidget(self.label_51, 1, 2, 1, 1)

        self.label_47 = QLabel(generator_audio)
        self.label_47.setObjectName(u"label_47")

        self.gridLayout_4.addWidget(self.label_47, 4, 0, 1, 1)

        self.label_45 = QLabel(generator_audio)
        self.label_45.setObjectName(u"label_45")

        self.gridLayout_4.addWidget(self.label_45, 2, 0, 1, 1)

        self.label_49 = QLabel(generator_audio)
        self.label_49.setObjectName(u"label_49")

        self.gridLayout_4.addWidget(self.label_49, 0, 4, 1, 1)

        self.label_50 = QLabel(generator_audio)
        self.label_50.setObjectName(u"label_50")

        self.gridLayout_4.addWidget(self.label_50, 0, 1, 1, 2)

        self.label_46 = QLabel(generator_audio)
        self.label_46.setObjectName(u"label_46")

        self.gridLayout_4.addWidget(self.label_46, 3, 0, 1, 1)

        self.label_48 = QLabel(generator_audio)
        self.label_48.setObjectName(u"label_48")

        self.gridLayout_4.addWidget(self.label_48, 1, 1, 1, 1)

        self.label_52 = QLabel(generator_audio)
        self.label_52.setObjectName(u"label_52")

        self.gridLayout_4.addWidget(self.label_52, 1, 3, 1, 1)

        self.label_53 = QLabel(generator_audio)
        self.label_53.setObjectName(u"label_53")

        self.gridLayout_4.addWidget(self.label_53, 1, 4, 1, 1)

        self.label_54 = QLabel(generator_audio)
        self.label_54.setObjectName(u"label_54")

        self.gridLayout_4.addWidget(self.label_54, 3, 2, 1, 1)

        self.label_55 = QLabel(generator_audio)
        self.label_55.setObjectName(u"label_55")

        self.gridLayout_4.addWidget(self.label_55, 3, 4, 1, 1)

        self.label_56 = QLabel(generator_audio)
        self.label_56.setObjectName(u"label_56")

        self.gridLayout_4.addWidget(self.label_56, 2, 2, 1, 1)

        self.label_57 = QLabel(generator_audio)
        self.label_57.setObjectName(u"label_57")

        self.gridLayout_4.addWidget(self.label_57, 2, 4, 1, 1)

        self.spbox_sdt_od_0 = QSpinBox(generator_audio)
        self.spbox_sdt_od_0.setObjectName(u"spbox_sdt_od_0")
        self.spbox_sdt_od_0.setMaximum(130)
        self.spbox_sdt_od_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_sdt_od_0, 2, 1, 1, 1)

        self.spbox_srt_od_0 = QSpinBox(generator_audio)
        self.spbox_srt_od_0.setObjectName(u"spbox_srt_od_0")
        self.spbox_srt_od_0.setMaximum(130)
        self.spbox_srt_od_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_srt_od_0, 3, 1, 1, 1)

        self.spbox_umd_od_0 = QSpinBox(generator_audio)
        self.spbox_umd_od_0.setObjectName(u"spbox_umd_od_0")
        self.spbox_umd_od_0.setMaximum(130)
        self.spbox_umd_od_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_umd_od_0, 4, 1, 1, 1)

        self.spbox_umd_od_1 = QSpinBox(generator_audio)
        self.spbox_umd_od_1.setObjectName(u"spbox_umd_od_1")
        self.spbox_umd_od_1.setMaximum(100)
        self.spbox_umd_od_1.setSingleStep(4)

        self.gridLayout_4.addWidget(self.spbox_umd_od_1, 4, 2, 1, 1)

        self.spbox_umd_oi_0 = QSpinBox(generator_audio)
        self.spbox_umd_oi_0.setObjectName(u"spbox_umd_oi_0")
        self.spbox_umd_oi_0.setMaximum(130)
        self.spbox_umd_oi_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_umd_oi_0, 4, 3, 1, 1)

        self.spbox_umd_oi_1 = QSpinBox(generator_audio)
        self.spbox_umd_oi_1.setObjectName(u"spbox_umd_oi_1")
        self.spbox_umd_oi_1.setMaximum(100)
        self.spbox_umd_oi_1.setSingleStep(4)

        self.gridLayout_4.addWidget(self.spbox_umd_oi_1, 4, 4, 1, 1)

        self.spbox_srt_oi_0 = QSpinBox(generator_audio)
        self.spbox_srt_oi_0.setObjectName(u"spbox_srt_oi_0")
        self.spbox_srt_oi_0.setMaximum(130)
        self.spbox_srt_oi_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_srt_oi_0, 3, 3, 1, 1)

        self.spbox_sdt_oi_0 = QSpinBox(generator_audio)
        self.spbox_sdt_oi_0.setObjectName(u"spbox_sdt_oi_0")
        self.spbox_sdt_oi_0.setMaximum(130)
        self.spbox_sdt_oi_0.setSingleStep(5)

        self.gridLayout_4.addWidget(self.spbox_sdt_oi_0, 2, 3, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout_4)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        self.line = QFrame(generator_audio)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.label_44 = QLabel(generator_audio)
        self.label_44.setObjectName(u"label_44")
        self.label_44.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_44)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_58 = QLabel(generator_audio)
        self.label_58.setObjectName(u"label_58")

        self.horizontalLayout_5.addWidget(self.label_58)

        self.chbox_recrut_od = QCheckBox(generator_audio)
        self.chbox_recrut_od.setObjectName(u"chbox_recrut_od")

        self.horizontalLayout_5.addWidget(self.chbox_recrut_od)

        self.chbox_recrut_oi = QCheckBox(generator_audio)
        self.chbox_recrut_oi.setObjectName(u"chbox_recrut_oi")

        self.horizontalLayout_5.addWidget(self.chbox_recrut_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_59 = QLabel(generator_audio)
        self.label_59.setObjectName(u"label_59")

        self.horizontalLayout_4.addWidget(self.label_59)

        self.chbox_det_od = QCheckBox(generator_audio)
        self.chbox_det_od.setObjectName(u"chbox_det_od")

        self.horizontalLayout_4.addWidget(self.chbox_det_od)

        self.chbox_det_oi = QCheckBox(generator_audio)
        self.chbox_det_oi.setObjectName(u"chbox_det_oi")

        self.horizontalLayout_4.addWidget(self.chbox_det_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_60 = QLabel(generator_audio)
        self.label_60.setObjectName(u"label_60")

        self.horizontalLayout_6.addWidget(self.label_60)

        self.label_61 = QLabel(generator_audio)
        self.label_61.setObjectName(u"label_61")
        self.label_61.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_61)

        self.cb_z_od = QComboBox(generator_audio)
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.addItem("")
        self.cb_z_od.setObjectName(u"cb_z_od")

        self.horizontalLayout_6.addWidget(self.cb_z_od)

        self.label_62 = QLabel(generator_audio)
        self.label_62.setObjectName(u"label_62")
        self.label_62.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_62)

        self.cb_z_oi = QComboBox(generator_audio)
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.addItem("")
        self.cb_z_oi.setObjectName(u"cb_z_oi")

        self.horizontalLayout_6.addWidget(self.cb_z_oi)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.label_63 = QLabel(generator_audio)
        self.label_63.setObjectName(u"label_63")
        self.label_63.setTextFormat(Qt.AutoText)
        self.label_63.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_63)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

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

        self.retranslateUi(generator_audio)

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

        self.label_63.setText(QCoreApplication.translate("generator_audio", u"Nota: todos los valores deben ser rellenados si alguno no existe en db poner 130 y al porcentaje 0, en el caso de UMD solo poner el valor maximo de discriminaci\u00f3n", None))
        self.btn_cancel.setText(QCoreApplication.translate("generator_audio", u"Cancelar", None))
        self.btn_create.setText(QCoreApplication.translate("generator_audio", u"Crear", None))
    # retranslateUi

