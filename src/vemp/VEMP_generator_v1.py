"""
VEMP Generator V1 - Modelo morfológico por suma de gaussianas.

Adaptación del pipeline de ABR_generator_v3 a VEMP (CVEMP/OVEMP/MVEMP).
Tres subtipos con picos clínicos reales (P13/N23 cervical, N10/P16 ocular,
P13/N23 masetero), ventana temporal más larga (35ms vs 12ms de ABR), peaks
más anchos (sigma ~0.4ms vs 0.2ms por ser respuesta electromiogénica, no
neural). Polaridad y rate con menos efectos que ABR porque el examen VEMP
es casi siempre monoaural, ~5 Hz, polaridad rarefacción fija.
"""

import json
import random
import numpy as np
import scipy.signal as signal
from core.base import context
from core import app_config_store


# Anchos base (sigma ms) por pico VEMP. Picos mioeléctricos son más anchos
# que neurales. P13 y P16 similares, N23 un poco más ancho (descenso del
# potencial muscular).
WAVE_SIGMA = {
    'p13': 0.40,
    'n23': 0.45,
    'n10': 0.35,
    'p16': 0.40,
}


# Picos por subtipo (orden de aparición, polaridad esperada).
SUBTIPO_PEAKS = {
    'CVEMP': ['p13', 'n23'],   # cervical, SCM
    'OVEMP': ['n10', 'p16'],   # ocular, oblicuo inferior
    'MVEMP': ['p13', 'n23'],   # masetero (experimental)
}


