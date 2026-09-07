"""Generador sintético SFOAE (Stimulus Frequency Otoacoustic Emissions).

Tono probe + barrido de supresor. Magnitud SFOAE cae cuando el supresor
se acerca a la frecuencia/nivel del probe. Devuelve magnitude + phase vs
nivel supresor para graficar curva de supresión o polar (si quisiéramos
mostrar I/Q en plano complejo).
"""
import numpy as np
from oae.generators.base import (
    OaeGeneratorBase,
    case_fingerprint,
    oae_attenuation_db,
    oae_noise_offset_db,
    oae_variability_db,
    stable_seed,
)


class SfoaeGenerator(OaeGeneratorBase):
    """Síntesis SFOAE - barrido de supresor."""

    # Promedios parciales de cada punto medido. Un equipo SFOAE real mide
    # nivel de supresor por nivel de supresor, promediando: el valor arranca
    # ruidoso y converge. Sin esto el panel pintaba la curva entera de golpe
    # y la prueba parecía un dibujo estático al lado de TEOAE/DPOAE.
    AVERAGES_PER_POINT = [1, 2, 4, 8, 16]

    def __init__(self, seed: int | None = None):
        super().__init__("sfoae", seed)
        self._rng = np.random.default_rng(self._seed)

    def _seed_from_params(self, ear: str = "OD", freq: float | None = None,
                          level: float | None = None,
                          case: dict | None = None) -> int:
        """Seed de la corrida: oído + probe + PERFIL DEL CASO.

        stable_seed y no hash(): hash() saltea por proceso, así que la
        curva de supresión del mismo paciente cambiaba entre aperturas
        de LabSim. El caso entra al seed para que el ruido de la curva sea
        propio de ese paciente y no un trazo compartido. Ver base.py.
        """
        return stable_seed("sfoae", ear, freq or 0, level or 0,
                           case_fingerprint(case))

    def _noise_floor_db(self, case: dict | None) -> float:
        """Piso de ruido del registro (dB), subido por el ruido del paciente.

        Sin piso el veredicto se tomaba contra un umbral fijo de 0 dB y la
        magnitud venía recortada a >= 0: cualquier oído daba PRESENTE, por
        muerta que estuviera la cóclea. Ahora la SFOAE se lee como las
        otras pruebas -- magnitud contra piso, criterio de SNR.
        """
        return float(self.normative["noise_floor_db"]) + oae_noise_offset_db(case)

    def _base_magnitude_db(self, freq_hz: float) -> float:
        """Interpola la magnitud SFOAE esperada en `freq_hz` sobre la curva
        normativa por frecuencia (análoga a expected_response_db de TEOAE):
        la SFOAE es más robusta en medios (1-1.5 kHz) y cae en los extremos."""
        ref_freqs = self.normative["reference_freqs_hz"]
        expected = self.normative["expected_magnitude_db"]
        mags = [expected.get(str(f), 3.0) for f in ref_freqs]
        # Interpolación en escala log de frecuencia (así se comporta el oído)
        return float(np.interp(np.log2(freq_hz), np.log2(ref_freqs), mags))

    def _point_frames(self, magnitude_db: float, phase_deg: float,
                      rng) -> list[dict]:
        """Promedios parciales de UN punto: k = 1, 2, 4 ... promedios.

        El error de medición cae con 1/sqrt(k), así que el punto entra
        disperso y se va asentando sobre su valor final. El último frame ES
        el valor definitivo (no una realización más) para que lo animado y
        lo que queda fijado en la curva coincidan.
        """
        ks = [int(k) for k in self.normative.get("averages_per_point",
                                                 self.AVERAGES_PER_POINT)]
        frames = []
        for k in ks:
            frames.append({
                "n_avg": k,
                "magnitude_db": float(magnitude_db + rng.normal(0, 2.5 / np.sqrt(k))),
                "phase_deg": float(phase_deg + rng.normal(0, 25.0 / np.sqrt(k))),
            })
        frames[-1] = {"n_avg": ks[-1], "magnitude_db": float(magnitude_db),
                      "phase_deg": float(phase_deg)}
        return frames

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
        self._rng = np.random.default_rng(
            self._seed_from_params(ear, freq_hz, level_db, case))

        smin = suppressor_min if suppressor_min is not None else self.normative["suppressor_min_db_spl"]
        smax = suppressor_max if suppressor_max is not None else self.normative["suppressor_max_db_spl"]
        sstep = suppressor_step if suppressor_step is not None else self.normative["suppressor_step_db_spl"]
        suppressor_levels = np.arange(smin, smax + 0.1, sstep)

        # Sin recorte a 0: una cóclea dañada tiene que poder caer BAJO el
        # piso de ruido, que es lo que hace la prueba interpretable.
        base_magnitude = self._base_magnitude_db(freq_hz) - oae_attenuation_db(case, freq_hz)
        noise_db = self._noise_floor_db(case)
        # Estructura fina del oído: mismo parámetro del caso que usan las
        # otras pruebas, para que un oído "de libro" y uno real se vean
        # distintos también acá.
        sigma = 0.3 + 0.25 * oae_variability_db(case, 2.5)
        offset = self.normative["suppression_offset_db"]
        slope = self.normative["suppression_slope_db"]
        phase_slope = self.normative["phase_slope_db"]
        criterion = level_db + offset

        # Sigmoide monótona decreciente sobre la AMPLITUD (lineal), no
        # sobre los dB: dividir los dB por la sigmoide invierte el efecto
        # cuando la magnitud base es negativa (un oído dañado "mejoraba"
        # al subir el supresor y la prueba salía PRESENTE siempre).
        suppression = 1.0 / (1 + np.exp((suppressor_levels - criterion) / slope))
        magnitude = base_magnitude + 20 * np.log10(np.maximum(suppression, 1e-3))
        magnitude = magnitude + self._rng.normal(0, sigma, size=suppressor_levels.shape)
        # Bajo el piso de ruido lo que se registra es ruido, no una emisión
        # cada vez más chica: se aplana ahí, como en las otras pruebas.
        magnitude = np.maximum(magnitude, noise_db - 6.0)
        # Phase: 0° sin supresión efectiva, ~180° cuando ya está suprimida
        phase = 180 / (1 + np.exp(-(suppressor_levels - criterion) / phase_slope))
        phase = phase + self._rng.normal(0, 3, size=suppressor_levels.shape)

        # Los frames se sortean DESPUES de las curvas finales: el rng ya
        # consumió lo mismo que antes, así que magnitude/phase no cambian
        # (mismos seeds golden de tests/test_oae_seeds.py).
        points = [
            {
                "suppressor_db": float(s_db),
                "magnitude_db": float(mag),
                "phase_deg": float(ph),
                "frames": self._point_frames(mag, ph, self._rng),
            }
            for s_db, mag, ph in zip(suppressor_levels, magnitude, phase)
        ]

        return {
            "freq_hz": freq_hz,
            "level_db_spl": level_db,
            "suppressor_levels": suppressor_levels,
            "magnitude_db": magnitude,
            "phase_deg": phase,
            "base_magnitude_db": base_magnitude,
            "noise_floor_db": noise_db,
            "min_snr_db": float(self.normative["min_snr_db"]),
            "points": points,
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
        self._rng = np.random.default_rng(self._seed_from_params(ear, fmin, fmax, case))
        # Atenuación por frecuencia: la curva de sintonía es justamente
        # donde se tiene que ver la muesca del perfil del caso, así que se
        # evalúa punto a punto y no con un único valor global.
        magnitudes = np.array([self._base_magnitude_db(f) - oae_attenuation_db(case, f)
                               for f in freqs])
        noise_db = self._noise_floor_db(case)
        magnitudes = magnitudes + self._rng.normal(
            0, 0.2 + 0.15 * oae_variability_db(case, 2.5), size=freqs.shape)
        magnitudes = np.maximum(magnitudes, noise_db - 6.0)
        points = [
            {
                "freq_hz": float(f),
                "magnitude_db": float(mag),
                "frames": self._point_frames(mag, 0.0, self._rng),
            }
            for f, mag in zip(freqs, magnitudes)
        ]
        return {"freqs": freqs, "magnitude_db": magnitudes, "points": points,
                "noise_floor_db": noise_db,
                "min_snr_db": float(self.normative["min_snr_db"])}
