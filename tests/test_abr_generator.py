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
import re
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
    INTERAURAL_ATTENUATION, NEURAL_BLOQUEO_OPTIONS, NEURAL_PARAM_DEFAULTS,
    RATE_REF, STIM_MAP, agitation_factor, default_settings, select_population)
from abr.protocols import PROTOCOLS, get_protocol  # noqa: E402

NORMS = os.path.join(os.path.dirname(__file__), '..', 'resources', 'abr', 'normative_data.json')

# Mismo eje que usa generate_curve: 12 ms, 500 puntos.
T_AXIS = np.linspace(0, 12, 500)
FS = (len(T_AXIS) - 1) / (T_AXIS[-1] / 1000.0)


def _gen():
    return ABRGenerator(NORMS)


def _params(intensity, threshold=20, pathology='normal', rate=None,
            neural=None):
    g = _gen()
    values, _ = g.calculate_wave_parameters(
        g.get_baseline_values(), intensity, threshold, pathology, neural=neural)
    if rate is not None:
        values = g.apply_rate_effects(values, rate, pathology, neural)
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
        60: {'I': (1.98, 0.165), 'II': (3.06, 0.080), 'III': (4.07, 0.328),
             'IV': (5.08, 0.229), 'V': (5.89, 0.534)},
        40: {'I': (2.49, 0.039), 'II': (3.60, 0.015), 'III': (4.62, 0.227),
             'IV': (5.66, 0.140), 'V': (6.49, 0.420)},
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
    """La coclear converge a la latencia normal cuando el SL es alto.

    "Nivel alto" es nivel de SENSACIÓN alto, no dB absolutos: con umbral 45,
    100 dB son 55 dB SL y ahí la V tiene que estar donde la de un oído sano.
    """
    sano = _params(100, threshold=15, pathology='normal')
    coclear = _params(100, threshold=45, pathology='cochlear')
    assert abs(coclear['V']['lat'] - sano['V']['lat']) < 0.01
    # ...y a igual umbral la conductiva sigue atrasada: el GAP la manda al
    # tramo empinado de la función (100 dB con 30 de GAP = 70 dB efectivos).
    conduct = _params(100, threshold=45, pathology='conductive')
    assert conduct['V']['lat'] > coclear['V']['lat'] + 0.3


def test_cochlear_latency_intensity_function_is_steep():
    """Coclear = función L-I EMPINADA, no la del oído sano.

    Caso detectado probando en la app: paciente coclear, subir de 80 a 100 dB
    y ver la onda V clavada en la misma latencia. La coclear no tocaba la
    latencia (solo amplitud), así que su función L-I salía idéntica a la de un
    oído normal y con la pendiente plana del tramo alto no se movía nada.
    """
    umbral = 60
    lat = {i: _params(i, threshold=umbral, pathology='cochlear')['V']['lat']
           for i in (80, 90, 100)}
    # Sube la intensidad -> la V se acorta, y de forma legible en pantalla.
    assert lat[80] > lat[90] > lat[100]
    assert lat[80] - lat[100] > 0.4, lat
    # Cerca del umbral está prolongada respecto del oído sano a la misma
    # intensidad; a nivel alto (SL 40) converge.
    sano = {i: _params(i, threshold=15, pathology='normal')['V']['lat']
            for i in (80, 100)}
    assert lat[80] - sano[80] > 0.2, (lat[80], sano[80])
    assert abs(lat[100] - sano[100]) < 0.01, (lat[100], sano[100])


def test_high_level_slope_is_readable():
    """Arriba de 80 dB la función es plana, pero no inmóvil.

    Con 0.08 ms/10 dB, 80 -> 100 movía la V 0.16 ms: menos que el error de
    lectura del alumno sobre el trazo.
    """
    v = {i: _params(i, threshold=15)['V']['lat'] for i in (80, 90, 100)}
    assert 0.2 <= v[80] - v[100] <= 0.4, v


def test_case_deviation_grows_toward_threshold():
    """La desviación del caso se define a nivel alto y se expresa más abajo.

    Sumada igual a toda intensidad dibujaba un corrimiento paralelo (pinta de
    conductiva) en cualquier patología.
    """
    dev = {'onda_V': {'lat': 0.5, 'amp': 0.0}}
    g = _gen()
    base = g.get_baseline_values()

    def delta(intensity):
        con, _ = g.calculate_wave_parameters(base, intensity, 20, 'normal', dev)
        sin, _ = g.calculate_wave_parameters(base, intensity, 20, 'normal')
        return con['V']['lat'] - sin['V']['lat']

    assert abs(delta(80) - 0.5) < 0.01          # anclada a 80 dB
    assert delta(40) > delta(80) + 0.05         # crece hacia el umbral
    assert delta(20) < 0.5 * 1.6                # con tope, no explota


def test_normative_band_covers_the_high_intensities():
    """La banda L-I llegaba a 80: los puntos de 90 y 100 quedaban sin norma."""
    x, lo, hi = _gen().latency_intensity_band()
    assert max(x) >= 100, x
    assert all(a < b for a, b in zip(lo, hi))


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

