"""
audio_proc.py — Síntesis de audio procedimental para audiología
Autor: (tu nombre)
Licencia: MIT

Resumen
-------
Librería para generar y reproducir audio procedimental:
- Tonos puros (continuo, pulsátil, FM)
- Ruidos: blanco, rosa (1/f), speech-shaped, narrow-band noise (NBN)

Backends de salida:
- SoundDeviceBackend (PortAudio)  -> requiere 'sounddevice'
- QtAudioBackend (QAudioOutput)   -> opcional 'PySide6'

Uso rápido
----------
from audio_proc import AudioEngine, PureTone, WhiteNoise

eng = AudioEngine(sample_rate=48000, backend="sounddevice")  # o "qt" si tienes PySide6
sig = PureTone(freq=1000, level_dbfs=-10, duration=3.0, pulsatile_hz=2.5, duty_cycle=0.5)
eng.play(sig)  # bloquea hasta terminar

Notas
-----
- 'level_dbfs' controla la ganancia relativa (0 dBFS ~= pico a 1.0). Ajusta según tu cadena.
- Para mapeo a dB HL/SPL agrega tu tabla/calibración en AudioEngine.calibration_gain_db().
"""

from __future__ import annotations
import math
import time
import threading
from dataclasses import dataclass
from typing import Generator, Optional, Iterable, Literal, Callable

import numpy as np

# =========================
# Utilidades de DSP simples
# =========================

def db_to_lin(db: float) -> float:
    """Convierte dB (amplitud) a factor lineal."""
    return 10 ** (db / 20.0)

def apply_envelope(signal: np.ndarray, sr: int, attack_ms=5.0, release_ms=5.0) -> np.ndarray:
    """Aplica fade in/out para evitar clics."""
    n = signal.size
    a = int(sr * attack_ms / 1000.0)
    r = int(sr * release_ms / 1000.0)
    env = np.ones(n, dtype=np.float32)
    if a > 0:
        env[:a] = np.linspace(0.0, 1.0, a, dtype=np.float32)
    if r > 0:
        env[-r:] = np.linspace(1.0, 0.0, r, dtype=np.float32)
    return signal * env

def biquad_bandpass_coeffs(fc: float, q: float, sr: int):
    """
    Coeficientes biquad (bandpass, peak gain = Q) estilo RBJ.
    Devuelve (b0, b1, b2, a0, a1, a2). Normalizarás por a0 al usar.
    """
    w0 = 2.0 * math.pi * fc / sr
    alpha = math.sin(w0) / (2.0 * q)
    b0 = q * alpha
    b1 = 0.0
    b2 = -q * alpha
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(w0)
    a2 = 1.0 - alpha
    return b0, b1, b2, a0, a1, a2

class Biquad:
    """Filtro biquad IIR directo I (mono)."""
    def __init__(self, b0, b1, b2, a0, a1, a2):
        self.b0 = b0 / a0
        self.b1 = b1 / a0
        self.b2 = b2 / a0
        self.a1 = a1 / a0
        self.a2 = a2 / a0
        self.x1 = self.x2 = 0.0
        self.y1 = self.y2 = 0.0

    def process(self, x: np.ndarray) -> np.ndarray:
        y = np.empty_like(x, dtype=np.float32)
        x1, x2, y1, y2 = self.x1, self.x2, self.y1, self.y2
        b0, b1, b2, a1, a2 = self.b0, self.b1, self.b2, self.a1, self.a2
        for i in range(x.size):
            xi = float(x[i])
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            y[i] = yi
            x2, x1 = x1, xi
            y2, y1 = y1, yi
        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2
        return y

# =========================
# Especificación de señales
# =========================

@dataclass
class Signal:
    """Base: implementa un generador por bloques en float32 [-1, 1]."""
    duration: float                 # segundos (o None si infinito)
    level_dbfs: float = -12.0       # nivel relativo
    block_size: int = 1024

    def stream(self, sample_rate: int) -> Iterable[np.ndarray]:
        raise NotImplementedError

