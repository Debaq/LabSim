"""Tests de core/dsp.py: los filtros que reemplazan a scipy.

1. Butterworth de fase cero: en el corte deja pasar la mitad (-3 dB de ida
   y -3 dB de vuelta), el pasa-bajo conserva la continua y el pasa-alto la
   mata.
2. Cortes chicos (pasa-alto de 3 Hz a 41.6 kHz): no explota ni da NaN.
3. Señal más corta que el relleno: ValueError, como scipy (VEMP lo ataja).
4. filtfilt sobre un eje es lo mismo que fila por fila.
5. Gaussiano: conserva una constante y el área.
6. Con scipy instalado se compara contra scipy.signal.sosfiltfilt,
   scipy.ndimage.gaussian_filter1d y scipy.stats.ncf; sin scipy se salta
   (la app ya no lo necesita).
"""

import os
import sys

import numpy as np

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core import dsp  # noqa: E402

try:
    import scipy.signal as sp_signal
    from scipy.ndimage import gaussian_filter1d as sp_gauss
    from scipy.stats import ncf as sp_ncf
except ImportError:
    sp_signal = None


def _amplitud_en(filt, wn, largo=4000):
    """Amplitud de salida de un seno de frecuencia normalizada wn, al medio."""
    n = np.arange(largo)
    y = dsp.filtfilt(filt, np.sin(np.pi * wn * n))
    medio = y[largo // 4: 3 * largo // 4]
    return np.sqrt(2.0 * np.mean(medio ** 2))


def test_en_el_corte_pasa_la_mitad():
    for orden in (2, 4, 5, 6):
        for tipo in ('low', 'high'):
            amp = _amplitud_en(dsp.butter(orden, 0.1, tipo), 0.1)
            assert abs(amp - 0.5) < 0.01, (orden, tipo, amp)


def test_pasa_bajo_conserva_la_continua_y_pasa_alto_la_mata():
    x = np.full(300, 3.0)
    assert np.allclose(dsp.filtfilt(dsp.butter(4, 0.2, 'low'), x), 3.0)
    assert np.allclose(dsp.filtfilt(dsp.butter(4, 0.2, 'high'), x), 0.0)


def test_corte_chico_no_explota():
    rng = np.random.default_rng(3)
    x = rng.standard_normal(5500).cumsum()
    y = dsp.filtfilt(dsp.butter(6, 3.0 / 20800, 'high'), x)
    assert np.all(np.isfinite(y))
    assert np.abs(y).max() < 2 * np.abs(x).max()


def test_senal_corta_levanta_valueerror():
    try:
        dsp.filtfilt(dsp.butter(4, 0.1), np.zeros(15))
    except ValueError:
        return
    raise AssertionError('tenía que levantar ValueError')


def test_eje_igual_que_fila_por_fila():
    rng = np.random.default_rng(4)
    x = rng.standard_normal((5, 200))
    filt = dsp.butter(4, 0.4, 'high')
    juntos = dsp.filtfilt(filt, x, axis=1)
    for i in range(5):
        assert np.allclose(juntos[i], dsp.filtfilt(filt, x[i]))
    assert np.allclose(dsp.filtfilt(filt, x.T, axis=0), juntos.T)


def test_gaussiano_conserva_constante_y_area():
    assert np.allclose(dsp.gaussian_filter1d(np.full(50, 2.0), 3), 2.0)
    x = np.zeros(101)
    x[50] = 1.0
    assert abs(dsp.gaussian_filter1d(x, 4).sum() - 1.0) < 1e-12


def test_igual_que_scipy():
    if sp_signal is None:
        print('  (salteado: sin scipy)')
        return
    rng = np.random.default_rng(1)
    for orden in range(1, 8):
        for wn in (1.6e-4, 5e-4, 3e-3, 0.07, 0.4, 0.5, 0.99):
            for tipo in ('low', 'high'):
                x = rng.standard_normal(3000).cumsum() * 0.1 + 3
                ref = sp_signal.sosfiltfilt(
                    sp_signal.butter(orden, wn, tipo, output='sos'), x)
                y = dsp.filtfilt(dsp.butter(orden, wn, tipo), x)
                err = np.abs(ref - y).max() / np.abs(ref).max()
                assert err < 1e-8, (orden, wn, tipo, err)
    for sigma in (0.3, 1, 2.5, 40):
        x = rng.standard_normal(60)
        assert np.allclose(sp_gauss(x, sigma), dsp.gaussian_filter1d(x, sigma),
                           atol=1e-13)
    # el FSP sortea con noncentral_f: es lo que llama ncf.rvs por dentro
    ref = sp_ncf.rvs(4, 300, 7.5, random_state=np.random.default_rng(9))
    assert ref == np.random.default_rng(9).noncentral_f(4, 300, 7.5)


if __name__ == '__main__':
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            try:
                fn()
                print(f'  {nombre} OK')
            except AssertionError as exc:
                fallos += 1
                print(f'  {nombre} FALLÓ: {exc}')
    print('TODOS LOS TESTS PASARON' if not fallos else f'{fallos} FALLARON')
