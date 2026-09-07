"""
Generador ABR - Modelo morfológico realista.

Único generador ABR de la app (reemplazó al modelo Bézier previo, borrado
junto con abr/bezier_prop.py):
- Ondas = suma de gaussianas centradas en cada latencia (no Bézier).
- Bézier aplastaba picos y generaba valles profundos entre ondas (1.25-1.6x amp).
- Valles entre ondas pequenos (~10-20% amp), morfologia ABR real.
- Baseline comun ~0 con drift LF, no escalonamiento por onda.
- Ondas VI (trough negativo) y VII (bump tardio) con morfologia propia.
- Ruido EEG = pink (1/f) + EMG HF, no blanco+butter.
- FSP como SNR creciente (ruido ~ 1/sqrt(N)), no mezcla lineal caos-objetivo.
- Filtros = solo butterworth (SOS), sin hacks morfológicos, con el fs real
  del eje temporal (~41.6 kHz) y no un 20000 fijo que corría cada corte
  2.08x arriba del rótulo.
- Amplitud gobernada por el nivel de sensación (SL = intensidad - umbral),
  saturante, no normalizada contra un techo fijo de 80 dB: un oído con
  umbral 60 ya no muestra a 80 dB la amplitud de un oído sano.
- Las ondas se apagan con un codo suave, sin el escalón de disappear_offset
  que borraba la onda I de golpe a 70 dB.
- Tasa de estimulación continua y anclada en 21.1/s, con magnitudes
  clínicas (onda V: ~+0.5 ms y -25% entre 11 y 91/s).
- La patología entra en la física, no solo en el umbral: conductiva =
  corrimiento paralelo por el GAP (interpicos intactos), neural =
  interpicos prolongados y razón V/I caída, coclear = reclutamiento.
- Enmascaramiento real: curva sombra del oído no evaluado cuando el
  estímulo cruza el cráneo, y sobreenmascaramiento cuando vuelve.
- Población normativa según edad/sexo del paciente (neonato, niño,
  adulto por sexo, adulto mayor), no siempre adult_female.
- Promediación como en un equipo: la señal está completa desde el primer
  barrido y lo que cae es el ruido (1/sqrt(N)), con el trazo asentándose
  de a poco en vez de sortearse entero en cada tick.
- Ruido sembrado con core.rng.stable_seed: la misma captura del mismo
  paciente se redibuja igual entre aperturas de la app.
- Subpromedios A/B (barridos pares e impares) e índice de replicabilidad:
  la replicabilidad se ve EN VIVO, no solo repitiendo la captura. Un caso
  no reproducible tampoco mantiene el timing dentro de una captura, así
  que sus dos subpromedios no se pegan nunca.
- Canal contralateral propio (onda I casi ausente, IV-V separadas, V un
  poco más tardía), no una copia del ipsi, y solo si ese electrodo está
  puesto.
- Monitor de EEG crudo por canal (raw_eeg): el 50 Hz, la impedancia y la
  tensión del paciente se ven ANTES de promediar, que es cuando se
  arreglan.
- El FSP medido cae con los electrodos malos (es una razón de varianzas):
  antes se podía registrar a 15 kOhm y el equipo declaraba igual
  "respuesta presente".
- Rangos normativos y banda latencia-intensidad calculados con la MISMA
  función latencia-intensidad que dibuja la curva, y para la población del
  paciente: con una banda fija de adulto, todo neonato quedaba fuera de
  norma.
"""

import json
import random
import numpy as np
import scipy.signal as signal
from core.base import context
from core import app_config_store
from abr.protocols import get_protocol
from core.rng import case_fingerprint, stable_seed


# Anchos base (sigma en ms) por onda. Calibrados para FWHM realista
# de ABR con click a 80 dB. Se multiplican por width_factor segun
# intensidad (mas ancho a menor dB).
WAVE_SIGMA = {
    'I':   0.22,
    'II':  0.18,
    'III': 0.22,
    'IV':  0.18,
    'V':   0.18,
    'VI':  0.22,   # trough negativo
    'VII': 0.40,   # bump tardio, mas ancho
}

# Crecimiento de amplitud por NIVEL DE SENSACION (SL = intensidad - umbral).
#   amp_factor = 1 - exp(-(SL - sl_min) / tau)
# Saturante y anclado al umbral del oido, no lineal contra un techo fijo de
# 80 dB: antes un oido con umbral 60 mostraba a 80 dB la amplitud normativa
# COMPLETA (0.6 uV de onda V a 20 dB SL), que es el aspecto de un oido sano.
#   sl_min = SL desde el que la onda empieza a emerger. I y II necesitan mas
#            nivel que V -- por eso son las primeras que se pierden al bajar.
#   tau    = que tan rapido satura.
# Calibrado para que a ~60 dB SL (oido normal estimulado a 80 dB, que es
# como estan medidos los valores del JSON normativo) el factor sea ~0.95.
WAVE_AMP_GROWTH = {
    'I':   {'sl_min': 20, 'tau': 13},   # la primera en perderse (~40 dB SL)
    'II':  {'sl_min': 22, 'tau': 14},
    'III': {'sl_min': 5,  'tau': 16},
    'IV':  {'sl_min': 8,  'tau': 17},
    'V':   {'sl_min': -4, 'tau': 20},   # sigue presente en el umbral mismo
}

# Reclutamiento: en perdida coclear la amplitud crece mas rapido con el SL,
# por eso a nivel alto la onda V puede verse casi normal pese al umbral
# elevado (recruitment: true en normative_data.json). Multiplica tau.
PATHOLOGY_TAU_FACTOR = {'cochlear': 0.65}

# Funcion latencia-intensidad de la perdida COCLEAR. No es la normal (que
# es lo que hacia antes: la patologia coclear no tocaba la latencia, solo
# la amplitud) ni el corrimiento paralelo de la conductiva. Cerca del
# umbral la latencia se alarga desproporcionado y al subir el nivel de
# sensacion converge a la normal -- por eso la V a nivel alto se ve casi
# normal pese al umbral elevado, y por eso la curva L-I de una coclear es
# EMPINADA en vez de corrida. Sin esto, subir de 80 a 100 dB en un caso
# coclear movia la V 0.16 ms y la funcion salia igual a la de un oido sano.
# Pendiente extra (ms) por cada 10 dB de SL por debajo de la referencia.
COCHLEAR_LI_SL_REF = 40.0
COCHLEAR_LI_SLOPE = 0.15

# Las desviaciones del caso se definen pensando en click a NIVEL ALTO
# (80 dB, que es como se leen los informes). Sumarlas iguales a toda
# intensidad dibujaba un corrimiento paralelo -- pinta de conductiva-- en
# cualquier patologia. La misma alteracion se expresa MAS cerca del umbral,
# asi que se amplifican con el corrimiento L-I, con tope.
DEV_LI_GAIN = 0.35
DEV_LI_MAX = 1.5

# La funcion latencia-intensidad no corre todas las ondas lo mismo: el
# interpico I-V se ensancha SOLO un poco al bajar la intensidad (0.2-0.4 ms
# entre 80 y 20 dB). Factor sobre el shift de la onda V. Antes la onda I
# usaba 0.2 y el resto 1.0 -> I-V pasaba de 3.85 a 5.11 ms, imposible.
LAT_SHIFT_FACTOR = {'I': 0.85, 'II': 0.90, 'III': 0.92, 'IV': 0.96, 'V': 1.0}

# Tasa de estimulacion. Los valores normativos se miden a ~21.1/s (tasa
# clinica tipica) -- ese es el ancla: ahi el modelo no toca nada. Por
# encima la latencia crece lineal (ms por estimulo/s) y la amplitud cae
# exponencial; por debajo el efecto se invierte suave. Todo continuo: antes
# habia tramos 15/50/60/70 con saltos (la onda II pasaba de 0.110 a 0.006
# uV entre 55 y 60/s) y rangos irreales (onda V variaba 6.4x en amplitud y
# 1.1 ms en latencia entre 11 y 90/s; lo real es ~25-30% y ~0.4-0.6 ms).
RATE_REF = 21.1
RATE_LAT_SLOPE = {'I': 0.0025, 'II': 0.0035, 'III': 0.0045,
                  'IV': 0.0055, 'V': 0.0060}
RATE_AMP_DECAY = {'I': 0.0060, 'II': 0.0070, 'III': 0.0045,
                  'IV': 0.0060, 'V': 0.0035}
# Patologia neural = mala resistencia a tasas altas ("rate_effect": "severe"
# en normative_data.json): mismo modelo, decaimiento y corrimiento mayores.
RATE_NEURAL_AMP_FACTOR = 2.2
RATE_NEURAL_LAT_FACTOR = 1.5

# Umbral de referencia de un oido sano (dB nHL). Lo que un oido tiene por
# ENCIMA de esto, en patologia conductiva, es GAP: atenuacion pura del
# estimulo antes de llegar a la coclea.
NORMAL_THRESHOLD_REF = 15

# Patologia neural (retrococlear): prolongacion de interpicos repartida
# desde la I (que no se mueve, es el nervio distal) hacia la V, y caida de
# amplitud de las ondas rostrales. Con estos factores la razon V/I cae de
# ~2.9 a ~1.3, dentro del rango [0.5, 1.5] que declara
# normative_data.json -> pathology_modifiers.neural.amplitude_v_i_ratio.
NEURAL_LAT_SHARE = {'I': 0.0, 'II': 0.25, 'III': 0.5, 'IV': 0.75, 'V': 1.0}
NEURAL_AMP_FACTOR = {'I': 1.0, 'II': 0.85, 'III': 0.75, 'IV': 0.55, 'V': 0.45}

# "Retrococlear" no es UN hallazgo ni un catalogo de diagnosticos: es un
# puñado de PATRONES electrofisiologicos que se combinan. El ABR no separa
# un schwannoma de un meningioma del angulo --eso lo dice la RM-- pero si
# separa un I-III largo de un III-V largo, un bloqueo proximal de una
# desincronia, o un retraso global de uno selectivo. Por eso el caso no
# elige "la entidad" sino los parametros del patron, y las entidades viven
# como presets del formulario docente (ABR_NEURAL_PRESETS en CaseBuilder.php)
# que los precargan y quedan editables.
#
# Cada parametro cubre uno de los patrones que se enseñan:
#   i_iii_ms          prolongacion selectiva I-III (nervio a puente inferior)
#   iii_v_ms          prolongacion selectiva III-V (pontino alto/mesencefalo)
#                     -- los dos juntos dan la prolongacion I-V global
#   global_delay_ms   TODO el complejo corrido, onda I incluida: no es una
#                     lesion de via sino conduccion lenta pareja
#                     (hipotermia, depresores del SNC, prematuro). El resto
#                     de los parametros deja la I quieta a proposito, porque
#                     nace antes de cualquier lesion retrococlear.
#   bloqueo           'post_i' = solo onda I (coclea viva, bloqueo proximal;
#                     tambien el patron de muerte encefalica), 'total' =
#                     ninguna respuesta neural.
#   v_i_factor        amplitud de la V respecto de la I (razon V/I). 1.0 =
#                     sin caida; 0.45 = la V a menos de la mitad.
#   microfonica       'amplificada' = queda el microfonico coclear cuando no
#                     hay ondas. Es lo que separa una desincronia (CM
#                     presente, invierte con la polaridad) de una ausencia
#                     de respuesta de verdad.
#   desincronia       ensancha las ondas y empeora la morfologia.
#   sensibilidad_tasa cuanto se degrada a tasas altas (fatiga de conduccion,
#                     el hallazgo de las desmielinizantes).
#
# Los defaults son el perfil que tenia el modelo cuando "neural" era un solo
# cuadro: un caso guardado antes de esto dibuja exactamente lo mismo.
NEURAL_PARAM_DEFAULTS = {
    'i_iii_ms': 0.2,
    'iii_v_ms': 0.2,
    'global_delay_ms': 0.0,
    'bloqueo': 'ninguno',
    'v_i_factor': 0.45,
    'microfonica': 'normal',
    'desincronia': 'ninguna',
    'sensibilidad_tasa': 'severa',
}
NEURAL_BLOQUEO_OPTIONS = ('ninguno', 'post_i', 'total')
# Reparto del retraso hacia las ondas intermedias: la II cae entre I y III,
# la IV entre III y V.
NEURAL_LAT_SHARE = {'I': 0.0, 'II': 0.5, 'III': 1.0, 'IV': 1.0, 'V': 1.0}
NEURAL_LAT_SHARE_IIIV = {'I': 0.0, 'II': 0.0, 'III': 0.0, 'IV': 0.5, 'V': 1.0}
# Cuanto de la caida de amplitud le toca a cada onda: la I intacta, la V
# con la caida completa (v_i_factor).
NEURAL_AMP_SHARE = {'I': 0.0, 'II': 0.25, 'III': 0.5, 'IV': 0.75, 'V': 1.0}
# Lo que queda de una onda "bloqueada": por debajo del umbral de
# visibilidad (0.02 uV), no un cero exacto -- el trazo sigue teniendo ruido.
NEURAL_BLOCK_AMP_FACTOR = 0.02
NEURAL_DESYNC_WIDTH = {'ninguna': 1.0, 'leve': 1.35, 'alta': 1.9}
# (latencia, amplitud) sobre el efecto de la tasa. 'severa' es el valor con
# el que se calibro "rate_effect": "severe" de normative_data.json.
NEURAL_RATE_FACTORS = {
    'normal': (1.0, 1.0),
    'moderada': (1.25, 1.6),
    'severa': (RATE_NEURAL_LAT_FACTOR, RATE_NEURAL_AMP_FACTOR),
}
NEURAL_CM_GAIN = {'normal': 1.0, 'amplificada': 7.0}
# El CM de una desincronia no es el pulso corto pre-onda I del oido sano:
# dura lo que dura el estimulo y se sigue viendo donde deberia estar la I.
NEURAL_CM_SIGMA_GAIN = 3.5