class VEMPGeneratorV1:
    """Generador de curvas VEMP con morfología realista."""

    def __init__(self, normative_data_path=None):
        if normative_data_path is None:
            normative_data_path = context.get_resource('vemp/normative_data.json')
        with open(normative_data_path, 'r', encoding='utf-8') as f:
            self.norms = json.load(f)

    # =====================================================================
    # VALORES NORMATIVOS
    # =====================================================================

    def get_baseline_values(self, population, subtipo, freq='500Hz'):
        """
        Devuelve dict {pico: {'lat': float, 'amp': float}} a 80 dB SPL
        tone burst, vía aérea, para la población/subtipo dados.

        Poblaciones disponibles: adult_male / adult_female / child / elderly.
        Para una población que no tenga el subtipo pedido, cae a adult_female
        como fallback (con un warning implícito en amp 0 silencioso).
        """
        pop_data = self.norms['populations'].get(population)
        if pop_data is None:
            pop_data = self.norms['populations']['adult_female']
        baseline = (pop_data.get('air_conduction', {})
                        .get('tone_burst', {})
                        .get(freq, {})
                        .get(subtipo, {}))
        if not baseline:
            # Fallback final: adult_female / 500Hz / subtipo
            baseline = (self.norms['populations']['adult_female']
                            ['air_conduction']['tone_burst']['500Hz']
                            .get(subtipo, {}))
        # Boost por sexo (mujeres tienen amplitudes un poco más altas).
        if population == 'adult_female' and 'physiological_modifiers' in self.norms:
            boost = self.norms['physiological_modifiers'].get('sex', {}).get('female_amp_boost', 1.0)
            for pico in baseline:
                baseline[pico]['amp'] *= boost
        return baseline

    def calculate_wave_parameters(self, baseline, intensity, threshold,
                                  pathology, subtipo, desviaciones=None,
                                  repro_shift=0.0):
        """
        Pendiente VEMP latencia-intensidad es más plana que ABR (~0.05ms/10dB).
        VEMP usa sólo tone burst (no click) así que no aplica el escalado por
        estímulo de ABR.
        """
        steps_from_80 = (80 - intensity) / 10
        lat_shift = steps_from_80 * 0.05

        modified = {}
        peaks = SUBTIPO_PEAKS.get(subtipo, ['p13', 'n23'])

        for pico in peaks:
            if pico not in baseline:
                continue
            base_lat = baseline[pico]['lat']
            base_amp = baseline[pico]['amp']

            calc_lat = base_lat + lat_shift + repro_shift

            # Amplitud: lineal con (intensidad - umbral), piso de ruido.
            if intensity >= threshold:
                db_range = max(80 - threshold, 1)
                amp_factor = 0.05 + 0.95 * ((intensity - threshold) / db_range)
            else:
                db_below = threshold - intensity
                amp_factor = max(0.05 * (1 - db_below / 10), 0.001)

            calc_amp = base_amp * amp_factor

            # Pathology modifiers
            path_mod = self.norms.get('pathology_modifiers', {}).get(pathology, {})
            if pathology == 'sacular' and subtipo == 'CVEMP':
                if pico == 'p13':
                    calc_amp *= path_mod.get('cvemp_p13_amp_reduction', 0.25)
                    calc_lat += path_mod.get('cvemp_p13_lat_prolongation_ms', 1.5)
                elif pico == 'n23':
                    calc_amp *= path_mod.get('cvemp_n23_amp_reduction', 0.30)
            elif pathology == 'utricular' and subtipo == 'OVEMP':
                if pico == 'n10':
                    calc_amp *= path_mod.get('ovemp_n10_amp_reduction', 0.20)
                    calc_lat += path_mod.get('ovemp_n10_lat_prolongation_ms', 1.2)
                elif pico == 'p16':
                    calc_amp *= path_mod.get('ovemp_p16_amp_reduction', 0.25)
            elif pathology == 'neural':
                calc_amp *= path_mod.get('amplitude_reduction_uniform', 0.40)
                if pico == peaks[1]:  # segundo pico (N23/P16)
                    calc_lat += path_mod.get('interpeak_prolongation_ms', 1.5)

            # Desviaciones del caso (docente las editó en case_create.php).
            # Shape: {'p13': {'lat': X, 'amp': Y}, ...}
            if desviaciones and pico in desviaciones:
                calc_lat += desviaciones[pico].get('lat', 0)
                calc_amp += desviaciones[pico].get('amp', 0)

            calc_amp = max(calc_amp, 0.001)
            modified[pico] = {
                'lat': calc_lat,
                'amp': calc_amp,
                'width': 1.0 if intensity >= 70 else 1.0 + (70 - intensity) * 0.04,
            }

        return modified, {p: True for p in peaks}

    # =====================================================================
    # MODELO MORFOLÓGICO
    # =====================================================================

    @staticmethod
    def _gaussian(t, center, amp, sigma):
        return amp * np.exp(-0.5 * ((t - center) / sigma) ** 2)

    def build_target_curve(self, t, values, subtipo):
        """Suma de gaussianas por pico, sin CM ni trough post-VI (VEMP es más simple)."""
        y = np.zeros_like(t)
        peaks = SUBTIPO_PEAKS.get(subtipo, ['p13', 'n23'])
        for pico in peaks:
            if pico not in values:
                continue
            v = values[pico]
            sigma = WAVE_SIGMA.get(pico, 0.40) * v.get('width', 1.0)
            y += self._gaussian(t, v['lat'], v['amp'], sigma=sigma)
        return y

    # =====================================================================
    # ARTEFACTOS Y RUIDO
    # =====================================================================

    def add_baseline_drift(self, t, amplitude=0.04):
        """Drift LF suave, igual que ABR."""
        f1 = random.uniform(0.4, 1.2)
        f2 = random.uniform(0.15, 0.4)
        return amplitude * (np.sin(2 * np.pi * f1 * t / 35) +
                            0.4 * np.sin(2 * np.pi * f2 * t / 35))

    def pink_noise(self, n, scale=1.0):
        white = np.random.normal(0, 1, n)
        fft = np.fft.rfft(white)
        freqs = np.fft.rfftfreq(n)
        fft[1:] /= np.sqrt(freqs[1:])
        fft[0] = 0
        pink = np.fft.irfft(fft, n)
        std = np.std(pink)
        return scale * pink / std if std > 0 else np.zeros(n)

    def add_emg_noise(self, t, current_avg, target_avg, impedance=3.0):
        """VEMP = EMG casi puro (respuesta muscular). Más EMG (HF), menos pink."""
        n = len(t)
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

        pink = self.pink_noise(n, 1.0) * 0.20  # mucho menos pink que ABR
        noise = 0.80 * emg + 0.20 * pink

        # SNR ~ 1/sqrt(N), piso 0.92 como ABR
        safe_target = max(target_avg, 1)
        snr_reduction = np.sqrt(max(current_avg, 1) / safe_target)
        snr_reduction = min(snr_reduction, 0.92)

        if impedance < 3:
            imp = 0.5
        elif impedance <= 5:
            imp = 1.0
        else:
            imp = 1.5

        base_amp = 0.10  # VEMP es más ruidoso que ABR (EMG)
        amp = base_amp * (1.0 - snr_reduction) * imp
        return noise * amp

    # =====================================================================
    # FILTROS
    # =====================================================================

    def apply_filters(self, y, filter_low, filter_high, fs=20000):
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

    def calculate_growth(self, current_avg, target_avg):
        if target_avg <= 0:
            return 0.0
        ratio = current_avg / target_avg
        return max(0.0, min(1.0, ratio))

    # =====================================================================
    # ORQUESTADOR
    # =====================================================================

    def generate_curve(self, population, pathology, subtipo,
                        stimulus_config, technical_config, case_config=None):
        # 1. Baseline normativo
        freq = stimulus_config.get('freq', '500Hz')
        baseline = self.get_baseline_values(population, subtipo, freq=freq)

        # 2. Override por curso (key 'normative_data.vemp' en app_config_store).
        # Mismo patrón genérico que ABR item 8 -- el docente puede ajustar
        # baselines absolutos por pico desde la UI admin.
        baseline_override = (case_config or {}).get('baseline_override')

        # 3. Umbral
        if case_config and 'umbral' in case_config:
            threshold = case_config['umbral']
        else:
            threshold = self.norms['pathology_modifiers'].get(
                pathology, {}).get('threshold_range', [0, 25])[0]

        # 4. Desviaciones del caso (shape {'p13':{'lat','amp'},...})
        desviaciones = (case_config or {}).get('desviaciones')

        # 5. Promediación
        current_avg = stimulus_config['current_avg']
        target_avg = stimulus_config['average']
        target_objetivo = (case_config or {}).get('average_objetivo') or target_avg

        # 6. Parámetros de ondas
        repro_shift = (case_config or {}).get('repro_shift', 0.0)
        values, waves_visible = self.calculate_wave_parameters(
            baseline, stimulus_config['int'], threshold, pathology, subtipo,
            desviaciones=desviaciones, repro_shift=repro_shift,
        )

        # Override por curso: aplica después de calculate_wave_parameters
        # pisando lat/amp con los del override del docente.
        if baseline_override:
            for pico, ovr in baseline_override.items():
                if pico in values:
                    if 'lat' in ovr:
                        values[pico]['lat'] = ovr['lat']
                    if 'amp' in ovr:
                        values[pico]['amp'] = ovr['amp']

        # 7. Eje temporal: VEMP llega hasta ~30ms (peak N23 a 23ms)
        t = np.linspace(0, 35, 800)

        # 8. Curva objetivo
        y_target = self.build_target_curve(t, values, subtipo)

        # 9. Drift LF
        y_drift = self.add_baseline_drift(t)

        # 10. Curva limpia
        y_clean = y_target + y_drift

        # 11. Growth por promediación
        growth = self.calculate_growth(current_avg, target_objetivo)
        if growth < 1.0:
            chaos_amp = (1 - growth) * 0.4
            chaos = np.random.normal(0, chaos_amp, t.shape)
            chaos = signal.filtfilt(*signal.butter(3, 0.2, 'low'), chaos)
            y_signal = growth * y_clean + chaos
        else:
            y_signal = y_clean

        # 12. Ruido EMG
        y_noisy = y_signal + self.add_emg_noise(
            t, current_avg, target_avg,
            technical_config.get('impedance', 3.0),
        )

        # 13. Filtros
        y_final = self.apply_filters(
            y_noisy,
            float(stimulus_config.get('filter_down', 1500)),
            float(stimulus_config.get('filter_passhigh', 10)),
        )

        return t, y_final, {
            'population': population,
            'pathology': pathology,
            'subtipo': subtipo,
            'waves_visible': waves_visible,
            'current_avg': current_avg,
            'target_avg': target_avg,
            'growth': growth,
        }


