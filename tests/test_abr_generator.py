"""
Tests del generador ABR (src/abr/ABR_generator.py).

Cubren las correcciones "P0" del modelo:
1. fs de los filtros sale del eje temporal real (~41.6 kHz), no de 20000
   fijo -- antes todo corte quedaba 2.08x arriba del rótulo.
2. Amplitud gobernada por el nivel de sensación (SL = intensidad - umbral)
   y no normalizada contra un techo fijo de 80 dB.
3. La onda I se apaga gradualmente, sin el escalón de disappear_offset.
4. El interpico I-V se ensancha ~0.2-0.4 ms entre 80 y 20 dB, no ~1.3.
5. El efecto de la tasa es continuo (sin quiebres en 15/50/60/70) y de
   magnitud fisiológica.

Y las "P1":
6. Física de patología: conductiva = corrimiento paralelo por el GAP,
   neural = interpicos prolongados y razón V/I caída.
7. Enmascaramiento: curva sombra del oído no evaluado y sobreenmascaramiento.
8. Población normativa según edad/sexo del paciente, no siempre adult_female.
9. Promediación: la señal está completa desde el principio y lo que cae es
   el ruido (1/sqrt(N)), con un trazo que se asienta en vez de parpadear.
10. Ruido reproducible entre ejecuciones (core.rng.stable_seed).

Y la configuración del equipo (Parámetros Avanzados), que antes se dibujaba
pero no la leía nadie:
11. Ventana de registro, transductor, montaje, electrodos e impedancias,
    rechazo de artefacto, ruido residual objetivo.
12. Protocolos por potencial evocado (abr/protocols.py) y todos los
    estímulos del combo funcionando en todas las poblaciones.

Sin scipy en el sandbox: se stubea para poder importar el módulo y correr
todo lo que es matemática de parámetros. Los tests del pipeline y de la
respuesta de los filtros necesitan scipy real y se saltan si no está.
"""

import os
import sys
import types

import numpy as np


SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    import scipy.signal  # noqa: F401
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    fake_signal = types.ModuleType('scipy.signal')
    fake_signal.butter = lambda *a, **k: ([1.0], [1.0])
    fake_signal.filtfilt = lambda *a, **k: None
    fake_signal.sosfiltfilt = lambda *a, **k: None
    scipy = types.ModuleType('scipy')
    scipy.signal = fake_signal
    sys.modules['scipy'] = scipy
    sys.modules['scipy.signal'] = fake_signal

from abr.ABR_generator import (  # noqa: E402
    ABRGenerator, IMPEDANCE_BALANCE_LIMIT_KOHM, IMPEDANCE_LIMIT_KOHM,
    INTERAURAL_ATTENUATION, RATE_REF, STIM_MAP, default_settings,
    select_population)
from abr.protocols import PROTOCOLS, get_protocol  # noqa: E402

NORMS = os.path.join(os.path.dirname(__file__), '..', 'resources', 'abr', 'normative_data.json')

# Mismo eje que usa generate_curve: 12 ms, 500 puntos.
T_AXIS = np.linspace(0, 12, 500)
FS = (len(T_AXIS) - 1) / (T_AXIS[-1] / 1000.0)


def _gen():
    return ABRGenerator(NORMS)


def _params(intensity, threshold=20, pathology='normal', rate=None):
    g = _gen()
    values, _ = g.calculate_wave_parameters(
        g.get_baseline_values(), intensity, threshold, pathology)
    if rate is not None:
        values = g.apply_rate_effects(values, rate, pathology)
    return values


# ---------------------------------------------------------------- filtros

def test_sampling_rate_comes_from_the_time_axis():
    """500 puntos en 12 ms = ~41.6 kHz, rango real de un equipo ABR."""
    assert 40000 < FS < 43000, FS


def test_filter_cutoff_lands_on_the_labeled_frequency():
    """Un tono en el corte tiene que quedar a -6 dB (filtfilt = doble pasada).

    Con el fs viejo (20000) el corte real quedaba 2.08x más arriba y este
    tono pasaba casi entero.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    for cutoff in (1500.0, 3000.0):
        for freq, lo, hi in ((cutoff / 3, 0.90, 1.05),
                             (cutoff, 0.35, 0.65),
                             (cutoff * 2.5, 0.0, 0.05)):
            x = np.sin(2 * np.pi * freq * T_AXIS / 1000.0)
            gain = np.max(np.abs(g.apply_filters(x, cutoff, 0, FS)[100:400]))
            assert lo <= gain <= hi, (cutoff, freq, gain)


def test_high_pass_removes_slow_drift():
    """El pasa-alto tiene que matar la deriva lenta y dejar pasar la banda ABR."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    slow = np.sin(2 * np.pi * 30.0 * T_AXIS / 1000.0)
    band = np.sin(2 * np.pi * 900.0 * T_AXIS / 1000.0)
    assert np.max(np.abs(g.apply_filters(slow, 0, 300.0, FS)[100:400])) < 0.15
    assert np.max(np.abs(g.apply_filters(band, 0, 300.0, FS)[100:400])) > 0.85


# ------------------------------------------------------- amplitud por SL

def test_amplitude_depends_on_sensation_level_not_absolute_db():
    """Mismo SL, misma amplitud: 40 dB con umbral 20 == 60 dB con umbral 40."""
    a = _params(40, threshold=20)
    b = _params(60, threshold=40)
    for wave in ('I', 'III', 'V'):
        assert abs(a[wave]['amp'] - b[wave]['amp']) < 1e-9, wave


