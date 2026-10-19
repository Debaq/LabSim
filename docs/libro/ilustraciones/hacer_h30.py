#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H30 (CPAP y dispositivos de avance mandibular):

    h30-ferula.svg        vía aérea superior colapsada frente a ferulizada por la presión positiva
    h30-interfaces.svg    tres interfaces: mascarilla nasal, almohadillas nasales, mascarilla oronasal
    h30-titulacion.svg    titulación manual: presión creciente y eventos por escalón
    h30-descarga.svg      resumen de descarga de datos de uso de un equipo (30 noches de ejemplo)
    h30-avance.svg        avance mandibular: la lengua y la pared faríngea se alejan de la pared posterior

SVG propios, no IA. Son esquemas: las proporciones anatómicas son aproximadas. Los datos de la
titulación y de la descarga son de ejemplo (no de pacientes) y se generan de forma determinista;
las cifras que aparecen en el capítulo salen de este script (se imprimen al correrlo)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h28 import Lienzo, Eje, TINTA, TENUE, GRILLA, FUERTE, AVISO, RETRO, COCLEAR, IZQ  # noqa: E402

AQUI = pathlib.Path(__file__).parent
AIRE = '#bcd8ec'       # luz de la vía aérea
PIEL = '#f3e4d8'
TEJIDO = '#e8b9b0'     # lengua y paladar
HUESO = '#d9cfa8'


# ------------------------------------------------------------------ cabeza de perfil
def ancho_luz(y, colapso_palatal=0.0, colapso_lingual=0.0, base=24.0):
    """Ancho de la luz faríngea (px) a la altura y; dos estrechamientos: retropalatal y retrolingual."""
    w = base
    w -= base * 0.93 * colapso_palatal * math.exp(-((y - 178) / 11) ** 2)
    w -= base * 0.93 * colapso_lingual * math.exp(-((y - 218) / 11) ** 2)
    return w


