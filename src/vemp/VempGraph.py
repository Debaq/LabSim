"""
Gráfico VEMP (por oído).

Mismo comportamiento que AbrGraph, con lo que el VEMP necesita distinto:

- ESCALA POR SUBTIPO. El cVEMP ronda los 150 µV y el oVEMP los 10: con un
  rango fijo (el módulo tenía -100/250 µV clavado) el ocular quedaba en una
  raya plana. Cada subtipo arranca en su escala y se abre/cierra con el
  menú del gráfico.
- CURVAS FILTRADAS POR SUBTIPO. Un cVEMP y un oVEMP del mismo oído no se
  dibujan juntos: no comparten ni picos ni escala. Cada curva recuerda con
  qué VEMP se registró y el gráfico muestra solo las del subtipo activo.
- MARCAS BIFÁSICAS. La marca guarda la amplitud CON SIGNO (P13 arriba, N23
  abajo) porque la amplitud que se informa es la pico-pico entre las dos, y
  eso solo sale bien si los signos son los de verdad.

El alumno mide con los cursores A/A' (igual que en el ABR): pone A en el
pico, hace clic en la celda de la tabla y la marca se dibuja ahí.
"""

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters  # noqa: F401  (registra ImageExporter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMenu

from abr.WidgetsMods import InfiniteLineMod, TextItemMod
from vemp.VEMP_generator_v1 import SUBTIPO_PEAKS, VENTANA_MS

# Escala vertical inicial (µV de alto de ventana) de cada subtipo. Sale de
# la amplitud normativa: el trazo tiene que entrar sin tocar el techo y sin
# quedar aplastado contra la línea de base.
ESCALA_INICIAL = {'CVEMP': 500.0, 'OVEMP': 40.0, 'MVEMP': 200.0}


