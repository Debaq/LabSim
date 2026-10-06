"""Electrococleografía: los potenciales del oído interno, no del tronco.

El ECochG cuelga de la misma ventana que el ABR --mismo equipo, mismos
electrodos, mismo promediador-- pero NO se lee igual, y por eso vive en su
propio módulo en vez de ser una fila más de `build_target_curve`:

- Lo que se registra son tres potenciales distintos, no cinco ondas de una
  misma vía: la microfónica coclear (MC, de las células ciliadas externas,
  sigue la forma de onda del estímulo), el potencial de sumación (PS, el
  desplazamiento DC de la membrana basilar) y el potencial de acción (PA o
  N1, la descarga sincrónica del nervio -- el MISMO evento que la onda I
  del ABR, registrado desde el otro extremo).
- La MC INVIERTE con la polaridad y el PS/PA no. Por eso una curva en
  rarefacción y otra en condensación separan la MC del resto, y la
  alternada la cancela. Esto no se programa acá: `build_polarity_curve`
  ya promedia las dos polaridades, así que basta con que la MC entre con
  signo.
- El resultado no es una latencia contra una tabla: es una RAZÓN entre el
  PS y el PA, que es lo que se eleva en el hidrops endolinfático.

Convención de trazo (decidida con el docente, ver docs/decisiones.md): PA hacia
ABAJO. El electrodo activo es el del oído (timpánico o de conducto), no el
vértex, así que la negatividad coclear queda hacia abajo en la pantalla --
que es como lo imprimen los equipos en modo ECochG. Es la convención
opuesta a la del ABR de la misma ventana, y eso es correcto: el montaje
está invertido.

El módulo no dibuja ni sabe de Qt: entrega la curva objetivo y las medidas
sobre un trazo ya registrado.
"""
import numpy as np


# ---------------------------------------------------------------------
# MORFOLOGÍA
# ---------------------------------------------------------------------

# Dónde cae el hombro del PS respecto del pico del PA, en ms. El PS no es
# un pico: es una meseta que arranca antes y se mantiene POR DEBAJO del PA
# (de ahí que el PA se lea como una espiga montada sobre ella). El hombro
# es el punto que el alumno marca.
SP_SHOULDER_MS = 0.55
# Cuánto antes del hombro empieza a despegarse de la base. El complejo
# entero arranca entonces SP_SHOULDER_MS + SP_ONSET_MS antes del PA: con el
# PA del click a 90 dB en ~1.4 ms, eso deja el despegue en ~0.6 ms y un
# tramo de base plana delante donde poner la marca BL. Más largo y el PS
# empezaría antes de que el sonido llegue a la cóclea.
SP_ONSET_MS = 0.25
# Pendiente del flanco de subida del PS (ms de la sigmoide). Un flanco
# instantáneo no deja hombro visible y la marca no tendría dónde caer; uno
# muy lento hace que el hombro caiga en plena subida y el trazo mida menos
# razón PS/PA de la que el caso declara.
SP_RISE_MS = 0.12
# Fracción de la amplitud del PS con la que se da por empezado el complejo
# (ver complex_onset). El despegue de la base es asintótico: sin un
# criterio el "inicio" se iría hasta el borde de la ventana.
ONSET_FRACTION = 0.10

# Ancho del PA. Es la onda I vista desde el oído: más angosta que
# cualquier onda del tronco porque no acumuló dispersión de vía.
AP_SIGMA_MS = 0.22
# Cuánto se ensancha el PA por cada punto de razón PS/PA sobre el límite.
# En el hidrops el PA no solo queda chico contra el PS: se ensancha,
# porque la membrana desplazada desincroniza la descarga. Es la segunda
# lectura del mismo registro y la que sigue estando cuando la razón queda
# en el borde.
AP_WIDTH_PER_RATIO = 2.5

# Segundo pico negativo (N2) y la positividad lenta con la que el complejo
# vuelve a la base. La positividad no es adorno: sin ella el trazo se
# acerca a la base por debajo sin cruzarla nunca, y el RETORNO A LA BASE
# --que es el límite derecho de las dos integrales del área-- no existiría
# como punto marcable. En un registro real ese cruce está siempre.
#
# El N2 tiene que verse como un valle propio, ~1 ms después del N1. Estuvo
# en 0.22 del PA con 0.30 ms de ancho y la positividad de abajo (ancha y
# centrada encima) se lo comía: quedaba un hombro de 0.04 uV sobre la cola
# del PS y el docente no lo encontraba en el trazo.
N2_RATIO = 0.30
N2_MS = 1.05
N2_SIGMA_MS = 0.22
# Cuánto dura el desplazamiento DC del PS después del pico del PA. Es lo
# que hace que la razón de ÁREAS sea distinta de la de amplitudes: la
# meseta corre por debajo de todo el complejo, no solo hasta el PA.
#
# Con click es CORTO. Estuvo en 1.35 ms un rato, estirado para que la razón
# de áreas diera el 1.94 publicado, y el precio fue que el trazo dejó de
# parecerse a un ECochG: en vez de una espiga con un hombro quedaba un
# bolsón ancho del que no se podía sacar ni dónde estaba el PA. La
# morfología manda; el límite de áreas sale del modelo (ver
# AREA_RATIO_LIMIT).
SP_TAIL_MS = 0.60
# Cuánto se PROLONGA la meseta por cada punto de razón por encima de la de
# un oído sano. En el hidrops el sumación no solo sube: dura más, porque el
# desplazamiento de la membrana tarda más en volver. Es la razón física de
# que la razón de ÁREAS detecte oídos que la de amplitudes todavía llama
# normales -- si la meseta solo cambiara de altura, las dos razones dirían
# exactamente lo mismo y la segunda no agregaría nada.
#
# Crece desde la razón de un oído sano (la mitad del límite del electrodo),
# no desde el límite: si empezara en el límite, las dos razones se cruzarían
# en el mismo punto y la de áreas volvería a ser redundante justo donde
# tiene que servir.
SP_TAIL_PER_RATIO = 3.0
SP_NORMAL_FRACTION = 0.5
POST_POSITIVITY_RATIO = 0.10
# Después del N2 y angosta: centrada sobre él lo tapaba (ver N2_RATIO).
POST_POSITIVITY_MS = 1.9
POST_POSITIVITY_SIGMA_MS = 0.35

