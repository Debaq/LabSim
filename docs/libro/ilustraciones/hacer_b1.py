#!/usr/bin/env python3
"""Dibuja los esquemas propios del capítulo B1 (anatomía), SVG a mano, no IA:

    b1-pabellon.svg        relieves del pabellón auricular (oído derecho, vista lateral)
    b1-membrana.svg        A: membrana timpánica derecha vista por otoscopía; B: dónde cae cada hallazgo
    b1-trompa.svg          trompa de Eustaquio del lactante y del adulto (esquema lateral)
    b1-via-auditiva.svg    vía auditiva central y generadores habituales del PEAT
    b1-via-vestibular.svg  vías vestibulares centrales
    b1-irrigacion.svg      arterias del oído interno
    b1-valvula.svg         A: pirámide nasal (vista lateral); B: la válvula nasal interna en corte frontal

Son esquemas didácticos, no medidas: las cifras que llevan salen de la bibliografía del capítulo."""
import math
import pathlib

TINTA, TENUE, GRILLA = '#24101a', '#6b6b72', '#e7e5e0'
PIEL, PIEL2, HUESO = '#f2cdb8', '#e3a98f', '#e8dfc8'
AZUL, ROJO, VERDE, NARANJA, VIOLETA = '#2b6cb0', '#c62f3a', '#21796c', '#c0571c', '#6b3fa0'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent


