# Form implementation generated from reading ui file '/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/UI/command_voice.ui'
#
# Created by: PySide6 UI code generator 6.2.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PySide6 import QtCore, QtGui, QtWidgets


class Ui_cmdVoice(object):
    def setupUi(self, cmdVoice):
        cmdVoice.setObjectName("cmdVoice")
        cmdVoice.resize(1021, 46)
        self.horizontalLayout = QtWidgets.QHBoxLayout(cmdVoice)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20,QtWidgets.QSizePolicy.Policy.Expanding,QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.retranslateUi(cmdVoice)
        QtCore.QMetaObject.connectSlotsByName(cmdVoice)

    def retranslateUi(self, cmdVoice):
        _translate = QtCore.QCoreApplication.translate
        cmdVoice.setWindowTitle(_translate("cmdVoice", "Form"))
