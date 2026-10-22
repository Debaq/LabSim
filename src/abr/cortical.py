"""Potenciales de latencia media y tardía: la vía tálamo-cortical y la corteza.

Cuelgan de la misma ventana que el ABR --mismo equipo, mismos electrodos,
mismo promediador-- como el ECochG, pero se leen distinto y por eso viven
en su propio módulo:

- PEALM (MLR, 10-80 ms): Na, Pa, Nb y Pb desde el mesencéfalo, el tálamo y
  la corteza auditiva primaria. Se registra en TRES canales a la vez (C3,
  Cz y C4) porque lo que localiza no es la latencia sino la comparación
  entre hemisferios: el efecto electrodo (el electrodo sobre la lesión
  muestra menos Na-Pa con cualquier oído) contra el efecto oído (un oído
  da menos en todos los electrodos y localiza poco).
- PEALT exógeno (CAEP, 50-300 ms): P1-N1-P2-N2. La P1 madura con la edad
  (Sharma 2002) y la N1 recién aparece de forma consistente pasados los 8
  a 10 años.
- P300 y MMN: paradigma oddball. Dos trazos por canal (frecuente y raro);
  la P300 se lee en el raro, la MMN en la DIFERENCIA raro menos frecuente.
  Las dos necesitan que el cerebro distinga los estímulos: con el mismo
  estímulo de frecuente y de raro no hay nada que medir.

Lo que varía entre pacientes viene del bloque `Central` del caso (nivel
paciente, no por oído: el efecto electrodo es de un hemisferio, no de un
oído). Sin ese bloque no hay registro: no se inventa una corteza normal.

Convención de trazo: positivo hacia ARRIBA, como el ABR de la misma
ventana (vértex positivo). Los textos de investigación imprimen a veces la
negatividad hacia arriba; en clínica audiológica no.

El módulo no dibuja ni sabe de Qt: entrega la curva objetivo por canal y
las medidas sobre un trazo ya registrado. Los números con cita están en
labsim_backend/src/CentralReferences.php (pantalla de bibliografía).
"""
import numpy as np


TESTS = ('MLR', 'CAEP', 'P300', 'MMN')
ODDBALL_TESTS = ('P300', 'MMN')

# Canales que registra cada prueba (activo contra la referencia del oído
# estimulado). El MLR compara hemisferios (C3 izquierdo, C4 derecho); los
# tardíos miran la topografía de adelante hacia atrás: la MMN es máxima en
# Fz, el complejo N1-P2 en Cz y la P3b en Pz.
CHANNELS = {
    'MLR': ('C3', 'Cz', 'C4'),
    'CAEP': ('Fz', 'Cz', 'Pz'),
    'P300': ('Fz', 'Cz', 'Pz'),
    'MMN': ('Fz', 'Cz', 'Pz'),
}
# Canal donde se lee cada prueba: el FSP, el ruido residual y la
# replicabilidad de la captura se informan sobre este.
READ_CHANNEL = {'MLR': 'Cz', 'CAEP': 'Cz', 'P300': 'Pz', 'MMN': 'Fz'}

# Hemisferio que tiene debajo cada electrodo lateral.
HEMISPHERE = {'C3': 'izquierdo', 'C4': 'derecho'}

# Escala de pantalla (alto de la ventana en uV, ver AbrGraph.set_scale).
# Unas cuatro veces la respuesta, como el ECochG: el Na-Pa es de ~1 uV y el
# N1-P2 de ~9.
DISPLAY_SCALE_UV = {'MLR': 5.0, 'CAEP': 30.0, 'P300': 40.0, 'MMN': 15.0}

# Muestreo de la época. El MLR tiene la onda V al inicio y el PAM de 1 ms
# de ancho; los tardíos no tienen nada por encima de 30 Hz.
SAMPLES_PER_MS = {'MLR': 5.0, 'CAEP': 1.0, 'P300': 1.0, 'MMN': 1.0}

# Cuánto dura la respuesta a UN estímulo: lo que queda de la anterior
# cuando llega la siguiente se suma (ver build_traces). Con 40/s eso es
# la respuesta de 40 Hz de Galambos, sin programarla aparte.
RESPONSE_SPAN_MS = {'MLR': 120.0, 'CAEP': 700.0, 'P300': 900.0, 'MMN': 700.0}


# ---------------------------------------------------------------------
# CASO
# ---------------------------------------------------------------------

ESTADOS = ('despierto', 'somnoliento', 'dormido', 'sedado')
HEMISFERIOS = ('ninguno', 'izquierdo', 'derecho', 'bilateral')
OIDOS = ('ninguno', 'OD', 'OI')