def cabeza(c, ox, oy, colapso_palatal=0.0, colapso_lingual=0.0, avance=0.0, ensanche_lingual=0.0):
    """Perfil de cabeza mirando a la derecha, con la vía aérea. Coordenadas locales 0..300 x 0..270.
    avance: desplazamiento (px) de la mandíbula y de la base de la lengua hacia delante."""
    def P(x, y):
        return f'{ox + x:.1f},{oy + y:.1f}'
    a = avance
    piel = (f'M{P(60, 262)} L{P(60, 170)} C{P(30, 140)} {P(30, 40)} {P(120, 20)} C{P(200, 5)} {P(240, 50)} {P(245, 90)} '
            f'L{P(272, 135)} L{P(250, 146)} L{P(252, 165)} L{P(246 + a * .5, 183)} L{P(247 + a, 206)} '
            f'L{P(226 + a, 226)} L{P(195, 236)} L{P(182, 262)}')
    c.raw(f'<path d="{piel}" fill="{PIEL}" stroke="{TINTA}" stroke-width="1.6" stroke-linejoin="round"/>')
    # vía aérea: nariz (banda horizontal) + faringe (banda vertical con estrechamientos)
    ys = list(range(150, 262, 2))
    atras = [(128, y) for y in ys]
    # base de la lengua: el ensanche corre la pared anterior hacia delante a la altura lingual
    adel = []
    for y in ys:
        w = ancho_luz(y, colapso_palatal, colapso_lingual)
        w += ensanche_lingual * math.exp(-((y - 218) / 14) ** 2)
        adel.append((128 + w, y))
    poli = [(128, 138)] + [(262, 138)] + [(262, 150)] + [(128 + 24, 150)] + adel[::-1][:0]
    cont = [(262, 138), (128, 138), (118, 150)] + [(128, y) for y in ys] + [(adel[-1][0], 262)] + adel[::-1] + [(150, 150), (262, 150)]
    c.raw('<polygon points="%s" fill="%s" stroke="%s" stroke-width="1"/>' % (
        ' '.join(P(x, y) for x, y in cont), AIRE, TENUE))
    # lengua (cuerpo en la boca + base contra la faringe), se mueve con la mandíbula
    lx = a
    lengua = [(172 + lx, 188), (222 + lx, 190), (238 + lx, 200), (222 + lx, 212), (190 + lx, 222), (168 + lx, 232), (160 + lx, 228)]
    # la base de la lengua forma la pared anterior de la faringe a la altura lingual
    frente = 128 + ancho_luz(218, colapso_palatal, colapso_lingual) + ensanche_lingual * 1.0
    lengua = [(x if x > 250 else x, y) for x, y in lengua]
    base_len = [(frente, 206), (frente, 232)]
    cont_l = [(172 + lx, 188), (222 + lx, 190), (238 + lx, 200), (222 + lx, 212), (200 + lx, 226), (frente + 8, 236),
              (frente, 232), (frente, 206), (frente + 4, 196)]
    c.raw('<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.1" stroke-linejoin="round"/>' % (
        ' '.join(P(x, y) for x, y in cont_l), TEJIDO, TINTA))
    # paladar duro y blando
    pb_fin = 128 + ancho_luz(178, colapso_palatal, colapso_lingual)
    c.raw(f'<path d="M{P(246, 160)} L{P(190, 162)} L{P(150, 164)} Q{P(pb_fin + 6, 170)} {P(pb_fin, 190)} '
          f'L{P(pb_fin - 2, 164)}" fill="none" stroke="none"/>')
    paladar = [(246, 156), (190, 158), (150, 160), (pb_fin + 8, 166), (pb_fin + 2, 186), (pb_fin - 6, 190), (128 + 24 - 18, 168)]
    c.raw('<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.1" stroke-linejoin="round"/>' % (
        ' '.join(P(x, y) for x, y in [(250, 152), (190, 154), (146, 156), (pb_fin + 10, 160), (pb_fin + 4, 186), (pb_fin - 6, 190),
                                      (pb_fin - 9, 170), (150, 166), (190, 166), (250, 164)]), TEJIDO, TINTA))
    # cavidad bucal (aire) entre paladar y lengua
    c.raw('<polygon points="%s" fill="%s" stroke="none"/>' % (
        ' '.join(P(x, y) for x, y in [(250, 166), (190, 168), (156, 170), (pb_fin - 4, 190), (172 + lx, 188), (222 + lx, 190), (240 + lx, 198), (252, 178)]), AIRE))
    # dientes
    c.raw(f'<rect x="{ox + 246:.1f}" y="{oy + 163:.1f}" width="5" height="12" rx="1.5" fill="#fff" stroke="{TINTA}" stroke-width=".9"/>')
    c.raw(f'<rect x="{ox + 244 + a:.1f}" y="{oy + 178:.1f}" width="5" height="12" rx="1.5" fill="#fff" stroke="{TINTA}" stroke-width=".9"/>')


def flecha(c, x1, y1, x2, y2, color=TINTA, w=1.6):
    ang = math.atan2(y2 - y1, x2 - x1)
    c.l(x1, y1, x2, y2, color, w)
    for s in (-1, 1):
        c.l(x2, y2, x2 - 7 * math.cos(ang + s * 0.45), y2 - 7 * math.sin(ang + s * 0.45), color, w)


# ------------------------------------------------------------------ 1. vía aérea colapsada y ferulizada
def sitio(c, x, y, texto, dx=0, dy=0):
    """Marca de cierre: círculo rojo en el sitio donde la luz se cierra."""
    c.raw(f'<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{AVISO}" stroke-width="2"/>')


