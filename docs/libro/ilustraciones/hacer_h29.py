#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H29 (espirometría):

    h29-volumenes.svg     espirograma de reposo y maniobras máximas: volúmenes y capacidades
    h29-esfuerzo.svg      A: presiones en la vía aérea durante la espiración forzada (punto de igual presión);
                          B: curvas flujo-volumen con tres esfuerzos distintos
    h29-maniobra.svg      curva flujo-volumen y curva volumen-tiempo de una maniobra normal
    h29-patrones.svg      normal, obstructivo, restrictivo y mixto, en flujo-volumen y volumen-tiempo
    h29-via-aerea.svg     obstrucción de la vía aérea superior: fija, variable extratorácica e intratorácica
    h29-errores.svg       maniobras inaceptables y la forma que dejan

SVG propios, no IA. Las curvas se CALCULAN con un modelo sencillo: el flujo espiratorio depende solo
del volumen que ya salió, F(x) = PEF · (1 - exp(-x/τ)) · (1 - x)^p (x = fracción de la capacidad vital
espirada), y la curva volumen-tiempo sale de integrar dV/dt = F(V). Los parámetros (FVC, PEF, p, τ) son
de ejemplo, no de pacientes; las razones y tiempos que aparecen en el capítulo salen de este script
(se imprimen al correrlo). Los valores previstos del informe de ejemplo son ilustrativos."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import re  # noqa: E402
from hacer_h25 import Lienzo as _Lienzo, TINTA, TENUE, GRILLA, FUERTE, AVISO, RETRO, COCLEAR, IZQ  # noqa: E402

AQUI = pathlib.Path(__file__).parent
GRIS = '#b9b6ae'


class Lienzo(_Lienzo):
    """Igual que el de H26, con coma decimal en los textos."""

    def t(self, x, y, s, *a, **k):
        super().t(x, y, re.sub(r'(?<=\d)\.(?=\d)', ',', str(s)), *a, **k)


# ------------------------------------------------------------------ modelo
class Maniobra:
    """Una espiración forzada: FVC (L), PEF (L/s), forma p (1 = descenso recto; >1 = cóncavo), tau (arranque)."""

    def __init__(self, fvc, pef, p, tau=0.05, pif=None):
        self.fvc, self.pef, self.p, self.tau = fvc, pef, p, tau
        self.pif = pif if pif is not None else pef * 0.6
        self._norm = max(self._crudo(i / 2000) for i in range(2001))

    def _crudo(self, x):
        return (1 - math.exp(-x / self.tau)) * (1 - x) ** self.p

    def F(self, x):
        """Flujo espiratorio (L/s) cuando ya salió la fracción x de la FVC."""
        x = min(max(x, 0.0), 1.0)
        return self.pef * self._crudo(x) / self._norm

    def FI(self, y):
        """Flujo inspiratorio (L/s, positivo) cuando ya entró la fracción y."""
        y = min(max(y, 0.0), 1.0)
        return self.pif * math.sin(math.pi * y) ** 0.6

    def tiempo(self, tmax=15.0, dt=0.002, x0=0.004, F=None):
        """Curva volumen-tiempo: integra dx/dt = F(x)/FVC. Devuelve [(t, V)]."""
        F = F or self.F
        x, t, out = x0, 0.0, []
        while t <= tmax:
            out.append((t, x * self.fvc))
            k1 = F(x) / self.fvc
            k2 = F(min(x + k1 * dt / 2, 1)) / self.fvc
            x = min(x + k2 * dt, 1.0)
            t += dt
        return out

    def fev(self, seg=1.0, F=None):
        c = self.tiempo(F=F)
        for t, v in c:
            if t >= seg:
                return v
        return c[-1][1]

    def meseta(self, F=None):
        """Primer instante en que el cambio de volumen en 1 s es < 0,025 L (criterio de fin de prueba)."""
        c = self.tiempo(tmax=40, F=F)
        paso = round(1 / 0.002)
        for i in range(len(c) - paso):
            if c[i + paso][1] - c[i][1] < 0.025:
                return c[i][0]
        return None

    def bev(self, F=None):
        """Volumen retroextrapolado: tangente en la pendiente máxima, cortada con V = 0."""
        c = self.tiempo(tmax=3, F=F)
        mejor = max(range(1, len(c) - 1), key=lambda i: c[i + 1][1] - c[i - 1][1])
        pend = (c[mejor + 1][1] - c[mejor - 1][1]) / (c[mejor + 1][0] - c[mejor - 1][0])
        t0 = c[mejor][0] - c[mejor][1] / pend
        v0 = 0.0
        if t0 > 0:
            v0 = min(c, key=lambda a: abs(a[0] - t0))[1]
        return t0, v0, pend, c[mejor]