# Bloque `Central` del caso. Espejo de CaseBuilder::CENTRAL_DEFAULTS: los
# valores por defecto son los de una vía central sana en un paciente
# despierto.
CASE_DEFAULTS = {
    # Estado durante el registro. Es del paciente, no del equipo: un niño
    # dormido no tiene Pa y eso no es una lesión.
    'estado': 'despierto',
    # Tensión cervical (0-1): cuánto reflejo postauricular (PAM) aparece
    # en el MLR. Con referencia en mastoides se ve mucho más.
    'tension_cervical': 0.3,
    # PEALM: hemisferio comprometido, cuánto se reduce el Na-Pa del
    # electrodo que tiene encima (0-1) y cuánto se atrasa su Pa.
    'mlr_hemisferio': 'ninguno',
    'mlr_reduccion': 0.0,
    'mlr_pa_retardo_ms': 0.0,
    # Efecto oído: el Na-Pa de ese oído baja en TODOS los electrodos.
    'mlr_oido': 'ninguno',
    'mlr_oido_reduccion': 0.0,
    # PEALT: P1 atrasada respecto de la edad (privación auditiva) y
    # complejo N1-P2 reducido.
    'p1_retardo_ms': 0.0,
    'n1p2_reduccion': 0.0,
    # Cognitivos.
    'p300_retardo_ms': 0.0,
    'p300_reduccion': 0.0,
    'mmn_reduccion': 0.0,
    # Error del paciente al contar los raros (fracción). La tarea es parte
    # de la P300: un conteo malo invalida la interpretación.
    'conteo_error': 0.0,
}

CASE_LIMITS = {
    'tension_cervical': (0.0, 1.0),
    'mlr_reduccion': (0.0, 1.0),
    'mlr_pa_retardo_ms': (0.0, 20.0),
    'mlr_oido_reduccion': (0.0, 1.0),
    'p1_retardo_ms': (0.0, 200.0),
    'n1p2_reduccion': (0.0, 1.0),
    'p300_retardo_ms': (0.0, 200.0),
    'p300_reduccion': (0.0, 1.0),
    'mmn_reduccion': (0.0, 1.0),
    'conteo_error': (0.0, 1.0),
}
CASE_OPTIONS = {
    'estado': ESTADOS,
    'mlr_hemisferio': HEMISFERIOS,
    'mlr_oido': OIDOS,
}


def case_params(central):
    """Parámetros del bloque `Central`, o None si el caso no lo trae.

    None quiere decir "sin registro", no "sano": un caso guardado antes de
    que existiera el bloque no tiene corteza que mostrar hasta que el
    docente lo guarde de nuevo.
    """
    if not isinstance(central, dict) or not central:
        return None
    out = dict(CASE_DEFAULTS)
    for clave, (lo, hi) in CASE_LIMITS.items():
        try:
            valor = float(central.get(clave, out[clave]))
        except (TypeError, ValueError):
            valor = float(out[clave])
        out[clave] = float(np.clip(valor, lo, hi))
    for clave, opciones in CASE_OPTIONS.items():
        valor = central.get(clave, out[clave])
        out[clave] = valor if valor in opciones else CASE_DEFAULTS[clave]
    return out


def age_years(patient):
    """Edad en años del paciente (las horas de vida mandan si están)."""
    patient = patient or {}
    horas = patient.get('edad_horas')
    if horas not in (None, ''):
        try:
            return max(float(horas) / 8766.0, 0.0)
        except (TypeError, ValueError):
            pass
    try:
        return max(float(patient.get('edad')), 0.0)
    except (TypeError, ValueError):
        return 30.0


# ---------------------------------------------------------------------
# NORMATIVA
# ---------------------------------------------------------------------

# Latencias del MLR en el adulto despierto (click a 60-70 dB, 7/s): media y
# desvío. Las medias son las de Pialarissi 2007 (Na 17.9, Pa 29.4, Nb 41.4,
# Pb 51.4 ms); esa serie no publica desvío y los de acá son calculados (ver
# CentralReferences en el backend).
MLR_LAT_ADULT = {'Na': (18.0, 2.0), 'Pa': (30.0, 3.0),
                 'Nb': (41.0, 3.0), 'Pb': (52.0, 4.0)}
# Amplitud Na-Pa normal (uV), Cz. Bajo el mínimo no es patológico por sí
# solo: la amplitud absoluta varía mucho entre sujetos y lo que localiza es
# la comparación (ver ELECTRODE_EFFECT_LIMIT).
MLR_NAPA_RANGE = (0.5, 2.0)
# Diferencia de amplitud Na-Pa entre C3 y C4 (o entre oídos) que se
# considera efecto electrodo (u oído): 1 - menor/mayor. Musiek 1999 y
# Weihing 2012 leen la diferencia PORCENTUAL entre lados (es menos variable
# que la amplitud absoluta), pero el corte publicado no se pudo verificar:
# el 50% es el criterio del docente.
ELECTRODE_EFFECT_LIMIT = 0.50
EAR_EFFECT_LIMIT = 0.50

# Latencia de la P1 según la edad (ms): la regresión de Sharma, Dorman y
# Spahr 2002 sobre 136 normoyentes de 0.1 a 20 años, latencia = 155.6 -
# 32.746 ln(edad). Fuera de ese tramo se usa el borde (no se extrapola: a
# los 60 años la recta daría 21 ms). El trabajo dibuja el intervalo de 95%
# pero no lo publica como fórmula: el límite superior es la media + 2 DE con
# DE del 12% de la media (calculado, se parece a la banda de la figura).
P1_INTERCEPT_MS = 155.6
P1_SLOPE_MS = 32.746
P1_AGE_RANGE = (0.1, 20.0)
P1_SD_FRACTION = 0.12

# Componentes exógenos del adulto (Cz, tono de 1 kHz a 70 dB, 1/s).
CAEP_LAT_ADULT = {'P1': (55.0, 8.0), 'N1': (100.0, 10.0),
                  'P2': (180.0, 15.0), 'N2': (250.0, 20.0)}