@dataclass
class PureTone(Signal):
    """
    Tono puro continuo, pulsátil (AM on/off) o FM.
    - freq: frecuencia base (Hz)
    - pulsatile_hz: frecuencia de modulación de pulso (on/off). Si None => continuo
    - duty_cycle: proporción encendido (0..1) cuando es pulsátil
    - fm_dev: desviación de frecuencia (Hz) para FM (vibrato); fm_rate: velocidad del vibrato
    """
    freq: float = 1000.0
    pulsatile_hz: Optional[float] = None
    duty_cycle: float = 0.5
    fm_dev: float = 0.0
    fm_rate: float = 5.0
    attack_ms: float = 5.0
    release_ms: float = 5.0

    def stream(self, sample_rate: int) -> Iterable[np.ndarray]:
        n_total = None if self.duration is None else int(self.duration * sample_rate)
        phase = 0.0
        phase_inc_base = 2.0 * math.pi * self.freq / sample_rate
        fm_phase = 0.0
        fm_inc = 2.0 * math.pi * self.fm_rate / sample_rate if self.fm_dev != 0 else 0.0
        amp = db_to_lin(self.level_dbfs)

        emitted = 0
        while n_total is None or emitted < n_total:
            n = self.block_size if n_total is None else min(self.block_size, n_total - emitted)

            # FM si corresponde
            if self.fm_dev != 0.0:
                # fase instantánea con desviación senoidal
                t = (np.arange(n, dtype=np.float32) + emitted) / sample_rate
                inst_freq = self.freq + self.fm_dev * np.sin(2*np.pi*self.fm_rate*t + fm_phase)
                phase_vec = 2*np.pi*np.cumsum(inst_freq)/sample_rate
                # re-anchorar para continuidad:
                phase0 = phase
                block = np.sin(phase0 + (phase_vec - phase_vec[0])).astype(np.float32)
                # actualizar fase aproximada
                phase = (phase + 2*np.pi*inst_freq[-1]/sample_rate) % (2*np.pi)
                fm_phase = (fm_phase + fm_inc * n) % (2*np.pi)
            else:
                # tono simple
                ph = phase + phase_inc_base * np.arange(n, dtype=np.float32)
                block = np.sin(ph).astype(np.float32)
                phase = (phase + phase_inc_base * n) % (2*np.pi)

            # Pulsátil (on/off por duty_cycle)
            if self.pulsatile_hz and self.pulsatile_hz > 0:
                t = (np.arange(n, dtype=np.float32) + emitted) / sample_rate
                pwm = ((t * self.pulsatile_hz) % 1.0) < self.duty_cycle
                block *= pwm.astype(np.float32)

            # Aplicar ganancia y suave envolvente al inicio/fin global
            block *= amp
            if emitted == 0 or (n_total is not None and emitted + n >= n_total):
                block = apply_envelope(block, sample_rate, self.attack_ms, self.release_ms)

            emitted += n
            yield block

@dataclass
class WhiteNoise(Signal):
    """Ruido blanco gaussiano."""
    def stream(self, sample_rate: int) -> Iterable[np.ndarray]:
        n_total = None if self.duration is None else int(self.duration * sample_rate)
        amp = db_to_lin(self.level_dbfs)
        emitted = 0
        while n_total is None or emitted < n_total:
            n = self.block_size if n_total is None else min(self.block_size, n_total - emitted)
            block = np.random.normal(0.0, 1.0, n).astype(np.float32)
            block *= amp
            if emitted == 0 or (n_total is not None and emitted + n >= n_total):
                block = apply_envelope(block, sample_rate)
            emitted += n
            yield block

@dataclass
class PinkNoise(Signal):
    """
    Ruido rosa (1/f) aproximado con método Voss-McCartney (suma de octavas aleatorias).
    """
    n_rows: int = 16  # más filas => espectro más estable

    def stream(self, sample_rate: int) -> Iterable[np.ndarray]:
        n_total = None if self.duration is None else int(self.duration * sample_rate)
        amp = db_to_lin(self.level_dbfs)
        rng = np.random.default_rng()
        # Estado para Voss
        rows = rng.random(self.n_rows)
        counters = np.zeros(self.n_rows, dtype=np.int64)
        emitted = 0
        while n_total is None or emitted < n_total:
            n = self.block_size if n_total is None else min(self.block_size, n_total - emitted)
            out = np.zeros(n, dtype=np.float32)
            for i in range(n):
                # actualizar una fila aleatoria en cada muestra
                k = int(rng.integers(0, self.n_rows))
                counters[k] += 1
                rows[k] = rng.random()
                out[i] = rows.sum()
            out = (out - np.mean(out)) / (np.std(out) + 1e-8)
            out *= amp
            if emitted == 0 or (n_total is not None and emitted + n >= n_total):
                out = apply_envelope(out, sample_rate)
            emitted += n
            yield out

