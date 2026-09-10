"""Cadena audiómetro -> listas de palabras -> CalculateLogo.

Cubre dos regresiones:
  - el constructor de ListWords llamaba a la_super() (que arma self.prev con
    el caso) y cuatro líneas después lo pisaba con None: el caso que llega
    por el constructor se perdía y calculate() no hacía nada hasta que
    main._hydrate_modules() volviera a llamar la_super();
  - el tipo de ruido enmascarante no viajaba desde el audiómetro, así que
    enmascarar habla con NBN rendía igual que con speech noise.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtWidgets import QApplication  # noqa: E402

from audiometria.ListWords import ListWords  # noqa: E402
from audiometria.masking_params import STIM_NBN, STIM_SN  # noqa: E402

QApplication.instance() or QApplication([])


def pad(filas):
    return filas + [filas[-1]] * (15 - len(filas))


def caso_anacusia_od():
    """OD anacúsico, OI normal: el caso clásico de curva sombra."""
    return {
        "id": 9, "gender": 1, "edad": 24, "sector": "Camara_sono",
        "Aerea": pad([[90, 5]] * 9), "Osea": pad([[90, 5]] * 9),
        "Aerea_mkg": pad([[90, 5]] * 9), "Osea_mkg": pad([[90, 5]] * 9),
        "LDL": pad([[120, 100]] * 9),
        "UMD": [{"int": 110, "percentage": 0},
                {"int": 40, "percentage": 100}],
        "SDT": [90, 5], "SRT": [90, 5], "recruit": [False, False],
    }


def estado(inten, side, ruido=None, stim=None):
    """El 'datasignal_speech' que emite el audiómetro:
    [activado, reverse, dB, oído, con_mkg, canal, dB ruido, stim ruido]."""
    return [True, True, inten, side, ruido is not None, 0, ruido, stim]


class ListWordsStateTest(unittest.TestCase):
    def setUp(self):
        self.w = ListWords(caso_anacusia_od())

    def aciertos(self, *args, **kwargs):
        self.w.update_state(estado(*args, **kwargs))
        return sum(self.w.list_response)

    def test_el_caso_del_constructor_no_se_pierde(self):
        self.assertIsNotNone(self.w.prev)

    def test_sin_ruido_responde_por_curva_sombra(self):
        """Habla a 90 dB en un OD anacúsico: la entiende con el OI."""
        self.assertEqual(self.aciertos(90, 0), 25)

    def test_el_speech_noise_desarma_la_sombra(self):
        self.assertEqual(self.aciertos(90, 0, 60, STIM_SN), 0)

    def test_el_nbn_al_mismo_nivel_rinde_menos(self):
        con_nbn = self.aciertos(90, 0, 60, STIM_NBN)
        con_sn = self.aciertos(90, 0, 60, STIM_SN)
        self.assertGreaterEqual(con_nbn, con_sn)

    def test_el_tipo_de_ruido_llega_al_estado(self):
        self.w.update_state(estado(90, 0, 60, STIM_NBN))
        self.assertEqual(self.w.playable[5], STIM_NBN)

    def test_estado_viejo_sin_tipo_de_ruido_no_rompe(self):
        """Un emisor que todavía mande 7 campos (sin el stim) tiene que
        seguir funcionando."""
        self.w.update_state([True, True, 90, 0, True, 0, 60])
        self.assertIsNone(self.w.playable[5])


if __name__ == "__main__":
    unittest.main()
