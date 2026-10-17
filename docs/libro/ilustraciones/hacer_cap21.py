#!/usr/bin/env python3
"""Dibuja las ilustraciones del cap. 21 (vértigo agudo):

    cap21-ficha-neuritis.svg, cap21-ficha-laberintitis.svg, cap21-ficha-pseudoneuritis.svg,
    cap21-ficha-aica.svg     la "hoja de cabecera" de cada caso: nistagmo sin fijación en tres
                             miradas, impulso cefálico a cada lado y prueba de oclusión alternada
    cap21-compensacion.svg   qué se recupera y qué se compensa con los días (esquema cualitativo)

Las cifras de las fichas son las de los pacientes inventados del capítulo (velocidad de fase lenta,
ganancia del impulso), no normas ni datos de pacientes reales. Las trazas del impulso salen del mismo
generador sintético de hacer_h17.py (cabeza gaussiana de 200 °/s, ojo = ganancia x cabeza + sacada).
El nistagmo es un diente de sierra a 2 Hz: lo único que cambia entre casos es la velocidad de la fase
lenta y el sentido de la fase rápida en cada mirada.  Uso:  python3 hacer_cap21.py"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h17 import (AVISO, CABEZA, FUERTE, OJO, OK, TENUE, TINTA, Ejes,  # noqa: E402
                       Lienzo, cabeza, ojo)

FREC = 2.0          # Hz: batidas por segundo del dibujo
VENTANA = 3.0       # s


def pos_nistagmo(t, v):
    """Posición horizontal (grados, + = derecha) de un nistagmo de velocidad de fase lenta |v| cuya
    fase rápida va hacia el lado de v (v>0 bate a la derecha: la fase lenta va hacia la izquierda)."""
    if v == 0:
        return 0.0
    T = 1.0 / FREC
    fase = t % T
    d = 1 if v > 0 else -1
    return d * (abs(v) * T * 0.5 - abs(v) * fase)


# spv: por mirada [izquierda, frente, derecha]; signo = lado hacia el que bate la fase rápida
CASOS = {
    'neuritis': dict(spv=(-9, -6, -3), g=(0.38, 0.96), skew=None, hit='anormal a la derecha',
                     nis='unidireccional, bate a la izquierda', verde=(True, True, True)),
    'laberintitis': dict(spv=(-10, -7, -4), g=(0.30, 0.98), skew=None, hit='anormal a la derecha',
                         nis='unidireccional, bate a la izquierda', verde=(True, True, True)),
    'pseudoneuritis': dict(spv=(-8, 0, 8), g=(0.98, 1.02), skew='derecho', hit='normal',
                           nis='cambia de sentido con la mirada', verde=(False, False, False)),
    'aica': dict(spv=(3, 5, 8), g=(0.97, 0.45), skew='izquierdo', hit='anormal a la izquierda',
                 nis='unidireccional, bate a la derecha', verde=(True, True, False)),
}


def ficha(nombre, d):
    c = Lienzo(740, 335)
    # --- A: nistagmo
    c.t(16, 20, 'A · Nistagmo sin fijación', 10, TINTA, 'start', 700)
    c.t(16, 33, 'posición horizontal del ojo, 3 s', 8, TENUE, 'start')
    etiquetas = ['mirada a la izquierda', 'mirada al frente', 'mirada a la derecha']
    for k, v in enumerate(d['spv']):
        e = Ejes(c, 16, 62 + k * 68, 215, 46, 0, VENTANA, -5.5, 5.5)
        c.l(e.px, e.Y(0), e.px + e.w, e.Y(0), FUERTE, 1, '3 3')
        n = 300
        pts = [(e.X(VENTANA * i / n), e.Y(pos_nistagmo(VENTANA * i / n, v))) for i in range(n + 1)]
        c.poli(pts, OJO if v else TENUE, 1.6)
        c.t(e.px, e.py - 14, etiquetas[k], 8, TINTA, 'start', 600)
        if v == 0:
            txt, col = 'sin nistagmo', TENUE
        else:
            txt = ('◄ bate a la izquierda' if v < 0 else 'bate a la derecha ►') + f' · {abs(v)} °/s'
            col = TINTA
        c.t(e.px, e.py - 3, txt, 8, col, 'start')
    c.l(16, 268, 16 + 71.7, 268, TENUE, 1)   # barra de 1 s (215 px = 3 s)
    c.t(52, 280, '1 s', 8, TENUE)
    # --- B: impulso cefálico
    c.t(262, 20, 'B · Impulso cefálico horizontal', 10, TINTA, 'start', 700)
    c.t(262, 33, 'cabeza (azul) y ojo invertido (naranja), °/s', 8, TENUE, 'start')
    for k, (lado, g) in enumerate((('a la derecha', d['g'][0]), ('a la izquierda', d['g'][1]))):
        e = Ejes(c, 272, 74 + k * 98, 150, 56, 0, 400, 0, 330)
        e.marco([0, 200, 400], [0, 200], 'ms' if k else '', None)
        e.curva(cabeza, CABEZA, 1.8, 400)
        e.curva(lambda t, g=g: ojo(t, g, 'manifiesta' if g < 0.8 else None), OJO, 1.8, 800)
        c.t(e.px, e.py - 15, f'impulso {lado}', 8, TINTA, 'start', 600)
        malo = g < 0.8
        c.t(e.px, e.py - 4, f'ganancia {g:.2f}'.replace('.', ','), 8.5, AVISO if malo else OK, 'start', 700)
        if malo:
            c.t(e.X(300), e.Y(150), 'sacada', 7.5, AVISO, 'start', 700)
    # --- C: oclusión alternada
    c.t(476, 20, 'C · Oclusión alternada', 10, TINTA, 'start', 700)
    c.t(476, 33, 'los dos ojos, tras destapar uno', 8, TENUE, 'start')
    sk = d['skew']
    for xc, lado in ((525, 'derecho'), (625, 'izquierdo')):
        yc = 110 + (11 if sk == lado else 0)
        c.out.append(f'<ellipse cx="{xc}" cy="{yc}" rx="30" ry="16" fill="#fff" stroke="{TINTA}" stroke-width="1.4"/>')
        c.out.append(f'<circle cx="{xc}" cy="{yc}" r="9.5" fill="{TINTA}"/>')
        c.t(xc, 148, 'ojo ' + lado, 8, TENUE)
    if sk:
        c.t(575, 178, f'el ojo {sk} queda más bajo y sube', 8, AVISO, 'middle', 700)
        c.t(575, 190, 'a re-fijar al destaparlo: skew presente', 8, AVISO, 'middle', 700)
    else:
        c.t(575, 178, 'los ojos no se mueven en vertical', 8, OK, 'middle', 700)
        c.t(575, 190, 'al destapar: skew ausente', 8, OK, 'middle', 700)
    # --- D: veredicto HINTS
    c.t(262, 266, 'HINTS', 10, TINTA, 'start', 700)
    chips = [('Impulso', d['hit'], d['verde'][0]), ('Nistagmo', d['nis'], d['verde'][1]),
             ('Skew', 'presente' if sk else 'ausente', d['verde'][2])]
    x0 = 262
    for (t1, t2, periferico), w in zip(chips, (165, 215, 90)):
        col = OK if periferico else AVISO
        c.out.append(f'<rect x="{x0}" y="274" width="{w - 6}" height="40" rx="6" fill="#fff" stroke="{col}" stroke-width="1.6"/>')
        c.t(x0 + (w - 6) / 2, 288, t1, 8.5, TENUE)
        c.t(x0 + (w - 6) / 2, 304, t2, 8.5, col, 'middle', 700)
        x0 += w
    c.t(262, 328, 'Verde: lo que se espera de una lesión periférica. Rojo: signo central. Cifras de los pacientes inventados.',
        7.5, TENUE, 'start')
    c.guardar(f'cap21-ficha-{nombre}.svg')


def compensacion():
    c = Lienzo(720, 300)
    c.t(14, 20, 'Qué cambia con el tiempo tras una pérdida vestibular unilateral aguda', 10.5, TINTA, 'start', 700)
    px, py, w, h = 70, 50, 620, 170
    c.l(px, py + h, px + w, py + h, FUERTE, 1)
    c.l(px, py, px, py + h, FUERTE, 1)
    for f, txt in ((0.0, 'inicio'), (0.17, 'días'), (0.42, 'semanas'), (0.72, 'meses')):
        x = px + f * w
        c.l(x, py + h, x, py + h + 4, TENUE, 1)
        c.t(x, py + h + 16, txt, 8.5, TENUE)
    c.t(px - 8, py + 8, 'más', 8, TENUE, 'end')
    c.t(px - 8, py + h, 'menos', 8, TENUE, 'end')
    fs = [i / 100 for i in range(101)]

    def X(f):
        return px + f * w

    def Y(v):
        return py + h - v * h
    # vértigo y nistagmo: caen en días
    c.poli([(X(f), Y(0.92 * math.exp(-f / 0.07) + 0.03)) for f in fs], AVISO, 2.4)
    c.t(X(0.36), Y(0.17), 'vértigo y nistagmo espontáneo', 8.5, AVISO, 'start', 700)
    c.t(X(0.36), Y(0.17) + 11, '(los núcleos y el cerebelo igualan los reposos)', 8, AVISO, 'start')
    # ganancia del impulso del lado enfermo: banda variable
    abajo = [(X(f), Y(0.18 + 0.22 * (1 - math.exp(-f / 0.35)))) for f in fs]
    arriba = [(X(f), Y(0.18 + 0.62 * (1 - math.exp(-f / 0.35)))) for f in fs]
    c.area(arriba + abajo[::-1], CABEZA, 0.16)
    c.poli(abajo, CABEZA, 1.4, '4 3')
    c.poli(arriba, CABEZA, 1.4, '4 3')
    c.t(X(0.5), Y(0.5), 'ganancia del impulso del lado enfermo:', 8.5, CABEZA, 'start', 700)
    c.t(X(0.5), Y(0.5) + 11, 'se recupera de forma variable', 8.5, CABEZA, 'start', 700)
    # equilibrio en la vida diaria
    ys = [0.12 + 0.76 * (1 - math.exp(-f / 0.22)) for f in fs]
    c.poli([(X(f), Y(y)) for f, y in zip(fs, ys)], OK, 2.4)
    c.t(X(1.0), Y(0.99), 'equilibrio en la vida diaria (compensación central)', 8.5, OK, 'end', 700)
    c.t(14, 280, 'Esquema cualitativo, sin cifras: importa la forma de las curvas. La compensación central y la '
        'recuperación del laberinto son procesos distintos.', 7.5, TENUE, 'start')
    c.guardar('cap21-compensacion.svg')


if __name__ == '__main__':
    for n, d in CASOS.items():
        ficha(n, d)
    compensacion()
