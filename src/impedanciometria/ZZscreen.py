import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QGraphicsRectItem
from PySide6.QtCore import Qt
import numpy as np
from impedanciometria.UI.Ui_Z_screen_z import Ui_Z_zscreen


class ZZscreen(QWidget, Ui_Z_zscreen):
    def __init__(self):
        # Inicialización de la ventana y propiedades
        QWidget.__init__(self)
        self.setupUi(self)
        self.create_graph()

    def create_graph(self, clear=False):
        if clear:
            self.pw1.clear()
            self.ploty.clear()
            self.ploty.setData()

        color = pg.mkColor(85,170,255,255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        self.pw1 = pg.PlotWidget(name='Plot1', background='default')
        self.pw1.setXRange(-405,205)
        self.pw1.setYRange(0,1.8)
        self.pw1.setLabel('left', '', units ='ml')
        self.pw1.setLabel('bottom', '', units ='daPa')
        self.pw1.setMouseEnabled(x=False, y=False)
        self.pw1.setMenuEnabled(False)
        pen1 = pg.mkPen('w', width=1, style=Qt.PenStyle.DashLine)          ## Make a dashed yellow line 2px wide
        self.inf1 = pg.InfiniteLine(movable=False, angle=90, pen=pen1)
        self.pw1.addItem(self.inf1)

        self.gradient_box = QGraphicsRectItem(0, 0, 0, 0)
        self.gradient_box.setPen(pg.mkPen('y', width=1, style=Qt.PenStyle.DashLine))
        self.gradient_box.setBrush(pg.mkBrush(255, 255, 0, 25))
        self.gradient_box.setVisible(False)
        self.pw1.addItem(self.gradient_box)

        self.ploty = self.pw1.plot()
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
    
    def set_gradient_box(self, p, c):
        if p is None or c is None or c <= 0:
            self.gradient_box.setVisible(False)
            return
        self.gradient_box.setRect(p-50, 0, 100, c)
        self.gradient_box.setVisible(True)

    def set_window(self, neg, pos):
        self.label.setText(f"{neg} daPa")
        self.label_4.setText(f"{pos} daPa")
        self.pw1.setXRange(neg-5, pos+5)

    def set_height(self, cc):
        self.label_5.setText(f"{cc} cc")
        self.pw1.setYRange(0, cc)

    def set_direction(self, text):
        self.label_6.setText(text)

    def set_side(self, side):
        self.lbl_side.setText(side)

    def set_probe_freq(self, freq):
        self.lbl_probe_freq.setText(f"{freq} Hz")
        
    def get_side(self):
        return self.lbl_side.text()

    def clearData(self):
        x = []
        y = []
        self.ploty.setData(x, y, pen='w')
        self.gradient_box.setVisible(False)

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
