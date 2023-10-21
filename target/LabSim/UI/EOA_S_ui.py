# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'EOA_S.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_Eoa_S(object):
    def setupUi(self, Eoa_S):
        if not Eoa_S.objectName():
            Eoa_S.setObjectName(u"Eoa_S")
        Eoa_S.resize(278, 421)
        Eoa_S.setMinimumSize(QSize(278, 0))
        Eoa_S.setMaximumSize(QSize(278, 16777215))
        self.verticalLayout = QVBoxLayout(Eoa_S)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(Eoa_S)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(0, 200))
        self.frame.setMaximumSize(QSize(16777215, 200))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)

        self.verticalLayout.addWidget(self.frame)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_3 = QPushButton(Eoa_S)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.horizontalLayout.addWidget(self.pushButton_3)

        self.pushButton = QPushButton(Eoa_S)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout.addWidget(self.pushButton)

        self.pushButton_4 = QPushButton(Eoa_S)
        self.pushButton_4.setObjectName(u"pushButton_4")

        self.horizontalLayout.addWidget(self.pushButton_4)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.pushButton_2 = QPushButton(Eoa_S)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout_2.addWidget(self.pushButton_2)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(Eoa_S)

        QMetaObject.connectSlotsByName(Eoa_S)
    # setupUi

    def retranslateUi(self, Eoa_S):
        Eoa_S.setWindowTitle(QCoreApplication.translate("Eoa_S", u"Form", None))
        self.pushButton_3.setText(QCoreApplication.translate("Eoa_S", u"Left", None))
        self.pushButton.setText(QCoreApplication.translate("Eoa_S", u"up", None))
        self.pushButton_4.setText(QCoreApplication.translate("Eoa_S", u"Rigth", None))
        self.pushButton_2.setText(QCoreApplication.translate("Eoa_S", u"down", None))
    # retranslateUi

