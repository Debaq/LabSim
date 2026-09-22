"""Generador de electrococleografia.

Separado del de ABR a proposito. Los dos examenes comparten el equipo
--electrodos, impedancias, rechazo de artefacto, promediador, modelo de
ruido, filtros-- y eso se reusa importando las piezas de ABRGenerator, que
es donde viven. Lo que NO se comparte es el flujo, y por eso este modulo
tiene su propio generate_curve en vez de una rama adentro del otro:

- Lo que se registra son tres potenciales del oido interno (microfonica,
  sumacion y accion), no cinco ondas de una via. La morfologia esta en
  abr/ecochg.py.
- No hay curva sombra ni canal contralateral: el electrodo esta pegado a
  ESTA coclea y lo que capta del otro lado queda muy por debajo de su
  propia respuesta. El ECochG no es la prueba con la que se ensena
  enmascaramiento.
- No hay falsa onda V ni reflejo post-auricular: los dos viven fuera de
  la ventana de registro.
- La ventana de analisis del FSP es la suya (0.6-3.5 ms): la respuesta
  entera termina antes de que empiece la de la onda V.
- El ruido del PACIENTE, en cambio, se despeja igual que en el ABR y con
  la morfologia del ABR, porque es del paciente y no del examen (ver
  ABRGenerator.sigma_from_criterion y el comentario de reference_sigma).

Sin bloque de ECochG en el caso no se registra nada: no se inventa un oido
normal para que el equipo tenga algo que dibujar.
"""
import numpy as np

from abr import ecochg
from abr.ABR_generator import (AIR_MAX_OUTPUT_DB, BONE_MAX_OUTPUT_DB,
                               CASE_REFERENCE_DEFAULT, NOISE_FLOOR_UV,
                               NOISE_REF_SWEEPS, PATHOLOGY_MAP, RATE_AMP_DECAY,
                               RATE_LAT_SLOPE, RATE_REF, SAMPLES_PER_MS,
                               STIM_MAP, TRANSDUCER_LATENCY_MS, ABRGenerator,
                               _get_generator, default_settings,
                               select_population, stimulus_width)
from core.rng import case_fingerprint, stable_seed


# Ventana de analisis del FSP. No depende de la poblacion: el PA es la onda
# I, que es lo que menos se corre con la edad.
FSP_WINDOW_MS = (0.6, 3.5)