def test_neural_interpeaks_move_independently():
    """I-III y III-V son parámetros separados, no un retraso repartido.

    Es la diferencia entre una lesión del nervio (I-III largo) y una pontina
    alta (III-V largo). Con un perfil único el retraso se repartía siempre
    igual y los dos cuadros salían iguales.
    """
    normal = _params(80, pathology='normal')
    ip = lambda v: (v['III']['lat'] - v['I']['lat'], v['V']['lat'] - v['III']['lat'])
    i_iii_n, iii_v_n = ip(normal)

    alto = _params(80, pathology='neural',
                   neural={'i_iii_ms': 0.8, 'iii_v_ms': 0.0})
    i_iii_a, iii_v_a = ip(alto)
    assert abs(i_iii_a - i_iii_n - 0.8) < 1e-9, (i_iii_n, i_iii_a)
    assert abs(iii_v_a - iii_v_n) < 1e-9, (iii_v_n, iii_v_a)

    bajo = _params(80, pathology='neural',
                   neural={'i_iii_ms': 0.0, 'iii_v_ms': 0.8})
    i_iii_b, iii_v_b = ip(bajo)
    assert abs(i_iii_b - i_iii_n) < 1e-9, (i_iii_n, i_iii_b)
    assert abs(iii_v_b - iii_v_n - 0.8) < 1e-9, (iii_v_n, iii_v_b)

    # En los dos casos la onda I se queda quieta: nace antes de la lesión.
    assert alto['I']['lat'] == bajo['I']['lat'] == normal['I']['lat']


def test_global_delay_moves_wave_I_too():
    """Conducción lenta pareja (hipotermia, depresores, prematuro).

    No es una lesión de vía: corre TODO el complejo, onda I incluida, y deja
    los interpicos intactos. Ningún otro parámetro toca la onda I.
    """
    normal = _params(80, pathology='normal')
    lento = _params(80, pathology='neural',
                    neural={'i_iii_ms': 0, 'iii_v_ms': 0, 'v_i_factor': 1.0,
                            'global_delay_ms': 1.0})
    for wave in ('I', 'III', 'V'):
        assert abs(lento[wave]['lat'] - normal[wave]['lat'] - 1.0) < 1e-9, wave


def test_proximal_block_leaves_only_wave_I():
    """Cóclea viva, bloqueo proximal: onda I sola y nada después.

    Es también el patrón que se busca en el estudio de muerte encefálica.
    """
    g = _gen()
    valores, visibles = g.calculate_wave_parameters(
        g.get_baseline_values(), 90, 20, 'neural', neural={'bloqueo': 'post_i'})
    assert visibles['I']
    assert not any(ok for wave, ok in visibles.items() if wave != 'I'), visibles


def test_total_block_leaves_no_response():
    """Ausencia total de respuesta con periferia conservada."""
    g = _gen()
    for intensity in (100, 80, 60):
        _, visibles = g.calculate_wave_parameters(
            g.get_baseline_values(), intensity, 20, 'neural',
            neural={'bloqueo': 'total'})
        assert not any(visibles.values()), (intensity, visibles)


def test_v_over_i_ratio_is_a_parameter():
    """La razón V/I se pide por número, no sale fija del perfil."""
    alta = _params(80, pathology='neural', neural={'v_i_factor': 1.0})
    baja = _params(80, pathology='neural', neural={'v_i_factor': 0.2})
    r_alta = alta['V']['amp'] / alta['I']['amp']
    r_baja = baja['V']['amp'] / baja['I']['amp']
    assert r_baja < 1.0 < r_alta, (r_baja, r_alta)
    # La onda I no se toca en ninguno de los dos.
    assert abs(alta['I']['amp'] - baja['I']['amp']) < 1e-9


def test_desync_widens_the_waves():
    """Morfología pobre: ondas anchas y romas antes de desaparecer."""
    nitido = _params(80, pathology='neural', neural={'desincronia': 'ninguna'})
    ancho = _params(80, pathology='neural', neural={'desincronia': 'alta'})
    assert ancho['V']['width'] > nitido['V']['width'] * 1.5


def test_rate_sensitivity_is_graduated():
    """Fatiga de conducción a tasas altas: graduable, no un interruptor."""
    def amp_v(sens):
        return _params(80, pathology='neural', rate=90.0,
                       neural={'sensibilidad_tasa': sens})['V']['amp']
    assert amp_v('normal') > amp_v('moderada') > amp_v('severa')


def test_microphonic_only_pattern_follows_polarity():
    """Desincronía: sin ondas, pero con microfónico que invierte.

    Es lo que separa una desincronía de una ausencia de respuesta de verdad:
    se busca con rarefacción y condensación por separado (con alternada el
    CM se cancela y no se ve nada).
    """
    g = _gen()
    ansd = {'bloqueo': 'total', 'microfonica': 'amplificada'}
    valores, visibles = g.calculate_wave_parameters(
        g.get_baseline_values(), 90, 20, 'neural', neural=ansd)
    assert not any(visibles.values())
    _, cm_rar = g.apply_polarity_effects(dict(valores), 'Rarefacción', 'neural', ansd)
    _, cm_con = g.apply_polarity_effects(dict(valores), 'Condensación', 'neural', ansd)
    _, cm_alt = g.apply_polarity_effects(dict(valores), 'Alternada', 'neural', ansd)
    assert cm_rar * cm_con < 0, (cm_rar, cm_con)
    assert cm_alt is None
    # Una ausencia de respuesta SIN desincronía no deja microfónico grande.
    _, cm_mudo = g.apply_polarity_effects(
        dict(valores), 'Rarefacción', 'neural', {'bloqueo': 'total'})
    assert abs(cm_rar) > 4 * abs(cm_mudo), (cm_rar, cm_mudo)


def test_neural_defaults_reproduce_the_old_single_profile():
    """Caso guardado antes de los parámetros: dibuja lo de siempre.

    Los defaults (I-III y III-V 0.2 ms, V/I 0.45, tasa severa) son el cuadro
    que daba el modelo cuando "neural" era uno solo.
    """
    viejo = _params(80, pathology='neural')                    # sin parámetros
    explicito = _params(80, pathology='neural', neural=dict(NEURAL_PARAM_DEFAULTS))
    raro = _params(80, pathology='neural', neural={'bloqueo': 'no-existe'})
    for wave in ('I', 'III', 'V'):
        assert viejo[wave]['lat'] == explicito[wave]['lat'] == raro[wave]['lat']
        assert viejo[wave]['amp'] == explicito[wave]['amp'] == raro[wave]['amp']
    # Y la razón V/I sigue dentro del rango que declara normative_data.json.
    ratio = viejo['V']['amp'] / viejo['I']['amp']
    rango = _gen().norms['pathology_modifiers']['neural']['amplitude_v_i_ratio']
    assert rango[0] <= ratio <= rango[1], ratio


