"""Potenciales de estado estable auditivo (ASSR) de 80 Hz.

El ASSR no se lee en el tiempo sino en frecuencia: cada portadora (500, 1000,
2000 y 4000 Hz) viaja modulada en amplitud a una frecuencia propia, y la
respuesta del cerebro aparece como una línea en el espectro del EEG justo en
esa frecuencia de modulación. Ocho portadoras a la vez (cuatro por oído), ocho
líneas distintas en el mismo registro. Detectar es decidir si esa línea
sobresale del ruido de los bins vecinos.

Este módulo es el modelo, sin Qt (lo dibuja AssrPanel):

- Cada época dura 1,024 s (2048 muestras a 2 kHz) y las modulaciones caen
  EXACTO en un bin de la FFT (resolución 0,977 Hz), así que la respuesta
  tiene fase fija de época en época y el ruido no. Por eso el promedio
  crece como la respuesta y el ruido baja como 1/raíz(N).
- Se generan las épocas directamente en el dominio de la frecuencia: bins de
  0 a 200 Hz, ruido gaussiano complejo con el espectro del EEG filtrado a
  30-300 Hz más la respuesta de las ocho portadoras. El rastro en el tiempo
  se reconstruye de ahí (suma de seis a ocho senoides).
- Normalización: un bin de módulo A reconstruye una senoide de amplitud A
  (µV). El ruido de cada bin tiene E|n|² = σ².
- Detección: razón F del bin de la modulación contra los bins vecinos (el
  ruido que hay "al lado", sin respuesta), y Rayleigh sobre las fases de las
  épocas. Con F(2, 2·vecinos) la cola tiene forma cerrada y no hace falta
  scipy.

El umbral fisiológico del ASSR queda por ENCIMA del conductual (hay que
sumar el nivel mínimo para sincronizar al generador), y el equipo informa
restando una corrección por frecuencia al umbral hallado: eso es el dB eHL
("estimated hearing level"). La corrección es calibrable (ver
DEFAULT_EHL_CORRECTION): es un criterio de trabajo, no una cifra de un
fabricante.
"""
import numpy as np

from abr.ABR_generator import INTERAURAL_ATTENUATION
from core.rng import case_fingerprint, stable_seed

FS = 2000.0
N_SAMPLES = 2048
EPOCH_S = N_SAMPLES / FS
DF = FS / N_SAMPLES
F_MAX = 200.0
N_BINS = int(F_MAX / DF) + 1

CARRIERS = (500, 1000, 2000, 4000)
SIDES = ('OD', 'OI')
# Bin de la modulación de cada portadora. Distintos entre oídos y entre
# portadoras, separados por dos bins como mínimo para que cada línea tenga
# ruido limpio al lado.
FM_BIN = {'OD': (82, 90, 98, 106), 'OI': (84, 92, 100, 108)}

LEVEL_MIN, LEVEL_MAX, LEVEL_STEP = 0, 120, 5
AUTO_STEP = 10
MAX_EPOCHS = 1500
MIN_EPOCHS = 30
# Alfa más estricto que el 5 % de rutina: el equipo mira el registro varias
# veces mientras promedia, y cada mirada es otra oportunidad de un falso
# positivo (con 0,05 y 60 miradas, 1 de cada 3 líneas sin respuesta se
# "detectaba" en una corrida larga).
ALPHA = 0.005
# Ruido residual (nV) por debajo del cual "no hay respuesta" es una
# conclusión y no un "no concluyente".
NOISE_CRITERION_NV = 12.0

# Corrección nHL -> HL de los tone bursts del ABR: es la misma tabla del
# backend (CaseProfile::STIM_NHL_CORRECTION). El caso trae el umbral del
# burst en nHL; el conductual en HL es ese valor menos esta corrección.
BURST_NHL_CORRECTION = {500: 20.0, 1000: 15.0, 2000: 10.0, 4000: 10.0}
FALLBACK_NHL_CORRECTION = 10.0

# Cuánto queda el umbral del ASSR por encima del conductual en un oído
# normal, y cuánto se achica con la pérdida (el reclutamiento acerca los
# dos umbrales). Valores de trabajo.
PHYS_OFFSET_DB = {500: 14.0, 1000: 11.0, 2000: 9.0, 4000: 11.0}
OFFSET_SHRINK = 0.5
OFFSET_SHRINK_HL = 70.0
# Corrección que aplica el equipo para informar en eHL. Arranca igual al
# offset de un oído normal; el docente la calibra.
DEFAULT_EHL_CORRECTION = {500: 15.0, 1000: 12.0, 2000: 10.0, 4000: 10.0}

