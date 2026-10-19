#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H14 (potenciales de latencia media y tardía):

    h14-mlr.svg          A: morfología de la respuesta de latencia media y ventanas de búsqueda;
                         B: el potencial de 40 Hz como suma de respuestas que se superponen
    h14-corticales.svg   respuesta cortical obligatoria del adulto, del escolar y del lactante
    h14-oddball.svg      secuencia oddball, MMN (onda de diferencia) y P300
    h14-cronologia.svg   de la onda V del ABR a la P300, en una sola linea de tiempo

SVG propios, no IA: son esquemas calculados (sumas de gaussianas centradas en las latencias
de la literatura). Las amplitudes son ilustrativas.
Latencias: Na 18, Pa 30, Nb 40, Pb 50 ms (Matas y cols., 2009); Pa 28, Nb 40, Pb 52 ms (Yvert y cols., 2001);
ventanas de búsqueda de Na/Pa/Nb/Pb (De Oliveira y cols., 2023); P1 50-70, N1 100-130, P2 200-250 ms
del adulto y onda positiva de 150-250 ms del lactante (BSA, 2022); P1 de ~100 ms y N1b de ~200 ms del nino
(Sharma y cols., 1997); MMN 150-250 ms y P300 300-400 ms (Duncan y cols., 2009); onda V del ABR 5-8 ms (Erwin y Buchwald, 1986)."""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO = '#c0571c', '#21796c', '#c62f3a'
AZUL = '#2f5d9e'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}/>')

    def r(self, x, y, w, h, fill, opac=1.0, stroke=None):
        s = f' stroke="{stroke}" stroke-width="1"' if stroke else ''
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
                        f'fill-opacity="{opac}"{s}/>')

    def poli(self, pts, color, w=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}">'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def g(t, mu, sd, a):
    return a * math.exp(-0.5 * ((t - mu) / sd) ** 2)


def eje_tiempo(c, x0, ancho, yb, t0, t1, paso, etiqueta='ms'):
    X = lambda t: x0 + (t - t0) / (t1 - t0) * ancho
    c.l(x0, yb, x0 + ancho, yb, FUERTE, 1)
    t = t0
    while t <= t1 + 1e-9:
        c.l(X(t), yb, X(t), yb + 4, FUERTE, 1)
        c.t(X(t), yb + 16, int(t), 8, TENUE)
        t += paso
    c.t(x0 + ancho / 2, yb + 30, f'tiempo desde el estímulo ({etiqueta})', 8.5, TENUE)
    return X


# ------------------------------------------------------------------ MLR
def mlr_kernel(t):
    # polaridad: positivo hacia arriba (vértice positivo)
    return (g(t, 6, 1.3, 0.35) + g(t, 18, 3.0, -0.55) + g(t, 30, 4.0, 1.0)
            + g(t, 40, 4.0, -0.75) + g(t, 51, 5.0, 0.8))


def mlr():
    c = Lienzo(700, 330)
    # Panel A
    x0, ancho, yc, amp = 40, 320, 130, 62
    c.t(14, 20, 'A · Respuesta de latencia media', 10.5, TINTA, 'start', 700)
    X = eje_tiempo(c, x0, ancho, 258, 0, 100, 20)
    c.l(x0, yc, x0 + ancho, yc, GRILLA, 1)
    ventanas = [('Na', 12, 27), ('Pa', 25, 40), ('Nb', 30, 50), ('Pb', 45, 65)]
    for i, (n, a, b) in enumerate(ventanas):
        y = 188 + i * 12
        c.r(X(a), y, X(b) - X(a), 8, COCLEAR, 0.35)
        c.t(X(a) - 3, y + 7, n, 7.5, TINTA, 'end', 700)
    c.t(x0 + 2, 252, 'ventanas de búsqueda (De Oliveira y cols., 2023)', 7.5, TENUE, 'start')
    pts = [(X(t), yc - amp * mlr_kernel(t)) for t in [i * 0.5 for i in range(0, 201)]]
    c.poli(pts, TINTA, 2)
    for nombre, t, signo, color in [('V', 6, 1, TENUE), ('Na', 18, -1, AZUL), ('Pa', 30, 1, COCLEAR),
                                    ('Nb', 40, -1, AZUL), ('Pb', 51, 1, COCLEAR)]:
        y = yc - amp * mlr_kernel(t)
        dy = -9 if signo > 0 else 15
        c.t(X(t), y + dy, nombre, 9.5, color, 'middle', 700)
        c.l(X(t), yc - amp * mlr_kernel(t) + (-2 if signo > 0 else 2), X(t), yc - amp * mlr_kernel(t) + (-2 if signo > 0 else 2), color, 1)
    c.t(x0 + ancho / 2 + 30, 40, 'positivo hacia arriba (vértice positivo)', 8, TENUE, 'middle')
    c.t(X(6), yc + 26, 'onda V', 7.5, TENUE)
    c.t(X(6), yc + 35, 'del ABR', 7.5, TENUE)

    # Panel B: 40 Hz como superposicion
    bx, bw = 410, 270
    c.t(bx - 10, 20, 'B · Si se repite cada 25 ms: 40 Hz', 10.5, TINTA, 'start', 700)
    XB = eje_tiempo(c, bx, bw, 258, 0, 150, 25)
    ybase, ampb = 140, 62
    c.l(bx, ybase, bx + bw, ybase, GRILLA, 1)
    for k in range(0, 6):
        tk = k * 25
        c.l(XB(tk), 70, XB(tk), 82, RETRO, 1.4)
    c.t(bx + 4, 64, 'estímulos cada 25 ms (40 por segundo)', 8, RETRO, 'start', 600)
    suma = []
    for i in range(0, 301):
        t = i * 0.5
        v = sum(mlr_kernel(t - k * 25) for k in range(0, 6) if t - k * 25 >= 0)
        suma.append((XB(t), ybase - ampb * 0.62 * v))
    c.poli(suma, TINTA, 2)
    c.t(bx + bw / 2, 228, 'las respuestas se encabalgan y forman una onda', 8.5, TINTA, 'middle', 600)
    c.t(bx + bw / 2, 241, 'casi sinusoidal de 40 Hz, estable desde el 3.º-4.º ciclo', 8.5, TINTA, 'middle', 600)
    c.t(14, 318, 'Esquema calculado: la respuesta de A repetida cada 25 ms y sumada. Amplitudes ilustrativas.', 8, TENUE, 'start')
    c.guardar('h14-mlr.svg')


# ------------------------------------------------------------------ corticales
def corticales():
    c = Lienzo(700, 400)
    x0, ancho = 90, 560
    c.t(14, 20, 'Respuesta cortical obligatoria según la edad', 10.5, TINTA, 'start', 700)
    t1 = 500
    X = lambda t: x0 + t / t1 * ancho
    filas = [
        ('Adulto', 80, lambda t: g(t, 60, 12, 0.45) + g(t, 115, 18, -1.0) + g(t, 220, 38, 0.95),
         [('P1', 60, 1), ('N1', 115, -1), ('P2', 220, 1)], TINTA),
        ('Escolar', 195, lambda t: g(t, 100, 22, 1.2) + g(t, 200, 40, -0.9),
         [('P1', 100, 1), ('N1b', 200, -1)], COCLEAR),
        ('Lactante', 300, lambda t: g(t, 80, 22, -0.3) + g(t, 200, 45, 0.8) + g(t, 400, 70, -0.5),
         [('', 80, -1), ('onda positiva', 200, 1), ('negatividad tardía', 400, -1)], RETRO),
    ]
    amp = 30
    for nombre, yc, f, marcas, color in filas:
        c.l(x0, yc, x0 + ancho, yc, GRILLA, 1)
        c.t(x0 - 10, yc + 4, nombre, 10, color, 'end', 700)
        c.poli([(X(t), yc - amp * f(t)) for t in range(0, t1 + 1, 4)], color, 2.2)
        for n, t, s in marcas:
            if not n:
                continue
            y = yc - amp * f(t)
            c.t(X(t), y + (-8 if s > 0 else 14), n, 9, color, 'middle', 700)
    ybase = 345
    c.l(x0, ybase, x0 + ancho, ybase, FUERTE, 1)
    for t in range(0, 501, 100):
        c.l(X(t), ybase, X(t), ybase + 4, FUERTE, 1)
        c.t(X(t), ybase + 16, t, 8, TENUE)
    c.t(x0 + ancho / 2, ybase + 30, 'tiempo desde el estímulo (ms)', 8.5, TENUE)
    c.t(14, 392, 'Esquema calculado con las latencias de la literatura; positivo hacia arriba. Amplitudes ilustrativas.', 8, TENUE, 'start')
    c.guardar('h14-corticales.svg')


# ------------------------------------------------------------------ oddball, MMN y P300
def oddball():
    c = Lienzo(700, 510)
    # A: secuencia
    c.t(14, 20, 'A · Paradigma oddball', 10.5, TINTA, 'start', 700)
    seq = 'EEEEDEEEEEEDEEEEDEEEEEDEEEE'
    x, y0 = 30, 80
    paso = 24.5
    for i, s in enumerate(seq):
        xx = x + i * paso
        if s == 'E':
            c.l(xx, y0, xx, y0 - 20, TENUE, 3)
        else:
            c.l(xx, y0, xx, y0 - 44, COCLEAR, 3)
    c.l(x - 6, y0, x + len(seq) * paso, y0, FUERTE, 1)
    c.t(30, 100, 'estándar (80-90 %)', 8.5, TENUE, 'start', 600)
    c.t(190, 100, 'desviante o blanco (10-20 %)', 8.5, COCLEAR, 'start', 700)
    c.t(400, 100, 'intervalo: 500 ms a 1 s (MMN); 1 a 2 s (P300)', 8.5, TENUE, 'start')
    # B: respuestas a estándar y desviante
    def panel(x0, y0, w, h, titulo, trazas, ventana=None, etq=None, t1=500, yc=None, nota=None):
        c.t(x0 - 8, y0 - 18, titulo, 10.5, TINTA, 'start', 700)
        X = lambda t: x0 + t / t1 * w
        yc = y0 + h / 2 if yc is None else yc
        c.l(x0, yc, x0 + w, yc, GRILLA, 1)
        if ventana:
            c.r(X(ventana[0]), y0, X(ventana[1]) - X(ventana[0]), h, COCLEAR, 0.10)
        for f, color, dash, wd in trazas:
            c.poli([(X(t), yc - 34 * f(t)) for t in range(0, t1 + 1, 4)], color, wd, dash)
        yb = y0 + h
        c.l(x0, yb, x0 + w, yb, FUERTE, 1)
        for t in range(0, t1 + 1, 100):
            c.l(X(t), yb, X(t), yb + 4, FUERTE, 1)
            c.t(X(t), yb + 15, t, 8, TENUE)
        c.t(x0 + w / 2, yb + 28, 'ms', 8.5, TENUE)
        return X, yc

    base = lambda t: g(t, 60, 14, 0.25) + g(t, 105, 18, -0.9) + g(t, 190, 40, 0.6)
    desv = lambda t: base(t) + g(t, 185, 35, -0.55)
    X, yc = panel(40, 150, 290, 110, 'B · Respuestas promediadas',
                  [(base, TENUE, None, 2), (desv, COCLEAR, None, 2)], ventana=(150, 250))
    c.t(X(330), yc - 28, 'estándar', 8.5, TENUE, 'start', 700)
    c.t(X(330), yc + 18, 'desviante', 8.5, COCLEAR, 'start', 700)

    dif = lambda t: desv(t) - base(t)
    X2, yc2 = panel(390, 150, 290, 110, 'C · Desviante − estándar = MMN',
                    [(lambda t: g(t, 185, 35, -0.55) * 1.5, AZUL, None, 2.4)], ventana=(150, 250))
    c.t(X2(185), yc2 + 52, 'MMN', 10, AZUL, 'middle', 700)

    # D: P300 con tarea
    estándar = lambda t: g(t, 60, 14, 0.25) + g(t, 105, 18, -0.8) + g(t, 190, 40, 0.5)
    blanco = lambda t: estándar(t) + g(t, 200, 30, -0.4) + g(t, 350, 55, 1.15)
    X3, yc3 = panel(40, 330, 290, 100, 'D · P300 (el paciente cuenta o responde al blanco)',
                    [(estándar, TENUE, None, 2), (blanco, RETRO, None, 2.4)], ventana=(300, 400), yc=330 + 62)
    c.t(X3(350), 330 + 62 - 34 * 1.55 - 6, 'P300', 10, RETRO, 'middle', 700)
    c.t(X3(430), 330 + 62 + 24, 'estándar', 8.5, TENUE, 'middle', 700)
    c.t(X3(120), 330 + 62 + 38, 'blanco', 8.5, RETRO, 'middle', 700)

    # E: que cambia
    c.t(392, 340, 'E · Qué pide cada una', 10.5, TINTA, 'start', 700)
    lineas = [('MMN', AZUL, 'aparece aunque el paciente ignore los sonidos (mira un video sin audio)'),
              ('P300', RETRO, 'exige que el paciente atienda el blanco y cumpla la tarea'),
              ('Las dos', TINTA, 'dependen de que el cerebro distinga el desviante del estándar')]
    for i, (a, col, tx) in enumerate(lineas):
        yy = 366 + i * 42
        c.t(392, yy, a, 9.5, col, 'start', 700)
        # texto en dos lineas
        palabras = tx.split()
        mid = len(palabras) // 2 + 1
        c.t(392, yy + 12, ' '.join(palabras[:mid]), 8.5, TINTA, 'start')
        c.t(392, yy + 23, ' '.join(palabras[mid:]), 8.5, TINTA, 'start')
    c.t(14, 500, 'Esquema calculado; positivo hacia arriba en B-D. Latencias de Duncan y cols. (2009). Amplitudes ilustrativas.', 8, TENUE, 'start')
    c.guardar('h14-oddball.svg')


# ------------------------------------------------------------------ cronología
def cronologia():
    c = Lienzo(700, 360)
    x0, ancho, t1 = 150, 510, 500
    X = lambda t: x0 + t / t1 * ancho
    c.t(14, 20, 'De la onda V del ABR a la P300', 10.5, TINTA, 'start', 700)
    # tres niveles de exigencia
    NIV = {'dormido': RETRO, 'despierto': COCLEAR, 'tarea': AVISO}
    filas = [
        ('ABR', 0, 10, 'dormido', 'ondas I-V'),
        ('Latencia media', 10, 100, 'despierto', 'Na Pa Nb Pb'),
        ('Corticales P1-N1-P2', 50, 250, 'despierto', 'P1  N1  P2'),
        ('MMN', 150, 250, 'despierto', 'diferencia'),
        ('P300', 300, 400, 'tarea', 'blanco'),
    ]
    yb = 52
    for i, (n, a, b, niv, tx) in enumerate(filas):
        y = yb + i * 40
        c.t(x0 - 10, y + 19, n, 9.5, TINTA, 'end', 700)
        c.l(x0, y + 12, x0 + ancho, y + 12, GRILLA, 1)
        w = max(X(b) - X(a), 5)
        c.r(X(a), y, w, 24, NIV[niv], 0.85)
        if b - a >= 90:
            c.t(X(a) + w / 2, y + 16, tx, 8.5, '#fff', 'middle', 700)
        else:
            c.t(X(b) + 6, y + 16, tx, 8.5, TINTA, 'start')
    ye = yb + 5 * 40 + 6
    c.l(x0, ye, x0 + ancho, ye, FUERTE, 1)
    for t in range(0, 501, 50):
        c.l(X(t), ye, X(t), ye + 4, FUERTE, 1)
        c.t(X(t), ye + 16, t, 8, TENUE)
    c.t(x0 + ancho / 2, ye + 31, 'tiempo desde el estímulo (ms)', 8.5, TENUE)
    # leyenda
    ly = ye + 52
    for i, (k, tx) in enumerate([('dormido', 'se puede registrar dormido'),
                                 ('despierto', 'despierto y quieto, sin tarea'),
                                 ('tarea', 'despierto, atento, con tarea')]):
        lx = [30, 270, 500][i]
        c.r(lx, ly - 9, 12, 12, NIV[k], 0.85)
        c.t(lx + 18, ly + 1, tx, 8.5, TINTA, 'start')
    c.t(14, 352, 'Las barras son las ventanas típicas del adulto; el ABR ocupa los primeros 10 ms (onda V entre 5 y 8 ms).', 8, TENUE, 'start')
    c.guardar('h14-cronologia.svg')


if __name__ == '__main__':
    mlr()
    corticales()
    oddball()
    cronologia()
