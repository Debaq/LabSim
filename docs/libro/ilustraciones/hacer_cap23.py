#!/usr/bin/env python3
"""Ilustraciones del capítulo 23 (crisis que vuelven):

    cap23-duraciones.svg   cuánto dura una crisis según el diagnóstico (criterios de la Sociedad Bárány)
    cap23-evolucion.svg    el audiograma OD de un Ménière en tres momentos (cifras del historial del caso)
    cap23-disociacion.svg  paresia calórica contra ganancia del vHIT, con los cuatro casos del capítulo

Esquemas docentes: los umbrales vienen de la bibliografía del capítulo; los puntos de los casos son los
resultados que el texto entrega. Ningún dato sale de los simuladores.
    python3 docs/libro/ilustraciones/hacer_cap23.py"""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
OD, OI = '#c62f3a', '#2b5fa8'
VERDE, NARANJA, MORADO = '#21796c', '#c0571c', '#6b4a9e'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{esc(s)}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}"{d}/>')

    def r(self, x, y, w, h, fill, op=1, stroke='none', rx=0):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                        f'fill-opacity="{op}" stroke="{stroke}"/>')

    def c(self, x, y, r, fill, stroke='none', w=1):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')

    def poli(self, pts, color, w=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def duraciones():
    c = Lienzo(720, 330)
    x0, x1 = 170, 690
    # eje logarítmico en minutos: 0,1 min (6 s) a 10.000 min (~7 días)
    lo, hi = math.log10(0.1), math.log10(10000)
    X = lambda m: x0 + (math.log10(m) - lo) / (hi - lo) * (x1 - x0)
    c.t(360, 22, 'Cuánto dura una crisis, según los criterios diagnósticos', 13, TINTA, 'middle', 700)
    for m, rot in [(0.1, '6 s'), (1, '1 min'), (10, '10 min'), (60, '1 h'), (600, '10 h'), (1440, '1 día'), (4320, '72 h'), (10000, '7 días')]:
        c.l(X(m), 44, X(m), 270, GRILLA, 1)
        c.t(X(m), 288, rot, 10, TENUE)
    c.t(x1 - 2, 311, 'duración de cada crisis (escala logarítmica)', 10, TENUE, 'end')
    filas = [
        ('VPPB (→ cap. 22)', 0.1, 1, MORADO, 'menos de 1 min'),
        ('Ménière definido', 20, 720, OD, '20 min a 12 h'),
        ('Ménière probable', 20, 1440, '#e08a90', 'hasta 24 h'),
        ('Migraña vestibular', 5, 4320, VERDE, '5 min a 72 h'),
    ]
    for k, (nom, a, b, col, rot) in enumerate(filas):
        y = 64 + k * 52
        c.t(x0 - 10, y + 16, nom, 12, TINTA, 'end', 700)
        c.r(X(a), y, X(b) - X(a), 26, col, 0.85, rx=4)
        c.t(X(b) + 6 if X(b) < 560 else X(a) - 6, y + 17, rot, 11, TINTA, 'start' if X(b) < 560 else 'end')
    c.guardar('cap23-duraciones.svg')


def evolucion():
    c = Lienzo(740, 330)
    F9 = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]
    paneles = [
        ('Año 0', 'ascendente', [60, 55, 35, 25, 20, 15, 20, 20, 25], 'etapa 1'),
        ('Año 3', 'se aplana', [60, 55, 50, 40, 35, 35, 40, 50, 55], 'etapa 2'),
        ('Hoy', 'fija, descendente', [45, 45, 50, 55, 55, 60, 70, 80, 85], 'etapa 3'),
    ]
    c.t(370, 22, 'Oído derecho de Ignacio: tres audiogramas en el historial', 13, TINTA, 'middle', 700)
    pw, ph, top = 200, 210, 56
    for k, (tit, forma, vals, etapa) in enumerate(paneles):
        ox = 40 + k * (pw + 25)
        c.t(ox + pw / 2, top - 10, f'{tit} · {forma}', 11, TINTA, 'middle', 700)
        c.r(ox, top, pw, ph, '#fff', 1, FUERTE)
        Y = lambda db: top + db / 120 * ph
        for db in range(0, 121, 20):
            c.l(ox, Y(db), ox + pw, Y(db), GRILLA, 1)
            if k == 0:
                c.t(ox - 5, Y(db) + 3, str(db), 9, TENUE, 'end')
        xs = [ox + 14 + i * (pw - 28) / 8 for i in range(9)]
        for i, f in enumerate(F9):
            c.t(xs[i], top + ph + 14, ('125' if f == 125 else f'{f/1000:g}k' if f >= 1000 else str(f)), 8, TENUE)
        c.poli([(xs[i], Y(v)) for i, v in enumerate(vals)], OD, 2)
        for i, v in enumerate(vals):
            c.c(xs[i], Y(v), 3.4, '#fff', OD, 1.6)
        pta = round((vals[2] + vals[3] + vals[4] + vals[5]) / 4)
        c.t(ox + pw / 2, top + ph + 34, f'promedio 500-3.000 Hz: {pta:g} dB · {etapa}', 10, TINTA)
    c.t(370, 318, 'dB HL, vía aérea. El de hoy es el audiograma del caso.', 9.5, TENUE)
    c.guardar('cap23-evolucion.svg')