# Nivel de sensación (dB SL) entre el que el PS no se distingue y aquel en
# que ya está entero. El PA existe hasta el umbral --es lo que define el
# umbral-- pero el PS necesita nivel: es un desplazamiento DC que solo se
# hace medible con la cóclea bien empujada. Por eso el ECochG clínico se
# hace a 80-90 dB nHL y no en una serie descendente, y por eso medir la
# razón a nivel bajo la da CHICA aunque el oído tenga hidrops. Que ese
# error se pueda cometer, y que el trazo no avise, es el ejercicio.
SP_SL_MIN = 30.0
SP_SL_FULL = 70.0

# Microfónica coclear. Con click la MC es una oscilación corta dominada por
# la base de la cóclea (la región de 2-3 kHz es la que responde primero y
# más sincronizada); con tone burst sigue la frecuencia del burst y dura lo
# que dura el burst, que es la razón clínica de usar burst de 1 kHz para
# mirar el PS.
CM_CLICK_HZ = 2500.0
# Con click es un ringing breve que se apaga antes del N1. Estuvo en 1.0 ms
# y seguía sonando bajo el PA: en una sola polaridad le corría el pico
# ±0.15 ms (para lados opuestos en rarefacción y condensación) y la
# separación rar/cond medida dejaba de ser la que declara el caso.
CM_CLICK_MS = 0.6
# Envolvente del tone burst cuando el equipo no trae una (la de rutina del
# ABR, ver AbrAdvanceSettings.BURST_ENVELOPES).
DEFAULT_BURST_ENVELOPE = '2-1-2'
# La MC arranca con la llegada del estímulo a la cóclea, antes que todo lo
# demás: es el único componente que no espera la sinapsis. Su latencia la
# fija la ACÚSTICA (el tubo del fono y el viaje hasta la base de la
# cóclea), no la del PA -- por eso entra como dato y no como "tanto antes
# del PA". Este valor es el respaldo para cuando no hay latencia de MC en
# la normativa.
CM_ONSET_BEFORE_AP_MS = 1.0


# ---------------------------------------------------------------------
# ELECTRODOS
# ---------------------------------------------------------------------

# Ganancia de amplitud por tipo de electrodo, contra el Cz-mastoides del
# ABR (= 1.0). No es un detalle de montaje: es LA decisión técnica del
# ECochG. Cuanto más cerca de la cóclea, más grande todo -- y también más
# invasivo. El de conducto (TipTrode) apenas gana sobre el ABR y obliga a
# promediar mucho más; el transtimpánico atraviesa el tímpano hasta el
# promontorio y da milivoltios de PA, pero lo pone un médico.
ELECTRODE_GAIN = {
    'extratympanic': 2.5,    # TipTrode en el conducto: PA ~1 uV
    'tympanic': 8.0,         # electrodo sobre la membrana: PA ~3.5 uV
    'transtympanic': 25.0,   # aguja en el promontorio: PA ~10 uV
}
# El valor que tenia 'tympanic' en el generador antes de que existiera esta
# tabla era 2.5 sobre el Cz-mastoides, y con eso el ECochG salia con PEOR
# relacion senial/ruido que un ABR: la banda del ECochG (10-3000 Hz, contra
# 100-3000) deja entrar ~3 veces mas ruido, asi que 2.5 de ganancia no
# alcanzaba ni para empatar. Un electrodo timpanico da PA de 1 a 5 uV
# --entre 6 y 15 veces la onda I de un registro de superficie-- y esa es
# justamente la razon clinica de meterse hasta la membrana.

# Alto de la ventana del gráfico, en µV, por cada unidad de ganancia del
# electrodo. El ABR se dibuja en 6 µV con ondas de medio µV; un ECochG
# timpánico tiene el PA en 3.5 µV y en esa misma escala se sale por abajo y
# se pisa con la curva de al lado. La escala tiene que seguir al electrodo:
# es lo primero que cambia de un registro al otro.
DISPLAY_UV_PER_GAIN = 2.0


def display_scale_uv(montage):
    """Alto de ventana con el que se dibuja un ECochG de ese electrodo."""
    return DISPLAY_UV_PER_GAIN * ELECTRODE_GAIN.get(montage, 1.0)


# Límite superior normal de la razón de AMPLITUDES PS/PA, por electrodo.
# Cambia con el electrodo y no por capricho: cuanto más lejos de la cóclea,
# más se atenúa el PA (que es de campo cercano y muy sincronizado) frente
# al PS, así que la misma cóclea da razones más altas medida desde el
# conducto. Comparar contra el límite equivocado es el error que el
# ejercicio tiene que dejar cometer.
SP_AP_LIMIT = {
    'extratympanic': 0.50,   # conducto (TipTrode)
    'tympanic': 0.40,        # sobre el tímpano
    'transtympanic': 0.35,   # promontorio
}
# Límite de la razón de ÁREAS (ver measure_complex para la definición
# exacta de las dos áreas). Es más sensible que la de amplitudes porque
# recoge las dos cosas que le pasan al sumación en el hidrops --que sube y
# que se prolonga-- y no solo su altura en un punto.
#
# 1.94 es el límite publicado para electrodo timpánico; las otras dos
# posiciones se escalan igual que el límite de amplitudes, por la misma
# razón (un mismo oído no puede cambiar de diagnóstico al cambiar de
# electrodo).
AREA_RATIO_LIMIT = {
    'tympanic': 1.94,
    'extratympanic': 1.94 * SP_AP_LIMIT['extratympanic'] / SP_AP_LIMIT['tympanic'],
    'transtympanic': 1.94 * SP_AP_LIMIT['transtympanic'] / SP_AP_LIMIT['tympanic'],
}

