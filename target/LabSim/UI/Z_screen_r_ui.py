# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Z_screen_r.ui'
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

class Ui_Z_rscreen(object):
    def setupUi(self, Z_rscreen):
        if not Z_rscreen.objectName():
            Z_rscreen.setObjectName(u"Z_rscreen")
        Z_rscreen.resize(580, 280)
        Z_rscreen.setMinimumSize(QSize(580, 280))
        Z_rscreen.setMaximumSize(QSize(580, 280))
        Z_rscreen.setStyleSheet(u"font: 10pt \"Monospace\";\n"
"color: rgb(255, 255, 255);")
        self.verticalLayout = QVBoxLayout(Z_rscreen)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_8 = QLabel(Z_rscreen)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout.addWidget(self.label_8)

        self.label_7 = QLabel(Z_rscreen)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout.addWidget(self.label_7)

        self.label_22 = QLabel(Z_rscreen)
        self.label_22.setObjectName(u"label_22")

        self.horizontalLayout.addWidget(self.label_22)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(20)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.graph_frame = QFrame(Z_rscreen)
        self.graph_frame.setObjectName(u"graph_frame")
        self.graph_frame.setMinimumSize(QSize(350, 0))
        self.graph_frame.setFrameShape(QFrame.Box)
        self.graph = QVBoxLayout(self.graph_frame)
        self.graph.setObjectName(u"graph")

        self.horizontalLayout_2.addWidget(self.graph_frame)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.label_10 = QLabel(Z_rscreen)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_10)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_11 = QLabel(Z_rscreen)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_9.addWidget(self.label_11)

        self.label_9 = QLabel(Z_rscreen)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFrameShape(QFrame.Box)

        self.horizontalLayout_9.addWidget(self.label_9)


        self.verticalLayout_2.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_13 = QLabel(Z_rscreen)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_8.addWidget(self.label_13)

        self.label_12 = QLabel(Z_rscreen)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFrameShape(QFrame.Box)

        self.horizontalLayout_8.addWidget(self.label_12)


        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_15 = QLabel(Z_rscreen)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_7.addWidget(self.label_15)

        self.label_14 = QLabel(Z_rscreen)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFrameShape(QFrame.Box)

        self.horizontalLayout_7.addWidget(self.label_14)


        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_17 = QLabel(Z_rscreen)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_6.addWidget(self.label_17)

        self.label_16 = QLabel(Z_rscreen)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setFrameShape(QFrame.Box)

        self.horizontalLayout_6.addWidget(self.label_16)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.label_21 = QLabel(Z_rscreen)
        self.label_21.setObjectName(u"label_21")

        self.horizontalLayout_10.addWidget(self.label_21)

        self.label_20 = QLabel(Z_rscreen)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setFrameShape(QFrame.Box)

        self.horizontalLayout_10.addWidget(self.label_20)


        self.verticalLayout_2.addLayout(self.horizontalLayout_10)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_19 = QLabel(Z_rscreen)
        self.label_19.setObjectName(u"label_19")

        self.horizontalLayout_4.addWidget(self.label_19)

        self.label_18 = QLabel(Z_rscreen)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setFrameShape(QFrame.Box)

        self.horizontalLayout_4.addWidget(self.label_18)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(40)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(15, -1, 15, -1)
        self.label_2 = QLabel(Z_rscreen)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_2)

        self.label_4 = QLabel(Z_rscreen)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_4)

        self.label_6 = QLabel(Z_rscreen)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_6)

        self.label_5 = QLabel(Z_rscreen)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_5)

        self.label_3 = QLabel(Z_rscreen)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.label = QLabel(Z_rscreen)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(Z_rscreen)

        QMetaObject.connectSlotsByName(Z_rscreen)
    # setupUi

    def retranslateUi(self, Z_rscreen):
        Z_rscreen.setWindowTitle(QCoreApplication.translate("Z_rscreen", u"Form", None))
        self.label_8.setText(QCoreApplication.translate("Z_rscreen", u"Reflex", None))
        self.label_7.setText(QCoreApplication.translate("Z_rscreen", u"OD", None))
        self.label_22.setText(QCoreApplication.translate("Z_rscreen", u"IPSI", None))
        self.label_10.setText(QCoreApplication.translate("Z_rscreen", u"Threshold", None))
        self.label_11.setText(QCoreApplication.translate("Z_rscreen", u"500 Hz", None))
        self.label_9.setText(QCoreApplication.translate("Z_rscreen", u"----", None))
        self.label_13.setText(QCoreApplication.translate("Z_rscreen", u"1000 Hz", None))
        self.label_12.setText(QCoreApplication.translate("Z_rscreen", u"----", None))
        self.label_15.setText(QCoreApplication.translate("Z_rscreen", u"2000 Hz", None))
        self.label_14.setText(QCoreApplication.translate("Z_rscreen", u"----", None))
        self.label_17.setText(QCoreApplication.translate("Z_rscreen", u"4000 Hz", None))
        self.label_16.setText(QCoreApplication.translate("Z_rscreen", u"----", None))
        self.label_21.setText(QCoreApplication.translate("Z_rscreen", u"NBN", None))
        self.label_20.setText(QCoreApplication.translate("Z_rscreen", u"----", None))
        self.label_19.setText(QCoreApplication.translate("Z_rscreen", u"Vol.:", None))
        self.label_18.setText(QCoreApplication.translate("Z_rscreen", u"0.0 ml", None))
        self.label_2.setText(QCoreApplication.translate("Z_rscreen", u"1000 Hz", None))
        self.label_4.setText(QCoreApplication.translate("Z_rscreen", u"Inicio", None))
        self.label_6.setText(QCoreApplication.translate("Z_rscreen", u"85 dB", None))
        self.label_5.setText(QCoreApplication.translate("Z_rscreen", u"IPSI", None))
        self.label_3.setText(QCoreApplication.translate("Z_rscreen", u"CONTRA", None))
        self.label.setText(QCoreApplication.translate("Z_rscreen", u"0 daP", None))
    # retranslateUi

