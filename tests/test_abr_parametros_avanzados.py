"""
Efecto en el trazo de los parámetros de Parámetros avanzados.

Estuvieron un tiempo en el diálogo sin hacer nada (UNCONNECTED_SETTINGS).
Cada uno, al conectarse, trae acá el test que muestra que mueve lo que
tiene que mover y nada más.

1. Filtros y red: notch, pendiente y jitter de la tasa.
2. Estímulo: duración del click y ventana (rampa) del burst.
"""

import os
import sys

import numpy as np

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from abr.ABR_generator import (MAINS_HZ, UNCONNECTED_SETTINGS,
                               _get_generator, default_settings)


def _gen():
    return _get_generator()


def _curva(technical=None, filter_high=100, intensity=80, capture='R1',
           stim='click', freq=None, pol='Alternada', caso_extra=None):
    """Una captura completa del ABR con el equipo que se pida."""
    g = _gen()
    estimulo = {'stim': stim, 'freq': freq, 'pol': pol, 'int': intensity,
                'rate': 21.1, 'filter_down': 3000,
                'filter_passhigh': filter_high, 'average': 2000,
                'current_avg': 2000, 'pathway': 'air_conduction'}
    tec = default_settings('ABR')
    tec.update(technical or {})
    caso = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
            'seed_key': 'caso-avanzados', 'capture_id': capture}
    caso.update(caso_extra or {})
    return g.generate_curve('adult_female', 'normal', estimulo, tec, caso)


SIN_TIERRA = {'electrodes': {'vertex': 'Cz', 'right': 'A2', 'left': 'A1',
                             'ground': 'No Conectado'}}


def _potencia_en(y, fs, f0, ancho=3.0):
    espectro = np.abs(np.fft.rfft(y - np.mean(y))) ** 2
    f = np.fft.rfftfreq(len(y), 1.0 / fs)
    return float(espectro[np.abs(f - f0) <= ancho].sum())


def _potencia_arriba(y, fs, f0):
    espectro = np.abs(np.fft.rfft(y)) ** 2
    f = np.fft.rfftfreq(len(y), 1.0 / fs)
    return float(espectro[f >= f0].sum())


# ------------------------------------------------------------ filtros y red

def test_the_filter_parameters_are_connected():
    for clave in ('notch_hz', 'filter_slope', 'rate_jitter_pct'):
        assert clave not in UNCONNECTED_SETTINGS, clave
        assert clave in default_settings('ABR'), clave


def test_the_notch_removes_its_own_frequency_and_nothing_else():
    """Un notch de 50 saca la fundamental de la red y deja los armónicos;
    uno de 60 con red de 50 no saca nada."""
    g = _gen()
    t = np.linspace(0, 300, 30000)          # 300 ms, como el monitor
    fs = (len(t) - 1) / (t[-1] / 1000.0)

    def red(notch):
        return g.mains_interference(t, True, 0.0,
                                    np.random.default_rng(1), notch)
    sin, con50, con60 = red(0.0), red(MAINS_HZ), red(60.0)
    assert _potencia_en(con50, fs, MAINS_HZ) < 0.01 * _potencia_en(sin, fs, MAINS_HZ)
    assert abs(_potencia_en(con50, fs, 3 * MAINS_HZ)
               - _potencia_en(sin, fs, 3 * MAINS_HZ)) < 0.05 * _potencia_en(sin, fs, 3 * MAINS_HZ)
    assert np.allclose(con60, sin)


def test_the_notch_cleans_a_badly_grounded_low_band_recording():
    """Sin tierra y con el pasa-alto bajo (la red entra entera), el notch
    limpia el trazo. Con el tubo pinzado lo que queda es ruido y red, así
    que se ve directo; uno de 60 Hz no hace nada con red de 50."""
    def trazo(notch):
        tec = dict(SIN_TIERRA, notch_hz=notch, tube_clamped=True)
        return _curva(technical=tec, filter_high=10)[1]
    sin, con50, con60 = trazo(0.0), trazo(MAINS_HZ), trazo(60.0)
    assert np.std(con50) < 0.85 * np.std(sin), (np.std(con50), np.std(sin))
    assert np.allclose(con60, sin)


def test_the_notch_only_bends_what_lives_near_the_mains():
    """El costo del notch: le come amplitud a lo que tiene energía cerca
    de la red (una respuesta de latencia media, ~40 Hz). Como es angosto,
    al complejo corto del ECochG casi no le hace nada."""
    g = _gen()
    fs = 20000.0
    t = np.arange(0, 200, 1000.0 / fs)          # ms
    media = np.sin(2 * np.pi * 45 * t / 1000) * np.exp(
        -0.5 * ((t - 60) / 25) ** 2)
    corta = -1.0 * ((t > 1.0) & (t < 4.0))
    d_media = np.max(np.abs(g.notch(media, fs, MAINS_HZ) - media))
    d_corta = np.max(np.abs(g.notch(corta, fs, MAINS_HZ) - corta))
    assert d_media > 0.05, d_media
    assert d_corta < 0.02, d_corta