# Montajes que son ECochG. El resto (Cz-mastoides y compañía) registran un
# ABR aunque el combo diga ECochG: no hay electrodo en el oído y lo que se
# ve es el tronco. Que eso se pueda hacer, y que el trazo salga sin PS, es
# parte del ejercicio.
ECOCHG_MONTAGES = tuple(ELECTRODE_GAIN)


# ---------------------------------------------------------------------
# CASO
# ---------------------------------------------------------------------

# Lo que el caso declara del ECochG de ESE oído. Son los parámetros del
# hidrops, no un enum de diagnósticos (mismo criterio que el patrón neural
# del ABR, ver NEURAL_PARAM_DEFAULTS).
CASE_DEFAULTS = {
    # Razón de amplitudes PS/PA que tiene este oído medido con electrodo
    # TIMPÁNICO. Las otras dos posiciones salen de acá escaladas por
    # SP_AP_LIMIT, para que un mismo oído no cambie de diagnóstico al
    # cambiar de electrodo.
    'sp_ap': 0.25,
    # Cuánto se le alarga la latencia del PA al subir la tasa, contra lo
    # que le pasa a un oído sano (1.0 = lo normal). En el hidrops la
    # adaptación es mayor.
    'tasa': 1.0,
    # Diferencia de latencia del PA entre rarefacción y condensación, en
    # ms. En el oído sano es la de la onda I (0.1 ms); el hidrops la
    # agranda porque la membrana desplazada responde distinto a cada
    # dirección del empuje.
    'rar_cond_ms': 0.1,
    # Microfónica: 'normal' o 'amplificada'. Amplificada es el hallazgo de
    # la desincronía auditiva, no del hidrops -- el mismo registro sirve
    # para las dos preguntas y por eso está acá.
    'mc': 'normal',
}

MC_GAIN = {'normal': 1.0, 'amplificada': 6.0}


def case_params(ecochg):
    """Parámetros del ECochG del caso, con los faltantes completados.

    Devuelve None si el caso NO trae bloque de ECochG: sin dato real del
    backend el módulo no inventa un oído normal (ver la regla de no
    generar nada sin datos). Quien llama tiene que bloquear la prueba.
    """
    if not isinstance(ecochg, dict) or not ecochg:
        return None
    out = dict(CASE_DEFAULTS)
    for clave, defecto in CASE_DEFAULTS.items():
        valor = ecochg.get(clave)
        if valor in (None, ''):
            continue
        out[clave] = valor if isinstance(defecto, str) else float(valor)
    if out['mc'] not in MC_GAIN:
        out['mc'] = 'normal'
    return out


def sp_ap_for_electrode(sp_ap_tympanic, montage):
    """La misma cóclea, medida con otro electrodo.

    El caso declara la razón medida con electrodo timpánico (la posición de
    referencia). Con otro electrodo la razón se mueve en la misma
    proporción en que se mueve el límite de normalidad, así que un oído
    normal sigue siendo normal y uno con hidrops sigue estándolo: lo que
    cambia es el número contra el que hay que compararlo.
    """
    base = SP_AP_LIMIT['tympanic']
    limite = SP_AP_LIMIT.get(montage, base)
    return float(sp_ap_tympanic) * limite / base


# ---------------------------------------------------------------------
# TONE BURST
# ---------------------------------------------------------------------

def freq_hz(freq):
    """'1000Hz' -> 1000.0 (la clave de banda de STIM_MAP)."""
    texto = str(freq or '').replace('Hz', '').replace('k', '000')
    try:
        return float(texto) or 1000.0
    except ValueError:
        return 1000.0


def burst_timing(envelope, hz):
    """Subida, meseta y bajada del burst, en ms.

    `envelope` es la clave del equipo (AbrAdvanceSettings.BURST_ENVELOPES):
    '2-1-2' va en CICLOS de la frecuencia del tono y 'ms-1-10-1' en
    milisegundos. Con ciclos la duración depende de la frecuencia (un 2-1-2
    dura 5 ms a 1 kHz y 1.25 ms a 4 kHz); con milisegundos no, que es por
    lo que el ECochG con burst se programa en ms.
    """
    codigo = str(envelope or DEFAULT_BURST_ENVELOPE)
    en_ms = codigo.startswith('ms-')
    partes = codigo[3:] if en_ms else codigo
    try:
        rise, plateau, fall = (float(p) for p in partes.split('-'))
    except ValueError:
        return burst_timing(DEFAULT_BURST_ENVELOPE, hz)
    if not en_ms:
        ciclo = 1000.0 / float(hz)
        rise, plateau, fall = rise * ciclo, plateau * ciclo, fall * ciclo
    return rise, plateau, fall


def burst_plateau_center(timing, onset=0.0):
    """Mitad de la meseta del estímulo: donde se lee el PS con burst."""
    rise, plateau, _ = timing
    return float(onset) + rise + plateau / 2.0


def _trapezoid(t, onset, timing):
    """Envolvente del burst (0 a 1) que arranca en `onset`."""
    rise, plateau, fall = timing
    dt = np.asarray(t, dtype=float) - float(onset)
    env = np.zeros_like(dt)
    if rise > 0:
        env = np.where((dt >= 0) & (dt < rise), dt / rise, env)
    meseta = (dt >= rise) & (dt <= rise + plateau)
    env = np.where(meseta, 1.0, env)
    if fall > 0:
        bajada = (dt > rise + plateau) & (dt < rise + plateau + fall)
        env = np.where(bajada, 1.0 - (dt - rise - plateau) / fall, env)
    return env


# ---------------------------------------------------------------------
# CURVA
# ---------------------------------------------------------------------

def _gaussian(t, center, amp, sigma):
    return amp * np.exp(-0.5 * ((t - center) / sigma) ** 2)


def _sigmoid(t, center, rise):
    return 1.0 / (1.0 + np.exp(-(t - center) / max(rise, 1e-6)))


