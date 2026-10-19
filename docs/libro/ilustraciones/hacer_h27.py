#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H27 (prick test):

    h27-mapa.svg      antebrazo volar: zona útil, distancias y orden de las punciones
    h27-lectura.svg   cómo se mide la pápula (diámetro mayor y perpendicular) y el umbral de 3 mm
    h27-curso.svg     curso temporal de la reacción inmediata y ventana de lectura
    h27-resultado.svg el mismo antebrazo a los 15 minutos, con las pápulas a escala

SVG propios, no IA. Las pápulas del ejemplo son inventadas (no son datos de un paciente);
el curso temporal es un esquema cualitativo: el momento del máximo y de la lectura salen de
Heinzerling y cols. (2013) y Bernstein y cols. (2008), la forma de la curva no es un dato.
Las cifras que aparecen en el capítulo salen de este script (se imprimen al correrlo)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h25 import Lienzo, TINTA, TENUE, GRILLA, FUERTE, AVISO, RETRO, COCLEAR, IZQ  # noqa: E402

PIEL, PIEL_BORDE = '#f3dcc8', '#b98f72'
ROJO_FLARE, PAPULA = '#e8564a', '#fbeee6'
AQUI = pathlib.Path(__file__).parent

# Ejemplo: (sigla, nombre, ancho mm, alto mm). El mismo orden de punciones en el mapa y el resultado.
SITIOS = [
    ('NEG', 'Control negativo (suero)', 0, 0),
    ('Dp', 'D. pteronyssinus', 8, 7),
    ('Df', 'D. farinae', 6, 5),
    ('Gato', 'Gato (epitelio)', 3, 3),
    ('Perro', 'Perro (epitelio)', 2, 2),
    ('Pasto', 'Mezcla de pastos', 5, 4),
    ('Alt', 'Alternaria', 0, 0),
    ('HIS', 'Control positivo (histamina)', 6, 5),
]
SUELO = 3  # mm: umbral de positividad


def brazo(c, x0, x1, y0, y1, esc):
    """Antebrazo en horizontal: codo a la izquierda, muñeca a la derecha."""
    r = (y1 - y0) / 2
    c.raw(f'<path d="M{x0},{y0 + 8} Q{x0 - 22},{(y0 + y1) / 2} {x0},{y1 - 8} L{x1},{y1 - 14} '
          f'L{x1 + 90},{y1 - 20} Q{x1 + 112},{(y0 + y1) / 2} {x1 + 90},{y0 + 20} L{x1},{y0 + 14} Z" '
          f'fill="{PIEL}" stroke="{PIEL_BORDE}" stroke-width="1.6" stroke-linejoin="round"/>')
    c.l(x0 + 2, y0 + 9, x0 + 2, y1 - 9, PIEL_BORDE, 1.3, '4 3')      # pliegue del codo
    c.l(x1, y0 + 14, x1, y1 - 14, PIEL_BORDE, 1.3, '4 3')            # pliegue de la muñeca