def test_impaired_ear_is_not_full_amplitude_at_80db():
    """Umbral 60 a 80 dB son 20 dB SL: no puede verse como un oído sano.

    Era el bug del modelo viejo (amp_factor normalizaba contra 80 dB fijo,
    así que cualquier umbral daba amplitud normativa completa a 80).
    """
    sano = _params(80, threshold=20)
    perdida = _params(80, threshold=60, pathology='cochlear')
    assert perdida['V']['amp'] < 0.92 * sano['V']['amp']
    assert perdida['V']['amp'] > 0.20 * sano['V']['amp']
    # Onda I: en pérdida coclear con umbral 60 a 80 dB no debe estar.
    assert perdida['I']['amp'] < 0.05


def test_no_response_below_threshold():
    """Bajo el umbral del oído no queda respuesta apreciable."""
    v = _params(40, threshold=60, pathology='cochlear')
    assert all(v[w]['amp'] < 0.02 for w in v), v


def test_recruitment_makes_cochlear_grow_faster():
    """Reclutamiento: a igual SL, la coclear crece más rápido que la normal."""
    normal = _params(50, threshold=20, pathology='normal')
    coclear = _params(90, threshold=60, pathology='cochlear')
    assert coclear['V']['amp'] > normal['V']['amp']


# ----------------------------------------------------------- onda I / cliff

def test_wave_I_decays_without_a_cliff():
    """La onda I se apaga gradual: nada de 0.21 -> 0.011 uV en un paso.

    El modelo viejo tenía disappear_offset = 70 para I y II, así que a 70 dB
    exactos la onda I ya era invisible en un oído normal.
    """
    amps = [_params(i)['I']['amp'] for i in (80, 70, 60, 50, 40)]
    for prev, cur in zip(amps, amps[1:]):
        assert cur < prev, amps
        assert cur > 0.15 * prev, amps          # sin escalones
    assert amps[2] > 0.5 * amps[0], amps        # visible a 60 dB
    assert amps[1] > 0.7 * amps[0], amps        # clara a 70 dB


# -------------------------------------------------------------- interpicos

def test_interpeak_widening_is_physiological():
    """I-V ensancha 0.1-0.45 ms entre 80 y 20 dB (antes: 1.26 ms)."""
    def i_v(intensity):
        v = _params(intensity)
        return v['V']['lat'] - v['I']['lat']
    delta = i_v(20) - i_v(80)
    assert 0.10 <= delta <= 0.45, delta


def test_interpeak_at_80db_matches_norms():
    """A 80 dB los interpicos caen dentro del rango clínico normal."""
    v = _params(80)
    i_iii = v['III']['lat'] - v['I']['lat']
    iii_v = v['V']['lat'] - v['III']['lat']
    i_v = v['V']['lat'] - v['I']['lat']
    assert 1.9 <= i_iii <= 2.4, i_iii
    assert 1.6 <= iii_v <= 2.1, iii_v
    assert 3.6 <= i_v <= 4.4, i_v


# -------------------------------------------------------------------- tasa

def test_rate_effect_is_continuous():
    """Sin quiebres: el modelo viejo saltaba en 15, 50, 60 y 70/s."""
    g = _gen()
    rates = np.arange(5.0, 95.5, 0.5)
    for wave in ('I', 'II', 'III', 'IV', 'V'):
        serie = []
        for r in rates:
            v, _ = g.calculate_wave_parameters(g.get_baseline_values(), 80, 20, 'normal')
            serie.append(g.apply_rate_effects(v, float(r), 'normal')[wave]['amp'])
        serie = np.array(serie)
        salto = np.max(np.abs(np.diff(serie)) / serie[:-1])
        assert salto < 0.01, (wave, salto)


def test_rate_effect_magnitude_is_clinical():
    """De 11 a 91/s: onda V ~+0.4-0.6 ms y -20-35% de amplitud."""
    lento = _params(80, rate=11.1)
    rapido = _params(80, rate=91.1)
    d_lat = rapido['V']['lat'] - lento['V']['lat']
    ratio = rapido['V']['amp'] / lento['V']['amp']
    assert 0.30 <= d_lat <= 0.70, d_lat
    assert 0.65 <= ratio <= 0.85, ratio
    # La onda I aguanta peor la tasa que la V.
    assert rapido['I']['amp'] / lento['I']['amp'] < ratio


def test_waves_II_and_IV_survive_moderate_rates():
    """A 61/s II y IV bajan, no desaparecen (antes caían a 0.006 uV)."""
    ref = _params(80, rate=RATE_REF)
    alto = _params(80, rate=61.1)
    for wave in ('II', 'IV'):
        assert alto[wave]['amp'] > 0.5 * ref[wave]['amp'], wave


def test_neural_is_more_rate_sensitive():
    """Patología neural = mala resistencia a tasas altas."""
    normal = _params(80, pathology='normal', rate=71.1)
    neural = _params(80, pathology='neural', rate=71.1)
    assert neural['V']['amp'] < normal['V']['amp']
    assert neural['V']['lat'] > normal['V']['lat']


def test_rate_reference_is_neutral():
    """A RATE_REF la tasa no modifica nada."""
    sin_tasa = _params(80)
    con_tasa = _params(80, rate=RATE_REF)
    for wave in sin_tasa:
        assert abs(sin_tasa[wave]['lat'] - con_tasa[wave]['lat']) < 1e-9
        assert abs(sin_tasa[wave]['amp'] - con_tasa[wave]['amp']) < 1e-9


# ------------------------------------------------------------------ golden

def test_golden_wave_parameters():
    """Snapshot del oído normal (umbral 20) para detectar drift del modelo."""
    golden = {
        80: {'I': (1.62, 0.200), 'II': (2.68, 0.103), 'III': (3.68, 0.358),
             'IV': (4.68, 0.257), 'V': (5.47, 0.576)},
        60: {'I': (1.94, 0.165), 'II': (3.02, 0.080), 'III': (4.03, 0.328),
             'IV': (5.04, 0.229), 'V': (5.85, 0.534)},
        40: {'I': (2.45, 0.039), 'II': (3.56, 0.015), 'III': (4.58, 0.227),
             'IV': (5.62, 0.140), 'V': (6.45, 0.420)},
    }
    for intensity, esperado in golden.items():
        v = _params(intensity)
        for wave, (lat, amp) in esperado.items():
            assert abs(v[wave]['lat'] - lat) < 0.01, (intensity, wave, v[wave]['lat'])
            assert abs(v[wave]['amp'] - amp) < 0.001, (intensity, wave, v[wave]['amp'])


