from PySide6.QtWidgets import QApplication, QFileDialog
from datetime import datetime


def printer(self, widget):
    screen = QApplication.primaryScreen()
    screenshot = screen.grabWindow(widget)
    now = datetime.now()
    current_time = now.strftime("%d-%m-%y_%H_%M_%S")        
    file = str(QFileDialog.getExistingDirectory(self, "Seleccionar destino"))
    name = file + '/'+ current_time + '.jpg'
    screenshot.save(name, 'jpg')

def date_time():
    now = datetime.now()
    current_time = now.strftime("%d/%m/%y %H:%M:%S")
    return current_time
    
def changeSide(side):
    if side == 1:
        result = 0
    else :
        result = 1
    return result

def changeSideText(side):
    _,text = side.split('_')
    if text == 'OD':
        result = 0
    else :
        result = 1
    return changeSide(result)


def sideText(side):
    print(side)
    _,text = side.split('_')
    if text == 'OD':
        result = 0
    else :
        result = 1
    return result

def getSideText(side):
    _,text = side.split('_')
    return text

