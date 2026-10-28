# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'AbrMain.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1016, 826)
        MainWindow.setDocumentMode(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_3 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(2, 0, 2, 0)
        self.layout_cuerpo = QHBoxLayout()
        self.layout_cuerpo.setSpacing(6)
        self.layout_cuerpo.setObjectName(u"layout_cuerpo")
        self.panel_izquierdo = QWidget(self.centralwidget)
        self.panel_izquierdo.setObjectName(u"panel_izquierdo")
        self.panel_izquierdo.setMinimumSize(QSize(318, 0))
        self.panel_izquierdo.setMaximumSize(QSize(318, 16777215))
        self.layout_panel_izquierdo = QVBoxLayout(self.panel_izquierdo)
        self.layout_panel_izquierdo.setObjectName(u"layout_panel_izquierdo")
        self.layout_panel_izquierdo.setContentsMargins(3, 3, 3, 3)

        self.layout_cuerpo.addWidget(self.panel_izquierdo)

        self.layout_derecha = QVBoxLayout()
        self.layout_derecha.setSpacing(0)
        self.layout_derecha.setObjectName(u"layout_derecha")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.lbl_info = QLabel(self.centralwidget)
        self.lbl_info.setObjectName(u"lbl_info")

        self.horizontalLayout.addWidget(self.lbl_info)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.layout_derecha.addLayout(self.horizontalLayout)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setMinimumSize(QSize(500, 0))
        self.tabWidget.setUsesScrollButtons(True)
        self.abr = QWidget()
        self.abr.setObjectName(u"abr")
        self.layout_abr_frame = QHBoxLayout(self.abr)
        self.layout_abr_frame.setSpacing(0)
        self.layout_abr_frame.setObjectName(u"layout_abr_frame")
        self.layout_abr_frame.setContentsMargins(0, 0, 0, 0)
        self.verticalFrame = QFrame(self.abr)
        self.verticalFrame.setObjectName(u"verticalFrame")
        self.verticalFrame.setMaximumSize(QSize(30, 16777215))
        self.verticalLayout = QVBoxLayout(self.verticalFrame)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 20, 0, 0)
        self.btn_scale_plus = QPushButton(self.verticalFrame)
        self.btn_scale_plus.setObjectName(u"btn_scale_plus")

        self.verticalLayout.addWidget(self.btn_scale_plus)

        self.lbl_scale = QLabel(self.verticalFrame)
        self.lbl_scale.setObjectName(u"lbl_scale")
        font = QFont()
        font.setPointSize(8)
        self.lbl_scale.setFont(font)
        self.lbl_scale.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_scale)

        self.btn_scale_minus = QPushButton(self.verticalFrame)
        self.btn_scale_minus.setObjectName(u"btn_scale_minus")

        self.verticalLayout.addWidget(self.btn_scale_minus)

        self.btn_toggle_sub = QPushButton(self.verticalFrame)
        self.btn_toggle_sub.setObjectName(u"btn_toggle_sub")
        self.btn_toggle_sub.setCheckable(True)
        self.btn_toggle_sub.setChecked(True)

        self.verticalLayout.addWidget(self.btn_toggle_sub)

        self.btn_toggle_contra = QPushButton(self.verticalFrame)
        self.btn_toggle_contra.setObjectName(u"btn_toggle_contra")
        self.btn_toggle_contra.setCheckable(True)
        self.btn_toggle_contra.setChecked(True)

        self.verticalLayout.addWidget(self.btn_toggle_contra)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.layout_abr_frame.addWidget(self.verticalFrame)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.layout_abr = QHBoxLayout()
        self.layout_abr.setObjectName(u"layout_abr")

        self.verticalLayout_2.addLayout(self.layout_abr)



        self.layout_abr_frame.addLayout(self.verticalLayout_2)

        self.tabWidget.addTab(self.abr, "")
        self.lat = QWidget()
        self.lat.setObjectName(u"lat")
        self.layout_lat_int = QHBoxLayout(self.lat)
        self.layout_lat_int.setObjectName(u"layout_lat_int")
        self.tabWidget.addTab(self.lat, "")
        self.conc = QWidget()
        self.conc.setObjectName(u"conc")
        self.layout_report = QHBoxLayout(self.conc)
        self.layout_report.setSpacing(0)
        self.layout_report.setObjectName(u"layout_report")
        self.layout_report.setContentsMargins(-1, -1, -1, 0)
        self.tabWidget.addTab(self.conc, "")

        self.layout_derecha.addWidget(self.tabWidget)

        self.panel_monitor = QWidget(self.centralwidget)
        self.panel_monitor.setObjectName(u"panel_monitor")
        self.layout_panel_monitor = QVBoxLayout(self.panel_monitor)
        self.layout_panel_monitor.setSpacing(0)
        self.layout_panel_monitor.setObjectName(u"layout_panel_monitor")
        self.layout_panel_monitor.setContentsMargins(0, 0, 0, 0)

        self.layout_derecha.addWidget(self.panel_monitor)


        self.layout_cuerpo.addLayout(self.layout_derecha)


        self.verticalLayout_3.addLayout(self.layout_cuerpo)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.lbl_info.setText("")
        self.btn_scale_plus.setText(QCoreApplication.translate("MainWindow", u"+", None))
        self.lbl_scale.setText(QCoreApplication.translate("MainWindow", u"8\u00b5V", None))
        self.btn_scale_minus.setText(QCoreApplication.translate("MainWindow", u"-", None))
#if QT_CONFIG(tooltip)
        self.btn_toggle_sub.setToolTip(QCoreApplication.translate("MainWindow", u"Mostrar/ocultar subpromedios A/B", None))
#endif // QT_CONFIG(tooltip)
        self.btn_toggle_sub.setText(QCoreApplication.translate("MainWindow", u"AB", None))
#if QT_CONFIG(tooltip)
        self.btn_toggle_contra.setToolTip(QCoreApplication.translate("MainWindow", u"Mostrar/ocultar canal contralateral", None))
#endif // QT_CONFIG(tooltip)
        self.btn_toggle_contra.setText(QCoreApplication.translate("MainWindow", u"C", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.abr), QCoreApplication.translate("MainWindow", u"Gr\u00e1ficos", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.lat), QCoreApplication.translate("MainWindow", u"Latencia/Intensidad", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.conc), QCoreApplication.translate("MainWindow", u"Conclusiones", None))
    # retranslateUi