# --------------------------------------------------------------- pipeline

def _curva(intensity=80, threshold=20, pathology='normal', population='adult_female',
           current=2000, target=2000, masking=0, contra=None, capture='R1',
           seed_key='caso-1', fsp=(2.3, 2.8), technical=None, filter_high=100):
    """Corre generate_curve con un caso completo (necesita scipy)."""
    g = _gen()
    stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': intensity,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': filter_high,
            'average': target, 'current_avg': current, 'pathway': 'air_conduction'}
    tech = default_settings('ABR')
    tech.update(technical or {})
    case = {'desviaciones': {}, 'fsp_puntos': {'800': fsp[0], '2000': fsp[1]},
            'umbral': threshold, 'average_objetivo': target, 'repro_shift': 0.0,
            'masking': masking, 'contra': contra,
            'seed_key': seed_key, 'capture_id': capture}
    return g.generate_curve(population, pathology, stim, tech, case)


# ------------------------------------------------------ pipeline (P0)

def test_pipeline_produces_a_wave_V_where_it_should():
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    stim = {'stim': 'click', 'freq': None, 'pol': 'Rarefacción', 'int': 80,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
            'average': 2000, 'current_avg': 2000, 'pathway': 'air_conduction'}
    tech = {'impedance': 3.0, 'transducer': 'insert_earphone'}
    case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0}
    t, y, meta = g.generate_curve('adult_female', 'normal', stim, tech, case)

    assert y.shape == t.shape == (500,)
    assert np.isfinite(y).all()
    esperado = _params(80)['V']['lat']
    pico = t[np.argmax(y)]
    assert abs(pico - esperado) < 0.4, (pico, esperado)
    assert 0.3 < y.max() < 1.0, y.max()
    assert meta['fsp'] > 0 and meta['growth'] == 1.0


def test_pipeline_low_intensity_is_smaller_and_later():
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()

    def corrida(intensity):
        stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': intensity,
                'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
                'average': 4000, 'current_avg': 4000, 'pathway': 'air_conduction'}
        tech = {'impedance': 3.0, 'transducer': 'insert_earphone'}
        case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.8, '2000': 3.5},
                'umbral': 20, 'average_objetivo': 4000, 'repro_shift': 0.0}
        t, y, _ = g.generate_curve('adult_female', 'normal', stim, tech, case)
        return t[np.argmax(y)], y.max()

    lat_alto, amp_alto = corrida(80)
    lat_bajo, amp_bajo = corrida(40)
    assert lat_bajo > lat_alto
    assert amp_bajo < amp_alto


# ------------------------------------------------------- patología (P1)

def test_conductive_shifts_the_whole_complex_in_parallel():
    """GAP conductivo = estímulo atenuado: todo se atrasa, interpicos intactos.

    Es el hallazgo que separa conductiva de coclear en el gráfico
    latencia-intensidad. Antes la patología no tocaba la latencia: una
    conductiva a 80 dB salía con latencias de oído sano.
    """
    sano = _params(80, threshold=15, pathology='normal')
    conduct = _params(80, threshold=45, pathology='conductive')
    assert conduct['V']['lat'] - sano['V']['lat'] > 0.5
    i_v_sano = sano['V']['lat'] - sano['I']['lat']
    i_v_cond = conduct['V']['lat'] - conduct['I']['lat']
    assert abs(i_v_cond - i_v_sano) < 0.15, (i_v_sano, i_v_cond)


def test_cochlear_keeps_normal_latency_at_high_level():
    """La coclear NO corre la latencia a nivel alto (no hay GAP que atenúe)."""
    sano = _params(80, threshold=15, pathology='normal')
    coclear = _params(80, threshold=45, pathology='cochlear')
    assert abs(coclear['V']['lat'] - sano['V']['lat']) < 0.01
    # ...y a igual umbral, la conductiva sí se atrasa respecto de la coclear.
    conduct = _params(80, threshold=45, pathology='conductive')
    assert conduct['V']['lat'] > coclear['V']['lat'] + 0.4


def test_neural_prolongs_interpeaks_and_drops_v_over_i():
    """Retrococlear: I-V largo y razón V/I dentro del rango del JSON."""
    normal = _params(80, pathology='normal')
    neural = _params(80, pathology='neural')
    i_v_normal = normal['V']['lat'] - normal['I']['lat']
    i_v_neural = neural['V']['lat'] - neural['I']['lat']
    assert i_v_neural - i_v_normal >= 0.3, (i_v_normal, i_v_neural)
    assert abs(neural['I']['lat'] - normal['I']['lat']) < 1e-9  # la I no se mueve
    ratio = neural['V']['amp'] / neural['I']['amp']
    rango = _gen().norms['pathology_modifiers']['neural']['amplitude_v_i_ratio']
    assert rango[0] <= ratio <= rango[1], ratio


# ------------------------------------------------------- población (P1)

def test_population_follows_age_and_sex():
    assert select_population(None) == 'adult_female'
    assert select_population(0) == 'neonate'
    assert select_population(0.2) == 'neonate'
    assert select_population(1) == 'child'
    assert select_population(9) == 'child'
    assert select_population(30, 0) == 'adult_male'
    assert select_population(30, 1) == 'adult_female'
    assert select_population(70, 0) == 'elderly'
    assert select_population("no es una edad") == 'adult_female'


