# Form implementation generated from reading ui file '/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/UI/Z_screen_z.ui'
#
# Created by: PySide6 UI code generator 6.2.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PySide6 import QtCore, QtGui, QtWidgets


class Ui_Z_zscreen(object):
    def setupUi(self, Z_zscreen):
        Z_zscreen.setObjectName("Z_zscreen")
        Z_zscreen.resize(580, 280)
        Z_zscreen.setMinimumSize(QtCore.QSize(580, 280))
        Z_zscreen.setMaximumSize(QtCore.QSize(590, 290))
        Z_zscreen.setStyleSheet("font: 10pt \"Monospace\";\n"
"color: rgb(255, 255, 255);")
        self.verticalLayout = QtWidgets.QVBoxLayout(Z_zscreen)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalFrame = QtWidgets.QFrame(Z_zscreen)
        self.horizontalFrame.setMinimumSize(QtCore.QSize(0, 20))
        self.horizontalFrame.setMaximumSize(QtCore.QSize(16777215, 20))
        self.horizontalFrame.setObjectName("horizontalFrame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout.setContentsMargins(10, 0, 10, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_8 = QtWidgets.QLabel(self.horizontalFrame)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout.addWidget(self.label_8)
        self.lbl_side = QtWidgets.QLabel(self.horizontalFrame)
        self.lbl_side.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_side.setObjectName("lbl_side")
        self.horizontalLayout.addWidget(self.lbl_side)
        self.lbl_timeDate = QtWidgets.QLabel(self.horizontalFrame)
        self.lbl_timeDate.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lbl_timeDate.setObjectName("lbl_timeDate")
        self.horizontalLayout.addWidget(self.lbl_timeDate)
        self.verticalLayout.addWidget(self.horizontalFrame)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(6, -1, 6, -1)
        self.horizontalLayout_2.setSpacing(20)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalFrame_2 = QtWidgets.QFrame(Z_zscreen)
        self.verticalFrame_2.setMinimumSize(QtCore.QSize(350, 0))
        self.verticalFrame_2.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.verticalFrame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.verticalFrame_2.setObjectName("verticalFrame_2")
        self.graph = QtWidgets.QVBoxLayout(self.verticalFrame_2)
        self.graph.setObjectName("graph")
        self.horizontalLayout_2.addWidget(self.verticalFrame_2)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_11 = QtWidgets.QLabel(Z_zscreen)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_5.addWidget(self.label_11)
        self.lbl_c = QtWidgets.QLabel(Z_zscreen)
        self.lbl_c.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.lbl_c.setText("")
        self.lbl_c.setObjectName("lbl_c")
        self.horizontalLayout_5.addWidget(self.lbl_c)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_13 = QtWidgets.QLabel(Z_zscreen)
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_7.addWidget(self.label_13)
        self.lbl_p = QtWidgets.QLabel(Z_zscreen)
        self.lbl_p.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.lbl_p.setText("")
        self.lbl_p.setObjectName("lbl_p")
        self.horizontalLayout_7.addWidget(self.lbl_p)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_15 = QtWidgets.QLabel(Z_zscreen)
        self.label_15.setObjectName("label_15")
        self.horizontalLayout_6.addWidget(self.label_15)
        self.lbl_v = QtWidgets.QLabel(Z_zscreen)
        self.lbl_v.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.lbl_v.setText("")
        self.lbl_v.setObjectName("lbl_v")
        self.horizontalLayout_6.addWidget(self.lbl_v)
        self.verticalLayout_2.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_17 = QtWidgets.QLabel(Z_zscreen)
        self.label_17.setObjectName("label_17")
        self.horizontalLayout_4.addWidget(self.label_17)
        self.lbl_g = QtWidgets.QLabel(Z_zscreen)
        self.lbl_g.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.lbl_g.setText("")
        self.lbl_g.setObjectName("lbl_g")
        self.horizontalLayout_4.addWidget(self.lbl_g)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        spacerItem = QtWidgets.QSpacerItem(20, 40,QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalFrame_3 = QtWidgets.QFrame(Z_zscreen)
        self.horizontalFrame_3.setMinimumSize(QtCore.QSize(0, 20))
        self.horizontalFrame_3.setMaximumSize(QtCore.QSize(16777215, 20))
        self.horizontalFrame_3.setObjectName("horizontalFrame_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalFrame_3)
        self.horizontalLayout_3.setContentsMargins(15, 0, 15, 0)
        self.horizontalLayout_3.setSpacing(40)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.horizontalFrame_3)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.label_2 = QtWidgets.QLabel(self.horizontalFrame_3)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.label_6 = QtWidgets.QLabel(self.horizontalFrame_3)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_3.addWidget(self.label_6)
        self.label_5 = QtWidgets.QLabel(self.horizontalFrame_3)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_3.addWidget(self.label_5)
        self.label = QtWidgets.QLabel(self.horizontalFrame_3)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.label_4 = QtWidgets.QLabel(self.horizontalFrame_3)
        self.label_4.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.verticalLayout.addWidget(self.horizontalFrame_3)

        self.retranslateUi(Z_zscreen)
        QtCore.QMetaObject.connectSlotsByName(Z_zscreen)

    def retranslateUi(self, Z_zscreen):
        _translate = QtCore.QCoreApplication.translate
        Z_zscreen.setWindowTitle(_translate("Z_zscreen", "ZSim"))
        self.label_8.setText(_translate("Z_zscreen", "Impedance"))
        self.lbl_side.setText(_translate("Z_zscreen", "OD"))
        self.lbl_timeDate.setText(_translate("Z_zscreen", "26/07/2021"))
        self.label_11.setText(_translate("Z_zscreen", "Compliance :"))
        self.label_13.setText(_translate("Z_zscreen", "Presure :"))
        self.label_15.setText(_translate("Z_zscreen", "Volume :"))
        self.label_17.setText(_translate("Z_zscreen", "Gradient :"))
        self.label_3.setText(_translate("Z_zscreen", "<--"))
        self.label_2.setText(_translate("Z_zscreen", "-->"))
        self.label_6.setText(_translate("Z_zscreen", "pos -> neg"))
        self.label_5.setText(_translate("Z_zscreen", "2 cc"))
        self.label.setText(_translate("Z_zscreen", "-200 daPa"))
        self.label_4.setText(_translate("Z_zscreen", "200 daPa"))
