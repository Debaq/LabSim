"""Generador de los potenciales de latencia media y tardía (MLR, CAEP,
P300 y MMN).

Separado del de ABR por lo mismo que el ECochG (ver ECochG_generator): el
equipo se comparte --electrodos, impedancias, red eléctrica, filtros,
promediador-- y se reusa desde ABRGenerator; lo que cambia es el flujo:

- Se registran VARIOS canales a la vez (C3/Cz/C4 o Fz/Cz/Pz) con el mismo
  barrido, así que el ruido de fondo es en parte común a los canales.
- El ruido no es el del ABR. A 100-3000 Hz lo que queda del EEG es casi
  blanco y de décimas de uV; a 1-30 Hz el EEG de fondo es de decenas de uV
  con su espectro 1/f y el alfa, y eso es lo que hace que un potencial
  tardío necesite 150 barridos y no 2000. Se genera acá con ese espectro y
  con el mismo modelo de promediación por bloques del ABR (la respuesta no
  crece, el ruido baja como 1/raíz de N).
- Parpadeos: en los tardíos son el artefacto principal (100-200 uV en Fz).
  Con el rechazo bien puesto se descartan y cuestan barridos; con el
  rechazo muy alto entran al promedio como ondas lentas.
- En el oddball el frecuente y el raro se promedian por separado, cada uno
  con sus barridos. La diferencia de la MMN tiene el ruido de los dos: con
  pocos desviantes no se ve, que es la lección.

Sin bloque `Central` en el caso no se registra nada (ver cortical.case_params).
"""
import numpy as np

from abr import cortical
from abr.ABR_generator import (AIR_MAX_OUTPUT_DB, PATHOLOGY_MAP, STIM_MAP,
                               NO_RESPONSE_DB, _get_generator,
                               default_settings, select_population)
from abr.protocols import get_protocol
from core.rng import case_fingerprint, stable_seed


# EEG de fondo de UN barrido, uV RMS entre 1 y 30 Hz, adulto despierto en
# Cz. Es lo que fija cuántos barridos hacen falta: con 150 el residual queda
# en ~1 uV contra un N1-P2 de ~9.
EEG_UV = 12.0
# Pendiente del espectro de amplitud del EEG (potencia 1/f^(2*pendiente)).
EEG_SLOPE = 0.75
# Pico alfa: fracción de la potencia de 1-30 Hz que se suma alrededor de
# 10 Hz (ojos abiertos; con somnolencia crece).
ALPHA_SHARE = 0.25
# Actividad muscular de un barrido, uV RMS entre 30 y 300 Hz, con el
# cuello relajado. Es lo que ensucia el MLR y lo que la tensión cervical
# (la misma que hace el PAM) aumenta.
EMG_UV = 1.5
# Correlación del ruido entre canales: el EEG de fondo es en buena parte
# común a electrodos vecinos.
CHANNEL_CORRELATION = 0.5
# Ruido por edad y estado (multiplica el EEG): el niño tiene más EEG de
# fondo; dormido domina el delta.
EEG_CHILD_FACTOR = 1.5
EEG_STATE_FACTOR = {'despierto': 1.0, 'somnoliento': 1.15, 'dormido': 1.4,
                    'sedado': 1.25}

# Parpadeos: probabilidad por barrido (depende del largo de la época) y
# amplitud en Fz. Los canales de atrás los ven menos.
BLINK_PER_SECOND = 0.25
BLINK_UV = 150.0
BLINK_TOPO = {'Fz': 1.0, 'Cz': 0.5, 'Pz': 0.25, 'C3': 0.35, 'C4': 0.35}
# Banda del parpadeo (Hz): una onda lenta de un cuarto de segundo.
BLINK_BAND_HZ = 4.0

# Promediación por bloques, como ABRGenerator.averaged_noise: pares de
# bloques A/B (subpromedios pares e impares), cada uno con su sorteo. El
# trazo converge solo a medida que entran bloques nuevos.
NOISE_PAIRS = 16
# Largo con el que se sortea el ruido de cada bloque: tiene que entrar el
# EEG lento (1 Hz) aunque la época sea de 100 ms.
NOISE_SPAN_MS = 1000.0

# Ventana del FSP por prueba (ms): donde está la respuesta que se lee.
FSP_WINDOW_MS = {'MLR': (12.0, 60.0), 'CAEP': (40.0, 300.0),
                 'P300': (200.0, 600.0), 'MMN': (100.0, 300.0)}



