#!/usr/bin/env python3
"""Ilustraciones del capítulo 11 (asimetría que no cierra). SVG propios, no IA:

    cap11-arco-reflejo.svg      el arco del reflejo estapedial en un corte frontal del tronco, con una
                                lesión del VIII par derecho y los cuatro registros que fallan
    cap11-generadores-peat.svg  A: la vía de la cóclea al colículo, con el generador de cada onda;
                                B: un PEAT normal y uno con schwannoma en el CAI, alineados en tiempo

Esquemas, no a escala. El arco sigue el texto del capítulo (Jerger y cols., 1974): aferente por el
VIII par, relevo en el núcleo coclear y el complejo olivar de los dos lados, eferente por el núcleo y el
nervio facial. Los generadores son los de Møller y Jannetta (1983) que usa el capítulo.
Latencias del PEAT normal: medias del adulto de la tabla de H10 (Sanfins y cols., 2026), redondeadas.
El trazo con tumor es ilustrativo: la I queda en su lugar, el I-III pasa el límite de H10 (2,72 ms) y la
V llega cerca de 1 ms más tarde, como en el paciente del capítulo."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h13 import AVISO, FUERTE, GRILLA, RETRO, TENUE, TINTA, Lienzo, punta  # noqa: E402
import hacer_h13  # noqa: E402

hacer_h13.ESCALA = 1.38   # letra más grande: los dos dibujos van a todo el ancho de la página

OD, OI = '#c62f3a', '#2c5f9e'     # convención del libro: oído derecho rojo, izquierdo azul
TRONCO = '#f4f1ec'
HUESO = '#e3ddd2'
MUSCULO = '#e9cdb8'


def circulo(c, x, y, r, relleno='#fff', borde=TINTA, grosor=1.4, extra=''):
    c.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{relleno}" stroke="{borde}" '
                 f'stroke-width="{grosor}"{extra}/>')


def rect(c, x, y, w, h, relleno='none', borde=TINTA, grosor=1.4, r=0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    c.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
                 f'fill="{relleno}" stroke="{borde}" stroke-width="{grosor}"{d}/>')


def espiral(c, cx, cy, color, espejo=False):
    """Cóclea como una espiral de dos vueltas y media vista de frente."""
    pts = []
    for i in range(160):
        a = i / 159 * 5 * math.pi
        r = 22 * (1 - i / 175)
        x = r * math.cos(a)
        pts.append((cx + (-x if espejo else x), cy + r * math.sin(a)))
    c.poli(pts, color, 2.2)


def cruz(c, x, y, s=9):
    c.l(x - s, y - s, x + s, y + s, AVISO, 3.4, extra=' stroke-linecap="round"')
    c.l(x - s, y + s, x + s, y - s, AVISO, 3.4, extra=' stroke-linecap="round"')


# ---------------------------------------------------------------- 11.1 arco del reflejo
def arco_reflejo():
    c = Lienzo(900, 432)
    c.t(14, 20, 'Arco del reflejo estapedial (corte frontal del tronco)', 10.5, TINTA, 'start', 700)
    c.t(70, 50, 'lado derecho (OD)', 8.5, OD, 'start', 700)
    c.t(590, 50, 'lado izquierdo (OI)', 8.5, OI, 'end', 700)

    # tronco y línea media
    tx0, tx1, ty0, ty1, mx = 215, 445, 66, 336, 330
    rect(c, tx0, ty0, tx1 - tx0, ty1 - ty0, TRONCO, FUERTE, 1.4, 46)
    c.l(mx, ty0 + 6, mx, ty1 - 6, FUERTE, 1, '3 4')
    c.t(mx, ty0 + 18, 'tronco', 8, TENUE, 'middle', 600)
    c.t(mx, ty1 - 8, 'línea media', 7.2, TENUE, 'middle')

    lados = {
        'D': dict(col=OD, s=-1, coc=(66, 142), ncv=(252, 142), cos=(298, 214), nf=(272, 284), est=(92, 272)),
        'I': dict(col=OI, s=1, coc=(594, 142), ncv=(408, 142), cos=(362, 214), nf=(388, 284), est=(568, 272)),
    }
    otro = {'D': 'I', 'I': 'D'}

    # vías de relevo (debajo de los núcleos): ipsi continua, contra discontinua
    for k, L in lados.items():
        O = lados[otro[k]]
        col, s = L['col'], L['s']
        # ipsilateral: núcleo coclear -> olivar del mismo lado -> núcleo del facial del mismo lado
        c.poli([L['ncv'], L['cos']], col, 2.2)
        c.poli([(L['cos'][0] + 4 * s, L['cos'][1]), (L['nf'][0] + 4 * s, L['nf'][1])], col, 2.2)
        # contralateral: núcleo coclear -> cruza -> olivar del otro lado -> núcleo del facial del otro lado
        c.poli([L['ncv'], O['cos']], col, 2.2, '6 4')
        c.poli([(O['cos'][0] + 4 * s, O['cos'][1]), (O['nf'][0] + 4 * s, O['nf'][1])], col, 2.2, '6 4')

    for k, L in lados.items():
        col, s = L['col'], L['s']
        cx, cy = L['coc']
        espiral(c, cx, cy, col, espejo=(k == 'I'))
        c.t(cx, cy - 32, 'cóclea', 8.2, col, 'middle', 700)
        # VIII par: cóclea -> núcleo coclear ventral (aferente, color del oído)
        c.poli([(cx - 26 * s, cy), L['ncv']], col, 3.2)
        # VII par: núcleo del facial -> sale del tronco -> músculo del estribo (eferente, tinta)
        ex, ey = L['est']
        borde = tx0 if s < 0 else tx1
        c.poli([L['nf'], (borde + 8 * s, 304), (ex - 26 * s, ey + 26), (ex - 8 * s, ey + 10)], TINTA, 2.2)
        # músculo del estribo
        c.out.append(f'<ellipse cx="{ex}" cy="{ey}" rx="22" ry="10" fill="{MUSCULO}" stroke="{TINTA}" '
                     f'stroke-width="1.2" transform="rotate({-20 * s} {ex} {ey})"/>')
        for i, s2 in enumerate(('músculo', 'del estribo')):
            c.t(ex, ey - 26 + 11 * i, s2, 8.2, TINTA, 'middle', 600)
        # núcleos
        for p in ('ncv', 'cos', 'nf'):
            circulo(c, *L[p], 8, '#fff', TINTA, 1.4)

    # rótulos de los núcleos (en la columna central del tronco)
    nd, ni = lados['D'], lados['I']
    c.t(mx, 112, 'núcleo coclear ventral', 8.2, TINTA, 'middle', 700)
    c.l(mx - 58, 116, nd['ncv'][0] + 9, nd['ncv'][1] - 6, TENUE, 0.8)
    c.l(mx + 58, 116, ni['ncv'][0] - 9, ni['ncv'][1] - 6, TENUE, 0.8)
    c.t(mx, 238, 'complejo', 8, TINTA, 'middle', 700)
    c.t(mx, 248, 'olivar sup.', 8, TINTA, 'middle', 700)
    c.t(mx, 300, 'núcleo', 8, TINTA, 'middle', 700)
    c.t(mx, 310, 'del facial', 8, TINTA, 'middle', 700)
    c.l(mx - 28, 296, nd['nf'][0] + 10, nd['nf'][1] + 3, TENUE, 0.8)
    c.l(mx + 28, 296, ni['nf'][0] - 10, ni['nf'][1] + 3, TENUE, 0.8)

    # rótulos de los nervios
    c.t(118, 134, 'VIII par', 8.2, OD, 'middle', 700)
    c.t(500, 134, 'VIII par', 8.2, OI, 'middle', 700)
    c.t(150, 326, 'nervio facial (VII)', 8.2, TINTA, 'middle', 600)
    c.t(510, 326, 'nervio facial (VII)', 8.2, TINTA, 'middle', 600)

    # lesión
    cruz(c, 178, 142)
    c.t(178, 170, 'lesión del VIII par', 8.2, AVISO, 'middle', 700)
    c.t(178, 181, 'derecho', 8.2, AVISO, 'middle', 700)

    # leyenda
    ly = 372
    c.l(14, ly - 18, 640, ly - 18, GRILLA, 1)
    c.l(20, ly, 52, ly, TINTA, 2.2)
    c.t(58, ly + 4, 'vía ipsilateral', 8.2, TINTA, 'start')
    c.l(170, ly, 202, ly, TINTA, 2.2, '6 4')
    c.t(208, ly + 4, 'vía contralateral (cruza la línea media)', 8.2, TINTA, 'start')
    c.l(20, ly + 22, 52, ly + 22, OD, 3)
    c.t(58, ly + 26, 'estímulo en el OD', 8.2, OD, 'start', 600)
    c.l(170, ly + 22, 202, ly + 22, OI, 3)
    c.t(208, ly + 26, 'estímulo en el OI', 8.2, OI, 'start', 600)
    c.l(350, ly + 22, 382, ly + 22, TINTA, 2.2)
    c.t(388, ly + 26, 'eferente: núcleo y nervio facial', 8.2, TINTA, 'start')

    # recuadro: los cuatro registros
    bx, by, bw, bh = 664, 70, 222, 266
    rect(c, bx, by, bw, bh, '#fbfaf8', FUERTE, 1.2, 8)
    c.t(bx + 12, by + 22, 'Con la lesión del VIII par OD', 9, TINTA, 'start', 700)
    filas = [('ipsi D', 'tono OD · sonda OD', False),
             ('ipsi I', 'tono OI · sonda OI', True),
             ('contra D→I', 'tono OD · sonda OI', False),
             ('contra I→D', 'tono OI · sonda OD', True)]
    for i, (nombre, detalle, ok) in enumerate(filas):
        y = by + 54 + 40 * i
        c.l(bx + 10, y - 16, bx + bw - 10, y - 16, GRILLA, 1)
        tono = OD if 'tono OD' in detalle else OI
        c.t(bx + 12, y, nombre, 8.6, TINTA, 'start', 700)
        c.t(bx + 12, y + 13, detalle, 7.6, tono, 'start', 600)
        c.t(bx + bw - 12, y + 6, 'presente' if ok else 'ausente', 8.6, RETRO if ok else AVISO, 'end', 700)
    yb = by + 54 + 40 * 4 - 16
    c.l(bx + 10, yb, bx + bw - 10, yb, GRILLA, 1)
    for i, s in enumerate(('Patrón diagonal: falla todo', 'lo que se estimula por el OD,',
                           'se registre donde se registre.')):
        c.t(bx + 12, yb + 18 + 12 * i, s, 8, AVISO if i == 0 else TINTA, 'start', 700 if i == 0 else 400)

    c.t(14, 424, 'A la izquierda queda el lado derecho del paciente.', 7.8, TENUE, 'start')
    c.guardar('cap11-arco-reflejo.svg')


# ---------------------------------------------------------------- 11.2 generadores del PEAT
NORMAL = {'I': (1.5, 0.30), 'II': (2.6, 0.16), 'III': (3.8, 0.30), 'IV': (4.9, 0.30), 'V': (5.7, 0.52)}
TUMOR = {'I': (1.5, 0.30), 'II': (2.95, 0.08), 'III': (4.6, 0.24), 'IV': (5.75, 0.22), 'V': (6.6, 0.42)}


def onda(t, picos):
    """Trazo esquemático: un pico gaussiano por onda y el valle que sigue a la V."""
    v = 0.0
    for nombre, (lat, amp) in picos.items():
        ancho = 0.28 if nombre == 'V' else 0.2
        v += amp * math.exp(-((t - lat) / ancho) ** 2)
    lat_v, amp_v = picos['V']
    v -= 0.55 * amp_v * math.exp(-((t - lat_v - 0.9) / 0.45) ** 2)
    v += 0.03 * math.sin(7.3 * t) * math.exp(-t / 6)
    return v


def generadores_peat():
    c = Lienzo(760, 540)
    defs = punta('p-v', AVISO)

    # ---- Panel A: la vía en línea
    c.t(14, 20, 'A · Dónde nace cada onda (de la cóclea al colículo)', 10.5, TINTA, 'start', 700)
    yv = 118
    x_coc, x_poro, x_tronco, x_fin = 64, 286, 404, 736
    # hueso temporal con el CAI
    rect(c, 102, yv - 46, x_poro - 102, 92, HUESO, 'none', 0, 6)
    c.t((102 + x_poro) / 2, yv + 62, 'hueso temporal', 8, TENUE, 'middle', 600)
    rect(c, 102, yv - 16, x_poro - 102, 32, '#fff', TENUE, 1, 3)
    c.t((102 + x_poro) / 2, yv - 22, 'conducto auditivo interno (CAI)', 8.2, TINTA, 'middle', 700)
    # ángulo pontocerebeloso
    c.t((x_poro + x_tronco) / 2, yv - 22, 'ángulo', 8, TENUE, 'middle', 600)
    # tronco
    rect(c, x_tronco, yv - 46, x_fin - x_tronco, 92, TRONCO, FUERTE, 1.2, 10)
    c.t((x_tronco + x_fin) / 2, yv + 62, 'tronco del encéfalo', 8, TENUE, 'middle', 600)
    # schwannoma (contorno) dentro del CAI, pegado al nervio
    c.out.append(f'<ellipse cx="240" cy="{yv + 8}" rx="34" ry="9" fill="{AVISO}" fill-opacity="0.12" '
                 f'stroke="{AVISO}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    c.t(240, yv + 34, 'aquí crece el schwannoma', 7.6, AVISO, 'middle', 700)
    c.l(240, yv + 25, 240, yv + 18, AVISO, 0.8)

    # cóclea y vía
    espiral(c, x_coc, yv, TINTA)
    c.t(x_coc, yv + 40, 'cóclea', 8.2, TINTA, 'middle', 700)
    x_nc, x_cos, x_ci = 440, 556, 700
    c.poli([(x_coc + 24, yv), (x_nc, yv)], TINTA, 3.2)          # nervio auditivo
    c.poli([(x_nc, yv), (x_cos, yv)], TINTA, 2.4)               # al complejo olivar
    c.poli([(x_cos, yv), (x_ci, yv)], TINTA, 2.4)               # lemnisco lateral
    c.t((x_cos + x_ci) / 2, yv + 16, 'lemnisco lateral', 7.8, TENUE, 'middle', 600)
    for x, s in ((x_nc, 'núcleo coclear'), (x_cos, 'complejo olivar'), (x_ci, 'colículo inferior')):
        circulo(c, x, yv, 8, '#fff', TINTA, 1.4)
    c.t(x_nc, yv + 24, 'núcleo', 7.8, TINTA, 'middle', 700)
    c.t(x_nc, yv + 34, 'coclear', 7.8, TINTA, 'middle', 700)
    c.t(x_cos, yv - 18, 'complejo olivar sup.', 7.8, TINTA, 'middle', 700)
    c.t(x_ci, yv + 24, 'colículo', 7.8, TINTA, 'middle', 700)
    c.t(x_ci, yv + 34, 'inferior', 7.8, TINTA, 'middle', 700)

    # generadores: I nervio distal, II nervio proximal, III núcleo coclear, IV olivar, V lemnisco al colículo
    gen = [('I', 118), ('II', 392), ('III', x_nc), ('IV', x_cos), ('V', 682)]
    yg = 54
    for nombre, x in gen:
        color = TINTA
        circulo(c, x, yg, 11, '#fff', color, 1.4)
        c.t(x, yg + 4, nombre, 8.2, color, 'middle', 700)
        c.l(x, yg + 11, x, yv - 6, TENUE, 0.9, '2 3')
    c.t(118, yv + 30, 'nervio', 7.6, TENUE, 'middle', 600)
    c.t(118, yv + 40, 'distal', 7.6, TENUE, 'middle', 600)
    c.t(366, yv + 24, 'nervio', 7.6, TENUE, 'middle', 600)
    c.t(366, yv + 34, 'proximal', 7.6, TENUE, 'middle', 600)
    # tramo I-III
    yb = 32
    c.l(118, yb, x_nc, yb, AVISO, 1.4)
    c.l(118, yb - 4, 118, yb + 4, AVISO, 1.4)
    c.l(x_nc, yb - 4, x_nc, yb + 4, AVISO, 1.4)
    c.t(x_nc + 10, yb + 4, 'I-III: el nervio en el CAI y el ángulo', 8.2, AVISO, 'start', 700)

    # ---- Panel B: los dos trazos
    yB = 214
    c.l(14, yB - 20, 746, yB - 20, GRILLA, 1)
    c.t(14, yB, 'B · El mismo click a 80 dB nHL: oído sano y oído con schwannoma en el CAI', 10.5, TINTA, 'start', 700)
    x0, x1, t1 = 150, 726, 10.0
    X = lambda t: x0 + t / t1 * (x1 - x0)
    esc = 70
    trazos = [('Normal', NORMAL, yB + 82, TINTA), ('Schwannoma', TUMOR, yB + 206, AVISO)]
    ytop, ybot = yB + 18, yB + 262
    for lat in (NORMAL['I'][0], NORMAL['III'][0], NORMAL['V'][0]):
        c.l(X(lat), ytop, X(lat), ybot, FUERTE, 0.9, '3 3')
    for etiqueta, picos, yc, color in trazos:
        pts = [(X(i / 400 * t1), yc - esc * onda(i / 400 * t1, picos)) for i in range(401)]
        c.poli(pts, color, 1.8)
        c.t(14, yc - 4, etiqueta, 9, color, 'start', 700)
        if etiqueta != 'Normal':
            c.t(14, yc + 8, 'en el CAI', 8, color, 'start', 600)
        for nombre in ('I', 'III', 'V'):
            lat, amp = picos[nombre]
            yp = yc - esc * onda(lat, picos)
            c.t(X(lat), yp - 8, nombre, 8.2, color, 'middle', 700)
        # interpicos debajo del trazo
        li, l3, l5 = picos['I'][0], picos['III'][0], picos['V'][0]
        yi = yc + 26
        largo = l3 - li > 2.72
        ci = AVISO if largo else TINTA
        c.l(X(li), yi, X(l3), yi, ci, 1.4)
        c.l(X(li), yi - 4, X(li), yi + 4, ci, 1.4)
        c.l(X(l3), yi - 4, X(l3), yi + 4, ci, 1.4)
        c.t((X(li) + X(l3)) / 2, yi + 13, f'I-III {l3 - li:.1f} ms'.replace('.', ','), 8.2, ci, 'middle', 700)
        c.l(X(l3), yi, X(l5), yi, TENUE, 1.2)
        c.l(X(l5), yi - 4, X(l5), yi + 4, TENUE, 1.2)
        c.t((X(l3) + X(l5)) / 2, yi + 13, f'III-V {l5 - l3:.1f}'.replace('.', ','), 8, TENUE, 'middle', 600)
        c.t(X(l5) + 8, yc - esc * onda(l5, picos) - 8, f'{l5:.1f} ms'.replace('.', ','), 8.2, color, 'start', 700)
    # atraso de la V
    yv2 = yB + 206 - esc * onda(TUMOR['V'][0], TUMOR) - 30
    c.l(X(NORMAL['V'][0]), yv2, X(TUMOR['V'][0]) - 3, yv2, AVISO, 1.4, extra=' marker-end="url(#p-v)"')
    c.t(X(NORMAL['V'][0]) - 4, yv2 + 3, 'V +0,9 ms', 8.2, AVISO, 'end', 700)
    # eje del tiempo
    ye = ybot + 6
    c.l(x0, ye, x1, ye, FUERTE, 1)
    for t in range(0, 11, 2):
        c.l(X(t), ye, X(t), ye + 4, FUERTE, 1)
        c.t(X(t), ye + 15, t, 8, TENUE)
    c.t(x1, ye + 28, 'tiempo desde el click (ms)', 8.2, TENUE, 'end')
    c.t(14, 532, 'El trazo normal usa las medias del adulto (H10).',
        7.8, TENUE, 'start')
    c.guardar('cap11-generadores-peat.svg', defs)


if __name__ == '__main__':
    arco_reflejo()
    generadores_peat()
