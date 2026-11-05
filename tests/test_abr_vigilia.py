"""
Despierto o dormido (src/abr/vigilia.py): el paciente llega despierto y los
potenciales salen sucios hasta que el alumno pide en el chat que lo duerman.
"""

import os
import sys

import numpy as np

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from abr import assr, vigilia  # noqa: E402
from abr.ABR_generator import ABRGenerator, default_settings  # noqa: E402

NORMS = os.path.join(os.path.dirname(__file__), '..', 'resources', 'abr', 'normative_data.json')
BEBE = {'id': '163', 'edad': 0}
ADULTO = {'id': '40', 'edad': 45}


def _con_chat(fn):
    viejo = vigilia.por_chat
    vigilia.por_chat = True
    try:
        for p in (BEBE, ADULTO):
            vigilia.despertar(p['id'])
        return fn()
    finally:
        vigilia.por_chat = viejo
        for p in (BEBE, ADULTO):
            vigilia.despertar(p['id'])


def _curva(patient):
    stim = {'stim': 'click', 'freq': None, 'pol': 'Alternada', 'int': 60,
            'rate': 21.1, 'filter_down': 3000, 'filter_passhigh': 100,
            'average': 2000, 'current_avg': 2000, 'pathway': 'air_conduction'}
    case = {'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'umbral': 20, 'average_objetivo': 2000, 'repro_shift': 0.0,
            'masking': 0, 'contra': None, 'seed_key': 'caso-1', 'capture_id': 'R1',
            'inquietud': vigilia.inquietud(patient, 0), 'vigilia_ruido': vigilia.ruido(patient)}
    return ABRGenerator(NORMS).generate_curve('adult_female', 'normal', stim,
                                              default_settings('ABR'), case)


def test_sin_chat_llega_dormido():
    """Sin chat no hay a quién pedírselo: nadie queda trabado."""
    viejo = vigilia.por_chat
    vigilia.por_chat = False
    try:
        assert vigilia.factores(BEBE) == (1.0, 0.0)
    finally:
        vigilia.por_chat = viejo


def test_despierto_ensucia_y_mas_al_bebe():
    def prueba():
        bebe, adulto = vigilia.factores(BEBE), vigilia.factores(ADULTO)
        assert bebe[0] > adulto[0] > 1.0 and bebe[1] > adulto[1] > 0.0
        vigilia.dormir('163')
        assert vigilia.factores(BEBE) == (1.0, 0.0)
        assert vigilia.factores(ADULTO) == adulto, "dormir a uno no duerme a otro"
        vigilia.despertar('163')
        assert vigilia.factores(BEBE) == bebe, "atención nueva: llega despierto"
    _con_chat(prueba)


def test_la_inquietud_del_caso_manda_si_es_mayor():
    def prueba():
        assert vigilia.inquietud(ADULTO, 0.9) == 0.9
        vigilia.dormir('40')
        assert vigilia.inquietud(ADULTO, 0.3) == 0.3, "dormido queda la del caso"
    _con_chat(prueba)


def test_dormirlo_baja_el_ruido_del_abr():
    def prueba():
        _, _, despierto = _curva(BEBE)
        vigilia.dormir('163')
        _, _, dormido = _curva(BEBE)
        assert dormido['residual_noise_nv'] < despierto['residual_noise_nv'] / 2, (
            despierto['residual_noise_nv'], dormido['residual_noise_nv'])
        assert dormido['fsp'] > despierto['fsp']
        assert dormido['accepted_sweeps'] >= despierto['accepted_sweeps']
    _con_chat(prueba)


def test_dormirlo_baja_el_ruido_del_assr():
    def prueba():
        rec = assr.Recording({'OD': None, 'OI': None}, patient=BEBE)
        despierto = rec._noise_sigma().mean()
        vigilia.dormir('163')
        assert rec._noise_sigma().mean() < despierto / 2
    _con_chat(prueba)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
