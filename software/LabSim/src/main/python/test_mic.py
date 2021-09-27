from PyQt5.QtWidgets import *
import sys

class MyWidget(QWidget):
    def __init__(self, parent, labelname, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.resize(350, 40)
        
        self.labelButton = QPushButton(self)
        self.labelButton.setText(str(labelname))
        self.labelButton.resize(300, 40)
        self.labelButton.move(0, 0)
        self.labelButton.clicked.connect(self.printbutton)

        self.buttonErase = QPushButton(self)
        self.buttonErase.setText("X")
        self.buttonErase.resize(40, 40)
        self.buttonErase.move(310, 0)
        self.buttonErase.clicked.connect(self.erasebutton)

        self.show()

    def printbutton(self):
        print('clicked:', self.labelButton.text())

    def erasebutton(self):
        print('clicked:', self.buttonErase.text())
        print('  erase:', self.labelButton.text())


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100, 100, 1500, 1500)
        self.setWindowTitle("My Program")
        self.widgets = []
        self.Yposition = 50
        self.initUI()

    def initUI(self):
        self.labelEntry = QLineEdit(self)
        self.labelEntry.move(50, self.Yposition)
        self.labelEntry.resize(300, 40)

        self.addLabelButton = QPushButton(self)
        self.addLabelButton.setText("Add Label")
        self.addLabelButton.move(400, self.Yposition)
        self.addLabelButton.resize(300, 40)
        self.addLabelButton.clicked.connect(self.addNewLabel)

    def addNewLabel(self):
        self.Yposition += 50
        text = self.labelEntry.text()
                
        widget = MyWidget(self, text)
        widget.move(50, self.Yposition)
        
        self.widgets.append(widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())