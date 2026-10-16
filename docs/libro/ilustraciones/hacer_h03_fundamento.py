#!/usr/bin/env python3
"""Dibuja los esquemas del Fundamento de H3 (audiometría tonal). SVG propios,
no IA: son esquemas exactos, con los números de sus fuentes.

    h03-dos-vias.svg            el camino de cada vía y qué lesión deja ver
    h03-funcion-psicometrica.svg el umbral como probabilidad de detección
    h03-hl-spl.svg              el cero audiométrico: dB SPL contra dB HL
    h03-metodo-ascendente.svg   la escalera de 10 abajo / 5 arriba
    h03-metodos-umbral.svg      las cuatro formas de buscar el umbral
    h03-tonotopia.svg           dónde cae cada frecuencia del audiograma

Fuentes de los números:
- RETSPL del TDH-39: ISO 389-1, tal como la reproduce la hoja técnica del
  Interacoustics AT235 (la misma que usa Bibliografia.php, clave AT235).
- Posición de cada frecuencia: función de Greenwood (1990) para el humano,
  F = 165,4 (10^(2,1 x) - 0,88), con x = fracción del largo desde el ápice.
- Ancho de la membrana basilar (~0,1 mm en la base, ~0,5 mm en el ápice): cifra
  clásica atribuida a Békésy, sin fuente primaria leída (verificar).
"""
import math
import pathlib

AQUI = pathlib.Path(__file__).parent
TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
OD, VERDE, OSEA, SOMBRA = '#c62f3a', '#2e8540', '#b86b12', '#f3efe6'
AZUL = '#2c5cb0'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
K = 1.3   # las figuras salen a ~16 cm de ancho: todo texto se agranda en esta proporción


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400, estilo=''):
        extra = f' font-style="{estilo}"' if estilo else ''
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * K:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}"{extra}>{s}</text>')

    def linea(self, x1, y1, x2, y2, color=TINTA, ancho=1, guion='', punta=''):
        g = f' stroke-dasharray="{guion}"' if guion else ''
        p = f' marker-end="url(#{punta})"' if punta else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                        f'stroke-width="{ancho}"{g}{p}/>')

    def rect(self, x, y, w, h, relleno='#fff', borde=TINTA, ancho=1, r=4):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
                        f'fill="{relleno}" stroke="{borde}" stroke-width="{ancho}"/>')

    def raw(self, s):
        self.out.append(s)

    def guardar(self, nombre):
        puntas = ''.join(
            f'<marker id="p-{n}" markerWidth="6" markerHeight="6" refX="5" refY="3" markerUnits="userSpaceOnUse" '
            f'orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="{c}"/></marker>'
            for n, c in (('tinta', TINTA), ('od', OD), ('osea', OSEA), ('verde', VERDE), ('azul', AZUL),
                         ('tenue', TENUE)))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><defs>{puntas}</defs><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def circulo(c, x, y, r=3.6, color=OD, lleno=False):
    c.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color if lleno else "#fff"}" '
          f'stroke="{color}" stroke-width="1.5"/>')


def corchete_oseo(c, x, y, color=OSEA):
    """El '<' de la ósea del OD, dibujado (no texto, para que no dependa de la fuente)."""
    c.raw(f'<path d="M{x + 4:.1f},{y - 6:.1f} L{x - 4:.1f},{y:.1f} L{x + 4:.1f},{y + 6:.1f}" fill="none" '
          f'stroke="{color}" stroke-width="1.8"/>')