def test_neonate_has_a_longer_wave_V_than_an_adult():
    """Vía auditiva inmadura: la onda V del neonato llega bastante después."""
    g = _gen()
    def lat_v(pop):
        valores, _ = g.calculate_wave_parameters(
            g.get_baseline_values(population=pop), 80, 20, 'normal')
        return valores['V']['lat']
    assert lat_v('neonate') - lat_v('adult_female') > 0.8
    assert lat_v('elderly') > lat_v('adult_female')


# --------------------------------------------------- enmascaramiento (P1)

def test_shadow_curve_appears_when_the_stimulus_crosses_the_skull():
    """Oído muerto estimulado fuerte: responde el otro y se registra igual."""
    g = _gen()
    ia = INTERAURAL_ATTENUATION['insert_earphone']
    stim = {'stim': 'click', 'freq': None, 'int': 90, 'pathway': 'air_conduction'}
    caso = {'contra': {'umbral': 15, 'type': 'normal'}}
    sombra = g.shadow_values('adult_female', 'air_conduction', stim, 0, ia, caso)
    assert sombra is not None
    # Es una respuesta de bajo nivel para esa cóclea: latencia larga.
    normal = _params(90)
    assert sombra['V']['lat'] > normal['V']['lat'] + 0.5
    # Y sin onda I reconocible, que es la pista de que es sombra.
    assert sombra['I']['amp'] < 0.5 * sombra['V']['amp']


def test_masking_kills_the_shadow_curve():
    g = _gen()
    ia = INTERAURAL_ATTENUATION['insert_earphone']
    stim = {'stim': 'click', 'freq': None, 'int': 90, 'pathway': 'air_conduction'}
    caso = {'contra': {'umbral': 15, 'type': 'normal'}}
    # Lo que cruza son 90 - 65 = 25 dB: con 40 de masking el otro oído no oye.
    assert g.shadow_values('adult_female', 'air_conduction', stim, 40, ia, caso) is None
    assert g.shadow_values('adult_female', 'air_conduction', stim, 0, ia, caso) is not None


def test_no_shadow_below_interaural_attenuation():
    """A 60 dB con insertos no cruza nada, aunque el otro oído sea normal."""
    g = _gen()
    ia = INTERAURAL_ATTENUATION['insert_earphone']
    stim = {'stim': 'click', 'freq': None, 'int': 60, 'pathway': 'air_conduction'}
    caso = {'contra': {'umbral': 15, 'type': 'normal'}}
    assert g.shadow_values('adult_female', 'air_conduction', stim, 0, ia, caso) is None


def test_shadow_shows_up_in_the_curve():
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    contra = {'umbral': 15, 'type': 'normal'}
    # Oído evaluado sin respuesta (umbral 95), otro oído sano.
    _, _, meta_sin = _curva(intensity=90, threshold=95, pathology='cochlear',
                            contra=contra, masking=0)
    _, _, meta_con = _curva(intensity=90, threshold=95, pathology='cochlear',
                            contra=contra, masking=45)
    assert meta_sin['shadow'] is True
    assert meta_con['shadow'] is False


def test_overmasking_degrades_the_test_ear():
    """Demasiado masking cruza de vuelta y enmascara el oído evaluado."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    contra = {'umbral': 20, 'type': 'normal'}
    _, y_sin, meta_sin = _curva(intensity=60, threshold=20, contra=contra, masking=0)
    _, y_over, meta_over = _curva(intensity=60, threshold=20, contra=contra, masking=100)
    assert meta_sin['threshold'] == 20
    assert meta_over['threshold'] > 20          # umbral efectivo elevado
    assert y_over.max() < y_sin.max()


# ----------------------------------------------------- promediación (P1)

def test_signal_does_not_grow_with_averaging():
    """La amplitud de la onda no depende de cuánto se lleve promediado.

    Antes se escalaba la señal por `growth`, así que a mitad de captura la
    onda V medía la mitad: en un equipo real está completa desde el primer
    barrido y lo que baja es el ruido.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t_med, y_med, _ = _curva(current=600, target=2000)
    t_fin, y_fin, _ = _curva(current=2000, target=2000)
    pico_med = y_med[(t_med > 4.5) & (t_med < 6.5)].max()
    pico_fin = y_fin[(t_fin > 4.5) & (t_fin < 6.5)].max()
    assert abs(pico_med - pico_fin) < 0.35 * pico_fin, (pico_med, pico_fin)


def test_residual_noise_falls_as_one_over_sqrt_n():
    """El ruido residual cae ~1/sqrt(N) y termina en el orden de 40 nV."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    def residual(n):
        ruido = g.averaged_noise(T_AXIS, n, 2000, 1.0, np.random.default_rng(11))
        return float(g.apply_filters(ruido, 3000.0, 100.0, FS).std())

    r_bajo, r_alto = residual(125), residual(2000)
    esperado = np.sqrt(2000 / 125)              # = 4
    assert 0.6 * esperado <= r_bajo / r_alto <= 1.6 * esperado, (r_bajo, r_alto)
    assert 0.01 < r_alto < 0.10, r_alto         # piso del equipo, en uV


def test_trace_settles_instead_of_flickering():
    """Dos ticks seguidos comparten el ruido ya acumulado."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, y1, _ = _curva(current=1000)
    _, y2, _ = _curva(current=1175)             # el tick siguiente
    _, y3, _ = _curva(current=1000, capture='R2')
    assert np.corrcoef(y1, y2)[0, 1] > 0.9      # se asienta
    assert np.corrcoef(y1, y3)[0, 1] < np.corrcoef(y1, y2)[0, 1]


