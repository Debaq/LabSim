"""
VEMP Generator V1 - Modelo morfológico por suma de gaussianas.

Adaptación del pipeline de ABR_generator a VEMP (CVEMP/OVEMP/MVEMP).
Tres subtipos con picos clínicos reales (P13/N23 cervical, N10/P16 ocular,
P13/N23 masetero), ventana temporal más larga (35ms vs 12ms de ABR), peaks
más anchos (sigma ~0.4ms vs 0.2ms por ser respuesta electromiogénica, no
neural). Polaridad y rate con menos efectos que ABR porque el examen VEMP
es casi siempre monoaural, ~5 Hz, polaridad rarefacción fija.

Lo que un VEMP tiene y un ABR no, y por eso está modelado acá:

- La MORFOLOGÍA ES BIFÁSICA. P13 va hacia arriba y N23 hacia abajo (N10
  abajo y P16 arriba en el ocular): la inicial del pico ES su polaridad.
  El módulo sumaba dos gaussianas positivas y dibujaba dos jorobas del
  mismo lado, que no es un VEMP.
- La respuesta VIVE DE LA CONTRACCIÓN MUSCULAR. Sin ECM contraído no hay
  cVEMP, sin mirada superior no hay oVEMP: la amplitud escala con el EMG
  tónico del músculo (ver MANIOBRAS/emg_gain). Es el error clásico del
  alumno y hasta acá el generador asumía siempre contracción perfecta.
- La AMPLITUD CRECE SOBRE EL UMBRAL Y SATURA (~20 dB de SL). La fórmula
  vieja normalizaba por (80 - umbral) y con umbrales altos extrapolaba:
  umbral 85 a 100 dB devolvía 1930 µV, catorce veces la normativa.
- El RUIDO ES PROPORCIONAL A LA RESPUESTA del subtipo. El cVEMP ronda los
  150 µV y el oVEMP los 10: un ruido absoluto de 0.1 µV dejaba las dos
  curvas perfectas desde el primer barrido y la promediación no servía
  para nada.
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

SUBTIPOS = ['CVEMP', 'OVEMP', 'MVEMP']

# Defaults por subtipo -- los MISMOS de CaseBuilder::VEMP_DEFAULTS. Se usan
# para los casos viejos, que traían un solo subtipo configurado (ver
# case_for_subtipo).
SUBTIPO_DEFAULTS = {
    'CVEMP': {'umbral': 60, 'average_objetivo': 200},
    'OVEMP': {'umbral': 65, 'average_objetivo': 300},
    'MVEMP': {'umbral': 70, 'average_objetivo': 300},
}
REPRO_VAR_DEFAULT = 0.2

# Intensidad a la que está definida la normativa y ancho del crecimiento.
INTENSIDAD_REF = 80
# El VEMP crece sobre el umbral y satura: a 20 dB de SL ya está en la
# amplitud normativa. Fijo, y no (80 - umbral): esa normalización hacía que
# la amplitud a 80 dB fuera la misma con cualquier umbral (el campo no movía
# nada) y extrapolaba sin techo por encima de 80.
SL_SATURACION_DB = 20
# Pendiente latencia-intensidad: mucho más plana que la del ABR.
LAT_SLOPE_MS_10DB = 0.05

# Ventana de registro. El N23 cae a 23 ms, así que 35 ms es lo mínimo que
# muestra la respuesta completa.
VENTANA_MS = 35
N_PUNTOS = 800

# Maniobra del paciente por subtipo -> EMG tónico del músculo registrador,
# en µV RMS. La normativa está medida con el músculo contraído (EMG_REF):
# con el paciente relajado la respuesta no aparece, que es exactamente el
# error que el alumno tiene que aprender a no cometer.
#
# El primer valor de cada subtipo es la posición SIN contracción: es el
# default del control a propósito (no un valor "correcto" precargado).
MANIOBRAS = {
    'CVEMP': [
        ('Relajado (decúbito)', 8.0),
        ('Rotación cefálica', 55.0),
        ('Elevación de la cabeza', 95.0),
    ],
    'OVEMP': [
        ('Mirada al frente', 6.0),
        ('Mirada superior ~30°', 45.0),
    ],
    'MVEMP': [
        ('Mandíbula relajada', 5.0),
        ('Mordida sostenida', 60.0),
    ],
}
# EMG al que corresponde la amplitud normativa de cada subtipo.
EMG_REF = {'CVEMP': 55.0, 'OVEMP': 45.0, 'MVEMP': 60.0}
# Rango de EMG aceptable para dar el registro por válido (el equipo real
# muestra esta banda y rechaza barridos fuera de ella).
EMG_BANDA = {'CVEMP': (30.0, 150.0), 'OVEMP': (20.0, 120.0), 'MVEMP': (25.0, 140.0)}


def peak_sign(pico):
    """Polaridad del pico: la dice su inicial (p13 arriba, n23 abajo)."""
    return -1.0 if str(pico).lower().startswith('n') else 1.0


def select_population(age=None, gender=None):
    """Población normativa del paciente (claves de normative_data.json).

    gender: 0 = hombre, 1 = mujer (mismo criterio que cases.data['gender']).
    MISMO criterio que la vista previa del backend (public/js/case/vemp.js):
    la edad manda sobre el sexo, que solo separa a los adultos. Sin edad ->
    adult_female, que era el valor fijo que usaba el módulo antes de esto.
    """
    if age is None:
        return 'adult_female'
    try:
        age = float(age)
    except (TypeError, ValueError):
        return 'adult_female'
    if age < 18:
        return 'child'
    if age >= 65:
        return 'elderly'
    return 'adult_male' if str(gender) == '0' else 'adult_female'


def maniobras_de(subtipo):
    """Nombres de maniobra disponibles para el subtipo (orden del combo)."""
    return [nombre for nombre, _ in MANIOBRAS.get(subtipo, MANIOBRAS['CVEMP'])]


def emg_de_maniobra(subtipo, maniobra):
    """EMG tónico (µV RMS) que produce esa maniobra. Sin maniobra válida,
    la primera de la lista -- que es la posición SIN contracción."""
    opciones = MANIOBRAS.get(subtipo, MANIOBRAS['CVEMP'])
    for nombre, nivel in opciones:
        if nombre == maniobra:
            return nivel
    return opciones[0][1]


def emg_en_banda(subtipo, emg):
    """¿El EMG registrado alcanza para dar el registro por válido?"""
    lo, hi = EMG_BANDA.get(subtipo, EMG_BANDA['CVEMP'])
    return lo <= float(emg) <= hi


def case_for_subtipo(ear, subtipo):
    """El caso de UN VEMP: lo del subtipo + el `type`, que es del oído.

    cases.data['VEMP'][OD|OI] guarda la patología en la raíz del oído (es el
    órgano el que está lesionado) y todo lo demás por subtipo, bajo
    `subtipos` (ver CaseForm::parseVemp).

    Compatibilidad con casos guardados antes de que fueran tres: traían un
    solo `subtipo` con sus valores en la raíz del oído. Se los queda el
    subtipo que el caso declaraba y los otros dos arrancan en su default --
    MISMO criterio que CaseBuilder::caseDataToForm, para que la app y el
    editor lean el mismo caso viejo igual.

    Devuelve None si el oído no tiene VEMP configurado: sin datos reales no
    se genera nada (ver VempMainWindow.graph).
    """
    if not isinstance(ear, dict) or not ear:
        return None
    if subtipo not in SUBTIPO_PEAKS:
        subtipo = 'CVEMP'
    guardados = ear.get('subtipos')
    sub = None
    if isinstance(guardados, dict) and isinstance(guardados.get(subtipo), dict):
        sub = guardados[subtipo]
    elif str(ear.get('subtipo') or '').upper() == subtipo:
        sub = ear      # caso viejo: sus valores estaban en la raíz del oído
    sub = sub or {}

    default = SUBTIPO_DEFAULTS[subtipo]
    desviaciones = sub.get('desviaciones') if isinstance(sub.get('desviaciones'), dict) else {}
    return {
        'type': ear.get('type', 'normal'),
        'subtipo': subtipo,
        'peaks': list(SUBTIPO_PEAKS[subtipo]),
        'umbral': int(sub.get('umbral', default['umbral'])),
        'repro': bool(sub.get('repro', True)),
        'repro_var': float(sub.get('repro_var', REPRO_VAR_DEFAULT)),
        'average_objetivo': int(sub.get('average_objetivo', default['average_objetivo'])),
        # Solo los picos de ESTE subtipo: cVEMP y mVEMP comparten los
        # nombres (p13/n23) y en el shape nuevo cada uno trae los suyos.
        'desviaciones': {p: dict(desviaciones.get(p) or {}) for p in SUBTIPO_PEAKS[subtipo]},
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
        # Copia: el boost por sexo multiplicaba EL JSON EN MEMORIA, así que
        # cada llamada devolvía amplitudes un 10% más altas que la anterior.
        baseline = {p: dict(v) for p, v in baseline.items()}
        if population == 'adult_female' and 'physiological_modifiers' in self.norms:
            boost = self.norms['physiological_modifiers'].get('sex', {}).get('female_amp_boost', 1.0)
            for pico in baseline:
                baseline[pico]['amp'] *= boost
        return baseline

    @staticmethod
    def amp_reference(baseline):
        """Amplitud de referencia del subtipo: la del pico más grande.

        Es la escala de TODO lo demás (ruido, drift, caos de promediación).
        Sin esto el ruido era absoluto y el oVEMP (10 µV) salía tan limpio
        como el cVEMP (170 µV).
        """
        amps = [abs(v.get('amp', 0.0)) for v in (baseline or {}).values()]
        return max(amps) if amps else 1.0

    def calculate_wave_parameters(self, baseline, intensity, threshold,
                                  pathology, subtipo, desviaciones=None,
                                  repro_shift=0.0, emg_gain=1.0):
        """
        Pendiente VEMP latencia-intensidad es más plana que ABR (~0.05ms/10dB).
        VEMP usa sólo tone burst (no click) así que no aplica el escalado por
        estímulo de ABR.

        emg_gain: cuánto contrajo el paciente respecto de la contracción con
        la que está medida la normativa. Multiplica la amplitud entera, que
        es lo que hace un VEMP de verdad.
        """
        steps_from_ref = (INTENSIDAD_REF - intensity) / 10
        lat_shift = steps_from_ref * LAT_SLOPE_MS_10DB

        modified = {}
        peaks = SUBTIPO_PEAKS.get(subtipo, ['p13', 'n23'])

        for pico in peaks:
            if pico not in baseline:
                continue
            base_lat = baseline[pico]['lat']
            base_amp = baseline[pico]['amp']

            calc_lat = base_lat + lat_shift + repro_shift

            # Amplitud: crece con el nivel de sensación (intensidad sobre el
            # umbral) y satura; por debajo del umbral, piso de ruido.
            sl = intensity - threshold
            if sl >= 0:
                amp_factor = 0.05 + 0.95 * min(sl / SL_SATURACION_DB, 1.0)
            else:
                amp_factor = max(0.05 * (1 + sl / 10), 0.001)

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
                calc_lat += desviaciones[pico].get('lat', 0) or 0
                calc_amp += desviaciones[pico].get('amp', 0) or 0

            # La contracción del músculo, al final: escala la respuesta que
            # los números del caso describen, no la reemplaza.
            calc_amp *= emg_gain

            # La polaridad la dice la inicial del pico -- va acá, después de
            # las desviaciones (que el docente escribe en magnitud), igual
            # que en la vista previa del backend.
            calc_amp = max(abs(calc_amp), 0.001) * peak_sign(pico)
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
        """Suma de gaussianas por pico. La amplitud ya viene con signo
        (ver calculate_wave_parameters), así que el trazo sale bifásico:
        P13 arriba y N23 abajo, no dos jorobas del mismo lado."""
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

    def add_baseline_drift(self, t, amp_ref=1.0, amplitude=0.02):
        """Drift LF suave, proporcional a la respuesta del subtipo."""
        f1 = random.uniform(0.4, 1.2)
        f2 = random.uniform(0.15, 0.4)
        return amplitude * amp_ref * (np.sin(2 * np.pi * f1 * t / VENTANA_MS) +
                                      0.4 * np.sin(2 * np.pi * f2 * t / VENTANA_MS))

    def pink_noise(self, n, scale=1.0):
        white = np.random.normal(0, 1, n)
        fft = np.fft.rfft(white)
        freqs = np.fft.rfftfreq(n)
        fft[1:] /= np.sqrt(freqs[1:])
        fft[0] = 0
        pink = np.fft.irfft(fft, n)
        std = np.std(pink)
        return scale * pink / std if std > 0 else np.zeros(n)

    def add_emg_noise(self, t, current_avg, target_avg, impedance=3.0,
                      amp_ref=1.0, emg_ratio=1.0):
        """VEMP = EMG casi puro (respuesta muscular). Más EMG (HF), menos pink.

        El nivel es proporcional a la respuesta del subtipo (amp_ref) y a lo
        contraído que esté el músculo: contraer más levanta la respuesta,
        pero también el ruido del que hay que sacarla promediando.
        """
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

        # SNR ~ 1/sqrt(N): el residual baja con la raíz de los barridos.
        safe_target = max(target_avg, 1)
        snr_reduction = np.sqrt(max(current_avg, 1) / safe_target)
        snr_reduction = min(snr_reduction, 0.94)

        if impedance < 3:
            imp = 0.5
        elif impedance <= 5:
            imp = 1.0
        else:
            imp = 1.5

        # Ruido crudo: casi la mitad de la respuesta del subtipo. Con un
        # valor absoluto (0.10 µV) el cVEMP salía perfecto de entrada.
        base_amp = 0.45 * amp_ref * np.sqrt(max(emg_ratio, 0.05))
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
        amp_ref = self.amp_reference(baseline)

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

        # 6. Contracción del músculo registrador. Sin ella no hay respuesta.
        emg_level = float(technical_config.get('emg_uv', EMG_REF.get(subtipo, 55.0)))
        emg_ref = EMG_REF.get(subtipo, 55.0)
        emg_ratio = emg_level / emg_ref if emg_ref else 1.0
        # Techo 1.6: contraer más sube la respuesta, pero el músculo satura
        # (y el ruido sube igual, ver add_emg_noise).
        emg_gain = max(min(emg_ratio, 1.6), 0.0)

        # 7. Parámetros de ondas
        repro_shift = (case_config or {}).get('repro_shift', 0.0)
        values, waves_visible = self.calculate_wave_parameters(
            baseline, stimulus_config['int'], threshold, pathology, subtipo,
            desviaciones=desviaciones, repro_shift=repro_shift,
            emg_gain=emg_gain,
        )

        # Override por curso: aplica después de calculate_wave_parameters
        # pisando lat/amp con los del override del docente.
        # Shape {subtipo: {pico: {lat, amp}}}, la que guarda courses.php.
        # Antes se iteraba el dict entero como si fuera {pico: ...}, así que
        # el override del curso no llegaba nunca a ningún pico.
        if isinstance(baseline_override, dict):
            for pico, ovr in (baseline_override.get(subtipo) or {}).items():
                if pico in values and isinstance(ovr, dict):
                    if 'lat' in ovr:
                        values[pico]['lat'] = ovr['lat']
                    if 'amp' in ovr:
                        values[pico]['amp'] = abs(ovr['amp']) * peak_sign(pico)

        # 8. Eje temporal: VEMP llega hasta ~30ms (peak N23 a 23ms)
        t = np.linspace(0, VENTANA_MS, N_PUNTOS)

        # 9. Curva objetivo
        y_target = self.build_target_curve(t, values, subtipo)

        # 10. Drift LF
        y_drift = self.add_baseline_drift(t, amp_ref=amp_ref)

        # 11. Curva limpia
        y_clean = y_target + y_drift

        # 12. Growth por promediación
        growth = self.calculate_growth(current_avg, target_objetivo)
        if growth < 1.0:
            chaos_amp = (1 - growth) * 0.25 * amp_ref
            chaos = np.random.normal(0, max(chaos_amp, 1e-6), t.shape)
            chaos = signal.filtfilt(*signal.butter(3, 0.2, 'low'), chaos)
            y_signal = growth * y_clean + chaos
        else:
            y_signal = y_clean

        # 13. Ruido EMG
        y_noisy = y_signal + self.add_emg_noise(
            t, current_avg, target_avg,
            technical_config.get('impedance', 3.0),
            amp_ref=amp_ref, emg_ratio=emg_ratio,
        )

        # 14. Filtros
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
            'amp_ref': amp_ref,
            'emg_uv': emg_level,
            'emg_ratio': emg_ratio,
            'emg_ok': emg_en_banda(subtipo, emg_level),
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


def VEMP_Curve(actual_intencity, control_setting, case, repro_prev, prom, done,
               patient=None):
    """
    Genera curva VEMP. Misma firma que ABR_Curve.

    control_setting: dict con 'pol', 'rate', 'filter_down', 'filter_passhigh',
                     'average', 'subtipo' (CVEMP/OVEMP/MVEMP), 'freq',
                     'maniobra'.
    case: el VEMP de UN subtipo de UN oído -- lo arma case_for_subtipo() a
          partir de cases.data['VEMP'][OD|OI], que guarda `type` en la raíz
          del oído y el resto bajo `subtipos`.
    prom: tupla (current_avg_rel, target_avg) -- misma convención que ABR.
    patient: cases.data del paciente en atención; de ahí salen edad y sexo
             para elegir la población normativa (antes: siempre mujer adulta).

    Devuelve (x, y, dx, dy, var_repro, metadata).
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

    freq = str(control_setting.get('freq', '500Hz'))
    stimulus_config = {
        'stim': 'tone_burst',
        'freq': freq,
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
        'impedance': float(control_setting.get('impedance', 3.0)),
        'transducer': 'insert_earphone',
        # La maniobra del paciente ES un parámetro técnico del registro:
        # decide cuánto EMG hay bajo el electrodo (ver MANIOBRAS).
        'emg_uv': emg_de_maniobra(subtipo, control_setting.get('maniobra')),
    }

    # Reproducibilidad: jitter igual que ABR
    repro_var = case.get('repro_var', REPRO_VAR_DEFAULT)
    if not case.get('repro', True):
        var_repro = random.uniform(-repro_var, repro_var) if repro_prev == 0 \
                    else -repro_prev + random.uniform(-repro_var / 2, repro_var / 2)
    else:
        var_repro = 0

    # Ratio/override por curso (genérico, mismo mecanismo que ABR).
    baseline_override = app_config_store.get('normative_data.vemp')

    case_config = {
        'desviaciones': case.get('desviaciones', {}),
        'umbral': case.get('umbral', SUBTIPO_DEFAULTS[subtipo]['umbral']),
        'average_objetivo': case.get('average_objetivo',
                                     SUBTIPO_DEFAULTS[subtipo]['average_objetivo']),
        'repro_shift': var_repro,
        'baseline_override': baseline_override,
    }

    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'))

    t, y, metadata = generator.generate_curve(
        population=population,
        pathology=pathology,
        subtipo=subtipo,
        stimulus_config=stimulus_config,
        technical_config=technical_config,
        case_config=case_config,
    )

    dx = t.copy()
    dy = y.copy()
    return t, y, dx, dy, var_repro, metadata
