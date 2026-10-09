"""
Tone Decay y ETF del impedanciómetro (impedanciometria/z_generator.py).

- Decay: el reflejo del oído estimulado retrococlear cae a menos de la mitad
  dentro de los 10 s; el sano se sostiene. Sin reflejo no hay porcentaje.
- ETF, membrana perforada: la presión del conducto solo se iguala con
  degluciones si la trompa es permeable (con la membrana íntegra el conducto
  queda sellado y no cambia).
- ETF, membrana íntegra (presión-deglución de Williams): con la trompa
  normal el pico se corre al lado contrario de la presión aplicada, en el
  orden de magnitud publicado; con disfunción casi no se mueve; con la
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


def _pico(etf, maniobra, letra='A', seed=(1, 'OD', 'etf')):
    x, y, c, p, *_ = etf_prueba_integra(etf, letra, 1.2, maniobra, seed_key=seed)
    return float(p) if float(c) > 0.05 else None


def _diferencia_maxima(etf, seed):
    picos = [_pico(etf, m, seed=seed) for m in ('reposo', 'positiva', 'negativa')]
    return max(picos) - min(picos), picos


def test_etf_integra_normal_corre_el_pico_al_lado_contrario():
    # Lu y Wang 2026: en sanos la diferencia máxima tiene mediana 11 daPa
    # (RIC 6-17); acá cada paciente cae entre 8 y 18.
    for paciente in range(20):
        dif, (reposo, positiva, negativa) = _diferencia_maxima('Normal', (paciente, 'OD', 'etf'))
        assert positiva < reposo < negativa, (paciente, reposo, positiva, negativa)
        assert 8 <= dif <= 18, (paciente, dif)


def test_etf_integra_disfuncion_casi_no_mueve_el_pico():
    # Con disfunción: mediana 0 (RIC 0-2), corte <= 4 daPa.
    for paciente in range(20):
        dif, _ = _diferencia_maxima('Disfunción tubaria', (paciente, 'OD', 'etf'))
        assert dif <= 2, (paciente, dif)


def test_etf_integra_el_reposo_es_estable():
    assert _pico('Normal', 'reposo') == _pico('Normal', 'reposo')


def test_etf_integra_con_membrana_perforada_no_tiene_pico():
    for etf in ('Permeable', 'No permeable'):
        assert _pico(etf, 'reposo') is None


def test_decay_del_caso_y_casos_viejos():
    from impedanciometria.z_generator import reflex_decay_del_caso
    assert reflex_decay_del_caso({'decay': {'od': True, 'oi': False}}, 'od') is True
    assert reflex_decay_del_caso({'decay': {'od': False}, 'tipo': {'od': 'off'}}, 'od') is False
    assert reflex_decay_del_caso({'tipo': {'od': 'off'}}, 'od') is True   # caso sin migrar
    assert reflex_decay_del_caso([], 'oi') is False


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