# Amplitud máxima de la respuesta (µV) y qué tan rápido se alcanza con el
# nivel de sensación (dB).
AMP_SAT_UV = {500: 0.130, 1000: 0.110, 2000: 0.090, 4000: 0.070}
AMP_TAU_DB = 28.0
# Retardo de grupo (s): la fase de la línea es -2π·fm·retardo.
GROUP_DELAY_S = {500: 0.022, 1000: 0.020, 2000: 0.017, 4000: 0.015}

# EEG de fondo por bin y por época (µV) a 90 Hz en un registro tranquilo,
# y cómo cae con la frecuencia.
NOISE_UV = 0.30
NOISE_SLOPE = 0.8
# Pasa-alto de 30 Hz y pasa-bajo de 300 Hz del protocolo.
HIGHPASS_HZ = 30.0
LOWPASS_HZ = 300.0
# Red eléctrica (Chile, 50 Hz) en µV por bin, escalada por la impedancia.
LINE_HZ = 50.0

# Artefactos de movimiento: probabilidad por época y tamaño relativo.
ART_P_BASE = 0.03
ART_P_INQUIETUD = 0.25
ART_SCALE = (4.0, 14.0)
# Pico de una época normal (µV) para el rechazo, en el canal filtrado.
EPOCH_PEAK_UV = 8.0


def fm_hz(side, carrier):
    """Frecuencia de modulación (Hz) de esa portadora en ese oído."""
    return FM_BIN[side][CARRIERS.index(carrier)] * DF


def channels():
    """Las ocho portadoras: (oído, portadora)."""
    return [(s, f) for s in SIDES for f in CARRIERS]


def behavioural_threshold(case, carrier):
    """Umbral conductual (dB HL) que el caso implica a esa frecuencia.

    None = el oído no responde a ningún nivel del equipo. Si el caso no trae
    datos para el oído, ValueError: sin datos reales no se genera nada.
    """
    if not isinstance(case, dict) or not case:
        raise ValueError('sin datos')
    tabla = case.get('umbral_por_estimulo') or {}
    clave = f'tone_burst_{carrier}Hz'
    if clave in tabla:
        nhl = tabla[clave]
        if nhl is None:
            return None
        return max(float(nhl) - BURST_NHL_CORRECTION[carrier], 0.0)
    if case.get('umbral') is not None:
        return max(float(case['umbral']) - FALLBACK_NHL_CORRECTION, 0.0)
    raise ValueError('sin datos')


def physiological_threshold(hl, carrier):
    """Umbral del ASSR (dB HL) de un oído con umbral conductual `hl`."""
    if hl is None:
        return None
    reduccion = 1.0 - OFFSET_SHRINK * min(max(hl / OFFSET_SHRINK_HL, 0.0), 1.0)
    return hl + PHYS_OFFSET_DB[carrier] * reduccion


def response_amplitude_uv(level, phys, carrier):
    """Amplitud de la línea (µV) con el estímulo a `level` dB HL."""
    if phys is None:
        return 0.0
    sl = level - phys
    if sl <= 0:
        return 0.0
    return AMP_SAT_UV[carrier] * (1.0 - np.exp(-sl / AMP_TAU_DB))


def f_sf(f_ratio, vecinos):
    """Cola de F(2, 2·vecinos): P(F >= f_ratio). Forma cerrada."""
    d2 = 2.0 * vecinos
    return float((1.0 + 2.0 * f_ratio / d2) ** (-d2 / 2.0))


def _filter_gain(freqs):
    f = np.maximum(np.asarray(freqs, dtype=float), 0.5)
    hp = 1.0 / np.sqrt(1.0 + (HIGHPASS_HZ / f) ** 4)
    lp = 1.0 / np.sqrt(1.0 + (f / LOWPASS_HZ) ** 4)
    return hp * lp