NORMAL = Maniobra(4.5, 9.0, 1.5, 0.05, pif=6.5)
OBSTRUCTIVO = Maniobra(3.4, 5.0, 3.2, 0.06, pif=4.2)
RESTRICTIVO = Maniobra(2.8, 7.0, 1.3, 0.05, pif=4.6)
MIXTO = Maniobra(2.3, 3.8, 3.0, 0.06, pif=3.2)


# ------------------------------------------------------------------ ejes
class Eje:
    def __init__(self, c, x0, y0, w, h, xmin, xmax, ymin, ymax):
        self.c, self.x0, self.y0, self.w, self.h = c, x0, y0, w, h
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax

    def X(self, v):
        return self.x0 + (v - self.xmin) / (self.xmax - self.xmin) * self.w

    def Y(self, v):
        return self.y0 + self.h - (v - self.ymin) / (self.ymax - self.ymin) * self.h

    def pts(self, xs, ys):
        return [(self.X(a), self.Y(b)) for a, b in zip(xs, ys)]

    def marco(self, xt=None, yt=None, xlab='', ylab='', cero=True, fmt_x='{:g}', fmt_y='{:g}'):
        c = self.c
        for v in (xt or []):
            c.l(self.X(v), self.y0, self.X(v), self.y0 + self.h, GRILLA, 1)
            c.t(self.X(v), self.Y(self.ymin) + 13, fmt_x.format(v), 8, TENUE)
        for v in (yt or []):
            c.l(self.x0, self.Y(v), self.x0 + self.w, self.Y(v), GRILLA, 1)
            c.t(self.x0 - 5, self.Y(v) + 3, fmt_y.format(v), 8, TENUE, 'end')
        if cero and self.ymin < 0 < self.ymax:
            c.l(self.x0, self.Y(0), self.x0 + self.w, self.Y(0), TINTA, 1.2)
        c.l(self.x0, self.y0, self.x0, self.y0 + self.h, TINTA, 1.3)
        c.l(self.x0, self.y0 + self.h, self.x0 + self.w, self.y0 + self.h, TINTA, 1.3)
        if xlab:
            c.t(self.x0 + self.w / 2, self.y0 + self.h + 28, xlab, 8.5, TINTA)
        if ylab:
            c.raw(f'<text x="{self.x0 - 36}" y="{self.y0 + self.h / 2}" font-family="\'Plus Jakarta Sans\', sans-serif" '
                  f'font-size="{8.5 * 1.2:.1f}" fill="{TINTA}" text-anchor="middle" '
                  f'transform="rotate(-90 {self.x0 - 36} {self.y0 + self.h / 2})">{ylab}</text>')


def lazo_pts(m, ej, F=None, n=200, insp=True, vmax=None):
    """Puntos del lazo flujo-volumen: espiración (arriba) e inspiración (abajo); x = litros espirados."""
    F = F or m.F
    ex = [(m.fvc * i / n, F(i / n)) for i in range(n + 1)]
    pe = [(ej.X(v), ej.Y(f)) for v, f in ex]
    if not insp:
        return pe, []
    # inspiración: de RV (extremo derecho) a TLC (izquierda)
    pi_ = [(ej.X(m.fvc * (1 - i / n)), ej.Y(-m.FI(i / n))) for i in range(n + 1)]
    return pe, pi_


def curva_tiempo(m, ej, F=None, tmax=None):
    c = m.tiempo(tmax=tmax or ej.xmax, F=F)
    return [(ej.X(t), ej.Y(v)) for t, v in c if t <= ej.xmax]


