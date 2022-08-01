# -*- coding: utf-8 -*-
import sys
from PySide6.QtWidgets import QWidget
from UI.Ui_CVC import Ui_CVC





class Audiometer(QWidget, Ui_CVC):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.show()
        
if __name__ == '__main__':
    window = Audiometer()
    exit_code = context.app.exec_()
    sys.exit(exit_code)