"""TEOAE: nivel del click y modo lineal / no lineal.

El nivel no movía la emisión (solo la estabilidad del estímulo) y no había
modo: el click de 60 dB SPL que traía el panel daba lo mismo que el de 80 no
lineal que pide el protocolo. Ahora:

1. La emisión es la normativa con click NO LINEAL a 80 dB SPL y crece
   compresiva con el nivel: a 60 dB sale más chica.
2. En LINEAL la emisión es más grande (la no lineal pierde al menos 6 dB),
   pero no se cancela la cola del click: con la sonda floja alcanza para un
   PASS falso en un oído sin emisiones.
3. El análisis arranca en la ventana del equipo (2,5 ms); el trazo que se
   muestra es el entero.
"""
import os
import sys

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from oae.generators.teoae import TeoaeGenerator  # noqa: E402


def _caso(sello=95, atten=0.0):
    return {"type": "normal", "umbral": 10, "desviaciones": {},
            "sello_pct": sello, "atten_db": atten}


def _snr_medio(r):
    return float(np.mean(list(r["snr_per_band"].values())))


def test_protocol_level_passes_a_normal_ear():
    g = TeoaeGenerator()
    for ear in ("OD", "OI"):
        r = g.generate(80, 260, ear, _caso(), n_frames=3, mode="no_lineal")
        assert r["overall_pass"], ear
        assert r["reproducibility_pct"] > 85, r["reproducibility_pct"]
        assert r["mode"] == "no_lineal"


def test_lower_click_gives_a_smaller_emission():
    g = TeoaeGenerator()
    assert g.level_shift_db(60, "no_lineal") < g.level_shift_db(70, "no_lineal") < 0
    assert g.level_shift_db(80, "no_lineal") == 0
    a80 = g.generate(80, 260, "OD", _caso(), n_frames=3)
    a60 = g.generate(60, 260, "OD", _caso(), n_frames=3)
    assert _snr_medio(a60) < _snr_medio(a80) - 4


def test_linear_mode_is_bigger_and_carries_the_click_tail():
    g = TeoaeGenerator()
    assert g.level_shift_db(80, "lineal") - g.level_shift_db(80, "no_lineal") >= 6
    # Oído sin emisiones (coclear severa) con la sonda floja: en no lineal
    # refiere; en lineal la cola del click, igual en A y en B, sube la
    # reproducibilidad y llega a pasar bandas.
    sin_eoa = _caso(sello=40, atten=40)
    nl = g.generate(80, 260, "OD", sin_eoa, n_frames=3, mode="no_lineal")
    li = g.generate(80, 260, "OD", sin_eoa, n_frames=3, mode="lineal")
    assert not nl["overall_pass"]
    assert li["reproducibility_pct"] > nl["reproducibility_pct"] + 40
    assert li["n_pass"] > nl["n_pass"]


def test_well_sealed_linear_does_not_fake_a_pass():
    """Con la sonda bien puesta la cola muere antes de la ventana."""
    g = TeoaeGenerator()
    r = g.generate(80, 260, "OD", _caso(sello=95, atten=40), n_frames=3, mode="lineal")
    assert not r["overall_pass"]


def test_unknown_mode_falls_back_to_the_protocol():
    r = TeoaeGenerator().generate(80, 260, "OD", _caso(), n_frames=3, mode="raro")
    assert r["mode"] == "no_lineal"


def test_shown_trace_keeps_the_stimulus_window():
    """Lo que se ve es el registro entero: la ventana solo recorta el análisis."""
    g = TeoaeGenerator()
    r = g.generate(80, 260, "OD", _caso(sello=40), n_frames=3, mode="lineal")
    t = r["time_ms"]
    temprano = np.abs(r["waveform"][t < 1.0]).max()
    assert temprano > 0


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print("ok", nombre)