# Amplitud N1-P2 (uV, Cz). Hall 2007: 5-10 uV.
N1P2_RANGE = (4.0, 15.0)

# P300 (P3b en Pz). Duncan 2009: pico típico entre 300 y 400 ms. Polich,
# Howard y Starr 1985: ~65 ms más entre los 20 y los 70 años (1.3 ms/año);
# en el niño es más tardía y baja hasta la adolescencia. La DE de 20 ms es
# calculada.
P300_ADULT_MS = 300.0
P300_MS_PER_YEAR = 1.3
P300_CHILD_MS_PER_YEAR = 7.0
P300_SD_MS = 20.0
# Amplitud (uV, Pz, desde la línea de base): baja con la edad.
P300_AMP_YOUNG = 12.0
P300_AMP_PER_YEAR = 0.08
P300_AMP_MIN_FRACTION = 0.45

# MMN en la diferencia (Fz). Duncan 2009: 150-250 ms (baja cuanto mayor es
# el cambio), 0.5-5 uV.
MMN_LAT_RANGE = (150.0, 250.0)
MMN_AMP_RANGE = (0.5, 5.0)


def p1_norm(edad):
    """(media, límite superior) de la latencia de la P1 a esa edad."""
    edad = float(np.clip(float(edad), *P1_AGE_RANGE))
    media = P1_INTERCEPT_MS - P1_SLOPE_MS * float(np.log(edad))
    return media, media * (1.0 + 2.0 * P1_SD_FRACTION)


def p300_norm(edad):
    """(media, DE) de la latencia de la P300 a esa edad."""
    edad = float(edad)
    if edad < 18.0:
        media = P300_ADULT_MS + P300_CHILD_MS_PER_YEAR * (18.0 - edad)
    elif edad <= 20.0:
        media = P300_ADULT_MS
    else:
        media = P300_ADULT_MS + P300_MS_PER_YEAR * (edad - 20.0)
    return media, P300_SD_MS


def p300_amp_norm(edad):
    """Amplitud media de la P300 (uV) a esa edad."""
    return max(P300_AMP_YOUNG - P300_AMP_PER_YEAR * max(float(edad) - 20.0, 0.0),
               4.0)


def mlr_pa_shift(edad):
    """Cuánto más tarde llega Pa en el niño (ms): madura hacia los 10 años."""
    return 0.8 * max(10.0 - float(edad), 0.0)


def normative(test, edad):
    """Límites de cada marca para la tabla: {'lat': {marca: (lo, hi)},
    'amp': {medida: (lo, hi)}}. Los límites de amplitud son orientativos;
    la interpretación pesa las comparaciones (efecto electrodo y oído)."""
    edad = float(edad)
    if test == 'MLR':
        lat = {}
        for marca, (m, de) in MLR_LAT_ADULT.items():
            corr = mlr_pa_shift(edad) if marca != 'Na' else 0.0
            lat[marca] = (m + corr - 2 * de, m + corr + 2 * de)
        return {'lat': lat, 'amp': {'Na-Pa': MLR_NAPA_RANGE},
                'electrode_effect': ELECTRODE_EFFECT_LIMIT,
                'ear_effect': EAR_EFFECT_LIMIT}
    if test in ('CAEP', 'P300'):
        p1, p1_hi = p1_norm(edad)
        lat = {'P1': (p1 * (1 - 2 * P1_SD_FRACTION), p1_hi)}
        if edad >= 10.0:
            for marca in ('N1', 'P2', 'N2'):
                m, de = CAEP_LAT_ADULT[marca]
                lat[marca] = (m - 2 * de, m + 2 * de)
        out = {'lat': lat, 'amp': {'N1-P2': N1P2_RANGE} if edad >= 10 else {}}
        if test == 'P300':
            m, de = p300_norm(edad)
            out['lat']['P3'] = (m - 2 * de, m + 2 * de)
            out['amp']['P3'] = (p300_amp_norm(edad) * P300_AMP_MIN_FRACTION,
                                p300_amp_norm(edad) * 2.0)
        return out
    if test == 'MMN':
        return {'lat': {'MMN': MMN_LAT_RANGE}, 'amp': {'MMN': MMN_AMP_RANGE}}
    return {'lat': {}, 'amp': {}}


# ---------------------------------------------------------------------
# MORFOLOGÍA
# ---------------------------------------------------------------------
#
# Cada componente es una gaussiana: latencia (ms), amplitud con signo (uV,
# en el canal de referencia de la prueba), sigma (ms) y peso por canal.

# MLR del adulto. La V del ABR entra al inicio, chica: con el pasa-bajo de
# 300 Hz queda como un abultamiento antes de Na, que es como se ve.
MLR_COMPONENTS = {
    'V': {'lat': 6.0, 'amp': 0.35, 'sigma': 0.6,
          'topo': {'C3': 0.9, 'Cz': 1.0, 'C4': 0.9}},
    'Na': {'lat': 18.0, 'amp': -0.45, 'sigma': 2.6,
           'topo': {'C3': 0.9, 'Cz': 1.0, 'C4': 0.9}},
    'Pa': {'lat': 30.0, 'amp': 0.75, 'sigma': 4.0,
           'topo': {'C3': 0.85, 'Cz': 1.0, 'C4': 0.85}},
    'Nb': {'lat': 41.0, 'amp': -0.45, 'sigma': 3.6,
           'topo': {'C3': 0.85, 'Cz': 1.0, 'C4': 0.85}},
    'Pb': {'lat': 52.0, 'amp': 0.35, 'sigma': 5.0,
           'topo': {'C3': 0.85, 'Cz': 1.0, 'C4': 0.85}},
}
# Los componentes que salen de la corteza (y no del tronco o el tálamo):
# son los que una lesión hemisférica reduce de verdad.
MLR_CORTICAL = ('Pa', 'Nb', 'Pb')
# Dominancia contralateral: el electrodo opuesto al oído estimulado recibe
# algo más de Pa. Es chica a propósito; el efecto electrodo es otra cosa.
MLR_CONTRA_GAIN = 0.05
# Cuánto de una lesión de un hemisferio llega a Cz (que está en el medio).
MLR_CZ_SHARE = 0.35

