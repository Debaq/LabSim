#!/usr/bin/env python3
"""Dibuja el esquema propio de H18 (maniobras de diagnóstico y reposición):

    h18-nistagmo-por-canal.svg   qué se ve en los ojos según el canal y la postura

Esquema, no datos de un paciente. Los ojos se ven como los ve el examinador:
el oído derecho del paciente queda a la izquierda del dibujo. Las flechas son
la fase RÁPIDA (la que se ve y la que da nombre al nistagmo). Las
imágenes de maniobras y de canales (h18-*.png) salen de labyrinthus3d con
herramientas/ (ver hacer_h18_capturas.py)."""
import math
import pathlib

TINTA, TENUE, GRILLA = '#24101a', '#8a8a90', '#e7e5e0'
ROJO, AZUL, VERDE = '#c62f3a', '#2b5fa8', '#21796c'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
out = []


def t(x, y, s, size=10, color=TINTA, anchor='middle', peso=400):
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{peso}">{s}</text>')


def linea(x1, y1, x2, y2, color=TINTA, w=1.2, flecha=None):
    m = f' marker-end="url(#{flecha})"' if flecha else ''
    out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{m}/>')


def ojo(cx, cy, r=24):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 5}" fill="#faf8f4" stroke="{TENUE}" stroke-width="1"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r - 3}" fill="#a9825a" stroke="{TINTA}" stroke-width="1"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.38}" fill="{TINTA}"/>')
    out.append(f'<circle cx="{cx - 4}" cy="{cy - 4}" r="2" fill="#fff"/>')


def par(cx, cy):
    """Los dos ojos; devuelve los centros (izquierda del dibujo = OD del paciente)."""
    ojo(cx - 38, cy)
    ojo(cx + 38, cy)
    return (cx - 38, cy), (cx + 38, cy)


def vertical(cx, cy, arriba, color=ROJO, grosor=2.4):
    y1, y2 = (cy + 30, cy - 30) if arriba else (cy - 30, cy + 30)
    linea(cx, y1, cx, y2, color, grosor, 'pr')


def horizontal(cx, cy, derecha_dibujo, color=ROJO, grosor=2.4, largo=60):
    x1, x2 = (cx - largo, cx + largo) if derecha_dibujo else (cx + largo, cx - largo)
    linea(x1, cy + 36, x2, cy + 36, color, grosor, 'pr')


def torsion(cx, cy, hacia_izq_dibujo, color=VERDE, r=34):
    """Arco sobre el polo superior de cada ojo, con la flecha hacia donde va ese polo."""
    for ox in (-38, 38):
        x0 = cx + ox
        a1, a2 = (math.radians(-55), math.radians(-125)) if hacia_izq_dibujo else (math.radians(-125), math.radians(-55))
        p1 = (x0 + r * math.cos(a1), cy + r * math.sin(a1))
        p2 = (x0 + r * math.cos(a2), cy + r * math.sin(a2))
        sweep = 0 if hacia_izq_dibujo else 1
        out.append(f'<path d="M{p1[0]:.1f},{p1[1]:.1f} A{r},{r} 0 0 {sweep} {p2[0]:.1f},{p2[1]:.1f}" fill="none" '
                   f'stroke="{color}" stroke-width="2.2" stroke-linecap="round" marker-end="url(#pv)"/>')


W, H = 760, 560
out.append(f'<rect width="{W}" height="{H}" fill="#fff"/>')
t(14, 22, 'Qué se ve en los ojos, según el canal y la postura', 12.5, TINTA, 'start', 700)
t(14, 38, 'Visto por el examinador: el oído derecho del paciente (aquí, el enfermo) queda a la izquierda. Flechas rojas = fase rápida; verde = polo superior del ojo.', 9, TENUE, 'start')

filas = [
    ('Posterior', 'Dix-Hallpike hacia el lado enfermo', 'canalitiasis (el más frecuente)', 'p'),
    ('Anterior', 'Dix-Hallpike o cabeza colgando', 'raro; cuidado con el central', 'a'),
    ('Lateral geotrópico', 'giro supino, cabeza al lado enfermo', 'hacia el oído de abajo; mayor del lado enfermo', 'g'),
    ('Lateral apogeotrópico', 'giro supino, cabeza al lado sano', 'hacia el oído de arriba; mayor del lado sano', 'x'),
    ('Alerta: central', 'al acostarse, sin latencia', 'vertical puro, que no se cansa', 'c'),
]
y0, dy = 62, 98
for i, (nombre, pos, texto, tipo) in enumerate(filas):
    y = y0 + i * dy
    cy = y + 38
    if i:
        linea(14, y - 14, W - 14, y - 14, GRILLA, 1)
    t(14, y + 14, nombre, 11.5, ROJO if tipo == 'c' else TINTA, 'start', 700)
    t(14, y + 30, pos, 9, TENUE, 'start')
    t(14, y + 44, texto, 9, TENUE, 'start')
    # ojos A: la postura que provoca (columna 1) y B: la contraria (columna 2)
    cxA, cxB = 330, 560
    par(cxA, cy)
    if tipo not in 'ac':
        par(cxB, cy)
    if tipo == 'p':
        vertical(cxA, cy, True)
        torsion(cxA, cy, True)
        t(cxA, y + 85, 'Hallpike, oído enfermo abajo', 8.5, TENUE)
        vertical(cxB, cy, False, '#d08a90', 1.6)
        t(cxB, y + 85, 'al sentarse: se invierte, más suave', 8.5, TENUE)
    elif tipo == 'a':
        vertical(cxA, cy, False)
        torsion(cxA, cy, True)
        t(cxA, y + 85, 'hacia abajo, con o sin torsión', 8.5, TENUE)
        t(cxB, cy - 4, 'al sentarse: invierte', 9, TENUE)
        t(cxB, cy + 10, '(hacia arriba, más suave)', 9, TENUE)
        vertical(cxB, cy - 12, True, '#d08a90', 1.6) if False else None
    elif tipo == 'g':
        horizontal(cxA, cy, False, ROJO, 3.0)
        t(cxA, y + 85, 'rueda al lado enfermo (OD): fuerte', 8.5, TENUE)
        horizontal(cxB, cy, True, '#d08a90', 1.6)
        t(cxB, y + 85, 'rueda al lado sano (OI): más débil', 8.5, TENUE)
    elif tipo == 'x':
        horizontal(cxA, cy, True, '#d08a90', 1.6)
        t(cxA, y + 85, 'rueda al lado enfermo (OD): débil', 8.5, TENUE)
        horizontal(cxB, cy, False, ROJO, 3.0)
        t(cxB, y + 85, 'rueda al lado sano (OI): fuerte', 8.5, TENUE)
    else:
        vertical(cxA, cy, False, ROJO, 3.0)
        t(cxA, y + 85, 'hacia abajo, sin torsión', 8.5, TENUE)
        t(cxB, cy - 4, 'sin latencia, sin fatiga,', 9, TENUE)
        t(cxB, cy + 10, 'persiste con la postura', 9, TENUE)

defs = ''.join(f'<marker id="{i}" markerWidth="8" markerHeight="8" refX="6" refY="4" markerUnits="userSpaceOnUse" orient="auto">'
               f'<path d="M0,0 L8,4 L0,8 z" fill="{c}"/></marker>' for i, c in (('pr', ROJO), ('pv', VERDE)))
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><defs>{defs}</defs>'
       + ''.join(out) + '</svg>')
(AQUI / 'h18-nistagmo-por-canal.svg').write_text(svg, encoding='utf-8')
print('h18-nistagmo-por-canal.svg')
