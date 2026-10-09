"""Pantalla "Tone Decay": decay del reflejo estapedial.

Protocolo clásico: tono de 500 o 1000 Hz, ipsi o contra, unos 10 dB sobre el
umbral del reflejo, sostenido 10 s. La traza muestra la contracción en el
tiempo y, a la derecha, cuánto de la amplitud inicial queda a los 5 y a los
10 s. El equipo no interpreta: lo concluye el alumno.

Las teclas bajo la pantalla (ver la fila de rótulos de abajo):
1 frecuencia · 2 Inicio · 3 intensidad · 4 IPSI/CONTRA · 6 presión.
"""
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from impedanciometria.z_generator import DECAY_DURACION_S

DECAY_FRECUENCIAS = ['500', '1000']


def _rotulo(texto="", alinear=Qt.AlignCenter):
    lbl = QLabel(texto)
    lbl.setAlignment(alinear)
    return lbl


class ZDscreen(QWidget):
    start_clicked = Signal()
    ipsi_clicked = Signal()
    contra_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(580, 280)
        self.setMaximumSize(580, 280)
        self.setStyleSheet("font: 10pt \"Monospace\";\ncolor: rgb(255, 255, 255);")

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        cabecera = QHBoxLayout()
        cabecera.addWidget(_rotulo("Tone Decay"))
        self.lbl_side = _rotulo("OD")
        self.lbl_mode = _rotulo("IPSI")
        cabecera.addWidget(self.lbl_side)
        cabecera.addWidget(self.lbl_mode)
        raiz.addLayout(cabecera)

        centro = QHBoxLayout()
        marco = QFrame(self)
        marco.setFrameShape(QFrame.Box)
        marco_layout = QVBoxLayout(marco)
        marco_layout.setContentsMargins(2, 2, 2, 2)
        color = pg.mkColor(85, 170, 255, 255)
        pg.setConfigOption('background', color)
        pg.setConfigOption('foreground', 'w')
        self.pw = pg.PlotWidget(background='default')
        self.pw.setRange(yRange=(-150, 150), xRange=(0, DECAY_DURACION_S), disableAutoRange=True)
        self.pw.showGrid(x=True, y=True)
        self.pw.setMouseEnabled(x=False, y=False)
        self.pw.setMenuEnabled(False)
        self.pw.setLabel(axis='bottom', text='S')
        self.pw.setLabel(axis='left', text='μl')
        self.pw.getAxis('bottom').setTicks([[(v, str(v)) for v in (0, 1, 6, 11, 12)]])
        self.pw.getAxis('left').setTicks([[(v, str(v)) for v in (-150, 0, 150)]])
        self.curve = self.pw.plot([], [], pen=pg.mkPen('y', width=2))
        marco_layout.addWidget(self.pw)
        centro.addWidget(marco, 1)

        lateral = QVBoxLayout()
        lateral.addWidget(_rotulo("Amplitud", Qt.AlignLeft))
        self.lbl_5s = _rotulo(" 5 s: ---- %", Qt.AlignLeft)
        self.lbl_10s = _rotulo("10 s: ---- %", Qt.AlignLeft)
        lateral.addWidget(self.lbl_5s)
        lateral.addWidget(self.lbl_10s)
        lateral.addStretch(1)
        self.lbl_vol = _rotulo("Vol.: N/D ml", Qt.AlignLeft)
        lateral.addWidget(self.lbl_vol)
        centro.addLayout(lateral)
        raiz.addLayout(centro, 1)

        # Rótulos de las seis teclas de abajo, en el mismo orden.
        teclas = QHBoxLayout()
        self.lbl_freq = _rotulo("1000 Hz")
        self.lbl_inicio = _rotulo("Inicio")
        self.lbl_db = _rotulo("85 dB")
        self.lbl_ipsi = _rotulo("IPSI")
        self.lbl_contra = _rotulo("CONTRA")
        self.lbl_presion = _rotulo("0 daP")
        for lbl in (self.lbl_freq, self.lbl_inicio, self.lbl_db, self.lbl_ipsi,
                    self.lbl_contra, self.lbl_presion):
            teclas.addWidget(lbl)
        for lbl, senal in ((self.lbl_inicio, self.start_clicked),
                           (self.lbl_ipsi, self.ipsi_clicked),
                           (self.lbl_contra, self.contra_clicked)):
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.mousePressEvent = lambda ev, s=senal: s.emit()
        raiz.addLayout(teclas)

    # Mismos nombres que ZRscreen: Z.py los llama sobre las dos pantallas.
    def set_side(self, side):
        self.lbl_side.setText(side)

    def set_mode(self, mode):
        self.lbl_mode.setText(mode)

    def set_intensity(self, db):
        self.lbl_db.setText(f"{db} dB")

    def set_pressure(self, pressure):
        self.lbl_presion.setText(f"{pressure} daP")

    def set_volume(self, vol):
        self.lbl_vol.setText(f"Vol.: {vol} ml" if vol is not None else "Vol.: N/D ml")

    def set_freq(self, freq):
        self.lbl_freq.setText(f"{freq} Hz")

    def set_result(self, pct5, pct10):
        self.lbl_5s.setText(f" 5 s: {pct5:>3} %" if pct5 is not None else " 5 s: ---- %")
        self.lbl_10s.setText(f"10 s: {pct10:>3} %" if pct10 is not None else "10 s: ---- %")

    def plot_response(self, x, y):
        self.curve.setData(x, y)

    def clear_response(self):
        self.curve.setData([], [])
        self.set_result(None, None)


if __name__ == "__main__":
    pass