def test_stopping_early_leaves_a_noisier_curve():
    """Parar antes del average que el caso necesita deja más ruido."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    # La señal es la misma en las tres (mismo caso, misma semilla), así que
    # la distancia contra una corrida muy promediada es ruido y nada más.
    _, y_corto, _ = _curva(current=1000, target=4000)
    _, y_completo, _ = _curva(current=4000, target=4000)
    _, y_ref, _ = _curva(current=16000, target=4000)
    ruido_corto = np.std(y_corto - y_ref)
    ruido_completo = np.std(y_completo - y_ref)
    assert ruido_corto > 1.5 * ruido_completo, (ruido_corto, ruido_completo)


def test_capture_is_reproducible_across_runs():
    """Mismo caso, mismos parámetros, misma curva: mismo trazo.

    hash() de Python no sirve para esto (saltea por proceso); el ruido va
    sembrado con core.rng.stable_seed.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, a, _ = _curva()
    _, b, _ = _curva()
    assert np.array_equal(a, b)
    _, otro_caso, _ = _curva(seed_key='caso-2')
    assert not np.array_equal(a, otro_caso)
    _, otra_curva, _ = _curva(capture='R7')
    assert not np.array_equal(a, otra_curva)


# ------------------------------------------------- protocolos y equipo (P2)

def test_protocol_table_covers_every_test_in_the_combo():
    """Los 8 potenciales del combo cb_test tienen protocolo descrito."""
    esperados = {'ABR', 'ASSR', 'MLR', 'P300', 'MMN', 'ECochG', 'CAEP',
                 'Stacked ABR'}
    assert esperados == set(PROTOCOLS)
    # Solo ABR tiene generador; el resto queda descrito pero deshabilitado.
    assert {n for n, p in PROTOCOLS.items() if p.implemented} == {'ABR'}
    for nombre, p in PROTOCOLS.items():
        assert p.window_ms > 0, nombre
        assert p.filter_high < p.filter_low, nombre     # pasa-alto < pasa-bajo
        assert p.averages > 0 and p.rate > 0, nombre
        assert p.stimuli, nombre


def test_defaults_follow_the_protocol():
    """El equipo arranca en el montaje de rutina de cada prueba."""
    abr = default_settings('ABR')
    assert abr['window_ms'] == get_protocol('ABR').window_ms
    assert abr['montage'] == 'vertex_mastoid'
    ecochg = default_settings('ECochG')
    assert ecochg['window_ms'] == 5           # ventana corta: MC, PS y PA
    assert ecochg['montage'] == 'tympanic'
    assert default_settings('P300')['window_ms'] == 800
    # Una prueba desconocida no puede reventar: cae en el protocolo de ABR.
    assert default_settings('no existe')['window_ms'] == abr['window_ms']


def test_window_sets_the_time_axis_without_moving_fs():
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    for ventana in (6.0, 12.0, 20.0):
        t, y, meta = _curva(technical={'window_ms': ventana})
        assert abs(t[-1] - ventana) < 1e-9
        fs = (len(t) - 1) / (t[-1] / 1000.0)
        assert abs(fs - FS) / FS < 0.01, (ventana, fs)
        assert meta['window_ms'] == ventana


def test_supraaural_makes_everything_earlier():
    """Sin el tubo del inserto, el complejo aparece ~0.9 ms antes."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t_ins, y_ins, _ = _curva()
    t_tdh, y_tdh, meta = _curva(technical={'transducer': 'TDH39_headphone'})
    adelanto = t_ins[np.argmax(y_ins)] - t_tdh[np.argmax(y_tdh)]
    assert 0.7 < adelanto < 1.1, adelanto
    assert meta['pathway'] == 'air_conduction'


def test_bone_vibrator_switches_to_bone_conduction():
    """El vibrador óseo no es otro fono: tiene su propio bloque normativo."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, meta = _curva(technical={'transducer': 'bone_vibrator'})
    assert meta['pathway'] == 'bone_conduction'


def test_montage_scales_amplitude():
    """Fz-mastoides recoge menos que Cz-mastoides (0.7 en el JSON)."""
    g = _gen()
    factor = g.montage_factor('forehead_mastoid')
    assert abs(factor - 0.7) < 1e-9
    assert g.montage_factor('vertex_mastoid') == 1.0
    assert g.montage_factor('tympanic') > 1.0        # ECochG: mucho más grande
    if not HAS_SCIPY:
        return
    _, y_cz, _ = _curva()
    _, y_fz, _ = _curva(technical={'montage': 'forehead_mastoid'})
    assert y_fz.max() < y_cz.max()


def test_disconnected_active_electrode_leaves_no_response():
    """Sin activo no hay diferencia de potencial: solo ruido, por más que promedie."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    electrodos = {'vertex': 'No Conectado', 'right': 'A2', 'left': 'A1',
                  'ground': 'Fpz'}
    t, y, meta = _curva(technical={'electrodes': electrodos})
    _, y_ok, _ = _curva()
    assert meta['recording'] is False
    assert y[t > 9].std() > 5 * y_ok[t > 9].std()

    # Y sobre todo: no hay onda. Con respuesta real el pico cae siempre en
    # la misma latencia; acá cada captura lo pone en otro lado, que es como
    # se reconoce que lo que se está viendo es ruido.
    def picos(**kw):
        return [_curva(capture=f"R{i}", **kw)[0][np.argmax(_curva(capture=f"R{i}", **kw)[1])]
                for i in range(1, 4)]
    sin_electrodo = picos(technical={'electrodes': electrodos})
    con_electrodo = picos()
    assert max(sin_electrodo) - min(sin_electrodo) > 0.5, sin_electrodo
    assert max(con_electrodo) - min(con_electrodo) < 0.2, con_electrodo


def test_missing_ground_brings_mains_hum():
    """Sin tierra entra la red: el zumbido se ve pese al pasa-alto de 100 Hz."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    electrodos = {'vertex': 'Cz', 'right': 'A2', 'left': 'A1',
                  'ground': 'No Conectado'}
    t, y_sin, meta = _curva(technical={'electrodes': electrodos})
    t, y_ok, _ = _curva()
    assert meta['mains'] is True
    assert y_sin[t > 9].std() > 5 * y_ok[t > 9].std()
    # Y con un pasa-alto más bajo (potenciales corticales) es peor todavía.
    t, y_bajo, _ = _curva(technical={'electrodes': electrodos}, filter_high=33)
    assert y_bajo[t > 9].std() > y_sin[t > 9].std()


