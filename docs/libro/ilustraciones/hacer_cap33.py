#!/usr/bin/env python3
"""Ilustraciones del capítulo 33 (el trabajador expuesto a ruido):

    cap33-cambio.svg   caso 1: control en cámara contra la base de la ficha, con el cambio y los tres criterios
    cap33-reposo.svg   caso 2: base, control al final del turno (valores inventados) y confirmación tras el reposo
    cap33-ttspts.svg   esquema: el desplazamiento temporal que vuelve a cero y el que deja un resto

Los umbrales del caso 1 y de la confirmación del caso 2 salen de los casos armados por el motor
(casos/generados/cap33_*.json); los del control al final del turno del caso 2 son inventados (LabSim no
simula el desplazamiento temporal); el tercer dibujo es un esquema sin cifras. SVG propios, no IA."""
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
from hacer_h22 import Lienzo, TINTA, TENUE, GRILLA, FUERTE, ROJO, AZUL, VERDE, NARANJA, punta  # noqa: E402

GEN = AQUI.parent / 'casos' / 'generados'
FREQS = ('500', '1 k', '2 k', '3 k', '4 k', '6 k', '8 k')
IDX = (2, 3, 4, 5, 6, 7, 8)   # posiciones de 500 a 8000 en el vector de 125 a 8000


def umbrales(nombre):
    d = json.load(open(GEN / f'{nombre}.json', encoding='utf-8'))['data']['Aerea']
    return [d[i][0] for i in IDX], [d[i][1] for i in IDX]


def criterios(base, ctrl):
    cambio = [b - a for a, b in zip(base, ctrl)]
    osha = sum(cambio[2:5]) / 3
    niosh = any(v >= 15 for v in cambio[:6])
    prexor = any(v >= 15 and u > 25 for v, u in zip(cambio, ctrl))
    return cambio, osha, niosh, prexor


def panel(c, x0, y0, ancho, alto, titulo, color, base, curvas, maxdb=100, cambio=None):
    """curvas: lista de (valores, color, dash, etiqueta de leyenda o None)."""
    c.t(x0, y0 - 14, titulo, 10, TINTA, 'start', 700)
    n = len(FREQS)
    paso = ancho / (n - 1)
    X = lambda i: x0 + i * paso            # noqa: E731
    Y = lambda db: y0 + db / maxdb * alto  # noqa: E731
    for db in range(0, maxdb + 1, 20):
        c.l(x0 - 8, Y(db), x0 + ancho + 8, Y(db), GRILLA, 1)
        c.t(x0 - 14, Y(db) + 3, str(db), 8, TENUE, 'end')
    c.l(x0 - 8, Y(25), x0 + ancho + 8, Y(25), FUERTE, 1, '4 3')
    for i, f in enumerate(FREQS):
        c.t(X(i), y0 + alto + 14, f, 8.5, TENUE)
    c.poli([(X(i), Y(v)) for i, v in enumerate(base)], TENUE, 2, '5 3')
    for vals, col, dash, _ in curvas:
        c.poli([(X(i), Y(v)) for i, v in enumerate(vals)], col, 2.4, dash)
        for i, v in enumerate(vals):
            c.circ(X(i), Y(v), 3.6, '#fff', col)
    if cambio:
        c.t(x0 - 14, y0 + alto + 32, 'cambio', 8, TENUE, 'end')
        for i, v in enumerate(cambio):
            c.t(X(i), y0 + alto + 32, f'+{v}' if v > 0 else str(v), 8.5, ROJO if v >= 15 else TENUE, 'middle', 700 if v >= 15 else 400)


def veredictos(c, x, y, od, oi):
    c.t(x, y, 'Criterio', 8.5, TENUE, 'start', 700)
    for k, nombre in enumerate(('OSHA: promedio 2-3-4 kHz ≥ 10 dB', 'NIOSH: ≥ 15 dB en una frecuencia (500 a 6 k)', 'PREXOR: ≥ 15 dB y umbral > 25 dB')):
        c.t(x, y + 16 + k * 15, nombre, 8.5, TINTA, 'start')
    for j, (lado, r) in enumerate((('OD', od), ('OI', oi))):
        _, osha, niosh, prexor = r
        xx = x + 250 + j * 120
        c.t(xx, y, lado, 8.5, TENUE, 'start', 700)
        celdas = ((osha >= 10, ('sí' if osha >= 10 else 'no') + f' · {osha:.1f} dB'.replace('.', ',')),
                  (niosh, 'sí' if niosh else 'no'), (prexor, 'sí' if prexor else 'no'))
        for k, (si, txt) in enumerate(celdas):
            c.t(xx, y + 16 + k * 15, f'<tspan fill="{ROJO if si else VERDE}" font-weight="700">{txt}</tspan>', 8.5, TINTA, 'start')


