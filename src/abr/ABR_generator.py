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
from core import dsp
from core.base import context
from abr import ecochg
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
#
# OJO con el cero: sl_min se cuenta desde el umbral FISIOLOGICO, que esta
# PHYSIOLOGICAL_OFFSET_DB por debajo del clinico (ver mas abajo). Los
# niveles de emergencia publicados estan en SL clinico, asi que aca van
# sumados el desfase: la I emerge a 20 dB sobre el umbral clinico = 29
# sobre el fisiologico. La unica que cambia de verdad es la V, que por
# definicion se apaga en el umbral fisiologico y por eso queda en 0: en el
# umbral clinico ya vale la mitad, que es lo que hace que el equipo la
# detecte ahi en la mitad de los registros.
WAVE_AMP_GROWTH = {
    'I':   {'sl_min': 29, 'tau': 13},   # la primera en perderse (~40 dB SL)
    'II':  {'sl_min': 31, 'tau': 14},
    'III': {'sl_min': 14, 'tau': 16},
    'IV':  {'sl_min': 17, 'tau': 17},
    'V':   {'sl_min': 0,  'tau': 15},   # la ultima: se apaga en el umbral
}

# Cuanto por debajo del umbral clinico esta el umbral fisiologico, en dB.
# Calibrado sobre el propio modelo: es el nivel de sensacion al que la
# deteccion por FSP >= 3.1 con 2000 barridos ocurre en la mitad de los
# registros, con un paciente de ruido tipico (N* = 1500 a 40 dB nHL). Con un
# paciente mas ruidoso hace falta mas nivel, que es justo lo que pasa en la
# clinica.
PHYSIOLOGICAL_OFFSET_DB = 9.0

# Nivel de sensacion al que la amplitud del normativo esta medida, y codo
# del arranque. Con el codo en 0.3*tau la onda V salia en el 31% de su
# amplitud a SL 0: encontrar el umbral era trivial. Ahora queda en ~3%.
#
# El ancla va en 70 y no en 40 porque el normativo esta medido a 80 dB nHL
# en oidos normales (umbral ~10), o sea SL ~70. Anclarlo en 40 hacia que
# cada onda creciera distinto por encima de ese punto --la I, que arranca
# mas tarde y satura mas rapido, se iba 21% por encima de su valor
# normativo-- y a nivel alto la onda I terminaba mas grande que la V, que
# es imposible y ademas rompe el criterio V/I. Ese 70 es SL clinico, asi
# que aca tambien se le suma el desfase: corriendo el ancla y los sl_min
# juntos, todo lo que pasa lejos del umbral queda exactamente como estaba.
AMP_SL_REF = 70.0 + PHYSIOLOGICAL_OFFSET_DB
AMP_KNEE_FRACTION = 0.05

# Reclutamiento: en perdida coclear la amplitud crece mas rapido con el SL,
# por eso a nivel alto la onda V puede verse casi normal pese al umbral
# elevado (recruitment: true en normative_data.json). Multiplica tau.
# 0.65 era demasiado: contando el SL desde el umbral fisiologico, un oido
# con umbral 60 estimulado a 80 dB llegaba al 95% de la amplitud del oido
# sano, o sea se veia sano. El reclutamiento acelera el crecimiento, no lo
# borra: a igual dB nHL el oido con perdida sigue dando menos.
PATHOLOGY_TAU_FACTOR = {'cochlear': 0.8}

# Funcion latencia-intensidad de la perdida COCLEAR. No es la normal (que
# es lo que hacia antes: la patologia coclear no tocaba la latencia, solo
# la amplitud) ni el corrimiento paralelo de la conductiva. Cerca del
# umbral la latencia se alarga desproporcionado y al subir el nivel de
# sensacion converge a la normal -- por eso la V a nivel alto se ve casi
# normal pese al umbral elevado, y por eso la curva L-I de una coclear es
# EMPINADA en vez de corrida. Sin esto, subir de 80 a 100 dB en un caso
# coclear movia la V 0.16 ms y la funcion salia igual a la de un oido sano.
# Pendiente extra (ms) por cada 10 dB de SL por debajo de la referencia.
# La referencia son 40 dB sobre el umbral CLINICO, asi que contada desde el
# fisiologico lleva sumado el desfase (igual que AMP_SL_REF y los sl_min).
COCHLEAR_LI_SL_REF = 40.0 + PHYSIOLOGICAL_OFFSET_DB
COCHLEAR_LI_SLOPE = 0.15

# Las desviaciones del caso se definen pensando en click a NIVEL ALTO
# (80 dB, que es como se leen los informes). Sumarlas iguales a toda
# intensidad dibujaba un corrimiento paralelo -- pinta de conductiva-- en
# cualquier patologia. La misma alteracion se expresa MAS cerca del umbral,
# asi que se amplifican con el corrimiento L-I, con tope.
DEV_LI_GAIN = 0.35
DEV_LI_MAX = 1.5

# La funcion latencia-intensidad no corre todas las ondas lo mismo. Factor
# sobre el shift de la onda V.
#
# F26 (Hood, tabla 2-3, serie completa 80->40 dB): la onda I se corre 1.43
# ms y la V 1.18 -> la I se mueve ~1.2 veces mas, y el I-V se ACORTA al
# bajar (3.85 -> 3.60). F22 (Delgado, 90->50) da I y V casi iguales
# (razon 0.97). Se toma 1.15, entre las dos series y mas cerca de la que
# tiene la serie completa.
#
# Antes estaba en 0.85 para la I: el interpico se ALARGABA al bajar la
# intensidad, que es lo contrario de lo que reportan las dos fuentes.
LAT_SHIFT_FACTOR = {'I': 1.15, 'II': 1.12, 'III': 1.05, 'IV': 1.02, 'V': 1.0}

# Tasa de estimulacion. Los valores normativos se miden a ~21.1/s (tasa
# clinica tipica) -- ese es el ancla: ahi el modelo no toca nada. Por
# encima la latencia crece lineal (ms por estimulo/s) y la amplitud cae
# exponencial; por debajo el efecto se invierte suave. Todo continuo: antes
# habia tramos 15/50/60/70 con saltos (la onda II pasaba de 0.110 a 0.006
# uV entre 55 y 60/s) y rangos irreales (onda V variaba 6.4x en amplitud y
# 1.1 ms en latencia entre 11 y 90/s; lo real es ~25-30% y ~0.4-0.6 ms).
# Correccion de latencia de la via osea, en ms, por nivel. NO es un offset
# fijo: a nivel alto la osea y la aerea dan lo mismo y la diferencia crece
# hacia el umbral.
#
# Beattie 1998 (Scand Audiol 27:120-6, B-71): +0.3 ms a 40 dB, +0.4 a 30,
# +0.5 a 20 y +0.8 a 10 dB nHL; a 55 dB no hace falta corregir. Es la misma
# idea que la funcion latencia-intensidad, pero de la VIA: el vibrador
# entrega menos energia util cerca del umbral.
BONE_LAT_CORRECTION = {55.0: 0.0, 40.0: 0.3, 30.0: 0.4, 20.0: 0.5, 10.0: 0.8}

# Lactante: la osea le sale MAS RAPIDA que la aerea, al reves que en el
# adulto. El craneo sin suturar transmite mejor y el vibrador saltea un oido
# medio que todavia tiene mesenquima, asi que por via osea el bebe se parece
# mucho mas a un adulto que por via aerea (Cobb y Stuart 2016; Yang,
# Rupert y Moushegian 1987; Stuart et al. 1993).
#
# El valor sale de cerrar contra la tabla de latencias publicada: con el
# offset de adulto el neonato quedaba 0.5-0.6 ms tarde en los tres niveles
# medidos (45, 30 y 15 dB nHL).
# Y no se le suma ademas la correccion por nivel: esa describe un vibrador
# que rinde menos cerca del umbral sobre un craneo adulto. En el lactante la
# funcion latencia-intensidad por via osea es mas PLANA que la del adulto
# (0.45 contra 0.52 ms/10 dB en la tabla publicada), asi que el offset
# constante es lo que cierra en los tres niveles medidos.
INFANT_BONE_LAT_MS = -0.60


# Por via osea, en la practica solo la onda V es confiable: la I y la III
# rara vez se identifican. El vibrador entrega menos energia y con un
# espectro mas pobre en agudos, que es justo la zona que genera la onda I, y
# ademas el artefacto del transductor tapa los primeros milisegundos. Factor
# de amplitud y de ancho por onda (Seo et al. 2018, revision; Turkman et al.
# 2018, que publica interpicos solo cuando la I se ve).
BONE_WAVE_AMP = {'I': 0.25, 'II': 0.35, 'III': 0.60, 'IV': 0.80, 'V': 1.0}
BONE_WAVE_WIDTH = {'I': 1.5, 'II': 1.4, 'III': 1.2, 'IV': 1.1, 'V': 1.05}


# Cuanto del artefacto sobrevive al promediar en polaridad alternada. En
# los fonos la cancelacion es practicamente completa; el vibrador no es
# simetrico entre polaridades y deja un residuo del orden del 15%.
ARTIFACT_ALT_RESIDUAL = {
    'insert_earphone': 0.035,   # la bobina esta lejos: casi simetrico
    'TDH39_headphone': 0.075,
    'bone_vibrator': 0.15,      # empuja contra el hueso: el menos simetrico
}


def bone_latency_correction(intensity):
    """Cuanto se atrasa la via osea respecto de la aerea a ese nivel (ms)."""
    niveles = sorted(BONE_LAT_CORRECTION)
    if intensity >= niveles[-1]:
        return 0.0
    if intensity <= niveles[0]:
        return BONE_LAT_CORRECTION[niveles[0]]
    for a, b in zip(niveles, niveles[1:]):
        if a <= intensity <= b:
            f = (intensity - a) / (b - a)
            return (BONE_LAT_CORRECTION[a]
                    + f * (BONE_LAT_CORRECTION[b] - BONE_LAT_CORRECTION[a]))
    return 0.0


# Umbral que se usa cuando el caso dice "sin respuesta": mas alto que
# cualquier salida del equipo, asi nada responde nunca.
NO_RESPONSE_DB = 999.0

# Salida maxima del vibrador oseo, en dB nHL. No es una limitacion del
# modelo: es la del transductor. F18 (200 oidos) construye su normativa a
# 50, 30 y 10 dB nHL porque el vibrador no entrega mas -- por encima de ahi
# distorsiona y el estimulo deja de ser el que dice la pantalla.
BONE_MAX_OUTPUT_DB = 55.0


# Se probo modelar compresion del vibrador en sus ultimos dB (la bobina se
# satura y la piel del mastoides deja de seguir el movimiento) y se
# descarto: el umbral del caso YA esta en unidades de dial, asi que
# descontar ahi otra vez convierte "respuesta fragil en el tope" en
# "respuesta ausente", que no es lo que se quiere mostrar. La fragilidad
# sale sola del nivel de sensacion: estimular justo en el umbral deja una
# onda minima (ver WAVE_AMP_GROWTH), y decidir si esta o no es la destreza
# que el alumno tiene que ejercitar.

# ---------------------------------------------------------------------
# Morfologia por estimulo
# ---------------------------------------------------------------------
# Un estimulo no solo corre la latencia y cambia la amplitud: cambia la
# FORMA. La onda del burst de 500 Hz es ancha y roma, la del chirp es
# angosta y limpia, y eso es lo que el alumno ve antes que cualquier
# numero.
#
# El motor es uno solo: cuanto se DESPARRAMAN en el tiempo los aportes de
# la particion coclear que el estimulo excita. Ese desparramo sale del
# retardo de la onda viajera, que llega tarde al apex y temprano a la base
# (tau(f) proporcional a f^-0.55). Un burst no lo compensa; un chirp
# presenta los graves antes y lo cancela: por eso el chirp sincroniza.
#
# STIM_DISPERSION es ese desparramo normalizado al del burst de 500 Hz
# (el peor). La compensacion del chirp lo reduce: banda estrecha ~0.5,
# banda ancha ~1.0.
#
# Anclaje: F23 (Pinto y Matas, 40 sujetos) reporta que con tone burst a 80
# dB HL "solo se identifico la onda V; las ondas I y III estuvieron
# ausentes en todas las frecuencias". Por eso la onda I del burst grave
# practicamente no existe acá. Se deja gradiente por frecuencia --a 4 kHz
# la I se sigue viendo-- porque su serie es en dB HL, que a 500 Hz es
# bastante menos nivel de sensacion que a 4 kHz. F24 no reporta anchos,
# asi que el afinamiento del chirp es derivado, no publicado.
STIM_DISPERSION = {'500Hz': 1.0, '1000Hz': 0.595, '2000Hz': 0.319, '4000Hz': 0.129}
STIM_COMPENSATION = {'tone_burst': 0.0, 'nb_ce_chirp_ls': 0.5,
                     'ce_chirp_ls': 1.0, 'ce_chirp': 1.0, 'click': 0.0}
# Cuanto ensancha cada onda por unidad de dispersion residual. La I es la
# mas corta y la que mas sufre; la V, generada por mas poblaciones a la
# vez, es la que mejor aguanta (por eso es la ultima que se pierde).
STIM_WIDTH_SENSITIVITY = {'I': 1.2, 'II': 1.0, 'III': 0.9, 'IV': 0.7, 'V': 0.6}
# Los chirp de banda ancha suman en fase lo que el click suma desparramado:
# la onda sale algo mas angosta. Derivado, no publicado.
WIDE_CHIRP_SHARPENING = {'I': 0.92, 'II': 0.95, 'III': 0.96, 'IV': 0.96, 'V': 0.96}


def stimulus_width(stim, freq=None):
    """Factor de ancho por onda para ese estimulo (1.0 = como el click)."""
    if stim in ('ce_chirp', 'ce_chirp_ls'):
        return dict(WIDE_CHIRP_SHARPENING)
    dispersion = STIM_DISPERSION.get(freq or '', 0.0)
    if not dispersion:
        return {}
    residual = dispersion * (1.0 - STIM_COMPENSATION.get(stim, 0.0))
    return {w: 1.0 + k * residual for w, k in STIM_WIDTH_SENSITIVITY.items()}


# Polaridad: caida de amplitud por onda al pasar de rarefaccion (el
# baseline) a condensacion. F27, mismo click en las dos polaridades sobre
# 100 oidos.
POLARITY_AMP_CONDENSATION = {'I': 0.82, 'II': 0.84, 'III': 0.85,
                             'IV': 0.92, 'V': 1.0}
# Las dos polaridades que se promedian al alternar. No se lista
# 'Alternada' a proposito: es el promedio de estas dos.
POLARITY_PAIR = ('Rarefacción', 'Condensación')