def test_neural_param_keys_match_the_backend():
    """Los parámetros del patrón son un contrato entre PHP y Python.

    El backend arma cases.data['ABR'][lado]['neural'] con estas claves; si
    una se renombra de un solo lado, el generador la ignora en silencio y el
    caso dibuja el default sin que nadie se entere.
    """
    php = os.path.join(os.path.dirname(__file__), '..', 'labsim_backend',
                       'src', 'CaseBuilder.php')
    if not os.path.exists(php):
        print("  (salteado: sin el backend en el checkout)")
        return
    with open(php, encoding='utf-8') as fh:
        texto = fh.read()
    bloque = texto.split('ABR_NEURAL_DEFAULTS = [', 1)[1].split('];', 1)[0]
    claves = set(re.findall(r"'([a-z_]+)' =>", bloque))
    assert claves == set(NEURAL_PARAM_DEFAULTS), (
        claves ^ set(NEURAL_PARAM_DEFAULTS))
    # Y los enums que el formulario ofrece tienen que existir en el modelo.
    bloqueos = set(re.findall(r"'([a-z_]+)'", texto.split(
        'ABR_NEURAL_BLOQUEO_OPTIONS = [', 1)[1].split('];', 1)[0]))
    assert bloqueos == set(NEURAL_BLOQUEO_OPTIONS), bloqueos


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
    # El ruido se mide como lo mide el equipo (A - B, donde la senial se
    # cancela) y no con la desviacion de la cola del trazo: ahi tambien
    # hay SN10 y onda VII, y la comparacion terminaba dependiendo de
    # cuanta senial quedaba en esos ultimos milisegundos.
    _, _, meta_habitual = _curva()
    _, _, meta_sin = _curva(technical={'artifact_reject_uv': 0.0})
    assert meta['residual_noise_nv'] > meta_habitual['residual_noise_nv']
    assert meta_sin['residual_noise_nv'] > meta_habitual['residual_noise_nv']


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
    """Los 11 estímulos del combo dan ondas ordenadas en las 5 poblaciones."""
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
    ls = g.get_baseline_values('neonate', 'ce_chirp_ls', 'air_conduction')
    assert burst['V']['lat'] > click['V']['lat'] + 1.0   # 500 Hz llega mucho después
    assert ls['V']['lat'] < click['V']['lat']            # el chirp sincroniza


def test_every_stimulus_changes_the_response_in_both_pathways():
    """Ningun estimulo puede dar la curva del click, por aire NI por hueso.

    La via osea del JSON solo describe click y burst: los chirps caian al
    bloque del click y el combo dejaba de hacer efecto apenas se cambiaba
    el transductor (el estimulo estaba, pero el potencial salia identico).
    """
    from abr.ABR_generator import STIM_MAP
    g = _gen()
    for via in ('air_conduction', 'bone_conduction'):
        click = g.get_baseline_values('adult_female', 'click', via)
        for etiqueta, (stim, freq) in STIM_MAP.items():
            if stim == 'click':
                continue
            base = g.get_baseline_values('adult_female', stim, via, freq=freq)
            distinto = any(abs(base[w]['lat'] - click[w]['lat']) > 0.02
                           or abs(base[w]['amp'] - click[w]['amp']) > 0.01
                           for w in ('I', 'III', 'V'))
            assert distinto, (via, etiqueta)


def test_narrow_band_chirp_sits_between_the_burst_and_the_wide_chirp():
    """El NB CE-Chirp LS es frecuencia especifico pero sincroniza mejor.

    Onda V antes que el burst de la misma banda (compensa el retardo de la
    onda viajera) y despues del chirp de banda ancha, con mas amplitud que
    el burst.
    """
    g = _gen()
    ancho = g.get_baseline_values('adult_female', 'ce_chirp_ls', 'air_conduction')
    for freq in ('500Hz', '1000Hz', '2000Hz', '4000Hz'):
        nb = g.get_baseline_values('adult_female', 'nb_ce_chirp_ls',
                                   'air_conduction', freq=freq)
        burst = g.get_baseline_values('adult_female', 'tone_burst',
                                      'air_conduction', freq=freq)
        assert ancho['V']['lat'] <= nb['V']['lat'] < burst['V']['lat'], freq
        assert burst['V']['amp'] < nb['V']['amp'] <= ancho['V']['amp'] * 1.05, freq


def test_old_case_keys_still_find_their_threshold():
    """Un caso guardado con 'ls_chirp' sigue leyendo su umbral.

    Sin el alias, la tabla del caso no matcheaba la clave nueva y el umbral
    caia al escalar del oido: el estimulo dejaba de hacer efecto en
    silencio, que es exactamente el sintoma que motivo el cambio.
    """
    g = _gen()
    caso = {'umbral': 80, 'umbral_por_estimulo': dict(DESCENDENTE)}
    caso['umbral_por_estimulo']['ls_chirp'] = caso['umbral_por_estimulo'].pop('ce_chirp_ls')
    assert g.case_threshold(caso, _stim('ce_chirp_ls'), 'air_conduction',
                            'normal') == 50


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
    # Curva sin respuesta (estimulo bajo el umbral): asi el trazo entero
    # es ruido y nada mas. Medirlo en la cola del registro ya no sirve:
    # ahi tambien viven el SN10 y la onda VII.
    t, y, meta = _curva(intensity=20, threshold=60, current=2000)
    razon = meta['sub_a'].std() / y.std()
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


