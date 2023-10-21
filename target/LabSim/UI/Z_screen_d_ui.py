# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Z_screen_d.ui'
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

class Ui_Z_dscreen(object):
    def setupUi(self, Z_dscreen):
        if not Z_dscreen.objectName():
            Z_dscreen.setObjectName(u"Z_dscreen")
        Z_dscreen.resize(580, 280)
        Z_dscreen.setMinimumSize(QSize(580, 280))
        Z_dscreen.setMaximumSize(QSize(580, 280))
        Z_dscreen.setStyleSheet(u"font: 10pt \"Monospace\";\n"
"color: rgb(255, 255, 255);")
        self.verticalLayout = QVBoxLayout(Z_dscreen)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_8 = QLabel(Z_dscreen)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout.addWidget(self.label_8)

        self.label_7 = QLabel(Z_dscreen)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout.addWidget(self.label_7)

        self.label_22 = QLabel(Z_dscreen)
        self.label_22.setObjectName(u"label_22")

        self.horizontalLayout.addWidget(self.label_22)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(20)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.graph_frame = QFrame(Z_dscreen)
        self.graph_frame.setObjectName(u"graph_frame")
        self.graph_frame.setMinimumSize(QSize(350, 0))
        self.graph_frame.setFrameShape(QFrame.Box)
        self.graph_main = QVBoxLayout(self.graph_frame)
        self.graph_main.setObjectName(u"graph_main")
        self.graph = QVBoxLayout()
        self.graph.setObjectName(u"graph")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.graph.addItem(self.verticalSpacer)


        self.graph_main.addLayout(self.graph)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.label_10 = QLabel(self.graph_frame)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_4.addWidget(self.label_10)

        self.label_9 = QLabel(self.graph_frame)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFrameShape(QFrame.Box)

        self.horizontalLayout_4.addWidget(self.label_9)


        self.graph_main.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_2.addWidget(self.graph_frame)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(40)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(15, -1, 15, -1)
        self.label_2 = QLabel(Z_dscreen)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_2)

        self.label_4 = QLabel(Z_dscreen)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_4)

        self.label_6 = QLabel(Z_dscreen)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_6)

        self.label_5 = QLabel(Z_dscreen)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_5)

        self.label_3 = QLabel(Z_dscreen)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.label = QLabel(Z_dscreen)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(Z_dscreen)

        QMetaObject.connectSlotsByName(Z_dscreen)
    # setupUi

    def retranslateUi(self, Z_dscreen):
        Z_dscreen.setWindowTitle(QCoreApplication.translate("Z_dscreen", u"Form", None))
        self.label_8.setText(QCoreApplication.translate("Z_dscreen", u"Tone Decay", None))
        self.label_7.setText(QCoreApplication.translate("Z_dscreen", u"OD", None))
        self.label_22.setText(QCoreApplication.translate("Z_dscreen", u"IPSI", None))
        self.label_10.setText(QCoreApplication.translate("Z_dscreen", u"Vol.:", None))
        self.label_9.setText(QCoreApplication.translate("Z_dscreen", u"0.0 ml", None))
        self.label_2.setText(QCoreApplication.translate("Z_dscreen", u"1000 Hz", None))
        self.label_4.setText(QCoreApplication.translate("Z_dscreen", u"Inicio", None))
        self.label_6.setText(QCoreApplication.translate("Z_dscreen", u"85 dB", None))
        self.label_5.setText(QCoreApplication.translate("Z_dscreen", u"IPSI", None))
        self.label_3.setText(QCoreApplication.translate("Z_dscreen", u"CONTRA", None))
        self.label.setText(QCoreApplication.translate("Z_dscreen", u"0 daP", None))
    # retranslateUi