# ---------------------------------------------------------------------------
# 1. Las dos vías
def dos_vias():
    c = Lienzo(680, 430)
    c.t(14, 18, 'El camino de cada vía', 10.5, TINTA, 'start', 700)
    cajas = [('Pabellón', 'y conducto', 'refuerza|2,5-3 kHz'),
             ('Membrana', 'timpánica', 'capta|la presión'),
             ('Cadena de', 'huesecillos', 'adapta aire|a líquido'),
             ('Ventana', 'oval', 'el estribo|empuja'),
             ('Cóclea', '', 'CCE amplifican|CCI transducen'),
             ('Nervio y', 'vía auditiva', 'llevan|la señal')]
    x0, w, gap, y, h = 82, 88, 12, 80, 66
    xs = [x0 + i * (w + gap) for i in range(len(cajas))]
    # tramos anatómicos
    tramos = [('oído externo', 0, 0), ('oído medio', 1, 2), ('oído interno', 3, 4), ('retrococlear', 5, 5)]
    for nombre, a, b in tramos:
        xa, xb = xs[a], xs[b] + w
        c.linea(xa + 2, 70, xb - 2, 70, TENUE, 0.8)
        c.linea(xa + 2, 66, xa + 2, 70, TENUE, 0.8)
        c.linea(xb - 2, 66, xb - 2, 70, TENUE, 0.8)
        c.t((xa + xb) / 2, 62, nombre, 8, TENUE)
    for i, (l1, l2, fun) in enumerate(cajas):
        coclea = i == 4
        c.rect(xs[i], y, w, h, '#fbf3e6' if coclea else '#fff', OSEA if coclea else TINTA, 1.6 if coclea else 1)
        c.t(xs[i] + w / 2, y + (18 if l2 else 24), l1, 8.5, TINTA, 'middle', 700)
        if l2:
            c.t(xs[i] + w / 2, y + 30, l2, 8.5, TINTA, 'middle', 700)
        a, b = fun.split('|')
        c.t(xs[i] + w / 2, y + 46, a, 6.8, TENUE)
        c.t(xs[i] + w / 2, y + 56, b, 6.8, TENUE)
        if i < len(cajas) - 1:
            c.linea(xs[i] + w + 1, y + h / 2, xs[i + 1] - 1, y + h / 2, TINTA, 1.2, punta='p-tinta')
    # vía aérea: entra por el fono a la izquierda y recorre todo
    c.rect(14, y + 14, 52, 38, '#fff', TINTA, 1, 10)
    c.t(40, y + 31, 'Fono', 8, TINTA, 'middle', 700)
    c.t(40, y + 43, '(aérea)', 6.8, TENUE)
    c.linea(66, y + h / 2, xs[0] - 1, y + h / 2, TINTA, 1.2, punta='p-tinta')
    c.linea(xs[0], 40, xs[5] + w, 40, TINTA, 2.2, punta='p-tinta')
    c.t(xs[0], 33, 'Vía aérea: recorre todo el camino', 8.5, TINTA, 'start', 700)
    # vía ósea: del vibrador al cráneo y directo a la cóclea
    yo = 176
    c.rect(14, yo - 17, 150, 34, '#fff', OSEA, 1.2, 10)
    c.t(89, yo - 3, 'Vibrador en la mastoides', 7.6, OSEA, 'middle', 700)
    c.t(89, yo + 10, 'hace vibrar el cráneo', 6.8, OSEA)
    c.linea(164, yo, xs[4] + w / 2, yo, OSEA, 2.2)
    c.linea(xs[4] + w / 2, yo, xs[4] + w / 2, y + h + 2, OSEA, 2.2, punta='p-osea')
    c.t(176, yo + 18, 'Vía ósea: salta el oído externo y el medio, directo a la cóclea',
        8.2, OSEA, 'start', 700)
    c.t(176, yo + 31, '(compresión de la cápsula, inercia de líquidos y cadena, radiación al conducto)',
        6.8, OSEA, 'start')

    # Qué deja ver cada vía: tres audiogramas chicos
    c.t(14, 240, 'Qué lesión deja ver cada una', 10, TINTA, 'start', 700)
    casos = [('Conductiva', 'falla antes de la cóclea', [45, 45, 40, 40], [5, 5, 10, 5], True),
             ('Sensorioneural', 'falla en la cóclea o el nervio', [30, 40, 55, 65], [25, 40, 50, 60], False),
             ('Mixta', 'fallan los dos tramos', [55, 60, 65, 70], [25, 30, 40, 45], True)]
    for k, (tit, sub, aer, ose, hay_gap) in enumerate(casos):
        ax, ay, aw = 52 + k * 216, 280, 150
        Y = lambda db: ay + db * 1.25
        for db in range(0, 81, 10):
            c.linea(ax, Y(db), ax + aw, Y(db), FUERTE if db % 20 == 0 else GRILLA, 0.7)
            if db % 20 == 0:
                c.t(ax - 4, Y(db) + 3, db, 6.5, TENUE, 'end')
        fx = [ax + aw * (i + 0.5) / 4 for i in range(4)]
        for x, s in zip(fx, ['500', '1k', '2k', '4k']):
            c.t(x, ay - 4, s, 6.5, TENUE)
        if hay_gap:
            pol = ' '.join(f'{x:.1f},{Y(v):.1f}' for x, v in zip(fx, ose)) + ' ' + \
                  ' '.join(f'{x:.1f},{Y(v):.1f}' for x, v in reversed(list(zip(fx, aer))))
            c.raw(f'<polygon points="{pol}" fill="{OSEA}" opacity=".13"/>')
            gx = (fx[1] + fx[2]) / 2
            c.t(gx, (Y(aer[1]) + Y(ose[1])) / 2 + 3, 'gap', 8, OSEA, 'middle', 700)
        c.raw('<polyline points="' + ' '.join(f'{x:.1f},{Y(v):.1f}' for x, v in zip(fx, aer)) +
              f'" fill="none" stroke="{OD}" stroke-width="1.3"/>')
        for x, v in zip(fx, aer):
            circulo(c, x, Y(v), 4.4)
        for x, v in zip(fx, ose):
            corchete_oseo(c, x - 9, Y(v), OD)
        c.t(ax + aw / 2, ay + 122, tit, 9, TINTA, 'middle', 700)
        c.t(ax + aw / 2, ay + 136, sub, 7, TENUE)
    c.t(668, 240, '○ aérea, &lt; ósea', 7.2, OD, 'end')
    c.t(668, 252, '(oído derecho)', 6.6, TENUE, 'end')
    c.guardar('h03-dos-vias.svg')