# Exógenos tardíos del adulto (Cz).
LATE_COMPONENTS = {
    'P1': {'lat': 55.0, 'amp': 1.5, 'sigma': 10.0,
           'topo': {'Fz': 0.8, 'Cz': 1.0, 'Pz': 0.7}},
    'N1': {'lat': 100.0, 'amp': -5.0, 'sigma': 14.0,
           'topo': {'Fz': 1.0, 'Cz': 1.0, 'Pz': 0.55}},
    'P2': {'lat': 180.0, 'amp': 4.0, 'sigma': 25.0,
           'topo': {'Fz': 0.8, 'Cz': 1.0, 'Pz': 0.7}},
    'N2': {'lat': 250.0, 'amp': -2.0, 'sigma': 30.0,
           'topo': {'Fz': 0.9, 'Cz': 1.0, 'Pz': 0.7}},
}
# Lo que se agrega al raro: N2b de clasificación y P3b (Pz).
N2B = {'lat': 220.0, 'amp': -2.0, 'sigma': 25.0,
       'topo': {'Fz': 0.8, 'Cz': 1.0, 'Pz': 0.6}}
P3B_TOPO = {'Fz': 0.45, 'Cz': 0.75, 'Pz': 1.0}
P3B_SIGMA_FRACTION = 0.2
# MMN en el desviante (Fz) y la P3a pasiva que acompaña a una desviación
# grande (orientación involuntaria).
MMN_TOPO = {'Fz': 1.0, 'Cz': 0.85, 'Pz': 0.35}
MMN_AMP = -3.0
MMN_SIGMA = 35.0
P3A = {'lat': 270.0, 'amp': 1.5, 'sigma': 35.0,
       'topo': {'Fz': 1.0, 'Cz': 0.9, 'Pz': 0.5}}
# Instrucción que el examinador le da al paciente en el oddball. La P3b
# es endógena: sale solo si el paciente atiende a los raros (los cuenta o
# aprieta un botón). La MMN es al revés: se registra con la atención en
# otra parte (video sin sonido), porque atender a los raros suma N2b y P3b
# encima y la diferencia ya no es solo MMN (Duncan 2009). Sin instrucción
# no hay P3b: queda la P3a pasiva de una desviación grande.
TAREAS = ('ninguna', 'pasiva', 'contar', 'boton')
TAREA_LABELS = {'ninguna': "Sin instrucción",
                'pasiva': "Pasiva: video sin sonido",
                'contar': "Contar los raros",
                'boton': "Apretar botón con el raro"}
TAREAS_ATENTAS = ('contar', 'boton')
# El raro encuentra la vía menos refractaria que el frecuente (otra
# frecuencia, menos repeticiones): su N1 sale algo más grande.
RARE_N1_GAIN = 1.15

# Retardo de los componentes por estímulo (ms, por frecuencia del burst):
# el burst grave llega más tarde y con menos sincronía que el click.
STIM_LAT_MS = {4000.0: 0.5, 2000.0: 1.0, 1000.0: 1.5, 500.0: 2.5}


def stim_latency(stim):
    """Retardo propio del estímulo (rótulo de cb_stim), en ms."""
    return STIM_LAT_MS.get(_freq_hz(stim), 0.0)

# Período refractario: constante de recuperación (ms) y la separación entre
# estímulos con la que se definen las amplitudes de rutina.
REFRACTORY_TAU_MS = {'MLR': 40.0, 'late': 1500.0}
REFRACTORY_REF_ISI_MS = {'MLR': 1000.0 / 7.1, 'late': 1000.0}
REFRACTORY_MAX = 1.6

# Nivel de sensación: con cuánto SL la respuesta llega a su tamaño de
# rutina y cuánto se atrasa por cada dB por debajo de ese nivel.
SL_FULL_DB = {'MLR': 50.0, 'late': 40.0}
SL_LAT_MS_PER_DB = {'MLR': 0.06, 'late': 0.5}
SL_REF_DB = 60.0


def refractory_factor(test, rate):
    """Cuánto de la respuesta se recupera con esa tasa (1 = la de rutina).

    A más latencia, más largo el período refractario: el N1 a 1/s es la
    mitad del que se obtiene cada 4 s, y estimular a 7/s (la tasa del MLR)
    lo deja casi en nada. Es la habituación que la clase pide evitar.
    """
    clave = 'MLR' if test == 'MLR' else 'late'
    tau = REFRACTORY_TAU_MS[clave]
    isi = 1000.0 / max(float(rate), 0.05)
    ref = REFRACTORY_REF_ISI_MS[clave]
    factor = (1.0 - np.exp(-isi / tau)) / (1.0 - np.exp(-ref / tau))
    return float(min(factor, REFRACTORY_MAX))


