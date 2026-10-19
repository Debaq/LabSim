#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H29 (polisomnografía y poligrafía respiratoria):

    h29-hipnograma.svg   hipnograma de una noche de ejemplo (etapas por época de 30 s agrupadas en minutos)
    h29-eventos.svg      trazos de 30 s: apnea obstructiva, central, mixta e hipopnea, con flujo, esfuerzo y SpO2
    h29-montaje.svg      EEG 10-20 (derivaciones recomendadas) y colocación de los demás sensores
    h29-informe.svg      resumen gráfico de un informe de ejemplo: hipnograma, eventos, posición y SpO2

SVG propios, no IA. Todo se CALCULA: el hipnograma y los eventos del informe salen de una noche simulada con
semilla fija (los números que usa el capítulo se imprimen al correr el script); los trazos de 30 s se generan
con senoides de frecuencia respiratoria constante, atenuadas o desfasadas según el tipo de evento. Las cifras
son de ejemplo, no de pacientes."""
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import re  # noqa: E402
from hacer_h25 import Lienzo as _Lienzo, TINTA, TENUE, GRILLA, FUERTE, AVISO, RETRO, COCLEAR  # noqa: E402

AQUI = pathlib.Path(__file__).parent
GRIS = '#b9b6ae'
AZUL = '#2f5d9e'


class Lienzo(_Lienzo):
    """Igual que el de H25, con coma decimal en los textos."""

    k = 1.0

    def t(self, x, y, s, size=9, *a, **kw):
        super().t(x, y, re.sub(r'(?<=\d)\.(?=\d)', ',', str(s)), size * self.k, *a, **kw)


# ------------------------------------------------------------------ noche simulada
# (etapa, minutos). W = vigilia, N1-N3, R = REM. La primera W es la latencia de sueño.
SECUENCIA = [
    ('W', 14),
    ('N1', 4), ('N2', 18), ('N3', 36), ('N2', 14), ('R', 10), ('W', 3),
    ('N1', 3), ('N2', 22), ('N3', 26), ('N2', 18), ('R', 14), ('W', 4),
    ('N2', 26), ('N3', 14), ('N2', 28), ('R', 18), ('N1', 4), ('W', 5),
    ('N2', 30), ('N3', 4), ('N2', 30), ('R', 22), ('N1', 5), ('W', 6),
    ('N2', 24), ('R', 30), ('N1', 4), ('N2', 12), ('W', 8),
    ('N2', 14), ('N1', 4), ('N2', 6),
]
# posición corporal: (inicio min, fin min, posición)
POSICIONES = [(0, 150, 'supino'), (150, 230, 'izquierda'), (230, 330, 'supino'), (330, 400, 'derecha'), (400, 600, 'supino')]
TASA = {'N1': 16.0, 'N2': 11.0, 'N3': 3.0, 'R': 34.0}         # eventos/h de sueño en posición lateral (base)
FACTOR_POS = {'supino': 1.7, 'izquierda': 0.5, 'derecha': 0.6}
TIPOS = [('apnea obstructiva', 0.30), ('hipopnea', 0.62), ('apnea mixta', 0.05), ('apnea central', 0.03)]
ORDEN_ETAPA = {'W': 4, 'R': 3, 'N1': 2, 'N2': 1, 'N3': 0}   # 0 abajo
NOMBRE_ETAPA = {'W': 'Vigilia', 'R': 'REM', 'N1': 'N1', 'N2': 'N2', 'N3': 'N3'}


def posicion(t):
    for a, b, p in POSICIONES:
        if a <= t < b:
            return p
    return POSICIONES[-1][2]


def noche():
    seg, t = [], 0
    for e, d in SECUENCIA:
        seg.append((e, t, t + d))
        t += d
    tib = t
    # eventos
    rng = random.Random(2910)
    ev = []
    for e, a, b in seg:
        if e == 'W':
            continue
        for m in range(a, b):
            lam = TASA[e] * FACTOR_POS[posicion(m)] / 60.0      # eventos por minuto
            # cada evento ocupa ~25 s; se sortea como Poisson por minuto
            n = 0
            L = math.exp(-lam)
            p = 1.0
            while True:
                p *= rng.random()
                if p <= L:
                    break
                n += 1
            for _ in range(n):
                r, acc, tipo = rng.random(), 0, TIPOS[0][0]
                for nom, pr in TIPOS:
                    acc += pr
                    if r <= acc:
                        tipo = nom
                        break
                dur = rng.randint(10, 32) if tipo != 'hipopnea' else rng.randint(10, 40)
                ev.append(dict(t=m + rng.random(), tipo=tipo, dur=dur, etapa=e, pos=posicion(m)))
    # RERA (no cumplen apnea ni hipopnea)
    sueno = [(e, a, b) for e, a, b in seg if e != 'W']
    rera = []
    for _ in range(26):
        e, a, b = rng.choice(sueno)
        m = a + rng.random() * (b - a)
        rera.append(dict(t=m, tipo='RERA', dur=rng.randint(10, 20), etapa=e, pos=posicion(m)))
    # SpO2 por segundo (3 min de margen de seguridad no hacen falta: se simula toda la noche)
    N = tib * 60
    spo2 = [95.6] * N
    for x in ev:
        if x['tipo'] == 'apnea central':
            caida = rng.uniform(2.5, 5.0)
        else:
            caida = 2.0 + 0.18 * x['dur'] + (2.5 if x['etapa'] == 'R' else 0) + rng.uniform(-1.0, 1.5)
        if x['tipo'] == 'hipopnea':
            caida *= 0.75
        x['caida'] = max(1.0, caida)
        ini = int(x['t'] * 60 + x['dur'] * 0.6)
        baja = int(x['dur'] * 0.7 + 4)
        sube = int(26 + caida * 2)
        for k in range(baja + sube):
            s = ini + k
            if s >= N:
                break
            f = k / baja if k < baja else 1 - (k - baja) / sube
            spo2[s] = min(spo2[s], 95.6 - caida * f)
    for s in range(N):
        spo2[s] += random.Random(s).uniform(-0.25, 0.25)
    return dict(seg=seg, tib=tib, ev=ev, rera=rera, spo2=spo2)


def resumen(n):
    seg, tib, ev, rera, spo2 = n['seg'], n['tib'], n['ev'], n['rera'], n['spo2']
    tst = sum(b - a for e, a, b in seg if e != 'W')
    lat = seg[0][2] - seg[0][1]
    r = {}
    r['TIB'], r['TST'], r['latencia'] = tib, tst, lat
    r['eficiencia'] = 100 * tst / tib
    rem_ini = next((a for e, a, b in seg if e == 'R'), None)
    r['latencia REM'] = rem_ini - lat
    r['WASO'] = sum(b - a for e, a, b in seg if e == 'W') - lat
    for e in ('N1', 'N2', 'N3', 'R'):
        r['min ' + e] = sum(b - a for ee, a, b in seg if ee == e)
        r['% ' + e] = 100 * r['min ' + e] / tst
    h = tst / 60.0
    for nom, _ in TIPOS:
        r[nom] = sum(1 for x in ev if x['tipo'] == nom)
    r['RERA'] = len(rera)
    r['eventos'] = len(ev)
    r['IAH'] = len(ev) / h
    r['IDR'] = (len(ev) + len(rera)) / h
    r['IAH obstructivo'] = sum(1 for x in ev if x['tipo'] in ('apnea obstructiva', 'hipopnea')) / h
    r['IAI'] = sum(1 for x in ev if x['tipo'].startswith('apnea')) / h
    r['IH'] = r['hipopnea'] / h
    r['IDO3'] = sum(1 for x in ev if x['caida'] >= 3) / h
    r['IDO4'] = sum(1 for x in ev if x['caida'] >= 4) / h
    # IAH por etapa y por posición
    for e in ('N1', 'N2', 'N3', 'R'):
        hh = r['min ' + e] / 60.0
        r['IAH ' + e] = sum(1 for x in ev if x['etapa'] == e) / hh if hh else 0
    for p in ('supino', 'izquierda', 'derecha'):
        mins = sum(min(b, sb) - max(a, sa) for e, sa, sb in seg if e != 'W' for (a, b, pp) in POSICIONES if pp == p
                   if min(b, sb) > max(a, sa))
        r['min ' + p] = mins
        r['IAH ' + p] = sum(1 for x in ev if x['pos'] == p) / (mins / 60.0) if mins else 0
    # SpO2 solo durante el sueño
    vals = []
    for e, a, b in seg:
        if e != 'W':
            vals.extend(spo2[a * 60:b * 60])
    r['SpO2 media'] = sum(vals) / len(vals)
    r['SpO2 mín'] = min(vals)
    r['T90'] = 100 * sum(1 for v in vals if v < 90) / len(vals)
    r['IAH REM/NREM'] = (r['IAH R'], (len(ev) - sum(1 for x in ev if x['etapa'] == 'R')) / ((tst - r['min R']) / 60.0))
    return r


def gravedad(iah):
    return 'normal' if iah < 5 else 'leve' if iah < 15 else 'moderado' if iah < 30 else 'grave'


# ------------------------------------------------------------------ utilidades gráficas
def hora(m):
    """Minutos desde apagar luces → 'h' con una decimal."""
    return m / 60.0


def hipnograma(c, x0, y0, w, h, n, xmax=None, rotulos=True, eventos=False):
    seg, tib = n['seg'], n['tib']
    xmax = xmax or tib
    X = lambda m: x0 + m / xmax * w
    nivel = lambda e: y0 + h - ORDEN_ETAPA[e] / 4 * h
    for k in range(5):
        y = y0 + h - k / 4 * h
        c.l(x0, y, x0 + w, y, GRILLA, 1)
    if rotulos:
        for e, k in ORDEN_ETAPA.items():
            c.t(x0 - 6, y0 + h - k / 4 * h + 3, NOMBRE_ETAPA[e], 8, TINTA, 'end')
    for hh in range(0, int(xmax / 60) + 1):
        c.l(X(hh * 60), y0, X(hh * 60), y0 + h, GRILLA, 1)
        c.t(X(hh * 60), y0 + h + 12, f'{hh}', 8, TENUE)
    # REM sombreado
    for e, a, b in seg:
        if e == 'R':
            c.raw(f'<rect x="{X(a):.1f}" y="{nivel("R") - 4:.1f}" width="{X(b) - X(a):.1f}" height="8" fill="{AVISO}" opacity=".45"/>')
    pts = []
    for e, a, b in seg:
        pts.append((X(a), nivel(e)))
        pts.append((X(b), nivel(e)))
    c.poli(pts, TINTA, 1.7)
    c.l(x0, y0 + h, x0 + w, y0 + h, TINTA, 1.2)
    c.l(x0, y0, x0, y0 + h, TINTA, 1.2)
    return X


# ------------------------------------------------------------------ 1. hipnograma
def fig_hipnograma(n, r):
    c = Lienzo(740, 290)
    c.t(14, 20, 'Hipnograma de una noche de ejemplo (8 h en cama)', 10, TINTA, 'start', 700)
    X = hipnograma(c, 70, 40, 640, 170, n)
    c.t(70 + 320, 40 + 170 + 28, 'horas desde que se apagan las luces', 8.5, TINTA)
    # ciclos: cada REM cierra un ciclo
    rems = [(a, b) for e, a, b in n['seg'] if e == 'R']
    # un ciclo termina al terminar cada bloque REM que dure al menos 5 min
    ini = n['seg'][0][2]
    cortes = [ini] + [b for a, b in rems if b - a >= 5]
    for i in range(len(cortes) - 1):
        c.raw(f'<rect x="{X(cortes[i]):.1f}" y="{26}" width="{X(cortes[i + 1]) - X(cortes[i]):.1f}" height="9" fill="{COCLEAR if i % 2 == 0 else RETRO}" opacity=".35"/>')
        c.t((X(cortes[i]) + X(cortes[i + 1])) / 2, 33.5, f'ciclo {i + 1}', 7.5, TINTA)
    c.t(14, 252, f'En rojo, los períodos REM. El sueño profundo (N3) se concentra en los primeros ciclos y los REM se alargan hacia la mañana.', 8, TENUE, 'start')
    c.t(14, 266, f'Tiempo total de sueño {r["TST"]} min de {r["TIB"]} min en cama; latencia de sueño {r["latencia"]} min; latencia REM {r["latencia REM"]} min.', 8, TENUE, 'start')
    c.t(14, 280, 'Cifras de ejemplo, calculadas con el script que dibuja la figura.', 8, TENUE, 'start')
    c.guardar('h29-hipnograma.svg')


# ------------------------------------------------------------------ 2. eventos de 30 s
def senales(tipo, dt=0.05, T=30.0):
    """Devuelve dict canal → lista de (t, y), con la inspiración hacia arriba."""
    f = 0.27                       # 16 resp/min
    ph = lambda t: 2 * math.pi * f * t
    nt = int(T / dt) + 1
    ts = [i * dt for i in range(nt)]
    # ventana del evento (s)
    if tipo == 'obstructiva':
        a, b = 6.0, 24.0
    elif tipo == 'central':
        a, b = 6.0, 22.0
    elif tipo == 'mixta':
        a, b = 5.0, 25.0
    else:
        a, b = 6.0, 26.0
    cen = 12.0 if tipo == 'mixta' else None     # la parte central de la apnea mixta termina a los 13 s
    out = {k: [] for k in ('termico', 'presion', 'torax', 'abdomen', 'spo2')}
    rnd = random.Random(7)
    for t in ts:
        base = math.sin(ph(t))
        env_fl = 1.0                       # amplitud del flujo
        env_ef = 1.0                       # amplitud del esfuerzo
        paradoja = 0.0                     # 0 = tórax y abdomen en fase; 1 = en oposición
        limita = False
        dentro = a <= t <= b
        if dentro:
            u = (t - a) / (b - a)
            if tipo == 'obstructiva':
                env_fl = 0.04
                env_ef = 0.5 + 1.1 * u
                paradoja = min(1.0, 0.4 + 0.8 * u)
            elif tipo == 'central':
                env_fl = 0.04
                env_ef = 0.04
            elif tipo == 'mixta':
                env_fl = 0.04
                if t < a + 8:
                    env_ef = 0.04
                else:
                    uu = (t - a - 8) / (b - a - 8)
                    env_ef = 0.5 + 1.1 * uu
                    paradoja = min(1.0, 0.4 + 0.8 * uu)
            else:   # hipopnea con limitación del flujo
                env_fl = 0.5
                env_ef = 0.75
                paradoja = 0.35
                limita = True
        elif b < t <= b + 3.5:             # respiraciones de recuperación tras el despertar
            env_fl = 1.45
            env_ef = 1.45
        # canales
        sn = base
        if limita:
            # aplanamiento inspiratorio: se corta la parte alta
            sn = max(-1, min(0.55, base)) / 0.55 * 0.8 if base > 0 else base
        termico = env_fl * math.sin(ph(t) + 0.15) + rnd.uniform(-0.02, 0.02)
        presion = env_fl * (sn if limita else base) + rnd.uniform(-0.03, 0.03)
        if limita:
            presion = env_fl * sn * 1.1 + rnd.uniform(-0.03, 0.03)
        torax = env_ef * base + rnd.uniform(-0.02, 0.02)
        # el abdomen oscila en fase con el tórax; con paradoja se invierte parcialmente
        abd = env_ef * (math.sin(ph(t) + 0.2) * (1 - 2 * paradoja)) + rnd.uniform(-0.02, 0.02)
        out['termico'].append((t, termico))
        out['presion'].append((t, presion))
        out['torax'].append((t, torax))
        out['abdomen'].append((t, abd))
    # SpO2: baja con retraso respecto del evento, nadir después de terminar
    nadir = {'obstructiva': 91.0, 'central': 93.0, 'mixta': 90.0, 'hipopnea': 92.0}[tipo]
    ini = a + 7.0
    pico = b + 6.0
    for t in ts:
        if t < ini:
            v = 96.0
        elif t < pico:
            v = 96.0 - (96.0 - nadir) * (t - ini) / (pico - ini)
        else:
            v = nadir + (t - pico) * 0.5
        out['spo2'].append((t, min(96.0, v) + rnd.uniform(-0.1, 0.1)))
    return out, (a, b), nadir


def fig_eventos():
    tipos = [('obstructiva', 'Apnea obstructiva', 'sin flujo, con esfuerzo'),
             ('central', 'Apnea central', 'sin flujo, sin esfuerzo'),
             ('mixta', 'Apnea mixta', 'primero sin esfuerzo, luego con esfuerzo'),
             ('hipopnea', 'Hipopnea', 'flujo reducido y aplanado')]
    W, H = 780, 470
    c = Lienzo(W, H)
    c.k = 1.08
    x0, ancho, sep = 92, 158, 10
    canales = [('termico', 'Flujo oronasal (térmico)'), ('presion', 'Presión nasal'), ('torax', 'Banda torácica'),
               ('abdomen', 'Banda abdominal'), ('spo2', 'SpO₂ (%)')]
    y0, alto, sepy = 78, 52, 12
    for j, (k, nom) in enumerate(canales):
        yy = y0 + j * (alto + sepy)
        c.t(x0 - 8, yy + alto / 2 - 2, nom.split(' (')[0], 8, TINTA, 'end', 700)
        if '(' in nom:
            c.t(x0 - 8, yy + alto / 2 + 9, '(' + nom.split(' (')[1], 7.5, TENUE, 'end')
    info = []
    for i, (tp, tit, sub) in enumerate(tipos):
        xi = x0 + i * (ancho + sep)
        s, (a, b), nadir = senales(tp)
        c.t(xi + ancho / 2, 22, tit, 9.5, TINTA, 'middle', 700)
        c.t(xi + ancho / 2, 36, sub, 8, TENUE)
        X = lambda t: xi + t / 30.0 * ancho
        for j, (k, nom) in enumerate(canales):
            yy = y0 + j * (alto + sepy)
            c.raw(f'<rect x="{xi}" y="{yy}" width="{ancho}" height="{alto}" fill="#fff" stroke="{FUERTE}" stroke-width="1"/>')
            for sg in (5, 10, 15, 20, 25):
                c.l(X(sg), yy, X(sg), yy + alto, GRILLA, 1)
            # evento sombreado
            c.raw(f'<rect x="{X(a):.1f}" y="{yy}" width="{X(b) - X(a):.1f}" height="{alto}" fill="{AVISO}" opacity=".07"/>')
            if k == 'spo2':
                Y = lambda v: yy + alto - (v - 88) / (98 - 88) * alto
                c.poli([(X(t), Y(v)) for t, v in s[k]], AZUL, 1.5)
                c.l(xi, Y(96), xi + ancho, Y(96), FUERTE, 1, '3 3')
                c.t(X(30) - 3, Y(nadir) + 10, f'{nadir:.0f} %', 7.5, AZUL, 'end', 700)
            else:
                Y = lambda v: yy + alto / 2 - v * (alto / 2 - 5) / 1.5
                col = {'termico': COCLEAR, 'presion': COCLEAR, 'torax': RETRO, 'abdomen': TINTA}[k]
                c.poli([(X(t), Y(v)) for t, v in s[k]], col, 1.3)
        # corchete de duración
        yb = y0 + 5 * (alto + sepy) - sepy + 12
        c.l(X(a), yb, X(b), yb, AVISO, 1.6)
        c.l(X(a), yb - 4, X(a), yb + 4, AVISO, 1.6)
        c.l(X(b), yb - 4, X(b), yb + 4, AVISO, 1.6)
        c.t((X(a) + X(b)) / 2, yb + 13, f'evento de {b - a:.0f} s', 8, AVISO, 'middle', 700)
        for sg in (0, 10, 20, 30):
            c.t(X(sg), yb + 28, f'{sg}', 7.5, TENUE)
        info.append((tp, b - a, nadir))
    c.t(x0, 458, 'segundos →   Ventanas de 30 s; la inspiración va hacia arriba; línea punteada de SpO₂: 96 %. Tórax y abdomen en oposición durante la apnea obstructiva (paradoja).', 8, TENUE, 'start')
    c.guardar('h29-eventos.svg')
    for tp, d, nadir in info:
        print('EVENTO', tp, 'duración', d, 's; SpO2 nadir', nadir)


# ------------------------------------------------------------------ 3. montaje
def fig_montaje():
    W, H = 800, 500
    c = Lienzo(W, H)
    c.k = 1.12
    c.t(14, 20, 'A · Cuero cabelludo (10-20, visto desde arriba)', 10, TINTA, 'start', 700)
    cx, cy, R = 172, 190, 100
    c.raw(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    c.raw(f'<polygon points="{cx - 14},{cy - R + 1} {cx + 14},{cy - R + 1} {cx},{cy - R - 18}" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    c.t(cx, cy - R - 24, 'nariz', 8, TENUE)
    for sx in (-1, 1):
        c.raw(f'<ellipse cx="{cx + sx * (R + 4)}" cy="{cy}" rx="6" ry="16" fill="#fff" stroke="{TINTA}" stroke-width="1.4"/>')
    sitios = {'Fp1': (-0.31, 0.95), 'Fp2': (0.31, 0.95), 'F7': (-0.81, 0.59), 'F3': (-0.42, 0.5), 'Fz': (0, 0.5), 'F4': (0.42, 0.5),
              'F8': (0.81, 0.59), 'T3': (-1.0, 0), 'C3': (-0.5, 0), 'Cz': (0, 0), 'C4': (0.5, 0), 'T4': (1.0, 0), 'T5': (-0.81, -0.59),
              'P3': (-0.42, -0.5), 'Pz': (0, -0.5), 'P4': (0.42, -0.5), 'T6': (0.81, -0.59), 'O1': (-0.31, -0.95), 'O2': (0.31, -0.95)}
    rec = {'F4', 'C4', 'O2'}
    resp = {'F3', 'C3', 'O1'}
    for nom, (x, y) in sitios.items():
        px, py = cx + x * (R - 10), cy - y * (R - 10)
        if nom in rec:
            c.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="11" fill="{COCLEAR}" stroke="#fff" stroke-width="1.2"/>')
            c.t(px, py + 3, nom, 7.5, '#fff', 'middle', 700)
        elif nom in resp:
            c.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="11" fill="#fff" stroke="{COCLEAR}" stroke-width="1.8"/>')
            c.t(px, py + 3, nom, 7.5, COCLEAR, 'middle', 700)
        else:
            c.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="#fff" stroke="{GRIS}" stroke-width="1.2"/>')
            c.t(px, py + 3, nom, 6.5, TENUE)
    # mastoides
    for nom, sx in (('M1', -1), ('M2', 1)):
        px, py = cx + sx * (R + 44), cy + 24
        c.raw(f'<circle cx="{px}" cy="{py}" r="11" fill="{RETRO}" stroke="#fff" stroke-width="1.2"/>')
        c.t(px, py + 3, nom, 7.5, '#fff', 'middle', 700)
    c.t(14, 340, 'Naranja lleno: derivaciones recomendadas (F4, C4, O2, cada una referida a M1).', 8, TINTA, 'start')
    c.t(14, 353, 'Naranja vacío: respaldo (F3, C3, O1, cada una referida a M2).', 8, TINTA, 'start')
    c.t(14, 366, 'M1 y M2: mastoides izquierda y derecha. En gris, el resto del sistema 10-20.', 8, TENUE, 'start')
    # cuerpo
    bx = 560
    c.t(400, 20, 'B · Resto de los sensores', 10, TINTA, 'start', 700)
    c.raw(f'<ellipse cx="{bx}" cy="85" rx="34" ry="42" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    c.raw(f'<rect x="{bx - 12}" y="124" width="24" height="18" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    c.raw(f'<path d="M{bx - 62},150 Q{bx - 62},140 {bx - 30},140 L{bx + 30},140 Q{bx + 62},140 {bx + 62},150 L{bx + 56},290 L{bx - 56},290 Z" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    c.raw(f'<rect x="{bx - 52}" y="290" width="46" height="150" rx="14" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    c.raw(f'<rect x="{bx + 6}" y="290" width="46" height="150" rx="14" fill="#fff" stroke="{TINTA}" stroke-width="1.6"/>')
    # ojos
    c.raw(f'<circle cx="{bx - 14}" cy="78" r="3" fill="{TINTA}"/><circle cx="{bx + 14}" cy="78" r="3" fill="{TINTA}"/>')
    def punto(x, y, col, r=5):
        c.raw(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}" stroke="#fff" stroke-width="1"/>')

    def llamada(px, py, tx, ty, texto, col=TINTA, ancla='start'):
        c.l(px, py, tx, ty, col, 1)
        c.t(tx + (4 if ancla == 'start' else -4), ty + 3, texto, 8, col, ancla)

    # EOG
    punto(bx + 22, 70, RETRO); punto(bx - 22, 88, RETRO)
    llamada(bx + 22, 70, bx + 70, 40, 'EOG E2 (canto externo der.)', RETRO)
    llamada(bx - 22, 88, bx - 75, 56, 'EOG E1 (canto externo izq.)', RETRO, 'end')
    # EMG mentoniano
    for dx, dy in ((-8, 118), (8, 118), (0, 124)):
        punto(bx + dx, dy, COCLEAR, 3.5)
    llamada(bx + 8, 120, bx + 80, 108, 'EMG mentoniano', COCLEAR)
    # cánula y termistor
    c.raw(f'<path d="M{bx - 14},97 Q{bx},106 {bx + 14},97" fill="none" stroke="{AVISO}" stroke-width="2.2"/>')
    c.raw(f'<path d="M{bx - 18},101 Q{bx},116 {bx + 18},101" fill="none" stroke="{AZUL}" stroke-width="1.6" stroke-dasharray="4 2"/>')
    llamada(bx - 16, 98, bx - 120, 84, 'Cánula de presión nasal', AVISO, 'end')
    llamada(bx - 18, 106, bx - 120, 112, 'Sensor térmico oronasal', AZUL, 'end')
    # ronquido
    punto(bx - 10, 134, TENUE, 4)
    llamada(bx - 10, 134, bx - 112, 142, 'Ronquido (micrófono o piezo)', TINTA, 'end')
    # ECG
    punto(bx - 26, 190, AVISO, 4); punto(bx + 26, 232, AVISO, 4)
    llamada(bx + 26, 232, bx + 80, 224, 'ECG (derivación II)', AVISO)
    # bandas
    c.raw(f'<rect x="{bx - 60}" y="166" width="120" height="12" rx="6" fill="{RETRO}" opacity=".55"/>')
    c.raw(f'<rect x="{bx - 56}" y="250" width="112" height="12" rx="6" fill="{RETRO}" opacity=".55"/>')
    llamada(bx + 60, 172, bx + 82, 160, 'Banda torácica (RIP)', RETRO)
    llamada(bx + 56, 256, bx + 82, 270, 'Banda abdominal (RIP)', RETRO)
    # posición
    punto(bx, 206, TINTA, 4)
    llamada(bx, 206, bx - 110, 200, 'Sensor de posición', TINTA, 'end')
    # oxímetro
    c.raw(f'<rect x="{bx + 50}" y="276" width="14" height="22" rx="3" fill="{AZUL}"/>')
    llamada(bx + 58, 296, bx + 82, 316, 'Oxímetro de pulso (dedo)', AZUL)
    # EMG tibial
    punto(bx - 29, 380, COCLEAR, 4); punto(bx + 29, 380, COCLEAR, 4)
    llamada(bx + 29, 380, bx + 80, 372, 'EMG tibial anterior', COCLEAR)
    c.t(14, 470, 'Poligrafía respiratoria: solo flujo (presión nasal), bandas, oximetría y frecuencia cardíaca,', 8, TENUE, 'start')
    c.t(14, 483, 'más ronquido y posición según el equipo. No lleva EEG, EOG ni EMG: no mide sueño.', 8, TENUE, 'start')
    c.guardar('h29-montaje.svg')


# ------------------------------------------------------------------ 4. informe
def fig_informe(n, r):
    c = Lienzo(780, 400)
    c.k = 1.12
    c.t(14, 20, 'Resumen gráfico de la noche de ejemplo', 10, TINTA, 'start', 700)
    x0, w = 90, 640
    tib = n['tib']
    X = lambda m: x0 + m / tib * w
    # A hipnograma
    c.t(14, 44, 'Etapas', 8.5, TINTA, 'start', 700)
    hipnograma(c, x0, 50, w, 90, n, rotulos=True)
    # B eventos
    ycol = {'apnea obstructiva': AVISO, 'hipopnea': COCLEAR, 'apnea mixta': TINTA, 'apnea central': AZUL}
    c.t(14, 178, 'Eventos', 8.5, TINTA, 'start', 700)
    filas = [('apnea obstructiva', 'AO'), ('apnea mixta', 'AM'), ('apnea central', 'AC'), ('hipopnea', 'H')]
    yb = 170
    for j, (tp, ab) in enumerate(filas):
        y = yb + j * 13
        c.t(x0 - 6, y + 7, ab, 8, ycol[tp], 'end', 700)
        c.l(x0, y + 11, x0 + w, y + 11, GRILLA, 1)
        for x in n['ev']:
            if x['tipo'] == tp:
                c.l(X(x['t']), y, X(x['t']), y + 10, ycol[tp], 1.1)
    # RERA
    y = yb + 4 * 13
    c.t(x0 - 6, y + 7, 'RERA', 8, TENUE, 'end', 700)
    c.l(x0, y + 11, x0 + w, y + 11, GRILLA, 1)
    for x in n['rera']:
        c.l(X(x['t']), y, X(x['t']), y + 10, TENUE, 1.1)
    # C posición
    yp = 250
    c.t(14, yp + 10, 'Posición', 8.5, TINTA, 'start', 700)
    col = {'supino': AVISO, 'izquierda': RETRO, 'derecha': AZUL}
    for a, b, p in POSICIONES:
        b = min(b, tib)
        c.raw(f'<rect x="{X(a):.1f}" y="{yp}" width="{X(b) - X(a):.1f}" height="14" fill="{col[p]}" opacity=".6"/>')
        c.t((X(a) + X(b)) / 2, yp + 11, p, 7.5, '#fff', 'middle', 700)
    # D SpO2
    ys, hs = 280, 70
    c.t(14, ys + 8, 'SpO₂ (%)', 8.5, TINTA, 'start', 700)
    Y = lambda v: ys + hs - (v - 80) / (100 - 80) * hs
    for v in (80, 90, 100):
        c.l(x0, Y(v), x0 + w, Y(v), GRILLA if v != 90 else FUERTE, 1, None if v != 90 else '4 3')
        c.t(x0 - 6, Y(v) + 3, f'{v}', 7.5, TENUE, 'end')
    sp = n['spo2']
    pts = []
    for m in range(0, tib * 60, 6):
        pts.append((x0 + (m / 60.0) / tib * w, Y(max(80, min(100, min(sp[m:m + 6]))))))
    c.poli(pts, AZUL, 0.9)
    for hh in range(0, int(tib / 60) + 1):
        c.t(X(hh * 60), ys + hs + 13, f'{hh}', 8, TENUE)
    c.t(x0 + w / 2, ys + hs + 28, 'horas desde que se apagan las luces', 8.5, TINTA)
    c.t(14, 392, 'AO apnea obstructiva · AM apnea mixta · AC apnea central · H hipopnea · RERA despertar por esfuerzo respiratorio. Cada marca es un evento.', 8, TENUE, 'start')
    c.guardar('h29-informe.svg')


if __name__ == '__main__':
    n = noche()
    r = resumen(n)
    for k, v in r.items():
        print(k, '=', round(v, 2) if isinstance(v, float) else v)
    print('gravedad por IAH:', gravedad(r['IAH']))
    fig_hipnograma(n, r)
    fig_eventos()
    fig_montaje()
    fig_informe(n, r)
