#!/usr/bin/env python3
"""Dibuja las figuras de las pruebas de H15 (Procesamiento auditivo central) que
reemplazan a las capturas de pantalla de un programa de evaluación:

    h15-patrones.svg         cómo se arma un patrón de frecuencia y uno de duración (esquema)
    h15-dicotico-oidos.svg   el total esconde la asimetría: dos pacientes con el mismo total
    h15-matrix.svg           la matriz de palabras y el recorrido adaptativo del SNR
    h15-patron-resultado.svg lo que se lee de una sesión de patrón de duración

Esquemas propios, no IA. Los resultados son INVENTADOS para el libro: no son
normas ni salen de ningún paciente. El recorrido adaptativo del Matrix es una
simulación con una regla de pasos genérica (cada versión trae la suya).

    python3 docs/libro/ilustraciones/hacer_h15_simulador.py
"""
import math
import pathlib
import random

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
OD, OI, ACENTO, BIEN, AVISO = '#c62f3a', '#2a62b4', '#5b4f72', '#21796c', '#c62f3a'
FONDO = '#f6f4ef'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
MONO = "font-family=\"'JetBrains Mono', 'DejaVu Sans Mono', monospace\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400, mono=False):
        fam = MONO if mono else F
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {fam} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}/>')

    def r(self, x, y, w, h, fill, stroke='none', sw=1, rx=4):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def c(self, x, y, rad, fill, stroke='none', sw=1.5):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def poli(self, pts, color, w=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}"{d} '
                        f'stroke-linejoin="round"/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


# ---------------------------------------------------------------- patrones
def patrones():
    c = Lienzo(700, 330)
    c.t(14, 20, 'Tres tonos, dos posibilidades: lo que cambia es el orden', 10.5, TINTA, 'start', 700)

    def panel(x0, titulo, sub, tonos, letras, nota, eje_frecuencia=True):
        c.t(x0, 46, titulo, 9.5, ACENTO, 'start', 700)
        c.t(x0, 62, sub, 7.8, TENUE, 'start')
        yb, ya = 150, 100           # alto de un tono grave y agudo
        c.l(x0, 172, x0 + 300, 172, FUERTE, 1)
        c.t(x0 + 300, 186, 'tiempo', 7.5, TENUE, 'end')
        c.l(x0, 172, x0, 80, FUERTE, 1)
        if eje_frecuencia:
            c.t(x0 - 4, 100, 'agudo', 7.5, TENUE, 'end')
            c.t(x0 - 4, 154, 'grave', 7.5, TENUE, 'end')
        x = x0 + 20
        for (largo, agudo), le in zip(tonos, letras):
            w = 78 if largo else 34
            y = ya if agudo else yb
            c.r(x, y - 9, w, 18, '#efeaf5', ACENTO, 1.5, 3)
            c.t(x + w / 2, 202, le, 11, ACENTO, 'middle', 700, mono=True)
            x += w + 24
        c.t(x0, 228, nota, 7.8, TINTA, 'start')

    panel(70, 'A · Patrón de frecuencia', 'mismo largo, dos tonos', [(0, 0), (0, 1), (0, 0)], 'GAG',
          'el paciente dice: «grave, agudo, grave»')
    panel(400, 'B · Patrón de duración', 'mismo tono, dos largos', [(1, 0), (0, 0), (1, 0)], 'LCL',
          'el paciente dice: «largo, corto, largo»', eje_frecuencia=False)

    c.l(14, 250, 686, 250, GRILLA, 1)
    c.t(14, 270, 'Las seis secuencias (sin las dos que repiten el mismo tono):', 8.5, TINTA, 'start', 700)
    for i, s in enumerate(['GGA', 'GAG', 'AGG', 'AAG', 'AGA', 'GAA']):
        c.r(14 + i * 60, 280, 52, 22, FONDO, FUERTE, 1, 3)
        c.t(40 + i * 60, 296, s, 9, TINTA, 'middle', 700, mono=True)
    c.t(400, 272, 'Dos errores distintos sobre GAG:', 8.5, TINTA, 'start', 700)
    c.t(400, 290, 'GGA → cambio de lugar («dónde»)', 8, AVISO, 'start', 400, mono=False)
    c.t(400, 306, 'AGA → inversión de todo («qué»)', 8, AVISO, 'start')
    c.t(14, 324, 'G: grave; A: agudo; L: largo; C: corto. Frecuencias, duraciones y pausas son las de cada versión.',
        7.3, TENUE, 'start')
    c.guardar('h15-patrones.svg')