# ------------------------------------------------ falsa onda V (artefacto)

def _curva_falsa(amp=0.25, lat=8.5, mitad='a', current=2000, intensity=80,
                 rango=None, **kw):
    """Igual que _curva pero con la falsa onda V del caso configurada.

    La latencia por defecto es 8.5 ms -- fuera de la respuesta real, para
    que el test mida el artefacto y no la onda V del paciente.
    """
    g = _gen()
    stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': intensity,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
            'average': 2000, 'current_avg': current, 'pathway': 'air_conduction'}
    case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
            'masking': 0, 'contra': None, 'seed_key': 'caso-1',
            'capture_id': 'R1'}
    case.update(kw)
    if amp:
        case['falsa_v'] = {'amp': amp, 'lat': lat, 'mitad': mitad}
        if rango:
            case['falsa_v']['int_min'], case['falsa_v']['int_max'] = rango
    tech = default_settings('ABR')
    return g.generate_curve('adult_female', 'normal', stim, tech, case)


def test_false_wave_lives_in_one_half_only():
    """El artefacto esta entero en un subpromedio y nada en el otro.

    Es la unica pista que tiene el alumno: en el promedio se ve una onda
    plausible, y solo comparando A con B se descubre que no replica.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y, meta = _curva_falsa(mitad='a')
    _, y0, base = _curva_falsa(amp=0)
    i = int(np.argmin(np.abs(t - 8.5)))
    en_a = meta['sub_a'][i] - base['sub_a'][i]
    en_b = meta['sub_b'][i] - base['sub_b'][i]
    assert en_a > 0.3, en_a                      # entero en A
    assert abs(en_b) < 0.01, en_b                # nada en B
    # En el promedio, la mitad: es (A+B)/2 y el artefacto vive en una sola.
    assert abs((y[i] - y0[i]) - en_a / 2) < 0.01

    # La otra mitad, con el mismo caso salvo el lado elegido.
    t, y, meta = _curva_falsa(mitad='b')
    assert abs(meta['sub_a'][i] - base['sub_a'][i]) < 0.01
    assert meta['sub_b'][i] - base['sub_b'][i] > 0.3


def test_false_wave_looks_like_a_real_wave_v():
    """Tiene el ancho de una onda V: no se descarta por la forma."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y, meta = _curva_falsa(amp=0.4)
    _, y0, _ = _curva_falsa(amp=0)
    solo = y - y0
    ventana = (t > 7.5) & (t < 9.5)
    pico = t[ventana][np.argmax(solo[ventana])]
    assert abs(pico - 8.5) < 0.2, pico
    # Ancho a media altura del orden de una onda V (sigma 0.18 ms).
    media = solo[ventana].max() / 2
    ancho = float(np.sum(solo[ventana] > media) * (t[1] - t[0]))
    assert 0.25 < ancho < 0.7, ancho


def test_false_wave_fades_with_averaging_but_not_as_fast_as_noise():
    """Promediar mas la achica -- si no, hacer lo correcto no serviria.

    Pero promedia peor que el ruido de fondo (es de baja frecuencia), asi
    que sigue ahi el tiempo suficiente para que el ejercicio exista.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    def altura(n):
        t, y, meta = _curva_falsa(current=n)
        _, _, base = _curva_falsa(amp=0, current=n)
        i = int(np.argmin(np.abs(t - 8.5)))
        return meta['sub_a'][i] - base['sub_a'][i]
    poco, medio, mucho = altura(200), altura(2000), altura(8000)
    assert poco > medio > mucho, (poco, medio, mucho)
    assert poco / mucho < 4.0, poco / mucho     # cae, pero no se borra


def test_false_wave_raises_residual_noise_but_not_fsp():
    """Sube el ruido residual y NO toca el FSP.

    El residual sale de A - B, donde el artefacto no se cancela: el equipo
    reporta mas ruido, que es la pista numerica coherente. El FSP no se
    mueve porque es del caso -- si subiera, el equipo estaria declarando
    respuesta presente sobre un artefacto.

    El indice de replicabilidad global NO sirve de pista: es una
    correlacion sobre los 12 ms enteros, dominada por el drift comun a las
    dos mitades. Por eso el ejercicio es mirar A y B en la latencia de la
    onda, no leer un numero.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, con = _curva_falsa(lat=5.6, umbral=90)
    _, _, sin = _curva_falsa(amp=0, umbral=90)
    assert con['residual_noise_nv'] > sin['residual_noise_nv'] * 1.5
    assert abs(con['fsp'] - sin['fsp']) < 1e-9