def sp_level_factor(sl):
    """Cuánto del PS es medible a ese nivel de sensación (0 a 1)."""
    if sl is None:
        return 1.0
    return float(np.clip((float(sl) - SP_SL_MIN) / (SP_SL_FULL - SP_SL_MIN),
                         0.0, 1.0))


def component_params(wave_i, case, montage, stim='click', freq=None,
                     mc_baseline=None, sl=None, gain=1.0, cm_lat=None,
                     envelope=None, sp_ref_amp=None):
    """Los tres potenciales, a partir de la onda I ya calculada.

    `wave_i` es values['I'] del ABR: latencia y amplitud con la intensidad,
    el umbral, la patología, la tasa, el montaje y las desviaciones del
    caso YA aplicadas. El PA no es otra cosa que esa misma onda registrada
    desde el oído, así que todo lo que el motor del ABR sabe del nivel de
    sensación vale acá sin duplicar nada.

    `gain` es la ganancia del electrodo, que el motor ya le aplicó a
    `wave_i`: acá se usa solo para la MC, cuya amplitud normativa viene
    medida en el montaje del ABR.

    `cm_lat` es la latencia de la MC, que NO se deriva de la del PA: la
    polaridad corre la onda I 0.1 ms y la MC no se entera (la mueve el
    viaje del sonido, no la sinapsis). Derivándola del PA, la MC de la
    curva en rarefacción y la de condensación quedaban desalineadas y NO
    se cancelaban al alternar -- que es justo lo que el examen usa para
    separarla del PS y del PA.

    Con tone burst (`envelope` es la del equipo) el PS deja de ser el
    hombro de un click: es un desplazamiento DC que dura lo que dura el
    estímulo, con su misma subida y bajada, y el PA queda como una espiga
    solo al comienzo. La altura de esa meseta es `sp_ref_amp` (el PA del
    CLICK a ese nivel) por la razón del caso, y no el PA del propio burst:
    el burst sincroniza mal y su PA es chico (a 1 kHz la cuarta parte que
    el del click), pero el sumación es un desplazamiento de la membrana y
    no depende de la sincronía. Escalarlo con el PA del burst lo dejaba
    invisible justo en el estímulo que se usa para mirarlo.
    """
    amp_pa = float(wave_i['amp'])
    lat_pa = float(wave_i['lat'])
    razon = sp_ap_for_electrode(case['sp_ap'], montage) * sp_level_factor(sl)
    exceso = max(razon - SP_AP_LIMIT.get(montage, SP_AP_LIMIT['tympanic']), 0.0)
    ancho = AP_SIGMA_MS * float(wave_i.get('width', 1.0)) * (
        1.0 + AP_WIDTH_PER_RATIO * exceso)
    normal = SP_NORMAL_FRACTION * SP_AP_LIMIT.get(montage,
                                                  SP_AP_LIMIT['tympanic'])
    cola_ps = SP_TAIL_MS * (1.0 + SP_TAIL_PER_RATIO * max(razon - normal, 0.0))

    timing = None
    if stim == 'tone_burst' and freq:
        cm_hz = freq_hz(freq)
        timing = burst_timing(envelope, cm_hz)
        cm_ms = sum(timing)
    else:
        cm_hz = CM_CLICK_HZ
        cm_ms = CM_CLICK_MS

    # Amplitud de la MC: la normativa la trae medida en el montaje del ABR
    # (clave 'MC' del bundle), así que se escala por el mismo electrodo que
    # todo lo demás. Es chica comparada con el PA salvo en la desincronía.
    cm_base = float((mc_baseline or {}).get('amp', 0.144))
    # Altura NOMINAL de la meseta. No es la definitiva: en el hombro el
    # trazo ya trae la cola de la gaussiana del PA (el hombro cae sobre la
    # rama ascendente, que es lo que lo hace un hombro y no un pico
    # aparte), y con polaridad alternada el trazo es además el promedio de
    # dos curvas con el PA en distinta latencia y amplitud. La altura que
    # deja la razón MEDIDA igual a la declarada se despeja sobre la curva
    # ya armada, en calibrate_sp.
    sp_amp = amp_pa * razon
    cm_onset = (lat_pa - CM_ONSET_BEFORE_AP_MS if cm_lat is None
                else float(cm_lat))

    out = {
        'ap_lat': lat_pa,
        'ap_amp': amp_pa,
        'ap_sigma': ancho,
        'sp_lat': lat_pa - SP_SHOULDER_MS,
        'sp_amp': sp_amp,
        'sp_onset': lat_pa - SP_SHOULDER_MS - SP_ONSET_MS,
        'sp_tail': cola_ps,
        'cm_amp': cm_base * float(gain) * MC_GAIN.get(case['mc'], 1.0),
        'cm_hz': cm_hz,
        'cm_ms': cm_ms,
        'cm_onset': cm_onset,
        'sp_ap': razon,
        'burst': None,
    }
    if timing is not None:
        # El PS arranca con el sonido en la cóclea (la misma llegada que la
        # MC) y sigue la envolvente del estímulo; se lee en la mitad de la
        # meseta, lejos de la espiga del PA y de la bajada.
        out['burst'] = timing
        out['sp_onset'] = cm_onset
        out['sp_lat'] = burst_plateau_center(timing, cm_onset)
        if sp_ref_amp:
            out['sp_amp'] = float(sp_ref_amp) * razon
    return out