def ferula():
    c = Lienzo(900, 350)
    c.t(14, 20, 'A · Sin presión positiva: la luz se cierra', 10, TINTA, 'start', 700)
    c.t(464, 20, 'B · Con presión positiva: la luz queda abierta', 10, TINTA, 'start', 700)
    ax, ay, bx, by = 20, 40, 470, 40
    cabeza(c, ax, ay, colapso_palatal=1.0, colapso_lingual=1.0)
    cabeza(c, bx, by)
    # A: sitios de cierre y rótulos
    sitio(c, ax + 130, ay + 178, '')
    sitio(c, ax + 130, ay + 218, '')
    c.t(ax + 290, ay + 102, 'nariz', 8.5, TINTA, 'start')
    c.l(ax + 286, ay + 99, ax + 262, ay + 128, TENUE, .8)
    c.t(ax + 290, ay + 158, 'cierre retropalatal', 8.5, AVISO, 'start', 700)
    c.l(ax + 286, ay + 155, ax + 140, ay + 176, AVISO, .8)
    c.t(ax + 290, ay + 238, 'cierre retrolingual', 8.5, AVISO, 'start', 700)
    c.l(ax + 286, ay + 235, ax + 140, ay + 220, AVISO, .8)
    c.t(ax + 290, ay + 196, 'paladar blando', 8.5, TINTA, 'start')
    c.l(ax + 286, ay + 193, ax + 200, ay + 160, TENUE, .8)
    c.t(ax + 290, ay + 214, 'lengua', 8.5, TINTA, 'start')
    c.l(ax + 286, ay + 211, ax + 214, ay + 204, TENUE, .8)
    # B: mascarilla nasal y presión
    c.raw(f'<path d="M{bx + 266:.1f},{by + 120:.1f} L{bx + 298:.1f},{by + 124:.1f} L{bx + 298:.1f},{by + 160:.1f} L{bx + 268:.1f},{by + 152:.1f} Z" '
          f'fill="#fff" fill-opacity=".85" stroke="{COCLEAR}" stroke-width="2" stroke-linejoin="round"/>')
    c.l(bx + 298, by + 142, bx + 340, by + 142, COCLEAR, 5)
    c.t(bx + 290, by + 104, 'mascarilla nasal', 8.5, COCLEAR, 'start', 700)
    c.t(bx + 290, by + 116, 'y tubo al equipo', 8.5, COCLEAR, 'start', 700)
    for y in (178, 218):
        for dx in (-1, 1):
            xc = bx + 128 + 12
            flecha(c, xc, by + y, xc + dx * 17, by + y, RETRO, 1.7)
    for x in (bx + 190, bx + 218):
        c.t(x, by + 148, '+', 13, RETRO, 'middle', 700)
    c.t(bx + 140, by + 250, '+', 13, RETRO, 'middle', 700)
    c.t(bx + 290, by + 196, 'la presión empuja', 8.5, RETRO, 'start', 700)
    c.t(bx + 290, by + 208, 'las paredes hacia fuera', 8.5, RETRO, 'start', 700)
    c.l(bx + 286, by + 205, bx + 170, by + 218, RETRO, .8)
    c.t(14, 322, 'En la inspiración la presión dentro de la faringe baja bajo la atmosférica y la pared, sin soporte, se apoya en el paladar y en la lengua.', 8, TENUE, 'start')
    c.t(14, 336, 'Con la presión positiva la luz queda a presión mayor que la atmosférica durante todo el ciclo: funciona como una férula neumática. Esquema; las proporciones son aproximadas.', 8, TENUE, 'start')
    c.guardar('h30-ferula.svg')


# ------------------------------------------------------------------ 2. interfaces
def cara(c, ox, oy):
    """Cara de frente (esquema)."""
    c.raw(f'<ellipse cx="{ox + 90}" cy="{oy + 110}" rx="62" ry="86" fill="{PIEL}" stroke="{TINTA}" stroke-width="1.6"/>')
    for dx in (-24, 24):
        c.raw(f'<ellipse cx="{ox + 90 + dx}" cy="{oy + 82}" rx="9" ry="4.5" fill="#fff" stroke="{TINTA}" stroke-width="1.1"/>')
        c.raw(f'<circle cx="{ox + 90 + dx}" cy="{oy + 82}" r="2.4" fill="{TINTA}"/>')
    c.raw(f'<path d="M{ox + 90},{oy + 88} L{ox + 84},{oy + 120} Q{ox + 90},{oy + 126} {ox + 96},{oy + 120} Z" fill="none" stroke="{TENUE}" stroke-width="1"/>')
    c.raw(f'<path d="M{ox + 70},{oy + 150} Q{ox + 90},{oy + 160} {ox + 110},{oy + 150}" fill="none" stroke="{TINTA}" stroke-width="1.6"/>')


