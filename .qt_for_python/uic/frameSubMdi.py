# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/UI/frameSubMdi.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(688, 174)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.barra = QtWidgets.QFrame(Form)
        self.barra.setMinimumSize(QtCore.QSize(0, 20))
        self.barra.setMaximumSize(QtCore.QSize(16777215, 20))
        self.barra.setLineWidth(0)
        self.barra.setObjectName("barra")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.barra)
        self.horizontalLayout.setContentsMargins(6, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lbl_title = QtWidgets.QLabel(self.barra)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.lbl_title.setFont(font)
        self.lbl_title.setObjectName("lbl_title")
        self.horizontalLayout.addWidget(self.lbl_title)
        self.verticalLayout_2.addWidget(self.barra)
        self.layout_content = QtWidgets.QVBoxLayout()
        self.layout_content.setContentsMargins(3, -1, 3, -1)
        self.layout_content.setObjectName("layout_content")
        self.verticalLayout_2.addLayout(self.layout_content)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))

