"""Titulación manual de CPAP (H32 del libro): la noche en el laboratorio con
la presión que va subiendo el alumno.

- **El paciente** es el del estudio de sueño (nasal/sueno.py): la misma
  arquitectura, posición, tasa de eventos y mezcla de tipos de su noche. Lo
  nuevo es la **presión eficaz** del caso, la que abre la vía en decúbito
  lateral y NREM; en supino y en REM hace falta más (`supino`, `rem`). Con
  la presión real por debajo de la eficaz los eventos siguen, cada tipo con
  su umbral: las apneas desaparecen primero (2 cmH2O antes de la eficaz),
  después las hipopneas (1 antes), los RERA (0,5 antes) y al final el
  ronquido (en la eficaz), como en el ejemplo de H32 (eventos hasta 8,
  ronquido hasta 9, presión elegida 10). Muy por encima de la eficaz
  aparecen apneas centrales y despertares.
- **La interfaz y la fuga**: la fuga crece con la presión; si la talla no
  es la que le calza, o si respira por la boca con una mascarilla nasal o
  almohadillas, la fuga sube y la presión que llega a la vía es menor que la
  del equipo (cap. 38: "la boca como salida").
- **La noche avanza por segundos** (`Titulacion.avanzar`) con un solo
  generador: la misma secuencia de cambios de presión rehace la misma noche
  (así se retoma la atención).
- **Lo que se informa** (`por_presion`, `grado`): cada escalón con sus
  minutos, sueño, REM en supino, eventos, IDR, SpO2 mínima, ronquido y
  fuga, y el grado de Kushida y cols. (2008) para una presión.
"""

import math
import random

from nasal import sueno as Z

INTERFACES = (('nasal', 'Mascarilla nasal'), ('almohadillas', 'Almohadillas nasales'),
              ('oronasal', 'Mascarilla oronasal'))
TALLAS = ('S', 'M', 'L')
P_MIN, P_MAX = 4, 20               # Kushida 2008: desde 4, hasta 20 cmH2O
INTERVALO_MIN_S = 5 * 60           # al menos 5 min entre cambios
# Criterios para subir en el período (Kushida 2008): 2 apneas, 3 hipopneas,
# 5 RERA o 3 minutos de ronquido.
CRITERIOS = {'apneas': 2, 'hipopneas': 3, 'rera': 5, 'ronquido_min': 3}
GRADOS = (('optima', 'Óptima'), ('buena', 'Buena'), ('adecuada', 'Adecuada'),
          ('inaceptable', 'Inaceptable'))
# Umbral de cada tipo respecto de la presión eficaz (cmH2O).
UMBRAL = {'ao': -2.0, 'am': -2.0, 'h': -1.0, 'rera': -0.5, 'ron': 0.0}
PRESION_PERFIL = {'roncador': 7, 'moderado': 10, 'grave': 13, 'dudosa': 8}
BOCA_PERFIL = {'moderado': True}     # 38.2: duerme con la boca abierta


def _rango(v, lo, hi, nombre):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f'{nombre}: no es un número') from None
    if not (math.isfinite(x) and lo <= x <= hi):
        raise ValueError(f'{nombre}: fuera de {lo}-{hi}')
    return x


def parametros(sueno_bloque):
    """La parte CPAP del bloque SUENO, con lo que falta según el perfil:
    {'p_eficaz', 'supino', 'rem', 'boca', 'talla'}."""
    perfil = sueno_bloque['perfil']
    c = sueno_bloque.get('cpap') or {}
    if perfil == 'personalizado':
        defecto = min(18.0, 5 + sueno_bloque['params']['tasa'] / 6)
    else:
        defecto = PRESION_PERFIL[perfil]
    return {'p_eficaz': _rango(c.get('p_eficaz', defecto), 4, 20, 'cpap.p_eficaz'),
            'supino': _rango(c.get('supino', 2), 0, 6, 'cpap.supino'),
            'rem': _rango(c.get('rem', 1.5), 0, 6, 'cpap.rem'),
            'boca': bool(c.get('boca', BOCA_PERFIL.get(perfil, False))),
            'talla': c.get('talla') if c.get('talla') in TALLAS else 'M'}


def fuga(presion, interfaz, talla, cp):
    """Fuga no intencional (L/min) con esa presión y esa interfaz."""
    f = 4 + 0.5 * presion
    if talla != cp['talla']:
        f += 12 + 0.8 * presion
    if cp['boca'] and interfaz != 'oronasal':
        f += 20 + 1.5 * presion
    return f


def presion_real(presion, f):
    """Lo que llega a la vía: una fuga grande se come parte de la presión."""
    return presion - max(0.0, f - 24) * 0.12


