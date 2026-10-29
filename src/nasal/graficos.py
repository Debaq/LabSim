"""Las pantallas de la rinomanometría y la rinometría, en pyqtgraph.

Dibujan lo mismo que js/graficos.js de RinoSim (las figuras del libro):
fosa derecha en rojo y fosa izquierda en azul, reposo en trazo lleno y con
vasoconstrictor en guiones. Solo dibujan: los números salen de
nasal/rinomanometria.py y nasal/rinometria.py.
"""

import math

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt

from core import tema
from nasal.referencias import REFERENCIA_UNILATERAL_150
from nasal.rinomanometria import PRESIONES, RADIO_BROMS
from nasal.rinometria import X_CONFIABLE, X_CURVA

COLOR = {'D': tema.OD, 'I': tema.OI}
ZONA_POCO_FIABLE = (244, 236, 230, 160)
MARCAS_LOG = [0.1, 0.2, 0.5, 1, 2, 5, 10]

# Topes "redondos" de los ejes, los mismos de RinoSim.
TOPES_P = [300, 450, 600, 900, 1200]
TOPES_V = [500, 750, 1000, 1500, 2000, 3000]
TOPES_R = [0.5, 0.8, 1.0, 1.5, 2, 3, 5]


def _tope(v, lista):
    return next((x for x in lista if x >= v), lista[-1])


def _plot(etiqueta_x, etiqueta_y):
    plot = pg.PlotWidget()
    plot.setBackground(tema.TARJETA)
    vb = plot.getPlotItem().getViewBox()
    vb.setMouseEnabled(x=False, y=False)
    vb.setMenuEnabled(False)
    plot.hideButtons()
    plot.setMenuEnabled(False)
    plot.showGrid(x=True, y=True, alpha=0.25)
    for nombre, texto in (('bottom', etiqueta_x), ('left', etiqueta_y)):
        eje = plot.getAxis(nombre)
        eje.setPen(pg.mkPen(tema.BORDE_FUERTE))
        eje.setTextPen(pg.mkPen(tema.TEXTO_TENUE))
        eje.setLabel(texto, color=tema.TEXTO_TENUE)
    return plot


def _pluma(lado, vc, ancho=2.4):
    if vc:
        return pg.mkPen(COLOR[lado], width=ancho - 0.4, style=Qt.PenStyle.DashLine)
    return pg.mkPen(COLOR[lado], width=ancho)


def _tenue(estilo=Qt.PenStyle.DotLine, ancho=1):
    return pg.mkPen(tema.TEXTO_TENUE, width=ancho, style=estilo)


def _texto(plot, x, y, texto, color=tema.TEXTO_TENUE, ancla=(0.5, 0.5), negrita=False):
    item = pg.TextItem(texto, color=color, anchor=ancla)
    if negrita:
        fuente = item.textItem.font()
        fuente.setBold(True)
        item.setFont(fuente)
    plot.addItem(item)
    item.setPos(x, y)
    return item


