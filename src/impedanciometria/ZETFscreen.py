import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt


class ZETFscreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(580, 280)
        self.setMaximumSize(580, 280)
        self.setStyleSheet("font: 10pt \"Monospace\";\ncolor: rgb(255, 255, 255);")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_layout = QHBoxLayout()
        header = QLabel("ETF")
        header.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header)
        self.lbl_pressure = QLabel("0 daPa")
        self.lbl_pressure.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.lbl_pressure)
        layout.addLayout(header_layout)

        graph_frame = QFrame(self)
        graph_frame.setFrameShape(QFrame.Box)
        graph_layout = QVBoxLayout(graph_frame)
        layout.addWidget(graph_frame)

        color = pg.mkColor(85, 170, 255, 255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        pw1 = pg.PlotWidget(name='Plot1', background='default')
        pw1.setRange(yRange=(-400, 200), xRange=(0, 10), disableAutoRange=True)
        pw1.showGrid(x=True, y=True)
        pw1.setMouseEnabled(x=False, y=False)
        pw1.setMenuEnabled(False)
        pw1.setLabel(axis='bottom', text='S')
        pw1.setLabel(axis='left', text='daPa')
        graph_layout.addWidget(pw1)

    def set_pressure(self, pressure):
        self.lbl_pressure.setText(f"{pressure} daPa")


if __name__ == "__main__":
    pass
