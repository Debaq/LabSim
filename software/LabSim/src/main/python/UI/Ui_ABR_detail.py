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
        ABR_detail.resize(400, 470)
        self.verticalLayout = QtWidgets.QVBoxLayout(ABR_detail)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(ABR_detail)
        self.groupBox.setMaximumSize(QtCore.QSize(300, 16777215))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.progressBar = QtWidgets.QProgressBar(self.groupBox)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout.addWidget(self.progressBar)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.horizontalFrame_2 = QtWidgets.QFrame(self.groupBox)
        self.horizontalFrame_2.setMinimumSize(QtCore.QSize(0, 80))
        self.horizontalFrame_2.setObjectName("horizontalFrame_2")
        self.layout_fsp = QtWidgets.QHBoxLayout(self.horizontalFrame_2)
        self.layout_fsp.setObjectName("layout_fsp")
        self.verticalLayout_2.addWidget(self.horizontalFrame_2)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.verticalFrame = QtWidgets.QFrame(self.groupBox)
        self.verticalFrame.setMinimumSize(QtCore.QSize(0, 80))
        self.verticalFrame.setObjectName("verticalFrame")
        self.layout_eeg = QtWidgets.QVBoxLayout(self.verticalFrame)
        self.layout_eeg.setObjectName("layout_eeg")
        self.verticalLayout_2.addWidget(self.verticalFrame)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(ABR_detail)
        self.groupBox_2.setMaximumSize(QtCore.QSize(300, 16777215))
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.pushButton = QtWidgets.QPushButton(self.groupBox_2)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout_3.addWidget(self.pushButton)
        self.pushButton_3 = QtWidgets.QPushButton(self.groupBox_2)
        self.pushButton_3.setObjectName("pushButton_3")
        self.verticalLayout_3.addWidget(self.pushButton_3)
        self.pushButton_2 = QtWidgets.QPushButton(self.groupBox_2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout_3.addWidget(self.pushButton_2)
        self.verticalLayout.addWidget(self.groupBox_2)
        spacerItem = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(ABR_detail)
        QtCore.QMetaObject.connectSlotsByName(ABR_detail)

    def retranslateUi(self, ABR_detail):
        _translate = QtCore.QCoreApplication.translate
        ABR_detail.setWindowTitle(_translate("ABR_detail", "Form"))
        self.groupBox.setTitle(_translate("ABR_detail", "Prueba"))
        self.label.setText(_translate("ABR_detail", "Reproductibilidad"))
        self.label_2.setText(_translate("ABR_detail", "fsp :"))
        self.label_3.setText(_translate("ABR_detail", "EEG:"))
        self.groupBox_2.setTitle(_translate("ABR_detail", "Resumen"))
        self.pushButton.setText(_translate("ABR_detail", "Iniciar"))
        self.pushButton_3.setText(_translate("ABR_detail", "Pausar"))
        self.pushButton_2.setText(_translate("ABR_detail", "Detener"))
