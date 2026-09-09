"""Sintesis DSP de los estimulos de tono y ruido del audiometro.

Reemplaza los mp3 estaticos de TONO / FM / NBN / WN / SN / PN por audio
generado en runtime con numpy y cacheado en disco como WAV. Los audios de
HABLA (palabras, logoaudiometria) NO pasan por aca: siguen usando los mp3.

Motivacion: los mp3 de tono y ruido pesaban ~360 MB en el arbol de trabajo
(120 s cada uno, 3 canales x 15 frecuencias x 6 estimulos). Como el player
reproduce en bucle (ver lib/audio_player.Player.check_end_of_media), alcanza
con generar unos pocos segundos y dejar que el loop lo repita.

Continuidad del bucle
---------------------
Todas las formas de onda se construyen para ser exactamente periodicas en la
duracion del archivo, asi el salto del final al inicio no produce click:

* Tono: se ajusta la frecuencia al numero entero de ciclos mas cercano, de
  modo que el archivo empieza y termina en el mismo cruce por cero.
* FM (warble): se sintetiza como modulacion de fase, beta*sin(2*pi*fm*t). Con
  un numero entero de ciclos de modulacion la fase vuelve a cero al final.
* Ruidos: se construyen en el dominio de la frecuencia (magnitud segun la
  forma espectral, fase aleatoria) y se pasan a tiempo con irfft. El
  resultado es periodico por definicion, y el filtrado circular no deja
  discontinuidad en el empalme.

Nivel de referencia
-------------------
La calibracion en dB de la aplicacion es independiente del archivo: se aplica
como ganancia con QAudioOutput.setVolume() (ver Audiometer.calibrate/volume).
Para no alterarla, todos los estimulos generados comparten el mismo pico de
referencia PEAK_REF, medido sobre los mp3 originales de tono (RMS 0.541, es
decir un seno de amplitud 0.765). El tono y el FM sintetizados quedan asi al
mismo nivel exacto que los archivos que reemplazan.

Los ruidos no pueden compartir el RMS del tono sin recortar: un seno tiene
factor de cresta 1.41 y el ruido gaussiano ronda 4. Se igualan entonces por
PICO (no por RMS), fijando el RMS del ruido en PEAK_REF/4 para que los picos
estadisticos caigan dentro del mismo techo sin clipping.
"""

import os
import tempfile
import wave
import zlib
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100
DURATION = 3.0  # segundos por archivo; el player lo repite en bucle

# Amplitud pico de referencia, comun a todos los estimulos generados.
# 0.765 reproduce el RMS 0.541 medido en los mp3 de tono originales.
PEAK_REF = 0.765

# RMS de los ruidos: con picos gaussianos de ~4 sigma queda bajo PEAK_REF.
NOISE_RMS = PEAK_REF / 4.0

# Warble: desviacion de +-5% de la portadora a 5 Hz (uso audiometrico habitual).
FM_RATE = 5.0
FM_DEPTH = 0.05

# Limites de la banda audible util para dar forma al ruido.
NOISE_LO = 20.0
NOISE_HI = 20000.0

# Ancho de la transicion de las faldas del ruido de banda angosta, en octavas.
# Con faldas de ley de potencia (-12 o -48 dB/oct) la energia acumulada sobre
# las muchas octavas de fuera de banda supera a la de la banda; una transicion
# corta y suave confina la energia y evita el ringing de un corte abrupto.
NBN_EDGE_OCTAVES = 1.0 / 24.0

# Estimulos que este modulo sabe sintetizar. El resto (habla) sigue con mp3.
SYNTH_STIMULI = ("Tono", "FM", "NBN", "WN", "SN", "PN")

# Estimulos de banda ancha: no llevan frecuencia central.
BROADBAND_STIMULI = ("WN", "SN", "PN")

_CACHE_DIRNAME = "_generated"
_fallback_dir = None
_resolved_cache_dirs: dict[str, Path] = {}


# ---------------------------------------------------------------- utilidades

def _seed_for(stim, freq):
    """Semilla estable por (estimulo, frecuencia).

    No depende del canal para que OD / OI / sim compartan exactamente la misma
    forma de onda, igual que los mp3 originales (los estereo derivaban del mono).
    """
    key = f"{stim}_{freq}".encode("utf-8")
    return zlib.crc32(key)


def _num_samples():
    return int(round(SAMPLE_RATE * DURATION))


# ------------------------------------------------------------ formas de onda

def _tone(freq, n):
    """Seno puro, ajustado a un numero entero de ciclos para que cierre el bucle."""
    cycles = max(1, int(round(freq * DURATION)))
    freq_eff = cycles / DURATION  # desviacion inaudible respecto de freq
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    return np.sin(2.0 * np.pi * freq_eff * t)