def _ruido(impedancias):
    """Ruido de fondo de la curva con esas impedancias (uV RMS)."""
    t, y, meta = _curva(technical={'impedance': impedancias})
    return float(y[t > 9].std()), meta


def test_impedance_limit_of_5k_is_visible():
    """Cruzar los 5 kOhm por electrodo tiene que NOTARSE, no subir 30%.

    Es una de las dos reglas que el alumno tiene que poder justificar
    mirando el trazo, así que el modelo tiene un codo ahí: por debajo sigue
    la tabla del JSON, por encima se acelera.
    """
    g = _gen()
    # Dentro de norma: pendiente suave.
    assert g.impedance_noise_factor(2) < g.impedance_noise_factor(4)
    assert g.impedance_noise_factor(5) / g.impedance_noise_factor(3) < 2.0
    # Pasado el límite se dispara, y sigue subiendo bien arriba (antes
    # np.interp saturaba: 8, 12 y 20 kOhm daban el mismo trazo).
    assert g.impedance_noise_factor(8) > 2.5 * g.impedance_noise_factor(5)
    assert g.impedance_noise_factor(12) > 2 * g.impedance_noise_factor(8)
    if not HAS_SCIPY:
        return
    todos = lambda k: {e: k for e in ('vertex', 'right', 'left', 'ground')}
    r5, meta5 = _ruido(todos(5.0))
    r8, meta8 = _ruido(todos(8.0))
    r12, _ = _ruido(todos(12.0))
    assert meta5['impedance_ok'] is True          # 5.0 justo en el límite
    assert meta8['impedance_ok'] is False
    assert r8 > 2 * r5, (r5, r8)
    assert r12 > r8
    # Con 12 kOhm el ruido es un orden de magnitud peor que en norma: la
    # onda V (0.5 uV) queda al nivel del piso y el registro es inservible.
    r2, _ = _ruido(todos(2.0))
    assert r12 > 6 * r2, (r2, r12)