class GraficoRinomanometria:
    """Curva presión-flujo en cuatro cuadrantes (H26): la FND por I y III,
    la FNI por II y IV. Inspiración arriba."""

    def __init__(self):
        self.widget = _plot('presión (Pa)', 'flujo (cm³/s)')

    def dibujar(self, series, ciclos=True, referencia=True, broms=False):
        """series: [(fosas {D, I} de mide_fosa o None, vc bool)]."""
        plot = self.widget
        plot.clear()
        pmax = vmax = 0.0
        for fosas, _vc in series:
            for f in filter(None, fosas.values()):
                for c in f['ciclos']:
                    pmax = max(pmax, max(abs(p) for p in c['P']))
                    vmax = max(vmax, max(abs(v) for v in c['V']))
        P = _tope(pmax * 1.02, TOPES_P)
        V = _tope(vmax * 1.05, TOPES_V)
        plot.setXRange(-P, P, padding=0)
        plot.setYRange(-V, V, padding=0)

        plot.addItem(pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(tema.BORDE_FUERTE, width=1.2)))
        plot.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(tema.BORDE_FUERTE, width=1.2)))
        for pr in PRESIONES:
            for s in (-1, 1):
                plot.addItem(pg.InfiniteLine(pos=s * pr, angle=90, pen=_tenue(Qt.PenStyle.DashLine, 0.8)))
        for x, y, t in ((P, V, 'I'), (-P, V, 'II'), (-P, -V, 'III'), (P, -V, 'IV')):
            _texto(plot, x * 0.95, y * 0.93, t)
        _texto(plot, P / 2, -V * 0.93, 'FND: I y III', COLOR['D'], negrita=True)
        _texto(plot, -P / 2, -V * 0.93, 'FNI: II y IV', COLOR['I'], negrita=True)

        if referencia:
            # V = P / 0,4: una curva por encima a 150 Pa tiene menos
            # resistencia que la referencia del libro.
            r = REFERENCIA_UNILATERAL_150['valor']
            fin = min(P, V * r)
            for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
                plot.plot([0, a * fin], [0, b * fin / r], pen=_tenue())
        if broms:
            # Radio 200 con 1 Pa = 1 cm³/s: en pantalla es una elipse si los
            # ejes no tienen la misma escala (igual que en RinoSim).
            t = np.linspace(0, 2 * math.pi, 181)
            plot.plot(RADIO_BROMS * np.cos(t), RADIO_BROMS * np.sin(t), pen=_tenue(Qt.PenStyle.DashLine))

        for fosas, vc in series:
            for lado in ('D', 'I'):
                f = fosas.get(lado)
                if not f:
                    continue
                signo = 1 if lado == 'D' else -1
                if ciclos and not vc:
                    color = pg.mkColor(COLOR[lado])
                    color.setAlphaF(0.35)
                    for c in f['ciclos']:
                        plot.plot([signo * p for p in c['P']], c['V'], pen=pg.mkPen(color, width=0.8))
                pluma = _pluma(lado, vc, 2.6)
                ins = f['media']['insp']
                esp = f['media']['esp']
                plot.plot([signo * p for p, _ in ins], [v for _, v in ins], pen=pluma)
                plot.plot([-signo * p for p, _ in esp], [-v for _, v in esp], pen=pluma)
                if broms and f.get('broms') and not vc:
                    b = f['broms']
                    plot.addItem(pg.ScatterPlotItem([signo * b['P']], [b['V']], size=8,
                                                    pen=pg.mkPen('#ffffff', width=1.2),
                                                    brush=pg.mkBrush(COLOR[lado])))


class GraficoResistencia:
    """Resistencia contra presión, rama inspiratoria: la resistencia SUBE
    con la presión (H26)."""

    def __init__(self):
        self.widget = _plot('presión (Pa)', 'R, Pa/(cm³/s)')

    def dibujar(self, series):
        plot = self.widget
        plot.clear()
        pmax = rmax = 0.0
        curvas = []
        for fosas, vc in series:
            for lado in ('D', 'I'):
                f = fosas.get(lado)
                if not f:
                    continue
                pts = [(p, p / v) for p, v in f['media']['insp'] if p >= 20 and v > 0]
                for p, r in pts:
                    pmax, rmax = max(pmax, p), max(rmax, r)
                curvas.append((pts, lado, vc))
        P = _tope(pmax, TOPES_P)
        R = _tope(rmax * 1.1, TOPES_R)
        plot.setXRange(0, P, padding=0)
        plot.setYRange(0, R, padding=0)
        for pr in PRESIONES:
            plot.addItem(pg.InfiniteLine(pos=pr, angle=90, pen=_tenue(Qt.PenStyle.DashLine, 0.8)))
        ref = REFERENCIA_UNILATERAL_150['valor']
        if ref <= R:
            plot.addItem(pg.InfiniteLine(pos=ref, angle=0, pen=_tenue()))
            _texto(plot, P, ref, f'referencia ≤ {str(ref).replace(".", ",")}',
                   ancla=(1, 1))
        for pts, lado, vc in curvas:
            if pts:
                plot.plot([p for p, _ in pts], [min(r, R) for _, r in pts], pen=_pluma(lado, vc))