def sl_factor(test, sl):
    """(factor de amplitud, retardo en ms) por nivel de sensación."""
    clave = 'MLR' if test == 'MLR' else 'late'
    if sl <= 0:
        return 0.0, 0.0
    amp = float(np.clip(sl / SL_FULL_DB[clave], 0.0, 1.0) ** 0.7)
    retardo = SL_LAT_MS_PER_DB[clave] * max(SL_REF_DB - sl, 0.0)
    return amp, retardo


# Integración temporal de los tardíos: el umbral del N1-P2 baja con la
# duración del tono, de 8 a 128 ms unos 24 dB a 1 kHz y 18 dB a 4 kHz
# (-4 a -6 dB por cada vez que se duplica), y a nivel fijo un tono más
# largo da N1 y P2 más grandes y más tempranos (Eddins y Peterson 1999,
# CentralReferences C13).
# Se aplica como nivel de sensación perdido: un burst de 1-10-1 ms, o un
# 2-1-2 ciclos heredado del ABR, rinde como un tono ~15 dB más suave que el
# 10-50-10 ms de rutina. Fuera de 8-128 ms no hay datos y se recorta.
DURATION_DB_PER_DOUBLING = {500.0: 6.0, 1000.0: 6.0, 2000.0: 5.25,
                            4000.0: 4.5}
DURATION_RANGE_MS = (8.0, 128.0)
# Envolvente de rutina de los tardíos y su duración efectiva (meseta más
# media rampa de cada lado): con ella el corrimiento es cero.
STANDARD_ENVELOPE = 'ms-10-50-10'


def effective_duration_ms(envelope, stim):
    """Duración efectiva del estímulo en ms (meseta + media rampa por
    lado). Un click o un chirp cuentan como el tono más corto medido."""
    hz = _freq_hz(stim)
    if hz is None:
        return DURATION_RANGE_MS[0]
    from abr.ecochg import burst_timing
    rise, plateau, fall = burst_timing(envelope or '2-1-2', hz)
    return float(plateau + (rise + fall) / 2.0)


def duration_shift_db(envelope, stim):
    """dB de sensación que se pierden (positivo) o se ganan (negativo)
    contra la envolvente de rutina, por la duración del estímulo."""
    lo, hi = DURATION_RANGE_MS
    hz = _freq_hz(stim) or 1000.0
    pendiente = DURATION_DB_PER_DOUBLING.get(hz, 6.0)
    dur = float(np.clip(effective_duration_ms(envelope, stim), lo, hi))
    ref = float(np.clip(effective_duration_ms(STANDARD_ENVELOPE,
                                              'Burst 1 kHz'), lo, hi))
    return float(pendiente * np.log2(ref / dur))


def deviance(stim_a, stim_b):
    """Qué tan distintos son frecuente y raro (0 = iguales, 1 = una octava
    o más, o click contra burst). Es lo que el cerebro tiene que detectar."""
    if stim_a == stim_b:
        return 0.0
    fa, fb = _freq_hz(stim_a), _freq_hz(stim_b)
    if fa is None or fb is None:
        return 1.0
    return float(np.clip(abs(np.log2(fb / fa)), 0.0, 1.0))


def _freq_hz(stim):
    """Frecuencia del burst de un rótulo de cb_stim, o None (click/chirp)."""
    stim = str(stim or '')
    for texto, hz in (('500 Hz', 500.0), ('1 kHz', 1000.0),
                      ('2 kHz', 2000.0), ('4 kHz', 4000.0)):
        if stim.endswith(texto):
            return hz
    return None


def _gauss(t, comp):
    return comp['amp'] * np.exp(-0.5 * ((t - comp['lat']) / comp['sigma']) ** 2)


def _copy(comps):
    return {k: dict(v, topo=dict(v['topo'])) for k, v in comps.items()}


def mlr_components(edad, central, side, ctx):
    """Componentes del MLR para el oído `side` ('OD'/'OI'), por canal.

    Devuelve {canal: {componente: dict}} porque la lesión de un hemisferio
    toca distinto a cada electrodo: no es un factor global.
    """
    comps = _copy(MLR_COMPONENTS)
    edad = float(edad)
    estado = central['estado']
    lat_stim = ctx.get('stim_lat', 0.0)
    amp_sl, lat_sl = ctx['sl']
    corticales = MLR_CORTICAL
    # Maduración: Pa más chica y más tarde hasta los 10 años.
    madurez = float(np.clip(edad / 10.0, 0.0, 1.0))
    amp_pa = 0.3 + 0.7 * madurez
    if edad > 40:
        # Adulto mayor: la Pa tiende a crecer.
        amp_pa *= 1.0 + 0.008 * (edad - 40.0)
    if estado == 'dormido':
        # Adulto: Pa estable. Niño: depende de la etapa del sueño y por eso
        # cambia de una captura a otra (ctx['sleep_draw'] es por captura).
        if edad < 10.0:
            amp_pa *= float(ctx.get('sleep_draw', 0.5))
        else:
            amp_pa *= 0.9
    elif estado == 'sedado':
        amp_pa *= 0.5
    elif estado == 'somnoliento':
        amp_pa *= 0.9
    for nombre, c in comps.items():
        c['lat'] += lat_stim
        if nombre != 'V':
            c['lat'] += lat_sl
        if nombre in corticales:
            c['lat'] += mlr_pa_shift(edad)
            if estado == 'sedado':
                c['lat'] += 4.0
            c['amp'] *= amp_pa
        c['amp'] *= amp_sl * ctx['refractory']
        if nombre != 'V' and central['mlr_oido'] == side:
            c['amp'] *= 1.0 - central['mlr_oido_reduccion']

    contra = 'C3' if side == 'OD' else 'C4'
    out = {}
    for canal in CHANNELS['MLR']:
        por_canal = _copy(comps)
        parte = _lesion_share(canal, central)
        red = parte * central['mlr_reduccion']
        for nombre in corticales:
            c = por_canal[nombre]
            c['amp'] *= 1.0 - red
            c['lat'] += parte * central['mlr_pa_retardo_ms']
            if canal in HEMISPHERE:
                c['amp'] *= (1.0 + MLR_CONTRA_GAIN if canal == contra
                             else 1.0 - MLR_CONTRA_GAIN)
        # El Na baja lo mismo: el caso declara cuánto pierde el Na-Pa de
        # ese electrodo, que es lo que el alumno mide y lo que el docente
        # tiene que poder leer en la ficha (caso 1 de la clase: -60%).
        por_canal['Na']['amp'] *= 1.0 - red
        out[canal] = por_canal
    return out


