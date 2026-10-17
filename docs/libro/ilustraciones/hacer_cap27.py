#!/usr/bin/env python3
"""Ilustraciones del capítulo 27 (mareo que no se va):

    cap27-curso.svg      esquema: tras un evento agudo, cómo baja el mareo cuando compensa y cómo se queda en el PPPD
    cap27-ciclo.svg      esquema: el círculo que mantiene el PPPD (vigilancia, rigidez, dependencia visual)
    cap27-criterios.svg  los cinco criterios de la Sociedad Bárány aplicados a los tres casos del capítulo

Esquemas docentes sin cifras: las curvas ilustran el principio, no los tiempos de un paciente. Los criterios
vienen de Staab y cols. (2017); lo que se marca de cada caso es lo que el texto del capítulo entrega.
    python3 docs/libro/ilustraciones/hacer_cap27.py"""
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
OD, OI = '#c62f3a', '#2b5fa8'
VERDE, NARANJA, MORADO = '#21796c', '#c0571c', '#6b4a9e'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{esc(s)}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}"{d}/>')

    def r(self, x, y, w, h, fill, op=1, stroke='none', rx=0):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                        f'fill-opacity="{op}" stroke="{stroke}"/>')

    def c(self, x, y, r, fill, stroke='none', w=1):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')

    def poli(self, pts, color, w=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def flecha(self, x1, y1, x2, y2, color=TINTA, w=1.6):
        import math
        self.l(x1, y1, x2, y2, color, w)
        a = math.atan2(y2 - y1, x2 - x1)
        for d in (2.6, -2.6):
            self.l(x2, y2, x2 - 9 * math.cos(a + d * 0.18), y2 - 9 * math.sin(a + d * 0.18), color, w)

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def curso():
    c = Lienzo(720, 330)
    ox, oy, w, h = 70, 50, 620, 220
    c.t(380, 24, 'Después de un evento agudo: dos caminos del mismo síntoma', 13, TINTA, 'middle', 700)
    c.r(ox, oy, w, h, '#fff', 1, FUERTE)
    for k in range(1, 4):
        c.l(ox, oy + k * h / 4, ox + w, oy + k * h / 4, GRILLA, 1)
    x0 = ox + 70                       # el evento
    c.r(ox, oy, x0 - ox, h, TENUE, 0.07)
    c.t(ox + 35, oy + 16, 'antes', 10, TENUE)
    c.l(x0, oy, x0, oy + h, TENUE, 1.2, '5 4')
    c.t(x0 + 6, oy + 16, 'evento agudo (neuritis, VPPB, crisis, pánico)', 10, TENUE, 'start')
    Y = lambda v: oy + h - 14 - v * (h - 40)
    # compensa: pico y baja hasta cerca de cero
    comp = [(ox, Y(0.02)), (x0 - 2, Y(0.02)), (x0 + 6, Y(1.0)), (x0 + 60, Y(0.62)), (x0 + 150, Y(0.30)),
            (x0 + 270, Y(0.10)), (x0 + 420, Y(0.04)), (ox + w - 8, Y(0.03))]
    # persiste: baja un poco y se queda en meseta, con picos al exponerse
    base = [(ox, Y(0.02)), (x0 - 2, Y(0.02)), (x0 + 6, Y(1.0)), (x0 + 60, Y(0.66)), (x0 + 150, Y(0.50)),
            (x0 + 250, Y(0.46))]
    pers = list(base)
    for k, cx in enumerate([x0 + 290, x0 + 370, x0 + 450, x0 + 520]):
        pers += [(cx - 18, Y(0.46)), (cx, Y(0.64 if k % 2 == 0 else 0.58)), (cx + 20, Y(0.46))]
    pers.append((ox + w - 8, Y(0.46)))
    c.poli(comp, VERDE, 2.6)
    c.poli(pers, NARANJA, 2.6)
    c.t(ox + w - 10, Y(0.03) - 8, 'compensa: el mareo se apaga', 11, VERDE, 'end', 700)
    c.t(ox + w - 10, Y(0.46) + 22, 'PPPD: el mareo se queda y sube al exponerse', 11, NARANJA, 'end', 700)
    c.t(x0 + 395, Y(0.74) - 6, 'supermercado, pantallas,', 9.5, TENUE)
    c.t(x0 + 395, Y(0.74) + 6, 'caminar, multitudes', 9.5, TENUE)
    c.l(x0 + 100, oy + h + 12, x0 + 255, oy + h + 12, FUERTE, 1)
    c.t(x0 + 178, oy + h + 26, 'semanas: aún es lo esperable', 10, TENUE)
    c.l(x0 + 270, oy + h + 12, ox + w - 8, oy + h + 12, TENUE, 1.4)
    c.t(x0 + 270 + (ox + w - 8 - x0 - 270) / 2, oy + h + 26, 'meses: el criterio A pide al menos 3', 10, TINTA, 'middle', 700)
    c.out.append(f'<text transform="translate(22,{oy + h / 2}) rotate(-90)" {F} font-size="11" fill="{TINTA}" text-anchor="middle">'
                 f'molestia por mareo e inestabilidad</text>')
    c.guardar('cap27-curso.svg')


def ciclo():
    c = Lienzo(720, 380)
    c.t(360, 24, 'El círculo que mantiene el mareo', 13, TINTA, 'middle', 700)
    nodos = {
        'ev': (360, 82, 'Un evento que mareó', 'neuritis, VPPB, migraña, pánico', MORADO),
        'vig': (590, 190, 'Vigilancia', 'atención puesta en el cuerpo y el entorno', NARANJA),
        'rig': (500, 316, 'Rigidez postural', 'se tensa el tronco y las piernas, se mira fijo', NARANJA),
        'dep': (220, 316, 'Peso de más a la vista', 'el entorno visual y el movimiento mandan', NARANJA),
        'sin': (130, 190, 'Síntomas', 'de pie, al moverse, con mucha imagen', OD),
    }
    for k, (x, y, tit, sub, col) in nodos.items():
        c.r(x - 100, y - 24, 200, 48, '#fff', 1, col, 8)
        c.r(x - 100, y - 24, 6, 48, col, 1, 'none', 3)
        c.t(x + 3, y - 4, tit, 12, TINTA, 'middle', 700)
        c.t(x + 3, y + 13, sub, 9.5, TENUE)
    A = lambda a, b, ax, ay, bx, by: c.flecha(ax, ay, bx, by, TENUE, 1.8)
    c.flecha(448, 104, 536, 156, TENUE)   # evento -> vigilancia
    c.flecha(570, 216, 540, 288, TENUE)   # vigilancia -> rigidez
    c.flecha(400, 316, 320, 316, TENUE)   # rigidez -> dependencia
    c.flecha(180, 288, 150, 216, TENUE)   # dependencia -> síntomas
    c.flecha(176, 168, 270, 104, TENUE)   # síntomas -> (vuelve al evento: miedo a que vuelva)
    c.t(360, 196, 'cada vez que marea,', 10.5, TINTA, 'middle', 700)
    c.t(360, 211, 'la vigilancia sube', 10.5, TINTA, 'middle', 700)
    c.t(360, 232, 'y el círculo se cierra', 10, TENUE)
    c.t(360, 366, 'Según la fisiopatología que describen Staab y cols. (2017) y Popkirov y cols. (2018).', 9.5, TENUE)
    c.guardar('cap27-ciclo.svg')


def criterios():
    c = Lienzo(720, 330)
    c.t(360, 22, 'Los cinco criterios de la Sociedad Bárány, aplicados a los tres casos', 13, TINTA, 'middle', 700)
    filas = [
        ('A', 'Síntomas casi todos los días, 3 meses o más'),
        ('B', 'Peor de pie, al moverse o con mucho estímulo visual'),
        ('C', 'Empezó tras una enfermedad o un evento que mareó'),
        ('D', 'Molestia importante o limitación'),
        ('E', 'No se explica mejor por otra enfermedad'),
    ]
    casos = [('Victoria', 'neuritis'), ('Eva', 'VPPB'), ('Joaquín', 'oído izquierdo')]
    marcas = {  # (símbolo, color)
        'Victoria': ['si', 'si', 'si', 'si', 'si'],
        'Eva': ['si', 'si', 'si', 'si', 'si'],
        'Joaquín': ['si', 'no', 'no', 'si', 'no'],
    }
    x0, wcol = 380, 110
    top = 52
    for j, (n, sub) in enumerate(casos):
        cx = x0 + j * wcol + wcol / 2 - 20
        c.t(cx, top - 6, n, 12, TINTA, 'middle', 700)
        c.t(cx, top + 8, sub, 9.5, TENUE)
    rh = 46
    for i, (let, txt) in enumerate(filas):
        y = top + 22 + i * rh
        if i % 2 == 0:
            c.r(14, y, 700, rh - 6, TENUE, 0.06, rx=4)
        c.c(40, y + rh / 2 - 3, 12, TINTA)
        c.t(40, y + rh / 2 + 1, let, 12, '#fff', 'middle', 700)
        c.t(62, y + rh / 2 + 1, txt, 11.5, TINTA, 'start')
        for j, (n, _) in enumerate(casos):
            cx = x0 + j * wcol + wcol / 2 - 20
            m = marcas[n][i]
            if m == 'si':
                c.c(cx, y + rh / 2 - 3, 12, VERDE)
                c.poli([(cx - 5, y + rh / 2 - 3), (cx - 1, y + rh / 2 + 1), (cx + 6, y + rh / 2 - 8)], '#fff', 2.4)
            else:
                c.c(cx, y + rh / 2 - 3, 12, OD)
                c.l(cx - 5, y + rh / 2 - 8, cx + 5, y + rh / 2 + 2, '#fff', 2.4)
                c.l(cx - 5, y + rh / 2 + 2, cx + 5, y + rh / 2 - 8, '#fff', 2.4)
    c.t(360, 318, 'Joaquín no cumple B, C ni E: sus síntomas empeoran a oscuras y su oído izquierdo explica el cuadro (caso 27.3).', 10, TENUE)
    c.guardar('cap27-criterios.svg')


if __name__ == '__main__':
    curso()
    ciclo()
    criterios()
