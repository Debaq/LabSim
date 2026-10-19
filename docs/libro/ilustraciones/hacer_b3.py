#!/usr/bin/env python3
"""Dibuja los esquemas propios del capítulo B3 (histología), SVG a mano, no IA:

    b3-coclea-corte.svg    corte de una vuelta de la cóclea con el tejido que daña cada cuadro del libro
    b3-ciliadas.svg        célula ciliada interna y externa (forma, número, hileras, inervación)
    b3-vestibular.svg      células ciliadas vestibulares tipo I y tipo II y capas de una mácula
    b3-mucosas.svg         epitelio respiratorio y epitelio olfatorio, lado a lado
    b3-oido-medio.svg      capas de la membrana timpánica y mucosa del oído medio (sana y con efusión)

Son esquemas didácticos, no medidas a escala. Las cifras que llevan (número de células, proporciones)
salen de la bibliografía del capítulo; el resto es forma y orden de las capas."""
import pathlib

TINTA, TENUE, GRILLA = '#24101a', '#6b6b72', '#e7e5e0'
AZUL, ROJO, VERDE, NARANJA, VIOLETA = '#2b6cb0', '#c62f3a', '#21796c', '#c0571c', '#6b3fa0'
HUESO, HUESO2 = '#e8dfc8', '#d8cba8'
ROSA, ROSA2 = '#f4cfc4', '#e6a899'
AMAR, AMAR2 = '#f6e3a0', '#e5c562'
CELE, CELE2 = '#cfe3f2', '#8fb8d8'
VERD_C, VERD_C2 = '#cfe6cf', '#86b886'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent


class L:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, []

    def add(self, s):
        self.o.append(s)

    def t(self, x, y, s, size=11, color=TINTA, anchor='middle', peso=400, estilo=''):
        e = f' font-style="{estilo}"' if estilo else ''
        size = size * 1.22
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size:.1f}" fill="{color}" '
                 f'text-anchor="{anchor}" font-weight="{peso}"{e}>{s}</text>')

    def linea(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                 f'stroke-width="{w}"{d} stroke-linecap="round"/>')

    def ruta(self, d, fill='none', stroke=TINTA, w=1.2, dash=None, extra=''):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"{da} '
                 f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')

    def rect(self, x, y, w, h, fill='#fff', stroke=TINTA, sw=1, r=3):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def el(self, cx, cy, rx, ry, fill='none', stroke=TINTA, w=1.2):
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{w}"/>')

    def punto(self, x, y, n, color=ROJO, r=11):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="#fff" stroke-width="1.5"/>')
        self.t(x, y + 4, str(n), 12, '#fff', peso=700)

    def rot(self, x, y, tx, ty, texto, ancla='start', color=TINTA, size=11):
        """Rótulo con línea guía: del punto (x, y) al texto (tx, ty)."""
        self.linea(x, y, tx, ty, TENUE, 0.8)
        dx = 4 if ancla == 'start' else -4
        self.t(tx + dx, ty + 4, texto, size, color, ancla)

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.o) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print('  ', nombre)


