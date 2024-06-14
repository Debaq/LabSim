# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ABR_config.ui'
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
        ABR_config.resize(255, 462)
        self.verticalLayout = QVBoxLayout(ABR_config)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBox = QGroupBox(ABR_config)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(150, 0))
        self.groupBox.setMaximumSize(QSize(150, 16777215))
        font = QFont()
        font.setPointSize(8)
        self.groupBox.setFont(font)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.groupBox.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setSpacing(3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(3, 3, 3, 3)
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

        self.horizontalLayout_6.addWidget(self.cb_stim)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout.addWidget(self.label)

        self.cb_pol = QComboBox(self.groupBox)
        self.cb_pol.addItem("")
        self.cb_pol.addItem("")
        self.cb_pol.addItem("")
        self.cb_pol.setObjectName(u"cb_pol")

        self.horizontalLayout.addWidget(self.cb_pol)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_7.addWidget(self.label_7)

        self.sb_intencity = QSpinBox(self.groupBox)
        self.sb_intencity.setObjectName(u"sb_intencity")
        self.sb_intencity.setEnabled(True)
        self.sb_intencity.setMinimumSize(QSize(40, 0))
        self.sb_intencity.setMaximumSize(QSize(100, 25))
        self.sb_intencity.setMaximum(100)
        self.sb_intencity.setSingleStep(5)
        self.sb_intencity.setValue(80)

        self.horizontalLayout_7.addWidget(self.sb_intencity)

        self.label_10 = QLabel(self.groupBox)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_7.addWidget(self.label_10)

        self.sb_mskg = QSpinBox(self.groupBox)
        self.sb_mskg.setObjectName(u"sb_mskg")
        self.sb_mskg.setEnabled(False)
        self.sb_mskg.setMaximumSize(QSize(100, 25))
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

        self.sb_rate = QDoubleSpinBox(self.groupBox)
        self.sb_rate.setObjectName(u"sb_rate")
        self.sb_rate.setDecimals(1)
        self.sb_rate.setSingleStep(0.100000000000000)
        self.sb_rate.setValue(10.100000000000000)

        self.horizontalLayout_5.addWidget(self.sb_rate)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_2.addWidget(self.label_2)

        self.cb_filterdown = QComboBox(self.groupBox)
        self.cb_filterdown.addItem("")
        self.cb_filterdown.addItem("")
        self.cb_filterdown.addItem("")
        self.cb_filterdown.addItem("")
        self.cb_filterdown.addItem("")
        self.cb_filterdown.addItem("")
        self.cb_filterdown.addItem("")
        self.cb_filterdown.addItem("")
        self.cb_filterdown.setObjectName(u"cb_filterdown")

        self.horizontalLayout_2.addWidget(self.cb_filterdown)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_4.addWidget(self.label_4)

        self.cb_filterup = QComboBox(self.groupBox)
        self.cb_filterup.addItem("")
        self.cb_filterup.addItem("")
        self.cb_filterup.addItem("")
        self.cb_filterup.addItem("")
        self.cb_filterup.addItem("")
        self.cb_filterup.addItem("")
        self.cb_filterup.setObjectName(u"cb_filterup")

        self.horizontalLayout_4.addWidget(self.cb_filterup)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_3.addWidget(self.label_3)

        self.sb_prom = QSpinBox(self.groupBox)
        self.sb_prom.setObjectName(u"sb_prom")
        self.sb_prom.setMaximum(8000)
        self.sb_prom.setValue(1000)

        self.horizontalLayout_3.addWidget(self.sb_prom)


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
        self.cb_side.setMaximumSize(QSize(150, 25))

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
        self.label_6.setText(QCoreApplication.translate("ABR_config", u"Est\u00edmulo :", None))
        self.cb_stim.setItemText(0, QCoreApplication.translate("ABR_config", u"Clic", None))
        self.cb_stim.setItemText(1, QCoreApplication.translate("ABR_config", u"Chirp", None))

        self.label.setText(QCoreApplication.translate("ABR_config", u"Polaridad :", None))
        self.cb_pol.setItemText(0, QCoreApplication.translate("ABR_config", u"Alternada", None))
        self.cb_pol.setItemText(1, QCoreApplication.translate("ABR_config", u"Conden.", None))
        self.cb_pol.setItemText(2, QCoreApplication.translate("ABR_config", u"Rarefac.", None))

        self.label_7.setText(QCoreApplication.translate("ABR_config", u"Int.", None))
        self.sb_intencity.setSuffix("")
        self.label_10.setText(QCoreApplication.translate("ABR_config", u"Mkg.", None))
        self.sb_mskg.setSuffix("")
        self.sb_mskg.setPrefix("")
        self.label_5.setText(QCoreApplication.translate("ABR_config", u"Tasa :", None))
        self.label_2.setText(QCoreApplication.translate("ABR_config", u"Pasa Bajo :", None))
        self.cb_filterdown.setItemText(0, QCoreApplication.translate("ABR_config", u"1000", None))
        self.cb_filterdown.setItemText(1, QCoreApplication.translate("ABR_config", u"1500", None))
        self.cb_filterdown.setItemText(2, QCoreApplication.translate("ABR_config", u"2000", None))
        self.cb_filterdown.setItemText(3, QCoreApplication.translate("ABR_config", u"2500", None))
        self.cb_filterdown.setItemText(4, QCoreApplication.translate("ABR_config", u"3000", None))
        self.cb_filterdown.setItemText(5, QCoreApplication.translate("ABR_config", u"3500", None))
        self.cb_filterdown.setItemText(6, QCoreApplication.translate("ABR_config", u"4000", None))
        self.cb_filterdown.setItemText(7, QCoreApplication.translate("ABR_config", u"4500", None))

        self.cb_filterdown.setCurrentText(QCoreApplication.translate("ABR_config", u"1000", None))
        self.label_4.setText(QCoreApplication.translate("ABR_config", u"Pasa Alto :", None))
        self.cb_filterup.setItemText(0, QCoreApplication.translate("ABR_config", u"50", None))
        self.cb_filterup.setItemText(1, QCoreApplication.translate("ABR_config", u"100", None))
        self.cb_filterup.setItemText(2, QCoreApplication.translate("ABR_config", u"200", None))
        self.cb_filterup.setItemText(3, QCoreApplication.translate("ABR_config", u"300", None))
        self.cb_filterup.setItemText(4, QCoreApplication.translate("ABR_config", u"400", None))
        self.cb_filterup.setItemText(5, QCoreApplication.translate("ABR_config", u"500", None))

        self.label_3.setText(QCoreApplication.translate("ABR_config", u"Prom. :", None))
        self.label_9.setText(QCoreApplication.translate("ABR_config", u"Lado", None))
        self.cb_side.setItemText(0, QCoreApplication.translate("ABR_config", u"OD", None))
        self.cb_side.setItemText(1, QCoreApplication.translate("ABR_config", u"OI", None))

    # retranslateUi

