#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H25 (rinometria acustica):

    h25-equipo.svg       tubo, adaptador nasal, microfono y el eco que vuelve de la fosa nasal
    h25-curva.svg        curva area-distancia normal: escotaduras I y C, MCA1/MCA2, volumenes
    h25-vasoconstrictor.svg  reposo y post-vasoconstrictor en cuatro situaciones
    h25-limites.svg      lo que la curva no ve: detras de un estrechamiento y mas alla de ~5 cm

SVG propios, no IA. Son ESQUEMAS: las curvas no son datos de nadie y no llevan escala de area;
la unica cifra de distancia sostenida por la literatura es la ventana fiable de ~5 cm
(Hilberg y Pedersen, 2000; Cakmak y cols., 2005)."""
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO, AZUL = '#c0571c', '#21796c', '#c62f3a', '#2a5d9f'
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

    def poli(self, pts, color, w=2, dash=None, fill='none', extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="{fill}" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}{extra}/>')

    def rect(self, x, y, w, h, fill='none', stroke=None, sw=1, rx=0, extra=''):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{s}{extra}/>')

    def circ(self, x, y, r, fill='#fff', stroke=TINTA, sw=1.6):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def guardar(self, nombre, defs=''):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><defs>{defs}</defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def punta(id_, color):
    return (f'<marker id="{id_}" markerWidth="8" markerHeight="8" refX="6" refY="3.5" '
            f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="{color}"/></marker>')


def spline(pts, n=14):
    """Catmull-Rom por tramos (x creciente): curva suave que pasa por los puntos."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
            out.append((x, y))
    out.append(pts[-1])
    return out


# Curvas esquematicas: (distancia en cm, area relativa 0-1). Sin escala de area.
NORMAL = [(0, .34), (.5, .52), (1.0, .56), (1.7, .26), (2.4, .50), (2.9, .58), (3.4, .40), (4.2, .66), (5.0, .86), (6.0, .95), (7.0, 1.0)]
VASOMOTOR_REPOSO = [(0, .30), (.5, .46), (1.0, .50), (1.7, .20), (2.4, .34), (2.9, .36), (3.4, .20), (4.2, .42), (5.0, .62), (6.0, .78), (7.0, .88)]
SEPTAL_REPOSO = [(0, .30), (.5, .40), (1.0, .38), (1.7, .10), (2.4, .22), (2.9, .30), (3.4, .22), (4.2, .38), (5.0, .56), (6.0, .74), (7.0, .85)]
SEPTAL_PVC = [(0, .31), (.5, .42), (1.0, .41), (1.7, .12), (2.4, .26), (2.9, .36), (3.4, .27), (4.2, .46), (5.0, .62), (6.0, .78), (7.0, .88)]
MIXTA_PVC = [(0, .32), (.5, .50), (1.0, .52), (1.7, .17), (2.4, .38), (2.9, .46), (3.4, .30), (4.2, .54), (5.0, .72), (6.0, .86), (7.0, .94)]
SEPTAL_V = SEPTAL_REPOSO  # alias


def ejes(c, x0, y0, w, h, xmax=7, ticks=range(0, 8), etiqueta=True, tam=8):
    X = lambda d: x0 + d / xmax * w
    c.l(x0, y0 + h, x0 + w, y0 + h, FUERTE, 1)
    c.l(x0, y0, x0, y0 + h, FUERTE, 1)
    for d in ticks:
        c.l(X(d), y0 + h, X(d), y0 + h + 4, FUERTE, 1)
        c.t(X(d), y0 + h + 15, d, tam, TENUE)
    if etiqueta:
        c.t(x0 + w / 2, y0 + h + 30, 'distancia desde la narina (cm)', tam + .5, TENUE)
    return X


def curva_pts(c_pts, X, Y):
    return [(X(a), Y(b)) for a, b in spline(c_pts)]