# ------------------------------------------------------------------ 1. volúmenes y capacidades
def volumenes():
    # litros de ejemplo; solo se usan para dibujar a escala y para las sumas que se imprimen
    TV, IRV, ERV, RV = 0.5, 3.0, 1.1, 1.2
    FRC, IC, VC, TLC = ERV + RV, TV + IRV, IRV + TV + ERV, IRV + TV + ERV + RV
    c = Lienzo(740, 400)
    c.t(14, 20, 'A · Espirograma: el volumen que entra y sale de la boca en el tiempo', 10, TINTA, 'start', 700)
    ej = Eje(c, 70, 40, 440, 290, 0, 40, 0, 6.2)
    ej.marco(xt=[0, 10, 20, 30, 40], yt=[0, 1, 2, 3, 4, 5, 6], ylab='volumen (L)', xlab='tiempo (s) →')
    # el espirómetro no ve el RV: zona gris desde 0 hasta RV
    c.raw(f'<rect x="{ej.X(0)}" y="{ej.Y(RV)}" width="{ej.w}" height="{ej.Y(0) - ej.Y(RV)}" fill="{GRIS}" opacity=".35"/>')
    c.t(ej.X(20), ej.Y(RV / 2) + 3, 'volumen residual (RV): no sale del tórax, el espirómetro no lo mide', 8.5, TINTA)
    # trazado: reposo, inspiración máxima, reposo, espiración máxima, reposo
    pts = []

    def seg(t0, t1, v0, v1, n=40, suave=True):
        for i in range(n + 1):
            u = i / n
            u = (1 - math.cos(math.pi * u)) / 2 if suave else u
            pts.append((t0 + (t1 - t0) * u, v0 + (v1 - v0) * u))

    base = RV + ERV     # FRC: nivel de reposo al final de la espiración tranquila
    tv = lambda t: base + TV * (0.5 - 0.5 * math.cos(2 * math.pi * t / 4))
    for i in range(0, 16 * 4 + 1):
        t = i * 0.25
        pts.append((t, tv(t)))
    # llegada a la inspiración máxima
    seg(16, 19, base, TLC, 30)
    seg(19, 21, TLC, TLC, 4)
    seg(21, 27, TLC, RV, 40)
    seg(27, 29, RV, RV, 4)
    seg(29, 31, RV, base, 20)
    for i in range(1, 9 * 4 + 1):
        t = 31 + i * 0.25
        pts.append((t, base + TV * (0.5 - 0.5 * math.cos(2 * math.pi * (t - 31) / 4))))
    c.poli([(ej.X(t), ej.Y(v)) for t, v in pts], COCLEAR, 2.2)
    # niveles
    for nom, v, col in (('TLC', TLC, TINTA), ('FRC', FRC + RV - RV, TENUE), ('RV', RV, TINTA)):
        pass
    c.l(ej.X(0), ej.Y(TLC), ej.X(40), ej.Y(TLC), FUERTE, 1, '4 3')
    c.l(ej.X(0), ej.Y(RV), ej.X(40), ej.Y(RV), FUERTE, 1, '4 3')
    c.l(ej.X(0), ej.Y(RV + ERV), ej.X(40), ej.Y(RV + ERV), FUERTE, 1, '4 3')
    # llaves (a la derecha, volúmenes) con flechas simples
    def llave(x, v0, v1, texto, col=TINTA, lado=1, ancho=7):
        ya, yb = ej.Y(v1), ej.Y(v0)
        c.l(x, ya, x, yb, col, 1.6)
        c.l(x, ya, x - lado * ancho, ya, col, 1.6)
        c.l(x, yb, x - lado * ancho, yb, col, 1.6)
        c.t(x + lado * 6, (ya + yb) / 2 + 3, texto, 8.5, col, 'start' if lado == 1 else 'end', 700)

    xr = ej.X(40) + 8
    llave(xr, RV + ERV + TV, TLC, 'IRV', RETRO)
    llave(xr, RV + ERV, RV + ERV + TV, 'TV', COCLEAR)
    llave(xr, RV, RV + ERV, 'ERV', RETRO)
    llave(xr, 0, RV, 'RV', TENUE)
    xr2 = xr + 52
    llave(xr2, RV, TLC, 'VC', AVISO)
    llave(xr2 + 52, 0, RV + ERV, 'FRC', TENUE)
    llave(xr2 + 52, RV + ERV, TLC, 'IC', AVISO)
    llave(xr2 + 104, 0, TLC, 'TLC', TINTA)
    c.t(ej.X(8), ej.Y(base + TV) - 18, 'respiración tranquila', 8.5, COCLEAR, 'middle', 700)
    c.t(ej.X(8), ej.Y(base + TV) - 6, '(volumen corriente, TV)', 8, COCLEAR)
    c.t(ej.X(18.5), ej.Y(TLC) - 6, 'inspiración máxima', 8.5, TINTA)
    c.t(ej.X(35), ej.Y(1.6), 'espiración máxima', 8.5, TINTA)
    # B: leyenda
    ly = 372
    c.t(14, ly, f'IRV volumen de reserva inspiratorio · TV volumen corriente · ERV volumen de reserva espiratorio · RV volumen residual', 8, TINTA, 'start')
    c.t(14, ly + 14, f'VC capacidad vital = IRV + TV + ERV · IC capacidad inspiratoria = TV + IRV · FRC capacidad residual funcional = ERV + RV · TLC = VC + RV',
        8, TINTA, 'start')
    c.guardar('h29-volumenes.svg')
    print('VOLUMENES (L, ejemplo):', dict(TV=TV, IRV=IRV, ERV=ERV, RV=RV, VC=VC, IC=IC, FRC=FRC, TLC=TLC))


