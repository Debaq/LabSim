# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/UI/ABR_control.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ABRSim(object):
    def setupUi(self, ABRSim):
        ABRSim.setObjectName("ABRSim")
        ABRSim.resize(1238, 493)
        self.horizontalLayout = QtWidgets.QHBoxLayout(ABRSim)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.control = QtWidgets.QFrame(ABRSim)
        self.control.setMinimumSize(QtCore.QSize(320, 0))
        self.control.setMaximumSize(QtCore.QSize(350, 16777215))
        self.control.setObjectName("control")
        self.layout_left = QtWidgets.QVBoxLayout(self.control)
        self.layout_left.setObjectName("layout_left")
        self.horizontalLayout.addWidget(self.control)
        self.line = QtWidgets.QFrame(ABRSim)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.layourt_ctrl_R = QtWidgets.QHBoxLayout()
        self.layourt_ctrl_R.setContentsMargins(4, 0, 4, -1)
        self.layourt_ctrl_R.setSpacing(0)
        self.layourt_ctrl_R.setObjectName("layourt_ctrl_R")
        self.verticalLayout_2.addLayout(self.layourt_ctrl_R)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalFrame_2 = QtWidgets.QFrame(ABRSim)
        self.verticalFrame_2.setMinimumSize(QtCore.QSize(40, 0))
        self.verticalFrame_2.setMaximumSize(QtCore.QSize(40, 16777215))
        self.verticalFrame_2.setObjectName("verticalFrame_2")
        self.layout_ctrl_curve_R = QtWidgets.QVBoxLayout(self.verticalFrame_2)
        self.layout_ctrl_curve_R.setContentsMargins(0, 0, 0, 6)
        self.layout_ctrl_curve_R.setSpacing(0)
        self.layout_ctrl_curve_R.setObjectName("layout_ctrl_curve_R")
        self.horizontalLayout_3.addWidget(self.verticalFrame_2)
        self.verticalFrame_3 = QtWidgets.QFrame(ABRSim)
        self.verticalFrame_3.setMinimumSize(QtCore.QSize(400, 0))
        self.verticalFrame_3.setObjectName("verticalFrame_3")
        self.layout_graph_R = QtWidgets.QVBoxLayout(self.verticalFrame_3)
        self.layout_graph_R.setContentsMargins(0, 6, 6, 6)
        self.layout_graph_R.setSpacing(0)
        self.layout_graph_R.setObjectName("layout_graph_R")
        self.horizontalLayout_3.addWidget(self.verticalFrame_3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.layourt_ctrl_L = QtWidgets.QHBoxLayout()
        self.layourt_ctrl_L.setContentsMargins(4, -1, 4, -1)
        self.layourt_ctrl_L.setSpacing(0)
        self.layourt_ctrl_L.setObjectName("layourt_ctrl_L")
        self.verticalLayout_4.addLayout(self.layourt_ctrl_L)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalFrame_4 = QtWidgets.QFrame(ABRSim)
        self.verticalFrame_4.setMinimumSize(QtCore.QSize(40, 0))
        self.verticalFrame_4.setMaximumSize(QtCore.QSize(40, 16777215))
        self.verticalFrame_4.setObjectName("verticalFrame_4")
        self.layout_ctrl_curve_L = QtWidgets.QVBoxLayout(self.verticalFrame_4)
        self.layout_ctrl_curve_L.setContentsMargins(0, 0, 0, 6)
        self.layout_ctrl_curve_L.setSpacing(0)
        self.layout_ctrl_curve_L.setObjectName("layout_ctrl_curve_L")
        self.horizontalLayout_2.addWidget(self.verticalFrame_4)
        self.verticalFrame_5 = QtWidgets.QFrame(ABRSim)
        self.verticalFrame_5.setMinimumSize(QtCore.QSize(400, 0))
        self.verticalFrame_5.setObjectName("verticalFrame_5")
        self.layout_graph_L = QtWidgets.QVBoxLayout(self.verticalFrame_5)
        self.layout_graph_L.setContentsMargins(0, 6, 6, 6)
        self.layout_graph_L.setSpacing(0)
        self.layout_graph_L.setObjectName("layout_graph_L")
        self.horizontalLayout_2.addWidget(self.verticalFrame_5)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.horizontalLayout.addLayout(self.verticalLayout_4)

        self.retranslateUi(ABRSim)
        QtCore.QMetaObject.connectSlotsByName(ABRSim)

    def retranslateUi(self, ABRSim):
        _translate = QtCore.QCoreApplication.translate
        ABRSim.setWindowTitle(_translate("ABRSim", "ABRSim"))