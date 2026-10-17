#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H17 (vHIT):

    h17-trazas.svg   velocidad de cabeza y de ojo (invertida): normal, sacada encubierta, sacada manifiesta
    h17-ganancia.svg la misma traza leída con tres métodos de ganancia (área, a 60 ms, regresión)
    h17-ewald.svg    A: respuesta de las aferentes de cada canal; B: ganancia según la velocidad del impulso

SVG propios, no IA. Son esquemas con la misma lógica del generador sintético de trainHIT
(js/ejemplo.js: velocidad de cabeza gaussiana, ojo = ganancia x cabeza, y una sacada que devuelve la
mirada al blanco), recalculados a 1 kHz y sin ruido. Las cifras son de ejemplo, no de un paciente ni
normas: las constantes (pico 200 °/s, latencia del reflejo 8 ms) se eligieron con los órdenes de
magnitud de Halmagyi y cols. (2017)."""
import math
import pathlib

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
CABEZA, OJO, AVISO, OK = '#2a6fc2', '#c0571c', '#c62f3a', '#21796c'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2

PICO, SIGMA, CENTRO, LATENCIA = 200.0, 28.0, 70.0, 8.0     # °/s, ms, ms, ms
AMPLITUD = PICO * SIGMA / 1000 * math.sqrt(2 * math.pi)    # grados que gira la cabeza


def cabeza(t):
    return PICO * math.exp(-((t - CENTRO) ** 2) / (2 * SIGMA ** 2))


def pos_cabeza(t):
    return AMPLITUD * 0.5 * (1 + math.erf((t - CENTRO) / (SIGMA * math.sqrt(2))))


def gauss(t, t0, area, sigma=10.0):
    """Sacada: pulso gaussiano de velocidad cuya área (grados) es el error que corrige."""
    return area / (sigma / 1000 * math.sqrt(2 * math.pi)) * math.exp(-((t - t0) ** 2) / (2 * sigma ** 2))


def ojo(t, g, sacada=None):
    v = g * cabeza(t - LATENCIA)
    if sacada == 'encubierta':
        t0 = 112.0
        v += gauss(t, t0, (1 - g) * pos_cabeza(t0))
    elif sacada == 'manifiesta':
        v += gauss(t, 280.0, (1 - g) * AMPLITUD)
    return v


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                        f'stroke-width="{w}"{d}/>')

    def poli(self, pts, color, w=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def area(self, pts, color, op=0.22):
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polygon points="{p}" fill="{color}" fill-opacity="{op}" stroke="none"/>')

    def punto(self, x, y, color, r=3.6):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


class Ejes:
    """Un panel con ejes: x en [x0,x1], y en [y0,y1]."""
    def __init__(self, c, px, py, w, h, x0, x1, y0, y1):
        self.c, self.px, self.py, self.w, self.h = c, px, py, w, h
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1

    def X(self, x):
        return self.px + (x - self.x0) / (self.x1 - self.x0) * self.w

    def Y(self, y):
        return self.py + self.h - (y - self.y0) / (self.y1 - self.y0) * self.h

    def marco(self, xt, yt, xlab, ylab=None, y_en_cero=True):
        c = self.c
        for y in yt:
            c.l(self.px, self.Y(y), self.px + self.w, self.Y(y), GRILLA, 1)
            c.t(self.px - 5, self.Y(y) + 3, f'{y:g}', 7.5, TENUE, 'end')
        for x in xt:
            c.l(self.X(x), self.py + self.h, self.X(x), self.py + self.h + 3, TENUE, 1)
            c.t(self.X(x), self.py + self.h + 13, f'{x:g}', 7.5, TENUE)
        c.l(self.px, self.py + self.h, self.px + self.w, self.py + self.h, FUERTE, 1)
        c.l(self.px, self.py, self.px, self.py + self.h, FUERTE, 1)
        c.t(self.px + self.w / 2, self.py + self.h + 26, xlab, 8, TENUE)
        if ylab:
            c.t(self.px - 26, self.py - 7, ylab, 8, TENUE, 'start')

    def curva(self, f, color, w=2, n=None, dash=None, desde=None, hasta=None):
        a = self.x0 if desde is None else desde
        b = self.x1 if hasta is None else hasta
        n = n or 240
        pts = [(self.X(a + (b - a) * i / n), self.Y(f(a + (b - a) * i / n))) for i in range(n + 1)]
        self.c.poli(pts, color, w, dash)


def trazas():
    c = Lienzo(720, 310)
    c.t(14, 18, 'Velocidad de la cabeza y del ojo en un impulso (la traza del ojo va invertida: si compensa, se superpone)',
        10, TINTA, 'start', 700)
    paneles = [('A · Reflejo normal', 1.0, None, 'ganancia cerca de 1: el ojo copia a la cabeza'),
               ('B · Sacada encubierta', 0.5, 'encubierta', 'la sacada cae mientras la cabeza aún gira'),
               ('C · Sacada manifiesta', 0.5, 'manifiesta', 'la sacada cae cuando la cabeza ya se detuvo')]
    for k, (tit, g, sac, nota) in enumerate(paneles):
        e = Ejes(c, 50 + k * 233, 62, 190, 150, 0, 400, 0, 320)
        c.t(e.px, 44, tit, 9.5, TINTA, 'start', 700)
        e.marco([0, 100, 200, 300, 400], [0, 100, 200, 300], 'tiempo desde el inicio del impulso (ms)', '°/s' if k == 0 else None)
        e.curva(cabeza, CABEZA, 2.2, 400)
        e.curva(lambda t: ojo(t, g, sac), OJO, 2.2, 800)
        c.t(e.px, 258, nota, 8, TINTA, 'start')
        if sac == 'encubierta':
            c.t(e.X(112) + 6, e.Y(ojo(112, g, sac)) - 6, 'sacada', 8, AVISO, 'start', 700)
            c.t(e.px, 271, 'encubierta: dentro del impulso', 8, AVISO, 'start')
        if sac == 'manifiesta':
            c.t(e.X(280) + 6, e.Y(ojo(280, g, sac)) - 6, 'sacada', 8, AVISO, 'start', 700)
            c.t(e.px, 271, 'manifiesta: después del impulso', 8, AVISO, 'start')
        if sac is None:
            c.t(e.px, 271, 'sin sacadas', 8, OK, 'start')
    # leyenda
    c.l(50, 297, 74, 297, CABEZA, 2.4)
    c.t(80, 300, 'cabeza', 8.5, TINTA, 'start')
    c.l(140, 297, 164, 297, OJO, 2.4)
    c.t(170, 300, 'ojo (invertido)', 8.5, TINTA, 'start')
    c.t(700, 300, 'Esquema con cifras de ejemplo, no datos de pacientes.', 7.5, TENUE, 'end')
    c.guardar('h17-trazas.svg')


def ganancia():
    g = 0.6
    t_fin = CENTRO + 2.1 * SIGMA                  # el impulso termina cuando la cabeza vuelve a cero
    ts = [i * 1.0 for i in range(0, 401)]
    ar_cab = sum(cabeza(t) for t in ts if t <= t_fin)
    ar_ojo = sum(ojo(t, g) for t in ts if t <= t_fin)
    g_area = ar_ojo / ar_cab
    g60 = ojo(60, g) / cabeza(60)
    # regresión: ojo contra cabeza en la subida (hasta el pico de la cabeza)
    sub = [t for t in ts if 20 <= t <= CENTRO]
    xs, ys = [cabeza(t) for t in sub], [ojo(t, g) for t in sub]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    g_reg = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    print(f'ganancia: area={g_area:.2f} 60ms={g60:.2f} regresion={g_reg:.2f}')

    c = Lienzo(720, 320)
    c.t(14, 18, 'Una misma traza, tres maneras de calcular la ganancia', 10, TINTA, 'start', 700)
    titulos = ['A · Área (ventana ancha)', 'B · Instantánea a 60 ms', 'C · Regresión (subida)']
    for k in range(3):
        px = 50 + k * 233
        c.t(px, 44, titulos[k], 9.5, TINTA, 'start', 700)
    # A y B comparten tipo de panel
    for k in (0, 1):
        e = Ejes(c, 50 + k * 233, 62, 190, 150, 0, 300, 0, 240)
        e.marco([0, 100, 200, 300], [0, 100, 200], 'tiempo (ms)', '°/s' if k == 0 else None)
        if k == 0:
            pc = [(e.X(t), e.Y(cabeza(t))) for t in range(0, int(t_fin) + 1)]
            po = [(e.X(t), e.Y(ojo(t, g))) for t in range(0, int(t_fin) + 1)]
            c.area(pc + [(e.X(t_fin), e.Y(0)), (e.X(0), e.Y(0))], CABEZA, 0.18)
            c.area(po + [(e.X(t_fin), e.Y(0)), (e.X(0), e.Y(0))], OJO, 0.30)
            c.l(e.X(t_fin), e.Y(0), e.X(t_fin), e.Y(235), TENUE, 1, '3 3')
            c.t(e.X(t_fin) + 4, e.Y(228), 'cabeza = 0', 7.5, TENUE, 'start')
        e.curva(cabeza, CABEZA, 2, 300)
        e.curva(lambda t: ojo(t, g), OJO, 2, 600)
        if k == 1:
            c.l(e.X(60), e.Y(0), e.X(60), e.Y(235), TINTA, 1, '3 3')
            c.punto(e.X(60), e.Y(cabeza(60)), CABEZA)
            c.punto(e.X(60), e.Y(ojo(60, g)), OJO)
            c.t(e.X(60) + 6, e.Y(235) + 8, '60 ms', 8, TINTA, 'start', 700)
            c.t(e.X(60) + 6, e.Y(ojo(60, g)) + 14, f'{ojo(60, g):.0f} / {cabeza(60):.0f}', 8, TINTA, 'start')
    c.t(50, 242 + 31, f'ojo ÷ cabeza = {g_area:.2f}'.replace('.', ','), 9, OJO, 'start', 700)
    c.t(50 + 233, 242 + 31, f'ojo ÷ cabeza = {g60:.2f}'.replace('.', ','), 9, OJO, 'start', 700)
    c.t(50, 242 + 43, 'cociente de las áreas, hasta el cruce por cero', 7.5, TENUE, 'start')
    c.t(50 + 233, 242 + 43, 'un solo instante: sensible al inicio y al ruido', 7.5, TENUE, 'start')
    # C: dispersión
    e = Ejes(c, 50 + 466, 62, 190, 150, 0, 220, 0, 220)
    e.marco([0, 100, 200], [0, 100, 200], 'velocidad de la cabeza (°/s)', 'ojo, °/s')
    for t in sub:
        c.punto(e.X(cabeza(t)), e.Y(ojo(t, g)), OJO, 2)
    e.curva(lambda x: my + g_reg * (x - mx), TINTA, 1.4, 20, '4 3', desde=30, hasta=205)
    c.t(50 + 466, 242 + 31, f'pendiente = {g_reg:.2f}'.replace('.', ','), 9, OJO, 'start', 700)
    c.t(50 + 466, 242 + 43, 'la recta que mejor une ojo y cabeza', 7.5, TENUE, 'start')
    c.t(700, 312, f'Reflejo de ganancia {g:.1f} con latencia de {LATENCIA:.0f} ms: la latencia hace que cada método lea algo distinto.'.replace('.', ','),
        7.5, TENUE, 'end')
    c.guardar('h17-ganancia.svg')


def ewald():
    c = Lienzo(720, 335)
    c.t(14, 18, 'Por qué el impulso hacia el lado enfermo muestra el déficit (ley de Ewald II)', 10, TINTA, 'start', 700)
    # A: tasa de descarga de las aferentes de cada canal
    b, k_exc, k_inh = 60.0, 0.50, 0.30            # reposo y pendientes (unidades arbitrarias, exc > inh)

    def izq(v):    # canal horizontal izquierdo: v > 0 = giro hacia la izquierda
        return b + k_exc * v if v >= 0 else max(0.0, b + k_inh * v)

    def der(v):
        return izq(-v)

    e = Ejes(c, 60, 62, 280, 170, -250, 250, 0, 200)
    c.t(e.px, 44, 'A · Descarga de las aferentes de cada canal', 9.5, TINTA, 'start', 700)
    e.marco([-200, -100, 0, 100, 200], [], 'velocidad de la cabeza (°/s)', None)
    c.l(e.px, e.Y(b), e.px + e.w, e.Y(b), GRILLA, 1, '4 3')
    c.t(e.px - 5, e.Y(b) + 3, 'reposo', 7.5, TENUE, 'end')
    c.t(e.px - 5, e.Y(0) + 3, '0', 7.5, TENUE, 'end')
    e.curva(izq, CABEZA, 2.4, 500)
    e.curva(der, OJO, 2.4, 500)
    c.t(e.X(150), e.Y(izq(150)) - 6, 'canal izquierdo', 8, CABEZA, 'middle', 700)
    c.t(e.X(-150), e.Y(der(-150)) - 6, 'canal derecho', 8, OJO, 'middle', 700)
    vc = -b / k_inh
    c.punto(e.X(vc), e.Y(0), AVISO)
    c.t(e.X(vc) + 8, e.Y(0) - 6, 'silencio total', 8, AVISO, 'start', 700)
    c.t(e.X(-180), e.Y(0) - 38, 'el canal izquierdo no', 7.5, TINTA, 'start')
    c.t(e.X(-180), e.Y(0) - 28, 'baja de cero', 7.5, TINTA, 'start')
    c.t(e.px + e.w / 2, 271, 'giro a la derecha  ←   → giro a la izquierda', 8, TENUE)
    c.t(e.px, 296, 'Excitar da más respuesta que inhibir (Ewald II), y a la inhibición le', 8, TINTA, 'start')
    c.t(e.px, 307, 'queda poco recorrido: el reposo es el piso. Esquema, sin unidades.', 8, TINTA, 'start')

    # B: ganancia según la velocidad del impulso, con el oído izquierdo dañado
    sat = 70.0                                       # tope del impulso hacia el lado enfermo (eje arbitrario)

    def sano(v):                                     # hacia el sano (derecha): casi completo
        return 0.9 * v

    def enfermo(v):                                  # hacia el enfermo: lo que aporta el oído sano antes de quedar en silencio
        return min(0.9 * v, sat) if v < 110 else sat - 0.12 * (v - 110)
    e2 = Ejes(c, 430, 62, 250, 170, 0, 300, 0, 300)
    c.t(e2.px, 44, 'B · Oído izquierdo dañado: lo que el ojo logra', 9.5, TINTA, 'start', 700)
    e2.marco([0, 100, 200, 300], [0, 100, 200, 300], 'velocidad del impulso (°/s)', 'ojo, °/s')
    e2.curva(lambda v: v, FUERTE, 1.4, 60, '4 3')
    c.t(e2.X(205), e2.Y(255), 'ganancia 1', 7.5, TENUE, 'start')
    e2.curva(sano, CABEZA, 2.4, 300)
    e2.curva(enfermo, AVISO, 2.4, 300)
    c.t(e2.X(300) - 2, e2.Y(sano(300)) + 18, 'hacia el oído sano', 8, CABEZA, 'end', 700)
    c.t(e2.X(300) - 2, e2.Y(enfermo(300)) + 16, 'hacia el oído dañado', 8, AVISO, 'end', 700)
    e2.curva(lambda v: 0, 'none', 1, 2)
    c.l(e2.X(110), e2.Y(0), e2.X(110), e2.Y(300), TENUE, 1, '3 3')
    c.t(e2.X(110) - 4, e2.Y(300) + 9, 'el oído sano', 7.5, TENUE, 'end')
    c.t(e2.X(110) - 4, e2.Y(300) + 18, 'queda en silencio', 7.5, TENUE, 'end')
    c.t(e2.px, 296, 'A baja velocidad el oído sano todavía alcanza a mover el ojo;', 8, TINTA, 'start')
    c.t(e2.px, 307, 'con un impulso rápido, ya no. Esquema, sin cifras clínicas.', 8, TINTA, 'start')
    c.guardar('h17-ewald.svg')


if __name__ == '__main__':
    trazas()
    ganancia()
    ewald()