# ------------------------------------------------------------------ 2. esfuerzo
def esfuerzo():
    c = Lienzo(740, 360)
    c.t(14, 20, 'A · Presiones en la vía aérea al espirar a la fuerza', 10, TINTA, 'start', 700)
    c.t(400, 20, 'B · Tres esfuerzos distintos, la misma curva al final', 10, TINTA, 'start', 700)
    PEL = 10.0  # cmH2O, ejemplo: retracción elástica a ese volumen
    casos = [('esfuerzo moderado', 10.0, 40), ('esfuerzo máximo', 30.0, 180)]
    res = []
    for (nom, ppl, y0) in casos:
        palv = ppl + PEL
        x_epp = PEL / palv   # fracción del camino alvéolo → boca en que P vía aérea = P pleural
        res.append((nom, ppl, palv, x_epp))
        xa, xb = 30, 330
        # tubo (vía aérea): alvéolo a la izquierda, boca a la derecha
        c.raw(f'<circle cx="{xa + 18}" cy="{y0 + 40}" r="22" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
        c.t(xa + 18, y0 + 44, 'alvéolo', 8, TINTA)
        ex = xa + 40 + (xb - xa - 40) * x_epp
        c.raw(f'<rect x="{xa + 40}" y="{y0 + 32}" width="{xb - xa - 40}" height="16" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
        # tramo comprimido (corriente abajo del punto de igual presión)
        c.raw(f'<rect x="{ex:.1f}" y="{y0 + 37}" width="{xb - ex:.1f}" height="6" fill="{AVISO}" opacity=".35"/>')
        c.l(ex, y0 + 22, ex, y0 + 58, AVISO, 1.6, '3 2')
        c.t(ex, y0 + 18, 'punto de igual presión', 8, AVISO, 'middle', 700)
        c.t((ex + xb) / 2, y0 + 70, 'vía aérea comprimida', 8, AVISO)
        c.t(xb + 6, y0 + 44, 'boca', 8, TENUE, 'start')
        c.t(xa, y0 - 4, f'{nom}: P pleural {ppl:g} cmH₂O · P alveolar {palv:g} cmH₂O', 8.5, TINTA, 'start', 700)
        # perfil de presión
        c.t(xa + 40, y0 + 90, f'presión en la vía aérea: de {palv:g} cmH₂O en el alvéolo a 0 en la boca', 8, TENUE, 'start')
    c.t(30, 330, 'La presión dentro de la vía aérea cae de la alveolar a cero en la boca. Donde iguala a la presión pleural, la vía', 8, TENUE, 'start')
    c.t(30, 342, 'aérea empieza a comprimirse. Hasta ese punto el aire lo empuja solo la retracción elástica del pulmón (10 cmH₂O en el ejemplo):', 8, TENUE, 'start')
    c.t(30, 354, 'esfuerzo mayor aumenta la presión pleural, pero no cambia esa presión motriz.', 8, TENUE, 'start')
    # B: flujo-volumen con tres esfuerzos
    ej = Eje(c, 440, 40, 270, 230, 0, 5, 0, 11)
    ej.marco(xt=[0, 1, 2, 3, 4, 5], yt=[0, 2, 4, 6, 8, 10], xlab='volumen espirado (L)', ylab='flujo (L/s)')
    m = NORMAL
    cols = [(1.0, AVISO, 'esfuerzo máximo'), (0.75, COCLEAR, 'submáximo'), (0.5, IZQ, 'débil')]
    for e, col, nom in cols:
        def Fe(x, e=e):
            tope = e * m.pef * (1 - math.exp(-x / m.tau * 0.8))
            return min(m.F(x), tope)
        pe, _ = lazo_pts(m, ej, F=Fe, insp=False)
        c.poli(pe, col, 2)
    c.t(ej.X(1.05), ej.Y(9.4), 'máximo', 8.5, AVISO, 'start', 700)
    c.t(ej.X(1.6), ej.Y(7.4), 'submáximo', 8.5, COCLEAR, 'start', 700)
    c.t(ej.X(0.9), ej.Y(3.0), 'débil', 8.5, IZQ, 'start', 700)
    c.t(ej.X(5), ej.Y(8.4), 'el último tramo', 8.5, TINTA, 'end', 700)
    c.t(ej.X(5), ej.Y(7.6), 'coincide: no depende', 8.5, TINTA, 'end', 700)
    c.t(ej.X(5), ej.Y(6.8), 'del esfuerzo', 8.5, TINTA, 'end', 700)
    c.guardar('h29-esfuerzo.svg')
    for r in res:
        print('EPP', r)


# ------------------------------------------------------------------ 3. maniobra normal
def maniobra():
    c = Lienzo(760, 400)
    m = NORMAL
    c.t(14, 20, 'A · Curva flujo-volumen', 10, TINTA, 'start', 700)
    c.t(404, 20, 'B · Curva volumen-tiempo', 10, TINTA, 'start', 700)
    ej = Eje(c, 60, 40, 300, 270, 0, 5, -8, 11)
    ej.marco(xt=[0, 1, 2, 3, 4, 5], yt=[-6, -4, -2, 0, 2, 4, 6, 8, 10], xlab='volumen espirado (L) →', ylab='flujo (L/s)')
    pe, pi_ = lazo_pts(m, ej)
    c.poli(pe + pi_, COCLEAR, 2.4)
    # PEF
    xp = max(range(len(pe)), key=lambda i: -pe[i][1])
    px, py = pe[xp]
    c.punto(px, py, AVISO)
    c.t(px + 12, py - 4, f'PEF {m.pef:g} L/s', 8.5, AVISO, 'start', 700)
    # FEF50
    v50 = m.fvc * 0.5
    c.l(ej.X(v50), ej.Y(0), ej.X(v50), ej.Y(m.F(0.5)), TENUE, 1, '3 3')
    c.punto(ej.X(v50), ej.Y(m.F(0.5)), RETRO)
    c.t(ej.X(v50) + 8, ej.Y(m.F(0.5)) - 6, f'FEF50 {m.F(0.5):.1f} L/s', 8.5, RETRO, 'start', 700)
    # FEF25-75
    for fr in (0.25, 0.75):
        c.l(ej.X(m.fvc * fr), ej.Y(0), ej.X(m.fvc * fr), ej.Y(-1.0), TENUE, 1)
    c.l(ej.X(m.fvc * 0.25), ej.Y(-1.0), ej.X(m.fvc * 0.75), ej.Y(-1.0), RETRO, 2)
    c.t(ej.X(m.fvc * .5), ej.Y(-1.0) + 12, 'FEF25-75', 8.5, RETRO, 'middle', 700)
    # FVC
    c.l(ej.X(m.fvc), ej.Y(0), ej.X(m.fvc), ej.Y(0) - 0, TINTA, 1)
    c.t(ej.X(m.fvc), ej.Y(0) - 8, f'FVC {m.fvc:g} L', 8.5, TINTA, 'end', 700)
    # inspiración
    c.t(ej.X(2.5), ej.Y(-4.2), 'inspiración forzada', 8.5, TENUE)
    # fases numeradas
    def fase(n, x, y, t, anc='middle'):
        c.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8.5" fill="#fff" stroke="{TINTA}" stroke-width="1.2"/>')
        c.t(x, y + 3.3, str(n), 8.5, TINTA, 'middle', 700)
    # 1: inspiración máxima (fin de la inspiración previa, en el origen), 2: inicio explosivo, 3: espiración completa, 4: inspiración rápida
    fase(1, ej.X(0.4), ej.Y(1.6), '')
    fase(2, ej.X(0.75), ej.Y(5.0), '')
    fase(3, ej.X(3.2), ej.Y(m.F(3.2 / m.fvc)) - 16, '')
    fase(4, ej.X(1.8), ej.Y(-m.FI(0.64)) - 16, '')
    # B volumen-tiempo
    ev = Eje(c, 440, 40, 300, 270, 0, 8, 0, 5)
    ev.marco(xt=[0, 1, 2, 3, 4, 5, 6, 7, 8], yt=[0, 1, 2, 3, 4, 5], xlab='tiempo (s) →', ylab='volumen espirado (L)')
    c.poli(curva_tiempo(m, ev), COCLEAR, 2.4)
    f1 = m.fev(1.0)
    c.l(ev.X(1), ev.Y(0), ev.X(1), ev.Y(f1), TENUE, 1, '3 3')
    c.l(ev.X(0), ev.Y(f1), ev.X(1), ev.Y(f1), TENUE, 1, '3 3')
    c.punto(ev.X(1), ev.Y(f1), AVISO)
    c.t(ev.X(1) + 10, ev.Y(f1) + 16, f'FEV1 {f1:.2f} L', 8.5, AVISO, 'start', 700)
    c.l(ev.X(0), ev.Y(m.fvc), ev.X(8), ev.Y(m.fvc), TENUE, 1, '3 3')
    c.t(ev.X(8) - 2, ev.Y(m.fvc) - 6, f'FVC {m.fvc:g} L', 8.5, TINTA, 'end', 700)
    tm = m.meseta()
    c.raw(f'<rect x="{ev.X(tm)}" y="{ev.Y(m.fvc) - 6}" width="{ev.X(tm + 1) - ev.X(tm)}" height="12" fill="{RETRO}" opacity=".25"/>')
    c.t(ev.X(tm + .5), ev.Y(m.fvc) + 22, 'meseta: &lt; 0,025 L en 1 s', 8, RETRO, 'middle', 700)
    # leyenda de fases
    ly = 372
    c.t(14, ly, '① punto de partida: inspiración máxima  ② inicio explosivo («soplar» fuerte y rápido)  ③ seguir espirando hasta vaciar  ④ inspiración rápida de vuelta a TLC', 8, TINTA, 'start')
    c.t(14, ly + 14, 'FEF25-75: flujo promedio entre el 25 % y el 75 % de la FVC espirada. FEF50: flujo cuando ya salió la mitad de la FVC.', 8, TENUE, 'start')
    c.guardar('h29-maniobra.svg')
    print('NORMAL FEV1', round(f1, 2), 'FVC', m.fvc, 'FEV1/FVC', round(f1 / m.fvc, 2), 'meseta (s)', round(tm, 1),
          'FEF50', round(m.F(.5), 1), 'FEF25-75', round(sum(m.F(0.25 + .5 * i / 100) for i in range(101)) / 101, 2))


# ------------------------------------------------------------------ 4. patrones
def patrones():
    c = Lienzo(780, 545)
    paneles = [('Obstructivo', OBSTRUCTIVO, AVISO), ('Restrictivo', RESTRICTIVO, IZQ), ('Mixto', MIXTO, COCLEAR)]
    ancho, sep = 200, 38
    x_ini = 62
    res = {}
    for k, (nom, m, col) in enumerate(paneles):
        x0 = x_ini + k * (ancho + sep)
        c.t(x0 + ancho / 2, 22, nom, 10.5, col, 'middle', 700)
        ej = Eje(c, x0, 36, ancho, 190, 0, 5, -7, 11)
        ej.marco(xt=[0, 1, 2, 3, 4, 5], yt=[-6, -3, 0, 3, 6, 9], xlab='volumen espirado (L)', ylab='flujo (L/s)' if k == 0 else '')
        pn, pin = lazo_pts(NORMAL, ej)
        c.poli(pn + pin, GRIS, 1.6, '4 3')
        pe, pi_ = lazo_pts(m, ej)
        c.poli(pe + pi_, col, 2.4)
        ev = Eje(c, x0, 292, ancho, 170, 0, 15, 0, 5)
        ev.marco(xt=[0, 3, 6, 9, 12, 15], yt=[0, 1, 2, 3, 4, 5], xlab='tiempo (s)', ylab='volumen (L)' if k == 0 else '')
        c.poli(curva_tiempo(NORMAL, ev, tmax=15), GRIS, 1.6, '4 3')
        c.poli(curva_tiempo(m, ev, tmax=15), col, 2.4)
        f1 = m.fev(1.0)
        c.punto(ev.X(1), ev.Y(f1), col)
        tm = m.meseta()
        res[nom] = (m.fvc, f1, f1 / m.fvc, m.pef, tm)
        c.t(x0 + ancho - 2, 292 + 18, f'FEV1 {f1:.2f} L · FVC {m.fvc:g} L', 8.5, col, 'end', 700)
        c.t(x0 + ancho - 2, 292 + 30, f'FEV1/FVC {f1 / m.fvc:.2f}', 8.5, col, 'end', 700)
    f1n = NORMAL.fev(1.0)
    res['Normal'] = (NORMAL.fvc, f1n, f1n / NORMAL.fvc, NORMAL.pef, NORMAL.meseta())
    c.t(14, 522, f'Línea gris punteada: la maniobra normal del ejemplo (FEV1 {f1n:.2f} L · FVC {NORMAL.fvc:g} L · FEV1/FVC {f1n / NORMAL.fvc:.2f}).', 8.5, TENUE, 'start')
    c.t(14, 536, 'Arriba, flujo-volumen; abajo, volumen-tiempo. En la espirometría sola, restrictivo y mixto se llaman «sospecha»: confirmarlos exige medir la TLC.', 8.5, TENUE, 'start')
    c.guardar('h29-patrones.svg')
    for k, v in res.items():
        print('PATRON', k, 'FVC %.2f FEV1 %.2f FEV1/FVC %.2f PEF %.1f meseta %s' % (v[0], v[1], v[2], v[3], None if v[4] is None else round(v[4], 1)))


# ------------------------------------------------------------------ 5. vía aérea superior
def via_aerea():
    c = Lienzo(780, 345)
    m = NORMAL
    casos = [('Normal', None, None, TENUE),
             ('Variable extratorácica', None, 3.0, IZQ),     # tope inspiratorio
             ('Variable intratorácica', 3.0, None, COCLEAR),  # tope espiratorio
             ('Fija', 3.0, 3.0, AVISO)]
    ancho, sep, x_ini = 150, 34, 56
    out = {}
    for k, (nom, tope_e, tope_i, col) in enumerate(casos):
        x0 = x_ini + k * (ancho + sep)
        ej = Eje(c, x0, 44, ancho, 220, 0, 5, -8, 11)
        ej.marco(xt=[0, 2, 4], yt=[-6, -3, 0, 3, 6, 9], xlab='volumen espirado (L)', ylab='flujo (L/s)' if k == 0 else '')
        c.t(x0 + ancho / 2, 24, nom, 9.5, col if col != TENUE else TINTA, 'middle', 700)
        Fe = (lambda x, t=tope_e: min(m.F(x), t)) if tope_e else m.F
        n = 200
        pe = [(ej.X(m.fvc * i / n), ej.Y(Fe(i / n))) for i in range(n + 1)]
        FIf = (lambda y, t=tope_i: min(m.FI(y), t)) if tope_i else m.FI
        pi_ = [(ej.X(m.fvc * (1 - i / n)), ej.Y(-FIf(i / n))) for i in range(n + 1)]
        c.poli(pe + pi_, col, 2.4)
        fef50 = Fe(0.5)
        fif50 = FIf(0.5)
        out[nom] = (max(Fe(i / n) for i in range(n + 1)), fef50, fif50, fif50 / fef50)
        c.t(x0 + ancho / 2, 44 + 220 + 46, f'PEF {out[nom][0]:.1f} · FIF50/FEF50 {fif50 / fef50:.2f}', 8, TINTA, 'middle', 700)
    c.t(14, 336, 'Meseta (plano) del flujo = el aire no pasa más rápido por mucho que se empuje. FIF50: flujo inspiratorio a la mitad de la capacidad vital; FEF50: espiratorio.',
        8, TENUE, 'start')
    c.guardar('h29-via-aerea.svg')
    for k, v in out.items():
        print('VIA AEREA', k, 'PEF %.1f FEF50 %.1f FIF50 %.1f FIF50/FEF50 %.2f' % v)


# ------------------------------------------------------------------ 6. errores
def errores():
    c = Lienzo(780, 520)
    m = NORMAL
    ancho, altura, sepx = 200, 150, 52
    x_ini, y_ini = 62, 40
    res = []

    def panel(k, titulo, F, sub, extra=None, tiempo=False, col=AVISO, insp=False):
        f, cc = divmod(k, 3)
        x0 = x_ini + cc * (ancho + sepx)
        y0 = y_ini + f * (altura + 98)
        c.t(x0 + ancho / 2, y0 - 12, titulo, 9.5, TINTA, 'middle', 700)
        if tiempo:
            ej = Eje(c, x0, y0, ancho, altura, 0, 0.5, 0, 1.4)
            ej.marco(xt=[0, 0.1, 0.2, 0.3, 0.4, 0.5], yt=[0, 0.5, 1.0], xlab='tiempo (s)', ylab='volumen (L)' if cc == 0 else '')
            extra(ej)
            return ej
        ej = Eje(c, x0, y0, ancho, altura, 0, 5, 0, 11)
        ej.marco(xt=[0, 1, 2, 3, 4, 5], yt=[0, 3, 6, 9], xlab='volumen espirado (L)', ylab='flujo (L/s)' if cc == 0 else '')
        pn, _ = lazo_pts(m, ej, insp=False)
        c.poli(pn, GRIS, 1.4, '4 3')
        if extra:
            extra(ej)
        else:
            n = 400
            pts = []
            for i in range(n + 1):
                x = i / n
                v = F(x)
                if v is None:
                    break
                pts.append((ej.X(m.fvc * x), ej.Y(v)))
            c.poli(pts, col, 2.4)
        c.t(x0 + ancho / 2, y0 + altura + 44, sub[0], 8, TINTA, 'middle', 700)
        c.t(x0 + ancho / 2, y0 + altura + 55, sub[1], 8, TENUE)
        return ej

    # 0 tos en el primer segundo
    def tos(x):
        v = m.F(x)
        for xc, w in ((0.17, 0.012), (0.24, 0.012)):
            v *= 1 - 0.85 * math.exp(-((x - xc) / w) ** 2)
        return v
    panel(0, 'Tos al inicio', tos, ('caídas bruscas en la rama descendente', 'FEV1 inválido; la FVC puede salvarse'))
    # 1 cierre glótico
    xg = 0.30

    def cierre(x):
        return m.F(x) if x < xg else None

    def ext_cierre(ej):
        pts = [(ej.X(m.fvc * i / 300 * xg), ej.Y(m.F(i / 300 * xg))) for i in range(301)]
        pts.append((ej.X(m.fvc * xg), ej.Y(0)))
        c.poli(pts, AVISO, 2.4)
    panel(1, 'Cierre de la glotis', cierre, ('el flujo cae a cero con el aire todavía saliendo', 'si ocurre en el primer segundo, FEV1 inválido'), ext_cierre)
    # 2 fin prematuro
    xf = 0.93

    def ext_fin(ej):
        pts = [(ej.X(m.fvc * i / 300 * xf), ej.Y(m.F(i / 300 * xf))) for i in range(301)]
        pts.append((ej.X(m.fvc * xf), ej.Y(0)))
        c.poli(pts, AVISO, 2.4)
    panel(2, 'Fin prematuro', None, (f'corte con flujo todavía de {m.F(xf):.1f} L/s', 'FVC subestimada; el FEV1/FVC sube'), ext_fin)
    # 3 inicio lento (volumen-tiempo con retroextrapolación)
    lento = Maniobra(4.5, 8.0, 1.5, 0.30)
    t0, v0, pend, (tm_, vm_) = lento.bev()
    lim = max(0.100, 0.05 * lento.fvc)

    def ext_lento(ej):
        c.poli([(a, b) for a, b in curva_tiempo(lento, ej, tmax=0.5) if b >= ej.Y(1.4)], AVISO, 2.4)
        # el eje de volumen llega a 1,4 L: se dibuja la tangente
        ta, tb = max(t0, 0), min(t0 + 1.4 / pend, 0.5)
        va = pend * (ta - t0)
        vb = pend * (tb - t0)
        c.poli([(ej.X(ta), ej.Y(va)), (ej.X(tb), ej.Y(min(vb, 1.4)))], TINTA, 1.4, '5 3')
        c.punto(ej.X(t0), ej.Y(0), TINTA, 3)
        c.t(ej.X(t0) + 6, ej.Y(0) - 8, 't₀', 8.5, TINTA, 'start', 700)
        c.l(ej.X(t0), ej.Y(0), ej.X(t0), ej.Y(v0), AVISO, 1.4)
        c.t(ej.X(t0) - 4, ej.Y(v0 / 2) - 2, 'BEV', 8.5, AVISO, 'end', 700)
    panel(3, 'Inicio lento', None, (f'volumen retroextrapolado {v0:.2f} L', f'límite: 5 % de la FVC ({lim:.3f} L) o 0,100 L, el mayor'), ext_lento, tiempo=True)
    res.append(('inicio lento', t0, v0, lim, lento.fev(1.0)))
    # 4 esfuerzo variable
    def ext_var(ej):
        for e, col in ((1.0, AVISO), (0.75, COCLEAR), (0.5, IZQ)):
            def Fe(x, e=e):
                return min(m.F(x), e * m.pef * (1 - math.exp(-x / m.tau * 0.8)))
            pe, _ = lazo_pts(m, ej, F=Fe, insp=False)
            c.poli(pe, col, 2.2)
    panel(4, 'Esfuerzo variable', None, ('tres maniobras, tres PEF distintos', 'sin repetibilidad; el final coincide'), ext_var)
    # 5 maniobra aceptable
    def ext_ok(ej):
        pe, _ = lazo_pts(m, ej, insp=False)
        c.poli(pe, RETRO, 2.4)
    panel(5, 'Para comparar: maniobra aceptable', None, ('subida explosiva, pico en el primer tramo', 'descenso suave hasta flujo cero'), ext_ok)
    c.t(14, 508, 'Línea gris punteada: la maniobra normal del ejemplo. Fuga en la boca y boquilla obstruida no dejan una forma propia: se ven mirando al paciente.', 8, TENUE, 'start')
    c.guardar('h29-errores.svg')
    for r in res:
        print('ERROR inicio lento: t0 %.2f s, BEV %.3f L, límite %.3f L, FEV1 (desde t=0) %.2f' % r[1:])
    print('fin prematuro: flujo restante', round(m.F(xf), 2), 'L/s;', 'volumen espirado', round(m.fvc * xf, 2), 'L de', m.fvc)
    # FEV1/FVC con fin prematuro: FEV1 completo vs FVC truncada
    f1 = m.fev(1.0)
    print('fin prematuro: FEV1/FVC con FVC truncada', round(f1 / (m.fvc * xf), 2), 'vs normal', round(f1 / m.fvc, 2), '; FVC truncada', round(m.fvc * xf, 2))
    print('BEV normal:', [round(v, 3) for v in NORMAL.bev()[:2]])


if __name__ == '__main__':
    volumenes()
    esfuerzo()
    maniobra()
    patrones()
    via_aerea()
    errores()
