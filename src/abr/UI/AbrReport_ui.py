# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'AbrReport.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QKeySequence, QLinearGradient, QPalette,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QSizePolicy,
    QSpacerItem, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_AbrReport(object):
    def setupUi(self, AbrReport):
        if not AbrReport.objectName():
            AbrReport.setObjectName(u"AbrReport")
        AbrReport.resize(951, 620)
        self.gridLayout = QGridLayout(AbrReport)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, -1, -1, 0)
        self.tabWidget = QTabWidget(AbrReport)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setTabPosition(QTabWidget.South)
        self.tabWidget.setTabShape(QTabWidget.Triangular)
        self.tabWidget.setDocumentMode(True)
        self.tab_1 = QWidget()
        self.tab_1.setObjectName(u"tab_1")
        self.verticalLayout = QVBoxLayout(self.tab_1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.lbl_date = QLabel(self.tab_1)
        self.lbl_date.setObjectName(u"lbl_date")

        self.horizontalLayout.addWidget(self.lbl_date)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label = QLabel(self.tab_1)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.label_2 = QLabel(self.tab_1)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.label_3 = QLabel(self.tab_1)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.text_edit_1 = QTextEdit(self.tab_1)
        self.text_edit_1.setObjectName(u"text_edit_1")

        self.verticalLayout.addWidget(self.text_edit_1)

        self.label_4 = QLabel(self.tab_1)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.text_edit_2 = QTextEdit(self.tab_1)
        self.text_edit_2.setObjectName(u"text_edit_2")

        self.verticalLayout.addWidget(self.text_edit_2)

        self.le_eva = QLineEdit(self.tab_1)
        self.le_eva.setObjectName(u"le_eva")

        self.verticalLayout.addWidget(self.le_eva)

        self.tabWidget.addTab(self.tab_1, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget.addTab(self.tab_2, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)


        self.retranslateUi(AbrReport)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AbrReport)
    # setupUi

    def retranslateUi(self, AbrReport):
        AbrReport.setWindowTitle(QCoreApplication.translate("AbrReport", u"Form", None))
        self.lbl_date.setText(QCoreApplication.translate("AbrReport", u"TextLabel", None))
        self.label.setText(QCoreApplication.translate("AbrReport", u"POTENCIALES EVOCADOS AUDITIVOS DE TRONCO CEREBRAL", None))
        self.label_2.setText(QCoreApplication.translate("AbrReport", u"PEATC", None))
        self.label_3.setText(QCoreApplication.translate("AbrReport", u"Descripci\u00f3n", None))
        self.text_edit_1.setHtml(QCoreApplication.translate("AbrReport", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Sans Serif'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.label_4.setText(QCoreApplication.translate("AbrReport", u"Conclusi\u00f3n", None))
        self.text_edit_2.setHtml(QCoreApplication.translate("AbrReport", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Sans Serif'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.le_eva.setPlaceholderText(QCoreApplication.translate("AbrReport", u"Evaluador/a", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), QCoreApplication.translate("AbrReport", u"Conclusiones", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("AbrReport", u"Esquema", None))
    # retranslateUi

