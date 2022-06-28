# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pref_cvc.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_pref_cvc(object):
    def setupUi(self, pref_cvc):
        if not pref_cvc.objectName():
            pref_cvc.setObjectName(u"pref_cvc")
        pref_cvc.resize(400, 300)
        self.horizontalLayout_3 = QHBoxLayout(pref_cvc)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, -1, -1, -1)

        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, -1, -1, -1)

        self.horizontalLayout_3.addLayout(self.verticalLayout_2)


        self.retranslateUi(pref_cvc)

        QMetaObject.connectSlotsByName(pref_cvc)
    # setupUi

    def retranslateUi(self, pref_cvc):
        pref_cvc.setWindowTitle(QCoreApplication.translate("pref_cvc", u"Form", None))
    # retranslateUi