def disociacion():
    c = Lienzo(720, 400)
    ox, oy, w, h = 80, 50, 590, 290
    xm, ym0, ym1 = 100, 0.4, 1.2
    X = lambda p: ox + p / xm * w
    Y = lambda g: oy + (ym1 - g) / (ym1 - ym0) * h
    c.t(375, 24, 'Calórica y vHIT del canal lateral, lado por lado', 13, TINTA, 'middle', 700)
    c.r(ox, oy, w, h, '#fff', 1, FUERTE)
    # cuadrante de disociación: paresia >=25 % con ganancia >=0,8
    c.r(X(25), Y(1.2), X(100) - X(25), Y(0.8) - Y(1.2), VERDE, 0.10)
    c.r(X(25), Y(0.8), X(100) - X(25), Y(0.4) - Y(0.8), OD, 0.08)
    for g in [0.4, 0.6, 0.8, 1.0, 1.2]:
        c.l(ox, Y(g), ox + w, Y(g), GRILLA, 1)
        c.t(ox - 6, Y(g) + 3, f'{g:.1f}'.replace('.', ','), 10, TENUE, 'end')
    for p in range(0, 101, 20):
        c.t(X(p), oy + h + 16, f'{p} %', 10, TENUE)
    c.l(X(25), oy, X(25), oy + h, TENUE, 1.2, '5 4')
    c.l(ox, Y(0.8), ox + w, Y(0.8), TENUE, 1.2, '5 4')
    c.t(X(25) + 4, oy + 12, 'paresia 25 %', 9.5, TENUE, 'start')
    c.t(ox + 4, Y(0.8) - 4, 'ganancia 0,8', 9.5, TENUE, 'start')
    c.t(X(62), Y(1.2) + 18, 'calórica alterada, vHIT normal:', 11, VERDE, 'middle', 700)
    c.t(X(62), Y(1.2) + 32, 'la disociación del hidrops', 11, VERDE, 'middle', 700)
    c.t(X(62), Y(0.4) - 8, 'las dos alteradas: pérdida del canal', 11, OD, 'middle', 700)
    c.t(X(12), Y(1.2) + 18, 'ambas normales', 11, TENUE, 'middle', 700)
    c.t(X(12), Y(0.4) - 8, 'vHIT solo alterado', 11, TENUE, 'middle')
    c.t(ox + w / 2, oy + h + 36, 'paresia canalicular de la calórica (%)', 11, TINTA)
    c.out.append(f'<text transform="translate(22,{oy + h / 2}) rotate(-90)" {F} font-size="11" fill="{TINTA}" text-anchor="middle">'
                 f'ganancia del vHIT, canal lateral del oído más débil</text>')
    pts = [('Ignacio', 55, 0.95, NARANJA), ('Clara', 12, 0.82, MORADO), ('Patricia', 3, 0.99, VERDE), ('Marina', 32, 0.97, OI)]
    for nom, p, g, col in pts:
        c.c(X(p), Y(g), 7, col, '#fff', 1.5)
        c.t(X(p) + 11, Y(g) + 4, nom, 11, TINTA, 'start', 700)
    c.t(375, 392, 'Cortes: paresia de 25 % (calórica mínima del protocolo, → H16) y ganancia de 0,8 como límite habitual (→ H17).', 9.5, TENUE)
    c.guardar('cap23-disociacion.svg')


if __name__ == '__main__':
    duraciones()
    evolucion()
    disociacion()
