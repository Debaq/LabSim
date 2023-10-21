# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Z_screen_z.ui'
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

class Ui_Z_zscreen(object):
    def setupUi(self, Z_zscreen):
        if not Z_zscreen.objectName():
            Z_zscreen.setObjectName(u"Z_zscreen")
        Z_zscreen.resize(580, 280)
        Z_zscreen.setMinimumSize(QSize(580, 280))
        Z_zscreen.setMaximumSize(QSize(590, 290))
        Z_zscreen.setStyleSheet(u"font: 10pt \"Monospace\";\n"
"color: rgb(255, 255, 255);")
        self.verticalLayout = QVBoxLayout(Z_zscreen)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalFrame = QFrame(Z_zscreen)
        self.horizontalFrame.setObjectName(u"horizontalFrame")
        self.horizontalFrame.setMinimumSize(QSize(0, 20))
        self.horizontalFrame.setMaximumSize(QSize(16777215, 20))
        self.horizontalLayout = QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(10, 0, 10, 0)
        self.label_8 = QLabel(self.horizontalFrame)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout.addWidget(self.label_8)

        self.lbl_side = QLabel(self.horizontalFrame)
        self.lbl_side.setObjectName(u"lbl_side")
        self.lbl_side.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.lbl_side)

        self.lbl_timeDate = QLabel(self.horizontalFrame)
        self.lbl_timeDate.setObjectName(u"lbl_timeDate")
        self.lbl_timeDate.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.lbl_timeDate)


        self.verticalLayout.addWidget(self.horizontalFrame)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(20)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, -1, 6, -1)
        self.verticalFrame_2 = QFrame(Z_zscreen)
        self.verticalFrame_2.setObjectName(u"verticalFrame_2")
        self.verticalFrame_2.setMinimumSize(QSize(350, 0))
        self.verticalFrame_2.setFrameShape(QFrame.Box)
        self.verticalFrame_2.setFrameShadow(QFrame.Plain)
        self.graph = QVBoxLayout(self.verticalFrame_2)
        self.graph.setObjectName(u"graph")

        self.horizontalLayout_2.addWidget(self.verticalFrame_2)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_11 = QLabel(Z_zscreen)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_5.addWidget(self.label_11)

        self.lbl_c = QLabel(Z_zscreen)
        self.lbl_c.setObjectName(u"lbl_c")
        self.lbl_c.setFrameShape(QFrame.Box)

        self.horizontalLayout_5.addWidget(self.lbl_c)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_13 = QLabel(Z_zscreen)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_7.addWidget(self.label_13)

        self.lbl_p = QLabel(Z_zscreen)
        self.lbl_p.setObjectName(u"lbl_p")
        self.lbl_p.setFrameShape(QFrame.Box)

        self.horizontalLayout_7.addWidget(self.lbl_p)


        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_15 = QLabel(Z_zscreen)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_6.addWidget(self.label_15)

        self.lbl_v = QLabel(Z_zscreen)
        self.lbl_v.setObjectName(u"lbl_v")
        self.lbl_v.setFrameShape(QFrame.Box)

        self.horizontalLayout_6.addWidget(self.lbl_v)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_17 = QLabel(Z_zscreen)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_4.addWidget(self.label_17)

        self.lbl_g = QLabel(Z_zscreen)
        self.lbl_g.setObjectName(u"lbl_g")
        self.lbl_g.setFrameShape(QFrame.Box)

        self.horizontalLayout_4.addWidget(self.lbl_g)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalFrame_3 = QFrame(Z_zscreen)
        self.horizontalFrame_3.setObjectName(u"horizontalFrame_3")
        self.horizontalFrame_3.setMinimumSize(QSize(0, 20))
        self.horizontalFrame_3.setMaximumSize(QSize(16777215, 20))
        self.horizontalLayout_3 = QHBoxLayout(self.horizontalFrame_3)
        self.horizontalLayout_3.setSpacing(40)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(15, 0, 15, 0)
        self.label_3 = QLabel(self.horizontalFrame_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.label_2 = QLabel(self.horizontalFrame_3)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_2)

        self.label_6 = QLabel(self.horizontalFrame_3)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_6)

        self.label_5 = QLabel(self.horizontalFrame_3)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_5)

        self.label = QLabel(self.horizontalFrame_3)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label)

        self.label_4 = QLabel(self.horizontalFrame_3)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_4)


        self.verticalLayout.addWidget(self.horizontalFrame_3)


        self.retranslateUi(Z_zscreen)

        QMetaObject.connectSlotsByName(Z_zscreen)
    # setupUi

    def retranslateUi(self, Z_zscreen):
        Z_zscreen.setWindowTitle(QCoreApplication.translate("Z_zscreen", u"ZSim", None))
        self.label_8.setText(QCoreApplication.translate("Z_zscreen", u"Impedance", None))
        self.lbl_side.setText(QCoreApplication.translate("Z_zscreen", u"OD", None))
        self.lbl_timeDate.setText(QCoreApplication.translate("Z_zscreen", u"26/07/2021", None))
        self.label_11.setText(QCoreApplication.translate("Z_zscreen", u"Compliance :", None))
        self.lbl_c.setText("")
        self.label_13.setText(QCoreApplication.translate("Z_zscreen", u"Presure :", None))
        self.lbl_p.setText("")
        self.label_15.setText(QCoreApplication.translate("Z_zscreen", u"Volume :", None))
        self.lbl_v.setText("")
        self.label_17.setText(QCoreApplication.translate("Z_zscreen", u"Gradient :", None))
        self.lbl_g.setText("")
        self.label_3.setText(QCoreApplication.translate("Z_zscreen", u"<--", None))
        self.label_2.setText(QCoreApplication.translate("Z_zscreen", u"-->", None))
        self.label_6.setText(QCoreApplication.translate("Z_zscreen", u"pos -> neg", None))
        self.label_5.setText(QCoreApplication.translate("Z_zscreen", u"2 cc", None))
        self.label.setText(QCoreApplication.translate("Z_zscreen", u"-200 daPa", None))
        self.label_4.setText(QCoreApplication.translate("Z_zscreen", u"200 daPa", None))
    # retranslateUi

