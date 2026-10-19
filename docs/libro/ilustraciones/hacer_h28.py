#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H28 (olfatometría):

    h28-via.svg           vía olfatoria esquemática: epitelio, lámina cribosa, bulbo, corteza; ortonasal y retronasal
    h28-transduccion.svg  transducción en un cilio: receptor, proteína G, AMPc, canal CNG y canal de cloro
    h28-pruebas.svg       las tres tareas psicofísicas (umbral, discriminación, identificación) y qué mide cada una
    h28-escalera.svg      procedimiento de umbral en escalera (3-AFC), CALCULADO con la regla de Oleszkiewicz y cols. (2019)
    h28-tdi.svg           tabla-ejemplo TDI con su clasificación y la diferencia mínima importante
    h28-edad.svg          TDI medio y percentil 10 por grupo de edad (Oleszkiewicz y cols., 2019), con el caso del ejemplo

SVG propios, no IA. La vía y la transducción son esquemas (las proporciones son ilustrativas).
Las cifras normativas salen de la tabla 1 de Oleszkiewicz y cols. (2019), todas las personas, ambos sexos.
La escalera se simula con la regla del artículo (dos aciertos seguidos bajan la concentración, un error la sube,
puntaje = promedio de las últimas cuatro inversiones) y un paciente de ejemplo con una función psicométrica
inventada: la secuencia de respuestas NO es un dato de un paciente real. Lo que se imprime al correrlo es lo
que aparece en el capítulo."""
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h25 import Lienzo as _L, TINTA, TENUE, GRILLA, FUERTE, AVISO, RETRO, COCLEAR, HUESO, MUCOSA, punta  # noqa: E402

AZUL = '#2d5f9a'
EPI = '#e0b83a'
SUAVE_R, SUAVE_C, SUAVE_A, SUAVE_G = '#e3f1ee', '#fbeadf', '#fbe3e4', '#f3f1ec'
AQUI = pathlib.Path(__file__).parent


class Lienzo(_L):
    def raw(self, s):
        self.out.append(s)

    def flecha(self, x1, y1, x2, y2, color=TINTA, w=1.6, dash=None, marca='pf'):
        self.l(x1, y1, x2, y2, color, w, dash, f' marker-end="url(#{marca})"')

    def curva(self, d, color=TINTA, w=1.8, marca='pf', dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{da} '
                        f'marker-end="url(#{marca})"/>')

    def num(self, x, y, n, color=TINTA):
        self.circ(x, y, 8.5, '#fff', color, 1.3)
        self.t(x, y + 3.4, str(n), 8.5, color, 'middle', 700)


DEFS = punta('pf', TINTA) + punta('pr', AVISO) + punta('pv', RETRO) + punta('pc', COCLEAR) + punta('pa', AZUL)


# ------------------------------------------------------------------ vía olfatoria
def via():
    c = Lienzo(760, 410)
    c.t(14, 20, 'Vía olfatoria (corte lateral esquemático, nariz a la izquierda)', 10, TINTA, 'start', 700)
    # encéfalo
    c.rect(200, 44, 540, 150, SUAVE_G, FUERTE, 1.4, 34)
    c.t(716, 62, 'encéfalo', 8.5, TENUE, 'end')
    # fosa nasal
    c.path('M70,300 C78,262 130,238 195,214 L342,212 L354,330 L140,324 C100,324 72,316 70,300 Z',
           MUCOSA, TINTA, 1.6)
    # lámina cribosa con orificios
    c.rect(205, 197, 140, 9, HUESO, TENUE, 1.2)
    xs = [225, 245, 265, 285, 305, 325]
    for x in xs:
        c.circ(x, 201.5, 2.6, '#fff', TENUE, 1)
    c.t(196, 205, 'lámina cribosa', 8.5, TINTA, 'end')
    # epitelio olfatorio y cilios
    c.l(212, 214, 338, 214, EPI, 7)
    for x in range(216, 338, 6):
        c.l(x, 218, x, 226, '#a8861c', 1)
    c.l(462, 247, 338, 219, TENUE, 1)
    c.t(468, 250, 'epitelio olfatorio', 9, TINTA, 'start', 700)
    c.t(468, 262, '(hendidura olfatoria, techo de la fosa)', 8, TENUE, 'start')
    # axones
    for x in xs:
        c.l(x, 212, x, 180, TINTA, 1.1)
    # bulbo
    c.elip(275, 168, 66, 22, '#e6dcf2', TINTA, 1.5)
    c.t(275, 162, 'bulbo olfatorio', 9, TINTA, 'middle', 700)
    for x in xs:
        c.circ(x, 180, 3.2, '#fff', TINTA, 1)
    c.l(222, 182, 188, 178, TENUE, 1)
    c.t(184, 176, 'glomérulos', 8.5, TINTA, 'end', 700)
    c.t(184, 188, '(1.ª sinapsis)', 8, TENUE, 'end')
    # tracto
    c.curva('M338,162 C385,150 420,146 452,138', TINTA, 2.4)
    c.t(352, 184, 'células mitrales y en penacho', 8.5, TINTA, 'start')
    c.t(352, 195, '(tracto olfatorio lateral)', 8, TENUE, 'start')
    # corteza primaria
    c.t(452, 78, 'corteza olfatoria primaria', 8.8, TINTA, 'start', 700)
    for k, nombre in enumerate(['corteza piriforme', 'amígdala (núcleo cortical)', 'corteza entorrinal']):
        y = 86 + k * 26
        c.rect(452, y, 150, 21, '#fff', TINTA, 1.2, 5)
        c.t(527, y + 14.5, nombre, 8.5, TINTA)
    c.flecha(602, 137, 626, 137, TINTA, 1.6)
    c.rect(628, 86, 104, 72, '#fff', TINTA, 1.2, 5)
    c.t(680, 102, 'áreas', 8.5, TINTA, 'middle', 700)
    c.t(680, 114, 'secundarias:', 8.5, TINTA, 'middle', 700)
    c.t(680, 128, 'orbitofrontal', 8.5, TINTA)
    c.t(680, 140, 'hipocampo', 8.5, TINTA)
    c.t(680, 152, 'ínsula', 8.5, TINTA)
    c.t(327, 62, 'sin relevo talámico obligatorio hacia la corteza primaria', 8, TENUE, 'middle')
    # flujos de aire
    c.curva('M16,292 C60,282 128,262 214,232', COCLEAR, 2.6, 'pc')
    c.t(16, 276, 'ortonasal', 9, COCLEAR, 'start', 700)
    c.t(16, 316, 'inspiración', 8, COCLEAR, 'start')
    c.t(16, 328, 'por la nariz', 8, COCLEAR, 'start')
    c.curva('M470,384 C420,372 372,340 332,238', RETRO, 2.6, 'pv')
    c.t(476, 378, 'retronasal', 9, RETRO, 'start', 700)
    c.t(476, 390, 'desde la boca y la faringe, al espirar o tragar', 8, RETRO, 'start')
    c.l(462, 322, 356, 322, TENUE, 1)
    c.t(468, 326, 'coana (hacia la nasofaringe)', 8.5, TINTA, 'start')
    c.l(86, 340, 100, 316, TENUE, 1)
    c.t(70, 352, 'narina', 8.5, TINTA, 'start')
    c.guardar('h28-via.svg', DEFS)


# ------------------------------------------------------------------ transducción
def transduccion():
    c = Lienzo(760, 400)
    c.t(14, 20, 'Transducción en el cilio de una neurona receptora olfatoria (esquema)', 10, TINTA, 'start', 700)
    # moco y citoplasma
    c.rect(40, 36, 680, 134, '#e8f0f8', 'none', 0, 6)
    c.rect(40, 210, 680, 122, '#f6efe3', 'none', 0, 6)
    c.t(52, 54, 'moco olfatorio', 9, AZUL, 'start', 700)
    c.t(52, 346, 'interior del cilio (citoplasma)', 9, '#8a6a2a', 'start', 700)
    # membrana
    c.rect(40, 170, 680, 40, '#fbf3cf', EPI, 1.6)
    c.t(52, 194, 'membrana', 8.5, '#8a6a2a', 'start')
    # odorante
    c.circ(150, 92, 9, COCLEAR, TINTA, 1.2)
    c.circ(166, 84, 6, COCLEAR, TINTA, 1.2)
    c.circ(138, 80, 5, COCLEAR, TINTA, 1.2)
    c.t(206, 90, 'molécula odorante', 9, COCLEAR, 'start', 700)
    c.flecha(150, 108, 158, 158, COCLEAR, 1.8, None, 'pc')
    c.num(120, 130, 1)
    # receptor
    c.rect(150, 160, 28, 58, '#d6e6f4', AZUL, 1.6, 10)
    for y in (172, 184, 196, 208):
        c.l(155, y, 173, y, AZUL, 1)
    c.t(186, 152, 'receptor', 8.5, AZUL, 'start', 700)
    # proteína G
    c.elip(176, 244, 36, 15, '#cfe6e1', RETRO, 1.6)
    c.t(176, 247, 'proteína G', 8.5, RETRO, 'middle', 700)
    c.flecha(178, 220, 178, 228, RETRO, 1.6, None, 'pv')
    c.num(128, 244, 2)
    # adenilil ciclasa
    c.rect(300, 160, 56, 58, '#fde2cc', COCLEAR, 1.6, 8)
    c.t(328, 185, 'adenilil', 8.5, COCLEAR, 'middle', 700)
    c.t(328, 197, 'ciclasa', 8.5, COCLEAR, 'middle', 700)
    c.flecha(214, 244, 300, 218, RETRO, 1.6, '5 3', 'pv')
    c.t(262, 252, 'activa', 8, RETRO, 'middle')
    # AMPc
    for dx, dy in ((0, 0), (16, 10), (-14, 14)):
        c.circ(330 + dx, 262 + dy, 6.5, '#fff', COCLEAR, 1.4)
    c.t(330, 296, 'AMPc', 9.5, COCLEAR, 'middle', 700)
    c.flecha(328, 220, 330, 250, COCLEAR, 1.6, None, 'pc')
    c.num(284, 262, 3)
    # canal CNG
    c.rect(470, 160, 44, 58, '#dfe9f5', AZUL, 1.6, 8)
    c.t(492, 184, 'canal', 8.5, AZUL, 'middle', 700)
    c.t(492, 196, 'CNG', 8.5, AZUL, 'middle', 700)
    c.flecha(356, 276, 478, 224, COCLEAR, 1.6, '5 3', 'pc')
    c.t(418, 270, 'se une y abre', 8, COCLEAR, 'middle')
    c.flecha(492, 106, 492, 158, AZUL, 2.2, None, 'pa')
    c.flecha(492, 220, 492, 272, AZUL, 2.2, None, 'pa')
    c.t(504, 100, 'entran cationes', 8.5, AZUL, 'start', 700)
    c.t(504, 112, '(entre ellos Ca²⁺)', 8.5, AZUL, 'start')
    c.num(446, 134, 4)
    # canal de cloro
    c.rect(606, 160, 68, 58, '#fbe3e4', AVISO, 1.6, 8)
    c.t(640, 182, 'canal Cl⁻', 8.5, AVISO, 'middle', 700)
    c.t(640, 194, 'activado', 8, AVISO, 'middle')
    c.t(640, 205, 'por Ca²⁺', 8, AVISO, 'middle')
    c.flecha(640, 272, 640, 222, AVISO, 2.2, None, 'pr')
    c.flecha(640, 158, 640, 106, AVISO, 2.2, None, 'pr')
    c.t(652, 100, 'sale Cl⁻', 8.5, AVISO, 'start', 700)
    c.curva('M520,246 C560,246 590,232 612,218', AZUL, 1.6, 'pa', '5 3')
    c.t(566, 262, 'el Ca²⁺ que entró', 8, AZUL, 'middle')
    c.num(600, 134, 5, AVISO)
    # resultado
    c.t(380, 372, 'Despolarización sumada → potencial de acción → axón hacia el bulbo', 9.5, TINTA, 'middle', 700)
    c.t(380, 388, 'La respuesta es transitoria: con estímulos prolongados o repetidos hay adaptación.', 8.5, TENUE, 'middle')
    c.guardar('h28-transduccion.svg', DEFS)


# ------------------------------------------------------------------ las tres pruebas
def boli(c, x, y, relleno='#fff', borde=TINTA):
    c.rect(x - 7, y, 14, 76, relleno, borde, 1.4, 4)
    c.rect(x - 8, y - 14, 16, 16, '#d9d4c8', borde, 1.2, 3)


def pruebas():
    c = Lienzo(760, 350)
    c.t(14, 20, 'Las tres tareas de la exploración psicofísica (elección forzada)', 10, TINTA, 'start', 700)
    paneles = [(14, 'U', 'Umbral (T)', 'Tres bolígrafos: uno con olor, dos con solvente.',
                '¿Cuál huele?', 'Sube o baja la concentración', 'puntaje 1 a 16'),
               (264, 'D', 'Discriminación (D)', 'Tres bolígrafos: dos iguales y uno distinto.',
                '¿Cuál es el distinto?', 'Olores bien por encima del umbral', 'puntaje 0 a 16'),
               (514, 'I', 'Identificación (I)', 'Un bolígrafo y cuatro opciones escritas.',
                '¿Qué olor es?', 'Olores familiares, elección múltiple', 'puntaje 0 a 16')]
    for x0, tipo, titulo, linea, preg, sub, punt in paneles:
        c.rect(x0, 34, 232, 232, '#fff', FUERTE, 1.2, 8)
        c.t(x0 + 116, 54, titulo, 10.5, TINTA, 'middle', 700)
        c.t(x0 + 116, 70, linea, 8, TENUE)
        if tipo == 'U':
            cols = ['#fff', '#fff', '#f4c27a']
            for k, col in enumerate(cols):
                boli(c, x0 + 56 + k * 60, 112, col)
            c.t(x0 + 56 + 60, 206, 'solvente', 8, TENUE)
            c.t(x0 + 56, 206, 'solvente', 8, TENUE)
            c.t(x0 + 56 + 120, 206, 'olor diluido', 8, COCLEAR, 'middle', 700)
        elif tipo == 'D':
            cols = ['#f4c27a', '#9ccfc6', '#f4c27a']
            for k, col in enumerate(cols):
                boli(c, x0 + 56 + k * 60, 112, col)
            c.t(x0 + 56, 206, 'olor A', 8, COCLEAR, 'middle', 700)
            c.t(x0 + 116, 206, 'olor B', 8, RETRO, 'middle', 700)
            c.t(x0 + 176, 206, 'olor A', 8, COCLEAR, 'middle', 700)
        else:
            boli(c, x0 + 52, 112, '#d6b8e6')
            for k, op in enumerate(['café', 'canela', 'ajo', 'pescado']):
                y = 112 + k * 24
                c.rect(x0 + 100, y, 112, 19, '#fff', TENUE, 1.1, 4)
                c.t(x0 + 156, y + 13.5, op, 8.5, TINTA)
            c.t(x0 + 52, 206, 'olor desconocido', 8, TENUE)
        c.t(x0 + 116, 232, preg, 9.5, TINTA, 'middle', 700)
        c.t(x0 + 116, 247, sub, 8, TENUE)
        c.t(x0 + 116, 260, punt, 8, TENUE)
    # suma
    c.rect(14, 280, 732, 56, SUAVE_G, 'none', 0, 8)
    c.t(380, 298, 'TDI = T + D + I   (1 a 48 puntos)', 10.5, TINTA, 'middle', 700)
    c.t(380, 314, 'T depende más del epitelio y de la vía periférica; D e I dependen más de la memoria y de la cognición.', 8.5, TINTA)
    c.t(380, 328, 'Por eso una misma enfermedad puede alterar más un subpuntaje que otro.', 8.5, TENUE)
    c.guardar('h28-pruebas.svg', DEFS)


# ------------------------------------------------------------------ escalera (calculada)
def conc(paso):
    """Concentración del paso (1 = 4 %), diluciones 1:2 sucesivas (16 pasos)."""
    return 4.0 / 2 ** (paso - 1)


def escalera_simulada(seed, m50, ancho):
    """Aplica la regla de Oleszkiewicz y cols. (2019): se empieza en el paso 16 (la más diluida) y se asciende en
    concentración hasta acertar; dos aciertos seguidos en un paso = inversión y se diluye un paso (paso + 1);
    un error = inversión (si se venía diluyendo) y se concentra un paso (paso - 1). Termina a la 7.ª inversión.
    Respuesta: probabilidad de acierto = 1/3 (azar) + 2/3 · logística centrada en m50."""
    rng = random.Random(seed)
    paso, direccion, seguidos = 16, 'sube', 0   # 'sube' = sube la concentración (baja el número de paso)
    ensayos, inversiones = [], []
    while len(inversiones) < 7 and len(ensayos) < 80:
        p = 1 / 3 + 2 / 3 / (1 + math.exp(-(m50 - paso) / ancho))
        ok = rng.random() < p
        ensayos.append((paso, ok))
        i = len(ensayos) - 1
        if ok:
            seguidos += 1
            if seguidos == 2:
                seguidos = 0
                if direccion == 'sube':
                    inversiones.append(i)
                    direccion = 'baja'
                paso = min(16, paso + 1)
        else:
            seguidos = 0
            if direccion == 'baja':
                inversiones.append(i)
                direccion = 'sube'
            paso = max(1, paso - 1)
    return ensayos, inversiones


def buscar_escalera(objetivo=4.5):
    for seed in range(1, 5000):
        ens, inv = escalera_simulada(seed, 5.2, 1.1)
        if len(inv) == 7 and 20 <= len(ens) <= 36:
            ult = [ens[i][0] for i in inv[-4:]]
            if sum(ult) / 4 == objetivo:
                return seed, ens, inv
    raise SystemExit('no se encontró una secuencia con el puntaje pedido')


def escalera():
    seed, ens, inv = buscar_escalera(4.5)
    n = len(ens)
    ult = inv[-4:]
    umbral = sum(ens[i][0] for i in ult) / 4
    c = Lienzo(760, 400)
    x0, y0, w, h = 82, 44, 590, 258
    c.t(14, 20, 'Umbral en escalera: 3 bolígrafos por paso, elección forzada (ejemplo calculado)', 10, TINTA, 'start', 700)
    ex = w / (n + 1)
    ey = h / 15
    # eje: paso 16 (más diluido) abajo, paso 1 (4 %) arriba
    yv = lambda paso: y0 + (paso - 1) * ey
    for p in range(1, 17):
        c.l(x0, yv(p), x0 + w, yv(p), GRILLA, 1)
        if p in (1, 4, 8, 12, 16):
            c.t(x0 - 8, yv(p) + 3.5, str(p), 8.5, TINTA, 'end')
            txt = f'{conc(p):.6f}'.rstrip('0').replace('.', ',')
            c.t(x0 + w + 6, yv(p) + 3.5, f'{txt} %', 8, TENUE, 'start')
    c.l(x0, y0 + h + 4, x0 + w, y0 + h + 4, TINTA, 1.2)
    c.l(x0, y0 - 4, x0, y0 + h + 4, TINTA, 1.2)
    for k in range(n):
        if (k + 1) % 5 == 0 or k == 0:
            c.t(x0 + (k + 1) * ex, y0 + h + 20, str(k + 1), 8.5)
    c.t(x0 + w / 2, y0 + h + 36, 'número de trío presentado (uno cada 20 s)', 9, TINTA)
    c.raw(f'<text x="22" y="{y0 + h / 2}" font-family="\'Plus Jakarta Sans\', sans-serif" font-size="10.8" '
          f'fill="{TINTA}" text-anchor="middle" transform="rotate(-90 22 {y0 + h / 2})">paso de dilución (1 = más concentrado)</text>')
    pts = [(x0 + (k + 1) * ex, yv(p)) for k, (p, ok) in enumerate(ens)]
    c.poli(pts, TENUE, 1.3)
    # marcas
    for k, (p, ok) in enumerate(ens):
        x, y = pts[k]
        if ok:
            c.circ(x, y, 4.2, RETRO, RETRO, 1)
        else:
            c.l(x - 3.6, y - 3.6, x + 3.6, y + 3.6, AVISO, 1.6)
            c.l(x - 3.6, y + 3.6, x + 3.6, y - 3.6, AVISO, 1.6)
    for k in inv:
        x, y = pts[k]
        usado = k in ult
        c.circ(x, y, 9, 'none', COCLEAR if usado else TENUE, 2.2 if usado else 1.3)
    # línea del umbral
    yu = y0 + (umbral - 1) * ey
    c.l(x0, yu, x0 + w, yu, COCLEAR, 1.6, '6 4')
    c.t(x0 + 8, yu - 6, f'umbral = {umbral:.2f}'.replace('.', ','), 9.5, COCLEAR, 'start', 700)
    # leyenda
    ly = 352
    c.circ(x0 + 8, ly, 4.2, RETRO, RETRO, 1)
    c.t(x0 + 18, ly + 3.5, 'acierto', 8.5, TINTA, 'start')
    c.l(x0 + 78, ly - 3.6, x0 + 85, ly + 3.6, AVISO, 1.6)
    c.l(x0 + 78, ly + 3.6, x0 + 85, ly - 3.6, AVISO, 1.6)
    c.t(x0 + 92, ly + 3.5, 'error', 8.5, TINTA, 'start')
    c.circ(x0 + 150, ly, 8, 'none', TENUE, 1.3)
    c.t(x0 + 163, ly + 3.5, 'inversión (7)', 8.5, TINTA, 'start')
    c.circ(x0 + 260, ly, 8, 'none', COCLEAR, 2.2)
    c.t(x0 + 273, ly + 3.5, 'últimas 4 inversiones: se promedian', 8.5, TINTA, 'start')
    c.t(x0, ly + 24, 'Regla: dos aciertos seguidos diluyen un paso; un error concentra un paso. La secuencia de respuestas es un ejemplo, no un paciente.',
        8, TENUE, 'start')
    c.guardar('h28-escalera.svg', DEFS)
    return seed, ens, inv, umbral


# ------------------------------------------------------------------ TDI
CORTES = [(0, 16, 'anosmia funcional', SUAVE_A, AVISO),
          (16.25, 30.5, 'hiposmia', SUAVE_C, COCLEAR),
          (30.75, 41.25, 'normosmia', SUAVE_R, RETRO),
          (41.5, 48, 'olfato superior', SUAVE_G, TENUE)]
T0, D0, I0 = 4.5, 10, 9           # ejemplo: primera evaluación
T1, D1, I1 = 6.0, 12, 11          # control a los 3 meses


def tdi():
    tdi0, tdi1 = T0 + D0 + I0, T1 + D1 + I1
    c = Lienzo(760, 400)
    c.t(14, 20, 'Puntaje TDI del ejemplo y su clasificación', 10, TINTA, 'start', 700)
    # tabla
    x0, y0 = 40, 40
    cols = [0, 150, 236, 322, 410]
    enc = ['Subprueba', 'Inicial', 'A los 3 meses', 'Máximo']
    filas = [('Umbral (T)', T0, T1, 16), ('Discriminación (D)', D0, D1, 16), ('Identificación (I)', I0, I1, 16),
             ('TDI = T + D + I', tdi0, tdi1, 48)]
    c.rect(x0, y0, 480, 28, SUAVE_G, FUERTE, 1.2)
    xs = [x0 + 10, x0 + 214, x0 + 306, x0 + 420]
    for x, e, a in zip(xs, enc, ['start', 'end', 'end', 'end']):
        c.t(x, y0 + 18, e, 9, TINTA, a, 700)
    for k, (nombre, a, b, m) in enumerate(filas):
        y = y0 + 28 + k * 28
        ultima = k == 3
        c.rect(x0, y, 480, 28, '#fff', FUERTE, 1.2)
        pes = 700 if ultima else 400
        c.t(xs[0], y + 18, nombre, 9, TINTA, 'start', pes)
        c.t(xs[1], y + 18, f'{a:g}'.replace('.', ','), 9.5, TINTA, 'end', pes)
        c.t(xs[2], y + 18, f'{b:g}'.replace('.', ','), 9.5, TINTA, 'end', pes)
        c.t(xs[3], y + 18, f'1 a {m}' if ultima else f'{m}', 9, TENUE, 'end')
    c.t(x0 + 500, y0 + 130, 'Cambio del TDI:', 9, TINTA, 'start', 700)
    c.t(x0 + 500, y0 + 144, f'{tdi1 - tdi0:+g}'.replace('.', ',').replace('+', '+') + ' puntos', 9.5, COCLEAR, 'start', 700)
    c.t(x0 + 500, y0 + 160, 'diferencia mínima', 8.5, TINTA, 'start')
    c.t(x0 + 500, y0 + 172, 'importante: 5,5', 8.5, TINTA, 'start')
    # escala
    sx0, sy, sw, sh = 40, 232, 680, 30
    ex = sw / 48
    for a, b, nombre, relleno, borde in CORTES:
        xa, xb = sx0 + a * ex, sx0 + b * ex
        c.rect(xa, sy, xb - xa, sh, relleno, borde, 1.2)
    c.t(sx0 + 8 * ex, sy + 19, 'anosmia funcional', 8.5, AVISO, 'middle', 700)
    c.t(sx0 + 23.4 * ex, sy + 19, 'hiposmia', 9, COCLEAR, 'middle', 700)
    c.t(sx0 + 36 * ex, sy + 19, 'normosmia', 9, RETRO, 'middle', 700)
    c.t(sx0 + 44.8 * ex, sy + 19, 'superior', 8.5, TENUE, 'middle', 700)
    for v in (0, 16, 30.75, 41.5, 48):
        c.l(sx0 + v * ex, sy + sh, sx0 + v * ex, sy + sh + 6, TINTA, 1.2)
        c.t(sx0 + v * ex, sy + sh + 19, f'{v:g}'.replace('.', ','), 8.5, TINTA)
    c.t(sx0 + sw / 2, sy + sh + 38, 'TDI (puntos). Cortes según adultos jóvenes sanos (Oleszkiewicz y cols., 2019)', 8.5, TENUE)
    # marcadores
    for v, etq, col, dy in ((tdi0, f'inicial {tdi0:g}'.replace('.', ','), COCLEAR, 0), (tdi1, f'3 meses {tdi1:g}'.replace('.', ','), AZUL, 0)):
        x = sx0 + v * ex
        c.l(x, sy - 6, x, sy + sh, col, 2.4)
        c.out.append(f'<path d="M{x - 6:.1f},{sy - 16:.1f} L{x + 6:.1f},{sy - 16:.1f} L{x:.1f},{sy - 5:.1f} Z" fill="{col}"/>')
    c.t(sx0 + tdi0 * ex - 8, sy - 22, f'inicial {tdi0:g}'.replace('.', ','), 9, COCLEAR, 'end', 700)
    c.t(sx0 + tdi1 * ex + 8, sy - 22, f'3 meses {tdi1:g}'.replace('.', ','), 9, AZUL, 'start', 700)
    c.t(sx0, 350, 'El caso mejora lo suficiente para que la diferencia sea clínicamente importante, pero sigue en el rango de hiposmia.', 8.5, TINTA, 'start')
    c.t(sx0, 366, 'Las diferencias mínimas por subprueba son otras: 2,5 para T y 3 para D e I (Gudziol y cols., 2006). Datos de ejemplo.', 8, TENUE, 'start')
    c.guardar('h28-tdi.svg', DEFS)
    return tdi0, tdi1


# ------------------------------------------------------------------ TDI por edad
GRUPOS = ['5–10', '11–20', '21–30', '31–40', '41–50', '51–60', '61–70', '71–80', '> 81']
MEDIA = [25.21, 34.00, 35.99, 35.55, 34.06, 32.85, 31.26, 27.93, 23.30]
MEDIA_TXT = ['25.2', '34.0', '36.0', '35.6', '34.1', '32.9', '31.3', '27.9', '23.3']   # redondeo habitual (mitad hacia arriba)
P10 = [19.4, 28.5, 30.75, 30.5, 28.15, 27.25, 24.88, 19.2, 13.0]


def edad():
    c = Lienzo(760, 380)
    x0, y0, w, h = 70, 40, 640, 244
    ymin, ymax = 10, 40
    c.t(14, 20, 'TDI por grupo de edad en personas sanas (Oleszkiewicz y cols., 2019, n = 9139)', 10, TINTA, 'start', 700)
    yv = lambda v: y0 + h - (v - ymin) / (ymax - ymin) * h
    xv = lambda k: x0 + (k + 0.5) * w / len(GRUPOS)
    for v in range(10, 41, 5):
        c.l(x0, yv(v), x0 + w, yv(v), GRILLA, 1)
        c.t(x0 - 8, yv(v) + 3.5, str(v), 8.5, TINTA, 'end')
    c.l(x0, y0 + h, x0 + w, y0 + h, TINTA, 1.2)
    c.l(x0, y0, x0, y0 + h, TINTA, 1.2)
    for k, g in enumerate(GRUPOS):
        c.t(xv(k), y0 + h + 17, g, 8.5)
    c.t(x0 + w / 2, y0 + h + 34, 'grupo de edad (años)', 9, TINTA)
    c.raw(f'<text x="22" y="{y0 + h / 2}" font-family="\'Plus Jakarta Sans\', sans-serif" font-size="10.8" '
          f'fill="{TINTA}" text-anchor="middle" transform="rotate(-90 22 {y0 + h / 2})">puntaje TDI</text>')
    # cortes fijos
    c.l(x0, yv(30.75), x0 + w, yv(30.75), COCLEAR, 1.3, '6 4')
    c.t(x0 + w - 2, yv(30.75) - 5, 'corte de hiposmia: 30,75', 8.2, COCLEAR, 'end', 700)
    c.l(x0, yv(16), x0 + w, yv(16), AVISO, 1.3, '6 4')
    c.t(x0 + 6, yv(16) - 5, 'anosmia funcional: 16', 8.2, AVISO, 'start', 700)
    c.poli([(xv(k), yv(v)) for k, v in enumerate(MEDIA)], RETRO, 2.4)
    c.poli([(xv(k), yv(v)) for k, v in enumerate(P10)], AZUL, 2.4, '7 4')
    for k, (m, p) in enumerate(zip(MEDIA, P10)):
        c.circ(xv(k), yv(m), 3.6, RETRO, RETRO, 1)
        c.circ(xv(k), yv(p), 3.6, '#fff', AZUL, 1.8)
        c.t(xv(k), yv(m) - 8, f'{MEDIA_TXT[k]}'.replace('.', ','), 8, RETRO, 'middle', 700)
        if k == 2:
            c.t(xv(k) - 8, yv(p) - 9, f'{p:g}'.replace('.', ','), 8, AZUL, 'end', 700)
        elif k == 3:
            c.t(xv(k) + 12, yv(p) - 6, f'{p:g}'.replace('.', ','), 8, AZUL, 'start', 700)
        elif k == 0:
            c.t(xv(k) + 12, yv(p) + 12, f'{p:g}'.replace('.', ','), 8, AZUL, 'start', 700)
        else:
            c.t(xv(k), yv(p) + 15, f'{p:g}'.replace('.', ','), 8, AZUL, 'middle', 700)
    c.t(xv(8) + 9, yv(MEDIA[8]) + 3.5, 'promedio', 8.8, RETRO, 'start', 700)
    c.t(xv(8) - 12, yv(P10[8]) + 4, 'percentil 10', 8.8, AZUL, 'end', 700)
    # caso del ejemplo: 34 años = grupo 31-40
    k = 3
    t0, t1 = T0 + D0 + I0, T1 + D1 + I1
    c.circ(xv(k), yv(t0), 6, COCLEAR, '#fff', 1.6)
    c.circ(xv(k), yv(t1), 6, '#fff', COCLEAR, 2.2)
    c.t(xv(k) - 12, yv(t0) + 4, f'ejemplo: {t0:g}'.replace('.', ','), 8.8, COCLEAR, 'end', 700)
    c.t(xv(k) - 12, yv(t1) + 4, f'a los 3 meses: {t1:g}'.replace('.', ','), 8.8, COCLEAR, 'end', 700)
    c.t(x0 + w / 2, 340, 'Bajo el percentil 10 de su edad, el puntaje es menor que el de 9 de cada 10 personas sanas de ese grupo.', 8.5, TINTA)
    c.t(x0 + w / 2, 356, 'Con la edad, el subpuntaje que más baja es el umbral. Los puntos del caso son datos de ejemplo.', 8, TENUE)
    c.guardar('h28-edad.svg', DEFS)


if __name__ == '__main__':
    via()
    transduccion()
    pruebas()
    seed, ens, inv, umbral = escalera()
    print(f'escalera: seed={seed}, {len(ens)} tríos, inversiones en los tríos {[i + 1 for i in inv]}, '
          f'pasos de las últimas 4 inversiones {[ens[i][0] for i in inv[-4:]]}, umbral={umbral}')
    print('secuencia (paso, acierto):', [(p, int(ok)) for p, ok in ens])
    print('concentraciones % por paso:', {p: round(conc(p), 6) for p in (1, 4, 5, 8, 16)})
    t0, t1 = tdi()
    print('TDI inicial', t0, 'a los 3 meses', t1, 'diferencia', t1 - t0)
    edad()
