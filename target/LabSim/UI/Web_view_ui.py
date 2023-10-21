# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Web_view.ui'
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
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QWidget)

class Ui_web(object):
    def setupUi(self, web):
        if not web.objectName():
            web.setObjectName(u"web")
        web.resize(400, 300)
        self.horizontalLayout = QHBoxLayout(web)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.view = QWebEngineView(web)
        self.view.setObjectName(u"view")
        self.view.setUrl(QUrl(u"about:blank"))

        self.horizontalLayout.addWidget(self.view)


        self.retranslateUi(web)

        QMetaObject.connectSlotsByName(web)
    # setupUi

    def retranslateUi(self, web):
        web.setWindowTitle(QCoreApplication.translate("web", u"Form", None))
    # retranslateUi

