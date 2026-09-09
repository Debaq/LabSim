"""
Latencia-intensidad y crecimiento de amplitud del VEMP.

Dos gráficos en la misma pestaña porque en un VEMP la lectura por
intensidad es sobre todo de AMPLITUD: la latencia casi no se mueve
(~0.05 ms/10 dB, ver LAT_SLOPE_MS_10DB) y lo que dice dónde está el umbral
es la amplitud pico-pico cayéndose hasta desaparecer.

- Arriba: latencia de cada pico vs intensidad, con la banda normativa.
- Abajo: amplitud pico-pico vs intensidad, un trazo por oído. Sin banda a
  propósito: la amplitud absoluta depende de cuánto contrajo el paciente
  (ver VempEmg), así que una banda fija ahí mentiría.

La banda de latencia sale de la MISMA normativa que genera las curvas
(resources/vemp/normative_data.json), corrida por la pendiente del
generador. El JSON no trae desviación estándar por pico, así que la
tolerancia es un valor declarado acá (TOLERANCIA_LAT_MS) y no un ±2 DE que
no tenemos: es una referencia de lectura, no un criterio normativo.
"""

import pyqtgraph as pg
import pyqtgraph.exporters  # noqa: F401  (registra ImageExporter)

from vemp.VEMP_generator_v1 import (INTENSIDAD_REF, LAT_SLOPE_MS_10DB,
                                    SUBTIPO_PEAKS)

TOLERANCIA_LAT_MS = 1.5
INT_MIN, INT_MAX = 30, 100

SIMBOLOS = {'p13': 'o', 'n23': 't1', 'n10': 't', 'p16': 't3'}
COLOR_LADO = {'OD': (192, 57, 43), 'OI': (41, 128, 185)}