def build_curve(t, params, polarity, sp_scale=1.0):
    """Curva objetivo del ECochG, en convención de pantalla (PA abajo).

    La MC entra con el signo de la polaridad; el PS y el PA no la miran.
    Con polaridad alternada la MC llega acá en None porque el promedio de
    las dos curvas ya la canceló (ver build_polarity_curve) -- no se
    apaga a mano.
    """
    y = np.zeros_like(t)
    amp_pa = params['ap_amp']
    sp_amp = params['sp_amp'] * float(sp_scale)
    timing = params.get('burst')

    if timing is not None:
        # Con burst el PS es la envolvente del estímulo: sube con la
        # rampa, se sostiene toda la meseta y baja con la bajada. El PA es
        # la descarga del COMIENZO y va montado encima de la meseta con su
        # amplitud entera: acá no hay razón de hombro que respetar.
        y -= sp_amp * _trapezoid(t, params['sp_onset'], timing)
        y -= _gaussian(t, params['ap_lat'], amp_pa, params['ap_sigma'])
    else:
        # PS: meseta que sube con una sigmoide y se sostiene POR DEBAJO de
        # todo el complejo. No decae con el PA: el desplazamiento DC dura
        # lo que dura el estímulo, y eso es lo que hace que la razón de
        # ÁREAS mida algo distinto de la de amplitudes.
        meseta = _sigmoid(t, params['sp_onset'] + SP_RISE_MS, SP_RISE_MS)
        meseta = meseta * (1.0 - _sigmoid(
            t, params['ap_lat'] + params['sp_tail'], SP_RISE_MS * 2))
        y -= sp_amp * meseta

        # PA (N1). La espiga se dibuja con lo que le FALTA para llegar a la
        # amplitud del PA: el PA se mide desde la línea de base, o sea que
        # la meseta del PS ya es parte de su profundidad. Si la gaussiana
        # valiera la amplitud entera, el trazo daría una razón PS/PA más
        # baja que la que declara el caso (el denominador se agrandaría
        # solo).
        y -= _gaussian(t, params['ap_lat'], amp_pa - sp_amp,
                       params['ap_sigma'])
    y -= _gaussian(t, params['ap_lat'] + N2_MS, amp_pa * N2_RATIO, N2_SIGMA_MS)
    y += _gaussian(t, params['ap_lat'] + POST_POSITIVITY_MS,
                   amp_pa * POST_POSITIVITY_RATIO, POST_POSITIVITY_SIGMA_MS)

    # MC: oscilación a la frecuencia del estímulo, con envolvente. El signo
    # es el de la polaridad -- es el componente que separa una curva en
    # rarefacción de una en condensación.
    signo = 0.0
    if polarity == 'Rarefacción':
        signo = 1.0
    elif polarity == 'Condensación':
        signo = -1.0
    if signo and params['cm_amp'] > 0:
        dt = t - params['cm_onset']
        if timing is not None:
            # Con burst la MC reproduce el estímulo entero, rampa incluida.
            env = _trapezoid(t, params['cm_onset'], timing)
        else:
            env = np.exp(-0.5 * ((dt - params['cm_ms'] / 2) /
                                 (params['cm_ms'] / 3)) ** 2)
            env[dt < 0] = 0.0
        y += signo * params['cm_amp'] * env * np.sin(
            2 * np.pi * params['cm_hz'] * dt / 1000.0)
    return y


def peak_time(t, y, lat_hint=None):
    """Instante del pico del PA en ESTA curva.

    Se busca cerca de donde el modelo lo puso, no en toda la ventana: con
    razones PS/PA muy altas la meseta del sumación llega a ser más profunda
    que la espiga del acción, y el mínimo absoluto del trazo se iría a la
    meseta, que no es el PA.
    """
    if lat_hint is None:
        return float(t[int(np.argmin(y))])
    cerca = np.where(np.abs(t - float(lat_hint)) <= 0.5)[0]
    if not len(cerca):
        return float(t[int(np.argmin(y))])
    return float(t[int(cerca[np.argmin(y[cerca])])])


def calibrate_sp(t, y_sin, y_con, razon, lat_hint=None):
    """Ajusta la meseta del PS para que lo MEDIDO sea lo declarado.

    `y_sin` es la curva sin meseta (solo el complejo del PA) e `y_con` la
    misma con la meseta nominal. La meseta entra LINEALMENTE en el trazo,
    así que cualquier altura intermedia es y_sin + k*(y_con - y_sin) y la
    k que deja la razón en el valor del caso se despeja de una sola
    ecuación -- no hace falta iterar.

    Se hace sobre la curva ya armada y no con una fórmula cerrada porque
    ahí ya están las dos cosas que la ensucian: la cola de la gaussiana del
    PA bajo el hombro, y el promedio de las dos polaridades (que corre el
    pico y le baja la amplitud). Con la fórmula cerrada un caso declarado
    en 0.55 se medía 0.43, o sea que el docente no podía poner un oído en
    el borde del límite y saber de qué lado iba a caer.

    Devuelve (k, x_pa, x_ps): la escala de la meseta y los dos instantes
    donde caen las marcas si se ponen bien.
    """
    x_pa = peak_time(t, y_con, lat_hint)
    i_pa = int(np.argmin(np.abs(t - x_pa)))
    x_ps = x_pa - SP_SHOULDER_MS
    i_ps = int(np.argmin(np.abs(t - x_ps)))
    a0, s0 = -float(y_sin[i_pa]), -float(y_sin[i_ps])
    a1, s1 = -float(y_con[i_pa]), -float(y_con[i_ps])
    den = (s1 - s0) - razon * (a1 - a0)
    k = 1.0 if abs(den) < 1e-9 else (razon * a0 - s0) / den
    return float(np.clip(k, 0.0, 20.0)), x_pa, x_ps


# ---------------------------------------------------------------------
# MEDIDAS
# ---------------------------------------------------------------------

# Marcas que el alumno pone sobre el trazo. No son ondas: son los cuatro
# puntos que definen las dos razones.
MARKS = ('BL', 'PS', 'PA', 'FIN')
MARK_LABELS = {
    'BL': 'Línea de base',
    'PS': 'Potencial de sumación',
    'PA': 'Potencial de acción',
    'FIN': 'Retorno a la base',
}


# ---------------------------------------------------------------------
# MARCADO AUTOMÁTICO
# ---------------------------------------------------------------------