def test_impedance_balance_limit_of_2k_is_visible():
    """Diferencias sobre 2 kOhm entre electrodos = zumbido de red.

    La otra regla. El desbalance es lo que rompe el rechazo de modo común
    del amplificador, así que se manifiesta distinto que la impedancia
    alta: no es más ruido de fondo, es 50 Hz.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    def con_dif(dif):
        return _ruido({'vertex': 2.0 + dif, 'right': 2.0, 'left': 2.0,
                       'ground': 2.0})

    r0, meta0 = con_dif(0.0)
    r_limite, meta_limite = con_dif(IMPEDANCE_BALANCE_LIMIT_KOHM)
    r_pasado, meta_pasado = con_dif(IMPEDANCE_BALANCE_LIMIT_KOHM + 1.0)

    # Dentro de norma no hay zumbido (el residual es invisible).
    assert meta0['mains'] is False and meta_limite['mains'] is False
    assert r_limite < 2.0 * r0
    # Pasando el límite salta.
    assert meta_pasado['mains'] is True
    assert meta_pasado['impedance_ok'] is False
    assert r_pasado > 3 * r_limite, (r_limite, r_pasado)
    # Y sigue creciendo con la diferencia.
    assert con_dif(4.0)[0] > r_pasado


def test_impedance_report_matches_the_two_rules():
    """El chequeo que muestra el diálogo usa los mismos límites."""
    g = _gen()
    peor, dif, ok = g.impedance_report(
        {'impedance': {'vertex': 4.0, 'right': 3.0, 'left': 2.5, 'ground': 2.0}})
    assert (peor, dif, ok) == (4.0, 2.0, True)          # justo en los dos límites
    _, _, ok = g.impedance_report(
        {'impedance': {'vertex': 5.5, 'right': 5.0, 'left': 5.0, 'ground': 5.0}})
    assert ok is False                                   # supera 5 kOhm
    _, _, ok = g.impedance_report(
        {'impedance': {'vertex': 4.5, 'right': 2.0, 'left': 2.0, 'ground': 2.0}})
    assert ok is False                                   # desbalance 2.5 kOhm
    # Un electrodo desconectado no cuenta para el chequeo.
    peor, dif, ok = g.impedance_report(
        {'electrodes': {'vertex': 'Cz', 'right': 'A2', 'left': 'No Conectado',
                        'ground': 'Fpz'},
         'impedance': {'vertex': 2.0, 'right': 2.5, 'left': 18.0, 'ground': 2.0}})
    assert peor == 2.5 and ok is True
    assert IMPEDANCE_LIMIT_KOHM == 5.0 and IMPEDANCE_BALANCE_LIMIT_KOHM == 2.0


def test_artifact_rejection_cuts_both_ways():
    """Umbral estrecho: promedio lento. Rechazo apagado: entra basura."""
    g = _gen()
    assert g.artifact_acceptance(25, 1.0) == 1.0          # habitual, no descarta
    assert g.artifact_acceptance(10, 1.0) < 0.7           # estrecho
    # Con un paciente inquieto el mismo umbral descarta más.
    assert g.artifact_acceptance(25, 2.0) < g.artifact_acceptance(25, 1.0)
    assert g.artifact_acceptance(0, 1.0) == 1.0           # desactivado
    if not HAS_SCIPY:
        return
    t, y_habitual, _ = _curva()
    t, y_estrecho, meta = _curva(technical={'artifact_reject_uv': 10.0})
    t, y_sin, _ = _curva(technical={'artifact_reject_uv': 0.0})
    assert meta['artifact_acceptance'] < 1.0
    assert meta['accepted_sweeps'] < 2000
    assert y_estrecho[t > 9].std() > y_habitual[t > 9].std()
    assert y_sin[t > 9].std() > y_habitual[t > 9].std()


def test_residual_noise_target_sets_the_floor():
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y_40, _ = _curva(technical={'residual_noise_nv': 40})
    t, y_120, _ = _curva(technical={'residual_noise_nv': 120})
    razon = y_120[t > 9].std() / y_40[t > 9].std()
    assert 2.0 < razon < 4.0, razon


def test_fsp_criterion_is_reported():
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, meta = _curva(technical={'fsp_criterion': 4.0}, fsp=(2.3, 2.8))
    assert meta['fsp_criterion'] == 4.0
    assert meta['fsp_pass'] is False            # el caso llega a 2.8, no a 4.0
    _, _, meta = _curva(technical={'fsp_criterion': 2.0})
    assert meta['fsp_pass'] is True


# ---------------------------------------------------------- estímulos (P2)

def test_every_stimulus_works_in_every_population():
    """Los 7 estímulos del combo dan ondas ordenadas en las 5 poblaciones."""
    g = _gen()
    for poblacion in ('adult_female', 'adult_male', 'child', 'neonate', 'elderly'):
        for etiqueta, (stim, freq) in STIM_MAP.items():
            base = g.get_baseline_values(poblacion, stim, 'air_conduction', freq=freq)
            lats = [base[w]['lat'] for w in ('I', 'II', 'III', 'IV', 'V')]
            assert lats == sorted(lats), (poblacion, etiqueta, lats)
            assert 2.0 < lats[-1] < 12.0, (poblacion, etiqueta, lats[-1])
            assert all(base[w]['amp'] > 0 for w in ('I', 'III', 'V'))


def test_stimulus_ratios_fall_back_to_the_adult_block():
    """Poblaciones sin ese estímulo en el JSON usan los ratios del adulto.

    El neonato solo trae click y ce_chirp: sin el fallback, pedir un burst
    devolvía los valores del click, o sea el estímulo no hacía nada.
    """
    g = _gen()
    click = g.get_baseline_values('neonate', 'click', 'air_conduction')
    burst = g.get_baseline_values('neonate', 'tone_burst', 'air_conduction', freq='500Hz')
    ls = g.get_baseline_values('neonate', 'ls_chirp', 'air_conduction')
    assert burst['V']['lat'] > click['V']['lat'] + 1.0   # 500 Hz llega mucho después
    assert ls['V']['lat'] < click['V']['lat']            # el chirp sincroniza


def test_tone_burst_interpolates_the_waves_it_does_not_describe():
    """Los bloques de burst solo traen I, III y V: II y IV se interpolan."""
    g = _gen()
    burst = g.get_baseline_values('adult_female', 'tone_burst',
                                  'air_conduction', freq='500Hz')
    assert burst['I']['lat'] < burst['II']['lat'] < burst['III']['lat']
    assert burst['III']['lat'] < burst['IV']['lat'] < burst['V']['lat']


# ------------------------------------------ replicabilidad en vivo (A/B)

def test_subaverages_average_to_the_full_curve():
    """El promedio total es exactamente el punto medio de A y B.

    Son las dos mitades de los mismos barridos: si no promedian al total,
    lo que se le muestra al alumno como replicabilidad no es el registro
    que esta mirando.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y, meta = _curva(current=1000)
    medio = (meta['sub_a'] + meta['sub_b']) / 2
    assert np.allclose(y, medio, atol=1e-9), float(np.abs(y - medio).max())


def test_subaverages_are_noisier_than_the_full_average():
    """Cada subpromedio lleva la mitad de los barridos: ~sqrt(2) mas ruido."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y, meta = _curva(current=2000)
    # Cola del registro (>9 ms): ahi no hay respuesta, es ruido y nada mas.
    cola = t > 9
    razon = meta['sub_a'][cola].std() / y[cola].std()
    assert 1.1 < razon < 1.9, razon


def test_replicability_rises_with_averaging():
    """A y B se van pegando a medida que la respuesta emerge del ruido."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    indices = [_curva(current=n)[2]['repro_index'] for n in (100, 500, 2000)]
    assert indices == sorted(indices), indices
    assert indices[0] < 0.85 < indices[-1], indices


def test_non_reproducible_patient_never_locks_ab():
    """El caso "no reproducible" tambien lo es DENTRO de una captura.

    Antes el jitter solo corria el complejo entre capturas distintas: los
    subpromedios de un paciente no reproducible convergian igual que los de
    uno normal, y "no reproducible" no se veia en vivo por ningun lado.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    def indice(jitter):
        stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': 80,
                'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
                'average': 2000, 'current_avg': 2000,
                'pathway': 'air_conduction', 'side': 'OD'}
        case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
                'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
                'repro_jitter': jitter, 'masking': 0, 'contra': None,
                'seed_key': 'caso-1', 'capture_id': 'R1'}
        return g.generate_curve('adult_female', 'normal', stim,
                                default_settings('ABR'), case)[2]['repro_index']
    assert indice(0.0) > 0.9
    assert indice(0.4) < 0.5


# ------------------------------------------------------- canal contralateral

def test_contra_channel_loses_wave_I_and_delays_wave_V():
    """El contra es el mismo generador visto desde el otro mastoides.

    Antes ABR_Curve devolvia una copia exacta del ipsi (dy = y.copy()) y la
    UI ni la dibujaba.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y, meta = _curva(current=2000)
    contra = meta['contra']
    assert contra is not None
    assert not np.array_equal(contra, y)
    ventana_i = (t > 1.2) & (t < 2.2)
    assert contra[ventana_i].max() < 0.5 * y[ventana_i].max()
    ventana_v = (t > 4.5) & (t < 7.0)
    lat_ipsi = t[ventana_v][np.argmax(y[ventana_v])]
    lat_contra = t[ventana_v][np.argmax(contra[ventana_v])]
    assert 0.05 < lat_contra - lat_ipsi < 0.4, (lat_ipsi, lat_contra)


