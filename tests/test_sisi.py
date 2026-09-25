"""
SISI: el paciente respondia una sola vez (al prender el tono) y despues nada,
porque el motor solo miraba el toc-toc y no las subidas de intensidad.

Ahora cada subida con el portador sonando es un incremento:
- 5 dB (familiarizacion) se nota siempre, SISI positivo o negativo.
- 1 dB (la prueba) se nota con el % SISI del caso.
- bajar (volver al portador) no se responde.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audiometria.response import ResponseAudiometry  # noqa: E402


class FakeLabel:
    def __init__(self):
        self.style = ""

    def setStyleSheet(self, value):
        self.style = value


class FakeAudio:
    def __init__(self):
        self.lbl_response = FakeLabel()


class FakeSender:
    def __init__(self, name, text):
        self._name, self._text = name, text

    def objectName(self):
        return self._name

    def text(self):
        return self._text


def flat(value):
    return [[value, value] for _ in range(15)]


class SisiTest(unittest.TestCase):
    def setUp(self):
        self.r = ResponseAudiometry(FakeAudio())
        self.r.set_case({
            "Aerea": flat(45), "Osea": flat(45),
            "Aerea_mkg": flat(45), "Osea_mkg": flat(45),
            "SISI": [0, 100],   # OD negativo, OI positivo
        })
        self.voces = []
        self.r.other_response.create_voice_ = self.voces.append
        self.r.history_command = ["cambie_de_volumen"]

    def portador(self, oido=0, nivel=65):
        self.r.data["audio"].update({
            "freq": 3, "test": "Umbrales", "stim": [0, 3],
            "output": [oido, 1 - oido], "int": [nivel, 0],
        })
        self.r.set_config(FakeSender("lbl_stimOn_ch0", "toc-toc"))

    def nivel(self, db):
        self.r.set_config(FakeSender("lbl_int_ch0", f"{db} dB HL"))

    def test_prender_el_tono_no_es_un_incremento(self):
        self.portador(oido=1)
        self.assertEqual(self.voces, [])

    def test_familiarizacion_de_5_db_siempre_responde_aunque_sea_negativo(self):
        self.portador(oido=0)
        for _ in range(5):
            self.nivel(70)
            self.nivel(65)
        self.assertEqual(self.voces, ["si"] * 5)

    def test_incremento_de_1_db_con_sisi_negativo_no_responde(self):
        self.portador(oido=0)
        for _ in range(20):
            self.nivel(66)
            self.nivel(65)
        self.assertEqual(self.voces, [])

    def test_incremento_de_1_db_con_sisi_positivo_responde_cada_vez(self):
        self.portador(oido=1)
        for _ in range(20):
            self.nivel(66)
            self.nivel(65)
        self.assertEqual(self.voces, ["si"] * 20)

    def test_incremento_de_1_db_usa_el_porcentaje_del_caso(self):
        self.r.dbdata["SISI"] = [40, 0]
        self.portador(oido=0)
        with mock.patch("audiometria.response.random.random",
                        side_effect=[0.39, 0.41]):
            self.nivel(66)
            self.nivel(65)
            self.nivel(66)
        self.assertEqual(self.voces, ["si"])

    def test_portador_bajo_el_umbral_no_deja_oir_incrementos(self):
        self.portador(oido=1, nivel=30)
        self.nivel(35)
        self.assertEqual(self.voces, [])

    def test_sin_tono_no_hay_incremento(self):
        self.portador(oido=1)
        self.r.set_config(FakeSender("lbl_stimOn_ch0", ""))
        self.nivel(70)
        self.assertEqual(self.voces, [])

    def test_otra_instruccion_no_responde_sisi(self):
        self.r.history_command = ["colocar_fonos"]
        self.portador(oido=1)
        self.voces.clear()
        self.nivel(70)
        self.assertEqual(self.voces, [])


if __name__ == "__main__":
    unittest.main()
