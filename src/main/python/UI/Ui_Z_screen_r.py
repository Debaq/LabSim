# Form implementation generated from reading ui file '/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/UI/Z_screen_r.ui'
#
# Created by: PySide6 UI code generator 6.2.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PySide6 import QtCore, QtGui, QtWidgets


class Ui_Z_rscreen(object):
    def setupUi(self, Z_rscreen):
        Z_rscreen.setObjectName("Z_rscreen")
        Z_rscreen.resize(580, 280)
        Z_rscreen.setMinimumSize(QtCore.QSize(580, 280))
        Z_rscreen.setMaximumSize(QtCore.QSize(580, 280))
        Z_rscreen.setStyleSheet("font: 10pt \"Monospace\";\n"
"color: rgb(255, 255, 255);")
        self.verticalLayout = QtWidgets.QVBoxLayout(Z_rscreen)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_8 = QtWidgets.QLabel(Z_rscreen)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout.addWidget(self.label_8)
        self.label_7 = QtWidgets.QLabel(Z_rscreen)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout.addWidget(self.label_7)
        self.label_22 = QtWidgets.QLabel(Z_rscreen)
        self.label_22.setObjectName("label_22")
        self.horizontalLayout.addWidget(self.label_22)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(20)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.graph_frame = QtWidgets.QFrame(Z_rscreen)
        self.graph_frame.setMinimumSize(QtCore.QSize(350, 0))
        self.graph_frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.graph_frame.setObjectName("graph_frame")
        self.graph = QtWidgets.QVBoxLayout(self.graph_frame)
        self.graph.setObjectName("graph")
        self.horizontalLayout_2.addWidget(self.graph_frame)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_10 = QtWidgets.QLabel(Z_rscreen)
        self.label_10.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_10.setObjectName("label_10")
        self.verticalLayout_2.addWidget(self.label_10)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_11 = QtWidgets.QLabel(Z_rscreen)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_9.addWidget(self.label_11)
        self.label_9 = QtWidgets.QLabel(Z_rscreen)
        self.label_9.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_9.addWidget(self.label_9)
        self.verticalLayout_2.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_13 = QtWidgets.QLabel(Z_rscreen)
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_8.addWidget(self.label_13)
        self.label_12 = QtWidgets.QLabel(Z_rscreen)
        self.label_12.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_8.addWidget(self.label_12)
        self.verticalLayout_2.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_15 = QtWidgets.QLabel(Z_rscreen)
        self.label_15.setObjectName("label_15")
        self.horizontalLayout_7.addWidget(self.label_15)
        self.label_14 = QtWidgets.QLabel(Z_rscreen)
        self.label_14.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_7.addWidget(self.label_14)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_17 = QtWidgets.QLabel(Z_rscreen)
        self.label_17.setObjectName("label_17")
        self.horizontalLayout_6.addWidget(self.label_17)
        self.label_16 = QtWidgets.QLabel(Z_rscreen)
        self.label_16.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_16.setObjectName("label_16")
        self.horizontalLayout_6.addWidget(self.label_16)
        self.verticalLayout_2.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_21 = QtWidgets.QLabel(Z_rscreen)
        self.label_21.setObjectName("label_21")
        self.horizontalLayout_10.addWidget(self.label_21)
        self.label_20 = QtWidgets.QLabel(Z_rscreen)
        self.label_20.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_20.setObjectName("label_20")
        self.horizontalLayout_10.addWidget(self.label_20)
        self.verticalLayout_2.addLayout(self.horizontalLayout_10)
        spacerItem = QtWidgets.QSpacerItem(20, 40,QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_19 = QtWidgets.QLabel(Z_rscreen)
        self.label_19.setObjectName("label_19")
        self.horizontalLayout_4.addWidget(self.label_19)
        self.label_18 = QtWidgets.QLabel(Z_rscreen)
        self.label_18.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.label_18.setObjectName("label_18")
        self.horizontalLayout_4.addWidget(self.label_18)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(15, -1, 15, -1)
        self.horizontalLayout_3.setSpacing(40)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_2 = QtWidgets.QLabel(Z_rscreen)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.label_4 = QtWidgets.QLabel(Z_rscreen)
        self.label_4.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.label_6 = QtWidgets.QLabel(Z_rscreen)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_3.addWidget(self.label_6)
        self.label_5 = QtWidgets.QLabel(Z_rscreen)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_3.addWidget(self.label_5)
        self.label_3 = QtWidgets.QLabel(Z_rscreen)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.label = QtWidgets.QLabel(Z_rscreen)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Z_rscreen)
        QtCore.QMetaObject.connectSlotsByName(Z_rscreen)

    def retranslateUi(self, Z_rscreen):
        _translate = QtCore.QCoreApplication.translate
        Z_rscreen.setWindowTitle(_translate("Z_rscreen", "Form"))
        self.label_8.setText(_translate("Z_rscreen", "Reflex"))
        self.label_7.setText(_translate("Z_rscreen", "OD"))
        self.label_22.setText(_translate("Z_rscreen", "IPSI"))
        self.label_10.setText(_translate("Z_rscreen", "Threshold"))
        self.label_11.setText(_translate("Z_rscreen", "500 Hz"))
        self.label_9.setText(_translate("Z_rscreen", "----"))
        self.label_13.setText(_translate("Z_rscreen", "1000 Hz"))
        self.label_12.setText(_translate("Z_rscreen", "----"))
        self.label_15.setText(_translate("Z_rscreen", "2000 Hz"))
        self.label_14.setText(_translate("Z_rscreen", "----"))
        self.label_17.setText(_translate("Z_rscreen", "4000 Hz"))
        self.label_16.setText(_translate("Z_rscreen", "----"))
        self.label_21.setText(_translate("Z_rscreen", "NBN"))
        self.label_20.setText(_translate("Z_rscreen", "----"))
        self.label_19.setText(_translate("Z_rscreen", "Vol.:"))
        self.label_18.setText(_translate("Z_rscreen", "0.0 ml"))
        self.label_2.setText(_translate("Z_rscreen", "1000 Hz"))
        self.label_4.setText(_translate("Z_rscreen", "Inicio"))
        self.label_6.setText(_translate("Z_rscreen", "85 dB"))
        self.label_5.setText(_translate("Z_rscreen", "IPSI"))
        self.label_3.setText(_translate("Z_rscreen", "CONTRA"))
        self.label.setText(_translate("Z_rscreen", "0 daP"))
