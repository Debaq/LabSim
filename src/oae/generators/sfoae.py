"""Generador sintético SFOAE (Stimulus Frequency Otoacoustic Emissions).

Tono probe + barrido de supresor. Magnitud SFOAE cae cuando el supresor
se acerca a la frecuencia/nivel del probe. Devuelve magnitude + phase vs
nivel supresor para graficar curva de supresión o polar (si quisiéramos
mostrar I/Q en plano complejo).
"""
import numpy as np
from oae.generators.base import OaeGeneratorBase, oae_attenuation_db


class SfoaeGenerator(OaeGeneratorBase):
    """Síntesis SFOAE - barrido de supresor."""

    def __init__(self, seed: int | None = None):
        super().__init__("sfoae", seed)
        self._rng = np.random.default_rng(self._seed)

    def _seed_from_params(self, ear: str = "OD", freq: float | None = None,
                          level: float | None = None) -> int:
        return int(abs(hash(("sfoae", ear, freq or 0, level or 0))) % (2**32))

    def _base_magnitude_db(self, freq_hz: float) -> float:
        """Interpola la magnitud SFOAE esperada en `freq_hz` sobre la curva
        normativa por frecuencia (análoga a expected_response_db de TEOAE):
        la SFOAE es más robusta en medios (1-1.5 kHz) y cae en los extremos."""
        ref_freqs = self.normative["reference_freqs_hz"]
        expected = self.normative["expected_magnitude_db"]
        mags = [expected.get(str(f), 3.0) for f in ref_freqs]
        # Interpolación en escala log de frecuencia (así se comporta el oído)
        return float(np.interp(np.log2(freq_hz), np.log2(ref_freqs), mags))

    def generate(self, freq_hz: float, level_db: float,
                 suppressor_min: float | None = None,
                 suppressor_max: float | None = None,
                 suppressor_step: float | None = None,
                 ear: str = "OD", case: dict | None = None) -> dict:
        """Devuelve dict con suppressor_levels, magnitude_db, phase_deg.

        Modelo: magnitud SFOAE en ausencia de supresor = curva normativa
        por frecuencia (`freq_hz` ahora sí determina el resultado, antes
        solo entraba al seed). A medida que sube el nivel del supresor la
        magnitud cae monótonamente (sigmoide) y la fase rota hacia 180°;
        el punto de supresión media escala con `level_db` (a mayor nivel
        de probe, se necesita más supresor para taparlo -- igual que en
        un equipo real). `case` atenúa la magnitud base según patología.
        """
        self._rng = np.random.default_rng(self._seed_from_params(ear, freq_hz, level_db))

        smin = suppressor_min if suppressor_min is not None else self.normative["suppressor_min_db_spl"]
        smax = suppressor_max if suppressor_max is not None else self.normative["suppressor_max_db_spl"]
        sstep = suppressor_step if suppressor_step is not None else self.normative["suppressor_step_db_spl"]
        suppressor_levels = np.arange(smin, smax + 0.1, sstep)

        base_magnitude = self._base_magnitude_db(freq_hz) - oae_attenuation_db(case)
        base_magnitude = max(0.0, base_magnitude)
        offset = self.normative["suppression_offset_db"]
        slope = self.normative["suppression_slope_db"]
        phase_slope = self.normative["phase_slope_db"]
        criterion = level_db + offset

        # Sigmoide monótona decreciente: magnitud máxima con poco
        # supresor, cae a medida que el supresor se acerca/supera `criterion`.
        magnitude = base_magnitude / (1 + np.exp((suppressor_levels - criterion) / slope))
        magnitude = magnitude + self._rng.normal(0, 0.3, size=suppressor_levels.shape)
        # Phase: 0° sin supresión efectiva, ~180° cuando ya está suprimida
        phase = 180 / (1 + np.exp(-(suppressor_levels - criterion) / phase_slope))
        phase = phase + self._rng.normal(0, 3, size=suppressor_levels.shape)

        return {
            "freq_hz": freq_hz,
            "level_db_spl": level_db,
            "suppressor_levels": suppressor_levels,
            "magnitude_db": magnitude,
            "phase_deg": phase,
            "base_magnitude_db": base_magnitude,
        }

    def tuning_curve(self, ear: str = "OD", case: dict | None = None,
                      freq_min_hz: float | None = None,
                      freq_max_hz: float | None = None,
                      n_points: int = 24) -> dict:
        """Curva de sintonía: magnitud SFOAE esperada (sin supresor) en
        función de la frecuencia probe, sobre el rango normativo. Muestra
        de un vistazo dónde el oído responde mejor/peor -- lo que la
        vista de un único freq_hz + barrido de supresor no deja ver."""
        ref_freqs = self.normative["reference_freqs_hz"]
        fmin = freq_min_hz or ref_freqs[0]
        fmax = freq_max_hz or ref_freqs[-1]
        freqs = np.geomspace(fmin, fmax, n_points)
        self._rng = np.random.default_rng(self._seed_from_params(ear, fmin, fmax))
        atten = oae_attenuation_db(case)
        magnitudes = np.array([self._base_magnitude_db(f) for f in freqs]) - atten
        magnitudes = np.clip(magnitudes, 0.0, None) + self._rng.normal(0, 0.2, size=freqs.shape)
        return {"freqs": freqs, "magnitude_db": magnitudes}
