#!/usr/bin/env python3
"""Ilustraciones del capítulo 24 (cuando fallan los dos lados):

    cap24-cociente.svg     suma de velocidades calóricas de cada oído de los cuatro casos: sobre la diagonal la paresia da 0
    cap24-causas.svg       causas de la vestibulopatía bilateral en dos series (Zingler 2007; Lucieer 2016)
    cap24-oscilopsia.svg   qué le pasa a la imagen en la retina al caminar con el reflejo íntegro y con el perdido

Esquemas docentes. Los umbrales (6 °/s, 25 %) vienen de la bibliografía del capítulo; los puntos de los casos son los
resultados que el texto entrega ("cifras inventadas para el libro"). Ningún dato sale de los simuladores.
    python3 docs/libro/ilustraciones/hacer_cap24.py"""
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

    def area(self, pts, color, op=0.25):
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polygon points="{p}" fill="{color}" fill-opacity="{op}" stroke="none"/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def cociente():
    c = Lienzo(720, 440)
    ox, oy, w, h = 80, 50, 590, 320
    lim = 14.0
    X = lambda v: ox + v / lim * w
    Y = lambda v: oy + (lim - v) / lim * h
    c.t(375, 24, 'Suma tibia + fría de cada oído: la fórmula de asimetría no la ve', 13, TINTA, 'middle', 700)
    c.r(ox, oy, w, h, '#fff', 1, FUERTE)
    for v in range(0, 15, 2):
        c.l(ox, Y(v), ox + w, Y(v), GRILLA, 1)
        c.l(X(v), oy, X(v), oy + h, GRILLA, 1)
        c.t(ox - 6, Y(v) + 3, str(v), 10, TENUE, 'end')
        c.t(X(v), oy + h + 16, str(v), 10, TENUE)
    # zona de la vestibulopatía en la calórica: los dos oídos con suma < 6 °/s
    c.r(ox, Y(6), X(6) - ox, oy + h - Y(6), VERDE, 0.13)
    c.l(X(6), Y(6), X(6), oy + h, VERDE, 1.4, '5 4')
    c.l(ox, Y(6), X(6), Y(6), VERDE, 1.4, '5 4')
    c.t(X(3), Y(6) - 6, 'los dos oídos bajo 6 °/s', 10.5, VERDE, 'middle', 700)
    # cuña de |paresia| < 25 %: OI/OD entre 0,6 y 5/3
    c.area([(X(0), Y(0)), (X(lim), Y(lim * 0.6)), (X(lim), Y(lim)), (X(lim * 0.6), Y(lim))], NARANJA, 0.10)
    c.l(X(0), Y(0), X(lim), Y(lim), TENUE, 1.2, '2 3')
    c.l(X(0), Y(0), X(lim), Y(lim * 0.6), NARANJA, 1.2, '5 4')
    c.l(X(0), Y(0), X(lim * 0.6), Y(lim), NARANJA, 1.2, '5 4')
    c.t(X(11.2), Y(11.2) + 15, 'paresia 0 %', 10, TENUE, 'middle')
    c.t(X(13.6), Y(13.6 * 0.6) - 6, 'paresia 25 %', 10, NARANJA, 'end')
    c.t(X(8.1), Y(13.7), 'paresia 25 % (el otro lado)', 10, NARANJA, 'end')
    c.t(X(8.9), Y(12.9), 'dentro de la cuña: la fórmula informa', 10, NARANJA, 'start')
    c.t(X(8.9), Y(12.2), '«paresia no significativa»', 10, NARANJA, 'start')
    pts = [('Enrique', 3, 4, '−14 %'), ('Verónica', 8, 5, '23 %'), ('Pilar', 4, 5, '−11 %'), ('Jorge', 2, 3, '−20 %')]
    pos = {'Enrique': (11, 14, 'start'), 'Verónica': (11, 4, 'start'), 'Pilar': (-10, -10, 'end'), 'Jorge': (-10, 14, 'end')}
    for nom, a, b, p in pts:
        c.c(X(a), Y(b), 7, MORADO, '#fff', 1.5)
        dx, dy, an = pos[nom]
        c.t(X(a) + dx, Y(b) + dy, f'{nom} ({p})', 10.5, TINTA, an, 700)
    c.t(ox + w / 2, oy + h + 36, 'oído derecho: suma de la velocidad de la fase lenta, tibia + fría (°/s)', 11, TINTA)
    c.out.append(f'<text transform="translate(26,{oy + h / 2}) rotate(-90)" {F} font-size="11" fill="{TINTA}" text-anchor="middle">'
                 f'oído izquierdo: suma tibia + fría (°/s)</text>')
    c.t(375, 430, 'Cifras inventadas para el libro. Entre paréntesis, la paresia canalicular con la fórmula de Jongkees; el eje llega solo a 14 °/s.', 9.5, TENUE)
    c.guardar('cap24-cociente.svg')


