"""
Tone Decay y ETF del impedanciómetro (impedanciometria/z_generator.py).

- Decay: el reflejo del oído estimulado retrococlear cae a menos de la mitad
  dentro de los 10 s; el sano se sostiene. Sin reflejo no hay porcentaje.
- ETF, membrana perforada: la presión del conducto solo se iguala con
  degluciones si la trompa es permeable (con la membrana íntegra el conducto
  queda sellado y no cambia).
- ETF, membrana íntegra (Williams): con la trompa normal el pico se corre
  (Valsalva a positivo, Toynbee a negativo); con disfunción, no; con la
  membrana perforada no hay pico.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from impedanciometria.z_generator import (decay_curve, etf_prueba_integra,  # noqa: E402
                                          etf_prueba_perforada)


def test_decay_retrococlear_cae_a_menos_de_la_mitad():
    _, _, pct5, pct10 = decay_curve(True, dB=95, threshold=85, decae=True)
    assert pct10 < 50, pct10
    assert pct5 > pct10


def test_decay_sano_se_sostiene():
    _, _, pct5, pct10 = decay_curve(True, dB=95, threshold=85, decae=False)
    assert pct10 >= 90, pct10


def test_decay_sin_reflejo_no_da_porcentaje():
    x, y, pct5, pct10 = decay_curve(False)
    assert pct5 is None and pct10 is None
    assert max(abs(v) for v in y) < 20  # solo ruido de la línea base


def test_etf_perforada_permeable_iguala():
    _, _, final = etf_prueba_perforada('Permeable', -200)
    assert abs(final) <= 20, final


def test_etf_perforada_no_permeable_y_membrana_integra_no_igualan():
    for etf in ('No permeable', 'Normal', 'Disfunción tubaria'):
        _, _, final = etf_prueba_perforada(etf, -200)
        assert final <= -180, (etf, final)


def _pico(etf, maniobra, letra='A'):
    x, y, c, p, *_ = etf_prueba_integra(etf, letra, 1.2, maniobra, seed_key=(1, 'OD', 'etf'))
    return float(p) if float(c) > 0.05 else None


def test_etf_integra_normal_corre_el_pico():
    reposo = _pico('Normal', 'reposo')
    assert _pico('Normal', 'valsalva') - reposo >= 25
    assert reposo - _pico('Normal', 'toynbee') >= 20


def test_etf_integra_disfuncion_no_corre_el_pico():
    reposo = _pico('Disfunción tubaria', 'reposo')
    for maniobra in ('valsalva', 'toynbee'):
        assert abs(_pico('Disfunción tubaria', maniobra) - reposo) <= 8


def test_etf_integra_con_membrana_perforada_no_tiene_pico():
    for etf in ('Permeable', 'No permeable'):
        assert _pico(etf, 'reposo') is None


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
