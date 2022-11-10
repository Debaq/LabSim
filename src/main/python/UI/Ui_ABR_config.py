# Form implementation generated from reading ui file 'ABR_config.ui'
#
# Created by: PySide6 UI code generator 6.2.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PySide6 import QtCore, QtGui, QtWidgets


class Ui_ABR_config(object):
    def setupUi(self, ABR_config):
        ABR_config.setObjectName("ABR_config")
        ABR_config.resize(255, 462)
        self.verticalLayout = QtWidgets.QVBoxLayout(ABR_config)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(ABR_config)
        self.groupBox.setMinimumSize(QtCore.QSize(150, 0))
        self.groupBox.setMaximumSize(QtCore.QSize(150, 16777215))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.groupBox.setFont(font)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.groupBox.setChecked(False)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout_2.setSpacing(3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.label_6.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_6.addWidget(self.label_6)
        self.cb_stim = QtWidgets.QComboBox(self.groupBox)
        self.cb_stim.setObjectName("cb_stim")
        self.cb_stim.addItem("")
        self.cb_stim.addItem("")
        self.horizontalLayout_6.addWidget(self.cb_stim)
        self.verticalLayout_2.addLayout(self.horizontalLayout_6)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.cb_pol = QtWidgets.QComboBox(self.groupBox)
        self.cb_pol.setObjectName("cb_pol")
        self.cb_pol.addItem("")
        self.cb_pol.addItem("")
        self.cb_pol.addItem("")
        self.horizontalLayout.addWidget(self.cb_pol)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_7.addWidget(self.label_7)
        self.sb_intencity = QtWidgets.QSpinBox(self.groupBox)
        self.sb_intencity.setEnabled(True)
        self.sb_intencity.setMinimumSize(QtCore.QSize(40, 0))
        self.sb_intencity.setMaximumSize(QtCore.QSize(100, 25))
        self.sb_intencity.setSuffix("")
        self.sb_intencity.setMaximum(100)
        self.sb_intencity.setSingleStep(5)
        self.sb_intencity.setProperty("value", 80)
        self.sb_intencity.setObjectName("sb_intencity")
        self.horizontalLayout_7.addWidget(self.sb_intencity)
        self.label_10 = QtWidgets.QLabel(self.groupBox)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_7.addWidget(self.label_10)
        self.sb_mskg = QtWidgets.QSpinBox(self.groupBox)
        self.sb_mskg.setEnabled(False)
        self.sb_mskg.setMaximumSize(QtCore.QSize(100, 25))
        self.sb_mskg.setSuffix("")
        self.sb_mskg.setPrefix("")
        self.sb_mskg.setMaximum(100)
        self.sb_mskg.setSingleStep(5)
        self.sb_mskg.setObjectName("sb_mskg")
        self.horizontalLayout_7.addWidget(self.sb_mskg)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.sb_rate = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.sb_rate.setDecimals(1)
        self.sb_rate.setSingleStep(0.1)
        self.sb_rate.setProperty("value", 10.1)
        self.sb_rate.setObjectName("sb_rate")
        self.horizontalLayout_5.addWidget(self.sb_rate)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.cb_filter_down = QtWidgets.QComboBox(self.groupBox)
        self.cb_filter_down.setObjectName("cb_filter_down")
        self.cb_filter_down.addItem("")
        self.cb_filter_down.addItem("")
        self.cb_filter_down.addItem("")
        self.cb_filter_down.addItem("")
        self.cb_filter_down.addItem("")
        self.cb_filter_down.addItem("")
        self.cb_filter_down.addItem("")
        self.cb_filter_down.addItem("")
        self.horizontalLayout_2.addWidget(self.cb_filter_down)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.cb_filter_up = QtWidgets.QComboBox(self.groupBox)
        self.cb_filter_up.setObjectName("cb_filter_up")
        self.cb_filter_up.addItem("")
        self.cb_filter_up.addItem("")
        self.cb_filter_up.addItem("")
        self.cb_filter_up.addItem("")
        self.cb_filter_up.addItem("")
        self.cb_filter_up.addItem("")
        self.horizontalLayout_4.addWidget(self.cb_filter_up)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.sb_prom = QtWidgets.QSpinBox(self.groupBox)
        self.sb_prom.setMaximum(8000)
        self.sb_prom.setProperty("value", 1000)
        self.sb_prom.setObjectName("sb_prom")
        self.horizontalLayout_3.addWidget(self.sb_prom)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_9 = QtWidgets.QLabel(self.groupBox)
        self.label_9.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_9.addWidget(self.label_9)
        self.cb_side = QtWidgets.QComboBox(self.groupBox)
        self.cb_side.setEnabled(True)
        self.cb_side.setMaximumSize(QtCore.QSize(150, 25))
        self.cb_side.setObjectName("cb_side")
        self.cb_side.addItem("")
        self.cb_side.addItem("")
        self.horizontalLayout_9.addWidget(self.cb_side)
        self.verticalLayout_2.addLayout(self.horizontalLayout_9)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(ABR_config)
        QtCore.QMetaObject.connectSlotsByName(ABR_config)

    def retranslateUi(self, ABR_config):
        _translate = QtCore.QCoreApplication.translate
        ABR_config.setWindowTitle(_translate("ABR_config", "Form"))
        self.groupBox.setTitle(_translate("ABR_config", "Configuración"))
        self.label_6.setText(_translate("ABR_config", "Estímulo :"))
        self.cb_stim.setItemText(0, _translate("ABR_config", "Clic"))
        self.cb_stim.setItemText(1, _translate("ABR_config", "Chirp"))
        self.label.setText(_translate("ABR_config", "Polaridad :"))
        self.cb_pol.setItemText(0, _translate("ABR_config", "Alternada"))
        self.cb_pol.setItemText(1, _translate("ABR_config", "Conden."))
        self.cb_pol.setItemText(2, _translate("ABR_config", "Rarefac."))
        self.label_7.setText(_translate("ABR_config", "Int."))
        self.label_10.setText(_translate("ABR_config", "Mkg."))
        self.label_5.setText(_translate("ABR_config", "Tasa :"))
        self.label_2.setText(_translate("ABR_config", "Pasa Bajo :"))
        self.cb_filter_down.setCurrentText(_translate("ABR_config", "1000"))
        self.cb_filter_down.setItemText(0, _translate("ABR_config", "1000"))
        self.cb_filter_down.setItemText(1, _translate("ABR_config", "1500"))
        self.cb_filter_down.setItemText(2, _translate("ABR_config", "2000"))
        self.cb_filter_down.setItemText(3, _translate("ABR_config", "2500"))
        self.cb_filter_down.setItemText(4, _translate("ABR_config", "3000"))
        self.cb_filter_down.setItemText(5, _translate("ABR_config", "3500"))
        self.cb_filter_down.setItemText(6, _translate("ABR_config", "4000"))
        self.cb_filter_down.setItemText(7, _translate("ABR_config", "4500"))
        self.label_4.setText(_translate("ABR_config", "Pasa Alto :"))
        self.cb_filter_up.setItemText(0, _translate("ABR_config", "50"))
        self.cb_filter_up.setItemText(1, _translate("ABR_config", "100"))
        self.cb_filter_up.setItemText(2, _translate("ABR_config", "200"))
        self.cb_filter_up.setItemText(3, _translate("ABR_config", "300"))
        self.cb_filter_up.setItemText(4, _translate("ABR_config", "400"))
        self.cb_filter_up.setItemText(5, _translate("ABR_config", "500"))
        self.label_3.setText(_translate("ABR_config", "Prom. :"))
        self.label_9.setText(_translate("ABR_config", "Lado"))
        self.cb_side.setItemText(0, _translate("ABR_config", "OD"))
        self.cb_side.setItemText(1, _translate("ABR_config", "OI"))