def interfaces():
    c = Lienzo(760, 360)
    titulos = ['A · Mascarilla nasal', 'B · Almohadillas nasales', 'C · Mascarilla oronasal']
    for i, t in enumerate(titulos):
        ox = 14 + i * 250
        c.t(ox, 20, t, 10, TINTA, 'start', 700)
        cara(c, ox + 20, 36)
    col = COCLEAR
    # A: triángulo sobre la nariz
    ox = 34
    c.raw(f'<path d="M{ox + 90},{36 + 80} L{ox + 66},{36 + 130} Q{ox + 90},{36 + 140} {ox + 114},{36 + 130} Z" fill="#fff" fill-opacity=".8" '
          f'stroke="{col}" stroke-width="2.4" stroke-linejoin="round"/>')
    c.l(ox + 90, 36 + 78, ox + 90, 36 + 52, col, 5)
    for yy in (74, 98):
        c.l(ox + 69, 36 + yy + 14, ox + 28, 36 + yy + 22, col, 1.5)
        c.l(ox + 111, 36 + yy + 14, ox + 152, 36 + yy + 22, col, 1.5)
    # B: dos óvalos en las narinas
    ox = 284
    for dx in (-9, 9):
        c.raw(f'<ellipse cx="{ox + 90 + dx}" cy="{36 + 123}" rx="7" ry="5" fill="#fff" stroke="{col}" stroke-width="2.2"/>')
    c.raw(f'<path d="M{ox + 81},{36 + 120} Q{ox + 90},{36 + 100} {ox + 99},{36 + 120}" fill="none" stroke="{col}" stroke-width="3"/>')
    c.l(ox + 90, 36 + 104, ox + 90, 36 + 52, col, 5)
    for yy in (74, 98):
        c.l(ox + 72, 36 + yy + 10, ox + 28, 36 + yy + 18, col, 1.5)
        c.l(ox + 108, 36 + yy + 10, ox + 152, 36 + yy + 18, col, 1.5)
    # C: forma que cubre nariz y boca
    ox = 534
    c.raw(f'<path d="M{ox + 90},{36 + 80} L{ox + 62},{36 + 130} Q{ox + 58},{36 + 168} {ox + 90},{36 + 176} Q{ox + 122},{36 + 168} {ox + 118},{36 + 130} Z" '
          f'fill="#fff" fill-opacity=".8" stroke="{col}" stroke-width="2.4" stroke-linejoin="round"/>')
    c.l(ox + 90, 36 + 78, ox + 90, 36 + 52, col, 5)
    for yy in (74, 98):
        c.l(ox + 65, 36 + yy + 14, ox + 28, 36 + yy + 22, col, 1.5)
        c.l(ox + 115, 36 + yy + 14, ox + 152, 36 + yy + 22, col, 1.5)
    c.l(ox + 90, 36 + 52, ox + 90, 36 + 40, col, 5)
    # textos
    notas = [
        ['cubre la nariz', 'exige respirar por la nariz:', 'con la boca abierta', 'el aire se escapa'],
        ['se apoyan en las narinas', 'poco contacto con la cara', 'la presión entra por las narinas;', 'menos espacio muerto bajo la máscara'],
        ['cubre nariz y boca', 'sirve si el paciente respira', 'por la boca; en un estudio se', 'asoció a presiones más altas'],
    ]
    for i, n in enumerate(notas):
        ox = 14 + i * 250
        for k, s in enumerate(n):
            c.t(ox + 4, 268 + k * 13, s, 8.5, TINTA if k == 0 else TENUE, 'start', 700 if k == 0 else 400)
    c.t(14, 346, 'Esquemas de frente. El tubo (arriba) va al equipo; las líneas laterales son el arnés que sujeta la interfaz.', 8, TENUE, 'start')
    c.guardar('h30-interfaces.svg')


