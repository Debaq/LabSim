#!/usr/bin/env python3
"""Dibuja ilustraciones/h03-ptp-nivelar.svg: la maña de calcular el promedio
tonal a ojo (nivelar y anclaje). SVG propio, no IA: es un esquema exacto."""
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
PUNTO, BAJA, SUBE, PTP = '#24101a', '#c62f3a', '#2c5cb0', '#2e8540'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
out = []


def t(x, y, s, size=9, color=TINTA, anchor='middle', peso=400):
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
               f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')


def mini(x0, y0, valores, flechas=(), linea=None, rot=None, db_min=15, db_max=65, ancho=118, px=3.2):
    """Un audiograma chico: dB hacia abajo, una columna por frecuencia."""
    Y = lambda db: y0 + (db - db_min) * px
    for db in range(db_min, db_max + 1, 5):
        out.append(f'<line x1="{x0}" y1="{Y(db):.1f}" x2="{x0 + ancho}" y2="{Y(db):.1f}" '
                   f'stroke="{FUERTE if db % 10 == 0 else GRILLA}" stroke-width="{0.8 if db % 10 == 0 else 0.5}"/>')
        if db % 10 == 0:
            t(x0 - 4, Y(db) + 3, db, 7, TENUE, 'end')
    n = len(valores)
    xs = [x0 + ancho * (i + 0.5) / n for i in range(n)]
    if linea is not None:
        out.append(f'<line x1="{x0}" y1="{Y(linea):.1f}" x2="{x0 + ancho}" y2="{Y(linea):.1f}" '
                   f'stroke="{PTP}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    for i, a, b in flechas:
        color = BAJA if b > a else SUBE
        y1, y2 = Y(a) + (4 if b > a else -4), Y(b) - (3 if b > a else -3)
        out.append(f'<line x1="{xs[i]:.1f}" y1="{y1:.1f}" x2="{xs[i]:.1f}" y2="{y2:.1f}" stroke="{color}" '
                   f'stroke-width="1.6" marker-end="url(#punta-{"b" if b > a else "s"})"/>')
    for x, v in zip(xs, valores):
        out.append(f'<circle cx="{x:.1f}" cy="{Y(v):.1f}" r="4" fill="#fff" stroke="{PUNTO}" stroke-width="1.6"/>')
    if rot:
        for x, s in zip(xs, rot):
            t(x, Y(db_max) + 12, s, 7.5, TENUE)
    return xs, Y


W, H = 680, 262
# Método 1: nivelar
t(14, 18, '1 · Nivelar: lo que uno baja, otro lo sube', 10, TINTA, 'start', 700)
estados = [([30, 40, 50], [(0, 30, 35), (2, 50, 45)], None, '30 · 40 · 50'),
           ([35, 40, 45], [(0, 35, 40), (2, 45, 40)], None, '35 · 40 · 45'),
           ([40, 40, 40], [], 40, 'PTP = 40 dB')]
for k, (vals, fl, lin, pie) in enumerate(estados):
    x0 = 40 + k * 150
    mini(x0, 34, vals, fl, lin, ['500', '1k', '2k'])
    t(x0 + 59, 222, pie, 9, PTP if lin else TINTA, 'middle', 700 if lin else 400)
    if k < 2:
        t(x0 + 133, 110, '→', 16, TENUE)
t(40, 244, 'Un escalón = 5 dB. Bajar en el gráfico es sumar dB; subir es restar. El promedio no cambia.', 8, TENUE, 'start')

# Método 2: anclaje
x0 = 500
t(x0 - 26, 18, '2 · Anclaje', 10, TINTA, 'start', 700)
xs, Y = mini(x0, 34, [20, 30, 40, 60], (), None, ['500', '1k', '2k', '4k'], db_min=15, db_max=65, ancho=150)
out.append(f'<line x1="{x0}" y1="{Y(30):.1f}" x2="{x0 + 150}" y2="{Y(30):.1f}" stroke="{TENUE}" stroke-width="1.2"/>')
for x, v, s in zip(xs, [20, 30, 40, 60], ['−2', '0', '+2', '+6']):
    if v != 30:
        out.append(f'<line x1="{x + 7:.1f}" y1="{Y(30):.1f}" x2="{x + 7:.1f}" y2="{Y(v):.1f}" '
                   f'stroke="{BAJA if v > 30 else SUBE}" stroke-width="2.4" opacity=".55"/>')
    t(x + 9, Y(v) + (12 if v > 30 else -7), s, 8, BAJA if v > 30 else (SUBE if v < 30 else TENUE), 'start', 700)
t(x0 + 75, 222, 'ancla 30 · neto +6 escalones', 8.5)
t(x0 + 75, 236, '+6 ÷ 4 = 1,5 escalones = 7,5 dB', 8.5)
t(x0 + 75, 254, 'PTP = 37,5 dB', 9, PTP, 'middle', 700)

defs = (f'<defs><marker id="punta-b" markerWidth="5" markerHeight="5" refX="3.5" refY="3.5" markerUnits="userSpaceOnUse" orient="auto">'
        f'<path d="M0,0 L7,3.5 L0,7 z" transform="scale(.75)" fill="{BAJA}"/></marker>'
        f'<marker id="punta-s" markerWidth="5" markerHeight="5" refX="3.5" refY="3.5" markerUnits="userSpaceOnUse" orient="auto">'
        f'<path d="M0,0 L7,3.5 L0,7 z" transform="scale(.75)" fill="{SUBE}"/></marker></defs>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{defs}'
       f'<rect width="{W}" height="{H}" fill="#fff"/>' + ''.join(out) + '</svg>')
(pathlib.Path(__file__).parent / 'h03-ptp-nivelar.svg').write_text(svg, encoding='utf-8')
print('h03-ptp-nivelar.svg')