def mapa():
    esc = 20  # px por cm
    c = Lienzo(780, 330)
    c.t(14, 20, 'Antebrazo, cara palmar (volar): el codo a la izquierda y la muñeca a la derecha', 10, TINTA, 'start', 700)
    x0, x1, y0, y1 = 70, 410, 80, 230
    brazo(c, x0, x1, y0, y1, esc)
    # zonas sin puncionar: 3 cm desde cada pliegue
    c.raw(f'<rect x="{x0 + 2}" y="{y0 + 10}" width="{3 * esc}" height="{y1 - y0 - 20}" fill="{AVISO}" opacity=".10"/>')
    c.raw(f'<rect x="{x1 - 3 * esc}" y="{y0 + 14}" width="{3 * esc}" height="{y1 - y0 - 28}" fill="{AVISO}" opacity=".10"/>')
    c.t(x0 + 3 * esc / 2 + 2, y0 - 8, 'pliegue del codo', 8, TENUE)
    c.t(x1, y0 - 8, 'pliegue de la muñeca', 8, TENUE)
    c.t(x0 + 3 * esc / 2 + 2, y1 + 18, '3 cm', 8, AVISO, 'middle', 700)
    c.t(x1 - 3 * esc / 2, y1 + 18, '3 cm', 8, AVISO, 'middle', 700)
    c.t((x0 + x1) / 2, y1 + 34, 'franjas rojas: no se punciona a menos de 3 cm de los pliegues', 8, AVISO)
    paso = 2.5 * esc
    xs0, ys = x0 + 3 * esc + 10, (y0 + 48, y0 + 48 + paso)
    pos = []
    for k, (sig, nom, a, b) in enumerate(SITIOS):
        f, col = divmod(k, 4)
        # fila 0: izquierda a derecha; fila 1: continúa de izquierda a derecha
        x, y = xs0 + col * paso, ys[f]
        pos.append((x, y))
        c.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{TINTA}"/>')
        c.raw(f'<circle cx="{x - 0:.1f}" cy="{y - 17:.1f}" r="8.5" fill="#fff" stroke="{TINTA}" stroke-width="1.2"/>')
        c.t(x, y - 13.8, str(k + 1), 8.5, TINTA, 'middle', 700)
        c.t(x, y + 17, sig, 8, COCLEAR if sig in ('NEG', 'HIS') else TINTA, 'middle', 700)
    # cota: distancia entre punciones
    xa, ya = pos[1]
    xb, yb = pos[2]
    c.l(xa, ya - 34, xb, yb - 34, TINTA, 1, extra=' marker-start="url(#cota)" marker-end="url(#cota)"')
    c.t((xa + xb) / 2, ya - 38, '2,5 cm', 8, TINTA, 'middle', 700)
    xc, yc = pos[0]
    xd, yd = pos[4]
    c.l(xc - 20, yc, xd - 20, yd, TINTA, 1, extra=' marker-start="url(#cota)" marker-end="url(#cota)"')
    c.t(xc - 26, (yc + yd) / 2 + 3, '2,5 cm', 8, TINTA, 'end', 700)
    # escala
    c.l(x1 - 4 * esc - 20, y1 + 58, x1 - 2 * esc - 20, y1 + 58, TINTA, 2)
    c.t(x1 - 3 * esc - 20, y1 + 72, '2 cm (escala)', 8, TENUE)
    # leyenda
    lx, ly = 560, 74
    c.t(lx, ly - 22, 'Orden de aplicación', 10, TINTA, 'start', 700)
    for k, (sig, nom, a, b) in enumerate(SITIOS):
        y = ly + k * 24
        c.raw(f'<circle cx="{lx + 8}" cy="{y - 3}" r="8.5" fill="#fff" stroke="{TINTA}" stroke-width="1.2"/>')
        c.t(lx + 8, y, str(k + 1), 8.5, TINTA, 'middle', 700)
        c.t(lx + 24, y, f'{sig} · {nom}', 8.5, TINTA, 'start', 400)
    c.t(lx, ly + 8 * 24 + 6, 'Se empieza por el negativo y se termina', 8, TENUE, 'start')
    c.t(lx, ly + 8 * 24 + 18, 'por la histamina, que reacciona primero.', 8, TENUE, 'start')
    cota = ('<marker id="cota" markerWidth="6" markerHeight="6" refX="3" refY="3" markerUnits="userSpaceOnUse" '
            'orient="auto"><path d="M3,0 L3,6" stroke="#24101a" stroke-width="1.2"/></marker>')
    c.guardar('h27-mapa.svg', cota)
    return pos


def pap(c, x, y, a, b, esc, rot=-12, flare=True):
    """Pápula (a × b mm) con su eritema, a escala esc px/mm."""
    if a == 0:
        c.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="#8d4a3e"/>')
        return
    if flare:
        r = max(a, b) * esc * 1.2 + 4
        c.raw(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r:.1f}" ry="{r * .92:.1f}" fill="{ROJO_FLARE}" opacity=".28" '
              f'transform="rotate({rot} {x:.1f} {y:.1f})"/>')
    c.raw(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{a * esc / 2:.1f}" ry="{b * esc / 2:.1f}" fill="{PAPULA}" '
          f'stroke="#d9a897" stroke-width="1" transform="rotate({rot} {x:.1f} {y:.1f})"/>')
    c.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.3" fill="#8d4a3e"/>')


def regla(c, x, y, mm, esc, color=TINTA):
    c.l(x, y, x + mm * esc, y, color, 1.2)
    for k in range(mm + 1):
        h = 9 if k % 5 == 0 else 5
        c.l(x + k * esc, y, x + k * esc, y - h, color, 1)
        if k % 2 == 0:
            c.t(x + k * esc, y + 11, str(k), 8, color)
    c.t(x + mm * esc + 14, y + 3, 'mm', 8, color, 'start')