# ============================================================================
# Interfaz pública (misma firma que ABR_Curve para que el orquestador la use
# de la misma forma).
# ============================================================================

_generator = None


def _get_generator():
    global _generator
    if _generator is None:
        _generator = VEMPGeneratorV1()
    return _generator


def VEMP_Curve(actual_intencity, control_setting, case, repro_prev, prom, done):
    """
    Genera curva VEMP. Misma firma que ABR_Curve.

    control_setting: dict con 'pol', 'rate', 'filter_down', 'filter_passhigh',
                     'average', 'subtipo' (CVEMP/OVEMP/MVEMP).
    case: dict con 'type', 'repro', 'repro_var', 'umbral', 'average_objetivo',
          'desviaciones' (shape {'p13':{'lat','amp'},...}).
    prom: tupla (current_avg_rel, target_avg) -- misma convención que ABR.
    """
    generator = _get_generator()

    subtipo = control_setting.get('subtipo', 'CVEMP')
    if subtipo not in SUBTIPO_PEAKS:
        subtipo = 'CVEMP'

    pathology_map = {
        'normal': 'normal',
        'sacular': 'sacular',
        'utricular': 'utricular',
        'neural': 'neural',
    }
    pathology = pathology_map.get(case.get('type', 'normal'), 'normal')

    if done and prom[0] == 0:
        current_averages = prom[1]
    elif prom[0] <= 1.0:
        current_averages = prom[0] * prom[1]
    else:
        current_averages = prom[0] * 2.5

    target_averages = prom[1]
    if current_averages >= target_averages:
        current_averages = target_averages

    stimulus_config = {
        'stim': 'tone_burst',
        'freq': '500Hz',
        'pol': control_setting.get('pol', 'Rarefacción'),
        'int': actual_intencity,
        'rate': control_setting.get('rate', 5.0),
        'filter_down': float(control_setting.get('filter_down', 1500)),
        'filter_passhigh': float(control_setting.get('filter_passhigh', 10)),
        'average': target_averages,
        'current_avg': current_averages,
        'pathway': 'air_conduction',
    }

    technical_config = {
        'impedance': 3.0,
        'transducer': 'insert_earphone',
    }

    # Reproducibilidad: jitter igual que ABR
    repro_var = case.get('repro_var', 0.2)
    if not case.get('repro', True):
        var_repro = random.uniform(-repro_var, repro_var) if repro_prev == 0 \
                    else -repro_prev + random.uniform(-repro_var / 2, repro_var / 2)
    else:
        var_repro = 0

    # Ratio/override por curso (genérico, mismo mecanismo que ABR).
    baseline_override = app_config_store.get('normative_data.vemp')

    case_config = {
        'desviaciones': case.get('desviaciones', {}),
        'umbral': case.get('umbral', 60),
        'average_objetivo': case.get('average_objetivo', 200),
        'repro_shift': var_repro,
        'baseline_override': baseline_override,
    }

    t, y, metadata = generator.generate_curve(
        population='adult_female',
        pathology=pathology,
        subtipo=subtipo,
        stimulus_config=stimulus_config,
        technical_config=technical_config,
        case_config=case_config,
    )

    dx = t.copy()
    dy = y.copy()
    return t, y, dx, dy, var_repro
