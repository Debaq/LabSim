"""FSP y ruido residual contra promediaciones acumuladas.

Antes eran dos viewboxes linkeados con ejes y titulo, sin una sola curva:
el generador calculaba el FSP en cada tick y no llegaba a ninguna parte.

Lo que se ve aca es el criterio de detencion objetivo del equipo:
- Curva de FSP (eje izquierdo) subiendo con los barridos.
- La linea del criterio elegido en Parametros Avanzados (fsp_criterion) y
  la marca de en cuantos barridos se cruza -- ese es el momento en que el
  equipo declara "respuesta presente".
- Ruido residual en nV (eje derecho), que es la otra mitad de la historia:
  el FSP sube porque el ruido baja como 1/sqrt(N), y con los electrodos
  malos no baja y el FSP se queda abajo por mas que se promedie.
"""
import pyqtgraph as pg
from PySide6.QtCore import Qt

# Techo del eje de ruido (nV RMS). Un registro que arranca esta arriba de
# 200 nV; el piso de un equipo bien puesto queda por debajo de 50.
NOISE_MAX_NV = 200.0


class FSP(pg.GraphicsLayoutWidget):
    def __init__(self, mean=1000):
        super().__init__()
        self.mean = mean
        self.criterion = None
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        self.setBackground('w')  # Fondo blanco
        self.pw1 = self.addPlot(row=0, col=0)

        # Segundo eje y (ViewBox)
        self.pw2 = pg.ViewBox()
        self.pw1.showAxis('right')
        self.pw1.scene().addItem(self.pw2)
        self.pw1.getAxis('right').linkToView(self.pw2)
        self.pw2.setXLink(self.pw1)

        # Actualizar el ViewBox cuando cambie el tamaño
        self.pw1.getViewBox().sigResized.connect(self.update_views)

        # Configuraciones de grilla y rango
        self.pw1.showGrid(x=False, y=True)
        self.pw1.setYRange(0, 6)
        self.pw1.setXRange(0, self.mean)
        self.pw2.setYRange(0, NOISE_MAX_NV)

        # Deshabilitar auto rango y habilitar menú contextual
        self.pw1.setMouseEnabled(x=False, y=False)
        self.pw1.setMenuEnabled(False)
        self.pw2.setMenuEnabled(False)

        self.pw1.disableAutoRange()
        self.pw2.disableAutoRange()

        # Estilo de ejes
        ax = self.pw1.getAxis('bottom')
        ay = self.pw1.getAxis('left')
        ax.setStyle(showValues=False)
        ax.setPen(self.color_pen)
        ay.setPen(self.color_pen)
        self.pw1.getAxis('right').setPen(pg.mkColor(120, 120, 120))

        # Curvas: FSP en el eje izquierdo, ruido residual en el derecho.
        self.curve_fsp = self.pw1.plot([], [], pen=pg.mkPen(0, 120, 0, width=2))
        self.curve_noise = pg.PlotCurveItem(
            [], [], pen=pg.mkPen(120, 120, 120, width=1, style=Qt.PenStyle.DashLine))
        self.pw2.addItem(self.curve_noise)

        # Criterio de deteccion y marca del cruce.
        self.line_criterion = pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen(200, 0, 0, width=1,
                                         style=Qt.PenStyle.DashLine))
        self.line_criterion.setVisible(False)
        self.pw1.addItem(self.line_criterion)
        self.mark_cross = pg.ScatterPlotItem(
            [], [], symbol='o', size=9, brush=pg.mkBrush(200, 0, 0), pen=None)
        self.pw1.addItem(self.mark_cross)
        self.lbl_cross = pg.TextItem(text='', color=(200, 0, 0), anchor=(0, 1))
        self.pw1.addItem(self.lbl_cross)

        self.sweeps = []
        self.values = []
        self.noise = []
        self.crossed_at = None

        # Agregar título
        self.title()

    def update_views(self):
        self.pw2.setGeometry(self.pw1.getViewBox().sceneBoundingRect())
        self.pw2.disableAutoRange()
        self.pw1.disableAutoRange()

    def title(self):
        text = pg.TextItem(text='FSP', color=(0, 0, 0))
        self.pw1.addItem(text)
        text.setPos(self.pw1.getViewBox().viewRange()[0][0],
                    self.pw1.getViewBox().viewRange()[1][1])

    def set_mean(self, value):
        self.mean = max(int(value or 0), 1)
        self.pw1.setXRange(0, self.mean)

    def set_criterion(self, value):
        """Criterio de deteccion del equipo (None = deshabilitado)."""
        self.criterion = float(value) if value else None
        if self.criterion:
            self.line_criterion.setPos(self.criterion)
            self.pw1.setYRange(0, max(6.0, self.criterion * 1.6))
        self.line_criterion.setVisible(bool(self.criterion))

    def push(self, sweeps, fsp, noise_nv=None):
        """Un punto por tick de promediacion."""
        self.sweeps.append(float(sweeps))
        self.values.append(float(fsp))
        self.noise.append(float(noise_nv or 0.0))
        self.curve_fsp.setData(self.sweeps, self.values)
        self.curve_noise.setData(self.sweeps, self.noise)
        if (self.criterion and self.crossed_at is None
                and self.values[-1] >= self.criterion):
            self.crossed_at = self.sweeps[-1]
            self.mark_cross.setData([self.crossed_at], [self.values[-1]])
            self.lbl_cross.setText(f'{int(self.crossed_at)} barridos')
            self.lbl_cross.setPos(self.crossed_at, self.values[-1])

    def clear_curve(self):
        self.sweeps, self.values, self.noise = [], [], []
        self.crossed_at = None
        self.curve_fsp.setData([], [])
        self.curve_noise.setData([], [])
        self.mark_cross.setData([], [])
        self.lbl_cross.setText('')