class VempGraph(pg.GraphicsLayoutWidget):
    sig_data_info = Signal(dict)          # cursores A/A' movidos
    sig_change_value_mark = Signal(dict)  # {curva: {pico: [lat, amp] | None}}
    sig_del_curve = Signal(str)
    sig_curve_selected = Signal(str)

    def __init__(self, side, subtipo='CVEMP'):
        super().__init__()
        self.side = side
        self.subtipo = subtipo
        self.peak_labels = list(SUBTIPO_PEAKS.get(subtipo, ['p13', 'n23']))
        # Una escala por subtipo: el alumno amplía el oVEMP sin descuadrar
        # el cVEMP que ya tomó (los dos siguen ahí, ocultos).
        self.escalas = dict(ESCALA_INICIAL)
        self.scale_uv = self.escalas.get(subtipo, 500.0)
        # Separación entre curvas como fracción de la escala.
        self.gap_ratio = 0.30

        self.data = {}        # curva -> {'x','y','y_raw','gap','int','subtipo','done'}
        self.marks = {}       # curva -> {pico: [lat, amp]}
        self.curve_int = {}   # curva -> intensidad (dB SPL)
        self.traces = {}      # curva -> PlotDataItem
        self.act_curve = None
        self.current_lat = 0.0

        self.setBackground('w')
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        self._setup_plot()
        self._colors_side()
        self._cursors()

    # =====================================================================
    # Construcción
    # =====================================================================

    def _setup_plot(self):
        self.pw = self.addPlot(row=0, col=1)
        self.pw.setRange(xRange=(0, VENTANA_MS + 2), disableAutoRange=True)
        self.grid = pg.GridItem(pen=self.color_pen, textPen=self.color_pen)
        self.pw.addItem(self.grid)
        self.grid.setTickSpacing(x=[5.0])
        self.pw.setMouseEnabled(x=False, y=True)
        self.pw.setMenuEnabled(False)
        self.pw.hideButtons()
        self.pw.setLabel('bottom', 'ms')
        self.pw.getAxis('left').setStyle(showValues=False)
        self.pw.getViewBox().setMouseMode(pg.ViewBox.PanMode)
        # Sin auto-range: el eje del examen no se reacomoda solo cada vez
        # que entra una curva (se ve como si el gráfico creciera con una
        # animación). La escala la manejan apply_view() y scale().
        self.pw.enableAutoRange(x=False, y=False)
        self.pw.setAutoVisible(x=False, y=False)
        self.apply_view()

    def _colors_side(self):
        if self.side == 0:
            self.active_color = pg.mkColor(255, 0, 0, 255)
            self.inactive_color = pg.mkColor(180, 0, 0, 255)
            self.active_fill_color = '#0EFA00'
            self.inactive_fill_color = '#B40000'
        else:
            self.active_color = pg.mkColor(106, 154, 242, 255)
            self.inactive_color = pg.mkColor(112, 142, 199, 255)
            self.active_fill_color = '#0EFA00'
            self.inactive_fill_color = '#708EC7'

    def _cursors(self):
        pen = pg.mkPen('b', width=1, style=Qt.PenStyle.DashLine)
        opts = {'position': 0.9, 'color': (255, 255, 255),
                'fill': (0, 0, 0, 255), 'movable': True}
        self.inf_a = InfiniteLineMod(lbl='A', pos=10, movable=True, angle=90,
                                     pen=pen, labelOpts=opts, name=f'A{self.side}')
        self.inf_b = InfiniteLineMod(lbl="A'", pos=20, movable=True, angle=90,
                                     pen=pen, labelOpts=opts, name=f'B{self.side}')
        self.inf_a.sigPositionChanged.connect(self.get_amplitude)
        self.inf_b.sigPositionChanged.connect(self.get_amplitude)
        self.pw.addItem(self.inf_a)
        self.pw.addItem(self.inf_b)

    # =====================================================================
    # Subtipo / escala / vista
    # =====================================================================

    def set_subtipo(self, subtipo):
        """Cambia el VEMP activo: otros picos, otra escala, otras curvas.

        Las curvas del subtipo anterior no se borran (el alumno vuelve a
        ellas cambiando el combo), se ocultan.
        """
        self.subtipo = subtipo
        self.peak_labels = list(SUBTIPO_PEAKS.get(subtipo, ['p13', 'n23']))
        self.scale_uv = self.escalas.get(subtipo, 500.0)
        self._apply_visibility()
        if self.act_curve and self.data.get(self.act_curve, {}).get('subtipo') != subtipo:
            self.act_curve = next((c for c, d in self.data.items()
                                   if d['subtipo'] == subtipo), None)
        self.apply_view()

    def _apply_visibility(self):
        for curva, item in self.traces.items():
            visible = self.data[curva]['subtipo'] == self.subtipo
            item.setVisible(visible)
        for item in self.pw.items:
            if isinstance(item, TextItemMod):
                padre = item.curve_parent
                if padre in self.data:
                    item.setVisible(self.data[padre]['subtipo'] == self.subtipo)

    def _curvas_visibles(self):
        return {c: d for c, d in self.data.items() if d['subtipo'] == self.subtipo}

    def next_gap(self):
        """Altura de la próxima curva: una ranura por DEBAJO de la última.

        Hacia abajo porque así se lee la serie: la intensidad más alta
        arriba y las siguientes descendiendo hacia el umbral.
        """
        visibles = self._curvas_visibles()
        if not visibles:
            return 0.0
        paso = self.scale_uv * self.gap_ratio
        return min(v.get('gap', 0.0) for v in visibles.values()) - paso

    def apply_view(self):
        piso = min((v.get('gap', 0.0) for v in self._curvas_visibles().values()),
                   default=0.0)
        self.pw.setYRange(piso - self.scale_uv / 2, self.scale_uv / 2, padding=0)
        self.grid.setTickSpacing(x=[5.0], y=[self._tick_y()])

    def _tick_y(self):
        """Un paso de grilla legible para la escala actual (10 divisiones)."""
        crudo = self.scale_uv / 10.0
        for paso in (1, 2, 5, 10, 20, 50, 100, 200, 500):
            if crudo <= paso:
                return float(paso)
        return crudo

    def scale(self, direction):
        actual = self.scale_uv
        if direction == 'plus':
            nueva = min(actual * 2, 4000)
        elif direction == 'minus':
            nueva = max(actual / 2, 5)
        else:
            nueva = actual
        if nueva != actual:
            factor = nueva / actual
            self.scale_uv = nueva
            self.escalas[self.subtipo] = nueva
            # Solo las curvas del subtipo activo: el apilado de los otros
            # está en la escala de ellos.
            for curva, valores in self._curvas_visibles().items():
                valores['gap'] = valores.get('gap', 0.0) * factor
                self.redraw(curva)
                self.move_label(curva)
                self.move_marks(curva)
            self.apply_view()
        return self.scale_uv

    def get_scale(self):
        return self.scale_uv

    # =====================================================================
    # Curvas
    # =====================================================================

    def create_line(self, name, x, y, intencity, subtipo=None, done=False):
        """Agrega o actualiza una curva. Durante la promediación se llama en
        cada tick con la curva un poco más limpia."""
        subtipo = subtipo or self.subtipo
        if name in self.data:
            self.data[name]['x'] = x
            self.data[name]['y'] = y
            self.data[name]['y_raw'] = y
            self.data[name]['done'] = done
            self.redraw(name)
            self.move_marks(name)
            self.get_amplitude()
            return

        gap = self.next_gap()
        self.data[name] = {'x': x, 'y': y, 'y_raw': y, 'gap': gap,
                           'int': intencity, 'subtipo': subtipo, 'done': done}
        self.marks[name] = {}
        self.curve_int[name] = intencity
        color = self.active_color
        self.traces[name] = self.pw.plot(x=x, y=np.asarray(y) + gap,
                                         pen=pg.mkPen(color, width=2), name=name)
        label = self._create_label(name, intencity, gap)
        self.pw.addItem(label)
        self.active_curve(name)
        self.apply_view()

    def _label_html(self, text, fill):
        return (f"<div style='text-align:center; background-color:{fill};'>"
                f"<span style='color:#000; font-size:7pt;'>{text} dB</span></div>")

    def _create_label(self, name, intencity, gap):
        lbl = TextItemMod(name=name, tipo='label', curve_parent=name,
                          html=self._label_html(intencity, self.active_fill_color),
                          border='w')
        lbl.sigDragged.connect(self.drag_curve)
        lbl.sigPositionChangeStarted.connect(self.active_curve)
        lbl.setPos(VENTANA_MS, gap)
        return lbl

    def redraw(self, name):
        item = self.traces.get(name)
        if item is None:
            return
        d = self.data[name]
        item.setData(x=d['x'], y=np.asarray(d['y']) + d['gap'])

    def drag_curve(self, value):
        curve = value['name']
        if curve not in self.data:
            return
        self.data[curve]['gap'] = value['pos'][1]
        self.redraw(curve)
        self.move_marks(curve)

    def move_label(self, curve):
        for item in self.pw.items:
            if (isinstance(item, TextItemMod) and item.tipo == 'label'
                    and item.curve_parent == curve):
                item.setPos(VENTANA_MS, self.data[curve]['gap'])

    def active_curve(self, name):
        if name not in self.data:
            return
        self.act_curve = name
        for curva, item in self.traces.items():
            activa = curva == name
            item.setPen(pg.mkPen(self.active_color if activa else self.inactive_color,
                                 width=2 if activa else 1))
        for item in self.pw.items:
            if isinstance(item, TextItemMod) and item.tipo == 'label':
                fill = (self.active_fill_color if item.curve_parent == name
                        else self.inactive_fill_color)
                item.setHtml(self._label_html(self.curve_int.get(item.curve_parent, ''), fill))
        self.sig_curve_selected.emit(name)
        self.get_amplitude()

    def get_active(self):
        return self.act_curve

    def delete_curve(self, name=None):
        name = name or self.act_curve
        if name not in self.data:
            return
        item = self.traces.pop(name, None)
        if item is not None:
            self.pw.removeItem(item)
        for item in self.pw.items[:]:
            if isinstance(item, TextItemMod) and item.curve_parent == name:
                self.pw.removeItem(item)
        self.data.pop(name, None)
        self.marks.pop(name, None)
        self.curve_int.pop(name, None)
        self.sig_del_curve.emit(name)
        if self.act_curve == name:
            self.act_curve = next(iter(self._curvas_visibles()), None)
        self.apply_view()

    def smooth(self, sigma):
        """Suaviza lo que se ve, sin tocar el registro original.

        y_raw es la curva como salió del equipo: suavizar dos veces suaviza
        el original, no el acumulado, y el alumno puede volver atrás.
        """
        from abr.smooth import smooth_curve_gaussian
        curve = self.act_curve
        if curve not in self.data:
            return
        d = self.data[curve]
        d['y'] = smooth_curve_gaussian(d['y_raw'], sigma=float(sigma))
        self.redraw(curve)
        self.move_marks(curve)

    # =====================================================================
    # Cursores y marcas
    # =====================================================================

    def get_amplitude(self):
        lat_a = max(0.0, min(VENTANA_MS, self.inf_a.getXPos()))
        lat_b = max(0.0, min(VENTANA_MS, self.inf_b.getXPos()))
        self.inf_a.setPos((lat_a, 0))
        self.inf_b.setPos((lat_b, 0))
        self.current_lat = lat_a
        if self.act_curve not in self.data:
            return
        d = self.data[self.act_curve]
        amp_a = self.find_nearest(d['x'], lat_a, d['y'])
        amp_b = self.find_nearest(d['x'], lat_b, d['y'])
        self.sig_data_info.emit({
            'curve': self.act_curve,
            'data': {
                'side': self.side,
                'lat_A': float(lat_a),
                'lat_B': float(lat_b),
                'amp_A': float(amp_a),
                'amp_B': float(amp_b),
                # Amplitud pico-pico entre los dos cursores: es LA amplitud
                # que se informa en un VEMP (P13-N23 / N10-P16).
                'amp_AB': float(abs(amp_a - amp_b)),
                'lat_AB': float(abs(lat_a - lat_b)),
            },
        })

    def create_marks(self, pico):
        """Marca el pico en la posición del cursor A de la curva activa."""
        curve = self.act_curve
        if curve not in self.data or pico not in self.peak_labels:
            return
        d = self.data[curve]
        idx = self.find_idx(d['x'], self.current_lat)
        x = float(d['x'][idx])
        y = float(d['y'][idx])
        self.marks[curve][pico] = [x, y]
        self._draw_mark(curve, pico, x, y)
        self.sig_change_value_mark.emit({curve: {pico: [x, y]}})

    def _draw_mark(self, curve, pico, x, y):
        name = f'{curve}_{pico}'
        for item in self.pw.items[:]:
            if isinstance(item, TextItemMod) and item.tipo == 'mark' and item.name == name:
                self.pw.removeItem(item)
        # La flecha apunta al pico desde el lado por el que ese pico sale:
        # abajo para los positivos, arriba para los negativos.
        arriba = not str(pico).lower().startswith('n')
        flecha = '&darr;' if arriba else '&uarr;'
        html = (f"<span style='color:#000; font-size:7pt;'>"
                f"<h3>{flecha}<sup>{pico.upper()}</sup></h3></span>")
        item = TextItemMod(name=name, tipo='mark', curve_parent=curve, html=html,
                           anchor=(0.34, 0.6 if arriba else 0.4), color=(0, 0, 0, 255))
        font = QFont()
        font.setPixelSize(13)
        item.setFont(font)
        item.setPos(x, y + self.data[curve]['gap'])
        item.setVisible(self.data[curve]['subtipo'] == self.subtipo)
        self.pw.addItem(item)

    def move_marks(self, curve):
        for pico, (x, y) in self.marks.get(curve, {}).items():
            self._draw_mark(curve, pico, x, y)

    def delete_mark(self, pico, curve=None):
        curve = curve or self.act_curve
        if curve not in self.marks:
            return
        self.marks[curve].pop(pico, None)
        for item in self.pw.items[:]:
            if (isinstance(item, TextItemMod) and item.tipo == 'mark'
                    and item.name == f'{curve}_{pico}'):
                self.pw.removeItem(item)
        self.sig_change_value_mark.emit({curve: {pico: None}})

    def delete_all_marks(self):
        curve = self.act_curve
        for pico in list(self.marks.get(curve, {})):
            self.delete_mark(pico, curve)

    def get_marks(self, curve):
        return dict(self.marks.get(curve, {}))

    # =====================================================================
    # Menú contextual
    # =====================================================================

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        borrar = menu.addAction('Eliminar curva')
        sub_marcas = menu.addMenu('Eliminar marcas')
        acciones_marca = {sub_marcas.addAction(p.upper()): p for p in self.peak_labels}
        todas = sub_marcas.addAction('Todas')
        sub_suave = menu.addMenu('Suavizar')
        acciones_suave = {sub_suave.addAction(f'x{i}'): s
                          for i, s in ((2, 0.5), (3, 1.0), (4, 2.0))}
        sub_escala = menu.addMenu('Escala')
        mas = sub_escala.addAction('Ampliar')
        menos = sub_escala.addAction('Reducir')

        accion = menu.exec_(event.globalPos())
        if accion is None:
            return
        if accion == borrar:
            self.delete_curve()
        elif accion in acciones_marca:
            self.delete_mark(acciones_marca[accion])
        elif accion == todas:
            self.delete_all_marks()
        elif accion in acciones_suave:
            self.smooth(acciones_suave[accion])
        elif accion == mas:
            self.scale('plus')
        elif accion == menos:
            self.scale('minus')

    def wheelEvent(self, ev, axis=None):
        # La rueda cambiaba el zoom y descuadraba la escala del examen.
        pass

    # =====================================================================
    # Helpers / limpieza / export
    # =====================================================================

    @staticmethod
    def find_nearest(array_in, value, array_out):
        idx = (np.abs(np.asarray(array_in) - value)).argmin()
        return array_out[idx]

    @staticmethod
    def find_idx(array_in, value):
        return int((np.abs(np.asarray(array_in) - value)).argmin())

    def limpiar_todo(self):
        for item in self.pw.listDataItems()[:]:
            self.pw.removeItem(item)
        for item in self.pw.items[:]:
            if isinstance(item, TextItemMod):
                self.pw.removeItem(item)
        self.data = {}
        self.marks = {}
        self.curve_int = {}
        self.traces = {}
        self.act_curve = None
        self.apply_view()

    def export_jpg(self, path):
        """Exporta el plot como JPEG (usado por submit_report)."""
        self.inf_a.hide()
        self.inf_b.hide()
        try:
            pg.exporters.ImageExporter(self.pw).export(path)
        finally:
            self.inf_a.show()
            self.inf_b.show()