# ---------------------------------------------------------------- dicótico
def dicotico():
    c = Lienzo(700, 316)
    c.t(14, 20, 'Mismo total, dos resultados distintos', 10.5, TINTA, 'start', 700)
    pacientes = [('Paciente 1', 80, 76), ('Paciente 2', 96, 60)]
    y0, y1 = 60, 220                # eje de 0 a 100 %
    p2y = lambda p: y1 - (y1 - y0) * p / 100
    for i, (nom, od, oi) in enumerate(pacientes):
        x0 = 60 + i * 330
        for p in range(0, 101, 25):
            c.l(x0, p2y(p), x0 + 250, p2y(p), GRILLA, 1)
            c.t(x0 - 6, p2y(p) + 3, f'{p}', 7.5, TENUE, 'end')
        c.t(x0 + 125, 46, nom, 9.5, TINTA, 'middle', 700)
        for j, (val, col, et) in enumerate([(od, OD, 'OD'), (oi, OI, 'OI')]):
            bx = x0 + 30 + j * 110
            c.r(bx, p2y(val), 70, y1 - p2y(val), col, rx=2)
            c.t(bx + 35, p2y(val) - 6, f'{val} %', 9, col, 'middle', 700)
            c.t(bx + 35, y1 + 16, et, 9, col, 'middle', 700)
        tot = (od + oi) / 2
        c.l(x0 + 10, p2y(tot), x0 + 240, p2y(tot), TINTA, 1.2, '5 3')
        c.t(x0 + 248, p2y(tot) + 3, f'total {tot:.0f} %', 7.5, TINTA, 'start', 700)
        c.t(x0 + 125, y1 + 36, f'diferencia OD − OI: {od - oi} puntos', 8.5,
            AVISO if od - oi > 10 else TINTA, 'middle', 700)
    c.t(14, 286, 'Aciertos por oído en recuerdo libre. El total es el mismo (78 %); solo el resultado por oído muestra la asimetría.',
        8, TINTA, 'start')
    c.guardar('h15-dicotico-oidos.svg')


# ---------------------------------------------------------------- matrix
PALABRAS = [
    ['Luis', 'Ana', 'Pedro', 'María', 'Juan'],
    ['compra', 'vende', 'trae', 'tiene', 'regala'],
    ['dos', 'tres', 'cuatro', 'cinco', 'seis'],
    ['coches', 'anillos', 'vasos', 'libros', 'platos'],
    ['rojos', 'verdes', 'nuevos', 'viejos', 'grandes'],
]
FRASE = [1, 0, 1, 3, 0]   # «Ana compra tres libros rojos»


def recorrido(n=20, srt=-7.0, pendiente=0.15, semilla=14):
    """Simula un oyente con función psicométrica logística y una regla adaptativa
    genérica: el paso depende de cuántas de las 5 palabras acertó y se achica
    con cada cambio de dirección. Datos inventados."""
    azar = random.Random(semilla)
    snr, pasos, puntos = 0.0, [3.0, 2.0, 1.5, 1.0], []
    k, ultimo_signo = 0, 0
    for _ in range(n):
        p = 1 / (1 + math.exp(-4 * pendiente * (snr - srt)))
        aciertos = sum(azar.random() < p for _ in range(5))
        puntos.append((snr, aciertos))
        signo = -1 if aciertos >= 3 else 1
        if ultimo_signo and signo != ultimo_signo:
            k = min(k + 1, len(pasos) - 1)
        ultimo_signo = signo
        snr += signo * pasos[k] * (abs(aciertos - 2.5) / 2.5 + 0.4)
        snr = round(snr * 2) / 2
    return puntos


