#!/usr/bin/env python3
"""Dibuja las ilustraciones del capítulo B4 (Física). SVG propios, no IA.
Todas las curvas se calculan aquí con las fórmulas del texto; las cifras que
el capítulo cita salen de `numeros()` (se imprimen y se comprueban con assert).

    b4-onda.svg              período, longitud de onda, amplitud, RMS y fase (suma de dos tonos)
    b4-estimulos.svg         tono puro, warble, click, burst y chirp: forma de onda y espectro
    b4-ruidos.svg            ruido blanco y rosa: en densidad y en bandas de 1/3 de octava
    b4-banda-critica.svg     banda crítica (Zwicker), ERB (Glasberg y Moore) y 1/3 de octava
    b4-filtros.svg           pasa altos + pasa bajos del PEAT y lo que cae dentro y fuera
    b4-decibel.svg           la escala de decibeles y cómo se suman dos fuentes
    b4-escalas.svg           el mismo tono en dB SPL, dB HL y dB SL
    b4-resonancia.svg        masa, rigidez y roce: la admitancia de tres oídos de juguete
    b4-promedio.svg          el ruido residual cae con la raíz del número de barridos
    b4-onda-estacionaria.svg tono puro, warble y ruido de banda estrecha frente a una pared
    b4-audifono.svg          entrada-salida (lineal y comprimido) y distorsión por recorte
    b4-nariz.svg             presión-flujo (laminar + turbulento) y resistencia contra radio
    b4-reflexion.svg         ecos en un tubo con un estrechamiento: signo, tamaño y lo que no se ve

Fuentes de los números:
- Velocidad del sonido: c = 331,3 + 0,606 T (T en °C), 343 m/s a 20 °C.
- Banda crítica: Zwicker (1961) y la fórmula analítica de Zwicker y Terhardt (1980):
  CB = 25 + 75 (1 + 1,4 f^2)^0,69 Hz, f en kHz. ERB: Glasberg y Moore (1990):
  ERB = 24,7 (4,37 f + 1) Hz, f en kHz.
- RETSPL del TDH-39: ISO 389-1, los mismos valores que usa H3 (45 / 25,5 / 7 dB SPL
  en 125 / 250 / 1000 Hz).
- Resistencias nasales: las de H24 (0,26 Pa/(cm3/s) a 75 Pa y 0,35 a 150 Pa en la
  fosa derecha del paciente simulado; 0,29 en la izquierda).
- Todo lo demás es aritmética o un modelo de juguete, y la figura lo dice.
"""
import math
import pathlib

import numpy as np

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO = '#c0571c', '#21796c', '#c62f3a'
AZUL, VERDE, VIOLETA = '#2c5cb0', '#2e8540', '#6a4fb3'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
K = 1.25
C_SON = 343.0


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400, estilo='', rot=None):
        e = f' font-style="{estilo}"' if estilo else ''
        r = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ''
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * K:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}"{e}{r}>{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, punta=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = f' marker-end="url(#p-{punta})"' if punta else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}{p}{extra}/>')

    def poli(self, pts, color, w=1.6, dash=None, fill='none', cerrar=False):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        tag = 'polygon' if cerrar else 'polyline'
        self.out.append(f'<{tag} points="{p}" fill="{fill}" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def rect(self, x, y, w, h, fill='#fff', stroke=TINTA, sw=1, r=3, op=None):
        o = f' fill-opacity="{op}"' if op is not None else ''
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
                        f'fill="{fill}"{o} stroke="{stroke}" stroke-width="{sw}"/>')

    def circ(self, x, y, r=3.5, fill='#fff', stroke=TINTA, sw=1.5):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def raw(self, s):
        self.out.append(s)

    def guardar(self, nombre):
        puntas = ''.join(
            f'<marker id="p-{n}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" markerUnits="userSpaceOnUse" '
            f'orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="{c}"/></marker>'
            for n, c in (('tinta', TINTA), ('tenue', TENUE), ('cocl', COCLEAR), ('retro', RETRO),
                         ('aviso', AVISO), ('azul', AZUL)))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><defs>{puntas}</defs><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print('  ', nombre)


class Ejes:
    """Un recuadro de gráfico con mapeo lineal o logarítmico."""

    def __init__(self, c, x0, y0, w, h, xr, yr, xlog=False, ylog=False):
        self.c, self.x0, self.y0, self.w, self.h = c, x0, y0, w, h
        self.xr, self.yr, self.xlog, self.ylog = xr, yr, xlog, ylog

    def X(self, v):
        a, b = self.xr
        if self.xlog:
            return self.x0 + (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a)) * self.w
        return self.x0 + (v - a) / (b - a) * self.w

    def Y(self, v):
        a, b = self.yr
        if self.ylog:
            return self.y0 + self.h - (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a)) * self.h
        return self.y0 + self.h - (v - a) / (b - a) * self.h

    def marco(self, xt=None, yt=None, xfmt=str, yfmt=str, grilla=True, xlab=None, ylab=None, size=8):
        c = self.c
        for v in (yt or []):
            if grilla:
                c.l(self.x0, self.Y(v), self.x0 + self.w, self.Y(v), GRILLA, 0.7)
            c.t(self.x0 - 6, self.Y(v) + 3, yfmt(v), size, TENUE, 'end')
        for v in (xt or []):
            if grilla:
                c.l(self.X(v), self.y0, self.X(v), self.y0 + self.h, GRILLA, 0.7)
            c.t(self.X(v), self.y0 + self.h + 13, xfmt(v), size, TENUE)
        c.l(self.x0, self.y0 + self.h, self.x0 + self.w, self.y0 + self.h, FUERTE, 1.2)
        c.l(self.x0, self.y0, self.x0, self.y0 + self.h, FUERTE, 1.2)
        if xlab:
            c.t(self.x0 + self.w / 2, self.y0 + self.h + 27, xlab, 8.5, TENUE)
        if ylab:
            c.t(self.x0 - 42, self.y0 + self.h / 2, ylab, 8.5, TENUE, rot=-90)

    def curva(self, xs, ys, color, w=1.8, dash=None):
        pts = [(self.X(x), self.Y(y)) for x, y in zip(xs, ys)]
        self.c.poli(pts, color, w, dash)


def num_es(x, d=1):
    """Número con coma decimal."""
    return f'{x:.{d}f}'.replace('.', ',')


def mil(x):
    return f'{x:,.0f}'.replace(',', '.')


def fhz(v):
    return f'{v / 1000:g} k'.replace('.', ',') if v >= 1000 else f'{v:g}'


