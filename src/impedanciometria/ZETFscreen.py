"""Pantalla "ETF": función tubaria, con dos pruebas según la membrana.

- Membrana perforada (o con tubo): se presuriza el conducto con el dial y
  se le pide al paciente que trague tres veces durante 10 s. Si la trompa
  abre, la presión se va a 0 con cada deglución.
- Membrana íntegra (presión-deglución de Williams): timpanograma en reposo,
  después de presurizar el conducto a +400 daPa y tragar, y después de
  -400 daPa y tragar. Si la trompa funciona, el pico se corre unos daPa.

La tecla 1 elige la prueba. Las teclas bajo la pantalla (ver la fila de
rótulos de abajo):
- perforada: 1 prueba · 2 Inicio · 6 presión (con el dial);
- íntegra:   1 prueba · 2 Reposo · 3 +400 y tragar · 4 -400 y tragar.
"""
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from impedanciometria.z_generator import ETF_DEGLUCIONES_S, ETF_DURACION_S

PRUEBA_PERFORADA = 'perforada'
PRUEBA_INTEGRA = 'integra'
NOMBRE_PRUEBA = {PRUEBA_PERFORADA: "Membrana perforada", PRUEBA_INTEGRA: "Membrana íntegra"}
MANIOBRAS = ('reposo', 'positiva', 'negativa')
NOMBRE_MANIOBRA = {'reposo': "Reposo", 'positiva': "+400 trag", 'negativa': "-400 trag"}
COLOR_MANIOBRA = {'reposo': 'w', 'positiva': 'y', 'negativa': (120, 255, 120)}


def _rotulo(texto="", alinear=Qt.AlignCenter):
    lbl = QLabel(texto)
    lbl.setAlignment(alinear)
    return lbl


class ZETFscreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(580, 280)
        self.setMaximumSize(580, 280)
        self.setStyleSheet("font: 10pt \"Monospace\";\ncolor: rgb(255, 255, 255);")
        self.prueba = PRUEBA_PERFORADA

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        cabecera = QHBoxLayout()
        cabecera.setSpacing(12)
        cabecera.addWidget(_rotulo("ETF"))
        self.lbl_side = _rotulo("OD")
        self.lbl_prueba = _rotulo(NOMBRE_PRUEBA[self.prueba])
        cabecera.addWidget(self.lbl_side)
        cabecera.addWidget(self.lbl_prueba, 2)
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
        self.pw.showGrid(x=True, y=True)
        self.pw.setMouseEnabled(x=False, y=False)
        self.pw.setMenuEnabled(False)
        marco_layout.addWidget(self.pw)
        centro.addWidget(marco, 1)

        lateral = QVBoxLayout()
        self.lbl_info = [_rotulo("", Qt.AlignLeft) for _ in range(3)]
        for lbl in self.lbl_info:
            lateral.addWidget(lbl)
        lateral.addStretch(1)
        centro.addLayout(lateral)
        raiz.addLayout(centro, 1)

        teclas = QHBoxLayout()
        self.lbl_teclas = [_rotulo() for _ in range(6)]
        for lbl in self.lbl_teclas:
            teclas.addWidget(lbl)
        raiz.addLayout(teclas)

        self.curvas = {}
        self.presion = 0
        self.set_prueba(self.prueba)

    # ------------------------------------------------------------------

    def set_side(self, side):
        self.lbl_side.setText(side)

    def set_pressure(self, pressure):
        self.presion = pressure
        if self.prueba == PRUEBA_PERFORADA:
            self.lbl_teclas[5].setText(f"{pressure} daPa")

    def set_prueba(self, prueba):
        """Cambia de prueba: otros ejes, otras teclas y la pantalla limpia."""
        self.prueba = prueba
        self.lbl_prueba.setText(NOMBRE_PRUEBA[prueba])
        self.pw.clear()
        self.curvas = {}
        textos = ["Prueba", "", "", "", "", ""]
        if prueba == PRUEBA_PERFORADA:
            self.pw.setRange(yRange=(-400, 200), xRange=(0, ETF_DURACION_S), disableAutoRange=True)
            self.pw.setLabel(axis='bottom', text='S')
            self.pw.setLabel(axis='left', text='daPa')
            self.pw.getAxis('bottom').setTicks(None)
            self.pw.getAxis('left').setTicks(None)
            # Un solo anchor: pyqtgraph elige uno u otro según el lado del
            # centro del gráfico y los rótulos de 2.5 y 5 s se juntaban.
            for s in ETF_DEGLUCIONES_S:
                self.pw.addItem(pg.InfiniteLine(pos=s, angle=90, pen=pg.mkPen('w', style=Qt.DashLine),
                                                label="trague", labelOpts={'position': 0.95, 'color': 'w',
                                                                           'anchors': [(0, 0.5), (0, 0.5)]}))
            self.curvas['presion'] = self.pw.plot([], [], pen=pg.mkPen('y', width=2))
            textos[1] = "Inicio"
            textos[5] = f"{self.presion} daPa"
        else:
            self.pw.setRange(yRange=(0, 2), xRange=(-400, 200), disableAutoRange=True)
            self.pw.setLabel(axis='bottom', text='daPa')
            self.pw.setLabel(axis='left', text='ml')
            textos[1:4] = [NOMBRE_MANIOBRA[m] for m in MANIOBRAS]
        for lbl, texto in zip(self.lbl_teclas, textos):
            lbl.setText(texto)
        self.limpiar_info()

    def limpiar_info(self):
        if self.prueba == PRUEBA_PERFORADA:
            textos = ["Inicial: ---- daPa", "Final:   ---- daPa", ""]
        else:
            textos = [f"{NOMBRE_MANIOBRA[m]:<10}---- daPa" for m in MANIOBRAS]
        for lbl, texto in zip(self.lbl_info, textos):
            lbl.setText(texto)

    def plot_presion(self, x, y):
        self.curvas['presion'].setData(x, y)

    def set_resultado_perforada(self, inicial, final):
        self.lbl_info[0].setText(f"Inicial: {inicial:>4} daPa")
        self.lbl_info[1].setText(f"Final:   {final:>4} daPa" if final is not None else "Final:   ---- daPa")

    def plot_timpanograma(self, maniobra, x, y, pico):
        """Agrega (o reemplaza) el timpanograma de una maniobra, con su pico."""
        if maniobra in self.curvas:
            self.pw.removeItem(self.curvas[maniobra])
        self.curvas[maniobra] = self.pw.plot(x, y, pen=pg.mkPen(COLOR_MANIOBRA[maniobra], width=2))
        i = MANIOBRAS.index(maniobra)
        texto = f"{pico:>4} daPa" if pico is not None else "sin pico"
        self.lbl_info[i].setText(f"{NOMBRE_MANIOBRA[maniobra]:<10}{texto}")


if __name__ == "__main__":
    pass
