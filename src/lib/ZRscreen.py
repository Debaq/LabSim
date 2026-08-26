import pyqtgraph as pg
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal

from UI.Ui_Z_screen_r import Ui_Z_rscreen




class ZRscreen(QWidget, Ui_Z_rscreen):
    start_clicked = Signal()
    ipsi_clicked = Signal()
    contra_clicked = Signal()

    def __init__(self):
        # Inicialización de la ventana y propiedades
        QWidget.__init__(self)
        self.setupUi(self)

        for label, signal in (
            (self.label_4, self.start_clicked),
            (self.label_5, self.ipsi_clicked),
            (self.label_3, self.contra_clicked),
        ):
            label.setCursor(Qt.PointingHandCursor)
            label.mousePressEvent = lambda ev, s=signal: s.emit()
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
        self.pw1 = pw1
        self.curve = pw1.plot([], [], pen=pg.mkPen('y', width=2))

    def set_mode(self, mode):
        self.label_22.setText(mode)

    def set_intensity(self, db):
        self.label_6.setText(f"{db} dB")

    def set_pressure(self, pressure):
        self.label.setText(f"{pressure} daP")

    def set_volume(self, vol):
        self.label_18.setText(f"{vol} ml" if vol is not None else "N/D ml")

    def set_freq(self, freq):
        self.label_2.setText(freq if freq == 'NBN' else f"{freq} Hz")

    def set_nbn_enabled(self, enabled):
        self.label_21.setEnabled(enabled)
        self.label_20.setEnabled(enabled)
        if not enabled:
            self.label_20.setText("N/A")
        elif self.label_20.text() == "N/A":
            self.label_20.setText("----")

    def set_results(self, values):
        labels = [self.label_9, self.label_12, self.label_14, self.label_16, self.label_20]
        for i, lbl in enumerate(labels):
            if i == 4 and not lbl.isEnabled():
                continue
            value = values[i] if i < len(values) else None
            lbl.setText(f"{value} dB" if value is not None else "----")

    def plot_response(self, x, y):
        self.curve.setData(x, y)

    def clear_response(self):
        self.curve.setData([], [])

if __name__ == "__main__":
    pass