def test_no_contra_channel_without_the_electrode():
    """Sin el electrodo del otro mastoides no hay canal contralateral."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    from abr.ABR_generator import DISCONNECTED
    electrodos = {'vertex': 'Cz', 'right': 'A2', 'left': DISCONNECTED,
                  'ground': 'Fpz'}
    _, _, meta = _curva(technical={'electrodes': electrodos})
    assert meta['contra'] is None and meta['contra_channel'] is None
    # Estimulando el otro oido, ese mismo electrodo pasa a ser el ipsi y el
    # contra existe.
    g = _gen()
    assert g.contra_channel({'electrodes': electrodos}, 'OI') == 'right'


# ------------------------------------------------------ rechazos y monitor

def test_rejected_sweeps_are_reported():
    """Presentados, aceptados y rechazados salen del generador.

    Se calculaban y no salian de ahi: ABR_Curve devolvia solo las curvas,
    asi que la UI no tenia como mostrar por que el promedio no avanzaba.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, meta = _curva(current=2000, technical={'artifact_reject_uv': 10.0})
    assert meta['accepted_sweeps'] < 2000
    assert abs(meta['accepted_sweeps'] + meta['rejected_sweeps'] - 2000) < 1e-6


def test_bad_impedance_drops_the_fsp():
    """El FSP cae con los electrodos malos, no solo el ruido.

    El FSP es una razon de varianzas: si el ruido sube, baja. Sin esto se
    podia registrar con 15 kOhm y el equipo declaraba igual "respuesta
    presente".
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, bueno = _curva(current=2000)
    malas = {'vertex': 15.0, 'right': 15.0, 'left': 15.0, 'ground': 15.0}
    _, _, malo = _curva(current=2000, technical={'impedance': malas})
    assert malo['fsp'] < bueno['fsp'] * 0.5, (bueno['fsp'], malo['fsp'])
    assert malo['fsp'] >= 1.0
    assert malo['residual_noise_nv'] > bueno['residual_noise_nv']


def test_raw_eeg_is_physiological():
    """El monitor crudo corre en decenas de uV, no en el orden de la curva."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    datos = g.raw_eeg(default_settings('ABR'), quality=1.0, seed=7, tick=1)
    assert 8 < datos['rms_R'] < 20, datos['rms_R']
    # Un EEG normal NO se pasa del rechazo de artefacto todo el tiempo: el
    # umbral mira la banda del ABR, no el EEG crudo entero.
    assert not datos['rejected_R']


def test_raw_eeg_shows_mains_without_ground():
    """Sin tierra el trazo crudo queda montado sobre el zumbido de red."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    from abr.ABR_generator import DISCONNECTED
    g = _gen()
    tech = default_settings('ABR')
    tech['electrodes'] = dict(tech['electrodes'], ground=DISCONNECTED)
    sin_tierra = g.raw_eeg(tech, seed=7, tick=1)
    con_tierra = g.raw_eeg(default_settings('ABR'), seed=7, tick=1)
    assert sin_tierra['rms_R'] > 2 * con_tierra['rms_R']
    assert sin_tierra['rejected_R']


def test_raw_eeg_is_flat_without_electrode():
    """Electrodo desconectado = canal sin registro, no un EEG limpio."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    from abr.ABR_generator import DISCONNECTED
    g = _gen()
    tech = default_settings('ABR')
    tech['electrodes'] = dict(tech['electrodes'], right=DISCONNECTED)
    datos = g.raw_eeg(tech, seed=7, tick=1)
    assert datos['R'] is None and datos['L'] is not None


def test_raw_eeg_runs_instead_of_repeating():
    """Cada tick trae EEG nuevo: es un monitor, no una foto."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    uno = g.raw_eeg(default_settings('ABR'), seed=7, tick=1)['R']
    dos = g.raw_eeg(default_settings('ABR'), seed=7, tick=2)['R']
    assert not np.array_equal(uno, dos)
    # Pero el mismo tick del mismo paciente se repite (seed estable).
    assert np.array_equal(uno, g.raw_eeg(default_settings('ABR'), seed=7, tick=1)['R'])


# ------------------------------------------------------- normativa por caso

def test_normative_band_follows_the_population():
    """La banda de la onda V sigue a la edad del paciente.

    Con la banda de adulto (fija, escrita a mano) un neonato quedaba
    SIEMPRE fuera de norma y el grafico latencia-intensidad no decia nada.
    """
    g = _gen()
    _, lo_adulto, _ = g.latency_intensity_band('adult_female')
    _, lo_neo, _ = g.latency_intensity_band('neonate')
    assert all(n > a for n, a in zip(lo_neo, lo_adulto))


def test_normative_limits_follow_intensity():
    """Una onda V de 6.4 ms es normal a 40 dB y tardia a 80.

    Es la misma funcion latencia-intensidad que dibuja la curva
    (latency_intensity_shift), no una tabla aparte.
    """
    g = _gen()
    alto = g.normative_limits('adult_female', 80)['lat']['V']
    bajo = g.normative_limits('adult_female', 40)['lat']['V']
    assert bajo[0] < 6.4 < bajo[1], bajo        # a 40 dB, normal
    assert not (alto[0] <= 6.4 <= alto[1]), alto  # a 80 dB, tardia
    assert alto[0] < 5.47 < alto[1]
    ip = g.normative_limits('adult_female', 80)['interpeak']['I-V']
    assert ip[0] < 4.0 < ip[1]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