# Dónde puede estar el PA de un click, en ms. Es un rango fisiológico (la
# onda I con fono de inserción no cae fuera de ahí), no el dato del caso:
# el detector trabaja sobre el TRAZO y no sabe qué declaró el docente. Por
# eso se equivoca cuando el trazo está mal registrado, que es justamente lo
# que el alumno tiene que poder ver.
AP_SEARCH_MS = (0.8, 3.5)
# Tramo del que sale la línea de base: antes de que llegue nada.
BASELINE_MS = (0.0, 0.35)
# Qué tan cerca de la base tiene que volver el trazo para darlo por vuelto,
# como fracción de la profundidad del PA. Un cruce estricto no sirve: basta
# un poco de deriva lenta para que el trazo se quede del lado de abajo toda
# la ventana y el retorno no exista, justo en los registros donde importa.
RETURN_FRACTION = 0.10
# Qué tan hondo tiene que ser un mínimo local para aceptarlo como el PA,
# contra el más hondo de la ventana. Por debajo de esto es una ondulación
# del ruido y se sigue buscando.
AP_MIN_DEPTH = 0.80

# Suavizado (en ms) con el que se buscan las pendientes. Sin esto el ruido
# del registro manda en la derivada y el hombro cae en cualquier lado.
SMOOTH_MS = 0.12


def _smooth(t, y, ms=SMOOTH_MS):
    """Media móvil de `ms` milisegundos."""
    if len(t) < 3:
        return y
    paso = float(t[1] - t[0])
    n = max(int(round(ms / paso)), 1)
    if n < 2:
        return y
    nucleo = np.ones(n) / n
    return np.convolve(y, nucleo, mode='same')


def auto_marks(t, y, ps_at=None):
    """Marcado automático del complejo, como lo hace el equipo.

    `ps_at` es la mitad de la meseta del estímulo cuando es un burst (ver
    burst_plateau_center): el equipo sabe qué estímulo mandó y cuándo, y
    con burst el PS se lee ahí y no en el hombro. Con click va en None.

    Devuelve {marca: latencia} con las cuatro marcas, o {} si no encuentra
    un complejo donde debería haberlo.

    Trabaja SOBRE EL TRAZO y nada más: no mira el caso, ni la razón que el
    docente declaró, ni la latencia que el modelo usó para dibujar. Esa es
    la diferencia entre un marcado automático y la respuesta regalada --
    con la banda mal puesta, el nivel bajo o el promedio a medias, esto
    marca mal, igual que el equipo real, y darse cuenta es parte del
    examen.

    Cómo encuentra cada punto:
      BL   el trazo antes de que llegue nada (BASELINE_MS).
      PA   el PRIMER mínimo del rango fisiológico (AP_SEARCH_MS) que sea
           bastante hondo -- no el más hondo: con un sumación grande el N2
           llega a medir casi lo mismo.
      PS   a SP_SHOULDER_MS del PA, por convención de protocolo: con click
           el hombro no tiene firma geométrica confiable.
      FIN  el primer punto después del PA en que el trazo vuelve a
           pegarse a la base, o donde termina de subir si nunca vuelve
           (con el pasa-alto bajo del ECochG la base se inclina).
    """
    if len(t) < 8:
        return {}
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    suave = _smooth(t, y)

    base_sel = (t >= BASELINE_MS[0]) & (t <= BASELINE_MS[1])
    if not base_sel.any():
        return {}
    base = float(np.mean(suave[base_sel]))
    # La marca de base va en el punto del tramo que mejor representa ese
    # nivel, no en un instante fijo: si el alumno la arrastra después, se
    # mueve sobre el trazo igual que las demás.
    x_bl = float(t[base_sel][int(np.argmin(np.abs(suave[base_sel] - base)))])

    pa_sel = np.where((t >= AP_SEARCH_MS[0]) & (t <= AP_SEARCH_MS[1]))[0]
    if not len(pa_sel):
        return {}
    # El PA es el PRIMER pico negativo del complejo, no el más profundo.
    # Con un sumación grande el N2 corre montado sobre la meseta y llega a
    # medir casi lo mismo que el PA: tomando el mínimo absoluto, la marca
    # se iba al N2 justo en los oídos con más hidrops, que son los que
    # importan.
    i_pa = int(pa_sel[int(np.argmin(suave[pa_sel]))])
    mas_hondo = base - float(suave[i_pa])
    if mas_hondo > 0:
        for k in range(1, len(pa_sel) - 1):
            i = int(pa_sel[k])
            if suave[i] > suave[i - 1] or suave[i] > suave[i + 1]:
                continue                      # no es un mínimo local
            if (base - float(suave[i])) >= AP_MIN_DEPTH * mas_hondo:
                i_pa = i
                break
    if suave[i_pa] >= base:
        # No hay ninguna deflexión negativa donde debería estar el PA: no
        # hay complejo que marcar. No se inventa uno.
        return {}
    x_pa = float(t[i_pa])

    marcas = {'BL': x_bl, 'PA': x_pa}

    # Hombro del PS: por CONVENCIÓN, a SP_SHOULDER_MS del pico del PA, y no
    # buscándolo en la forma del trazo.
    #
    # No es pereza: con un click el complejo entero dura alrededor de un
    # milisegundo y los dos potenciales se superponen, así que el hombro no
    # tiene firma geométrica confiable (ver docs/decisiones.md -- se probaron tres
    # detectores y ninguno aguantó el ruido). Es una limitación real de la
    # técnica con click, no del simulador, y por eso los protocolos fijan
    # el punto en vez de buscarlo.
    #
    # Fijar el INSTANTE no regala el resultado: la amplitud sale del trazo,
    # así que con la banda mal puesta o el nivel bajo el PS no está ahí y la
    # razón sale mal igual. Lo que el marcado automático no puede hacer es
    # salvar un registro malo.
    x_ps = x_pa - SP_SHOULDER_MS if ps_at is None else float(ps_at)
    if float(t[0]) < x_ps < float(t[-1]):
        marcas['PS'] = x_ps

    # Retorno a la base: el primer punto después del PA en que el trazo
    # vuelve a pegarse a ella (ver RETURN_FRACTION). Con burst se busca
    # después de la meseta: antes de eso el trazo está sostenido abajo a
    # propósito, y cualquier ondulación del ruido sobre ella parecería el
    # final de la recuperación.
    desde = i_pa
    if ps_at is not None:
        desde = max(i_pa, int(np.argmin(np.abs(t - float(ps_at)))))
    umbral_vuelta = base - RETURN_FRACTION * (base - float(suave[desde]))
    vueltas = np.where(suave[desde:] >= umbral_vuelta)[0]
    fin = int(vueltas[0]) if len(vueltas) else None
    # Si nunca vuelve --con el pasa-alto bajo del ECochG la línea de base
    # se inclina y el trazo puede terminar la ventana del lado de abajo--
    # se usa el final de la recuperación: el primer punto en que deja de
    # subir. Es lo que marca cualquiera mirando el trazo, y sin esto el
    # área quedaba sin medir en uno de cada tres registros del electrodo
    # de conducto, que es donde más falta hace.
    #
    # Con burst solo si nunca vuelve: sobre la meseta el ruido hace topes
    # en cualquier lado y el primero caería en plena meseta.
    subiendo = np.diff(suave[desde:])
    topes = np.where((subiendo[:-1] > 0) & (subiendo[1:] <= 0))[0]
    minimo = int(round(0.3 / max(float(t[1] - t[0]), 1e-9)))
    topes = topes[topes >= minimo]
    if len(topes) and fin is None:
        fin = int(topes[0]) + 1
    if fin is not None:
        marcas['FIN'] = float(t[desde + fin])
    return marcas