def _lesion_share(canal, central):
    """Qué parte de la lesión del caso ve ese electrodo (0-1).

    Entera el electrodo que está sobre el hemisferio comprometido, nada el
    del otro lado y una fracción Cz, que está en el medio. Vale para la
    reducción del Na-Pa y para el retardo de Pa.
    """
    hemi = central['mlr_hemisferio']
    if hemi == 'ninguno':
        return 0.0
    if canal == 'Cz':
        return 0.8 if hemi == 'bilateral' else MLR_CZ_SHARE
    if hemi == 'bilateral' or HEMISPHERE.get(canal) == hemi:
        return 1.0
    return 0.0


def late_components(edad, central, ctx, rare=False):
    """Exógenos tardíos (P1-N1-P2-N2) a esa edad y en ese estado."""
    comps = _copy(LATE_COMPONENTS)
    edad = float(edad)
    estado = central['estado']
    amp_sl, lat_sl = ctx['sl']
    # Maduración: la P1 grande y tardía del niño; la N1 aparece entre los
    # 8 y los 12 años; la N2 domina el trazo infantil.
    n1 = float(np.clip((edad - 7.0) / 5.0, 0.0, 1.0))
    p1_lat = p1_norm(edad)[0] + central['p1_retardo_ms']
    comps['P1']['lat'] = p1_lat
    comps['P1']['sigma'] = 0.18 * p1_lat
    comps['P1']['amp'] = 1.5 + 3.0 * (1.0 - n1)
    comps['N1']['amp'] *= n1
    comps['P2']['amp'] *= 0.4 + 0.6 * n1
    comps['N2']['amp'] = -2.0 - 1.5 * (1.0 - n1)
    comps['N2']['lat'] = 250.0 + 50.0 * (1.0 - n1)
    # La privación atrasa todo el complejo, la P1 entera y lo demás a medias.
    for nombre in ('N1', 'P2', 'N2'):
        comps[nombre]['lat'] += 0.5 * central['p1_retardo_ms']
    for nombre in ('N1', 'P2'):
        comps[nombre]['amp'] *= 1.0 - central['n1p2_reduccion']
    if estado == 'somnoliento':
        comps['N1']['amp'] *= 0.7
    elif estado == 'dormido':
        comps['N1']['amp'] *= 0.4
        comps['P2']['amp'] *= 1.1
    elif estado == 'sedado':
        for c in comps.values():
            c['amp'] *= 0.3
    if rare:
        comps['N1']['amp'] *= RARE_N1_GAIN
    for c in comps.values():
        c['lat'] += lat_sl + ctx.get('stim_lat', 0.0)
        c['amp'] *= amp_sl * ctx['refractory']
    return comps


def attends(ctx):
    """¿El paciente atiende a los raros? Lo decide la instrucción."""
    return ctx.get('tarea', 'ninguna') in TAREAS_ATENTAS


def p300_component(edad, central, ctx):
    """P3b del raro, o None si no se puede generar."""
    estado = central['estado']
    dev = ctx['deviance']
    if dev <= 0 or estado in ('dormido', 'sedado') or not attends(ctx):
        return None
    lat = p300_norm(edad)[0] + central['p300_retardo_ms']
    amp = p300_amp_norm(edad) * (1.0 - central['p300_reduccion'])
    if estado == 'somnoliento':
        amp *= 0.4
        lat += 40.0
    # Más rara, más grande (la amplitud es la "sorpresa"); y una
    # discriminación difícil la achica y la atrasa.
    prob = float(np.clip(ctx.get('rare_fraction', 0.2), 0.05, 0.5))
    amp *= float(np.clip((0.2 / prob) ** 0.5, 0.0, 1.4))
    amp *= dev ** 0.5
    lat += 40.0 * (1.0 - dev)
    amp *= min(ctx['sl'][0] * 1.5, 1.0)
    if amp <= 0:
        return None
    return {'lat': lat, 'amp': amp, 'sigma': P3B_SIGMA_FRACTION * lat,
            'topo': dict(P3B_TOPO)}