# Atenuacion interaural (dB): cuanto pierde el estimulo al cruzar el craneo
# hasta la coclea del otro lado. Por debajo de esto no hay curva sombra.
# Insertos aislan mucho mas que los supraaurales, que es justamente el
# argumento clinico para usarlos.
INTERAURAL_ATTENUATION = {
    'insert_earphone': 65.0,
    'TDH39_headphone': 45.0,
    'bone_vibrator': 0.0,     # el vibrador oseo estimula las dos cocleas
}
# La respuesta del oido NO evaluado se registra desde un montaje pensado
# para el otro lado: llega mas chica y sobre todo sin onda I reconocible.
SHADOW_AMP_FACTOR = 0.7
SHADOW_WAVE_I_FACTOR = 0.3

# Ruido residual del promediado (uV RMS) con FSP y electrodos ideales, al
# llegar al average objetivo del caso. NOISE_BLOCKS = en cuantos bloques se
# parte ese objetivo: el residual es el promedio de los bloques ya
# acumulados, asi que cae como 1/sqrt(N) y ADEMAS evoluciona de a poco
# (agregar un bloque mueve el trazo 1/m), en vez de sortearse entero de
# nuevo en cada tick como antes.
NOISE_FLOOR_UV = 0.055
NOISE_BLOCKS = 200
# Techo de seguridad del ruido al arrancar la promediacion: mas que esto se
# sale de la escala del grafico y deja de leerse como ruido.
NOISE_MAX_UV = 1.2

# Muestras por ms del registro: 500 puntos en 12 ms. Se mantiene constante
# al cambiar la ventana para que fs no dependa del protocolo (~41.6 kHz,
# rango real de un equipo). Ver technical_config['window_ms'].
SAMPLES_PER_MS = 500 / 12

# El tubo del fono de insercion retrasa el sonido ~0.9 ms y los valores
# normativos estan medidos CON insertos: al pasar a supraaural todo el
# complejo aparece 0.9 ms antes. Es el ajuste que en clinica se hace de
# cabeza al comparar informes de equipos distintos.
TRANSDUCER_LATENCY_MS = {
    'insert_earphone': 0.0,
    'TDH39_headphone': -0.9,
    'bone_vibrator': 0.0,   # via osea: tiene su propio bloque normativo
}

# Montajes fuera de technical_factors.electrode_montage del JSON.
EXTRA_MONTAGE_FACTOR = {
    'tympanic': 2.5,        # ECochG: electrodo en la membrana, todo mas grande
}

# Rechazo de artefacto: un umbral estrecho descarta mas barridos (el
# promedio avanza mas lento) y uno ancho deja entrar barridos sucios.
ARTIFACT_REJECT_REF_UV = 18.0
NO_REJECT_NOISE_FACTOR = 1.4

# Limites clinicos de impedancia de electrodos. No son adorno: son las dos
# reglas que el alumno tiene que poder justificar mirando el trazo.
#   - Cada electrodo bajo 5 kOhm: por encima, el contacto es malo y el
#     ruido del registro se dispara.
#   - Diferencia entre electrodos bajo 2 kOhm: el amplificador diferencial
#     rechaza el modo comun (CMRR) solo si las impedancias son parecidas;
#     desbalanceadas, la red electrica entra como senial diferencial.
# Los dos limites son codos del modelo, no una pendiente suave: cruzarlos
# tiene que verse.
IMPEDANCE_LIMIT_KOHM = 5.0
IMPEDANCE_BALANCE_LIMIT_KOHM = 2.0
# Cuanto empeora el ruido por cada kOhm sobre el limite (exponente > 1: se
# acelera, un electrodo a 20 kOhm es un electrodo despegado). El tope es
# el electrodo despegado: mas alla de ahi el trazo ya es inservible y da
# lo mismo cuanto peor sea.
IMPEDANCE_OVER_EXPONENT = 1.5
IMPEDANCE_OVER_SCALE = 2.0
IMPEDANCE_MAX_FACTOR = 12.0

# Interferencia de red (50 Hz en Chile). Aparece cuando los electrodos
# quedan desbalanceados en impedancia o cuando falta la tierra: es EL
# artefacto que el alumno tiene que aprender a reconocer y corregir.
MAINS_HZ = 50.0
# Calibrados sobre lo que SOBREVIVE al pasa-alto de 100 Hz del ABR: sin
# tierra el trazo queda claramente montado sobre el zumbido (~0.2 uV RMS,
# la mitad de una onda V).
# Con el desbalance DENTRO de norma queda un zumbido residual invisible;
# pasado el limite el CMRR se cae y crece rapido, asi que la diferencia
# entre 2 y 3 kOhm se ve en pantalla.
MAINS_UV_PER_KOHM_IN_SPEC = 0.03
MAINS_UV_PER_KOHM_OVER = 1.2
MAINS_NO_GROUND_UV = 3.0

DISCONNECTED = 'No Conectado'

# Canal contralateral: la misma respuesta registrada desde el mastoides del
# oido NO estimulado. No es otra respuesta -- es el mismo generador visto
# desde otro vector, y por eso:
#   - la onda I casi desaparece (la genera el nervio distal, que esta
#     pegado al electrodo IPSI y lejisimos del contra);
#   - III-V se conservan (generadores de tronco, mas mediales);
#   - el complejo IV-V se separa y la V queda un pelo mas tarde y mas ancha.
# Esa comparacion ipsi/contra es lo que permite lateralizar una lesion de
# tronco, y es la razon clinica de registrar los dos canales a la vez.
CONTRA_AMP_FACTOR = {'I': 0.15, 'II': 0.55, 'III': 0.85, 'IV': 0.75, 'V': 0.90}
CONTRA_LAT_SHIFT = {'I': 0.0, 'II': 0.05, 'III': 0.05, 'IV': -0.10, 'V': 0.15}
CONTRA_WIDTH_FACTOR = 1.15

# EEG crudo (monitor previo a promediar). Un adulto relajado corre en
# ~10-15 uV RMS; tenso o con EMG de cuello se va al doble o mas. Es el
# trazo donde el alumno tiene que ver el 50 Hz y la tension ANTES de
# promediar, no despues de 2000 barridos.
EEG_BASELINE_UV = 12.0
EEG_TENSION_UV = 9.0
# Lo que el pasa-alto de 100 Hz del ABR se come del zumbido de red y en el
# monitor crudo (sin filtrar) se ve entero. MAINS_* estan calibrados sobre
# el residuo post-filtro, ver mains_interference.
MAINS_RAW_GAIN = 12.0
# Frecuencia de muestreo del monitor de EEG: no hace falta el fs del
# promediador (41.6 kHz) para mirar un trazo con 50 Hz y EMG.
EEG_DISPLAY_FS = 500.0

# Bloques de ruido por tanda. Fijo (no min(64, faltantes)) para que el
# bloque i sea SIEMPRE el mismo bloque, no dependa de cuantos se pidieron:
# de eso vive que el trazo se asiente en vez de resortearse, y que los
# subpromedios A/B (pares/impares) sean estables entre ticks.
NOISE_TANDA = 64

# Impedancia de referencia (kOhm): el equipo bien puesto de default_settings.
# Es el punto donde el FSP del caso vale tal cual; de ahi para arriba el
# ruido sube y el FSP medido cae solo.
IMPEDANCE_REF_KOHM = 2.0

# Rango de normalidad clinico: +-2 DE alrededor del valor poblacional.
# El JSON normativo trae las medias, no las desviaciones -- estas son las
# DE tipicas de click a 80 dB nHL con las que se leen los informes.
NORM_SD_LIMIT = 2.0
NORM_LAT_SD = {'I': 0.20, 'II': 0.25, 'III': 0.22, 'IV': 0.28, 'V': 0.25}
NORM_INTERPEAK_SD = {'I-III': 0.22, 'III-V': 0.22, 'I-V': 0.25}
# Razon V/I: por debajo de esto la onda V esta desproporcionadamente chica
# respecto de la I, hallazgo retrococlear clasico.
NORM_VI_RATIO_MIN = 0.5
# Diferencia interaural de la onda V que se considera significativa (ms).
NORM_INTERAURAL_MAX = 0.4


def select_population(age=None, gender=None):
    """Poblacion normativa segun el paciente (claves de normative_data.json).

    gender: 0 = hombre, 1 = mujer (mismo criterio que cases.data['gender']
    en CaseBuilder.php). Sin edad -> adult_female, que era el valor fijo
    que usaba el modulo antes de esto.

    Las franjas del JSON dejan huecos (neonate 0-0.25, child 2-12,
    adult 18-50, elderly 60-85); acá se cubren completas porque un paciente
    de 1, 15 o 55 anios existe igual. Un lactante se aproxima con 'child'
    (la via auditiva ya madura cerca de los 18 meses) y 13-17 tambien,
    porque a esa edad las latencias ya son practicamente de adulto.
    """
    if age is None:
        return 'adult_female'
    try:
        age = float(age)
    except (TypeError, ValueError):
        return 'adult_female'
    if age < 1:
        return 'neonate'
    if age < 18:
        return 'child'
    if age >= 60:
        return 'elderly'
    return 'adult_male' if str(gender) == '0' else 'adult_female'


