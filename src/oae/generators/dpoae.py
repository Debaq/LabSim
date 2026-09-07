"""Generador sintético DPOAE (Distortion Product Otoacoustic Emissions).

Para cada f2 en el rango, computa f1 = f2/ratio y la frecuencia DP
2f1-f2. Genera DP-gram con pico ~3 kHz y caída característica ~24 dB/oct
fuera del pico, cuyo nivel efectivo depende de L1/L2 (growth function +
paradigma óptimo de Kummer) y de la patología del caso. Devuelve curva DP
+ noise floor por punto para el DP-gram (f2 vs nivel) y, con
`generate_io`, la función de crecimiento (L2 vs DP) a f2 fijo.
"""
import numpy as np
from oae.generators.base import OaeGeneratorBase, oae_attenuation_db


class DpoaeGenerator(OaeGeneratorBase):
    """Síntesis DPOAE - barrido de f2 + DP-gram."""

    def __init__(self, seed: int | None = None):
        super().__init__("dpoae", seed)
        self._rng = np.random.default_rng(self._seed)

    def _seed_from_params(self, ear: str = "OD", l1: float | None = None,
                          l2: float | None = None) -> int:
        return int(abs(hash(("dpoae", ear, l1 or 0, l2 or 0))) % (2**32))

    def generate(self, l1_db: float, l2_db: float, ear: str = "OD",
                 case: dict | None = None) -> dict:
        """Devuelve dict con f2_list, dp_levels_db_spl, noise_floors_db_spl.

        DP-gram sintético: pico en peak_f2_hz, cae rolloff_db_per_oct por
        octava fuera del pico. L2 mueve el nivel del DP (growth function
        simplificada: +growth_rate_db_per_db_l2 dB de DP por dB de L2 sobre
        el default). L1 penaliza si se aleja del paradigma óptimo L1/L2 de
        Kummer (L1 = 0.4*L2 + 39) -- alejarse de esa relación atenúa el DP,
        igual que en un equipo real. `case` (dict con 'type'/'umbral' del
        caso clínico) atenúa el pico según patología -- ver
        oae_attenuation_db.
        """
        self._rng = np.random.default_rng(self._seed_from_params(ear, l1_db, l2_db))

        f2_min = self.normative["f2_min_hz"]
        f2_max = self.normative["f2_max_hz"]
        f2_step = self.normative["f2_step_hz"]
        f2_list = np.arange(f2_min, f2_max + 1, f2_step)

        peak_f2 = self.normative["peak_f2_hz"]
        peak_db = self.normative["peak_dp_db_spl"]
        rolloff = self.normative["rolloff_db_per_oct"]
        nf_db = self.normative["noise_floor_db_spl"]
        growth_rate = self.normative["growth_rate_db_per_db_l2"]
        l1_penalty_rate = self.normative["l1_l2_penalty_db_per_db"]
        default_l2 = self.normative["default_l2_db_spl"]

        optimal_l1 = 0.4 * l2_db + 39
        l1_penalty = l1_penalty_rate * abs(l1_db - optimal_l1)
        level_gain = (l2_db - default_l2) * growth_rate
        atten = oae_attenuation_db(case)
        effective_peak_db = peak_db + level_gain - l1_penalty - atten

        dp_levels = []
        noise_floors = []
        for f2 in f2_list:
            # Caída en octavas desde el pico (signed: ambos lados del peak)
            octaves_from_peak = np.log2(f2 / peak_f2)
            base = effective_peak_db - abs(octaves_from_peak) * rolloff
            # Pequeña variación biológica
            level = base + self._rng.normal(0, 1.5)
            # Noise floor varía por frecuencia también
            noise = nf_db + self._rng.normal(0, 1.0) + abs(octaves_from_peak) * 2
            dp_levels.append(level)
            noise_floors.append(noise)

        return {
            "f2_list": f2_list,
            "dp_levels_db_spl": np.array(dp_levels),
            "noise_floors_db_spl": np.array(noise_floors),
            "l1_db": l1_db,
            "l2_db": l2_db,
            "f1_list": f2_list / self.normative["f2_f1_ratio"],
        }

    def generate_io(self, f2_hz: float | None = None, ear: str = "OD",
                     case: dict | None = None) -> dict:
        """Función I/O (crecimiento): DP y noise floor vs L2, a f2 fijo,
        siguiendo el paradigma L1=0.4*L2+39 en cada punto (el que usaría
        un equipo real al correr una función de crecimiento)."""
        f2 = f2_hz or self.normative["io_f2_hz"]
        self._rng = np.random.default_rng(self._seed_from_params(ear, f2, "io"))

        l2_min = self.normative["io_l2_min_db_spl"]
        l2_max = self.normative["io_l2_max_db_spl"]
        l2_step = self.normative["io_l2_step_db_spl"]
        l2_list = np.arange(l2_min, l2_max + 1, l2_step)

        peak_f2 = self.normative["peak_f2_hz"]
        peak_db = self.normative["peak_dp_db_spl"]
        rolloff = self.normative["rolloff_db_per_oct"]
        nf_db = self.normative["noise_floor_db_spl"]
        growth_rate = self.normative["growth_rate_db_per_db_l2"]
        default_l2 = self.normative["default_l2_db_spl"]
        atten = oae_attenuation_db(case)
        octaves_from_peak = np.log2(f2 / peak_f2)

        dp_levels = []
        noise_floors = []
        for l2 in l2_list:
            level_gain = (l2 - default_l2) * growth_rate
            base = peak_db + level_gain - abs(octaves_from_peak) * rolloff - atten
            level = base + self._rng.normal(0, 1.2)
            noise = nf_db + self._rng.normal(0, 1.0)
            dp_levels.append(level)
            noise_floors.append(noise)

        return {
            "f2_hz": f2,
            "l2_list": l2_list,
            "dp_levels_db_spl": np.array(dp_levels),
            "noise_floors_db_spl": np.array(noise_floors),
        }