@dataclass
class SpeechNoise(Signal):
    """
    Speech-shaped noise (aprox. LTASS): se obtiene filtrando ruido blanco con
    dos shelving y un pasa-banda suave para enfatizar 300–3000 Hz.
    Parámetros simples y eficientes (no pretende ser clavado a LTASS publicado).
    """
    def stream(self, sample_rate: int) -> Iterable[np.ndarray]:
        # Diseño aproximado: suma de 3 biquads para dar forma
        # 1) high-pass suave ~ 200 Hz (emular menos energía subgrave)
        hp = Biquad(*biquad_bandpass_coeffs(200, q=0.5, sr=sample_rate))
        # 2) band-pass ancho ~ 1000 Hz (centro de inteligibilidad)
        bp = Biquad(*biquad_bandpass_coeffs(1000, q=0.7, sr=sample_rate))
        # 3) low-pass suave ~ 6 kHz (menos energía en agudos altos)
        lp = Biquad(*biquad_bandpass_coeffs(6000, q=0.5, sr=sample_rate))

        base = WhiteNoise(duration=self.duration, level_dbfs=self.level_dbfs, block_size=self.block_size)
        emitted = 0
        n_total = None if self.duration is None else int(self.duration * sample_rate)
        for block in base.stream(sample_rate):
            # El "shape" se aproxima combinando filtros banda y realzando su suma
            y = hp.process(block) + 1.5 * bp.process(block) + 0.6 * lp.process(block)
            # normalizar bloque para no clippear tras suma
            y = y / (np.max(np.abs(y)) + 1e-8)
            if emitted == 0 or (n_total is not None and emitted + block.size >= n_total):
                y = apply_envelope(y, sample_rate)
            emitted += block.size
            yield y.astype(np.float32)

@dataclass
class NarrowBandNoise(Signal):
    """
    Narrow-Band Noise (NBN) a partir de ruido blanco filtrado con bandpass biquad.
    Parámetros:
    - center_hz: frecuencia central
    - bandwidth_hz: ancho de banda (aprox. FWHM). Q ~ center/bandwidth.
    """
    center_hz: float = 1000.0
    bandwidth_hz: float = 160.0  # p. ej., ruidos NB típicos ~ 1/3 de octava
    def stream(self, sample_rate: int) -> Iterable[np.ndarray]:
        q = max(0.1, self.center_hz / max(1.0, self.bandwidth_hz))
        b = Biquad(*biquad_bandpass_coeffs(self.center_hz, q=q, sr=sample_rate))
        base = WhiteNoise(duration=self.duration, level_dbfs=self.level_dbfs, block_size=self.block_size)
        emitted = 0
        n_total = None if self.duration is None else int(self.duration * sample_rate)
        for block in base.stream(sample_rate):
            y = b.process(block)
            # normalización ligera para estabilidad de nivel
            y = y / (np.max(np.abs(y)) + 1e-6)
            if emitted == 0 or (n_total is not None and emitted + block.size >= n_total):
                y = apply_envelope(y, sample_rate)
            emitted += block.size
            yield y.astype(np.float32)

# =========================
# Motor de audio y backends
# =========================

class PlaybackBackend:
    """Interfaz para backends de reproducción en tiempo real."""
    def play_stream(self, frames: Iterable[np.ndarray], sample_rate: int, block_size: int):
        raise NotImplementedError

class SoundDeviceBackend(PlaybackBackend):
    """Backend basado en sounddevice (PortAudio)."""
    def __init__(self):
        try:
            import sounddevice as sd  # type: ignore
        except Exception as e:
            raise RuntimeError("sounddevice no está instalado. `pip install sounddevice`") from e
        self.sd = sd

    def play_stream(self, frames: Iterable[np.ndarray], sample_rate: int, block_size: int):
        sd = self.sd
        # callback pull-model
        it = iter(frames)
        buffer = np.zeros(block_size, dtype=np.float32)

        def callback(outdata, frames, time_info, status):
            nonlocal buffer
            try:
                buffer = next(it)
            except StopIteration:
                outdata[:] = np.zeros((frames, 1), dtype=np.float32)
                raise sd.CallbackStop()
            # garantizar tamaño
            if buffer.size < frames:
                tmp = np.zeros(frames, dtype=np.float32)
                tmp[:buffer.size] = buffer
                buffer = tmp
            elif buffer.size > frames:
                buffer = buffer[:frames]
            outdata[:, 0] = buffer

        with sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32',
                             blocksize=block_size, callback=callback):
            # Esperar a terminar
            while True:
                try:
                    time.sleep(0.05)
                except KeyboardInterrupt:
                    break
                # el stream se cierra solo al agotar 'frames'