def _warble(freq, n):
    """Tono warble: portadora modulada en frecuencia +-FM_DEPTH a FM_RATE Hz.

    Se implementa como modulacion de fase equivalente, sin(wc*t + beta*sin(wm*t)),
    con beta = desviacion / tasa. Al haber un numero entero de ciclos tanto de
    portadora como de modulante, la fase vuelve a cero al final del archivo.
    """
    cycles = max(1, int(round(freq * DURATION)))
    freq_eff = cycles / DURATION
    mod_cycles = max(1, int(round(FM_RATE * DURATION)))
    rate_eff = mod_cycles / DURATION

    beta = (FM_DEPTH * freq_eff) / rate_eff
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    phase = 2.0 * np.pi * freq_eff * t + beta * np.sin(2.0 * np.pi * rate_eff * t)
    return np.sin(phase)


def _shaped_noise(n, magnitude, seed):
    """Ruido con la forma espectral dada, periodico en n muestras.

    magnitude(freqs) devuelve la magnitud deseada por bin. Se le asigna fase
    aleatoria y se vuelve al dominio del tiempo; el resultado es exactamente
    periodico, por lo que el bucle no produce discontinuidad.
    """
    rng = np.random.default_rng(seed)
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)

    mag = magnitude(freqs)
    mag[0] = 0.0  # sin componente continua

    phase = rng.uniform(0.0, 2.0 * np.pi, size=freqs.shape)
    spectrum = mag * np.exp(1j * phase)
    if n % 2 == 0:
        spectrum[-1] = np.abs(spectrum[-1])  # Nyquist debe ser real

    return np.fft.irfft(spectrum, n=n)


def _band_mask(freqs, lo, hi, edge=NBN_EDGE_OCTAVES):
    """1 dentro de [lo, hi], 0 fuera, con transicion coseno de `edge` octavas.

    La transicion se define en escala logaritmica (octavas), que es la escala
    natural en audiometria, y se aplica a la magnitud con forma de coseno
    elevado para no introducir ringing en el dominio del tiempo.
    """
    mag = np.zeros_like(freqs)
    safe = np.maximum(freqs, 1e-9)
    octaves = np.log2(safe)
    lo_oct, hi_oct = np.log2(lo), np.log2(hi)

    inside = (octaves >= lo_oct) & (octaves <= hi_oct)
    mag[inside] = 1.0

    lower = (octaves >= lo_oct - edge) & (octaves < lo_oct)
    x = (octaves[lower] - (lo_oct - edge)) / edge
    mag[lower] = 0.5 * (1.0 - np.cos(np.pi * x))

    upper = (octaves > hi_oct) & (octaves <= hi_oct + edge)
    x = (octaves[upper] - hi_oct) / edge
    mag[upper] = 0.5 * (1.0 + np.cos(np.pi * x))

    mag[freqs <= 0.0] = 0.0
    return mag


def _white_shape(freqs):
    """Ruido blanco: densidad plana en la banda audible."""
    mag = np.ones_like(freqs)
    mag[(freqs < NOISE_LO) | (freqs > NOISE_HI)] = 0.0
    return mag


def _pink_shape(freqs):
    """Ruido rosa: potencia 1/f, es decir magnitud 1/sqrt(f)."""
    mag = np.zeros_like(freqs)
    band = (freqs >= NOISE_LO) & (freqs <= NOISE_HI)
    mag[band] = 1.0 / np.sqrt(freqs[band])
    return mag


def _speech_shape(freqs):
    """Ruido de habla: plano hasta 1 kHz y -12 dB/octava por encima.

    Aproxima el espectro promedio de la voz (energia concentrada bajo 1 kHz)
    con la pendiente del speech noise de IEC 60645. No busca precision clinica.
    """
    mag = np.zeros_like(freqs)
    safe = np.maximum(freqs, 1e-9)

    low_knee, high_knee = 100.0, 1000.0

    flat = (freqs >= low_knee) & (freqs <= high_knee)
    mag[flat] = 1.0

    rise = (freqs >= NOISE_LO) & (freqs < low_knee)
    mag[rise] = safe[rise] / low_knee  # -6 dB/oct hacia los graves

    fall = (freqs > high_knee) & (freqs <= NOISE_HI)
    mag[fall] = (high_knee / safe[fall]) ** 2  # -12 dB/oct hacia los agudos

    return mag


def _narrow_band_shape(center):
    """Ruido de banda angosta: un tercio de octava alrededor de la frecuencia."""
    half = 2.0 ** (1.0 / 6.0)  # medio ancho de 1/3 de octava
    lo = center / half
    hi = min(center * half, SAMPLE_RATE / 2.0)

    def shape(freqs):
        return _band_mask(freqs, lo, hi)

    return shape


# ------------------------------------------------------------- normalizacion

