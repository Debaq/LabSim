"""Poligrafía y polisomnografía (H31 y cap. 38 del libro): la noche del
paciente, lo que ven los sensores y lo que se calcula de la puntuación.

- **La noche** (`PACIENTES`, `simular`, `odi`, `resumen`, `ventana`): el
  código de libro-orl/material/ilustraciones/hacer_cap38.py portado tal
  cual, con los mismos pacientes y semillas: hipnograma, posición, eventos
  respiratorios (tipo, duración, caída de SpO2, despertar), despertares
  espontáneos, SpO2 segundo a segundo y ronquido por minuto. Con el mismo
  perfil, los índices son los del capítulo 38 (tests/test_nasal_sueno.py lo
  compara con el script del libro si está a mano).
- **Lo que se agrega** (más abajo): el termistor y el EOG en `senales`, la
  noche de un perfil personalizado (`perfil_personalizado`), la cánula que
  se suelta en la casa, la puntuación automática que el alumno corrige
  (`auto_puntuar`) y los índices calculados con SU puntuación
  (`indices`).

La verdad (los eventos del modelo) no la ve el alumno: va a "Lo que el
equipo no sabe" y al log.

Sin `cases.data['SUENO']` no hay paciente: no se registra nada.
"""

import math
import random

ORDEN = {'W': 4, 'R': 3, 'N1': 2, 'N2': 1, 'N3': 0}
NOM_ETAPA = {'W': 'Vigilia', 'R': 'REM', 'N1': 'N1', 'N2': 'N2', 'N3': 'N3'}


# ── La noche (libro-orl, hacer_cap38.py; solo `simular` acepta otro perfil) ──