# ---------------------------------------------------------------- cóclea en corte
def coclea_corte():
    c = L(980, 640)
    S, TX, TY = 1.3, -110, -90

    def P(x, y):
        return S * x + TX, S * y + TY

    c.t(490, 24, 'Una vuelta de la cóclea en corte: tejido y cuadro', 15, peso=700)
    c.add(f'<g transform="translate({TX},{TY}) scale({S})">')
    c.ruta('M100,110 L190,110 L190,430 L100,430 Z', HUESO, HUESO2, 1)       # modiolo
    c.ruta('M690,110 L770,110 L770,430 L690,430 Z', HUESO, HUESO2, 1)       # pared ósea
    c.ruta('M640,150 L690,130 L690,330 L640,330 Z', '#f0d9c4', '#c9a98a', 1)   # ligamento espiral
    c.ruta('M190,110 L690,110 L690,130 L640,150 L300,215 L190,215 Z', CELE, CELE2, 1)           # vestibular
    c.ruta('M190,330 L300,310 L640,310 L640,330 L690,330 L690,430 L190,430 Z', CELE, CELE2, 1)  # timpánica
    c.ruta('M300,215 L640,150 L640,310 L300,310 Z', '#e9f3d6', '#9ab36a', 1)                     # media
    c.ruta('M190,215 L300,215 L330,240 L330,262 L300,262 L300,300 L190,300 Z', '#f0d9c4', '#c9a98a', 1)  # limbo
    c.ruta('M190,300 L300,300 L300,310 L190,330 Z', HUESO, HUESO2, 1)
    c.ruta('M300,215 L640,150', fill='none', stroke=VIOLETA, w=2.2)                              # Reissner
    c.ruta('M640,152 L664,148 L664,308 L640,308 Z', '#e8a87c', '#b5683a', 1.2)                  # estría
    for yy in (180, 230, 280):
        c.el(652, yy, 5, 8, '#c62f3a', '#8a1d26', 0.8)
    c.ruta('M300,308 L640,308', fill='none', stroke=AZUL, w=3)                                   # basilar
    c.ruta('M340,308 L340,262 L350,254 L372,254 L372,262 L396,262 L396,308 Z', '#f8e8c8', '#c9a56a', 1)
    c.ruta('M356,308 L370,262 L384,308 Z', '#fff', '#c9a56a', 1)
    c.ruta('M340,262 L340,240 L350,236 L350,262 Z', AMAR, AMAR2, 1)                              # CCI
    for x in (405, 428, 451):
        c.ruta(f'M{x},266 L{x},238 L{x+13},238 L{x+13},266 Z', ROSA, ROSA2, 1)                   # CCE
        c.ruta(f'M{x+1},266 L{x-3},308 L{x+14},308 L{x+12},266 Z', '#f0e6d8', '#c9a56a', 1)
    c.ruta('M470,308 L470,266 L496,262 L506,308 Z', '#f0e6d8', '#c9a56a', 1)
    c.ruta('M506,308 L520,300 L560,296 L600,308 Z', '#f0e6d8', '#c9a56a', 1)
    c.ruta('M300,225 Q380,205 470,232 L474,244 Q400,228 330,248 L330,236 Z', '#d9d2e8', '#8a7fb0', 1.2)  # tectoria
    for (x, y) in ((125, 280), (145, 298), (162, 282), (128, 322), (152, 326)):
        c.el(x, y, 10, 7.5, '#f6e3a0', '#b89a30', 1)
    c.ruta('M170,300 L300,305', fill='none', stroke=VERDE, w=2)
    c.ruta('M170,290 L318,262', fill='none', stroke=VERDE, w=1.2)
    c.add('</g>')

    def rot(px, py, tx, ty, texto, ancla='start', color=TINTA):
        x, y = P(px, py)
        c.rot(x, y, tx, ty, texto, ancla, color)

    c.t(430, 70, 'escala vestibular (perilinfa)', 11, TENUE)
    c.t(430, 470, 'escala timpánica (perilinfa)', 11, TENUE)
    c.t(560, 232, 'escala media', 10.5, '#5a7a2a')
    c.t(560, 245, '(endolinfa)', 10.5, '#5a7a2a')
    rot(470, 182, 430, 96, 'membrana de Reissner', 'middle', VIOLETA)
    rot(400, 222, 230, 125, 'membrana tectoria', 'end', VIOLETA)
    rot(345, 262, 250, 380, 'CCI', 'end')
    rot(430, 308, 470, 380, 'CCE (3 hileras) sobre las células de Deiters', 'start')
    rot(560, 308, 650, 420, 'membrana basilar', 'start', AZUL)
    rot(652, 190, 800, 175, 'estría vascular', 'start')
    rot(682, 240, 800, 240, 'ligamento espiral', 'start')
    rot(250, 262, 60, 175, 'limbo espiral', 'start')
    rot(125, 322, 30, 420, 'ganglio espiral', 'start')
    c.t(60, 470, 'modiolo', 11, TENUE)
    c.t(865, 470, 'pared ósea', 11, TENUE)
    x, y = P(446, 236); c.punto(x + 4, y - 8, 1, ROJO)
    x, y = P(652, 250); c.punto(x, y, 2, NARANJA)
    x, y = P(676, 285); c.punto(x, y, 3, VERDE)
    x, y = P(560, 165); c.punto(x, y, 4, VIOLETA)
    x, y = P(145, 270); c.punto(x, y, 5, AZUL)
    items = [(ROJO, '1', 'Células ciliadas externas: ruido y ototóxicos (desde la base); presbiacusia sensorial'),
             (NARANJA, '2', 'Estría vascular: presbiacusia estrial; diuréticos de asa'),
             (VERDE, '3', 'Ligamento espiral y células de sostén (uniones comunicantes): conexina 26'),
             (VIOLETA, '4', 'Reissner abombada hacia la rampa vestibular: hidrops de la enfermedad de Ménière'),
             (AZUL, '5', 'Ganglio y sinapsis en cinta: presbiacusia neural; sinaptopatía por ruido')]
    for i, (col, n, tx) in enumerate(items):
        yy = 520 + i * 25
        c.punto(40, yy - 4, n, col, 9)
        c.t(58, yy, tx, 11.5, TINTA, 'start')
    c.guardar("b3-coclea-corte.svg")