def cambio():
    od, oi = umbrales('cap33_control')
    base = [0] * 7
    r_od, r_oi = criterios(base, od), criterios(base, oi)
    c = Lienzo(700, 360)
    c.t(14, 18, 'Control en cámara, ocho años después, contra la base de la ficha (0 dB HL en los dos oídos)', 10.5, TINTA, 'start', 700)
    panel(c, 60, 56, 250, 150, 'Oído derecho', ROJO, base, [(od, ROJO, None, None)], cambio=r_od[0])
    panel(c, 390, 56, 250, 150, 'Oído izquierdo', AZUL, base, [(oi, AZUL, None, None)], cambio=r_oi[0])
    c.l(60, 332, 84, 332, TENUE, 2, '5 3')
    c.t(90, 335, 'base', 8.5, TENUE, 'start')
    c.l(130, 332, 154, 332, TINTA, 2.4)
    c.t(160, 335, 'control (umbral, dB HL)', 8.5, TINTA, 'start')
    veredictos(c, 60, 270, r_od, r_oi)
    c.guardar('cap33-cambio.svg')
    return r_od, r_oi


OD_TURNO = [0, 0, 5, 15, 30, 25, 10]
OI_TURNO = [0, 0, 5, 15, 25, 20, 10]


def reposo():
    od, oi = umbrales('cap33_reposo')
    base = [0] * 7
    r_od, r_oi = criterios(base, OD_TURNO), criterios(base, OI_TURNO)
    c = Lienzo(700, 360)
    c.t(14, 18, 'El mismo trabajador: al final del turno y tras 14 horas de reposo', 10.5, TINTA, 'start', 700)
    panel(c, 60, 56, 250, 110, 'Oído derecho', ROJO, base,
          [(OD_TURNO, NARANJA, None, None), (od, VERDE, '2 3', None)], maxdb=60, cambio=r_od[0])
    panel(c, 390, 56, 250, 110, 'Oído izquierdo', AZUL, base,
          [(OI_TURNO, NARANJA, None, None), (oi, VERDE, '2 3', None)], maxdb=60, cambio=r_oi[0])
    c.l(60, 250, 84, 250, TENUE, 2, '5 3')
    c.t(90, 253, 'base (ficha)', 8.5, TENUE, 'start')
    c.l(190, 250, 214, 250, NARANJA, 2.4)
    c.t(220, 253, 'fin de turno, en terreno', 8.5, TINTA, 'start')
    c.l(380, 250, 404, 250, VERDE, 2.4, '2 3')
    c.t(410, 253, 'confirmación en cámara tras reposo', 8.5, TINTA, 'start')
    veredictos(c, 60, 280, r_od, r_oi)
    c.t(60, 346, 'Los criterios se aplican al control del final del turno; la confirmación, igual a la base, no cumple ninguno.', 8.5, TENUE, 'start')
    c.guardar('cap33-reposo.svg')


def ttspts():
    c = Lienzo(700, 300)
    c.t(14, 18, 'Esquema (sin cifras): lo que sube en el turno y lo que queda', 10.5, TINTA, 'start', 700)
    for x0, titulo, resto in ((50, 'Primeros meses: el oído vuelve a la base', 0), (390, 'Años después: queda un resto', 1)):
        y0, alto, ancho = 60, 160, 270
        c.t(x0, y0 - 14, titulo, 10, TINTA, 'start', 700)
        c.l(x0, y0, x0, y0 + alto, FUERTE, 1)
        c.l(x0, y0 + alto, x0 + ancho, y0 + alto, FUERTE, 1)
        c.t(x0 - 8, y0 + 8, 'peor', 8, TENUE, 'end')
        c.t(x0 - 8, y0 + alto, 'base', 8, TENUE, 'end')
        c.t(x0 + ancho / 2, y0 + alto + 26, 'días de trabajo', 8.5, TENUE)
        pts = []
        piso = 0
        dias = 5
        for d in range(dias):
            xa = x0 + 20 + d * (ancho - 30) / dias
            w = (ancho - 30) / dias
            piso_d = (resto * (d + 1) * 5) if resto else 0
            base_y = y0 + alto - piso_d
            pico = base_y - 60
            pts += [(xa, base_y), (xa + w * 0.35, pico), (xa + w * 0.45, pico + 2), (xa + w * 0.95, base_y - (6 if resto else 0))]
        c.poli(pts, NARANJA, 2.2)
        if resto:
            ult = pts[-1]
            c.l(x0, ult[1], x0 + ancho, ult[1], ROJO, 1, '4 3')
            c.l(x0 + ancho - 30, y0 + alto - 2, x0 + ancho - 30, ult[1] + 3, ROJO, 1.4, None, ' marker-end="url(#fl)"')
            c.t(x0 + ancho - 38, y0 + alto - 7, 'resto que no vuelve (permanente)', 8.5, ROJO, 'end', 700)
        c.t(x0 + 40, y0 + 12, 'sube en el turno', 8.5, NARANJA, 'start')
        c.t(x0 + 40, y0 + 24, 'y baja en el reposo', 8.5, NARANJA, 'start')
    c.t(14, 285, 'Cada onda es un turno (sube) y la noche siguiente (baja). Esquema cualitativo, no son datos de ninguna persona.', 8.5, TENUE, 'start')
    c.guardar('cap33-ttspts.svg', punta('fl', ROJO))


if __name__ == '__main__':
    cambio()
    reposo()
    ttspts()