def factor(tipo, p_real, p_ef):
    """Cuánto queda de la tasa de ese tipo de evento con esa presión."""
    umbral = p_ef + UMBRAL[tipo]
    if p_real >= umbral:
        return 0.0
    return min(1.0, (umbral - p_real) / max(1.0, umbral - P_MIN)) ** 1.3


class Titulacion:
    """La noche de titulación. `cambios`: [(segundo, presión)] en orden."""

    def __init__(self, sueno_bloque, semilla, interfaz='nasal', talla='M', presion=P_MIN):
        self.S = Z.noche(sueno_bloque, 'psg')
        self.P = self.S['P']
        self.cp = parametros(sueno_bloque)
        self.interfaz = interfaz
        self.talla = talla
        self.rng = random.Random(f'cpap/{semilla}')
        self.t = 0
        self.presion = presion
        self.cambios = [(0, presion)]
        self.eventos = []              # {'t', 'dur', 'tipo', 'drop', 'presion', 'arousal'}
        self.ronquido = []             # por minuto: (minuto, bool)
        self.fugas = []                # por minuto
        self.caida = [0.0] * self.S['N']
        self._libre = 0
        rr = random.Random(f'cpap/{semilla}/spo2')
        self._ruido = [rr.uniform(-0.08, 0.08) for _ in range(self.S['N'])]

    @property
    def N(self):
        return self.S['N']

    @property
    def terminada(self):
        return self.t >= self.N

    def cambiar(self, presion):
        presion = max(P_MIN, min(P_MAX, presion))
        if presion != self.presion:
            self.presion = presion
            self.cambios.append((self.t, presion))

    def p_eficaz(self, s):
        e, pos = self.S['etapa'][s], self.S['pos'][s]
        return self.cp['p_eficaz'] + (self.cp['supino'] if pos == 'supino' else 0) + \
            (self.cp['rem'] if e == 'R' else 0)

    def avanzar(self, segundos):
        fin = min(self.N, self.t + int(segundos))
        P = self.P
        rng = self.rng
        tipos = list(P['mix'])
        while self.t < fin:
            s = self.t
            e, pos = self.S['etapa'][s], self.S['pos'][s]
            f = fuga(self.presion, self.interfaz, self.talla, self.cp)
            pr = presion_real(self.presion, f)
            pe = self.p_eficaz(s)
            if s % 60 == 0:
                self.fugas.append(f)
                ron = e != 'W' and rng.random() < P['ron_p'][pos] * factor('ron', pr, pe) * (
                    0.4 if e == 'N3' else 1.0)
                self.ronquido.append((s // 60, ron))
            if e != 'W' and s >= self._libre:
                base = P['tasa'][e] * P['fpos'][pos] / 3600
                pesos = []
                for tp in tipos:
                    k = 0.5 if tp == 'ac' else factor('ao' if tp == 'am' else tp, pr, pe)
                    pesos.append(P['mix'][tp] * k)
                # Presión de más: centrales y despertares (tratamiento).
                extra_c = max(0.0, pr - pe - 4) * 3 / 3600
                lam = base * sum(pesos) + extra_c
                if rng.random() < lam:
                    if rng.random() < extra_c / lam:
                        tp = 'ac'
                    else:
                        tp = rng.choices(tipos, pesos)[0]
                    dur = rng.randint(*(P['dur_h'] if tp in ('h', 'rera') else P['dur_ap']))
                    if tp == 'rera':
                        dur = rng.randint(10, 18)
                    # La presión acorta y suaviza lo que queda.
                    alivio = 1 - 0.5 * min(1.0, max(0.0, (pr - P_MIN) / max(1.0, pe - P_MIN)))
                    if tp in ('ao', 'am'):
                        drop = max(1.0, rng.gauss(P['drop_ap'] * alivio + 0.06 * dur, 1.4))
                    elif tp == 'ac':
                        drop = max(1.0, rng.gauss(P['drop_ap'] * 0.6, 1.0))
                    elif tp == 'h':
                        drop = (rng.uniform(0.4, 2.6) if rng.random() < P['hip_sin']
                                else max(3.0, rng.gauss(P['drop_hip'] * alivio + 1, 1.0)))
                    else:
                        drop = rng.uniform(0.0, 1.6)
                    ev = {'t': s, 'dur': dur, 'tipo': tp, 'drop': drop, 'presion': self.presion,
                          'arousal': tp == 'rera' or rng.random() < P['p_ar'], 'etapa': e, 'pos': pos}
                    self.eventos.append(ev)
                    if tp != 'rera':
                        self._desaturar(ev)
                    self._libre = s + dur + rng.randint(*P.get('gap', (6, 22)))
            self.t += 1

    def _desaturar(self, x):
        t0 = x['t'] + int(0.3 * x['dur'])
        nadir = x['t'] + x['dur'] + 7
        for k in range(t0, min(self.N, nadir + 60)):
            v = x['drop'] * (k - t0) / max(1, nadir - t0) if k <= nadir else x['drop'] * math.exp(-(k - nadir) / 9.0)
            self.caida[k] = max(self.caida[k], v)

    def spo2(self, s):
        return round(self.P['base'] - self.caida[s] + self._ruido[s], 1)

    # --- Lo que se mira durante la noche --------------------------------

    def periodo(self, desde, hasta=None):
        """Lo del período [desde, hasta) s: apneas, hipopneas, RERA y
        minutos de ronquido (los criterios para subir)."""
        hasta = self.t if hasta is None else hasta
        evs = [x for x in self.eventos if desde <= x['t'] < hasta]
        return {'apneas': sum(1 for x in evs if x['tipo'] in Z.APNEAS),
                'obstructivas': sum(1 for x in evs if x['tipo'] in ('ao', 'am')),
                'centrales': sum(1 for x in evs if x['tipo'] == 'ac'),
                'hipopneas': sum(1 for x in evs if x['tipo'] == 'h'),
                'rera': sum(1 for x in evs if x['tipo'] == 'rera'),
                'ronquido_min': sum(1 for m, r in self.ronquido if r and desde <= m * 60 < hasta)}

    def cumple_criterio(self, desde, hasta=None):
        p = self.periodo(desde, hasta)
        return (p['obstructivas'] >= CRITERIOS['apneas'] or p['hipopneas'] >= CRITERIOS['hipopneas']
                or p['rera'] >= CRITERIOS['rera'] or p['ronquido_min'] >= CRITERIOS['ronquido_min'])

    def escalones(self):
        """[(desde, hasta, presión)] hasta ahora."""
        out = []
        for i, (t, p) in enumerate(self.cambios):
            hasta = self.cambios[i + 1][0] if i + 1 < len(self.cambios) else self.t
            if hasta > t:
                out.append((t, hasta, p))
        return out

    def por_presion(self):
        """Una fila por presión (juntando los tramos con la misma)."""
        filas = {}
        for a, b, p in self.escalones():
            f = filas.setdefault(p, {'presion': p, 'seg': 0, 'sueno': 0, 'rem_supino': 0, 'ao': 0, 'am': 0,
                                     'ac': 0, 'h': 0, 'rera': 0, 'ron': 0, 'spo2_min': None, 'fugas': [],
                                     'tramos': []})
            f['tramos'].append((a, b))
            f['seg'] += b - a
            for s in range(a, b):
                if self.S['etapa'][s] != 'W':
                    f['sueno'] += 1
                    if self.S['etapa'][s] == 'R' and self.S['pos'][s] == 'supino':
                        f['rem_supino'] += 1
                    v = self.spo2(s)
                    f['spo2_min'] = v if f['spo2_min'] is None else min(f['spo2_min'], v)
            for x in self.eventos:
                if a <= x['t'] < b and self.S['etapa'][x['t']] != 'W':
                    f[x['tipo']] += 1
            f['ron'] += sum(1 for m, r in self.ronquido if r and a <= m * 60 < b)
            f['fugas'] += [self.fugas[m] for m in range(a // 60, min(len(self.fugas), (b + 59) // 60))]
        out = []
        for p in sorted(filas):
            f = filas[p]
            h = f['sueno'] / 3600
            n_iah = f['ao'] + f['am'] + f['ac'] + f['h']
            f['IAH'] = n_iah / h if h else None
            f['IDR'] = (n_iah + f['rera']) / h if h else None
            f['fuga'] = sum(f['fugas']) / len(f['fugas']) if f['fugas'] else None
            del f['fugas']
            out.append(f)
        return out

    def idr_basal(self):
        """El IDR de la polisomnografía diagnóstica (la noche sin CPAP)."""
        return Z.resumen(self.S, 'psg')['IDR']

    def grado(self, presion):
        """Grado de Kushida y cols. (2008) para esa presión, con lo medido."""
        fila = next((f for f in self.por_presion() if f['presion'] == presion), None)
        if fila is None or fila['IDR'] is None or fila['sueno'] < 15 * 60:
            return 'inaceptable'
        basal = self.idr_basal()
        idr = fila['IDR']
        rem_supino = fila['rem_supino'] > 0
        if idr < 5 and rem_supino:
            return 'optima'
        if (idr <= 10 or (basal < 15 and idr <= basal / 2)) and rem_supino:
            return 'buena'
        if idr <= 10 or idr <= basal * 0.25:
            return 'adecuada'
        return 'inaceptable'