# ---------------------------------------------------------------- ciliadas internas y externas
def ciliadas():
    c = L(900, 620)
    c.t(450, 24, 'Célula ciliada interna y externa', 15, peso=700)
    # CCI (matraz)
    cx = 150
    c.ruta(f'M{cx-20},150 Q{cx-30},210 {cx-26},270 Q{cx-24},330 {cx-10},350 L{cx+10},350 '
           f'Q{cx+24},330 {cx+26},270 Q{cx+30},210 {cx+20},150 Z', AMAR, AMAR2, 1.4)
    c.el(cx, 285, 10, 12, '#e5c562', AMAR2, 1)
    # estereocilios CCI: 3 hileras en recta/pared lateral (vista de lado: 3 alturas)
    for i, (dx, h) in enumerate(((-14, 20), (0, 32), (14, 46))):
        c.linea(cx + dx, 150, cx + dx - 3 + i, 150 - h, '#a06020', 3)
    c.ruta(f'M{cx-20},150 L{cx+20},150', stroke='#a06020', w=3)
    # fibras aferentes tipo I (muchas boutons)
    for k in range(4):
        c.linea(cx + 20, 300 + k * 8, cx + 60, 330 + k * 5, VERDE, 2)
        c.el(cx + 20, 300 + k * 8, 3, 3, VERDE, VERDE, 1)
    c.t(cx, 70, 'CCI', 14, peso=700)
    # CCE (cilindro)
    cx2 = 400
    c.ruta(f'M{cx2-16},150 L{cx2-16},320 Q{cx2-16},345 {cx2},345 Q{cx2+16},345 {cx2+16},320 L{cx2+16},150 Z',
           ROSA, ROSA2, 1.4)
    c.el(cx2, 305, 9, 11, '#d98a78', ROSA2, 1)
    # estereocilios en V
    for dx, h in ((-12, 22), (-4, 34), (4, 34), (12, 22)):
        c.linea(cx2 + dx, 150, cx2 + dx * 1.3, 150 - h, '#a06020', 3)
    c.ruta(f'M{cx2-16},150 L{cx2+16},150', stroke='#a06020', w=3)
    # aferente tipo II (una bouton) y eferente grande
    c.el(cx2 + 16, 320, 3, 3, VERDE, VERDE, 1)
    c.linea(cx2 + 16, 320, cx2 + 55, 345, VERDE, 1.4)
    c.ruta(f'M{cx2-16},300 Q{cx2-40},315 {cx2-50},345', stroke=NARANJA, w=3)
    c.el(cx2 - 16, 300, 5, 6, NARANJA, NARANJA, 1)
    c.t(cx2, 70, 'CCE', 14, peso=700)
    # vista superior: lámina reticular
    c.t(705, 70, 'Vista desde la rampa media', 12, peso=700)
    c.rect(540, 90, 330, 150, '#faf7f2', GRILLA, 1)
    for x in (600,):
        pass
    # hilera CCI
    for j in range(5):
        x = 580 + j * 56
        c.el(x, 120, 14, 11, AMAR, AMAR2, 1)
        c.linea(x - 11, 117, x + 11, 117, '#a06020', 2)
        c.linea(x - 11, 121, x + 11, 121, '#a06020', 2)
        c.linea(x - 11, 125, x + 11, 125, '#a06020', 2)
    # tres hileras CCE con haz en W
    for r in range(3):
        for j in range(6):
            x = 575 + j * 50 + r * 12
            y = 165 + r * 26
            c.el(x, y, 9, 9, ROSA, ROSA2, 1)
            c.ruta(f'M{x-8},{y-2} L{x-3},{y+6} L{x+1},{y-2} L{x+5},{y+6} L{x+9},{y-2}', stroke='#a06020', w=1.5)
    c.t(705, 262, '1 hilera interna y 3 externas; haz en W o V', 10.5, TENUE)
    # tabla comparativa
    y0 = 420
    cols = [(60, 'Característica'), (300, 'CCI'), (540, 'CCE')]
    c.rect(40, y0 - 24, 820, 24, '#f2efe8', GRILLA, 1, 0)
    for x, tx in cols:
        c.t(x, y0 - 8, tx, 11.5, peso=700, anchor='start')
    filas = [('Número por cóclea (humano)', '≈ 3.400', '≈ 12.000'),
             ('Hileras', '1', '3'),
             ('Forma de la célula', 'matraz', 'cilindro'),
             ('Aferencias', '90–95 % de las fibras (tipo I)', '5–10 % de las fibras (tipo II)'),
             ('Eferencias', 'sobre la fibra aferente', 'directo sobre la célula'),
             ('Frente al ruido y los ototóxicos', 'más resistente', 'más vulnerable; se pierde desde la base')]
    for i, (a, b, d) in enumerate(filas):
        y = y0 + 20 + i * 26
        c.linea(40, y + 8, 860, y + 8, GRILLA, 1)
        c.t(60, y, a, 11, TINTA, 'start', 600)
        c.t(300, y, b, 11, TINTA, 'start')
        c.t(540, y, d, 11, TINTA, 'start')
    c.guardar('b3-ciliadas.svg')


