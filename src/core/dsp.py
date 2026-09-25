"""Filtros de señal en numpy puro: Butterworth de fase cero y gaussiano.

Reemplazan a scipy.signal (butter + filtfilt/sosfiltfilt) y a
scipy.ndimage.gaussian_filter1d, que eran lo único que la app usaba de
scipy: el paquete sumaba ~70 MB al build para cuatro funciones. Ver
docs/decisiones.md, "Build más liviano".

Dan lo mismo que scipy (hasta el redondeo, tests/test_dsp.py lo compara):
- butter(): mismo diseño (prototipo analógico + transformada bilineal con
  prewarp), en secciones de primer y segundo orden como output='sos'.
- filtfilt(): mismo relleno impar de 3*(orden+1) muestras y mismas
  condiciones iniciales de régimen (sosfilt_zi): filtrar arrancando del
  estado estacionario es lo mismo que filtrar la señal prolongada hacia
  atrás con su primera muestra, y eso tiene forma cerrada.

Cada sección no se recorre muestra a muestra (en Python serían decenas de
ms por curva): su respuesta al impulso sale cerrada de los polos y se
convoluciona por FFT. Para las primeras L salidas alcanza con los primeros
L términos de la respuesta, así que el recorte no aproxima nada. La cola
(lo que aporta la historia constante antes de la muestra 0) también es
cerrada: sum_{k>n} h[k].

Todo se escribe en factores (p - c), (1 - p) calculados sin restar números
parecidos: con cortes chicos (pasa-alto de 3 Hz a 41.6 kHz) los polos
quedan a 1e-4 de z=1 y la forma polinómica perdería la mitad de los dígitos
(es la misma razón por la que el generador ABR ya usaba SOS y no (b, a)).
"""
import functools

import numpy as np


class Butter:
    """Butterworth digital pasa-bajo o pasa-alto, listo para filtfilt()."""

    def __init__(self, order, wn, btype='low'):
        order = int(order)
        wn = float(wn)
        if order < 1:
            raise ValueError('orden del filtro < 1')
        if not 0.0 < wn < 1.0:
            raise ValueError('frecuencia de corte normalizada fuera de (0, 1)')
        if btype not in ('low', 'high'):
            raise ValueError(f'btype desconocido: {btype!r}')
        self.order = order
        self.low = btype == 'low'
        # c: los ceros del filtro digital, todos en z=-1 (bajo) o z=+1 (alto)
        self._c = -1.0 if self.low else 1.0
        # prewarp con fs=2 y bilineal con 2*fs=4, como scipy.signal.iirfilter
        wo = 4.0 * np.tan(np.pi * wn / 2.0)
        k = np.arange(-order + 1, order, 2)
        proto = -np.exp(1j * np.pi * k / (2 * order))
        self._sections = []
        for pa in proto:
            if pa.imag < -1e-12:            # el conjugado ya entra con su par
                continue
            s = wo * pa if self.low else wo / pa
            self._sections.append(self._section(s, abs(pa.imag) <= 1e-12))
        self._cache = {}

    def _section(self, s, real):
        """Polo digital de una sección y su ganancia, sin cancelaciones.

        p = (4 + s)/(4 - s); de ahí 1 - p = -2s/(4 - s) y 1 + p = 8/(4 - s).
        La ganancia se normaliza a 1 en la banda de paso de cada sección
        (DC en el bajo, Nyquist en el alto): igual que el Butterworth
        entero, que tiene ganancia 1 ahí.
        """
        den = 4.0 - s
        one_minus_p = -2.0 * s / den
        one_plus_p = 8.0 / den
        p_minus_c = one_plus_p if self.low else -one_minus_p
        gain_ref = one_minus_p if self.low else one_plus_p
        if real:
            p = ((4.0 + s) / den).real
            g = gain_ref.real / 2.0
            return (1, p, g, p_minus_c.real, one_minus_p.real, 0.0)
        p = (4.0 + s) / den
        g = abs(gain_ref) ** 2 / 4.0
        p_minus_conj = 2j * (8.0 * s.imag / abs(den) ** 2)
        return (2, p, g, p_minus_c, one_minus_p, p_minus_conj)

    def _responses(self, length):
        """(h, cola, ganancia DC) de cada sección para señales de ese largo."""
        n = np.arange(length)
        out = []
        for kind, p, g, p_minus_c, one_minus_p, p_minus_conj in self._sections:
            h = np.empty(length)
            h[0] = g
            if kind == 1:
                amp = g * p_minus_c
                pw = np.power(p, n)
                h[1:] = amp * pw[:-1]
                tail = amp * pw / one_minus_p
            else:
                amp = g * p_minus_c ** 2 / p_minus_conj
                pw = np.power(p, n)
                h[1:] = 2.0 * (amp * pw[:-1]).real
                tail = 2.0 * (amp * pw / one_minus_p).real
            out.append((h, tail, 1.0 if self.low else 0.0))
        return out

    def _cascade(self, x, x0, nfft):
        """Pasa x por las secciones, una tras otra, con historia constante x0."""
        length = x.shape[-1]
        for h, tail, dc in self._responses(length):
            spec = np.fft.rfft(x, nfft) * np.fft.rfft(h, nfft)
            x = np.fft.irfft(spec, nfft)[..., :length] + x0 * tail
            x0 = x0 * dc
        return x

    def _kernel(self, length):
        """Espectro de la respuesta al impulso de la cascada y su cola.

        Se arman una vez por largo de señal (pasando un impulso y un cero
        con historia 1 por las secciones) y después cada pasada es una
        sola convolución, no una por sección."""
        cached = self._cache.get(length)
        if cached is None:
            nfft = 1 << (2 * length - 1).bit_length()
            impulse = np.zeros(length)
            impulse[0] = 1.0
            h = self._cascade(impulse, 0.0, nfft)
            tail = self._cascade(np.zeros(length), 1.0, nfft)
            cached = (nfft, np.fft.rfft(h, nfft), tail)
            if len(self._cache) >= 8:
                self._cache.clear()
            self._cache[length] = cached
        return cached

    def _forward(self, x):
        """Filtrado causal desde el régimen de la primera muestra."""
        length = x.shape[-1]
        nfft, spec, tail = self._kernel(length)
        y = np.fft.irfft(np.fft.rfft(x, nfft) * spec, nfft)[..., :length]
        return y + x[..., :1] * tail


