"""
Gráfico VEMP (por oído).

Adaptación simplificada de AbrGraph: usa pyqtgraph nativo (no WidgetsMods
para evitar arrastrar custom widgets). El alumno selecciona curvas
capturadas, las mueve verticalmente (gap), marca los picos arrastrando
labels que se asocian a pico/subtipo activo.

peak_labels: lista dinámica (ej. ['p13','n23'] para CVEMP/MVEMP,
             ['n10','p16'] para OVEMP). Cambia con subtipo.
"""

import pyqtgraph as pg
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor


COLOR_OD_ACTIVE = QColor(255, 0, 0)
COLOR_OI_ACTIVE = QColor(106, 154, 242)
COLOR_LABEL_ACTIVE = QColor(14, 250, 0)


class VempGraph(pg.GraphicsLayoutWidget):
    sig_change_value_mark = Signal(dict)  # al crear/borrar marca de pico
    sig_del_curve = Signal(str)
    sig_curve_selected = Signal(str)

    def __init__(self, side, peak_labels=None):
        super().__init__()
        self.side = side
        self.peak_labels = list(peak_labels or ['p13', 'n23'])
        self.setBackground('w')

        self.pw = self.addPlot(row=0, col=1)
        self.pw.setRange(yRange=(-100, 250), xRange=(0, 35), disableAutoRange=True)
        # Grid explícito con tick spacing (estilo ABR): más prolijo que
        # showGrid() default de pyqtgraph. Eje x en pasos de 5ms, eje y en 50µV.
        self.color_pen = pg.mkColor(0, 0, 0, 255)
        self.grid = pg.GridItem(pen=self.color_pen, textPen=self.color_pen)
        self.pw.addItem(self.grid)
        self.grid.setTickSpacing(x=[5.0], y=[50.0])
        self.pw.setMouseEnabled(x=False, y=True)
        self.pw.setMenuEnabled(False)
        self.pw.hideButtons()
        self.pw.setLabel('bottom', 'ms')
        self.pw.getAxis('left').setStyle(showValues=False)
        self.pw.getViewBox().setMouseMode(pg.ViewBox.PanMode)

        # Estado
        self.data = {}  # curve_name -> {'x','y','gap','int','LatAmp':{}}
        self.marks = {}  # curve_name -> {pico: (lat, amp)}
        self.act_curve = None
        self.curve_int = {}  # curve_name -> int (dB SPL)

    # =====================================================================
    # API pública
    # =====================================================================

    def set_peak_labels(self, labels):
        """Cambia los picos que muestra (al cambiar subtipo). Limpia marcas."""
        self.peak_labels = list(labels)
        self.marks = {}

    def create_line(self, name, x, y, intencity):
        """Agrega o actualiza una curva. x,y son arrays."""
        if name in self.data:
            self.data[name]['x'] = x
            self.data[name]['y'] = y
        else:
            gap = 0
            self.data[name] = {
                'x': x, 'y': y, 'gap': gap,
                'LatAmp': {p: [None, None] for p in self.peak_labels},
            }
            self.act_curve = name
            color = COLOR_OD_ACTIVE if self.side == 0 else COLOR_OI_ACTIVE
            self.pw.plot(x=x, y=y + gap, pen=pg.mkPen(color, width=2), name=name)
            # Label intensidad como TextItem arriba de la curva
            label = pg.TextItem(text=f'{intencity} dB', color='k', anchor=(0.5, 1))
            label.setPos(x[-1], y[-1] + gap + 20)
            self.pw.addItem(label)
            label.curve_name = name
            self.curve_int[name] = intencity

    def active_curve(self, name):
        """Cambia la curva activa (la que recibe marcas)."""
        self.act_curve = name

    def delete_curve(self, name=None):
        """Borra curva (default = activa)."""
        name = name or self.act_curve
        if name not in self.data:
            return
        for item in list(self.pw.listDataItems()):
            if getattr(item, 'name', lambda: None)() == name:
                self.pw.removeItem(item)
        for item in list(self.pw.items):
            if getattr(item, 'curve_name', None) == name:
                self.pw.removeItem(item)
        for item in list(self.pw.items):
            if getattr(item, 'pico', None) and getattr(item, 'curve_parent', None) == name:
                self.pw.removeItem(item)
        self.data.pop(name, None)
        self.marks.pop(name, None)
        self.curve_int.pop(name, None)
        self.sig_del_curve.emit(name)
        if self.act_curve == name:
            self.act_curve = next(iter(self.data), None)

    def set_mark(self, curve_name, pico, lat, amp):
        """Marca un pico (drag del alumno). actualiza LatAmp + dibuja flecha."""
        if curve_name not in self.data:
            return
        if pico not in self.peak_labels:
            return
        self.data[curve_name]['LatAmp'][pico] = [lat, amp]
        # Borra marca previa del mismo pico
        for item in list(self.pw.items):
            if (getattr(item, 'pico', None) == pico and
                    getattr(item, 'curve_parent', None) == curve_name):
                self.pw.removeItem(item)
        # Crea flecha en (lat, amp)
        arrow = pg.TextItem(text=f'↓{pico.upper()}', color='k', anchor=(0.5, 0))
        arrow.setPos(lat, amp + 5)
        arrow.pico = pico
        arrow.curve_parent = curve_name
        self.pw.addItem(arrow)
        self.sig_change_value_mark.emit({
            'curve': curve_name, 'pico': pico, 'lat': lat, 'amp': amp,
        })

    def delete_mark(self, curve_name, pico):
        if curve_name in self.data and pico in self.data[curve_name]['LatAmp']:
            self.data[curve_name]['LatAmp'][pico] = [None, None]
        for item in list(self.pw.items):
            if (getattr(item, 'pico', None) == pico and
                    getattr(item, 'curve_parent', None) == curve_name):
                self.pw.removeItem(item)

    def limpiar_todo(self):
        self.pw.clear()
        self.data = {}
        self.marks = {}
        self.act_curve = None
        self.curve_int = {}

    # =====================================================================
    # Export
    # =====================================================================

    def export_jpg(self, path):
        """Exporta el plot como JPEG (usado por submit_report)."""
        exporter = pg.exporters.ImageExporter(self.pw)
        exporter.export(path)
