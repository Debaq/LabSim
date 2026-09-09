"""
Generador VEMP: lo que se rompió y no se ve mirando una curva.

1. La MORFOLOGÍA ES BIFÁSICA. El generador sumaba dos gaussianas positivas
   y dibujaba dos jorobas del mismo lado; la vista previa del backend, que
   sí toma la polaridad de la inicial del pico, mostraba otra cosa.
2. La AMPLITUD NO EXTRAPOLA. La fórmula vieja normalizaba por (80-umbral):
   con umbral 85 a 100 dB devolvía 1930 µV, catorce veces la normativa.
3. El CASO SE LEE CON EL SHAPE NUEVO (cases.data['VEMP'][lado]['subtipos'])
   y los casos viejos (un solo subtipo en la raíz del oído) siguen abriendo.
4. Sin CONTRACCIÓN no hay respuesta: la amplitud escala con el EMG del
   músculo registrador.
5. get_baseline_values no puede MUTAR la normativa en memoria (el boost por
   sexo multiplicaba el dict del JSON y crecía en cada llamada).

Sin scipy en el sandbox: se stubbea con filtros pasa-todo, así que lo que
se prueba es el modelo (latencias, amplitudes, polaridad), no el filtrado.
Si scipy está instalado se usa el de verdad.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import json
import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
REPO = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
os.chdir(REPO)


def stub_scipy():
    """scipy.signal con filtros pasa-todo, solo si no está el real."""
    try:
        import scipy.signal  # noqa: F401
        return
    except ImportError:
        pass
    import numpy as np
    fake = types.ModuleType("scipy.signal")
    fake.butter = lambda *a, **k: (np.array([1.0]), np.array([1.0]))
    fake.filtfilt = lambda b, a, x, **k: np.asarray(x)
    scipy = types.ModuleType("scipy")
    scipy.signal = fake
    sys.modules.setdefault("scipy", scipy)
    sys.modules["scipy.signal"] = fake


stub_scipy()

SUBTIPOS = ("CVEMP", "OVEMP", "MVEMP")
PEAKS = {"CVEMP": ["p13", "n23"], "OVEMP": ["n10", "p16"], "MVEMP": ["p13", "n23"]}


def _caso_nuevo(umbral=60, tipo="normal"):
    """Un oído con el shape que guarda CaseForm::parseVemp."""
    return {"type": tipo, "subtipos": {
        s: {"peaks": PEAKS[s], "umbral": umbral, "repro": True, "repro_var": 0.2,
            "average_objetivo": 200,
            "desviaciones": {p: {"lat": 0, "amp": 0} for p in PEAKS[s]}}
        for s in SUBTIPOS}}


def _caso_viejo():
    """Un oído guardado antes de que fueran tres subtipos."""
    return {"type": "sacular", "subtipo": "CVEMP", "umbral": 85, "repro": True,
            "repro_var": 0.2, "average_objetivo": 300,
            "desviaciones": {"p13": {"lat": 0.5, "amp": 0},
                             "n23": {"lat": 0, "amp": 0}}}


def _curva(case, subtipo, intensidad, maniobra, average=200, patient=None):
    from vemp.VEMP_generator_v1 import VEMP_Curve
    control = {"subtipo": subtipo, "maniobra": maniobra, "freq": "500Hz",
               "pol": "Rarefacción", "rate": 5.1, "average": average,
               "filter_down": 1500, "filter_passhigh": 10}
    x, y, _dx, _dy, _repro, meta = VEMP_Curve(
        intensidad, control, case, 0, [1.0, average], done=True, patient=patient)
    return x, y, meta


def test_normative_data_structure():
    """El JSON normativo tiene la estructura esperada por VEMP_generator_v1."""
    with open(os.path.join("resources", "vemp", "normative_data.json")) as f:
        n = json.load(f)
    assert "populations" in n
    assert "pathology_modifiers" in n
    for pop in ["adult_male", "adult_female"]:
        assert pop in n["populations"], f"falta población {pop}"
        air = n["populations"][pop]["air_conduction"]["tone_burst"]
        assert "500Hz" in air, f"falta 500Hz en {pop}"
        for sub in SUBTIPOS:
            assert sub in air["500Hz"], f"falta {sub} en {pop}/500Hz"
    for patho in ["normal", "sacular", "utricular", "neural"]:
        assert patho in n["pathology_modifiers"], f"falta pathology {patho}"


def test_vemp_generator_imports():
    from vemp.VEMP_generator_v1 import (SUBTIPO_PEAKS, VEMP_Curve,  # noqa: F401
                                        VEMPGeneratorV1, WAVE_SIGMA)
    assert SUBTIPO_PEAKS == PEAKS
    assert set(WAVE_SIGMA.keys()) == {"p13", "n23", "n10", "p16"}


def test_baseline_values_returns_peaks():
    from vemp.VEMP_generator_v1 import VEMPGeneratorV1
    gen = VEMPGeneratorV1()
    for sub, picos in [("CVEMP", ["p13", "n23"]), ("OVEMP", ["n10", "p16"])]:
        baseline = gen.get_baseline_values("adult_female", sub)
        for pico in picos:
            assert pico in baseline, f"{sub} sin pico {pico}"
            assert baseline[pico]["lat"] > 0
            assert baseline[pico]["amp"] > 0


def test_baseline_no_muta_la_normativa():
    """El boost por sexo multiplicaba el dict del JSON en memoria: cada
    llamada devolvía amplitudes un 10% más altas que la anterior."""
    from vemp.VEMP_generator_v1 import VEMPGeneratorV1
    gen = VEMPGeneratorV1()
    primera = gen.get_baseline_values("adult_female", "CVEMP")["p13"]["amp"]
    for _ in range(5):
        gen.get_baseline_values("adult_female", "CVEMP")
    assert gen.get_baseline_values("adult_female", "CVEMP")["p13"]["amp"] == primera


def test_fallback_population():
    from vemp.VEMP_generator_v1 import VEMPGeneratorV1
    assert "p13" in VEMPGeneratorV1().get_baseline_values("alien_pop", "CVEMP")


def test_select_population():
    """Mismo criterio que la vista previa del backend (public/js/case/vemp.js)."""
    from vemp.VEMP_generator_v1 import select_population
    assert select_population(9) == "child"
    assert select_population(30, 0) == "adult_male"
    assert select_population(30, 1) == "adult_female"
    assert select_population(70) == "elderly"
    assert select_population(None) == "adult_female"


def test_case_for_subtipo_shape_nuevo():
    from vemp.VEMP_generator_v1 import case_for_subtipo
    case = case_for_subtipo(_caso_nuevo(umbral=72, tipo="neural"), "OVEMP")
    assert case["type"] == "neural"          # la patología es del OÍDO
    assert case["umbral"] == 72
    assert case["peaks"] == ["n10", "p16"]
    assert set(case["desviaciones"]) == {"n10", "p16"}


def test_case_for_subtipo_caso_viejo():
    """Los valores de la raíz se los queda el subtipo que el caso declaraba;
    los otros dos arrancan en su default (criterio de
    CaseBuilder::caseDataToForm)."""
    from vemp.VEMP_generator_v1 import case_for_subtipo
    viejo = case_for_subtipo(_caso_viejo(), "CVEMP")
    assert viejo["umbral"] == 85
    assert viejo["average_objetivo"] == 300
    assert viejo["desviaciones"]["p13"]["lat"] == 0.5
    otro = case_for_subtipo(_caso_viejo(), "OVEMP")
    assert otro["type"] == "sacular"     # la patología sí es del oído
    assert otro["umbral"] == 65          # default del oVEMP, no el 85 del cVEMP


def test_case_for_subtipo_sin_datos():
    """Sin VEMP configurado no hay caso -- el módulo no genera nada."""
    from vemp.VEMP_generator_v1 import case_for_subtipo
    assert case_for_subtipo(None, "CVEMP") is None
    assert case_for_subtipo({}, "CVEMP") is None


def test_morfologia_bifasica():
    """P13 arriba y N23 abajo, en ese orden. Antes eran dos jorobas
    positivas y la previa del backend mostraba otra cosa."""
    from vemp.VEMP_generator_v1 import case_for_subtipo
    case = case_for_subtipo(_caso_nuevo(), "CVEMP")
    x, y, _ = _curva(case, "CVEMP", 100, "Rotación cefálica", average=500)
    assert y.max() > 0 and y.min() < 0
    assert x[y.argmax()] < x[y.argmin()]          # el positivo llega primero
    assert 10 < x[y.argmax()] < 17                # P13
    assert 19 < x[y.argmin()] < 27                # N23


def test_amplitud_no_extrapola_sobre_el_umbral():
    """Umbral 85 a 110 dB no puede dar catorce veces la amplitud normativa."""
    from vemp.VEMP_generator_v1 import VEMPGeneratorV1, case_for_subtipo
    gen = VEMPGeneratorV1()
    normativa = gen.get_baseline_values("adult_female", "CVEMP")
    techo = abs(normativa["p13"]["amp"]) + abs(normativa["n23"]["amp"])
    case = case_for_subtipo(_caso_nuevo(umbral=85), "CVEMP")
    _x, y, _ = _curva(case, "CVEMP", 110, "Rotación cefálica", average=500)
    assert (y.max() - y.min()) < techo * 1.5


def test_amplitud_crece_con_la_intensidad():
    from vemp.VEMP_generator_v1 import case_for_subtipo
    case = case_for_subtipo(_caso_nuevo(umbral=70), "CVEMP")
    p2p = {}
    for db in (90, 70, 50):
        _x, y, _ = _curva(case, "CVEMP", db, "Rotación cefálica", average=500)
        p2p[db] = y.max() - y.min()
    assert p2p[90] > p2p[70] > p2p[50]


def test_sin_contraccion_no_hay_respuesta():
    """El error clásico: cVEMP registrado con el paciente relajado."""
    from vemp.VEMP_generator_v1 import case_for_subtipo
    case = case_for_subtipo(_caso_nuevo(), "CVEMP")
    _x, relajado, meta_r = _curva(case, "CVEMP", 100, "Relajado (decúbito)",
                                  average=500)
    _x, contraido, meta_c = _curva(case, "CVEMP", 100, "Rotación cefálica",
                                   average=500)
    assert not meta_r["emg_ok"] and meta_c["emg_ok"]
    assert (relajado.max() - relajado.min()) < (contraido.max() - contraido.min()) / 3


def test_escala_del_ovemp():
    """El oVEMP vive en otro orden de magnitud (µV de un dígito): el ruido
    del generador es proporcional a la respuesta, no absoluto."""
    from vemp.VEMP_generator_v1 import case_for_subtipo
    cvemp = case_for_subtipo(_caso_nuevo(), "CVEMP")
    ovemp = case_for_subtipo(_caso_nuevo(umbral=65), "OVEMP")
    _x, yc, _ = _curva(cvemp, "CVEMP", 100, "Rotación cefálica", average=500)
    _x, yo, _ = _curva(ovemp, "OVEMP", 100, "Mirada superior ~30°", average=500)
    assert (yc.max() - yc.min()) > 5 * (yo.max() - yo.min())
    assert 5 < (yo.max() - yo.min()) < 60


def test_patologia_cruza_con_el_subtipo():
    """Sacular pega en el cVEMP y deja el oVEMP como está."""
    from vemp.VEMP_generator_v1 import case_for_subtipo
    sano = case_for_subtipo(_caso_nuevo(), "CVEMP")
    sacular = case_for_subtipo(_caso_nuevo(tipo="sacular"), "CVEMP")
    ocular_sano = case_for_subtipo(_caso_nuevo(umbral=65), "OVEMP")
    ocular_sac = case_for_subtipo(_caso_nuevo(umbral=65, tipo="sacular"), "OVEMP")
    _x, y_sano, _ = _curva(sano, "CVEMP", 100, "Rotación cefálica", average=500)
    _x, y_sac, _ = _curva(sacular, "CVEMP", 100, "Rotación cefálica", average=500)
    assert (y_sac.max() - y_sac.min()) < (y_sano.max() - y_sano.min()) / 2
    _x, o_sano, _ = _curva(ocular_sano, "OVEMP", 100, "Mirada superior ~30°", average=500)
    _x, o_sac, _ = _curva(ocular_sac, "OVEMP", 100, "Mirada superior ~30°", average=500)
    assert abs((o_sac.max() - o_sac.min()) - (o_sano.max() - o_sano.min())) < \
        (o_sano.max() - o_sano.min()) * 0.5


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  {nombre} OK")
            except AssertionError as exc:
                fallos += 1
                print(f"  {nombre} FALLÓ: {exc}")
    print("TODOS LOS TESTS PASARON" if not fallos else f"{fallos} FALLARON")
