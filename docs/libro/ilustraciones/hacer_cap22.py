#!/usr/bin/env python3
"""Dibuja los esquemas propios del capítulo 22 (Gira al acostarse):

    cap22-trazas-posterior.svg      Dix-Hallpike derecho e izquierdo, canal posterior (caso 22.1)
    cap22-trazas-geotropico.svg     giro supino, lateral geotrópico izquierdo (caso 22.2)
    cap22-trazas-apogeotropico.svg  giro supino, lateral apogeotrópico derecho (caso 22.3)
    cap22-trazas-central.svg        cabeza colgando, nistagmo posicional central (caso 22.4)
    cap22-decision.svg              del hallazgo a la maniobra (o a la derivación)

Son ESQUEMAS construidos a partir de los criterios de la guía y de la Sociedad
Bárány (latencia, forma crescendo-decrescendo, duración menor o mayor de 1
minuto, inversión al sentarse, fatiga, dirección por canal): no son datos de un
paciente ni salen del simulador, y el eje vertical no tiene unidades. Las
trazas se leen en el marco del PACIENTE: arriba = fase rápida hacia arriba o
hacia su derecha, según la fila. Imprime en la salida estándar la posición de
cada panel (en %) para poner los globos."""
import math
import pathlib

TINTA, TENUE, GRILLA = '#24101a', '#8a8a90', '#e7e5e0'
ROJO, AZUL, VERDE, NARANJA = '#c62f3a', '#2b5fa8', '#21796c', '#b8741a'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
PXS = 4.2          # píxeles por segundo, el mismo en todos los paneles de una figura
ALTO = 46          # media altura de una fila de traza


class Dibujo:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, []
        self.o.append(f'<rect width="{w}" height="{h}" fill="#fff"/>')
        self.o.append('<defs><marker id="pf" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">'
                      f'<path d="M0,0 L8,4 L0,8 z" fill="{TENUE}"/></marker></defs>')

    def t(self, x, y, s, size=10, color=TINTA, anchor='middle', peso=400):
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1.2, dash=None, flecha=False):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        m = ' marker-end="url(#pf)"' if flecha else ''
        self.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d}{m}/>')

    def r(self, x, y, w, h, fill='none', stroke=TENUE, sw=1, rx=6):
        self.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def guarda(self, nombre):
        (AQUI / nombre).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">\n'
                                   + '\n'.join(self.o) + '\n</svg>\n')


def campana(t, ini, dur, amp, forma=1.5):
    """Crescendo-decrescendo: media onda de seno elevada a `forma`, de ini a ini+dur."""
    if t < ini or t > ini + dur:
        return 0.0
    return amp * max(0.0, math.sin(math.pi * (t - ini) / dur)) ** forma


def meseta(t, ini, dur, amp, cae=0.0):
    """Sin latencia: sube en un instante y se sostiene (baja `cae` de su valor al final de `dur`)."""
    if t < ini or t > ini + dur:
        return 0.0
    k = min(1.0, (t - ini) / 2.5)
    k = k * k * (3 - 2 * k)
    return amp * k * (1 - cae * (t - ini) / dur)


def traza(d, x0, yc, seg, f, color, sw=2.2):
    """Una traza en el panel que parte de x0, con la línea de cero en yc."""
    n = int(seg * 2)
    pts = [(x0 + i / 2 * PXS, yc - ALTO * f(i / 2)) for i in range(n + 1)]
    # sin puntos repetidos en los tramos planos (WeasyPrint se confunde con rectas largas de puntos iguales)
    ys = [round(p[1], 1) for p in pts]
    pts = [p for i, p in enumerate(pts) if i in (0, len(pts) - 1) or ys[i] != ys[i - 1] or ys[i] != ys[i + 1]]
    d.o.append('<path fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" d="M%s"/>'
               % (color, sw, ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)))


def panel(d, x0, y0, seg, titulo, filas, marca_t=None, sigue=False, notas=()):
    """Un panel de `seg` segundos con una fila por traza: (rótulo, función, color, signo_arriba, signo_abajo).
    Devuelve (x, y, ancho, alto) en píxeles."""
    ancho = seg * PXS
    alto = 22 + len(filas) * (2 * ALTO + 12) + 22
    d.r(x0 - 8, y0, ancho + 16, alto, '#fcfbf9', GRILLA)
    d.t(x0 + ancho / 2, y0 + 15, titulo, 10.5, TINTA, 'middle', 700)
    for i, (rot, f, color, up, down) in enumerate(filas):
        yc = y0 + 22 + ALTO + i * (2 * ALTO + 12)
        d.l(x0, yc, x0 + ancho, yc, GRILLA, 1)
        d.l(x0, yc - ALTO, x0, yc + ALTO, TENUE, 1)
        d.t(x0 + 4, yc - ALTO + 9, up, 8, TENUE, 'start')
        d.t(x0 + 4, yc + ALTO - 2, down, 8, TENUE, 'start')
        traza(d, x0, yc, seg, f, color)
        d.t(x0 + ancho - 2, yc - ALTO + 9, rot, 8.5, color, 'end', 700)
    ye = y0 + alto - 22
    d.l(x0, ye, x0 + ancho, ye, TENUE, 1)
    paso = 10 if seg > 35 else 10
    for s in range(0, int(seg) + 1, paso):
        d.l(x0 + s * PXS, ye, x0 + s * PXS, ye + 4, TENUE, 1)
        d.t(x0 + s * PXS, ye + 14, f'{s} s', 8, TENUE)
    if sigue:
        d.t(x0 + ancho - 4, y0 + alto - 26, 'sigue ▶', 9, ROJO, 'end', 700)
    return x0, y0, ancho, alto