# ---------------------------------------------------------------------------
# Los números del capítulo, calculados y comprobados una vez
def numeros():
    N = {}
    L = math.log10
    N['lambda'] = {f: C_SON / f for f in (125, 250, 500, 1000, 2000, 4000, 8000)}
    N['lambda_226'] = C_SON / 226
    N['canal_cuarto'] = C_SON / (4 * 0.025)
    assert abs(N['lambda'][1000] - 0.343) < 1e-9 and abs(N['lambda'][125] - 2.744) < 1e-3
    assert abs(N['canal_cuarto'] - 3430) < 1e-6
    # suma de dos tonos iguales con desfase
    N['suma_fase'] = {ph: 2 * math.cos(math.radians(ph) / 2) for ph in (0, 90, 120, 180)}
    assert abs(20 * L(N['suma_fase'][0]) - 6.02) < 0.01 and abs(20 * L(N['suma_fase'][90]) - 3.01) < 0.01
    assert abs(N['suma_fase'][120] - 1) < 1e-9 and abs(N['suma_fase'][180]) < 1e-12
    # presiones
    N['pres'] = {l: 20e-6 * 10 ** (l / 20) for l in range(0, 141, 20)}
    assert abs(N['pres'][120] - 20) < 1e-9 and abs(N['pres'][140] - 200) < 1e-6
    # suma de niveles
    N['suma'] = {'90+90': 10 * L(2 * 10 ** 9), '90+80': 10 * L(10 ** 9 + 10 ** 8), '90+60': 10 * L(10 ** 9 + 10 ** 6),
                 '3x80': 10 * L(3 * 10 ** 8), 'resta': 10 * L(10 ** 6.6 - 10 ** 6.0)}
    assert abs(N['suma']['90+90'] - 93.01) < 0.01 and abs(N['suma']['90+80'] - 90.41) < 0.01
    assert abs(N['suma']['3x80'] - 84.77) < 0.01 and abs(N['suma']['resta'] - 64.74) < 0.01
    # RETSPL TDH-39 y escalas
    N['tdh'] = {125: 45.0, 250: 25.5, 1000: 7.0}
    N['spl_de_hl'] = {(125, 40): 85.0, (1000, 40): 47.0}
    # filtro de la fuga
    N['fuga'] = -10 * L(10 ** -3 + 10 ** -2)
    assert abs(N['fuga'] - 19.59) < 0.01
    # aire contra líquido
    z1, z2 = 415.0, 1000 * 1480.0
    t = 4 * z1 * z2 / (z1 + z2) ** 2
    N['aire_liquido'] = (t, 10 * L(t), z2 / z1)
    assert abs(N['aire_liquido'][1] + 29.5) < 0.05
    # por qué 226 Hz
    rc2 = 1.4 * 1.01325e6   # dyn/cm2
    N['mmho_por_ml'] = {226: 2 * math.pi * 226 / rc2 * 1e3, 1000: 2 * math.pi * 1000 / rc2 * 1e3}
    assert abs(N['mmho_por_ml'][226] - 1.0) < 0.01 and abs(N['mmho_por_ml'][1000] - 4.43) < 0.01
    N['dapa'] = (1000 / 101325 * 100, 10 / 9.80665)
    # promediación
    N['prom'] = {n: 5 / math.sqrt(n) for n in (1, 100, 500, 1000, 2000, 4000, 8000)}
    N['snr'] = {n: 20 * L(0.5 / r) for n, r in N['prom'].items()}
    N['mejora_dB'] = {n: 10 * L(n) for n in N['prom']}
    N['t_barrido'] = (2000 / 21.1, 8000 / 21.1)
    # reproducibilidad <-> SNR
    N['repro'] = {r: 10 * L(r / (1 - r)) for r in (0.05, 0.70, 0.91)}
    assert abs(N['repro'][0.70] - 3.68) < 0.01 and abs(N['repro'][0.91] - 10.05) < 0.01
    # reflexión en pared
    N['ripple'] = {r: 20 * L((1 + r) / (1 - r)) for r in (0.5, 0.7, 0.8, 0.9)}
    # reflexión en tubo
    A1 = 1.5
    N['refl'] = {}
    for ra in (0.4, 0.1, 0.02):
        R = (1 - ra) / (1 + ra)
        N['refl'][ra] = (R, 1 - R * R, (1 - R * R) ** 2, 10 * L((1 - R * R) ** 2))
    R = (1.5 - 0.6) / (1.5 + 0.6)
    N['refl_ej'] = dict(R=R, R2=R * R, A=A1 * (1 - R) / (1 + R), t1=2 * 0.013 / C_SON * 1e6, t2=2 * 0.031 / C_SON * 1e6,
                        eco2=(2 * 1.5 / 2.1) * (-R) * (2 * 0.6 / 2.1))
    assert abs(N['refl_ej']['R'] - 0.4286) < 1e-3 and abs(N['refl_ej']['A'] - 0.6) < 1e-9
    # Leq y dosis
    N['leq'] = 10 * L(0.5 * 10 ** 8.8 + 0.5 * 10 ** 8.2)
    assert abs(N['leq'] - (85 + 10 * L(1.25))) < 0.01
    # nariz
    q1, q2 = 75 / 0.26, 150 / 0.35
    k2 = (0.35 - 0.26) / (q2 - q1)
    k1 = 0.26 - k2 * q1
    N['nariz'] = dict(q1=q1, q2=q2, k1=k1, k2=k2, lam75=k1 / 0.26, lam150=k1 / 0.35, par=0.35 * 0.29 / (0.35 + 0.29))
    assert abs(N['nariz']['par'] - 0.159) < 1e-3
    return N


NUM = numeros()


# ---------------------------------------------------------------------------
def onda():
    c = Lienzo(700, 330)
    # Panel A: un tono puro
    c.t(14, 20, 'A · Un tono puro en el tiempo', 10.5, TINTA, 'start', 700)
    x0, w, yc, A = 46, 290, 150, 62
    for g in (-1, 0, 1):
        c.l(x0, yc - g * A, x0 + w, yc - g * A, GRILLA, 0.8)
    c.l(x0, yc, x0 + w, yc, FUERTE, 1.2)
    n = 600
    pts = [(x0 + i / n * w, yc - A * math.sin(2 * math.pi * 2 * i / n)) for i in range(n + 1)]
    c.poli(pts, COCLEAR, 2.2)
    # período
    xa, xb = x0 + 0, x0 + w / 2
    yb = yc + A + 22
    c.l(xa, yb, xb, yb, TINTA, 1.2, punta='tinta')
    c.l(xb, yb, xa, yb, TINTA, 1.2, punta='tinta')
    c.t((xa + xb) / 2, yb + 15, 'período T = 1 / f', 9, TINTA, 'middle', 700)
    c.t((xa + xb) / 2, yb + 28, 'a 1.000 Hz, T = 1 ms', 8, TENUE)
    # amplitud pico
    xp = x0 + w / 8
    c.l(xp, yc, xp, yc - A + 2, AVISO, 1.4, punta='aviso')
    c.t(xp + 9, yc - A - 3, 'amplitud de pico', 8.5, AVISO, 'start', 700)
    # RMS
    rms = A / math.sqrt(2)
    c.l(x0, yc - rms, x0 + w, yc - rms, AZUL, 1.2, '5 3')
    c.t(x0 + w + 4, yc - rms + 3, 'RMS', 8.5, AZUL, 'start', 700)
    c.t(x0 + w + 4, yc - rms + 14, '0,707 × pico', 8, AZUL, 'start')
    c.t(x0 - 6, yc - A + 3, '+', 10, TENUE, 'end')
    c.t(x0 - 6, yc + A + 3, '−', 10, TENUE, 'end')
    c.t(x0 - 6, yc + 3, '0', 8.5, TENUE, 'end')
    c.t(x0 + w / 2, 44, 'presión sonora: sube y baja respecto de la presión del aire', 8, TENUE)
    c.t(x0 + w - 60, yc + 4 + 12, 'tiempo →', 8.5, TENUE)

    # Panel B: dos tonos iguales con distinto desfase
    bx, bw = 410, 270
    c.t(bx - 20, 20, 'B · Dos tonos iguales: lo que cambia la fase', 10.5, TINTA, 'start', 700)
    filas = [(0, 'en fase', 'suma ×2 = +6 dB'), (90, 'desfase de 90°', 'suma ×1,41 = +3 dB'),
             (180, 'en oposición (180°)', 'se cancelan: 0')]
    for k, (ph, tit, res) in enumerate(filas):
        y = 90 + k * 78
        amp = 15
        pa = [(bx + i / 300 * bw, y - amp * math.sin(2 * math.pi * 3 * i / 300)) for i in range(301)]
        pb = [(bx + i / 300 * bw, y - amp * math.sin(2 * math.pi * 3 * i / 300 + math.radians(ph))) for i in range(301)]
        ps = [(bx + i / 300 * bw, y - amp * (math.sin(2 * math.pi * 3 * i / 300) +
                                          math.sin(2 * math.pi * 3 * i / 300 + math.radians(ph)))) for i in range(301)]
        c.l(bx, y, bx + bw, y, GRILLA, 0.8)
        c.poli(pa, TENUE, 1.0)
        c.poli(pb, AZUL, 1.0, '4 2')
        c.poli(ps, COCLEAR, 2.0)
        c.t(bx, y - 36, tit, 8.5, TINTA, 'start', 700)
        c.t(bx + bw, y - 36, res, 8.5, COCLEAR, 'end', 700)
    c.t(bx, 300, 'gris y azul: los dos tonos · naranja: la suma', 8, TENUE, 'start')
    c.t(14, 322, 'La fase es el punto del ciclo en que está la onda; un click o un ruido se suman de otra manera.', 8, TENUE, 'start')
    c.guardar('b4-onda.svg')


# ---------------------------------------------------------------------------
FS = 192000


def _espectro(x, fmin=100, fmax=16000, n=2 ** 19, norm=None):
    X = np.abs(np.fft.rfft(x, n))
    f = np.fft.rfftfreq(n, 1 / FS)
    m = (f >= fmin) & (f <= fmax)
    f, X = f[m], X[m]
    ref = X.max() if norm is None else norm
    return f, 20 * np.log10(np.maximum(X / ref, 1e-6))


