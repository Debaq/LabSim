"""FSP y ruido residual contra promediaciones acumuladas.

Antes eran dos viewboxes linkeados con ejes y titulo, sin una sola curva:
el generador calculaba el FSP en cada tick y no llegaba a ninguna parte.
Despues sí dibujaba, pero como dos trazos pelados sin ejes rotulados, sin
valores en el eje x y sin decir en ningun momento si el equipo ya declaro
la respuesta: el alumno veia dos lineas y ninguna lectura.

Lo que se ve aca es el criterio de detencion objetivo del equipo:
- Curva de FSP (eje izquierdo, rellena) subiendo con los barridos.
- La banda verde por encima del criterio elegido en Parametros Avanzados
  (fsp_criterion): mientras la curva no entra ahi, no hay respuesta.
- La marca de en cuantos barridos se cruza -- ese es el momento en que el
  equipo declara "respuesta presente", y queda escrito en el rotulo de
  estado arriba a la derecha.
- Ruido residual en nV (eje derecho), que es la otra mitad de la historia:
  el FSP sube porque el ruido baja como 1/sqrt(N), y con los electrodos
  malos no baja y el FSP se queda abajo por mas que se promedie. La escala
  del ruido se ajusta al registro (un piso de 20 nV contra un techo fijo de
  200 dejaba la curva pegada al eje, sin mostrar la caida).
"""
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Piso del eje de ruido (nV RMS). El eje crece con el registro, pero nunca
# baja de esto: si no, un registro limpio infla el ruido a pantalla completa
# y parece un desastre.
NOISE_MIN_NV = 60.0
# Colores: el verde es el FSP (y su eje), el gris el ruido (y el suyo), el
# rojo el criterio del equipo.
C_FSP = (0, 130, 60)
C_FSP_FILL = (0, 130, 60, 45)
C_NOISE = (120, 120, 120)
C_CRIT = (200, 30, 30)
C_OK = (0, 130, 60)
C_AXIS = (60, 60, 60)


def _font(size, bold=False):
    f = QFont()
    f.setPointSize(size)
    f.setBold(bold)
    return f


