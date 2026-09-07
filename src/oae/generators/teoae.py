"""Generador sintético TEOAE (Transient Evoked Otoacoustic Emissions).

Click Hann 80µs @ sample_rate → respuesta sintética = suma de sinusoides
decaídas por banda (1-4 kHz default), amplitud según expected_response_db.
Promediado de N sweeps con ruido decreciente ~1/sqrt(N). Devuelve waveform
+ spectrum + SNR por banda + decisión pass/refer por criterio clínico
(default: 6 dB SNR por banda, ≥3 bandas pasan).
"""
import numpy as np
from oae.generators.base import OaeGeneratorBase, oae_attenuation_db


class TeoaeGenerator(OaeGeneratorBase):
    """Síntesis TEOAE. Sin QTimer aquí: cada llamada a generate() es síncrona,
    el caller (panel) decide cuándo disparar y cuándo actualizar el plot."""

    def __init__(self, seed: int | None = None):
        super().__init__("teoae", seed)
        self._rng = np.random.default_rng(self._seed)

    def _seed_from_params(self, ear: str = "OD", level_db: float | None = None,
                          n_sweeps: int | None = None) -> int:
        base = abs(hash(("teoae", ear, level_db or 0, n_sweeps or 0))) % (2**32)
        return int(base)

    def click_stimulus(self, level_db_spl: float, duration_us: float = 80.0) -> np.ndarray:
        """Click Hann-windowed, pico escalado a dB SPL (referencia 1 Pa ≈ 94 dB SPL).

        Devuelve array de longitud ~80µs @ 44.1kHz. La escala absoluta no es
        físicamente rigurosa: solo da una onda visible en el plot del estímulo
        que crece con el nivel seleccionado.
        """
        n = max(1, int(round(duration_us * 1e-6 * self.SAMPLE_RATE)))
        window = np.hanning(n)
        # Pico del click en Pascales relativo. 94 dB SPL = 1 Pa → factor 10**((L-94)/20).
        peak_pa = 10 ** ((level_db_spl - 94) / 20)
        # Frecuencia central ~1 kHz para que tenga un solo ciclo visible
        t = np.arange(n) / self.SAMPLE_RATE
        click = peak_pa * np.sin(2 * np.pi * 1000 * t) * window
        return click

    def generate(self, level_db: float, n_sweeps: int, ear: str = "OD",
                 case: dict | None = None) -> dict:
        """Genera una 'medición' TEOAE completa.

        Returns dict con keys: time_ms, waveform, spectrum, freqs,
        snr_per_band, pass_per_band, overall_pass, wave_a, wave_b (split
        buffer A/B para cálculo de reproducibilidad).
        """
        # Re-seedear para que la misma (level, ear, n_sweeps) → misma curva
        # entre sweeps del UI (consistente visualmente), pero distinta entre
        # oídos y entre niveles.
        self._rng = np.random.default_rng(self._seed_from_params(ear, level_db, n_sweeps))

        fs = self.SAMPLE_RATE
        win_ms = self.normative["window_ms"]
        decay_ms = self.normative["decay_ms"]
        n_samples = int(round(win_ms * 1e-3 * fs))
        t = np.arange(n_samples) / fs

        # Envolvente exponencial ~8ms decay (típico TEOAE)
        decay = np.exp(-t / (decay_ms * 1e-3))

        # Componente limpio: suma de sinusoides por banda, amplitud por
        # expected_response_db del normativo.
        expected = self.normative["expected_response_db"]
        atten = oae_attenuation_db(case)
        clean = np.zeros_like(t)
        for band_hz in self.normative["bands_hz"]:
            amp_db = expected.get(str(band_hz), 5) - atten
            # Normalizar a pascales aprox (1 Pa = 94 dB SPL, factor 10**((L-94)/20))
            amp_pa = 10 ** ((amp_db - 94) / 20)
            clean += amp_pa * np.sin(2 * np.pi * band_hz * t) * decay

        # Ruido promediado: N realizaciones → ruido ~1/sqrt(N)
        noise_std = 10 ** ((self.normative["noise_floor_db_spl"] - 94) / 20)
        noise_per_sweep = self._rng.normal(0, noise_std, size=(n_sweeps, n_samples))
        waveform = clean + noise_per_sweep.mean(axis=0)

        # Checkpoints de promedio acumulado: en un equipo real el trazo se
        # ve construyendo/estabilizando a medida que se acumulan barridos
        # (el ruido va bajando ~1/sqrt(n)), no aparece de golpe. El caller
        # anima pasando por estos snapshots antes de mostrar el resultado
        # final (que es exactamente el último checkpoint).
        n_checkpoints = int(np.clip(n_sweeps, 4, 24))
        checkpoint_ns = np.unique(
            np.linspace(1, n_sweeps, n_checkpoints).astype(int)
        )
        checkpoint_ns[-1] = n_sweeps
        cum_noise_mean = np.cumsum(noise_per_sweep, axis=0) / np.arange(1, n_sweeps + 1)[:, None]
        sweep_checkpoints = [
            {"n_sweeps": int(k), "waveform": clean + cum_noise_mean[k - 1]}
            for k in checkpoint_ns
        ]

        # Split buffer A/B: primera mitad vs segunda mitad de sweeps
        half = n_sweeps // 2
        a_noise = self._rng.normal(0, noise_std, size=(half, n_samples))
        b_noise = self._rng.normal(0, noise_std, size=(half, n_sweeps and n_samples))
        # Reusar ruido total si split demasiado pequeño
        if half < 1:
            a = waveform
            b = waveform
        else:
            a = clean + a_noise.mean(axis=0)
            b = clean + b_noise.mean(axis=0)

        # FFT. Ganancia coherente de la ventana Hann: para un tono puro
        # windowed, |FFT[bin]| ≈ amplitud_pa * sum(window)/2, así que hay
        # que deshacer ese factor para volver a Pascales reales antes de
        # convertir a dB SPL (ref 20 µPa) -- si no, el espectro queda en
        # dB "crudo" sin referencia (valores tipo -90 dB en vez del rango
        # real -5..+20 dB SPL que muestra un equipo real).
        window = np.hanning(n_samples)
        coherent_gain = window.sum() / 2
        spectrum = np.abs(np.fft.rfft(waveform * window)) / coherent_gain
        freqs = np.fft.rfftfreq(n_samples, 1 / fs)

        # Espectro de la diferencia A-B: la señal común a ambos buffers se
        # cancela, así que esto aísla el ruido no correlacionado -- mismo
        # truco que usa un equipo real para estimar noise floor sin
        # contaminarlo con la señal (a diferencia de tomar un percentil
        # DENTRO de la banda de la señal, que sobreestima el SNR con pocos
        # bins por sesgo de estadística de orden).
        diff = (a - b) / 2
        spectrum_diff = np.abs(np.fft.rfft(diff * window)) / coherent_gain

        snr_per_band = {}
        pass_per_band = {}
        ratio = self.normative["band_halfwidth_ratio"]
        min_snr = self.normative["min_snr_db"]
        for band_hz in self.normative["bands_hz"]:
            mask = (freqs >= band_hz * ratio) & (freqs <= band_hz / ratio)
            if not mask.any():
                snr_per_band[band_hz] = 0.0
                pass_per_band[band_hz] = False
                continue
            # Potencia total medida (señal+ruido, mezclados incoherentemente)
            # menos potencia de ruido estimada por A-B = potencia de señal
            # "limpia". Comparar max-de-señal contra mean-de-ruido (como se
            # hacía antes) sesga el SNR +6..10 dB incluso sin señal real,
            # porque un máximo y una media de la MISMA distribución de
            # ruido no son comparables.
            signal_power = float(np.mean(spectrum[mask] ** 2))
            noise_power = float(np.mean(spectrum_diff[mask] ** 2))
            clean_power = max(0.0, signal_power - noise_power)
            if clean_power <= 0 or noise_power <= 0:
                snr_db = -100.0
            else:
                snr_db = 10 * np.log10(clean_power / noise_power)
            snr_per_band[band_hz] = float(snr_db)
            pass_per_band[band_hz] = snr_db >= min_snr

        n_pass = sum(1 for v in pass_per_band.values() if v)
        overall_pass = n_pass >= self.normative["pass_bands_min"]

        # Espectro recortado al rango visible
        spec_lo = self.normative["spectrum_low_hz"]
        spec_hi = self.normative["spectrum_high_hz"]
        spec_mask = (freqs >= spec_lo) & (freqs <= spec_hi)
        spectrum_db = 20 * np.log10(spectrum[spec_mask] / 20e-6 + 1e-12)
        freqs_plot = freqs[spec_mask]

        # % Reproducibilidad: correlación de Pearson entre buffers A/B, el
        # criterio de control de calidad estándar en equipos clínicos
        # (ILO/Otoport). >70% típicamente aceptable.
        if np.std(a) > 0 and np.std(b) > 0:
            corr = float(np.corrcoef(a, b)[0, 1])
        else:
            corr = 0.0
        reproducibility_pct = max(0.0, corr) * 100

        # Estabilidad del estímulo: jitter simulado del nivel de click
        # sweep a sweep (probe fit / sello del canal). Mismo seed que el
        # resto de la captura -> reproducible dentro de la sesión.
        jitter_db = self.normative["stim_jitter_db"]
        tolerance_db = self.normative["stim_jitter_tolerance_db"]
        click_levels = self._rng.normal(level_db, jitter_db, size=max(n_sweeps, 1))
        measured_jitter = float(np.std(click_levels))
        stability_pct = max(0.0, min(100.0, 100 * (1 - measured_jitter / tolerance_db)))

        # Respuesta total vs noise floor, en dB SPL real (misma referencia
        # 20 µPa usada para sintetizar clean/noise), análogo al "Response"
        # / "Noise" que reporta un equipo TEOAE real.
        response_rms_pa = float(np.sqrt(np.mean(clean ** 2)))
        noise_rms_pa = noise_std / np.sqrt(max(n_sweeps, 1))
        total_response_db = 20 * np.log10(response_rms_pa / 20e-6) if response_rms_pa > 0 else -100.0
        total_noise_db = 20 * np.log10(noise_rms_pa / 20e-6) if noise_rms_pa > 0 else -100.0

        return {
            "time_ms": t * 1000,
            "waveform": waveform,
            "sweep_checkpoints": sweep_checkpoints,
            "n_sweeps": n_sweeps,
            "spectrum_db": spectrum_db,
            "freqs": freqs_plot,
            "snr_per_band": snr_per_band,
            "pass_per_band": pass_per_band,
            "overall_pass": overall_pass,
            "n_pass": n_pass,
            "n_bands": len(self.normative["bands_hz"]),
            "wave_a": a,
            "wave_b": b,
            "reproducibility_pct": reproducibility_pct,
            "stability_pct": stability_pct,
            "total_response_db": total_response_db,
            "total_noise_db": total_noise_db,
        }