def senales():
    s = {}
    t = np.arange(int(0.2 * FS)) / FS
    rampa = np.minimum(1, np.minimum(t, t[-1] - t) / 0.01)
    s['tono'] = np.sin(2 * np.pi * 1000 * t) * (0.5 - 0.5 * np.cos(np.pi * np.minimum(1, rampa)))
    # warble: 1 kHz +-5 %, 5 Hz
    tw = np.arange(int(1.0 * FS)) / FS
    fi = 1000 * (1 + 0.05 * np.sin(2 * np.pi * 5 * tw))
    ph = 2 * np.pi * np.cumsum(fi) / FS
    s['warble'] = (tw, fi, np.sin(ph))
    # click de 100 us
    tc = np.arange(int(0.05 * FS)) / FS
    s['click'] = (tc, (tc < 100e-6).astype(float))
    # burst 2-1-2
    def burst(f0):
        ciclos = 5
        d = ciclos / f0
        tb = np.arange(int(max(d * 3, 0.012) * FS)) / FS
        env = np.zeros_like(tb)
        up = 2 / f0
        pl = 1 / f0
        m = tb < up
        env[m] = 0.5 - 0.5 * np.cos(np.pi * tb[m] / up)
        m = (tb >= up) & (tb < up + pl)
        env[m] = 1
        m = (tb >= up + pl) & (tb < d)
        env[m] = 0.5 + 0.5 * np.cos(np.pi * (tb[m] - up - pl) / up)
        return tb, env * np.sin(2 * np.pi * f0 * tb), d
    s['b500'], s['b1000'], s['b4000'] = burst(500), burst(1000), burst(4000)
    # chirp: frecuencia que crece con el tiempo; retardo coclear ~ 3 ms (1000/f)^0.5 (ilustrativo)
    T0 = 3e-3 * math.sqrt(10)          # f = 100 Hz sale en t = 0
    tt = np.arange(int(0.012 * FS)) / FS
    tmax = T0 - 3e-3 * math.sqrt(1000 / 8000)
    sel = tt < tmax
    td = tt[sel]
    f_t = 1000 * (3e-3 / (T0 - td)) ** 2
    fase = 2 * np.pi * 1000 * 9e-6 * (1 / (T0 - td) - 1 / T0)
    amp = np.sqrt(np.gradient(f_t, td))
    amp = amp / amp.max()
    s['chirp'] = (td, amp * np.sin(fase), f_t)
    return s


def estimulos():
    S = senales()
    c = Lienzo(700, 660)
    c.t(14, 20, 'Forma de onda (izquierda) y espectro (derecha) de cada estímulo', 10.5, TINTA, 'start', 700)
    filas = ['Tono puro, 1 kHz', 'Tono modulado (warble), 1 kHz ± 5 %', 'Click de 100 µs',
             'Tone burst 2-1-2, 500, 1.000 y 4.000 Hz', 'Chirp']
    alto, y00 = 112, 34
    xl, wl = 46, 262
    xr, wr = 392, 270
    for k, tit in enumerate(filas):
        y = y00 + k * alto
        c.t(14, y + 10, tit, 9, TINTA, 'start', 700)
        # waveform
        yc = y + 58
        A = 30
        c.l(xl, yc, xl + wl, yc, GRILLA, 0.8)
        if k == 0:
            tms = 8
            n = int(tms / 1000 * FS)
            tt = np.arange(n) / FS * 1000
            sig = np.sin(2 * np.pi * 1000 * tt / 1000)
            pts = [(xl + a / tms * wl, yc - A * b) for a, b in zip(tt[::8], sig[::8])]
            c.poli(pts, COCLEAR, 1.5)
            c.t(xl + wl, yc + 44, '8 ms', 8, TENUE, 'end')
            c.t(xl + 2, yc + 44, '8 ciclos de 1 ms', 8, TENUE, 'start')
        elif k == 1:
            tw, fi, _ = S['warble']
            m = tw <= 0.4
            f_ax = Ejes(c, xl, yc - 38, wl, 76, (0, 400), (900, 1100))
            f_ax.curva(tw[m][::40] * 1000, fi[m][::40], COCLEAR, 1.8)
            c.t(xl - 5, yc - 34 + 3, '1.050', 7.5, TENUE, 'end')
            c.t(xl - 5, yc + 36, '950', 7.5, TENUE, 'end')
            c.t(xl - 5, yc + 3, '1.000 Hz', 7.5, TENUE, 'end')
            c.t(xl + wl, yc + 52, 'frecuencia instantánea · 0,4 s (2 ciclos de modulación a 5 Hz)', 8, TENUE, 'end')
            pass
        elif k == 2:
            tc, cl = S['click']
            tms = 0.5
            n = int(tms / 1000 * FS)
            pts = [(xl, yc), (xl + 2, yc), (xl + 2, yc - A), (xl + 2 + 100e-6 * 1000 / tms * wl, yc - A),
                   (xl + 2 + 100e-6 * 1000 / tms * wl, yc), (xl + wl, yc)]
            c.poli(pts, COCLEAR, 1.8)
            c.t(xl + 2 + 100e-6 * 1000 / tms * wl + 6, yc - A + 6, '100 µs', 8, COCLEAR, 'start', 700)
            c.t(xl + wl, yc + 44, '0,5 ms', 8, TENUE, 'end')
        elif k == 3:
            tms = 12
            for nombre, color, f0 in (('b500', AZUL, 500), ('b1000', COCLEAR, 1000), ('b4000', VERDE, 4000)):
                tb, sg, d = S[nombre]
                pts = [(xl + a * 1000 / tms * wl, yc - A * b) for a, b in zip(tb[::6], sg[::6]) if a * 1000 <= tms]
                c.poli(pts, color, 1.3)
            c.t(xl + 2, yc + 44, '5 ciclos:', 8, TENUE, 'start')
            c.t(xl + 50, yc + 44, '4.000 Hz = 1,25 ms', 8, VERDE, 'start', 700)
            c.t(xl + 150, yc + 44, '1.000 Hz = 5 ms', 8, COCLEAR, 'start', 700)
            c.t(xl + 236, yc + 44, '500 Hz = 10 ms', 8, AZUL, 'start', 700)
            c.t(xl + wl, yc - 42, 'eje de 12 ms', 8, TENUE, 'end')
        else:
            td, ch, f_t = S['chirp']
            tms = 12
            pts = [(xl + a * 1000 / tms * wl, yc - A * b) for a, b in zip(td[::3], ch[::3])]
            c.poli(pts, COCLEAR, 1.0)
            c.t(xl + wl, yc + 44, '12 ms: primero graves, al final agudos', 8, TENUE, 'end')
        # spectrum
        yb, hh = y + 22, 76
        ax = Ejes(c, xr, yb, wr, hh, (100, 16000), (-50, 0), xlog=True)
        ax.marco(xt=[125, 250, 500, 1000, 2000, 4000, 8000, 16000], yt=[-40, -20, 0],
                 xfmt=lambda v: fhz(v), yfmt=lambda v: str(v), size=7.5)
        if k == 0:
            f, X = _espectro(S['tono'])
            ax.curva(f[::20], np.maximum(X[::20], -50), COCLEAR, 1.5)
            c.t(xr + wr, yb + hh + 24, 'frecuencia (Hz) · dB respecto del máximo', 7.5, TENUE, 'end')
        elif k == 1:
            _, _, sg = S['warble']
            f, X = _espectro(sg)
            ax.curva(f[::60], np.maximum(X[::60], -50), COCLEAR, 1.2)
            c.t(ax.X(1300), ax.Y(-12), '950 a 1.050 Hz', 7.5, TENUE, 'start')
        elif k == 2:
            _, cl = S['click']
            f, X = _espectro(cl)
            ax.curva(f[::200], np.maximum(X[::200], -50), COCLEAR, 1.5)
            c.t(ax.X(9000), ax.Y(-34), 'primer nulo: 10 kHz', 7.5, TENUE, 'end')
        elif k == 3:
            for nombre, color in (('b500', AZUL), ('b1000', COCLEAR), ('b4000', VERDE)):
                tb, sg, d = S[nombre]
                f, X = _espectro(sg, n=2 ** 18)
                ax.curva(f[::20], np.maximum(X[::20], -50), color, 1.3)
        else:
            td, ch, _ = S['chirp']
            f, X = _espectro(ch, n=2 ** 18)
            ax.curva(f[::20], np.maximum(X[::20], -50), COCLEAR, 1.2)
    c.t(14, 640, 'El click, el burst y el chirp son ideales: el transductor y el equipo los modifican.', 7.5, TENUE, 'start')
    c.t(14, 653, 'Cada equipo usa su propio chirp; el eje de frecuencias de los espectros es logarítmico.', 7.5, TENUE, 'start')
    c.guardar('b4-estimulos.svg')


