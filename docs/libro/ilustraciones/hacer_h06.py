#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H6 (pruebas supraliminares):

    h06-sonoridad.svg   crecimiento de la sonoridad (normal, coclear, retrococlear)
                        y las escaleras del Fowler que salen de esas curvas
    h06-adaptacion.svg  la descarga del nervio durante un tono continuo y los
                        relojes del Carhart y del Rosenberg

SVG propios, no IA: son esquemas. Las cifras del Fowler son las mismas de la
tabla "Cómo se lee el Fowler" del capítulo (ilustrativas, no datos)."""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
NORMAL, COCLEAR, RETRO, AVISO = '#24101a', '#c0571c', '#21796c', '#c62f3a'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2   # la figura va a todo el ancho de la página: letra legible impresa


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400, rot=None):
        tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ''
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}"{tr}>{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}{extra}/>')

    def poli(self, pts, color, w=2.2, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}{extra}/>')

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


# ---------------------------------------------------------------- sonoridad
def sonoridad():
    c = Lienzo(700, 318)
    # Panel A: sonoridad contra nivel
    x0, y0, ancho, alto = 112, 46, 300, 190
    X = lambda db: x0 + db / 120 * ancho
    Y = lambda s: y0 + alto - s / 6 * alto
    c.t(14, 20, 'A · Cuánto suena el tono a medida que sube', 10.5, TINTA, 'start', 700)
    categorias = ['umbral', 'muy suave', 'suave', 'cómoda', 'fuerte', 'muy fuerte', 'molesta']
    for i, nombre in enumerate(categorias):
        c.l(x0, Y(i), x0 + ancho, Y(i), FUERTE if i in (0, 6) else GRILLA, 0.7)
        c.t(x0 - 6, Y(i) + 3, nombre, 8, TENUE, 'end')
    for db in range(0, 121, 20):
        c.l(X(db), y0, X(db), y0 + alto, GRILLA, 0.5)
        c.t(X(db), y0 + alto + 12, db, 8, TENUE)
    c.t(x0 + ancho / 2, y0 + alto + 25, 'nivel del tono (dB HL)', 8.5, TENUE)

    normal = lambda db: 6 * (db - 10) / 100            # umbral 10, molestia 110
    # Coclear: los pares de igual sonoridad de la tabla del Fowler (completo)
    pares_c = [(45, 10), (55, 30), (65, 50), (70, 70), (110, 110)]
    coclear = [(X(e), Y(normal(r))) for e, r in pares_c]
    retro = [(X(db), Y(normal(db - 35))) for db in (45, 120)]

    # misma sonoridad: una línea horizontal corta las tres curvas
    s = normal(50)
    c.l(X(50), Y(s), X(85), Y(s), TENUE, 1, '2 3')
    for db, col in ((50, NORMAL), (65, COCLEAR), (85, RETRO)):
        c.l(X(db), Y(s), X(db), y0 + alto, col, 0.8, '2 3')
    c.t(X(87), Y(0.75), 'igual de fuerte en', 8, TENUE, 'start')
    c.t(X(87), Y(0.75) + 11, '50 · 65 · 85 dB HL', 8, TENUE, 'start')

    c.poli([(X(10), Y(0)), (X(110), Y(6))], NORMAL, 2.2)
    c.poli(coclear, COCLEAR, 2.6, '7 3')
    c.poli(retro, RETRO, 2.6, '2 3', ' marker-end="url(#p-retro)"')
    for x, y, col in ((X(110), Y(6), NORMAL),):
        c.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#fff" stroke="{col}" stroke-width="1.6"/>')

    # rótulos de las curvas
    c.t(X(12), Y(1.6), 'normal', 9, NORMAL, 'start', 700)
    c.t(X(44), Y(2.2), 'coclear', 9, COCLEAR, 'end', 700)
    c.t(X(96), Y(2.3), 'retrococlear', 9, RETRO, 'start', 700)
    c.t(X(112), Y(6) - 8, 'LDL', 8, TINTA, 'middle', 700)

    # campo dinámico, bajo el gráfico
    yb = y0 + alto + 44
    c.t(x0 - 6, yb - 10, 'campo dinámico', 8.5, TINTA, 'end', 700)
    for k, (a, b, col, txt) in enumerate(((10, 110, NORMAL, '100 dB'), (45, 110, COCLEAR, '65 dB: estrecho'),
                                          (45, 120, RETRO, 'más de 75 dB: no marca molestia'))):
        y = yb + k * 13
        c.l(X(a), y, X(b), y, col, 5, extra=' stroke-linecap="round" opacity=".75"')
        c.t(X(b) + 6, y + 3, txt, 8, col, 'start', 600)

    # Panel B: las escaleras del Fowler que salen de las curvas
    bx, by, bal = 500, 46, 190
    YB = lambda db: by + db / 120 * bal
    c.t(bx - 32, 20, 'B · El Fowler lee esas curvas', 10.5, TINTA, 'start', 700)
    for db in range(0, 121, 20):
        c.t(bx - 10, YB(db) + 3, db, 8, TENUE, 'end')
    escaleras = (('reclutamiento|completo', COCLEAR, [(10, 45), (30, 55), (50, 65), (70, 70)], bx),
                 ('sin|reclutamiento', RETRO, [(10, 45), (30, 65), (50, 85), (70, 105)], bx + 100))
    for titulo, col, pares, xa in escaleras:
        xb = xa + 52
        for x in (xa, xb):
            c.l(x, by, x, by + bal, FUERTE, 1)
        c.t(xa, by - 8, 'ref.', 8, TENUE)
        c.t(xb, by - 8, 'estudio', 8, TENUE)
        for r, e in pares:
            c.l(xa, YB(r), xb, YB(e), col, 1.8)
            c.out.append(f'<circle cx="{xa}" cy="{YB(r):.1f}" r="3" fill="#fff" stroke="{TINTA}" stroke-width="1.3"/>')
            c.out.append(f'<circle cx="{xb}" cy="{YB(e):.1f}" r="3" fill="#fff" stroke="{col}" stroke-width="1.6"/>')
        for k, renglon in enumerate(titulo.split('|')):
            c.t((xa + xb) / 2, by + bal + 16 + 11 * k, renglon, 8.5, col, 'middle', 700)
    c.t(bx + 76, by + bal + 48, 'dB HL hacia abajo, como en el audiograma.', 8, TENUE)
    c.t(bx + 76, by + bal + 60, 'Se cierran: recluta. Paralelas: no.', 8, TENUE)
    c.guardar('h06-sonoridad.svg', punta('p-retro', RETRO))


# --------------------------------------------------------------- adaptación
def adaptacion():
    c = Lienzo(700, 262)
    # Panel A: descarga del nervio en el minuto
    x0, y0, ancho, alto = 70, 44, 300, 170
    X = lambda s: x0 + s / 60 * ancho
    Y = lambda v: y0 + alto - v * alto
    c.t(14, 20, 'A · Un tono continuo durante un minuto', 10.5, TINTA, 'start', 700)
    for s in range(0, 61, 10):
        c.l(X(s), y0, X(s), y0 + alto, GRILLA, 0.5)
        c.t(X(s), y0 + alto + 12, s, 8, TENUE)
    c.t(x0 + ancho / 2, y0 + alto + 25, 'segundos de tono', 8.5, TENUE)
    c.l(x0, y0, x0, y0 + alto, FUERTE, 1)
    c.l(x0, y0 + alto, x0 + ancho, y0 + alto, FUERTE, 1)
    c.t(x0 - 10, y0 + alto / 2, 'descarga del nervio', 8.5, TENUE, 'middle', 400, -90)

    umbral = 0.3
    c.l(x0, Y(umbral), x0 + ancho, Y(umbral), AVISO, 1.1, '5 3')
    c.t(x0 + ancho - 2, Y(umbral) - 5, 'lo que hace falta para oír el tono', 8, AVISO, 'end')

    def traza(sostenido, tau_lento, pico):
        pts = [(X(0), Y(0)), (X(0.05), Y(pico))]
        for i in range(1, 241):
            s = i / 4
            rapido = (pico - 0.62) * math.exp(-s / 0.6)
            v = 0.62 * (sostenido + (1 - sostenido) * math.exp(-s / tau_lento)) + rapido
            pts.append((X(s), Y(v)))
        return pts

    sano = traza(1.0, 1, 0.95)
    nervio = traza(0.1, 22, 0.85)
    c.poli(sano, NORMAL, 2.2)
    c.poli(nervio, RETRO, 2.4, '6 3')
    # dónde cruza el nervio la línea
    s_cruce = next(i / 4 for i in range(1, 241)
                   if 0.62 * (0.1 + 0.9 * math.exp(-(i / 4) / 22)) < umbral)
    c.l(X(s_cruce), Y(umbral) - 4, X(s_cruce), y0 + alto, RETRO, 0.9, '2 2')
    c.out.append(f'<circle cx="{X(s_cruce):.1f}" cy="{Y(umbral):.1f}" r="3.6" fill="{RETRO}"/>')
    c.t(X(s_cruce) - 6, Y(umbral) + 16, 'baja la mano', 8.5, RETRO, 'end', 700)
    c.t(X(30), Y(0.62) - 7, 'fibra sana: se adapta y se sostiene', 8.5, NORMAL, 'middle', 700)
    c.t(X(2.2), Y(0.95) + 2, 'arranque', 8, TENUE, 'start')
    c.t(X(14), Y(0.47) + 3, 'nervio comprimido', 8.5, RETRO, 'start', 700)

    RELOJ = '#5b4f72'
    # Panel B: los relojes
    bx, ancho_b = 430, 250
    XB = lambda s: bx + s / 120 * ancho_b
    c.t(bx - 18, 20, 'B · Qué hace el reloj cuando baja la mano', 10.5, TINTA, 'start', 700)
    for s in (0, 30, 60, 90, 120):
        c.l(XB(s), 44, XB(s), 214, GRILLA, 0.5)
        c.t(XB(s), 226, s, 8, TENUE)
    c.t(bx + ancho_b / 2, 239, 'segundos desde el primer tono', 8.5, TENUE)

    def barra(y, tramos, titulo, col):
        c.t(bx, y - 12, titulo, 9, col, 'start', 700)
        for a, b, nivel, op in tramos:
            c.out.append(f'<rect x="{XB(a):.1f}" y="{y:.1f}" width="{XB(b) - XB(a):.1f}" height="16" '
                         f'fill="{col}" opacity="{op}" stroke="#fff" stroke-width="1.5"/>')
            c.t((XB(a) + XB(b)) / 2, y + 11.5, nivel, 8, '#fff', 'middle', 700)

    # Carhart: cada subida abre un minuto nuevo
    barra(64, [(0, 20, 'umbral', .45), (20, 44, '+5', .65), (44, 104, '+10: minuto entero', .9)],
          'Carhart: el minuto vuelve a empezar', RELOJ)
    c.l(XB(44), 90, XB(104), 90, RELOJ, 1, extra=' marker-start="url(#p-c-ini)" marker-end="url(#p-c)"')
    c.t((XB(44) + XB(104)) / 2, 101, '60 s seguidos al mismo nivel', 8, RELOJ)
    c.t(bx, 116, 'deterioro = 10 dB', 8.5, TINTA, 'start', 700)

    # Rosenberg: un solo minuto
    barra(156, [(0, 18, '+5 SL', .45), (18, 41, '+10', .65), (41, 60, '+15', .9)],
          'Rosenberg: un solo minuto', RELOJ)
    c.l(XB(60), 146, XB(60), 182, TINTA, 1.4)
    c.t(XB(60) + 5, 168, 'fin', 8.5, TINTA, 'start', 700)
    c.t(bx, 199, 'subió 10 dB en el minuto = deterioro 10 dB', 8.5, TINTA, 'start', 700)

    defs = punta('p-c', RELOJ) + (f'<marker id="p-c-ini" markerWidth="6" markerHeight="6" refX="3" refY="3.5" '
                                    f'markerUnits="userSpaceOnUse" orient="auto-start-reverse">'
                                    f'<path d="M0,0 L7,3.5 L0,7 z" transform="scale(.8)" fill="{RELOJ}"/></marker>')
    c.guardar('h06-adaptacion.svg', defs)


if __name__ == '__main__':
    sonoridad()
    adaptacion()