def test_the_slope_sets_how_sharp_the_filter_is():
    """Pendiente fuerte: más "ringing" alrededor de una espiga. Pendiente
    suave: deja pasar más ruido de fuera de la banda."""
    g = _gen()
    fs = 41600.0
    n = 1000
    espiga = np.zeros(n)
    espiga[n // 2] = 1.0
    suave = g.apply_filters(espiga, 3000.0, 100.0, fs, slope_db=6.0)
    fuerte = g.apply_filters(espiga, 3000.0, 100.0, fs, slope_db=48.0)
    # El ringing: lóbulos negativos al lado de la espiga.
    assert fuerte.min() < suave.min()
    # Fuera de la banda: con pendiente suave pasa bastante más de lo que
    # está por encima del pasa-bajo (la curva sale "peluda").
    ruido = np.random.default_rng(3).standard_normal(n)
    pasa_suave = g.apply_filters(ruido, 3000.0, 100.0, fs, slope_db=6.0)
    pasa_fuerte = g.apply_filters(ruido, 3000.0, 100.0, fs, slope_db=48.0)
    assert (_potencia_arriba(pasa_suave, fs, 4000.0)
            > 1.8 * _potencia_arriba(pasa_fuerte, fs, 4000.0))


def test_the_slope_changes_the_recorded_trace():
    """Conectada de punta a punta: otra pendiente, otro trazo."""
    _, a, _ = _curva(technical={'filter_slope': 6.0})
    _, b, _ = _curva(technical={'filter_slope': 48.0})
    assert not np.allclose(a, b)


def test_rate_jitter_unlocks_the_mains_from_the_stimulus():
    """Con la tasa fija una parte del zumbido queda enganchada al estímulo
    y el promedio la dibuja; el jitter la reparte entre los barridos y se
    promedia como ruido."""
    g = _gen()
    assert g.jitter_coherence(0) == 1.0
    assert g.jitter_coherence(5) < 0.5
    assert g.jitter_coherence(20) < 0.05
    # Sin respuesta (tubo pinzado), lo que queda en el promedio es ruido y
    # red: con jitter queda menos zumbido dibujado.
    sin = _curva(technical=dict(SIN_TIERRA, tube_clamped=True),
                 filter_high=10)[1]
    con = _curva(technical=dict(SIN_TIERRA, tube_clamped=True,
                                rate_jitter_pct=20.0), filter_high=10)[1]
    assert np.std(con) < np.std(sin), (np.std(con), np.std(sin))



# ---------------------------------------------------------------- estímulo

def test_the_stimulus_parameters_are_connected():
    for clave in ('click_us', 'burst_window'):
        assert clave not in UNCONNECTED_SETTINGS, clave
        assert clave in default_settings('ABR'), clave


def _ondas(stim, technical):
    g = _gen()
    base = {'I': {'lat': 1.5, 'amp': 0.4, 'width': 1.0},
            'V': {'lat': 5.6, 'amp': 0.5, 'width': 1.0}}
    return g.stimulus_settings_effects(
        {w: dict(d) for w, d in base.items()}, stim, technical)


def test_a_longer_click_comes_later_wider_and_smaller():
    rutina = _ondas('click', {'click_us': 100.0})
    largo = _ondas('click', {'click_us': 500.0})
    corto = _ondas('click', {'click_us': 50.0})
    assert rutina['V']['lat'] == 5.6 and rutina['V']['width'] == 1.0
    assert largo['V']['lat'] > rutina['V']['lat'] + 0.1
    assert largo['V']['width'] > 1.1 and largo['V']['amp'] < 0.5
    # Más corto que el de rutina casi no cambia nada.
    assert abs(corto['V']['lat'] - 5.6) < 0.05
    # Y no toca el burst.
    assert _ondas('tone_burst', {'click_us': 500.0})['V']['lat'] == 5.6


def test_a_longer_click_shifts_the_recorded_wave_V():
    """De punta a punta: con el click de 500 µs la onda V del trazo llega
    más tarde que con el de 100."""
    def pico_v(click_us):
        t, y, _ = _curva(technical={'click_us': click_us})
        ventana = (t > 4.5) & (t < 7.5)
        return float(t[ventana][np.argmax(y[ventana])])
    assert pico_v(500.0) > pico_v(100.0) + 0.08


def test_the_burst_ramp_changes_synchrony_a_little():
    """Rampa lineal: más salpicadura espectral, sincroniza algo mejor."""
    blackman = _ondas('tone_burst', {'burst_window': 'blackman'})
    lineal = _ondas('tone_burst', {'burst_window': 'linear'})
    assert lineal['V']['width'] < blackman['V']['width']
    assert lineal['V']['amp'] > blackman['V']['amp']
    assert _ondas('click', {'burst_window': 'linear'})['V']['width'] == 1.0


def test_the_burst_ramp_shapes_the_ecochg_envelope():
    """En el ECochG con burst, la rampa del equipo es la del PS y la MC."""
    from abr import ecochg as E
    t = np.linspace(0, 5, 501)
    timing = (1.0, 2.0, 1.0)
    lineal = E._trapezoid(t, 0.5, timing, 'linear')
    coseno = E._trapezoid(t, 0.5, timing, 'blackman')
    cuarto = int(np.argmin(np.abs(t - 0.75)))      # un cuarto de la subida
    assert abs(lineal[cuarto] - 0.25) < 0.02
    assert coseno[cuarto] < lineal[cuarto]
    assert lineal.max() == coseno.max() == 1.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
