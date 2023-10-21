# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ABR_detail.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_ABR_detail(object):
    def setupUi(self, ABR_detail):
        if not ABR_detail.objectName():
            ABR_detail.setObjectName(u"ABR_detail")
        ABR_detail.resize(150, 444)
        font = QFont()
        font.setPointSize(8)
        ABR_detail.setFont(font)
        self.verticalLayout = QVBoxLayout(ABR_detail)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBox_2 = QGroupBox(ABR_detail)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setMinimumSize(QSize(150, 0))
        self.groupBox_2.setMaximumSize(QSize(150, 16777215))
        self.groupBox_2.setFont(font)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setSpacing(3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(3, 3, 3, 3)
        self.btn_start = QPushButton(self.groupBox_2)
        self.btn_start.setObjectName(u"btn_start")

        self.verticalLayout_3.addWidget(self.btn_start)

        self.btn_stop = QPushButton(self.groupBox_2)
        self.btn_stop.setObjectName(u"btn_stop")

        self.verticalLayout_3.addWidget(self.btn_stop)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.groupBox = QGroupBox(ABR_detail)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(150, 0))
        self.groupBox.setMaximumSize(QSize(150, 16777215))
        self.groupBox.setFont(font)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setSpacing(3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.horizontalLayout.addWidget(self.label)

        self.pb_repro = QProgressBar(self.groupBox)
        self.pb_repro.setObjectName(u"pb_repro")
        self.pb_repro.setFont(font)
        self.pb_repro.setValue(0)

        self.horizontalLayout.addWidget(self.pb_repro)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.verticalLayout_2.addWidget(self.label_2)

        self.horizontalFrame_2 = QFrame(self.groupBox)
        self.horizontalFrame_2.setObjectName(u"horizontalFrame_2")
        self.horizontalFrame_2.setMinimumSize(QSize(0, 60))
        self.horizontalFrame_2.setMaximumSize(QSize(16777215, 60))
        self.layout_fsp = QHBoxLayout(self.horizontalFrame_2)
        self.layout_fsp.setSpacing(0)
        self.layout_fsp.setObjectName(u"layout_fsp")
        self.layout_fsp.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_2.addWidget(self.horizontalFrame_2)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_2.addWidget(self.label_3)

        self.verticalFrame = QFrame(self.groupBox)
        self.verticalFrame.setObjectName(u"verticalFrame")
        self.verticalFrame.setMinimumSize(QSize(0, 60))
        self.verticalFrame.setMaximumSize(QSize(16777215, 60))
        self.layout_eeg = QVBoxLayout(self.verticalFrame)
        self.layout_eeg.setSpacing(0)
        self.layout_eeg.setObjectName(u"layout_eeg")
        self.layout_eeg.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_2.addWidget(self.verticalFrame)


        self.verticalLayout.addWidget(self.groupBox)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(ABR_detail)

        QMetaObject.connectSlotsByName(ABR_detail)
    # setupUi

    def retranslateUi(self, ABR_detail):
        ABR_detail.setWindowTitle(QCoreApplication.translate("ABR_detail", u"Form", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("ABR_detail", u"Control", None))
        self.btn_start.setText(QCoreApplication.translate("ABR_detail", u"Iniciar", None))
        self.btn_stop.setText(QCoreApplication.translate("ABR_detail", u"Detener", None))
        self.groupBox.setTitle(QCoreApplication.translate("ABR_detail", u"Prueba", None))
        self.label.setText(QCoreApplication.translate("ABR_detail", u"Reproduc.:", None))
        self.label_2.setText(QCoreApplication.translate("ABR_detail", u"fsp :", None))
        self.label_3.setText(QCoreApplication.translate("ABR_detail", u"EEG:", None))
    # retranslateUi