RATE_REF = 21.1
# F13 (Jiang, 80 ninios + 21 adultos, click de 10 a 90/s): de 10 a 90/s la
# onda I se prolonga 4-10%, la III 9-13% y la V 12-15%, y los interpicos se
# prolongan con ella. Las pendientes salen de ahi (ms por estimulo/s sobre
# el baseline adulto): I 0.12 ms = 8%, III 0.40 ms = 11%, V 0.75 ms = 14%.
# Antes la V se movia la mitad de lo publicado (7.6%).
RATE_LAT_SLOPE = {'I': 0.0015, 'II': 0.0028, 'III': 0.0050,
                  'IV': 0.0072, 'V': 0.0094}
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
    'insert_earphone': 65.0,   # publicado 60-70
    'TDH39_headphone': 45.0,   # publicado 40-50: cruza 20 dB antes
    'bone_vibrator': 5.0,      # publicado 0-10 en ADULTO: practicamente nula
}

# La via osea del LACTANTE si tiene atenuacion interaural apreciable: 10-25
# dB, y baja con la edad. La cabeza es chica y el craneo sin suturar no
# conduce de un lado al otro como el del adulto, que es un bloque rigido.
#
# Importa para la curva sombra: en un adulto, estimular por hueso responde
# siempre la mejor coclea y hay que enmascarar SIEMPRE. En un neonato, con
# 20 dB de atenuacion, una asimetria moderada se puede ver sin enmascarar --
# y por eso el screening oseo neonatal es viable.
INFANT_BONE_IA_DB = 22.0


def interaural_attenuation(transducer, population='adult_female'):
    """Cuanto se atenua el estimulo al cruzar el craneo, en dB."""
    base = INTERAURAL_ATTENUATION.get(transducer, 65.0)
    if transducer != 'bone_vibrator':
        return base
    peso = INFANT_POPULATIONS.get(population, 0.0)
    return base + peso * (INFANT_BONE_IA_DB - base)


# Salida maxima por via aerea, en dB nHL. Ni el fono de insercion ni el
# supraaural pasan de 90-100: pedirle 120 a un equipo real no entrega 120,
# entrega distorsion. Mismo criterio que BONE_MAX_OUTPUT_DB.
AIR_MAX_OUTPUT_DB = 100.0
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
# Barridos a los que esta referido ese ruido residual. El residual cae como
# 1/sqrt(N) desde ahi: a 2000 barridos es 1/sqrt(2) del de 1000, a 4000 la
# mitad. Es lo que hace que promediar mas sirva -- y lo que obliga a
# promediar mas para confirmar una respuesta cerca del umbral.
NOISE_REF_SWEEPS = 1000.0

# Ventana de analisis del FSP (ms), por poblacion: la respuesta del neonato
# esta corrida a la derecha y hay que mirarla donde esta.
FSP_WINDOW_MS = {
    'adulto': (4.0, 10.0),
    'neonate': (5.0, 12.0),
    'toddler': (4.6, 11.3),
    'child': (4.3, 10.7),
}
# Grados de libertad del estadistico F con el que se sortea el FSP
# observado (Elberling y Don): 5 puntos de la ventana contra 250 barridos.
FSP_DF1 = 5
FSP_DF2 = 250
# Criterio de respuesta presente. Es el que trae el equipo por defecto y el
# que se usa para despejar el ruido del paciente desde N* (ver
# sigma_from_criterion).
FSP_CRITERION = 3.1
NOISE_MODEL_GAIN = 1.13

# Ruido de UN barrido por debajo del cual no baja ningun paciente: es el
# EEG de fondo, no una propiedad del equipo. Con 2000 barridos deja el
# residual en ~11 nV, mas limpio que cualquier registro real.
MIN_PATIENT_SIGMA_UV = 0.5

# Como el caso declara cuan ruidoso es el paciente: a que nivel se midio,
# cuantos barridos hicieron falta para que el equipo declarara respuesta, y
# si a ese nivel habia respuesta. De ahi sale sigma (ver
# sigma_from_criterion). Los valores por defecto son los de un paciente
# tipico dormido.
CASE_REFERENCE_DEFAULT = {
    # None = el UMBRAL de ese oido para ese estimulo. Es el default a
    # proposito: con la referencia en el umbral y N* = 2000, el umbral que
    # declara el caso ES el nivel donde el equipo declara respuesta en la
    # mitad de los registros con 2000 barridos. Las dos definiciones de
    # umbral --la del caso y la que mide el alumno-- pasan a ser la misma.
    'nivel_referencia': None,
    'barridos_criterio': 2000.0,
    'respuesta_en_referencia': 'presente',
}
# El ruido se genera con RMS 1 y DESPUES pasa por la banda de registro, que
# se queda con una fraccion (el EEG es 1/f y el EMG es de alta: la mayor
# parte de su energia cae fuera de 100-3000 Hz). El equipo mide el residual
# sobre el trazo YA filtrado, asi que la escala tiene que definirse ahi: sin
# esta compensacion el trazo salia 3.7 veces mas limpio de lo que el propio
# equipo declaraba (11 nV cuando decia 40).
NOISE_BAND_CALIBRATION = 3.7
# Techo de seguridad del ruido al arrancar la promediacion, EN EL TRAZO YA
# FILTRADO (que es lo que se ve): mas que esto se sale de la escala del
# grafico y deja de leerse como ruido. Estaba en 1.2 y se expresaba en
# unidades del ruido sin filtrar, asi que al calibrar la escala contra el
# trazo filtrado quedo mordiendo en el caso normal: cualquier objetivo de
# ruido de 40 nV para arriba daba exactamente el mismo trazo, y el ajuste
# del equipo dejaba de hacer efecto.
NOISE_MAX_UV = 2.5

# Falsa onda V: pico de ruido con forma de onda que el docente pone a
# proposito para que el alumno tenga que decidir con los subpromedios A/B y
# no leyendo el promedio. Vive en UNA sola mitad de los barridos (el ruido
# no se reparte parejo entre pares e impares), asi que en el promedio se ve
# a la mitad de su amplitud, en un subpromedio entera y en el otro nada --
# que es exactamente como se delata un artefacto en un equipo real.
FALSE_V_LAT_MS = 5.6            # zona de la onda V a intensidades medias
FALSE_V_AMP_UV = 0.25
# La amplitud configurada es la que queda AL LLEGAR al average objetivo.
# Hacia atras crece como m^-0.25 (al arrancar la promediacion, ~3.8x): un
# artefacto de baja frecuencia promedia peor que 1/sqrt(N), pero promedia.
# Sin este decaimiento el alumno hace lo correcto -- seguir promediando --
# y no pasa nada, que es la leccion opuesta.
FALSE_V_DECAY_EXP = 0.25

# Agitacion del paciente DURANTE la captura. Hasta aca `quality` era una
# constante de todo el registro: el paciente estaba igual de quieto en el
# barrido 1 que en el 2000, asi que el promedio avanzaba parejo y mirar el
# monitor antes de seguir no cambiaba nada. Con esto la captura tiene
# tramos: el paciente se mueve, el canal se agranda, el equipo descarta y
# el promedio se queda quieto hasta que se calma.
#
# Un episodio dura AGITATION_RUN_BLOCKS bloques de promediado (con el
# objetivo partido en NOISE_BLOCKS, son ~2 s de registro a 21/s) y
# multiplica el canal por AGITATION_GAIN. La probabilidad de que un tramo
# este agitado es la inquietud del caso: 1.0 = se mueve la mitad del
# tiempo.
AGITATION_RUN_BLOCKS = 4
AGITATION_GAIN = 6.0
AGITATION_MAX_DUTY = 0.5
# Por encima de este factor el barrido cruza el umbral de rechazo y el
# equipo lo descarta entero, en vez de promediarlo sucio.
AGITATION_REJECT_FACTOR = 2.0

# Reparto del zumbido de red entre lo que sobrevive al promediado (queda
# dibujado en el trazo) y lo que entra con fase distinta en cada barrido
# (no se cancela en A-B y por eso se lleva puesto el FSP). En cuadratura:
# 0.8^2 + 0.6^2 = 1, o sea que la potencia total del zumbido es la misma
# que antes de separarlo.
MAINS_COHERENT = 0.8
MAINS_INCOHERENT = 0.6

# Reflejo post-auricular (PAM): contraccion del musculo auricular
# posterior ante un sonido fuerte. Es miogenico, no neural, pero se
# PROMEDIA como cualquier respuesta -- aparece igual en los dos
# subpromedios --, asi que A/B no lo delata: lo delatan la latencia (12-14
# ms, fuera de todo el complejo I-V), el tamanio (uV, no decimas) y que se
# va cuando el paciente relaja el cuello. Es el contraejemplo de la falsa
# onda V, y por eso vale la pena tenerlo: la replicabilidad no alcanza
# para todo.
#
# Aparece solo con sonido fuerte (es un reflejo, tiene umbral) y crece con
# el nivel; el pasa-alto se lo come porque es lento.
PAM_LAT_MS = 13.0
PAM_SIGMA_MS = 1.1
PAM_MIN_DB = 60.0
PAM_FULL_DB = 100.0
PAM_AMP_UV = 3.5

# SN10: el valle lento que sigue a la onda V. Lento de verdad (un ancho
# de gaussiana de ~0.55 ms contra los 0.18 de una onda neural) y grande
# -- casi la mitad de V --, porque de eso dependen las dos cosas que
# hace: dar el valle contra el que se mide la amplitud de V, y ser lo
# primero que se pierde cuando el pasa-alto sube.
SN10_SIGMA_MS = 0.55
SN10_AMP_RATIO = 0.45

# Muestras por ms del registro: 500 puntos en 12 ms. Se mantiene constante
# al cambiar la ventana para que fs no dependa del protocolo (~41.6 kHz,
# rango real de un equipo). Ver technical_config['window_ms'].
SAMPLES_PER_MS = 500 / 12

# El tubo del fono de insercion retrasa el sonido ~0.9 ms y los valores
# normativos estan medidos CON insertos: al pasar a supraaural todo el
# complejo aparece 0.9 ms antes. Es el ajuste que en clinica se hace de
# cabeza al comparar informes de equipos distintos.
# Retardo acustico del transductor, en ms, respecto del fono de insercion
# (que es la referencia del normativo). El de insercion tiene 0.9-1.0 ms de
# tubo; el supraaural apenas 0.1 (el timpano queda a unos 3 cm del
# diafragma), asi que su respuesta entera aparece ~0.8 ms ANTES.
TRANSDUCER_LATENCY_MS = {
    'insert_earphone': 0.0,
    'TDH39_headphone': -0.8,
    'bone_vibrator': 0.0,   # via osea: tiene su propio bloque normativo
}

# Montajes fuera de technical_factors.electrode_montage del JSON: los del
# ECochG, que no son "otra posicion de electrodo" sino otra distancia a la
# coclea (ver abr.ecochg.ELECTRODE_GAIN). La tabla vive alla porque el
# limite de normalidad de la razon PS/PA depende del mismo electrodo.
EXTRA_MONTAGE_FACTOR = dict(ecochg.ELECTRODE_GAIN)

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
# En el canal SIN promediar el zumbido es mucho mas grande que el residuo
# de arriba: 50 Hz no es coherente con el rate del estimulo, asi que el
# promediado lo reduce (no lo cancela) y lo que queda en la curva es una
# fraccion de lo que se ve en el monitor. Sin esto la falta de tierra era
# invisible en el monitor y arruinaba el FSP igual -- el alumno no tenia
# como enterarse antes de gastar 2000 barridos.
MAINS_MONITOR_GAIN = 6.0

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

# Monitor de EEG previo a promediar. NO es el EEG de banda ancha: un
# equipo muestra el canal YA filtrado en la banda de registro (100-3000 Hz
# en ABR), que es tambien la senial sobre la que decide el rechazo de
# artefacto. Dibujar el crudo era lo que rompia la coherencia del modulo:
# un EEG normal de 12 uV RMS cruzaba los +-25 uV del rechazo en casi todos
# los barridos, o sea el monitor se veia siempre sucio mientras el promedio
# avanzaba lo mas bien -- justo al reves de lo que hay que enseñar.
#
# En la banda del ABR un adulto relajado con los electrodos bien puestos
# queda en ~2 uV RMS: lejos del rechazo, trazo fino. Lo que lo ensucia es
# lo mismo que ensucia el promedio (paciente tenso, impedancias altas,
# desbalance/tierra, banda mas ancha), y por eso ahora las dos cosas se
# mueven juntas.
EEG_BAND_UV = 2.2
EEG_TENSION_BAND_UV = 2.0
# Banda de referencia del ABR de rutina. Al abrir el pasa-alto entra el
# EEG de baja frecuencia, que es 1/f: bajar de 100 a 30 Hz casi duplica lo
# que se ve (y ademas deja pasar la fundamental de 50 Hz).
EEG_HP_REF_HZ = 100.0
EEG_LP_REF_HZ = 3000.0
EEG_HP_EXPONENT = 0.5
EEG_LP_EXPONENT = 0.15
# Que parte del ruido de mas que deja entrar un pasa-alto bajo es ONDULACION
# LENTA (ver sweep_noise). El resto sigue siendo ruido de banda.
BAND_SLOW_SHARE = 0.80
# Artefactos de movimiento/EMG del monitor: pico respecto del umbral de
# rechazo (los que el equipo descarta se tienen que VER cruzando la barra)
# y duracion de la rafaga.
EEG_BURST_PEAK = (1.05, 2.0)
EEG_BURST_MS = (10.0, 30.0)
# Pico de la rafaga con el rechazo apagado: no hay barra contra la cual
# escalar, pero el paciente se sigue moviendo (y ahi la basura entra al
# promedio, ver NO_REJECT_NOISE_FACTOR).
EEG_BURST_NO_REJECT_UV = 45.0
# Frecuencia de muestreo del monitor. 500 Hz no alcanza para mostrar la
# banda del ABR (Nyquist 250): a 2 kHz entra hasta ~900 Hz, que es donde
# vive el EMG que dispara el rechazo.
EEG_DISPLAY_FS = 2000.0
# Barridos por segundo de referencia para contar cuantos artefactos caben
# en un trozo del monitor, si el llamador no pasa el rate del equipo.
EEG_DEFAULT_RATE = 21.1

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
# Razon V/I: en un oido normal la onda V es MAYOR que la I, asi que la razon
# pasa de 1. Por debajo de 1 la V esta desproporcionadamente chica respecto
# de la I, que es el hallazgo retrococlear clasico. Estaba en 0.5, que daba
# por normal una V de la mitad de la I (criterio de la docente, 2026-09-11).
NORM_VI_RATIO_MIN = 1.0
# Diferencia interaural de la onda V que se considera significativa (ms).
NORM_INTERAURAL_MAX = 0.4