# Ancho (ms) con el que se lee el trazo para medir una amplitud. Un cursor
# sobre una pantalla lee la CURVA, no una muestra suelta: con el ruido
# residual de un registro normal, dos marcas puestas en el mismo lugar daban
# amplitudes que se diferenciaban en un 30%, y la razón PS/PA saltaba sola
# entre capturas idénticas.
READ_MS = 0.15


def _sample_at(t, y, x, ms=READ_MS):
    """Valor del trazo en x, leído como lo lee un cursor."""
    i = int(np.argmin(np.abs(t - x)))
    if len(t) < 3 or ms <= 0:
        return float(y[i])
    paso = float(t[1] - t[0])
    n = max(int(round(ms / paso)) // 2, 0)
    desde, hasta = max(i - n, 0), min(i + n + 1, len(y))
    return float(np.mean(y[desde:hasta]))


def complex_onset(t, y, base, x_ps):
    """Dónde se despega el complejo de la línea de base.

    Es el límite izquierdo de las dos integrales y NO se marca a mano: es
    el último punto antes del PS en que el trazo todavía estaba pegado a la
    base (dentro de ONSET_FRACTION de la altura del PS). Marcarlo sería
    pedir una quinta marca para un punto que el trazo ya define.
    """
    idx_ps = int(np.argmin(np.abs(t - x_ps)))
    desvio = base - y[:idx_ps + 1]
    umbral = ONSET_FRACTION * max(float(desvio[idx_ps]), 0.0)
    cruces = np.where(desvio <= umbral)[0]
    if len(cruces):
        return float(t[cruces[-1]])
    return float(t[0])


def ap_half_width(t, y, x_pa, base, amp_ps, amp_pa):
    """Ancho del PA a media altura, en ms.

    Se mide POR ENCIMA de la meseta del PS, no desde la línea de base: lo
    que se quiere leer es cuán sincrónica fue la descarga del nervio, y la
    parte de la profundidad que aporta el desplazamiento DC no tiene nada
    que ver con eso. No pide marca nueva -- sale del pico del PA, de la
    base y del nivel del PS, que el alumno ya marcó.
    """
    altura = amp_pa - amp_ps
    if altura <= 0:
        return None
    nivel = base - (amp_ps + altura / 2.0)
    idx = int(np.argmin(np.abs(t - x_pa)))
    izq = np.where(y[:idx + 1] >= nivel)[0]
    der = np.where(y[idx:] >= nivel)[0]
    if not len(izq) or not len(der):
        return None
    return float(t[idx + der[0]] - t[izq[-1]])


def measure_complex(t, y, marks):
    """Medidas del ECochG a partir de las marcas del alumno.

    Convención: el trazo tiene el PA hacia abajo, así que una amplitud
    positiva es una deflexión negativa (hacia abajo) respecto de la base.

    Las dos áreas se separan con una línea HORIZONTAL a la altura del PS,
    no con un corte en el tiempo:
      - área PS = lo que aporta la meseta del sumación, que corre por
        DEBAJO de todo el complejo de punta a punta;
      - área PA = lo que la espiga del acción agrega POR ENCIMA de esa
        meseta.
    Es la separación que reproduce los valores publicados de la razón de
    áreas (normal ~1.2, límite 1.94): cortando por tiempo en el hombro del
    PS la razón daría ~0.3 y no habría contra qué compararla. Ver docs/decisiones.md.
    """
    faltan = [m for m in ('BL', 'PS', 'PA') if m not in marks]
    if faltan:
        return {'faltan': faltan}

    base = float(marks['BL'][1])
    x_ps, x_pa = float(marks['PS'][0]), float(marks['PA'][0])
    amp_ps = base - _sample_at(t, y, x_ps)
    amp_pa = base - _sample_at(t, y, x_pa)

    out = {
        'base': base,
        'sp_lat': x_ps, 'sp_amp': amp_ps,
        'ap_lat': x_pa, 'ap_amp': amp_pa,
        'sp_ap': (amp_ps / amp_pa) if amp_pa else None,
        'faltan': [],
    }

    if 'FIN' not in marks:
        out['faltan'] = ['FIN']
        return out

    out['ancho_pa'] = ap_half_width(t, y, x_pa, base, amp_ps, amp_pa)

    x_fin = float(marks['FIN'][0])
    x_ini = complex_onset(t, y, base, x_ps)
    out['inicio'] = x_ini
    out['ancho'] = x_fin - x_ini
    vent = (t >= x_ini) & (t <= x_fin)
    if vent.sum() < 2 or amp_ps <= 0 or amp_pa <= 0:
        return out
    desvio = np.clip(base - y[vent], 0.0, None)
    tv = t[vent]
    area_ps = float(np.trapezoid(np.clip(desvio, None, amp_ps), tv))
    # Área PA: solo el lóbulo del N1 por encima de la meseta, o sea el
    # tramo continuo alrededor del pico del PA en que el trazo pasa la
    # altura del PS. El N2 también puede pasarla y no es la espiga del
    # acción: contándolo, un N2 visible bajaba la razón de áreas de 2.0 a
    # 1.5 en el mismo oído (ver docs/decisiones.md).
    exceso = np.clip(desvio - amp_ps, 0.0, None)
    i_pa = int(np.argmin(np.abs(tv - x_pa)))
    desde, hasta = i_pa, i_pa
    while desde > 0 and exceso[desde - 1] > 0:
        desde -= 1
    while hasta < len(exceso) - 1 and exceso[hasta + 1] > 0:
        hasta += 1
    area_pa = (float(np.trapezoid(exceso[desde:hasta + 1],
                                  tv[desde:hasta + 1]))
               if hasta > desde else 0.0)
    out['area_ps'] = area_ps
    out['area_pa'] = area_pa
    out['area_ratio'] = (area_ps / area_pa) if area_pa > 0 else None
    return out


def rate_shift(curvas):
    """Corrimiento del PA entre la tasa más baja y la más alta registradas.

    `curvas` es una lista de dicts {'rate':, 'ap_lat':, 'ap_amp':}. No se
    calcula sobre una curva sola a propósito: el corrimiento por tasa es
    una comparación entre dos registros del mismo oído, y el alumno tiene
    que haberlos capturado.
    """
    con_dato = [c for c in curvas
                if c.get('rate') and c.get('ap_lat') and c.get('ap_amp')]
    if len(con_dato) < 2:
        return None
    lenta = min(con_dato, key=lambda c: c['rate'])
    rapida = max(con_dato, key=lambda c: c['rate'])
    if rapida['rate'] <= lenta['rate']:
        return None
    return {
        'rate_lenta': lenta['rate'], 'rate_rapida': rapida['rate'],
        'd_lat': rapida['ap_lat'] - lenta['ap_lat'],
        'd_amp_pct': 100.0 * (rapida['ap_amp'] - lenta['ap_amp']) / lenta['ap_amp'],
    }


# Corrimiento de latencia del PA esperable entre 11.1/s y 91/s en un oído
# sano, en ms, y caída de amplitud en %. Salen del mismo modelo de tasa que
# el ABR (RATE_LAT_SLOPE / RATE_AMP_DECAY de la onda I): no son una tabla
# aparte que pueda quedar desincronizada del motor.
# Limite del corrimiento de latencia del PA entre la tasa mas lenta y la
# mas rapida. Sale del propio modelo de tasa (el de la onda I del ABR): un
# oido sano corre 0.12 ms entre 11 y 91/s y uno que se adapta al doble y
# medio corre 0.29. El limite va en el medio.
RATE_SHIFT_LIMIT_MS = 0.20
RATE_AMP_DROP_LIMIT_PCT = -65.0

# Diferencia de latencia del PA entre rarefacción y condensación por encima
# de la cual se considera alargada (criterio de hidrops, con click).
RAR_COND_LIMIT_MS = 0.38
POLARITY_PAIR = ('Rarefacción', 'Condensación')


def polarity_shift(curvas):
    """Diferencia de latencia del PA entre rarefacción y condensación.

    `curvas` es una lista de dicts {'pol':, 'stim':, 'int':, 'ap_lat':} en
    el orden en que se registraron. Igual que el corrimiento por tasa, es
    una comparación entre dos registros: solo se arma con una curva de
    cada polaridad del MISMO estímulo y nivel (a distinto nivel el PA se
    corre solo por la intensidad, y eso no es la separación que se busca).
    Si hay más de un par se toma el de nivel más alto, que es donde se
    hace el examen; dentro de cada polaridad, la última registrada.

    La diferencia va en valor absoluto: el criterio es cuánto se separan,
    no cuál llega primero.
    """
    pares = {}
    for c in curvas:
        if c.get('pol') not in POLARITY_PAIR or c.get('ap_lat') is None:
            continue
        try:
            nivel = float(c.get('int'))
        except (TypeError, ValueError):
            continue
        clave = (str(c.get('stim') or ''), nivel)
        pares.setdefault(clave, {})[c['pol']] = float(c['ap_lat'])
    completos = [(k, v) for k, v in pares.items() if len(v) == 2]
    if not completos:
        return None
    (stim, nivel), lat = max(completos, key=lambda kv: kv[0][1])
    rar, cond = lat['Rarefacción'], lat['Condensación']
    return {'stim': stim, 'int': nivel, 'lat_rar': rar, 'lat_cond': cond,
            'd_rc': abs(cond - rar)}


def normative(montage, ap_lat_range=None, burst=False):
    """Límites contra los que se pinta la tabla del ECochG.

    Con burst las dos razones se miden igual pero no se pintan: sus
    límites publicados son de click, y con burst el PA es chico y el PS
    sostenido, así que el mismo oído sano las da muy por encima. Pintarlas
    de rojo sería decirle al alumno que un oído normal tiene hidrops.
    """
    normas = {
        'ap_lat': ap_lat_range,
        'ancho_pa': (None, 0.65),
        'd_lat': (None, RATE_SHIFT_LIMIT_MS),
        'd_rc': (None, RAR_COND_LIMIT_MS),
    }
    if not burst:
        normas['sp_ap'] = (None, SP_AP_LIMIT.get(montage,
                                                 SP_AP_LIMIT['tympanic']))
        normas['area_ratio'] = (None, AREA_RATIO_LIMIT.get(
            montage, AREA_RATIO_LIMIT['tympanic']))
    return normas
