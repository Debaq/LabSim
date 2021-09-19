import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('test_java')
        self.setGeometry(5,30,1355,730)
        self.browser = QWebEngineView()
        url = QUrl.fromLocalFile(r"/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/python/test/test.html")
        self.browser.load(url)
        self.setCentralWidget(self.browser)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    win=MainWindow()
    win.show()
    app.exit(app.exec_())