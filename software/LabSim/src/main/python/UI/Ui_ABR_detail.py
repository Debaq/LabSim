# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/UI/ABR_detail.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ABR_detail(object):
    def setupUi(self, ABR_detail):
        ABR_detail.setObjectName("ABR_detail")
        ABR_detail.resize(150, 444)
        font = QtGui.QFont()
        font.setPointSize(8)
        ABR_detail.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(ABR_detail)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_2 = QtWidgets.QGroupBox(ABR_detail)
        self.groupBox_2.setMinimumSize(QtCore.QSize(150, 0))
        self.groupBox_2.setMaximumSize(QtCore.QSize(150, 16777215))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout_3.setSpacing(3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.btn_start = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_start.setObjectName("btn_start")
        self.verticalLayout_3.addWidget(self.btn_start)
        self.btn_stop = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_stop.setObjectName("btn_stop")
        self.verticalLayout_3.addWidget(self.btn_stop)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.groupBox = QtWidgets.QGroupBox(ABR_detail)
        self.groupBox.setMinimumSize(QtCore.QSize(150, 0))
        self.groupBox.setMaximumSize(QtCore.QSize(150, 16777215))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout_2.setSpacing(3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.pb_repro = QtWidgets.QProgressBar(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.pb_repro.setFont(font)
        self.pb_repro.setProperty("value", 0)
        self.pb_repro.setObjectName("pb_repro")
        self.horizontalLayout.addWidget(self.pb_repro)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.horizontalFrame_2 = QtWidgets.QFrame(self.groupBox)
        self.horizontalFrame_2.setMinimumSize(QtCore.QSize(0, 60))
        self.horizontalFrame_2.setMaximumSize(QtCore.QSize(16777215, 60))
        self.horizontalFrame_2.setObjectName("horizontalFrame_2")
        self.layout_fsp = QtWidgets.QHBoxLayout(self.horizontalFrame_2)
        self.layout_fsp.setContentsMargins(0, 0, 0, 0)
        self.layout_fsp.setSpacing(0)
        self.layout_fsp.setObjectName("layout_fsp")
        self.verticalLayout_2.addWidget(self.horizontalFrame_2)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.verticalFrame = QtWidgets.QFrame(self.groupBox)
        self.verticalFrame.setMinimumSize(QtCore.QSize(0, 60))
        self.verticalFrame.setMaximumSize(QtCore.QSize(16777215, 60))
        self.verticalFrame.setObjectName("verticalFrame")
        self.layout_eeg = QtWidgets.QVBoxLayout(self.verticalFrame)
        self.layout_eeg.setContentsMargins(0, 0, 0, 0)
        self.layout_eeg.setSpacing(0)
        self.layout_eeg.setObjectName("layout_eeg")
        self.verticalLayout_2.addWidget(self.verticalFrame)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(ABR_detail)
        QtCore.QMetaObject.connectSlotsByName(ABR_detail)

    def retranslateUi(self, ABR_detail):
        _translate = QtCore.QCoreApplication.translate
        ABR_detail.setWindowTitle(_translate("ABR_detail", "Form"))
        self.groupBox_2.setTitle(_translate("ABR_detail", "Control"))
        self.btn_start.setText(_translate("ABR_detail", "Iniciar"))
        self.btn_stop.setText(_translate("ABR_detail", "Detener"))
        self.groupBox.setTitle(_translate("ABR_detail", "Prueba"))
        self.label.setText(_translate("ABR_detail", "Reproduc.:"))
        self.label_2.setText(_translate("ABR_detail", "fsp :"))
        self.label_3.setText(_translate("ABR_detail", "EEG:"))
