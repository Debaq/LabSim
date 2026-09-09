"""
Monitor de EMG tónico del músculo registrador.

El equivalente VEMP del monitor de EEG crudo del ABR: el trazo que corre
SIEMPRE que hay un paciente cargado, promediando o no. Muestra cuánto está
contrayendo el paciente el músculo del que se registra (ECM en el cVEMP,
oblicuo inferior en el oVEMP, masetero en el mVEMP) y la banda en la que
ese registro es válido.

Es la mitad del examen que no se veía: la amplitud del VEMP escala con la
contracción, así que un cVEMP plano puede ser una respuesta ausente o un
paciente que soltó la cabeza, y sin este monitor las dos cosas se ven igual.
"""

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from vemp.VEMP_generator_v1 import EMG_BANDA, emg_en_banda

# Muestras visibles del trazo (a 300 ms por tick, ~15 s de historia).
N_MUESTRAS = 50


class VempEmg(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.subtipo = 'CVEMP'
        self.nivel = 0.0
        self.trace = np.zeros(N_MUESTRAS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.lbl = QLabel('EMG --')
        layout.addWidget(self.lbl)

        self.plot = pg.PlotWidget()
        self.plot.setBackground('w')
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        self.plot.getAxis('bottom').setStyle(showValues=False)
        self.plot.setLabel('left', 'µV')
        self.plot.setFixedHeight(90)
        layout.addWidget(self.plot)

        self.curve = self.plot.plot(pen=pg.mkPen((40, 40, 40), width=1))
        # Banda de EMG aceptable: entre esas dos líneas el registro vale.
        self._lo = pg.InfiniteLine(angle=0, pen=pg.mkPen((0, 140, 70), width=1,
                                                         style=Qt.PenStyle.DashLine))
        self._hi = pg.InfiniteLine(angle=0, pen=pg.mkPen((0, 140, 70), width=1,
                                                         style=Qt.PenStyle.DashLine))
        self.plot.addItem(self._lo)
        self.plot.addItem(self._hi)
        self.set_subtipo('CVEMP')

    def set_subtipo(self, subtipo):
        """La banda válida es del músculo, así que cambia con el subtipo."""
        self.subtipo = subtipo if subtipo in EMG_BANDA else 'CVEMP'
        lo, hi = EMG_BANDA[self.subtipo]
        self._lo.setPos(lo)
        self._hi.setPos(hi)
        self.plot.setYRange(0, hi * 1.35, padding=0)
        self._refresh_label()

    def push(self, nivel):
        """Un tramo nuevo de EMG. `nivel` es el tónico en µV RMS; el trazo
        le agrega la variabilidad del músculo, que nunca contrae parejo."""
        self.nivel = float(nivel)
        jitter = np.random.normal(0, max(self.nivel * 0.12, 0.5))
        muestra = max(self.nivel + jitter, 0.0)
        self.trace = np.roll(self.trace, -1)
        self.trace[-1] = muestra
        self.curve.setData(self.trace)
        self._refresh_label()

    def clear_trace(self):
        self.nivel = 0.0
        self.trace = np.zeros(N_MUESTRAS)
        self.curve.setData(self.trace)
        self.lbl.setText('EMG --')
        self.lbl.setStyleSheet('')

    def _refresh_label(self):
        lo, hi = EMG_BANDA[self.subtipo]
        if self.nivel <= 0:
            self.lbl.setText('EMG --')
            self.lbl.setStyleSheet('')
            return
        ok = emg_en_banda(self.subtipo, self.nivel)
        estado = 'en rango' if ok else ('insuficiente' if self.nivel < lo else 'excesivo')
        self.lbl.setText(f'EMG {self.nivel:.0f} µV ({estado}, rango {lo:.0f}-{hi:.0f})')
        self.lbl.setStyleSheet('' if ok else 'color: #b00; font-weight: bold;')