def select_population(age=None, gender=None, horas=None):
    """Poblacion normativa segun el paciente (claves de normative_data.json).

    gender: 0 = hombre, 1 = mujer (mismo criterio que cases.data['gender']
    en CaseBuilder.php). Sin edad -> adult_female, que era el valor fijo
    que usaba el modulo antes de esto.

    Las franjas del JSON dejan huecos (neonate 0-0.25, child 2-12,
    adult 18-50, elderly 60-85); acá se cubren completas porque un paciente
    de 1, 15 o 55 anios existe igual.

    El tramo de 1 a 3 anios tiene bloque propio ('toddler'): la via esta
    madurando --equivalencia adulta entre los 9 meses y los 3 anios, con la
    onda V ultima-- y meterlo en 'child', que ya es casi adulto, le borraba
    justo eso. De 3 a 17 va 'child': a esa edad las latencias ya son
    practicamente de adulto.

    El sexo separa de los 18 en adelante, adulto mayor incluido. Antes el
    adulto mayor era uno solo: un hombre de 70 se dibujaba con la curva de
    una mujer. No separa en pediatria a proposito -- la diferencia por sexo
    aparece con la pubertad, no antes.
    """
    # Horas de vida: cuando estan, mandan. Sin esto un bebe de ocho meses
    # tomaba las latencias del recien nacido, porque los dos son "0 anios" y
    # el corte iba por ahi. El bloque 'neonate' es el del recien nacido de
    # termino; pasados los tres meses la via ya arranco a madurar y lo que
    # corresponde es 'toddler', que es justamente el tramo de la maduracion.
    if horas not in (None, ''):
        try:
            meses = float(horas) / 720.0
        except (TypeError, ValueError):
            meses = None
        if meses is not None:
            if meses < 3:
                return 'neonate'
            if meses < 36:
                return 'toddler'
    if age is None:
        return 'adult_female'
    try:
        age = float(age)
    except (TypeError, ValueError):
        return 'adult_female'
    if age < 1:
        return 'neonate'
    if age < 3:
        return 'toddler'
    if age < 18:
        return 'child'
    hombre = str(gender) == '0'
    if age >= 60:
        return 'elderly_male' if hombre else 'elderly_female'
    return 'adult_male' if hombre else 'adult_female'


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
                            freq=None):
        """
        Click SIEMPRE sale del baseline poblacional tal cual -- el perfil
        real del paciente lo ajusta aparte via 'desviaciones' del caso (ver
        calculate_wave_parameters), nunca se pisa desde acá. Cualquier otro
        estimulo guarda solo un ratio respecto a click (lat_ratio/amp_ratio,
        nunca su propio absoluto ni un delta): cuanto se desvia chirp/burst
        del click de ESE paciente. Sin ratio -> 1.0 (misma forma que click).

        Lo que el JSON no describe se DERIVA del bloque que si existe, no
        se copia (ver _rescale_ratio_block).
        """
        pop = self.norms['populations'].get(population)
        if pop is None:
            # 'elderly' era una sola poblacion antes de separarla por sexo;
            # un caso guardado con esa clave sigue resolviendo.
            pop = self.norms['populations'][LEGACY_POPULATIONS.get(population,
                                                                   'adult_female')]
        via = pop.get(pathway) or pop['air_conduction']
        click = via['click']
        if stimulus == 'click':
            return click

        stim_key = self.stim_key(stimulus, freq)

        def ratios_de(bloque):
            if not bloque:
                return None
            if stimulus in STIM_BY_BAND:
                return (bloque.get(stimulus) or {}).get(freq or '1000Hz')
            return bloque.get(stimulus)

        default_ratio_block = ratios_de(via)

        # El JSON no describe todos los estimulos en todas las vias ni en
        # todas las poblaciones (el neonato solo trae click y ce_chirp; la
        # via osea no trae los chirps de banda ancha). Lo que falta NO se
        # copia del adulto: se DERIVA, reexpresando el corrimiento del
        # estimulo sobre el click de esta poblacion y esta via (ver
        # _rescale_ratio_block). Copiarlo tal cual era el bug: el ratio
        # del adulto aplicado a un neonato le estira el retardo del burst
        # con su inmadurez central, que no es de donde sale ese retardo.
        pop_af = self.norms['populations']['adult_female']
        if not default_ratio_block:
            for bloque in (pop.get('air_conduction'),
                           pop_af.get(pathway),
                           pop_af['air_conduction']):
                prestado = ratios_de(bloque)
                if prestado:
                    default_ratio_block = self._rescale_ratio_block(
                        prestado, bloque['click'], click)
                    break

        default_ratio_block = self._complete_ratio_block(default_ratio_block, click)

        baseline = {}
        for wave, click_vals in click.items():
            if wave == 'interpeak':
                continue
            ratio = {'lat_ratio': 1.0, 'amp_ratio': 1.0}
            if default_ratio_block and wave in default_ratio_block:
                ratio.update(default_ratio_block[wave])
            baseline[wave] = {
                'lat': click_vals['lat'] * ratio['lat_ratio'],
                'amp': click_vals['amp'] * ratio['amp_ratio'],
            }
        return baseline

    @staticmethod
    def _rescale_ratio_block(block, ref_click, click):
        """Reexpresa los ratios de otra poblacion/via sobre ESTE click.

        Lo que el estimulo le hace a la respuesta se sabe del adulto: el
        burst de 500 Hz llega ~0.7 ms mas tarde que el click en la onda I y
        ~2.5 ms en la V, el chirp adelanta y agranda. Lo que falta para las
        otras poblaciones no es ese dato, es COMO se traslada. La regla:

        - Parte periferica: el corrimiento que ya se ve en la onda I
          (recorrido coclear y oido medio). Escala con la onda I de esta
          poblacion/via, que es justo lo que mide esa parte.
        - Parte central: lo que el estimulo ADEMAS alarga de la I a la V.
          Escala con el interpico I-V de esta poblacion.

        Copiar el ratio tal cual --que es lo que se hacia-- asume que todo
        escala con la latencia absoluta del click. En un neonato eso estira
        el retardo del burst con su inmadurez central, cuando ese retardo es
        coclear; y en la via osea le pasa lo mismo con el corrimiento del
        oido medio.

        La amplitud no se toca: es propiedad del estimulo (cuanta coclea
        sincroniza), no de la maduracion.
        """
        if not block:
            return block
        for clave in ('I', 'V'):
            if clave not in ref_click or clave not in click:
                return block
        ref_I, ref_V = ref_click['I']['lat'], ref_click['V']['lat']
        lat_I, lat_V = click['I']['lat'], click['V']['lat']
        if not ref_I or ref_V == ref_I:
            return block

        m_perif = lat_I / ref_I
        m_central = (lat_V - lat_I) / (ref_V - ref_I)

        def corrimiento(wave):
            r = block.get(wave)
            if not isinstance(r, dict) or wave not in ref_click:
                return None
            return ref_click[wave]['lat'] * (float(r.get('lat_ratio', 1.0)) - 1.0)

        shift_I = corrimiento('I') or 0.0
        fuera = {}
        for wave, r in block.items():
            if not isinstance(r, dict) or 'lat_ratio' not in r:
                continue
            base = click.get(wave)
            if base is None:
                continue
            shift = corrimiento(wave)
            if shift is None:
                continue
            # La microfonica es prearterial: pura periferia, sin parte central.
            central = 0.0 if wave == 'MC' else shift - shift_I
            nuevo = m_perif * shift_I + m_central * central
            fuera[wave] = dict(r)
            fuera[wave]['lat_ratio'] = (base['lat'] + nuevo) / base['lat']

        salida = {k: v for k, v in block.items() if k not in fuera}
        salida.update(fuera)
        # El interpico declarado quedaria mintiendo contra las latencias
        # nuevas: se recalcula de ellas.
        if 'interpeak' in block and {'I', 'III', 'V'} <= set(fuera):
            lat = {w: click[w]['lat'] * fuera[w]['lat_ratio'] for w in ('I', 'III', 'V')}
            salida['interpeak'] = {
                'I-III': round(lat['III'] - lat['I'], 2),
                'III-V': round(lat['V'] - lat['III'], 2),
                'I-V': round(lat['V'] - lat['I'], 2),
            }
        return salida

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
                                   click_baseline=None, neural=None,
                                   stim_width=None):
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
        #
        # Y se mide desde el umbral FISIOLOGICO, que esta PHYSIOLOGICAL_
        # OFFSET_DB por debajo del que declara el caso. El del caso es el
        # umbral CLINICO --el que el equipo informa, el que sale de la
        # bibliografia via STIM_NHL_CORRECTION y el que el alumno tiene que
        # encontrar-- y un umbral clinico no es el nivel donde la respuesta
        # empieza a existir: es el nivel donde se la puede DETECTAR. Por
        # debajo la respuesta existe, pero queda bajo el ruido.
        #
        # Sin este desfase las dos definiciones no coincidian: el caso
        # decia "umbral 30" y el alumno, midiendo bien, informaba 35 o 40.
        sl = intensity - (threshold - PHYSIOLOGICAL_OFFSET_DB)

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
            #
            # El codo era de 0.3*tau y dejaba un PISO: la onda V salia en el
            # 31% de su amplitud estimulando justo en el umbral, o sea clara
            # y facil de encontrar. En el umbral la respuesta tiene que
            # quedar a la altura del ruido residual -- es lo que obliga a
            # promediar mas y a repetir el registro para confirmarla, que es
            # la maniobra clinica. Con 0.05*tau el codo sigue siendo suave
            # pero no regala amplitud.
            knee = AMP_KNEE_FRACTION * tau
            sl_eff = knee * np.logaddexp(0.0, (sl - growth['sl_min']) / knee)
            # Normalizado a AMP_SL_REF: la amplitud del normativo es la que
            # se mide a ~40 dB SL, no un techo asintotico que no se alcanza
            # nunca (antes a 40 dB SL se llegaba al 89% y el normativo
            # quedaba sistematicamente sub-representado).
            ref = 1.0 - np.exp(-max(AMP_SL_REF - growth['sl_min'], 1.0) / tau)
            amp_factor = (1.0 - np.exp(-sl_eff / tau)) / ref

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
            # ensanchaba nunca). Los quiebres estan en SL clinico, asi que
            # se les suma el desfase como a todo lo demas.
            sl_clin = sl - PHYSIOLOGICAL_OFFSET_DB
            if sl_clin >= 50:
                width_factor = 1.0
            elif sl_clin >= 30:
                width_factor = 1.0 + (50 - sl_clin) * 0.03
            else:
                width_factor = min(1.6 + (30 - sl_clin) * 0.05, 2.6)
            if is_neural:
                # Morfologia pobre/desincronizada: ondas anchas y romas, que
                # es lo que se ve antes de que desaparezcan del todo.
                width_factor *= NEURAL_DESYNC_WIDTH.get(
                    neural_params['desincronia'], 1.0)
            # Ancho propio del estimulo (ver stimulus_width): el burst de
            # 500 Hz desparrama los aportes de la coclea y el chirp los
            # alinea. Es lo que hace que dos estimulos con la misma
            # latencia y amplitud no se vean iguales.
            if stim_width:
                width_factor *= stim_width.get(wave, 1.0)

            modified[wave] = {
                'lat': calc_lat,
                'amp': calc_amp,
                'width': width_factor,
            }

        return modified, {w: modified[w]['amp'] > 0.02 for w in modified}

    def apply_polarity_effects(self, values, polarity, pathology='normal',
                               neural=None):
        # El baseline normativo esta medido EN RAREFACCION (F01 y F27 usan
        # click de rarefaccion), asi que esa polaridad no corrige nada: es
        # el punto de partida. Las otras dos se expresan contra ella.
        #
        # F27 (50 adultos, 100 oidos, el MISMO click en las dos
        # polaridades) da la caida de amplitud al pasar a condensacion:
        # onda I ~0.82, onda III ~0.85, onda V sin efecto consistente
        # (1.10 en mujeres, 0.87 en hombres). F10 (Stockard) agrega que en
        # latencia el efecto es de la onda I --rarefaccion la adelanta-- y
        # que en III y V no hay diferencia consistente.
        #
        # Antes esto multiplicaba TODAS las amplitudes por 1.1 en
        # rarefaccion y la V por 1.15 en condensacion, que es al reves de
        # lo que mide F27.
        CM_value = None
        if polarity == 'Rarefacción':
            CM_value = -0.15
        elif polarity == 'Condensación':
            for w, factor in POLARITY_AMP_CONDENSATION.items():
                if w in values:
                    values[w]['amp'] *= factor
            if 'I' in values:
                values['I']['lat'] += 0.1
            CM_value = 0.15
        elif polarity in ('Alternada', 'Alternante'):
            # La alternada no se calcula: se PROMEDIAN las dos polaridades,
            # que es lo que el equipo hace barrido a barrido (ver
            # build_polarity_curve). Aca solo se marca, y la microfonica
            # queda en None porque se cancela -- ese es el punto de
            # alternar.
            return values, None
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

    def build_polarity_curve(self, t, values, polarity, pathology, neural,
                             cm_sigma_gain):
        """Curva objetivo para esa polaridad.

        Alternada NO es un caso aparte con sus propios factores: es el
        PROMEDIO de la curva en rarefaccion y la curva en condensacion, que
        es lo que el equipo suma barrido a barrido. De ahi salen solos el
        ensanchamiento y la caida del pico --las dos polaridades no tienen
        la misma latencia (ver POLARITY_AMP_CONDENSATION y el +0.1 ms de la
        onda I)-- sin fijar ningun factor a mano. Y la microfonica se
        cancela sola, porque entra con signo opuesto en cada una.
        """
        if polarity not in ('Alternada', 'Alternante'):
            v, cm = self.apply_polarity_effects(
                {w: dict(d) for w, d in values.items()}, polarity, pathology, neural)
            return self.build_target_curve(t, v, cm, cm_sigma_gain), cm

        curvas = []
        for pol in POLARITY_PAIR:
            v, cm = self.apply_polarity_effects(
                {w: dict(d) for w, d in values.items()}, pol, pathology, neural)
            curvas.append(self.build_target_curve(t, v, cm, cm_sigma_gain))
        return (curvas[0] + curvas[1]) / 2.0, None

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

        # SN10: el valle negativo lento que sigue a la onda V. Era una
        # gaussiana tan angosta como las ondas neurales (sigma_V * 1.3) y
        # eso lo volvia otra ondita mas; el SN10 real es lento -- dura
        # varios ms -- y es la mitad de la amplitud de V. Importa por dos
        # cosas: la amplitud de V se mide de pico a valle CONTRA el SN10,
        # y al ser lento es lo primero que se lleva un pasa-alto mal
        # puesto, asi que subirlo achica la amplitud medida sin tocar la
        # latencia -- el error de medir con la banda equivocada y comparar
        # contra la normativa igual.
        if 'V' in values:
            v = values['V']
            amp_V = v['amp']
            sigma_V = WAVE_SIGMA['V'] * v.get('width', 1.0)
            lat_sn10 = v['lat'] + 0.9 + sigma_V * 2
            y += self._gaussian(t, lat_sn10, -amp_V * SN10_AMP_RATIO,
                                sigma=SN10_SIGMA_MS * v.get('width', 1.0))

        # VII: bump tardio pequeno (opcional, amp ~15% V)
        if 'V' in values:
            v = values['V']
            sigma_V = WAVE_SIGMA['V'] * v.get('width', 1.0)
            lat_VII = v['lat'] + 2.5
            y += self._gaussian(t, lat_VII, v['amp'] * 0.18, sigma=WAVE_SIGMA['VII'])

        return y

    def false_wave(self, t, case_config, accepted, target_avg, rng,
                   intensidad=None):
        """Pico espureo con forma de onda V, presente en una sola mitad.

        Devuelve (mitad_a, mitad_b): lo que se le suma a cada subpromedio.
        El promedio es (A+B)/2, asi que la falsa onda aparece ahi con la
        mitad de la amplitud sola, sin tener que sumarla aparte.

        No toca el FSP (que es del caso): queda FSP bajo + onda visible +
        A/B que no se pegan, tres pistas coherentes en vez de una.
        """
        cfg = (case_config or {}).get('falsa_v')
        if not isinstance(cfg, dict):
            return None, None
        amp = float(cfg.get('amp') or 0.0)
        if amp <= 0:
            return None, None
        lat = float(cfg.get('lat') or FALSE_V_LAT_MS)
        if not (0 < lat < float(t[-1])):
            return None, None
        # Rango de intensidades donde aparece. Sin esto salia en TODA la
        # serie y siempre en la misma latencia, asi que el alumno no podia
        # usar la otra prueba real: una onda V migra al bajar la
        # intensidad, un artefacto se queda quieto. Acotarla a las
        # intensidades bajas deja la serie coherente arriba y el engano
        # donde de verdad se busca el umbral.
        if intensidad is not None:
            desde = cfg.get('int_min')
            hasta = cfg.get('int_max')
            if desde is not None and float(intensidad) < float(desde):
                return None, None
            if hasta is not None and float(intensidad) > float(hasta):
                return None, None
        m = self.noise_blocks_done(accepted, target_avg)
        # `amp` es lo que el docente ve EN EL PROMEDIO (que es (A+B)/2), asi
        # que en la mitad donde vive el artefacto va al doble.
        escala = 2 * amp * (NOISE_BLOCKS / max(m, 1)) ** FALSE_V_DECAY_EXP
        # Mismo ancho que una onda V real: si fuera mas angosto o mas ancho
        # se descartaria por la forma y el ejercicio dejaria de ser sobre
        # la replicabilidad.
        pico = self._gaussian(t, lat, escala, sigma=WAVE_SIGMA['V'])
        mitad = str(cfg.get('mitad') or 'auto').lower()
        if mitad not in ('a', 'b'):
            mitad = 'a' if rng.random() < 0.5 else 'b'
        return (pico, None) if mitad == 'a' else (None, pico)

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

    def reject_impedance_factor(self, impedance):
        """Cuanto mas seguido cruza el umbral de rechazo por impedancia.

        Dentro de norma (<= IMPEDANCE_LIMIT_KOHM) no cambia nada: el canal
        crece, pero sigue lejos de los +-25 uV y el equipo promedia igual.
        Pasado el limite el trazo empieza a golpear la barra, y ahi el
        promedio se frena -- que es lo que el monitor muestra.
        """
        return max(1.0, self.impedance_noise_factor(impedance)
                   / self.impedance_noise_factor(IMPEDANCE_LIMIT_KOHM))

    @staticmethod
    def artifact_acceptance(reject_uv, quality, imp_factor=1.0):
        """Fraccion de barridos que sobrevive al rechazo de artefacto.

        Un umbral estrecho con un paciente inquieto descarta la mitad de
        los barridos: el contador del equipo sube igual pero el promedio
        avanza mucho mas lento, que es exactamente lo que pasa en clinica.
        Con el rechazo apagado no se descarta nada, pero entra basura (ver
        NO_REJECT_NOISE_FACTOR en averaged_noise).

        imp_factor (cuanto mas ruidoso esta el registro que con los
        electrodos bien puestos, 1.0 = ideal) entra igual que la calidad
        del paciente: el umbral es fijo en uV, asi que si el canal esta mas
        grande lo cruza mas seguido. Sin esto el monitor mostraba el trazo
        golpeando la barra de rechazo con 8 kOhm mientras el promedio
        avanzaba como si nada -- la incoherencia que hacia que el alumno
        dejara de mirar el monitor.
        """
        if not reject_uv:
            return 1.0
        return float(np.clip(
            float(reject_uv) / (ARTIFACT_REJECT_REF_UV * quality
                                * max(float(imp_factor), 1e-6)),
            0.25, 1.0))

    def add_transducer_artifact(self, t, transducer='insert_earphone',
                                intensity=80.0, polarity=None):
        """Artefacto electromagnetico del estimulo, en los primeros ms.

        No es acustico: el transductor es una bobina con un iman, y la
        corriente del click induce un voltaje en los electrodos y sus
        cables. Por eso CRECE CON LA INTENSIDAD (mas nivel, mas corriente)
        y depende de cuan cerca del electrodo quede la bobina.

        El supraaural es el caso feo: apoyado sobre la oreja, a pocos
        centimetros del electrodo de mastoides, y ADEMAS casi no tiene
        retardo acustico (0.1 ms contra los 0.9-1.0 del tubo de insercion),
        asi que el artefacto y la onda I quedan pegados en el tiempo. A
        nivel alto tapa la onda I o la deforma, y se lee una I temprana y
        grande que es puro estimulo. El de insercion aleja la bobina 33 cm
        de tubo y practicamente lo elimina; el vibrador, apoyado en el
        mastoides, lo tiene entero.

        Polaridad: el artefacto SE INVIERTE con el estimulo, asi que en
        alternada se cancela al promediar mientras la respuesta neural en
        buena parte no. Es la razon principal de alternar, mas alla de la
        microfonica -- y el motivo de que una onda I "que solo aparece en
        rarefaccion" haya que mirarla con desconfianza.

        La escala es 10^((int-ref)/25) y el ref es de CADA transductor, no
        80 para todos: 80 dB es un nivel de rutina para un fono pero esta
        por encima de lo que el vibrador puede entregar. Con el ref unico,
        el vibrador --que fisicamente es el peor, va apoyado sobre el hueso
        a centimetros del electrodo-- terminaba con el artefacto mas chico
        de los tres, porque nunca llega a 80. Su nivel de trabajo alto es
        50-55, y ahi el artefacto tiene que ser grande: es la razon de que
        por via osea las ondas tempranas se pierdan tan seguido.
        """
        cancela = polarity in ('Alternada', 'Alternante')
        cfg = {
            'insert_earphone': {'dur': 0.8, 'amp': 0.05, 'ref': 80.0},
            'TDH39_headphone': {'dur': 1.0, 'amp': 0.12, 'ref': 80.0},
            'bone_vibrator':   {'dur': 1.5, 'amp': 0.30, 'ref': 50.0},
        }.get(transducer, {'dur': 0.8, 'amp': 0.05, 'ref': 80.0})
        if cancela:
            # La cancelacion no es perfecta: el artefacto no sale identico
            # en las dos polaridades, y por via osea menos todavia (la
            # bobina empuja contra el hueso, que no responde igual en los
            # dos sentidos). Queda un residuo. Darlo por cancelado del todo
            # dejaba la via osea mas limpia de lo que es.
            residuo = ARTIFACT_ALT_RESIDUAL.get(transducer, 0.0)
            if residuo <= 0.0:
                return np.zeros_like(t)
        escala = 10 ** ((float(intensity) - cfg['ref']) / 25.0)
        if cancela:
            escala *= residuo
        art = np.zeros_like(t)
        mask = t < cfg['dur']
        art[mask] = cfg['amp'] * escala * np.exp(-t[mask] * 5)
        return art

    def postauricular_reflex(self, t, pam, intensity):
        """Onda miogenica tardia del musculo auricular posterior.

        Bifasica y ancha (es musculo, no nervio) alrededor de los 13 ms,
        asi que en la ventana de rutina de 12 ms apenas asoma la subida y
        recien se ve entera cuando el alumno abre la ventana. No toca el
        FSP: el equipo no la mide como respuesta, y ese es justamente el
        problema -- la mide el alumno con el cursor.
        """
        pam = float(pam or 0.0)
        if pam <= 0:
            return np.zeros_like(t)
        sobre_umbral = float(intensity) - PAM_MIN_DB
        if sobre_umbral <= 0:
            return np.zeros_like(t)
        escala = (pam * PAM_AMP_UV
                  * min(sobre_umbral / (PAM_FULL_DB - PAM_MIN_DB), 1.0))
        onda = self._gaussian(t, PAM_LAT_MS, escala, sigma=PAM_SIGMA_MS)
        onda += self._gaussian(t, PAM_LAT_MS + 2.4, -0.55 * escala,
                               sigma=PAM_SIGMA_MS * 1.2)
        return onda

    def add_baseline_drift(self, t, rng, amplitude=0.04):
        """Drift LF suave. La frecuencia sale del rng del caso: varia entre
        capturas distintas pero se repite si el alumno reabre la app y toma
        la misma captura otra vez."""
        f1 = rng.uniform(0.4, 1.2)
        f2 = rng.uniform(0.15, 0.4)
        return amplitude * (np.sin(2 * np.pi * f1 * t / 12) +
                            0.4 * np.sin(2 * np.pi * f2 * t / 12))

    @staticmethod
    def agitation_run(seed_key, inquietud, bloque):
        """Factor del canal para ESE bloque de promediado (1.0 = quieto).

        Deterministico por caso y por numero de bloque: el mismo paciente
        se mueve en los mismos momentos de la captura aunque se cierre la
        app, y el monitor y el promediador pueden calcularlo por separado
        sin ponerse de acuerdo (los dos preguntan por el mismo bloque).
        """
        inquietud = float(inquietud or 0.0)
        if inquietud <= 0:
            return 1.0
        tramo = int(bloque) // AGITATION_RUN_BLOCKS
        rng = np.random.default_rng(stable_seed(seed_key, 'agit', tramo))
        if rng.random() >= min(inquietud, 1.0) * AGITATION_MAX_DUTY:
            return 1.0
        # No todos los movimientos son iguales: los hay chicos (traga,
        # frunce) y los hay de descartar el barrido entero.
        return 1.0 + (AGITATION_GAIN - 1.0) * float(rng.uniform(0.35, 1.0))

    def sweep_noise(self, n, blocks, rng, band_factor=1.0):
        """`blocks` realizaciones independientes de ruido de barrido (n muestras).

        Devuelve una matriz (blocks, n) de RMS `band_factor`. Pink (EEG de
        fondo, 1/f) 70% + EMG (musculo, HF) 30%, generadas de una sola vez
        para poder promediarlas.

        `band_factor` es cuanto ruido de mas deja entrar la banda elegida
        (ver band_noise_factor), y NO entra como un multiplicador parejo:
        lo que se suma al abrir el pasa-alto es ruido LENTO, porque es
        justamente lo que el pasa-alto estaba sacando. La diferencia
        importa mucho:

        - Dentro de una epoca de 10-12 ms no entra ni un ciclo de 10 Hz,
          asi que ese ruido no se ve como un trazo peludo sino como una
          linea de base que se va para arriba o para abajo en cada
          barrido. En el promedio eso queda como una ondulacion lenta, que
          es exactamente lo que se ve en un ABR registrado con el
          pasa-alto en 3.3 Hz.
        - Y una medida de amplitud PICO A PICO, o de base a pico, se come
          casi todo ese error: los dos puntos estan a menos de un
          milisegundo uno del otro y la ondulacion los mueve a los dos
          juntos.

        Como multiplicador parejo el modelo cobraba 3.16x de ruido de alta
        frecuencia por usar la banda de 10 Hz, que es la banda OBLIGATORIA
        del ECochG: la razon PS/PA quedaba con un 40% de dispersion y no
        se podia separar un oido normal de uno con hidrops. El RMS total
        es el mismo de antes, asi que el ruido residual que declara el
        equipo y el FSP no cambian.
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
                emg = dsp.filtfilt(dsp.butter(4, 0.4, 'high'), emg, axis=1)
                std = np.std(emg, axis=1, keepdims=True)
                emg = np.divide(emg, std, out=np.zeros_like(emg), where=std > 0)
            except Exception:
                pass

        base = 0.70 * pink + 0.30 * emg
        exceso = float(band_factor) ** 2 - 1.0
        if exceso <= 0 or n < 8:
            return base
        # El exceso se reparte: casi todo va a la parte lenta (es lo que el
        # pasa-alto estaba sacando) y una porcion sigue siendo ruido de
        # banda. Dejarlo TODO en la parte lenta no sirve: dentro de una
        # ventana corta la ondulacion tiene muy pocos grados de libertad,
        # asi que el ruido residual que declara el equipo saltaba seis
        # veces entre dos capturas iguales.
        base = base * np.sqrt(1.0 + (1.0 - BAND_SLOW_SHARE) * exceso)
        exceso = BAND_SLOW_SHARE * exceso
        # Componente lenta. Lo que deja entrar un pasa-alto de 10 Hz que
        # un pasa-alto de 100 no dejaba son periodos de 10 a 100 ms: en
        # una ventana de 10-12 ms eso es, como mucho, UN ciclo, y en el
        # extremo lento ni siquiera eso -- es un escalon o una rampa. Se
        # arma con esas cuatro formas y nada mas rapido, que es el punto:
        # un escalon por barrido mueve la linea de base entera y una
        # medida de base a pico no se entera.
        x = np.linspace(-1.0, 1.0, n)
        formas = np.stack([np.ones(n), x, np.sin(np.pi * x), np.cos(np.pi * x)])
        pesos = rng.standard_normal((blocks, formas.shape[0]))
        lento = pesos @ formas
        std = np.std(lento, axis=1, keepdims=True)
        # El escalon puro tiene desviacion cero: se normaliza por la
        # amplitud para que no se vaya al infinito, y sigue siendo el
        # termino que mas mueve la linea de base.
        norma = np.where(std > 1e-9, std,
                         np.max(np.abs(lento), axis=1, keepdims=True))
        lento = np.divide(lento, norma, out=np.zeros_like(lento),
                          where=norma > 1e-9)
        return base + np.sqrt(exceso) * lento

    def averaged_noise(self, t, current_avg, target_avg, quality, rng,
                       imp_factor=1.0, noise_floor_uv=NOISE_FLOOR_UV,
                       split=False, band_factor=1.0, agitacion=None,
                       reject_uv=None):
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

        agitacion: callable(indice de bloque) -> factor del canal en ese
        tramo (ver agitation_run). Con el rechazo puesto, los bloques que
        lo cruzan NO entran al promedio -- el trazo se queda quieto
        mientras el paciente se mueve, y el contador de aceptados deja de
        subir. Sin rechazo entran igual y ensucian el promedio para
        siempre, que es exactamente la diferencia que hay que mostrar.
        Devuelve tambien, en split, cuantos bloques entraron de los m.
        """
        n = len(t)
        m = self.noise_blocks_done(current_avg, target_avg)
        # El ancho de banda NO entra aca: entra en la forma del ruido de
        # cada barrido (ver sweep_noise), no como un multiplicador parejo.
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
        usados = 0
        while hechos < m:
            bloques = self.sweep_noise(
                n, NOISE_TANDA, np.random.default_rng([semilla, hechos // NOISE_TANDA]),
                band_factor=band_factor)
            usar = min(NOISE_TANDA, m - hechos)
            bloques = bloques[:usar]
            idx = np.arange(hechos, hechos + usar)
            if agitacion is not None:
                factores = np.array([float(agitacion(i)) for i in idx])
                if reject_uv:
                    # Barrido que cruza la barra: el equipo lo tira. El
                    # promedio no mejora ni empeora, se queda donde estaba.
                    entra = factores <= AGITATION_REJECT_FACTOR
                    bloques = bloques[entra]
                    idx = idx[entra]
                    factores = factores[entra]
                if len(bloques):
                    bloques = bloques * factores[:, None]
            hechos += usar
            if not len(bloques):
                continue
            total += bloques.sum(axis=0)
            usados += len(bloques)
            pares = bloques[idx % 2 == 0]
            impares = bloques[idx % 2 == 1]
            if len(pares):
                suma_a += pares.sum(axis=0)
                n_a += len(pares)
            if len(impares):
                suma_b += impares.sum(axis=0)
                n_b += len(impares)

        # El denominador son los bloques que ENTRARON, no los que se
        # presentaron: promediar 2000 barridos de los que se descartaron
        # 600 deja el ruido de 1400, y ese es el punto.
        residual = total / max(usados, 1) * escala
        if not split:
            return residual
        # Subpromedios A/B: barridos pares e impares promediados en
        # paralelo. Misma senial en los dos (es el mismo paciente), la
        # mitad de barridos cada uno -> sqrt(2) mas ruido, que es lo que
        # hace que A y B se peguen recien cuando hay respuesta de verdad.
        sub_a = suma_a / max(n_a, 1) * escala
        sub_b = suma_b / max(n_b, 1) * escala if n_b else np.zeros(n)
        return residual, sub_a, sub_b, usados / max(m, 1)

    @staticmethod
    def noise_blocks_done(current_avg, target_avg):
        """Bloques de ruido ya acumulados para `current_avg` barridos."""
        # El bloque es un numero ABSOLUTO de barridos, no una fraccion del
        # objetivo. Antes era target/NOISE_BLOCKS, asi que al llegar al
        # objetivo siempre habia NOISE_BLOCKS bloques y el ruido final era
        # el mismo pidiendo 1000 barridos que pidiendo 4000: promediar mas
        # no servia de nada, que es justo la maniobra con la que se confirma
        # una respuesta cerca del umbral.
        block = max(NOISE_REF_SWEEPS / NOISE_BLOCKS, 1.0)
        m = int(np.ceil(max(float(current_avg), 1.0) / block))
        return max(min(m, NOISE_BLOCKS * 16), 1)

    @staticmethod
    def band_noise_factor(filter_high, filter_low):
        """Cuanto ruido deja entrar la banda de registro elegida.

        Referencia: la banda del ABR de rutina (100-3000 Hz). Abrir el
        pasa-alto es lo que mas pesa, porque el EEG es 1/f: a 3.3 Hz (el
        primer item del combo, o sea con lo que arranca el equipo) entra
        cinco veces mas ruido que a 100. El pasa-bajo pesa poco, es EMG.

        Lo usan el monitor (raw_eeg) y el promediador: mover los filtros
        tiene que ensuciar las DOS cosas o el alumno aprende que da lo
        mismo como los deja.
        """
        hp = max(float(filter_high or EEG_HP_REF_HZ), 1.0)
        lp = max(float(filter_low or EEG_LP_REF_HZ), 1.0)
        return float((EEG_HP_REF_HZ / hp) ** EEG_HP_EXPONENT
                     * (lp / EEG_LP_REF_HZ) ** EEG_LP_EXPONENT)

    @staticmethod
    def noise_scale(quality, imp_factor, noise_floor_uv=NOISE_FLOOR_UV,
                    band_factor=1.0):
        """Amplitud del ruido de UN barrido (el promedio ya divide por m).

        El promedio de m bloques YA tiene RMS 1/sqrt(m): la caida con las
        promediaciones sale de ahi. Esta constante solo fija la escala
        para que al llegar al objetivo (m = NOISE_BLOCKS) el piso quede
        en el ruido residual que declara el equipo, con paciente tipico.
        """
        amp = (noise_floor_uv * NOISE_BAND_CALIBRATION * np.sqrt(NOISE_BLOCKS)
               * quality * imp_factor * max(float(band_factor), 1e-6))
        # El techo existe para que el arranque de la promediacion no se
        # salga de la escala del grafico; NO para tapar unos electrodos
        # malos, asi que sube con ellos. Sin esto, de 6 kOhm para arriba
        # todo daba el mismo trazo y la regla de los 5 kOhm no se podia
        # mostrar.
        techo = NOISE_MAX_UV * NOISE_BAND_CALIBRATION * max(imp_factor, 1.0)
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
            out = dsp.filtfilt(dsp.butter(order, low_n, 'low'), out)

        if filter_high > 0:
            high_n = min(max(filter_high / nyq, 1e-5), 0.99)
            order = 6 if filter_high >= 150 else (5 if filter_high >= 50 else 4)
            filt = dsp.butter(order, high_n, 'high')
            # La epoca NO es la senial: es una ventana sobre un registro
            # continuo que antes y despues del estimulo esta en la linea de
            # base. El pasa-alto en el equipo real trabaja sobre ese
            # registro continuo, no sobre los 5 o 12 ms recortados.
            #
            # Filtrar la epoca sola con el padding corto de filtfilt
            # (unas decenas de muestras) le da al filtro un tramo mucho mas
            # corto que su propia respuesta al impulso (1/f = 100 ms para un
            # corte de 10 Hz) y el resultado es que se lleva puesto lo que
            # en el equipo sobrevive. Donde mas se nota es en el ECochG: el
            # potencial de sumacion es un desplazamiento DC de 2 ms dentro
            # de una ventana de 5, y desaparecia entero con el pasa-alto en
            # 10 Hz -- o sea que el examen no se podia hacer.
            #
            # Se extiende la epoca con su propio borde --que es la linea de
            # base-- hasta cubrir tres constantes de tiempo del corte, y
            # despues se recorta. Con cortes altos (100 Hz y ABR de 12 ms)
            # el relleno es corto y el resultado es el de antes.
            relleno = int(min(3 * fs / filter_high, 5 * len(out)))
            if relleno > 0:
                largo = len(out)
                ext = np.pad(out, relleno, mode='edge')
                ext = dsp.filtfilt(filt, ext)
                out = ext[relleno:relleno + largo]
            else:
                out = dsp.filtfilt(filt, out)

        return out

    # =====================================================================
    # FSP / TRANSICION
    # =====================================================================

    @staticmethod
    def sigma_from_criterion(a_rms, barridos_criterio):
        """Ruido de UN barrido que hace que el FSP llegue a 3.1 con N*.

        Es la forma en que el caso declara cuan ruidoso es el paciente, y es
        una cantidad que el docente puede medir: "a este nivel, este
        paciente necesita N* barridos para que el equipo declare respuesta".
        Despejado de FSP = 1 + A^2 N / sigma^2 con FSP = FSP_CRITERION:

            sigma = A_rms * sqrt(N* / (FSP_CRITERION - 1))

        Antes el caso declaraba el FSP directo (`fsp_puntos`), que es el
        RESULTADO y no una propiedad del paciente: el mismo numero valia a
        cualquier nivel y con cualquier cantidad de barridos.
        """
        if a_rms <= 0 or barridos_criterio <= 0:
            return None
        # NOISE_MODEL_GAIN: el ruido que el equipo INFORMA (estimado de la
        # diferencia de los dos subpromedios, sobre una ventana finita) sale
        # ~13% por encima del sigma/sqrt(N) ideal. Medido sobre el propio
        # modelo a 400, 800, 1600 y 3200 barridos. Sin esta correccion, un
        # caso que declara N* barridos para llegar al criterio necesitaba
        # ~25% mas, y la promesa del campo no se cumplia.
        sigma = float(a_rms * np.sqrt(barridos_criterio / (FSP_CRITERION - 1.0))
                     / NOISE_MODEL_GAIN)
        # Piso: ningun paciente esta MAS quieto que su propio EEG. Sin
        # esto, un caso sin respuesta a su nivel de referencia --una
        # neuropatia con bloqueo, por ejemplo-- despejaba un sigma casi
        # cero, el residual se iba al piso y el FSP declaraba respuesta
        # presente justo donde no hay ninguna.
        return max(sigma, MIN_PATIENT_SIGMA_UV)

    @staticmethod
    def criterion_sweeps_from_fsp(fsp_2000, barridos=2000.0):
        """Migracion: N* equivalente a un FSP declarado a `barridos`.

        De FSP = 1 + A^2 N / sigma^2 se despeja sigma^2 = A^2 N /(FSP - 1), y
        de ahi N* = (FSP_CRITERION - 1) * sigma^2 / A^2 = (FSP_CRITERION - 1)
        * N / (FSP - 1). La amplitud se cancela: la conversion no depende del
        caso, solo del FSP que tenia declarado.
        """
        fsp = max(float(fsp_2000), 1.01)
        return float((FSP_CRITERION - 1.0) * barridos / (fsp - 1.0))

    @staticmethod
    def fsp_window(population):
        """Ventana de analisis del FSP (ms), por poblacion.

        El neonato tiene la respuesta entera corrida a la derecha (su onda V
        esta cerca de 7 ms contra 5.5 del adulto), asi que la ventana que se
        analiza tambien se corre: medir al bebe con la ventana del adulto
        deja la onda V pegada al borde y baja el FSP por recorte, no por
        falta de respuesta.
        """
        return FSP_WINDOW_MS.get(population, FSP_WINDOW_MS['adulto'])

    def expected_fsp(self, t, senial, residual_uv, population):
        """FSP esperado del registro: VAR(S) / (VAR(SP)/N).

        Elberling y Don 1984. En la forma que se puede calcular sin simular
        barrido por barrido:

            FSP = 1 + A_rms^2 * N / sigma^2 = 1 + (A_rms / R)^2

        porque el ruido del PROMEDIO es R = sigma / sqrt(N). O sea: el FSP
        es la razon entre lo que hay de senial y lo que quedo de ruido, y
        sale solo de esas dos cosas. Crece con el nivel (mas senial), crece
        con los barridos (menos ruido) y cae con impedancias altas o un
        paciente inquieto (mas ruido). Nada de eso hay que programarlo
        aparte: sale de la formula.

        Antes el FSP lo declaraba el caso (`fsp_puntos`) y se degradaba a
        mano; daba el mismo numero con respuesta clara que sin respuesta.
        """
        desde, hasta = self.fsp_window(population)
        vent = (t >= desde) & (t <= hasta)
        if not vent.any() or residual_uv <= 0:
            return 1.0
        a_rms = float(np.sqrt(np.mean(senial[vent] ** 2)))
        return 1.0 + (a_rms / residual_uv) ** 2

    @staticmethod
    def observed_fsp(esperado, rng):
        """FSP que muestra el equipo: un sorteo, no el valor teorico.

        El FSP es un estadistico F calculado sobre una muestra, asi que dos
        registros del mismo paciente en las mismas condiciones NO dan el
        mismo numero -- y esa es justamente la razon por la que se repite el
        registro para confirmar. Se sortea de una F no central con
        df1 = FSP_DF1 y df2 = FSP_DF2, con el parametro de no centralidad
        elegido para que la MEDIA de la distribucion sea el FSP esperado.
        """
        media = max(float(esperado), 1.0)
        # media de una F no central = (df1 + nc)/df1 * df2/(df2 - 2)
        nc = max(FSP_DF1 * (media * (FSP_DF2 - 2) / FSP_DF2 - 1.0), 0.0)
        # mismo sorteo que daba scipy.stats.ncf.rvs, que llama a esto
        sorteo = np.random.default_rng(int(rng.integers(1 << 32)))
        valor = float(sorteo.noncentral_f(FSP_DF1, FSP_DF2, nc))
        return max(valor, 1.0)

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

    @staticmethod
    def stim_key(stim, freq=None):
        """Clave del estimulo tal como la indexan el normativo y el caso.

        Misma forma que arma get_baseline_values: 'click', 'ce_chirp',
        'ce_chirp_ls' o '<estimulo de banda>_<freq>' (tone_burst y
        nb_ce_chirp_ls).
        """
        if stim in STIM_BY_BAND:
            return f"{stim}_{freq or '1000Hz'}"
        return stim

    def case_threshold(self, case_config, stimulus_config, pathway, pathology):
        """Umbral del oido para ESTE estimulo, en dB nHL.

        El caso trae una tabla por estimulo cuando el docente derivo el ABR
        del audiograma (ver CaseProfile::abrThresholds en el backend): sin
        ella el umbral era un escalar por oido y una hipoacusia descendente
        respondia igual a un burst de 500 Hz que a uno de 4 kHz --el
        estimulo solo movia latencias, ver get_baseline_values-- asi que la
        evaluacion frecuencia especifica no tenia nada que encontrar.

        La via osea tiene su propia tabla, calculada sobre los umbrales
        oseos: el gap conductivo del ABR sale del audiograma solo.

        Fallback en cascada: tabla del estimulo -> escalar 'umbral' del caso
        (todos los casos guardados antes de esto) -> minimo normativo de la
        patologia.
        """
        if case_config:
            clave = ('umbral_por_estimulo_oseo' if pathway == 'bone_conduction'
                     else 'umbral_por_estimulo')
            tabla = case_config.get(clave) or {}
            key = self.stim_key(stimulus_config['stim'],
                                stimulus_config.get('freq'))
            if key not in tabla:
                # Casos guardados con la nomenclatura vieja (ls_chirp).
                viejo = {v: k for k, v in LEGACY_STIM_KEYS.items()}.get(key)
                if viejo in tabla:
                    key = viejo
            if key in tabla:
                valor = tabla[key]
                if valor is None:
                    # La clave ESTA y vale null: el backend dice "sin
                    # respuesta", no "sin dato" (ver CaseProfile::
                    # abrThresholds). Pasa cuando ninguna frecuencia
                    # respondio en el tonal, y en la via osea cuando el
                    # umbral se va por encima de lo que entrega el
                    # vibrador. Antes esto caia al umbral escalar del oido
                    # y el equipo dibujaba una respuesta que en el caso no
                    # existe.
                    return NO_RESPONSE_DB
                return float(valor)
            if 'umbral' in case_config:
                return float(case_config['umbral'])
        return self.norms['pathology_modifiers'][pathology]['threshold_range'][0]

    def shadow_values(self, population, pathway, stimulus_config, masking, ia,
                      case_config, click_baseline=None):
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
        # El oido no evaluado tiene su propia tabla por estimulo: si no, un
        # paciente con una sola coclea descendente daba sombra a 4 kHz
        # cuando su umbral ahi es 80.
        threshold = max(
            self.case_threshold(contra, stimulus_config, pathway,
                                contra.get('type', 'normal')),
            float(masking))
        if level < threshold:
            return None

        baseline = self.get_baseline_values(
            population, stimulus_config['stim'], pathway,
            freq=stimulus_config.get('freq'),
        )
        values, _ = self.calculate_wave_parameters(
            baseline, level, threshold, contra.get('type', 'normal'),
            desviaciones=contra.get('desviaciones'),
            click_baseline=click_baseline,
            neural=contra.get('neural'),
            stim_width=stimulus_width(stimulus_config['stim'],
                                      stimulus_config.get('freq')),
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
                duration_ms=300.0, fs=EEG_DISPLAY_FS, filter_high=None,
                filter_low=None, rate=None):
        """Trozo del canal de registro por lado (R/L), en uV, sin promediar.

        Es el monitor previo del equipo: lo que el alumno tiene que mirar
        ANTES de apretar promediar. Ahi se ve de una si el paciente esta
        tenso (EMG), si falta la tierra o si los electrodos quedaron
        desbalanceados (50 Hz), sin tener que gastar 2000 barridos para
        enterarse.

        Lo que se devuelve es el canal YA FILTRADO en la banda de registro
        (filter_high/filter_low, los mismos combos del panel de control),
        que es lo que muestra un equipo real y lo unico contra lo que tiene
        sentido comparar el umbral de rechazo: el EEG de banda ancha son
        ~12 uV RMS y cruzaria los +-25 uV todo el tiempo mientras el
        promedio avanza sin problema.

        El trazo comparte TODOS los terminos con el promediador
        (`quality` del caso, impedancias, desbalance/tierra, umbral de
        rechazo): si el monitor se ve sucio, el promedio no avanza y el FSP
        se queda abajo; si el promedio corre, el monitor esta limpio.

        Devuelve {'R': array|None, 'L': array|None, 'rejected_R': bool,
        'rejected_L': bool, 'rms_R': float, 'rms_L': float}. Canal en None =
        electrodo desconectado, no hay registro de ese lado.
        """
        n = max(int(round(duration_ms * fs / 1000.0)), 8)
        # Margen a los lados que se filtra y se descarta: sin esto el
        # transitorio de borde del filtro aparece como un salto cada vez
        # que entra un trozo nuevo al monitor.
        margen = max(int(round(0.1 * fs)), 16)
        n_pad = n + 2 * margen
        t_pad = np.linspace(0, duration_ms * n_pad / n, n_pad)
        impedancias = technical_config.get('impedance')
        if not isinstance(impedancias, dict):
            valor = 3.0 if impedancias is None else float(impedancias)
            impedancias = {k: valor for k in ('vertex', 'right', 'left', 'ground')}
        electrodos = technical_config.get('electrodes') or {}

        def conectado(key):
            return electrodos.get(key, 'A1') != DISCONNECTED

        sin_tierra = not conectado('ground')
        reject = float(technical_config.get('artifact_reject_uv') or 0.0)
        # Banda de registro del equipo. El pasa-bajo se limita a lo que el
        # muestreo del monitor puede mostrar (Nyquist), pero el ANCHO de
        # banda sigue contando en la amplitud: es el efecto que el alumno
        # tiene que ver al tocar los filtros.
        hp = float(filter_high or EEG_HP_REF_HZ)
        lp = float(filter_low or EEG_LP_REF_HZ)
        banda = self.band_noise_factor(hp, lp)
        lp_display = min(lp, fs / 2 * 0.9)
        # Cuantos barridos se presentan en este trozo: es la cantidad de
        # oportunidades que tiene el paciente de meter un artefacto.
        barridos = max(int(round(duration_ms / 1000.0
                                 * float(rate or EEG_DEFAULT_RATE))), 1)

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
            amp = ((EEG_BAND_UV + EEG_TENSION_BAND_UV * max(quality - 1.0, 0.0))
                   * imp_factor * banda)
            # EEG de fondo llevado a la banda del equipo y recien ahi
            # escalado: la amplitud es la de la banda, no la de banda ancha.
            crudo = self.sweep_noise(n_pad, 1, rng)[0]
            crudo = self.apply_filters(crudo, lp_display, hp, fs)[margen:margen + n]
            trazo = crudo / (float(np.std(crudo)) or 1.0) * amp
            # Zumbido de red, a la amplitud del canal sin promediar (ver
            # MAINS_MONITOR_GAIN): a 100 Hz de pasa-alto sobreviven los
            # armonicos, la fundamental de 50 no -- bajar el pasa-alto la
            # deja entrar entera, que es justo lo que hay que mostrar.
            red = MAINS_MONITOR_GAIN * self.mains_interference(
                t_pad, sin_tierra, desbalance, rng)
            red = self.apply_filters(red, lp_display, hp, fs)[margen:margen + n]
            trazo = trazo + red
            # Artefactos de movimiento/EMG: tantos tiros como barridos entren
            # en el trozo, con LA MISMA fraccion que el promediador descarta
            # (paciente + impedancias). Con el rechazo apagado el paciente se
            # mueve igual -- lo que cambia es que nadie descarta nada y esa
            # basura entra al promedio, y eso hay que poder verlo.
            p_artefacto = 1.0 - self.artifact_acceptance(
                reject or ARTIFACT_REJECT_REF_UV, quality,
                self.reject_impedance_factor(max(imp)) * banda)
            artefactos = 0
            for _ in range(barridos):
                if rng.random() >= p_artefacto:
                    continue
                artefactos += 1
                trazo = trazo + self._eeg_burst(n, fs, reject, rng)
            salida[canal] = trazo
            salida[f'rms_{canal}'] = float(np.std(trazo))
            salida[f'peak_{canal}'] = float(np.abs(trazo).max())
            # Cuanto de lo que se ve es red: a 3 s de ventana el zumbido no
            # se distingue como periodico a ojo, asi que el monitor lo tiene
            # que NOMBRAR (un equipo real tambien avisa).
            salida[f'mains_{canal}'] = float(np.std(red))
            # El rechazo se decide contra el trazo que se esta mostrando:
            # la barra del monitor y el contador de barridos aceptados
            # cuentan la misma historia.
            salida[f'rejected_{canal}'] = bool(reject and np.abs(trazo).max() > reject)
            salida[f'reject_rate_{canal}'] = (p_artefacto if reject else 0.0)
        return salida

    @staticmethod
    def _eeg_burst(n, fs, reject_uv, rng):
        """Rafaga de EMG/movimiento: lo que el equipo descarta como artefacto.

        Escalada al umbral de rechazo para que se vea cruzando la barra del
        monitor (con el rechazo apagado no hay barra, pero el paciente se
        mueve igual y esa basura entra al promedio).
        """
        pico = (reject_uv * rng.uniform(*EEG_BURST_PEAK) if reject_uv
                else EEG_BURST_NO_REJECT_UV * rng.uniform(0.6, 1.4))
        largo = max(int(rng.uniform(*EEG_BURST_MS) * fs / 1000.0), 4)
        centro = int(rng.integers(0, n))
        idx = np.arange(n)
        sobre = np.exp(-0.5 * ((idx - centro) / (largo / 2.0)) ** 2)
        emg = rng.standard_normal(n)
        emg = emg / (float(np.std(emg)) or 1.0)
        rafaga = sobre * emg
        return rafaga / (float(np.abs(rafaga).max()) or 1.0) * pico

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

        Tres tramos, de la serie completa de F26 (Hood, tabla 2-3, onda V
        de 80 a 20 dB) contrastada con F22 (Delgado, 90 a 10 dB):

            >= 70 dB   0.12 ms/10 dB   casi plana cerca del techo
            70-50 dB   0.28 ms/10 dB   F26: 5.64 -> 6.19 entre 70 y 50
            < 50 dB    0.50 ms/10 dB   F26: 6.19 -> 7.52 entre 50 y 20

        El tercer tramo faltaba: con una sola pendiente de 0.3 abajo de 70
        la V quedaba 0.45 ms rapida a 30 dB (6.79 contra 7.24 de F26 y 7.47
        de F22), justo donde el alumno busca el umbral.

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
        alto = 0.12
        if intensity >= 50:
            return alto + (70 - intensity) / 10 * 0.28
        return alto + 2 * 0.28 + (50 - intensity) / 10 * 0.50

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
            # El vibrador no pasa de BONE_MAX_OUTPUT_DB: pedirle 80 dB
            # entrega 55 y el registro es el de 55, no el de 80. Se recorta
            # aca y no en el panel porque el equipo tampoco avisa: lo que
            # delata el tope es que la respuesta deja de crecer.
            if float(stimulus_config['int']) > BONE_MAX_OUTPUT_DB:
                stimulus_config = dict(stimulus_config)
                stimulus_config['int'] = BONE_MAX_OUTPUT_DB
        elif float(stimulus_config['int']) > AIR_MAX_OUTPUT_DB:
            # Los fonos tampoco son infinitos: 90-100 dB nHL es el tope.
            stimulus_config = dict(stimulus_config)
            stimulus_config['int'] = AIR_MAX_OUTPUT_DB
        baseline = self.get_baseline_values(
            population, stimulus_config['stim'], pathway,
            freq=stimulus_config.get('freq'),
        )
        # Baseline de click (misma poblacion/via) para escalar
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
        threshold = self.case_threshold(case_config, stimulus_config, pathway, pathology)

        masking = float((case_config or {}).get('masking') or 0.0)
        # Atenuacion interaural del ESTIMULO: cuanto le llega al otro oido
        # de lo que se esta midiendo (ver shadow_values).
        ia = interaural_attenuation(transducer, population)
        # La del RUIDO es otra: el enmascaramiento se entrega por via aerea
        # al oido contrario, con un fono, aunque el estimulo vaya por hueso.
        # Con el vibrador (ia = 0) usar la del estimulo hacia que CUALQUIER
        # nivel de masking enmascarara tambien el oido que se esta midiendo:
        # 70 dB de ruido subian su umbral a 70. Y entre fonos tampoco es lo
        # mismo -- el de copa deja cruzar el ruido 20 dB antes que el de
        # insercion, que es el motivo clinico de preferir insercion cuando
        # hay que enmascarar fuerte.
        ia_masking = interaural_attenuation(
            technical_config.get('masking_transducer')
            or (transducer if transducer != 'bone_vibrator' else 'insert_earphone'),
            population)
        if masking > 0:
            # El ruido que cruza el craneo llega a la coclea POR VIA OSEA,
            # asi que hay que compararlo contra el umbral OSEO de este
            # oido, no contra el aereo. Comparandolo con el aereo se
            # subestima el sobreenmascaramiento justo en las conductivas,
            # que es donde mas importa: un oido con 40 dB de gap tiene la
            # coclea sana y el ruido cruzado la enmascara mucho antes de lo
            # que sugiere su umbral aereo.
            cruzado = masking - ia_masking
            oseo = self.case_threshold(case_config, stimulus_config,
                                       'bone_conduction', pathology)
            if cruzado > oseo:
                # Lo que el estimulo tiene que superar ahora es el ruido en
                # la coclea, mas lo que le cuesta llegar hasta ahi por la
                # via que se esta usando (el gap, si lo hay).
                gap = max(threshold - oseo, 0.0)
                threshold = max(threshold, cruzado + gap)

        # 3. Desviaciones (el caso trae un solo set, plano por onda -- no
        # esta anidado por estimulo, ver CaseBuilder.abrBuild en case_create.php).
        # Se escalan por estimulo en calculate_wave_parameters via click_baseline.
        desviaciones = case_config.get('desviaciones') if case_config else None

        # 4. Cuan ruidoso es ESTE paciente. El caso ya no declara el FSP
        # --que es el resultado-- sino las condiciones en que se midio:
        # a `nivel_referencia`, hicieron falta `barridos_criterio` para que
        # el equipo declarara respuesta. De ahi se despeja el ruido de un
        # barrido (ver sigma_from_criterion) y ese ruido vale para TODOS
        # los niveles, que es lo que un paciente tiene.
        #
        # Los casos guardados con `fsp_puntos` se convierten al vuelo (ver
        # criterion_sweeps_from_fsp): la conversion no depende del caso,
        # solo del FSP que tenia declarado.
        referencia = dict(CASE_REFERENCE_DEFAULT)
        if case_config:
            for clave in referencia:
                if case_config.get(clave) is not None:
                    referencia[clave] = case_config[clave]
            if 'barridos_criterio' not in (case_config or {}) \
                    and case_config.get('fsp_puntos'):
                referencia['barridos_criterio'] = self.criterion_sweeps_from_fsp(
                    case_config['fsp_puntos'].get('2000', 2.8))

        # 5. FSP actual
        current_avg = stimulus_config['current_avg']
        target_avg = stimulus_config['average']
        # OJO: se calcula mas abajo, con los barridos que de verdad
        # entraron al promedio (ver "accepted"), no con los presentados.

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
        def ondas_a(nivel):
            """Ondas tal como quedan a ESE nivel, con todo aplicado.

            Se usa dos veces: para el nivel que se esta registrando y para
            el nivel de referencia del caso, del que sale el ruido del
            paciente (ver sigma_from_criterion).
            """
            v, visibles = self.calculate_wave_parameters(
                baseline, nivel, threshold, pathology, desviaciones,
                repro_shift=repro_shift, click_baseline=click_baseline,
                neural=neural,
                stim_width=stimulus_width(stimulus_config['stim'],
                                          stimulus_config.get('freq')),
            )
            # Via osea: la diferencia con la aerea no es un offset fijo,
            # crece hacia el umbral (ver BONE_LAT_CORRECTION). En el
            # LACTANTE el signo se invierte: el craneo sin suturar y el
            # oido medio salteado le dan una osea mas rapida que la aerea,
            # asi que por esta via el bebe se parece mucho mas a un adulto
            # que por aire.
            if pathway == 'bone_conduction':
                w = INFANT_POPULATIONS.get(population, 0.0)
                corr = (w * INFANT_BONE_LAT_MS
                        + (1.0 - w) * bone_latency_correction(float(nivel)))
                for wave, onda in v.items():
                    onda['lat'] += corr
                    # Y solo la onda V es confiable por esta via (ver
                    # BONE_WAVE_AMP): buscar interpicos en un registro oseo
                    # es el error que el ejercicio tiene que dejar ver.
                    onda['amp'] *= BONE_WAVE_AMP.get(wave, 1.0)
                    onda['width'] = onda.get('width', 1.0) * BONE_WAVE_WIDTH.get(wave, 1.0)
            return v, visibles

        values, waves_visible = ondas_a(stimulus_config['int'])

        # 7. Polaridad + rate. La polaridad ya no se aplica sobre el vector
        # de ondas: se aplica al ARMAR la curva (ver build_polarity_curve),
        # porque la alternada es el promedio de las otras dos y eso no se
        # puede expresar como un factor por onda.
        values = self.apply_rate_effects(values, stimulus_config['rate'],
                                         pathology, neural)
        _, CM_value = self.apply_polarity_effects(
            {w: dict(d) for w, d in values.items()},
            stimulus_config['pol'], pathology, neural)
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
        pol = stimulus_config['pol']
        y_target_a, _ = self.build_polarity_curve(
            t, values_a, pol, pathology, neural, cm_sigma_gain)
        y_target_b = y_target_a if not jitter else self.build_polarity_curve(
            t, values_b, pol, pathology, neural, cm_sigma_gain)[0]
        y_target = (y_target_a + y_target_b) / 2

        # 9b. Curva sombra: si el estimulo cruza el craneo por encima de la
        # atenuacion interaural, la coclea del oido NO evaluado tambien
        # responde y el electrodo la registra igual. Con enmascaramiento
        # suficiente en ese oido desaparece, que es exactamente el ejercicio
        # (estimular fuerte un oido muerto y ver "respuesta" hasta que se
        # enmascara). Antes el spinbox de masking se leia y se tiraba.
        shadow = self.shadow_values(
            population, pathway, stimulus_config, masking, ia, case_config,
            click_baseline=click_baseline,
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
        clamp = (bool(technical_config.get('tube_clamped'))
                 and transducer == 'insert_earphone')
        y_drift = self.add_baseline_drift(t, rng)
        y_artifact = self.add_transducer_artifact(
            t, transducer, stimulus_config['int'], stimulus_config.get('pol'))

        # 11. Curva limpia (sin ruido). La senial NO se escala por cuanto
        # se lleva promediado: en un equipo real esta completa desde el
        # primer barrido y lo que baja es el ruido (ver averaged_noise).
        # Reflejo post-auricular: se promedia como cualquier respuesta, o
        # sea entra por igual en el promedio y en los dos subpromedios.
        # Que A/B NO lo delate es el punto (ver postauricular_reflex).
        y_pam = self.postauricular_reflex(
            t, (case_config or {}).get('pam'), stimulus_config['int'])
        y_clean = y_target + y_drift + y_artifact + y_pam
        y_clean_a = y_target_a + y_drift + y_artifact + y_pam
        y_clean_b = y_target_b + y_drift + y_artifact + y_pam

        # 11b. Tubo pinzado: la maniobra de equipo para saber si lo que se
        # ve es respuesta o es el estimulo acoplandose al electrodo. Con el
        # tubo del insert cerrado NO llega sonido a la coclea, asi que
        # desaparecen la respuesta, la microfonica y la curva sombra --
        # pero el artefacto electrico sigue, porque la corriente al
        # transductor no se pinza. Si algo persiste, no era respuesta.
        # Solo tiene sentido con inserts: el supraaural y el vibrador no
        # tienen tubo, y que la maniobra no haga nada ahi tambien se
        # aprende.
        if clamp:
            y_clean = y_drift + y_artifact
            y_clean_a = y_clean.copy()
            y_clean_b = y_clean.copy()
            waves_visible = False

        # 12. Ruido residual del promediado. El denominador es lo que el
        # CASO necesita (average_objetivo), no lo que el alumno pidio en el
        # equipo: si detiene antes, la curva queda enterrada en ruido
        # aunque el equipo diga "listo".
        growth_target = target_avg
        if case_config and case_config.get('average_objetivo'):
            growth_target = case_config['average_objetivo']
        growth = self.calculate_growth(current_avg, growth_target)
        # Cuanto ruido trae el paciente. Sale de las condiciones en que se
        # midio (nivel de referencia y barridos que hicieron falta), no de
        # un FSP declarado: el FSP es el resultado, no la causa.
        #
        # sigma es el ruido de UN barrido; el modelo de ruido trabaja con
        # el residual al llegar a NOISE_REF_SWEEPS, que es sigma/sqrt(N).
        quality = 1.0
        sigma_paciente = None
        if str(referencia.get('respuesta_en_referencia', 'presente')) != 'ausente':
            nivel_ref = referencia.get('nivel_referencia')
            nivel_ref = threshold if nivel_ref in (None, '') else float(nivel_ref)
            v_ref, _ = ondas_a(nivel_ref)
            v_ref = self.apply_rate_effects(v_ref, stimulus_config['rate'],
                                            pathology, neural)
            # La referencia se arma SIEMPRE con la morfologia del tronco y
            # se mide en la ventana del tronco, corra la prueba que corra.
            # Lo que se despeja aca es cuanto ruido trae EL PACIENTE, y eso
            # no cambia porque se cambie de examen: el caso declara "a tal
            # nivel hicieron falta tantos barridos" una sola vez.
            #
            # Armandola con la curva del ECochG el numero salia absurdo: al
            # nivel de referencia (el umbral) el potencial de sumacion vale
            # cero, asi que la referencia era ~0, sigma caia al piso
            # (MIN_PATIENT_SIGMA_UV) y el mismo paciente resultaba cuatro
            # veces mas silencioso en ECochG que en ABR. Con la respuesta
            # siete veces mas grande, el complejo salia entero en el primer
            # bloque de barridos y promediar no cambiaba nada en pantalla.
            y_ref, _ = self.build_polarity_curve(
                t, v_ref, stimulus_config['pol'], pathology, neural,
                cm_sigma_gain)
            y_ref = self.apply_filters(
                y_ref, float(stimulus_config['filter_down']),
                float(stimulus_config['filter_passhigh']), fs)
            desde, hasta = self.fsp_window(population)
            vent = (t >= desde) & (t <= hasta)
            a_ref = float(np.sqrt(np.mean(y_ref[vent] ** 2))) if vent.any() else 0.0
            sigma_paciente = self.sigma_from_criterion(
                a_ref, float(referencia['barridos_criterio']))
            referencia['a_rms'] = a_ref


        # Estado de los electrodos y rechazo de artefacto: es la parte que
        # el alumno controla desde Parametros Avanzados.
        hay_registro, sin_tierra, imp_max, desbalance = self.electrode_state(
            technical_config)
        # Banda de registro: la MISMA cuenta que ensucia el monitor. Sin
        # esto, dejar el pasa-alto en 3.3 Hz (como arranca el equipo) se
        # veia en el EEG y no costaba nada en la curva -- o sea el alumno
        # aprendia que los filtros dan lo mismo.
        band_factor = self.band_noise_factor(
            stimulus_config['filter_passhigh'], stimulus_config['filter_down'])
        # Lo que cruza el umbral de rechazo: paciente, electrodos fuera de
        # norma y ancho de banda, los tres terminos que agrandan el canal.
        acceptance = self.artifact_acceptance(
            technical_config.get('artifact_reject_uv'), quality,
            self.reject_impedance_factor(imp_max) * band_factor)
        # El ruido del trazo es el del PACIENTE (sigma, del caso). El
        # `residual_noise_nv` del equipo es el criterio con el que el
        # alumno decide cuando parar, no una propiedad del paciente: antes
        # se usaba como escala del ruido y eso mezclaba las dos cosas.
        # Queda de respaldo para los casos que no declaran referencia.
        if sigma_paciente:
            noise_floor = sigma_paciente / float(np.sqrt(NOISE_REF_SWEEPS))
        else:
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

        # 12b. Falsa onda V del caso (si el docente la configuro): entra
        # como ruido de una sola mitad, antes del ruido de fondo, para que
        # los filtros la traten igual que a todo lo demas. Sobrevive al
        # tubo pinzado a proposito: es un artefacto, no una respuesta, y
        # que siga ahi con el tubo cerrado es justo lo que lo delata.
        falsa_a, falsa_b = self.false_wave(
            t, case_config, accepted, growth_target, rng,
            intensidad=stimulus_config['int'])
        if hay_registro and (falsa_a is not None or falsa_b is not None):
            aporte_a = falsa_a if falsa_a is not None else np.zeros_like(t)
            aporte_b = falsa_b if falsa_b is not None else np.zeros_like(t)
            y_clean_a = y_clean_a + aporte_a
            y_clean_b = y_clean_b + aporte_b
            y_clean = y_clean + (aporte_a + aporte_b) / 2

        # Agitacion del paciente a lo largo de la captura (ver
        # agitation_run): la misma serie que ve el monitor de EEG, para que
        # el trazo sucio y el promedio frenado sean el mismo evento.
        inquietud = float((case_config or {}).get('inquietud') or 0.0)
        agitacion = None
        if inquietud > 0:
            seed_key = (case_config or {}).get('seed_key', '')
            agitacion = lambda i: self.agitation_run(seed_key, inquietud, i)
        ruido, ruido_a, ruido_b, entraron = self.averaged_noise(
            t, accepted, growth_target, quality, rng, imp_factor, noise_floor,
            split=True, band_factor=band_factor, agitacion=agitacion,
            reject_uv=technical_config.get('artifact_reject_uv'),
        )
        # Los barridos descartados por moverse no promediaron: el equipo
        # sigue contando los presentados, pero el FSP y el ruido residual
        # son los de lo que realmente entro.
        bloque_actual = self.noise_blocks_done(accepted, growth_target)
        accepted = accepted * entraron
        # El FSP sale de los barridos ACEPTADOS: un paciente que se mueve
        # hace que el equipo cuente 2000 presentados con 1500 promediados,
        # y el criterio de deteccion tiene que ir con los 1500 -- si no,
        # descartar barridos saldria gratis.
        # El zumbido no es todo igual en las dos mitades. Una parte queda
        # enganchada al estimulo (la que el promediado NO borra: es la que
        # se ve dibujada en el trazo aunque se promedien miles de barridos)
        # y otra entra con la fase que le toca a cada barrido, porque 50 Hz
        # y una tasa de 21.1/s son incoherentes. Esa segunda parte sobrevive
        # distinta en A y en B, o sea que NO se cancela en A-B: es la que
        # hace que el residual se dispare y el FSP se caiga.
        #
        # Con una sola realizacion para las dos mitades el zumbido se
        # cancelaba exacto en A-B: el equipo lo dibujaba, pero el residual y
        # el FSP no se enteraban y sin tierra se seguia declarando respuesta
        # presente sobre un trazo inservible.
        red_coh = MAINS_COHERENT * self.mains_interference(
            t, sin_tierra, desbalance, rng)
        inc_a = MAINS_INCOHERENT * self.mains_interference(
            t, sin_tierra, desbalance, rng)
        inc_b = MAINS_INCOHERENT * self.mains_interference(
            t, sin_tierra, desbalance, rng)
        red_a = red_coh + inc_a
        red_b = red_coh + inc_b
        red = red_coh + (inc_a + inc_b) / 2.0
        y_noisy = y_clean + ruido + red

        # 13. Canal contralateral: el mismo estimulo, el mismo paciente,
        # leido entre el vertex y el mastoides del oido NO estimulado.
        # Comparte el ruido del promediado (es el mismo amplificador y el
        # mismo momento) pero la respuesta llega proyectada distinto.
        contra_key = self.contra_channel(technical_config,
                                         stimulus_config.get('side', 'OD'))
        y_contra = None
        if contra_key and hay_registro and clamp:
            # Mismo canal, mismo ruido, sin respuesta: el contra tiene que
            # apagarse con la maniobra igual que el ipsi.
            y_contra = self.apply_filters(
                y_clean + ruido_b + red_b,
                float(stimulus_config['filter_down']),
                float(stimulus_config['filter_passhigh']), fs)
        elif contra_key and hay_registro:
            y_contra_clean = (self.build_target_curve(
                t, self.contra_values(values), CM_value)
                + y_drift + y_artifact)
            if shadow:
                # La sombra viene de la coclea del otro oido: en el canal
                # contralateral queda MAS cerca del electrodo, no menos.
                y_contra_clean = y_contra_clean + self.build_target_curve(
                    t, shadow_values, shadow_cm)
            y_contra = self.apply_filters(
                y_contra_clean + ruido_b + red_b,
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
            y_clean_a + ruido_a + red_a, float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']), fs)
        sub_b = self.apply_filters(
            y_clean_b + ruido_b + red_b, float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']), fs)
        repro_index = self.replicability(sub_a, sub_b)

        # Ruido residual REAL de este registro (nV RMS), que es lo que el
        # equipo muestra al lado del FSP: la diferencia entre los dos
        # subpromedios es ruido y nada mas (la senial se cancela), asi que
        # sale de ahi sin tener que separar senial de ruido a mano.
        residual_nv = float(np.std(sub_a - sub_b) / 2.0 * 1000.0)

        # FSP: sale del trazo, no del caso. Es la razon entre la senial que
        # hay en la ventana de analisis y el ruido que quedo despues de
        # promediar (ver expected_fsp). Que suba con el nivel, que suba con
        # los barridos y que caiga con impedancias altas o un paciente
        # inquieto no se programa: es consecuencia de esa razon, porque
        # todas esas cosas ya estan en el ruido residual.
        #
        # La senial es la RESPUESTA (con la sombra, si la hay), no el trazo
        # entero: el drift y el artefacto del transductor no son respuesta y
        # meterlos daba un FSP que subia con el artefacto. Se mide filtrada,
        # que es como la ve el equipo: con la banda mal elegida el FSP tiene
        # que caer igual que cae la onda. Es la MISMA cantidad con la que se
        # despejo el ruido del paciente (ver sigma_from_criterion), asi que
        # el caso que declara N* barridos para llegar al criterio, llega.
        senial_filtrada = self.apply_filters(
            y_target, float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']), fs)
        desde_v, hasta_v = self.fsp_window(population)
        vent_v = (t >= desde_v) & (t <= hasta_v)
        a_rms_registro = (float(np.sqrt(np.mean(senial_filtrada[vent_v] ** 2)))
                          if vent_v.any() else 0.0)
        fsp_esperado = self.expected_fsp(t, senial_filtrada,
                                         residual_nv / 1000.0, population)
        # Y lo que el equipo muestra es un sorteo alrededor de ese valor:
        # dos registros iguales no dan el mismo numero, que es la razon de
        # repetir para confirmar.
        fsp_actual = self.observed_fsp(fsp_esperado, rng)
        if clamp:
            # Sin estimulo no hay senial: la formula ya da 1, pero se deja
            # explicito porque es el punto de la maniobra.
            fsp_esperado = fsp_actual = 1.0

        return t, y_final, {
            'population': population,
            'pathology': pathology,
            'test': stimulus_config.get('test', 'ABR'),
            'waves_visible': waves_visible,
            'current_avg': current_avg,
            'target_avg': target_avg,
            'fsp': fsp_actual,
            'fsp_esperado': fsp_esperado,
            # Las dos cantidades de las que sale el FSP, para poder
            # auditarlo: la senial en la ventana y el ruido del paciente.
            'fsp_a_rms': a_rms_registro,
            'fsp_sigma': sigma_paciente,
            'fsp_a_referencia': referencia.get('a_rms'),
            'growth': growth,
            'threshold': threshold,
            'masking': masking,
            'shadow': bool(shadow),
            'window_ms': window_ms,
            'transducer': transducer,
            'pathway': pathway,
            # Lo que el transductor entrego de verdad: con vibrador oseo
            # puede ser menos que lo que pidio el panel (BONE_MAX_OUTPUT_DB).
            'output_db': float(stimulus_config['int']),
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
            'tube_clamped': clamp,
            # Bloque de promediado en curso: con el lo calcula el monitor
            # de EEG el mismo tramo de agitacion que el promediador, y el
            # trazo sucio y el promedio frenado quedan sincronizados.
            'noise_blocks': bloque_actual,
            'agitation': (float(agitacion(bloque_actual - 1))
                          if agitacion else 1.0),
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
        'artifact_reject_uv': protocol.reject_uv,
        'residual_noise_nv': 40.0,
        'fsp_criterion': 3.1,
        # --- Todavia SIN EFECTO en el trazo -----------------------------
        # Estan en el equipo real y el alumno los busca, asi que el dialogo
        # los muestra y el technical_config los transporta. El generador no
        # los lee ADREDE: conectarlos es leerlos aca, uno por uno, con su
        # modelo y su test. Ver UNCONNECTED_SETTINGS.
        'click_us': 100.0,
        'burst_envelope': '2-1-2',
        'burst_window': 'blackman',
        'level_unit': 'nHL',
        'rate_jitter_pct': 0.0,
        'presentation': 'monaural',
        'masking_noise': 'white',
        'masking_offset_db': 0.0,
        'channels': 1,
        'gain': 100000.0,
        'notch_hz': 0.0,
        'filter_slope': 12.0,
        'sample_rate_hz': 30000.0,
        'weighted_averaging': False,
        'auto_stop': 'ambos',
        'fsp_window_ms': None,
        'smoothing': 0.0,
    }


# Lo que el dialogo de Parametros Avanzados muestra pero el generador
# todavia no lee. Se lista explicito para que los tests puedan exigir que
# el resto SI se use, y para que la lista se achique sola a medida que se
# vayan conectando: sacar una clave de aca es el ultimo paso de
# conectarla.
UNCONNECTED_SETTINGS = (
    'click_us', 'burst_envelope', 'burst_window', 'level_unit',
    'rate_jitter_pct', 'presentation', 'masking_noise', 'masking_offset_db',
    'channels', 'gain', 'notch_hz', 'filter_slope', 'sample_rate_hz',
    'weighted_averaging', 'auto_stop', 'fsp_window_ms', 'smoothing',
)


def _get_generator():
    global _generator
    if _generator is None:
        _generator = ABRGenerator()
    return _generator


# Texto del combo cb_stim (AbrConfig_ui.py) -> (clave en normative_data.json, freq)
#
# Los estimulos son los del equipo real: click, CE-Chirp de banda ancha
# (el original, no level-specific), CE-Chirp LS (nivel-especifico, el que
# se usa de rutina hoy), NB CE-Chirp LS por banda y tone burst por
# frecuencia. Los dos primeros y los dos ultimos NO son lo mismo: el chirp
# de banda ancha explora toda la coclea a la vez --sirve para umbral
# global, no para evaluacion frecuencia especifica-- y el NB/burst miran
# una banda sola. La via (aerea/osea) no es un estimulo: la define el
# transductor en Parametros Avanzados (ver AbrAdvanceSettings).
STIM_MAP = {
    'Click':                 ('click', None),
    'CE-Chirp':              ('ce_chirp', None),
    'CE-Chirp LS':           ('ce_chirp_ls', None),
    'NB CE-Chirp LS 500 Hz': ('nb_ce_chirp_ls', '500Hz'),
    'NB CE-Chirp LS 1 kHz':  ('nb_ce_chirp_ls', '1000Hz'),
    'NB CE-Chirp LS 2 kHz':  ('nb_ce_chirp_ls', '2000Hz'),
    'NB CE-Chirp LS 4 kHz':  ('nb_ce_chirp_ls', '4000Hz'),
    'Burst 500 Hz':          ('tone_burst', '500Hz'),
    'Burst 1 kHz':           ('tone_burst', '1000Hz'),
    'Burst 2 kHz':           ('tone_burst', '2000Hz'),
    'Burst 4 kHz':           ('tone_burst', '4000Hz'),
}


# Estimulos que llevan frecuencia: la clave del normativo y la del caso se
# arman con la banda pegada (ver ABRGenerator.stim_key).
STIM_BY_BAND = ('tone_burst', 'nb_ce_chirp_ls')


# Rotulos y claves viejas -> las de ahora. Los casos y las configuraciones
# guardadas antes del cambio de nomenclatura traen 'Ls-chirp'/'ls_chirp' y
# 'Burst 1kHz': sin esto el combo se iba al primer item y la tabla de
# umbrales por estimulo del caso no matcheaba ninguna clave (o sea, el
# estimulo dejaba de hacer efecto, en silencio).
LEGACY_STIM_LABELS = {
    'Chirp':       'CE-Chirp',
    'Ls-chirp':    'CE-Chirp LS',
    'Burst 500Hz': 'Burst 500 Hz',
    'Burst 1kHz':  'Burst 1 kHz',
    'Burst 2kHz':  'Burst 2 kHz',
    'Burst 4kHz':  'Burst 4 kHz',
}

LEGACY_STIM_KEYS = {
    'ls_chirp': 'ce_chirp_ls',
}

# Poblaciones que dejaron de existir tal cual. 'elderly' era una sola hasta
# que se separo por sexo; los casos guardados con esa clave siguen andando.
LEGACY_POPULATIONS = {
    'elderly': 'elderly_female',
}

# Poblaciones con el craneo todavia sin suturar: la via osea se comporta
# distinto (ver INFANT_BONE_LAT_MS).
# Cuanto le queda de craneo sin suturar a cada poblacion, entre 0 y 1: es
# lo que pondera la osea de lactante contra la de adulto. El de 1 a 3 anios
# tiene las suturas a medio cerrar, asi que le toca la mitad de cada una.
INFANT_POPULATIONS = {'neonate': 1.0, 'toddler': 0.5}


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
        # Que potencial se esta registrando. El generador lo usa para la
        # curva objetivo y la ventana de analisis del FSP; el resto del
        # equipo es el mismo (ver abr/protocols.py).
        'test': control_setting.get('test', 'ABR'),
    }

    # Equipo: lo que el alumno dejo en Parametros Avanzados. El fallback es
    # el montaje de rutina del protocolo (ver abr.protocols), no un dict
    # fijo -- cuando cuelguen los otros potenciales de esta ventana, cada
    # uno trae su ventana de registro y su montaje.
    technical_config = default_settings(control_setting.get('test', 'ABR'))
    if technical:
        technical_config.update(technical)
    # Pinzar el tubo es una maniobra del panel de control (se hace en plena
    # captura), no un parametro del dialogo de equipo, pero para el
    # generador es una condicion del registro como cualquier otra.
    technical_config['tube_clamped'] = bool(control_setting.get('clamp'))

    # Oido no evaluado: umbral y patologia propios, para decidir si aparece
    # curva sombra al pasar la atenuacion interaural (ver shadow_values).
    contra_config = None
    if contra:
        contra_config = {
            'umbral': contra.get('umbral', contra.get('th', 20)),
            # Tabla por estimulo del oido no evaluado (ver case_threshold).
            'umbral_por_estimulo': contra.get('umbral_por_estimulo'),
            'umbral_por_estimulo_oseo': contra.get('umbral_por_estimulo_oseo'),
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

    case_config = {
        'desviaciones': preferences.get('desviaciones', {}),
        # Falsa onda V: artefacto docente que solo delatan los subpromedios
        # A/B (ver false_wave). Los casos guardados antes no la traen.
        'falsa_v': preferences.get('falsa_v'),
        # Cuanto se mueve el paciente durante la captura (0 = quieto, que
        # es lo que traen los casos de antes de esto).
        'inquietud': preferences.get('inquietud', 0),
        # Reflejo post-auricular (miogenico, ~13 ms): 0 = no aparece.
        'pam': preferences.get('pam', 0),
        'fsp_puntos': preferences.get('fsp_puntos', {'800': 2.3, '2000': 2.8}),
        'umbral': preferences.get('umbral', preferences.get('th', 20)),
        # Umbral por estimulo derivado del audiograma del caso (ver
        # case_threshold). Los casos guardados antes de esto no lo traen y
        # caen en el escalar de arriba, que es como se comportaban.
        'umbral_por_estimulo': preferences.get('umbral_por_estimulo'),
        'umbral_por_estimulo_oseo': preferences.get('umbral_por_estimulo_oseo'),
        'average_objetivo': preferences.get('average_objetivo', 2000),
        'repro_shift': var_repro,
        # Jitter DENTRO de la captura: lo que hace que los subpromedios A/B
        # de un paciente no reproducible no lleguen a pegarse nunca.
        'repro_jitter': 0.0 if preferences.get('repro', True) else repro_var,
        # Patron retrococlear del caso (I-III, III-V, bloqueo, razon V/I,
        # microfonica, desincronia, tasa). Los casos guardados antes de que
        # existiera no lo traen y caen en NEURAL_PARAM_DEFAULTS, que es como
        # se dibujaban.
        'neural': preferences.get('neural'),
        # Bloque de electrococleografia de ESTE oido (razon PS/PA, efecto
        # de la tasa, separacion rarefaccion-condensacion, microfonica).
        # Sin el, la prueba no se registra -- ver ecochg.case_params.
        'ecochg': preferences.get('ecochg'),
        'masking': control_setting.get('mkg', 0),
        'contra': contra_config,
        # Semilla estable del ruido: identifica el perfil del oido, no la
        # corrida. Ver core.rng.stable_seed.
        'seed_key': case_fingerprint(preferences),
        'capture_id': capture_id,
    }

    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'),
                                   (patient or {}).get('edad_horas'))

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

def agitation_factor(preferences, block):
    """Factor de agitacion del caso en ese bloque de promediado.

    Lo usa el monitor de EEG para ensuciar el trazo en EL MISMO tramo en
    que el promediador esta descartando barridos: si el alumno ve el
    monitor limpio mientras el promedio no avanza, el equipo le esta
    mintiendo.
    """
    inquietud = float((preferences or {}).get('inquietud') or 0.0)
    if inquietud <= 0:
        return 1.0
    return _get_generator().agitation_run(
        case_fingerprint(preferences or {}), inquietud, block)


def case_quality(preferences):
    """Cuanto ruido trae ESTE paciente (1.0 = tipico).

    Misma cuenta que generate_curve: sale de los puntos FSP del caso, que
    es donde el caso declara "este paciente es ruidoso".
    """
    puntos = (preferences or {}).get('fsp_puntos') or {}
    fsp_2000 = float(puntos.get('2000', 2.8) or 2.8)
    return float(np.clip(2.8 / max(fsp_2000, 0.5), 0.5, 2.5))


def raw_eeg(technical=None, quality=1.0, seed=0, tick=0, duration_ms=300.0,
            test='ABR', setting=None):
    """Trozo del canal de registro para el monitor (ver ABRGenerator.raw_eeg).

    `setting` es lo que devuelve AbrControl.get_data(): de ahi salen la
    banda de registro y el rate, que son parte del equipo tanto como las
    impedancias -- el monitor tiene que mostrar la MISMA banda que se va a
    promediar.
    """
    technical_config = default_settings(test)
    if technical:
        technical_config.update(technical)
    setting = setting or {}
    def _num(clave, defecto):
        try:
            return float(setting.get(clave) or defecto)
        except (TypeError, ValueError):
            return defecto
    return _get_generator().raw_eeg(
        technical_config, quality=quality, seed=seed, tick=tick,
        duration_ms=duration_ms,
        filter_high=_num('filter_passhigh', EEG_HP_REF_HZ),
        filter_low=_num('filter_down', EEG_LP_REF_HZ),
        rate=_num('rate', EEG_DEFAULT_RATE))


def normative_limits(patient=None, intensity=80, stim='Click'):
    """Rangos de normalidad para el paciente en atencion, a esa intensidad."""
    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'),
                                   (patient or {}).get('edad_horas'))
    stim_key, freq = STIM_MAP.get(stim, ('click', None))
    return _get_generator().normative_limits(population, intensity,
                                             stim_key, freq=freq)


def latency_intensity_band(patient=None, wave='V', stim='Click'):
    """Banda normativa (x, lo, hi) del grafico latencia-intensidad."""
    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'),
                                   (patient or {}).get('edad_horas'))
    stim_key, freq = STIM_MAP.get(stim, ('click', None))
    return _get_generator().latency_intensity_band(population, wave,
                                                   stimulus=stim_key, freq=freq)