def reference_of(montage):
    """'earlobe' o 'mastoid': dónde está la referencia de ese montaje.

    El MLR se hace con referencia en el lóbulo (menos PAM); el equipo llega
    del ABR con mastoides y cambiarlo es parte del protocolo.
    """
    return 'earlobe' if 'earlobe' in str(montage or '') else 'mastoid'

# Fracción de raros del oddball, de rutina.
DEFAULT_RARE_PCT = 20.0


def _spectrum(f, test, central, edad, inquietud):
    """Amplitud espectral (no normalizada) del ruido de un barrido."""
    f = np.asarray(f, dtype=float)
    # Potencia 1/f^1.5: el EEG de fondo cae rápido sobre 10 Hz, y por eso
    # el MLR (10-300 Hz) se promedia con mucho menos ruido que un tardío.
    eeg = np.maximum(f, 0.3) ** -EEG_SLOPE
    eeg[f < 0.2] = 0.0
    banda = (f >= 1.0) & (f <= 30.0)
    df = f[1] - f[0] if len(f) > 1 else 1.0
    pot_banda = float(np.sum(eeg[banda] ** 2) * df) or 1.0
    estado = central['estado']
    alfa_share = ALPHA_SHARE * (1.6 if estado == 'somnoliento' else
                                0.3 if estado in ('dormido', 'sedado') else 1.0)
    alfa = np.exp(-0.5 * ((f - 10.0) / 1.5) ** 2)
    pot_alfa = float(np.sum(alfa[banda] ** 2) * df) or 1.0
    escala = EEG_UV * (EEG_CHILD_FACTOR if edad < 10 else 1.0) \
        * EEG_STATE_FACTOR.get(estado, 1.0)
    p_eeg = escala ** 2 * (eeg ** 2 / pot_banda
                           + alfa_share * alfa ** 2 / pot_alfa)
    emg_uv = EMG_UV * (0.5 + float(central['tension_cervical'])) \
        * (1.0 + 0.5 * float(inquietud or 0.0))
    emg = 1.0 / (1.0 + np.exp(-(f - 25.0) / 4.0))
    emg[f > 1500.0] = 0.0
    tramo = (f >= 30.0) & (f <= 300.0)
    pot_emg = float(np.sum(emg[tramo] ** 2) * df) or 1.0
    p_emg = emg_uv ** 2 * emg ** 2 / pot_emg
    return np.sqrt(p_eeg + p_emg)


def _colored(rng, amp, n_fft, df):
    """Una realización de ruido gaussiano con esa amplitud espectral.

    La potencia de cada bin es amp^2 * df repartida entre seno y coseno (y
    entre la frecuencia positiva y su espejo): la varianza que sale es la
    integral del espectro, sin normalizar a mano.
    """
    re = rng.standard_normal(len(amp))
    im = rng.standard_normal(len(amp))
    X = amp * np.sqrt(df / 4.0) * (re + 1j * im) * n_fft
    return np.fft.irfft(X, n_fft)


