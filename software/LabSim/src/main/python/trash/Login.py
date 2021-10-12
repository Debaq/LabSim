# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Login.ui'
#
# Created by: PyQt6 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Login(object):
    def setupUi(self, Login):
        Login.setObjectName("Login")
        Login.resize(250, 350)
        Login.setAutoFillBackground(True)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Login)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalFrame = QtWidgets.QFrame(Login)
        self.verticalFrame.setStyleSheet("background-color: rgb(170, 170, 255);")
        self.verticalFrame.setFrameShape(QtWidgets.QFrame.Box)
        self.verticalFrame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.verticalFrame.setObjectName("verticalFrame")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalFrame)
        self.verticalLayout_3.setContentsMargins(-1, -1, -1, 1)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem)
        self.label_5 = QtWidgets.QLabel(self.verticalFrame)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_6.addWidget(self.label_5)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.label = QtWidgets.QLabel(self.verticalFrame)
        self.label.setMaximumSize(QtCore.QSize(16777215, 40))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setAutoFillBackground(False)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.line = QtWidgets.QFrame(self.verticalFrame)
        self.line.setFrameShadow(QtWidgets.QFrame.Plain)
        self.line.setLineWidth(3)
        self.line.setMidLineWidth(0)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setObjectName("line")
        self.verticalLayout_3.addWidget(self.line)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.verticalFrame)
        self.label_2.setAutoFillBackground(False)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.line_user = QtWidgets.QLineEdit(self.verticalFrame)
        self.line_user.setMinimumSize(QtCore.QSize(130, 0))
        self.line_user.setMaximumSize(QtCore.QSize(130, 16777215))
        self.line_user.setAutoFillBackground(False)
        self.line_user.setObjectName("line_user")
        self.horizontalLayout.addWidget(self.line_user)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.verticalFrame)
        self.label_3.setAutoFillBackground(False)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.line_pass = QtWidgets.QLineEdit(self.verticalFrame)
        self.line_pass.setMinimumSize(QtCore.QSize(130, 0))
        self.line_pass.setMaximumSize(QtCore.QSize(130, 16777215))
        self.line_pass.setAutoFillBackground(False)
        self.line_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.line_pass.setObjectName("line_pass")
        self.horizontalLayout_2.addWidget(self.line_pass)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.btn_login = QtWidgets.QPushButton(self.verticalFrame)
        self.btn_login.setAutoFillBackground(False)
        self.btn_login.setObjectName("btn_login")
        self.horizontalLayout_3.addWidget(self.btn_login)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem4)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.line_2 = QtWidgets.QFrame(self.verticalFrame)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Plain)
        self.line_2.setLineWidth(3)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setObjectName("line_2")
        self.verticalLayout_3.addWidget(self.line_2)
        self.label_4 = QtWidgets.QLabel(self.verticalFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setMinimumSize(QtCore.QSize(0, 0))
        self.label_4.setMaximumSize(QtCore.QSize(16777215, 15))
        self.label_4.setObjectName("label_4")
        self.verticalLayout_3.addWidget(self.label_4)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem5 = QtWidgets.QSpacerItem(40, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem5)
        self.btn_load_scene = QtWidgets.QPushButton(self.verticalFrame)
        self.btn_load_scene.setAutoFillBackground(False)
        self.btn_load_scene.setObjectName("btn_load_scene")
        self.horizontalLayout_4.addWidget(self.btn_load_scene)
        spacerItem6 = QtWidgets.QSpacerItem(40, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem6)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.line_3 = QtWidgets.QFrame(self.verticalFrame)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Plain)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setObjectName("line_3")
        self.verticalLayout_3.addWidget(self.line_3)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.line_scene = QtWidgets.QLineEdit(self.verticalFrame)
        self.line_scene.setObjectName("line_scene")
        self.horizontalLayout_5.addWidget(self.line_scene)
        self.btn_code_scene = QtWidgets.QPushButton(self.verticalFrame)
        self.btn_code_scene.setObjectName("btn_code_scene")
        self.horizontalLayout_5.addWidget(self.btn_code_scene)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.verticalLayout_2.addWidget(self.verticalFrame)

        self.retranslateUi(Login)
        QtCore.QMetaObject.connectSlotsByName(Login)

    def retranslateUi(self, Login):
        _translate = QtCore.QCoreApplication.translate
        Login.setWindowTitle(_translate("Login", "Login"))
        self.label_5.setText(_translate("Login", "X"))
        self.label.setText(_translate("Login", "LabSim : Audios"))
        self.label_2.setText(_translate("Login", "Usuario :"))
        self.label_3.setText(_translate("Login", "Contraseña :"))
        self.btn_login.setText(_translate("Login", "Ingresar"))
        self.label_4.setText(_translate("Login", "Otros Medios"))
        self.btn_load_scene.setText(_translate("Login", "Abrir escenario"))
        self.btn_code_scene.setText(_translate("Login", "código"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Login = QtWidgets.QWidget()
    ui = Ui_Login()
    ui.setupUi(Login)
    Login.show()
    sys.exit(app.exec_())