def lectura():
    esc = 20  # px por mm
    c = Lienzo(700, 330)
    c.t(14, 20, 'A · Medir una pápula', 10, TINTA, 'start', 700)
    c.t(380, 20, 'B · El umbral de 3 mm', 10, TINTA, 'start', 700)
    # A: piel, pápula irregular y seudópodo
    c.raw(f'<rect x="14" y="34" width="330" height="270" rx="10" fill="{PIEL}" stroke="{PIEL_BORDE}" stroke-width="1.4"/>')
    cx, cy = 150, 170
    c.raw(f'<ellipse cx="{cx}" cy="{cy}" rx="{12 * esc / 2:.0f}" ry="{9.5 * esc / 2:.0f}" fill="{ROJO_FLARE}" opacity=".25" '
          f'transform="rotate(-25 {cx} {cy})"/>')
    # pápula de 8 x 6 mm girada -25 grados, con un seudópodo
    ang = math.radians(-25)
    pts = []
    for k in range(48):
        t = 2 * math.pi * k / 48
        rx, ry = 4 * esc, 3 * esc
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    c.poli(pts + [pts[0]], '#d9a897', 1.2, fill=PAPULA)
    c.raw(f'<circle cx="{cx}" cy="{cy}" r="2" fill="#8d4a3e"/>')
    # diámetro mayor y perpendicular
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    c.l(cx - 4 * esc * ux, cy - 4 * esc * uy, cx + 4 * esc * ux, cy + 4 * esc * uy, AVISO, 1.8)
    c.l(cx - 3 * esc * vx, cy - 3 * esc * vy, cx + 3 * esc * vx, cy + 3 * esc * vy, IZQ, 1.8)
    c.t(cx + 4 * esc * ux + 6, cy + 4 * esc * uy - 6, 'D mayor', 8.5, AVISO, 'start', 700)
    c.t(cx - 3 * esc * vx - 6, cy - 3 * esc * vy - 8, 'D perpendicular', 8.5, IZQ, 'end', 700)
    c.t(cx, cy + 112, 'Se anota 8 × 6 mm; el diámetro mayor (8 mm) manda', 8.5, TINTA, 'middle', 700)
    c.t(cx, cy + 124, 'La zona roja tenue es el eritema: no se mide como pápula', 8, TENUE)
    regla(c, 40, 60, 14, esc * 0.9)
    # B: tres círculos a escala frente a la regla
    c.raw(f'<rect x="380" y="34" width="306" height="270" rx="10" fill="{PIEL}" stroke="{PIEL_BORDE}" stroke-width="1.4"/>')
    ex = 14
    base = 120
    datos = [('Negativo', 0, 'sin pápula', RETRO), ('Perro', 2, '2 mm', TENUE), ('Gato', 3, '3 mm', AVISO), ('Dp', 8, '8 mm', AVISO)]
    xs = [412, 470, 530, 622]
    for (nom, mm, rot, col), x in zip(datos, xs):
        pap(c, x, base, mm, mm, ex, rot=0, flare=False)
        c.t(x, base + 70, nom, 8.5, TINTA, 'middle', 700)
        c.t(x, base + 82, rot, 8, col, 'middle', 700)
    c.raw(f'<circle cx="{xs[2]}" cy="{base}" r="{SUELO * ex / 2 + 5}" fill="none" stroke="{AVISO}" stroke-width="1" stroke-dasharray="3 3"/>')
    c.t(530, 218, '2 mm no alcanza; 3 mm sí', 9, TINTA, 'middle', 700)
    c.t(530, 232, 'Positivo: pápula de 3 mm o más, y 3 mm', 8, TENUE)
    c.t(530, 244, 'mayor que la del control negativo', 8, TENUE)
    regla(c, 410, 270, 14, ex)
    c.guardar('h27-lectura.svg')


def curso():
    c = Lienzo(700, 335)
    x0, y0, w, h = 70, 40, 580, 210
    c.t(14, 20, 'Reacción inmediata de la piel según el tiempo (esquema cualitativo)', 10, TINTA, 'start', 700)
    c.l(x0, y0 + h, x0 + w, y0 + h, TINTA, 1.4)
    c.l(x0, y0, x0, y0 + h, TINTA, 1.4)
    esc = w / 60
    for m in range(0, 61, 10):
        c.l(x0 + m * esc, y0 + h, x0 + m * esc, y0 + h + 5, TINTA, 1.2)
        c.t(x0 + m * esc, y0 + h + 18, str(m), 8.5)
    c.t(x0 + w / 2, y0 + h + 34, 'minutos desde la punción', 9, TINTA)
    c.raw(f'<text x="22" y="{y0 + h / 2}" font-family="\'Plus Jakarta Sans\', sans-serif" font-size="10.8" fill="{TINTA}" '
          f'text-anchor="middle" transform="rotate(-90 22 {y0 + h / 2})">tamaño de la pápula</text>')
    # ventana de lectura 15-20
    c.raw(f'<rect x="{x0 + 15 * esc}" y="{y0}" width="{5 * esc}" height="{h}" fill="{COCLEAR}" opacity=".16"/>')
    c.t(x0 + 17.5 * esc, y0 + 12, 'lectura', 8.5, COCLEAR, 'middle', 700)
    c.t(x0 + 17.5 * esc, y0 + 24, '15–20 min', 8.5, COCLEAR, 'middle', 700)

    def curva(pico_t, pico_h, sube, baja, cola):
        pts = []
        for k in range(0, 601):
            t = k / 10
            if t <= pico_t:
                v = pico_h * (1 - math.exp(-sube * t)) / (1 - math.exp(-sube * pico_t))
            else:
                v = pico_h * math.exp(-baja * (t - pico_t)) if t < cola else pico_h * math.exp(-baja * (t - pico_t))
            pts.append((x0 + t * esc, y0 + h - v * h))
        return pts
    # histamina: pico ~10 min; alérgeno: pico ~15-20 min y más sostenido
    c.poli(curva(9, 0.62, .35, .05, 60), AVISO, 2.4)
    c.poli(curva(17, 0.80, .18, .045, 60), IZQ, 2.4)
    c.t(x0 + 26 * esc, y0 + h - 0.34 * h - 14, 'histamina (control positivo): máximo cerca de los 8–10 min', 8.5, AVISO, 'start', 700)
    c.t(x0 + 26 * esc, y0 + h - 0.80 * h + 4, 'alérgeno: máximo a los 15–20 min', 8.5, IZQ, 'start', 700)
    c.t(x0 + w / 2, 306, 'La pápula desaparece, habitualmente, en cerca de una hora.', 8.5, TINTA)
    c.t(x0 + w / 2, 322, 'Después puede venir una fase tardía (horas), mediada por células y no por IgE; no se usa para leer el examen.', 8, TENUE)
    c.guardar('h27-curso.svg')