def neighbor_bins_of(channel, min_neighbors=24):
    """Bins vecinos de la línea de ese canal, sin las otras líneas."""
    k = FM_BIN[channel[0]][CARRIERS.index(channel[1])]
    todas = {b for s in SIDES for b in FM_BIN[s]}
    prohibidos = set()
    for b in todas:
        prohibidos.update((b - 1, b, b + 1))
    ancho = max(min_neighbors // 2, 12)
    cand = [b for b in range(k - ancho - 2, k + ancho + 3)
            if abs(b - k) >= 2 and b not in prohibidos and 0 < b < N_BINS]
    return np.array(cand, dtype=int)


def channel_key(channel):
    return f"{channel[0]}:{channel[1]}"


def parse_channel(key):
    side, f = key.split(':')
    return side, int(f)


class Recording:
    """Un registro de ASSR: las épocas, los niveles y la estadística.

    Cada época se sortea con una semilla propia (caso, índice), así que el
    mismo paciente da el mismo registro cada vez. Los niveles se cambian por
    portadora y reinician SOLO la cuenta de esa portadora.
    """

    def __init__(self, cases, patient=None, quality=1.0, inquietud=0.0,
                 reject_uv=25.0, impedance_kohm=2.0, transducer='insert_earphone',
                 min_neighbors=24):
        # cases: {'OD': dict|None, 'OI': dict|None}. Un oído sin datos no se
        # registra: no hay fallback sintético.
        self.cases = {s: (cases or {}).get(s) for s in SIDES}
        self.quality = float(quality)
        self.inquietud = float(inquietud or 0.0)
        self.reject_uv = float(reject_uv)
        self.impedance_kohm = float(impedance_kohm)
        self.transducer = transducer
        self.min_neighbors = min_neighbors
        self.key = stable_seed(
            'assr', case_fingerprint(self.cases['OD']),
            case_fingerprint(self.cases['OI']),
            (patient or {}).get('edad'))
        self.freqs = np.arange(N_BINS) * DF
        self.hl = {}
        self.phys = {}
        for s in SIDES:
            for f in CARRIERS:
                try:
                    self.hl[(s, f)] = behavioural_threshold(self.cases[s], f)
                    self.phys[(s, f)] = physiological_threshold(self.hl[(s, f)], f)
                except ValueError:
                    self.hl[(s, f)] = self.phys[(s, f)] = False
        self.reset()

    # ------------------------------------------------------------------
    # estado
    # ------------------------------------------------------------------
    def reset(self):
        self.rows = np.zeros((MAX_EPOCHS, N_BINS), dtype=complex)
        self.levels = {c: 60 for c in channels()}
        self.n = 0              # épocas aceptadas
        self.index = 0          # épocas presentadas (con las rechazadas)
        self.rejected = 0
        self.start = {c: 0 for c in channels()}
        self.history = {c: [] for c in channels()}
        self.last_epoch = None
        self.tips = {c: [] for c in channels()}

    def has_ear(self, side):
        return self.cases.get(side) is not None and all(
            self.hl[(side, f)] is not False for f in CARRIERS)

    def active(self, channel):
        return self.has_ear(channel[0])

    def set_level(self, channel, level):
        """Cambia el nivel de una portadora y cierra su tramo anterior."""
        level = int(np.clip(round(level / LEVEL_STEP) * LEVEL_STEP,
                            LEVEL_MIN, LEVEL_MAX))
        if level == self.levels[channel]:
            return
        self._close_run(channel)
        self.levels[channel] = level
        self.start[channel] = self.n
        self.tips[channel] = []

    def _close_run(self, channel):
        st = self.stats(channel)
        if st['n'] >= MIN_EPOCHS:
            self.history[channel].append({
                'level': self.levels[channel], 'n': st['n'],
                'detected': st['detected'], 'conclusive': st['conclusive'],
                'amp_nv': st['amp_nv'], 'noise_nv': st['noise_nv'],
                'p': st['p']})

    # ------------------------------------------------------------------
    # generación
    # ------------------------------------------------------------------
    def _noise_sigma(self):
        f = self.freqs
        sigma = NOISE_UV * self.quality * (90.0 / np.maximum(f, 5.0)) ** NOISE_SLOPE
        return sigma * _filter_gain(f)

    def _signal(self):
        """Línea de cada portadora a los niveles actuales (µV complejos)."""
        sig = np.zeros(N_BINS, dtype=complex)
        for (side, f) in channels():
            if not self.has_ear(side):
                continue
            lado_opuesto = 'OI' if side == 'OD' else 'OD'
            sl_nivel = self.levels[(side, f)]
            amp = response_amplitude_uv(sl_nivel, self.phys[(side, f)], f)
            # Cruce de sonido al otro oído: la línea tiene la modulación del
            # oído estimulado aunque la responda la cóclea contraria.
            if self.has_ear(lado_opuesto):
                cruzado = sl_nivel - INTERAURAL_ATTENUATION.get(
                    self.transducer, 65.0)
                amp = max(amp, response_amplitude_uv(
                    cruzado, self.phys[(lado_opuesto, f)], f))
            k = FM_BIN[side][CARRIERS.index(f)]
            fase = -2.0 * np.pi * (k * DF) * GROUP_DELAY_S[f]
            sig[k] += amp * np.exp(1j * fase)
        return sig

    def step(self, count=1):
        """Presenta `count` épocas. Devuelve cuántas se aceptaron."""
        aceptadas = 0
        sigma = self._noise_sigma()
        senial = self._signal()
        linea = 0.04 * max(self.impedance_kohm - 1.0, 0.0) * self.quality
        k_linea = (int(round(LINE_HZ / DF)), int(round(2 * LINE_HZ / DF)))
        for _ in range(count):
            if self.n >= MAX_EPOCHS:
                break
            rng = np.random.default_rng(stable_seed(self.key, self.index))
            self.index += 1
            g = rng.standard_normal((N_BINS, 2))
            ruido = (g[:, 0] + 1j * g[:, 1]) * (sigma / np.sqrt(2.0))
            escala = 1.0
            if rng.random() < ART_P_BASE + ART_P_INQUIETUD * min(self.inquietud, 1.0):
                escala = rng.uniform(*ART_SCALE)
                ruido = ruido * escala
            pico = EPOCH_PEAK_UV * self.quality * escala
            if pico > self.reject_uv:
                self.rejected += 1
                continue
            epoca = ruido + senial
            for kb in k_linea:
                epoca[kb] += linea * np.exp(1j * rng.uniform(0, 2 * np.pi))
            self.rows[self.n] = epoca
            self.last_epoch = epoca
            self.n += 1
            aceptadas += 1
        for c in channels():
            if self.active(c) and self.n > self.start[c]:
                self._remember_tip(c)
        return aceptadas

    def _remember_tip(self, channel):
        # Un punto de la punta del vector medio cada 6 épocas.
        run = self.n - self.start[channel]
        if run >= MIN_EPOCHS and run % 6 == 0:
            k = FM_BIN[channel[0]][CARRIERS.index(channel[1])]
            v = self.rows[self.start[channel]:self.n, k].mean()
            self.tips[channel].append(v)

    # ------------------------------------------------------------------
    # análisis
    # ------------------------------------------------------------------
    def neighbor_bins(self, channel):
        """Bins vecinos que estiman el ruido de esa línea (sin otras líneas)."""
        return neighbor_bins_of(channel, self.min_neighbors)

    def mean_spectrum(self, channel):
        """Espectro medio desde que esa portadora cambió de nivel."""
        a, b = self.start[channel], self.n
        if b <= a:
            return np.zeros(N_BINS, dtype=complex), 0
        return self.rows[a:b].mean(axis=0), b - a

    def epoch_phasors(self, channel):
        """Un vector por época en el bin de esa portadora (µV complejos)."""
        k = FM_BIN[channel[0]][CARRIERS.index(channel[1])]
        return self.rows[self.start[channel]:self.n, k]

    def stats(self, channel):
        side, f = channel
        k = FM_BIN[side][CARRIERS.index(f)]
        n = self.n - self.start[channel]
        vacio = {'n': n, 'amp_nv': 0.0, 'phase_deg': 0.0, 'noise_nv': 0.0,
                 'f_ratio': 0.0, 'p': 1.0, 'p_rayleigh': 1.0,
                 'coherence': 0.0, 'detected': False, 'conclusive': False,
                 'estado': 'sin datos'}
        if n < 2 or not self.has_ear(side):
            return vacio
        bloque = self.rows[self.start[channel]:self.n]
        medio = bloque.mean(axis=0)
        vec = medio[k]
        vecinos = self.neighbor_bins(channel)
        potencia_vec = float(np.mean(np.abs(medio[vecinos]) ** 2))
        noise = float(np.sqrt(potencia_vec))
        f_ratio = float(abs(vec) ** 2 / max(potencia_vec, 1e-18))
        p = f_sf(f_ratio, len(vecinos))
        fases = np.angle(bloque[:, k])
        r = float(abs(np.exp(1j * fases).mean()))
        p_ray = float(np.exp(-n * r * r)) if n >= 2 else 1.0
        detectada = n >= MIN_EPOCHS and p < ALPHA
        concluyente = detectada or (n >= MIN_EPOCHS
                                    and noise * 1000.0 <= NOISE_CRITERION_NV)
        if detectada:
            estado = 'respuesta'
        elif concluyente:
            estado = 'sin respuesta'
        else:
            estado = 'en curso'
        return {'n': n, 'amp_nv': abs(vec) * 1000.0,
                'phase_deg': float(np.degrees(np.angle(vec))),
                'noise_nv': noise * 1000.0, 'f_ratio': f_ratio, 'p': p,
                'p_rayleigh': p_ray, 'coherence': r, 'detected': detectada,
                'conclusive': concluyente, 'estado': estado}

    def polar_data(self, channel, blocks=6):
        """(vector medio, sub-promedios, camino de la punta), en nV."""
        fases = self.epoch_phasors(channel) * 1000.0
        if len(fases) == 0:
            return 0j, [], []
        tam = max(1, len(fases) // blocks)
        bloques = [complex(fases[i:i + tam].mean())
                   for i in range(0, len(fases) - tam + 1, tam)]
        puntas = [complex(v) * 1000.0 for v in self.tips[channel]]
        return complex(fases.mean()), bloques, puntas

    def snapshot(self, correction=None):
        """Estado completo para guardar el informe y volver a mirarlo.

        No son las épocas (serían MB): es lo que las vistas necesitan para
        redibujarse -- el espectro promedio, el vector y sus sub-promedios,
        el camino de la punta, la estadística y el historial de niveles.
        """
        canales = {}
        for c in channels():
            if not self.active(c):
                continue
            medio, _n = self.mean_spectrum(c)
            vec, bloques, puntas = self.polar_data(c)
            paso = max(1, len(puntas) // 60)
            canales[channel_key(c)] = {
                'nivel': self.levels[c],
                'stats': self.stats(c),
                'espectro': [[round(float(v.real) * 1000.0, 2),
                              round(float(v.imag) * 1000.0, 2)] for v in medio],
                'vector': [round(vec.real, 2), round(vec.imag, 2)],
                'bloques': [[round(b.real, 2), round(b.imag, 2)] for b in bloques],
                'puntas': [[round(p.real, 2), round(p.imag, 2)]
                           for p in puntas[::paso]],
                'historial': list(self.history[c]),
                'umbral_hl': self.threshold_hl(c),
                'umbral_ehl': self.threshold_ehl(c, correction),
                'hl_caso': self.hl[c],
            }
        return {'n': self.n, 'rechazadas': self.rejected,
                'correccion': {str(f): float(v) for f, v in
                               (correction or DEFAULT_EHL_CORRECTION).items()},
                'oidos': [s for s in SIDES if self.has_ear(s)],
                'canales': canales}

    def trace(self, spectrum, only_bin=None, window=None):
        """Rastro en el tiempo de un espectro (µV), t en s."""
        t = np.arange(N_SAMPLES) / FS
        if window is not None:
            t = t[t <= window]
        n_t = len(t)
        spec = np.array(spectrum, dtype=complex)
        if only_bin is not None:
            keep = np.zeros(N_BINS, dtype=bool)
            keep[max(only_bin - 1, 0):only_bin + 2] = True
            spec = np.where(keep, spec, 0.0)
        spec[0] = 0.0
        k = np.arange(N_BINS)[:, None]
        fases = np.exp(2j * np.pi * k * (t[None, :] / EPOCH_S))
        return t, np.real(spec[:, None] * fases).sum(axis=0)[:n_t]

    # ------------------------------------------------------------------
    # umbral
    # ------------------------------------------------------------------
    def threshold_hl(self, channel):
        """Menor nivel (dB HL) con respuesta detectada, o None.

        Incluye el tramo abierto. 'sin_respuesta' dice que se agotó el
        ruido sin respuesta al nivel más alto probado.
        """
        tramos = list(self.history[channel])
        st = self.stats(channel)
        if st['n'] >= MIN_EPOCHS:
            tramos.append({'level': self.levels[channel],
                           'detected': st['detected'],
                           'conclusive': st['conclusive']})
        con = [t['level'] for t in tramos if t['detected']]
        return min(con) if con else None

    def threshold_ehl(self, channel, correction=None):
        corr = correction or DEFAULT_EHL_CORRECTION
        thr = self.threshold_hl(channel)
        return None if thr is None else max(thr - corr[channel[1]], -10.0)

    # ------------------------------------------------------------------
    # estrategia automática de niveles
    # ------------------------------------------------------------------
    def auto_step(self):
        """Mueve los niveles como un equipo: baja 10 dB tras una respuesta
        y sube 10 dB tras un 'sin respuesta' concluyente. Devuelve las
        portadoras que ya terminaron (respuesta a L y nada a L-10)."""
        terminadas = []
        for c in channels():
            if not self.active(c):
                continue
            if self._is_done(c):
                terminadas.append(c)
                continue
            st = self.stats(c)
            if not st['conclusive']:
                continue
            nivel = self.levels[c]
            if st['detected']:
                if nivel - AUTO_STEP < LEVEL_MIN:
                    terminadas.append(c)
                    continue
                self.set_level(c, nivel - AUTO_STEP)
            else:
                if nivel + AUTO_STEP > LEVEL_MAX:
                    terminadas.append(c)
                    continue
                self.set_level(c, nivel + AUTO_STEP)
        return terminadas

    def _is_done(self, channel):
        """Terminó: hubo respuesta a un nivel y 'sin respuesta' diez dB abajo."""
        tramos = list(self.history[channel])
        st = self.stats(channel)
        if st['conclusive']:
            tramos.append({'level': self.levels[channel],
                           'detected': st['detected'], 'conclusive': True})
        por_nivel = {}
        for t in tramos:
            if t.get('conclusive'):
                por_nivel[t['level']] = t['detected'] or por_nivel.get(
                    t['level'], False)
        for nivel, det in por_nivel.items():
            if det and por_nivel.get(nivel - AUTO_STEP) is False:
                return True
        return False

    def all_done(self):
        activos = [c for c in channels() if self.active(c)]
        return bool(activos) and all(self._is_done(c) for c in activos)


class RecordingGuardado(Recording):
    """Un registro ya guardado, para mirarlo (informe y sesiones anteriores).

    Reconstruye lo que las vistas leen a partir de snapshot(); no genera
    épocas ni cambia niveles.
    """
    guardado = True

    def __init__(self, snap):  # pylint: disable=super-init-not-called
        self.snap = snap
        self.freqs = np.arange(N_BINS) * DF
        self.n = int(snap.get('n') or 0)
        self.rejected = int(snap.get('rechazadas') or 0)
        self.oidos = set(snap.get('oidos') or [])
        self.min_neighbors = 24
        self.last_epoch = None
        self.levels, self.history, self.tips, self.hl = {}, {}, {}, {}
        self.start = {c: 0 for c in channels()}
        for c in channels():
            d = (snap.get('canales') or {}).get(channel_key(c)) or {}
            self.levels[c] = int(d.get('nivel') or 0)
            self.history[c] = list(d.get('historial') or [])
            self.tips[c] = [complex(a, b) / 1000.0 for a, b in d.get('puntas') or []]
            hl = d.get('hl_caso')
            self.hl[c] = hl if c[0] in self.oidos else False

    def _datos(self, channel):
        return (self.snap.get('canales') or {}).get(channel_key(channel)) or {}

    def has_ear(self, side):
        return side in self.oidos

    def set_level(self, channel, level):
        return None

    def step(self, count=1):
        return 0

    def stats(self, channel):
        d = self._datos(channel)
        st = d.get('stats')
        if st:
            return dict(st)
        return {'n': 0, 'amp_nv': 0.0, 'phase_deg': 0.0, 'noise_nv': 0.0,
                'f_ratio': 0.0, 'p': 1.0, 'p_rayleigh': 1.0, 'coherence': 0.0,
                'detected': False, 'conclusive': False, 'estado': 'sin datos'}

    def mean_spectrum(self, channel):
        d = self._datos(channel)
        esp = d.get('espectro') or []
        spec = np.zeros(N_BINS, dtype=complex)
        for i, (a, b) in enumerate(esp[:N_BINS]):
            spec[i] = complex(a, b) / 1000.0
        return spec, int(self.stats(channel)['n'])

    def epoch_phasors(self, channel):
        return np.zeros(0, dtype=complex)

    def polar_data(self, channel, blocks=6):
        d = self._datos(channel)
        vec = complex(*(d.get('vector') or (0.0, 0.0)))
        bloques = [complex(a, b) for a, b in d.get('bloques') or []]
        puntas = [complex(a, b) for a, b in d.get('puntas') or []]
        return vec, bloques, puntas
