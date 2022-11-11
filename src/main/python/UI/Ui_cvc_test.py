# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cvc_test_subwindow.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_test(object):
    def setupUi(self, test):
        if not test.objectName():
            test.setObjectName(u"test")
        test.resize(400, 300)
        self.horizontalLayout_2 = QHBoxLayout(test)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.layout_eye_2 = QHBoxLayout()
        self.layout_eye_2.setObjectName(u"layout_eye_2")

        self.horizontalLayout_2.addLayout(self.layout_eye_2)

        self.layout_graph = QVBoxLayout()
        self.layout_graph.setObjectName(u"layout_graph")

        self.horizontalLayout_2.addLayout(self.layout_graph)

        self.verticalFrame = QFrame(test)
        self.verticalFrame.setObjectName(u"verticalFrame")
        self.verticalFrame.setMaximumSize(QSize(150, 16777215))
        self.verticalLayout = QVBoxLayout(self.verticalFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btn_play_pause = QPushButton(self.verticalFrame)
        self.btn_play_pause.setObjectName(u"btn_play_pause")
        self.btn_play_pause.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_play_pause)

        self.btn_state = QPushButton(self.verticalFrame)
        self.btn_state.setObjectName(u"btn_state")
        self.btn_state.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_state)

        self.btn_param = QPushButton(self.verticalFrame)
        self.btn_param.setObjectName(u"btn_param")
        self.btn_param.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_param)

        self.btn_demo = QPushButton(self.verticalFrame)
        self.btn_demo.setObjectName(u"btn_demo")
        self.btn_demo.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_demo)

        self.btn_change_eye = QPushButton(self.verticalFrame)
        self.btn_change_eye.setObjectName(u"btn_change_eye")
        self.btn_change_eye.setMaximumSize(QSize(150, 16777215))

        self.verticalLayout.addWidget(self.btn_change_eye)

        self.btn_cancel = QPushButton(self.verticalFrame)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.verticalLayout.addWidget(self.btn_cancel)

        self.lbl_time = QLabel(self.verticalFrame)
        self.lbl_time.setObjectName(u"lbl_time")
        self.lbl_time.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_time)


        self.horizontalLayout_2.addWidget(self.verticalFrame)


        self.retranslateUi(test)

        QMetaObject.connectSlotsByName(test)
    # setupUi

    def retranslateUi(self, test):
        test.setWindowTitle(QCoreApplication.translate("test", u"Form", None))
        self.btn_play_pause.setText(QCoreApplication.translate("test", u"Iniciar", None))
        self.btn_state.setText(QCoreApplication.translate("test", u"Mostrar estado", None))
        self.btn_param.setText(QCoreApplication.translate("test", u"Cambiar Par\u00e1metros", None))
        self.btn_demo.setText(QCoreApplication.translate("test", u"DEMOSTRACI\u00d3N", None))
        self.btn_change_eye.setText(QCoreApplication.translate("test", u"Examinar el otro ojo", None))
        self.btn_cancel.setText(QCoreApplication.translate("test", u"Cancelar prueba", None))
        self.lbl_time.setText(QCoreApplication.translate("test", u"Hora: 00:00", None))
    # retranslateUi

