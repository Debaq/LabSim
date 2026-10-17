#!/usr/bin/env python3
"""Ilustraciones del capítulo 26 (una tercera ventana). SVG propios, no IA:

    cap26-ventanas.svg     cóclea desenrollada con dos ventanas (oído sano) y con una tercera
    cap26-dehiscencia.svg  la dehiscencia del conducto superior en tres paneles (audiograma,
                           reflejo estapedial y VEMP), construida con cifras de la literatura

LabSim no puede escribir una dehiscencia: su motor recorta la vía ósea en 0 dB y apaga el reflejo
con cualquier gap. Por eso el segundo dibujo NO es un registro del simulador y lo dice en el pie.
Cifras de la literatura (Minor 2005; Zhou 2007; Welgampola 2008): ver el pie de cada panel.
La vía ósea del audiograma es ilustrativa; el gap medio es el de Minor 2005."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h13 import AVISO, COCLEAR, FUERTE, GRILLA, RETRO, TENUE, TINTA, Lienzo, punta  # noqa: E402


def rect(c, x, y, w, h, relleno='none', borde=TINTA, grosor=1.6, r=0):
    c.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
                 f'fill="{relleno}" stroke="{borde}" stroke-width="{grosor}"/>')


def flecha(c, x1, y1, x2, y2, color, w=2, id_='p-a'):
    c.l(x1, y1, x2, y2, color, w, extra=f' marker-end="url(#{id_})"')


def coclea(c, x0, y0, tercera):
    """Cóclea desenrollada: rampa vestibular arriba, timpánica abajo, partición en medio."""
    ancho, alto, mitad = 250, 100, 50
    rect(c, x0, y0, ancho, alto, '#f6f3ee', TINTA, 1.6, 10)
    c.l(x0 + 6, y0 + mitad, x0 + ancho - 26, y0 + mitad, COCLEAR, 3.2)
    c.t(x0 + ancho / 2 - 10, y0 + mitad + 13, 'membrana basilar', 8, COCLEAR, 'middle', 600)
    c.t(x0 + 120, y0 + 14, 'rampa vestibular', 8, TENUE)
    c.t(x0 + 120, y0 + alto - 6, 'rampa timpánica', 8, TENUE)
    # ventana oval (arriba, izq) y ventana redonda (abajo, izq)
    c.l(x0, y0 + 10, x0, y0 + 36, '#f6f3ee', 4)
    c.l(x0, y0 + 64, x0, y0 + 90, '#f6f3ee', 4)
    c.t(x0 - 6, y0 + 8, 'ventana oval', 8, TINTA, 'end', 700)
    c.t(x0 - 6, y0 + 96, 'ventana redonda', 8, TINTA, 'end', 700)
    flecha(c, x0 - 30, y0 + 23, x0 + 14, y0 + 23, TINTA, 2.4)
    flecha(c, x0 + 10, y0 + 77, x0 - 30, y0 + 77, TINTA, 1.4)
    # helicotrema
    c.t(x0 + ancho - 14, y0 + mitad - 6, 'ápex', 8, TENUE, 'middle')
    if tercera:
        c.l(x0 + 150, y0, x0 + 190, y0, '#f6f3ee', 4)
        c.t(x0 + 170, y0 - 8, 'tercera ventana', 9, AVISO, 'middle', 700)
        flecha(c, x0 + 170, y0 + 24, x0 + 170, y0 - 16, AVISO, 2.2, 'p-r')
        flecha(c, x0 + 60, y0 + 30, x0 + 60, y0 + 41, TINTA, 1.4)
        flecha(c, x0 + 60, y0 + 70, x0 + 60, y0 + 59, TINTA, 1.4)
    else:
        flecha(c, x0 + 60, y0 + 24, x0 + 60, y0 + 42, TINTA, 2.6)
        flecha(c, x0 + 60, y0 + 76, x0 + 60, y0 + 58, TINTA, 2.6)


def ventanas():
    c = Lienzo(700, 330)
    c.t(14, 20, 'Una cóclea con dos ventanas y con tres (cóclea desenrollada)', 10.5, TINTA, 'start', 700)
    coclea(c, 90, 76, False)
    coclea(c, 420, 76, True)
    c.t(215, 50, 'A · Oído sano', 9.5, TINTA, 'middle', 700)
    c.t(545, 50, 'B · Con una tercera ventana', 9.5, TINTA, 'middle', 700)
    c.t(215, 202, 'La presión que entra por la ventana oval', 8.5, TINTA)
    c.t(215, 214, 'sale por la redonda y, en el camino,', 8.5, TINTA)
    c.t(215, 226, 'mueve la membrana basilar con toda su fuerza.', 8.5, TINTA)
    c.t(545, 202, 'Parte de la presión se escapa por el tercer orificio:', 8.5, TINTA)
    c.t(545, 214, 'llega menos a la membrana basilar por vía aérea', 8.5, TINTA)
    c.t(545, 226, '(la aérea empeora), y por vía ósea se oye mejor.', 8.5, TINTA)
    c.l(14, 244, 686, 244, GRILLA, 1)
    c.t(14, 262, 'Lo que sigue por la ventana de arriba: el vestíbulo comparte líquido con la cóclea, así que el tercer orificio', 8.5, TINTA, 'start')
    c.t(14, 275, 'también deja que el sonido y la presión muevan la endolinfa de los conductos y del sáculo (Tullio, Hennebert, VEMP).', 8.5, TINTA, 'start')
    c.t(14, 318, 'Mecánica de la tercera ventana: Merchant y Rosowski (2008).', 8, TENUE, 'start')
    c.guardar('cap26-ventanas.svg', punta('p-a', TINTA) + punta('p-r', AVISO))


def dehiscencia():
    c = Lienzo(700, 420)
    c.t(14, 20, 'Dehiscencia del conducto superior derecho', 10.5, TINTA, 'start', 700)
    # ---- Panel 1: audiograma (OD)
    x0, y0, ancho, alto = 62, 84, 215, 200
    frs = [250, 500, 1000, 2000, 4000]
    X = lambda i: x0 + 22 + i * (ancho - 44) / 4
    dmin, dmax = -20, 40
    Y = lambda db: y0 + (db - dmin) / (dmax - dmin) * alto
    c.t(x0 - 40, y0 - 38, '1 · Audiograma', 10, TINTA, 'start', 700)
    for db in range(-20, 41, 10):
        c.l(x0, Y(db), x0 + ancho, Y(db), GRILLA if db else FUERTE, 0.8 if db else 1.4)
        c.t(x0 - 6, Y(db) + 3, db, 8, TENUE, 'end')
    for i, f in enumerate(frs):
        c.t(X(i), y0 - 10, f, 8, TENUE)
    c.t(x0 - 6, y0 - 10, 'dB HL', 8, TENUE, 'end')
    gap = [19, 15, 11, 4, 0]           # Minor 2005, media, 250 / 500 / 1000 / 2000 Hz
    osea = [-10, -5, 0, 5, 5]         # ilustrativa: 60 % tenía ósea mejor que 0 dB en 250 o 500 (Zhou 2007)
    aerea = [o + g for o, g in zip(osea, gap)]
    c.poli([(X(i), Y(aerea[i])) for i in range(5)], AVISO, 1.8)
    c.poli([(X(i) - 10, Y(osea[i])) for i in range(5)], AVISO, 1.1, '3 3')
    for i in range(5):
        c.out.append(f'<circle cx="{X(i):.1f}" cy="{Y(aerea[i]):.1f}" r="4.5" fill="#fff" stroke="{AVISO}" stroke-width="1.8"/>')
        xb, yb = X(i) - 10, Y(osea[i])
        c.out.append(f'<path d="M{xb + 4:.1f},{yb - 5:.1f} L{xb - 2:.1f},{yb - 5:.1f} L{xb - 2:.1f},{yb + 5:.1f} L{xb + 4:.1f},{yb + 5:.1f}" '
                     f'fill="none" stroke="{AVISO}" stroke-width="1.8"/>')
    c.t(X(0) + 6, Y(-10) - 12, 'ósea bajo 0', 8, AVISO, 'start', 700)
    c.t(X(0) + 2, Y(aerea[0]) + 22, 'gap 19 dB', 8, TINTA, 'start', 700)
    c.t(x0 + ancho / 2, y0 + alto + 16, 'frecuencia (Hz)', 8, TENUE)
    c.t(x0 - 40, y0 + alto + 38, 'Gap medio de Minor (2005): 19, 15, 11 y 4 dB', 8, TENUE, 'start')
    c.t(x0 - 40, y0 + alto + 50, 'en 250 a 2.000 Hz. Ósea bajo 0 dB HL', 8, TENUE, 'start')
    c.t(x0 - 40, y0 + alto + 62, 'en 250 o 500 Hz en el 60 % de los oídos', 8, TENUE, 'start')
    c.t(x0 - 40, y0 + alto + 74, '(Zhou y cols., 2007).', 8, TENUE, 'start')
    # ---- Panel 2: reflejo
    px = 318
    c.t(px, y0 - 38, '2 · Reflejo estapedial', 10, TINTA, 'start', 700)
    rect(c, px, y0 + 6, 128, 58, '#fff', RETRO, 1.6, 6)
    c.t(px + 64, y0 + 32, 'PRESENTE', 12, RETRO, 'middle', 700)
    c.t(px + 64, y0 + 49, 'con gap y timpanograma A', 7.5, TINTA)
    c.t(px, y0 + 90, 'En 89 % de los oídos con', 8.5, TINTA, 'start')
    c.t(px, y0 + 102, 'dehiscencia el reflejo estaba', 8.5, TINTA, 'start')
    c.t(px, y0 + 114, 'presente (Zhou y cols., 2007).', 8.5, TINTA, 'start')
    c.t(px, y0 + 138, 'En la otoesclerosis, con un', 8.5, TENUE, 'start')
    c.t(px, y0 + 150, 'gap así, el reflejo suele', 8.5, TENUE, 'start')
    c.t(px, y0 + 162, 'faltar (cap. 4 y H7).', 8.5, TENUE, 'start')
    # ---- Panel 3: VEMP
    vx = 470
    c.t(vx, y0 - 38, '3 · cVEMP: umbral', 10, TINTA, 'start', 700)
    ax0, ax1 = vx + 8, vx + 205
    Vx = lambda db: ax0 + (db - 60) / (110 - 60) * (ax1 - ax0)
    ybase = y0 + 88
    c.l(ax0, ybase, ax1, ybase, FUERTE, 1)
    for db in range(60, 111, 10):
        c.l(Vx(db), ybase, Vx(db), ybase + 4, FUERTE, 1)
        c.t(Vx(db), ybase + 15, db, 8, TENUE)
    c.t((ax0 + ax1) / 2, ybase + 28, 'umbral (dB nHL)', 8, TENUE)
    filas = [('oído con dehiscencia', 81, 9, AVISO, y0 + 12), ('oído sano del mismo paciente', 99, 7, RETRO, y0 + 40),
             ('controles', 98, 4, TENUE, y0 + 68)]
    for nombre, media, de, col, yy in filas:
        c.l(Vx(media - de), yy, Vx(media + de), yy, col, 1.6)
        c.l(Vx(media - de), yy - 4, Vx(media - de), yy + 4, col, 1.6)
        c.l(Vx(media + de), yy - 4, Vx(media + de), yy + 4, col, 1.6)
        c.out.append(f'<circle cx="{Vx(media):.1f}" cy="{yy:.1f}" r="4.5" fill="{col}"/>')
        c.t(ax0, yy - 8, f'{nombre}: {media} ± {de}', 8, TINTA, 'start', 600)
    c.t(vx, y0 + 138, 'Barras: media ± 1 DE (Minor, 2005).', 8.5, TINTA, 'start')
    c.t(vx, y0 + 150, 'La amplitud, además, sale grande.', 8.5, TINTA, 'start')
    c.t(vx, y0 + 162, 'Equipos distintos, umbrales distintos:', 8.5, TENUE, 'start')
    c.t(vx, y0 + 174, 'cada servicio necesita su normativa.', 8.5, TENUE, 'start')
    # ---- Trazas esquemáticas (forma, sin escala)
    ty = y0 + 205
    c.t(vx, ty - 6, 'Forma de la respuesta:', 8, TENUE, 'start')
    for k, (amp, col, nom) in enumerate([(14, RETRO, 'normal'), (38, AVISO, 'dehiscencia')]):
        bx = vx + k * 108
        c.l(bx, ty + 40, bx + 95, ty + 40, GRILLA, 1)
        pts = []
        for j in range(96):
            u = j / 95
            v = amp * (math.exp(-((u - .26) / .09) ** 2) - 1.25 * math.exp(-((u - .46) / .11) ** 2))
            pts.append((bx + j, ty + 40 - v))
        c.poli(pts, col, 1.8)
        c.t(bx + 47, ty + 100, nom, 8, col, 'middle', 700)
    c.t(14, 410, 'Cifras: Minor (2005), 65 pacientes; Zhou y cols. (2007), 26 con dehiscencia. En LabSim el motor recorta la ósea en 0 dB y apaga el reflejo con gap.', 7.5, TENUE, 'start')
    c.guardar('cap26-dehiscencia.svg', punta('p-a', TINTA))


if __name__ == '__main__':
    ventanas()
    dehiscencia()