def matrix():
    c = Lienzo(700, 470)
    c.t(14, 20, 'Matrix: una palabra de cada columna, el SNR se ajusta frase a frase', 10.5, TINTA, 'start', 700)
    # A: la matriz
    c.t(14, 46, 'A · La matriz (cinco de las diez palabras de cada columna)', 9, ACENTO, 'start', 700)
    cols = ['nombre', 'verbo', 'número', 'objeto', 'adjetivo']
    xs = [70 + i * 130 for i in range(5)]
    c.poli([(xs[i], 88 + FRASE[i] * 20 - 4) for i in range(5)], ACENTO, 1, '3 3')
    for i, (col, x) in enumerate(zip(cols, xs)):
        c.t(x, 68, col.upper(), 7.5, TENUE, 'middle', 700)
        for j, pal in enumerate(PALABRAS[i]):
            y = 88 + j * 20
            if FRASE[i] == j:
                c.r(x - 40, y - 13, 80, 18, '#efeaf5', ACENTO, 1.2, 3)
                c.t(x, y, pal, 9, ACENTO, 'middle', 700)
            else:
                c.t(x, y, pal, 9, TENUE)
    c.t(350, 196, 'una frase: «Ana compra tres libros rojos». Gramatical, pero imposible de adivinar por el contexto.',
        8, TINTA)

    # B: el recorrido adaptativo
    c.t(14, 228, 'B · El recorrido del SNR en una lista de 20 frases', 9, ACENTO, 'start', 700)
    pts = recorrido()
    x0, x1, y0, y1 = 70, 660, 246, 410
    smin, smax = -14, 4
    s2y = lambda s: y0 + (smax - s) / (smax - smin) * (y1 - y0)
    i2x = lambda i: x0 + 18 + i * (x1 - x0 - 18) / (len(pts) - 1)
    for s in range(smin, smax + 1, 2):
        c.l(x0, s2y(s), x1, s2y(s), GRILLA if s else FUERTE, 1)
        c.t(x0 - 6, s2y(s) + 3, f'{s:+d}'.replace('+0', '0').replace('-', '−'), 7.5, TENUE, 'end')
    c.t(24, (y0 + y1) / 2 - 8, 'SNR', 8, TENUE, 'middle', 700)
    c.t(24, (y0 + y1) / 2 + 6, '(dB)', 7.5, TENUE)
    ultimos = [s for s, _ in pts[-10:]]
    srt = sum(ultimos) / len(ultimos)
    c.l(i2x(10), s2y(srt), x1, s2y(srt), BIEN, 1.5, '6 3')
    c.t(i2x(10), s2y(srt) + 24, f'SRT ≈ {srt:.1f} dB'.replace('-', '−').replace('.', ','), 8.5, BIEN, 'start', 700)
    c.poli([(i2x(i), s2y(s)) for i, (s, _) in enumerate(pts)], FUERTE, 1.2)
    for i, (s, a) in enumerate(pts):
        col = TINTA if a >= 3 else AVISO
        c.c(i2x(i), s2y(s), 8, '#fff', col, 1.5)
        c.t(i2x(i), s2y(s) + 3.5, str(a), 7, col, 'middle', 700)
        if i % 2 == 0 or i == len(pts) - 1:
            c.t(i2x(i), y1 + 16, str(i + 1), 7.5, TENUE)
    c.t((x0 + x1) / 2, y1 + 32, 'frase', 8, TENUE)
    c.t(14, 458, 'En cada círculo, cuántas de las cinco palabras acertó: 3 o más baja el SNR; menos de 3 lo sube (en rojo).', 7.5, TENUE, 'start')
    c.guardar('h15-matrix.svg')