class ABRGenerator:
    """Generador de curvas ABR con morfologia realista."""

    def __init__(self, normative_data_path=None):
        if normative_data_path is None:
            normative_data_path = context.get_resource('abr/normative_data.json')
        with open(normative_data_path, 'r', encoding='utf-8') as f:
            self.norms = json.load(f)

    # =====================================================================
    # VALORES NORMATIVOS Y PARAMETROS POR ONDA
    # =====================================================================

    def get_baseline_values(self, population='adult_female',
                            stimulus='click', pathway='air_conduction',
                            freq=None, ratio_override=None):
        """
        Click SIEMPRE sale del baseline poblacional tal cual -- el perfil
        real del paciente lo ajusta aparte via 'desviaciones' del caso (ver
        calculate_wave_parameters), nunca se pisa desde acá. Cualquier otro
        estimulo guarda solo un ratio respecto a click (lat_ratio/amp_ratio,
        nunca su propio absoluto ni un delta): cuanto se desvia chirp/burst
        del click de ESE paciente. Ese ratio SI es configurable por curso
        (ratio_override, ver core.app_config_store / AppConfig.php en el
        backend) -- es comportamiento del estimulo/equipo que el docente
        calibra, no un dato del paciente. Sin ratio (ni override ni default
        bundleado) -> 1.0 (misma forma que click).

        ratio_override: dict {stim_key: {onda: {'lat_ratio':.., 'amp_ratio':..}}}
        -- stim_key = 'ce_chirp'/'ls_chirp'/'tone_burst_<freq>' (ver STIM_MAP).
        Gana sobre el default bundleado, onda por onda.
        """
        pop = self.norms['populations'][population]
        via = pop.get(pathway) or pop['air_conduction']
        click = via['click']
        if stimulus == 'click':
            return click

        if stimulus == 'tone_burst':
            stim_key = f"tone_burst_{freq or '1000Hz'}"
            default_ratio_block = (via.get('tone_burst') or {}).get(freq or '1000Hz')
        else:
            stim_key = stimulus
            default_ratio_block = via.get(stimulus)

        # El JSON no describe todos los estimulos en todas las poblaciones
        # (neonato solo trae click y ce_chirp, por ejemplo). Sin esto, pedir
        # un burst de 500 Hz en un neonato devolvia los valores del click en
        # silencio, o sea el estimulo no hacia NADA. Los ratios son una
        # propiedad del estimulo mucho mas que de la poblacion, asi que se
        # caen a los del adulto en vez de inventarse un 1.0.
        if not default_ratio_block:
            fallback = (self.norms['populations']['adult_female'].get(pathway)
                        or self.norms['populations']['adult_female']['air_conduction'])
            if stimulus == 'tone_burst':
                default_ratio_block = (fallback.get('tone_burst') or {}).get(freq or '1000Hz')
            else:
                default_ratio_block = fallback.get(stimulus)

        default_ratio_block = self._complete_ratio_block(default_ratio_block, click)
        override_block = (ratio_override or {}).get(stim_key)

        baseline = {}
        for wave, click_vals in click.items():
            if wave == 'interpeak':
                continue
            ratio = {'lat_ratio': 1.0, 'amp_ratio': 1.0}
            if default_ratio_block and wave in default_ratio_block:
                ratio.update(default_ratio_block[wave])
            if override_block and wave in override_block:
                ratio.update(override_block[wave])
            baseline[wave] = {
                'lat': click_vals['lat'] * ratio['lat_ratio'],
                'amp': click_vals['amp'] * ratio['amp_ratio'],
            }
        return baseline

    @staticmethod
    def _complete_ratio_block(block, click):
        """Rellena las ondas que el bloque de ratios no describe.

        Los bloques de tone_burst solo traen I, III y V (son las que se
        miden en clinica). Dejar II y IV en 1.0 daba una curva imposible:
        un burst de 500 Hz corria la I y la III casi un ms y dejaba la II
        clavada en la latencia del click, cruzandose con ellas. Se
        interpola por posicion de onda entre las descritas.
        """
        if not block:
            return block
        orden = [w for w in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'] if w in click]
        idx_con = [i for i, w in enumerate(orden)
                   if w in block and isinstance(block[w], dict)]
        if not idx_con or len(idx_con) == len(orden):
            return block

        completo = dict(block)
        for clave in ('lat_ratio', 'amp_ratio'):
            xs = idx_con
            ys = [float(block[orden[i]].get(clave, 1.0)) for i in idx_con]
            for i, wave in enumerate(orden):
                if i in idx_con:
                    continue
                valor = float(np.interp(i, xs, ys))
                completo.setdefault(wave, {})
                completo[wave] = dict(completo[wave])
                completo[wave][clave] = valor
        return completo

    @staticmethod
    def neural_params(neural=None):
        """Parametros del patron retrococlear, completados con los defaults.

        Un caso guardado antes de que existieran (o con una clave sola)
        cae en NEURAL_PARAM_DEFAULTS, que es el cuadro que dibujaba el
        modelo cuando 'neural' era uno solo.
        """
        params = dict(NEURAL_PARAM_DEFAULTS)
        for clave, valor in (neural or {}).items():
            if clave in params and valor is not None:
                params[clave] = valor
        if params['bloqueo'] not in NEURAL_BLOQUEO_OPTIONS:
            params['bloqueo'] = 'ninguno'
        return params

    def calculate_wave_parameters(self, baseline, intensity, threshold,
                                   pathology, desviaciones=None, repro_shift=0.0,
                                   click_baseline=None, neural=None):
        modified = {}
        # Patologia conductiva = el estimulo llega atenuado a una coclea
        # sana, asi que la respuesta es la de un nivel MENOR: toda la
        # funcion latencia-intensidad se corre a la derecha en paralelo,
        # con los interpicos intactos. Ese corrimiento paralelo es el
        # hallazgo que distingue conductiva de coclear en el grafico
        # latencia-intensidad, y antes no existia (la patologia entraba
        # solo por el umbral, que unicamente afectaba amplitud).
        gap = 0.0
        if pathology == 'conductive':
            gap = max(threshold - NORMAL_THRESHOLD_REF, 0.0)
        lat_intensity = intensity - gap

        lat_shift = self.latency_intensity_shift(lat_intensity)

        # Nivel de sensacion: cuanto por encima del umbral DE ESTE OIDO se
        # esta estimulando. Es lo que manda en amplitud y en ancho de la
        # onda; la intensidad absoluta sola no dice nada (80 dB en un oido
        # con umbral 60 son 20 dB SL, no una respuesta maxima).
        sl = intensity - threshold

        # Coclear: la funcion L-I se empina cerca del umbral (ver
        # COCHLEAR_LI_SLOPE) y converge a la normal a SL alto.
        if pathology == 'cochlear':
            lat_shift += (COCHLEAR_LI_SLOPE
                          * max(0.0, COCHLEAR_LI_SL_REF - sl) / 10.0)

        # Amplificacion de las desviaciones del caso segun donde cae la
        # respuesta en la funcion L-I (ver DEV_LI_GAIN).
        dev_int_scale = min(1.0 + DEV_LI_GAIN * max(lat_shift, 0.0), DEV_LI_MAX)

        # Patologia neural (retrococlear): el retraso se acumula de la I
        # hacia la V, o sea prolonga los interpicos I-III/III-V en vez de
        # correr el complejo entero.
        neural_params = self.neural_params(neural)
        is_neural = pathology == 'neural'

        tau_factor = PATHOLOGY_TAU_FACTOR.get(pathology, 1.0)

        for wave in ['I', 'II', 'III', 'IV', 'V']:
            if wave not in baseline:
                continue
            base_lat = baseline[wave]['lat']
            # repro_shift: jitter de "no reproducible" -- mueve TODO el
            # complejo junto (misma respuesta neural, timing inconsistente),
            # no una onda aislada.
            calc_lat = (base_lat + lat_shift * LAT_SHIFT_FACTOR.get(wave, 1.0)
                        + repro_shift)
            if is_neural:
                # I-III y III-V se prolongan por separado: es la diferencia
                # entre una lesion del nervio y una pontina alta. El retraso
                # global corre TODO, onda I incluida (conduccion lenta
                # pareja, no lesion de via).
                calc_lat += (
                    float(neural_params['global_delay_ms'])
                    + float(neural_params['i_iii_ms']) * NEURAL_LAT_SHARE.get(wave, 1.0)
                    + float(neural_params['iii_v_ms']) * NEURAL_LAT_SHARE_IIIV.get(wave, 1.0)
                )
            # Escala de la desviacion segun estimulo: el caso clinico define
            # la desviacion pensando en click (estimulo estandar), pero
            # latencia/amplitud base cambian fuerte con el estimulo (burst
            # de baja frecuencia agrega ms de recorrido coclear, chirp
            # sincroniza y sube amplitud). Sin escalar, el mismo delta
            # absoluto de click quedaria sub/sobre-representado en otros
            # estimulos. ref = baseline de click misma poblacion/via.
            lat_scale, amp_scale = 1.0, 1.0
            if click_baseline and wave in click_baseline:
                ref_lat = click_baseline[wave]['lat']
                ref_amp = click_baseline[wave]['amp']
                if ref_lat:
                    lat_scale = base_lat / ref_lat
                if ref_amp:
                    amp_scale = baseline[wave]['amp'] / ref_amp
            if desviaciones and wave in ['I', 'III', 'V']:
                key = f"onda_{wave}"
                if key in desviaciones:
                    calc_lat += (desviaciones[key]['lat'] * lat_scale
                                 * dev_int_scale)

            # Amplitud = curva de crecimiento saturante sobre el SL (ver
            # WAVE_AMP_GROWTH). Reemplaza el escalon de disappear_offset,
            # que borraba la onda I de golpe a 70 dB (0.21 -> 0.011 uV en un
            # paso) cuando en un oido normal la I se sigue viendo hasta
            # 50-60 dB.
            growth = WAVE_AMP_GROWTH[wave]
            tau = growth['tau'] * tau_factor
            # Codo suave (softplus) en vez de max(x, 0): la onda se apaga
            # de forma gradual al acercarse a su sl_min en vez de cortarse
            # seco. logaddexp para que no reviente con exponentes grandes.
            knee = 0.3 * tau
            sl_eff = knee * np.logaddexp(0.0, (sl - growth['sl_min']) / knee)
            amp_factor = 1.0 - np.exp(-sl_eff / tau)

            calc_amp = baseline[wave]['amp'] * amp_factor
            if is_neural:
                # Las ondas rostrales son las que se caen: baja la razon
                # V/I, repartida de la I (intacta) a la V (v_i_factor).
                caida = (1.0 - float(neural_params['v_i_factor'])) \
                    * NEURAL_AMP_SHARE.get(wave, 1.0)
                calc_amp *= max(1.0 - caida, 0.0)
                # Bloqueo proximal: la coclea responde (onda I) pero mas
                # arriba no pasa nada. 'total' no deja ninguna.
                bloqueo = neural_params['bloqueo']
                if bloqueo == 'total' or (bloqueo == 'post_i' and wave != 'I'):
                    calc_amp *= NEURAL_BLOCK_AMP_FACTOR
            if desviaciones and wave in ['I', 'III', 'V']:
                key = f"onda_{wave}"
                if key in desviaciones:
                    calc_amp += desviaciones[key]['amp'] * amp_scale
            calc_amp = max(calc_amp, 0.001)

            # Ensanchamiento cerca del umbral, tambien por SL (antes iba
            # contra la intensidad absoluta: un oido con perdida no
            # ensanchaba nunca).
            if sl >= 50:
                width_factor = 1.0
            elif sl >= 30:
                width_factor = 1.0 + (50 - sl) * 0.03
            else:
                width_factor = min(1.6 + (30 - sl) * 0.05, 2.6)
            if is_neural:
                # Morfologia pobre/desincronizada: ondas anchas y romas, que
                # es lo que se ve antes de que desaparezcan del todo.
                width_factor *= NEURAL_DESYNC_WIDTH.get(
                    neural_params['desincronia'], 1.0)

            modified[wave] = {
                'lat': calc_lat,
                'amp': calc_amp,
                'width': width_factor,
            }

        return modified, {w: modified[w]['amp'] > 0.02 for w in modified}

    def apply_polarity_effects(self, values, polarity, pathology='normal',
                               neural=None):
        CM_value = None
        if polarity == 'Rarefacción':
            for w in values:
                values[w]['amp'] *= 1.1
            if 'I' in values:
                values['I']['lat'] -= 0.1
            CM_value = -0.15
        elif polarity == 'Condensación':
            if 'V' in values:
                values['V']['amp'] *= 1.15
            if 'I' in values:
                values['I']['lat'] += 0.1
            CM_value = 0.15
        # Con polaridad alternada el CM se cancela (CM_value queda None):
        # es justamente por eso que una desincronia auditiva se busca con
        # rarefaccion y condensacion por separado.
        if CM_value is not None and pathology == 'neural':
            CM_value *= NEURAL_CM_GAIN.get(
                self.neural_params(neural)['microfonica'], 1.0)
        return values, CM_value

    def apply_rate_effects(self, values, rate, pathology, neural=None):
        """Efecto de la tasa de estimulacion, continuo y anclado en RATE_REF.

        Latencia lineal en la tasa (ms por estimulo/s) y amplitud
        exponencial decreciente, ambas por onda: la I es la mas sensible a
        la tasa y la V la que mejor aguanta, que es justo lo que se ensena.
        Sin escalones ni tramos: el modelo viejo tenia quiebres en 15/50/60
        y rangos irreales (ver comentario de RATE_REF).
        """
        d_rate = rate - RATE_REF
        lat_gain, amp_gain = 1.0, 1.0
        if pathology == 'neural':
            lat_gain, amp_gain = NEURAL_RATE_FACTORS.get(
                self.neural_params(neural)['sensibilidad_tasa'],
                NEURAL_RATE_FACTORS['severa'])

        for wave, v in values.items():
            if wave not in RATE_LAT_SLOPE:
                continue
            v['lat'] += RATE_LAT_SLOPE[wave] * d_rate * lat_gain
            decay = np.exp(-RATE_AMP_DECAY[wave] * amp_gain * d_rate)
            # Techo bajo (tasas lentas suben poco la amplitud) y piso: ni a
            # 91/s la respuesta desaparece del todo en un oido normal.
            v['amp'] *= float(np.clip(decay, 0.15, 1.20))
        return values

    # =====================================================================
    # MODELO MORFOLOGICO (NUEVO): SUMA DE GAUSSIANAS
    # =====================================================================

    @staticmethod
    def _gaussian(t, center, amp, sigma):
        return amp * np.exp(-0.5 * ((t - center) / sigma) ** 2)

    def build_target_curve(self, t, values, CM_value=None, cm_sigma_gain=1.0):
        """
        Suma de gaussianas:
        - CM: pulso corto pre-I (si polaridad lo activa)
        - I,II,III,IV,V: picos positivos
        - VI: trough negativo despues de V
        - VII: bump tardio (suele no aparecer)
        Baseline comun ~0, no escalonamiento.
        """
        y = np.zeros_like(t)

        # CM (microfonico coclear) - pulso gaussiano corto pre-onda I
        if CM_value is not None and CM_value != 0:
            cm_lat = values.get('I', {'lat': 1.6})['lat'] / 3
            y += self._gaussian(t, cm_lat, CM_value * 0.25,
                                sigma=0.06 * cm_sigma_gain)

        # Picos positivos I-V
        for wave in ['I', 'II', 'III', 'IV', 'V']:
            if wave not in values:
                continue
            v = values[wave]
            sigma = WAVE_SIGMA[wave] * v.get('width', 1.0)
            y += self._gaussian(t, v['lat'], v['amp'], sigma=sigma)

        # Trough negativo VI (despues de V, ~SN10)
        if 'V' in values:
            v = values['V']
            amp_V = v['amp']
            sigma_V = WAVE_SIGMA['V'] * v.get('width', 1.0)
            # Latency VI ~ V + 1.0-1.5 ms (proporcional al ancho de V)
            lat_VI = v['lat'] + 0.9 + sigma_V * 2
            # Trough ~30% de V (negativo)
            y += self._gaussian(t, lat_VI, -amp_V * 0.30, sigma=sigma_V * 1.3)

        # VII: bump tardio pequeno (opcional, amp ~15% V)
        if 'V' in values:
            v = values['V']
            sigma_V = WAVE_SIGMA['V'] * v.get('width', 1.0)
            lat_VII = v['lat'] + 2.5
            y += self._gaussian(t, lat_VII, v['amp'] * 0.18, sigma=WAVE_SIGMA['VII'])

        return y

    # =====================================================================
    # ARTEFACTOS Y RUIDO
    # =====================================================================

    # =====================================================================
    # CONFIGURACION TECNICA (transductor, montaje, electrodos, rechazo)
    # =====================================================================

    def montage_factor(self, montage):
        """Factor de amplitud del montaje (Cz-mastoides = 1.0)."""
        tabla = self.norms.get('technical_factors', {}).get('electrode_montage', {})
        if montage in tabla:
            return float(tabla[montage].get('amplitude_factor', 1.0))
        return EXTRA_MONTAGE_FACTOR.get(montage, 1.0)

    def impedance_noise_factor(self, impedance):
        """Ruido segun la impedancia del PEOR electrodo.

        Hasta el limite clinico (5 kOhm) sigue la tabla del JSON
        (technical_factors.electrode_impedance: 20 nV a <=3 kOhm, 40 nV
        entre 3 y 5, 80 nV de 5 a 10), interpolada: subir de 2.9 a 3.1 no
        puede duplicar el ruido de golpe.

        Pasado el limite deja de ser una pendiente y se acelera. Antes esto
        se interpolaba tambien arriba y ADEMAS np.interp satura fuera de la
        tabla: 8, 12 y 20 kOhm daban exactamente el mismo trazo, o sea un
        electrodo despegado se veia igual que uno apenas fuera de norma, y
        cruzar los 5 kOhm no se notaba (subia 29%). Justo lo que hay que
        poder mostrarle al alumno.
        """
        tabla = self.norms.get('technical_factors', {}).get('electrode_impedance', {})
        puntos = []
        for grado in tabla.values():
            lo, hi = grado.get('range', [0, 0])
            puntos.append(((lo + hi) / 2.0, float(grado.get('noise_level', 0.04))))
        if not puntos:
            return 1.0
        puntos.sort()
        xs = [p[0] for p in puntos]
        ys = [p[1] for p in puntos]

        impedance = float(impedance)
        en_norma = min(impedance, IMPEDANCE_LIMIT_KOHM)
        nivel = float(np.interp(en_norma, xs, ys))
        referencia = float(np.interp(4.0, xs, ys)) or 0.04
        factor = nivel / referencia

        exceso = max(impedance - IMPEDANCE_LIMIT_KOHM, 0.0)
        if exceso:
            factor *= 1.0 + (exceso / IMPEDANCE_OVER_SCALE) ** IMPEDANCE_OVER_EXPONENT
        return min(factor, IMPEDANCE_MAX_FACTOR)

    @staticmethod
    def impedance_report(technical_config):
        """Chequeo de impedancias, como la pantalla previa de un equipo real.

        Devuelve (peor_kohm, desbalance_kohm, dentro_de_norma) segun los dos
        limites clinicos: cada electrodo bajo IMPEDANCE_LIMIT_KOHM y las
        diferencias entre ellos bajo IMPEDANCE_BALANCE_LIMIT_KOHM.
        """
        impedancias = technical_config.get('impedance')
        if not isinstance(impedancias, dict):
            valor = 3.0 if impedancias is None else float(impedancias)
            impedancias = {'vertex': valor, 'right': valor, 'left': valor,
                           'ground': valor}
        electrodos = technical_config.get('electrodes') or {}
        usados = [k for k in impedancias
                  if electrodos.get(k, 'A1') != DISCONNECTED]
        valores = [float(impedancias[k]) for k in usados] or [3.0]
        peor = max(valores)
        desbalance = max(valores) - min(valores)
        ok = (peor <= IMPEDANCE_LIMIT_KOHM
              and desbalance <= IMPEDANCE_BALANCE_LIMIT_KOHM)
        return peor, desbalance, ok

    @staticmethod
    def electrode_state(technical_config):
        """Que pasa con los electrodos: (hay_registro, sin_tierra, desbalance).

        - El vertex (activo) o las dos referencias desconectadas dejan el
          registro en nada: no hay diferencia de potencial que amplificar.
        - Sin tierra el amplificador no rechaza el modo comun y entra la
          red electrica.
        - El desbalance de impedancia entre activo y referencia es lo que
          convierte esa interferencia en 50 Hz visible en el trazo.
        """
        electrodos = technical_config.get('electrodes') or {}
        impedancias = technical_config.get('impedance')
        if not isinstance(impedancias, dict):
            valor = 3.0 if impedancias is None else float(impedancias)
            impedancias = {k: valor for k in ('vertex', 'right', 'left', 'ground')}

        def conectado(key):
            return electrodos.get(key, 'A1') != DISCONNECTED

        activo = conectado('vertex') if electrodos else True
        referencias = [k for k in ('right', 'left') if conectado(k)] if electrodos else ['right']
        hay_registro = activo and bool(referencias)
        sin_tierra = bool(electrodos) and not conectado('ground')

        usados = ['vertex'] + referencias if hay_registro else list(impedancias)
        valores = [float(impedancias.get(k, 3.0)) for k in usados] or [3.0]
        desbalance = max(valores) - min(valores)
        return hay_registro, sin_tierra, max(valores), desbalance

    def mains_interference(self, t, sin_tierra, desbalance, rng):
        """Zumbido de red por desbalance de electrodos o falta de tierra.

        Con los armonicos, no solo la fundamental: a 50 Hz el pasa-alto de
        100 Hz del ABR se la come entera, y en un equipo real el zumbido
        igual se ve. Lo que sobrevive al filtro son 150 y 250 Hz, y por eso
        bajar el pasa-alto (para mirar potenciales corticales, por ejemplo)
        deja el trazo inservible hasta que se arreglan los electrodos.
        """
        # Dentro de norma el CMRR hace su trabajo y queda un zumbido
        # residual que no se ve; pasado el limite se cae rapido.
        en_norma = min(desbalance, IMPEDANCE_BALANCE_LIMIT_KOHM)
        exceso = max(desbalance - IMPEDANCE_BALANCE_LIMIT_KOHM, 0.0)
        amp = en_norma * MAINS_UV_PER_KOHM_IN_SPEC + exceso * MAINS_UV_PER_KOHM_OVER
        if sin_tierra:
            amp += MAINS_NO_GROUND_UV
        if amp <= 0:
            return np.zeros_like(t)
        zumbido = np.zeros_like(t)
        for armonico, peso in ((1, 1.0), (3, 0.5), (5, 0.3)):
            fase = rng.uniform(0, 2 * np.pi)
            zumbido += peso * np.sin(
                2 * np.pi * MAINS_HZ * armonico * t / 1000.0 + fase)
        return amp * zumbido

    @staticmethod
    def artifact_acceptance(reject_uv, quality):
        """Fraccion de barridos que sobrevive al rechazo de artefacto.

        Un umbral estrecho con un paciente inquieto descarta la mitad de
        los barridos: el contador del equipo sube igual pero el promedio
        avanza mucho mas lento, que es exactamente lo que pasa en clinica.
        Con el rechazo apagado no se descarta nada, pero entra basura (ver
        NO_REJECT_NOISE_FACTOR en averaged_noise).
        """
        if not reject_uv:
            return 1.0
        return float(np.clip(float(reject_uv) / (ARTIFACT_REJECT_REF_UV * quality),
                             0.25, 1.0))

    def add_transducer_artifact(self, t, transducer='insert_earphone'):
        cfg = {
            'insert_earphone': {'dur': 0.8, 'amp': 0.05},
            'TDH39_headphone': {'dur': 1.2, 'amp': 0.12},
            'bone_vibrator':   {'dur': 1.5, 'amp': 0.20},
        }.get(transducer, {'dur': 0.8, 'amp': 0.05})
        art = np.zeros_like(t)
        mask = t < cfg['dur']
        art[mask] = cfg['amp'] * np.exp(-t[mask] * 5)
        return art

    def add_baseline_drift(self, t, rng, amplitude=0.04):
        """Drift LF suave. La frecuencia sale del rng del caso: varia entre
        capturas distintas pero se repite si el alumno reabre la app y toma
        la misma captura otra vez."""
        f1 = rng.uniform(0.4, 1.2)
        f2 = rng.uniform(0.15, 0.4)
        return amplitude * (np.sin(2 * np.pi * f1 * t / 12) +
                            0.4 * np.sin(2 * np.pi * f2 * t / 12))

    def sweep_noise(self, n, blocks, rng):
        """`blocks` realizaciones independientes de ruido de barrido (n muestras).

        Devuelve una matriz (blocks, n) de RMS 1. Pink (EEG de fondo, 1/f)
        70% + EMG (musculo, HF) 30%, igual que antes, pero generadas de una
        sola vez para poder promediarlas.
        """
        white = rng.standard_normal((blocks, n))
        fft = np.fft.rfft(white, axis=1)
        freqs = np.fft.rfftfreq(n)
        fft[:, 1:] /= np.sqrt(freqs[1:])
        fft[:, 0] = 0
        pink = np.fft.irfft(fft, n, axis=1)
        std = np.std(pink, axis=1, keepdims=True)
        pink = np.divide(pink, std, out=np.zeros_like(pink), where=std > 0)

        emg = rng.standard_normal((blocks, n))
        if n > 12:
            try:
                sos = signal.butter(4, 0.4, 'high', output='sos')
                emg = signal.sosfiltfilt(sos, emg, axis=1)
                std = np.std(emg, axis=1, keepdims=True)
                emg = np.divide(emg, std, out=np.zeros_like(emg), where=std > 0)
            except Exception:
                pass

        return 0.70 * pink + 0.30 * emg

    def averaged_noise(self, t, current_avg, target_avg, quality, rng,
                       imp_factor=1.0, noise_floor_uv=NOISE_FLOOR_UV,
                       split=False):
        """Ruido RESIDUAL de un promediado de `current_avg` barridos.

        El equipo promedia: la senial esta completa desde el primer barrido
        y lo que baja es el ruido, como 1/sqrt(N). El modelo viejo hacia lo
        contrario (escalaba la senial con `growth`) y ademas sorteaba ruido
        nuevo e independiente en cada tick, asi que el trazo parpadeaba
        entero cada 300 ms en vez de irse asentando.

        Aca el objetivo del caso se parte en NOISE_BLOCKS bloques de
        barridos; el residual es el promedio de los bloques ya acumulados.
        Eso da a la vez las dos cosas: RMS ~ 1/sqrt(N), y un trazo que
        cambia de a poco (un bloque nuevo lo mueve 1/m) porque los bloques
        anteriores son los MISMOS: cada tanda de NOISE_TANDA bloques sale
        de su propio rng sembrado con (semilla del caso, indice de tanda),
        asi que el bloque i no depende de cuantos bloques se pidieron.

        split=True devuelve ademas los dos subpromedios A (bloques pares) y
        B (impares), que es como un equipo real muestra la replicabilidad
        mientras promedia.

        quality: cuanto ruido trae ESTE paciente (1.0 = tipico). Sale de
        los puntos FSP del caso, no del FSP corriente: el FSP medido es
        consecuencia del ruido residual, usarlo para calcularlo era
        circular -- y ademas venia por tramos, asi que el ruido pegaba
        saltos de 8x al cruzar un tramo en plena captura.
        """
        n = len(t)
        m = self.noise_blocks_done(current_avg, target_avg)
        escala = self.noise_scale(quality, imp_factor, noise_floor_uv)

        # Semilla de los bloques: UN solo tiro del rng del caso, sin
        # importar cuantos bloques se pidan. Asi el bloque i es siempre el
        # mismo bloque (el trazo se asienta) y ademas lo que el rng entregue
        # despues -- el zumbido de red -- no cambia con la promediacion.
        semilla = int(rng.integers(1 << 62))

        # Se acumula por tandas: con ventanas largas (P300 son 800 ms, o
        # sea decenas de miles de muestras) una matriz m x n entera no
        # entra en memoria, y el promedio por tandas da lo mismo.
        total = np.zeros(n)
        suma_a = np.zeros(n)
        suma_b = np.zeros(n)
        n_a = n_b = 0
        hechos = 0
        while hechos < m:
            bloques = self.sweep_noise(
                n, NOISE_TANDA, np.random.default_rng([semilla, hechos // NOISE_TANDA]))
            usar = min(NOISE_TANDA, m - hechos)
            bloques = bloques[:usar]
            idx = np.arange(hechos, hechos + usar)
            total += bloques.sum(axis=0)
            pares = bloques[idx % 2 == 0]
            impares = bloques[idx % 2 == 1]
            if len(pares):
                suma_a += pares.sum(axis=0)
                n_a += len(pares)
            if len(impares):
                suma_b += impares.sum(axis=0)
                n_b += len(impares)
            hechos += usar

        residual = total / m * escala
        if not split:
            return residual
        # Subpromedios A/B: barridos pares e impares promediados en
        # paralelo. Misma senial en los dos (es el mismo paciente), la
        # mitad de barridos cada uno -> sqrt(2) mas ruido, que es lo que
        # hace que A y B se peguen recien cuando hay respuesta de verdad.
        sub_a = suma_a / max(n_a, 1) * escala
        sub_b = suma_b / max(n_b, 1) * escala if n_b else np.zeros(n)
        return residual, sub_a, sub_b

    @staticmethod
    def noise_blocks_done(current_avg, target_avg):
        """Bloques de ruido ya acumulados para `current_avg` barridos."""
        target = max(float(target_avg), 1.0)
        block = max(target / NOISE_BLOCKS, 10.0)
        m = int(np.ceil(max(float(current_avg), 1.0) / block))
        return max(min(m, NOISE_BLOCKS * 4), 1)

    @staticmethod
    def noise_scale(quality, imp_factor, noise_floor_uv=NOISE_FLOOR_UV):
        """Amplitud del ruido de UN barrido (el promedio ya divide por m).

        El promedio de m bloques YA tiene RMS 1/sqrt(m): la caida con las
        promediaciones sale de ahi. Esta constante solo fija la escala
        para que al llegar al objetivo (m = NOISE_BLOCKS) el piso quede
        en el ruido residual que declara el equipo, con paciente tipico.
        """
        amp = noise_floor_uv * np.sqrt(NOISE_BLOCKS) * quality * imp_factor
        # El techo existe para que el arranque de la promediacion no se
        # salga de la escala del grafico; NO para tapar unos electrodos
        # malos, asi que sube con ellos. Sin esto, de 6 kOhm para arriba
        # todo daba el mismo trazo y la regla de los 5 kOhm no se podia
        # mostrar.
        techo = NOISE_MAX_UV * max(imp_factor, 1.0)
        return min(amp, techo)

    # =====================================================================
    # FILTROS (limpios: solo butterworth, sin hacks)
    # =====================================================================

    def apply_filters(self, y, filter_low, filter_high, fs):
        """Butterworth pasa-bajo + pasa-alto, en secciones de segundo orden.

        fs LLEGA CALCULADA del eje temporal real (ver generate_curve): 500
        puntos en 12 ms son ~41.6 kHz, no los 20000 fijos que habia antes.
        Con ese fs equivocado todo corte quedaba 2.08x arriba del rotulo
        (pasa-alto de 100 Hz filtrando en ~208 Hz, pasa-bajo de 1500 en
        ~3120): el alumno movia los filtros y veia la mitad del efecto.

        SOS en vez de (b, a): con cortes normalizados tan chicos
        (3.3 Hz / 20.8 kHz = 1.6e-4) la forma transfer-function de orden 6
        queda mal condicionada y el filtro devuelve basura.

        Los efectos morfologicos (ensanchamiento, drift) son parte del
        modelo de ruido, no del filtro.
        """
        nyq = fs / 2
        out = y.copy()

        if 0 < filter_low < nyq:
            low_n = min(filter_low / nyq, 0.99)
            order = 4 if filter_low >= 3000 else (5 if filter_low >= 2000 else 6)
            sos = signal.butter(order, low_n, 'low', output='sos')
            out = signal.sosfiltfilt(sos, out)

        if filter_high > 0:
            high_n = min(max(filter_high / nyq, 1e-5), 0.99)
            order = 6 if filter_high >= 150 else (5 if filter_high >= 50 else 4)
            sos = signal.butter(order, high_n, 'high', output='sos')
            out = signal.sosfiltfilt(sos, out)

        return out

    # =====================================================================
    # FSP / TRANSICION
    # =====================================================================

    def calculate_fsp(self, prom_actual, fsp_800, fsp_2000):
        if prom_actual <= 0:
            return 0.5
        if prom_actual < 800:
            return 0.5 + (fsp_800 - 0.5) * prom_actual / 800
        if prom_actual <= 2000:
            return fsp_800 + (fsp_2000 - fsp_800) * (prom_actual - 800) / 1200
        return fsp_2000

    @staticmethod
    def replicability(sub_a, sub_b):
        """Indice de replicabilidad entre los dos subpromedios (0-1).

        Correlacion cruzada de A contra B. Con puro ruido los dos
        subpromedios son independientes y da ~0; a medida que la respuesta
        emerge por debajo del ruido, la parte comun crece y el indice sube
        solo como 1/sqrt(N). Un paciente "no reproducible" nunca los pega:
        la respuesta esta, pero llega con un timing distinto cada vez.

        Se recorta en 0: una correlacion negativa entre subpromedios no es
        "menos que nada", es ruido igual.
        """
        a = np.asarray(sub_a, dtype=float)
        b = np.asarray(sub_b, dtype=float)
        if a.size < 2 or b.size < 2:
            return 0.0
        a = a - a.mean()
        b = b - b.mean()
        denom = np.sqrt(float(a @ a) * float(b @ b))
        if denom <= 0:
            return 0.0
        return float(max(0.0, (a @ b) / denom))

    def calculate_growth(self, current_avg, target_avg):
        """
        Growth factor 0..1 que escala la amplitud visible del target
        a medida que promedian mas muestras.
        """
        if target_avg <= 0:
            return 0.0
        ratio = current_avg / target_avg
        return max(0.0, min(1.0, ratio))

    # =====================================================================
    # ORQUESTADOR
    # =====================================================================

    def shadow_values(self, population, pathway, stimulus_config, masking, ia,
                      case_config, click_baseline=None, ratio_override=None):
        """Respuesta de la coclea del oido NO evaluado, o None si no cruza.

        Al otro oido le llega el estimulo atenuado por el craneo
        (INTERAURAL_ATTENUATION). Si eso queda sobre su umbral, responde y
        el registro lo recoge: la curva sombra. El enmascaramiento que se
        pone en ese oido le sube el umbral, asi que con suficiente masking
        la sombra desaparece.

        Se ve como una respuesta de baja intensidad (latencia larga,
        amplitud chica) porque, para esa coclea, ES de baja intensidad --
        no hay que forzar nada aparte del montaje (SHADOW_*).
        """
        contra = (case_config or {}).get('contra')
        if not contra:
            return None
        # ia = 0 es el vibrador oseo: no hay atenuacion que cruzar, las dos
        # cocleas reciben lo mismo y la sombra sale siempre que no este
        # enmascarada. Por eso no se corta aca.

        level = stimulus_config['int'] - ia
        threshold = max(float(contra.get('umbral', 20)), float(masking))
        if level <= threshold:
            return None

        baseline = self.get_baseline_values(
            population, stimulus_config['stim'], pathway,
            freq=stimulus_config.get('freq'), ratio_override=ratio_override,
        )
        values, _ = self.calculate_wave_parameters(
            baseline, level, threshold, contra.get('type', 'normal'),
            desviaciones=contra.get('desviaciones'),
            click_baseline=click_baseline,
            neural=contra.get('neural'),
        )
        for wave, v in values.items():
            factor = SHADOW_AMP_FACTOR
            if wave == 'I':
                # La onda I es generada por el nervio del lado estimulado;
                # con el montaje puesto en el otro oido practicamente no
                # aparece, y esa es la pista de que la curva es sombra.
                factor *= SHADOW_WAVE_I_FACTOR
            v['amp'] *= factor
        return values

    @staticmethod
    def _shift_latencies(values, dt):
        """Las mismas ondas corridas dt ms (sin tocar el dict original)."""
        if not dt:
            return values
        return {w: dict(v, lat=v['lat'] + dt) for w, v in values.items()}

    @staticmethod
    def contra_values(values):
        """Las mismas ondas vistas desde el mastoides del oido NO estimulado.

        No es una respuesta distinta: es el mismo generador proyectado sobre
        otro vector de registro. La onda I se pierde (nervio distal, pegado
        al electrodo ipsi), III-V se conservan y el complejo IV-V se abre.
        Ver CONTRA_*.
        """
        contra = {}
        for wave, v in values.items():
            nuevo = dict(v)
            nuevo['amp'] = v['amp'] * CONTRA_AMP_FACTOR.get(wave, 0.8)
            nuevo['lat'] = v['lat'] + CONTRA_LAT_SHIFT.get(wave, 0.0)
            nuevo['width'] = v.get('width', 1.0) * CONTRA_WIDTH_FACTOR
            contra[wave] = nuevo
        return contra

    @staticmethod
    def contra_channel(technical_config, side):
        """Clave del electrodo de referencia contralateral, o None.

        El canal contra existe solo si ese electrodo esta puesto: si el
        alumno desconecta A1 y estimula el oido derecho, se queda sin canal
        contralateral, igual que en el equipo.
        """
        ipsi = 'right' if side == 'OD' else 'left'
        otro = 'left' if ipsi == 'right' else 'right'
        electrodos = technical_config.get('electrodes') or {}
        if electrodos.get(otro, 'A1') == DISCONNECTED:
            return None
        if electrodos.get('vertex', 'Cz') == DISCONNECTED:
            return None
        return otro

    def raw_eeg(self, technical_config, quality=1.0, seed=0, tick=0,
                duration_ms=300.0, fs=EEG_DISPLAY_FS):
        """Trozo de EEG CRUDO por canal (R/L), en uV, sin promediar.

        Es el monitor previo del equipo: lo que el alumno tiene que mirar
        ANTES de apretar promediar. Ahi se ve de una si el paciente esta
        tenso (EMG), si falta la tierra o si los electrodos quedaron
        desbalanceados (50 Hz), sin tener que gastar 2000 barridos para
        enterarse.

        Devuelve {'R': array|None, 'L': array|None, 'rejected_R': bool,
        'rejected_L': bool, 'rms_R': float, 'rms_L': float}. Canal en None =
        electrodo desconectado, no hay registro de ese lado.
        """
        n = max(int(round(duration_ms * fs / 1000.0)), 8)
        t = np.linspace(0, duration_ms, n)
        impedancias = technical_config.get('impedance')
        if not isinstance(impedancias, dict):
            valor = 3.0 if impedancias is None else float(impedancias)
            impedancias = {k: valor for k in ('vertex', 'right', 'left', 'ground')}
        electrodos = technical_config.get('electrodes') or {}

        def conectado(key):
            return electrodos.get(key, 'A1') != DISCONNECTED

        sin_tierra = not conectado('ground')
        reject = float(technical_config.get('artifact_reject_uv') or 0.0)
        salida = {}
        for canal, key in (('R', 'right'), ('L', 'left')):
            if not conectado('vertex') or not conectado(key):
                salida[canal] = None
                salida[f'rejected_{canal}'] = False
                salida[f'rms_{canal}'] = 0.0
                continue
            # Cada canal se lee entre el activo y SU referencia: la
            # impedancia que manda es la peor de las dos, y el desbalance
            # (lo que rompe el CMRR) es la diferencia entre ellas.
            imp = [float(impedancias.get('vertex', 3.0)), float(impedancias.get(key, 3.0))]
            # Relativo al equipo bien puesto (IMPEDANCE_REF_KOHM): a 2 kOhm
            # el EEG queda en su amplitud fisiologica y de ahi para arriba
            # crece. impedance_noise_factor esta normalizado contra 4 kOhm
            # (le sirve al promediador), aca hace falta contra el default.
            imp_factor = (self.impedance_noise_factor(max(imp))
                          / self.impedance_noise_factor(IMPEDANCE_REF_KOHM))
            desbalance = abs(imp[0] - imp[1])
            # rng propio del canal y del tick: el trazo corre, no se repite.
            rng = np.random.default_rng([int(seed) & ((1 << 62) - 1),
                                         int(tick), 0 if canal == 'R' else 1])
            amp = (EEG_BASELINE_UV + EEG_TENSION_UV * max(quality - 1.0, 0.0)) * imp_factor
            crudo = self.sweep_noise(n, 1, rng)[0]
            desvio = float(np.std(crudo)) or 1.0
            trazo = crudo / desvio * amp
            trazo = trazo + MAINS_RAW_GAIN * self.mains_interference(
                t, sin_tierra, desbalance, rng)
            salida[canal] = trazo
            salida[f'rms_{canal}'] = float(np.std(trazo))
            # El rechazo de artefacto no mira el EEG crudo: mira el canal
            # ya filtrado en la banda del ABR. Sobre el crudo, un EEG normal
            # de 12 uV RMS cruzaria los +-25 uV en casi todos los barridos y
            # el equipo no promediaria nunca. Lo que queda arriba de 30 Hz
            # es el EMG y el zumbido de red -- justo lo que se descarta.
            banda = self.apply_filters(trazo, 0.0, 30.0, fs)
            salida[f'rejected_{canal}'] = bool(reject and np.abs(banda).max() > reject)
        return salida

    def normative_limits(self, population='adult_female', intensity=80,
                         stimulus='click', pathway='air_conduction', freq=None):
        """Rangos de normalidad para leer la tabla del alumno.

        Latencias absolutas: valor poblacional corrido por la MISMA funcion
        latencia-intensidad que usa el generador (una V de 6.4 ms a 40 dB no
        es tardia, a 80 si), +- NORM_SD_LIMIT desviaciones.
        Interpicos y razon V/I no dependen de la intensidad.
        """
        baseline = self.get_baseline_values(population, stimulus, pathway, freq=freq)
        lat_shift = self.latency_intensity_shift(intensity)
        latencias = {}
        for wave, sd in NORM_LAT_SD.items():
            if wave not in baseline:
                continue
            centro = baseline[wave]['lat'] + lat_shift * LAT_SHIFT_FACTOR.get(wave, 1.0)
            margen = sd * NORM_SD_LIMIT
            latencias[wave] = (centro - margen, centro + margen)

        interpicos = {}
        norm_ip = baseline.get('interpeak') or {}
        for clave, sd in NORM_INTERPEAK_SD.items():
            a, b = clave.split('-')
            if clave in norm_ip:
                centro = float(norm_ip[clave])
            elif a in baseline and b in baseline:
                centro = baseline[b]['lat'] - baseline[a]['lat']
            else:
                continue
            margen = sd * NORM_SD_LIMIT
            interpicos[clave] = (centro - margen, centro + margen)

        return {
            'population': population,
            'intensity': intensity,
            'lat': latencias,
            'interpeak': interpicos,
            'v_i_ratio': (NORM_VI_RATIO_MIN, None),
            'interaural_v': NORM_INTERAURAL_MAX,
        }

    @staticmethod
    def latency_intensity_shift(intensity):
        """Corrimiento de la funcion latencia-intensidad (ms) respecto de 80 dB.

        Pendiente (onda V, click): ~0.12 ms/10 dB cerca del techo (por
        encima de 70 dB, casi plana) y ~0.3 ms/10 dB de ahi para abajo --
        Hood, "Clinical Applications of the ABR", reporta ~0.3 ms/10 dB
        entre 70 y 50 dB. Quiebre en 70 (antes estaba en 60, dejaba el
        tramo 70-60 con la pendiente plana que no corresponde). El tramo
        alto estaba en 0.08: de 80 a 100 dB la V se movia 0.16 ms, menos
        que el error de lectura del alumno.

        Es la funcion del oido NORMAL. La perdida coclear la empina cerca
        del umbral (COCHLEAR_LI_SLOPE) y la conductiva la corre en paralelo
        (el GAP entra como intensidad efectiva), las dos en
        calculate_wave_parameters.

        Vive en un solo lugar porque la usan las dos puntas: el generador
        para dibujar la curva y la banda normativa para juzgarla. Si se
        separan, el alumno queda fuera de norma por un error de la app.
        """
        if intensity >= 70:
            return (80 - intensity) / 10 * 0.12
        return (80 - 70) / 10 * 0.12 + (70 - intensity) / 10 * 0.3

    def latency_intensity_band(self, population='adult_female', wave='V',
                               intensities=None, stimulus='click',
                               pathway='air_conduction', freq=None):
        """Banda normativa del grafico latencia-intensidad, por poblacion.

        Fija no sirve: la V de un neonato corre ~1 ms mas tarde que la de un
        adulto, asi que con una banda de adulto TODO neonato queda fuera de
        norma y el grafico deja de decir nada.
        """
        if intensities is None:
            intensities = list(range(0, 110, 10))
        xs, lo, hi = [], [], []
        for intensidad in intensities:
            limites = self.normative_limits(population, intensidad, stimulus,
                                            pathway, freq)
            rango = limites['lat'].get(wave)
            if rango is None:
                continue
            xs.append(intensidad)
            lo.append(rango[0])
            hi.append(rango[1])
        return xs, lo, hi

    def generate_curve(self, population, pathology, stimulus_config,
                        technical_config, case_config=None):
        # 1. Baseline normativo. El vibrador oseo no es "otro transductor
        # de aire": estimula la coclea directo y tiene su propio bloque
        # normativo (bone_conduction), asi que la via la manda el equipo.
        transducer = technical_config.get('transducer', 'insert_earphone')
        pathway = ('air_conduction' if 'pathway' not in stimulus_config
                   else stimulus_config['pathway'])
        if transducer == 'bone_vibrator':
            pathway = 'bone_conduction'
        # Ratio de desviacion por curso (ver core.app_config_store en el
        # cliente / AppConfig.php en el backend) -- afecta solo como se
        # desvian chirp/burst respecto al click, nunca el click en si
        # (eso lo define el caso/paciente via 'desviaciones', mas abajo).
        ratio_override = case_config.get('ratio_override') if case_config else None
        baseline = self.get_baseline_values(
            population, stimulus_config['stim'], pathway,
            freq=stimulus_config.get('freq'), ratio_override=ratio_override,
        )
        # Baseline de click (misma poblacion/via, sin override) para escalar
        # desviaciones cuando el estimulo activo no es click (ver
        # calculate_wave_parameters).
        click_baseline = None
        if stimulus_config['stim'] != 'click':
            click_baseline = self.get_baseline_values(population, 'click', pathway)

        # 2. Umbral del oido evaluado. El enmascaramiento que se le pone al
        # OTRO oido tambien cruza el craneo de vuelta: si lo que llega
        # (mkg - IA) supera el umbral de este oido, lo esta enmascarando a
        # el -- sobreenmascaramiento, y la respuesta se degrada. Sale gratis
        # subiendo el umbral efectivo, porque la amplitud ya va por nivel
        # de sensacion.
        if case_config and 'umbral' in case_config:
            threshold = case_config['umbral']
        else:
            threshold = self.norms['pathology_modifiers'][pathology]['threshold_range'][0]

        masking = float((case_config or {}).get('masking') or 0.0)
        ia = INTERAURAL_ATTENUATION.get(transducer, 65.0)
        if masking > 0:
            threshold = max(threshold, masking - ia)

        # 3. Desviaciones (el caso trae un solo set, plano por onda -- no
        # esta anidado por estimulo, ver CaseBuilder.abrBuild en case_create.php).
        # Se escalan por estimulo en calculate_wave_parameters via click_baseline.
        desviaciones = case_config.get('desviaciones') if case_config else None

        # 4. FSP del caso
        if case_config and 'fsp_puntos' in case_config:
            fsp_800 = case_config['fsp_puntos']['800']
            fsp_2000 = case_config['fsp_puntos']['2000']
        else:
            fsp_800, fsp_2000 = 2.3, 2.8

        # 5. FSP actual
        current_avg = stimulus_config['current_avg']
        target_avg = stimulus_config['average']
        fsp_actual = self.calculate_fsp(current_avg, fsp_800, fsp_2000)

        # 5b. rng propio de ESTA captura: mismo paciente, mismo oido, mismos
        # parametros y misma curva -> mismo ruido, aunque se cierre y se
        # vuelva a abrir LabSim (stable_seed usa blake2b, no hash(), ver
        # core.rng). Capturas distintas del mismo caso siguen saliendo
        # distintas porque el id de curva entra en la semilla.
        rng = np.random.default_rng(stable_seed(
            (case_config or {}).get('seed_key', ''),
            (case_config or {}).get('capture_id', ''),
            population, pathology,
            # El patron retrococlear cambia la respuesta, asi que entra en la
            # semilla -- pero solo cuando aplica: si entrara siempre,
            # cambiaria el ruido de todos los casos no neurales.
            (repr(sorted(self.neural_params(
                (case_config or {}).get('neural')).items()))
             if pathology == 'neural' else ''), pathway,
            stimulus_config['stim'], stimulus_config.get('freq'),
            stimulus_config['int'], stimulus_config['pol'],
            stimulus_config['rate'], stimulus_config['filter_down'],
            stimulus_config['filter_passhigh'],
        ))

        # 6. Parametros de ondas. El patron retrococlear no es un enum sino
        # un juego de parametros (I-III, III-V, bloqueo, razon V/I,
        # microfonica, desincronia, tasa) -- ver NEURAL_PARAM_DEFAULTS.
        repro_shift = case_config.get('repro_shift', 0.0) if case_config else 0.0
        neural = (case_config or {}).get('neural')
        values, waves_visible = self.calculate_wave_parameters(
            baseline, stimulus_config['int'], threshold, pathology, desviaciones,
            repro_shift=repro_shift, click_baseline=click_baseline,
            neural=neural,
        )

        # 7. Polaridad + rate
        values, CM_value = self.apply_polarity_effects(
            values, stimulus_config['pol'], pathology, neural)
        values = self.apply_rate_effects(values, stimulus_config['rate'],
                                         pathology, neural)
        # El microfonico de una desincronia dura lo que dura el estimulo, no
        # es el pulso corto pre-onda I del oido sano.
        cm_sigma_gain = (
            NEURAL_CM_SIGMA_GAIN
            if pathology == 'neural'
            and self.neural_params(neural)['microfonica'] == 'amplificada'
            else 1.0)

        # 7b. Ajustes del equipo sobre las ondas: retardo del transductor y
        # montaje de electrodos. Van despues de polaridad/tasa porque son
        # del registro, no del paciente.
        lat_offset = TRANSDUCER_LATENCY_MS.get(transducer, 0.0)
        montage_gain = self.montage_factor(
            technical_config.get('montage', 'vertex_mastoid'))
        if lat_offset or montage_gain != 1.0:
            for v in values.values():
                v['lat'] += lat_offset
                v['amp'] *= montage_gain

        # 8. Eje temporal. La ventana la fija el protocolo (12 ms en ABR,
        # 5 en ECochG, cientos en los corticales -- ver abr/protocols.py) y
        # las muestras por ms se mantienen para que fs no dependa de eso:
        # ~41.6 kHz, dentro del rango real de un equipo (20-50 kHz).
        window_ms = float(technical_config.get('window_ms') or 12)
        n_samples = max(int(round(window_ms * SAMPLES_PER_MS)), 64)
        t = np.linspace(0, window_ms, n_samples)
        fs = (len(t) - 1) / (t[-1] / 1000.0)

        # 9. Curva objetivo (gaussianas). Un paciente "no reproducible" no
        # responde con un timing distinto de una captura a otra nomas:
        # tampoco lo mantiene DENTRO de una captura, y por eso sus dos
        # subpromedios no se pegan nunca por mucho que promedie. El jitter
        # se reparte entre las dos mitades (+/- la mitad cada una) y el
        # promedio total sigue siendo el punto medio.
        jitter = float((case_config or {}).get('repro_jitter') or 0.0)
        values_a = self._shift_latencies(values, jitter / 2)
        values_b = self._shift_latencies(values, -jitter / 2)
        y_target_a = self.build_target_curve(t, values_a, CM_value,
                                             cm_sigma_gain)
        y_target_b = (y_target_a if not jitter
                      else self.build_target_curve(t, values_b, CM_value,
                                                   cm_sigma_gain))
        y_target = (y_target_a + y_target_b) / 2

        # 9b. Curva sombra: si el estimulo cruza el craneo por encima de la
        # atenuacion interaural, la coclea del oido NO evaluado tambien
        # responde y el electrodo la registra igual. Con enmascaramiento
        # suficiente en ese oido desaparece, que es exactamente el ejercicio
        # (estimular fuerte un oido muerto y ver "respuesta" hasta que se
        # enmascara). Antes el spinbox de masking se leia y se tiraba.
        shadow = self.shadow_values(
            population, pathway, stimulus_config, masking, ia, case_config,
            click_baseline=click_baseline, ratio_override=ratio_override,
        )
        if shadow:
            contra_case = (case_config or {}).get('contra') or {}
            shadow_values, shadow_cm = self.apply_polarity_effects(
                shadow, stimulus_config['pol'],
                contra_case.get('type', 'normal'),
                contra_case.get('neural'))
            shadow_values = self.apply_rate_effects(
                shadow_values, stimulus_config['rate'],
                contra_case.get('type', 'normal'),
                contra_case.get('neural'))
            for v in shadow_values.values():
                v['lat'] += lat_offset
                v['amp'] *= montage_gain
            y_shadow = self.build_target_curve(t, shadow_values, shadow_cm)
            y_target = y_target + y_shadow
            y_target_a = y_target_a + y_shadow
            y_target_b = y_target_b + y_shadow

        # 10. Drift LF + artefacto transductor
        y_drift = self.add_baseline_drift(t, rng)
        y_artifact = self.add_transducer_artifact(t, transducer)

        # 11. Curva limpia (sin ruido). La senial NO se escala por cuanto
        # se lleva promediado: en un equipo real esta completa desde el
        # primer barrido y lo que baja es el ruido (ver averaged_noise).
        y_clean = y_target + y_drift + y_artifact
        y_clean_a = y_target_a + y_drift + y_artifact
        y_clean_b = y_target_b + y_drift + y_artifact

        # 12. Ruido residual del promediado. El denominador es lo que el
        # CASO necesita (average_objetivo), no lo que el alumno pidio en el
        # equipo: si detiene antes, la curva queda enterrada en ruido
        # aunque el equipo diga "listo".
        growth_target = target_avg
        if case_config and case_config.get('average_objetivo'):
            growth_target = case_config['average_objetivo']
        growth = self.calculate_growth(current_avg, growth_target)
        # Calidad de registro del paciente: un caso con FSP objetivo bajo
        # es un paciente ruidoso (se mueve, tensa el cuello) y su curva
        # tarda mas en limpiarse.
        quality = float(np.clip(2.8 / max(fsp_2000, 0.5), 0.5, 2.5))

        # Estado de los electrodos y rechazo de artefacto: es la parte que
        # el alumno controla desde Parametros Avanzados.
        hay_registro, sin_tierra, imp_max, desbalance = self.electrode_state(
            technical_config)
        acceptance = self.artifact_acceptance(
            technical_config.get('artifact_reject_uv'), quality)
        noise_floor = float(technical_config.get('residual_noise_nv') or
                            NOISE_FLOOR_UV * 1000) / 1000.0
        imp_factor = self.impedance_noise_factor(imp_max)
        if not technical_config.get('artifact_reject_uv'):
            imp_factor *= NO_REJECT_NOISE_FACTOR

        # Barridos que realmente entraron al promedio: el equipo cuenta los
        # presentados, no los aceptados.
        accepted = current_avg * acceptance

        if not hay_registro:
            # Sin electrodo activo o sin ninguna referencia no hay nada que
            # amplificar: queda el ruido del amplificador al aire, sin
            # respuesta ninguna por mas que se promedie.
            y_clean = np.zeros_like(t)
            y_clean_a = np.zeros_like(t)
            y_clean_b = np.zeros_like(t)
            accepted = 1.0

        ruido, ruido_a, ruido_b = self.averaged_noise(
            t, accepted, growth_target, quality, rng, imp_factor, noise_floor,
            split=True,
        )
        red = self.mains_interference(t, sin_tierra, desbalance, rng)
        y_noisy = y_clean + ruido + red

        # 13. Canal contralateral: el mismo estimulo, el mismo paciente,
        # leido entre el vertex y el mastoides del oido NO estimulado.
        # Comparte el ruido del promediado (es el mismo amplificador y el
        # mismo momento) pero la respuesta llega proyectada distinto.
        contra_key = self.contra_channel(technical_config,
                                         stimulus_config.get('side', 'OD'))
        y_contra = None
        if contra_key and hay_registro:
            y_contra_clean = (self.build_target_curve(
                t, self.contra_values(values), CM_value)
                + y_drift + y_artifact)
            if shadow:
                # La sombra viene de la coclea del otro oido: en el canal
                # contralateral queda MAS cerca del electrodo, no menos.
                y_contra_clean = y_contra_clean + self.build_target_curve(
                    t, shadow_values, shadow_cm)
            y_contra = self.apply_filters(
                y_contra_clean + ruido_b + red,
                float(stimulus_config['filter_down']),
                float(stimulus_config['filter_passhigh']),
                fs,
            )

        # 14. Filtros al final (como equipos reales)
        y_final = self.apply_filters(
            y_noisy,
            float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']),
            fs,
        )
        # Subpromedios A/B: mismos filtros, misma senial, distinta mitad de
        # los barridos. Es la replicabilidad EN VIVO -- el criterio con el
        # que se decide si una onda es respuesta o es ruido, sin tener que
        # repetir la captura entera.
        sub_a = self.apply_filters(
            y_clean_a + ruido_a + red, float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']), fs)
        sub_b = self.apply_filters(
            y_clean_b + ruido_b + red, float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']), fs)
        repro_index = self.replicability(sub_a, sub_b)

        # Ruido residual REAL de este registro (nV RMS), que es lo que el
        # equipo muestra al lado del FSP: la diferencia entre los dos
        # subpromedios es ruido y nada mas (la senial se cancela), asi que
        # sale de ahi sin tener que separar senial de ruido a mano.
        residual_nv = float(np.std(sub_a - sub_b) / 2.0 * 1000.0)

        # El FSP del caso esta medido con el equipo bien puesto. Con los
        # electrodos malos el ruido sube y el FSP CAE solo (es una razon de
        # varianzas): si no, se podia registrar con 15 kOhm y el equipo
        # igual declaraba "respuesta presente".
        escala_ref = self.noise_scale(
            quality, self.impedance_noise_factor(IMPEDANCE_REF_KOHM), noise_floor)
        ruido_ref = escala_ref / max(np.sqrt(self.noise_blocks_done(
            accepted, growth_target)), 1.0)
        degradacion = max(np.sqrt((float(np.std(ruido)) ** 2
                                   + float(np.std(red)) ** 2)) / max(ruido_ref, 1e-9), 1.0)
        # Piso en 1.0: el FSP es una razon de varianzas (senial+ruido
        # sobre ruido), no puede dar menos que 1 -- por debajo de eso
        # simplemente no hay nada que detectar.
        fsp_actual = max(1.0, 1.0 + (fsp_actual - 1.0) / degradacion ** 2)

        return t, y_final, {
            'population': population,
            'pathology': pathology,
            'waves_visible': waves_visible,
            'current_avg': current_avg,
            'target_avg': target_avg,
            'fsp': fsp_actual,
            'growth': growth,
            'threshold': threshold,
            'masking': masking,
            'shadow': bool(shadow),
            'window_ms': window_ms,
            'transducer': transducer,
            'pathway': pathway,
            'accepted_sweeps': accepted,
            'rejected_sweeps': max(current_avg - accepted, 0.0),
            'artifact_acceptance': acceptance,
            # Trazos extra del mismo registro: los dos subpromedios (A/B) y
            # el canal contralateral. Van en la metadata y no en el retorno
            # para no romper a quien solo quiere (t, y).
            'sub_a': sub_a,
            'sub_b': sub_b,
            'repro_index': repro_index,
            'contra': y_contra,
            'contra_channel': contra_key,
            'residual_noise_nv': residual_nv,
            'recording': hay_registro,
            'mains': bool(sin_tierra or desbalance > IMPEDANCE_BALANCE_LIMIT_KOHM),
            'impedance_max': imp_max,
            'impedance_imbalance': desbalance,
            'impedance_ok': (imp_max <= IMPEDANCE_LIMIT_KOHM
                             and desbalance <= IMPEDANCE_BALANCE_LIMIT_KOHM),
            # Criterio de deteccion configurado en Parametros Avanzados: el
            # equipo declara "respuesta presente" cuando el FSP lo supera.
            'fsp_criterion': technical_config.get('fsp_criterion'),
            'fsp_pass': (fsp_actual >= technical_config['fsp_criterion']
                         if technical_config.get('fsp_criterion') else None),
        }


# ============================================================================
# Interfaz publica: la usa AbrMainWindow
# ============================================================================

_generator = None


def default_settings(test='ABR'):
    """Equipo de rutina del protocolo, sin depender de Qt.

    AbrAdvanceSettings.default_settings vive en el modulo del dialogo (que
    importa PySide6); el generador no puede depender de la UI, asi que la
    tabla base sale de abr.protocols y se arma aca.
    """
    protocol = get_protocol(test)
    return {
        'transducer': 'insert_earphone',
        'window_ms': protocol.window_ms,
        'montage': protocol.montage,
        'electrodes': {'vertex': 'Cz', 'right': 'A2', 'left': 'A1', 'ground': 'Fpz'},
        'impedance': {'vertex': 2.0, 'right': 2.0, 'left': 2.0, 'ground': 2.0},
        'artifact_reject_uv': 25.0,
        'residual_noise_nv': 40.0,
        'fsp_criterion': 3.1,
    }


def _get_generator():
    global _generator
    if _generator is None:
        _generator = ABRGenerator()
    return _generator


# Texto del combo cb_stim (AbrConfig_ui.py) -> (clave en normative_data.json, freq)
STIM_MAP = {
    'Click':       ('click', None),
    'Ls-chirp':    ('ls_chirp', None),
    'Chirp':       ('ce_chirp', None),
    'Burst 500Hz': ('tone_burst', '500Hz'),
    'Burst 1kHz':  ('tone_burst', '1000Hz'),
    'Burst 2kHz':  ('tone_burst', '2000Hz'),
    'Burst 4kHz':  ('tone_burst', '4000Hz'),
}


# Tipo de patologia del caso (como lo guarda CaseBuilder.abrBuild) ->
# clave de normative_data.json.
PATHOLOGY_MAP = {
    'normal': 'normal',
    'coclear': 'cochlear',
    'transmission': 'conductive',
    'neural': 'neural',
}


def ABR_Curve(actual_intencity, control_setting, preferences, repro_prev, prom,
              done, patient=None, contra=None, capture_id="", technical=None):
    """
    Genera curva ABR con modelo morfolgico realista.

    patient: dict del paciente en atencion (cases.data) -- de ahi salen
        'edad' y 'gender' para elegir la poblacion normativa. Sin esto se
        usa adult_female, que es lo que el modulo asumia siempre.
    contra: perfil ABR del oido NO evaluado (cases.data['ABR'][otro lado]),
        para la curva sombra cuando el estimulo cruza el craneo.
    capture_id: nombre de la curva ("R1", "L2"...). Entra en la semilla del
        ruido: la misma curva se redibuja igual entre aperturas de la app,
        pero dos capturas de la misma intensidad salen distintas.
    technical: configuracion del equipo (transductor, ventana, montaje,
        electrodos e impedancias, rechazo de artefacto, ruido residual y
        criterio FSP), tal como la entrega AbrAdvanceSettings.get_data().
        Sin esto se usa el equipo de rutina del protocolo.

    Devuelve (t, y_ipsi, t_contra, y_contra, var_repro, metadata). El canal
    contralateral es None si ese electrodo esta desconectado. La metadata
    trae lo que el equipo muestra durante la captura y antes no salia de
    aca: barridos aceptados/rechazados, FSP, ruido residual, subpromedios
    A/B e indice de replicabilidad.
    """
    generator = _get_generator()

    pathology = PATHOLOGY_MAP.get(preferences.get('type', 'normal'), 'normal')

    if done and prom[0] == 0:
        current_averages = prom[1]
    elif prom[0] <= 1.0:
        current_averages = prom[0] * prom[1]
    else:
        current_averages = prom[0] * 2.5

    target_averages = prom[1]
    if current_averages >= target_averages:
        current_averages = target_averages

    stim_key, stim_freq = STIM_MAP.get(control_setting['stim'], ('click', None))

    stimulus_config = {
        'stim': stim_key,
        'freq': stim_freq,
        'pol': control_setting['pol'],
        'int': actual_intencity,
        'rate': control_setting['rate'],
        'filter_down': float(control_setting['filter_down']),
        'filter_passhigh': float(control_setting['filter_passhigh']),
        'average': target_averages,
        'current_avg': current_averages,
        'pathway': 'air_conduction',
        # Lado estimulado: decide cual referencia es la ipsi y cual la
        # contra (ver ABRGenerator.contra_channel).
        'side': control_setting.get('side', 'OD'),
    }

    # Equipo: lo que el alumno dejo en Parametros Avanzados. El fallback es
    # el montaje de rutina del protocolo (ver abr.protocols), no un dict
    # fijo -- cuando cuelguen los otros potenciales de esta ventana, cada
    # uno trae su ventana de registro y su montaje.
    technical_config = default_settings(control_setting.get('test', 'ABR'))
    if technical:
        technical_config.update(technical)

    # Oido no evaluado: umbral y patologia propios, para decidir si aparece
    # curva sombra al pasar la atenuacion interaural (ver shadow_values).
    contra_config = None
    if contra:
        contra_config = {
            'umbral': contra.get('umbral', contra.get('th', 20)),
            'type': PATHOLOGY_MAP.get(contra.get('type', 'normal'), 'normal'),
            'neural': contra.get('neural'),
            'desviaciones': contra.get('desviaciones', {}),
        }

    # Reproducibilidad: si el caso es "no reproducible", cada captura a la
    # misma intensidad corre el complejo I-V un poco (jitter), en vez de
    # calcular un numero que despues no se usaba en la curva.
    repro_var = preferences.get('repro_var', 0.2)
    if not preferences.get('repro', True):
        var_repro = random.uniform(-repro_var, repro_var) if repro_prev == 0 \
                    else -repro_prev + random.uniform(-repro_var / 2, repro_var / 2)
    else:
        var_repro = 0

    # Ratio de desviacion de chirp/burst por curso -- config del docente
    # (ver AppConfig.php), sincronizada al cliente en core.app_config_store
    # bajo key generica "normative_data.<examen>" (mismo mecanismo para
    # P300/electrococleografia a futuro). Nunca toca click -- eso lo define
    # el caso via 'desviaciones', abajo.
    ratio_override = app_config_store.get('normative_data.abr')

    case_config = {
        'desviaciones': preferences.get('desviaciones', {}),
        'fsp_puntos': preferences.get('fsp_puntos', {'800': 2.3, '2000': 2.8}),
        'umbral': preferences.get('umbral', preferences.get('th', 20)),
        'average_objetivo': preferences.get('average_objetivo', 2000),
        'repro_shift': var_repro,
        # Jitter DENTRO de la captura: lo que hace que los subpromedios A/B
        # de un paciente no reproducible no lleguen a pegarse nunca.
        'repro_jitter': 0.0 if preferences.get('repro', True) else repro_var,
        'ratio_override': ratio_override,
        # Patron retrococlear del caso (I-III, III-V, bloqueo, razon V/I,
        # microfonica, desincronia, tasa). Los casos guardados antes de que
        # existiera no lo traen y caen en NEURAL_PARAM_DEFAULTS, que es como
        # se dibujaban.
        'neural': preferences.get('neural'),
        'masking': control_setting.get('mkg', 0),
        'contra': contra_config,
        # Semilla estable del ruido: identifica el perfil del oido, no la
        # corrida. Ver core.rng.stable_seed.
        'seed_key': case_fingerprint(preferences),
        'capture_id': capture_id,
    }

    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'))

    t, y, metadata = generator.generate_curve(
        population=population,
        pathology=pathology,
        stimulus_config=stimulus_config,
        technical_config=technical_config,
        case_config=case_config,
    )

    # Canal contralateral: si el electrodo del otro mastoides esta puesto,
    # el generador entrega su propio trazo (antes esto era una copia exacta
    # del ipsi, que ademas nadie dibujaba). Sin ese electrodo no hay canal.
    dy = metadata.get('contra')
    dx = t.copy() if dy is not None else None
    return t, y, dx, dy, var_repro, metadata


# ----------------------------------------------------------------------
# Helpers que consume la UI (monitor de EEG, banda normativa, tabla)
# ----------------------------------------------------------------------

def case_quality(preferences):
    """Cuanto ruido trae ESTE paciente (1.0 = tipico).

    Misma cuenta que generate_curve: sale de los puntos FSP del caso, que
    es donde el caso declara "este paciente es ruidoso".
    """
    puntos = (preferences or {}).get('fsp_puntos') or {}
    fsp_2000 = float(puntos.get('2000', 2.8) or 2.8)
    return float(np.clip(2.8 / max(fsp_2000, 0.5), 0.5, 2.5))


def raw_eeg(technical=None, quality=1.0, seed=0, tick=0, duration_ms=300.0,
            test='ABR'):
    """Trozo de EEG crudo por canal para el monitor (ver ABRGenerator.raw_eeg)."""
    technical_config = default_settings(test)
    if technical:
        technical_config.update(technical)
    return _get_generator().raw_eeg(technical_config, quality=quality, seed=seed,
                                    tick=tick, duration_ms=duration_ms)


def normative_limits(patient=None, intensity=80, stim='Click'):
    """Rangos de normalidad para el paciente en atencion, a esa intensidad."""
    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'))
    stim_key, freq = STIM_MAP.get(stim, ('click', None))
    return _get_generator().normative_limits(population, intensity,
                                             stim_key, freq=freq)


def latency_intensity_band(patient=None, wave='V', stim='Click'):
    """Banda normativa (x, lo, hi) del grafico latencia-intensidad."""
    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'))
    stim_key, freq = STIM_MAP.get(stim, ('click', None))
    return _get_generator().latency_intensity_band(population, wave,
                                                   stimulus=stim_key, freq=freq)