# ---------------------------------------------------------------------------
def ruidos():
    c = Lienzo(700, 310)
    fs = np.geomspace(100, 10000, 80)
    blanco_d = np.zeros_like(fs)
    rosa_d = -10 * np.log10(fs / 1000)
    ancho = fs * (2 ** (1 / 6) - 2 ** (-1 / 6))
    blanco_b = 10 * np.log10(ancho / ancho[np.argmin(abs(fs - 1000))])
    rosa_b = rosa_d + 10 * np.log10(ancho / ancho[np.argmin(abs(fs - 1000))])
    assert abs((blanco_b[-1] - blanco_b[0]) / math.log2(fs[-1] / fs[0]) - 3.01) < 0.02
    assert np.allclose(rosa_b, rosa_b[0], atol=1e-6)
    for pan, (x0, tit, yb, yr, ylab) in enumerate([
            (60, 'A · Por hercio (densidad espectral)', 'densidad', (-15, 10), 'nivel por Hz (dB, relativo)'),
            (400, 'B · Por banda de 1/3 de octava', 'banda', (-15, 10), 'nivel por banda (dB, relativo)')]):
        c.t(x0 - 20, 20, tit, 10.5, TINTA, 'start', 700)
        ax = Ejes(c, x0, 40, 270, 200, (100, 10000), yr, xlog=True)
        ax.marco(xt=[125, 250, 500, 1000, 2000, 4000, 8000], yt=[-10, -5, 0, 5, 10],
                 xfmt=fhz, yfmt=lambda v: f'{v:+d}'.replace('+0', '0'), xlab='frecuencia (Hz)', ylab=ylab)
        if pan == 0:
            ax.curva(fs, blanco_d, TINTA, 2.4)
            ax.curva(fs, rosa_d, COCLEAR, 2.4)
            c.t(ax.X(150), ax.Y(0) - 7, 'blanco: plano', 8.5, TINTA, 'start', 700)
            c.t(ax.X(10000), ax.Y(5.5), 'rosa: baja 3 dB por octava', 8.5, COCLEAR, 'end', 700)
        else:
            ax.curva(fs, blanco_b, TINTA, 2.4)
            ax.curva(fs, rosa_b, COCLEAR, 2.4)
            c.t(ax.X(10000), ax.Y(-6.5), 'blanco: sube 3 dB por octava', 8.5, TINTA, 'end', 700)
            c.t(ax.X(130), ax.Y(0) - 8, 'rosa: plano', 8.5, COCLEAR, 'start', 700)
    c.t(14, 286, 'Curvas calculadas. Ancho de una banda de 1/3 de octava = f × (2^(1/6) − 2^(−1/6)) = 0,23 f.', 8, TENUE, 'start')
    c.t(14, 299, 'Referencia: el nivel en 1.000 Hz. Un ruido de habla y uno de banda estrecha son otras formas (ver el texto).', 8, TENUE, 'start')
    c.guardar('b4-ruidos.svg')


# ---------------------------------------------------------------------------
def cb_zwicker(f):
    k = f / 1000
    return 25 + 75 * (1 + 1.4 * k ** 2) ** 0.69


def erb(f):
    return 24.7 * (4.37 * f / 1000 + 1)


def banda_critica():
    c = Lienzo(700, 340)
    c.t(14, 20, 'Ancho de una banda crítica según la frecuencia', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, 66, 40, 440, 240, (100, 10000), (10, 3000), xlog=True, ylog=True)
    ax.marco(xt=[125, 250, 500, 1000, 2000, 4000, 8000], yt=[10, 30, 100, 300, 1000, 3000],
             xfmt=fhz, yfmt=lambda v: mil(v), xlab='frecuencia central (Hz)', ylab='ancho de banda (Hz)')
    fs = np.geomspace(100, 10000, 90)
    ax.curva(fs, [cb_zwicker(f) for f in fs], COCLEAR, 2.6)
    ax.curva(fs, [erb(f) for f in fs], AZUL, 2.0)
    ax.curva(fs, [f * (2 ** (1 / 6) - 2 ** (-1 / 6)) for f in fs], TINTA, 1.6, '6 3')
    ax.curva(fs, [f * (2 ** 0.5 - 2 ** -0.5) for f in fs], TENUE, 1.2, '2 3')
    # el cruce 1/3 oct = banda crítica
    cruces = [f for f in fs if abs(cb_zwicker(f) - 0.2316 * f) / cb_zwicker(f) < 0.03]
    assert cruces and 400 < cruces[0] < 700, cruces
    c.circ(ax.X(500), ax.Y(cb_zwicker(500)), 4, '#fff', AVISO, 1.8)
    c.t(ax.X(500) + 8, ax.Y(cb_zwicker(500)) + 30, 'cerca de 500 Hz', 8.5, AVISO, 'start', 700)
    c.t(ax.X(500) + 8, ax.Y(cb_zwicker(500)) + 42, 'coinciden', 8.5, AVISO, 'start', 700)
    lx = 530
    for k, (txt, col, dash) in enumerate([('banda crítica (Zwicker)', COCLEAR, None), ('ERB (Glasberg y Moore)', AZUL, None),
                                          ('1/3 de octava', TINTA, '6 3'), ('1 octava', TENUE, '2 3')]):
        yy = 80 + k * 22
        c.l(lx, yy, lx + 26, yy, col, 2.2, dash)
        c.t(lx + 32, yy + 3, txt, 8.5, TINTA, 'start')
    c.t(lx, 190, 'En 1.000 Hz:', 8.5, TINTA, 'start', 700)
    c.t(lx, 203, f'banda crítica ≈ {cb_zwicker(1000):.0f} Hz'.replace('.', ','), 8.5, TENUE, 'start')
    c.t(lx, 216, f'ERB ≈ {erb(1000):.0f} Hz'.replace('.', ','), 8.5, TENUE, 'start')
    c.t(lx, 229, f'1/3 de octava ≈ {0.2316 * 1000:.0f} Hz'.replace('.', ','), 8.5, TENUE, 'start')
    c.t(14, 326, 'Curvas calculadas con las fórmulas de Zwicker y Terhardt (1980) y de Glasberg y Moore (1990); son promedios de oyentes jóvenes.', 8, TENUE, 'start')
    c.guardar('b4-banda-critica.svg')


# ---------------------------------------------------------------------------
def butter_hp(f, fc, n):
    return 1 / np.sqrt(1 + (fc / f) ** (2 * n))


def butter_lp(f, fc, n):
    return 1 / np.sqrt(1 + (f / fc) ** (2 * n))


def filtros():
    c = Lienzo(700, 370)
    c.t(14, 20, 'El filtro del PEAT: pasa altos de 100 Hz y pasa bajos de 3.000 Hz', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, 56, 48, 600, 220, (10, 10000), (-60, 6), xlog=True)
    # bandas de lo que hay en el electrodo (órdenes de magnitud)
    bandas = [(1, 30, AZUL, 'EEG de fondo'), (20, 400, TENUE, 'músculo (EMG), sube hacia los agudos'),
              (100, 3000, COCLEAR, 'energía del PEAT')]
    ax.marco(xt=[10, 30, 100, 300, 1000, 3000, 10000], yt=[-60, -40, -20, 0],
             xfmt=lambda v: mil(v), yfmt=lambda v: str(v), xlab='frecuencia (Hz)', ylab='ganancia del filtro (dB)')
    fs = np.geomspace(10, 10000, 400)
    for n, col, dash, w in ((1, TENUE, '5 3', 1.4), (2, COCLEAR, None, 2.6)):
        g = 20 * np.log10(butter_hp(fs, 100, n) * butter_lp(fs, 3000, n))
        ax.curva(fs, g, col, w, dash)
    # marcas de red y corte
    c.l(ax.X(50), ax.Y(6), ax.X(50), ax.Y(-60), AVISO, 1.0, '3 3')
    c.t(ax.X(50), ax.Y(6) - 4, 'red 50 Hz', 8, AVISO, 'middle', 700)
    for fc in (100, 3000):
        c.circ(ax.X(fc), ax.Y(-3.01), 3.5, '#fff', AVISO, 1.6)
    c.t(ax.X(100) - 6, ax.Y(-3) - 8, '−3 dB', 8, AVISO, 'end', 700)
    c.t(ax.X(3000) + 6, ax.Y(-3) - 8, '−3 dB', 8, AVISO, 'start', 700)
    # bandas
    for k, (a, b, col, txt) in enumerate(bandas):
        yy = ax.y0 + ax.h + 42 + k * 0
    yb = 320
    for k, (a, b, col, txt) in enumerate(bandas):
        yy = yb + k * 11
        c.rect(ax.X(max(a, 10)), yy - 6, ax.X(b) - ax.X(max(a, 10)), 7, col, col, 0, 1, op=0.55)
        c.t(ax.X(b) + 6, yy + 1, txt, 7.5, TINTA, 'start')
    # leyenda
    c.l(330, 190, 356, 190, TENUE, 1.6, '5 3')
    c.t(362, 193, 'filtros de 1.er orden (6 dB por octava)', 8, TINTA, 'start')
    c.l(330, 206, 356, 206, COCLEAR, 2.8)
    c.t(362, 209, 'filtros de 2.º orden (12 dB por octava)', 8, TINTA, 'start')
    g50 = 20 * math.log10(butter_hp(50, 100, 2))
    c.t(14, 362, f'La red de 50 Hz queda {num_es(abs(g50), 1)} dB abajo con el pasa altos de 2.º orden.', 8, TENUE, 'start')
    NUM['g50_hp2'] = g50
    c.guardar('b4-filtros.svg')


