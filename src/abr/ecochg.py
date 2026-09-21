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

Convención de trazo (decidida con el docente, ver TODO.md): PA hacia
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
N2_RATIO = 0.22
N2_MS = 1.05
N2_SIGMA_MS = 0.30
# Cuánto dura el desplazamiento DC del PS después del pico del PA. Es lo
# que hace que la razón de ÁREAS sea distinta de la de amplitudes: la
# meseta corre por debajo de todo el complejo, no solo hasta el PA.
SP_TAIL_MS = 1.35
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
SP_TAIL_PER_RATIO = 5.0
SP_NORMAL_FRACTION = 0.5
POST_POSITIVITY_RATIO = 0.10
POST_POSITIVITY_MS = 2.1
POST_POSITIVITY_SIGMA_MS = 0.55

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
CM_CLICK_MS = 1.0
# Ciclos del tone burst (envolvente 2-1-2): cuánto dura la MC en ms sale de
# la frecuencia del burst.
BURST_CYCLES = 5.0
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

# Cuánto MÁS ruido del propio paciente entra por ese electrodo, contra el
# Cz-mastoides del ABR. NO es lo mismo que la ganancia: la ganancia es el
# camino de la cóclea al electrodo, y el ruido no viene de la cóclea.
#
# Sin esto el electrodo timpánico multiplicaba la respuesta por 8 y dejaba
# el ruido igual, así que el complejo salía entero en el primer bloque de
# barridos: se podía ver la promediación corriendo, pero no había nada que
# mirar. Un electrodo metido en el conducto o apoyado en la membrana toma
# el músculo de ahí mismo, tiene bastante más impedancia que uno de
# superficie y va sobre un paciente incómodo, que se mueve más.
#
# La ventaja de acercarse a la cóclea sigue estando y es la que manda --la
# señal crece mucho más rápido que el ruido: 1.8x de relación señal/ruido
# con el de conducto, 4.4x con el timpánico y 11x con el transtimpánico
# contra un registro de superficie-- pero no es gratis.
ELECTRODE_NOISE_GAIN = {
    'extratympanic': 1.4,
    'tympanic': 1.8,
    'transtympanic': 2.2,
}


# Límite superior normal de la razón de AMPLITUDES PS/PA, por electrodo.
# Cambia con el electrodo y no por capricho: cuanto más lejos de la cóclea,
# más se atenúa el PA (que es de campo cercano y muy sincronizado) frente
# al PS, así que la misma cóclea da razones más altas medida desde el
# conducto. Comparar contra el límite equivocado es el error que el
# ejercicio tiene que dejar cometer.
SP_AP_LIMIT = {
    'extratympanic': 0.50,
    'tympanic': 0.40,
    'transtympanic': 0.30,
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
                     mc_baseline=None, sl=None, gain=1.0, cm_lat=None):
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

    if stim == 'tone_burst' and freq:
        hz = float(str(freq).replace('Hz', '').replace('k', '000') or 1000)
        cm_hz = hz
        cm_ms = BURST_CYCLES * 1000.0 / hz
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

    return {
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
        'cm_onset': (lat_pa - CM_ONSET_BEFORE_AP_MS if cm_lat is None
                     else float(cm_lat)),
        'sp_ap': razon,
    }


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

    # PS: meseta que sube con una sigmoide y se sostiene POR DEBAJO de todo
    # el complejo. No decae con el PA: el desplazamiento DC dura lo que dura
    # el estímulo, y eso es lo que hace que la razón de ÁREAS mida algo
    # distinto de la de amplitudes.
    meseta = _sigmoid(t, params['sp_onset'] + SP_RISE_MS, SP_RISE_MS)
    meseta = meseta * (1.0 - _sigmoid(t, params['ap_lat'] + params['sp_tail'],
                                      SP_RISE_MS * 2))
    y -= sp_amp * meseta

    # PA (N1). La espiga se dibuja con lo que le FALTA para llegar a la
    # amplitud del PA: el PA se mide desde la línea de base, o sea que la
    # meseta del PS ya es parte de su profundidad. Si la gaussiana valiera
    # la amplitud entera, el trazo daría una razón PS/PA más baja que la
    # que declara el caso (el denominador se agrandaría solo).
    y -= _gaussian(t, params['ap_lat'], amp_pa - sp_amp, params['ap_sigma'])
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


def _sample_at(t, y, x):
    """Valor del trazo en x (el más cercano, como cualquier cursor)."""
    return float(y[int(np.argmin(np.abs(t - x)))])


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
    PS la razón daría ~0.3 y no habría contra qué compararla. Ver TODO.md.
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
    area_total = float(np.trapezoid(desvio, t[vent]))
    area_ps = float(np.trapezoid(np.clip(desvio, None, amp_ps), t[vent]))
    area_pa = area_total - area_ps
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
RATE_SHIFT_LIMIT_MS = 0.30
RATE_AMP_DROP_LIMIT_PCT = -65.0


def normative(montage, ap_lat_range=None):
    """Límites contra los que se pinta la tabla del ECochG."""
    return {
        'sp_ap': (None, SP_AP_LIMIT.get(montage, SP_AP_LIMIT['tympanic'])),
        'area_ratio': (None, AREA_RATIO_LIMIT.get(
            montage, AREA_RATIO_LIMIT['tympanic'])),
        'ap_lat': ap_lat_range,
        'ancho_pa': (None, 0.65),
        'd_lat': (None, RATE_SHIFT_LIMIT_MS),
    }
