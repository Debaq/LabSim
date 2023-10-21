# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Create_case.ui'
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
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QTextEdit,
    QVBoxLayout, QWidget, QWizard, QWizardPage)

class Ui_Wizard(object):
    def setupUi(self, Wizard):
        if not Wizard.objectName():
            Wizard.setObjectName(u"Wizard")
        Wizard.resize(594, 815)
        self.wizardPage1 = QWizardPage()
        self.wizardPage1.setObjectName(u"wizardPage1")
        self.verticalLayout_4 = QVBoxLayout(self.wizardPage1)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label = QLabel(self.wizardPage1)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.label)

        self.line_7 = QFrame(self.wizardPage1)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.HLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line_7)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.label_18 = QLabel(self.wizardPage1)
        self.label_18.setObjectName(u"label_18")

        self.horizontalLayout_2.addWidget(self.label_18)


        self.verticalLayout_4.addLayout(self.horizontalLayout_2)

        self.label_3 = QLabel(self.wizardPage1)
        self.label_3.setObjectName(u"label_3")
        font1 = QFont()
        font1.setPointSize(11)
        self.label_3.setFont(font1)

        self.verticalLayout_4.addWidget(self.label_3)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(10, -1, 10, -1)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_8 = QLabel(self.wizardPage1)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_6.addWidget(self.label_8)

        self.lineEdit_2 = QLineEdit(self.wizardPage1)
        self.lineEdit_2.setObjectName(u"lineEdit_2")

        self.horizontalLayout_6.addWidget(self.lineEdit_2)

        self.label_7 = QLabel(self.wizardPage1)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_6.addWidget(self.label_7)

        self.lineEdit = QLineEdit(self.wizardPage1)
        self.lineEdit.setObjectName(u"lineEdit")

        self.horizontalLayout_6.addWidget(self.lineEdit)


        self.verticalLayout_5.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer)

        self.checkBox = QCheckBox(self.wizardPage1)
        self.checkBox.setObjectName(u"checkBox")

        self.horizontalLayout_7.addWidget(self.checkBox)

        self.pushButton = QPushButton(self.wizardPage1)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_7.addWidget(self.pushButton)


        self.verticalLayout_5.addLayout(self.horizontalLayout_7)


        self.verticalLayout_4.addLayout(self.verticalLayout_5)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(10, -1, 10, -1)
        self.label_6 = QLabel(self.wizardPage1)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_5.addWidget(self.label_6)

        self.spinBox = QSpinBox(self.wizardPage1)
        self.spinBox.setObjectName(u"spinBox")

        self.horizontalLayout_5.addWidget(self.spinBox)

        self.label_5 = QLabel(self.wizardPage1)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_5.addWidget(self.label_5)

        self.comboBox = QComboBox(self.wizardPage1)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setMaxVisibleItems(2)

        self.horizontalLayout_5.addWidget(self.comboBox)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.line = QFrame(self.wizardPage1)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(10, 0, 10, 0)
        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.checkBox_3 = QCheckBox(self.wizardPage1)
        self.checkBox_3.setObjectName(u"checkBox_3")

        self.verticalLayout_8.addWidget(self.checkBox_3)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_10 = QLabel(self.wizardPage1)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_9.addWidget(self.label_10)

        self.comboBox_3 = QComboBox(self.wizardPage1)
        self.comboBox_3.setObjectName(u"comboBox_3")

        self.horizontalLayout_9.addWidget(self.comboBox_3)


        self.verticalLayout_8.addLayout(self.horizontalLayout_9)

        self.label_11 = QLabel(self.wizardPage1)
        self.label_11.setObjectName(u"label_11")

        self.verticalLayout_8.addWidget(self.label_11)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, -1, -1, -1)
        self.spinBox_4 = QSpinBox(self.wizardPage1)
        self.spinBox_4.setObjectName(u"spinBox_4")

        self.verticalLayout_12.addWidget(self.spinBox_4)

        self.label_23 = QLabel(self.wizardPage1)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setAlignment(Qt.AlignCenter)

        self.verticalLayout_12.addWidget(self.label_23)


        self.horizontalLayout_8.addLayout(self.verticalLayout_12)

        self.verticalLayout_13 = QVBoxLayout()
        self.verticalLayout_13.setSpacing(0)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, -1, -1, -1)
        self.spinBox_3 = QSpinBox(self.wizardPage1)
        self.spinBox_3.setObjectName(u"spinBox_3")

        self.verticalLayout_13.addWidget(self.spinBox_3)

        self.label_24 = QLabel(self.wizardPage1)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setAlignment(Qt.AlignCenter)

        self.verticalLayout_13.addWidget(self.label_24)


        self.horizontalLayout_8.addLayout(self.verticalLayout_13)

        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setSpacing(0)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(0, -1, -1, -1)
        self.spinBox_2 = QSpinBox(self.wizardPage1)
        self.spinBox_2.setObjectName(u"spinBox_2")

        self.verticalLayout_14.addWidget(self.spinBox_2)

        self.label_25 = QLabel(self.wizardPage1)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setAlignment(Qt.AlignCenter)

        self.verticalLayout_14.addWidget(self.label_25)


        self.horizontalLayout_8.addLayout(self.verticalLayout_14)


        self.verticalLayout_8.addLayout(self.horizontalLayout_8)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer)


        self.horizontalLayout_14.addLayout(self.verticalLayout_8)

        self.line_4 = QFrame(self.wizardPage1)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.VLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_14.addWidget(self.line_4)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(-1, -1, -1, 0)
        self.checkBox_2 = QCheckBox(self.wizardPage1)
        self.checkBox_2.setObjectName(u"checkBox_2")

        self.verticalLayout_7.addWidget(self.checkBox_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_4 = QLabel(self.wizardPage1)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_3.addWidget(self.label_4)

        self.comboBox_2 = QComboBox(self.wizardPage1)
        self.comboBox_2.setObjectName(u"comboBox_2")

        self.horizontalLayout_3.addWidget(self.comboBox_2)


        self.verticalLayout_7.addLayout(self.horizontalLayout_3)

        self.label_9 = QLabel(self.wizardPage1)
        self.label_9.setObjectName(u"label_9")

        self.verticalLayout_7.addWidget(self.label_9)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setSpacing(0)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, -1, -1, -1)
        self.spinBox_7 = QSpinBox(self.wizardPage1)
        self.spinBox_7.setObjectName(u"spinBox_7")

        self.verticalLayout_15.addWidget(self.spinBox_7)

        self.label_26 = QLabel(self.wizardPage1)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setAlignment(Qt.AlignCenter)

        self.verticalLayout_15.addWidget(self.label_26)


        self.horizontalLayout_4.addLayout(self.verticalLayout_15)

        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setSpacing(0)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(0, -1, -1, -1)
        self.spinBox_6 = QSpinBox(self.wizardPage1)
        self.spinBox_6.setObjectName(u"spinBox_6")

        self.verticalLayout_16.addWidget(self.spinBox_6)

        self.label_27 = QLabel(self.wizardPage1)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setAlignment(Qt.AlignCenter)

        self.verticalLayout_16.addWidget(self.label_27)


        self.horizontalLayout_4.addLayout(self.verticalLayout_16)

        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setSpacing(0)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.verticalLayout_17.setContentsMargins(0, -1, -1, -1)
        self.spinBox_5 = QSpinBox(self.wizardPage1)
        self.spinBox_5.setObjectName(u"spinBox_5")

        self.verticalLayout_17.addWidget(self.spinBox_5)

        self.label_28 = QLabel(self.wizardPage1)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setAlignment(Qt.AlignCenter)

        self.verticalLayout_17.addWidget(self.label_28)


        self.horizontalLayout_4.addLayout(self.verticalLayout_17)


        self.verticalLayout_7.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(-1, 0, -1, -1)
        self.label_14 = QLabel(self.wizardPage1)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_12.addWidget(self.label_14)

        self.comboBox_5 = QComboBox(self.wizardPage1)
        self.comboBox_5.setObjectName(u"comboBox_5")

        self.horizontalLayout_12.addWidget(self.comboBox_5)


        self.verticalLayout_7.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(-1, 0, -1, -1)
        self.label_15 = QLabel(self.wizardPage1)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_13.addWidget(self.label_15)

        self.comboBox_6 = QComboBox(self.wizardPage1)
        self.comboBox_6.setObjectName(u"comboBox_6")

        self.horizontalLayout_13.addWidget(self.comboBox_6)


        self.verticalLayout_7.addLayout(self.horizontalLayout_13)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_2)


        self.horizontalLayout_14.addLayout(self.verticalLayout_7)

        self.line_5 = QFrame(self.wizardPage1)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_14.addWidget(self.line_5)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.checkBox_4 = QCheckBox(self.wizardPage1)
        self.checkBox_4.setObjectName(u"checkBox_4")

        self.verticalLayout_9.addWidget(self.checkBox_4)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_12 = QLabel(self.wizardPage1)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_11.addWidget(self.label_12)

        self.comboBox_4 = QComboBox(self.wizardPage1)
        self.comboBox_4.setObjectName(u"comboBox_4")

        self.horizontalLayout_11.addWidget(self.comboBox_4)


        self.verticalLayout_9.addLayout(self.horizontalLayout_11)

        self.label_13 = QLabel(self.wizardPage1)
        self.label_13.setObjectName(u"label_13")

        self.verticalLayout_9.addWidget(self.label_13)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.verticalLayout_18 = QVBoxLayout()
        self.verticalLayout_18.setSpacing(0)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.spinBox_9 = QSpinBox(self.wizardPage1)
        self.spinBox_9.setObjectName(u"spinBox_9")

        self.verticalLayout_18.addWidget(self.spinBox_9)

        self.label_29 = QLabel(self.wizardPage1)
        self.label_29.setObjectName(u"label_29")
        self.label_29.setAlignment(Qt.AlignCenter)

        self.verticalLayout_18.addWidget(self.label_29)


        self.horizontalLayout_10.addLayout(self.verticalLayout_18)

        self.verticalLayout_19 = QVBoxLayout()
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.spinBox_10 = QSpinBox(self.wizardPage1)
        self.spinBox_10.setObjectName(u"spinBox_10")

        self.verticalLayout_19.addWidget(self.spinBox_10)

        self.label_30 = QLabel(self.wizardPage1)
        self.label_30.setObjectName(u"label_30")
        self.label_30.setAlignment(Qt.AlignCenter)

        self.verticalLayout_19.addWidget(self.label_30)


        self.horizontalLayout_10.addLayout(self.verticalLayout_19)

        self.verticalLayout_20 = QVBoxLayout()
        self.verticalLayout_20.setSpacing(0)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.spinBox_8 = QSpinBox(self.wizardPage1)
        self.spinBox_8.setObjectName(u"spinBox_8")

        self.verticalLayout_20.addWidget(self.spinBox_8)

        self.label_31 = QLabel(self.wizardPage1)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setAlignment(Qt.AlignCenter)

        self.verticalLayout_20.addWidget(self.label_31)


        self.horizontalLayout_10.addLayout(self.verticalLayout_20)


        self.verticalLayout_9.addLayout(self.horizontalLayout_10)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer_3)


        self.horizontalLayout_14.addLayout(self.verticalLayout_9)


        self.verticalLayout_4.addLayout(self.horizontalLayout_14)

        self.line_3 = QFrame(self.wizardPage1)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line_3)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(10, 0, 10, 0)
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(-1, -1, -1, 0)
        self.checkBox_5 = QCheckBox(self.wizardPage1)
        self.checkBox_5.setObjectName(u"checkBox_5")

        self.verticalLayout_10.addWidget(self.checkBox_5)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_16 = QLabel(self.wizardPage1)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_16.addWidget(self.label_16)

        self.comboBox_7 = QComboBox(self.wizardPage1)
        self.comboBox_7.setObjectName(u"comboBox_7")

        self.horizontalLayout_16.addWidget(self.comboBox_7)


        self.verticalLayout_10.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(-1, 0, -1, -1)
        self.label_17 = QLabel(self.wizardPage1)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_17.addWidget(self.label_17)

        self.comboBox_8 = QComboBox(self.wizardPage1)
        self.comboBox_8.setObjectName(u"comboBox_8")

        self.horizontalLayout_17.addWidget(self.comboBox_8)


        self.verticalLayout_10.addLayout(self.horizontalLayout_17)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer_4)


        self.horizontalLayout_15.addLayout(self.verticalLayout_10)

        self.line_6 = QFrame(self.wizardPage1)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_15.addWidget(self.line_6)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.checkBox_6 = QCheckBox(self.wizardPage1)
        self.checkBox_6.setObjectName(u"checkBox_6")

        self.verticalLayout_11.addWidget(self.checkBox_6)

        self.checkBox_8 = QCheckBox(self.wizardPage1)
        self.checkBox_8.setObjectName(u"checkBox_8")

        self.verticalLayout_11.addWidget(self.checkBox_8)

        self.checkBox_9 = QCheckBox(self.wizardPage1)
        self.checkBox_9.setObjectName(u"checkBox_9")

        self.verticalLayout_11.addWidget(self.checkBox_9)

        self.checkBox_7 = QCheckBox(self.wizardPage1)
        self.checkBox_7.setObjectName(u"checkBox_7")

        self.verticalLayout_11.addWidget(self.checkBox_7)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_5)


        self.horizontalLayout_15.addLayout(self.verticalLayout_11)


        self.verticalLayout_4.addLayout(self.horizontalLayout_15)

        self.line_2 = QFrame(self.wizardPage1)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line_2)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(10, -1, 10, -1)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(self.wizardPage1)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.comboBox_9 = QComboBox(self.wizardPage1)
        self.comboBox_9.setObjectName(u"comboBox_9")

        self.horizontalLayout.addWidget(self.comboBox_9)


        self.horizontalLayout_18.addLayout(self.horizontalLayout)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_18)

        Wizard.addPage(self.wizardPage1)
        self.wizardPage2 = QWizardPage()
        self.wizardPage2.setObjectName(u"wizardPage2")
        self.verticalLayout_3 = QVBoxLayout(self.wizardPage2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_19 = QLabel(self.wizardPage2)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setFont(font)
        self.label_19.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_19)

        self.line_8 = QFrame(self.wizardPage2)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.HLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line_8)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_19.addItem(self.horizontalSpacer_5)

        self.label_20 = QLabel(self.wizardPage2)
        self.label_20.setObjectName(u"label_20")

        self.horizontalLayout_19.addWidget(self.label_20)


        self.verticalLayout_3.addLayout(self.horizontalLayout_19)

        self.label_21 = QLabel(self.wizardPage2)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setFont(font1)

        self.verticalLayout_3.addWidget(self.label_21)

        self.textEdit = QTextEdit(self.wizardPage2)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.textEdit)

        self.label_22 = QLabel(self.wizardPage2)
        self.label_22.setObjectName(u"label_22")

        self.verticalLayout_3.addWidget(self.label_22)

        self.textEdit_2 = QTextEdit(self.wizardPage2)
        self.textEdit_2.setObjectName(u"textEdit_2")

        self.verticalLayout_3.addWidget(self.textEdit_2)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalLayout_20.setContentsMargins(-1, 0, -1, -1)
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_6)

        self.pushButton_2 = QPushButton(self.wizardPage2)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout_20.addWidget(self.pushButton_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_20)

        Wizard.addPage(self.wizardPage2)

        self.retranslateUi(Wizard)

        QMetaObject.connectSlotsByName(Wizard)
    # setupUi

    def retranslateUi(self, Wizard):
        Wizard.setWindowTitle(QCoreApplication.translate("Wizard", u"Wizard", None))
        self.label.setText(QCoreApplication.translate("Wizard", u"Generador de casos", None))
        self.label_18.setText(QCoreApplication.translate("Wizard", u"P\u00e1g. 1/4", None))
        self.label_3.setText(QCoreApplication.translate("Wizard", u"B\u00e1sicos :", None))
        self.label_8.setText(QCoreApplication.translate("Wizard", u"Nombre", None))
        self.label_7.setText(QCoreApplication.translate("Wizard", u"Nombre Social", None))
        self.checkBox.setText(QCoreApplication.translate("Wizard", u"Iguales", None))
        self.pushButton.setText(QCoreApplication.translate("Wizard", u"Generar", None))
        self.label_6.setText(QCoreApplication.translate("Wizard", u"Edad", None))
        self.label_5.setText(QCoreApplication.translate("Wizard", u"Sexo", None))
        self.checkBox_3.setText(QCoreApplication.translate("Wizard", u"Hipoacusia", None))
        self.label_10.setText(QCoreApplication.translate("Wizard", u"Lado", None))
        self.label_11.setText(QCoreApplication.translate("Wizard", u"T/evoluci\u00f3n", None))
        self.label_23.setText(QCoreApplication.translate("Wizard", u"d\u00eda", None))
        self.label_24.setText(QCoreApplication.translate("Wizard", u"mes", None))
        self.label_25.setText(QCoreApplication.translate("Wizard", u"a\u00f1o", None))
        self.checkBox_2.setText(QCoreApplication.translate("Wizard", u"Tinnitus", None))
        self.label_4.setText(QCoreApplication.translate("Wizard", u"Lado", None))
        self.label_9.setText(QCoreApplication.translate("Wizard", u"T/evoluci\u00f3n", None))
        self.label_26.setText(QCoreApplication.translate("Wizard", u"d\u00eda", None))
        self.label_27.setText(QCoreApplication.translate("Wizard", u"mes", None))
        self.label_28.setText(QCoreApplication.translate("Wizard", u"a\u00f1o", None))
        self.label_14.setText(QCoreApplication.translate("Wizard", u"Tipo", None))
        self.label_15.setText(QCoreApplication.translate("Wizard", u"Similar a", None))
        self.checkBox_4.setText(QCoreApplication.translate("Wizard", u"Otalg\u00eda", None))
        self.label_12.setText(QCoreApplication.translate("Wizard", u"Lado", None))
        self.label_13.setText(QCoreApplication.translate("Wizard", u"T/evoluci\u00f3n", None))
        self.label_29.setText(QCoreApplication.translate("Wizard", u"d\u00eda", None))
        self.label_30.setText(QCoreApplication.translate("Wizard", u"mes", None))
        self.label_31.setText(QCoreApplication.translate("Wizard", u"a\u00f1o", None))
        self.checkBox_5.setText(QCoreApplication.translate("Wizard", u"Aud\u00edfonos", None))
        self.label_16.setText(QCoreApplication.translate("Wizard", u"Lado", None))
        self.label_17.setText(QCoreApplication.translate("Wizard", u"Tipo", None))
        self.checkBox_6.setText(QCoreApplication.translate("Wizard", u"Lentes", None))
        self.checkBox_8.setText(QCoreApplication.translate("Wizard", u"HTA", None))
        self.checkBox_9.setText(QCoreApplication.translate("Wizard", u"Diabetes", None))
        self.checkBox_7.setText(QCoreApplication.translate("Wizard", u"Fuma", None))
        self.label_2.setText(QCoreApplication.translate("Wizard", u"Tipo de Atenci\u00f3n", None))
        self.label_19.setText(QCoreApplication.translate("Wizard", u"Generador de casos", None))
        self.label_20.setText(QCoreApplication.translate("Wizard", u"P\u00e1g. 2/4", None))
        self.label_21.setText(QCoreApplication.translate("Wizard", u"Historia  y di\u00e1logos:", None))
        self.textEdit.setHtml(QCoreApplication.translate("Wizard", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Noto Sans'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; font-weight:600;\">Explicaci\u00f3n:</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">A continuaci\u00f3n debe ingresar los di\u00e1logos e historia del caso en el orden pregunta -&gt; respuesta.</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /><"
                        "/p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">Para identificarlos debe agregar antes de cada parrafo el identificador del hablante.</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">Los hablantes predefinidos son evaluador </span><span style=\" font-size:9pt; font-weight:600;\">%E%</span><span style=\" font-size:9pt;\"> y paciente </span><span style=\" font-size:9pt; font-weight:600;\">%P%</span><span style=\" font-size:9pt;\">. </span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-ind"
                        "ent:0px;\"><span style=\" font-size:9pt;\">Puede definir un nuevo hablante de la siguiente forma: </span><span style=\" font-size:9pt; text-decoration: underline;\">#%I% = &quot;Nombre o tipo de persona&quot;</span><span style=\" font-size:9pt;\"> adem\u00e1s puede utilizar algunos datos llenados en la ficha b\u00e1sica </span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; text-decoration: underline;\">Variables (se distinge may\u00fasculas de minusculas)</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">{n} : nombre de pila, {N} : nombre completo, {ap}: ape"
                        "llidos, {NS}: nombre social</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">{e} : edad, {s} : sexo, {he}: t/evoluci\u00f3n de la hipoacusia</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">{te}: t/evoluci\u00f3n del tinnitus, {oe}: t/evoluci\u00f3n de la otalg\u00eda</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; font-weight:600;\">Ejemplo de di\u00e1logo simple:</span></p>\n"
"<p align=\"justify\" style=\"-qt-parag"
                        "raph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt; font-weight:600;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">%E% \u00bfme dice su nombre?</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">%P% {n}</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">%E% \u00bfy sus apellidos?</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">%P% {ap}</span></p>\n"
"<p align=\"justify\" style=\"-qt-pa"
                        "ragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; font-weight:600;\">Ejemplo de agregar un nuevo hablante</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; font-style:italic;\">&quot;en este caso la atenci\u00f3n es a un menor de edad&quot;</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; font-style:italic;\">*debe definir los hablantes al inicio del texto</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-"
                        "block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; font-style:italic;\">*la letra que use puede ser cualquiera, no deben repetirse y siempre estar en mayuscula</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">#%M% = Mam\u00e1</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">%E% \u00bfque edad tiene el ni\u00f1o?</span></p>\n"
"<p align=\"justify\""
                        " style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt;\">%M% {n} tiene {e}</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt;\"><br /></p></body></html>", None))
        self.label_22.setText(QCoreApplication.translate("Wizard", u"Historia:", None))
        self.pushButton_2.setText(QCoreApplication.translate("Wizard", u"Previsualizar", None))
    # retranslateUi

