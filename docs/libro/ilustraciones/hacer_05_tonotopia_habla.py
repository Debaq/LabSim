#!/usr/bin/env python3
"""Dibuja ilustraciones/05-tonotopia-habla.svg (cap. 5): la cóclea
desenrollada de H3 (h03-tonotopia.svg, misma función de Greenwood) con los
sonidos del habla encima, y la base sombreada como la zona que la edad daña
primero. SVG propio, no IA.

Bandas de los sonidos del habla: aproximadas, las de la "banana" del habla
de los textos de audiología (voz y vocales en graves y medios; s, f, ch y t
en agudos). Son rangos de energía principal, no límites exactos.

    python3 docs/libro/ilustraciones/hacer_05_tonotopia_habla.py
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h03_fundamento import AZUL, OD, OSEA, TENUE, TINTA, VERDE, Lienzo, desde_base  # noqa: E402

GRAVE, AGUDO = '#6a4fb3', '#c62f3a'

# (texto, f_min, f_max, color, fila): fila 0 arriba, 1 abajo
SONIDOS = [
    ('voz', 100, 250, GRAVE, 0),
    ('m · n', 250, 500, GRAVE, 1),
    ('a · o · u', 300, 1000, GRAVE, 0),
    ('e · i', 1500, 2500, GRAVE, 2),
    ('t · k', 2000, 4000, AGUDO, 0),
    ('ch', 2000, 4000, AGUDO, 1),
    ('f', 4000, 8000, AGUDO, 0),
    ('s', 4000, 8000, AGUDO, 1),
]


def tonotopia_habla():
    c = Lienzo(680, 262)
    x0, x1, ym = 40, 640, 162
    X = lambda frac: x0 + frac * (x1 - x0)
    # base sombreada: lo que la edad daña primero (de la base hasta ~2 kHz)
    xb = X(desde_base(2000))
    c.raw(f'<defs><linearGradient id="edad" x1="0" x2="1"><stop offset="0" stop-color="{OD}" stop-opacity=".30"/>'
          f'<stop offset="1" stop-color="{OD}" stop-opacity="0"/></linearGradient></defs>')
    c.raw(f'<rect x="{x0}" y="{ym - 112}" width="{xb - x0:.1f}" height="170" fill="url(#edad)"/>')
    c.t(x0 + 4, ym + 72, 'con la edad se pierde primero la base: s, f, ch, t', 7.8, OD, 'start', 700)
    # membrana basilar (igual que H3.4)
    c.raw(f'<polygon points="{x0},{ym - 6} {x1},{ym - 20} {x1},{ym + 20} {x0},{ym + 6}" fill="#fbf3e6" '
          f'stroke="{OSEA}" stroke-width="1.2"/>')
    for f, s in ((8000, '8k'), (4000, '4k'), (2000, '2k'), (1000, '1k'), (500, '500'), (250, '250'), (125, '125')):
        x = X(desde_base(f))
        c.linea(x, ym - 22, x, ym + 22, TINTA, 0.9)
        c.t(x, ym + 36, s, 8, TINTA, 'middle', 700)
    c.t(x0, ym + 36, 'BASE', 7.5, TENUE, 'start', 700)
    c.t(x1, ym + 36, 'ÁPICE', 7.5, TENUE, 'end', 700)
    # sonidos del habla: barras sobre la membrana
    for texto, fa, fb, col, fila in SONIDOS:
        xa, xz = X(desde_base(fb)), X(desde_base(fa))
        y = ym - 40 - fila * 26
        c.raw(f'<rect x="{xa:.1f}" y="{y - 7:.1f}" width="{max(xz - xa, 8):.1f}" height="14" rx="7" '
              f'fill="{col}" opacity=".16"/>')
        c.t((xa + xz) / 2, y + 3.6, texto, 8.6, col, 'middle', 700)
    c.t(x1, ym - 92 + 8, 'vocales y voz: graves y medios', 7.6, GRAVE, 'end', 700)
    c.t(14, 18, 'Dónde caen los sonidos del habla en la cóclea', 10.5, TINTA, 'start', 700)
    c.t(14, 35, 'Cóclea desenrollada como en la figura H3.4 (Greenwood, 1990). Bandas de energía principal, '
        'aproximadas.', 7.5, TENUE, 'start')
    c.guardar('05-tonotopia-habla.svg')


if __name__ == '__main__':
    tonotopia_habla()