# ---------------------------------------------------------------------------
# 2. Función psicométrica
def psicometrica():
    c = Lienzo(680, 256)
    x0, x1, y0, y1 = 64, 400, 30, 200       # área del gráfico
    dmin, dmax = 5, 45
    X = lambda db: x0 + (db - dmin) / (dmax - dmin) * (x1 - x0)
    Y = lambda p: y1 - p / 100 * (y1 - y0)
    for p in (0, 25, 50, 75, 100):
        c.linea(x0, Y(p), x1, Y(p), FUERTE if p in (0, 100) else GRILLA, 0.7)
        c.t(x0 - 5, Y(p) + 3, f'{p} %', 7, TENUE, 'end')
    for db in range(dmin, dmax + 1, 5):
        c.linea(X(db), y1, X(db), y1 + 3, TENUE, 0.7)
        c.t(X(db), y1 + 13, db, 7, TENUE)
    c.t((x0 + x1) / 2, y1 + 27, 'Nivel del tono (dB HL)', 8, TENUE)
    c.raw(f'<text transform="translate(20 {(y0 + y1) / 2:.0f}) rotate(-90)" {F} font-size="10" fill="{TENUE}" '
          f'text-anchor="middle">Tonos detectados</text>')

    def curva(centro, k=3.4):
        return [(db / 4, 100 / (1 + math.exp(-(db / 4 - centro) / k))) for db in range(dmin * 4, dmax * 4 + 1)]

    estricta = curva(30)
    c.raw('<polyline points="' + ' '.join(f'{X(d):.1f},{Y(p):.1f}' for d, p in estricta) +
          f'" fill="none" stroke="{TENUE}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    normal = curva(25)
    c.raw('<polyline points="' + ' '.join(f'{X(d):.1f},{Y(p):.1f}' for d, p in normal) +
          f'" fill="none" stroke="{TINTA}" stroke-width="2"/>')
    # umbral = 50 %
    c.linea(x0, Y(50), X(25), Y(50), VERDE, 1.3, '4 3')
    c.linea(X(25), Y(50), X(25), y1, VERDE, 1.3, '4 3')
    c.raw(f'<circle cx="{X(25):.1f}" cy="{Y(50):.1f}" r="4.5" fill="{VERDE}"/>')
    c.t(X(25) + 7, Y(50) + 16, 'umbral: 50 %', 8.5, VERDE, 'start', 700)
    # zonas
    c.t(X(10), Y(14), 'nunca lo oye', 7.5, TENUE)
    c.t(X(23), Y(88), 'a veces sí,', 7.5, TENUE)
    c.t(X(23), Y(81), 'a veces no', 7.5, TENUE)
    c.t(X(40), Y(106), 'siempre lo oye', 7.5, TENUE)
    c.t(X(36), Y(42), 'paciente que espera', 7.3, TENUE, 'start', 400, 'italic')
    c.t(X(36), Y(35), 'estar seguro', 7.3, TENUE, 'start', 400, 'italic')
    # texto a la derecha
    tx = 425
    lineas = [('El umbral es el nivel con', 400), ('50 % de detecciones.', 700), ('', 0),
              ('En la clínica se estima así:', 400), ('el nivel más bajo con respuesta', 400),
              ('en la mitad de los ascensos,', 400), ('mínimo 2 de 3.', 700), ('', 0),
              ('Si el paciente espera a estar', 400), ('seguro, la curva se corre a la', 400),
              ('derecha (línea punteada) y los', 400), ('umbrales salen peores.', 400)]
    yy = 40
    for s, peso in lineas:
        if s:
            c.t(tx, yy, s, 8, TINTA, 'start', peso)
        yy += 14.5
    c.t(tx, 246, 'Esquema: la pendiente real cambia con la persona.', 6.6, TENUE, 'start', 400, 'italic')
    c.guardar('h03-funcion-psicometrica.svg')


# ---------------------------------------------------------------------------
# 3. dB SPL contra dB HL
RETSPL_TDH39 = [(125, 45), (250, 25.5), (500, 11.5), (1000, 7), (1500, 6.5), (2000, 9), (3000, 10),
                (4000, 9.5), (6000, 15.5), (8000, 13)]


def hl_spl():
    c = Lienzo(680, 240)
    fmin, fmax = math.log2(125), math.log2(8000)

    def ejes_x(ax, aw, yb):
        X = lambda f: ax + (math.log2(f) - fmin) / (fmax - fmin) * aw
        for f, s in ((125, '125'), (250, '250'), (500, '500'), (1000, '1k'), (2000, '2k'), (4000, '4k'),
                     (8000, '8k')):
            c.t(X(f), yb + 12, s, 7, TENUE)
        c.t(ax + aw / 2, yb + 24, 'Frecuencia (Hz)', 7.5, TENUE)
        return X

    # panel izquierdo: dB SPL hacia arriba
    ax, aw, yt, yb = 52, 230, 46, 206
    Y = lambda db: yb - db / 50 * (yb - yt)
    c.t(ax - 30, 22, 'Medido con un micrófono (dB SPL)', 9.5, TINTA, 'start', 700)
    for db in range(0, 51, 10):
        c.linea(ax, Y(db), ax + aw, Y(db), FUERTE if db == 0 else GRILLA, 0.7)
        c.t(ax - 5, Y(db) + 3, db, 7, TENUE, 'end')
    X = ejes_x(ax, aw, yb)
    c.raw('<polyline points="' + ' '.join(f'{X(f):.1f},{Y(v):.1f}' for f, v in RETSPL_TDH39) +
          f'" fill="none" stroke="{TINTA}" stroke-width="1.6"/>')
    for f, v in RETSPL_TDH39:
        circulo(c, X(f), Y(v), 3, TINTA)
    c.t(X(125) + 7, Y(45) + 3, '45 dB SPL', 7.5, TINTA, 'start', 700)
    c.t(X(1000), Y(7) - 9, '7 dB SPL', 7.5, TINTA, 'middle', 700)
    c.t(X(2000) + 10, Y(41), 'umbral de un oído joven', 7.5, TENUE, 'middle')
    c.t(X(2000) + 10, Y(37), 'normal con el fono TDH-39', 7.5, TENUE, 'middle')
    c.t(X(2000) + 10, Y(32), '↑ más presión = más fuerte', 7, TENUE, 'middle')

    # flecha central
    c.linea(300, 120, 388, 120, VERDE, 2, punta='p-verde')
    c.t(344, 98, 'se resta la', 7.5, VERDE, 'middle', 700)
    c.t(344, 110, 'referencia', 7.5, VERDE, 'middle', 700)
    c.t(344, 138, 'de cada', 7.5, VERDE)
    c.t(344, 150, 'frecuencia', 7.5, VERDE)
    c.t(344, 162, '(ISO 389-1)', 7.5, VERDE)

    # panel derecho: dB HL hacia abajo
    bx, bw, ytop, ybot = 420, 230, 46, 206
    Yh = lambda db: ytop + (db + 10) / 70 * (ybot - ytop)
    c.t(bx - 30, 22, 'En el audiograma (dB HL)', 9.5, TINTA, 'start', 700)
    for db in range(-10, 61, 10):
        c.linea(bx, Yh(db), bx + bw, Yh(db), FUERTE if db == 0 else GRILLA, 0.9 if db == 0 else 0.7)
        c.t(bx - 5, Yh(db) + 3, db, 7, TENUE, 'end')
    Xh = ejes_x(bx, bw, ybot)
    c.linea(Xh(125), Yh(0), Xh(8000), Yh(0), OD, 1.4)
    for f, _ in RETSPL_TDH39:
        circulo(c, Xh(f), Yh(0), 3.2)
    c.t(Xh(1000), Yh(0) - 8, 'el mismo oído: 0 dB HL en todas', 7.5, OD, 'middle', 700)
    c.linea(bx + bw - 22, Yh(14), bx + bw - 22, Yh(56), TENUE, 1.4, punta='p-tenue')
    c.t(bx + bw - 28, Yh(28), 'más abajo =', 7.5, TENUE, 'end')
    c.t(bx + bw - 28, Yh(28) + 13, 'más dB para', 7.5, TENUE, 'end')
    c.t(bx + bw - 28, Yh(28) + 26, 'detectarlo:', 7.5, TENUE, 'end')
    c.t(bx + bw - 28, Yh(28) + 39, 'oye peor', 7.5, TENUE, 'end', 700)
    c.guardar('h03-hl-spl.svg')


# ---------------------------------------------------------------------------
# 4. Método ascendente
def ascendente():
    c = Lienzo(680, 264)
    seq = [(40, True), (30, True), (20, False), (25, True), (15, False), (20, False), (25, True),
           (15, False), (20, False), (25, True)]
    x0, dx, ytop, ybot = 92, 52, 40, 200
    Y = lambda db: ybot - (db - 10) / 30 * (ybot - ytop)
    X = lambda i: x0 + i * dx
    # ascensos sombreados: desde la falta de respuesta hasta la respuesta
    for k, (a, b) in enumerate(((2, 3), (4, 6), (7, 9)), 1):
        c.rect(X(a) - 16, ytop - 6, X(b) - X(a) + 32, ybot - ytop + 12, SOMBRA, SOMBRA, 0, 6)
        c.t((X(a) + X(b)) / 2, ybot + 30, f'ascenso {k}', 8, TENUE, 'middle', 700)
    for db in range(10, 41, 5):
        c.linea(x0 - 24, Y(db), X(9) + 24, Y(db), FUERTE if db % 10 == 0 else GRILLA, 0.7)
        c.t(x0 - 30, Y(db) + 3, db, 7.5, TENUE, 'end')
    c.raw(f'<text transform="translate(26 {(ytop + ybot) / 2:.0f}) rotate(-90)" {F} font-size="10" '
          f'fill="{TENUE}" text-anchor="middle">dB HL (crecen hacia arriba)</text>')
    # umbral
    c.linea(x0 - 24, Y(25), X(9) + 24, Y(25), VERDE, 1.4, '5 3')
    for i in range(len(seq) - 1):
        (a, _), (b, _) = seq[i], seq[i + 1]
        baja = b < a
        col = OD if baja else AZUL
        y1, y2 = Y(a) + (5 if baja else -5), Y(b) - (6 if baja else -6)
        c.linea(X(i) + 4, y1, X(i + 1) - 4, y2, col, 1.4, punta='p-od' if baja else 'p-azul')
        c.t((X(i) + X(i + 1)) / 2 + (13 if baja else -8), (Y(a) + Y(b)) / 2 + (13 if baja else 3), '−10' if baja else '+5',
            7, col, 'middle', 700)
    for i, (db, r) in enumerate(seq):
        circulo(c, X(i), Y(db), 4.6, VERDE if r else TINTA, lleno=r)
        c.t(X(i), ybot + 15, i + 1, 7, TENUE)
    c.t(X(0), Y(40) - 10, 'familiarización', 7.5, TENUE)
    # leyenda
    lx = 470
    circulo(c, lx, 22, 4.6, VERDE, True)
    c.t(lx + 9, 25, 'respondió', 8, TINTA, 'start')
    circulo(c, lx + 80, 22, 4.6, TINTA)
    c.t(lx + 89, 25, 'no respondió', 8, TINTA, 'start')
    c.t(X(9) + 30, Y(25) - 6, 'umbral', 8.5, VERDE, 'start', 700)
    c.t(X(9) + 30, Y(25) + 6, '25 dB HL', 8.5, VERDE, 'start', 700)
    c.t(x0 - 24, 254, 'En 25 dB responde en los 3 ascensos; en 20, en ninguno: el umbral es 25 dB HL.',
        8, TINTA, 'start')
    c.t(x0 - 24, ybot + 15, 'tono n.°', 7, TENUE, 'end')
    c.guardar('h03-metodo-ascendente.svg')


def _escalera(c, x0, y0, ancho, alto, seq, umbral, titulo, sub, notas, db_min=10, db_max=40, autores=''):
    """Un panel de búsqueda de umbral: tonos en orden, respuesta o no, el
    paso entre tonos y la línea del umbral."""
    Y = lambda db: y0 + alto - (db - db_min) / (db_max - db_min) * alto
    n = len(seq)
    paso = (ancho - 60) / max(n - 1, 1)
    X = lambda i: x0 + 40 + i * paso
    c.t(x0, y0 - 44, titulo, 9.5, TINTA, 'start', 700)
    if autores:
        c.t(x0, y0 - 31, autores, 7.4, TINTA, 'start', estilo='italic')
    c.t(x0, y0 - 17, sub, 7.4, TENUE, 'start')
    for db in range(db_min, db_max + 1, 5):
        c.linea(x0 + 26, Y(db), x0 + ancho, Y(db), FUERTE if db % 10 == 0 else GRILLA, 0.6)
        if db % 10 == 0:
            c.t(x0 + 20, Y(db) + 3, db, 7, TENUE, 'end')
    c.linea(x0 + 26, Y(umbral), x0 + ancho, Y(umbral), VERDE, 1.3, '5 3')
    for i in range(n - 1):
        (a, _), (b, _) = seq[i], seq[i + 1]
        if a == b:
            c.t((X(i) + X(i + 1)) / 2, Y(a) - 7, 'otra vez', 6.4, TENUE, 'middle', 700)
            continue
        baja = b < a
        col = OD if baja else AZUL
        c.linea(X(i) + 4, Y(a) + (4 if baja else -4), X(i + 1) - 4, Y(b) - (5 if baja else -5), col, 1.2,
                punta='p-od' if baja else 'p-azul')
        c.t((X(i) + X(i + 1)) / 2 + (11 if baja else -9), (Y(a) + Y(b)) / 2 + (2 if baja else -3),
            f'{b - a:+d}'.replace('-', '−'), 6.4, col, 'start' if baja else 'end', 700)
    for i, (db, r) in enumerate(seq):
        circulo(c, X(i), Y(db), 4, VERDE if r else TINTA, lleno=r)
    for k, nota in enumerate(notas):
        c.t(x0, y0 + alto + 18 + k * 12, nota, 7.4, VERDE if k == len(notas) - 1 else TINTA, 'start',
            700 if k == len(notas) - 1 else 400)


def metodos_umbral():
    """Las cuatro formas de buscar el umbral, cada una con un ejemplo que
    llega a 25 dB HL. El ejemplo de la combinada acortada lo dio una
    audióloga del equipo (2026-10-16)."""
    c = Lienzo(680, 530)
    w, h = 300, 120
    _escalera(c, 20, 100, w, h,
              [(40, True), (30, True), (20, False), (25, True), (15, False), (20, False), (25, True),
               (15, False), (20, False), (25, True)], 25,
              'A · Ascendente', 'baja 10 si responde, sube 5 si no',
              ['el umbral se juzga solo subiendo', '25 dB: responde en 3 de 3 ascensos'],
              autores='Hughson y Westlake (1944); Carhart y Jerger (1959)')
    _escalera(c, 360, 100, w, h,
              [(40, True), (35, True), (30, True), (25, True), (20, False)], 25,
              'B · Descendente', 'baja de 5 en 5 hasta que deja de responder',
              ['riesgo: sigue respondiendo por inercia', 'umbral: la última respuesta, 25 dB'],
              autores='método de límites (Fechner, 1860); en audiometría, Bunch (1943)')
    _escalera(c, 20, 348, w, h,
              [(10, False), (15, False), (20, False), (25, True), (30, True), (25, True), (20, False),
               (25, True)], 25,
              'C · Horquilla', 'series de 5 dB que suben y bajan alrededor del umbral',
              ['3 series ascendentes y 3 descendentes', 'umbral: promedio de los niveles más bajos oídos'],
              autores='ISO 8253-1 (1989)')
    _escalera(c, 360, 348, w, h,
              [(40, True), (30, True), (20, False), (20, False), (25, True), (25, True)], 25,
              'D · Combinada acortada', 'baja 10 si responde, sube 5 si no; repite al mismo nivel',
              ['en 20, dos sin respuesta: ya no llega a 2 de 3', 'en 25, dos respuestas: umbral 25 dB'],
              autores='variante clínica: 2 de 3 tonos al mismo nivel')
    circulo(c, 470, 18, 4, VERDE, True)
    c.t(479, 21, 'respondió', 7.6, TINTA, 'start')
    circulo(c, 545, 18, 4, TINTA)
    c.t(554, 21, 'no respondió', 7.6, TINTA, 'start')
    c.t(20, 22, 'Cuatro formas de buscar el umbral', 10.5, TINTA, 'start', 700)
    c.guardar('h03-metodos-umbral.svg')


# ---------------------------------------------------------------------------
# 5. Tonotopía (Greenwood)
def desde_base(f):
    """Fracción del largo de la cóclea desde la base (Greenwood 1990, humano)."""
    return 1 - math.log10(f / 165.4 + 0.88) / 2.1


def tonotopia():
    c = Lienzo(680, 236)
    x0, x1, ym = 40, 640, 110
    X = lambda frac: x0 + frac * (x1 - x0)
    # membrana basilar: angosta en la base, ancha en el ápice
    c.raw(f'<polygon points="{x0},{ym - 6} {x1},{ym - 20} {x1},{ym + 20} {x0},{ym + 6}" fill="#fbf3e6" '
          f'stroke="{OSEA}" stroke-width="1.2"/>')
    # ancho de la membrana en cada extremo (cotas)
    c.linea(x0 + 4, ym - 6, x0 + 4, ym + 6, OSEA, 1.4)
    c.linea(x0 + 4, ym + 8, x0 + 4, ym + 24, OSEA, 0.7, '2 2')
    c.t(x0, ym + 35, 'ancho ≈ 0,1 mm', 7.6, OSEA, 'start', 700)
    c.linea(x1 - 4, ym - 20, x1 - 4, ym + 20, OSEA, 1.4)
    c.linea(x1 - 4, ym + 22, x1 - 4, ym + 26, OSEA, 0.7, '2 2')
    c.t(x1, ym + 37, 'ancho ≈ 0,5 mm', 7.6, OSEA, 'end', 700)
    # tramos
    a8, a125, a16 = desde_base(8000), desde_base(125), desde_base(16000)
    c.raw(f'<rect x="{X(a16):.1f}" y="{ym - 50}" width="{X(a8) - X(a16):.1f}" height="8" fill="{AZUL}" opacity=".35"/>')
    c.raw(f'<rect x="{X(a8):.1f}" y="{ym - 50}" width="{X(a125) - X(a8):.1f}" height="8" fill="{OD}" opacity=".35"/>')
    c.t(X(a16) + 2, ym - 56, 'alta frecuencia', 7.5, AZUL, 'start', 700)
    c.t((X(a8) + X(a125)) / 2, ym - 56, 'audiometría convencional: 125 a 8.000 Hz', 8, OD, 'middle', 700)
    for f, s in ((16000, '16k'), (8000, '8k'), (4000, '4k'), (2000, '2k'), (1000, '1k'), (500, '500'),
                 (250, '250'), (125, '125')):
        x = X(desde_base(f))
        c.linea(x, ym - 22, x, ym + 22, TINTA if f <= 8000 else AZUL, 0.9)
        c.t(x, ym - 28 if f > 8000 else ym - 28, s, 8, TINTA if f <= 8000 else AZUL, 'middle', 700)
    # octavas sobre 500 Hz
    for fa, fb in ((500, 1000), (1000, 2000), (2000, 4000), (4000, 8000)):
        xa, xb = X(desde_base(fb)), X(desde_base(fa))
        c.linea(xa + 2, ym + 34, xb - 2, ym + 34, VERDE, 1.2)
        c.linea(xa + 2, ym + 30, xa + 2, ym + 38, VERDE, 1.2)
        c.linea(xb - 2, ym + 30, xb - 2, ym + 38, VERDE, 1.2)
        c.t((xa + xb) / 2, ym + 48, f'{(desde_base(fa) - desde_base(fb)) * 100:.0f} %', 7.5, VERDE, 'middle', 700)
    c.t((X(desde_base(8000)) + X(desde_base(500))) / 2, ym + 60,
        'sobre 500 Hz, cada octava ocupa un tramo parecido de la cóclea', 7.5, VERDE)
    c.t(x0, ym + 88, 'BASE · junto a la ventana oval', 8.5, TINTA, 'start', 700)
    c.t(x0, ym + 103, 'membrana angosta y rígida: agudos', 7.5, TENUE, 'start')
    c.t(x0, ym + 118, 'la primera en dañarse con ruido, edad y ototóxicos', 7.5, OD, 'start', 700)
    c.t(x1, ym + 88, 'ÁPICE', 8.5, TINTA, 'end', 700)
    c.t(x1, ym + 103, 'membrana ancha y flexible: graves', 7.5, TENUE, 'end')
    c.t(14, 18, 'Dónde cae cada frecuencia del audiograma (cóclea desenrollada)', 10.5, TINTA, 'start', 700)
    c.t(14, 35, f'Fracción del largo según Greenwood (1990). Sobre 8 kHz queda el {a8 * 100:.0f} % más basal, '
        'fuera del audiograma convencional.', 7.5, TENUE, 'start')
    c.guardar('h03-tonotopia.svg')


if __name__ == '__main__':
    dos_vias()
    psicometrica()
    hl_spl()
    ascendente()
    metodos_umbral()
    tonotopia()