def test_false_wave_only_in_its_intensity_range():
    """Fuera del rango configurado la serie queda limpia.

    Es lo que deja al alumno usar la segunda prueba real: en las curvas
    donde la falsa onda no esta, la V verdadera migra en latencia con la
    intensidad -- y la falsa, en las suyas, no se mueve nunca.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    def altura(intensity):
        t, y, meta = _curva_falsa(intensity=intensity, rango=(20, 40))
        _, _, base = _curva_falsa(amp=0, intensity=intensity)
        i = int(np.argmin(np.abs(t - 8.5)))
        return meta['sub_a'][i] - base['sub_a'][i]
    assert altura(30) > 0.3                 # dentro del rango
    assert abs(altura(60)) < 0.01           # por encima
    assert abs(altura(10)) < 0.01           # por debajo


def _curva_tec(intensity=80, transducer='insert_earphone', clamp=False,
               pathology='normal', neural=None, pol='Alternada', **kw):
    """Curva con el equipo en cierto estado (transductor, tubo pinzado)."""
    g = _gen()
    stim = {'stim': 'click', 'freq': None, 'pol': pol, 'int': intensity,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
            'average': 2000, 'current_avg': 2000, 'pathway': 'air_conduction'}
    tech = default_settings('ABR')
    tech.update({'transducer': transducer, 'tube_clamped': clamp})
    case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
            'masking': 0, 'contra': None, 'seed_key': 'caso-1',
            'capture_id': 'R1', 'neural': neural}
    case.update(kw)
    return g.generate_curve('adult_female', pathology, stim, tech, case)


# ------------------------------------------------- SN10 y banda mal puesta

def test_sn10_is_slow_and_deep():
    """El valle que sigue a la V es lento y grande, no otra ondita.

    De el dependen las dos cosas: la amplitud de V se mide de pico a valle
    contra el SN10, y por ser lento es lo primero que se lleva un
    pasa-alto mal puesto.
    """
    g = _gen()
    valores = _params(80)
    y = g.build_target_curve(T_AXIS, valores)
    lat_v = valores['V']['lat']
    valle = (T_AXIS > lat_v) & (T_AXIS < lat_v + 3.5)
    fondo = T_AXIS[valle][np.argmin(y[valle])]
    assert lat_v + 0.8 < fondo < lat_v + 2.2, fondo
    profundidad = -y[valle].min()
    assert profundidad > valores['V']['amp'] * 0.3, profundidad
    # Ancho a media profundidad: mas de un ms, o sea mas lento que una
    # onda neural (que dura decimas).
    ancho = float(np.sum(y[valle] < y[valle].min() / 2)
                  * (T_AXIS[1] - T_AXIS[0]))
    assert ancho > 0.8, ancho


def test_a_high_high_pass_eats_the_amplitude_not_the_latency():
    """Subir el pasa-alto achica la amplitud medida y deja la latencia.

    Es el error de medir con la banda equivocada y comparar igual contra
    la normativa: la onda sigue donde estaba, pero es la mitad de alta.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    def pico_valle(hp):
        t, y, _ = _curva(filter_high=hp)
        zona = (t > 4) & (t < 9)
        return t[zona][np.argmax(y[zona])], y[zona].max() - y[zona].min()
    lat_ok, pv_ok = pico_valle(100)
    lat_mal, pv_mal = pico_valle(300)
    assert pv_mal < pv_ok * 0.85, (pv_ok, pv_mal)
    assert abs(lat_mal - lat_ok) < 0.2, (lat_ok, lat_mal)
    # Y con el pasa-alto en 750 no queda casi nada que medir.
    _, pv_peor = pico_valle(750)
    assert pv_peor < pv_mal


# --------------------------------------- agitacion del paciente (tramos)

def _curva_agit(inquietud=0.6, current=2000, reject=25.0, **kw):
    """Curva de un paciente que se mueve durante la captura."""
    g = _gen()
    stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': 40,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
            'average': 2000, 'current_avg': current, 'pathway': 'air_conduction'}
    tech = default_settings('ABR')
    tech['artifact_reject_uv'] = reject
    case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
            'masking': 0, 'contra': None, 'seed_key': 'caso-1',
            'capture_id': 'R1', 'inquietud': inquietud}
    case.update(kw)
    return g.generate_curve('adult_female', 'normal', stim, tech, case)


def test_a_still_patient_is_unchanged():
    """inquietud 0 = lo de siempre: los casos viejos no se mueven."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, con, meta_con = _curva_agit(inquietud=0)
    _, sin, meta_sin = _curva_agit(inquietud=None)
    assert np.array_equal(con, sin)
    assert meta_con['accepted_sweeps'] == meta_sin['accepted_sweeps'] == 2000
    assert meta_con['agitation'] == 1.0


def test_moving_patient_loses_sweeps_to_the_reject():
    """Con rechazo puesto, los barridos del movimiento no promedian.

    El equipo sigue contando los presentados -- el contador sube igual --
    pero el promedio avanza con menos, y el FSP va con los que entraron.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, quieto = _curva_agit(inquietud=0)
    _, _, movido = _curva_agit(inquietud=0.6)
    assert movido['accepted_sweeps'] < quieto['accepted_sweeps'] * 0.9
    assert movido['current_avg'] == quieto['current_avg']    # presentados
    assert movido['fsp'] < quieto['fsp']


