import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
import numpy as np
from UI.Ui_Z_screen_z import Ui_Z_zscreen


class ZZscreen(QWidget, Ui_Z_zscreen):
    def __init__(self):
        # Inicialización de la ventana y propiedades
        print("iniciando wid")
        
        QWidget.__init__(self)
        print("iniciando wid 2")
        
        self.setupUi(self)
        print("iniciado setup")

        self.create_graph()

    def create_graph(self, clear=False):
        if clear:
            self.pw1.clear()
            self.ploty.clear()
            self.ploty.setData()

        color = pg.mkColor(85,170,255,255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        print("hasta aca todo ok 0")

        self.pw1 = pg.PlotWidget(name='Plot1', background='default')
        print("hasta aca todo ok 1")

        self.pw1.setXRange(-405,205)
        self.pw1.setYRange(0,1.8)
        print("hasta aca todo ok 2")

        self.pw1.setLabel('left', '', units ='ml')
        self.pw1.setLabel('bottom', '', units ='daPa')
        print("hasta aca todo ok 3")

        self.pw1.setMouseEnabled(x=False, y=False)
        self.pw1.setMenuEnabled(False)
        print("hasta aca todo ok 4")

        pen1 = pg.mkPen('w', width=1, style=Qt.PenStyle.DashLine)          ## Make a dashed yellow line 2px wide
        self.inf1 = pg.InfiniteLine(movable=False, angle=90, pen=pen1)
        print("hasta aca todo ok 5")

        self.pw1.addItem(self.inf1)
        self.ploty = self.pw1.plot()
        print("hasta aca todo ok 6")

        self.graph.addWidget(self.pw1)
    
    def update_graph(self, x,y):
        idx_y = y.index(max(y))
        pos_max = x[idx_y]
        self.inf1.setPos([pos_max,2])
        #pen_color = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
        #pen_idx = random.randint(0,7)
        self.ploty.setData(x, y, pen='w')

    def move_mark(self, pos):
        
        pos_mark = self.inf1.value() + pos*2
        
        self.inf1.setPos([pos_mark,2])
        return pos_mark
    
    def set_side(self, side):
        self.lbl_side.setText(side)
        
    def get_side(self):
        return self.lbl_side.text()

    def clearData(self):
        x = []
        y = []
        self.ploty.setData(x, y, pen='w')

    def find_nearest(self, array_in, value, array_out):
        array = np.asarray(array_in)
        idx = (np.abs(array - value)).argmin()
        return array_out[idx]

    def clear_lbl(self):
        self.lbl_p.setText("")
        self.lbl_c.setText("")
        self.lbl_v.setText("")
        self.lbl_g.setText("")

if __name__ == "__main__":
    pass