def pct(w, h, x, y):
    return f'{100 * x / w:.0f},{100 * y / h:.0f}'


def trazas_posterior():
    W = 760
    d = Dibujo(W, 330)
    d.t(14, 20, 'Caso 22.1 · Dix-Hallpike, vistos en los ojos del paciente', 12.5, TINTA, 'start', 700)
    d.t(14, 35, 'Fase rápida: arriba = hacia arriba; torsión arriba = polo superior del ojo hacia el oído derecho. Mismo tiempo en los tres paneles.', 8.5, TENUE, 'start')
    vert = lambda fn: ('vertical', fn, ROJO, 'arriba', 'abajo')
    tors = lambda fn: ('torsión', fn, VERDE, 'hacia OD', 'hacia OI')
    sube_v = lambda t: campana(t, 6, 26, 1.0)
    sube_t = lambda t: campana(t, 6, 26, 0.75)
    inv_v = lambda t: -campana(t, 3, 10, 0.45)
    inv_t = lambda t: -campana(t, 3, 10, 0.35)
    cero = lambda t: 0.0
    y0 = 52
    p1 = panel(d, 30, y0, 60, 'Sentada → cabeza colgando, derecha (E-CCD)', [vert(sube_v), tors(sube_t)])
    p2 = panel(d, 30 + 60 * PXS + 40, y0, 30, 'Colgando → sentada (CCD-E)', [vert(inv_v), tors(inv_t)])
    p3 = panel(d, 30 + 90 * PXS + 80, y0, 40, 'Cabeza colgando, izquierda', [vert(cero), tors(cero)])
    d.guarda('cap22-trazas-posterior.svg')
    return W, 330, p1, p2, p3


def roll(nombre, titulo, sub, izq, der, tipo, sigue):
    """Giro supino: dos paneles de 30 s, hacia la derecha y hacia la izquierda; la traza es horizontal."""
    W, H = 760, 232
    d = Dibujo(W, H)
    d.t(14, 20, titulo, 12.5, TINTA, 'start', 700)
    d.t(14, 35, sub, 8.5, TENUE, 'start')
    fila = lambda fn: ('horizontal', fn, AZUL, 'hacia la derecha', 'hacia la izquierda')
    global PXS
    PXS = 8.0
    seg = 30
    p1 = panel(d, 40, 52, seg, 'Cabeza girada 90° a la derecha (OD abajo)', [fila(der)], sigue=sigue)
    p2 = panel(d, 40 + seg * PXS + 90, 52, seg, 'Cabeza girada 90° a la izquierda (OI abajo)', [fila(izq)], sigue=sigue)
    d.t(40 + seg * PXS / 2, H - 8, tipo[0], 10, AZUL, 'middle', 700)
    d.t(40 + seg * PXS + 90 + seg * PXS / 2, H - 8, tipo[1], 10, AZUL, 'middle', 700)
    d.guarda(nombre)
    PXS = 4.2
    return W, H, p1, p2