# ---------------------------------------------------------------- equipo
def equipo():
    c = Lienzo(700, 330)
    c.t(14, 20, 'Cómo el sonido mide la nariz', 10.5, TINTA, 'start', 700)
    yc = 120
    # tubo
    c.rect(70, yc - 16, 260, 32, '#f6f4ef', FUERTE, 1.4, 4)
    c.t(200, yc + 4, 'tubo de onda (sección constante)', 8.5, TENUE)
    # fuente
    c.rect(34, yc - 22, 34, 44, '#fff', TINTA, 1.6, 4)
    c.t(51, yc + 3, 'F', 11, TINTA, 'middle', 700)
    # microfono en el tubo
    c.rect(185, yc - 36, 14, 20, '#fff', TINTA, 1.6, 3)
    c.t(192, yc - 41, 'M', 9, TINTA, 'middle', 700)
    # adaptador
    pts = [(330, yc - 16), (352, yc - 9), (352, yc + 9), (330, yc + 16)]
    c.poli(pts, TINTA, 1.6, fill='#e7e5e0')
    # fosa nasal: ancho segun la curva normal (esquema)
    x0, xl = 352, 330
    base = yc
    def ancho(d):
        sp = spline(NORMAL)
        best = min(sp, key=lambda p: abs(p[0] - d))
        return 4 + best[1] * 22
    top, bot = [], []
    for i in range(0, 331, 5):
        d = i / 330 * 7
        a = ancho(d)
        top.append((x0 + i, base - a))
        bot.append((x0 + i, base + a))
    c.poli(top + bot[::-1], '#b9b4aa', 1.6, fill='#f3e3dc')
    c.poli([(x0, base - ancho(0))] + [(x0, base + ancho(0))], '#b9b4aa', 1.0)
    # notas anatomicas
    xv = x0 + 1.7 / 7 * 330
    xc = x0 + 3.4 / 7 * 330
    c.l(xv, base - 44, xv, base - ancho(1.7) - 3, COCLEAR, 1.2)
    c.t(xv, base - 48, 'válvula nasal', 8.5, COCLEAR, 'middle', 700)
    c.l(xc, base + 50, xc, base + ancho(3.4) + 3, RETRO, 1.2)
    c.t(xc, base + 62, 'cabeza del cornete inferior', 8.5, RETRO, 'middle', 700)
    c.t(x0 + 300, base - 36, 'hacia la rinofaringe', 8, TENUE, 'middle')
    c.l(x0 + 255, base - 28, x0 + 333, base - 28, TENUE, 1, extra=' marker-end="url(#pt)"')
    # pulso y eco
    c.l(80, yc - 6, 180, yc - 6, AZUL, 2, extra=' marker-end="url(#pa)"')
    c.l(300, yc + 8, 215, yc + 8, AVISO, 2, extra=' marker-end="url(#pr)"')
    c.t(130, yc - 20, 'pulso', 8.5, AZUL, 'middle', 700)
    c.t(258, yc + 28, 'eco', 8.5, AVISO, 'middle', 700)
    # leyenda inferior (panel de tiempo -> distancia)
    y2 = 250
    c.t(14, y2 - 24, 'Lo que registra el micrófono y lo que se hace con ello', 10.5, TINTA, 'start', 700)
    c.l(34, y2 + 28, 330, y2 + 28, FUERTE, 1)
    c.l(34, y2 - 12, 34, y2 + 28, FUERTE, 1)
    eco = [(34, y2 + 10), (60, y2 + 10), (70, y2 - 6), (86, y2 + 20), (110, y2 + 8), (140, y2 + 14), (160, y2 - 4), (180, y2 + 18),
           (210, y2 + 10), (260, y2 + 12), (330, y2 + 11)]
    c.poli(spline(eco), AVISO, 1.6)
    c.t(182, y2 + 44, 'tiempo en que vuelve cada eco →', 8.5, TENUE)
    c.l(350, y2 + 8, 400, y2 + 8, TINTA, 1.4, extra=' marker-end="url(#pt)"')
    c.t(375, y2 - 2, 'velocidad', 8, TENUE)
    c.t(375, y2 + 22, 'del sonido', 8, TENUE)
    c.t(540, y2 - 4, 'un eco más tardío viene de más adentro', 9, TINTA, 'middle', 600)
    c.t(540, y2 + 12, 'un eco más fuerte o más débil dice si la sección', 9, TINTA, 'middle', 600)
    c.t(540, y2 + 28, 'se estrechó o se ensanchó', 9, TINTA, 'middle', 600)
    c.t(14, 322, 'Esquema, no a escala: F es la fuente del pulso, M el micrófono. La fosa dibujada usa la misma forma que la curva de la figura siguiente.', 8, TENUE, 'start')
    defs = punta('pa', AZUL) + punta('pr', AVISO) + punta('pt', TINTA)
    c.guardar('h25-equipo.svg', defs)