class VempLatIntGraph(pg.GraphicsLayoutWidget):
    def __init__(self, peak_labels=None, parent=None):
        super().__init__(parent)
        self.peak_labels = list(peak_labels or SUBTIPO_PEAKS['CVEMP'])
        self.subtipo = 'CVEMP'
        self.baseline = {}
        self._bandas = []
        self.setBackground('w')
        self._setup()

    def _setup(self):
        color = pg.mkColor(0, 0, 0, 255)

        self.pw = self.addPlot(row=0, col=0)
        self.pw.setLabel('bottom', 'dB SPL')
        self.pw.setLabel('left', 'Latencia (ms)')
        self.grid = pg.GridItem(pen=color, textPen=color)
        self.pw.addItem(self.grid)
        self.grid.setTickSpacing(x=[10.0], y=[5.0])
        self.pw.setMouseEnabled(x=False, y=True)
        self.pw.setMenuEnabled(False)
        self.legend = self.pw.addLegend(offset=(10, 10))

        self.pw_amp = self.addPlot(row=1, col=0)
        self.pw_amp.setLabel('bottom', 'dB SPL')
        self.pw_amp.setLabel('left', 'Amplitud p-p (µV)')
        self.grid_amp = pg.GridItem(pen=color, textPen=color)
        self.pw_amp.addItem(self.grid_amp)
        self.grid_amp.setTickSpacing(x=[10.0])
        self.pw_amp.setMouseEnabled(x=False, y=True)
        self.pw_amp.setMenuEnabled(False)

        # El rango es FIJO y se pone a mano. Con el auto-range de pyqtgraph
        # encendido, cada item que se agrega (las dos líneas de cada banda,
        # el relleno, cada scatter) dispara un reajuste, y como pyqtgraph
        # los aplica de a uno el gráfico se ve crecer solo, como si tuviera
        # una animación. Un eje de un examen no se mueve mientras se mira.
        for plot in (self.pw, self.pw_amp):
            plot.enableAutoRange(x=False, y=False)
            plot.setAutoVisible(x=False, y=False)
            plot.hideButtons()          # el botón "A" vuelve a autoescalar
        self.set_rango_latencia()
        self.set_rango_amplitud()

    def set_rango_latencia(self, lo=0.0, hi=30.0):
        self.pw.setRange(xRange=(INT_MIN, INT_MAX), yRange=(lo, hi),
                         padding=0, disableAutoRange=True)

    def set_rango_amplitud(self, medido=None):
        """Escala de amplitud: se fija una vez, no la mueve el auto-range.

        El piso es la amplitud pico-pico normativa del subtipo, así que un
        examen sin respuesta se ve chico y no amplificado hasta llenar el
        gráfico; si lo medido es mayor (paciente que contrajo de más), manda
        lo medido para que el punto entre en pantalla.
        """
        amps = [abs(b.get('amp', 0.0)) for b in (self.baseline or {}).values()]
        normativa = sum(amps) if amps else 100.0
        hi = max(float(normativa), float(medido or 0.0), 1.0) * 1.15
        self.pw_amp.setRange(xRange=(INT_MIN, INT_MAX), yRange=(0, hi),
                             padding=0, disableAutoRange=True)
        self.grid_amp.setTickSpacing(x=[10.0], y=[self._paso(hi)])

    @staticmethod
    def _paso(rango):
        """Un paso de grilla legible para ~6 divisiones."""
        crudo = rango / 6.0
        for paso in (1, 2, 5, 10, 20, 25, 50, 100, 200, 500):
            if crudo <= paso:
                return float(paso)
        return crudo

    # =====================================================================
    # Banda normativa
    # =====================================================================

    def set_subtipo(self, subtipo, baseline=None):
        """Cambia los picos y redibuja la banda con la normativa de ESTE
        paciente (la que el generador usa para sus curvas)."""
        self.subtipo = subtipo
        self.peak_labels = list(SUBTIPO_PEAKS.get(subtipo, ['p13', 'n23']))
        self.baseline = baseline or {}
        self._draw_bands()

    def _draw_bands(self):
        for item in self._bandas:
            self.pw.removeItem(item)
        self._bandas = []
        if not self.baseline:
            return
        for pico in self.peak_labels:
            base = self.baseline.get(pico)
            if not base:
                continue
            xs = [INT_MIN, INT_MAX]
            # Misma pendiente con la que el generador corre las latencias.
            lats = [base['lat'] + (INTENSIDAD_REF - x) / 10 * LAT_SLOPE_MS_10DB
                    for x in xs]
            top = self.pw.plot(xs, [l + TOLERANCIA_LAT_MS for l in lats],
                               pen=pg.mkPen((100, 100, 200, 100), width=1))
            bot = self.pw.plot(xs, [l - TOLERANCIA_LAT_MS for l in lats],
                               pen=pg.mkPen((100, 100, 200, 100), width=1))
            top.is_band = True
            bot.is_band = True
            fill = pg.FillBetweenItem(top, bot)
            fill.setBrush(pg.mkBrush(100, 100, 250, 60))
            self.pw.addItem(fill)
            self._bandas += [top, bot, fill]
        # Rango vertical alrededor de la banda: con 0-35 fijo, un oVEMP
        # (9-16 ms) quedaba apretado en el tercio de abajo. Se calcula acá y
        # queda quieto -- el eje no se reacomoda al agregar puntos.
        lats = [b['lat'] for b in self.baseline.values() if 'lat' in b]
        if lats:
            self.set_rango_latencia(max(0.0, min(lats) - 6), max(lats) + 6)
        self.set_rango_amplitud()

    # =====================================================================
    # Puntos
    # =====================================================================

    def plot_data(self, data_dict, subtipo=None):
        """data_dict: la memoria de curvas del módulo. Se dibujan solo las
        del subtipo activo: latencias arriba, amplitud pico-pico abajo."""
        subtipo = subtipo or self.subtipo
        self.clear_graph()

        puntos = {p: {'x': [], 'y': [], 'brush': []} for p in self.peak_labels}
        crecimiento = {'OD': {}, 'OI': {}}

        for _, info in (data_dict or {}).items():
            if not isinstance(info, dict) or info.get('subtipo') != subtipo:
                continue
            intensidad = info.get('int')
            if intensidad is None:
                continue
            lado = info.get('side', 'OD')
            latamp = info.get('LatAmp') or {}
            for pico, vals in latamp.items():
                if pico not in puntos or not isinstance(vals, (list, tuple)):
                    continue
                if vals[0] is None:
                    continue
                puntos[pico]['x'].append(intensidad)
                puntos[pico]['y'].append(vals[0])
                puntos[pico]['brush'].append(COLOR_LADO.get(lado, (100, 100, 100)))
            p2p = info.get('p2p')
            if p2p is not None and lado in crecimiento:
                # Una curva por intensidad: si hay repetición, queda la mayor
                # (es la que el alumno informa).
                previo = crecimiento[lado].get(intensidad)
                crecimiento[lado][intensidad] = max(p2p, previo) if previo else p2p

        for pico, pts in puntos.items():
            if not pts['x']:
                continue
            scatter = pg.ScatterPlotItem(
                x=pts['x'], y=pts['y'], pen=pg.mkPen(width=0),
                symbol=SIMBOLOS.get(pico, 'o'), size=10,
                brush=[pg.mkBrush(*c) for c in pts['brush']],
                name=pico.upper())
            self.pw.addItem(scatter)

        medido = max((max(serie.values()) for serie in crecimiento.values() if serie),
                     default=0.0)
        self.set_rango_amplitud(medido)

        for lado, serie in crecimiento.items():
            if not serie:
                continue
            xs = sorted(serie)
            ys = [serie[x] for x in xs]
            color = COLOR_LADO[lado]
            self.pw_amp.plot(xs, ys, pen=pg.mkPen(color, width=2),
                             symbol='o', symbolSize=8,
                             symbolBrush=pg.mkBrush(*color), name=lado)

    def clear_graph(self):
        for item in self.pw.listDataItems():
            if not getattr(item, 'is_band', False):
                self.pw.removeItem(item)
        for item in list(self.pw.items):
            if isinstance(item, pg.ScatterPlotItem):
                self.pw.removeItem(item)
        for item in self.pw_amp.listDataItems():
            self.pw_amp.removeItem(item)

    def export_jpg(self, path):
        """Exporta el plot como JPEG (usado por submit_report)."""
        pg.exporters.ImageExporter(self.pw.scene()).export(path)