def test_without_reject_the_movement_enters_the_average():
    """Rechazo apagado: la basura entra y el FSP no cruza nunca.

    Es la diferencia que hay que poder mostrar -- apagar el rechazo no
    "acelera" la prueba, la arruina.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, con_rechazo = _curva_agit(inquietud=0.6, reject=25.0)
    _, _, sin_rechazo = _curva_agit(inquietud=0.6, reject=None)
    assert sin_rechazo['accepted_sweeps'] > con_rechazo['accepted_sweeps']
    assert sin_rechazo['residual_noise_nv'] > con_rechazo['residual_noise_nv'] * 2
    assert sin_rechazo['fsp'] < 1.5 < con_rechazo['fsp']


def test_agitation_comes_in_runs_and_repeats():
    """Los episodios duran varios bloques y son los mismos siempre.

    Si cada bloque se sorteara solo, el paciente "tiritaria" en vez de
    moverse; y si no fuera determinista, el mismo caso se veria distinto
    en cada corrida y no se podria enseñar sobre el.
    """
    serie = [ABRGenerator.agitation_run('caso-1', 0.8, i) for i in range(80)]
    otra = [ABRGenerator.agitation_run('caso-1', 0.8, i) for i in range(80)]
    assert serie == otra
    assert max(serie) > 2.0 and min(serie) == 1.0
    # Cada tramo es homogeneo: 4 bloques con el mismo factor.
    for inicio in range(0, 80, 4):
        assert len(set(serie[inicio:inicio + 4])) == 1
    # Otro caso, otros momentos.
    assert serie != [ABRGenerator.agitation_run('caso-2', 0.8, i) for i in range(80)]


def test_the_eeg_monitor_shares_the_agitation():
    """El monitor se ensucia en el MISMO tramo en que se descartan barridos.

    Si el trazo se ve limpio mientras el promedio no avanza, el equipo le
    esta mintiendo al alumno.
    """
    caso = {'fsp_puntos': {'800': 2.3, '2000': 2.8}, 'inquietud': 0.8}
    factores = [agitation_factor(caso, i) for i in range(80)]
    assert max(factores) > 2.0
    assert agitation_factor(dict(caso, inquietud=0), 3) == 1.0


# ------------------------------------------ reflejo post-auricular (PAM)

def _curva_pam(pam=0.8, intensity=90, window=20.0, filter_high=100,
               clamp=False, **kw):
    """Curva con reflejo post-auricular, en ventana larga para verlo."""
    g = _gen()
    stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': intensity,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': filter_high,
            'average': 2000, 'current_avg': 2000, 'pathway': 'air_conduction'}
    tech = default_settings('ABR')
    tech['window_ms'] = window
    tech['tube_clamped'] = clamp
    case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
            'masking': 0, 'contra': None, 'seed_key': 'caso-1',
            'capture_id': 'R1', 'pam': pam}
    case.update(kw)
    return g.generate_curve('adult_female', 'normal', stim, tech, case)


def test_pam_is_late_big_and_needs_a_loud_click():
    """13 ms, en uV, y solo con sonido fuerte: es un reflejo, tiene umbral."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y, _ = _curva_pam(intensity=90)
    tardio = t > 10
    pico = t[tardio][np.argmax(y[tardio])]
    assert abs(pico - 13.0) < 1.5, pico
    assert y[tardio].max() > 0.8, y[tardio].max()   # uV, no decimas
    # Por debajo del umbral del reflejo no hay nada.
    _, bajo, _ = _curva_pam(intensity=50)
    assert bajo[tardio].max() < 0.2, bajo[tardio].max()
    # Y crece con el nivel.
    _, medio, _ = _curva_pam(intensity=75)
    assert medio[tardio].max() < y[tardio].max()


def test_pam_replicates_in_both_subaverages():
    """El contraejemplo de la falsa onda V: A/B NO lo delata.

    Se promedia como cualquier respuesta, asi que aparece igual en las dos
    mitades. Lo delatan la latencia y el tamanio, no la replicabilidad.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, y, meta = _curva_pam()
    i = int(np.argmin(np.abs(t - 13.0)))
    assert meta['sub_a'][i] > 0.8 and meta['sub_b'][i] > 0.8
    assert abs(meta['sub_a'][i] - meta['sub_b'][i]) < 0.3


def test_pam_does_not_move_the_fsp():
    """El equipo no lo mide como respuesta -- lo mide el alumno con el cursor."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, _, con = _curva_pam(pam=0.8)
    _, _, sin = _curva_pam(pam=0)
    assert abs(con['fsp'] - sin['fsp']) < 1e-9


def test_pam_shrinks_with_a_higher_high_pass():
    """Es lento: subir el pasa-alto se lo come, y eso es una maniobra."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, abierto, _ = _curva_pam(filter_high=30)
    _, cerrado, _ = _curva_pam(filter_high=300)
    tardio = t > 10
    assert cerrado[tardio].max() < abierto[tardio].max() / 2


def test_pam_barely_fits_the_routine_window():
    """En 12 ms apenas asoma: se ve entero cuando se abre la ventana."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t12, corta, _ = _curva_pam(window=12.0)
    t20, larga, _ = _curva_pam(window=20.0)
    assert corta.max() < larga[t20 > 10].max()


def test_clamping_the_tube_removes_the_pam():
    """Sin sonido no hay reflejo: la maniobra tambien lo apaga."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, abierto, _ = _curva_pam()
    _, pinzado, _ = _curva_pam(clamp=True)
    tardio = t > 10
    assert pinzado[tardio].max() < abierto[tardio].max() / 3


# ------------------------------------------ artefacto de estimulo y clamp

def test_stimulus_artifact_grows_with_intensity_and_transducer():
    """Es electrico: sube con el nivel y el insert casi no lo tiene.

    A intensidades altas cae justo donde va la onda I, que es el error que
    produce -- se lee I donde solo hay estimulo.
    """
    g = _gen()
    t = np.linspace(0, 12, 500)
    alto = g.add_transducer_artifact(t, 'TDH39_headphone', 100).max()
    medio = g.add_transducer_artifact(t, 'TDH39_headphone', 80).max()
    bajo = g.add_transducer_artifact(t, 'TDH39_headphone', 40).max()
    assert alto > medio * 4 > bajo * 100, (alto, medio, bajo)
    # El insert deja la bobina a 33 cm del electrodo.
    insert = g.add_transducer_artifact(t, 'insert_earphone', 100).max()
    assert insert < alto / 2, (insert, alto)
    # Vive en el primer ms, donde se busca la onda I.
    pico = t[np.argmax(g.add_transducer_artifact(t, 'TDH39_headphone', 100))]
    assert pico < 1.0, pico


def test_clamping_the_tube_kills_the_response_but_not_the_artifact():
    """La maniobra: sin sonido no hay respuesta, el artefacto sigue.

    Es la prueba de que lo que se ve en los primeros ms no es onda I.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    t, abierto, _ = _curva_tec()
    _, pinzado, meta = _curva_tec(clamp=True)
    # La onda V se cae.
    ventana_v = (t > 5) & (t < 7)
    assert pinzado[ventana_v].max() < abierto[ventana_v].max() / 3
    assert meta['tube_clamped'] is True
    # Sin estimulo el equipo no puede declarar respuesta presente.
    assert meta['fsp'] == 1.0
    # Pero el artefacto de estimulo sigue ahi (mismo equipo, misma corriente).
    _, sup_abierto, _ = _curva_tec(intensity=100, transducer='TDH39_headphone')
    _, sup_pinzado, _ = _curva_tec(intensity=100, transducer='TDH39_headphone',
                                   clamp=True)
    # Filtrado queda bifasico (el pasa-alto le saca el DC), asi que se
    # mide en valor absoluto: lo que importa es que siga estando.
    inicio = t < 1.5
    assert np.abs(sup_pinzado[inicio]).max() > 0.3, np.abs(sup_pinzado[inicio]).max()
    assert np.abs(sup_abierto[inicio]).max() > 0.3


