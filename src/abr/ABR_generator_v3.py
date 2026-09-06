"""
ABR Generator V3 - Modelo morfológico realista.

Diferencias vs V2:
- Ondas = suma de gaussianas centradas en cada latencia (no Bézier).
- Bézier aplastaba picos y generaba valles profundos entre ondas (1.25-1.6x amp).
- Valles entre ondas ahora pequenos (~10-20% amp), morfologia ABR real.
- Baseline comun ~0 con drift LF, no escalonamiento por onda.
- Ondas VI (trough negativo) y VII (bump tardio) renderizadas con morfologia propia.
- Ruido EEG = pink (1/f) + EMG HF, no blanco+butter.
- FSP como SNR creciente (ruido ~ 1/sqrt(N)), no mezcla lineal caos-objetivo.
- Filtros = solo butterworth, sin hacks morfológicos.
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


class ABRGeneratorV3:
    """Generador de curvas ABR con morfologia realista."""

    def __init__(self, normative_data_path=None):
        if normative_data_path is None:
            normative_data_path = context.get_resource('abr/normative_data.json')
        with open(normative_data_path, 'r', encoding='utf-8') as f:
            self.norms = json.load(f)

    # =====================================================================
    # VALORES NORMATIVOS Y PARAMETROS POR ONDA
    # (Misma logica que V2; mantiene compatibilidad con JSON)
    # =====================================================================

    def get_baseline_values(self, population='adult_female',
                            stimulus='click', pathway='air_conduction',
                            freq=None, click_override=None):
        """
        Click guarda lat/amp absolutos (editable por curso/caso). Cualquier
        otro estimulo guarda solo un ratio respecto a click (lat_ratio/
        amp_ratio) -- nunca su propio absoluto ni un delta -- para que un
        override de click (config por curso, o desviacion del caso) se
        propague solo a chirp/burst sin tener que redefinirlos aparte.
        Sin ratio para esa combinacion poblacion/estimulo -> ratio 1.0
        (misma forma que click), no una tabla aparte silenciosa.

        click_override: dict {onda: {'lat':.., 'amp':..}} que pisa el default
        bundleado (resources/abr/normative_data.json) onda por onda -- llega
        de la config del curso (ver core.app_config_store, key
        "normative_data.abr", resuelta por el backend en AppConfig.php) via
        ABR_Curve(). Ondas no listadas en el override usan el default tal cual.
        """
        pop = self.norms['populations'][population]
        click = pop[pathway]['click']
        if click_override:
            click = {**click, **{
                wave: {**click.get(wave, {}), **vals}
                for wave, vals in click_override.items()
            }}
        if stimulus == 'click':
            return click

        if stimulus == 'tone_burst':
            by_freq = pop[pathway].get('tone_burst', {})
            ratio_block = by_freq.get(freq or '1000Hz')
        else:
            ratio_block = pop[pathway].get(stimulus)

        if not ratio_block:
            return click

        baseline = {}
        for wave, click_vals in click.items():
            if wave == 'interpeak':
                continue
            ratio = ratio_block.get(wave, {'lat_ratio': 1.0, 'amp_ratio': 1.0})
            baseline[wave] = {
                'lat': click_vals['lat'] * ratio.get('lat_ratio', 1.0),
                'amp': click_vals['amp'] * ratio.get('amp_ratio', 1.0),
            }
        return baseline

    def calculate_wave_parameters(self, baseline, intensity, threshold,
                                   pathology, desviaciones=None, repro_shift=0.0,
                                   click_baseline=None):
        modified = {}
        steps_from_80 = (80 - intensity) / 10

        if intensity >= 60:
            lat_shift = steps_from_80 * 0.08
        else:
            lat_shift = (80 - 60) / 10 * 0.08 + (60 - intensity) / 10 * 0.3

        for wave in ['I', 'II', 'III', 'IV', 'V']:
            if wave not in baseline:
                continue
            base_lat = baseline[wave]['lat']
            # repro_shift: jitter de "no reproducible" -- mueve TODO el
            # complejo junto (misma respuesta neural, timing inconsistente),
            # no una onda aislada.
            calc_lat = base_lat + lat_shift + repro_shift
            if wave == 'I':
                calc_lat = base_lat + lat_shift * 0.2 + repro_shift
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

            base_amp = baseline[wave]['amp']
            if wave == 'V':
                if intensity >= threshold:
                    db_range = 80 - threshold
                    if db_range == 0:
                        amp_factor = 1.0
                    else:
                        amp_factor = 0.05 + 0.95 * ((intensity - threshold) / db_range)
                else:
                    db_below = threshold - intensity
                    amp_factor = max(0.05 * (1 - db_below / 10), 0.001)
            else:
                disappear_offset = {'I': 70, 'II': 70,
                                    'III': threshold + 10, 'IV': threshold + 8}
                disappear_at = disappear_offset.get(wave, threshold + 10)
                if intensity >= disappear_at:
                    db_range = 80 - disappear_at
                    if db_range <= 0:
                        amp_factor = 1.0 if disappear_at >= 80 else 0.05
                    else:
                        amp_factor = 0.05 + 0.95 * ((intensity - disappear_at) / db_range)
                else:
                    db_below = disappear_at - intensity
                    amp_factor = max(0.05 * (1 - db_below / 10), 0.001)

            calc_amp = base_amp * amp_factor
            if desviaciones and wave in ['I', 'III', 'V']:
                key = f"onda_{wave}"
                if key in desviaciones:
                    calc_amp += desviaciones[key]['amp'] * amp_scale
            calc_amp = max(calc_amp, 0.001)

            if intensity >= 70:
                width_factor = 1.0
            elif intensity >= 50:
                width_factor = 1.0 + (70 - intensity) * 0.03
            else:
                width_factor = 1.6 + (50 - intensity) * 0.05

            modified[wave] = {
                'lat': calc_lat,
                'amp': calc_amp,
                'width': width_factor,
            }

        return modified, {w: True for w in ['I', 'II', 'III', 'IV', 'V']}

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
        if rate <= 15:
            if 'I' in values:
                values['I']['lat'] -= 0.35
                values['I']['amp'] *= 1.70
            if 'II' in values:
                values['II']['amp'] *= 1.50
            if 'III' in values:
                values['III']['lat'] -= 0.25
                values['III']['amp'] *= 1.50
            if 'IV' in values:
                values['IV']['amp'] *= 1.40
            if 'V' in values:
                values['V']['lat'] -= 0.35
                values['V']['amp'] *= 1.60
        elif 15 < rate <= 50:
            factor = (rate - 15) / 35
            if 'I' in values:
                values['I']['lat'] += -0.35 * (1 - factor)
                values['I']['amp'] *= 1.70 - 0.70 * factor
            if 'II' in values:
                values['II']['amp'] *= 1.50 - 0.50 * factor
            if 'III' in values:
                values['III']['lat'] += -0.25 * (1 - factor)
                values['III']['amp'] *= 1.50 - 0.50 * factor
            if 'IV' in values:
                values['IV']['amp'] *= 1.40 - 0.40 * factor
            if 'V' in values:
                values['V']['lat'] += -0.35 * (1 - factor)
                values['V']['amp'] *= 1.60 - 0.60 * factor
        else:
            if rate <= 70:
                factor = (rate - 50) / 20
            else:
                factor = min(1.0 + (rate - 70) / 30, 1.5)
            if 'I' in values:
                values['I']['lat'] += 0.40 * factor
                values['I']['amp'] *= max(1.0 - 0.70 * factor, 0.001)
            if 'III' in values:
                values['III']['lat'] += 0.40 * factor
                values['III']['amp'] *= max(1.0 - 0.50 * factor, 0.001)
            if 'V' in values:
                values['V']['lat'] += 0.50 * factor
                values['V']['amp'] *= max(1.0 - 0.50 * factor, 0.001)
            if 'II' in values:
                if rate >= 60:
                    values['II']['amp'] *= 0.05
                else:
                    df = (rate - 50) / 10
                    values['II']['amp'] *= max(1.0 - 0.95 * df, 0.05)
            if 'IV' in values:
                if rate >= 60:
                    values['IV']['amp'] *= 0.05
                else:
                    df = (rate - 50) / 10
                    values['IV']['amp'] *= max(1.0 - 0.95 * df, 0.05)

        if pathology == 'neural' and 10 < rate < 30:
            if 'II' in values:
                values['II']['amp'] *= 0.30
            if 'IV' in values:
                values['IV']['amp'] *= 0.30
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

    def apply_filters(self, y, filter_low, filter_high, fs=20000):
        """
        Solo butterworth pasa-bajo + pasa-alto.
        Los efectos morfológicos (ensanchamiento, drift) son parte
        del modelo de ruido, no del filtro.
        """
        nyq = fs / 2
        out = y.copy()

        if 0 < filter_low < nyq:
            low_n = min(filter_low / nyq, 0.99)
            order = 4 if filter_low >= 3000 else (5 if filter_low >= 2000 else 6)
            b, a = signal.butter(order, low_n, 'low')
            out = signal.filtfilt(b, a, out)

        if filter_high > 0:
            high_n = max(filter_high / nyq, 1e-4)
            high_n = min(high_n, 0.99)
            order = 6 if filter_high >= 150 else (5 if filter_high >= 50 else 4)
            b, a = signal.butter(order, high_n, 'high')
            out = signal.filtfilt(b, a, out)

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
        # Override de click por curso (ver core.app_config_store en el
        # cliente / AppConfig.php en el backend) -- se propaga aca para que
        # tanto el baseline del estimulo activo como el de click (usado para
        # escalar desviaciones) usen el mismo click "editado".
        click_override = case_config.get('normative_override') if case_config else None
        baseline = self.get_baseline_values(
            population, stimulus_config['stim'], pathway,
            freq=stimulus_config.get('freq'), click_override=click_override,
        )
        # Baseline de click (misma poblacion/via) para escalar desviaciones
        # cuando el estimulo activo no es click (ver calculate_wave_parameters).
        click_baseline = None
        if stimulus_config['stim'] != 'click':
            click_baseline = self.get_baseline_values(
                population, 'click', pathway, click_override=click_override,
            )

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

        # 8. Eje temporal
        t = np.linspace(0, 12, 500)

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
# Interfaz compatible con V2 (misma firma -> drop-in)
# ============================================================================

_generator = None


def _get_generator():
    global _generator
    if _generator is None:
        _generator = ABRGeneratorV3()
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
    Misma firma que V2. Genera curva ABR con modelo morfolgico realista.
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

    # Override de click por curso -- config del docente (ver AppConfig.php),
    # sincronizada al cliente en core.app_config_store bajo key generica
    # "normative_data.<examen>" (mismo mecanismo para P300/electrococleografia
    # a futuro). Un override propio del caso (si case_create.php llega a
    # exponerlo) manda por sobre el del curso.
    normative_override = preferences.get('normative_override') or \
        (app_config_store.get('normative_data.abr') or {}).get('click')

    case_config = {
        'desviaciones': preferences.get('desviaciones', {}),
        'fsp_puntos': preferences.get('fsp_puntos', {'800': 2.3, '2000': 2.8}),
        'umbral': preferences.get('umbral', preferences.get('th', 20)),
        'average_objetivo': preferences.get('average_objetivo', 2000),
        'repro_shift': var_repro,
        'normative_override': normative_override,
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
