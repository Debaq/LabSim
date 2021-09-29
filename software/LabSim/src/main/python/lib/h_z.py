from PyQt5.QtWidgets import QApplication, QFileDialog
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
    _,text = side.split('_')
    if text == 'OD':
        result = 0
    else :
        result = 1
    return result

def getSideText(side):
    _,text = side.split('_')
    return text


class storage():
    def __init__(self, n):
        self.n = n
        self.data = []
        self.create(n)

    def create(self,n):
        for i in range(n):
            self.data.append(None)
    
    def clean(self):
        self.data = []
        self.create(self.n)

    def get(self, idx):
        return self.data[idx]
    
    def set(self, idx, dat):
        self.data[idx] = dat

    def agrege(self, idx, dat):
        try:
            self.data[idx].append(dat)
        except:
            self.data[idx] = list()
            self.data[idx].append(dat)


    def isFull(self, idx):
        state = True
        if self.data[idx] == None:
            state = False
        return state
    
    def isNull(self, idx):
        return not self.isFull(idx)

    def isEmpty(self):
        state = False
        for i in self.data:
            if i == None:
                state = True
        return state