# ---------------------------------------------------------------------------
def decibel():
    c = Lienzo(700, 420)
    c.t(14, 20, 'A · La escala de decibeles (dB SPL)', 10.5, TINTA, 'start', 700)
    x, y0, h = 150, 40, 320
    Y = lambda db: y0 + h - db / 140 * h
    c.l(x, y0, x, y0 + h, FUERTE, 2)
    for db in range(0, 141, 20):
        c.l(x - 5, Y(db), x + 5, Y(db), TINTA, 1.2)
        c.t(x - 10, Y(db) + 3, f'{db}', 8.5, TINTA, 'end', 700)
        p = NUM['pres'][db]
        txt = (f'{p * 1e6:g} µPa' if p < 1e-3 else f'{p * 1e3:g} mPa' if p < 1 else f'{p:g} Pa').replace('.', ',')
        c.t(x + 12, Y(db) + 3, txt, 8.5, TENUE, 'start')
    c.t(x - 10, y0 - 8, 'dB SPL', 8.5, TINTA, 'end', 700)
    c.t(x + 12, y0 - 8, 'presión', 8.5, TENUE, 'start')
    ej = [(0, 'umbral a 1 kHz (0 a 7 dB SPL)'), (30, 'sala muy silenciosa'),
          (60, 'conversación a 1 m'), (85, 'límite de 8 horas (→ H22)'), (120, 'dolor')]
    for db, txt in ej:
        c.circ(x, Y(db), 3.5, COCLEAR, COCLEAR, 1)
        c.t(x + 78, Y(db) + 3, txt, 8, TINTA, 'start')
    # reglas
    c.rect(380, 290, 300, 110, '#fbf3e6', COCLEAR, 1, 5)
    c.t(392, 308, 'Cada paso de la regla', 9, COCLEAR, 'start', 700)
    reglas = ['+ 6 dB  →  presión ×2 (energía ×4)', '+ 3 dB  →  energía ×2 (presión ×1,41)',
              '+ 10 dB  →  energía ×10 (sonoridad ≈ ×2)', '+ 20 dB  →  presión ×10 (energía ×100)']
    for k, r in enumerate(reglas):
        c.t(392, 326 + k * 17, r, 8.5, TINTA, 'start')

    # B: suma de dos fuentes
    bx = 450
    c.t(bx - 60, 20, 'B · Cuánto sube el nivel al sumar dos fuentes', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, bx, 50, 200, 190, (0, 20), (0, 3.5))
    ax.marco(xt=[0, 5, 10, 15, 20], yt=[0, 1, 2, 3], xfmt=str, yfmt=str,
             xlab='diferencia entre las dos fuentes (dB)', ylab='sube sobre la más fuerte (dB)')
    ds = np.linspace(0, 20, 100)
    inc = 10 * np.log10(1 + 10 ** (-ds / 10))
    ax.curva(ds, inc, COCLEAR, 2.4)
    for d in (0, 10, 20):
        v = 10 * math.log10(1 + 10 ** (-d / 10))
        c.circ(ax.X(d), ax.Y(v), 3.5, '#fff', COCLEAR, 1.6)
        c.t(ax.X(d) + 8, ax.Y(v) - 6, f'+{num_es(v, 2)}', 8, COCLEAR, 'start', 700)
    c.t(14, 410, 'dB = 20 log(p / 20 µPa) = 10 log(I / I0).', 8, TENUE, 'start')
    c.guardar('b4-decibel.svg')


# ---------------------------------------------------------------------------
def escalas():
    c = Lienzo(700, 380)
    c.t(14, 20, 'El mismo tono, en tres escalas (fono TDH-39)', 10.5, TINTA, 'start', 700)
    casos = [(1000, 60, 40, 'Tono de 1.000 Hz'), (125, 60, 10, 'Tono de 125 Hz')]
    top, bot = -5, 90
    y0, h = 98, 230
    Y = lambda spl_v: y0 + (bot - spl_v) / (bot - top) * h
    NUM['escalas'] = {}
    for k, (f, spl, umbral_hl, tit) in enumerate(casos):
        x0 = 20 + k * 345
        ret = NUM['tdh'][f]
        hl = spl - ret
        sl = hl - umbral_hl
        NUM['escalas'][f] = (spl, hl, sl)
        c.t(x0, 46, f'{tit}, a {spl} dB SPL', 9.5, TINTA, 'start', 700)
        c.t(x0, 60, f'umbral del paciente: {umbral_hl} dB HL', 8, TENUE, 'start')
        escala = [('dB SPL', 0, lambda v: v), ('dB HL', 1, lambda v: v - ret), ('dB SL', 2, lambda v: v - ret - umbral_hl)]
        for nombre, j, fn in escala:
            xx = x0 + 40 + j * 90
            c.t(xx, y0 - 12, nombre, 9, TINTA, 'middle', 700)
            c.l(xx, y0, xx, y0 + h, FUERTE, 2)
            for sv in range(0, 91, 10):
                if abs(sv - spl) < 6:
                    continue
                c.l(xx - 4, Y(sv), xx + 4, Y(sv), TENUE, 1)
                c.t(xx - 8, Y(sv) + 3, f'{fn(sv):g}'.replace('-', '−'), 7.5, TENUE, 'end')
            c.circ(xx, Y(spl), 4.5, COCLEAR, COCLEAR, 1)
            val = fn(spl)
            c.t(xx + 9, Y(spl) - 6, f'{val:g}'.replace('-', '−'), 9, COCLEAR, 'start', 700)
        c.l(x0 + 40, Y(spl), x0 + 220, Y(spl), COCLEAR, 1.2, '4 3')
        # el cero de HL (en dB SPL) y el umbral del paciente
        xh = x0 + 130
        c.l(xh - 12, Y(ret), xh + 12, Y(ret), AVISO, 2.4)
        c.l(xh + 12, Y(ret), x0 + 238, Y(ret), AVISO, 1, '2 3')
        c.t(x0 + 244, Y(ret) + 3, f'0 dB HL = {num_es(ret, 1) if ret % 1 else int(ret)} SPL'.replace('.', ','), 8, AVISO, 'start', 700)
        xs_ = x0 + 220
        c.l(xs_ - 12, Y(ret + umbral_hl), xs_ + 12, Y(ret + umbral_hl), AZUL, 2.4)
        c.t(xs_ + 18, Y(ret + umbral_hl) + 3, 'umbral', 8, AZUL, 'start', 700)
    c.t(14, 352, 'Mismo sonido, tres números.', 8, TENUE, 'start')
    c.t(14, 365, 'RETSPL del TDH-39 (ISO 389-1, 2017): 45 dB SPL en 125 Hz y 7 dB SPL en 1.000 Hz, los mismos valores que usa H3.', 8, TENUE, 'start')
    c.guardar('b4-escalas.svg')


# ---------------------------------------------------------------------------
def Y_modelo(f, M, C, R):
    w = 2 * np.pi * f
    Z = R + 1j * (w * M - 1 / (w * C))
    return 1 / np.abs(Z)