class QtAudioBackend(PlaybackBackend):
    """
    Backend basado en PySide6.QtMultimedia (QAudioOutput).
    Útil cuando quieres que el audio “salga por el sistema de Qt”.
    """
    def __init__(self):
        try:
            from PySide6.QtMultimedia import QAudioFormat, QAudioOutput
            from PySide6.QtCore import QIODevice, QByteArray, QBuffer, QCoreApplication
        except Exception as e:
            raise RuntimeError("PySide6 no está instalado. `pip install PySide6`") from e
        # guardar refs de tipos para no recrear imports
        self.QAudioFormat = QAudioFormat
        self.QAudioOutput = QAudioOutput
        self.QIODevice = QIODevice
        self.QByteArray = QByteArray
        self.QBuffer = QBuffer
        self.QCoreApplication = QCoreApplication
        self.app = None

    def play_stream(self, frames: Iterable[np.ndarray], sample_rate: int, block_size: int):
        from PySide6.QtMultimedia import QAudioFormat, QAudioOutput
        from PySide6.QtCore import QIODevice, QByteArray, QBuffer, QCoreApplication

        # Crear app si no existe (modo consola)
        if QCoreApplication.instance() is None:
            self.app = QCoreApplication([])

        # Configurar formato PCM float32 mono
        fmt = QAudioFormat()
        fmt.setSampleRate(sample_rate)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.Float)  # float32

        audio = QAudioOutput(fmt)
        audio.setBufferSize(block_size * 4)  # bytes aprox.

        # Implementar un QIODevice "pull" desde el generador
        class StreamDevice(QIODevice):
            def __init__(self, gen: Iterable[np.ndarray], parent=None):
                super().__init__(parent)
                self.it = iter(gen)
                self.buffer = np.zeros(0, dtype=np.float32)

            def readData(self, maxlen: int) -> bytes:
                # Qt pedirá bytes; convertimos floats a bytes
                needed = maxlen // 4  # float32
                out = np.empty(0, dtype=np.float32)
                while out.size < needed:
                    if self.buffer.size == 0:
                        try:
                            self.buffer = next(self.it)
                        except StopIteration:
                            break
                    take = min(needed - out.size, self.buffer.size)
                    out = np.concatenate((out, self.buffer[:take]))
                    self.buffer = self.buffer[take:]
                    if self.buffer.size == 0:
                        self.buffer = np.zeros(0, dtype=np.float32)
                return out.tobytes()

            def writeData(self, data: bytes, maxlen: int) -> int:
                return 0  # no se usa (solo salida)

            def bytesAvailable(self) -> int:
                return 1024 * 1024  # anunciar bastante disponible

        dev = StreamDevice(frames)
        dev.open(QIODevice.ReadOnly)
        audio.start(dev)

        # Ejecutar event loop hasta que el stream termine (cuando dev no entregue más datos)
        # Monitorear en un hilo: cuando se acaben los datos, detener
        def monitor():
            while audio.state() == QAudioOutput.ActiveState:
                time.sleep(0.05)
            dev.close()
            audio.stop()
            if self.app:
                self.app.quit()

        th = threading.Thread(target=monitor, daemon=True)
        th.start()

        if self.app:
            self.app.exec()

# ==============
# AudioEngine API
# ==============