def p3a_component(central, ctx):
    """P3a pasiva (orientación involuntaria a una desviación grande)."""
    if ctx['deviance'] >= 0.9 and central['estado'] == 'despierto':
        return {'P3a': dict(P3A, topo=dict(P3A['topo']))}
    return {}


def attended_components(edad, central, ctx):
    """N2b y P3b del raro atendido, o {} si no atiende o no puede."""
    p3 = p300_component(edad, central, ctx)
    if p3 is None:
        return {}
    return {'N2b': dict(N2B, topo=dict(N2B['topo'])), 'P3': p3}


def mmn_components(central, ctx):
    """MMN (y P3a pasiva) del desviante, o {} si no hay desviación."""
    dev = ctx['deviance']
    if dev <= 0:
        return {}
    factor = {'despierto': 1.0, 'somnoliento': 0.8, 'dormido': 0.3,
              'sedado': 0.0}[central['estado']]
    amp = MMN_AMP * dev ** 0.5 * factor * (1.0 - central['mmn_reduccion'])
    amp *= min(ctx['sl'][0] * 1.5, 1.0)
    out = {}
    if amp < 0:
        out['MMN'] = {'lat': 170.0 + 40.0 * (1.0 - dev), 'amp': amp,
                      'sigma': MMN_SIGMA, 'topo': dict(MMN_TOPO)}
    out.update(p3a_component(central, ctx))
    return out


def _evaluate(t, comps, canal):
    y = np.zeros_like(t, dtype=float)
    for c in comps.values():
        peso = c['topo'].get(canal, 0.0)
        if peso:
            y = y + peso * _gauss(t, c)
    return y