# ----------------------------------------------------------------------------------- pacientes
# seq: etapas (etapa, minutos); la primera W es la latencia. pos: (desde, hasta, posición) en min desde apagar luces.
# tasa: eventos/h de sueño por etapa en posición lateral; fpos: factor por posición; mix: tipo -> proporción
# drop_*: caída media de SpO2 (puntos) de apneas e hipopneas; hip_sin: fracción de hipopneas con caída < 3 (solo despertar)
PACIENTES = {
    'roncador': dict(
        titulo='Poligrafía · roncador simple', semilla=3801, tib=470,
        seq=[('W', 16), ('N1', 6), ('N2', 30), ('N3', 40), ('N2', 20), ('R', 14), ('W', 4), ('N2', 36), ('N3', 24),
             ('N2', 28), ('R', 22), ('W', 6), ('N2', 40), ('R', 28), ('N1', 6), ('N2', 30), ('R', 30), ('W', 5),
             ('N2', 20), ('N1', 5), ('N2', 20), ('W', 8), ('N2', 32)],
        pos=[(0, 130, 'supino'), (130, 250, 'derecha'), (250, 330, 'supino'), (330, 470, 'izquierda')],
        tasa=dict(N1=4.0, N2=2.4, N3=0.6, R=4.5), fpos=dict(supino=1.6, izquierda=0.6, derecha=0.7),
        mix=dict(ao=0.30, am=0.0, ac=0.05, h=0.65), drop_ap=3.5, drop_hip=3.4, hip_sin=0.35, rem_extra=0.8,
        base=96.8, p_ar=0.7, ar_esp=9.0, ron_p=dict(supino=0.85, izquierda=0.5, derecha=0.6), dur_ap=(10, 20), dur_h=(10, 24)),
    'moderado': dict(
        titulo='Poligrafía · SAOS moderado con obstrucción nasal', semilla=3802, tib=475,
        seq=[('W', 20), ('N1', 6), ('N2', 22), ('N3', 28), ('N2', 18), ('R', 10), ('W', 6), ('N1', 4), ('N2', 30),
             ('N3', 14), ('N2', 22), ('R', 16), ('W', 8), ('N2', 34), ('N1', 6), ('R', 20), ('W', 6), ('N2', 30),
             ('N1', 8), ('R', 24), ('W', 10), ('N2', 26), ('N1', 6), ('N2', 20), ('W', 5), ('N2', 30)],
        pos=[(0, 140, 'supino'), (140, 210, 'derecha'), (210, 340, 'supino'), (340, 400, 'izquierda'), (400, 475, 'supino')],
        tasa=dict(N1=21.0, N2=18.0, N3=9.0, R=40.0), fpos=dict(supino=1.7, izquierda=0.45, derecha=0.55),
        mix=dict(ao=0.30, am=0.05, ac=0.02, h=0.63), drop_ap=6.5, drop_hip=4.8, hip_sin=0.15, rem_extra=2.2,
        base=95.3, p_ar=0.85, ar_esp=8.0, ron_p=dict(supino=0.85, izquierda=0.35, derecha=0.5), dur_ap=(11, 34), dur_h=(10, 36)),
    'grave': dict(
        titulo='Polisomnografía · SAOS grave', semilla=3803, tib=462,
        seq=[('W', 18), ('N1', 14), ('N2', 26), ('N1', 6), ('W', 8), ('N2', 20), ('N3', 6), ('N2', 16), ('N1', 8), ('R', 8),
             ('W', 14), ('N1', 10), ('N2', 30), ('N1', 6), ('W', 10), ('N2', 28), ('R', 10), ('N1', 8), ('W', 12),
             ('N2', 30), ('N1', 10), ('R', 12), ('W', 14), ('N1', 8), ('N2', 26), ('W', 8), ('N2', 22), ('R', 8), ('N1', 6),
             ('W', 4), ('N2', 18)],
        pos=[(0, 90, 'supino'), (90, 160, 'derecha'), (160, 300, 'supino'), (300, 370, 'izquierda'), (370, 462, 'supino')],
        tasa=dict(N1=95.0, N2=90.0, N3=70.0, R=120.0), fpos=dict(supino=1.25, izquierda=0.75, derecha=0.85), gap=(3, 10),
        mix=dict(ao=0.42, am=0.07, ac=0.01, h=0.50), drop_ap=11.0, drop_hip=6.5, hip_sin=0.07, rem_extra=4.0,
        base=93.6, p_ar=0.9, ar_esp=5.0, ron_p=dict(supino=0.95, izquierda=0.7, derecha=0.8), dur_ap=(12, 44), dur_h=(11, 36)),
    'dudosa': dict(
        titulo='Polisomnografía · cuando la poligrafía no alcanza', semilla=3804, tib=456,
        seq=[('W', 38), ('N1', 10), ('N2', 22), ('W', 16), ('N1', 6), ('N2', 26), ('N3', 14), ('N2', 10), ('W', 24),
             ('N1', 8), ('N2', 24), ('R', 10), ('W', 30), ('N1', 6), ('N2', 20), ('R', 14), ('N1', 6), ('W', 22),
             ('N2', 30), ('N1', 8), ('R', 18), ('W', 26), ('N2', 20), ('N1', 6), ('W', 12), ('N2', 10)],
        pos=[(0, 120, 'supino'), (120, 200, 'izquierda'), (200, 330, 'supino'), (330, 456, 'derecha')],
        tasa=dict(N1=44.0, N2=34.0, N3=14.0, R=52.0), fpos=dict(supino=1.2, izquierda=0.8, derecha=0.9),
        mix=dict(ao=0.04, am=0.0, ac=0.01, h=0.70, rera=0.25), drop_ap=3.6, drop_hip=3.5, hip_sin=0.82, rem_extra=0.8,
        base=97.4, p_ar=1.0, ar_esp=6.0, ron_p=dict(supino=0.45, izquierda=0.15, derecha=0.2), dur_ap=(10, 18), dur_h=(10, 30)),
    # la noche de poligrafía en casa del mismo paciente (sueño más largo, mismas características)
    'dudosa_pg': dict(
        titulo='Poligrafía previa', semilla=3805, tib=438,
        seq=[('W', 30), ('N1', 8), ('N2', 30), ('N3', 22), ('N2', 16), ('W', 12), ('N2', 26), ('R', 12), ('N1', 6),
             ('W', 14), ('N2', 34), ('N3', 10), ('N2', 20), ('R', 16), ('W', 18), ('N2', 36), ('N1', 6), ('R', 20),
             ('W', 10), ('N2', 22), ('N1', 8), ('R', 14), ('W', 6), ('N2', 20)],
        pos=[(0, 150, 'supino'), (150, 260, 'derecha'), (260, 438, 'izquierda')],
        tasa=dict(N1=44.0, N2=34.0, N3=14.0, R=52.0), fpos=dict(supino=1.2, izquierda=0.8, derecha=0.9),
        mix=dict(ao=0.04, am=0.0, ac=0.01, h=0.70, rera=0.25), drop_ap=3.6, drop_hip=3.5, hip_sin=0.82, rem_extra=0.8,
        base=97.4, p_ar=1.0, ar_esp=6.0, ron_p=dict(supino=0.45, izquierda=0.15, derecha=0.2), dur_ap=(10, 18), dur_h=(10, 30)),
}
TIPOS = [('ao', 'apnea obstructiva'), ('am', 'apnea mixta'), ('ac', 'apnea central'), ('h', 'hipopnea'), ('rera', 'RERA')]