def causas():
    c = Lienzo(720, 285)
    c.t(360, 22, 'De qué se debe una vestibulopatía bilateral: dos series de pacientes', 13, TINTA, 'middle', 700)
    x0, x1 = 60, 680
    X = lambda p: x0 + p / 100 * (x1 - x0)
    series = [
        ('Zingler 2007 · 255 pacientes', 62,
         [('aminoglucósidos', 13, NARANJA), ('Ménière', 7, OD), ('meningitis', 5, MORADO), ('otras, definidas o probables', 24, OI), ('sin causa', 51, '#b9b6b0')]),
        ('Lucieer 2016 · 154 pacientes', 165,
         [('causa definida', 47, OI), ('causa probable', 22, '#7ea3d4'), ('idiopática', 31, '#b9b6b0')]),
    ]
    for tit, y, partes in series:
        c.t(x0, y - 10, tit, 11.5, TINTA, 'start', 700)
        acc = 0
        for nom, v, col in partes:
            c.r(X(acc), y, X(v) - x0, 40, col, 0.9, '#fff')
            c.t(X(acc + v / 2), y + 24, f'{v} %', 11.5, '#fff' if col != '#b9b6b0' else TINTA, 'middle', 700)
            ancho = X(v) - x0
            if ancho > 70:
                c.t(X(acc + v / 2), y + 58, nom, 9.5, TINTA, 'middle')
            else:
                c.t(X(acc + v / 2), y + 58 + (11 if nom == 'Ménière' else 0), nom, 9.5, TINTA, 'middle')
            acc += v
    c.t(360, 250, 'Los porcentajes salen de los resúmenes de cada serie; las categorías de cada una no son las mismas y no se comparan entre sí.', 9.5, TENUE)
    c.t(360, 266, 'En la de Zingler, «otras» es la diferencia entre el 49 % con causa definida o probable y las tres causas nombradas (25 %).', 9.5, TENUE)
    c.guardar('cap24-causas.svg')


def oscilopsia():
    c = Lienzo(720, 375)
    c.t(360, 22, 'La cabeza se mueve al caminar: cuánto resbala la imagen en la retina', 13, TINTA, 'middle', 700)
    paneles = [('A · Reflejo íntegro (ganancia 1,0)', 1.0), ('B · Pérdida bilateral (ganancia 0,2)', 0.2)]
    for k, (tit, g) in enumerate(paneles):
        px, py, pw, ph = 70 + k * 330, 70, 270, 200
        c.t(px, py - 14, tit, 11, TINTA, 'start', 700)
        c.r(px, py, pw, ph, '#fff', 1, FUERTE)
        X = lambda t: px + t / 1.0 * pw
        Y = lambda v: py + ph / 2 - v / 110 * ph / 2
        for v in (-90, 0, 90):
            c.l(px, Y(v), px + pw, Y(v), GRILLA if v else FUERTE, 1)
            if k == 0:
                c.t(px - 6, Y(v) + 3, str(v), 9.5, TENUE, 'end')
        cab = lambda t: 90 * math.sin(2 * math.pi * 2 * t)
        ts = [i / 200 for i in range(201)]
        # lo que resbala la imagen: cabeza menos ojo compensando
        c.area([(X(t), Y(cab(t))) for t in ts] + [(X(t), Y(g * cab(t))) for t in reversed(ts)], NARANJA, 0.30)
        c.poli([(X(t), Y(cab(t))) for t in ts], OI, 2.2)
        c.poli([(X(t), Y(g * cab(t))) for t in ts], VERDE, 2.2)
        resb = (1 - g) * 90
        c.t(px + pw / 2, py + ph + 18, 'tiempo (1 s)', 9.5, TENUE)
        c.t(px + pw / 2, py + ph + 36, f'deslizamiento máximo de la imagen: {resb:g} °/s'.replace('.', ','), 10.5, NARANJA, 'middle', 700)
    c.out.append(f'<text transform="translate(24,{70 + 100}) rotate(-90)" {F} font-size="10" fill="{TINTA}" text-anchor="middle">velocidad (°/s)</text>')
    c.l(70, 340, 94, 340, OI, 2.4); c.t(100, 343, 'cabeza', 9.5, TINTA, 'start')
    c.l(160, 340, 184, 340, VERDE, 2.4); c.t(190, 343, 'ojo (invertido)', 9.5, TINTA, 'start')
    c.r(300, 334, 14, 10, NARANJA, 0.35); c.t(320, 343, 'lo que resbala en la retina = (1 − ganancia) × cabeza', 9.5, TINTA, 'start')
    c.t(700, 366, 'Esquema: 2 ciclos por segundo, pico de 90 °/s (ilustrativo).', 8.5, TENUE, 'end')
    c.guardar('cap24-oscilopsia.svg')


if __name__ == '__main__':
    cociente()
    causas()
    oscilopsia()