def decision():
    W, H = 760, 470
    d = Dibujo(W, H)
    d.t(14, 20, 'Del hallazgo a la maniobra (o a la derivación)', 12.5, TINTA, 'start', 700)

    def caja(x, y, w, h, lineas, color=TINTA, fill='#fff', peso=400):
        d.r(x, y, w, h, fill, color, 1.3)
        n = len(lineas)
        for i, s in enumerate(lineas):
            d.t(x + w / 2, y + h / 2 + (i - (n - 1) / 2) * 12 + 4, s, 9.5, color, 'middle', 700 if i == 0 and peso > 400 else 400)

    def flecha(x1, y1, x2, y2, color=TENUE):
        d.l(x1, y1, x2, y2, color, 1.4, flecha=True)

    caja(250, 36, 260, 40, ['Vértigo breve al acostarse o girar', 'Se examinan los dos lados'], peso=700)
    flecha(380, 76, 380, 96)
    caja(250, 96, 260, 40, ['Dix-Hallpike', '(canales verticales)'], peso=700)
    # tres salidas del Dix-Hallpike
    flecha(300, 136, 130, 176)
    flecha(380, 136, 380, 176)
    flecha(460, 136, 640, 176)
    caja(20, 176, 220, 56, ['Arriba + torsional,', 'con latencia, &lt; 1 min,', 'se invierte al sentarse'], VERDE)
    caja(270, 176, 220, 56, ['Horizontal, o nada,', 'con síntomas de posición'], AZUL)
    caja(520, 176, 220, 56, ['Abajo puro, sin latencia,', 'no se cansa, o signos', 'neurológicos'], ROJO)
    # posterior
    flecha(130, 232, 130, 262, VERDE)
    caja(20, 262, 220, 50, ['Canalitiasis del posterior', 'del oído de abajo', 'Epley (Semont si cupular)'], VERDE, '#f1f8f6', 700)
    # lateral
    flecha(380, 232, 380, 250, AZUL)
    caja(270, 250, 220, 36, ['Giro supino (roll test)'], AZUL, '#fff', 700)
    flecha(330, 286, 240, 318, AZUL)
    flecha(430, 286, 450, 318, AZUL)
    caja(130, 318, 190, 64, ['Geotrópico', 'lado más fuerte = afectado', 'Lempert o Gufoni canalar'], AZUL, '#f2f6fb')
    caja(340, 318, 190, 64, ['Apogeotrópico', 'lado más débil = afectado', 'Gufoni cupular'], AZUL, '#f2f6fb')
    flecha(435, 382, 435, 404, AZUL)
    caja(340, 404, 190, 40, ['Repetir el giro supino:', 'si pasa a geotrópico, canalar'], AZUL)
    # central
    flecha(630, 232, 630, 262, ROJO)
    caja(550, 262, 190, 76, ['No es un VPPB típico', 'No se hacen maniobras', 'Examen neurológico', 'Derivar'], ROJO, '#fdf1f2', 700)
    d.guarda('cap22-decision.svg')
    return W, H


if __name__ == '__main__':
    W, H, p1, p2, p3 = trazas_posterior()
    print('posterior', W, H, [tuple(round(v) for v in p) for p in (p1, p2, p3)])
    geo_der = lambda t: campana(t, 4, 22, 0.36)
    geo_izq = lambda t: -campana(t, 4, 24, 0.8)
    r = roll('cap22-trazas-geotropico.svg', 'Caso 22.2 · Giro supino, lateral geotrópico',
             'Trazas en el marco del paciente. Geotrópico: el nistagmo bate hacia el oído de abajo, a los dos lados.',
             geo_izq, geo_der, ('Bate hacia el suelo, más débil', 'Bate hacia el suelo, más fuerte'), False)
    print('geotropico', [tuple(round(v) for v in p) for p in r[2:]])
    ap_der = lambda t: -meseta(t, 0, 30, 0.36, 0.25)
    ap_izq = lambda t: meseta(t, 0, 30, 0.8, 0.25)
    r = roll('cap22-trazas-apogeotropico.svg', 'Caso 22.3 · Giro supino, lateral apogeotrópico',
             'Trazas en el marco del paciente. Apogeotrópico: el nistagmo bate hacia el oído de arriba, a los dos lados.',
             ap_izq, ap_der, ('Bate hacia el techo, más débil', 'Bate hacia el techo, más fuerte'), True)
    print('apogeotropico', [tuple(round(v) for v in p) for p in r[2:]])
    # central
    W, H = 760, 215
    d = Dibujo(W, H)
    d.t(14, 20, 'Caso 22.4 · Cabeza colgando: lo que NO encaja en un canal', 12.5, TINTA, 'start', 700)
    d.t(14, 35, 'Fase rápida hacia abajo, vertical puro, sin latencia, sin torsión. Mismo tiempo en los tres paneles.', 8.5, TENUE, 'start')
    fila = lambda fn: ('vertical', fn, ROJO, 'arriba', 'abajo')
    cen = lambda t: -meseta(t, 0, 60, 0.65, 0.0)
    cen2 = lambda t: -meseta(t, 0, 60, 0.65, 0.0)
    sent = lambda t: -meseta(t, 0, 5, 0.25, 1.0)
    pa = panel(d, 30, 52, 60, 'Colgando (primera vez)', [fila(cen)], sigue=True)
    pb = panel(d, 30 + 60 * PXS + 40, 52, 30, 'Sentado otra vez', [fila(sent)])
    pc = panel(d, 30 + 90 * PXS + 80, 52, 40, 'Colgando, repetido', [fila(lambda t: -meseta(t, 0, 40, 0.65, 0.0))], sigue=True)
    d.guarda('cap22-trazas-central.svg')
    print('central', W, H, [tuple(round(v) for v in p) for p in (pa, pb, pc)])
    print('decision', decision())