def resonancia():
    c = Lienzo(700, 366)
    c.t(14, 20, 'A · Tres elementos', 10.5, TINTA, 'start', 700)
    # resorte, masa, amortiguador (esquema)
    x = 26
    c.rect(x, 52, 14, 120, FUERTE, TENUE, 1, 2)
    # resorte
    pts = [(x + 14, 78)]
    for i in range(7):
        pts += [(x + 34 + (i % 2) * 0, 78 + i * 0)]
    zz = [(x + 14, 78), (x + 30, 78)]
    for i in range(6):
        zz.append((x + 36 + i * 8, 78 + (-10 if i % 2 == 0 else 10)))
    zz += [(x + 90, 78), (x + 104, 78)]
    c.poli(zz, VERDE, 2)
    c.t(x + 58, 66, 'rigidez', 8.5, VERDE, 'middle', 700)
    # amortiguador
    c.l(x + 14, 112, x + 40, 112, AZUL, 2)
    c.rect(x + 40, 100, 34, 24, '#fff', AZUL, 2, 1)
    c.l(x + 50, 106, x + 50, 118, AZUL, 2)
    c.l(x + 74, 112, x + 104, 112, AZUL, 2)
    c.t(x + 58, 98 - 2, 'roce', 8.5, AZUL, 'middle', 700)
    # masa
    c.rect(x + 104, 56, 46, 116, COCLEAR, COCLEAR, 1, 3, op=0.25)
    c.t(x + 127, 118, 'masa', 8.5, COCLEAR, 'middle', 700)
    c.l(x + 14, 142, x + 104, 142, GRILLA, 0.1)
    c.t(x + 70, 196, 'el sonido empuja', 8.5, TENUE, 'middle')
    c.l(x + 70, 206, x + 70, 206, TINTA, 1)
    c.l(x + 20, 188, x + 20, 188, TINTA, 1)
    c.l(x + 38, 208, x + 98, 208, TINTA, 1.4, punta='tinta')
    cuadro = [('Rigidez (compliancia)', VERDE, 'se opone más a lo lento: más con los graves'),
              ('Masa', COCLEAR, 'se opone más a lo rápido: más con los agudos'),
              ('Roce', AZUL, 'no depende de la frecuencia: gasta energía')]
    for k, (a, col, b) in enumerate(cuadro):
        c.t(14, 232 + k * 32, a, 8.5, col, 'start', 700)
        c.t(14, 245 + k * 32, b, 8, TENUE, 'start')
    # B: admitancia
    c.t(250, 20, 'B · Admitancia según la frecuencia (modelo de juguete)', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, 290, 44, 380, 250, (100, 4000), (0.0, 5.0), xlog=True)
    ax.marco(xt=[125, 250, 500, 1000, 2000, 4000], yt=[0, 1, 2, 3, 4], xfmt=fhz, yfmt=str,
             xlab='frecuencia de la sonda (Hz)', ylab='admitancia (relativa)')
    f0 = 1000.0
    w0 = 2 * math.pi * f0
    C0 = 1.0
    M0 = 1 / (w0 ** 2 * C0)
    R0 = w0 * M0 / 1.0
    ref = Y_modelo(226.0, M0, C0, R0)
    fs = np.geomspace(100, 4000, 300)
    mods = [('oído normal', C0, M0, TINTA, None, 2.6), ('más rígido (otosclerosis)', 0.4 * C0, M0, AVISO, None, 2.0),
            ('más laxo (disyunción)', 2.5 * C0, M0, AZUL, None, 2.0)]
    res = {}
    for nom, C_, M_, col, dash, w in mods:
        yy = Y_modelo(fs, M_, C_, R0) / ref
        ax.curva(fs, yy, col, w, dash)
        res[nom] = (1 / (2 * math.pi * math.sqrt(M_ * C_)), Y_modelo(226.0, M_, C_, R0) / ref, Y_modelo(1000.0, M_, C_, R0) / ref)
    NUM['reson'] = res
    assert abs(res['oído normal'][0] - 1000) < 0.1
    for fx, nom in ((226, '226 Hz'), (1000, '1.000 Hz')):
        c.l(ax.X(fx), ax.y0, ax.X(fx), ax.y0 + ax.h, COCLEAR, 1.2, '4 3')
        c.t(ax.X(fx), ax.y0 - 4, nom, 8, COCLEAR, 'middle', 700)
    for k, (nom, C_, M_, col, dash, w) in enumerate(mods):
        yy = 62 + k * 14
        corto = ('normal', 'rígido', 'laxo')[k]
        c.l(300, yy, 322, yy, col, w)
        c.t(328, yy + 3, f'{corto} (f₀ {res[nom][0]:.0f} Hz)'.replace('.', ','), 8, TINTA, 'start')
    c.t(14, 340, 'Modelo de masa, resorte y roce en serie: la masa y el roce son los mismos en los tres; solo cambia la rigidez.', 8, TENUE, 'start')
    c.t(14, 353, 'Admitancia en unidades relativas (el oído normal vale 1 en 226 Hz).', 8, TENUE, 'start')
    c.guardar('b4-resonancia.svg')


# ---------------------------------------------------------------------------
def promedio():
    rng = np.random.default_rng(20261017)
    fs = 20000
    t = np.arange(int(0.012 * fs)) / fs * 1000   # ms

    def bump(c0, w, a):
        return a * np.exp(-((t - c0) / w) ** 2)
    señal = bump(1.6, 0.22, 0.20) - bump(2.3, 0.3, 0.10) + bump(3.7, 0.25, 0.30) - bump(4.4, 0.3, 0.12) + bump(5.6, 0.3, 0.50) - bump(6.6, 0.55, 0.45)
    ruido_rms = 5.0

    def un_barrido():
        r = rng.normal(0, 1, len(t) + 8)
        r = np.convolve(r, np.ones(5) / 5, 'valid')[:len(t)]
        return r / 0.4472 * ruido_rms * 0.0 + r * ruido_rms / np.std(r) if False else r
    # un ruido "tipo EEG": filtrado por media móvil y escalado a 5 µV RMS por barrido
    base = np.array([np.convolve(rng.normal(0, 1, len(t) + 4), np.ones(5) / 5, 'valid')[:len(t)] for _ in range(8000)])
    base = base / base.std() * ruido_rms
    c = Lienzo(700, 520)
    c.t(14, 20, 'A · Lo que se ve al promediar', 10.5, TINTA, 'start', 700)
    Ns = [1, 100, 500, 2000, 8000]
    x0, w = 56, 330
    medidos = {}
    for k, n in enumerate(Ns):
        y = 100 + k * 80
        prom = señal + base[:n].mean(axis=0)
        medidos[n] = float(np.std(prom - señal))
        esc = {1: 4.0, 100: 30.0, 500: 60.0, 2000: 80.0, 8000: 80.0}[n]   # px por µV (se agranda a medida que baja el ruido)
        c.l(x0, y, x0 + w, y, GRILLA, 0.8)
        pts = [(x0 + i / len(t) * w, y - v * esc) for i, v in enumerate(prom)]
        c.poli(pts, COCLEAR, 1.2)
        pts2 = [(x0 + i / len(t) * w, y - v * esc) for i, v in enumerate(señal)]
        c.poli(pts2, TINTA, 1.0, '4 3')
        c.t(14, y + 3, f'N = {mil(n)}', 8.5, TINTA, 'start', 700)
        c.l(x0 + w + 12, y - esc / 2, x0 + w + 12, y + esc / 2, TENUE, 1.4)
        c.t(x0 + w + 18, y + 3, '1 µV', 8, TENUE, 'start')
    c.t(x0 + w / 2, 100 + 5 * 80 - 22, 'tiempo después del estímulo (0-12 ms)', 8, TENUE)
    c.t(x0, 44, 'punteada: la señal verdadera (0,5 µV en la onda V) · cada fila tiene su escala', 8, TINTA, 'start')
    NUM['prom_medido'] = medidos
    for n in Ns:   # el ruido residual simulado sigue a 5/sqrt(N)
        esperado = 5 / math.sqrt(n)
        assert abs(medidos[n] - esperado) / esperado < 0.2, (n, medidos[n], esperado)
    # B: ruido residual vs N
    c.t(436, 20, 'B · El ruido residual cae con √N', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, 480, 64, 190, 220, (1, 10000), (0.03, 10), xlog=True, ylog=True)
    ax.marco(xt=[1, 10, 100, 1000, 10000], yt=[0.1, 0.5, 1, 5], xfmt=mil, yfmt=lambda v: num_es(v, 1) if v < 1 else f'{v:g}',
             xlab='barridos promediados (N)', ylab='ruido residual (µV RMS)')
    ns = np.geomspace(1, 10000, 60)
    ax.curva(ns, 5 / np.sqrt(ns), COCLEAR, 2.2)
    for n in Ns:
        c.circ(ax.X(n), ax.Y(medidos[n]), 3.6, '#fff', TINTA, 1.5)
    c.l(ax.x0, ax.Y(0.5), ax.x0 + ax.w, ax.Y(0.5), AZUL, 1.2, '5 3')
    c.t(ax.x0 + 4, ax.Y(0.5) - 5, 'onda V: 0,5 µV', 8, AZUL, 'start', 700)
    c.t(436, 50, 'se divide por 2 cada vez que N se multiplica por 4', 8, COCLEAR, 'start', 700)
    c.t(436, 322, 'círculos: ruido residual medido', 8, TENUE, 'start')
    c.t(436, 335, 'línea: 5 / √N', 8, TENUE, 'start')
    c.t(436, 360, f'N = 2.000: 5 / √2000 = {num_es(5 / math.sqrt(2000), 2)} µV', 8.5, TINTA, 'start', 700)
    c.t(436, 374, f'razón señal/ruido: {num_es(20 * math.log10(0.5 / (5 / math.sqrt(2000))), 0)} dB', 8.5, TINTA, 'start', 700)
    c.t(14, 508, 'Ruido de 5 µV RMS por barrido.', 8, TENUE, 'start')
    c.guardar('b4-promedio.svg')


# ---------------------------------------------------------------------------
def nivel_pared(D, freqs, r):
    """Nivel (dB) del campo directo + una reflexión, promediado en potencia sobre las frecuencias."""
    out = []
    for d in D:
        k = 2 * np.pi * freqs / C_SON
        p2 = np.abs(1 + r * np.exp(-1j * k * 2 * d)) ** 2
        out.append(10 * np.log10(np.mean(p2)))
    return np.array(out)


