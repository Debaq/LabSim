import pyqtgraph as pg
from PySide6.QtWidgets import QWidget

from impedanciometria.UI.Ui_Z_screen_r import Ui_Z_rscreen
from impedanciometria.UI.Ui_Z_screen_d import Ui_Z_dscreen



class ZDscreen(QWidget, Ui_Z_dscreen):
    def __init__(self):
        # Inicialización de la ventana y propiedades
        QWidget.__init__(self)
        self.setupUi(self)
        color = pg.mkColor(85,170,255,255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        pw1 = pg.PlotWidget(name='Plot1', background='default')
        pw1.setRange(yRange = (-225, 225), xRange = (0, 12), disableAutoRange=True)
        pw1.showGrid(x=True, y=True)
        pw1.setMouseEnabled(x=False, y=False)
        pw1.setMenuEnabled(False)
        ax = pw1.getAxis('bottom')
        ay = pw1.getAxis('left')
        pw1.setLabel(axis='bottom', text='S')
        pw1.setLabel(axis='left', text='μl')
        ticksx = [ 12]
        ticksy = [-225,0, 225]
        ax.setTicks([[(v, str(v)) for v in ticksx ]])
        ay.setTicks([[(v, str(v)) for v in ticksy ]])
        self.graph.addWidget(pw1)

    def set_intensity(self, db):
        self.label_6.setText(f"{db} dB")

    def set_pressure(self, pressure):
        self.label.setText(f"{pressure} daP")


if __name__ == "__main__":
    pass