# ---------------------------------------------------------------- curva normal
def curva():
    c = Lienzo(700, 400)
    x0, y0, w, h = 70, 40, 560, 230
    c.t(14, 20, 'La curva área-distancia de una fosa nasal (esquema)', 10.5, TINTA, 'start', 700)
    X = ejes(c, x0, y0, w, h)
    Y = lambda a: y0 + h - a * h * 0.9
    c.t(34, y0 + h / 2, 'área de la sección', 8.5, TENUE, 'middle', 400)
    c.out[-1] = c.out[-1].replace(f'x="34.0" y="{y0 + h / 2:.1f}"', f'x="34.0" y="{y0 + h / 2:.1f}" transform="rotate(-90 34 {y0 + h / 2:.1f})"')
    # zona 0-5 cm
    c.rect(X(0), y0, X(5) - X(0), h, '#f4ece6')
    c.rect(X(5), y0, X(7) - X(5), h, '#f1f1f1')
    c.t(X(6), y0 + h - 34, 'cada vez menos fiable', 8.5, TENUE, 'middle', 700)
    c.t(X(6), y0 + h - 21, '(senos, rinofaringe)', 8, TENUE)
    pts = curva_pts(NORMAL, X, Y)
    c.poli(pts, TINTA, 2.4)
    # minimos
    for d, a, nom, col, dx in ((1.7, .26, 'MCA1 · escotadura I', COCLEAR, 0), (3.4, .40, 'MCA2 · escotadura C', RETRO, 0)):
        c.l(X(d), Y(a), X(d), y0 + h, col, 1.2, '3 3')
        c.circ(X(d), Y(a), 5, '#fff', col, 2)
    c.t(X(1.7) + 12, Y(.26) + 14, 'MCA1 · escotadura I', 9.5, COCLEAR, 'start', 700)
    c.t(X(1.7) + 12, Y(.26) + 27, 'válvula nasal (istmo)', 8.5, COCLEAR, 'start', 600)
    c.t(X(3.4) + 12, Y(.40) + 14, 'MCA2 · escotadura C', 9.5, RETRO, 'start', 700)
    c.t(X(3.4) + 12, Y(.40) + 27, 'cabeza del cornete inferior', 8.5, RETRO, 'start', 600)
    c.t(X(1.7) - 4, y0 + h - 6, 'Dist 1', 8, COCLEAR, 'middle', 700)
    c.t(X(3.4) - 4, y0 + h - 6, 'Dist 2', 8, RETRO, 'middle', 700)
    c.t(X(0) + 6, y0 + h - 6, 'narina', 8.5, TENUE, 'start')
    # volumenes
    yv = y0 + h + 46
    c.l(X(0), yv, X(3.4), yv, RETRO, 2)
    c.l(X(0), yv - 4, X(0), yv + 4, RETRO, 2); c.l(X(3.4), yv - 4, X(3.4), yv + 4, RETRO, 2)
    c.t(X(1.7), yv + 14, 'Vol 1: de la narina al segundo mínimo', 8.5, RETRO, 'middle', 700)
    c.l(X(0), yv + 24, X(5), yv + 24, COCLEAR, 2)
    c.l(X(0), yv + 20, X(0), yv + 28, COCLEAR, 2); c.l(X(5), yv + 20, X(5), yv + 28, COCLEAR, 2)
    c.t(X(2.5), yv + 38, 'Vol 2: los primeros 5 cm', 8.5, COCLEAR, 'middle', 700)
    c.t(14, 392, 'Esquema: la forma es típica, no es de un paciente ni lleva escala de área. Las distancias de los mínimos varían entre personas.', 8, TENUE, 'start')
    c.guardar('h25-curva.svg')


# ---------------------------------------------------------------- vasoconstrictor
def vasoconstrictor():
    c = Lienzo(700, 470)
    c.t(14, 20, 'Reposo y después del vasoconstrictor (esquemas)', 10.5, TINTA, 'start', 700)
    paneles = [
        ('A · Sin estrechamiento', 'el descongestionante cambia poco', NORMAL, [(a, min(1, b + (.03 if .3 < a < 5 else 0))) for a, b in NORMAL]),
        ('B · Vasomotora (mucosa)', 'sube hasta la curva normal', VASOMOTOR_REPOSO, NORMAL),
        ('C · Mecánica (p. ej. tabique)', 'casi no se mueve', SEPTAL_REPOSO, SEPTAL_PVC),
        ('D · Mixta', 'mejora, pero no llega', SEPTAL_REPOSO, MIXTA_PVC),
    ]
    anchos, altos = 300, 120
    pos = [(50, 55), (390, 55), (50, 270), (390, 270)]
    for (tit, sub, rep, pvc), (x0, y0) in zip(paneles, pos):
        c.t(x0 - 24, y0 - 10, tit, 9.5, TINTA, 'start', 700)
        X = ejes(c, x0, y0, anchos, altos, etiqueta=False, ticks=range(0, 8, 1), tam=7.5)
        Y = lambda a, y0=y0: y0 + altos - a * altos * 0.9
        c.rect(X(0), y0, X(5) - X(0), altos, '#f7f1ec')
        c.poli(curva_pts(NORMAL, X, Y), FUERTE, 1.4, '4 3') if tit[0] != 'A' else None
        c.poli(curva_pts(rep, X, Y), COCLEAR, 2.2)
        if tit[0] != 'A':
            c.poli(curva_pts(pvc, X, Y), RETRO, 2.2, '6 3')
        c.t(x0 + anchos / 2, y0 + altos + 29, f'distancia (cm) · {sub}', 8, TENUE)
    # leyenda
    ly = 450
    c.l(54, ly - 3, 84, ly - 3, COCLEAR, 2.2); c.t(90, ly, 'reposo', 8.5, TINTA, 'start')
    c.l(150, ly - 3, 180, ly - 3, RETRO, 2.2, '6 3'); c.t(186, ly, 'después del vasoconstrictor', 8.5, TINTA, 'start')
    c.l(340, ly - 3, 370, ly - 3, FUERTE, 1.4, '4 3'); c.t(376, ly, 'curva normal de comparación (B, C y D)', 8.5, TINTA, 'start')
    c.t(54, 466, 'Esquemas, no datos. Cuánto es "mejora" o "casi no se mueve" lo define el criterio de cada servicio (→ Cómo se informa).', 8, TENUE, 'start')
    c.guardar('h25-vasoconstrictor.svg')