class ECochGGenerator:
    """Registro de electrococleografia, con el equipo del ABR."""

    def __init__(self, abr=None):
        # El generador de ABR es la caja de herramientas compartida: la
        # normativa, las ondas, el ruido, los filtros y el estado de los
        # electrodos. No se duplica nada de eso aca.
        self.abr = abr or _get_generator()

    # ------------------------------------------------------------------
    # Curva objetivo
    # ------------------------------------------------------------------

    def _una_polaridad(self, t, values, polarity, ctx, sp_scale=1.0):
        """Curva de UNA polaridad, con sus parametros."""
        v, _ = self.abr.apply_polarity_effects(
            {w: dict(d) for w, d in values.items()}, polarity,
            ctx['pathology'], ctx['neural'])
        onda = v.get('I')
        if onda is not None:
            # Adaptacion propia del oido: apply_rate_effects ya le puso al
            # PA la del oido sano (es la misma onda I). El caso declara
            # cuanto MAS se adapta este, y eso es lo que se agrega, sobre
            # la misma pendiente y la misma referencia de tasa.
            exceso = float(ctx['case']['tasa']) - 1.0
            if exceso:
                d_rate = float(ctx['rate']) - RATE_REF
                onda['lat'] += RATE_LAT_SLOPE['I'] * d_rate * exceso
                onda['amp'] *= float(np.clip(
                    np.exp(-RATE_AMP_DECAY['I'] * exceso * d_rate), 0.15, 1.2))
            if polarity == 'Condensación':
                # apply_polarity_effects ya le puso a la onda I los 0.1 ms
                # que separan condensacion de rarefaccion en un oido sano.
                # El caso puede declarar una separacion mayor --es lo que
                # pasa con la membrana desplazada-- y se agrega la
                # diferencia.
                onda['lat'] += float(ctx['case']['rar_cond_ms']) - 0.1
        params = ecochg.component_params(
            onda or {'lat': 1.5, 'amp': 0.0}, ctx['case'], ctx['montage'],
            stim=ctx['stim'], freq=ctx['freq'], mc_baseline=ctx['mc'],
            sl=ctx['sl'], gain=ctx['gain'], cm_lat=ctx['cm_lat'])
        return ecochg.build_curve(t, params, polarity, sp_scale), params

    def target_curve(self, t, values, polarity, ctx):
        """Curva objetivo, con la alternada como promedio real.

        La alternada no tiene factores propios: es el promedio de las dos
        polaridades, que es lo que el equipo hace barrido a barrido. De ahi
        sale sola la cancelacion de la microfonica, que es la mitad del
        examen.

        La altura de la meseta del PS se despeja SIEMPRE sobre la curva
        alternada, tenga la que tenga el equipo: es la unica sin
        microfonica encima, y la microfonica --que en una desincronia es
        mas grande que el propio PS-- no tiene por que cambiar cuanto PS
        produce esta coclea.
        """
        def alternada(escala):
            y_r, par = self._una_polaridad(t, values, 'Rarefacción', ctx,
                                           escala)
            y_c, _ = self._una_polaridad(t, values, 'Condensación', ctx,
                                         escala)
            return (y_r + y_c) / 2.0, par

        y_con, params = alternada(1.0)
        if params['sp_ap'] <= 0 or params['ap_amp'] <= 0:
            escala, x_pa, x_ps = 1.0, params['ap_lat'], params['sp_lat']
        else:
            y_sin, _ = alternada(0.0)
            escala, x_pa, x_ps = ecochg.calibrate_sp(
                t, y_sin, y_con, params['sp_ap'], params['ap_lat'])

        if polarity in ('Alternada', 'Alternante'):
            y_r, params = self._una_polaridad(t, values, 'Rarefacción', ctx,
                                              escala)
            y_c, _ = self._una_polaridad(t, values, 'Condensación', ctx,
                                         escala)
            y = (y_r + y_c) / 2.0
        else:
            y, params = self._una_polaridad(t, values, polarity, ctx, escala)
            # La latencia del PA es la de ESTA curva y no la de la
            # alternada con la que se calibro: rarefaccion y condensacion
            # no tienen el PA en el mismo lugar, y esa separacion es un
            # hallazgo.
            x_pa = ecochg.peak_time(t, y, params['ap_lat'])
            x_ps = x_pa - ecochg.SP_SHOULDER_MS
        return y, dict(params, ap_lat=x_pa, sp_lat=x_ps)

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------

    def reference_sigma(self, t, fs, population, pathology, neural,
                        baseline, click_baseline, threshold, stimulus_config,
                        case_config, desviaciones, repro_shift):
        """Cuanto ruido trae ESTE paciente, en uV RMS por barrido.

        Se despeja de lo que declara el caso ("a tal nivel hicieron falta
        tantos barridos para llegar al criterio") y se arma con la
        morfologia y la ventana del ABR aunque la prueba sea otra: lo que
        se mide aca es el paciente, y el paciente no cambia de ruido
        porque se cambie de examen.

        Armandola con la curva del ECochG el numero salia absurdo: al nivel
        de referencia --que es el umbral-- el potencial de sumacion vale
        cero, asi que la referencia era ~0, sigma caia al piso y el mismo
        paciente resultaba cuatro veces mas silencioso en ECochG que en
        ABR. Con la respuesta ocho veces mas grande, el complejo salia
        entero en el primer bloque de barridos.
        """
        referencia = dict(CASE_REFERENCE_DEFAULT)
        for clave in referencia:
            if (case_config or {}).get(clave) is not None:
                referencia[clave] = case_config[clave]
        if 'barridos_criterio' not in (case_config or {}) \
                and (case_config or {}).get('fsp_puntos'):
            referencia['barridos_criterio'] = self.abr.criterion_sweeps_from_fsp(
                case_config['fsp_puntos'].get('2000', 2.8))
        if str(referencia.get('respuesta_en_referencia', 'presente')) == 'ausente':
            return None, referencia

        nivel = referencia.get('nivel_referencia')
        nivel = threshold if nivel in (None, '') else float(nivel)
        v_ref, _ = self.abr.calculate_wave_parameters(
            baseline, nivel, threshold, pathology, desviaciones,
            repro_shift=repro_shift, click_baseline=click_baseline,
            neural=neural,
            stim_width=stimulus_width(stimulus_config['stim'],
                                      stimulus_config.get('freq')))
        v_ref = self.abr.apply_rate_effects(v_ref, stimulus_config['rate'],
                                            pathology, neural)
        y_ref, _ = self.abr.build_polarity_curve(
            t, v_ref, stimulus_config['pol'], pathology, neural, 1.0)
        y_ref = self.abr.apply_filters(
            y_ref, float(stimulus_config['filter_down']),
            float(stimulus_config['filter_passhigh']), fs)
        desde, hasta = self.abr.fsp_window(population)
        vent = (t >= desde) & (t <= hasta)
        a_ref = float(np.sqrt(np.mean(y_ref[vent] ** 2))) if vent.any() else 0.0
        referencia['a_rms'] = a_ref
        return self.abr.sigma_from_criterion(
            a_ref, float(referencia['barridos_criterio'])), referencia

    def generate_curve(self, population, pathology, stimulus_config,
                       technical_config, case_config=None):
        abr = self.abr
        case_ec = ecochg.case_params((case_config or {}).get('ecochg'))

        transducer = technical_config.get('transducer', 'insert_earphone')
        pathway = 'air_conduction'
        if transducer == 'bone_vibrator':
            pathway = 'bone_conduction'
            if float(stimulus_config['int']) > BONE_MAX_OUTPUT_DB:
                stimulus_config = dict(stimulus_config,
                                       int=BONE_MAX_OUTPUT_DB)
        elif float(stimulus_config['int']) > AIR_MAX_OUTPUT_DB:
            stimulus_config = dict(stimulus_config, int=AIR_MAX_OUTPUT_DB)

        baseline = abr.get_baseline_values(
            population, stimulus_config['stim'], pathway,
            freq=stimulus_config.get('freq'))
        click_baseline = (None if stimulus_config['stim'] == 'click'
                          else abr.get_baseline_values(population, 'click',
                                                       pathway))
        threshold = abr.case_threshold(case_config, stimulus_config, pathway,
                                       pathology)
        desviaciones = (case_config or {}).get('desviaciones')
        repro_shift = (case_config or {}).get('repro_shift', 0.0)
        neural = (case_config or {}).get('neural')

        # Eje temporal. La ventana la fija el protocolo y las muestras por
        # ms se mantienen para que fs no dependa de eso.
        window_ms = float(technical_config.get('window_ms') or 10)
        n_samples = max(int(round(window_ms * SAMPLES_PER_MS)), 64)
        t = np.linspace(0, window_ms, n_samples)
        fs = (len(t) - 1) / (t[-1] / 1000.0)

        rng = np.random.default_rng(stable_seed(
            (case_config or {}).get('seed_key', ''),
            (case_config or {}).get('capture_id', ''),
            population, pathology, 'ECochG', pathway,
            stimulus_config['stim'], stimulus_config.get('freq'),
            stimulus_config['int'], stimulus_config['pol'],
            stimulus_config['rate'], stimulus_config['filter_down'],
            stimulus_config['filter_passhigh'],
            technical_config.get('montage'),
        ))

        values, _ = abr.calculate_wave_parameters(
            baseline, stimulus_config['int'], threshold, pathology,
            desviaciones, repro_shift=repro_shift,
            click_baseline=click_baseline, neural=neural,
            stim_width=stimulus_width(stimulus_config['stim'],
                                      stimulus_config.get('freq')))
        values = abr.apply_rate_effects(values, stimulus_config['rate'],
                                        pathology, neural)
        lat_offset = TRANSDUCER_LATENCY_MS.get(transducer, 0.0)
        montage = technical_config.get('montage', 'vertex_mastoid')
        gain = abr.montage_factor(montage)
        for v in values.values():
            v['lat'] += lat_offset
            v['amp'] *= gain

        cm_lat = float((baseline.get('MC') or {}).get('lat', 0.0)) or None
        if cm_lat is not None:
            cm_lat += lat_offset
        ctx = {
            'pathology': pathology, 'neural': neural, 'case': case_ec,
            'montage': montage, 'stim': stimulus_config['stim'],
            'freq': stimulus_config.get('freq'),
            # El PS necesita nivel para ser medible: el nivel de sensacion
            # es lo que separa un ECochG clinico a 90 dB de una serie
            # descendente que no sirve para medir la razon.
            'sl': float(stimulus_config['int']) - threshold,
            'gain': gain, 'mc': baseline.get('MC'), 'cm_lat': cm_lat,
            'rate': float(stimulus_config['rate']),
        }

        jitter = float((case_config or {}).get('repro_jitter') or 0.0)
        ec_params = None
        if case_ec is None:
            y_target = y_target_a = y_target_b = np.zeros_like(t)
        else:
            values_a = abr._shift_latencies(values, jitter / 2)
            values_b = abr._shift_latencies(values, -jitter / 2)
            pol = stimulus_config['pol']
            y_target_a, ec_params = self.target_curve(t, values_a, pol, ctx)
            y_target_b = (y_target_a if not jitter
                          else self.target_curve(t, values_b, pol, ctx)[0])
            y_target = (y_target_a + y_target_b) / 2

        # Drift y artefacto del transductor: son del equipo, valen igual.
        clamp = (bool(technical_config.get('tube_clamped'))
                 and transducer == 'insert_earphone')
        y_drift = abr.add_baseline_drift(t, rng)
        y_artifact = abr.add_transducer_artifact(
            t, transducer, stimulus_config['int'], stimulus_config.get('pol'))
        y_clean = y_target + y_drift + y_artifact
        y_clean_a = y_target_a + y_drift + y_artifact
        y_clean_b = y_target_b + y_drift + y_artifact
        if clamp:
            y_clean = y_drift + y_artifact
            y_clean_a = y_clean.copy()
            y_clean_b = y_clean.copy()

        hay_registro, sin_tierra, imp_max, desbalance = abr.electrode_state(
            technical_config)
        # Sin bloque de ECochG en el caso no hay registro. NO se dibuja un
        # ABR en su lugar ni se supone un oido normal.
        if case_ec is None:
            hay_registro = False

        sigma, referencia = self.reference_sigma(
            t, fs, population, pathology, neural, baseline, click_baseline,
            threshold, stimulus_config, case_config, desviaciones,
            repro_shift)
        noise_floor = (sigma / float(np.sqrt(NOISE_REF_SWEEPS)) if sigma else
                       float(technical_config.get('residual_noise_nv')
                             or NOISE_FLOOR_UV * 1000) / 1000.0)

        band_factor = abr.band_noise_factor(
            stimulus_config['filter_passhigh'], stimulus_config['filter_down'])
        acceptance = abr.artifact_acceptance(
            technical_config.get('artifact_reject_uv'), 1.0,
            abr.reject_impedance_factor(imp_max) * band_factor)
        current_avg = stimulus_config['current_avg']
        target_avg = stimulus_config['average']
        accepted = current_avg * acceptance
        if not hay_registro:
            y_clean = np.zeros_like(t)
            y_clean_a = np.zeros_like(t)
            y_clean_b = np.zeros_like(t)
            accepted = 1.0

        growth_target = ((case_config or {}).get('average_objetivo')
                         or target_avg)
        inquietud = float((case_config or {}).get('inquietud') or 0.0)
        agitacion = None
        if inquietud > 0:
            seed_key = (case_config or {}).get('seed_key', '')
            agitacion = lambda i: abr.agitation_run(seed_key, inquietud, i)
        ruido, ruido_a, ruido_b, entraron = abr.averaged_noise(
            t, accepted, growth_target, 1.0, rng,
            abr.impedance_noise_factor(imp_max), noise_floor, split=True,
            band_factor=band_factor, agitacion=agitacion,
            reject_uv=technical_config.get('artifact_reject_uv'))
        bloque_actual = abr.noise_blocks_done(accepted, growth_target)
        accepted = accepted * entraron

        red_coh = 0.8 * abr.mains_interference(t, sin_tierra, desbalance, rng)
        inc_a = 0.6 * abr.mains_interference(t, sin_tierra, desbalance, rng)
        inc_b = 0.6 * abr.mains_interference(t, sin_tierra, desbalance, rng)
        red = red_coh + (inc_a + inc_b) / 2.0

        hp = float(stimulus_config['filter_passhigh'])
        lp = float(stimulus_config['filter_down'])
        y_final = abr.apply_filters(y_clean + ruido + red, lp, hp, fs)
        sub_a = abr.apply_filters(y_clean_a + ruido_a + red_coh + inc_a,
                                  lp, hp, fs)
        sub_b = abr.apply_filters(y_clean_b + ruido_b + red_coh + inc_b,
                                  lp, hp, fs)
        residual_nv = float(np.std(sub_a - sub_b) / 2.0 * 1000.0)

        senial = abr.apply_filters(y_target, lp, hp, fs)
        desde, hasta = FSP_WINDOW_MS
        vent = (t >= desde) & (t <= hasta)
        a_rms = float(np.sqrt(np.mean(senial[vent] ** 2))) if vent.any() else 0.0
        fsp_esperado = (1.0 + (a_rms / (residual_nv / 1000.0)) ** 2
                        if residual_nv > 0 else 1.0)
        fsp = abr.observed_fsp(fsp_esperado, rng)
        if clamp or not hay_registro:
            fsp_esperado = fsp = 1.0

        criterio = technical_config.get('fsp_criterion')
        return t, y_final, {
            'test': 'ECochG',
            'population': population,
            'pathology': pathology,
            'ecochg': case_ec is not None,
            'ecochg_sin_datos': case_ec is None,
            # Latencia del PA que el modelo puso en el trazo: el informe y
            # los tests la usan para auditar la marca del alumno. La razon
            # PS/PA NO va, que es el resultado que tiene que medir.
            'ecochg_ap_lat': (ec_params or {}).get('ap_lat'),
            'waves_visible': bool(hay_registro and case_ec),
            'current_avg': current_avg,
            'target_avg': target_avg,
            'fsp': fsp,
            'fsp_esperado': fsp_esperado,
            'fsp_a_rms': a_rms,
            'fsp_sigma': sigma,
            'fsp_a_referencia': referencia.get('a_rms'),
            'growth': abr.calculate_growth(current_avg, growth_target),
            'threshold': threshold,
            'masking': float((case_config or {}).get('masking') or 0.0),
            # El ECochG no tiene curva sombra ni canal contralateral: el
            # electrodo esta pegado a ESTA coclea.
            'shadow': False,
            'contra': None,
            'contra_channel': None,
            'window_ms': window_ms,
            'transducer': transducer,
            'pathway': pathway,
            'output_db': float(stimulus_config['int']),
            'accepted_sweeps': accepted,
            'rejected_sweeps': max(current_avg - accepted, 0.0),
            'artifact_acceptance': acceptance,
            'sub_a': sub_a,
            'sub_b': sub_b,
            'repro_index': abr.replicability(sub_a, sub_b),
            'residual_noise_nv': residual_nv,
            'recording': hay_registro,
            'tube_clamped': clamp,
            'noise_blocks': bloque_actual,
            'agitation': float(agitacion(bloque_actual - 1)) if agitacion else 1.0,
            'mains': bool(sin_tierra or desbalance > 2.0),
            'impedance_max': imp_max,
            'impedance_imbalance': desbalance,
            'impedance_ok': abr.impedance_report(technical_config)[2],
            'fsp_criterion': criterio,
            'fsp_pass': (fsp >= criterio) if criterio else None,
        }


