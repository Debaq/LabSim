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
"""

import json
import random
import numpy as np
import scipy.signal as signal
from core.base import context
from core import app_config_store
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
        click = pop[pathway]['click']
        if stimulus == 'click':
            return click

        if stimulus == 'tone_burst':
            stim_key = f"tone_burst_{freq or '1000Hz'}"
            default_ratio_block = pop[pathway].get('tone_burst', {}).get(freq or '1000Hz')
        else:
            stim_key = stimulus
            default_ratio_block = pop[pathway].get(stimulus)

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

    def calculate_wave_parameters(self, baseline, intensity, threshold,
                                   pathology, desviaciones=None, repro_shift=0.0,
                                   click_baseline=None):
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

        # Pendiente de la funcion latencia-intensidad (onda V, click): ~0.08ms/10dB
        # cerca del techo (80-70dB, casi plana) y ~0.3ms/10dB de ahi para abajo
        # -- Hood, "Clinical Applications of the ABR" reporta ~0.3ms/10dB entre
        # 70 y 50dB. Quiebre en 70 (antes estaba en 60, dejaba el tramo 70-60
        # con la pendiente plana que no corresponde).
        if lat_intensity >= 70:
            lat_shift = (80 - lat_intensity) / 10 * 0.08
        else:
            lat_shift = (80 - 70) / 10 * 0.08 + (70 - lat_intensity) / 10 * 0.3

        # Patologia neural (retrococlear): el retraso se acumula de la I
        # hacia la V, o sea prolonga los interpicos I-III/III-V en vez de
        # correr el complejo entero.
        neural_delay = 0.0
        if pathology == 'neural':
            neural_delay = self.norms['pathology_modifiers']['neural'].get(
                'interpeak_prolongation', 0.4)

        # Nivel de sensacion: cuanto por encima del umbral DE ESTE OIDO se
        # esta estimulando. Es lo que manda en amplitud y en ancho de la
        # onda; la intensidad absoluta sola no dice nada (80 dB en un oido
        # con umbral 60 son 20 dB SL, no una respuesta maxima).
        sl = intensity - threshold
        tau_factor = PATHOLOGY_TAU_FACTOR.get(pathology, 1.0)

        for wave in ['I', 'II', 'III', 'IV', 'V']:
            if wave not in baseline:
                continue
            base_lat = baseline[wave]['lat']
            # repro_shift: jitter de "no reproducible" -- mueve TODO el
            # complejo junto (misma respuesta neural, timing inconsistente),
            # no una onda aislada.
            calc_lat = (base_lat + lat_shift * LAT_SHIFT_FACTOR.get(wave, 1.0)
                        + neural_delay * NEURAL_LAT_SHARE.get(wave, 1.0)
                        + repro_shift)
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
                    calc_lat += desviaciones[key]['lat'] * lat_scale

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
            if pathology == 'neural':
                # Las ondas rostrales son las que se caen: baja la razon
                # V/I, que es el otro hallazgo retrococlear clasico.
                calc_amp *= NEURAL_AMP_FACTOR.get(wave, 1.0)
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

            modified[wave] = {
                'lat': calc_lat,
                'amp': calc_amp,
                'width': width_factor,
            }

        return modified, {w: modified[w]['amp'] > 0.02 for w in modified}

    def apply_polarity_effects(self, values, polarity):
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
        return values, CM_value

    def apply_rate_effects(self, values, rate, pathology):
        """Efecto de la tasa de estimulacion, continuo y anclado en RATE_REF.

        Latencia lineal en la tasa (ms por estimulo/s) y amplitud
        exponencial decreciente, ambas por onda: la I es la mas sensible a
        la tasa y la V la que mejor aguanta, que es justo lo que se ensena.
        Sin escalones ni tramos: el modelo viejo tenia quiebres en 15/50/60
        y rangos irreales (ver comentario de RATE_REF).
        """
        d_rate = rate - RATE_REF
        neural = pathology == 'neural'
        lat_gain = RATE_NEURAL_LAT_FACTOR if neural else 1.0
        amp_gain = RATE_NEURAL_AMP_FACTOR if neural else 1.0

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

    def build_target_curve(self, t, values, CM_value=None):
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
            y += self._gaussian(t, cm_lat, CM_value * 0.25, sigma=0.06)

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
                       impedance=3.0):
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
        anteriores son los MISMOS (el rng entrega siempre las filas en el
        mismo orden desde la misma semilla).

        quality: cuanto ruido trae ESTE paciente (1.0 = tipico). Sale de
        los puntos FSP del caso, no del FSP corriente: el FSP medido es
        consecuencia del ruido residual, usarlo para calcularlo era
        circular -- y ademas venia por tramos, asi que el ruido pegaba
        saltos de 8x al cruzar un tramo en plena captura.
        """
        n = len(t)
        target = max(float(target_avg), 1.0)
        block = max(target / NOISE_BLOCKS, 10.0)
        m = int(np.ceil(max(float(current_avg), 1.0) / block))
        m = max(min(m, NOISE_BLOCKS * 4), 1)

        residual = self.sweep_noise(n, m, rng).mean(axis=0)

        # Impedancia de electrodos (peor = mas ruido).
        if impedance < 3:
            imp = 0.5
        elif impedance <= 5:
            imp = 1.0
        else:
            imp = 1.5

        # El promedio de m bloques YA tiene RMS 1/sqrt(m): la caida con las
        # promediaciones sale de ahi. Esta constante solo fija la escala
        # para que al llegar al objetivo (m = NOISE_BLOCKS) el piso quede
        # en NOISE_FLOOR_UV con paciente y electrodos tipicos.
        amp = NOISE_FLOOR_UV * np.sqrt(NOISE_BLOCKS) * quality * imp
        return residual * min(amp, NOISE_MAX_UV)

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

    def generate_curve(self, population, pathology, stimulus_config,
                        technical_config, case_config=None):
        # 1. Baseline normativo
        pathway = ('air_conduction' if 'pathway' not in stimulus_config
                   else stimulus_config['pathway'])
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
        ia = INTERAURAL_ATTENUATION.get(technical_config.get('transducer'), 65.0)
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
            population, pathology, pathway,
            stimulus_config['stim'], stimulus_config.get('freq'),
            stimulus_config['int'], stimulus_config['pol'],
            stimulus_config['rate'], stimulus_config['filter_down'],
            stimulus_config['filter_passhigh'],
        ))

        # 6. Parametros de ondas
        repro_shift = case_config.get('repro_shift', 0.0) if case_config else 0.0
        values, waves_visible = self.calculate_wave_parameters(
            baseline, stimulus_config['int'], threshold, pathology, desviaciones,
            repro_shift=repro_shift, click_baseline=click_baseline,
        )

        # 7. Polaridad + rate
        values, CM_value = self.apply_polarity_effects(values, stimulus_config['pol'])
        values = self.apply_rate_effects(values, stimulus_config['rate'], pathology)

        # 8. Eje temporal (12 ms). fs sale de aca, no de una constante:
        # 500 puntos en 12 ms = ~41.6 kHz, dentro del rango real de un
        # equipo ABR (20-50 kHz).
        t = np.linspace(0, 12, 500)
        fs = (len(t) - 1) / (t[-1] / 1000.0)

        # 9. Curva objetivo (gaussianas)
        y_target = self.build_target_curve(t, values, CM_value)

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
            shadow_values, shadow_cm = self.apply_polarity_effects(
                shadow, stimulus_config['pol'])
            shadow_values = self.apply_rate_effects(
                shadow_values, stimulus_config['rate'],
                ((case_config or {}).get('contra') or {}).get('type', 'normal'))
            y_target = y_target + self.build_target_curve(
                t, shadow_values, shadow_cm)

        # 10. Drift LF + artefacto transductor
        y_drift = self.add_baseline_drift(t, rng)
        y_artifact = self.add_transducer_artifact(t, technical_config['transducer'])

        # 11. Curva limpia (sin ruido). La senial NO se escala por cuanto
        # se lleva promediado: en un equipo real esta completa desde el
        # primer barrido y lo que baja es el ruido (ver averaged_noise).
        y_clean = y_target + y_drift + y_artifact

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
        y_noisy = y_clean + self.averaged_noise(
            t, current_avg, growth_target, quality, rng,
            technical_config.get('impedance', 3.0),
        )

        # 14. Filtros al final (como equipos reales)
        y_final = self.apply_filters(
            y_noisy,
            float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']),
            fs,
        )

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
        }


# ============================================================================
# Interfaz publica: la usa AbrMainWindow
# ============================================================================

_generator = None


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
              done, patient=None, contra=None, capture_id=""):
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
    }

    technical_config = {
        'impedance': 3.0,
        'transducer': 'insert_earphone',
    }

    # Oido no evaluado: umbral y patologia propios, para decidir si aparece
    # curva sombra al pasar la atenuacion interaural (ver shadow_values).
    contra_config = None
    if contra:
        contra_config = {
            'umbral': contra.get('umbral', contra.get('th', 20)),
            'type': PATHOLOGY_MAP.get(contra.get('type', 'normal'), 'normal'),
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
        'ratio_override': ratio_override,
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

    dx = t.copy()
    dy = y.copy()
    return t, y, dx, dy, var_repro