# ---------------------------------------------------------------- vestibular: tipo I y II
def vestibular():
    c = L(900, 560)
    c.t(450, 24, 'Células ciliadas vestibulares y capas de una mácula', 15, peso=700)
    # Tipo I
    cx = 110
    c.ruta(f'M{cx-8},120 L{cx-8},175 Q{cx-34},210 {cx-30},270 Q{cx-26},330 {cx},335 Q{cx+26},330 {cx+30},270 '
           f'Q{cx+34},210 {cx+8},175 L{cx+8},120 Z', AMAR, AMAR2, 1.4)
    c.el(cx, 280, 12, 14, '#e5c562', AMAR2, 1)
    # cáliz
    c.ruta(f'M{cx-38},250 Q{cx-44},210 {cx-14},168 L{cx-4},172 Q{cx-30},210 {cx-26},250 Z', VERDE, '#146050', 1)
    c.ruta(f'M{cx+38},250 Q{cx+44},210 {cx+14},168 L{cx+4},172 Q{cx+30},210 {cx+26},250 Z', VERDE, '#146050', 1)
    c.linea(cx, 335, cx, 372, VERDE, 3)
    for dx, h in ((-6, 30), (-2, 38), (2, 30), (6, 24)):
        c.linea(cx + dx, 120, cx + dx, 120 - h, '#a06020', 2.5)
    c.linea(cx + 10, 120, cx + 12, 70, '#6b3fa0', 2.5)
    c.t(cx, 395, 'Tipo I', 13, peso=700)
    c.t(cx, 412, 'en matraz, cáliz de una fibra', 10.5, TENUE)
    # Tipo II
    cx2 = 330
    c.ruta(f'M{cx2-18},120 L{cx2-18},320 Q{cx2-18},335 {cx2},335 Q{cx2+18},335 {cx2+18},320 L{cx2+18},120 Z',
           ROSA, ROSA2, 1.4)
    c.el(cx2, 290, 11, 13, '#d98a78', ROSA2, 1)
    for k, y in enumerate((255, 285, 315)):
        c.el(cx2 + 20, y, 5, 5, VERDE, '#146050', 1)
        c.linea(cx2 + 25, y, cx2 + 55, y + 20, VERDE, 1.5)
    c.linea(cx2 + 3, 335, cx2 + 3, 372, NARANJA, 2)
    for dx, h in ((-8, 30), (-3, 38), (2, 30), (7, 24)):
        c.linea(cx2 + dx, 120, cx2 + dx, 120 - h, '#a06020', 2.5)
    c.linea(cx2 + 12, 120, cx2 + 14, 70, '#6b3fa0', 2.5)
    c.t(cx2, 395, 'Tipo II', 13, peso=700)
    c.t(cx2, 412, 'cilíndrica, botones de varias fibras', 10.5, TENUE)
    c.t(220, 60, 'kinocilio', 10.5, '#6b3fa0')
    c.linea(190, 58, 124, 78, '#6b3fa0', 0.8)
    # capas de la mácula (corte)
    x0 = 510
    W = 280
    c.t(x0 + W / 2, 60, 'Mácula (corte)', 12, peso=700)
    c.ruta(f'M{x0},90 Q{x0+W/2},60 {x0+W},90 L{x0+W},125 L{x0},125 Z', '#e7edf5', '#9fb0c8', 1)     # capa de otoconias
    for i in range(26):
        x = x0 + 14 + (i * 10.3) % 255
        y = 82 + ((i * 7) % 3) * 9 + (6 if 80 < (i * 11) % 100 else 0)
        c.ruta(f'M{x-4},{y} L{x},{y-4} L{x+4},{y} L{x},{y+4} Z', '#fff', '#7a8fa8', 0.8)
    c.rect(x0, 125, W, 25, '#dfe9f3', '#9fb0c8', 1, 0)
    c.t(x0 + W / 2, 142, 'membrana otolítica (gel)', 10.5, TENUE)
    # epitelio
    c.rect(x0, 215, W, 55, '#fbeedd', '#d3b48e', 1, 0)
    for j in range(5):
        x = x0 + 30 + j * 55
        c.ruta(f'M{x-9},218 L{x-9},248 Q{x},262 {x+9},248 L{x+9},218 Z', ROSA, ROSA2, 1)
        c.linea(x, 218, x, 152, '#a06020', 2)
        c.linea(x + 7, 218, x + 7, 160, '#6b3fa0', 1.5)
    for j in range(5):
        x = x0 + 8 + j * 55
        c.ruta(f'M{x+6},262 L{x+6},236 L{x+36},236 L{x+36},262 Z', '#f6e8da', '#d3b48e', 0.8)
    c.rect(x0, 270, W, 30, '#f2ecdf', '#d3b48e', 1, 0)
    c.t(x0 + W / 2, 289, 'lámina propia y fibras del nervio', 10.5, TENUE)
    # rótulos
    c.rot(x0 + 250, 98, x0 + W + 12, 100, 'otoconias', 'start')
    c.rot(x0 + 250, 140, x0 + W + 12, 140, 'gel', 'start')
    c.rot(x0 + 230, 190, x0 + W + 12, 190, 'haces ciliares', 'start')
    c.rot(x0 + 250, 235, x0 + W + 12, 235, 'epitelio', 'start')
    c.t(x0 + W / 2, 330, 'Las otoconias se apoyan en el gel,', 10.5, TENUE)
    c.t(x0 + W / 2, 346, 'no en el epitelio', 10.5, TENUE)
    c.t(x0 + W / 2, 380, 'La cúpula de la cresta cubre las células', 10.5, TENUE)
    c.t(x0 + W / 2, 396, 'como un gel, sin otoconias.', 10.5, TENUE)
    # proporción
    c.rect(40, 450, 820, 90, '#faf7f2', GRILLA, 1, 4)
    c.t(60, 474, 'Al nacer, la razón tipo I : tipo II es 2,4 : 1 en las crestas y 1,3 : 1 en las máculas (Merchant y cols., 2000).', 10.5, TINTA, 'start')
    c.t(60, 496, 'Las tipo I se pierden con la edad más rápido en las crestas que en las máculas; las tipo II, al mismo ritmo.', 10.5, TINTA, 'start')
    c.t(60, 518, 'Las fibras que solo forman cálices están en la zona central de la cresta y en la estriola (Eatock y Songer, 2011).', 10.5, TINTA, 'start')
    c.guardar('b3-vestibular.svg')