# ------------------------------------------------------------------ 3. titulación
def lcg(seed):
    s = seed
    while True:
        s = (s * 1103515245 + 12345) % 2 ** 31
        yield s / 2 ** 31


def titulacion():
    """Titulación manual de ejemplo: IAH basal 38/h; presión eficaz 10 cmH2O. Escalones de 1 cmH2O cada 10 min."""
    p0, peff, dur = 4, 10, 10
    escalones = list(range(p0, 12))                         # 4..11
    base = 38.0
    tasa = lambda p: base * math.exp(-(p - p0) / 1.7) if p < peff else 1.6
    c = Lienzo(760, 420)
    c.t(14, 20, 'Titulación manual de ejemplo: la presión sube hasta que desaparecen los eventos obstructivos', 10, TINTA, 'start', 700)
    t_fin = len(escalones) * dur
    ej1 = Eje(c, 130, 40, 600, 130, 0, t_fin, 0, 14)
    ej1.marco(xt=list(range(0, t_fin + 1, 10)), yt=[0, 4, 8, 12], ylab='presión (cmH₂O)')
    pts = []
    for i, p in enumerate(escalones):
        pts += [(ej1.X(i * dur), ej1.Y(p)), (ej1.X((i + 1) * dur), ej1.Y(p))]
    c.poli(pts, COCLEAR, 2.6)
    c.t(ej1.X(0.6), ej1.Y(4) - 8, 'inicio: 4 cmH₂O', 8.5, TINTA, 'start')
    # zona de la presión eficaz
    ie = escalones.index(peff)
    c.raw(f'<rect x="{ej1.X(ie * dur):.1f}" y="{ej1.y0}" width="{ej1.X(t_fin) - ej1.X(ie * dur):.1f}" height="{ej1.h}" fill="{RETRO}" opacity=".10"/>')
    c.t(ej1.X(ie * dur + 1), ej1.Y(13), 'presión sin eventos obstructivos', 8.5, RETRO, 'start', 700)
    # eventos
    ej2 = Eje(c, 130, 210, 600, 100, 0, t_fin, 0, 1)
    ej2.marco(xt=list(range(0, t_fin + 1, 10)), yt=[], xlab='tiempo desde el inicio de la titulación (min)')
    c.raw(f'<rect x="{ej2.X(ie * dur):.1f}" y="{ej2.y0}" width="{ej2.X(t_fin) - ej2.X(ie * dur):.1f}" height="{ej2.h}" fill="{RETRO}" opacity=".10"/>')
    c.t(120, ej2.y0 + 25, 'apnea', 8.5, AVISO, 'end')
    c.t(120, ej2.y0 + 55, 'hipopnea', 8.5, IZQ, 'end')
    c.t(120, ej2.y0 + 85, 'ronquido', 8.5, TENUE, 'end')
    r = lcg(7)
    resumen = []
    for i, p in enumerate(escalones):
        n = tasa(p) * dur / 60
        n_ap = round(n * 0.55)
        n_hi = round(n * 0.45)
        n_ro = round(n * 0.5 + (2 if p < peff else 0))
        resumen.append((p, n_ap, n_hi, n_ro))
        for fila, cant, col, yy in ((0, n_ap, AVISO, 18), (1, n_hi, IZQ, 48), (2, n_ro, TENUE, 78)):
            for k in range(cant):
                x = ej2.X(i * dur + 0.4 + (dur - 0.8) * next(r))
                c.l(x, ej2.y0 + yy - 9, x, ej2.y0 + yy + 9, col, 2)
    # recuento por escalón
    for i, (p, a, h, ro) in enumerate(resumen):
        x = ej2.X(i * dur + dur / 2)
        c.t(x, ej2.y0 + ej2.h + 40, f'{p}', 8.5, TINTA, 'middle', 700)
    c.t(ej2.x0 - 6, ej2.y0 + ej2.h + 40, 'presión:', 8.5, TENUE, 'end')
    c.t(ej2.x0 - 6, ej2.y0 + ej2.h + 54, 'apneas + hipopneas:', 8.5, TENUE, 'end')
    for i, (p, a, h, ro) in enumerate(resumen):
        x = ej2.X(i * dur + dur / 2)
        c.t(x, ej2.y0 + ej2.h + 54, f'{a + h}', 8.5, TINTA)
    # reglas
    c.t(14, 386, 'Cada escalón dura 10 min y sube 1 cmH₂O mientras persisten eventos obstructivos. La guía fija como mínimo 1 cmH₂O y 5 min por escalón,', 8, TENUE, 'start')
    c.t(14, 398, 'partiendo de 4 cmH₂O (Kushida y cols., 2008). Las marcas y los recuentos son datos de ejemplo.', 8, TENUE, 'start')
    c.guardar('h30-titulacion.svg')
    print('titulación (presión, apneas, hipopneas, ronquido):', resumen)
    print('tasa modelo (eventos/h):', {p: round(tasa(p), 1) for p in escalones})