def onda_estacionaria():
    c = Lienzo(700, 340)
    # A: geometría
    c.t(14, 20, 'A · Un parlante, la cabeza y una pared', 10.5, TINTA, 'start', 700)
    c.rect(20, 80, 28, 50, '#fff', TINTA, 1.5, 3)
    c.t(34, 74, 'parlante', 8, TINTA)
    c.circ(150, 105, 17, '#fbf3e6', TINTA, 1.5)
    c.t(150, 138, 'cabeza', 8, TINTA)
    c.l(300, 50, 300, 190, TINTA, 4)
    c.t(300, 206, 'pared', 8, TINTA)
    c.l(48, 100, 130, 100, COCLEAR, 2, punta='cocl')
    c.t(86, 92, 'directo', 8, COCLEAR, 'middle', 700)
    c.l(170, 100, 296, 100, AZUL, 1.6, punta='azul')
    c.l(296, 112, 170, 112, AZUL, 1.6, punta='azul')
    c.t(235, 140, 'reflejado', 8, AZUL, 'middle', 700)
    c.l(150, 160, 300, 160, TENUE, 1, punta='tenue')
    c.l(300, 160, 150, 160, TENUE, 1, punta='tenue')
    c.t(225, 175, 'distancia a la pared', 8, TENUE)
    c.t(14, 235, 'El sonido directo y el reflejado se suman:', 8.5, TINTA, 'start', 700)
    c.t(14, 249, 'donde llegan en fase, el nivel sube;', 8.5, TENUE, 'start')
    c.t(14, 262, 'donde llegan en oposición, baja.', 8.5, TENUE, 'start')
    c.t(14, 280, 'Para un tono de 1.000 Hz, de un máximo al', 8.5, TENUE, 'start')
    c.t(14, 293, f'mínimo hay {num_es(C_SON / 1000 / 4 * 100, 1)} cm (un cuarto de longitud de onda).', 8.5, TENUE, 'start')
    # B: curva
    c.t(350, 20, 'B · El nivel al mover la cabeza (1.000 Hz)', 10.5, TINTA, 'start', 700)
    D = np.linspace(1.00, 1.50, 500)
    r = 0.7
    f_tono = np.array([1000.0])
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    f_warble = 1000 * (1 + 0.05 * np.sin(th))
    f_nbn = np.geomspace(1000 * 2 ** (-1 / 6), 1000 * 2 ** (1 / 6), 200)
    Lt, Lw, Ln = nivel_pared(D, f_tono, r), nivel_pared(D, f_warble, r), nivel_pared(D, f_nbn, r)
    pp = lambda a: float(a.max() - a.min())
    NUM['pared'] = dict(tono=pp(Lt), warble=pp(Lw), nbn=pp(Ln))
    assert abs(NUM['pared']['tono'] - NUM['ripple'][r]) < 0.2
    assert NUM['pared']['warble'] < NUM['pared']['tono'] and NUM['pared']['nbn'] < NUM['pared']['warble']
    ax = Ejes(c, 392, 44, 270, 220, (1.0, 1.5), (-12, 12))
    ax.marco(xt=[1.0, 1.1, 1.2, 1.3, 1.4, 1.5], yt=[-10, -5, 0, 5, 10], xfmt=lambda v: num_es(v, 1), yfmt=lambda v: f'{v:+d}'.replace('+0', '0'),
             xlab='distancia a la pared (m)', ylab='nivel en la cabeza (dB)')
    ax.curva(D, Lt, COCLEAR, 2.2)
    ax.curva(D, Lw, AZUL, 2.0)
    ax.curva(D, Ln, VERDE, 2.0)
    for k, (txt, col, v) in enumerate([('tono puro', COCLEAR, pp(Lt)), ('warble ± 5 %', AZUL, pp(Lw)), ('ruido de 1/3 de octava', VERDE, pp(Ln))]):
        c.l(402, 52 + k * 14, 424, 52 + k * 14, col, 2.2)
        c.t(430, 55 + k * 14, f'{txt}: varía {num_es(v, 1)} dB', 8, TINTA, 'start')
    c.t(14, 328, 'Cálculo con el campo directo más una sola reflexión (coeficiente de presión 0,7); el warble y el ruido promedian la potencia sobre su banda.', 8, TENUE, 'start')
    c.guardar('b4-onda-estacionaria.svg')


# ---------------------------------------------------------------------------
def audifono():
    c = Lienzo(700, 350)
    c.t(14, 20, 'A · Entrada y salida de un audífono', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, 56, 44, 300, 240, (20, 100), (20, 130))
    ax.marco(xt=[20, 40, 60, 80, 100], yt=[20, 40, 60, 80, 100, 120], xfmt=str, yfmt=str,
             xlab='nivel de entrada (dB SPL)', ylab='nivel de salida (dB SPL)')
    xs = np.arange(20, 101, 1.0)
    ospl = 115.0
    lineal = np.minimum(xs + 30, ospl)
    comp = np.where(xs <= 45, xs + 30, 75 + (xs - 45) / 2.0)
    comp = np.minimum(comp, ospl)
    ax.curva(xs, xs, FUERTE, 1.2, '4 3')
    ax.curva(xs, lineal, COCLEAR, 2.4)
    ax.curva(xs, comp, AZUL, 2.4)
    assert lineal[60 - 20] - 60 == 30 and lineal[90 - 20] == 115 and abs(comp[90 - 20] - 97.5) < 1e-9
    c.t(ax.X(52), ax.Y(24) - 6, 'sin amplificar (salida = entrada)', 7.5, TENUE, 'start')
    c.t(ax.X(21), ax.Y(ospl) - 6, 'tope de salida (OSPL90, 115 dB)', 8, COCLEAR, 'start', 700)
    c.l(ax.X(60), ax.Y(60), ax.X(60), ax.Y(90), COCLEAR, 1.2, '3 2')
    c.t(ax.X(58), ax.Y(100), 'ganancia 30 dB', 8, COCLEAR, 'end', 700)
    c.t(ax.X(62), ax.Y(comp[62 - 20]) + 28, 'comprimido 2:1', 8, AZUL, 'start', 700)
    c.t(ax.X(62), ax.Y(comp[62 - 20]) + 39, 'sobre 45 dB de entrada', 8, AZUL, 'start')
    c.t(ax.X(99), ax.Y(110), 'recorta desde 85 dB de entrada', 8, COCLEAR, 'end', 700)
    # B: recorte
    c.t(400, 20, 'B · Qué agrega el recorte', 10.5, TINTA, 'start', 700)
    t = np.linspace(0, 2, 600, endpoint=False)
    sig = np.sin(2 * np.pi * 5 * t)
    clip = np.clip(1.25 * sig, -1.0, 1.0)
    x0, w = 410, 250
    for k, (s, col, tit) in enumerate([(1.4 * sig / 1.4, TENUE, 'tono limpio'), (clip / 0.7 * 0.7, COCLEAR, 'tono recortado')]):
        pass
    yc = 90
    amp = 38
    c.l(x0, yc, x0 + w, yc, GRILLA, 0.8)
    c.poli([(x0 + i / 600 * w, yc - amp * 1.25 * sig[i]) for i in range(600)], TENUE, 1.0, '4 3')
    c.poli([(x0 + i / 600 * w, yc - amp * clip[i]) for i in range(600)], COCLEAR, 2.0)
    c.l(x0, yc - amp, x0 + w, yc - amp, AVISO, 0.8, '2 2')
    c.t(x0 + w, yc - amp + 12, 'tope', 7.5, AVISO, 'end')
    c.t(x0, yc - amp * 1.25 - 12, 'gris: el tono sin recortar · naranja: lo que sale', 7.5, TENUE, 'start')
    # armónicos del recortado
    nn = 6000
    tt = np.arange(nn) / nn * 10
    xx = np.clip(1.25 * np.sin(2 * np.pi * tt), -1.0, 1.0)
    sp = np.abs(np.fft.rfft(xx)) / (nn / 2)
    base = sp[10]
    armon = [sp[10 * k] / base for k in range(1, 8)]
    thd = math.sqrt(sum(a * a for a in armon[1:]))
    NUM['thd'] = dict(thd=thd, db=20 * math.log10(thd), arm=armon)
    ax2 = Ejes(c, x0, 170, 250, 100, (0.5, 7.5), (-60, 0))
    ax2.marco(xt=[1, 2, 3, 4, 5, 6, 7], yt=[-60, -40, -20, 0], xfmt=lambda v: f'{v}f', yfmt=str, grilla=True, size=7.5)
    for k, a in enumerate(armon):
        h = max(20 * math.log10(max(a, 1e-4)), -60)
        c.rect(ax2.X(k + 1) - 6, ax2.Y(h), 12, ax2.Y(-60) - ax2.Y(h), COCLEAR if k else TINTA, COCLEAR if k else TINTA, 0, 1, op=0.8)
    c.t(x0 + 125, 296, 'nivel de cada armónico respecto del tono (dB)', 8, TENUE)
    c.t(x0 + 125, 314, f'distorsión armónica total: {num_es(thd * 100, 0)} % ({num_es(20 * math.log10(thd), 0)} dB)', 8.5, COCLEAR, 'middle', 700)
    c.t(14, 340, 'Ganancia lineal de 30 dB con tope de 115 dB; compresor de 2:1 desde 45 dB de entrada.', 8, TENUE, 'start')
    c.guardar('b4-audifono.svg')


