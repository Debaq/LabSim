#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H21 (medición electroacústica del audífono):

    h21-caja-acoplador.svg   la cámara de medida con el altavoz, el micrófono de referencia,
                             el audífono y el acoplador de 2 cc
    h21-curva-ejemplo.svg    curvas inventadas: OSPL90 y respuesta con 60 dB de entrada
    h21-distorsion-ruido.svg A: armónicos de un tono puro; B: ruido interno referido a la entrada

SVG propios, no IA. Son esquemas: ninguna curva ni cifra es de un audífono real."""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO = '#c0571c', '#21796c', '#c62f3a'
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

    def r(self, x, y, w, h, fill='none', color=TINTA, sw=1.2, rx=4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                        f'stroke="{color}" stroke-width="{sw}"{d}/>')

    def raw(self, s):
        self.out.append(s)

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


def caja():
    c = Lienzo(700, 330)
    c.t(14, 20, 'Montaje de la medición: cámara de medida, audífono y acoplador de 2 cc (esquema)', 10.5, TINTA, 'start', 700)
    # camara
    c.r(20, 40, 400, 250, '#f6f5f2', FUERTE, 1.5, 8)
    c.t(30, 58, 'cámara de medida (aislada del ruido)', 8.5, TENUE, 'start', 600)
    # altavoz
    c.r(40, 120, 16, 70, '#fff', TINTA, 1.4, 2)
    c.raw(f'<polygon points="56,125 86,100 86,210 56,185" fill="#fff" stroke="{TINTA}" stroke-width="1.4"/>')
    c.t(70, 230, 'altavoz', 9, TINTA, 'middle', 600)
    # ondas
    for i, rr in enumerate((24, 44, 64)):
        a = math.radians(32)
        pts = [(86 + rr * 0.9 + rr * math.cos(t), 155 + rr * math.sin(t)) for t in
               [(-a + 2 * a * k / 12) for k in range(13)]]
        c.poli(pts, COCLEAR, 1.4)
    c.t(200, 100, 'tono puro que barre las frecuencias', 8.5, COCLEAR, 'middle', 600)
    # micro referencia
    c.r(205, 130, 10, 36, '#fff', RETRO, 1.6, 3)
    c.t(210, 182, 'micrófono de', 8, RETRO, 'middle', 600)
    c.t(210, 193, 'referencia', 8, RETRO, 'middle', 600)
    # audifono BTE (forma)
    c.raw(f'<path d="M262,150 C262,118 300,112 306,140 C310,165 296,196 282,198 C268,198 262,175 262,150 z" '
          f'fill="#e9e4dc" stroke="{TINTA}" stroke-width="1.4"/>')
    c.raw(f'<circle cx="275" cy="150" r="3" fill="{TINTA}"/>')
    c.t(284, 222, 'audífono', 9, TINTA, 'middle', 600)
    c.t(284, 234, '(abierto y encendido)', 8, TENUE, 'middle')
    # tubo
    c.poli([(300, 128), (330, 100), (350, 100)], TINTA, 3)
    c.t(318, 112, 'tubo corto', 8, TINTA, 'end', 600)
    # acoplador
    c.r(350, 80, 56, 40, '#fff', AVISO, 1.6, 4)
    c.t(378, 98, '2 cc', 10, AVISO, 'middle', 700)
    c.t(378, 111, 'acoplador', 8, AVISO, 'middle', 600)
    # micro medicion
    c.r(380, 124, 12, 30, '#fff', AVISO, 1.6, 3)
    c.t(378, 170, 'micrófono de', 8, AVISO, 'middle', 600)
    c.t(378, 181, 'medida', 8, AVISO, 'middle', 600)
    # cables
    c.poli([(420, 140), (450, 140), (450, 100), (480, 100)], TENUE, 1.2)
    c.poli([(420, 150), (440, 150), (440, 230), (480, 230)], TENUE, 1.2)
    # analizador
    c.r(480, 60, 190, 210, '#fff', TINTA, 1.5, 8)
    c.t(575, 82, 'analizador de audífonos', 9.5, TINTA, 'middle', 700)
    c.t(575, 100, 'genera el tono y regula', 8.5, TINTA)
    c.t(575, 112, 'su nivel con el micrófono de referencia', 8.5, TINTA)
    c.t(575, 134, 'mide la presión que llega', 8.5, TINTA)
    c.t(575, 146, 'al micrófono de medida', 8.5, TINTA)
    c.t(575, 168, 'calcula ganancia = salida − entrada', 8.5, COCLEAR, 'middle', 600)
    c.r(500, 188, 150, 62, '#f6f5f2', FUERTE, 1, 4)
    c.poli([(508, 238), (530, 228), (548, 214), (565, 204), (585, 210), (610, 224), (640, 240)], COCLEAR, 1.6)
    c.t(575, 262, 'pantalla: curva e informe', 8, TENUE)
    c.t(20, 312, 'Esquema para explicar la disposición; no representa un equipo en particular.', 8.5, TENUE, 'start')
    c.guardar('h21-caja-acoplador.svg')


def curva():
    c = Lienzo(700, 360)
    x0, x1, y0, y1 = 70, 660, 50, 300      # marco
    fmin, fmax = 200, 8000
    dmin, dmax = 30, 130

    def X(f):
        return x0 + (math.log10(f) - math.log10(fmin)) / (math.log10(fmax) - math.log10(fmin)) * (x1 - x0)

    def Y(d):
        return y1 - (d - dmin) / (dmax - dmin) * (y1 - y0)

    c.t(14, 20, 'Ejemplo de salida de un audífono en el acoplador de 2 cc', 10.5, TINTA, 'start', 700)
    for d in range(40, 131, 10):
        c.l(x0, Y(d), x1, Y(d), GRILLA, 0.8)
        c.t(x0 - 8, Y(d) + 3, str(d), 8.5, TENUE, 'end')
    for f in (250, 500, 1000, 2000, 4000, 8000):
        c.l(X(f), y0, X(f), y1, GRILLA, 0.8)
        c.t(X(f), y1 + 14, str(f), 8.5, TENUE)
    c.t(x0 - 40, (y0 + y1) / 2, 'dB SPL en el acoplador', 8.5, TENUE, 'middle')
    c.out[-1] = c.out[-1].replace('<text ', f'<text transform="rotate(-90 {x0 - 52} {(y0 + y1) / 2})" ', 1)
    c.t((x0 + x1) / 2, y1 + 32, 'frecuencia (Hz)', 8.5, TENUE)
    fs = [200 * (8000 / 200) ** (i / 120) for i in range(121)]

    def ospl(f):
        # forma inventada: sube, pico cerca de 2 kHz, cae en agudos
        return 70 + 38 * math.exp(-((math.log2(f / 1900)) ** 2) / 1.3) + 6 * math.exp(-((math.log2(f / 700)) ** 2) / 0.4)

    def rta(f):
        return 52 + 24 * math.exp(-((math.log2(f / 1800)) ** 2) / 1.8) + 3 * math.exp(-((math.log2(f / 800)) ** 2) / 0.5)

    c.poli([(X(f), Y(ospl(f))) for f in fs], AVISO, 2.4)
    c.poli([(X(f), Y(rta(f))) for f in fs], RETRO, 2.4)
    # entrada 60
    c.l(x0, Y(60), x1, Y(60), TENUE, 1, '5 3')
    c.t(x0 + 6, Y(60) - 5, 'entrada de 60 dB SPL', 8.5, TENUE, 'start')
    # pico OSPL90
    fp = max(fs, key=ospl)
    c.l(X(fp), Y(ospl(fp)), X(fp), y1, AVISO, 1, '2 3')
    c.raw(f'<circle cx="{X(fp):.1f}" cy="{Y(ospl(fp)):.1f}" r="4" fill="{AVISO}"/>')
    c.t(X(fp) + 8, Y(ospl(fp)) - 10, 'OSPL90 máximo', 9, AVISO, 'start', 700)
    # HFA
    for f in (1000, 1600, 2500):
        c.raw(f'<circle cx="{X(f):.1f}" cy="{Y(ospl(f)):.1f}" r="3" fill="#fff" stroke="{AVISO}" stroke-width="1.5"/>')
        c.raw(f'<circle cx="{X(f):.1f}" cy="{Y(rta(f)):.1f}" r="3" fill="#fff" stroke="{RETRO}" stroke-width="1.5"/>')
    c.l(X(1000), y0 + 6, X(2500), y0 + 6, TINTA, 1.2)
    c.l(X(1000), y0 + 2, X(1000), y0 + 10, TINTA, 1.2)
    c.l(X(2500), y0 + 2, X(2500), y0 + 10, TINTA, 1.2)
    c.t((X(1000) + X(2500)) / 2, y0 - 4, 'HFA: promedio en 1.000, 1.600 y 2.500 Hz', 8.5, TINTA, 'middle', 600)
    # ganancia
    xg = X(1600)
    c.raw(f'<line x1="{xg:.1f}" y1="{Y(60):.1f}" x2="{xg:.1f}" y2="{Y(rta(1600)) + 3:.1f}" stroke="{RETRO}" '
          f'stroke-width="1.6" marker-end="url(#gp)"/>')
    c.t(xg - 8, (Y(60) + Y(rta(1600))) / 2 + 3, 'ganancia', 8.5, RETRO, 'end', 700)
    c.t(130, Y(rta(250)) + 20, 'respuesta con 60 dB de entrada', 9, RETRO, 'start', 700)
    c.t(100, Y(88), 'OSPL90: salida con 90 dB de entrada', 9, AVISO, 'start', 700)
    c.t(14, 352, 'Curvas de ejemplo para explicar los términos: no son de ningún audífono ni tienen valores de referencia.', 8.5, TENUE, 'start')
    c.guardar('h21-curva-ejemplo.svg', punta('gp', RETRO))


def distorsion():
    c = Lienzo(700, 290)
    # Panel A: armonicos
    c.t(14, 20, 'A · Distorsión armónica', 10.5, TINTA, 'start', 700)
    xa, ya = 50, 230
    c.l(xa, ya, 320, ya, FUERTE, 1.2)
    c.t(310, ya + 26, 'frecuencia →', 8.5, TENUE, 'end')
    c.t(185, 44, 'salida del audífono con un tono puro de entrada', 8.5, TENUE)
    barras = [(90, 130, TINTA, 'f', 'tono de entrada'), (150, 40, AVISO, '2f', ''), (210, 22, AVISO, '3f', ''), (270, 11, AVISO, '4f', '')]
    for x, h, col, lab, nota in barras:
        c.r(x - 9, ya - h, 18, h, col, col, 0, 1)
        c.t(x, ya + 12, lab, 9, col, 'middle', 700)
    c.t(210, 100, 'armónicos: frecuencias que', 8.5, AVISO, 'middle', 600)
    c.t(210, 112, 'el audífono agrega y que no estaban', 8.5, AVISO, 'middle', 600)
    c.t(185, 268, 'distorsión = potencia de los armónicos / potencia del fundamental', 8.5, TINTA, 'middle', 600)
    # Panel B: EIN
    c.t(360, 20, 'B · Ruido interno referido a la entrada', 10.5, TINTA, 'start', 700)
    c.r(370, 60, 90, 56, '#fff', TINTA, 1.4, 4)
    c.t(415, 84, 'audífono', 9, TINTA, 'middle', 700)
    c.t(415, 98, 'con ganancia G', 8.5, TINTA)
    c.raw(f'<line x1="340" y1="88" x2="368" y2="88" stroke="{TINTA}" stroke-width="1.4" marker-end="url(#pa)"/>')
    c.raw(f'<line x1="462" y1="88" x2="492" y2="88" stroke="{TINTA}" stroke-width="1.4" marker-end="url(#pa)"/>')
    c.t(340, 76, 'entrada:', 8.5, TENUE, 'end')
    c.t(340, 88, 'silencio', 8.5, TENUE, 'end')
    c.t(500, 76, 'salida:', 8.5, TENUE, 'start')
    c.t(500, 88, 'siseo propio', 8.5, AVISO, 'start', 700)
    # ruido
    pts = []
    import random
    rnd = random.Random(21)
    for i in range(60):
        pts.append((500 + i * 3, 112 + rnd.uniform(-9, 9)))
    c.poli(pts, AVISO, 1)
    c.t(515, 148, 'nivel de salida sin señal', 8.5, AVISO, 'start', 600)
    c.t(515, 170, 'EIN = ese nivel de salida − ganancia', 9, TINTA, 'start', 700)
    c.t(380, 200, 'Es el nivel de un ruido imaginario a la entrada', 8.5, TINTA, 'start')
    c.t(380, 213, 'de un audífono perfecto que daría ese mismo siseo.', 8.5, TINTA, 'start')
    c.t(380, 233, 'Ese número es el que se puede comparar entre audífonos', 8.5, TENUE, 'start')
    c.t(380, 246, 'de distinta ganancia.', 8.5, TENUE, 'start')
    c.t(14, 282, 'Esquema: las alturas y los niveles son ilustrativos, no mediciones.', 8.5, TENUE, 'start')
    c.guardar('h21-distorsion-ruido.svg', punta('pa', TINTA))


if __name__ == '__main__':
    caja()
    curva()
    distorsion()