class FSP(pg.GraphicsLayoutWidget):
    def __init__(self, mean=1000):
        super().__init__()
        self.mean = mean
        self.criterion = None
        self.color_pen = pg.mkColor(*C_AXIS)
        self.setBackground('w')  # Fondo blanco
        self.setAntialiasing(True)
        self.pw1 = self.addPlot(row=0, col=0)
        self.pw1.setContentsMargins(2, 2, 2, 2)

        # Segundo eje y (ViewBox)
        self.pw2 = pg.ViewBox()
        self.pw1.showAxis('right')
        self.pw1.scene().addItem(self.pw2)
        self.pw1.getAxis('right').linkToView(self.pw2)
        self.pw2.setXLink(self.pw1)

        # Actualizar el ViewBox cuando cambie el tamaño
        self.pw1.getViewBox().sigResized.connect(self.update_views)

        # Configuraciones de grilla y rango
        self.pw1.showGrid(x=True, y=True, alpha=0.15)
        self.y_max = 6.0
        self.noise_max = NOISE_MIN_NV
        self.pw1.setYRange(0, self.y_max)
        self.pw1.setXRange(0, self.mean)
        self.pw2.setYRange(0, self.noise_max)

        # Deshabilitar auto rango y habilitar menú contextual
        self.pw1.setMouseEnabled(x=False, y=False)
        self.pw1.setMenuEnabled(False)
        self.pw2.setMenuEnabled(False)
        self.pw1.hideButtons()

        self.pw1.disableAutoRange()
        self.pw2.disableAutoRange()

        # Ejes rotulados y con valores: sin el eje x el grafico no decia
        # contra que crece la curva, que es justo lo que se enseña aca.
        ax = self.pw1.getAxis('bottom')
        ay = self.pw1.getAxis('left')
        aright = self.pw1.getAxis('right')
        etiqueta = {'font-size': '8pt'}
        ax.setLabel('barridos promediados', **etiqueta)
        ay.setLabel('FSP', color=pg.mkColor(*C_FSP).name(), **etiqueta)
        aright.setLabel('ruido nV', color=pg.mkColor(*C_NOISE).name(), **etiqueta)
        for eje, color in ((ax, C_AXIS), (ay, C_FSP), (aright, C_NOISE)):
            eje.setPen(pg.mkColor(*color))
            eje.setTextPen(pg.mkColor(*color))
            eje.setStyle(tickFont=_font(7), tickTextOffset=3)
        ay.setWidth(28)
        aright.setWidth(30)
        ax.setHeight(28)

        # Banda de deteccion: por encima del criterio el equipo declara
        # respuesta presente. Es la lectura de un vistazo -- la curva entro
        # o no entro en el verde.
        self.band_ok = pg.LinearRegionItem(
            values=(0, 0), orientation='horizontal', movable=False,
            brush=pg.mkBrush(0, 130, 60, 18))
        for linea in self.band_ok.lines:
            linea.setPen(pg.mkPen(None))
        self.band_ok.setZValue(-10)
        self.band_ok.setVisible(False)
        self.pw1.addItem(self.band_ok)

        # Curvas: FSP en el eje izquierdo (rellena hasta 0, que es lo que
        # da la sensacion de "cuanto falta"), ruido residual en el derecho.
        self.curve_fsp = self.pw1.plot(
            [], [], pen=pg.mkPen(*C_FSP, width=2.5),
            fillLevel=0, brush=pg.mkBrush(*C_FSP_FILL))
        self.curve_noise = pg.PlotCurveItem(
            [], [], pen=pg.mkPen(*C_NOISE, width=1.6,
                                 style=Qt.PenStyle.DashLine))
        self.pw2.addItem(self.curve_noise)
        # Punta de la curva: el valor de FSP de ahora, que es el numero que
        # el alumno mira mientras promedia.
        self.head = pg.ScatterPlotItem(
            [], [], symbol='o', size=7, brush=pg.mkBrush(*C_FSP), pen=None)
        self.pw1.addItem(self.head)

        # Criterio de deteccion y marca del cruce.
        self.line_criterion = pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen(*C_CRIT, width=1.5,
                                         style=Qt.PenStyle.DashLine))
        self.line_criterion.setVisible(False)
        self.pw1.addItem(self.line_criterion)
        # Debajo de la linea del criterio: arriba chocaba con la lectura.
        self.lbl_criterion = pg.TextItem(text='', color=C_CRIT, anchor=(0, 0))
        self.lbl_criterion.setFont(_font(7))
        self.lbl_criterion.setVisible(False)
        self.pw1.addItem(self.lbl_criterion)
        # Vertical del cruce: deja ver en el eje x en cuantos barridos fue.
        self.line_cross = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen(*C_CRIT, width=1,
                                          style=Qt.PenStyle.DotLine))
        self.line_cross.setVisible(False)
        self.pw1.addItem(self.line_cross)
        self.mark_cross = pg.ScatterPlotItem(
            [], [], symbol='o', size=10, brush=pg.mkBrush(*C_CRIT), pen=None)
        self.pw1.addItem(self.mark_cross)
        # A la izquierda del punto de cruce: pegado al borde derecho el
        # rotulo se salia del area de dibujo (el cruce suele caer tarde).
        self.lbl_cross = pg.TextItem(text='', color=C_CRIT, anchor=(1, 1),
                                     fill=pg.mkBrush(255, 255, 255, 210))
        self.lbl_cross.setFont(_font(7, bold=True))
        self.pw1.addItem(self.lbl_cross)

        # Lecturas: titulo con los valores de ahora y estado de deteccion.
        self.lbl_read = pg.TextItem(text='', anchor=(0, 0),
                                    fill=pg.mkBrush(255, 255, 255, 210))
        self.lbl_read.setFont(_font(8, bold=True))
        self.pw1.addItem(self.lbl_read)
        # Abajo a la derecha, no arriba: en el ancho real del dock los dos
        # rotulos de arriba se pisaban.
        self.lbl_state = pg.TextItem(text='', anchor=(1, 1),
                                     fill=pg.mkBrush(255, 255, 255, 210))
        self.lbl_state.setFont(_font(8, bold=True))
        self.pw1.addItem(self.lbl_state)

        self.sweeps = []
        self.values = []
        self.noise = []
        self.crossed_at = None

        self.title()

    # ------------------------------------------------------------ layout
    def update_views(self):
        self.pw2.setGeometry(self.pw1.getViewBox().sceneBoundingRect())
        self.pw2.disableAutoRange()
        self.pw1.disableAutoRange()

    def title(self):
        """Rotulos flotantes de las esquinas, en coordenadas de datos."""
        self._refresh_read()

    def _place_labels(self):
        """Reubica los rotulos: viven en datos, y los rangos cambian."""
        x0, x1 = 0.0, float(self.mean)
        ancho = x1 - x0
        self.lbl_read.setPos(x0 + ancho * 0.01, self.y_max * 0.99)
        self.lbl_state.setPos(x1 - ancho * 0.01, self.y_max * 0.02)
        if self.criterion:
            self.lbl_criterion.setPos(x0 + ancho * 0.01, self.criterion)

    def _refresh_read(self):
        """Texto de las esquinas segun el ultimo punto empujado."""
        if not self.values:
            self.lbl_read.setText('FSP —', color=C_AXIS)
        else:
            self.lbl_read.setText(
                f'FSP {self.values[-1]:.1f}   ruido {self.noise[-1]:.0f} nV',
                color=C_AXIS)
        if not self.criterion:
            self.lbl_state.setText('sin criterio', color=C_NOISE)
        elif self.crossed_at is not None:
            self.lbl_state.setText(
                f'respuesta presente · {int(self.crossed_at)} barridos',
                color=C_OK)
        else:
            self.lbl_state.setText(
                f'sin respuesta (criterio {self.criterion:.1f})', color=C_CRIT)
        self._place_labels()

    # ------------------------------------------------------------- datos
    def set_mean(self, value):
        self.mean = max(int(value or 0), 1)
        self.pw1.setXRange(0, self.mean)
        self._place_labels()

    def set_criterion(self, value):
        """Criterio de deteccion del equipo (None = deshabilitado)."""
        self.criterion = float(value) if value else None
        if self.criterion:
            self.line_criterion.setPos(self.criterion)
            self.y_max = max(6.0, self.criterion * 1.6)
            self.pw1.setYRange(0, self.y_max)
            self.band_ok.setRegion((self.criterion, self.y_max))
            self.lbl_criterion.setText(f'detección FSP {self.criterion:.1f}')
        self.line_criterion.setVisible(bool(self.criterion))
        self.lbl_criterion.setVisible(bool(self.criterion))
        self.band_ok.setVisible(bool(self.criterion))
        self._refresh_read()

    def push(self, sweeps, fsp, noise_nv=None):
        """Un punto por tick de promediacion."""
        self.sweeps.append(float(sweeps))
        self.values.append(float(fsp))
        self.noise.append(float(noise_nv or 0.0))
        if (self.criterion and self.crossed_at is None
                and self.values[-1] >= self.criterion):
            self.crossed_at = self.sweeps[-1]
        self._redraw()

    # --------------------------------------------------- dibujo / memoria
    def _redraw(self):
        """Vuelve a dibujar todo con lo que hay en sweeps/values/noise."""
        self.curve_fsp.setData(self.sweeps, self.values)
        self.curve_noise.setData(self.sweeps, self.noise)
        if self.sweeps:
            self.head.setData([self.sweeps[-1]], [self.values[-1]])
        else:
            self.head.setData([], [])
        # El eje del ruido sigue al registro: el arranque marca el techo.
        techo = max(NOISE_MIN_NV, max(self.noise) * 1.15) if self.noise else NOISE_MIN_NV
        if abs(techo - self.noise_max) > 1e-6:
            self.noise_max = techo
            self.pw2.setYRange(0, self.noise_max)
        if self.crossed_at is not None:
            y = self.criterion or 0.0
            for x, v in zip(self.sweeps, self.values):
                if x == self.crossed_at:
                    y = v
                    break
            self.mark_cross.setData([self.crossed_at], [y])
            self.line_cross.setPos(self.crossed_at)
            self.line_cross.setVisible(True)
            self.lbl_cross.setText(f'{int(self.crossed_at)} barridos')
            self.lbl_cross.setPos(self.crossed_at - self.mean * 0.01, y)
        else:
            self.mark_cross.setData([], [])
            self.line_cross.setVisible(False)
            self.lbl_cross.setText('')
        self._refresh_read()

    def get_track(self):
        """Lo dibujado ahora, para guardarlo junto a la curva registrada.

        El FSP es de la curva, no del equipo: al volver a seleccionar una
        curva ya tomada hay que poder ver con cuantos barridos cruzo el
        criterio esa curva, no la ultima que se promedio."""
        return {'sweeps': list(self.sweeps), 'fsp': list(self.values),
                'noise': list(self.noise), 'mean': self.mean,
                'criterion': self.criterion, 'crossed_at': self.crossed_at}

    def set_track(self, track):
        """Redibuja un FSP guardado (o deja el grafico vacio si no hay)."""
        self.clear_curve()
        if not track:
            self.set_criterion(None)
            return
        self.set_mean(track.get('mean') or self.mean)
        self.set_criterion(track.get('criterion'))
        self.sweeps = [float(v) for v in (track.get('sweeps') or [])]
        self.values = [float(v) for v in (track.get('fsp') or [])]
        ruido = [float(v) for v in (track.get('noise') or [])]
        # Registros viejos podian venir sin ruido: se completa con ceros
        # para que las tres series tengan el mismo largo.
        self.noise = ruido + [0.0] * (len(self.sweeps) - len(ruido))
        cruce = track.get('crossed_at')
        self.crossed_at = float(cruce) if cruce is not None else None
        self._redraw()

    def clear_curve(self):
        self.sweeps, self.values, self.noise = [], [], []
        self.crossed_at = None
        self.noise_max = NOISE_MIN_NV
        self.pw2.setYRange(0, self.noise_max)
        self.curve_fsp.setData([], [])
        self.curve_noise.setData([], [])
        self.head.setData([], [])
        self.mark_cross.setData([], [])
        self.line_cross.setVisible(False)
        self.lbl_cross.setText('')
        self._refresh_read()