# ---------------------------------------------------------------------------
def nariz():
    N = NUM['nariz']
    k1, k2 = N['k1'], N['k2']
    c = Lienzo(700, 340)
    c.t(14, 20, 'A · Presión contra flujo en una fosa nasal', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, 60, 44, 300, 240, (0, 600), (0, 200))
    ax.marco(xt=[0, 100, 200, 300, 400, 500, 600], yt=[0, 50, 100, 150, 200], xfmt=str, yfmt=str,
             xlab='flujo (cm³/s)', ylab='presión (Pa)')
    q = np.linspace(0, 600, 200)
    ax.curva(q, k1 * q + k2 * q ** 2, COCLEAR, 2.6)
    ax.curva(q, k1 * q, TENUE, 1.4, '5 3')
    ax.curva(q, 0.26 * q, FUERTE, 0.1)
    for P, R in ((75, 0.26), (150, 0.35)):
        qq = P / R
        ax.curva([0, qq], [0, P], AZUL, 1.3)
        c.circ(ax.X(qq), ax.Y(P), 4, '#fff', AZUL, 1.8)
        c.l(ax.X(qq), ax.Y(P), ax.X(qq), ax.Y(0), AZUL, 0.8, '3 3')
        c.t(ax.X(qq) + 8, ax.Y(P) + 14, f'{P} Pa: R = {num_es(R, 2)}', 8, AZUL, 'start', 700)
    c.t(ax.X(380), ax.Y(k1 * 380) + 14, 'solo laminar (recta)', 8, TENUE, 'start')
    c.t(ax.X(25), ax.Y(185), 'laminar + turbulento (curva)', 8, COCLEAR, 'start', 700)
    # B: resistencia vs radio
    c.t(400, 20, 'B · Un tubo: la resistencia contra el radio', 10.5, TINTA, 'start', 700)
    ax2 = Ejes(c, 440, 44, 220, 240, (0.4, 1.2), (0.3, 30), xlog=False, ylog=True)
    ax2.marco(xt=[0.4, 0.6, 0.8, 1.0, 1.2], yt=[0.3, 1, 3, 10, 30], xfmt=lambda v: num_es(v, 1), yfmt=lambda v: num_es(v, 1) if v < 1 else f'{v:g}',
              xlab='radio (1 = el de reposo)', ylab='resistencia (1 = la de reposo)')
    rs = np.linspace(0.4, 1.2, 80)
    ax2.curva(rs, 1 / rs ** 4, COCLEAR, 2.4)
    for r in (1.0, 0.8, 0.5):
        v = 1 / r ** 4
        c.circ(ax2.X(r), ax2.Y(v), 3.6, '#fff', COCLEAR, 1.8)
        c.t(ax2.X(r) + 8, ax2.Y(v) - 6, f'×{num_es(v, 1)}' if v < 10 else f'×{v:.0f}', 8, COCLEAR, 'start', 700)
    c.t(14, 322, f'A: curva de la forma ΔP = k₁ V̇ + k₂ V̇², ajustada a las dos resistencias de H24 (0,26 a 75 Pa y 0,35 a 150 Pa): k₁ = {num_es(k1, 3)}, k₂ = {num_es(k2 * 1000, 2)}·10⁻³.', 8, TENUE, 'start')
    c.t(14, 335, 'B: ley de Poiseuille, R proporcional a 1 / r⁴ (tubo recto y liso).', 8, TENUE, 'start')
    c.guardar('b4-nariz.svg')


# ---------------------------------------------------------------------------
def reflexion():
    c = Lienzo(700, 430)
    c.t(14, 20, 'A · Un tubo con un estrechamiento y el eco que devuelve', 10.5, TINTA, 'start', 700)
    # tubo: ancho 1.5 -> 0.6 (x 1.3 cm) -> 1.5 (x 3.1 cm)
    X0, esc = 70, 62   # px por cm
    xs = [X0, X0 + 1.3 * esc, X0 + 3.1 * esc, X0 + 5.2 * esc]
    hmid = 120
    def alto(a):
        return 30 * a / 1.5
    # contorno
    sup = [(xs[0], hmid - alto(1.5)), (xs[1], hmid - alto(1.5)), (xs[1], hmid - alto(0.6)), (xs[2], hmid - alto(0.6)),
           (xs[2], hmid - alto(1.5)), (xs[3], hmid - alto(1.5))]
    inf = [(x, 2 * hmid - y) for x, y in sup]
    c.poli(sup, TINTA, 2.4)
    c.poli(inf, TINTA, 2.4)
    c.t((xs[1] + xs[2]) / 2, hmid + 4, '0,6 cm²', 8, COCLEAR, 'middle', 700)
    c.t(xs[3] - 50, hmid + 4, 'A₁ = 1,5 cm² (tubo)', 8.5, TENUE, 'middle')
    c.l(xs[0] - 4, hmid, xs[0] + 26, hmid, COCLEAR, 2.2, punta='cocl')
    c.t(xs[0] - 4, hmid - 36, 'pulso', 8, COCLEAR, 'start', 700)
    # posiciones
    c.l(xs[1], hmid + 40, xs[1], hmid + 52, TENUE, 1)
    c.t(xs[1], hmid + 64, '1,3 cm', 8, TENUE)
    c.l(xs[2], hmid + 40, xs[2], hmid + 52, TENUE, 1)
    c.t(xs[2], hmid + 64, '3,1 cm', 8, TENUE)
    # eco (lollipops)
    E = NUM['refl_ej']
    R = E['R']
    eco2 = E['eco2']
    yb = 262
    c.l(X0, yb, X0 + 5.2 * esc, yb, FUERTE, 1.2)
    c.t(X0 - 6, yb - 36, '+', 10, TENUE, 'end')
    c.t(X0 - 6, yb + 38, '−', 10, TENUE, 'end')
    c.t(X0 + 5.2 * esc, yb - 6, 'tiempo de vuelta →', 8, TENUE, 'end')
    for t_us, v, col in ((E['t1'], R, AVISO), (E['t2'], eco2, AZUL)):
        px = X0 + (t_us / 2 * C_SON / 1e4) * esc   # mismo eje que la distancia
        c.l(px, yb, px, yb - v * 80, col, 3)
        c.circ(px, yb - v * 80, 3.6, col, col, 1)
        c.t(px + 8, yb - v * 80 + (3 if v > 0 else 14), f'{v:+.2f}'.replace('.', ',').replace('-', '−'), 8.5, col, 'start', 700)
        c.t(px if v > 0 else px + 8, yb + 16, f'{t_us:.0f} µs', 8, TENUE, 'middle' if v > 0 else 'start')
    c.t(X0 + 10, yb - 62, f'se estrecha: eco del mismo signo (+{num_es(R, 2)})', 8, AVISO, 'start', 700)
    c.t(X0 + 3.1 * esc + 14, yb + 62, f'se ensancha: eco de signo contrario ({num_es(eco2, 2)})'.replace('(-', '(−'), 8, AZUL, 'start', 700)
    # B: R y energía de ida y vuelta vs A2/A1
    bx = 440
    c.t(bx - 14, 20, 'B · Cuánto del pulso pasa y vuelve', 10.5, TINTA, 'start', 700)
    ax = Ejes(c, bx + 6, 44, 210, 200, (0.01, 1), (0, 1), xlog=True)
    ax.marco(xt=[0.01, 0.03, 0.1, 0.3, 1], yt=[0, 0.25, 0.5, 0.75, 1], xfmt=lambda v: num_es(v, 2) if v < 0.1 else num_es(v, 1) if v < 1 else '1',
             yfmt=lambda v: num_es(v, 2), xlab='área del estrechamiento / área del tubo', ylab='fracción')
    r = np.geomspace(0.01, 1, 80)
    Rr = (1 - r) / (1 + r)
    ax.curva(r, Rr, AVISO, 2.2)
    ax.curva(r, (1 - Rr ** 2) ** 2, AZUL, 2.2)
    c.t(ax.X(0.011), ax.Y(0.62), 'eco de la entrada (R)', 8, AVISO, 'start', 700)
    c.t(ax.X(0.011), ax.Y(0.36), 'energía que vuelve', 8, AZUL, 'start', 700)
    c.t(ax.X(0.011), ax.Y(0.29), 'desde lo de atrás', 8, AZUL, 'start', 700)
    for ra in (0.4, 0.1, 0.02):
        v = NUM['refl'][ra][2]
        c.circ(ax.X(ra), ax.Y(v), 3.5, '#fff', AZUL, 1.6)
    c.t(14, 414, 'Cálculo con las ecuaciones de la onda plana en un tubo: R = (A₁ − A₂) / (A₁ + A₂); la distancia sale de la demora, x = c·t/2 con c = 343 m/s.', 8, TENUE, 'start')
    c.guardar('b4-reflexion.svg')


if __name__ == '__main__':
    print('dibujando B4...')
    onda()
    estimulos()
    ruidos()
    banda_critica()
    filtros()
    decibel()
    escalas()
    resonancia()
    promedio()
    onda_estacionaria()
    audifono()
    nariz()
    reflexion()
    import json
    print(json.dumps({k: (v if not isinstance(v, dict) else {str(a): b for a, b in v.items()}) for k, v in NUM.items()
                      if k in ('pared', 'thd', 'reson', 'prom_medido', 'g50_hp2')}, indent=1, default=str))