class CorticalGenerator:
    """Registro de MLR, CAEP, P300 y MMN con el equipo del ABR."""

    def __init__(self, abr=None):
        self.abr = abr or _get_generator()
        self._cache_key = None
        self._cache = {}

    # ------------------------------------------------------------------
    # Ruido
    # ------------------------------------------------------------------

    def _block(self, key, j, n, fs, spectrum_args, canales):
        """Ruido unitario del bloque j: {'eeg': (canales, n), 'blink': (n,)}.

        Se guarda por captura: cada tick vuelve a armar la curva entera y
        sortear de nuevo todos los bloques sería lo más caro del registro.
        """
        if self._cache_key != key[:-1]:
            self._cache_key = key[:-1]
            self._cache = {}
        clave = (key[-1], j)
        if clave in self._cache:
            return self._cache[clave]
        n_fft = 1 << int(np.ceil(np.log2(max(n, NOISE_SPAN_MS * fs / 1000.0))))
        f = np.fft.rfftfreq(n_fft, 1.0 / fs)
        df = f[1] - f[0]
        amp = _spectrum(f, *spectrum_args)
        rng = np.random.default_rng(stable_seed(*key, j))
        comun = _colored(rng, amp, n_fft, df)[:n]
        rho = CHANNEL_CORRELATION
        eeg = np.array([np.sqrt(rho) * comun
                        + np.sqrt(1 - rho) * _colored(rng, amp, n_fft, df)[:n]
                        for _ in canales])
        lento = np.where(f <= BLINK_BAND_HZ, 1.0, 0.0)
        lento[0] = 0.0
        pot = float(np.sum(lento ** 2) * df) or 1.0
        blink = _colored(rng, lento / np.sqrt(pot), n_fft, df)[:n]
        self._cache[clave] = {'eeg': eeg, 'blink': blink}
        return self._cache[clave]

    def averaged(self, key, n_accepted, target, n, fs, spectrum_args,
                 canales, blink_uv):
        """(promedio, sub_a, sub_b) del ruido con n_accepted barridos.

        Cada uno es (canales, n) en uV. Mismo esquema que el ABR: pares de
        bloques A/B de B barridos; con n barridos entraron k pares y el
        residual queda escalado a sigma/raíz(n) exacto.
        """
        n_acc = max(float(n_accepted), 1.0)
        barridos_bloque = max(float(target) / (2 * NOISE_PAIRS), 1.0)
        k = int(np.clip(np.ceil(n_acc / (2 * barridos_bloque)), 1, NOISE_PAIRS))
        topo = np.array([BLINK_TOPO.get(c, 0.3) for c in canales])[:, None]
        sumas = []
        for par in (0, 1):
            acc = np.zeros((len(canales), n))
            for j in range(k):
                b = self._block(key, 2 * j + par, n, fs, spectrum_args, canales)
                acc += b['eeg'] + blink_uv * topo * b['blink']
            sumas.append(acc / np.sqrt(k))
        mitad = max(n_acc / 2.0, 0.5)
        sub_a = sumas[0] / np.sqrt(mitad)
        sub_b = sumas[1] / np.sqrt(mitad)
        return (sub_a + sub_b) / 2.0, sub_a, sub_b, k

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------

    def generate_curve(self, test, side, population, pathology,
                       stimulus_config, technical_config, case_config,
                       central, edad):
        abr = self.abr
        canales = cortical.CHANNELS[test]
        lectura = cortical.READ_CHANNEL[test]
        oddball = test in cortical.ODDBALL_TESTS

        if float(stimulus_config['int']) > AIR_MAX_OUTPUT_DB:
            stimulus_config = dict(stimulus_config, int=AIR_MAX_OUTPUT_DB)
        nivel = float(stimulus_config['int'])

        window_ms = float(technical_config.get('window_ms')
                          or get_protocol(test).window_ms)
        fs = cortical.SAMPLES_PER_MS[test] * 1000.0
        n = max(int(round(window_ms * fs / 1000.0)) + 1, 64)
        t = np.linspace(0.0, window_ms, n)
        fs = (n - 1) / (window_ms / 1000.0)

        seed_key = (case_config or {}).get('seed_key', '')
        capture_id = (case_config or {}).get('capture_id', '')
        rng = np.random.default_rng(stable_seed(
            seed_key, capture_id, test, side, stimulus_config['label'],
            nivel, stimulus_config['rate'], stimulus_config['filter_down'],
            stimulus_config['filter_passhigh'],
            technical_config.get('montage'),
        ))

        rare_label = technical_config.get('oddball_rare') or 'Burst 2 kHz'
        rare_pct = float(technical_config.get('oddball_pct')
                         or DEFAULT_RARE_PCT)
        rare_fraction = float(np.clip(rare_pct / 100.0, 0.01, 0.5))

        umbral = abr.case_threshold(case_config, stimulus_config,
                                    'air_conduction', pathology)
        sl = nivel - umbral if umbral < NO_RESPONSE_DB else -1.0

        datos = central is not None
        ctx = {
            'rate': float(stimulus_config['rate']),
            'refractory': cortical.refractory_factor(test,
                                                     stimulus_config['rate']),
            'sl': cortical.sl_factor(test, sl),
            'stim_lat': cortical.stim_latency(stimulus_config['label']),
            'deviance': (cortical.deviance(stimulus_config['label'], rare_label)
                         if oddball else 0.0),
            'rare_fraction': rare_fraction,
            # Etapa de sueño del niño: cambia de una captura a otra.
            'sleep_draw': float(rng.uniform(0.0, 1.0)),
            'tarea': stimulus_config.get('tarea') or 'ninguna',
        }
        if datos:
            traces = cortical.build_traces(test, t, edad, central, side, ctx)
        else:
            traces = {'main': {c: np.zeros_like(t) for c in canales},
                      'overlays': ({'frecuente': {c: np.zeros_like(t)
                                                  for c in canales}}
                                   if oddball else {})}
            if test == 'MMN':
                traces['overlays']['raro'] = {c: np.zeros_like(t)
                                              for c in canales}

        # Lo que no es la respuesta pero está en el registro.
        referencia = reference_of(technical_config.get('montage'))
        tension = float((central or {}).get('tension_cervical', 0.3))
        pam = (cortical.pam_curve(t, referencia, tension, nivel, rng)
               if test == 'MLR' and datos else np.zeros_like(t))

        hay_registro, sin_tierra, imp_max, desbalance = abr.electrode_state(
            technical_config)
        clamp = (bool(technical_config.get('tube_clamped'))
                 and technical_config.get('transducer',
                                          'insert_earphone') == 'insert_earphone')
        if not datos:
            hay_registro = False

        # Barridos: rechazo de artefactos con el EEG de ESTA banda.
        inquietud = float((case_config or {}).get('inquietud') or 0.0)
        spectrum_args = (test, central or cortical.CASE_DEFAULTS, edad,
                         inquietud)
        hp = float(stimulus_config['filter_passhigh'])
        lp = float(stimulus_config['filter_down'])
        notch = float(technical_config.get('notch_hz') or 0.0)
        pendiente = technical_config.get('filter_slope')
        imp_factor = abr.impedance_noise_factor(imp_max) / \
            abr.impedance_noise_factor(2.0)
        key_base = (seed_key, capture_id, test, side, window_ms, fs,
                    repr(spectrum_args[1]), round(edad, 2), inquietud)
        muestra = self._block(key_base + ('frecuente',), 0, n, fs,
                              spectrum_args, canales)['eeg'][0]
        sigma_banda = float(np.std(abr.apply_filters(
            muestra * imp_factor, lp, hp, fs, slope_db=pendiente)))
        rechazo = abr.effective_reject_uv(technical_config) or 0.0
        p_parpadeo = float(np.clip(BLINK_PER_SECOND * window_ms / 1000.0,
                                   0.0, 0.5))
        if test == 'MLR' or not datos:
            p_parpadeo *= 0.3
        if rechazo:
            razon = rechazo / max(3.0 * sigma_banda, 1e-6)
            aceptacion = float(1.0 - np.exp(-razon ** 3))
            # El parpadeo se ve con cualquier filtro: es de 150 uV.
            parpadeo_rechazado = rechazo < 0.8 * BLINK_UV
        else:
            aceptacion, parpadeo_rechazado = 1.0, False
        if parpadeo_rechazado:
            aceptacion *= 1.0 - p_parpadeo
            blink_uv = 0.0
        else:
            blink_uv = BLINK_UV * np.sqrt(p_parpadeo)
        aceptacion = max(aceptacion, 0.02)

        current_avg = float(stimulus_config['current_avg'])
        target_avg = float(stimulus_config['average'])
        aceptados = current_avg * aceptacion
        if not hay_registro or clamp:
            for grupo in (traces['main'], *traces['overlays'].values()):
                for c in grupo:
                    grupo[c] = np.zeros_like(t)
            pam = np.zeros_like(t)

        def promedio(cond, fraccion):
            barridos = max(aceptados * fraccion, 1.0)
            ruido, a, b, k = self.averaged(
                key_base + (cond,), barridos, target_avg * fraccion, n, fs,
                spectrum_args, canales, blink_uv)
            return ruido * imp_factor, a * imp_factor, b * imp_factor, k

        red_coh = abr.mains_interference(t, sin_tierra, desbalance, rng, notch)

        def registrar(senial, ruido):
            return {c: abr.apply_filters(senial[c] + ruido[i] + red_coh,
                                         lp, hp, fs, notch_hz=notch,
                                         slope_db=pendiente)
                    for i, c in enumerate(canales)}

        if not oddball:
            ruido, sub_a, sub_b, bloques = promedio('frecuente', 1.0)
            senial = {c: traces['main'][c] + pam for c in canales}
            final = registrar(senial, ruido)
            subs = {c: (abr.apply_filters(senial[c] + sub_a[i] + red_coh, lp,
                                          hp, fs, slope_db=pendiente),
                        abr.apply_filters(senial[c] + sub_b[i] + red_coh, lp,
                                          hp, fs, slope_db=pendiente))
                    for i, c in enumerate(canales)}
            overlays = {}
            barridos_raros = None
        else:
            r_f, a_f, b_f, bloques = promedio('frecuente', 1.0 - rare_fraction)
            r_r, a_r, b_r, _ = promedio('raro', rare_fraction)
            frec = traces['overlays']['frecuente']
            raro = (traces['main'] if test == 'P300'
                    else traces['overlays']['raro'])
            f_final = registrar(frec, r_f)
            r_final = registrar(raro, r_r)
            sa_f, sb_f = registrar(frec, a_f), registrar(frec, b_f)
            sa_r, sb_r = registrar(raro, a_r), registrar(raro, b_r)
            if test == 'P300':
                final = r_final
                overlays = {'frecuente': f_final}
                subs = {c: (sa_r[c], sb_r[c]) for c in canales}
            else:
                final = {c: r_final[c] - f_final[c] for c in canales}
                overlays = {'frecuente': f_final, 'raro': r_final}
                subs = {c: (sa_r[c] - sa_f[c], sb_r[c] - sb_f[c])
                        for c in canales}
            barridos_raros = aceptados * rare_fraction

        sub_a_l, sub_b_l = subs[lectura]
        residual_nv = float(np.std(sub_a_l - sub_b_l) / 2.0 * 1000.0)
        senial_l = abr.apply_filters(traces['main'][lectura], lp, hp, fs,
                                     slope_db=pendiente)
        desde, hasta = FSP_WINDOW_MS[test]
        vent = (t >= desde) & (t <= min(hasta, window_ms))
        a_rms = float(np.sqrt(np.mean(senial_l[vent] ** 2))) if vent.any() else 0.0
        fsp_esperado = (1.0 + (a_rms / (residual_nv / 1000.0)) ** 2
                        if residual_nv > 0 else 1.0)
        fsp = abr.observed_fsp(fsp_esperado, rng)
        if clamp or not hay_registro:
            fsp_esperado = fsp = 1.0
        criterio = technical_config.get('fsp_criterion')

        meta = {
            'test': test,
            'population': population,
            'pathology': pathology,
            'cortical': True,
            'cortical_sin_datos': not datos,
            'edad': edad,
            'channels': list(canales),
            'read_channel': lectura,
            'channel_subs': {c: {'sub_a': subs[c][0], 'sub_b': subs[c][1]}
                             for c in canales},
            'overlays': overlays,
            'waves_visible': bool(hay_registro and datos and not clamp),
            'current_avg': current_avg,
            'target_avg': target_avg,
            'fsp': fsp,
            'fsp_esperado': fsp_esperado,
            'fsp_a_rms': a_rms,
            'growth': abr.calculate_growth(current_avg, target_avg),
            'threshold': umbral,
            'sl': sl,
            'masking': float((case_config or {}).get('masking') or 0.0),
            'shadow': False,
            'contra': None,
            'contra_channel': None,
            'window_ms': window_ms,
            'transducer': technical_config.get('transducer', 'insert_earphone'),
            'pathway': 'air_conduction',
            'output_db': nivel,
            'reference': referencia,
            'accepted_sweeps': aceptados,
            'rejected_sweeps': max(current_avg - aceptados, 0.0),
            'artifact_acceptance': aceptacion,
            'blinks_in_average': bool(blink_uv > 0 and test != 'MLR'),
            'rare_sweeps': barridos_raros,
            'rare_stim': rare_label if oddball else None,
            'rare_pct': rare_pct if oddball else None,
            'sub_a': sub_a_l,
            'sub_b': sub_b_l,
            'repro_index': abr.replicability(sub_a_l, sub_b_l),
            'residual_noise_nv': residual_nv,
            'recording': hay_registro,
            'tube_clamped': clamp,
            'noise_blocks': bloques,
            'agitation': 1.0,
            'mains': bool(sin_tierra or desbalance > 2.0),
            'impedance_max': imp_max,
            'impedance_imbalance': desbalance,
            'impedance_ok': abr.impedance_report(technical_config)[2],
            'fsp_criterion': criterio,
            'fsp_pass': (fsp >= criterio) if criterio else None,
        }
        meta['tarea'] = ctx['tarea']
        if test == 'P300' and datos:
            meta['conteo'] = self.patient_count(central, current_avg,
                                                rare_fraction, rng,
                                                ctx['tarea'])
        return t, final, meta

    @staticmethod
    def patient_count(central, presentados, rare_fraction, rng,
                      tarea='contar'):
        """Lo que respondió el paciente a la tarea (None si no hubo tarea).

        La tarea es parte de la P300: sin instrucción de contar o apretar
        no hay respuesta que revisar, dormido o sedado tampoco, y una
        respuesta muy lejos de lo presentado invalida la interpretación
        (ver diapositiva 44: oye el estímulo, entiende la tarea, está
        atento). Contando dice un número; con el botón quedan los aciertos
        y las falsas alarmas (botón con un frecuente).
        """
        estado = central['estado']
        if estado in ('dormido', 'sedado') or tarea not in cortical.TAREAS_ATENTAS:
            return None
        reales = int(round(presentados * rare_fraction))
        error = float(central['conteo_error'])
        if estado == 'somnoliento':
            error = max(error, 0.3)
        if tarea == 'boton':
            perdidos = float(rng.uniform(0.0, error)) if error else 0.0
            falsas = int(round(reales * float(rng.uniform(0.0, error * 0.3))))
            return {'tarea': 'boton', 'reales': reales,
                    'aciertos': max(int(round(reales * (1 - perdidos))), 0),
                    'falsas': falsas}
        desvio = float(rng.uniform(-error, error * 0.3)) if error else 0.0
        return {'tarea': 'contar', 'reales': reales,
                'dice': max(int(round(reales * (1 + desvio))), 0)}