# ------------------------------------------------------------------ 4. descarga de datos
def descarga():
    """30 noches de ejemplo. Horas de uso; el patrón mejora a partir de la segunda semana."""
    r = lcg(21)
    horas = []
    for n in range(30):
        u = next(r)
        if n in (3, 9, 17):
            h = 0.0                                          # noches sin uso
        elif n in (4, 10, 11, 18):
            h = round(1.2 + 2.2 * u, 1)                      # uso corto
        else:
            h = round(5.0 + 2.8 * u, 1)
        horas.append(h)
    uso_medio = sum(horas) / 30
    noches4 = sum(1 for h in horas if h >= 4)
    pct4 = 100 * noches4 / 30
    con_uso = [h for h in horas if h > 0]
    uso_dias_uso = sum(con_uso) / len(con_uso)
    iah, fuga = 3.1, 11
    c = Lienzo(760, 380)
    c.t(14, 20, 'Resumen de 30 noches descargado del equipo (datos de ejemplo)', 10, TINTA, 'start', 700)
    ej = Eje(c, 60, 44, 440, 230, 0.5, 30.5, 0, 10)
    ej.marco(xt=[1, 5, 10, 15, 20, 25, 30], yt=[0, 2, 4, 6, 8, 10], ylab='horas de uso', xlab='noche')
    c.l(ej.x0, ej.Y(4), ej.x0 + ej.w, ej.Y(4), AVISO, 1.4, '5 3')
    c.t(ej.x0 + ej.w + 4, ej.Y(4) + 3, '4 h', 8.5, AVISO, 'start', 700)
    bw = ej.w / 30 * 0.7
    for i, h in enumerate(horas):
        col = RETRO if h >= 4 else FUERTE
        x = ej.X(i + 1) - bw / 2
        c.raw(f'<rect x="{x:.1f}" y="{ej.Y(h):.1f}" width="{bw:.1f}" height="{ej.Y(0) - ej.Y(h):.1f}" fill="{col}"/>')
    c.t(ej.x0, 318, 'Verde: noche con 4 h o más de uso. Gris: menos de 4 h (incluye 3 noches sin uso).', 8, TENUE, 'start')
    # tarjetas con métricas
    tarjetas = [
        ('Uso promedio', f'{uso_medio:.1f} h'.replace('.', ','), 'de las 30 noches'),
        ('Noches con ≥ 4 h', f'{noches4} de 30', f'({pct4:.0f} %)'),
        ('IAH residual', f'{iah:.1f}'.replace('.', ','), 'eventos por hora'),
        ('Fuga no intencional', f'{fuga} L/min', 'percentil 95'),
    ]
    for k, (a, b, d) in enumerate(tarjetas):
        x, y = 524, 44 + k * 58
        c.raw(f'<rect x="{x}" y="{y}" width="222" height="50" rx="6" fill="#faf8f4" stroke="{FUERTE}" stroke-width="1"/>')
        c.t(x + 10, y + 17, a, 8.5, TENUE, 'start')
        c.t(x + 10, y + 40, b, 15, TINTA, 'start', 700)
        c.t(x + 212, y + 40, d, 8.5, TENUE, 'end')
    c.t(524, 290, 'Modo: CPAP fijo, 10 cmH₂O', 8.5, TINTA, 'start')
    c.t(524, 303, 'Interfaz: mascarilla nasal', 8.5, TINTA, 'start')
    c.t(524, 316, 'Humidificador: nivel 3', 8.5, TINTA, 'start')
    c.t(14, 346, 'El límite de fuga aceptable depende de la interfaz y del fabricante del equipo; el valor del ejemplo es ilustrativo.', 8, TENUE, 'start')
    c.t(14, 360, 'Las cifras salen de las 30 barras: promedio de todas las noches, incluidas las de cero horas.', 8, TENUE, 'start')
    c.guardar('h30-descarga.svg')
    print('descarga: horas =', horas)
    print('descarga: uso medio %.2f h; media en noches de uso %.2f h; noches >=4 h: %d de 30 (%.1f %%)' % (uso_medio, uso_dias_uso, noches4, pct4))


