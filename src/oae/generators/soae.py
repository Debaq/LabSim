"""Generador sintético SOAE (Spontaneous Otoacoustic Emissions).

Emisiones espontáneas: la cóclea sana emite tonos puros de forma continua,
sin ningún estímulo. El registro clínico es simplemente grabar el conducto
con la sonda en silencio durante 30-60 s y promediar espectros de potencia.

OJO con el mecanismo (no es el de TEOAE): sin estímulo no hay promediación
coherente, así que el NIVEL MEDIO del ruido no baja con los promedios --
lo que baja es su DISPERSIÓN bin a bin (~4.34/sqrt(k) dB). El SOAE, que es
una señal determinística, se queda clavado en su nivel mientras el ruido
deja de fluctuar: por eso los picos emergen y los falsos picos de los
primeros segundos desaparecen. De ahí el criterio clásico: pico >= 3 dB
sobre el piso local Y reproducible en dos mitades independientes del
registro.

Modelo (todo sintético, sin audio device):

- Prevalencia: los SOAE NO están en todos los oídos normales (~40-50%),
  son más frecuentes en OD que en OI. La ausencia por sí sola no es
  patológica -- el panel tiene que decirlo, es el punto pedagógico.
- Frecuencia: agrupados en 1-2 kHz, rara vez sobre 4.5 kHz o bajo 700 Hz,
  y dos picos del mismo oído no caen pegados (separación mínima ~6%,
  el "0.4 bark" de la literatura).
- Nivel: mediana cercana a 0 dB SPL, casi nunca sobre 20 dB SPL.
- Patología: se apagan con daño de CCE o con pérdida conductiva (ver
  oae_attenuation_db); con umbral > ~30 dB HL en esa zona no hay SOAE.
  En pérdida neural/retrococlear la cóclea está intacta y los SOAE
  siguen presentes -- mismo contraste con ABR que el resto del módulo.
- El docente manda: si el caso trae `soae_mode` 'presentes'/'ausentes'
  (tab EOA del backend) el hallazgo queda fijo, y `soae_peaks` permite
  cargar los picos a mano (frecuencia + nivel) para poder mostrarlos en
  clase o evaluar sobre algo que no dependa del sorteo.

`generate()` devuelve la captura por frames (promedios acumulados) para
que el panel la anime como un equipo real, no la respuesta final de golpe.
"""
import numpy as np

from oae.generators.base import (
    OaeGeneratorBase,
    case_fingerprint,
    stable_seed,
    oae_attenuation_db,
    oae_noise_offset_db,
    oae_variability_db,
)


