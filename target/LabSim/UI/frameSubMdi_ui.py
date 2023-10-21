# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'frameSubMdi.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(688, 174)
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.barra = QFrame(Form)
        self.barra.setObjectName(u"barra")
        self.barra.setMinimumSize(QSize(0, 20))
        self.barra.setMaximumSize(QSize(16777215, 20))
        self.barra.setLineWidth(0)
        self.horizontalLayout = QHBoxLayout(self.barra)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 0, 0, 0)
        self.lbl_title = QLabel(self.barra)
        self.lbl_title.setObjectName(u"lbl_title")
        font = QFont()
        font.setPointSize(8)
        self.lbl_title.setFont(font)

        self.horizontalLayout.addWidget(self.lbl_title)


        self.verticalLayout_2.addWidget(self.barra)

        self.layout_content = QVBoxLayout()
        self.layout_content.setObjectName(u"layout_content")
        self.layout_content.setContentsMargins(3, -1, 3, -1)

        self.verticalLayout_2.addLayout(self.layout_content)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
    # retranslateUi

