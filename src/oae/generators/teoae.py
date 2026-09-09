"""Generador sintético TEOAE (Transient Evoked Otoacoustic Emissions).

Click → respuesta coclear sintetizada como banco de componentes log-espaciados
(no 5 sinusoides puras): cada componente tiene su propia latencia y decaimiento
dependientes de la frecuencia (agudos temprano y cortos, graves tarde y largos),
que es lo que le da a la TEOAE real su forma de "chirp" invertido y su espectro
ancho y rugoso en vez de 5 picos de laboratorio.

La captura se entrega como una secuencia de frames (promedio acumulado a k
barridos, con split-buffer A/B alternando barridos pares/impares) para que el
panel anime TODOS los gráficos mientras "corre" el examen, igual que un equipo
real: el ruido baja ~1/sqrt(k), la reproducibilidad sube, y el SNR por banda
cruza el umbral en algún momento de la captura.
"""
import numpy as np
from oae.generators.base import (
    OaeGeneratorBase,
    case_fingerprint,
    oae_attenuation_db,
    oae_noise_offset_db,
    oae_probe_fit,
    oae_probe_loss_db,
    oae_variability_db,
    stable_seed,
)


class TeoaeGenerator(OaeGeneratorBase):
    """Síntesis TEOAE. Sin QTimer aquí: cada llamada a generate() es síncrona,
    el caller (panel) decide cuándo disparar y cuándo actualizar el plot."""

    # Densidad del banco de componentes. 16/octava sobre 0.5-5 kHz ≈ 53
    # componentes: suficiente para que el espectro se vea continuo y con
    # estructura fina, barato de sintetizar.
    COMPONENTS_PER_OCTAVE = 16
    # Caída de energía fuera del rango de bandas normativas (la TEOAE real
    # se concentra en 1-4 kHz y se apaga rápido hacia los extremos).
    SKIRT_DB_PER_OCTAVE = 14.0
    # Estructura fina: la respuesta real no es plana dentro de la banda,
    # tiene picos y valles de varios dB de componente a componente.
    FINE_STRUCTURE_SD_DB = 2.5
    # Latencia de la emisión a 1 kHz; escala con (1000/f)^0.5 (agudos antes).
    LATENCY_1K_MS = 9.0
    LATENCY_MIN_MS = 2.5
    SNR_FLOOR_DB = -12.0
    BANDPASS_LOW_HZ = 400.0
    BANDPASS_HIGH_HZ = 6000.0

    def __init__(self, seed: int | None = None):
        super().__init__("teoae", seed)
        self._rng = np.random.default_rng(self._seed)

    def _seed_from_params(self, ear: str = "OD", level_db: float | None = None,
                          n_sweeps: int | None = None,
                          case: dict | None = None) -> int:
        """Seed de la captura: oído + parámetros + PERFIL DEL CASO.

        stable_seed y no hash(): hash() saltea por proceso, así que la
        misma captura cambiaba de una apertura de LabSim a la siguiente
        (con un SNR borderline eso mueve el PASS/REFER). Ver base.py.

        El caso entra al seed para que el ruido residual y la estructura
        fina sean propios de ESE paciente: sin él, dos pacientes con el
        mismo nivel y promedios compartían el trazo de ruido bit a bit
        (y `variabilidad_db` solo escalaba una curva común).
        """
        return stable_seed("teoae", ear, level_db or 0, n_sweeps or 0,
                           case_fingerprint(case))

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

    # ------------------------------------------------------------------
    # Síntesis de la respuesta "limpia" (sin ruido)
    # ------------------------------------------------------------------
    def _component_levels_db(self, freqs_hz: np.ndarray,
                             case: dict | None) -> np.ndarray:
        """Nivel esperado (dB SPL) por componente, interpolado en log-frecuencia
        sobre expected_response_db y con caída fuera del rango de bandas.

        La atenuación del caso se pide POR componente: el perfil por
        frecuencia del paciente (muesca en 4 kHz, caída en agudos) tiene
        que deformar el espectro, no bajarlo parejo."""
        bands = np.array(self.normative["bands_hz"], dtype=float)
        expected = self.normative["expected_response_db"]
        levels = np.array([float(expected.get(str(int(b)), 5)) for b in bands])
        lf = np.log2(freqs_hz)
        lb = np.log2(bands)
        interp = np.interp(lf, lb, levels)
        below = np.clip(lb[0] - lf, 0.0, None)
        above = np.clip(lf - lb[-1], 0.0, None)
        atten = np.array([oae_attenuation_db(case, f) for f in freqs_hz])
        return interp - self.SKIRT_DB_PER_OCTAVE * (below + above) - atten

    def _synth_clean(self, t: np.ndarray, case: dict | None, rng) -> np.ndarray:
        lo = float(self.normative["spectrum_low_hz"])
        hi = float(self.normative["spectrum_high_hz"])
        n_comp = max(8, int(round(self.COMPONENTS_PER_OCTAVE * np.log2(hi / lo))))
        fc = np.logspace(np.log10(lo), np.log10(hi), n_comp)

        amp = 10 ** ((self._component_levels_db(fc, case) - 94) / 20)
        fine_sd = oae_variability_db(case, self.FINE_STRUCTURE_SD_DB)
        amp = amp * 10 ** (rng.normal(0, fine_sd, n_comp) / 20)
        # N componentes de fase aleatoria dentro de una banda suman en potencia
        # (RMS = a*sqrt(N/2)); dividir por sqrt(N_banda) deja el RMS de la banda
        # igual al de una sinusoide de amplitud 10**((L-94)/20), que es lo que
        # expected_response_db pretende describir.
        bands = np.array(self.normative["bands_hz"], dtype=float)
        idx = np.argmin(np.abs(np.log2(fc[:, None] / bands[None, :])), axis=1)
        counts = np.bincount(idx, minlength=len(bands)).astype(float)
        amp = amp / np.sqrt(counts[idx])

        lat = np.clip(self.LATENCY_1K_MS * (1000.0 / fc) ** 0.5,
                      self.LATENCY_MIN_MS, None) * 1e-3
        tau = self.normative["decay_ms"] * (1000.0 / fc) ** 0.5 * 1e-3

        u = (t[None, :] - lat[:, None]) / tau[:, None]
        u_pos = np.clip(u, 0.0, None)
        # Onset rápido (15% de tau) + decaimiento exponencial: paquete de
        # energía por componente en vez de un escalón en t=0.
        env = np.exp(-u_pos) * (1.0 - np.exp(-u_pos / 0.15)) * (u > 0)
        phase = rng.uniform(0, 2 * np.pi, n_comp)
        osc = np.sin(2 * np.pi * fc[:, None] * t[None, :] + phase[:, None])
        return (amp[:, None] * env * osc).sum(axis=0)

    def _shaped_noise(self, rng, n_sweeps: int, n_samples: int,
                      noise_std: float) -> np.ndarray:
        """Ruido de canal por barrido, con espectro realista en vez de blanco.

        El ruido en el conducto (respiración, deglución, mioclonías, ruido de
        sala) es de baja frecuencia: cae ~3 dB/oct sobre 200 Hz y prácticamente
        no existe sobre 5-6 kHz. Con ruido blanco, en cambio, casi toda su
        potencia cae FUERA de la banda de análisis (0.5-5 kHz sobre 22 kHz de
        Nyquist): el SNR por banda salía ~15 dB por encima de lo que muestra un
        equipo real para la misma reproducibilidad.
        """
        fs = self.SAMPLE_RATE
        freqs = np.fft.rfftfreq(n_samples, 1 / fs)
        shape = np.ones_like(freqs)
        knee = 200.0
        above = freqs > knee
        shape[above] = (knee / freqs[above]) ** 0.5
        # Pasabanda del equipo (~0.4-6 kHz): un TEOAE real filtra la señal
        # antes de mostrarla, por eso el trazo se ve como una oscilación que
        # decae y no como pasto de ruido de banda ancha.
        shape *= (freqs >= self.BANDPASS_LOW_HZ) & (freqs <= self.BANDPASS_HIGH_HZ)
        white = rng.normal(0.0, 1.0, size=(n_sweeps, n_samples))
        shaped = np.fft.irfft(np.fft.rfft(white, axis=1) * shape,
                              n=n_samples, axis=1)
        rms = float(np.sqrt(np.mean(shaped ** 2)))
        return shaped * (noise_std / rms if rms > 0 else 0.0)

    # ------------------------------------------------------------------
    # Análisis de un promedio parcial (un frame de la captura)
    # ------------------------------------------------------------------
    def _analyze(self, waveform, a, b, window, coherent_gain, freqs,
                 spec_mask, clean, n_sweeps_done, noise_std, click_levels):
        # FFT. Ganancia coherente de la ventana Hann: para un tono puro
        # windowed, |FFT[bin]| ≈ amplitud_pa * sum(window)/2, así que hay que
        # deshacer ese factor para volver a Pascales reales antes de convertir
        # a dB SPL (ref 20 µPa).
        spectrum = np.abs(np.fft.rfft(waveform * window)) / coherent_gain
        # Espectro de la diferencia A-B: la señal común a ambos buffers se
        # cancela, así que esto aísla el ruido no correlacionado -- mismo truco
        # que usa un equipo real para estimar noise floor sin contaminarlo con
        # la señal.
        diff = (a - b) / 2
        spectrum_diff = np.abs(np.fft.rfft(diff * window)) / coherent_gain

        snr_per_band = {}
        pass_per_band = {}
        ratio = self.normative["band_halfwidth_ratio"]
        min_snr = self.normative["min_snr_db"]
        for band_hz in self.normative["bands_hz"]:
            mask = (freqs >= band_hz * ratio) & (freqs <= band_hz / ratio)
            if not mask.any():
                snr_per_band[band_hz] = self.SNR_FLOOR_DB
                pass_per_band[band_hz] = False
                continue
            # Potencia medida (señal+ruido) menos potencia de ruido estimada
            # por A-B = potencia de señal limpia.
            signal_power = float(np.mean(spectrum[mask] ** 2))
            noise_power = float(np.mean(spectrum_diff[mask] ** 2))
            clean_power = max(0.0, signal_power - noise_power)
            if clean_power <= 0 or noise_power <= 0:
                snr_db = self.SNR_FLOOR_DB
            else:
                # Piso: sin emisión el SNR real fluctúa alrededor de 0, no se
                # va a -100 dB. Sin clamp las barras rompen la escala del plot.
                snr_db = max(self.SNR_FLOOR_DB,
                             10 * np.log10(clean_power / noise_power))
            snr_per_band[band_hz] = float(snr_db)
            pass_per_band[band_hz] = snr_db >= min_snr

        n_pass = sum(1 for v in pass_per_band.values() if v)
        overall_pass = n_pass >= self.normative["pass_bands_min"]

        spectrum_db = 20 * np.log10(spectrum[spec_mask] / 20e-6 + 1e-12)
        noise_db = 20 * np.log10(spectrum_diff[spec_mask] / 20e-6 + 1e-12)

        # % Reproducibilidad: correlación de Pearson entre buffers A/B, el
        # criterio de control de calidad estándar en equipos clínicos.
        if np.std(a) > 0 and np.std(b) > 0:
            corr = float(np.corrcoef(a, b)[0, 1])
        else:
            corr = 0.0

        # Estabilidad del estímulo: jitter del nivel de click de los barridos
        # ya presentados (probe fit / sello del canal).
        tolerance_db = self.normative["stim_jitter_tolerance_db"]
        measured_jitter = float(np.std(click_levels[:max(2, n_sweeps_done)]))
        stability = max(0.0, min(100.0, 100 * (1 - measured_jitter / tolerance_db)))

        response_rms_pa = float(np.sqrt(np.mean(clean ** 2)))
        noise_rms_pa = noise_std / np.sqrt(max(n_sweeps_done, 1))
        return {
            "n_sweeps": int(n_sweeps_done),
            "waveform": waveform,
            "wave_a": a,
            "wave_b": b,
            "spectrum_db": spectrum_db,
            "noise_db": noise_db,
            "snr_per_band": snr_per_band,
            "pass_per_band": pass_per_band,
            "overall_pass": overall_pass,
            "n_pass": n_pass,
            "reproducibility_pct": max(0.0, corr) * 100,
            "stability_pct": stability,
            "total_response_db": (20 * np.log10(response_rms_pa / 20e-6)
                                  if response_rms_pa > 0 else -100.0),
            "total_noise_db": (20 * np.log10(noise_rms_pa / 20e-6)
                               if noise_rms_pa > 0 else -100.0),
        }

    def generate(self, level_db: float, n_sweeps: int, ear: str = "OD",
                 case: dict | None = None, n_frames: int = 40) -> dict:
        """Genera una 'medición' TEOAE completa.

        Devuelve el resultado final (mismas keys que antes: time_ms, waveform,
        wave_a/wave_b, spectrum_db, freqs, snr_per_band, ...) más "frames": la
        lista de promedios parciales, en orden, para animar la captura. El
        último frame ES el resultado final (no hay salto al terminar).
        """
        # Re-seedear para que la misma (level, ear, n_sweeps) → misma curva
        # entre capturas (consistente visualmente), pero distinta entre oídos
        # y entre niveles.
        rng = np.random.default_rng(
            self._seed_from_params(ear, level_db, n_sweeps, case))
        self._rng = rng

        fs = self.SAMPLE_RATE
        win_ms = self.normative["window_ms"]
        n_samples = int(round(win_ms * 1e-3 * fs))
        t = np.arange(n_samples) / fs
        n_sweeps = max(2, int(n_sweeps))

        clean = self._synth_clean(t, case, rng)

        # Ruido de canal por barrido. Al promediar k barridos baja ~1/sqrt(k):
        # eso es lo que hace que la captura "se construya" en pantalla. El
        # caso puede subirlo (paciente inquieto): mismo oído, misma cóclea,
        # pero REFER por ruido -- ver oae_noise_offset_db.
        noise_db = (self.normative["noise_floor_db_spl"]
                    + oae_noise_offset_db(case))
        noise_std = 10 ** ((noise_db - 94) / 20)
        noise = self._shaped_noise(rng, n_sweeps, n_samples, noise_std)
        # Split-buffer A/B como el equipo real: barridos pares a A, impares a B.
        cum_all = np.cumsum(noise, axis=0)
        cum_a = np.cumsum(noise[0::2], axis=0)
        cum_b = np.cumsum(noise[1::2], axis=0)

        # Sello de sonda: con la sonda floja llega menos estímulo al conducto
        # (20*log10 del fit, igual que el probe check) y el nivel es más
        # inestable, así que la barra de estabilidad del panel baja.
        fit = oae_probe_fit(case)
        jitter_db = self.normative["stim_jitter_db"]
        if fit is not None:
            jitter_db *= 1.0 + 2.0 * (1.0 - fit)
        click_levels = rng.normal(level_db - oae_probe_loss_db(case),
                                  jitter_db, size=n_sweeps)

        window = np.hanning(n_samples)
        coherent_gain = window.sum() / 2
        freqs = np.fft.rfftfreq(n_samples, 1 / fs)
        spec_mask = ((freqs >= self.normative["spectrum_low_hz"])
                     & (freqs <= self.normative["spectrum_high_hz"]))

        n_frames = int(np.clip(n_frames, 2, 400))
        ks = np.unique(np.linspace(2, n_sweeps, n_frames).astype(int))
        frames = []
        for k in ks:
            k = int(k)
            na = (k + 1) // 2
            nb = k // 2
            a = clean + cum_a[na - 1] / na
            b = clean + cum_b[nb - 1] / nb
            waveform = clean + cum_all[k - 1] / k
            frames.append(self._analyze(waveform, a, b, window, coherent_gain,
                                        freqs, spec_mask, clean, k, noise_std,
                                        click_levels))

        result = dict(frames[-1])
        result.update({
            "time_ms": t * 1000,
            "freqs": freqs[spec_mask],
            "n_bands": len(self.normative["bands_hz"]),
            "n_sweeps_total": n_sweeps,
            "frames": frames,
        })
        return result