_generator = None


def _get_cortical_generator():
    global _generator
    if _generator is None:
        _generator = CorticalGenerator()
    return _generator


def Cortical_Curve(test, actual_intencity, control_setting, preferences,
                   central, prom, done, patient=None, capture_id="",
                   technical=None):
    """Interfaz pública, espejo de ECochG_Curve para la ventana del módulo.

    Devuelve (t, {canal: y}, metadata). `preferences` es el dict del oído
    (cases.data['ABR'][lado]): de ahí salen el umbral y la inquietud.
    `central` es cases.data['Central'], el bloque del paciente.
    """
    generator = _get_cortical_generator()
    preferences = preferences or {}
    pathology = PATHOLOGY_MAP.get(preferences.get('type', 'normal'), 'normal')

    if done and prom[0] == 0:
        current_averages = prom[1]
    elif prom[0] <= 1.0:
        current_averages = prom[0] * prom[1]
    else:
        current_averages = prom[0] * 2.5
    target_averages = prom[1]
    current_averages = min(current_averages, target_averages)

    label = control_setting['stim']
    stim_key, stim_freq = STIM_MAP.get(label, ('click', None))
    stimulus_config = {
        'stim': stim_key, 'freq': stim_freq, 'label': label,
        'pol': control_setting.get('pol'),
        'int': actual_intencity, 'rate': control_setting['rate'],
        'filter_down': float(control_setting['filter_down']),
        'filter_passhigh': float(control_setting['filter_passhigh']),
        'average': target_averages, 'current_avg': current_averages,
        'pathway': 'air_conduction',
        'side': control_setting.get('side', 'OD'),
        'test': test,
        'tarea': control_setting.get('tarea') or 'ninguna',
    }
    technical_config = default_settings(test)
    if technical:
        technical_config.update(technical)
    technical_config['tube_clamped'] = bool(control_setting.get('clamp'))

    case_config = {
        'umbral': preferences.get('umbral', preferences.get('th', 20)),
        'umbral_por_estimulo': preferences.get('umbral_por_estimulo'),
        'inquietud': preferences.get('inquietud', 0),
        'masking': control_setting.get('mkg', 0),
        'seed_key': case_fingerprint(preferences),
        'capture_id': capture_id,
    }
    patient = patient or {}
    population = select_population(patient.get('edad'), patient.get('gender'),
                                   patient.get('edad_horas'))
    return generator.generate_curve(
        test, stimulus_config['side'], population, pathology,
        stimulus_config, technical_config, case_config,
        cortical.case_params(central), cortical.age_years(patient))