# ----------------------------------------------------------------------------------- simulación
def simular(clave, P=None):
    # LabSim: `P` permite un perfil que no es del libro (perfil_personalizado).
    P = P or PACIENTES[clave]
    rng = random.Random(P['semilla'])
    seg, t = [], 0
    for e, d in P['seq']:
        seg.append((e, t * 60, (t + d) * 60))
        t += d
    # la noche dura lo que dice tib: se recorta o se rellena con la última etapa
    N = P['tib'] * 60
    seg = [(e, a, min(b, N)) for e, a, b in seg if a < N]
    if seg[-1][2] < N:
        e, a, b = seg[-1]
        seg[-1] = (e, a, N)
    etapa = ['W'] * N
    for e, a, b in seg:
        for s in range(a, b):
            etapa[s] = e
    pos = ['supino'] * N
    for a, b, p in P['pos']:
        for s in range(a * 60, min(b * 60, N)):
            pos[s] = p
    ev, s, libre = [], 0, 0
    tipos, pesos = zip(*P['mix'].items())
    while s < N:
        e = etapa[s]
        if e == 'W' or s < libre:
            s += 1
            continue
        lam = P['tasa'][e] * P['fpos'][pos[s]] / 3600.0
        if rng.random() < lam:
            tp = rng.choices(tipos, pesos)[0]
            if tp == 'rera':
                dur = rng.randint(10, 18)
            elif tp == 'h':
                dur = rng.randint(*P['dur_h'])
            else:
                dur = rng.randint(*P['dur_ap'])
            fin_seg = next(b for ee, a, b in seg if a <= s < b)
            dur = min(dur, fin_seg - s - 3)
            if dur < 10:
                s += 1
                continue
            extra = P['rem_extra'] if e == 'R' else 0.0
            if tp in ('ao', 'am'):
                drop = max(1.0, rng.gauss(P['drop_ap'] + extra + 0.06 * dur, 1.6))
            elif tp == 'ac':
                drop = max(1.0, rng.gauss(P['drop_ap'] - 1.0, 1.0))
            elif tp == 'h':
                if rng.random() < P['hip_sin']:
                    drop = rng.uniform(0.4, 2.6)
                else:
                    drop = max(3.0, rng.gauss(P['drop_hip'] + extra * 0.7, 1.2))
            else:
                drop = rng.uniform(0.0, 1.6)
            if tp == 'rera' or (tp == 'h' and drop < 3.0):
                arousal = True
            else:
                arousal = rng.random() < P['p_ar']
            ev.append(dict(t=s, dur=dur, tipo=tp, etapa=e, pos=pos[s], drop=drop, arousal=arousal))
            libre = s + dur + rng.randint(*P.get('gap', (6, 22)))
            s = libre
        else:
            s += 1
    # despertares espontáneos
    esp = []
    for s in range(N):
        if etapa[s] != 'W' and rng.random() < P['ar_esp'] / 3600.0:
            esp.append(s)
    # SpO2 segundo a segundo
    caida = [0.0] * N
    for x in ev:
        if x['tipo'] == 'rera':
            continue
        t0 = x['t'] + int(0.3 * x['dur'])
        nadir_t = x['t'] + x['dur'] + 7
        d = x['drop']
        for k in range(t0, min(N, nadir_t + 60)):
            if k <= nadir_t:
                v = d * (k - t0) / max(1, nadir_t - t0)
            else:
                v = d * math.exp(-(k - nadir_t) / 9.0)
            caida[k] = max(caida[k], v)
    sp = []
    rr = random.Random(P['semilla'] + 1)
    ruido = 0.0
    for k in range(N):
        ruido = 0.8 * ruido + rr.uniform(-0.08, 0.08)
        sp.append(round(P['base'] - caida[k] + ruido, 1))
    # ronquido por minuto
    ron = [False] * (N // 60 + 1)
    for m in range(N // 60):
        if etapa[m * 60 + 30] != 'W':
            p = P['ron_p'][pos[m * 60 + 30]] * (0.4 if etapa[m * 60 + 30] == 'N3' else 1.0)
            ron[m] = rr.random() < p
    return dict(P=P, clave=clave, seg=seg, N=N, etapa=etapa, pos=pos, ev=ev, esp=esp, sp=sp, ron=ron)


def odi(sp, etapa, umbral=3):
    """Cuenta caídas de la saturación de al menos `umbral` puntos respecto del máximo de los 2 min previos (solo sueño)."""
    n, k, en = 0, 0, False
    ref = 0
    N = len(sp)
    for s in range(N):
        a = max(0, s - 120)
        if not en:
            ref = max(sp[a:s + 1])
            if etapa[s] != 'W' and sp[s] <= ref - umbral:
                n += 1
                en = True
        else:
            if sp[s] >= ref - 1:
                en = False
    return n


def resumen(S, modo='psg'):
    """modo 'psg': por hora de sueño. modo 'pg': por hora de registro, sin etapas (solo lo que ve una poligrafía)."""
    ev, etapa, pos, N, sp, seg = S['ev'], S['etapa'], S['pos'], S['N'], S['sp'], S['seg']
    r = {}
    sueno = [s for s in range(N) if etapa[s] != 'W']
    tst = len(sueno) / 60.0
    tib = N / 60.0
    r['TIB'], r['TST'] = tib, tst
    r['eficiencia'] = 100 * tst / tib
    lat = seg[0][2] / 60.0
    r['latencia'] = lat
    rem = next((a for e, a, b in seg if e == 'R'), None)
    r['latencia REM'] = (rem / 60.0 - lat) if rem is not None else None
    r['WASO'] = sum(b - a for e, a, b in seg if e == 'W') / 60.0 - lat
    for e in ('N1', 'N2', 'N3', 'R'):
        m = sum(b - a for ee, a, b in seg if ee == e) / 60.0
        r['min ' + e] = m
        r['% ' + e] = 100 * m / tst
    cuenta = {tp: sum(1 for x in ev if x['tipo'] == tp) for tp, _ in TIPOS}
    r['n'] = cuenta
    hip_des = [x for x in ev if x['tipo'] == 'h' and x['drop'] >= 3.0]
    hip_ar = [x for x in ev if x['tipo'] == 'h' and x['drop'] < 3.0]
    r['hip con desaturación'], r['hip solo despertar'] = len(hip_des), len(hip_ar)
    apn = [x for x in ev if x['tipo'] in ('ao', 'am', 'ac')]
    r['n IAH'] = len(apn) + cuenta['h']
    r['n REI'] = len(apn) + len(hip_des)                    # lo que ve una poligrafía: sin despertares
    r['n IAH4'] = len(apn) + sum(1 for x in ev if x['tipo'] == 'h' and x['drop'] >= 4.0)
    base_h = tst if modo == 'psg' else tib
    r['base horas'] = base_h / 60.0
    r['IAH'] = r['n IAH'] / (tst / 60.0)
    r['IAH4'] = r['n IAH4'] / (tst / 60.0)
    r['IDR'] = (r['n IAH'] + cuenta['rera']) / (tst / 60.0)
    r['REI'] = r['n REI'] / (tib / 60.0)                     # por hora de registro
    r['REI sobre TST'] = r['n REI'] / (tst / 60.0)
    r['IAI'] = len(apn) / (tst / 60.0)
    r['durmax'] = max(x['dur'] for x in ev if x['tipo'] != 'rera')
    r['durmed'] = sum(x['dur'] for x in ev if x['tipo'] != 'rera') / max(1, len([x for x in ev if x['tipo'] != 'rera']))
    nar = sum(1 for x in ev if x['arousal']) + len(S['esp'])
    r['n despertares'] = nar
    r['IDespertares'] = nar / (tst / 60.0)
    r['ODI3'] = odi(sp, etapa, 3)
    r['IDO3'] = r['ODI3'] / (tst / 60.0)
    r['IDO3 reg'] = r['ODI3'] / (tib / 60.0)
    r['ODI4'] = odi(sp, etapa, 4)
    r['IDO4'] = r['ODI4'] / (tst / 60.0)
    if modo == 'psg':
        vals = [round(sp[s]) for s in sueno]
        r['T90'] = 100 * sum(1 for v in vals if v < 90) / len(vals)
        r['T88'] = 100 * sum(1 for v in vals if v <= 88) / len(vals)
    else:
        vals = [round(v) for v in sp]
        r['T90'] = 100 * sum(1 for v in vals if v < 90) / len(vals)
    r['SpO2 media'] = sum(vals) / len(vals)
    r['SpO2 min'] = min(vals)
    for p in ('supino', 'izquierda', 'derecha'):
        m_reg = sum(1 for s in range(N) if pos[s] == p) / 60.0
        m_sue = sum(1 for s in sueno if pos[s] == p) / 60.0
        r['min ' + p] = m_reg
        r['REI ' + p] = sum(1 for x in apn + hip_des if x['pos'] == p) / (m_reg / 60.0) if m_reg else 0
        r['IAH ' + p] = sum(1 for x in apn + [y for y in ev if y['tipo'] == 'h'] if x['pos'] == p) / (m_sue / 60.0) if m_sue else 0
    for e in ('N1', 'N2', 'N3', 'R'):
        h = r['min ' + e] / 60.0
        r['IAH ' + e] = sum(1 for x in apn + [y for y in ev if y['tipo'] == 'h'] if x['etapa'] == e) / h if h else 0
    nrem_h = (tst - r['min R']) / 60.0
    r['IAH NREM'] = sum(1 for x in apn + [y for y in ev if y['tipo'] == 'h'] if x['etapa'] != 'R') / nrem_h
    s2 = sum(1 for k in range(min(7200, N)) if etapa[k] != 'W') / 3600.0
    r['sueño primeras 2 h'] = s2 * 60
    r['IAH primeras 2 h'] = sum(1 for x in apn + [y for y in ev if y['tipo'] == 'h'] if x['t'] < 7200) / s2
    r['ronquido %'] = 100 * sum(S['ron']) / tib if modo == 'pg' else 100 * sum(S['ron']) / tst
    return r


def gravedad(i):
    return 'normal' if i < 5 else 'leve' if i < 15 else 'moderada' if i < 30 else 'grave'



def ventana(S, t0, dur, fs=20):
    """Flujo (presión nasal), tórax, abdomen, EEG, EMG, ronquido: generados a partir de los eventos reales."""
    P = S['P']
    rng = random.Random(P['semilla'] + t0)
    f = 0.25
    out = {k: [] for k in ('flujo', 'torax', 'abd', 'eeg', 'emg', 'ron')}
    evs = [x for x in S['ev'] if x['t'] + x['dur'] + 10 >= t0 and x['t'] <= t0 + dur]
    ph0 = rng.random() * 6
    # fase respiratoria acumulada
    ph = ph0
    et = S['etapa'][min(S['N'] - 1, t0 + dur // 2)]
    eeg_amp = {'W': 0.25, 'N1': 0.35, 'N2': 0.45, 'N3': 0.9, 'R': 0.3}[et]
    for i in range(int(dur * fs)):
        t = t0 + i / fs
        env_f, env_e, par, lim, silencio_e = 1.0, 1.0, 0.0, False, False
        arousal_on = False
        ron_amp = 0.0
        for x in evs:
            a, b = x['t'], x['t'] + x['dur']
            if a <= t <= b:
                u = (t - a) / x['dur']
                tp = x['tipo']
                if tp == 'ao':
                    env_f, env_e, par = 0.05, 0.5 + 1.1 * u, min(1.0, 0.4 + 0.8 * u)
                elif tp == 'ac':
                    env_f, env_e = 0.05, 0.05
                elif tp == 'am':
                    env_f = 0.05
                    if u < 0.4:
                        env_e = 0.05
                    else:
                        env_e, par = 0.5 + 1.1 * (u - 0.4) / 0.6, min(1.0, 0.4 + 0.8 * (u - 0.4) / 0.6)
                elif tp == 'h':
                    env_f, env_e, par, lim = 0.5, 0.8 + 0.4 * u, 0.3, True
                else:  # RERA: flujo casi normal, aplanado; esfuerzo creciente
                    env_f, env_e, par, lim = 0.8, 0.8 + 0.7 * u, 0.4, True
            elif b < t <= b + 4:
                if x['tipo'] != 'rera':
                    env_f, env_e = 1.45, 1.4
                    ron_amp = 0.9
            if x['arousal'] and b - 1 <= t <= b + 5:
                arousal_on = True
        for s0 in S['esp']:
            if s0 - 0 <= t <= s0 + 5:
                arousal_on = True
        if S['ron'][min(len(S['ron']) - 1, int(t // 60))] and ron_amp == 0.0:
            ron_amp = 0.45
        ph += 2 * math.pi * f / fs * (1 + 0.04 * math.sin(t / 3.1))
        base = math.sin(ph)
        sn = base
        if lim and base > 0:
            sn = min(base, 0.6) / 0.6 * 0.85
        flujo = env_f * sn + rng.uniform(-0.03, 0.03)
        torax = env_e * base + rng.uniform(-0.03, 0.03)
        abd = env_e * math.sin(ph + 0.2) * (1 - 2 * par) + rng.uniform(-0.03, 0.03)
        insp = max(0.0, base)
        ron = ron_amp * insp * rng.uniform(-1, 1) * (1.0 if env_f > 0.3 else 0.0)
        # EEG: delta/theta de fondo; ráfaga alfa en el despertar
        if arousal_on:
            eeg = 0.28 * math.sin(2 * math.pi * 10.5 * t) + 0.12 * rng.uniform(-1, 1)
            emg = rng.uniform(-1, 1) * 0.9
        else:
            eeg = eeg_amp * (0.6 * math.sin(2 * math.pi * 1.1 * t + 1) + 0.25 * math.sin(2 * math.pi * 5.5 * t)) \
                + 0.1 * rng.uniform(-1, 1)
            emg = rng.uniform(-1, 1) * (0.08 if et in ('R',) else 0.22)
        out['flujo'].append(flujo)
        out['torax'].append(torax)
        out['abd'].append(abd)
        out['eeg'].append(eeg)
        out['emg'].append(emg)
        out['ron'].append(ron)
    return out




# ── LabSim: el caso ─────────────────────────────────────────────────────────

PERFILES_LIBRO = (
    ('roncador', 'Roncador simple (cap. 38.1)'),
    ('moderado', 'SAOS moderado con obstrucción nasal (cap. 38.2)'),
    ('grave', 'SAOS grave (cap. 38.3)'),
    ('dudosa', 'Poligrafía que no alcanza: hipopneas con despertar (cap. 38.4)'),
)
# La poligrafía en la casa del paciente de 38.4 fue otra noche (dudosa_pg).
PG_LIBRO = {'dudosa': 'dudosa_pg'}
ESTUDIOS = (('psg', 'Polisomnografía (laboratorio)'), ('pg', 'Poligrafía respiratoria (domicilio)'))

# Perfil personalizado: (clave, mínimo, máximo, por defecto).
PARAMETROS = (
    ('tasa', 0, 120, 15.0),          # eventos/h en N2, decúbito lateral
    ('rem', 0.5, 5, 2.0),            # veces la tasa en REM
    ('supino', 0.5, 4, 1.6),         # veces la tasa en supino
    ('obstructivas', 0, 1, 0.30),    # fracciones de cada tipo (se normalizan)
    ('mixtas', 0, 1, 0.05),
    ('centrales', 0, 1, 0.02),
    ('hipopneas', 0, 1, 0.63),
    ('rera', 0, 1, 0.0),
    ('caida_apnea', 1, 20, 6.0),     # puntos de SpO2
    ('caida_hipopnea', 3, 12, 4.5),
    ('hip_sin_desaturar', 0, 1, 0.2),  # hipopneas que solo dan despertar
    ('spo2_basal', 85, 99, 95.5),
    ('tib', 300, 600, 470),          # minutos en cama
    ('semilla', 1, 99999, 1),
)


def _rango(v, lo, hi, nombre):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f'{nombre}: no es un número') from None
    if not (math.isfinite(x) and lo <= x <= hi):
        raise ValueError(f'{nombre}: fuera de {lo}-{hi}')
    return x


def normaliza(bloque):
    """Valida el bloque SUENO del caso (ValueError si no sirve). Forma:
    {'perfil': clave del libro | 'personalizado', 'params': {...} (solo
    personalizado), 'canula_suelta': None | {'desde', 'hasta'} (minutos desde
    que apaga la luz, solo en la poligrafía de la casa), 'cpap': None |
    {'p_eficaz', 'supino', 'rem', 'boca', 'talla'} (la titulación, nasal/cpap.py;
    lo que falta sale del perfil)}."""
    if not isinstance(bloque, dict):
        raise ValueError('SUENO no es un objeto')
    perfil = bloque.get('perfil')
    out = {'perfil': perfil, 'params': None, 'canula_suelta': None}
    if perfil == 'personalizado':
        p = bloque.get('params') or {}
        if not isinstance(p, dict):
            raise ValueError('params no es un objeto')
        out['params'] = {k: _rango(p.get(k, d), lo, hi, k) for k, lo, hi, d in PARAMETROS}
        if sum(out['params'][k] for k in ('obstructivas', 'mixtas', 'centrales', 'hipopneas', 'rera')) <= 0:
            raise ValueError('la mezcla de tipos suma cero')
    elif perfil not in dict(PERFILES_LIBRO):
        raise ValueError(f'perfil desconocido: {perfil}')
    c = bloque.get('canula_suelta')
    if isinstance(c, dict) and c.get('desde') is not None:
        desde = _rango(c.get('desde'), 0, 600, 'canula_suelta.desde')
        hasta = _rango(c.get('hasta'), desde + 1, 601, 'canula_suelta.hasta')
        out['canula_suelta'] = {'desde': desde, 'hasta': hasta}
    c = bloque.get('cpap')
    out['cpap'] = None
    if isinstance(c, dict) and c:
        cp = {}
        for k, lo, hi in (('p_eficaz', 4, 20), ('supino', 0, 6), ('rem', 0, 6)):
            if c.get(k) is not None:
                cp[k] = _rango(c[k], lo, hi, f'cpap.{k}')
        if 'boca' in c:
            cp['boca'] = bool(c['boca'])
        if c.get('talla') in ('S', 'M', 'L'):
            cp['talla'] = c['talla']
        out['cpap'] = cp or None
    return out


def desde_caso(data):
    """`cases.data` -> {'sueno', 'edad', 'sexo'} o None si el caso no trae
    estudio de sueño (o lo trae mal escrito)."""
    if not isinstance(data, dict) or not isinstance(data.get('SUENO'), dict):
        return None
    try:
        bloque = normaliza(data['SUENO'])
    except ValueError as exc:
        print(f'sueño: el caso trae SUENO inválido: {exc}')
        return None
    return {'sueno': bloque, 'edad': data.get('edad'), 'sexo': 'F' if data.get('gender') == 1 else 'M'}


def perfil_personalizado(p):
    """El diccionario de `simular` para un perfil que no es del libro: una
    arquitectura normal (ciclos de ~90 min, N3 al comienzo, REM que crece)
    y los eventos del docente."""
    rng = random.Random(int(p['semilla']) * 7919)
    tib = int(p['tib'])
    seq = [('W', rng.randint(12, 24))]
    n3 = [36, 24, 12, 6, 0, 0]
    rem = [12, 18, 24, 28, 30, 30]
    k = 0
    while sum(d for _e, d in seq) < tib:
        seq += [('N1', rng.randint(4, 8)), ('N2', rng.randint(20, 32))]
        if n3[min(k, 5)]:
            seq += [('N3', n3[min(k, 5)] + rng.randint(-4, 4)), ('N2', rng.randint(10, 18))]
        seq += [('R', rem[min(k, 5)] + rng.randint(-4, 4)), ('W', rng.randint(2, 8))]
        k += 1
    pos, t = [], 0
    lado = rng.choice(('izquierda', 'derecha'))
    while t < tib:
        d = rng.randint(60, 140)
        pos.append((t, min(tib, t + d), 'supino' if len(pos) % 2 == 0 else lado))
        lado = 'derecha' if lado == 'izquierda' else 'izquierda'
        t += d
    tasa = p['tasa']
    return dict(
        titulo='Perfil personalizado', semilla=int(p['semilla']), tib=tib, seq=seq, pos=pos,
        tasa=dict(N1=tasa * 1.2, N2=tasa, N3=tasa * 0.4, R=tasa * p['rem']),
        fpos=dict(supino=p['supino'], izquierda=0.6, derecha=0.7),
        mix={k: v for k, v in (('ao', p['obstructivas']), ('am', p['mixtas']), ('ac', p['centrales']),
                               ('h', p['hipopneas']), ('rera', p['rera'])) if v > 0},
        drop_ap=p['caida_apnea'], drop_hip=p['caida_hipopnea'], hip_sin=p['hip_sin_desaturar'],
        rem_extra=1.5, base=p['spo2_basal'], p_ar=0.85, ar_esp=8.0,
        ron_p=dict(supino=min(1.0, 0.4 + tasa / 40), izquierda=min(1.0, 0.2 + tasa / 80), derecha=min(1.0, 0.25 + tasa / 70)),
        dur_ap=(10, 30), dur_h=(10, 30),
        # Con muchos eventos, la pausa corta del perfil grave del libro: si no,
        # el IAH no pasa de ~45 por falta de tiempo entre uno y otro.
        **({'gap': (3, 10)} if tasa >= 40 else {}))


def noche(sueno, estudio):
    """La noche simulada del caso para ese estudio ('psg' o 'pg'). La
    poligrafía se hace en la casa: puede ser otra noche (38.4) y la cánula
    se puede soltar."""
    if sueno['perfil'] == 'personalizado':
        S = simular('personalizado', perfil_personalizado(sueno['params']))
    else:
        clave = PG_LIBRO.get(sueno['perfil'], sueno['perfil']) if estudio == 'pg' else sueno['perfil']
        S = simular(clave)
    S['estudio'] = estudio
    c = sueno['canula_suelta'] if estudio == 'pg' else None
    S['canula_suelta'] = None if not c else (int(c['desde'] * 60), int(c['hasta'] * 60))
    return S


# ── Lo que registran los sensores ───────────────────────────────────────────

# (clave, nombre, en la poligrafía): lo que se monta (H31, tabla de canales).
SENSORES = (
    ('eeg', 'EEG (F4, C4, O2 con M1)', False),
    ('eog', 'EOG (E1, E2)', False),
    ('emg', 'EMG mentoniano', False),
    ('termico', 'Sensor térmico oronasal', False),
    ('canula', 'Cánula de presión nasal', True),
    ('torax', 'Banda de tórax', True),
    ('abd', 'Banda de abdomen', True),
    ('spo2', 'Oxímetro de pulso', True),
    ('ron', 'Micrófono de ronquido', True),
    ('pos', 'Sensor de posición', True),
)
NOMBRE_SENSOR = {k: n for k, n, _pg in SENSORES}


def sensores_del_estudio(estudio):
    return [k for k, _n, pg in SENSORES if estudio == 'psg' or pg]


def senales(S, t0, dur, montados, fs=10):
    """Los canales de una ventana [t0, t0+dur) s, como los ve el equipo: lo
    no montado no está (None) y la cánula suelta da una línea plana."""
    v = ventana(S, int(t0), int(dur), fs=fs)
    n = len(v['flujo'])
    rng = random.Random(S['P']['semilla'] * 31 + int(t0))
    out = {}
    # El térmico no es proporcional al flujo: cae menos en la hipopnea.
    termico = [math.copysign(abs(f) ** 0.8, f) for f in v['flujo']]
    canula = list(v['flujo'])
    suelta = S.get('canula_suelta')
    if suelta:
        for i in range(n):
            if suelta[0] <= t0 + i / fs < suelta[1]:
                canula[i] = rng.uniform(-0.02, 0.02)
    # El EOG: rápidos en REM, lentos en N1, opuestos entre E1 y E2.
    eog = []
    sac = 0.0
    for i in range(n):
        t = t0 + i / fs
        e = S['etapa'][min(S['N'] - 1, int(t))]
        if e == 'R' and rng.random() < 0.04:
            sac = rng.choice((-1, 1)) * rng.uniform(0.5, 1.0)
        elif e == 'N1':
            sac = 0.4 * math.sin(2 * math.pi * 0.15 * t)
        elif e != 'R':
            sac *= 0.9
        eog.append(sac + rng.uniform(-0.04, 0.04))
    sp = S['sp']
    spo2 = []
    for i in range(n):
        t = t0 + i / fs
        a = min(S['N'] - 1, int(t))
        b = min(S['N'] - 1, a + 1)
        spo2.append(sp[a] + (sp[b] - sp[a]) * (t - int(t)))
    canales = {'eeg': v['eeg'], 'eog': eog, 'emg': v['emg'], 'termico': termico, 'canula': canula,
               'torax': v['torax'], 'abd': v['abd'], 'spo2': spo2, 'ron': v['ron']}
    for k, x in canales.items():
        out[k] = x if k in montados else None
    out['t'] = [t0 + i / fs for i in range(n)]
    return out


def posicion_en(S, t):
    return S['pos'][min(S['N'] - 1, max(0, int(t)))]


def etapa_en(S, t):
    return S['etapa'][min(S['N'] - 1, max(0, int(t)))]


# ── La puntuación ───────────────────────────────────────────────────────────

APNEAS = ('ao', 'am', 'ac')
NOMBRE_TIPO = dict(TIPOS)
REGLAS = (('3', 'Recomendada: caída ≥ 30 % con desaturación ≥ 3 % o despertar'),
          ('4', 'Aceptable: caída ≥ 30 % con desaturación ≥ 4 %'))


def auto_puntuar(S, montados, semilla):
    """Lo que propone el programa del equipo, con sus errores: sin EEG no ve
    los despertares (las hipopneas que solo dan despertar no salen), se le
    escapa alguna hipopnea, confunde alguna obstructiva con central si el
    esfuerzo es débil, no puntúa RERA, y donde la cánula se soltó ve apneas
    que no existen. Sin cánula ni térmico no puntúa nada."""
    rng = random.Random(semilla)
    if 'canula' not in montados and 'termico' not in montados:
        return []
    con_eeg = 'eeg' in montados
    out = []
    suelta = S.get('canula_suelta')
    for x in S['ev']:
        tp = x['tipo']
        if tp == 'rera':
            continue
        if suelta and suelta[0] <= x['t'] < suelta[1]:
            continue
        if tp == 'h':
            if x['drop'] < 3 and not con_eeg:
                continue
            if rng.random() < 0.06:
                continue
        elif tp == 'ao' and rng.random() < 0.04:
            tp = 'ac'
        elif tp == 'ac' and rng.random() < 0.15:
            tp = 'ao'
        out.append({'t': x['t'], 'dur': x['dur'], 'tipo': tp, 'auto': True})
    if suelta and 'termico' not in montados:
        t = suelta[0] + rng.randint(5, 30)
        while t < suelta[1] - 12:
            dur = rng.randint(12, 40)
            out.append({'t': t, 'dur': min(dur, suelta[1] - t), 'tipo': 'ao', 'auto': True, 'falso': True})
            t += dur + rng.randint(4, 25)
    out.sort(key=lambda e: e['t'])
    return out


def caida(S, ev):
    """Puntos de SpO2 que cae con el evento: el máximo de los 2 min previos
    contra el mínimo hasta 30 s después de terminar."""
    sp = S['sp']
    a = max(0, int(ev['t']) - 120)
    b = min(S['N'], int(ev['t'] + ev['dur']) + 30)
    if b <= int(ev['t']):
        return 0.0
    return max(sp[a:int(ev['t']) + 1]) - min(sp[int(ev['t']):b])


def en_excluido(t, excluidos):
    return any(a <= t < b for a, b in excluidos)


def indices(S, eventos, regla='3', excluidos=()):
    """Los índices con la puntuación del alumno (`eventos`: {'t', 'dur',
    'tipo'}), descontando los tramos excluidos [(desde, hasta) s]. En la
    polisomnografía, por hora de sueño; en la poligrafía, por hora de
    registro válido (REI)."""
    psg = S['estudio'] == 'psg'
    N, etapa, pos, sp = S['N'], S['etapa'], S['pos'], S['sp']
    excl = [(int(a), int(b)) for a, b in excluidos]
    validos = [s for s in range(N) if not en_excluido(s, excl)]
    sueno = [s for s in validos if etapa[s] != 'W']
    base = sueno if psg else validos
    horas = len(base) / 3600
    r = {'estudio': S['estudio'], 'regla': regla}
    evs = [e for e in eventos if not en_excluido(e['t'], excl) and (not psg or etapa_en(S, e['t']) != 'W')]
    for e in evs:
        e['caida'] = round(caida(S, e), 1)
    cuenta = {tp: sum(1 for e in evs if e['tipo'] == tp) for tp, _ in TIPOS}
    hip = [e for e in evs if e['tipo'] == 'h' and (regla == '3' or e['caida'] >= 4)]
    apn = [e for e in evs if e['tipo'] in APNEAS]
    r['n'] = cuenta
    r['hipopneas contadas'] = len(hip)
    r['horas'] = horas
    cuenta_iah = apn + hip
    r['IAH'] = len(cuenta_iah) / horas if horas else None
    r['IAI'] = len(apn) / horas if horas else None
    r['IDR'] = (len(cuenta_iah) + cuenta['rera']) / horas if horas and psg else None
    for p in ('supino', 'izquierda', 'derecha'):
        h = sum(1 for s in base if pos[s] == p) / 3600
        r['min ' + p] = h * 60
        r['IAH ' + p] = sum(1 for e in cuenta_iah if posicion_en(S, e['t']) == p) / h if h >= 0.25 else None
    if psg:
        h_rem = sum(1 for s in sueno if etapa[s] == 'R') / 3600
        h_nrem = len(sueno) / 3600 - h_rem
        r['IAH REM'] = sum(1 for e in cuenta_iah if etapa_en(S, e['t']) == 'R') / h_rem if h_rem else None
        r['IAH NREM'] = sum(1 for e in cuenta_iah if etapa_en(S, e['t']) != 'R') / h_nrem if h_nrem else None
    # Oximetría: la del equipo, sobre lo válido.
    en_base = bytearray(N)
    for s in base:
        en_base[s] = 1
    etapa_ox = [etapa[s] if en_base[s] else 'W' for s in range(N)] if psg else \
        ['N2' if en_base[s] else 'W' for s in range(N)]
    r['IDO3'] = odi(sp, etapa_ox, 3) / horas if horas else None
    r['IDO4'] = odi(sp, etapa_ox, 4) / horas if horas else None
    vals = [round(sp[s]) for s in base] or [0]
    r['SpO2 media'] = sum(vals) / len(vals)
    r['SpO2 min'] = min(vals)
    r['T90'] = 100 * sum(1 for v in vals if v < 90) / len(vals)
    r['min validos'] = len(validos) / 60
    r['min registro'] = N / 60
    if psg:
        seg = S['seg']
        tst = len([s for s in range(N) if etapa[s] != 'W']) / 60
        r['TIB'] = N / 60
        r['TST'] = tst
        r['eficiencia'] = 100 * tst / (N / 60)
        lat = seg[0][2] / 60
        r['latencia'] = lat
        rem = next((a for e, a, b in seg if e == 'R'), None)
        r['latencia REM'] = (rem / 60 - lat) if rem is not None else None
        r['WASO'] = sum(b - a for e, a, b in seg if e == 'W') / 60 - lat
        for e in ('N1', 'N2', 'N3', 'R'):
            r['% ' + e] = 100 * sum(b - a for ee, a, b in seg if ee == e) / 60 / tst if tst else 0
    r['ronquido %'] = 100 * sum(S['ron']) / max(1, len(S['ron']))
    return r


def gravedad_clave(iah):
    return None if iah is None else ('normal' if iah < 5 else 'leve' if iah < 15 else 'moderada' if iah < 30 else 'grave')
