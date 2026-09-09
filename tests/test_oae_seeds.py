"""
Semilla de los generadores OAE (TEOAE / DPOAE / SFOAE / SOAE).

Dos propiedades que se rompieron una vez y no se ven a simple vista:

1. El seed NO puede salir de hash(): Python lo saltea con PYTHONHASHSEED,
   distinto en cada proceso, así que el mismo paciente daba otra captura en
   cada apertura de LabSim (y en SOAE cambiaba directamente si el oído
   tenía emisiones o no). Se usa stable_seed() -- blake2b, ver
   src/oae/generators/base.py.

2. El perfil del caso entra al seed. Sin eso, dos pacientes distintos con
   el mismo nivel/promedios compartían el ruido bit a bit: el trazo A-B de
   TEOAE era idéntico y el DP-grama tenía la misma silueta apenas corrida
   en vertical (o sea, variabilidad_db no distinguía un oído de otro).

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))


def _caso(**kw):
    """Perfil EOA de un oído con el shape que guarda el backend."""
    base = {
        "type": "normal", "umbral": 20, "atten_db": 0.0, "ruido_db": 0.0,
        "sello_pct": 85, "variabilidad_db": 2.5, "soae_mode": "auto",
        "desviaciones": {str(h): 0.0 for h in
                         (500, 1000, 1500, 2000, 3000, 4000, 6000, 8000)},
    }
    base.update(kw)
    return base


def test_stable_seed_goldens():
    """Valores fijos: fallan si alguien vuelve a hash() o cambia el hash."""
    from oae.generators.base import stable_seed, case_fingerprint
    from oae.generators.teoae import TeoaeGenerator
    from oae.generators.dpoae import DpoaeGenerator
    from oae.generators.sfoae import SfoaeGenerator

    assert stable_seed("soae", "OD", "type=normal", 30.0) == 4222648189
    assert case_fingerprint(None) == ""
    esperados = [
        (TeoaeGenerator, ("OD", 60.0, 260), 173268071),
        (DpoaeGenerator, ("OD", 65.0, 55.0), 3391123732),
        (SfoaeGenerator, ("OD", 1000.0, 40.0), 684235549),
    ]
    for cls, args, seed in esperados:
        assert cls()._seed_from_params(*args) == seed, cls.__name__


def test_case_changes_the_noise_realization():
    """Dos pacientes distintos no comparten el ruido ni la estructura fina."""
    from oae.generators.teoae import TeoaeGenerator
    from oae.generators.dpoae import DpoaeGenerator
    from oae.generators.sfoae import SfoaeGenerator

    a, b = _caso(), _caso(umbral=10, sello_pct=95)

    t = TeoaeGenerator()
    fa = t.generate(level_db=60, n_sweeps=260, ear="OD", case=a, n_frames=4)["frames"][-1]
    fb = t.generate(level_db=60, n_sweeps=260, ear="OD", case=b, n_frames=4)["frames"][-1]
    # A-B es ruido residual puro: entre pacientes tiene que descorrelacionar.
    ruido_a = fa["wave_a"] - fa["wave_b"]
    ruido_b = fb["wave_a"] - fb["wave_b"]
    corr = float(np.corrcoef(ruido_a, ruido_b)[0, 1])
    assert abs(corr) < 0.3, f"el ruido TEOAE sigue compartido (corr {corr:.2f})"

    dp = DpoaeGenerator()
    da = dp.generate(l1_db=65, l2_db=55, ear="OD", case=a)
    db = dp.generate(l1_db=65, l2_db=55, ear="OD", case=b)
    assert not np.allclose(da["noise_floors_db_spl"], db["noise_floors_db_spl"])

    sf = SfoaeGenerator()
    assert not np.allclose(
        sf.generate(freq_hz=1000, level_db=40, ear="OD", case=a)["magnitude_db"],
        sf.generate(freq_hz=1000, level_db=40, ear="OD", case=b)["magnitude_db"])


def test_same_case_repeats_identically():
    """Volver a medir al mismo paciente da la misma captura (no es azar)."""
    from oae.generators.teoae import TeoaeGenerator
    from oae.generators.dpoae import DpoaeGenerator
    from oae.generators.sfoae import SfoaeGenerator
    from oae.generators.soae import SoaeGenerator

    caso = _caso()
    t = TeoaeGenerator()
    assert np.allclose(
        t.generate(level_db=60, n_sweeps=260, ear="OD", case=caso, n_frames=4)["frames"][-1]["waveform"],
        t.generate(level_db=60, n_sweeps=260, ear="OD", case=caso, n_frames=4)["frames"][-1]["waveform"])
    dp = DpoaeGenerator()
    assert np.allclose(dp.generate(l1_db=65, l2_db=55, ear="OD", case=caso)["dp_levels_db_spl"],
                       dp.generate(l1_db=65, l2_db=55, ear="OD", case=caso)["dp_levels_db_spl"])
    sf = SfoaeGenerator()
    assert np.allclose(sf.generate(freq_hz=1000, level_db=40, ear="OD", case=caso)["magnitude_db"],
                       sf.generate(freq_hz=1000, level_db=40, ear="OD", case=caso)["magnitude_db"])
    so = SoaeGenerator()
    assert np.allclose(so.generate(ear="OD", case=caso)["frames"][-1]["spec_db"],
                       so.generate(ear="OD", case=caso)["frames"][-1]["spec_db"])


def test_ears_differ_within_the_same_case():
    """OD y OI del mismo caso no pueden salir calcados."""
    from oae.generators.dpoae import DpoaeGenerator
    dp = DpoaeGenerator()
    caso = _caso()
    assert not np.allclose(dp.generate(l1_db=65, l2_db=55, ear="OD", case=caso)["dp_levels_db_spl"],
                           dp.generate(l1_db=65, l2_db=55, ear="OI", case=caso)["dp_levels_db_spl"])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