class L:
    def __init__(self, w, h):
        self.w, self.h, self.o, self.defs = w, h, [], []

    def add(self, s):
        self.o.append(s)

    def t(self, x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
                 f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def linea(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, flecha=False):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        m = f' marker-end="url(#fl{color[1:]})"' if flecha else ''
        if flecha:
            self.flecha(color)
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                 f'stroke-width="{w}"{d}{m} stroke-linecap="round"/>')

    def flecha(self, color):
        i = f'fl{color[1:]}'
        if not any(i in d for d in self.defs):
            self.defs.append(f'<marker id="{i}" markerWidth="8" markerHeight="8" refX="6" refY="3.5" '
                             f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" '
                             f'fill="{color}"/></marker>')

    def ruta(self, d, fill='none', stroke=TINTA, w=1.2, dash=None, extra=''):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"{da} '
                 f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')

    def caja(self, x, y, w, h, texto, fill='#fff', stroke=TINTA, size=10.5, color=TINTA, peso=600, r=6):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="1.2"/>')
        lineas = texto.split('\n')
        y0 = y + h / 2 - (len(lineas) - 1) * size * 0.6 + size * 0.35
        for i, s in enumerate(lineas):
            self.t(x + w / 2, y0 + i * size * 1.2, s, size, color, 'middle', peso)

    def elipse(self, cx, cy, rx, ry, fill='none', stroke=TINTA, w=1.2, dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{w}"{da}/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><defs>{"".join(self.defs)}</defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.o) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def rotulo(c, x, y, tx, ty, texto, ancla='start', color=TINTA, size=11):
    """Texto en (tx, ty) con una línea fina hasta el punto (x, y) de la figura. La línea llega al borde
    del texto más cercano, no lo atraviesa."""
    import re
    primero = re.sub(r'<[^>]+>', '', texto.split('<tspan')[0])
    ancho = len(primero) * size * 0.58
    if tx + ancho < x:           # texto a la izquierda del punto: la línea sale de su borde derecho
        ex = tx + 4 + ancho + 3
    else:
        ex = tx - 1
    c.linea(x, y, ex, ty, color, 0.9)
    c.add(f'<circle cx="{x}" cy="{y}" r="2.2" fill="{color}"/>')
    c.t(tx + 4, ty + 4, texto, size, color, ancla, 600)


# ---------------------------------------------------------------- pabellón
def pabellon():
    c = L(520, 470)
    c.t(14, 22, 'Pabellón auricular derecho, vista lateral', 12.5, TINTA, 'start', 700)
    cont = ('M170,95 C120,75 105,150 112,225 C118,285 128,335 150,372 C160,392 182,398 198,382 '
            'C212,366 214,335 226,300 C246,245 262,150 170,95 Z')
    c.defs.append('<clipPath id="clh"><polygon points="0,0 520,0 520,215 236,215 236,470 0,470"/></clipPath>')
    c.ruta(cont, PIEL, '#b98068', 1.6)
    # hélix: borde enrollado, un poco por dentro del contorno
    c.add('<g clip-path="url(#clh)" transform="translate(172 250) scale(.9) translate(-172 -250)">')
    c.ruta(cont, 'none', '#c79880', 9)
    c.add('</g>')
    # fosa escafoidea
    c.ruta('M158,205 C152,170 162,140 185,128 C215,120 232,150 234,190 C234,225 226,262 216,290',
           'none', '#c99882', 1.1, '3 3')
    # antihélix y sus dos ramas
    c.ruta('M200,312 C184,270 168,240 160,212 C156,188 168,168 190,160', 'none', '#a8705a', 5)
    c.ruta('M190,160 C178,146 180,132 194,128', 'none', '#a8705a', 5)
    c.ruta('M190,160 C210,160 222,172 224,192', 'none', '#a8705a', 5)
    # concha, conducto, trago y antitrago
    c.ruta('M180,226 C172,256 186,300 210,298 C232,296 238,262 224,238 C210,214 184,210 180,226 Z',
           PIEL2, '#a8705a', 1.2)
    c.elipse(206, 262, 12, 16, '#8b4a3a', '#5a2c20', 1)
    c.ruta('M236,236 C248,236 254,250 248,264 C242,274 232,270 230,258 C229,246 230,240 236,236 Z',
           PIEL, '#a8705a', 1.4)
    c.ruta('M200,314 C208,326 222,320 220,306 C216,298 206,300 200,314 Z', PIEL, '#a8705a', 1.4)
    c.elipse(170, 376, 26, 17, 'none', '#c99882', 1, '3 3')
    rotulo(c, 132, 150, 20, 58, 'Hélix', 'start')
    rotulo(c, 166, 150, 20, 98, 'Fosa escafoidea', 'start')
    rotulo(c, 162, 214, 20, 160, 'Antihélix', 'start')
    rotulo(c, 205, 163, 280, 70, 'Ramas del antihélix y<tspan x="284" dy="14">fosa triangular entre ellas</tspan>', 'start')
    rotulo(c, 190, 280, 20, 250, 'Concha', 'start')
    rotulo(c, 206, 262, 290, 335, 'Conducto auditivo externo', 'start')
    rotulo(c, 246, 250, 330, 212, 'Trago', 'start')
    rotulo(c, 214, 312, 290, 372, 'Antitrago', 'start')
    rotulo(c, 170, 384, 20, 430, 'Lóbulo (sin cartílago)', 'start')
    c.t(500, 452, 'Esquema, no a escala', 9, TENUE, 'end')
    c.guardar('b1-pabellon.svg')


# ---------------------------------------------------------------- membrana timpánica
def tm(c, cx, cy, s=1.0, zona=None, rotulos=False):
    """Membrana timpánica derecha vista por otoscopía (anterior a la derecha). zona: None, 'central',
    'marginal', 'atico'."""
    rx, ry = 105 * s, 120 * s
    c.elipse(cx, cy, rx, ry, '#d9b9b0', '#8a5a4a', 1.6)
    # anillo
    c.elipse(cx, cy, rx - 5 * s, ry - 5 * s, 'none', '#b78d80', 1, '2 2')
    # umbo y mango (≈ 20° hacia adelante)
    ux, uy = cx, cy + 10 * s
    a = math.radians(20)
    px, py = ux + 100 * s * math.sin(a), uy - 100 * s * math.cos(a)
    # pars flaccida: sobre la apófisis corta
    pf = (f'M{px - 34 * s:.1f},{py - 4 * s:.1f} C{px - 26 * s:.1f},{py - 26 * s:.1f} {px + 28 * s:.1f},{py - 28 * s:.1f} '
          f'{px + 38 * s:.1f},{py - 2 * s:.1f} Z')
    c.ruta(pf, '#e9a9a0', '#8a5a4a', 1)
    # pliegues maleolares
    c.linea(px, py, px - 34 * s, py - 4 * s, '#8a5a4a', 1)
    c.linea(px, py, px + 38 * s, py - 2 * s, '#8a5a4a', 1)
    # yunque tras la membrana (posterosuperior)
    c.ruta(f'M{ux - 42 * s:.1f},{uy - 52 * s:.1f} C{ux - 38 * s:.1f},{uy - 18 * s:.1f} {ux - 30 * s:.1f},{uy - 4 * s:.1f} '
           f'{ux - 24 * s:.1f},{uy + 2 * s:.1f}', 'none', '#fff', 5 * s, extra='opacity=".6"')
    # mango
    c.linea(ux, uy, px, py, '#fff', 8 * s)
    c.linea(ux, uy, px, py, '#a58a7e', 1.2 * s)
    c.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{4.2 * s:.1f}" fill="#fff" stroke="#a58a7e"/>')
    c.add(f'<circle cx="{ux:.1f}" cy="{uy:.1f}" r="{3.6 * s:.1f}" fill="#fff" stroke="#a58a7e"/>')
    # cono luminoso hacia las 5
    b = math.radians(150)
    fx, fy = ux + 98 * s * math.sin(b), uy - 98 * s * math.cos(b)
    nx, ny = math.cos(b), math.sin(b)
    c.ruta(f'M{ux:.1f},{uy:.1f} L{fx + 16 * s * nx:.1f},{fy + 16 * s * ny:.1f} '
           f'L{fx - 16 * s * nx:.1f},{fy - 16 * s * ny:.1f} Z', '#fffbe6', 'none', 0, extra='opacity=".95"')
    if zona == 'central':
        c.elipse(cx - 28 * s, cy + 42 * s, 20 * s, 15 * s, '#2a1a1a', ROJO, 2)
    elif zona == 'marginal':
        c.ruta(f'M{cx - rx + 4:.1f},{cy + 10 * s:.1f} C{cx - rx + 22 * s:.1f},{cy - 4 * s:.1f} '
               f'{cx - rx + 30 * s:.1f},{cy + 52 * s:.1f} {cx - rx + 9 * s:.1f},{cy + 56 * s:.1f} Z', '#2a1a1a', ROJO, 2)
    elif zona == 'atico':
        c.elipse(px + 2 * s, py - 14 * s, 17 * s, 10 * s, '#5a3a35', ROJO, 2)
    return ux, uy, px, py, fx, fy


def membrana():
    c = L(700, 430)
    c.t(14, 22, 'A · Membrana timpánica derecha, vista por otoscopía', 12, TINTA, 'start', 700)
    ux, uy, px, py, fx, fy = tm(c, 215, 225, 1.25)
    # ejes de los cuadrantes
    a = math.radians(20)
    s = 1.25
    c.linea(ux - 120 * s * math.sin(a), uy + 120 * s * math.cos(a), ux + 110 * s * math.sin(a), uy - 110 * s * math.cos(a),
            ROJO, 1, '5 4')
    c.linea(ux - 108 * s * math.cos(a), uy - 108 * s * math.sin(a), ux + 108 * s * math.cos(a), uy + 108 * s * math.sin(a),
            ROJO, 1, '5 4')
    c.t(300, 135, 'AS', 11, ROJO, 'middle', 700)
    c.t(122, 135, 'PS', 11, ROJO, 'middle', 700)
    c.t(300, 345, 'AI', 11, ROJO, 'middle', 700)
    c.t(122, 345, 'PI', 11, ROJO, 'middle', 700)
    rotulo(c, px + 14, py - 14, 330, 52, 'Pars flaccida (de Shrapnell)')
    rotulo(c, px, py + 4, 360, 84, 'Apófisis corta del martillo')
    rotulo(c, (ux + px) / 2 - 3, (uy + py) / 2, 360, 116, 'Mango del martillo')
    rotulo(c, ux, uy, 20, 262, 'Umbo', 'start', size=11)
    rotulo(c, (ux + fx) / 2, (uy + fy) / 2, 340, 345, 'Cono luminoso (5 h)')
    rotulo(c, 215 + 90 * 1.25 * 0.35, 225 + 60 * 1.25, 350, 280, 'Pars tensa')
    rotulo(c, ux - 36, uy - 36, 20, 76, 'Rama larga del yunque<tspan x="24" dy="14">(se transparenta)</tspan>', 'start')
    c.t(215, 412, 'AS anterosuperior · PS posterosuperior · AI anteroinferior · PI posteroinferior', 9.5, TENUE)
    # panel B
    c.t(470, 150, 'B · Dónde cae cada hallazgo', 12, TINTA, 'start', 700)
    # tres miniaturas en una fila
    for i, (z, tit, sub) in enumerate([('central', 'Perforación central', 'pars tensa;\nanillo intacto'),
                                       ('marginal', 'Perforación marginal', 'llega al anillo\ntimpánico'),
                                       ('atico', 'Bolsa de retracción', 'pars flaccida,\nen el ático')]):
        x = 438 + i * 85
        tm(c, x, 238, 0.36, z)
        c.t(x, 298, tit.split(' ')[0], 9.5, TINTA, 'middle', 700)
        c.t(x, 310, ' '.join(tit.split(' ')[1:]), 9.5, TINTA, 'middle', 700)
        for j, ln in enumerate(sub.split('\n')):
            c.t(x, 326 + j * 11.5, ln, 8.5, TENUE)
    c.t(570, 375, '→ cap. 2 y cap. 3', 10, TENUE)
    c.t(570, 395, 'Esquema, no a escala', 9, TENUE)
    c.guardar('b1-membrana.svg')


# ---------------------------------------------------------------- trompa
def trompa():
    c = L(700, 330)

    def panel(x0, ang, largo, frac_oseo, tit, sub, txt):
        c.t(x0, 22, tit, 12, TINTA, 'start', 700)
        c.t(x0, 38, sub, 9.5, TENUE, 'start')
        ox, oy = x0 + 20, 100            # caja timpánica
        a = math.radians(ang)
        ex, ey = ox + largo * math.cos(a), oy + largo * math.sin(a)
        c.linea(ox, oy, ox + 280, oy, TENUE, 1, '4 4')
        mx, my = ox + largo * frac_oseo * math.cos(a), oy + largo * frac_oseo * math.sin(a)
        c.linea(ox, oy, mx, my, '#b9a37a', 14)
        c.linea(mx, my, ex, ey, '#7fb3d5', 14)
        c.elipse(ox - 6, oy, 26, 30, '#f7e9e4', '#8a5a4a', 1.4)
        c.t(ox - 6, oy + 3, 'oído', 9, TENUE)
        c.ruta(f'M{ex - 4:.1f},{ey - 14:.1f} L{ex + 40:.1f},{ey - 14:.1f} L{ex + 40:.1f},{ey + 70:.1f} L{ex - 4:.1f},{ey + 50:.1f}',
               '#f3dede', '#8a5a4a', 1.2)
        c.t(ex + 18, ey + 24, 'rino-', 9, TENUE)
        c.t(ex + 18, ey + 35, 'faringe', 9, TENUE)
        c.t((ox + ex) / 2 + (0 if ang < 20 else 40), oy + (ey - oy) / 2 + 34, txt, 10, TINTA, 'middle', 600)
    panel(20, 10, 160, 0.11, 'Lactante', 'más corta y más cerca de la horizontal', 'largo ≈ 21 mm (3 meses)')
    panel(360, 40, 240, 0.2, 'Adulto', 'más larga e inclinada hacia abajo', 'largo ≈ 37 mm')
    c.add('<rect x="22" y="250" width="14" height="10" fill="#b9a37a"/>')
    c.t(42, 259, 'porción ósea (la más corta; relativamente más corta aún en el lactante)', 10, TINTA, 'start')
    c.add('<rect x="22" y="268" width="14" height="10" fill="#7fb3d5"/>')
    c.t(42, 277, 'porción de transición y cartilaginosa-membranosa (hacia la rinofaringe)', 10, TINTA, 'start')
    c.t(22, 300, 'Esquema. Largos y proporciones de Ishijima y cols. (2000); el ángulo está exagerado para que se vea.', 9, TENUE, 'start')
    c.guardar('b1-trompa.svg')


# ---------------------------------------------------------------- vía auditiva
def via_auditiva():
    c = L(720, 600)
    c.t(14, 22, 'Vía auditiva central (esquema frontal, simplificado)', 12.5, TINTA, 'start', 700)
    xi, xd = 170, 400            # columna izquierda y derecha del esquema
    niveles = [(60, 'Corteza auditiva\n(giro de Heschl)'), (140, 'Cuerpo geniculado\nmedial'),
               (220, 'Colículo inferior'), (300, 'Lemnisco lateral\n(y sus núcleos)'),
               (380, 'Complejo olivar\nsuperior'), (460, 'Núcleo coclear\n(ventral y dorsal)')]
    W, H = 118, 40
    ys = {}
    for y, tx in niveles:
        ys[tx] = y
        for x, col in ((xi, '#fff'), (xd, '#fff')):
            c.caja(x - W / 2, y, W, H, tx, col, TINTA, 10)
    # conexiones: ipsilaterales y cruces
    cola = NARANJA
    # oído izquierdo estimulado (naranja); sus fibras suben por ambos lados, más por el contralateral
    c.linea(xi, 540, xi, 500, cola, 2.2, flecha=True)
    c.linea(xi, 460, xi - 0, 420, cola, 2, flecha=True)                       # CN -> SOC ipsi
    c.linea(xi + 14, 462, xd - 14, 420, cola, 2.6, flecha=True)               # CN -> SOC contra (cruce)
    for y1, y2 in ((380, 340), (300, 260), (220, 180), (140, 100)):
        c.linea(xi, y1, xi, y2, '#9a9a9a', 1.8, flecha=True)
        c.linea(xd, y1, xd, y2, '#9a9a9a', 1.8, flecha=True)
    # comisura y cuerpo calloso
    c.linea(xi + W / 2, 240, xd - W / 2, 240, TENUE, 1.2, '4 3')
    c.t((xi + xd) / 2, 234, 'comisura', 9, TENUE)
    c.linea(xi + W / 2, 80, xd - W / 2, 80, VIOLETA, 1.6, '4 3')
    c.t((xi + xd) / 2, 74, 'cuerpo calloso', 9.5, VIOLETA, 'middle', 600)
    # oídos
    c.caja(xi - 52, 540, 104, 30, 'Oído izquierdo\n(nervio VIII)', '#fff', NARANJA, 9.5, NARANJA, 600)
    c.caja(xd - 52, 540, 104, 30, 'Oído derecho\n(nervio VIII)', '#fff', '#9a9a9a', 9.5, TENUE, 600)
    c.linea(xd, 540, xd, 500, '#9a9a9a', 1.8, flecha=True)
    c.linea(xd, 460, xd, 420, '#9a9a9a', 1.8, flecha=True)
    c.linea(xd - 14, 462, xi + 14, 420, '#9a9a9a', 1.8, flecha=True)
    # ondas del PEAT (generadores habituales)
    xr = 500
    c.t(xr, 50, 'Onda del PEAT', 11, TINTA, 'start', 700)
    c.t(xr, 64, '(generador habitual)', 9.5, TENUE, 'start')
    ondas = [(550, 'I', 'nervio VIII distal'), (510, 'II', 'nervio VIII proximal'),
             (470, 'III', 'núcleo coclear'), (400, 'IV', 'complejo olivar superior'),
             (280, 'V', 'lemnisco lateral, al llegar\nal colículo inferior')]
    for y, w, tx in ondas:
        c.add(f'<circle cx="{xr + 12}" cy="{y}" r="13" fill="{AZUL}"/>')
        c.t(xr + 12, y + 4, w, 9.5 if len(w) > 1 else 11, '#fff', 'middle', 700)
        for j, ln in enumerate(tx.split('\n')):
            c.t(xr + 32, y - 2 + j * 12.5, ln, 10, TINTA, 'start')
    c.t(xr, 574, 'Desde el núcleo coclear, cada oído', 9.5, TENUE, 'start')
    c.t(xr, 587, 'llega a los dos lados del tronco.', 9.5, TENUE, 'start')
    # nota abajo izquierda
    c.guardar('b1-via-auditiva.svg')


# ---------------------------------------------------------------- vía vestibular
def via_vestibular():
    c = L(720, 470)
    c.t(14, 22, 'Vías vestibulares centrales (esquema)', 12.5, TINTA, 'start', 700)
    c.caja(10, 190, 150, 56, 'Laberinto\n(3 canales, utrículo,\nsáculo)', '#fff', AZUL, 10, AZUL)
    c.caja(190, 190, 110, 56, 'Nervio\nvestibular\n(VIII par)', '#fff', AZUL, 10, AZUL)
    c.linea(160, 218, 190, 218, AZUL, 2, flecha=True)
    c.caja(340, 170, 120, 96, 'Núcleos\nvestibulares\n(superior, medial,\nlateral, inferior)\nen el tronco', '#ffe9d5', NARANJA, 10)
    c.linea(300, 218, 340, 218, AZUL, 2, flecha=True)
    destinos = [
        (30, 'Núcleos oculomotores\n(III, IV y VI)', 'por el fascículo\nlongitudinal medial', 'reflejo vestíbulo-ocular', VERDE),
        (115, 'Médula espinal', 'vías vestibuloespinales\nlateral y medial', 'postura y equilibrio', VERDE),
        (200, 'Cerebelo\n(flóculo y nódulo)', 'conexión de ida y vuelta', 'calibra y suprime', VIOLETA),
        (285, 'Tálamo y corteza\nvestibular', 'vía ascendente', 'percepción del movimiento', VIOLETA),
        (370, 'Formación reticular\ny núcleo del vago', 'conexiones autonómicas', 'náusea, palidez, sudor', TENUE),
    ]
    for y, d, via, fn, col in destinos:
        c.caja(520, y, 180, 56, d, '#fff', col, 10, col)
        c.linea(460, 218, 520, y + 28, col, 1.8, flecha=True)
        c.t(490, y + 14, '', 9)
        c.t(612, y + 70 - 6 - 5, '', 9)
    # leyendas de función bajo cada caja (a la derecha no hay espacio: van entre comillas pequeñas)
    for y, d, via, fn, col in destinos:
        c.t(520 + 90, y + 69, fn, 9, TENUE, 'middle')
    for i, ln in enumerate(['Los núcleos vestibulares comparan lo que dicen', 'los dos laberintos: cada canal informa en su',
                            'plano y los pares coplanares trabajan en oposición.']):
        c.t(20, 330 + i * 15, ln, 10.5, TINTA, 'start', 600 if i == 0 else 400)
    for i, ln in enumerate(['Rama superior del nervio: utrículo y canales superior y lateral.',
                            'Rama inferior: sáculo y canal posterior.']):
        c.t(20, 392 + i * 14, ln, 9.5, TENUE, 'start')
    c.t(20, 456, 'Esquema simplificado, no a escala', 9, TENUE, 'start')
    c.guardar('b1-via-vestibular.svg')


# ---------------------------------------------------------------- irrigación
def irrigacion():
    c = L(720, 430)
    c.t(14, 22, 'Irrigación del oído interno', 12.5, TINTA, 'start', 700)
    c.caja(20, 180, 100, 40, 'Arteria\nbasilar', '#fff', ROJO, 10, ROJO)
    c.caja(150, 180, 110, 40, 'AICA\n(cerebelosa antero-\ninferior)', '#fff', ROJO, 9.5, ROJO)
    c.linea(120, 200, 150, 200, ROJO, 2, flecha=True)
    c.caja(290, 180, 120, 40, 'Arteria laberíntica\n(auditiva interna)', '#ffe9d5', ROJO, 10, ROJO)
    c.linea(260, 200, 290, 200, ROJO, 2, flecha=True)
    # ramas
    c.caja(450, 60, 140, 48, 'Arteria vestibular\nanterior', '#fff', AZUL, 10, AZUL)
    c.caja(450, 250, 140, 48, 'Arteria coclear\ncomún', '#fff', VERDE, 10, VERDE)
    c.linea(410, 192, 450, 90, AZUL, 2, flecha=True)
    c.linea(410, 208, 450, 270, VERDE, 2, flecha=True)
    c.t(520, 128, 'utrículo, canales superior y lateral,', 9.5, TINTA, 'middle')
    c.t(520, 141, 'parte del sáculo', 9.5, TINTA, 'middle')
    c.t(520, 154, '(territorio del nervio vestibular superior)', 9, TENUE, 'middle')
    c.caja(280, 332, 140, 48, 'Arteria coclear\nprincipal', '#fff', VERDE, 10, VERDE)
    c.caja(470, 332, 150, 48, 'Arteria\nvestibulococlear', '#fff', VERDE, 10, VERDE)
    c.linea(500, 298, 360, 332, VERDE, 2, flecha=True)
    c.linea(540, 298, 545, 332, VERDE, 2, flecha=True)
    for i, ln in enumerate(['cóclea: ápice y', 'vueltas medias']):
        c.t(350, 398 + i * 12.5, ln, 9.5, TINTA, 'middle')
    for i, ln in enumerate(['vuelta basal, sáculo inferior', 'y canal posterior']):
        c.t(545, 398 + i * 12.5, ln, 9.5, TINTA, 'middle')
    c.t(640, 218, 'Son arterias terminales:', 10.5, ROJO, 'middle', 700)
    c.t(640, 232, 'casi sin colaterales,', 10.5, ROJO, 'middle')
    c.t(640, 246, 'el laberinto no tolera la isquemia.', 10.5, ROJO, 'middle')
    c.guardar('b1-irrigacion.svg')


# ---------------------------------------------------------------- válvula nasal
def valvula():
    c = L(760, 420)
    # A: perfil de la pirámide (vista lateral, cara a la izquierda)
    c.t(14, 22, 'A · Pirámide nasal, vista lateral', 12, TINTA, 'start', 700)
    c.ruta('M150,40 C140,90 120,150 95,215 C80,250 78,280 100,290 C120,300 150,296 170,290', 'none', '#b98068', 2)
    c.ruta('M150,40 C170,100 200,170 215,230 C220,262 205,284 170,290', 'none', '#b98068', 2)
    # huesos nasales
    c.ruta('M150,40 C142,85 128,130 114,170 L152,160 C160,120 165,80 150,40 Z', HUESO, '#a8946a', 1.2)
    # cartílago lateral superior
    c.ruta('M114,170 C108,190 100,205 96,222 L150,226 C156,200 160,178 152,160 Z', '#bfd9ec', '#2b6cb0', 1.2)
    # cartílago alar mayor (punta)
    c.ruta('M96,222 C84,248 82,274 104,282 C120,286 138,278 142,262 C146,246 136,234 126,230 Z', '#cfe9d6', VERDE, 1.2)
    # ala nasal (partes blandas)
    c.ruta('M150,226 C175,240 200,248 212,262 C206,282 190,290 170,290 C156,292 146,282 142,262 Z', '#f6e3d9', '#b98068', 1)
    rotulo(c, 140, 100, 250, 66, 'Huesos nasales', 'start', size=10.5)
    rotulo(c, 130, 200, 250, 132, 'Cartílago lateral superior', 'start', size=10.5)
    rotulo(c, 110, 262, 20, 332, 'Cartílago alar mayor<tspan x="24" dy="13">(forma la punta)</tspan>', 'start', size=10.5)
    rotulo(c, 190, 262, 250, 330, 'Ala de la nariz', 'start', size=10.5)
    c.add(f'<circle cx="152" cy="190" r="10" fill="none" stroke="{ROJO}" stroke-width="1.6" stroke-dasharray="3 2"/>')
    c.t(250, 200, 'unión con el tabique:', 10.5, ROJO, 'start', 600)
    c.t(250, 214, 'zona de la válvula interna', 10.5, ROJO, 'start', 600)
    c.linea(248, 205, 164, 192, ROJO, 1)
    # B: corte frontal (el ángulo se mide entre el tabique, vertical, y el cartílago lateral superior)
    c.t(400, 22, 'B · Válvula nasal interna, corte frontal', 12, TINTA, 'start', 700)
    X, Y0, Y1 = 440, 60, 340
    a = math.radians(14)
    ex, ey = X + 280 * math.sin(a), Y0 + 280 * math.cos(a)
    c.ruta(f'M{X},{Y0} L{ex:.1f},{ey:.1f} L{X},{ey:.1f} Z', '#f6c9cc', 'none', 0)
    c.linea(X, Y0, X, Y1, '#8a8a90', 6)
    c.linea(X, Y0, ex, ey, '#2b6cb0', 6)
    c.linea(X, Y1, X + 200, Y1, HUESO, 6)
    c.t(X - 12, 200, 'tabique', 10.5, TINTA, 'end', 600)
    c.t(X + 62, 246, 'cartílago lateral', 10.5, '#2b6cb0', 'start', 600)
    c.t(X + 62, 260, 'superior', 10.5, '#2b6cb0', 'start', 600)
    c.linea(X + 60, 244, X + 46, 238, '#2b6cb0', 0.8)
    c.elipse(ex + 52, 308, 34, 24, '#f1c9d0', '#b98068', 1.3)
    c.t(ex + 52, 306, 'cabeza del', 9.5, TINTA, 'middle')
    c.t(ex + 52, 318, 'cornete inf.', 9.5, TINTA, 'middle')
    r = 120
    c.ruta(f'M{X},{Y0 + r} A{r},{r} 0 0 0 {X + r * math.sin(a):.1f},{Y0 + r * math.cos(a):.1f}', 'none', ROJO, 2)
    c.t(X + 70, Y0 + 26, '10–15°', 12, ROJO, 'start', 700)
    c.linea(X + 66, Y0 + 24, X + 16, Y0 + 114, ROJO, 1)
    c.t(X + 100, 130, 'vía aérea: el punto más estrecho', 10, TENUE, 'start')
    c.t(X + 100, 143, '(40–60 mm²), la mayor', 10, TENUE, 'start')
    c.t(X + 100, 156, 'parte de la resistencia', 10, TENUE, 'start')
    c.t(X + 12, Y1 + 18, 'piso', 10, TENUE, 'start')
    c.t(14, 408, 'Esquemas, no a escala.', 9, TENUE, 'start')
    c.guardar('b1-valvula.svg')


if __name__ == '__main__':
    pabellon()
    membrana()
    trompa()
    via_auditiva()
    via_vestibular()
    irrigacion()
    valvula()