def test_clamping_does_nothing_without_a_tube():
    """Supraaural y vibrador no tienen tubo que pinzar."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    for transductor in ('TDH39_headphone', 'bone_vibrator'):
        _, abierto, _ = _curva_tec(transducer=transductor)
        _, pinzado, meta = _curva_tec(transducer=transductor, clamp=True)
        assert np.array_equal(abierto, pinzado), transductor
        assert meta['tube_clamped'] is False


def test_clamping_removes_the_microphonic_too():
    """En neuropatia: la microfonica se va con el sonido, el artefacto no.

    Es la unica forma real de separarlas -- las dos siguen al estimulo y
    las dos estan en los primeros ms.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    neural = {'microfonica': 'amplificada', 'bloqueo': 'total'}
    t, abierto, _ = _curva_tec(pathology='neural', neural=neural,
                               pol='Rarefacción')
    _, pinzado, _ = _curva_tec(pathology='neural', neural=neural,
                               pol='Rarefacción', clamp=True)
    cm = (t > 0.3) & (t < 1.5)
    assert np.abs(pinzado[cm]).max() < np.abs(abierto[cm]).max() / 2


def test_the_false_wave_survives_the_clamp():
    """Pinzar no la borra: no es respuesta, y por eso se descubre.

    Es la segunda maniobra que la delata, ademas de A/B.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    def altura(clamp):
        """Cuanto aporta la falsa onda en 8.5 ms, con y sin ella."""
        def corre(con_falsa):
            stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada',
                    'int': 80, 'rate': 21.1, 'filter_down': 3000,
                    'filter_passhigh': 100, 'average': 2000,
                    'current_avg': 2000, 'pathway': 'air_conduction'}
            tech = default_settings('ABR')
            tech['tube_clamped'] = clamp
            case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
                    'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
                    'masking': 0, 'contra': None, 'seed_key': 'caso-1',
                    'capture_id': 'R1'}
            if con_falsa:
                case['falsa_v'] = {'amp': 0.3, 'lat': 8.5, 'mitad': 'a'}
            t, y, meta = g.generate_curve('adult_female', 'normal', stim,
                                          tech, case)
            i = int(np.argmin(np.abs(t - 8.5)))
            return meta['sub_a'][i]
        return corre(True) - corre(False)
    assert altura(True) > 0.3
    assert abs(altura(True) - altura(False)) < 0.05


def test_false_wave_is_off_by_default():
    """Sin configurarla no existe: los casos viejos no cambian."""
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    _, y0, _ = _curva_falsa(amp=0)
    _, y1, _ = _curva_falsa(amp=0.0, lat=8.5)
    assert np.array_equal(y0, y1)
    g = _gen()
    for cfg in ({}, {'falsa_v': None}, {'falsa_v': {'amp': 0}},
                {'falsa_v': {'amp': 0.3, 'lat': 99}}):   # fuera de ventana
        stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': 80,
                'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
                'average': 2000, 'current_avg': 2000,
                'pathway': 'air_conduction'}
        case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
                'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
                'masking': 0, 'contra': None, 'seed_key': 'caso-1',
                'capture_id': 'R1'}
        case.update(cfg)
        _, y, _ = g.generate_curve('adult_female', 'normal', stim,
                                   default_settings('ABR'), case)
        assert np.allclose(y, y0), cfg


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
    """El monitor corre en la BANDA del equipo, no en banda ancha.

    El EEG de banda ancha son ~12 uV RMS y cruzaria los +-25 uV del
    rechazo casi siempre; lo que un equipo muestra (y lo unico contra lo
    que tiene sentido comparar el umbral) es el canal ya filtrado, que con
    los electrodos bien puestos queda en ~2 uV.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    datos = g.raw_eeg(default_settings('ABR'), quality=1.0, seed=7, tick=1)
    assert 1.0 < datos['rms_R'] < 4.0, datos['rms_R']
    # Un EEG normal NO se pasa del rechazo de artefacto: si lo hiciera, el
    # promedio tampoco avanzaria (misma cuenta en artifact_acceptance).
    assert not datos['rejected_R']


def test_raw_eeg_and_the_average_reject_together():
    """Monitor sucio = promedio frenado, y al reves.

    Era la incoherencia del modulo: el monitor golpeando la barra de
    rechazo mientras el promediador aceptaba el 100% de los barridos.
    """
    if not HAS_SCIPY:
        print("  (salteado: sin scipy)")
        return
    g = _gen()
    tech = default_settings('ABR')
    limpio = g.raw_eeg(tech, quality=1.0, seed=7, tick=1)
    assert g.artifact_acceptance(tech['artifact_reject_uv'], 1.0,
                                 g.reject_impedance_factor(2.0)) == 1.0
    assert not limpio['rejected_R']

    tech['impedance'] = dict(tech['impedance'], vertex=12.0)
    sucio = g.raw_eeg(tech, quality=1.0, seed=7, tick=1)
    assert sucio['rms_R'] > 4 * limpio['rms_R']
    assert sucio['rejected_R']
    assert g.artifact_acceptance(tech['artifact_reject_uv'], 1.0,
                                 g.reject_impedance_factor(12.0)) < 0.5


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
    assert not con_tierra['mains_R']
    # El zumbido es la mayor parte de lo que se ve, y NO lo descarta el
    # rechazo: se cuela bajo el umbral y arruina el promedio igual. Por eso
    # el monitor ademas lo nombra (ver EEG.push).
    assert sin_tierra['mains_R'] > 0.5 * sin_tierra['rms_R']
    assert not sin_tierra['rejected_R']


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