# ---------------------------------------------------------------- patrón de duración: resultado
SESION = [  # (presentado, respondido) de 30 ítems inventados
    ('LCC', 'LCC'), ('LCL', 'LCL'), ('CLL', 'CLL'), ('LLC', 'LLC'), ('CCL', 'CCL'), ('CLC', 'CLC'),
    ('LCL', 'LLC'), ('LLC', 'LLC'), ('CCL', 'CCL'), ('CLL', 'CLL'), ('LLC', 'LCL'), ('CLC', 'CLC'),
    ('LCC', 'LCC'), ('CCL', 'CLC'), ('CLL', 'CLL'), ('LCL', 'LCL'), ('CLC', 'CCL'), ('LLC', 'LLC'),
    ('CLL', 'LCL'), ('LCC', 'LCC'), ('CCL', 'CCL'), ('LCL', 'LLC'), ('CLC', 'CLC'), ('LLC', 'LLC'),
    ('CLL', 'CLL'), ('LCC', 'LCL'), ('CCL', 'CCL'), ('CLC', 'CLC'), ('LCL', 'LCL'), ('LLC', 'LLC'),
]


def patron_resultado():
    c = Lienzo(700, 420)
    aciertos = sum(p == r for p, r in SESION)
    c.t(14, 20, f'Patrón de duración, una sesión: {aciertos} de {len(SESION)} ({100 * aciertos / len(SESION):.0f} %)',
        10.5, TINTA, 'start', 700)
    # A: ítem por ítem
    c.t(14, 46, 'A · Ítem por ítem: lo presentado y, si falló, lo respondido', 9, ACENTO, 'start', 700)
    for i, (p, r) in enumerate(SESION):
        fila, col = divmod(i, 6)
        x, y = 14 + col * 112, 58 + fila * 30
        ok = p == r
        c.r(x, y, 104, 24, '#fff' if ok else '#fbe9e6', FUERTE if ok else AVISO, 1, 3)
        c.t(x + 12, y + 16, str(i + 1), 7, TENUE, 'middle')
        txt = p if ok else f'{p}→{r}'
        c.t(x + 60, y + 16, txt, 8.5, TINTA if ok else AVISO, 'middle', 700, mono=True)
    # B: acierto por posición
    yb = 236
    c.t(14, yb, 'B · Acierto por posición', 9, ACENTO, 'start', 700)
    por_pos = [sum(p[k] == r[k] for p, r in SESION) for k in range(3)]
    for k, n in enumerate(por_pos):
        y = yb + 22 + k * 30
        pct = 100 * n / len(SESION)
        c.t(14, y + 12, f'{k + 1}.º tono', 8.5, TINTA, 'start')
        c.r(80, y, 220, 16, GRILLA, rx=3)
        c.r(80, y, 220 * pct / 100, 16, BIEN if pct >= 90 else AVISO, rx=3)
        c.t(308, y + 12, f'{pct:.0f} % ({n}/{len(SESION)})', 8.5, TINTA, 'start', 700)
    # C: confusiones
    c.t(420, yb, 'C · Qué confunde', 9, ACENTO, 'start', 700)
    lc = sum(p[k] == 'L' and r[k] == 'C' for p, r in SESION for k in range(3))
    cl = sum(p[k] == 'C' and r[k] == 'L' for p, r in SESION for k in range(3))
    cambia_lugar = sum(1 for p, r in SESION if p != r and sorted(p) == sorted(r))
    c.t(420, yb + 34, f'largo oído como corto: {lc}', 8.5, TINTA, 'start')
    c.t(420, yb + 56, f'corto oído como largo: {cl}', 8.5, TINTA, 'start')
    c.t(420, yb + 78, f'mismos tonos en otro orden: {cambia_lugar} de {len(SESION) - aciertos} errores', 8.5, TINTA, 'start')
    c.t(14, 372, f'Falla en el segundo y el tercer tono, y en {cambia_lugar} de los {len(SESION) - aciertos} errores dijo los mismos tonos en otro orden:',
        8, TINTA, 'start')
    c.t(14, 388, 'distingue el largo del corto, pero no los ordena. El total solo no lo dice.', 8, TINTA, 'start')
    c.t(14, 410, 'L: largo; C: corto.', 7.5, TENUE, 'start')
    c.guardar('h15-patron-resultado.svg')


if __name__ == '__main__':
    patrones()
    dicotico()
    matrix()
    patron_resultado()
