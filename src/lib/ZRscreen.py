import pyqtgraph as pg
from PySide6.QtWidgets import QWidget

from UI.Ui_Z_screen_r import Ui_Z_rscreen




class ZRscreen(QWidget, Ui_Z_rscreen):
    def __init__(self):
        # Inicialización de la ventana y propiedades
        QWidget.__init__(self)
        self.setupUi(self)
        color = pg.mkColor(85,170,255,255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        pw1 = pg.PlotWidget(name='Plot1', background='default')
        pw1.setRange(yRange = (-150, 150), xRange = (0, 2), disableAutoRange=True)
        pw1.showGrid(x=True, y=True)
        pw1.setMouseEnabled(x=False, y=False)
        pw1.setMenuEnabled(False)
        ax = pw1.getAxis('bottom')
        ay = pw1.getAxis('left')
        pw1.setLabel(axis='bottom', text='S')
        pw1.setLabel(axis='left', text='μl')
        ticksx = [ 2]
        ticksy = [-150,0, 150]
        ax.setTicks([[(v, str(v)) for v in ticksx ]])
        ay.setTicks([[(v, str(v)) for v in ticksy ]])
        self.graph.addWidget(pw1)

if __name__ == "__main__":
    pass