class GraficoRinometria:
    """Área contra distancia desde la narina (H27), en escala logarítmica
    por defecto, con la zona poco fiable pasados ~5 cm y MCA1/MCA2."""

    AMIN = 0.1

    def __init__(self):
        self.widget = _plot('distancia desde la narina (cm)', 'área (cm²)')

    def dibujar(self, series, log=True, registros=True, verdad=False):
        """series: [(fosas {D, I} de rinometria.mide_fosa o None, vc bool)]."""
        plot = self.widget
        plot.clear()
        amax = 10 if log else 4
        y = (lambda a: math.log10(max(self.AMIN, min(amax, a)))) if log else \
            (lambda a: max(0.0, min(amax, a)))
        plot.setXRange(0, X_CURVA, padding=0)
        # La escala log se hace a mano (log10 del área + marcas rotuladas en
        # cm²): setLogMode de pyqtgraph no deja acotar el área a [0,1; 10].
        eje = plot.getAxis('left')
        if log:
            plot.setYRange(math.log10(self.AMIN), math.log10(amax), padding=0)
            eje.setTicks([[(math.log10(a), str(a).replace('.', ',')) for a in MARCAS_LOG]])
        else:
            plot.setYRange(0, amax, padding=0)
            eje.setTicks(None)

        zona = pg.LinearRegionItem(values=(X_CONFIABLE, X_CURVA), movable=False,
                                   brush=pg.mkBrush(*ZONA_POCO_FIABLE), pen=pg.mkPen(None))
        zona.setZValue(-10)
        plot.addItem(zona)
        # Arriba de la zona, sobre la grilla: el rótulo no pisa las curvas.
        _texto(plot, (X_CONFIABLE + X_CURVA) / 2, y(amax), 'más allá de ~5 cm: poco fiable',
               tema.AVISO, ancla=(0.5, 0))

        for fosas, vc in series:
            for lado in ('D', 'I'):
                f = fosas.get(lado)
                if not f:
                    continue
                if verdad and not vc:
                    plot.plot(f['verdad']['x'], [y(a) for a in f['verdad']['A']],
                              pen=pg.mkPen(COLOR[lado], width=1.2, style=Qt.PenStyle.DotLine))
                if registros:
                    color = pg.mkColor(COLOR[lado])
                    color.setAlphaF(0.45)
                    estilo = Qt.PenStyle.DashLine if vc else Qt.PenStyle.SolidLine
                    for r in f['registros']:
                        plot.plot(r['x'], [y(a) for a in r['A']], pen=pg.mkPen(color, width=0.9, style=estilo))
                media = curva_media(f)
                plot.plot([x for x, _ in media], [y(a) for _, a in media], pen=_pluma(lado, vc))
                if not vc:
                    p = f['promedio']
                    for d, a, nombre in ((p['dist1'], p['mca1'], 'MCA1'), (p['dist2'], p['mca2'], 'MCA2')):
                        plot.addItem(pg.ScatterPlotItem([d], [y(a)], size=8,
                                                        pen=pg.mkPen('#ffffff', width=1.2),
                                                        brush=pg.mkBrush(COLOR[lado])))
                        _texto(plot, d, y(a), nombre, COLOR[lado], ancla=(0.5, -0.4), negrita=True)


def curva_media(f):
    """Promedio punto a punto de los registros de una fosa (curvaMedia de RinoSim)."""
    n = len(f['registros'])
    x0 = f['registros'][0]['x']
    return [(x, sum(r['A'][i] for r in f['registros']) / n) for i, x in enumerate(x0)]