def resultado():
    ex = 4.2       # px por mm
    paso = 25 * ex  # 2,5 cm
    c = Lienzo(700, 330)
    c.t(14, 20, 'El mismo antebrazo a los 15 minutos (pápulas a escala)', 10, TINTA, 'start', 700)
    x0, y0 = 36, 40
    c.raw(f'<rect x="{x0}" y="{y0}" width="{4 * paso + 40}" height="{2 * paso + 30}" rx="16" fill="{PIEL}" '
          f'stroke="{PIEL_BORDE}" stroke-width="1.6"/>')
    for k, (sig, nom, a, b) in enumerate(SITIOS):
        f, col = divmod(k, 4)
        x, y = x0 + 40 + col * paso, y0 + 44 + f * (paso + 4)
        pap(c, x, y, a, b, ex, rot=-15 if k % 2 else 10)
        c.raw(f'<circle cx="{x - 34}" cy="{y - 24}" r="8.5" fill="#fff" stroke="{TINTA}" stroke-width="1.2"/>')
        c.t(x - 34, y - 21, str(k + 1), 8.5, TINTA, 'middle', 700)
        mx = max(a, b)
        veredicto = 'control' if sig in ('NEG', 'HIS') else ('positivo' if mx >= SUELO else 'negativo')
        txt = f'{a} × {b} mm' if a else 'sin pápula'
        col_t = AVISO if veredicto == 'positivo' else TINTA
        c.t(x, y + 36, sig, 8.5, TINTA, 'middle', 700)
        c.t(x, y + 47, txt, 8, col_t, 'middle', 700 if veredicto == 'positivo' else 400)
    # escala de 1 cm
    c.l(x0 + 4, y0 + 2 * paso + 52, x0 + 4 + 10 * ex, y0 + 2 * paso + 52, TINTA, 2)
    c.t(x0 + 4 + 5 * ex, y0 + 2 * paso + 66, '1 cm', 8, TENUE)
    # lectura a la derecha
    rx = x0 + 4 * paso + 70
    c.t(rx, 66, 'Lectura', 10, TINTA, 'start', 700)
    lineas = [
        ('Negativo: sin pápula', 'el examen es interpretable', RETRO),
        ('Histamina: 6 mm', 'la piel reaccionó (≥ 3 mm)', RETRO),
        ('Positivos: Dp, Df, gato, pasto', 'pápula ≥ 3 mm', AVISO),
        ('Negativos: perro, Alternaria', 'menos de 3 mm', TINTA),
    ]
    for k, (a, b, col) in enumerate(lineas):
        c.t(rx, 90 + k * 40, a, 8.8, col, 'start', 700)
        c.t(rx, 103 + k * 40, b, 8, TENUE, 'start')
    c.guardar('h27-resultado.svg')


if __name__ == '__main__':
    pos = mapa()
    d = [math.dist(pos[i], pos[i + 1]) / 20 for i in range(3)]
    print('distancia entre punciones (cm):', [round(v, 2) for v in d])
    lectura()
    curso()
    resultado()
    for sig, nom, a, b in SITIOS:
        print(sig, f'{a}x{b}', 'positivo' if max(a, b) >= SUELO and sig not in ('NEG', 'HIS') else '')
