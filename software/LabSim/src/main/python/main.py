# -*- coding utf-8 -*-

import sys
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

__VERSION__ = "0.9.1"

#from libs.exchange_data import *



if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.load(os.path.join(os.path.dirname(__file__), 'data/qml/main.qml'))
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec_())
