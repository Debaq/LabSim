"""Generador sintético DPOAE (Distortion Product Otoacoustic Emissions).

Un equipo DPOAE real mide UN punto a la vez: presenta el par f1/f2
(f1 = f2/ratio) durante unos segundos, promedia, y lee la energía del
bin 2f1-f2 contra los bins vecinos (noise floor). Recién ahí pasa al
siguiente f2 y agrega el punto al DP-grama.

Por eso este generador NO devuelve la curva de golpe: devuelve la
captura punto por punto y, dentro de cada punto, la secuencia de
promedios parciales (averages_per_point) con el espectro FFT de ese
instante. Así el panel puede animar la medición como el equipo real:
el piso de ruido baja ~10*log10(k) mientras el DP se estabiliza.

- `generate()`  -> DP-grama (barrido de f2)
- `generate_io()` -> función I/O (crecimiento: L2 vs DP a f2 fijo), en el
  mismo formato de puntos, para que se construya en la misma corrida.
"""
import numpy as np
from oae.generators.base import (
    OaeGeneratorBase,
    oae_attenuation_db,
    oae_noise_offset_db,
    oae_variability_db,
)


class DpoaeGenerator(OaeGeneratorBase):
    """Síntesis DPOAE - DP-grama por punto + función I/O."""

    # Espectro que muestra el equipo alrededor del par primario.
    FFT_N = 4096
    SPEC_LOW_HZ = 500.0
    SPEC_HIGH_HZ = 10000.0
    # Ancho de los picos en el espectro: unos pocos bins (ventana FFT).
    PEAK_SIGMA_BINS = 2.5
    # Piso al que se recorta el espectro dibujado (dB SPL).
    SPEC_FLOOR_DB = -40.0

    def __init__(self, seed: int | None = None):
        super().__init__("dpoae", seed)
        self._rng = np.random.default_rng(self._seed)

    def _seed_from_params(self, ear: str = "OD", l1: float | None = None,
                          l2: float | None = None) -> int:
        return int(abs(hash(("dpoae", ear, l1 or 0, l2 or 0))) % (2**32))

    # ------------------------------------------------------------------
    # Normativa
    # ------------------------------------------------------------------
    def f2_list(self) -> np.ndarray:
        """Frecuencias f2 del barrido (media octava, 1-8 kHz por defecto).

        Antes el barrido era `arange(1000, 6000, 500)`: 11 puntos
        equiespaciados en Hz, que en un eje log se apelotonan arriba y
        no corresponden a ninguna serie clínica. Un DP-grama real se
        corre en pasos de media octava.
        """
        return np.array(self.normative["f2_list_hz"], dtype=float)

    def normal_band(self, f2_hz) -> tuple[np.ndarray, np.ndarray]:
        """(low, high) dB SPL del rango normal de nivel DP para cada f2.

        Interpolado en log-frecuencia sobre normative['normal_band_db'],
        para que el área verde siga existiendo si el curso configura otras
        f2 que las tabuladas.
        """
        pairs = sorted((float(k), v) for k, v in self.normative["normal_band_db"].items())
        ref = np.array([p[0] for p in pairs])
        low = np.array([float(p[1][0]) for p in pairs])
        high = np.array([float(p[1][1]) for p in pairs])
        lf = np.log2(np.atleast_1d(np.asarray(f2_hz, dtype=float)))
        lr = np.log2(ref)
        return np.interp(lf, lr, low), np.interp(lf, lr, high)

    def _noise_floor_db(self, f2_hz: float, case: dict | None = None) -> float:
        """Piso de ruido final esperado en ese f2.

        El ruido en el conducto es de baja frecuencia: el piso sube hacia
        los graves (por eso en un DP-grama real el punto de 1 kHz es el
        que más seguido queda tapado por ruido) y es plano en agudos.
        `case` puede subirlo parejo (paciente inquieto -- ver
        oae_noise_offset_db).
        """
        nf = float(self.normative["noise_floor_db_spl"])
        rise = float(self.normative["noise_floor_lf_rise_db_per_oct"])
        return (nf + rise * max(0.0, np.log2(2000.0 / f2_hz))
                + oae_noise_offset_db(case))

    def _clean_dp_db(self, f2_hz: float, l1_db: float, l2_db: float,
                     atten_db: float) -> float:
        """Nivel DP "limpio" (sin ruido) en ese f2 para ese par L1/L2.

        Pico en peak_f2_hz con caídas distintas hacia graves y agudos: el
        DP-grama normal es bastante plano entre 1 y 4 kHz y cae en 6-8 kHz.
        L2 mueve el nivel con crecimiento COMPRESIVO (la cóclea sana
        comprime: bajando L2 el DP cae casi 1 dB por dB, pero subiéndolo
        crece apenas ~0.25 dB/dB y satura) y L1 penaliza al alejarse del
        paradigma óptimo de Kummer (L1 = 0.4*L2 + 39). Con una pendiente
        única de 0.6 dB/dB la función I/O salía como una recta y a 30 dB
        SPL todavía había DP de sobra: nunca aparecía el umbral.
        """
        peak_f2 = float(self.normative["peak_f2_hz"])
        octaves = np.log2(f2_hz / peak_f2)
        rolloff = (self.normative["rolloff_high_db_per_oct"] if octaves > 0
                   else self.normative["rolloff_low_db_per_oct"])
        optimal_l1 = 0.4 * l2_db + 39
        l1_penalty = self.normative["l1_l2_penalty_db_per_db"] * abs(l1_db - optimal_l1)
        delta_l2 = l2_db - float(self.normative["default_l2_db_spl"])
        slope = (self.normative["growth_rate_db_per_db_l2"] if delta_l2 >= 0
                 else self.normative["growth_rate_low_db_per_db_l2"])
        level_gain = delta_l2 * float(slope)
        return (float(self.normative["peak_dp_db_spl"])
                - abs(octaves) * float(rolloff)
                + level_gain - l1_penalty - atten_db)

    # ------------------------------------------------------------------
    # Espectro FFT de un punto (lo que el equipo muestra mientras mide)
    # ------------------------------------------------------------------
    def _spectrum(self, f1: float, f2: float, fdp: float, l1_db: float,
                  l2_db: float, dp_db: float, nf_db: float, rng) -> tuple:
        """Espectro del canal en ese instante de la captura.

        Bins de ruido con distribución exponencial en potencia (chi2 de 2
        gl, como una FFT real), más los picos de los primarios f1/f2, el
        producto de distorsión 2f1-f2 y los DP de orden superior 2f2-f1 y
        3f1-2f2, que un equipo real también muestra.
        """
        freqs = np.fft.rfftfreq(self.FFT_N, 1 / self.SAMPLE_RATE)
        mask = (freqs >= self.SPEC_LOW_HZ) & (freqs <= self.SPEC_HIGH_HZ)
        freqs = freqs[mask]
        df = self.SAMPLE_RATE / self.FFT_N

        # Ruido: piso del punto, con la misma pendiente hacia graves.
        rise = float(self.normative["noise_floor_lf_rise_db_per_oct"])
        shape = nf_db + rise * np.clip(np.log2(2000.0 / freqs), 0, None)
        power = 10 ** (shape / 10) * rng.exponential(1.0, freqs.size)

        peaks = [
            (f1, l1_db),
            (f2, l2_db),
            (fdp, dp_db),
            (2 * f2 - f1, dp_db - 12),
            (3 * f1 - 2 * f2, dp_db - 10),
        ]
        sigma = self.PEAK_SIGMA_BINS * df
        for freq, level in peaks:
            if not (self.SPEC_LOW_HZ <= freq <= self.SPEC_HIGH_HZ):
                continue
            power += 10 ** (level / 10) * np.exp(-0.5 * ((freqs - freq) / sigma) ** 2)
        db = 10 * np.log10(np.maximum(power, 1e-12))
        return freqs, np.maximum(db, self.SPEC_FLOOR_DB)

    def _point_frames(self, f2: float, l1_db: float, l2_db: float,
                      clean_dp: float, nf_final: float, rng) -> list[dict]:
        """Promedios parciales de UN punto: k = 1, 2, 4 ... averages.

        Con pocos promedios el bin del DP está dominado por ruido y "lee"
        alto; al promediar el piso baja 10*log10(k) y el valor converge al
        DP real. Es exactamente lo que se ve en pantalla en un equipo:
        el punto baja y se estabiliza antes de quedar fijado.
        """
        ratio = float(self.normative["f2_f1_ratio"])
        f1 = f2 / ratio
        fdp = 2 * f1 - f2
        averages = [int(k) for k in self.normative["averages_per_point"]]
        k_max = max(averages)
        frames = []
        for k in averages:
            nf_k = nf_final + 10 * np.log10(k_max / k)
            # Lo que mide el equipo en el bin del DP: señal + ruido.
            measured = 10 * np.log10(10 ** (clean_dp / 10) + 10 ** (nf_k / 10))
            measured += rng.normal(0, 1.2 / np.sqrt(k))
            nf_read = nf_k + rng.normal(0, 1.0 / np.sqrt(k))
            spec_freqs, spec_db = self._spectrum(
                f1, f2, fdp, l1_db, l2_db, measured, nf_k, rng
            )
            frames.append({
                "n_avg": k,
                "dp_db": float(measured),
                "nf_db": float(nf_read),
                "snr_db": float(measured - nf_read),
                "spec_freqs": spec_freqs,
                "spec_db": spec_db,
            })
        return frames

    # ------------------------------------------------------------------
    # DP-grama
    # ------------------------------------------------------------------
    def generate(self, l1_db: float, l2_db: float, ear: str = "OD",
                 case: dict | None = None) -> dict:
        """Captura DP-grama completa, punto por punto.

        Devuelve {"points": [...], "f2_list", "dp_levels_db_spl",
        "noise_floors_db_spl", ...}: los arrays finales están para el
        resumen/tabla, pero el panel anima recorriendo points[i]["frames"].
        `case` (dict 'type'/'umbral' del caso clínico) atenúa el DP según
        patología -- ver oae_attenuation_db.
        """
        rng = np.random.default_rng(self._seed_from_params(ear, l1_db, l2_db))
        self._rng = rng
        ratio = float(self.normative["f2_f1_ratio"])
        min_snr = float(self.normative["min_dp_above_noise_db"])
        # Estructura fina del DP-grama: cuánto se aparta punto a punto de la
        # curva teórica. Configurable por caso (0 = curva de libro).
        var_db = oae_variability_db(case, 1.5)

        points = []
        for f2 in self.f2_list():
            # La atenuación se pide POR f2: además de la patología, el caso
            # puede traer un perfil por frecuencia (muesca en 4 kHz, caída
            # en agudos), que se aplana si se calcula una sola vez.
            clean = self._clean_dp_db(f2, l1_db, l2_db,
                                      oae_attenuation_db(case, f2))
            clean += rng.normal(0, var_db)
            nf_final = self._noise_floor_db(f2, case) + rng.normal(0, 1.5)
            frames = self._point_frames(f2, l1_db, l2_db, clean, nf_final, rng)
            final = frames[-1]
            points.append({
                "f2_hz": float(f2),
                "f1_hz": float(f2 / ratio),
                "fdp_hz": float(2 * (f2 / ratio) - f2),
                "dp_db": final["dp_db"],
                "nf_db": final["nf_db"],
                "snr_db": final["snr_db"],
                "passed": bool(final["snr_db"] >= min_snr),
                "frames": frames,
            })

        f2_arr = np.array([p["f2_hz"] for p in points])
        dp_arr = np.array([p["dp_db"] for p in points])
        nf_arr = np.array([p["nf_db"] for p in points])
        n_pass = int(sum(1 for p in points if p["passed"]))
        return {
            "points": points,
            "f2_list": f2_arr,
            "f1_list": f2_arr / ratio,
            "dp_levels_db_spl": dp_arr,
            "noise_floors_db_spl": nf_arr,
            "snr_db": dp_arr - nf_arr,
            "n_pass": n_pass,
            "n_total": len(points),
            "overall_pass": n_pass >= int(self.normative["pass_points_min"]),
            "l1_db": l1_db,
            "l2_db": l2_db,
        }

    # ------------------------------------------------------------------
    # Función I/O (crecimiento)
    # ------------------------------------------------------------------
    def generate_io(self, f2_hz: float | None = None, ear: str = "OD",
                    case: dict | None = None) -> dict:
        """DP vs L2 a f2 fijo, siguiendo L1 = 0.4*L2 + 39 en cada punto.

        Mismo formato de puntos que el DP-grama (con espectro por punto)
        para animarla en la misma corrida. Devuelve además "threshold_l2":
        el L2 más bajo que todavía deja SNR >= criterio, que es el umbral
        DP que se lee de la función de crecimiento.
        """
        f2 = float(f2_hz or self.normative["io_f2_hz"])
        rng = np.random.default_rng(self._seed_from_params(ear, f2, "io"))
        atten = oae_attenuation_db(case, f2)
        min_snr = float(self.normative["min_dp_above_noise_db"])

        l2_list = np.arange(
            self.normative["io_l2_min_db_spl"],
            self.normative["io_l2_max_db_spl"] + 1,
            self.normative["io_l2_step_db_spl"],
            dtype=float,
        )
        nf_final = self._noise_floor_db(f2, case) + rng.normal(0, 1.0)
        ratio = float(self.normative["f2_f1_ratio"])
        points = []
        for l2 in l2_list:
            l1 = 0.4 * l2 + 39
            clean = self._clean_dp_db(f2, l1, l2, atten) + rng.normal(0, 1.0)
            frames = self._point_frames(f2, l1, l2, clean, nf_final, rng)
            final = frames[-1]
            points.append({
                "l2_db": float(l2),
                "l1_db": float(l1),
                "f2_hz": f2,
                # El panel dibuja el mismo espectro para el DP-grama y la
                # I/O, así que cada punto lleva el par primario completo.
                "f1_hz": float(f2 / ratio),
                "fdp_hz": float(2 * (f2 / ratio) - f2),
                "dp_db": final["dp_db"],
                "nf_db": final["nf_db"],
                "snr_db": final["snr_db"],
                "passed": bool(final["snr_db"] >= min_snr),
                "frames": frames,
            })

        above = [p["l2_db"] for p in points if p["passed"]]
        return {
            "f2_hz": f2,
            "points": points,
            "l2_list": l2_list,
            "dp_levels_db_spl": np.array([p["dp_db"] for p in points]),
            "noise_floors_db_spl": np.array([p["nf_db"] for p in points]),
            "threshold_l2": float(min(above)) if above else None,
        }
