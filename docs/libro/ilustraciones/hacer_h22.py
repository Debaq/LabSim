#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H22 (audiometría ocupacional):

    h22-intercambio.svg     tiempo diario permitido según el nivel, con tasa de intercambio de 3 dB y de 5 dB
    h22-cambio-umbral.svg   dos controles inventados de un mismo trabajador contra su base, y qué dice cada criterio
    h22-flujo.svg           del control periódico al cambio confirmado

SVG propios, no IA. Las cifras del primer dibujo salen de las fórmulas de NIOSH (1998) y OSHA
(29 CFR 1910.95, Tabla G-16); los umbrales del segundo son inventados para el ejemplo (parten de la
base real del paciente de práctica 33, todo en 0 dB HL); el tercero es un esquema."""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
ROJO, AZUL, VERDE, AVISO, NARANJA = '#c62f3a', '#2b5fa8', '#21796c', '#c62f3a', '#c0571c'
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

    def rect(self, x, y, w, h, fill='none', stroke=None, sw=1, rx=0, extra=''):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                        f'fill="{fill}"{s}{extra}/>')

    def circ(self, x, y, r, fill='none', stroke=None, sw=1.6):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"{s}/>')

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


# ---------------------------------------------------------------- tasa de intercambio
def t3(nivel):   # NIOSH 1998: T(min) = 480 / 2^((L-85)/3)
    return 480 / 2 ** ((nivel - 85) / 3)


def t5(nivel):   # OSHA, Tabla G-16 (equivale a 480 / 2^((L-90)/5))
    return 480 / 2 ** ((nivel - 90) / 5)


def intercambio():
    c = Lienzo(700, 270)
    x0, x1, y0, y1 = 70, 660, 36, 214          # área del gráfico
    niveles = (80, 115)
    tmin, tmax = 1, 1000                       # minutos, escala log

    def X(n):
        return x0 + (n - niveles[0]) / (niveles[1] - niveles[0]) * (x1 - x0)

    def Y(m):
        return y1 - (math.log10(m) - math.log10(tmin)) / (math.log10(tmax) - math.log10(tmin)) * (y1 - y0)

    c.t(14, 20, 'Cuánto tiempo al día se puede estar a cada nivel (dB(A))', 10.5, TINTA, 'start', 700)
    for m, et in ((1, '1 min'), (10, '10 min'), (60, '1 h'), (480, '8 h')):
        c.l(x0, Y(m), x1, Y(m), GRILLA, 1)
        c.t(x0 - 8, Y(m) + 4, et, 8.5, TENUE, 'end')
    for n in range(80, 116, 5):
        c.l(X(n), y1, X(n), y1 + 4, FUERTE, 1)
        c.t(X(n), y1 + 18, str(n), 9, TENUE)
    c.t((x0 + x1) / 2, y1 + 38, 'nivel de presión sonora continuo equivalente, dB(A)', 9, TENUE)
    c.l(x0, y0, x0, y1, FUERTE, 1)
    c.l(x0, y1, x1, y1, FUERTE, 1)

    for f, color, a, b in ((t3, VERDE, 85, 115), (t5, NARANJA, 90, 115)):
        pts = [(X(n), Y(f(n))) for n in range(a, b + 1)]
        c.poli(pts, color, 2.4)
    # puntos de referencia (valores de las fuentes)
    for n in (85, 88, 91, 94, 100):
        c.circ(X(n), Y(t3(n)), 3.2, VERDE)
    for n in (90, 95, 100, 105, 110, 115):
        c.circ(X(n), Y(t5(n)), 3.2, NARANJA)
    # etiquetas
    c.t(X(85) + 8, Y(480) - 8, '85 dB(A): 8 h', 9, VERDE, 'start', 700)
    c.t(X(90) + 8, Y(480) - 8, '90 dB(A): 8 h', 9, NARANJA, 'start', 700)
    c.t(X(100) - 6, Y(t3(100)) + 22, '100 dB(A): 15 min', 9, VERDE, 'end', 700)
    c.t(X(100) + 8, Y(t5(100)) - 6, '100 dB(A): 2 h', 9, NARANJA, 'start', 700)
    # leyenda
    c.l(90, 150, 122, 150, VERDE, 2.4)
    c.t(128, 154, '3 dB por cada mitad del tiempo', 9, TINTA, 'start')
    c.t(128, 167, 'NIOSH, Unión Europea, Chile', 8.5, TENUE, 'start')
    c.l(90, 184, 122, 184, NARANJA, 2.4)
    c.t(128, 188, '5 dB por cada mitad del tiempo', 9, TINTA, 'start')
    c.t(128, 201, 'OSHA (EE. UU.)', 8.5, TENUE, 'start')
    c.guardar('h22-intercambio.svg')


# ---------------------------------------------------------------- cambio de umbral
FREQS = ('500', '1 k', '2 k', '3 k', '4 k', '6 k', '8 k')
BASE = (0, 0, 0, 0, 0, 0, 0)
CASO_A = (0, 0, 5, 15, 30, 20, 10)
CASO_B = (0, 0, 0, 5, 20, 15, 5)


def criterios(base, ctrl):
    cambio = [b - a for a, b in zip(base, ctrl)]
    osha = sum(cambio[2:5]) / 3
    niosh = any(v >= 15 for v in cambio[:6])          # 500 a 6000 Hz
    prexor = any(v >= 15 and u > 25 for v, u in zip(cambio, ctrl))
    return osha, niosh, prexor


def panel(c, x0, y0, ancho, alto, titulo, datos, veredicto):
    c.t(x0, y0 - 14, titulo, 10, TINTA, 'start', 700)
    n = len(FREQS)
    paso = ancho / (n - 1)

    def X(i):
        return x0 + i * paso

    def Y(db):
        return y0 + db / 50 * alto

    c.rect(X(2) - 8, y0, X(4) - X(2) + 16, alto, '#f5ece6')     # 2, 3 y 4 kHz
    for db in range(0, 51, 10):
        c.l(x0 - 8, Y(db), x0 + ancho + 8, Y(db), GRILLA, 1)
        c.t(x0 - 14, Y(db) + 3, str(db), 8, TENUE, 'end')
    for i, f in enumerate(FREQS):
        c.t(X(i), y0 + alto + 14, f, 8.5, TENUE)
    c.l(x0 - 8, Y(25), x0 + ancho + 8, Y(25), FUERTE, 1, '4 3')
    c.t(x0 + ancho + 8, Y(25) - 3, '25', 7.5, TENUE, 'end')
    c.poli([(X(i), Y(v)) for i, v in enumerate(BASE)], TENUE, 2, '5 3')
    c.poli([(X(i), Y(v)) for i, v in enumerate(datos)], ROJO, 2.4)
    for i, v in enumerate(datos):
        c.circ(X(i), Y(v), 3.6, '#fff', ROJO)
    c.t(X(3), y0 + alto - 6, '2-3-4 kHz', 8, NARANJA)
    # cambios
    for i, (b, v) in enumerate(zip(BASE, datos)):
        if v - b >= 10:
            c.t(X(i) + 10, Y(v) + 12, f'+{v - b}', 8.5, ROJO, 'start', 700)
    # veredictos
    yy = y0 + alto + 38
    for k, (nombre, texto, si) in enumerate(veredicto):
        color = AVISO if si else VERDE
        c.t(x0 - 12, yy + k * 16, f'<tspan font-weight="700">{nombre}</tspan>', 8.5, TINTA, 'start')
        c.t(x0 + 52, yy + k * 16, f'<tspan fill="{color}" font-weight="700">{"sí" if si else "no"}</tspan>'
            f' · {texto}', 8.5, TINTA, 'start')


def cambio_umbral():
    c = Lienzo(700, 330)
    c.t(14, 18, 'Dos controles de un mismo trabajador, cada uno contra su base (0 dB HL; los dos oídos iguales)',
        10.5, TINTA, 'start', 700)
    for x0, titulo, datos in ((60, 'A · control con la muesca ya formada', CASO_A),
                              (390, 'B · control con la muesca incipiente', CASO_B)):
        o, n, p = criterios(BASE, datos)
        cambio = [b - a for a, b in zip(BASE, datos)]
        peor = max(range(6), key=lambda i: cambio[i])
        ver = [('OSHA', f'promedio 2-3-4 kHz: {o:.1f} dB (criterio ≥ 10)'.replace('.', ','), o >= 10),
               ('NIOSH', f'{FREQS[peor].strip()}: +{cambio[peor]} dB (criterio ≥ 15)', n),
               ('PREXOR*', f'+15 dB y umbral sobre 25 dB HL', p)]
        panel(c, x0, 66, 250, 150, titulo, datos, ver)
    c.t(14, 322, 'línea gris punteada: la base · línea roja: el control · * lectura de este libro del texto de PREXOR',
        8, TENUE, 'start')
    c.guardar('h22-cambio-umbral.svg')


# ---------------------------------------------------------------- flujo
def caja(c, x, y, w, h, texto, fill='#fff', stroke=TINTA, color=TINTA, peso=400):
    c.rect(x, y, w, h, fill, stroke, 1.4, 6)
    lineas = texto.split('|')
    y0 = y + h / 2 - (len(lineas) - 1) * 6.5 + 3
    for i, s in enumerate(lineas):
        c.t(x + w / 2, y0 + i * 13, s, 8.8, color, 'middle', peso)


def flecha(c, x1, y1, x2, y2, color=TINTA, etiqueta=None, ex=0, ey=-4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    c.out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.5"{d} '
                 f'marker-end="url(#pf)"/>')
    if etiqueta:
        c.t((x1 + x2) / 2 + ex, (y1 + y2) / 2 + ey, etiqueta, 8.5, color, 'middle', 700)


def flujo():
    c = Lienzo(700, 360)
    c.t(14, 18, 'Del control periódico al cambio confirmado', 10.5, TINTA, 'start', 700)
    caja(c, 20, 150, 110, 52, 'Audiometría|de base|(ingreso)', '#eef5f2', VERDE, TINTA, 700)
    caja(c, 165, 150, 110, 52, 'Control|periódico|contra la base')
    caja(c, 310, 150, 110, 52, '¿Cambio mayor|que el criterio|de la norma?')
    caja(c, 310, 36, 110, 44, 'Sin cambio:|sigue el calendario', '#fff', VERDE, VERDE)
    caja(c, 310, 250, 110, 56, 'Reexplicar,|recolocar fonos|y repetir al tiro')
    caja(c, 455, 250, 105, 56, '¿Persiste?|Confirmación en|condiciones de base')
    caja(c, 455, 150, 105, 52, 'Cambio|no persiste|(era variación)', '#fff', VERDE, VERDE)
    caja(c, 598, 250, 92, 56, 'Revisión por|médico o|audiólogo', '#fbeeee', AVISO, TINTA, 700)
    caja(c, 598, 130, 92, 92, 'Si es laboral:|avisar al|trabajador, revisar|el puesto, protección,|nueva base', '#fbeeee', AVISO)
    caja(c, 598, 40, 92, 62, 'Si no es laboral|o hay dudas:|derivar a ORL', '#fff', NARANJA, TINTA)
    defs = punta('pf', TINTA)
    flecha(c, 130, 176, 165, 176)
    flecha(c, 275, 176, 310, 176)
    flecha(c, 365, 150, 365, 80, VERDE, 'no', 12, 0)
    flecha(c, 365, 202, 365, 250, AVISO, 'sí', 12, 0)
    flecha(c, 420, 278, 455, 278)
    flecha(c, 507, 250, 507, 202, VERDE, 'no', 12, 0)
    flecha(c, 560, 278, 598, 278, AVISO, 'sí', 0, -6)
    flecha(c, 644, 250, 644, 222, AVISO)
    flecha(c, 644, 130, 644, 102, NARANJA)
    # el control vuelve al calendario
    c.t(14, 346, 'La norma de cada país fija el criterio, los plazos y quién revisa (tablas de este capítulo).', 8.5, TENUE, 'start')
    c.guardar('h22-flujo.svg', defs)


if __name__ == '__main__':
    intercambio()
    cambio_umbral()
    flujo()
