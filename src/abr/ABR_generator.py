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
"""

import json
import random
import numpy as np
import scipy.signal as signal
from core.base import context
from core import app_config_store


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
        # Pendiente de la funcion latencia-intensidad (onda V, click): ~0.08ms/10dB
        # cerca del techo (80-70dB, casi plana) y ~0.3ms/10dB de ahi para abajo
        # -- Hood, "Clinical Applications of the ABR" reporta ~0.3ms/10dB entre
        # 70 y 50dB. Quiebre en 70 (antes estaba en 60, dejaba el tramo 70-60
        # con la pendiente plana que no corresponde).
        steps_from_80 = (80 - intensity) / 10

        if intensity >= 70:
            lat_shift = steps_from_80 * 0.08
        else:
            lat_shift = (80 - 70) / 10 * 0.08 + (70 - intensity) / 10 * 0.3

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

    def add_baseline_drift(self, t, amplitude=0.04):
        """Drift LF suave. Frecuencia aleatoria para variar entre capturas."""
        f1 = random.uniform(0.4, 1.2)
        f2 = random.uniform(0.15, 0.4)
        return amplitude * (np.sin(2 * np.pi * f1 * t / 12) +
                            0.4 * np.sin(2 * np.pi * f2 * t / 12))

    def pink_noise(self, n, scale=1.0):
        """
        Ruido 1/f via FFT (pink spectrum). EMG separado en add_eeg_noise.
        """
        white = np.random.normal(0, 1, n)
        fft = np.fft.rfft(white)
        freqs = np.fft.rfftfreq(n)
        # 1/f scaling, omitir DC
        fft[1:] /= np.sqrt(freqs[1:])
        fft[0] = 0
        pink = np.fft.irfft(fft, n)
        std = np.std(pink)
        return scale * pink / std if std > 0 else np.zeros(n)

    def add_eeg_noise(self, t, current_avg, target_avg, fsp_actual, impedance=3.0):
        """
        Ruido realista:
        - Pink (LF: drift + EEG background) ~70%
        - EMG (HF muscle artifact) ~30%
        Escala = SNR(1/sqrt(N)) * FSP * impedancia.
        """
        n = len(t)
        pink = self.pink_noise(n, 1.0)

        # EMG (musculo) - ruido pasa-altos
        emg = np.random.normal(0, 1, n)
        if n > 12:
            nyq = 0.5
            cutoff = min(0.4, nyq * 0.99)
            try:
                b, a = signal.butter(4, cutoff, 'high')
                emg = signal.filtfilt(b, a, emg)
                std = np.std(emg)
                emg = emg / std if std > 0 else emg
            except Exception:
                pass

        noise = 0.70 * pink + 0.30 * emg

        # SNR: ruido cae como 1/sqrt(promedaciones), pero nunca a cero
        # (equipo real siempre deja un piso de ruido visible, incluso a
        # 2000+ promediaciones).
        safe_target = max(target_avg, 1)
        snr_reduction = np.sqrt(max(current_avg, 1) / safe_target)
        snr_reduction = min(snr_reduction, 0.92)

        # FSP mapping (factor de mejora segun calidad del caso)
        fsp_scale = {
            (0.0, 1.0): 1.0,
            (1.0, 1.5): 0.7,
            (1.5, 2.0): 0.45,
            (2.0, 2.5): 0.25,
            (2.5, 99):  0.12,
        }
        scale = 0.4
        for (lo, hi), s in fsp_scale.items():
            if lo <= fsp_actual < hi:
                scale = s
                break

        # Impedancia (peor = mas ruido)
        if impedance < 3:
            imp = 0.5
        elif impedance <= 5:
            imp = 1.0
        else:
            imp = 1.5

        base_amp = 0.06
        amp = base_amp * (1.0 - snr_reduction) * scale * imp
        return noise * amp

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

        # 2. Umbral
        if case_config and 'umbral' in case_config:
            threshold = case_config['umbral']
        else:
            threshold = self.norms['pathology_modifiers'][pathology]['threshold_range'][0]

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

        # 10. Drift LF + artefacto transductor
        y_drift = self.add_baseline_drift(t)
        y_artifact = self.add_transducer_artifact(t, technical_config['transducer'])

        # 11. Curva limpia (sin ruido)
        y_clean = y_target + y_drift + y_artifact

        # 12. Growth: a mas promediaciones, target mas visible.
        # El denominador es lo que el CASO realmente necesita
        # (average_objetivo), no lo que el alumno pidio en el equipo -- si
        # el alumno detiene la captura antes de eso, la onda queda
        # parcialmente sin resolver aunque el equipo diga "listo".
        growth_target = target_avg
        if case_config and case_config.get('average_objetivo'):
            growth_target = case_config['average_objetivo']
        growth = self.calculate_growth(current_avg, growth_target)
        # Mezcla suave con curva caotica al inicio (solo si growth < 1)
        if growth < 1.0:
            chaos_amp = (1 - growth) * 0.4
            chaos = np.random.normal(0, chaos_amp, t.shape)
            chaos = signal.filtfilt(*signal.butter(3, 0.2, 'low'), chaos)
            y_signal = growth * y_clean + chaos
        else:
            y_signal = y_clean

        # 13. Ruido EEG segun FSP/SNR
        y_noisy = y_signal + self.add_eeg_noise(
            t, current_avg, target_avg, fsp_actual,
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


def ABR_Curve(actual_intencity, control_setting, preferences, repro_prev, prom, done):
    """
    Genera curva ABR con modelo morfolgico realista.
    """
    generator = _get_generator()

    pathology_map = {
        'normal': 'normal',
        'coclear': 'cochlear',
        'transmission': 'conductive',
        'neural': 'neural',
    }
    pathology = pathology_map.get(preferences.get('type', 'normal'), 'normal')

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
    }

    t, y, metadata = generator.generate_curve(
        population='adult_female',
        pathology=pathology,
        stimulus_config=stimulus_config,
        technical_config=technical_config,
        case_config=case_config,
    )

    dx = t.copy()
    dy = y.copy()
    return t, y, dx, dy, var_repro
