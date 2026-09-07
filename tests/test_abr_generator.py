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
    ABRGenerator, INTERAURAL_ATTENUATION, RATE_REF, select_population)

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
           seed_key='caso-1', fsp=(2.3, 2.8)):
    """Corre generate_curve con un caso completo (necesita scipy)."""
    g = _gen()
    stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': intensity,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
            'average': target, 'current_avg': current, 'pathway': 'air_conduction'}
    tech = {'impedance': 3.0, 'transducer': 'insert_earphone'}
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
        ruido = g.averaged_noise(T_AXIS, n, 2000, 1.0, np.random.default_rng(11), 3.0)
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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
