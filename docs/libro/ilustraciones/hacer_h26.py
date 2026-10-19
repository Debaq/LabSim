#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H26 (rinomanometría anterior):

    h26-montaje.svg     el montaje de la rinomanometría anterior activa (esquema)
    h26-curvas.svg      A: curva presión-flujo en los cuatro cuadrantes; B: resistencia según la presión
    h26-broms.svg       la idea del gráfico polar de Broms: resistencia en un radio estándar
    h26-vasoconstrictor.svg  antes y después del vasoconstrictor: tres patrones

SVG propios, no IA. Las curvas salen de la ecuación de Rohrer, P = k1·V + k2·V², con
parámetros inventados para el ejemplo (no son datos de pacientes). Todas las cifras que
aparecen en el capítulo salen de este script (se imprimen al correrlo)."""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO = '#c0571c', '#21796c', '#c62f3a'
DER, IZQ = '#c62f3a', '#2b5fa8'   # derecha en rojo, izquierda en azul, como en el audiograma
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400, extra=''):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}"{extra}>{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}{extra}/>')

    def poli(self, pts, color, w=2, dash=None, extra='', fill='none'):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="{fill}" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}{extra}/>')

    def raw(self, s):
        self.out.append(s)

    def punto(self, x, y, color, r=4):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="#fff" stroke-width="1.2"/>')

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


# ---- el modelo: P = a·V + b·V², con la resistencia R150 = 150 / V(150) ----
def params(r150, frac_lineal=0.4):
    v150 = 150 / r150
    a = frac_lineal * r150
    b = (150 - a * v150) / v150 ** 2
    return a, b


def flujo(P, a, b):
    return (-a + math.sqrt(a * a + 4 * b * P)) / (2 * b)


DERECHA = params(0.50)     # 300 cm3/s a 150 Pa
IZQUIERDA = params(0.25)   # 600 cm3/s a 150 Pa


# ------------------------------------------------------------------ montaje
def montaje():
    c = Lienzo(700, 330)
    c.t(14, 20, 'A · De perfil, midiendo la fosa derecha', 10.5, TINTA, 'start', 700)
    # perfil de la cabeza
    perfil = [(112, 52), (150, 46), (170, 60), (176, 96), (180, 112), (212, 150), (206, 160), (182, 164),
              (184, 178), (186, 196), (178, 214), (180, 232), (168, 244), (150, 262), (150, 300)]
    c.poli(perfil, TINTA, 1.8)
    c.poli([(112, 52), (92, 80), (86, 140), (96, 200), (120, 250), (130, 300)], TINTA, 1.8)
    c.t(130, 150, 'paciente', 8, TENUE)
    # mascarilla sobre nariz y boca
    mask = [(176, 108), (246, 120), (262, 200), (234, 236), (176, 242)]
    c.poli(mask, COCLEAR, 2.2, fill='#c0571c14')
    # neumotacógrafo: tubo con malla
    c.raw(f'<rect x="256" y="154" width="122" height="44" rx="6" fill="#fff" stroke="{TINTA}" stroke-width="1.8"/>')
    for k in range(5):
        c.l(316, 160 + k * 8.5, 316, 160 + k * 8.5 + 6, TENUE, 1.2)
    c.l(310, 154, 310, 198, TINTA, 1, '3 3')
    c.l(322, 154, 322, 198, TINTA, 1, '3 3')
    # tomas a cada lado de la malla hacia el transductor de flujo
    c.l(296, 154, 296, 110, COCLEAR, 1.6)
    c.l(338, 154, 338, 110, COCLEAR, 1.6)
    c.raw(f'<rect x="282" y="76" width="70" height="34" rx="5" fill="#c0571c14" stroke="{COCLEAR}" stroke-width="1.6"/>')
    c.t(317, 91, 'transductor', 8, COCLEAR, 'middle', 700)
    c.t(317, 102, 'de flujo (Δp)', 8, COCLEAR, 'middle', 700)
    # flecha del aire
    c.l(268, 176, 292, 176, TENUE, 1.2, extra=' marker-end="url(#p-aire)"')
    c.l(372, 176, 392, 176, TENUE, 1.2, extra=' marker-end="url(#p-aire)"')
    # tubo de presión desde la fosa izquierda (ocluida con adaptador)
    c.raw(f'<circle cx="204" cy="156" r="6" fill="{IZQ}" stroke="#fff" stroke-width="1"/>')
    c.poli([(204, 160), (204, 190), (230, 252), (300, 270), (420, 270), (420, 240)], IZQ, 1.8)
    c.raw(f'<rect x="388" y="204" width="70" height="36" rx="5" fill="#2b5fa814" stroke="{IZQ}" stroke-width="1.6"/>')
    c.t(423, 219, 'transductor', 8, IZQ, 'middle', 700)
    c.t(423, 231, 'de presión', 8, IZQ, 'middle', 700)
    # computador
    c.l(352, 93, 480, 93, TENUE, 1.2, '4 3')
    c.l(458, 222, 480, 222, TENUE, 1.2, '4 3')
    c.l(480, 93, 480, 222, TENUE, 1.2, '4 3')
    c.raw(f'<rect x="480" y="128" width="64" height="58" rx="6" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    c.t(512, 150, 'registro', 8.5, TINTA, 'middle', 700)
    c.t(512, 162, 'P · V', 8.5, TINTA, 'middle', 700)
    c.t(512, 175, '(→ curva)', 8, TENUE, 'middle')
    c.l(480, 157, 462, 157, TENUE, 1.2)
    # B: vista de frente de las narinas
    c.t(540, 20, 'B · Narinas, de frente', 10.5, TINTA, 'start', 700)
    c.raw(f'<path d="M598,92 Q612,60 628,92 Q650,150 676,196 Q640,214 612,206 Q584,214 548,196 Q574,150 598,92 z" '
          f'fill="none" stroke="{TINTA}" stroke-width="1.6"/>')
    c.raw(f'<ellipse cx="590" cy="196" rx="12" ry="7" fill="none" stroke="{DER}" stroke-width="2.4" '
          f'transform="rotate(-18 590 196)"/>')
    c.raw(f'<ellipse cx="634" cy="196" rx="12" ry="7" fill="{IZQ}33" stroke="{IZQ}" stroke-width="2.4" '
          f'transform="rotate(18 634 196)"/>')
    c.poli([(634, 204), (634, 250), (600, 280), (560, 286)], IZQ, 1.8)
    c.t(590, 226, 'D', 9, DER, 'middle', 700)
    c.t(634, 226, 'I', 9, IZQ, 'middle', 700)
    c.t(612, 308, 'Mides la derecha: el tubo de presión', 8, TENUE, 'middle')
    c.t(612, 320, 'va en la izquierda (adaptador).', 8, TENUE, 'middle')
    c.guardar('h26-montaje.svg', punta('p-aire', TENUE))


# ------------------------------------------------------------------ curvas
def curvas():
    c = Lienzo(700, 385)
    # Panel A: cuatro cuadrantes
    cx, cy, ax, ay = 215, 190, 175, 140        # centro y semiejes en px
    PX, VY = 300.0, 1000.0
    X = lambda p: cx + p / PX * ax
    Y = lambda v: cy - v / VY * ay
    c.t(14, 20, 'A · Curva presión-flujo, fosa por fosa', 10.5, TINTA, 'start', 700)
    for p in (-300, -200, -100, 100, 200, 300):
        c.l(X(p), Y(-1000), X(p), Y(1000), GRILLA, 0.6)
    for v in (-1000, -500, 500, 1000):
        c.l(X(-300), Y(v), X(300), Y(v), GRILLA, 0.6)
    c.l(X(-300), cy, X(300), cy, FUERTE, 1.2)
    c.l(cx, Y(1000), cx, Y(-1000), FUERTE, 1.2)
    for p in (-300, -150, 150, 300):
        c.t(X(p), cy + 12, abs(p), 8, TENUE)
    for v in (500, 1000):
        c.t(cx - 5, Y(v) + 3, v, 8, TENUE, 'end')
        c.t(cx - 5, Y(-v) + 3, v, 8, TENUE, 'end')
    c.t(X(300), cy + 24, 'presión (Pa)', 8.5, TENUE, 'end')
    c.t(cx + 6, Y(1000) - 6, 'flujo (cm³/s)', 8.5, TENUE, 'start')
    for q, (x, y) in zip(('I', 'II', 'III', 'IV'), ((1, 1), (-1, 1), (-1, -1), (1, -1))):
        c.t(cx + x * 92, cy - y * 22 + 4, q, 11, TENUE, 'middle', 700)
    # 150 Pa
    for s in (1, -1):
        c.l(X(150 * s), Y(-1000), X(150 * s), Y(1000), TENUE, 1, '4 3')
    n = 60
    ptsD = [(X(p), Y(flujo(p, *DERECHA))) for p in [i * PX / n for i in range(n + 1)]]
    ptsD_e = [(X(-p), Y(-flujo(p, *DERECHA))) for p in [i * PX / n for i in range(n + 1)]]
    ptsI = [(X(-p), Y(flujo(p, *IZQUIERDA))) for p in [i * PX / n for i in range(n + 1)]]
    ptsI_e = [(X(p), Y(-flujo(p, *IZQUIERDA))) for p in [i * PX / n for i in range(n + 1)]]
    c.poli(ptsD, DER, 2.4)
    c.poli(ptsD_e, DER, 2.4, '6 3')
    c.poli(ptsI, IZQ, 2.4)
    c.poli(ptsI_e, IZQ, 2.4, '6 3')
    vd, vi = flujo(150, *DERECHA), flujo(150, *IZQUIERDA)
    c.l(cx, cy, X(150), Y(vd), DER, 1, '2 2')
    c.l(cx, cy, X(-150), Y(vi), IZQ, 1, '2 2')
    c.punto(X(150), Y(vd), DER)
    c.punto(X(-150), Y(vi), IZQ)
    c.t(X(150) + 8, Y(vd) + 14, f'{vd:.0f} cm³/s', 8.5, DER, 'start', 700)
    c.t(X(150) + 8, Y(vd) + 26, f'R = {150 / vd:.2f}'.replace('.', ','), 8.5, DER, 'start', 700)
    c.t(X(-150) - 8, Y(vi) + 14, f'{vi:.0f} cm³/s', 8.5, IZQ, 'end', 700)
    c.t(X(-150) - 8, Y(vi) + 26, f'R = {150 / vi:.2f}'.replace('.', ','), 8.5, IZQ, 'end', 700)
    c.t(X(150), Y(1000) + 12, '150 Pa', 8.5, TENUE, 'middle', 700)
    c.t(X(-150), Y(1000) + 12, '150 Pa', 8.5, TENUE, 'middle', 700)
    c.l(14, 365, 40, 365, TINTA, 2.2)
    c.t(46, 368, 'inspiración', 8.5, TINTA, 'start')
    c.l(112, 365, 138, 365, TINTA, 2.2, '6 3')
    c.t(144, 368, 'espiración', 8.5, TINTA, 'start')
    c.t(212, 368, '· fosa derecha en rojo, izquierda en azul', 8.5, TENUE, 'start')

    # Panel B: resistencia según la presión
    bx, by, bw, bh = 470, 52, 200, 230
    c.t(bx - 20, 20, 'B · La resistencia depende de la presión', 10.5, TINTA, 'start', 700)
    Rmax = 0.8
    XB = lambda p: bx + p / 300 * bw
    YB = lambda r: by + bh - r / Rmax * bh
    for r in (0.2, 0.4, 0.6, 0.8):
        c.l(bx, YB(r), bx + bw, YB(r), GRILLA, 0.6)
        c.t(bx - 6, YB(r) + 3, f'{r:.1f}'.replace('.', ','), 8, TENUE, 'end')
    c.l(bx, by + bh, bx + bw, by + bh, FUERTE, 1.2)
    c.l(bx, by, bx, by + bh, FUERTE, 1.2)
    for p in (0, 75, 150, 225, 300):
        c.t(XB(p), by + bh + 14, p, 8, TENUE)
    c.t(bx + bw / 2, by + bh + 28, 'presión (Pa)', 8.5, TENUE)
    c.t(bx - 6, by - 8, 'R (Pa/cm³/s)', 8.5, TENUE, 'end')
    for par, col, nombre in ((DERECHA, DER, 'derecha'), (IZQUIERDA, IZQ, 'izquierda')):
        pts = [(XB(p), YB(p / flujo(p, *par))) for p in [5 + i * 295 / 60 for i in range(61)]]
        c.poli(pts, col, 2.4)
        for pp in (75, 150):
            r = pp / flujo(pp, *par)
            c.punto(XB(pp), YB(r), col, 3.6)
            c.t(XB(pp), YB(r) - 8, f'{r:.2f}'.replace('.', ','), 8, col, 'middle', 700)
    c.l(XB(75), by, XB(75), by + bh, TENUE, 1, '4 3')
    c.l(XB(150), by, XB(150), by + bh, TENUE, 1, '4 3')
    c.t(bx + bw / 2, by + bh + 44, 'Una recta daría una resistencia fija;', 8, TENUE)
    c.t(bx + bw / 2, by + bh + 55, 'la curva real sube con la presión.', 8, TENUE)
    c.guardar('h26-curvas.svg')
    for par, n in ((DERECHA, 'derecha'), (IZQUIERDA, 'izquierda')):
        print(n, {p: round(p / flujo(p, *par), 3) for p in (75, 150)}, 'flujo', {p: round(flujo(p, *par)) for p in (75, 150)})


# ------------------------------------------------------------------ Broms
def broms():
    c = Lienzo(700, 345)
    ox, oy = 70, 305
    kx, ky = 0.95, 0.255      # px por Pa y por cm3/s (ejes a escala del equipo)
    X = lambda p: ox + p * kx
    Y = lambda v: oy - v * ky
    c.t(14, 20, 'El gráfico polar de Broms: la resistencia en un radio estándar', 10.5, TINTA, 'start', 700)
    c.l(ox, oy, ox + 330, oy, FUERTE, 1.2)
    c.l(ox, oy, ox, oy - 250, FUERTE, 1.2)
    c.t(ox + 330, oy + 30, 'presión (Pa) →', 8.5, TENUE, 'end')
    c.t(ox + 6, oy - 254, 'flujo (cm³/s)', 8.5, TENUE, 'start')
    for p in (100, 200, 300):
        c.l(X(p), oy, X(p), oy + 4, FUERTE, 1)
        c.t(X(p), oy + 15, p, 8, TENUE)
    for v in (250, 500, 750, 1000):
        c.l(ox - 4, Y(v), ox, Y(v), FUERTE, 1)
        c.t(ox - 7, Y(v) + 3, v, 8, TENUE, 'end')
    R = 205   # radio del círculo, en px
    # círculos concéntricos tenues
    for r in (80, 140):
        pts = [(ox + r * math.cos(t), oy - r * math.sin(t)) for t in [i * (math.pi / 2) / 50 for i in range(51)]]
        c.poli(pts, GRILLA, 1)
    pts = [(ox + R * math.cos(t), oy - R * math.sin(t)) for t in [i * (math.pi / 2) / 80 for i in range(81)]]
    c.poli(pts, TINTA, 1.4, '5 3')
    c.t(ox + 8, oy - R - 8, 'radio de referencia', 8.5, TINTA, 'start', 700)
    resultados = []
    for r150, col, nombre, dy in ((0.50, DER, 'nariz con más resistencia', 0), (0.25, IZQ, 'nariz con menos resistencia', 0)):
        a, b = params(r150)
        # P donde el punto (kx*P, ky*V) cae a distancia R del origen
        lo, hi = 1.0, 400.0
        for _ in range(60):
            m = (lo + hi) / 2
            d = math.hypot(m * kx, flujo(m, a, b) * ky)
            lo, hi = (m, hi) if d < R else (lo, m)
        P = lo
        V = flujo(P, a, b)
        pts = [(X(p), Y(flujo(p, a, b))) for p in [i * 330 / 80 for i in range(81)]]
        pts = [q for q in pts if q[1] > oy - 250]
        c.poli(pts, col, 2.4)
        c.l(ox, oy, X(P), Y(V), col, 1.2, '3 2')
        c.punto(X(P), Y(V), col)
        alfa = math.degrees(math.atan2(V * ky, P * kx))
        resultados.append((nombre, P, V, P / V, alfa))
    nom0, P0, V0, R0, al0 = resultados[0]
    nom1, P1, V1, R1, al1 = resultados[1]
    c.t(X(P0) + 10, Y(V0) + 4, f'{P0:.0f} Pa · {V0:.0f} cm³/s'.replace('.', ','), 8.5, DER, 'start', 700)
    c.t(X(P0) + 10, Y(V0) + 16, f'R = {R0:.2f} Pa/cm³/s'.replace('.', ','), 8.5, DER, 'start', 700)
    c.t(X(P1) + 22, Y(V1) + 24, f'{P1:.0f} Pa · {V1:.0f} cm³/s', 8.5, IZQ, 'start', 700)
    c.t(X(P1) + 22, Y(V1) + 36, f'R = {R1:.2f} Pa/cm³/s'.replace('.', ','), 8.5, IZQ, 'start', 700)
    # textos
    tx = 440
    c.t(tx, 70, 'Cómo se lee', 10, TINTA, 'start', 700)
    for i, s in enumerate(['1. La curva se traza P contra V, sin tiempo.',
                           '2. El equipo dibuja un círculo de radio fijo',
                           '    centrado en el origen.',
                           '3. Donde el círculo corta la curva hay un punto.',
                           '4. La resistencia de ese punto es P / V: la',
                           '    pendiente de la recta que va del origen',
                           '    al punto. Más empinada, menos resistencia.',
                           '5. El mismo radio para todos: dos narices se',
                           '    comparan en una misma "distancia" del',
                           '    origen, aunque el punto caiga a otra presión.']):
        c.t(tx, 90 + i * 14, s, 8.5, TINTA, 'start')
    c.t(tx, 250, 'Las dos curvas: R a 150 Pa de 0,50 y 0,25.', 8, TENUE, 'start')
    c.t(tx, 262, 'Los ejes se dibujan a la escala del equipo;', 8, TENUE, 'start')
    c.t(tx, 274, 'el valor numérico del radio estándar depende de ella.', 8, TENUE, 'start')
    c.guardar('h26-broms.svg')
    for r in resultados:
        print(r)


# ------------------------------------------------------------------ vasoconstrictor
def vasoconstrictor():
    c = Lienzo(700, 320)
    casos = [('Vasomotora', 250, 400, 'baja hasta la referencia'),
             ('Mixta', 250, 330, 'baja, pero no llega'),
             ('Mecánica', 250, 255, 'casi no cambia')]
    ancho, alto = 180, 170
    c.t(14, 20, 'La misma fosa, antes y después del vasoconstrictor (inspiración)', 10.5, TINTA, 'start', 700)
    for i, (nombre, v0, v1, frase) in enumerate(casos):
        x0 = 50 + i * 218
        y0 = 62
        XP = lambda p: x0 + p / 250 * ancho
        YV = lambda v: y0 + alto - v / 700 * alto
        c.t(x0 + ancho / 2, y0 - 20, f'{nombre}', 10, TINTA, 'middle', 700)
        for p in (0, 75, 150, 250):
            c.l(XP(p), y0, XP(p), y0 + alto, GRILLA, 0.6)
            c.t(XP(p), y0 + alto + 13, p, 8, TENUE)
        for v in (0, 200, 400, 600):
            c.l(x0, YV(v), x0 + ancho, YV(v), GRILLA, 0.6)
            if i == 0:
                c.t(x0 - 5, YV(v) + 3, v, 8, TENUE, 'end')
        c.l(x0, y0 + alto, x0 + ancho, y0 + alto, FUERTE, 1.2)
        c.l(x0, y0, x0, y0 + alto, FUERTE, 1.2)
        c.t(x0 + ancho / 2, y0 + alto + 27, 'presión (Pa)', 8.5, TENUE)
        if i == 0:
            c.t(x0 - 4, y0 - 8, 'flujo (cm³/s)', 8.5, TENUE, 'start')
        # línea de la referencia (R = 0,4): V = P / 0,4
        ref = [(XP(p), YV(p / 0.4)) for p in (0, 250) if p / 0.4 <= 700]
        c.l(XP(0), YV(0), XP(250), YV(min(250 / 0.4, 700)), TENUE, 1.2, '5 3')
        c.l(XP(150), y0, XP(150), y0 + alto, TENUE, 1, '4 3')
        for v150, col in ((v0, AVISO), (v1, RETRO)):
            r150 = 150 / v150
            a, b = params(r150)
            pts = [(XP(p), YV(flujo(p, a, b))) for p in [j * 250 / 60 for j in range(61)]]
            pts = [q for q in pts if q[1] >= y0]
            c.poli(pts, col, 2.4)
            c.punto(XP(150), YV(v150), col)
            c.t(XP(150) + 7, YV(v150) + (14 if col == AVISO else -14), f'{v150} → R {r150:.2f}'.replace('.', ','), 8.5, col, 'start', 700, extra=' stroke="#fff" stroke-width="3" paint-order="stroke"')
        c.t(x0 + ancho / 2, y0 + alto + 44, frase, 9, TINTA, 'middle', 600)
    c.l(14, 300, 34, 300, AVISO, 2.4)
    c.t(40, 303, 'antes (reposo)', 8.5, TINTA, 'start')
    c.l(120, 300, 140, 300, RETRO, 2.4)
    c.t(146, 303, 'después (PVC)', 8.5, TINTA, 'start')
    c.l(226, 300, 246, 300, TENUE, 1.4, '5 3')
    c.t(252, 303, 'recta de la resistencia de referencia (0,4 Pa/cm³/s)', 8.5, TENUE, 'start')
    c.guardar('h26-vasoconstrictor.svg')


if __name__ == '__main__':
    montaje()
    curvas()
    broms()
    vasoconstrictor()