def _superpose(t, comps_by_channel, test, rate):
    """Respuesta en régimen estable: la actual más lo que queda de las
    anteriores (que llegaron cada 1/tasa). Con 40/s el MLR se superpone a
    sí mismo y sale la respuesta de 40 Hz."""
    isi = 1000.0 / max(float(rate), 0.05)
    span = RESPONSE_SPAN_MS[test]
    k_max = int(span // isi) if isi < span else 0
    # Y los estímulos que llegan DENTRO de la época: a 40/s, en 100 ms
    # entran tres más.
    k_sig = int(float(np.max(t)) // isi) if len(t) else 0
    out = {}
    for canal, comps in comps_by_channel.items():
        y = _evaluate(t, comps, canal)
        for k in range(1, k_max + 1):
            y = y + _evaluate(t + k * isi, comps, canal)
        for k in range(1, k_sig + 1):
            y = y + _evaluate(t - k * isi, comps, canal)
        out[canal] = y
    return out


def build_traces(test, t, edad, central, side, ctx):
    """Curvas objetivo por canal: {'main': {canal: y}, 'overlays': {...}}.

    - MLR y CAEP: un trazo por canal.
    - P300: el trazo principal es el RARO (donde está la P3); el frecuente
      va superpuesto para comparar.
    - MMN: el principal es la DIFERENCIA raro menos frecuente; los dos
      promedios van superpuestos.

    `ctx` trae: sl (factor, retardo), refractory, stim_lat, deviance,
    rare_fraction, sleep_draw y tarea (la instrucción al paciente).
    """
    rate = ctx['rate']
    canales = CHANNELS[test]
    if test == 'MLR':
        comps = mlr_components(edad, central, side, ctx)
        return {'main': _superpose(t, comps, test, rate), 'overlays': {}}
    frecuentes = late_components(edad, central, ctx)
    if test == 'CAEP':
        return {'main': _superpose(t, {c: frecuentes for c in canales},
                                   test, rate),
                'overlays': {}}
    raros = late_components(edad, central, ctx, rare=bool(ctx['deviance']))
    # Atendido (contar o botón), el raro suma N2b y P3b; si no, en la
    # P300 queda la P3a pasiva y la MMN sale limpia.
    atendidos = attended_components(edad, central, ctx)
    if test == 'P300':
        raros.update(atendidos or p3a_component(central, ctx))
    else:
        raros.update(mmn_components(central, ctx))
        raros.update(atendidos)
    # Lo que precede a cada estímulo es casi siempre un frecuente: es lo
    # que se superpone, tanto al frecuente como al raro.
    y_frec = _superpose(t, {c: frecuentes for c in canales}, test, rate)
    cola = {c: y_frec[c] - _evaluate(t, frecuentes, c) for c in canales}
    y_raro = {c: _evaluate(t, raros, c) + cola[c] for c in canales}
    if test == 'P300':
        return {'main': y_raro, 'overlays': {'frecuente': y_frec}}
    return {'main': {c: y_raro[c] - y_frec[c] for c in canales},
            'overlays': {'frecuente': y_frec, 'raro': y_raro}}


# ---------------------------------------------------------------------
# PAM (reflejo postauricular)
# ---------------------------------------------------------------------

# Pico agudo de 12-15 ms. Es del músculo detrás de la oreja: lo recoge la
# REFERENCIA, así que entra igual en los tres canales y con mastoides es
# varias veces más grande que con lóbulo.
PAM_LAT_MS = 13.5
PAM_SIGMA_MS = 1.1
PAM_UV = {'mastoid': 3.0, 'earlobe': 0.3}
PAM_MIN_DB = 50.0


def pam_curve(t, reference, tension, nivel_db, rng):
    """PAM del registro (uV) o ceros. Bifásico: el músculo, no un pico."""
    if nivel_db < PAM_MIN_DB or tension <= 0:
        return np.zeros_like(t)
    amp = PAM_UV.get(reference, PAM_UV['earlobe']) * float(tension)
    amp *= float(np.clip((nivel_db - PAM_MIN_DB) / 30.0, 0.0, 1.0))
    amp *= float(rng.uniform(0.7, 1.3))
    lat = PAM_LAT_MS + float(rng.uniform(-1.0, 1.0))
    return amp * (np.exp(-0.5 * ((t - lat) / PAM_SIGMA_MS) ** 2)
                  - 0.6 * np.exp(-0.5 * ((t - lat - 2.2) / (1.5 * PAM_SIGMA_MS)) ** 2))


# ---------------------------------------------------------------------
# MARCAS Y MEDIDAS
# ---------------------------------------------------------------------

MARKS = {
    'MLR': ('Na', 'Pa', 'Nb', 'Pb'),
    'CAEP': ('P1', 'N1', 'P2', 'N2'),
    'P300': ('N1', 'P2', 'N2', 'P3'),
    'MMN': ('MMN',),
}
# Las negativas se pegan al mínimo, las positivas al máximo.
NEGATIVE_MARKS = ('Na', 'Nb', 'N1', 'N2', 'MMN')
# Cuánto busca el pico alrededor de la bandera (ms).
SNAP_MS = {'MLR': 3.0, 'CAEP': 15.0, 'P300': 25.0, 'MMN': 20.0}
# Tramo del inicio de la época que hace de línea de base (ms): antes de
# que llegue nada cortical. La época arranca en el estímulo (el equipo no
# guarda pre-estímulo en esta ventana).
BASELINE_MS = {'MLR': (0.0, 4.0), 'CAEP': (0.0, 30.0),
               'P300': (0.0, 40.0), 'MMN': (0.0, 60.0)}


def mark_polarity(mark):
    """-1 si la marca va en un valle, +1 si va en un pico."""
    return -1 if mark in NEGATIVE_MARKS else 1


def baseline(test, t, y):
    desde, hasta = BASELINE_MS[test]
    t = np.asarray(t)
    tramo = (t >= desde) & (t <= hasta)
    if not tramo.any():
        return 0.0
    return float(np.mean(np.asarray(y)[tramo]))


def measure(test, t, y, marks):
    """Medidas de un canal a partir de sus marcas ({marca: [x, y]}).

    Latencia al pico de cada marca y la amplitud que se informa en cada
    prueba: Na-Pa y N1-P2 de pico a pico; la P3 y la MMN desde la línea
    de base (la MMN en negativo, como en la onda de diferencia).
    """
    marks = marks or {}
    out = {'lat': {}, 'amp': {}}
    for marca, xy in marks.items():
        if xy is not None:
            out['lat'][marca] = float(xy[0])

    def valor(m):
        xy = marks.get(m)
        return None if xy is None else float(xy[1])

    if test == 'MLR' and valor('Na') is not None and valor('Pa') is not None:
        out['amp']['Na-Pa'] = valor('Pa') - valor('Na')
    if test in ('CAEP', 'P300') and valor('N1') is not None \
            and valor('P2') is not None:
        out['amp']['N1-P2'] = valor('P2') - valor('N1')
    base = baseline(test, t, y) if t is not None and y is not None else 0.0
    if test == 'P300' and valor('P3') is not None:
        out['amp']['P3'] = valor('P3') - base
    if test == 'MMN' and valor('MMN') is not None:
        out['amp']['MMN'] = base - valor('MMN')
    return out


def asymmetry(a, b):
    """1 - menor/mayor entre dos amplitudes (0 = iguales), o None."""
    if a is None or b is None:
        return None
    a, b = abs(float(a)), abs(float(b))
    mayor = max(a, b)
    if mayor <= 0:
        return None
    return 1.0 - min(a, b) / mayor


def electrode_effect(napa):
    """Efecto electrodo con las amplitudes Na-Pa {(oído, canal): uV}.

    Compara C3 contra C4 con cada oído y promedia lo que haya. Devuelve
    (diferencia 0-1, hemisferio con menos amplitud) o (None, None). El
    hemisferio es el del ELECTRODO más chico: eso es lo que localiza.
    """
    difs, menores = [], []
    for oido in ('OD', 'OI'):
        c3, c4 = napa.get((oido, 'C3')), napa.get((oido, 'C4'))
        d = asymmetry(c3, c4)
        if d is None:
            continue
        difs.append(d)
        menores.append('izquierdo' if abs(c3) < abs(c4) else 'derecho')
    if not difs:
        return None, None
    lado = max(set(menores), key=menores.count)
    return float(np.mean(difs)), lado


def ear_effect(napa):
    """Efecto oído: Na-Pa de cada oído promediado en los tres electrodos.

    Devuelve (diferencia 0-1, oído con menos amplitud) o (None, None).
    """
    medias = {}
    for oido in ('OD', 'OI'):
        valores = [abs(v) for (o, _), v in napa.items()
                   if o == oido and v is not None]
        if valores:
            medias[oido] = float(np.mean(valores))
    if len(medias) < 2:
        return None, None
    d = asymmetry(medias['OD'], medias['OI'])
    return d, ('OD' if medias['OD'] < medias['OI'] else 'OI')