def _normalize_tonal(signal):
    """Lleva la señal tonal al pico de referencia."""
    peak = float(np.max(np.abs(signal)))
    if peak <= 0.0:
        return signal
    return signal * (PEAK_REF / peak)


def _normalize_noise(signal):
    """Fija el RMS del ruido y recorta por seguridad al pico de referencia.

    Se normaliza por RMS (no por pico) para que el nivel no dependa del pico
    aleatorio de una realizacion concreta. El recorte defensivo afecta a una
    fraccion despreciable de muestras y garantiza que no haya clipping.
    """
    rms = float(np.sqrt(np.mean(np.square(signal))))
    if rms <= 0.0:
        return signal
    return np.clip(signal * (NOISE_RMS / rms), -PEAK_REF, PEAK_REF)


def _to_stereo(mono, ch):
    """Coloca la señal en el canal correspondiente.

    OD -> solo canal derecho, OI -> solo canal izquierdo, cualquier otro
    valor (sim) -> ambos. Coincide con _PAN_FILTERS de lib/h_audio.py.
    """
    stereo = np.zeros((mono.size, 2), dtype=np.float64)
    if ch == "OD":
        stereo[:, 1] = mono
    elif ch == "OI":
        stereo[:, 0] = mono
    else:
        stereo[:, 0] = mono
        stereo[:, 1] = mono
    return stereo


def _write_wav(path, stereo):
    """Escribe WAV PCM 16 bit estereo de forma atomica."""
    samples = np.clip(stereo, -1.0, 1.0)
    pcm = np.round(samples * 32767.0).astype("<i2")

    tmp_path = f"{path}.{os.getpid()}.tmp"
    with wave.open(tmp_path, "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())
    os.replace(tmp_path, path)


# --------------------------------------------------------------- generacion

def render(stim, freq, ch):
    """Devuelve el estimulo pedido como array estereo float en [-1, 1].

    stim: uno de SYNTH_STIMULI. freq: frecuencia en Hz (ignorada en los
    ruidos de banda ancha). ch: "OD", "OI" o "sim".
    """
    if stim not in SYNTH_STIMULI:
        raise ValueError(f"estimulo no sintetizable: {stim}")

    n = _num_samples()
    seed = _seed_for(stim, freq)

    if stim == "Tono":
        mono = _normalize_tonal(_tone(freq, n))
    elif stim == "FM":
        mono = _normalize_tonal(_warble(freq, n))
    elif stim == "NBN":
        mono = _normalize_noise(_shaped_noise(n, _narrow_band_shape(freq), seed))
    elif stim == "WN":
        mono = _normalize_noise(_shaped_noise(n, _white_shape, seed))
    elif stim == "SN":
        mono = _normalize_noise(_shaped_noise(n, _speech_shape, seed))
    else:  # PN
        mono = _normalize_noise(_shaped_noise(n, _pink_shape, seed))

    return _to_stereo(mono, ch)


def _cache_dir(audio_dir):
    """Directorio de cache, con reserva en /tmp si resources no es escribible.

    En una app freezeada el arbol de recursos puede ser de solo lectura, asi
    que se cae a un directorio temporal en vez de fallar al generar.
    """
    global _fallback_dir

    # Cacheado por audio_dir: sin esto, cada estimulo reproducido en un examen
    # (docenas por sesion) pagaba un mkdir()+access() de mas solo para
    # confirmar un directorio que ya existia desde la primera vez.
    cached = _resolved_cache_dirs.get(audio_dir)
    if cached is not None:
        return cached

    target = Path(audio_dir) / _CACHE_DIRNAME
    try:
        target.mkdir(parents=True, exist_ok=True)
        if os.access(target, os.W_OK):
            _resolved_cache_dirs[audio_dir] = target
            return target
    except OSError:
        pass

    if _fallback_dir is None:
        _fallback_dir = Path(tempfile.mkdtemp(prefix="labsim_audio_"))
    _resolved_cache_dirs[audio_dir] = _fallback_dir
    return _fallback_dir


def stimulus_file(stim, freq, ch, audio_dir):
    """Ruta al WAV del estimulo, generandolo y cacheandolo si no existe.

    Devuelve None si el estimulo no es sintetizable o la frecuencia no es
    valida, para que quien llame pueda recurrir al archivo estatico.
    """
    if stim not in SYNTH_STIMULI:
        return None

    if stim in BROADBAND_STIMULI:
        freq_value = 0.0
        freq_tag = ""
    else:
        try:
            freq_value = float(freq)
        except (TypeError, ValueError):
            return None
        if not (0.0 < freq_value < SAMPLE_RATE / 2.0):
            return None
        freq_tag = f"{freq}"

    destination = _cache_dir(audio_dir) / f"{stim}_{freq_tag}_{ch}.wav"
    if not destination.exists():
        _write_wav(str(destination), render(stim, freq_value, ch))
    return str(destination)
