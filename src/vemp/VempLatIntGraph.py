"""
Gráfico latencia-intensidad para VEMP.

Réplica de AbrLatIntGraph con peak_labels parametrizable. Banda normativa
fija (placeholder, los rangos reales deberían venir de normative_data.json
en una iteración futura -- por ahora el patrón es mostrar el rango clínico
aceptado).
"""

import pyqtgraph as pg
from PySide6.QtWidgets import QWidget


class VempLatIntGraph(pg.GraphicsLayoutWidget):
    def __init__(self, peak_labels=None, parent=None):
        super().__init__(parent)
        self.peak_labels = peak_labels or ['p13', 'n23']
        self._setup()

    def _setup(self):
        self.pw = self.addPlot()
        self.pw.setLabel('bottom', 'dB SPL')
        self.pw.setLabel('left', 'ms')
        self.pw.setXRange(0, 100)
        self.pw.setYRange(0, 35)
        # Grid explícito con tick spacing (estilo ABR): x cada 10dB, y cada 2ms.
        self._color_pen = pg.mkColor(0, 0, 0, 255)
        self._grid = pg.GridItem(pen=self._color_pen, textPen=self._color_pen)
        self.pw.addItem(self._grid)
        self._grid.setTickSpacing(x=[10.0], y=[2.0])
        self.pw.setMouseEnabled(x=False, y=True)

        # Banda normativa placeholder (rangos clínicos aproximados por pico)
        self._filled_area()
        self.legend = self.pw.addLegend(offset=(10, 10))

    def _filled_area(self):
        # Banda genérica alrededor del baseline de cada pico (placeholder).
        # En una iteración futura, leer rangos reales de normative_data.json.
        bandas = {
            'p13': ([(0, 14.5), (100, 12.0)], [(0, 11.5), (100, 14.0)]),
            'n23': ([(0, 25.0), (100, 21.0)], [(0, 21.0), (100, 25.0)]),
            'n10': ([(0, 11.5), (100, 9.0)],  [(0, 9.0),  (100, 11.5)]),
            'p16': ([(0, 18.0), (100, 14.5)], [(0, 14.5), (100, 18.0)]),
        }
        for pico in self.peak_labels:
            if pico not in bandas:
                continue
            (top_pts, bot_pts) = bandas[pico]
            xs_top = [p[0] for p in top_pts]
            ys_top = [p[1] for p in top_pts]
            xs_bot = [p[0] for p in bot_pts]
            ys_bot = [p[1] for p in bot_pts]
            top = self.pw.plot(xs_top, ys_top, pen=pg.mkPen((100, 100, 200, 100), width=1))
            bot = self.pw.plot(xs_bot, ys_bot, pen=pg.mkPen((100, 100, 200, 100), width=1))
            top.is_band = True
            bot.is_band = True
            fill = pg.FillBetweenItem(top, bot)
            fill.setBrush(pg.mkBrush(100, 100, 250, 60))
            self.pw.addItem(fill)

    def plot_data(self, data_dict):
        """data_dict: {curve_name: {'side','int','LatAmp':{pico:[lat,amp]}}}"""
        # Limpia puntos anteriores (preserva bandas)
        for item in list(self.pw.listDataItems()):
            if not getattr(item, 'is_band', False):
                self.pw.removeItem(item)

        symbols = {'p13': 'o', 'n23': 't1', 'n10': 't', 'p16': 't3'}
        colors = {'OD': (192, 57, 43), 'OI': (41, 128, 185)}
        points = {p: {'x': [], 'y': [], 'brush': []} for p in self.peak_labels}

        for name, info in (data_dict or {}).items():
            if not isinstance(info, dict):
                continue
            side = info.get('side', 'OD')
            intensity = info.get('int')
            la = info.get('LatAmp', {})
            if intensity is None:
                continue
            for pico, vals in la.items():
                if pico not in self.peak_labels or not isinstance(vals, (list, tuple)):
                    continue
                lat = vals[0] if vals[0] is not None else None
                if lat is None:
                    continue
                points[pico]['x'].append(intensity)
                points[pico]['y'].append(lat)
                points[pico]['brush'].append(colors.get(side, (100, 100, 100)))

        for pico, pts in points.items():
            if pts['x']:
                pen = pg.mkPen(width=0)
                symbol = symbols.get(pico, 'o')
                brushes = [pg.mkBrush(*c) for c in pts['brush']]
                scatter = pg.ScatterPlotItem(
                    x=pts['x'], y=pts['y'], pen=pen, symbol=symbol,
                    size=10, brush=brushes,
                )
                self.pw.addItem(scatter)

    def clear_graph(self):
        for item in list(self.pw.listDataItems()):
            if not getattr(item, 'is_band', False):
                self.pw.removeItem(item)

    def export_jpg(self, path):
        """Exporta el plot como JPEG (usado por submit_report)."""
        exporter = pg.exporters.ImageExporter(self.pw)
        exporter.export(path)
