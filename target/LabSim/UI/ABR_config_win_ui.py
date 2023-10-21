# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ABR_config_win.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QGroupBox,
    QHBoxLayout, QLabel, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_ABR_config(object):
    def setupUi(self, ABR_config):
        if not ABR_config.objectName():
            ABR_config.setObjectName(u"ABR_config")
        ABR_config.resize(350, 462)
        self.verticalLayout = QVBoxLayout(ABR_config)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBox = QGroupBox(ABR_config)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(300, 0))
        self.groupBox.setMaximumSize(QSize(300, 16777215))
        font = QFont()
        font.setPointSize(8)
        self.groupBox.setFont(font)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_6.addWidget(self.label_6)

        self.cb_stim = QComboBox(self.groupBox)
        self.cb_stim.addItem("")
        self.cb_stim.addItem("")
        self.cb_stim.setObjectName(u"cb_stim")
        self.cb_stim.setEnabled(False)
        self.cb_stim.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_6.addWidget(self.cb_stim)

        self.label_11 = QLabel(self.groupBox)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_6.addWidget(self.label_11)

        self.comboBox_11 = QComboBox(self.groupBox)
        self.comboBox_11.addItem("")
        self.comboBox_11.addItem("")
        self.comboBox_11.addItem("")
        self.comboBox_11.addItem("")
        self.comboBox_11.setObjectName(u"comboBox_11")
        self.comboBox_11.setEnabled(False)
        self.comboBox_11.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_6.addWidget(self.comboBox_11)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_12 = QLabel(self.groupBox)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMaximumSize(QSize(80, 16777215))

        self.verticalLayout_3.addWidget(self.label_12)

        self.spinBox_5 = QSpinBox(self.groupBox)
        self.spinBox_5.setObjectName(u"spinBox_5")
        self.spinBox_5.setEnabled(False)
        self.spinBox_5.setMaximumSize(QSize(80, 16777215))
        self.spinBox_5.setMinimum(1)
        self.spinBox_5.setMaximum(100)

        self.verticalLayout_3.addWidget(self.spinBox_5)


        self.horizontalLayout_10.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_13 = QLabel(self.groupBox)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setMaximumSize(QSize(80, 16777215))

        self.verticalLayout_4.addWidget(self.label_13)

        self.spinBox_6 = QSpinBox(self.groupBox)
        self.spinBox_6.setObjectName(u"spinBox_6")
        self.spinBox_6.setEnabled(False)
        self.spinBox_6.setMaximumSize(QSize(80, 16777215))
        self.spinBox_6.setMinimum(1)
        self.spinBox_6.setMaximum(100)

        self.verticalLayout_4.addWidget(self.spinBox_6)


        self.horizontalLayout_10.addLayout(self.verticalLayout_4)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_14 = QLabel(self.groupBox)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setMaximumSize(QSize(80, 16777215))

        self.verticalLayout_5.addWidget(self.label_14)

        self.spinBox_7 = QSpinBox(self.groupBox)
        self.spinBox_7.setObjectName(u"spinBox_7")
        self.spinBox_7.setEnabled(False)
        self.spinBox_7.setMaximumSize(QSize(80, 16777215))
        self.spinBox_7.setMinimum(1)
        self.spinBox_7.setMaximum(100)

        self.verticalLayout_5.addWidget(self.spinBox_7)


        self.horizontalLayout_10.addLayout(self.verticalLayout_5)


        self.verticalLayout_2.addLayout(self.horizontalLayout_10)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout.addWidget(self.label)

        self.comboBox = QComboBox(self.groupBox)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setEnabled(False)

        self.horizontalLayout.addWidget(self.comboBox)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_7.addWidget(self.label_7)

        self.sb_int = QSpinBox(self.groupBox)
        self.sb_int.setObjectName(u"sb_int")
        self.sb_int.setEnabled(True)
        self.sb_int.setMaximumSize(QSize(100, 16777215))
        self.sb_int.setMaximum(100)
        self.sb_int.setSingleStep(5)
        self.sb_int.setValue(80)

        self.horizontalLayout_7.addWidget(self.sb_int)

        self.label_10 = QLabel(self.groupBox)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_7.addWidget(self.label_10)

        self.sb_mskg = QSpinBox(self.groupBox)
        self.sb_mskg.setObjectName(u"sb_mskg")
        self.sb_mskg.setEnabled(False)
        self.sb_mskg.setMaximumSize(QSize(100, 16777215))
        self.sb_mskg.setMaximum(100)
        self.sb_mskg.setSingleStep(5)

        self.horizontalLayout_7.addWidget(self.sb_mskg)


        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_5.addWidget(self.label_5)

        self.doubleSpinBox = QDoubleSpinBox(self.groupBox)
        self.doubleSpinBox.setObjectName(u"doubleSpinBox")
        self.doubleSpinBox.setEnabled(False)
        self.doubleSpinBox.setMaximumSize(QSize(150, 16777215))
        self.doubleSpinBox.setDecimals(1)
        self.doubleSpinBox.setSingleStep(0.100000000000000)
        self.doubleSpinBox.setValue(21.100000000000001)

        self.horizontalLayout_5.addWidget(self.doubleSpinBox)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_8 = QLabel(self.groupBox)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_8.addWidget(self.label_8)

        self.spinBox_3 = QSpinBox(self.groupBox)
        self.spinBox_3.setObjectName(u"spinBox_3")
        self.spinBox_3.setEnabled(False)
        self.spinBox_3.setMaximumSize(QSize(120, 16777215))
        self.spinBox_3.setMinimum(1)
        self.spinBox_3.setMaximum(300)
        self.spinBox_3.setValue(12)

        self.horizontalLayout_8.addWidget(self.spinBox_3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_2.addWidget(self.label_2)

        self.comboBox_2 = QComboBox(self.groupBox)
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.setObjectName(u"comboBox_2")
        self.comboBox_2.setEnabled(False)
        self.comboBox_2.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_2.addWidget(self.comboBox_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_4.addWidget(self.label_4)

        self.comboBox_4 = QComboBox(self.groupBox)
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.setObjectName(u"comboBox_4")
        self.comboBox_4.setEnabled(False)
        self.comboBox_4.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_4.addWidget(self.comboBox_4)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_3.addWidget(self.label_3)

        self.spinBox_4 = QSpinBox(self.groupBox)
        self.spinBox_4.setObjectName(u"spinBox_4")
        self.spinBox_4.setEnabled(False)
        self.spinBox_4.setMaximumSize(QSize(150, 16777215))
        self.spinBox_4.setMinimum(1)
        self.spinBox_4.setMaximum(5000)
        self.spinBox_4.setValue(2000)

        self.horizontalLayout_3.addWidget(self.spinBox_4)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_9 = QLabel(self.groupBox)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_9.addWidget(self.label_9)

        self.cb_side = QComboBox(self.groupBox)
        self.cb_side.addItem("")
        self.cb_side.addItem("")
        self.cb_side.setObjectName(u"cb_side")
        self.cb_side.setEnabled(True)
        self.cb_side.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_9.addWidget(self.cb_side)


        self.verticalLayout_2.addLayout(self.horizontalLayout_9)


        self.verticalLayout.addWidget(self.groupBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(ABR_config)

        QMetaObject.connectSlotsByName(ABR_config)
    # setupUi

    def retranslateUi(self, ABR_config):
        ABR_config.setWindowTitle(QCoreApplication.translate("ABR_config", u"Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("ABR_config", u"Configuraci\u00f3n", None))
        self.label_6.setText(QCoreApplication.translate("ABR_config", u"Est\u00edmulo", None))
        self.cb_stim.setItemText(0, QCoreApplication.translate("ABR_config", u"Click", None))
        self.cb_stim.setItemText(1, QCoreApplication.translate("ABR_config", u"Tono Burst", None))

        self.label_11.setText(QCoreApplication.translate("ABR_config", u"Frecuencia", None))
        self.comboBox_11.setItemText(0, QCoreApplication.translate("ABR_config", u"500 Hz", None))
        self.comboBox_11.setItemText(1, QCoreApplication.translate("ABR_config", u"1000 Hz", None))
        self.comboBox_11.setItemText(2, QCoreApplication.translate("ABR_config", u"2000 Hz", None))
        self.comboBox_11.setItemText(3, QCoreApplication.translate("ABR_config", u"4000 Hz", None))

        self.label_12.setText(QCoreApplication.translate("ABR_config", u"inicio", None))
        self.spinBox_5.setSuffix(QCoreApplication.translate("ABR_config", u" ms", None))
        self.label_13.setText(QCoreApplication.translate("ABR_config", u"ca\u00edda", None))
        self.spinBox_6.setSuffix(QCoreApplication.translate("ABR_config", u" ms", None))
        self.label_14.setText(QCoreApplication.translate("ABR_config", u"plato", None))
        self.spinBox_7.setSuffix(QCoreApplication.translate("ABR_config", u" ms", None))
        self.label.setText(QCoreApplication.translate("ABR_config", u"Polaridad", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("ABR_config", u"Alteranada", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("ABR_config", u"Condensaci\u00f3n", None))
        self.comboBox.setItemText(2, QCoreApplication.translate("ABR_config", u"Rarefacci\u00f3n", None))

        self.label_7.setText(QCoreApplication.translate("ABR_config", u"Int.", None))
        self.sb_int.setSuffix(QCoreApplication.translate("ABR_config", u" dB nHL", None))
        self.label_10.setText(QCoreApplication.translate("ABR_config", u"Mkg.", None))
        self.sb_mskg.setSuffix(QCoreApplication.translate("ABR_config", u" dB nHL", None))
        self.sb_mskg.setPrefix("")
        self.label_5.setText(QCoreApplication.translate("ABR_config", u"Tasa", None))
        self.doubleSpinBox.setPrefix("")
        self.doubleSpinBox.setSuffix(QCoreApplication.translate("ABR_config", u" /segundo", None))
        self.label_8.setText(QCoreApplication.translate("ABR_config", u"Ventana", None))
        self.spinBox_3.setSuffix(QCoreApplication.translate("ABR_config", u" segundos", None))
        self.label_2.setText(QCoreApplication.translate("ABR_config", u"Filtro Pasa Bajo", None))
        self.comboBox_2.setItemText(0, QCoreApplication.translate("ABR_config", u"3000 Hz", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("ABR_config", u"500 Hz", None))
        self.comboBox_2.setItemText(2, QCoreApplication.translate("ABR_config", u"750 Hz", None))
        self.comboBox_2.setItemText(3, QCoreApplication.translate("ABR_config", u"1000 Hz", None))
        self.comboBox_2.setItemText(4, QCoreApplication.translate("ABR_config", u"1500 Hz", None))
        self.comboBox_2.setItemText(5, QCoreApplication.translate("ABR_config", u"2000 Hz", None))
        self.comboBox_2.setItemText(6, QCoreApplication.translate("ABR_config", u"4000 Hz", None))
        self.comboBox_2.setItemText(7, QCoreApplication.translate("ABR_config", u"6000 Hz", None))
        self.comboBox_2.setItemText(8, QCoreApplication.translate("ABR_config", u"8000 Hz", None))

        self.label_4.setText(QCoreApplication.translate("ABR_config", u"Filtro Pasa Alto", None))
        self.comboBox_4.setItemText(0, QCoreApplication.translate("ABR_config", u"100 Hz", None))
        self.comboBox_4.setItemText(1, QCoreApplication.translate("ABR_config", u"5 Hz", None))
        self.comboBox_4.setItemText(2, QCoreApplication.translate("ABR_config", u"10 hz", None))
        self.comboBox_4.setItemText(3, QCoreApplication.translate("ABR_config", u"20 Hz", None))
        self.comboBox_4.setItemText(4, QCoreApplication.translate("ABR_config", u"30 Hz", None))
        self.comboBox_4.setItemText(5, QCoreApplication.translate("ABR_config", u"50 Hz", None))
        self.comboBox_4.setItemText(6, QCoreApplication.translate("ABR_config", u"80 Hz", None))
        self.comboBox_4.setItemText(7, QCoreApplication.translate("ABR_config", u"200 Hz", None))

        self.label_3.setText(QCoreApplication.translate("ABR_config", u"Promediaciones", None))
        self.label_9.setText(QCoreApplication.translate("ABR_config", u"Lado", None))
        self.cb_side.setItemText(0, QCoreApplication.translate("ABR_config", u"OD", None))
        self.cb_side.setItemText(1, QCoreApplication.translate("ABR_config", u"OI", None))

    # retranslateUi

