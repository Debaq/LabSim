#!/usr/bin/env python3
"""Esquemas de la herramienta H2 (acumetría). SVG propios, no IA:

    h02-weber-conductivo.svg  por qué el Weber se va al oído con pérdida conductiva:
                              A, dos oídos sanos; B, el conducto derecho tapado

El oído tapado oye mejor el diapasón por dos razones: no le entra el ruido ambiente, que al oído
abierto lo enmascara un poco, y el efecto de oclusión (la pared del conducto vibra con el cráneo y su
sonido, encerrado, empuja el tímpano).

Corte frontal de la cabeza, mirada de frente al paciente: el OD queda a la izquierda del dibujo.
Esquema, no a escala. La explicación (oclusión y ruido ambiente) es la clásica que da el capítulo, marcada allí como `verificar`.

`cabeza_frontal` la usa también hacer_h04_esquemas.py."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h13 import COCLEAR, GRILLA, TENUE, TINTA, Lienzo, punta  # noqa: E402,F401

OD, OI = '#c62f3a', '#2c5cb0'
OD_CLARO, OI_CLARO = '#f7dfe1', '#dfe7f6'
TINTA_2 = '#55555b'
PIEL = '#fbf6f1'
HUESO = '#d9d1c3'
HUESO_CLARO = '#ece6db'
CEREBRO = '#f6f4f1'
TAPON = '#a8793a'


def camino(c, d, relleno='none', borde=TINTA_2, grosor=1.4, extra=''):
    c.out.append(f'<path d="{d}" fill="{relleno}" stroke="{borde}" stroke-width="{grosor}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{extra}/>')


def rect(c, x, y, w, h, relleno='none', borde=TINTA_2, grosor=1.2, r=0):
    c.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
                 f'fill="{relleno}" stroke="{borde}" stroke-width="{grosor}"/>')


def flecha(c, d, color, grosor, id_, dash=None):
    """Flecha por un camino SVG con punta `id_` (definida en las defs del lienzo)."""
    extra = f' marker-end="url(#{id_})"' + (f' stroke-dasharray="{dash}"' if dash else '')
    camino(c, d, 'none', color, grosor, extra)


def onda(c, x0, y0, x1, y1, color, grosor=1.3, id_=None, amp=2.6, ciclos=3):
    """Línea ondulada de (x0, y0) a (x1, y1), con punta al final si se da `id_`."""
    largo = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / largo, (y1 - y0) / largo
    pts = []
    n = 60
    for i in range(n + 1):
        u = i / n
        a = amp * math.sin(2 * math.pi * ciclos * u) * (1 - u ** 4)
        pts.append((x0 + ux * largo * u - uy * a, y0 + uy * largo * u + ux * a))
    d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    camino(c, d, 'none', color, grosor, f' marker-end="url(#{id_})"' if id_ else '')


def pared_vibrando(c, xa, xb, y):
    """Las dos paredes del conducto, entre xa y xb, dibujadas vibrando."""
    x0, x1 = min(xa, xb), max(xa, xb)
    for yp, sg in ((y - 5, -1), (y + 5, 1)):
        pts = [(x0 + (x1 - x0) * i / 40, yp + sg * 1.3 * math.sin(2 * math.pi * 5 * i / 40)) for i in range(41)]
        c.poli(pts, COCLEAR, 1.1)


def espiral(c, x, y, r, color, relleno):
    c.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 2:.1f}" fill="{relleno}" stroke="none"/>')
    pts = []
    vueltas = 2.5
    for i in range(121):
        u = i / 120
        th = 2 * math.pi * vueltas * u
        rr = r * (1 - 0.82 * u)
        pts.append((x + rr * math.cos(th), y + rr * math.sin(th)))
    c.poli(pts, color, 1.6)


def cabeza_frontal(c, cx, cy, s=1.0, cuello=125):
    """Corte frontal de la cabeza a la altura de los oídos, de frente al paciente
    (OD a la izquierda del dibujo). (cx, cy) es el centro a la altura de los conductos.
    Devuelve los puntos útiles de cada oído."""
    X = lambda dx: cx + dx * s  # noqa: E731
    Y = lambda dy: cy + dy * s  # noqa: E731
    puntos = {}
    # pabellones (antes que la cabeza, que tapa su mitad interna)
    for lado, sg in (('od', -1), ('oi', 1)):
        c.out.append(f'<ellipse cx="{X(sg * 100):.1f}" cy="{Y(-6):.1f}" rx="{9 * s:.1f}" ry="{22 * s:.1f}" '
                     f'fill="{PIEL}" stroke="{TINTA_2}" stroke-width="1.3"/>')
    # contorno: cráneo (media elipse) y mandíbula hacia el cuello
    d = (f'M{X(-44):.1f},{Y(cuello):.1f} L{X(-44):.1f},{Y(92):.1f} '
         f'C{X(-72):.1f},{Y(78):.1f} {X(-92):.1f},{Y(45):.1f} {X(-92):.1f},{Y(0):.1f} '
         f'A{92 * s:.1f},{150 * s:.1f} 0 0 1 {X(92):.1f},{Y(0):.1f} '
         f'C{X(92):.1f},{Y(45):.1f} {X(72):.1f},{Y(78):.1f} {X(44):.1f},{Y(92):.1f} '
         f'L{X(44):.1f},{Y(cuello):.1f}')
    camino(c, d + ' Z', PIEL, 'none', 0)
    camino(c, d, 'none', TINTA_2, 1.4)
    # encéfalo y bóveda craneana
    camino(c, f'M{X(-84):.1f},{Y(-8):.1f} A{84 * s:.1f},{140 * s:.1f} 0 0 1 {X(84):.1f},{Y(-8):.1f} '
              f'L{X(20):.1f},{Y(-8):.1f} L{X(-20):.1f},{Y(-8):.1f} Z', CEREBRO, 'none', 0)
    camino(c, f'M{X(-86):.1f},{Y(-4):.1f} A{86 * s:.1f},{144 * s:.1f} 0 0 1 {X(86):.1f},{Y(-4):.1f}',
           'none', HUESO, 6 * s)
    # peñascos (hueso temporal) a la altura de los oídos
    for sg in (-1, 1):
        camino(c, f'M{X(sg * 90):.1f},{Y(-24):.1f} L{X(sg * 20):.1f},{Y(-12):.1f} L{X(sg * 20):.1f},{Y(8):.1f} '
                  f'L{X(sg * 88):.1f},{Y(30):.1f} Z', HUESO_CLARO, HUESO, 1)
    # conducto, tímpano, oído medio y cóclea de cada lado
    for lado, sg in (('od', -1), ('oi', 1)):
        col, claro = (OD, OD_CLARO) if lado == 'od' else (OI, OI_CLARO)
        x_ent, x_tim = X(sg * 101), X(sg * 64)
        xa, xb = min(x_ent, x_tim), max(x_ent, x_tim)
        rect(c, xa, Y(-5), xb - xa, 10 * s, '#ffffff', 'none', 0)
        c.l(xa, Y(-5), xb, Y(-5), TINTA_2, 0.9)
        c.l(xa, Y(5), xb, Y(5), TINTA_2, 0.9)
        xm1, xm2 = X(sg * 64), X(sg * 53)
        rect(c, min(xm1, xm2), Y(-10), abs(xm2 - xm1), 20 * s, '#ffffff', 'none', 0, 3)
        c.l(X(sg * 66), Y(-8), X(sg * 62), Y(8), TINTA, 1.6)
        c.poli([(X(sg * 63), Y(-1)), (X(sg * 60), Y(-6)), (X(sg * 56), Y(-6)), (X(sg * 55), Y(-1))], TENUE, 1.4)
        espiral(c, X(sg * 42), Y(-1), 8.5 * s, col, claro)
        puntos[lado] = {'entrada': x_ent, 'timpano': x_tim, 'coclea': (X(sg * 42), Y(-1)),
                        'pabellon': X(sg * 100), 'sg': sg, 'color': col, 'y': Y(0)}
    puntos['tope'] = Y(-150)
    puntos['base'] = Y(cuello)
    return puntos


def diapason(c, cx, y_base, s=1.0):
    """Diapasón apoyado por su base en (cx, y_base)."""
    c.out.append(f'<circle cx="{cx:.1f}" cy="{y_base - 2 * s:.1f}" r="{3.2 * s:.1f}" fill="{TINTA_2}"/>')
    c.l(cx, y_base - 4 * s, cx, y_base - 22 * s, TINTA_2, 2.6 * s)
    camino(c, f'M{cx - 7 * s:.1f},{y_base - 66 * s:.1f} L{cx - 7 * s:.1f},{y_base - 30 * s:.1f} '
              f'Q{cx - 7 * s:.1f},{y_base - 22 * s:.1f} {cx:.1f},{y_base - 22 * s:.1f} '
              f'Q{cx + 7 * s:.1f},{y_base - 22 * s:.1f} {cx + 7 * s:.1f},{y_base - 30 * s:.1f} '
              f'L{cx + 7 * s:.1f},{y_base - 66 * s:.1f}', 'none', TINTA_2, 3 * s)
    for sg in (-1, 1):
        for k, r in enumerate((6, 11)):
            x = cx + sg * (12 + 5 * k) * s
            camino(c, f'M{x:.1f},{y_base - (56 + r) * s:.1f} Q{x + sg * r * 0.5 * s:.1f},{y_base - 56 * s:.1f} '
                      f'{x:.1f},{y_base - (56 - r) * s:.1f}', 'none', TENUE, 1)


def escala_lateral(c, cx, y, donde):
    """Regla OD-centro-OI con un punto donde el paciente oye el diapasón (-1, 0, 1)."""
    c.l(cx - 70, y, cx + 70, y, GRILLA, 3)
    for x in (cx - 70, cx, cx + 70):
        c.l(x, y - 5, x, y + 5, TENUE, 1)
    c.t(cx - 78, y + 4, 'OD', 9, OD, 'end', 700)
    c.t(cx + 78, y + 4, 'OI', 9, OI, 'start', 700)
    xp = cx + 70 * donde
    col = TINTA if donde == 0 else (OD if donde < 0 else OI)
    c.out.append(f'<circle cx="{xp:.1f}" cy="{y:.1f}" r="6" fill="{col}"/>')
    c.t(cx, y + 22, 'dónde lo oye el paciente', 8, TENUE, 'middle')


def weber():
    c = Lienzo(820, 470)
    defs = punta('p-c', COCLEAR) + punta('p-t', TENUE) + punta('p-g', TINTA_2)
    c.t(14, 20, 'El Weber en un corte frontal de la cabeza (de frente al paciente)',
        10.5, TINTA, 'start', 700)
    cy = 290
    paneles = ((215, 'A · Los dos oídos sanos', False), (615, 'B · Conducto derecho tapado', True))
    for cx, titulo, tapado in paneles:
        c.t(cx, 50, titulo, 9.5, TINTA, 'middle', 700)
        p = cabeza_frontal(c, cx, cy, cuello=104)
        diapason(c, cx, p['tope'] + 1)
        # la vibración baja por el hueso, igual a las dos cócleas
        for lado in ('od', 'oi'):
            xc, yc = p[lado]['coclea']
            sg = p[lado]['sg']
            flecha(c, f'M{cx + sg * 4:.1f},{p["tope"] + 14:.1f} Q{cx + sg * 12:.1f},{cy - 70:.1f} '
                      f'{xc - sg * 6:.1f},{yc - 13:.1f}', COCLEAR, 2.6, 'p-c')
        if not tapado:
            c.t(cx - 66, cy - 128, 'vibración', 8, COCLEAR, 'end', 700)
            c.t(cx - 66, cy - 118, 'por el hueso', 8, COCLEAR, 'end', 700)
            c.l(cx - 64, cy - 121, cx - 12, cy - 104, TENUE, 0.8)
        # cada conducto: el ruido ambiente entra por el abierto y lo enmascara un poco; el tapado
        # no deja entrar ruido y suma el efecto de oclusión (la pared vibra y su sonido, encerrado,
        # empuja el tímpano)
        for lado in ('od', 'oi'):
            q = p[lado]
            sg, ye = q['sg'], q['y']
            if tapado and lado == 'od':
                rect(c, min(q['entrada'], q['entrada'] - sg * 18), ye - 5, 18, 10, TAPON, '#7b5524', 0.8, 3)
                pared_vibrando(c, q['entrada'] - sg * 18, q['timpano'], ye)
                flecha(c, f'M{q["entrada"] - sg * 21:.1f},{ye:.1f} L{q["timpano"] + sg * 3:.1f},{ye:.1f}',
                       COCLEAR, 2, 'p-c')
                flecha(c, f'M{q["entrada"] + sg * 46:.1f},{ye - 46:.1f} L{q["entrada"] + sg * 6:.1f},{ye - 9:.1f}',
                       TENUE, 1.3, 'p-t', '3 2')
                c.l(q['entrada'] + sg * 4, ye - 14, q['entrada'] + sg * 12, ye - 6, OD, 1.6)
                c.l(q['entrada'] + sg * 4, ye - 6, q['entrada'] + sg * 12, ye - 14, OD, 1.6)
                c.out.append(f'<circle cx="{q["coclea"][0]:.1f}" cy="{q["coclea"][1]:.1f}" r="15" fill="none" '
                             f'stroke="{OD}" stroke-width="1.4" stroke-dasharray="2 2"/>')
                xt = cx - 64
                c.t(xt, ye + 44, 'tapón: no entra ruido', 8, '#7b5524', 'start', 700)
                c.t(xt, ye + 54, 'y el sonido de la pared', 8, TINTA_2, 'start', 600)
                c.t(xt, ye + 64, 'que vibra empuja el tímpano', 8, TINTA_2, 'start', 600)
                c.t(xt, ye + 74, '(efecto de oclusión)', 8, TINTA_2, 'start', 600)
                c.l(xt + 4, ye + 34, q['entrada'] - sg * 12, ye + 7, TENUE, 0.8)
            else:
                flecha(c, f'M{q["entrada"] + sg * 46:.1f},{ye - 46:.1f} L{q["entrada"] + sg * 4:.1f},{ye - 7:.1f}',
                       TENUE, 1.3, 'p-t', '3 2')
                camino(c, f'M{q["entrada"]:.1f},{ye:.1f} L{q["timpano"] + sg * 4:.1f},{ye:.1f}', 'none', TENUE, 1.3,
                       ' marker-end="url(#p-t)" stroke-dasharray="3 2"')
                if lado == 'oi':
                    xt = q['entrada'] + sg * 46
                    c.t(xt, ye - 52, 'ruido ambiente', 8, TENUE, 'middle', 600)
                    c.t(xt, ye + 26, 'entra y enmascara', 8, TINTA_2, 'middle', 600)
                    c.t(xt, ye + 36, 'un poco al diapasón', 8, TINTA_2, 'middle', 600)
        # rótulos de estructuras, solo en A
        if not tapado:
            q = p['od']
            c.t(q['entrada'] - 22, cy + 44, 'conducto', 8, TINTA_2, 'end', 600)
            c.l(q['entrada'] - 20, cy + 38, q['entrada'] + 10, cy + 5, TENUE, 0.8)
            c.t(cx - 20, cy + 52, 'cóclea', 8, TINTA_2, 'middle', 600)
            c.l(cx - 26, cy + 42, q['coclea'][0] + 2, q['coclea'][1] + 11, TENUE, 0.8)
            c.t(cx + 26, p['tope'] - 50, 'diapasón en', 8, TINTA_2, 'start', 600)
            c.t(cx + 26, p['tope'] - 40, 'la línea media', 8, TINTA_2, 'start', 600)
        for lado in ('od', 'oi'):
            q = p[lado]
            c.t(q['pabellon'], cy + 82, lado.upper(), 9.5, q['color'], 'middle', 700)
        escala_lateral(c, cx, p['base'] + 32, -1 if tapado else 0)
    c.guardar('h02-weber-conductivo.svg', defs)


if __name__ == '__main__':
    weber()