# ------------------------------- umbral por estimulo (perfil auditivo)

# Tabla como la que emite CaseProfile::abrThresholds en el backend para una
# hipoacusia descendente (graves conservados, 4 kHz en 70 dB HL).
DESCENDENTE = {
    'tone_burst_500Hz': 30, 'tone_burst_1000Hz': 30,
    'tone_burst_2000Hz': 50, 'tone_burst_4000Hz': 75,
    'nb_ce_chirp_ls_500Hz': 25, 'nb_ce_chirp_ls_1000Hz': 25,
    'nb_ce_chirp_ls_2000Hz': 45, 'nb_ce_chirp_ls_4000Hz': 70,
    'click': 65, 'ce_chirp': 50, 'ce_chirp_ls': 50,
}


def _stim(stim, freq=None):
    return {'stim': stim, 'freq': freq, 'int': 60, 'pathway': 'air_conduction'}


def test_threshold_falls_back_to_the_scalar_without_a_table():
    """Caso guardado antes del perfil: sigue leyendo el umbral escalar."""
    g = _gen()
    caso = {'umbral': 45}
    for stim, freq in (('click', None), ('tone_burst', '500Hz')):
        assert g.case_threshold(caso, _stim(stim, freq), 'air_conduction',
                                'normal') == 45


def test_threshold_falls_back_to_the_norm_without_a_case():
    """Sin caso no se inventa nada: el minimo normativo de la patologia."""
    g = _gen()
    esperado = g.norms['pathology_modifiers']['normal']['threshold_range'][0]
    assert g.case_threshold(None, _stim('click'), 'air_conduction',
                            'normal') == esperado


def test_threshold_is_frequency_specific():
    """El problema que motivo el perfil: 500 Hz y 4 kHz tienen que diferir.

    Antes el caso traia un solo umbral por oido y el estimulo solo movia
    latencias (get_baseline_values), asi que una hipoacusia descendente
    respondia igual a un burst de 500 que a uno de 4 kHz.
    """
    g = _gen()
    caso = {'umbral': 65, 'umbral_por_estimulo': DESCENDENTE}
    b500 = g.case_threshold(caso, _stim('tone_burst', '500Hz'),
                            'air_conduction', 'cochlear')
    b4k = g.case_threshold(caso, _stim('tone_burst', '4000Hz'),
                           'air_conduction', 'cochlear')
    assert b500 == 30
    assert b4k == 75
    assert b4k - b500 == 45


def test_click_follows_the_cochlear_base_not_the_low_frequencies():
    """El click de una descendente sale elevado aunque los graves esten bien."""
    g = _gen()
    caso = {'umbral': 65, 'umbral_por_estimulo': DESCENDENTE}
    click = g.case_threshold(caso, _stim('click'), 'air_conduction', 'cochlear')
    b500 = g.case_threshold(caso, _stim('tone_burst', '500Hz'),
                            'air_conduction', 'cochlear')
    assert click > b500 + 30


def test_bone_pathway_uses_its_own_table():
    """Conductiva: la via osea tiene su propia tabla, y ahi esta el gap."""
    g = _gen()
    caso = {
        'umbral': 55,
        'umbral_por_estimulo': {'click': 55},
        'umbral_por_estimulo_oseo': {'click': 15},
    }
    stim = _stim('click')
    assert g.case_threshold(caso, stim, 'air_conduction', 'conductive') == 55
    assert g.case_threshold(caso, stim, 'bone_conduction', 'conductive') == 15


def test_response_dies_in_the_high_frequencies_of_a_descending_loss():
    """Misma intensidad, dos estimulos: en 4 kHz no queda nivel de sensacion."""
    g = _gen()
    base = g.get_baseline_values()
    intensidad = 60
    v500, _ = g.calculate_wave_parameters(
        base, intensidad, DESCENDENTE['tone_burst_500Hz'], 'cochlear')
    v4k, visibles = g.calculate_wave_parameters(
        base, intensidad, DESCENDENTE['tone_burst_4000Hz'], 'cochlear')
    # 30 dB SL contra -15 dB SL: la V de 4 kHz tiene que quedar muy por
    # debajo, que es lo que el alumno lee como "no hay respuesta".
    assert v4k['V']['amp'] < 0.2 * v500['V']['amp']


def test_shadow_curve_uses_the_contralateral_table():
    """El oido no evaluado tambien responde por frecuencia.

    Con un contralateral descendente, un burst de 4 kHz que cruza el craneo
    no puede dar sombra: para esa coclea el nivel queda bajo su umbral.
    """
    g = _gen()
    ia = INTERAURAL_ATTENUATION['insert_earphone']
    contra = {'umbral': 30, 'type': 'normal', 'umbral_por_estimulo': DESCENDENTE}
    caso = {'contra': contra}
    grave = {'stim': 'tone_burst', 'freq': '500Hz', 'int': 100,
             'pathway': 'air_conduction'}
    agudo = dict(grave, freq='4000Hz')
    assert g.shadow_values('adult_female', 'air_conduction', grave, 0, ia,
                           caso) is not None
    assert g.shadow_values('adult_female', 'air_conduction', agudo, 0, ia,
                           caso) is None


def test_stim_key_matches_the_normative_keys():
    """La clave del caso y la del normativo tienen que ser la misma."""
    g = _gen()
    for etiqueta, (stim, freq) in STIM_MAP.items():
        clave = g.stim_key(stim, freq)
        assert clave in DESCENDENTE, (etiqueta, clave)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