# ------------------------------------------------------------------ 5. avance mandibular
def avance():
    c = Lienzo(900, 350)
    c.t(14, 20, 'A · Sin dispositivo: la lengua cae hacia atrás', 10, TINTA, 'start', 700)
    c.t(464, 20, 'B · Con dispositivo: la mandíbula arrastra la lengua', 10, TINTA, 'start', 700)
    ax, ay, bx, by = 20, 40, 470, 40
    cabeza(c, ax, ay, colapso_palatal=0.35, colapso_lingual=0.9)
    cabeza(c, bx, by, colapso_palatal=0.15, colapso_lingual=0.0, avance=9, ensanche_lingual=10)
    c.t(ax + 290, ay + 214, 'luz retrolingual angosta', 8.5, AVISO, 'start', 700)
    c.l(ax + 286, ay + 211, ax + 140, ay + 220, AVISO, .8)
    c.t(ax + 290, ay + 238, 'mandíbula en reposo', 8.5, TINTA, 'start')
    c.l(ax + 286, ay + 235, ax + 250, ay + 214, TENUE, .8)
    # B: férulas, flecha de avance, ensanche
    c.raw(f'<rect x="{bx + 242:.1f}" y="{by + 161:.1f}" width="9" height="4" rx="1.5" fill="{COCLEAR}"/>')
    c.raw(f'<rect x="{bx + 251:.1f}" y="{by + 187:.1f}" width="9" height="4" rx="1.5" fill="{COCLEAR}"/>')
    c.l(bx + 251, by + 163, bx + 255, by + 189, COCLEAR, 1.4)
    c.t(bx + 290, by + 120, 'férula sobre', 8.5, COCLEAR, 'start', 700)
    c.t(bx + 290, by + 132, 'las dos arcadas', 8.5, COCLEAR, 'start', 700)
    c.l(bx + 286, by + 129, bx + 258, by + 170, COCLEAR, .8)
    flecha(c, bx + 240, by + 250, bx + 272, by + 250, COCLEAR, 2)
    c.t(bx + 290, by + 246, 'avance de la mandíbula', 8.5, COCLEAR, 'start', 700)
    c.t(bx + 290, by + 258, '(unos milímetros)', 8.5, COCLEAR, 'start')
    c.t(bx + 290, by + 206, 'la luz retrolingual', 8.5, RETRO, 'start', 700)
    c.t(bx + 290, by + 218, 'se ensancha', 8.5, RETRO, 'start', 700)
    c.l(bx + 286, by + 215, bx + 168, by + 220, RETRO, .8)
    c.t(14, 322, 'La mandíbula y la base de la lengua van unidas por los músculos: al adelantar la mandíbula, la lengua se aleja de la pared posterior de la faringe.', 8, TENUE, 'start')
    c.t(14, 336, 'Esquema; las proporciones son aproximadas. El avance real lo gradúa el dentista con el paciente, hasta el máximo que tolera.', 8, TENUE, 'start')
    c.guardar('h30-avance.svg')


if __name__ == '__main__':
    ferula()
    interfaces()
    titulacion()
    descarga()
    avance()