@functools.lru_cache(maxsize=32)
def butter(order, wn, btype='low'):
    """Como scipy.signal.butter(order, wn, btype) con wn normalizada a Nyquist.

    Cacheado: los mismos filtros se piden en cada curva y el diseño guarda
    los núcleos ya armados."""
    return Butter(order, wn, btype)


def filtfilt(filt, x, axis=-1):
    """Filtrado de fase cero, como scipy.signal.sosfiltfilt/filtfilt.

    Relleno impar de 3*(orden+1) muestras en cada punta; con una señal más
    corta que eso levanta ValueError, igual que scipy.
    """
    x = np.moveaxis(np.asarray(x, dtype=float), axis, -1)
    padlen = 3 * (filt.order + 1)
    if x.shape[-1] <= padlen:
        raise ValueError(f'la señal debe ser más larga que padlen={padlen}')
    left = 2.0 * x[..., :1] - x[..., padlen:0:-1]
    right = 2.0 * x[..., -1:] - x[..., -2:-padlen - 2:-1]
    ext = np.concatenate([left, x, right], axis=-1)
    y = filt._forward(ext)
    y = filt._forward(y[..., ::-1])[..., ::-1]
    return np.moveaxis(y[..., padlen:-padlen], -1, axis)


def gaussian_filter1d(x, sigma, truncate=4.0):
    """Como scipy.ndimage.gaussian_filter1d (modo 'reflect'), en 1D."""
    x = np.asarray(x, dtype=float)
    radius = int(truncate * float(sigma) + 0.5)
    if radius <= 0:
        return x.copy()
    k = np.arange(-radius, radius + 1)
    weights = np.exp(-0.5 * k * k / float(sigma) ** 2)
    weights /= weights.sum()
    # 'reflect' de scipy repite el borde (d c b a | a b c d): es 'symmetric'
    padded = np.pad(x, radius, mode='symmetric')
    return np.convolve(padded, weights, mode='valid')