_generator = None


def _get_ecochg_generator():
    global _generator
    if _generator is None:
        _generator = ECochGGenerator()
    return _generator


def ECochG_Curve(actual_intencity, control_setting, preferences, prom, done,
                 patient=None, capture_id="", technical=None):
    """Interfaz publica, espejo de ABR_Curve para la ventana del modulo.

    Devuelve (t, y, metadata). No devuelve canal contralateral ni jitter de
    reproducibilidad: el ECochG no los tiene.
    """
    generator = _get_ecochg_generator()
    pathology = PATHOLOGY_MAP.get(preferences.get('type', 'normal'), 'normal')

    if done and prom[0] == 0:
        current_averages = prom[1]
    elif prom[0] <= 1.0:
        current_averages = prom[0] * prom[1]
    else:
        current_averages = prom[0] * 2.5
    target_averages = prom[1]
    current_averages = min(current_averages, target_averages)

    stim_key, stim_freq = STIM_MAP.get(control_setting['stim'], ('click', None))
    stimulus_config = {
        'stim': stim_key, 'freq': stim_freq, 'pol': control_setting['pol'],
        'int': actual_intencity, 'rate': control_setting['rate'],
        'filter_down': float(control_setting['filter_down']),
        'filter_passhigh': float(control_setting['filter_passhigh']),
        'average': target_averages, 'current_avg': current_averages,
        'pathway': 'air_conduction',
        'side': control_setting.get('side', 'OD'),
        'test': 'ECochG',
    }

    technical_config = default_settings('ECochG')
    if technical:
        technical_config.update(technical)
    technical_config['tube_clamped'] = bool(control_setting.get('clamp'))

    case_config = {
        'desviaciones': preferences.get('desviaciones', {}),
        'inquietud': preferences.get('inquietud', 0),
        'fsp_puntos': preferences.get('fsp_puntos'),
        'umbral': preferences.get('umbral', preferences.get('th', 20)),
        'umbral_por_estimulo': preferences.get('umbral_por_estimulo'),
        'umbral_por_estimulo_oseo': preferences.get('umbral_por_estimulo_oseo'),
        'average_objetivo': preferences.get('average_objetivo', 2000),
        'nivel_referencia': preferences.get('nivel_referencia'),
        'barridos_criterio': preferences.get('barridos_criterio'),
        'respuesta_en_referencia': preferences.get('respuesta_en_referencia'),
        'neural': preferences.get('neural'),
        'ecochg': preferences.get('ecochg'),
        'masking': control_setting.get('mkg', 0),
        'seed_key': case_fingerprint(preferences),
        'capture_id': capture_id,
        'repro_jitter': (0.0 if preferences.get('repro', True)
                         else preferences.get('repro_var', 0.2)),
    }

    population = select_population((patient or {}).get('edad'),
                                   (patient or {}).get('gender'),
                                   (patient or {}).get('edad_horas'))
    return generator.generate_curve(
        population=population, pathology=pathology,
        stimulus_config=stimulus_config, technical_config=technical_config,
        case_config=case_config)
