#!/usr/bin/env python3
"""Esquemas de la herramienta H4 (enmascaramiento). SVG propios, no IA:

    h04-cruce-craneo.svg     atenuación interaural según el transductor: fono supraaural,
                             vibrador óseo y fono de inserción
    h04-efecto-oclusion.svg  efecto de oclusión: conducto abierto, conducto tapado por la copa
                             de un fono y la tabla del capítulo en barras

Esquemas, no a escala. Las cifras son las del capítulo: atenuación interaural 40 a 80 dB con
supraaural, 55 dB o más con inserción y casi 0 dB con vibrador (BSA, 2018; Munro y Agnew, 1999);
efecto de oclusión con supraaural 15/15/10/0 dB (tabla de la cátedra, marcada `verificar`).
El corte frontal de la cabeza viene de hacer_h02_esquemas.py (de frente al paciente: OD a la
izquierda del dibujo)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h02_esquemas import (HUESO, HUESO_CLARO, OD, OI, TINTA_2, cabeza_frontal, camino,  # noqa: E402
                                onda, rect)
from hacer_h13 import COCLEAR, GRILLA, TENUE, TINTA, Lienzo  # noqa: E402

GRIS_FONO = '#6b6b72'
ESPUMA = '#e9b949'


def punta(id_, color, tam=7):
    """Punta de flecha de tamaño fijo `tam` (en unidades del dibujo)."""
    return (f'<marker id="{id_}" markerWidth="{tam}" markerHeight="{tam}" refX="{tam * 0.55:.1f}" '
            f'refY="{tam / 2:.1f}" markerUnits="userSpaceOnUse" orient="auto">'
            f'<path d="M0,0 L{tam},{tam / 2:.1f} L0,{tam} z" fill="{color}"/></marker>')


def flecha(c, d, color, grosor, id_, dash=None):
    extra = f' marker-end="url(#{id_})"' + (f' stroke-dasharray="{dash}"' if dash else '')
    c.out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{grosor}" '
                 f'stroke-linecap="butt"{extra}/>')


# ---------------------------------------------------------------- atenuación interaural

def copa(c, xp, y, sg, activa):
    """Copa de un fono supraaural sobre el pabellón en xp (sg = -1 OD, 1 OI)."""
    borde = OD if activa and sg < 0 else (OI if activa else GRIS_FONO)
    xa = xp + sg * 8
    rect(c, min(xa, xa + sg * 6), y - 30, 6, 60, '#4a4a50', 'none', 0, 3)          # almohadilla
    rect(c, min(xa + sg * 6, xa + sg * 20), y - 26, 14, 52, '#ffffff', borde, 1.6, 5)  # caja
    return xa


def cruce():
    c = Lienzo(840, 418)
    defs = (punta('g-od', OD, 11) + punta('f-od', OD, 7) + punta('f-oi', OI, 7) + punta('g-oi', OI, 11))
    c.t(14, 20, 'Cuánto llega a la otra cóclea según el transductor (corte frontal, de frente al paciente; '
        'esquema)', 10.5, TINTA, 'start', 700)
    cy, s = 214, 0.82
    paneles = ((145, 'A · Fono supraaural en el OD', 'supra'),
               (425, 'B · Vibrador en la mastoides derecha', 'vibra'),
               (705, 'C · Fono de inserción en el OD', 'inser'))
    for cx, titulo, modo in paneles:
        c.t(cx, 52, titulo, 9.5, TINTA, 'middle', 700)
        p = cabeza_frontal(c, cx, cy, s, cuello=100)
        od, oi = p['od'], p['oi']
        (xod, yod), (xoi, yoi) = od['coclea'], oi['coclea']
        if modo == 'supra':
            # vincha y las dos copas; solo la del OD lleva el tono
            camino(c, f'M{od["pabellon"] - 20:.1f},{cy - 30:.1f} C{od["pabellon"] - 26:.1f},{p["tope"] - 30:.1f} '
                      f'{oi["pabellon"] + 26:.1f},{p["tope"] - 30:.1f} {oi["pabellon"] + 20:.1f},{cy - 30:.1f}',
                   'none', GRIS_FONO, 3)
            xa = copa(c, od['pabellon'], cy - 4, -1, True)
            copa(c, oi['pabellon'], cy - 4, 1, False)
            flecha(c, f'M{xa + 2:.1f},{cy:.1f} L{xod - 12:.1f},{yod:.1f}', OD, 4.5, 'g-od')
            flecha(c, f'M{xa + 4:.1f},{cy + 24:.1f} Q{cx:.1f},{cy + 64:.1f} {xoi - 6:.1f},{yoi + 12:.1f}',
                   OI, 1.2, 'f-oi')
            ai, regla = 'atenuación interaural: 40 a 80 dB', 'para decidir se usa 40 dB'
            via = 'la caja hace vibrar el cráneo'
        elif modo == 'vibra':
            xv = cx - 92 * s
            camino(c, f'M{xv - 12:.1f},{cy + 20:.1f} C{xv - 34:.1f},{cy - 20:.1f} {xv - 30:.1f},{p["tope"] + 6:.1f} '
                      f'{cx:.1f},{p["tope"] - 10:.1f} S{cx + 106 * s:.1f},{cy - 80 * s:.1f} '
                      f'{cx + 93 * s:.1f},{cy - 40 * s:.1f}', 'none', GRIS_FONO, 2.4)
            rect(c, cx + 91 * s, cy - 48 * s, 6, 14, GRIS_FONO, 'none', 0, 2)
            rect(c, xv - 14, cy + 16, 14, 22, '#4a4a50', 'none', 0, 3)
            flecha(c, f'M{xv + 2:.1f},{cy + 22:.1f} Q{xod - 12:.1f},{cy + 20:.1f} {xod - 4:.1f},{yod + 11:.1f}',
                   OD, 3, 'f-od')
            flecha(c, f'M{xv + 2:.1f},{cy + 30:.1f} Q{cx:.1f},{cy + 64:.1f} {xoi - 6:.1f},{yoi + 12:.1f}',
                   OI, 3, 'f-oi')
            ai, regla = 'atenuación interaural: casi 0 dB', 'para decidir se usa 0 dB'
            via = 'vibra todo el cráneo'
            c.t(xv - 16, cy + 56, 'vibrador', 8, TINTA_2, 'end', 600)
            c.l(xv - 14, cy + 48, xv - 8, cy + 39, TENUE, 0.8)
        else:
            xe = od['entrada']
            rect(c, xe - 2, cy - 4.5, 14, 9, ESPUMA, '#b8892a', 0.8, 3)          # espuma en el conducto
            camino(c, f'M{xe - 2:.1f},{cy:.1f} C{xe - 16:.1f},{cy + 4:.1f} {xe - 28:.1f},{cy + 20:.1f} '
                      f'{xe - 30:.1f},{cy + 44:.1f}', 'none', GRIS_FONO, 2.2)     # tubo
            rect(c, xe - 40, cy + 44, 20, 24, '#ffffff', OD, 1.6, 4)              # transductor
            flecha(c, f'M{xe + 13:.1f},{cy:.1f} L{xod - 12:.1f},{yod:.1f}', OD, 4.5, 'g-od')
            flecha(c, f'M{xe + 16:.1f},{cy + 8:.1f} Q{cx:.1f},{cy + 64:.1f} {xoi - 6:.1f},{yoi + 12:.1f}',
                   OI, 0.9, 'f-oi', '3 2')
            ai, regla = 'atenuación interaural: 55 dB o más', 'para decidir se usa 55 dB'
            via = 'la espuma casi no hace vibrar el hueso'
            c.t(xe - 28, cy - 22, 'espuma', 8, '#8a6a1f', 'end', 600)
            c.l(xe - 26, cy - 18, xe + 2, cy - 5, TENUE, 0.8)
        for q in (od, oi):
            c.t(q['pabellon'], cy + 70, 'OD' if q is od else 'OI', 9.5, q['color'], 'middle', 700)
        c.t(cx, p['base'] + 22, via, 8, TINTA_2, 'middle', 600)
        c.t(cx, p['base'] + 42, ai, 8.8, TINTA, 'middle', 700)
        c.t(cx, p['base'] + 56, regla, 8.2, TENUE, 'middle', 600)
    c.l(14, 396, 826, 396, GRILLA, 1)
    c.t(14, 411, 'Flecha roja: lo que llega a la cóclea del OD. Flecha azul: lo que cruza a la del OI. '
        'El grosor indica cuánto llega.', 7.8, TENUE, 'start')
    c.guardar('h04-cruce-craneo.svg', defs)


# ---------------------------------------------------------------- efecto de oclusión

def conducto(c, x0, y0, tapado):
    """Conducto en corte, de afuera (izquierda) al tímpano (derecha). Devuelve el eje del conducto."""
    yc = y0 + 92
    x_ent, x_tim = x0 + 70, x0 + 214
    # hueso alrededor del conducto (parte del cráneo que vibra)
    rect(c, x_ent, y0 + 20, 196, 150, HUESO_CLARO, HUESO, 1.2, 10)
    # piel de afuera: el borde del bloque, con la concha
    c.l(x_ent, y0 + 20, x_ent, y0 + 170, TINTA_2, 1.4)
    # luz del conducto, tímpano y oído medio
    rect(c, x_ent - 1, yc - 17, x_tim - x_ent + 1, 34, '#ffffff', 'none', 0)
    c.l(x_ent, yc - 17, x_tim, yc - 17, TINTA_2, 1.1)
    c.l(x_ent, yc + 17, x_tim, yc + 17, TINTA_2, 1.1)
    rect(c, x_tim, yc - 32, 34, 60, '#ffffff', 'none', 0, 6)
    c.l(x_tim - 4, yc - 22, x_tim + 4, yc + 22, TINTA, 2)
    c.poli([(x_tim + 1, yc), (x_tim + 12, yc - 14), (x_tim + 24, yc - 12), (x_tim + 28, yc - 2)], TENUE, 2)
    # vibrador en la mastoides
    rect(c, x_ent - 20, y0 + 132, 20, 30, '#4a4a50', 'none', 0, 4)
    for k in range(3):
        r = 9 + 7 * k
        camino(c, f'M{x_ent + 4:.1f},{y0 + 146 - r:.1f} A{r},{r} 0 0 1 {x_ent + 4:.1f},{y0 + 146 + r:.1f}',
               'none', COCLEAR, 1, ' stroke-opacity="0.6"')
    # el hueso irradia energía grave hacia la luz del conducto
    for x in (x_ent + 40, x_ent + 80, x_ent + 120):
        onda(c, x, yc - 27, x, yc - 11, COCLEAR, 1.2, 'p-c', 1.6, 2)
        onda(c, x, yc + 27, x, yc + 11, COCLEAR, 1.2, 'p-c', 1.6, 2)
    c.t(x_tim + 4, yc - 40, 'tímpano', 8, TINTA_2, 'middle', 600)
    c.t(x_ent + 98, y0 + 14, 'hueso del cráneo (vibra)', 8, TENUE, 'middle', 600)
    c.t(x_ent - 2, y0 + 180, 'vibrador', 8, TINTA_2, 'end', 600)
    return x_ent, x_tim, yc


def oclusion():
    c = Lienzo(860, 292)
    defs = punta('p-c', COCLEAR, 6) + punta('p-cg', COCLEAR, 12)
    c.t(14, 20, 'El efecto de oclusión (conducto en corte, de afuera hacia el tímpano; esquema)',
        10.5, TINTA, 'start', 700)
    # A: abierto
    c.t(150, 52, 'A · Conducto abierto', 9.5, TINTA, 'middle', 700)
    x_ent, x_tim, yc = conducto(c, 14, 64, False)
    flecha(c, f'M{x_tim - 30:.1f},{yc:.1f} L{x_ent - 30:.1f},{yc:.1f}', COCLEAR, 5, 'p-cg')
    c.t(x_ent - 6, yc - 30, 'los graves', 8.2, COCLEAR, 'end', 700)
    c.t(x_ent - 6, yc - 20, 'escapan', 8.2, COCLEAR, 'end', 700)
    # B: tapado por la copa del fono
    c.t(440, 52, 'B · Conducto tapado por un fono', 9.5, TINTA, 'middle', 700)
    x_ent, x_tim, yc = conducto(c, 300, 64, True)
    rect(c, x_ent - 8, yc - 52, 8, 92, '#4a4a50', 'none', 0, 3)          # almohadilla
    rect(c, x_ent - 26, yc - 46, 18, 80, '#ffffff', GRIS_FONO, 1.6, 6)    # copa
    c.t(x_ent - 30, yc - 60, 'copa', 8, TINTA_2, 'start', 600)
    flecha(c, f'M{x_tim - 60:.1f},{yc - 6:.1f} L{x_ent + 18:.1f},{yc - 6:.1f} Q{x_ent + 6:.1f},{yc:.1f} '
              f'{x_ent + 18:.1f},{yc + 6:.1f} L{x_tim - 24:.1f},{yc + 6:.1f}', COCLEAR, 3, 'p-cg')
    for k in range(3):
        r = 8 + 6 * k
        camino(c, f'M{x_tim - 6:.1f},{yc - r:.1f} A{r},{r} 0 0 0 {x_tim - 6:.1f},{yc + r:.1f}',
               'none', COCLEAR, 2.2 - 0.5 * k)
    c.t(x_tim - 10, yc + 106, 'sube la presión', 8.2, COCLEAR, 'middle', 700)
    c.t(x_tim - 10, yc + 116, 'frente al tímpano', 8.2, COCLEAR, 'middle', 700)
    c.l(x_tim - 10, yc + 94, x_tim - 12, yc + 22, TENUE, 0.8)
    # C: la tabla del capítulo en barras
    x0, y0, w, h = 642, 92, 190, 150
    c.t(x0 + w / 2 - 6, 52, 'C · Cuánto mejora la ósea', 9.5, TINTA, 'middle', 700)
    c.t(x0 + w / 2 - 6, 66, 'al tapar con fono supraaural', 8.2, TENUE, 'middle', 600)
    top = 20
    Y = lambda v: y0 + h - v / top * h  # noqa: E731
    for v in (0, 5, 10, 15, 20):
        c.l(x0, Y(v), x0 + w, Y(v), GRILLA, 1)
        c.t(x0 - 6, Y(v) + 3.5, str(v), 7.6, TENUE, 'end')
    c.t(x0 - 28, y0 + h / 2, 'dB', 8, TENUE, 'middle', 600)
    datos = (('250', 15), ('500', 15), ('1.000', 10), ('2.000 y más', 0))
    paso = w / len(datos)
    for i, (f, v) in enumerate(datos):
        xb = x0 + paso * i + paso * 0.2
        bw = paso * 0.6
        if v:
            rect(c, xb, Y(v), bw, Y(0) - Y(v), COCLEAR, 'none', 0, 2)
        else:
            c.l(xb, Y(0), xb + bw, Y(0), COCLEAR, 2.4)
        c.t(xb + bw / 2, Y(v) - 6, f'{v} dB', 8.2, TINTA, 'middle', 700)
        c.t(xb + bw / 2, Y(0) + 15, f, 8, TINTA_2, 'middle', 600)
    c.t(x0 + w / 2, Y(0) + 32, 'Hz', 8, TENUE, 'middle', 600)
    c.l(x0, Y(0), x0 + w, Y(0), TENUE, 1)
    c.guardar('h04-efecto-oclusion.svg', defs)


if __name__ == '__main__':
    cruce()
    oclusion()