# ---------------------------------------------------------------- mucosas
def mucosas():
    c = L(900, 660)
    c.t(450, 24, 'Dos epitelios de la nariz', 15, peso=700)
    W = 390

    def marco(x0, titulo):
        c.t(x0 + W / 2, 56, titulo, 13.5, peso=700)

    # ---------- respiratoria
    x0 = 30
    marco(x0, 'Mucosa respiratoria')
    yt = 100
    c.rect(x0, yt - 14, W, 14, '#cfe3f2', '#8fb8d8', 1, 0)
    c.rect(x0, yt, W, 100, '#fbe6e1', '#e0a898', 1, 0)
    xs = [x0 + 35 + i * 64 for i in range(6)]
    for i, x in enumerate(xs):
        if i in (1, 4):
            c.ruta(f'M{x-10},{yt} Q{x-20},{yt+22} {x-4},{yt+34} L{x-4},{yt+100} L{x+4},{yt+100} L{x+4},{yt+34} Q{x+20},{yt+22} {x+10},{yt} Z',
                   '#d9e3f5', '#7a8fb8', 1)
        else:
            c.ruta(f'M{x-12},{yt} L{x-12},{yt+80} L{x+12},{yt+80} L{x+12},{yt} Z', '#f6c9bd', '#d68a78', 1)
            for k in range(-4, 5):
                c.linea(x + k * 2.7, yt, x + k * 2.7, yt - 11, '#a06020', 1)
            c.el(x, yt + 52, 7, 9, '#c57a68', '#9a5040', 1)
    for i in range(6):
        x = x0 + 60 + i * 64
        c.ruta(f'M{x-10},{yt+100} Q{x},{yt+74} {x+10},{yt+100} Z', '#e0b8a8', '#b07060', 1)
    c.linea(x0, yt + 100, x0 + W, yt + 100, '#8a4a30', 3)
    c.rect(x0, yt + 103, W, 230, '#fdf3ea', '#e5cdb5', 1, 0)
    for gx, gy in ((x0 + 80, yt + 175), (x0 + 310, yt + 190)):
        c.el(gx, gy, 28, 18, '#e9d4ef', '#9c78b0', 1.2)
        c.linea(gx, gy - 18, gx, yt + 101, '#9c78b0', 2.5)
    for kx in range(6):
        c.el(x0 + 40 + kx * 64, yt + 120, 7, 4.5, '#c62f3a', '#8a1d26', 1)
    for sx, sy in ((x0 + 170, yt + 205), (x0 + 250, yt + 250), (x0 + 120, yt + 275), (x0 + 330, yt + 295),
                   (x0 + 200, yt + 305)):
        c.el(sx, sy, 32, 13, '#7aa0d8', '#2b5ca0', 1.2)
    c.punto(x0 + W - 18, yt - 7, 1, '#2b6cb0', 8)
    c.punto(xs[0] + 20, yt - 22, 2, '#a06020', 8)
    c.punto(xs[5] + 22, yt + 50, 3, ROJO, 8)
    c.punto(xs[4] - 22, yt + 50, 4, '#5a6fa0', 8)
    c.punto(x0 + 60 + 4 * 64 + 22, yt + 92, 5, '#8a4a30', 8)
    c.punto(x0 + 18, yt + 100, 6, '#6a3a20', 8)
    c.punto(x0 + 118, yt + 175, 7, VIOLETA, 8)
    c.punto(x0 + 170, yt + 235, 8, '#2b5ca0', 8)
    # ---------- olfatoria
    x1 = 480
    marco(x1, 'Mucosa olfatoria')
    c.rect(x1, yt - 14, W, 14, '#cfe3f2', '#8fb8d8', 1, 0)
    c.rect(x1, yt, W, 140, '#f6efd8', '#d8c58a', 1, 0)
    for i in range(7):
        x = x1 + 30 + i * 55
        c.ruta(f'M{x-8},{yt} L{x-8},{yt+130} L{x+8},{yt+130} L{x+8},{yt} Z', '#efe3b8', '#bfae6a', 1)
        c.el(x, yt + 26, 6, 8, '#b8a050', '#8a7a30', 1)
    for i in range(6):
        x = x1 + 58 + i * 55
        c.linea(x, yt + 4, x, yt + 52, '#d49a2a', 2.2)
        c.el(x, yt + 3, 4.5, 4.5, '#d49a2a', '#d49a2a', 1)
        for k in (-1, 0, 1):
            c.linea(x + k * 2, yt - 1, x + k * 15, yt - 13, '#a06020', 0.9)
        c.el(x, yt + 82, 8, 11, '#e5b84a', '#a07818', 1)
        c.linea(x, yt + 93, x, yt + 160, '#d49a2a', 1.8)
    for i in range(7):
        x = x1 + 22 + i * 55
        c.ruta(f'M{x-10},{yt+140} Q{x},{yt+114} {x+10},{yt+140} Z', '#d6c07a', '#8a7a30', 1)
    c.linea(x1, yt + 140, x1 + W, yt + 140, '#8a6a20', 3)
    c.rect(x1, yt + 143, W, 190, '#fdf6e8', '#e5d5a8', 1, 0)
    for gx, gy in ((x1 + 95, yt + 205), (x1 + 300, yt + 235)):
        c.el(gx, gy, 28, 18, '#e9d4ef', '#9c78b0', 1.2)
        c.linea(gx, gy - 18, gx, yt + 141, '#9c78b0', 2.5)
    for fx, fy in ((x1 + 170, yt + 250), (x1 + 245, yt + 195), (x1 + 120, yt + 290)):
        c.el(fx, fy, 26, 13, '#f6e3a0', '#b89a30', 1.2)
        for k in (-10, -4, 2, 8):
            c.el(fx + k, fy, 2.4, 2.4, '#d49a2a', '#d49a2a', 1)
    c.punto(x1 + W - 18, yt - 7, 1, '#2b6cb0', 8)
    c.punto(x1 + 58 + 15 + 12, yt - 20, 2, '#a06020', 8)
    c.punto(x1 + 58 + 4 * 55 + 22, yt + 82, 3, '#a07818', 8)
    c.punto(x1 + 30 + 5 * 55 + 22, yt + 40, 4, '#8a7a30', 8)
    c.punto(x1 + 22 + 5 * 55 + 24, yt + 134, 5, '#8a6a20', 8)
    c.punto(x1 + 18, yt + 140, 6, '#6a3a20', 8)
    c.punto(x1 + 124, yt + 205, 7, VIOLETA, 8)
    c.punto(x1 + 205, yt + 250, 8, '#a07818', 8)
    # ---------- leyenda
    y0 = 470
    izq = ['moco', 'cilios', 'célula ciliada', 'célula caliciforme (moco)', 'célula basal (reserva)',
           'membrana basal', 'glándula seromucosa', 'seno venoso (tejido eréctil del cornete)']
    der = ['moco de las glándulas de Bowman', 'cilios largos sin movimiento (el receptor)',
           'neurona olfatoria (bipolar): su axón cruza la lámina cribosa', 'célula sustentacular',
           'célula basal (da neuronas nuevas)', 'membrana basal', 'glándula de Bowman',
           'haz de axones (filete olfatorio) con células envolventes']
    for i, (a_, b_) in enumerate(zip(izq, der)):
        y = y0 + i * 23
        colores = ['#2b6cb0', '#a06020', ROJO, '#5a6fa0', '#8a4a30', '#6a3a20', VIOLETA, '#2b5ca0']
        c.punto(40, y - 4, i + 1, colores[i], 8)
        c.t(56, y, a_, 11, TINTA, 'start')
        c.punto(490, y - 4, i + 1, ['#2b6cb0', '#a06020', '#a07818', '#8a7a30', '#8a6a20', '#6a3a20', VIOLETA, '#a07818'][i], 8)
        c.t(506, y, b_, 11, TINTA, 'start')
    c.guardar('b3-mucosas.svg')