class AudioEngine:
    """
    Engine de reproducción y helpers de construcción.

    Parámetros:
    - sample_rate: 44100/48000/96000 típicos
    - backend: "sounddevice" (por defecto) o "qt"
    - block_size: tamaño de bloque de stream

    Hooks:
    - calibration_gain_db: función que devuelve una ganancia adicional (dB)
      para mapear tu cadena a dB SPL/HL (por defecto 0.0 dB)
    """
    def __init__(self, sample_rate: int = 48000, backend: Literal["sounddevice", "qt"] = "sounddevice",
                 block_size: int = 1024,
                 calibration_gain_db: Optional[Callable[[float], float]] = None):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self._backend_name = backend
        self._backend = self._make_backend(backend)
        self._cal_hook = calibration_gain_db or (lambda lvl_dbfs: 0.0)

    def _make_backend(self, name: str) -> PlaybackBackend:
        if name == "sounddevice":
            return SoundDeviceBackend()
        elif name == "qt":
            return QtAudioBackend()
        else:
            raise ValueError("Backend desconocido. Usa 'sounddevice' o 'qt'.")

    # ---------- Factories de señales ----------
    def pure_tone(self, freq: float, duration: float, level_dbfs: float = -12.0,
                  pulsatile_hz: Optional[float] = None, duty_cycle: float = 0.5,
                  fm_dev: float = 0.0, fm_rate: float = 5.0) -> PureTone:
        return PureTone(freq=freq, duration=duration, level_dbfs=level_dbfs, block_size=self.block_size,
                        pulsatile_hz=pulsatile_hz, duty_cycle=duty_cycle,
                        fm_dev=fm_dev, fm_rate=fm_rate)

    def white_noise(self, duration: float, level_dbfs: float = -12.0) -> WhiteNoise:
        return WhiteNoise(duration=duration, level_dbfs=level_dbfs, block_size=self.block_size)

    def pink_noise(self, duration: float, level_dbfs: float = -12.0) -> PinkNoise:
        return PinkNoise(duration=duration, level_dbfs=level_dbfs, block_size=self.block_size)

    def speech_noise(self, duration: float, level_dbfs: float = -12.0) -> SpeechNoise:
        return SpeechNoise(duration=duration, level_dbfs=level_dbfs, block_size=self.block_size)

    def nbn(self, center_hz: float, bandwidth_hz: float, duration: float, level_dbfs: float = -12.0) -> NarrowBandNoise:
        return NarrowBandNoise(center_hz=center_hz, bandwidth_hz=bandwidth_hz,
                               duration=duration, level_dbfs=level_dbfs, block_size=self.block_size)

    # ---------- Reproducción ----------
    def play(self, signal: Signal):
        """
        Reproduce una señal (mono) bloqueando hasta terminar.
        Aplica ganancia de calibración si está definida.
        """
        # Envolver stream para añadir calibración en dB (si la usas)
        cal_db = self._cal_hook(signal.level_dbfs)
        g = db_to_lin(cal_db)

        def frames():
            for blk in signal.stream(self.sample_rate):
                y = np.clip(blk * g, -0.9999, 0.9999).astype(np.float32)
                yield y

        self._backend.play_stream(frames(), self.sample_rate, signal.block_size)

# =========================
# Helpers de frecuencias ISO
# =========================

# Frecuencias audiométricas típicas (puedes extender)
AUDIO_FREQS = [125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000]

# =========================
# Ejemplo de uso (opcional)
# =========================

if __name__ == "__main__":
    """
    Ejemplos de ejecución directa.
    NOTA: para usar el backend Qt, ejecuta con backend="qt" y tener PySide6 instalado.
    """
    # 1) Tono 1 kHz pulsátil (2.5 Hz, duty 50%) por 3 s utilizando sounddevice
    eng = AudioEngine(sample_rate=48000, backend="sounddevice", block_size=1024)

    print("Tono 1 kHz pulsátil 3 s...")
    tone_pulse = eng.pure_tone(freq=1000, duration=3.0, level_dbfs=-10,
                               pulsatile_hz=2.5, duty_cycle=0.5)
    eng.play(tone_pulse)

    # 2) Tono 2 kHz con FM (vibrato 5 Hz, ±10 Hz) por 3 s
    print("Tono 2 kHz con FM (±10 Hz @ 5 Hz) 3 s...")
    tone_fm = eng.pure_tone(freq=2000, duration=3.0, level_dbfs=-12,
                            fm_dev=10.0, fm_rate=5.0)
    eng.play(tone_fm)

    # 3) NBN centrado en 1 kHz con BW=1/3 octava (~ 231 Hz a 1 kHz)
    print("NBN 1 kHz, BW≈1/3 octava, 3 s...")
    bw = 1000 * (2 ** (1/6) - 2 ** (-1/6))  # ancho aprox 1/3 oct
    nbn = eng.nbn(center_hz=1000, bandwidth_hz=bw, duration=3.0, level_dbfs=-12)
    eng.play(nbn)

    # 4) Speech-shaped noise 3 s
    print("Speech-shaped noise 3 s...")
    sp = eng.speech_noise(duration=3.0, level_dbfs=-12)
    eng.play(sp)

    # 5) Ruido rosa 3 s
    print("Ruido rosa 3 s...")
    pn = eng.pink_noise(duration=3.0, level_dbfs=-12)
    eng.play(pn)

    print("Fin de ejemplos.")