class SoaeGenerator(OaeGeneratorBase):
    """Síntesis SOAE - registro en silencio + detección de picos."""

    def __init__(self, seed: int | None = None):
        super().__init__("soae", seed)
        self._rng = np.random.default_rng(self._seed)

    def _seed_from_params(self, ear: str = "OD", case: dict | None = None,
                          record_s: float | None = None) -> int:
        return stable_seed("soae", ear, case_fingerprint(case),
                           round(float(record_s or 0), 1))

    # ------------------------------------------------------------------
    # Ejes / piso de ruido
    # ------------------------------------------------------------------
    def spectrum_freqs(self) -> np.ndarray:
        """Bins del espectro analizado (rango clínico de búsqueda de SOAE)."""
        n = int(self.normative["fft_n"])
        freqs = np.fft.rfftfreq(n, 1 / self.SAMPLE_RATE)
        lo = float(self.normative["spectrum_low_hz"])
        hi = float(self.normative["spectrum_high_hz"])
        return freqs[(freqs >= lo) & (freqs <= hi)]

    def block_seconds(self) -> float:
        """Duración de audio de UN promedio (una ventana FFT)."""
        return float(self.normative["fft_n"]) / self.SAMPLE_RATE

    def _noise_floor_db(self, freqs: np.ndarray, case: dict | None) -> np.ndarray:
        """Piso de ruido esperado (dB SPL por bin) tras todos los promedios.

        El ruido del conducto es de baja frecuencia (respiración, latido,
        movimiento) y sube hacia los graves; en agudos el que manda es el
        ruido propio del micrófono, que sube apenas. `case` puede subirlo
        parejo (paciente inquieto -- oae_noise_offset_db): ese es el
        registro "no concluyente por ruido" que el alumno debe distinguir
        de la ausencia real de SOAE.
        """
        base = float(self.normative["noise_floor_db_spl"])
        lf = float(self.normative["noise_floor_lf_rise_db_per_oct"])
        hf = float(self.normative["noise_floor_hf_rise_db_per_oct"])
        shape = (base
                 + lf * np.clip(np.log2(2000.0 / freqs), 0, None)
                 + hf * np.clip(np.log2(freqs / 4000.0), 0, None))
        return shape + oae_noise_offset_db(case)

    # ------------------------------------------------------------------
    # Picos verdaderos del oído
    # ------------------------------------------------------------------
    def _configured_peaks(self, case: dict | None) -> list[dict]:
        """Picos que el docente cargó a mano para este oído, o [].

        El nivel cargado es el que se ve: NO se le resta la atenuación por
        patología ni la pérdida por sello. Si el docente pide mostrar un
        SOAE de 6 dB SPL en 1.5 kHz, tiene que salir 6 dB SPL -- lo único
        que todavía puede taparlo es el ruido del paciente, que sube el
        piso (y ese sí es un hallazgo que se quiere poder enseñar).
        """
        if not case:
            return []
        try:
            raw = case.get("soae_peaks") or []
        except AttributeError:
            return []
        peaks = []
        for item in raw:
            try:
                freq = float(item["hz"])
                level = float(item.get("db", self.normative["peak_level_mean_db_spl"]))
            except (TypeError, ValueError, KeyError, IndexError):
                continue
            if freq <= 0:
                continue
            peaks.append({"freq_hz": freq, "level_db_spl": level})
        peaks.sort(key=lambda p: p["freq_hz"])
        return peaks

    @staticmethod
    def _mode(case: dict | None) -> str:
        """'auto' (sorteo por prevalencia), 'presentes' o 'ausentes'."""
        if not case:
            return "auto"
        try:
            mode = case.get("soae_mode") or "auto"
        except AttributeError:
            return "auto"
        return mode if mode in ("auto", "presentes", "ausentes") else "auto"

    def true_peaks(self, ear: str, case: dict | None, rng) -> list[dict]:
        """Picos SOAE realmente presentes en ese oído (antes de medirlos).

        En 'auto' se sortean: el mismo tipo de caso no da siempre el mismo
        oído, y el seed depende de oído+caso, así que volver a medir al
        mismo paciente da el mismo hallazgo. Si el caso fija el modo, manda
        el docente (ver _configured_peaks / _mode).
        """
        mode = self._mode(case)
        if mode == "ausentes":
            return []
        configurados = self._configured_peaks(case)
        if mode == "presentes" and configurados:
            return configurados

        prevalence = float(self.normative["prevalence_pct"]) / 100.0
        if ear == "OD":
            prevalence *= float(self.normative["prevalence_right_ear_factor"])
        # En 'presentes' sin picos cargados el sorteo sigue eligiendo
        # cuántos y en qué frecuencias, pero la presencia está garantizada.
        if mode != "presentes" and rng.random() > min(prevalence, 0.95):
            return []

        n_target = 1 + int(rng.poisson(float(self.normative["peak_count_lambda"])))
        n_target = min(n_target, int(self.normative["max_peaks"]))
        f_min = float(self.normative["peak_freq_min_hz"])
        f_max = float(self.normative["peak_freq_max_hz"])
        center = np.log2(float(self.normative["peak_freq_center_hz"]))
        spread = float(self.normative["peak_freq_spread_oct"])
        spacing = float(self.normative["min_peak_spacing_ratio"])
        lvl_mean = float(self.normative["peak_level_mean_db_spl"])
        lvl_sd = float(self.normative["peak_level_sd_db"])
        lvl_max = float(self.normative["peak_level_max_db_spl"])
        # La variabilidad biológica del caso también dispersa el nivel de
        # los picos, igual que hace con TEOAE/DPOAE.
        lvl_sd = max(1.0, lvl_sd + oae_variability_db(case, 0.0))

        peaks = []
        for _ in range(n_target * 6):
            if len(peaks) >= n_target:
                break
            f = float(2 ** rng.normal(center, spread))
            if not (f_min <= f <= f_max):
                continue
            # Dos SOAE del mismo oído no coexisten pegados: se suprimen
            # mutuamente (separación mínima ~0.4 bark).
            if any(max(f, p) / min(f, p) < spacing for p in (q["freq_hz"] for q in peaks)):
                continue
            level = float(np.clip(rng.normal(lvl_mean, lvl_sd), -12.0, lvl_max))
            # Patología + perfil por frecuencia + pérdida por sello: un
            # SOAE de 2 dB SPL con 20 dB de atenuación ya no sale del ruido.
            atten = oae_attenuation_db(case, f)
            # Los SOAE son el hallazgo más frágil de las cuatro pruebas: se
            # apagan con daño de CCE mucho antes de que caiga la TEOAE, así
            # que por sobre max_atten_for_peaks_db el pico directamente no
            # existe (y no queda a merced de que el sorteo le diera un nivel
            # alto). Ver la nota de patología en el docstring del módulo.
            if atten > float(self.normative["max_atten_for_peaks_db"]):
                continue
            peaks.append({"freq_hz": f, "level_db_spl": level - atten})
        peaks.sort(key=lambda p: p["freq_hz"])
        return peaks

    # ------------------------------------------------------------------
    # Espectro de un promedio parcial
    # ------------------------------------------------------------------
    def _half_spectrum(self, freqs, floor_db, peaks, k: int, rng) -> np.ndarray:
        """Potencia (lineal) de una mitad del registro con k promedios.

        El ruido de cada bin de una FFT es exponencial (chi2, 2 gl);
        promediar k espectros lo vuelve una gamma(k, 1/k): MISMO valor
        esperado, desviación /sqrt(k). Por eso el piso no baja pero sí se
        aplana, y un pico de pocos dB deja de confundirse con una
        fluctuación. El SOAE, en cambio, suma potencia constante: no se
        promedia a cero.
        """
        power = 10 ** (floor_db / 10) * rng.gamma(k, 1.0 / k, size=freqs.size)
        df = self.SAMPLE_RATE / float(self.normative["fft_n"])
        sigma = float(self.normative["peak_bandwidth_bins"]) * df
        jitter = float(self.normative["peak_level_jitter_db"])
        for peak in peaks:
            # El nivel de un SOAE fluctúa un poco entre bloques (deriva
            # fisiológica), pero no baja con los promedios.
            level = peak["level_db_spl"] + rng.normal(0, jitter / np.sqrt(k))
            power += 10 ** (level / 10) * np.exp(
                -0.5 * ((freqs - peak["freq_hz"]) / sigma) ** 2)
        return power

    def _local_floor_db(self, power: np.ndarray, k: int) -> np.ndarray:
        """Piso local estimado por mediana móvil, como hace el equipo.

        Mediana y no media: si la ventana pisa un SOAE, la media se
        contamina con el pico y el SNR sale subestimado. Los bordes se
        rellenan con la mediana del primer/último bloque completo.
        """
        win = int(self.normative["floor_window_bins"]) | 1
        if power.size <= win:
            return np.full(power.shape, 10 * np.log10(np.median(power)))
        view = np.lib.stride_tricks.sliding_window_view(power, win)
        med = np.median(view, axis=1)
        pad = win // 2
        med = np.concatenate([np.full(pad, med[0]), med, np.full(pad, med[-1])])
        # La mediana de una gamma(k, 1/k) está por debajo de su media, y
        # el sesgo depende de k (con 1 promedio son -1.6 dB, con 64 casi
        # nada): sin corregirlo por k el criterio de 3 dB se ablandaría a
        # medida que avanza el registro. Aproximación de Wilson-Hilferty.
        bias = 30 * np.log10(max(1.0 - 1.0 / (9.0 * max(k, 1)), 1e-6))
        return 10 * np.log10(np.maximum(med, 1e-12)) - bias

    def _detect(self, freqs, total_db, floor_db, a_db, b_db) -> list[dict]:
        """Picos detectados sobre el espectro promediado.

        Criterio clínico (no "el máximo del espectro"):
          1) máximo local aislado (no un bin cualquiera del ruido),
          2) >= min_snr_db sobre el piso local,
          3) reproducible: presente en las DOS mitades independientes del
             registro con al menos min_snr_half_db.
        La condición 3 es la que mata los falsos positivos de los primeros
        promedios, igual que en un registro real.
        """
        min_snr = float(self.normative["min_snr_db"])
        min_half = float(self.normative["min_snr_half_db"])
        sep = int(self.normative["peak_separation_bins"])
        snr = total_db - floor_db
        peaks = []
        for i in range(sep, snr.size - sep):
            if snr[i] < min_snr:
                continue
            window = snr[i - sep:i + sep + 1]
            if snr[i] < window.max():
                continue
            if (a_db[i] - floor_db[i]) < min_half or (b_db[i] - floor_db[i]) < min_half:
                continue
            # Interpolación parabólica en dB sobre 3 bins: la frecuencia
            # del SOAE cae entre bins y el equipo la informa con decimales.
            y0, y1, y2 = total_db[i - 1], total_db[i], total_db[i + 1]
            denom = (y0 - 2 * y1 + y2)
            delta = 0.0 if denom == 0 else 0.5 * (y0 - y2) / denom
            delta = float(np.clip(delta, -0.5, 0.5))
            df = freqs[1] - freqs[0]
            # Nivel de la emisión, no del bin: al bin lo llena señal +
            # ruido, así que se le resta la potencia del piso (para un
            # pico de 3 dB de SNR eso son ~3 dB menos, nada despreciable).
            emission = 10 ** (y1 / 10) - 10 ** (floor_db[i] / 10)
            peaks.append({
                "freq_hz": float(freqs[i] + delta * df),
                "level_db_spl": float(10 * np.log10(max(emission, 1e-12))),
                "bin_level_db_spl": float(y1),
                "floor_db_spl": float(floor_db[i]),
                "snr_db": float(snr[i]),
                "bin": i,
            })
        # Un mismo SOAE puede dejar dos bins vecinos sobre el criterio:
        # queda el más alto de cada grupo.
        merged = []
        for peak in sorted(peaks, key=lambda p: -p["snr_db"]):
            if all(abs(peak["bin"] - m["bin"]) > sep for m in merged):
                merged.append(peak)
        merged.sort(key=lambda p: p["freq_hz"])
        return merged

    # ------------------------------------------------------------------
    # Captura
    # ------------------------------------------------------------------
    def generate(self, ear: str = "OD", case: dict | None = None,
                 record_s: float | None = None) -> dict:
        """Registro SOAE completo, devuelto como secuencia de promedios.

        `record_s` es la duración del registro en segundos (lo que el
        operador elige en el equipo); de ahí sale el nº total de promedios
        = record_s / block_seconds(). Cada frame trae el espectro
        acumulado hasta ese instante, su piso local y los picos que ya
        cumplen criterio, para que el panel anime la emergencia de los
        SOAE por sobre el ruido.
        """
        record_s = float(record_s or self.normative["default_record_s"])
        rng = np.random.default_rng(self._seed_from_params(ear, case, record_s))
        self._rng = rng
        freqs = self.spectrum_freqs()
        floor_db = self._noise_floor_db(freqs, case)
        peaks = self.true_peaks(ear, case, rng)

        block_s = self.block_seconds()
        # Dos mitades independientes (A/B) -> cada una promedia la mitad
        # de los bloques del registro.
        k_total = max(2, int(record_s / block_s) // 2)
        n_frames = int(self.normative["n_frames"])
        schedule = np.unique(np.geomspace(1, k_total, n_frames).astype(int))

        frames = []
        # El ruido se acumula: cada frame agrega bloques al promedio previo
        # en vez de re-sortear el espectro desde cero (si no, el trazo
        # "salta" y no se ve la convergencia).
        acc_a = np.zeros(freqs.size)
        acc_b = np.zeros(freqs.size)
        done = 0
        for k in schedule:
            step = int(k) - done
            if step <= 0:
                continue
            acc_a = (acc_a * done + self._half_spectrum(freqs, floor_db, peaks, step, rng) * step) / (done + step)
            acc_b = (acc_b * done + self._half_spectrum(freqs, floor_db, peaks, step, rng) * step) / (done + step)
            done += step
            total = 0.5 * (acc_a + acc_b)
            total_db = 10 * np.log10(np.maximum(total, 1e-12))
            a_db = 10 * np.log10(np.maximum(acc_a, 1e-12))
            b_db = 10 * np.log10(np.maximum(acc_b, 1e-12))
            # `total` promedia las dos mitades: 2*done espectros en total.
            local_floor = self._local_floor_db(total, 2 * done)
            frames.append({
                "n_avg": int(2 * done),
                "elapsed_s": float(2 * done * block_s),
                "spec_db": total_db,
                "spec_a_db": a_db,
                "spec_b_db": b_db,
                "floor_db": local_floor,
                "peaks": self._detect(freqs, total_db, local_floor, a_db, b_db),
            })

        final = frames[-1]
        return {
            "ear": ear,
            "freqs": freqs,
            "frames": frames,
            "record_s": float(2 * done * block_s),
            "n_avg_total": int(2 * done),
            "bin_width_hz": float(freqs[1] - freqs[0]),
            "expected_floor_db": floor_db,
            "true_peaks": peaks,
            "peaks": final["peaks"],
            "n_peaks": len(final["peaks"]),
            "present": bool(final["peaks"]),
        }