# ---------------------------------------------------------------- limites
def limites():
    c = Lienzo(700, 300)
    c.t(14, 20, 'Lo que la curva puede no ver (esquema)', 10.5, TINTA, 'start', 700)
    anchos, altos = 290, 140
    verdadera = [(0, .34), (.5, .52), (1.0, .56), (1.7, .26), (2.4, .50), (2.9, .58), (3.4, .40), (4.2, .66), (5.0, .86), (6.0, .95), (7.0, 1.0)]
    # A: detras de una valvula muy estrecha
    x0, y0 = 50, 60
    c.t(x0 - 24, y0 - 14, 'A · Detrás de un estrechamiento marcado', 9.5, TINTA, 'start', 700)
    X = ejes(c, x0, y0, anchos, altos, etiqueta=False, tam=7.5)
    Y = lambda a: y0 + altos - a * altos * .9
    estrecha = [(0, .30), (.5, .40), (1.0, .38), (1.7, .06), (2.4, .22), (2.9, .30), (3.4, .24), (4.2, .40), (5.0, .56), (6.0, .66), (7.0, .72)]
    real = [(0, .30), (.5, .40), (1.0, .38), (1.7, .06), (2.4, .50), (2.9, .62), (3.4, .46), (4.2, .74), (5.0, .92), (6.0, 1.0), (7.0, 1.04)]
    c.poli(curva_pts(real, X, Y), FUERTE, 2, '4 3')
    c.poli(curva_pts(estrecha, X, Y), COCLEAR, 2.2)
    c.t(X(4.9), Y(.92) - 6, 'lo que hay', 8, TENUE, 'middle', 700)
    c.t(X(5.6), Y(.60) + 22, 'lo que se mide', 8, COCLEAR, 'middle', 700)
    c.t(x0 + anchos / 2, y0 + altos + 29, 'el pulso apenas pasa: lo de atrás se subestima o se confunde', 8, TENUE)
    # B: mas alla de 5 cm
    x0, y0 = 390, 60
    c.t(x0 - 24, y0 - 14, 'B · Más allá de los 5 cm', 9.5, TINTA, 'start', 700)
    X = ejes(c, x0, y0, anchos, altos, etiqueta=False, tam=7.5)
    Y = lambda a: y0 + altos - a * altos * .9
    c.rect(X(5), y0, X(7) - X(5), altos, '#f1f1f1')
    real2 = [(0, .34), (.5, .52), (1.0, .56), (1.7, .26), (2.4, .50), (2.9, .58), (3.4, .40), (4.2, .62), (5.0, .72), (6.0, .76), (7.0, .78)]
    medida = [(0, .34), (.5, .52), (1.0, .56), (1.7, .26), (2.4, .50), (2.9, .58), (3.4, .40), (4.2, .64), (5.0, .80), (6.0, 1.0), (7.0, 1.12)]
    c.poli(curva_pts(real2, X, Y), FUERTE, 2, '4 3')
    c.poli(curva_pts(medida, X, Y), COCLEAR, 2.2)
    c.t(X(6), Y(.76) + 18, 'lo que hay', 8, TENUE, 'middle', 700)
    c.t(X(5.8), Y(1.0) - 10, 'lo que se mide', 8, COCLEAR, 'middle', 700)
    c.t(x0 + anchos / 2, y0 + altos + 29, 'senos y fosa contraria suman área: la curva sobreestima', 8, TENUE)
    c.l(54, 262, 84, 262, FUERTE, 2, '4 3'); c.t(90, 265, 'anatomía real', 8.5, TINTA, 'start')
    c.l(190, 262, 220, 262, COCLEAR, 2.2); c.t(226, 265, 'lo que dibuja el equipo', 8.5, TINTA, 'start')
    c.t(54, 288, 'Esquemas para ver el sentido del error; la magnitud real depende de cada nariz (Cakmak y cols., 2005; Hilberg y Pedersen, 1996).', 8, TENUE, 'start')
    c.guardar('h25-limites.svg')


if __name__ == '__main__':
    equipo()
    curva()
    vasoconstrictor()
    limites()