# ---------------------------------------------------------------- oído medio y membrana timpánica
def oido_medio():
    c = L(900, 560)
    c.t(450, 24, 'Membrana timpánica y mucosa del oído medio', 15, peso=700)
    c.t(260, 56, 'A. Capas de la membrana timpánica', 13, peso=700)
    c.t(710, 56, 'B. Mucosa del oído medio', 13, peso=700)

    def capas(x0, w, y0, fibrosa, titulo, placa=False):
        c.t(x0 + w / 2, y0 - 10, titulo, 11.5, peso=700)
        c.rect(x0, y0, w, 18, '#f2d0b8', '#c9946c', 1, 0)
        h = 44 if fibrosa else 22
        c.rect(x0, y0 + 18, w, h, '#f7edd5', '#cfbf8a', 1, 0)
        if fibrosa:
            for k in range(5):
                c.linea(x0 + 6, y0 + 26 + k * 8, x0 + w - 6, y0 + 26 + k * 8, '#b8a050', 1.2)
            for k in range(7):
                c.el(x0 + 20 + k * (w - 40) / 6, y0 + 40, 2.5, 9, '#b8a050', '#b8a050', 1)
        c.rect(x0, y0 + 18 + h, w, 12, '#e3eef8', '#8fb8d8', 1, 0)
        if placa:
            c.ruta(f'M{x0+w*0.38},{y0+24} L{x0+w*0.7},{y0+24} L{x0+w*0.68},{y0+56} L{x0+w*0.4},{y0+56} Z',
                   '#fff', '#555', 1.5)

    capas(40, 260, 100, True, 'Pars tensa')
    c.rot(290, 109, 312, 109, 'epidérmica (epitelio plano estratificado)', 'start')
    c.rot(290, 140, 312, 140, 'lámina propia: fibras radiales y circulares', 'start')
    c.rot(290, 170, 312, 170, 'mucosa (epitelio plano o cúbico)', 'start')
    capas(40, 260, 250, False, 'Pars flaccida')
    c.t(170, 318, 'lámina propia fina y laxa', 10.5, TENUE)
    capas(40, 260, 390, True, 'Timpanoesclerosis')
    c.ruta('M142,414 L220,414 L216,446 L148,446 Z', '#fff', '#555', 1.5)
    c.rot(185, 430, 312, 430, 'placa: colágeno hialinizado con calcio', 'start')
    c.t(170, 480, 'dentro de la lámina propia', 10.5, TENUE)

    def muc(x0, y0, titulo, enfermo):
        w = 250
        c.t(x0 + w / 2, y0 - 10, titulo, 11.5, peso=700)
        base = y0 + 90
        c.rect(x0, base, w, 22, '#f2ecdf', '#d3b48e', 1, 0)
        for i in range(6):
            x = x0 + 22 + i * 41
            if enfermo and i in (1, 3, 5):
                c.ruta(f'M{x-9},{base} Q{x-15},{base-18} {x-3},{base-34} L{x-3},{base-66} L{x+3},{base-66} L{x+3},{base-34} Q{x+15},{base-18} {x+9},{base} Z',
                       '#d9e3f5', '#7a8fb8', 1)
            elif enfermo or i % 2 == 0:
                hh = 60 if enfermo else 26
                c.ruta(f'M{x-10},{base} L{x-10},{base-hh} L{x+10},{base-hh} L{x+10},{base} Z', '#f6c9bd', '#d68a78', 1)
                for k in (-3, 0, 3):
                    c.linea(x + k * 2.5, base - hh, x + k * 2.5, base - hh - 8, '#a06020', 1)
            else:
                c.ruta(f'M{x-10},{base} L{x-10},{base-12} L{x+10},{base-12} L{x+10},{base} Z', '#cfe3f2', '#8fb8d8', 1)
        if enfermo:
            c.rect(x0, y0 - 2, w, 16, '#f3e6b8', '#cfbf8a', 1, 0)
            c.t(x0 + w / 2, y0 + 10, 'efusión', 10, TENUE)

    muc(585, 130, 'Sana', False)
    c.t(710, 255, 'epitelio plano o cúbico, con zonas ciliadas', 10.5, TENUE)
    muc(585, 330, 'Otitis con efusión', True)
    c.t(710, 455, 'epitelio más alto, ciliado, con más caliciformes', 10.5, TENUE)
    c.t(710, 500, 'Caliciformes (azul): Tos y Bak-Pedersen, 1977', 10.5, TENUE)
    c.t(710, 516, 'Tipos de epitelio por zona: Sadé, 1966', 10.5, TENUE)
    c.guardar('b3-oido-medio.svg')


if __name__ == '__main__':
    print('dibujando B3...')
    coclea_corte()
    ciliadas()
    vestibular()
    mucosas()
    oido_medio()
