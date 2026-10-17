#!/usr/bin/env python3
"""Ilustración del capítulo 9 (hidrops). SVG propio, no IA:

    cap09-hidrops.svg  corte de una espira de la cóclea, normal y con hidrops

Esquema, no a escala. La rampa media distendida, con la membrana de Reissner abombada hacia la
rampa vestibular, es el hallazgo histológico del hidrops (Hallpike y Cairns, 1938; Merchant y
cols., 2005). El leve desplazamiento de la membrana basilar hacia la rampa timpánica sigue al texto
del capítulo (Salt y Plontke, 2010), que lo marca como `verificar`."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h13 import AVISO, COCLEAR, GRILLA, TENUE, TINTA, Lienzo  # noqa: E402

PERI = '#f6efe2'      # perilinfa
ENDO = '#cfe2f3'      # endolinfa
HUESO = '#b9b2a6'
ESTRIA = '#c0504d'
R = 112               # radio del contorno óseo de la espira


def en_circulo(cx, cy, grados, r=R):
    a = math.radians(grados)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def espira(c, cx, cy, hidrops):
    """Una espira en corte: modiolo a la izquierda, pared lateral a la derecha."""
    # contorno óseo lleno de perilinfa
    c.out.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{PERI}" stroke="{HUESO}" stroke-width="9"/>')

    limbo = (cx - 30, cy - 4)                   # donde nace la Reissner
    base = (cx - 30, cy + 4)                    # donde nace la basilar (fin de la lámina ósea)
    reissner_fin = en_circulo(cx, cy, -48, R - 4)
    basilar_fin = en_circulo(cx, cy, 6, R - 4)

    if hidrops:
        # Reissner abombada hacia arriba y a la izquierda (hacia la rampa vestibular)
        ctrl_r = (cx - 40, cy - 125)
        # basilar levemente combada hacia abajo (rampa timpánica)
        ctrl_b = (cx + 34, cy + 26)
    else:
        ctrl_r = ((limbo[0] + reissner_fin[0]) / 2, (limbo[1] + reissner_fin[1]) / 2)
        ctrl_b = ((base[0] + basilar_fin[0]) / 2, (base[1] + basilar_fin[1]) / 2)

    # rampa media (endolinfa): Reissner, pared lateral (arco), basilar de vuelta
    d = (f'M{limbo[0]:.1f},{limbo[1]:.1f} Q{ctrl_r[0]:.1f},{ctrl_r[1]:.1f} {reissner_fin[0]:.1f},{reissner_fin[1]:.1f} '
         f'A{R - 4},{R - 4} 0 0 1 {basilar_fin[0]:.1f},{basilar_fin[1]:.1f} '
         f'Q{ctrl_b[0]:.1f},{ctrl_b[1]:.1f} {base[0]:.1f},{base[1]:.1f} Z')
    c.out.append(f'<path d="{d}" fill="{ENDO}" stroke="none"/>')

    # estría vascular: franja sobre la pared lateral de la rampa media
    e1, e2 = en_circulo(cx, cy, -40, R - 8), en_circulo(cx, cy, -2, R - 8)
    c.out.append(f'<path d="M{e1[0]:.1f},{e1[1]:.1f} A{R - 8},{R - 8} 0 0 1 {e2[0]:.1f},{e2[1]:.1f}" '
                 f'fill="none" stroke="{ESTRIA}" stroke-width="7" stroke-linecap="round"/>')

    # membrana de Reissner y membrana basilar
    c.out.append(f'<path d="M{limbo[0]:.1f},{limbo[1]:.1f} Q{ctrl_r[0]:.1f},{ctrl_r[1]:.1f} '
                 f'{reissner_fin[0]:.1f},{reissner_fin[1]:.1f}" fill="none" stroke="{TINTA}" stroke-width="1.8"/>')
    c.out.append(f'<path d="M{base[0]:.1f},{base[1]:.1f} Q{ctrl_b[0]:.1f},{ctrl_b[1]:.1f} '
                 f'{basilar_fin[0]:.1f},{basilar_fin[1]:.1f}" fill="none" stroke="{COCLEAR}" stroke-width="3.2"/>')

    # lámina espiral ósea y limbo (desde el modiolo)
    c.out.append(f'<path d="M{cx - R:.1f},{cy - 7} L{cx - 30},{cy - 7} L{cx - 30},{cy + 7} L{cx - R:.1f},{cy + 7} Z" '
                 f'fill="{HUESO}" stroke="none"/>')

    # órgano de Corti sobre la basilar (punto medio de la curva) y membrana tectoria
    t = 0.42
    mx = (1 - t) ** 2 * base[0] + 2 * (1 - t) * t * ctrl_b[0] + t ** 2 * basilar_fin[0]
    my = (1 - t) ** 2 * base[1] + 2 * (1 - t) * t * ctrl_b[1] + t ** 2 * basilar_fin[1]
    c.out.append(f'<path d="M{mx - 17:.1f},{my - 1:.1f} Q{mx - 6:.1f},{my - 19:.1f} {mx + 4:.1f},{my - 16:.1f} '
                 f'Q{mx + 15:.1f},{my - 12:.1f} {mx + 19:.1f},{my:.1f} Z" fill="#e9c46a" stroke="{TINTA}" stroke-width="0.8"/>')
    c.out.append(f'<path d="M{cx - 30},{cy - 9} Q{mx - 18:.1f},{my - 30:.1f} {mx + 8:.1f},{my - 20:.1f}" '
                 f'fill="none" stroke="{TENUE}" stroke-width="2.4"/>')
    return reissner_fin, (mx, my), ctrl_r, ctrl_b


def rotulo(c, x, y, xa, ya, texto, color=TINTA, anchor='start', peso=600):
    """Texto en (x, y) con una línea corta hasta el punto (xa, ya) de la estructura."""
    c.l(xa, ya, x + (2 if anchor == 'start' else -2), y - 3, color, 0.8)
    c.t(x, y, texto, 8.2, color, anchor, peso)


def hidrops():
    c = Lienzo(720, 372)
    c.t(14, 20, 'Corte de una espira de la cóclea', 10.5, TINTA, 'start', 700)
    cy = 190
    for cx, titulo, h in ((190, 'A · Normal', False), (540, 'B · Hidrops endolinfático', True)):
        c.t(cx, 46, titulo, 9.5, TINTA, 'middle', 700)
        espira(c, cx, cy, h)
        if h:   # la rampa vestibular queda a la izquierda del abombamiento
            for k, s in enumerate(('rampa', 'vestibular')):
                c.t(cx - 68, cy - 52 + 10 * k, s, 8, TENUE, 'middle', 600)
            c.t(cx - 68, cy - 32, '(perilinfa)', 7.5, TENUE, 'middle')
            xm, ym = cx + 34, cy - 40
        else:
            c.t(cx - 4, cy - 66, 'rampa vestibular', 8, TENUE, 'middle', 600)
            c.t(cx - 4, cy - 56, '(perilinfa)', 7.5, TENUE, 'middle')
            xm, ym = cx + 58, cy - 34
        c.t(xm, ym, 'rampa media', 8, '#2f5d8a', 'middle', 700)
        c.t(xm, ym + 10, '(endolinfa)', 7.5, '#2f5d8a', 'middle')
        c.t(cx - 22, cy + 70, 'rampa timpánica', 8, TENUE, 'middle', 600)
        c.t(cx - 22, cy + 80, '(perilinfa)', 7.5, TENUE, 'middle')
        c.t(cx - R - 8, cy + 3, 'modiolo', 7.5, TENUE, 'end')
        c.t(cx - 56, cy + 20, 'lámina espiral ósea', 7.2, TENUE, 'middle')
    # panel A: rótulos en el espacio entre los dos cortes
    cx = 190
    rotulo(c, 314, 124, cx + 24, cy - 44, 'membrana de Reissner')
    rotulo(c, 314, 152, cx + R - 14, cy - 40, 'estría vascular', ESTRIA)
    rotulo(c, 314, 214, cx + 78, cy + 8, 'membrana basilar', COCLEAR)
    rotulo(c, 314, 240, cx + 4, cy - 2, 'órgano de Corti')
    # panel B: lo que cambia
    cx = 540
    c.t(cx - 112, 68, 'Reissner abombada hacia la rampa vestibular', 8.2, AVISO, 'start', 700)
    c.l(cx - 8, 72, cx - 8, cy - 82, AVISO, 0.8)
    c.t(cx - 112, 322, 'basilar algo desplazada hacia la rampa timpánica', 8.2, AVISO, 'start', 700)
    c.l(cx + 44, 312, cx + 44, cy + 16, AVISO, 0.8)
    c.l(14, 340, 706, 340, GRILLA, 1)
    c.t(14, 356, 'En el hidrops crece el volumen de endolinfa: la rampa media se agranda a costa de la vestibular.', 7.8, TENUE, 'start')
    c.t(14, 367, 'Hallazgo histológico descrito por Hallpike y Cairns (1938).', 7.8, TENUE, 'start')
    c.guardar('cap09-hidrops.svg')


if __name__ == '__main__':
    hidrops()
