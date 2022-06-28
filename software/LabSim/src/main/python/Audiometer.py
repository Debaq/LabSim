# -*- coding: utf-8 -*-
from base import context

import sys
from PySide6.QtWidgets import QWidget, QApplication,QMainWindow

from UI.Ui_CVC import Ui_CVC





class Audiometer(QWidget, Ui_CVC):
    def __init__(self):
        super(Audiometer, self).__init__()
        self.setupUi(self)


app = QWidget(sys.argv)

window = Audiometer()
window.show()
app.exec_()
