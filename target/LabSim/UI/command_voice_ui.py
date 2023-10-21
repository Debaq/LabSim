# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'command_voice.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QSpacerItem,
    QWidget)

class Ui_cmdVoice(object):
    def setupUi(self, cmdVoice):
        if not cmdVoice.objectName():
            cmdVoice.setObjectName(u"cmdVoice")
        cmdVoice.resize(1021, 46)
        self.horizontalLayout = QHBoxLayout(cmdVoice)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.retranslateUi(cmdVoice)

        QMetaObject.connectSlotsByName(cmdVoice)
    # setupUi

    def retranslateUi(self, cmdVoice):
        cmdVoice.setWindowTitle(QCoreApplication.translate("cmdVoice", u"Form", None))
    # retranslateUi

