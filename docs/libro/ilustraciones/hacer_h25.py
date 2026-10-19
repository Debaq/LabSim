#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H25 (anamnesis rinológica y rinoscopía):

    h25-fosa-lateral.svg    pared lateral de la fosa nasal: vestíbulo, válvula, cornetes, meatos, coana
    h25-ciclo-corte.svg     corte frontal de las dos fosas y ciclo nasal
    h25-valvula.svg         ángulo valvular, resistencia contra radio (Poiseuille) y efecto Bernoulli
    h25-equipo.svg          espéculo nasal, espejo frontal y lámpara
    h25-posiciones.svg      cabeza recta, 30° y 60° de extensión: hasta dónde llega la vista

SVG propios, no IA: son esquemas anatómicos y físicos, no datos. Las proporciones son
ilustrativas; ninguna medida sale del dibujo."""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO = '#c0571c', '#21796c', '#c62f3a'
MUCOSA, CORNETE, HUESO, OLFA = '#fbefec', '#f0c3b8', '#efe9dc', '#f6e7a8'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}{extra}/>')

    def poli(self, pts, color, w=2, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}{extra}/>')

    def path(self, d, fill='none', stroke=TINTA, w=1.4, extra=''):
        self.out.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{extra}/>')

    def rect(self, x, y, w, h, fill, stroke=TINTA, sw=1.2, r=0):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
                        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circ(self, x, y, r, fill='none', stroke=TINTA, w=1.2):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')

    def elip(self, x, y, rx, ry, fill='none', stroke=TINTA, w=1.2, rot=0):
        tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ''
        self.out.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx}" ry="{ry}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{w}"{tr}/>')

    def guardar(self, nombre, defs=''):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><defs>{defs}</defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def punta(id_, color):
    return (f'<marker id="{id_}" markerWidth="6" markerHeight="6" refX="4" refY="3.5" '
            f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" '
            f'transform="scale(.8)" fill="{color}"/></marker>')


# ---------------------------------------------------------------- pared lateral (perfil)
# Coordenadas base: nariz hacia la izquierda, 100..600 de ancho, 40..330 de alto.
def cavidad(c, ox=0.0, oy=0.0, s=1.0):
    """Dibuja la fosa en perfil con transformación (ox, oy, s). Sin rótulos."""
    P = lambda x, y: (ox + x * s, oy + y * s)

    def d(*pts):
        return ' '.join(f'{ox + x * s:.1f},{oy + y * s:.1f}' for x, y in pts)

    # seno frontal y esfenoidal
    c.elip(*P(222, 88), 34 * s, 24 * s, fill=HUESO, stroke=FUERTE, rot=-25)
    # nasofaringe
    c.path(f'M {d((520, 175))} L {d((600, 175))} L {d((600, 318))} L {d((520, 318))} Z', '#f6f1ec', FUERTE, 1)
    c.path(f'M {d((455, 128))} L {d((545, 128))} Q {d((560, 128))} {d((560, 150))} L {d((560, 172))} '
           f'Q {d((560, 188))} {d((542, 188))} L {d((470, 188))} Z', HUESO, FUERTE, 1.2)
    # cavidad
    c.path(f'M {d((118, 300))} L {d((120, 262))} Q {d((124, 232))} {d((158, 205))} L {d((205, 152))} '
           f'Q {d((215, 140))} {d((240, 138))} L {d((452, 128))} L {d((470, 150))} L {d((520, 178))} '
           f'L {d((520, 300))} Z', MUCOSA, TINTA, 1.6)
    # región olfatoria
    c.path(f'M {d((262, 138))} L {d((452, 128))} L {d((452, 140))} L {d((262, 150))} Z', OLFA, 'none', 0)
    # cornetes: inferior, medio y superior
    c.path(f'M {d((188, 276))} C {d((196, 238))} {d((300, 232))} {d((446, 276))} '
           f'C {d((352, 262))} {d((262, 266))} {d((188, 276))} Z', CORNETE, COCLEAR, 1.4)
    c.path(f'M {d((238, 206))} C {d((252, 172))} {d((340, 166))} {d((436, 206))} '
           f'C {d((352, 194))} {d((292, 198))} {d((238, 206))} Z', CORNETE, COCLEAR, 1.4)
    c.path(f'M {d((372, 172))} C {d((384, 150))} {d((422, 148))} {d((454, 170))} '
           f'C {d((424, 162))} {d((398, 164))} {d((372, 172))} Z', CORNETE, COCLEAR, 1.4)
    # paladar duro
    c.path(f'M {d((112, 300))} L {d((520, 300))} L {d((520, 314))} L {d((112, 314))} Z', HUESO, TINTA, 1.2)
    # perfil externo de la nariz
    c.poli([P(205, 110), P(150, 165), P(98, 238), P(82, 270), P(96, 292), P(118, 300)], TINTA, 1.6)
    return P


def fosa_lateral():
    c = Lienzo(760, 420)
    c.t(14, 20, 'Pared lateral de la fosa nasal derecha (se ve como si no tuviera tabique)', 10.5, TINTA, 'start', 700)
    P = cavidad(c, 0, 10, 1.0)
    # válvula nasal
    c.l(160, 232, 160, 305, AVISO, 2, '5 3')
    # coana
    c.l(520, 188, 520, 310, COCLEAR, 2, '5 3')
    # trompa de Eustaquio
    c.circ(552, 268, 8, '#fff', RETRO, 1.8)
    c.circ(552, 268, 2.5, RETRO, RETRO, 1)
    # rótulos
    r = lambda x, y, s, col=TINTA, a='start', p=600, z=8.7: c.t(x, y, s, z, col, a, p)
    r(30, 345, 'vestíbulo', TENUE, 'start', 400)
    c.l(80, 338, 120, 310, TENUE, .8)
    r(110, 375, 'válvula nasal', AVISO, 'start', 700)
    c.l(160, 307, 150, 366, AVISO, .8)
    r(215, 392, 'meato inferior', TINTA, 'start')
    c.l(250, 384, 250, 318, TENUE, .8)
    r(335, 356, 'cornete inferior', COCLEAR, 'start', 700)
    c.l(360, 348, 360, 320, COCLEAR, .8)
    r(430, 392, 'coana', COCLEAR, 'start', 700)
    c.l(520, 380, 520, 312, COCLEAR, .8)
    r(330, 253, 'meato medio', TINTA, 'start')
    r(325, 232, 'cornete medio', COCLEAR, 'start', 700)
    r(465, 214, 'cornete superior', COCLEAR, 'start', 700)
    c.l(468, 212, 440, 192, COCLEAR, .8)
    r(215, 117, 'hendidura olfatoria y lámina cribosa', '#8a6d00', 'start', 700)
    r(150, 52, 'seno frontal', TENUE, 'start', 400)
    r(468, 118, 'seno esfenoidal', TENUE, 'start', 400)
    r(528, 340, 'nasofaringe', TENUE, 'start', 400)
    r(542, 296, 'trompa', RETRO, 'start', 700)
    r(542, 308, '(→ H7)', RETRO, 'start', 400)
    r(430, 350, 'paladar duro', TENUE, 'start', 400)
    c.l(480, 344, 480, 325, TENUE, .8)
    c.guardar('h25-fosa-lateral.svg')


# ---------------------------------------------------------------- corte frontal y ciclo
def fosas_corte(c, ox, oy, congestion):
    """Corte frontal. congestion: 'D' = cornete inferior derecho hinchado; 'I' = el izquierdo.
    Lo que se ve de frente: izquierda de la imagen = fosa derecha del paciente (OD)."""
    def fosa(x0, lado):  # x0 = borde lateral, lado -1 (izq. de imagen) / +1
        # paredes: techo, piso, tabique (centro) y pared lateral
        centro = ox + 140
        lat = ox + 140 + lado * 100
        top, bot = oy + 20, oy + 170
        c.path(f'M {centro:.1f},{top} L {centro:.1f},{bot} L {lat:.1f},{bot} L {lat:.1f},{top + 22} '
               f'L {centro + lado * 25:.1f},{top} Z', MUCOSA, TINTA, 1.4)
        hinch = (congestion == 'D' and lado == -1) or (congestion == 'I' and lado == 1)
        # cornete inferior (cuelga de la pared lateral, abajo)
        ex = 17 if hinch else 8
        c.elip(lat - lado * 22, bot - 36, ex + 12, 18 if hinch else 15, CORNETE, COCLEAR, 1.4)
        # cornete medio (arriba)
        c.elip(lat - lado * 20, top + 46, 8, 20, CORNETE, COCLEAR, 1.2)
        return hinch
    fosa(0, -1)
    fosa(0, 1)
    c.t(ox + 140 - 52, oy + 190, 'OD', 8.5, TENUE, 'middle', 700)
    c.t(ox + 140 + 52, oy + 190, 'OI', 8.5, TENUE, 'middle', 700)


def ciclo_corte():
    c = Lienzo(760, 330)
    c.t(14, 20, 'Corte frontal de la nariz, visto desde delante', 10.5, TINTA, 'start', 700)
    c.t(150, 52, 'A · ahora', 9.5, TINTA, 'middle', 700)
    c.t(520, 52, 'B · unas horas después', 9.5, TINTA, 'middle', 700)
    fosas_corte(c, 10, 60, 'D')
    fosas_corte(c, 380, 60, 'I')
    # flechas de flujo
    for ox, grande in ((10, 'D'), (380, 'I')):
        for lado, nombre in ((-1, 'D'), (1, 'I')):
            ancho = 2.4 if grande == nombre else 4
            xx = ox + 140 + lado * 60
            c.l(xx, 100, xx, 138, AVISO if grande == nombre else RETRO, ancho,
                extra=' marker-end="url(#p-fino)"' if grande == nombre else ' marker-end="url(#p-flujo)"')
    c.t(150, 290, 'derecha congestionada, izquierda abierta', 8.8, TINTA, 'middle', 600)
    c.t(520, 290, 'se invierte; la suma de las dos casi no cambia', 8.8, TINTA, 'middle', 600)
    c.t(150, 306, 'flujo grueso = fosa más abierta', 8, TENUE, 'middle')
    c.t(520, 306, 'flujo fino = fosa más cerrada', 8, TENUE, 'middle')
    c.t(335, 160, '⇄', 22, TENUE, 'middle', 700)
    c.t(14, 322, 'La alternancia ocurre en el tejido eréctil del cornete inferior.', 8, TENUE, 'start')
    c.t(150, 74, 'tabique', 8, TINTA, 'middle', 600)
    c.t(335, 200, 'cornetes en naranja:', 8, COCLEAR, 'middle', 600)
    c.t(335, 212, 'medio arriba, inferior abajo', 8, COCLEAR, 'middle', 600)
    c.guardar('h25-ciclo-corte.svg', punta('p-flujo', RETRO) + punta('p-fino', AVISO))


# ---------------------------------------------------------------- válvula, Poiseuille y Bernoulli
def valvula():
    c = Lienzo(760, 370)
    # Panel A: ángulo de la válvula
    c.t(14, 20, 'A · El ángulo de la válvula', 10.5, TINTA, 'start', 700)
    ax, ay = 90, 250
    ang = 14
    L = 150
    c.l(ax, ay, ax, ay - L, TINTA, 3)                       # tabique
    ex = ax + L * math.sin(math.radians(ang))
    ey = ay - L * math.cos(math.radians(ang))
    c.l(ax, ay, ex, ey, COCLEAR, 3)                          # cartílago lateral superior
    c.path(f'M {ax},{ay - 70} A 70 70 0 0 1 {ax + 70 * math.sin(math.radians(ang)):.1f},'
           f'{ay - 70 * math.cos(math.radians(ang)):.1f}', 'none', AVISO, 1.6)
    c.t(ax + 28, ay - 82, '10 a 15°', 9.5, AVISO, 'start', 700)
    c.t(ax - 10, ay - 40, 'tabique', 8.5, TINTA, 'end', 600)
    c.t(ex + 8, ey + 4, 'cartílago lateral superior', 8.5, COCLEAR, 'start', 600)
    c.t(ax + 4, ay + 18, 'aire', 8.5, TENUE, 'start')
    c.l(ax + 30, ay + 12, ax + 30, ay - 10, RETRO, 2)
    c.t(14, 290, 'Corte frontal.', 8, TENUE, 'start')
    c.t(14, 302, 'Si el ángulo se cierra, el pasaje se estrecha.', 8, TENUE, 'start')
    # Panel B: resistencia contra radio
    bx, by, bw, bh = 300, 52, 200, 190
    c.t(bx - 20, 20, 'B · Resistencia contra radio', 10.5, TINTA, 'start', 700)
    X = lambda r: bx + (r - 0.4) / 1.2 * bw
    Y = lambda v: by + bh - v / 20 * bh
    c.l(bx, by + bh, bx + bw, by + bh, FUERTE, 1)
    c.l(bx, by, bx, by + bh, FUERTE, 1)
    pts = []
    r = 0.5
    while r <= 1.6 + 1e-9:
        v = min(1 / r ** 4, 20)
        pts.append((X(r), Y(v)))
        r += 0.01
    c.poli(pts, COCLEAR, 2.2)
    for rr, lab in ((0.5, '1/2'), (1.0, '1'), (1.5, '1,5')):
        c.l(X(rr), by + bh, X(rr), by + bh + 4, FUERTE, 1)
        c.t(X(rr), by + bh + 16, lab, 8, TENUE)
    for v in (1, 5, 10, 16):
        c.l(bx - 4, Y(v), bx, Y(v), FUERTE, 1)
        c.t(bx - 8, Y(v) + 3, v, 8, TENUE, 'end')
    c.t(bx + bw / 2, by + bh + 32, 'radio del pasaje (1 = el de partida)', 8.5, TENUE)
    c.t(bx - 8, by - 10, 'resistencia', 8.5, TENUE, 'start')
    for rr in (0.5, 1.0):
        v = 1 / rr ** 4
        c.circ(X(rr), Y(v), 4.5, '#fff', AVISO, 1.8)
    c.t(X(0.5) + 10, Y(16) + 14, 'mitad del radio: 16 veces', 8.5, AVISO, 'start', 700)
    c.t(X(1.0) + 6, Y(1) - 8, 'punto de partida', 8.5, TINTA, 'start', 600)
    c.t(bx - 20, 300, 'Tubo rígido de flujo laminar: R crece como 1/r⁴.', 8, TENUE, 'start')
    # Panel C: Bernoulli
    cx, cy = 545, 120
    c.t(cx - 10, 20, 'C · Estrechez y presión', 10.5, TINTA, 'start', 700)
    # tubo con estrechamiento y pared lateral móvil
    c.path(f'M {cx},{cy - 50} L {cx + 60},{cy - 50} Q {cx + 100},{cy - 50} {cx + 120},{cy - 20} '
           f'Q {cx + 140},{cy - 50} {cx + 180},{cy - 50}', 'none', TINTA, 2.4)
    c.path(f'M {cx},{cy + 50} L {cx + 60},{cy + 50} Q {cx + 100},{cy + 50} {cx + 120},{cy + 20} '
           f'Q {cx + 140},{cy + 50} {cx + 180},{cy + 50}', 'none', TINTA, 2.4)
    for dy, g in ((-34, 1.4), (-14, 1.8), (14, 1.8), (34, 1.4)):
        c.l(cx + 8, cy + dy, cx + 54, cy + dy, RETRO, g, extra='')
        sy = dy * 0.38
        c.l(cx + 94, cy + sy, cx + 146, cy + sy, RETRO, g + 1.4)
        c.l(cx + 150, cy + dy, cx + 176, cy + dy, RETRO, g)
    c.t(cx + 30, cy - 62, 'lento', 8.5, TENUE, 'middle')
    c.t(cx + 120, cy - 62, 'rápido', 8.5, RETRO, 'middle', 700)
    c.t(cx + 30, cy + 74, 'presión mayor', 8.5, TENUE, 'middle')
    c.t(cx + 120, cy + 74, 'presión menor', 8.5, AVISO, 'middle', 700)
    c.l(cx + 120, cy - 17, cx + 120, cy - 3, AVISO, 2.4, extra=' marker-end="url(#p-flujo)"')
    c.t(cx - 10, cy + 110, 'Si la pared es blanda, la presión menor', 8.5, TINTA, 'start', 600)
    c.t(cx - 10, cy + 123, 'tira de ella hacia dentro:', 8.5, TINTA, 'start', 600)
    c.t(cx - 10, cy + 136, 'colapso inspiratorio.', 8.5, TINTA, 'start', 600)
    c.t(cx - 10, cy + 155, 'Solo la idea: la nariz es más compleja y su', 8, TENUE, 'start')
    c.t(cx - 10, cy + 167, 'flujo es en parte turbulento.', 8, TENUE, 'start')
    c.t(14, 352, 'Tres ideas de física sobre un mismo punto, la válvula nasal.', 8, TENUE, 'start')
    c.guardar('h25-valvula.svg', punta('p-flujo', AVISO))


# ---------------------------------------------------------------- equipo
def equipo():
    c = Lienzo(760, 400)
    c.t(14, 20, 'Lo que se usa en la rinoscopía anterior', 10.5, TINTA, 'start', 700)
    # --- espéculo nasal bivalvo (de perfil) ---
    ox, oy = 40, 80
    c.path(f'M {ox},{oy + 30} L {ox + 70},{oy + 22} L {ox + 70},{oy + 62} L {ox},{oy + 56} Z', '#dcdcdf', TINTA, 1.5)
    c.path(f'M {ox + 70},{oy + 22} L {ox + 108},{oy + 26} L {ox + 108},{oy + 62} L {ox + 70},{oy + 62} Z', '#bdbdc2', TINTA, 1.5)
    c.circ(ox + 108, oy + 44, 5, '#fff', TINTA, 1.5)
    # mangos y resorte
    c.path(f'M {ox + 108},{oy + 40} Q {ox + 170},{oy + 10} {ox + 215},{oy - 10}', 'none', TINTA, 7)
    c.path(f'M {ox + 108},{oy + 48} Q {ox + 170},{oy + 80} {ox + 215},{oy + 100}', 'none', TINTA, 7)
    c.path(f'M {ox + 108},{oy + 40} Q {ox + 170},{oy + 10} {ox + 215},{oy - 10}', 'none', '#dcdcdf', 4)
    c.path(f'M {ox + 108},{oy + 48} Q {ox + 170},{oy + 80} {ox + 215},{oy + 100}', 'none', '#dcdcdf', 4)
    c.path(f'M {ox + 150},{oy + 30} Q {ox + 130},{oy + 44} {ox + 150},{oy + 58}', 'none', COCLEAR, 2)
    c.t(ox + 110, oy + 142, 'Espéculo nasal bivalvo', 9.5, TINTA, 'middle', 700)
    c.t(ox + 110, oy + 156, 'Las valvas abren; los mangos quedan', 8.2, TENUE, 'middle')
    c.t(ox + 110, oy + 168, 'en la mano que lo sostiene.', 8.2, TENUE, 'middle')
    # vista de las valvas abiertas desde la punta
    c.elip(ox + 200, oy + 205, 38, 30, '#fff', FUERTE, 1)
    c.path(f'M {ox + 168},{oy + 205} Q {ox + 200},{oy + 170} {ox + 232},{oy + 205}', 'none', TINTA, 3)
    c.path(f'M {ox + 168},{oy + 205} Q {ox + 200},{oy + 240} {ox + 232},{oy + 205}', 'none', TINTA, 3)
    c.t(ox + 200, oy + 248, 'valvas abiertas, de frente', 8.2, TENUE, 'middle')
    # --- espejo frontal ---
    mx, my = 360, 105
    c.path(f'M {mx - 70},{my + 40} Q {mx},{my - 40} {mx + 70},{my + 40}', 'none', '#7d7d83', 5)
    c.circ(mx, my + 16, 36, '#e8f0f2', '#7d7d83', 3)
    c.circ(mx, my + 16, 6, '#fff', '#7d7d83', 1.5)
    c.circ(mx, my + 16, 26, 'none', '#a7bcc2', 1)
    c.t(mx, my + 85, 'Espejo frontal', 9.5, TINTA, 'middle', 700)
    c.t(mx, my + 99, 'Cóncavo y con un agujero central: miras', 8.2, TENUE, 'middle')
    c.t(mx, my + 111, 'por él mientras refleja la luz de la lámpara.', 8.2, TENUE, 'middle')
    # --- lámpara de cuello flexible ---
    lx, ly = 560, 70
    c.path(f'M {lx},{ly + 240} L {lx + 70},{ly + 240} L {lx + 62},{ly + 226} L {lx + 8},{ly + 226} Z', '#bdbdc2', TINTA, 1.5)
    c.path(f'M {lx + 35},{ly + 226} C {lx + 35},{ly + 140} {lx - 20},{ly + 120} {lx - 20},{ly + 60}', 'none', '#7d7d83', 6)
    c.path(f'M {lx - 20},{ly + 60} L {lx - 56},{ly + 24} L {lx - 8},{ly + 4} L {lx + 22},{ly + 44} Z', '#ffe9a8', TINTA, 1.5)
    c.l(lx - 56, ly + 24, lx - 120, ly + 38, COCLEAR, 1.4, '5 3')
    c.l(lx - 56, ly + 24, lx - 112, ly + 4, COCLEAR, 1.4, '5 3')
    c.t(lx + 35, ly + 266, 'Lámpara de cuello flexible', 9.5, TINTA, 'middle', 700)
    c.t(lx + 35, ly + 280, 'A un lado del paciente; el cuello flexible', 8.2, TENUE, 'middle')
    c.t(lx + 35, ly + 292, 'deja la luz apuntada sin sostenerla.', 8.2, TENUE, 'middle')
    c.guardar('h25-equipo.svg')


# ---------------------------------------------------------------- posiciones de cabeza
def posiciones():
    c = Lienzo(760, 290)
    c.t(14, 20, 'Hasta dónde llega la mirada según la inclinación de la cabeza', 10.5, TINTA, 'start', 700)
    s = 0.42
    for i, (ang, tit, que) in enumerate(((0, 'Cabeza recta (0°)', 'piso, cabeza del cornete inferior, tabique'),
                                         (30, '30° de extensión', 'cornete medio y meato medio'),
                                         (60, '60° de extensión', 'techo de la fosa y zona alta del tabique'))):
        ox, oy = 6 + i * 250, 50
        P = cavidad(c, ox, oy, s)
        # punto de entrada: vestíbulo
        x0, y0 = P(135, 262)
        rad = math.radians(ang)
        long = (150, 125, 78)[i]
        x1, y1 = x0 + long * math.cos(rad), y0 - long * math.sin(rad)
        # cono de luz
        for da in (-9, 9):
            xr, yr = x0 + long * math.cos(rad + math.radians(da)), y0 - long * math.sin(rad + math.radians(da))
            c.l(x0, y0, xr, yr, AVISO, 1.2, '4 3')
        c.l(x0, y0, x1, y1, AVISO, 2.4)
        c.circ(x0, y0, 3.4, AVISO, AVISO)
        c.t(ox + 120, 222, tit, 9.2, TINTA, 'middle', 700)
        c.t(ox + 120, 236, que, 8, TENUE, 'middle')
    c.t(14, 280, 'La luz y la mirada entran por el vestíbulo; al extender la cabeza la línea de visión sube dentro de la nariz.', 8, TENUE, 'start')
    c.guardar('h25-posiciones.svg')


if __name__ == '__main__':
    fosa_lateral()
    ciclo_corte()
    valvula()
    equipo()
    posiciones()
