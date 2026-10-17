#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H13 (potenciales de estado estable):

    h13-modulacion-espectro.svg  A: tono portador modulado en amplitud;
                                 B: espectro del EEG con un pico en cada frecuencia de modulación
    h13-correccion.svg           del umbral del ASSR (dB nHL) al audiograma estimado (dB eHL)

SVG propios, no IA: son esquemas. Las cifras son ilustrativas; la corrección del
segundo dibujo es la Tabla 1 de BSA (2023) para fonos de inserción, <= 12 semanas."""
import math
import pathlib
import random

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO = '#c0571c', '#21796c', '#c62f3a'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}{extra}/>')

    def poli(self, pts, color, w=2, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}{extra}/>')

    def guardar(self, nombre, defs=''):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><defs>{defs}</defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def punta(id_, color):
    return (f'<marker id="{id_}" markerWidth="6" markerHeight="6" refX="4" refY="3.5" '
            f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" '
            f'transform="scale(.8)" fill="{color}"/></marker>')


def modulacion():
    c = Lienzo(700, 290)
    # Panel A: portador modulado
    x0, ancho, yc, amp = 40, 280, 120, 46
    c.t(14, 20, 'A · Un tono modulado en amplitud', 10.5, TINTA, 'start', 700)
    c.l(x0, yc, x0 + ancho, yc, GRILLA, 1)
    n = 900
    pts = []
    for i in range(n + 1):
        u = i / n
        env = 0.5 * (1 + math.cos(2 * math.pi * 3 * u - math.pi))   # 3 ciclos de modulación
        env = 0.12 + 0.88 * env
        pts.append((x0 + u * ancho, yc - amp * env * math.sin(2 * math.pi * 36 * u)))
    c.poli(pts, TINTA, 0.8)
    for signo in (1, -1):
        e = [(x0 + (i / 200) * ancho, yc - signo * amp * (0.12 + 0.88 * 0.5 * (1 + math.cos(2 * math.pi * 3 * i / 200 - math.pi))))
             for i in range(201)]
        c.poli(e, COCLEAR, 1.8, '5 3')
    c.t(x0 + ancho / 2, yc + amp + 56, 'tiempo →', 8.5, TENUE)
    c.t(x0 + 6, yc - amp - 10, 'portador (tono de la frecuencia a estudiar)', 8.5, TINTA, 'start', 600)
    c.t(x0 + ancho - 2, yc + amp + 38, 'envolvente = frecuencia de modulación', 8.5, COCLEAR, 'end', 700)
    # periodo
    xa = x0 + ancho / 3
    c.l(xa, yc + amp + 8, xa + ancho / 3, yc + amp + 8, COCLEAR, 1)
    c.t(xa + ancho / 6, yc + amp + 19, '1 / frecuencia de modulación', 8, COCLEAR)

    # Panel B: espectro del EEG
    bx, by, bw, bh = 400, 52, 270, 150
    c.t(bx - 20, 20, 'B · Espectro del EEG del paciente', 10.5, TINTA, 'start', 700)
    f0, f1 = 70, 115
    X = lambda f: bx + (f - f0) / (f1 - f0) * bw
    c.l(bx, by + bh, bx + bw, by + bh, FUERTE, 1)
    c.l(bx, by, bx, by + bh, FUERTE, 1)
    for f in range(70, 116, 10):
        c.l(X(f), by + bh, X(f), by + bh + 4, FUERTE, 1)
        c.t(X(f), by + bh + 16, f, 8, TENUE)
    c.t(bx + bw / 2, by + bh + 30, 'frecuencia (Hz)', 8.5, TENUE)
    c.t(bx - 8, by + 8, 'amplitud', 8.5, TENUE, 'end')
    random.seed(13)
    picos = {82: 'ej. 500 Hz', 90: '1000 Hz', 98: '2000 Hz', 106: '4000 Hz'}
    ruido = []
    f = f0
    while f <= f1 + 1e-9:
        v = 6 + abs(random.gauss(0, 3.2))
        for p in picos:
            v += 62 * math.exp(-((f - p) / 0.45) ** 2) * (0.75 + 0.25 * random.random())
        ruido.append((X(f), by + bh - v))
        f += 0.25
    c.poli(ruido, TINTA, 1.1)
    c.l(bx, by + bh - 24, bx + bw, by + bh - 24, TENUE, 1, '4 3')
    c.t(bx + bw + 2, by + bh - 21, 'ruido', 8, TENUE, 'start')
    for p, nombre in picos.items():
        c.t(X(p), by + bh - 78, f'{p}', 8, COCLEAR, 'middle', 700)
        c.t(X(p), by + bh - 88, nombre.replace('ej. ', ''), 7.5, TENUE, 'middle')
    c.t(bx + bw / 2, by - 12, 'un oído, cuatro portadores, cuatro moduladores distintos', 8.5, TINTA, 'middle', 600)
    c.t(14, 282, 'Esquema, no datos: las frecuencias de modulación son un ejemplo; cada equipo usa las suyas.', 8, TENUE, 'start')
    c.guardar('h13-modulacion-espectro.svg')


def correccion():
    c = Lienzo(700, 300)
    x0, y0, ancho, alto = 90, 48, 330, 190
    frs = [500, 1000, 2000, 4000]
    X = lambda i: x0 + 45 + i * (ancho - 90) / 3
    Y = lambda db: y0 + db / 100 * alto
    c.t(14, 20, 'Del umbral del ASSR al audiograma estimado (recién nacido, fonos de inserción)', 10.5, TINTA, 'start', 700)
    for db in range(0, 101, 20):
        c.l(x0, Y(db), x0 + ancho, Y(db), GRILLA, 0.6)
        c.t(x0 - 8, Y(db) + 3, db, 8, TENUE, 'end')
    for i, fr in enumerate(frs):
        c.t(X(i), y0 - 8, fr, 8.5, TENUE)
    c.t(x0 + ancho / 2, y0 + alto + 18, 'frecuencia (Hz)', 8.5, TENUE)
    c.t(x0 - 54, y0 + alto / 2, 'dB', 8.5, TENUE, 'middle')
    nhl = [70, 65, 60, 60]
    corr = [20, 20, 15, 15]
    ehl = [a - b for a, b in zip(nhl, corr)]
    for i in range(4):
        c.l(X(i), Y(nhl[i]) - 6, X(i), Y(ehl[i]) + 6, AVISO, 1.4, extra=' marker-end="url(#p-corr)"')
        c.out.append(f'<circle cx="{X(i):.1f}" cy="{Y(nhl[i]):.1f}" r="4.5" fill="#fff" stroke="{TENUE}" stroke-width="1.6"/>')
        c.out.append(f'<rect x="{X(i) - 4.5:.1f}" y="{Y(ehl[i]) - 4.5:.1f}" width="9" height="9" fill="{COCLEAR}"/>')
        c.t(X(i) + 12, (Y(nhl[i]) + Y(ehl[i])) / 2 + 3, f'−{corr[i]}', 8.5, AVISO, 'start', 700)
    c.poli([(X(i), Y(ehl[i])) for i in range(4)], COCLEAR, 1.6)
    # leyenda
    lx = 470
    c.out.append(f'<circle cx="{lx}" cy="80" r="4.5" fill="#fff" stroke="{TENUE}" stroke-width="1.6"/>')
    c.t(lx + 12, 83, 'umbral del ASSR (dB nHL)', 9, TINTA, 'start')
    c.out.append(f'<rect x="{lx - 4.5}" y="102.5" width="9" height="9" fill="{COCLEAR}"/>')
    c.t(lx + 12, 111, 'audiograma estimado (dB eHL)', 9, TINTA, 'start')
    c.l(lx, 150, lx, 134, AVISO, 1.4, extra=' marker-end="url(#p-corr)"')
    c.t(lx + 12, 146, 'corrección que se resta', 9, TINTA, 'start')
    c.t(lx - 6, 182, 'Ejemplo: 70 − 20 = 50 dB eHL en 500 Hz.', 8.5, TINTA, 'start', 600)
    c.t(lx - 6, 196, 'Correcciones de BSA (2023), recién nacido', 8.5, TENUE, 'start')
    c.t(lx - 6, 208, 'hasta 12 semanas, fonos de inserción:', 8.5, TENUE, 'start')
    c.t(lx - 6, 220, '500 y 1000 Hz: −20 · 2000 y 4000 Hz: −15.', 8.5, TENUE, 'start')
    c.t(14, 292, 'Esquema con umbrales de ejemplo. Valen solo para umbrales sobre 30 dB eHL.', 8, TENUE, 'start')
    c.guardar('h13-correccion.svg', punta('p-corr', AVISO))


if __name__ == '__main__':
    modulacion()
    correccion()
