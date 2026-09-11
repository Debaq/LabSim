"""Instrucción de enmascaramiento dada, pero sin ruido encendido.

Regresión: tras el comando 'aerea_+_ruido' (o 'vibrador_+_ruido') el paciente
dejaba de responder mientras el canal de ruido estuviera apagado. La
instrucción no lo enmudece: sigue oyendo el tono y, si necesitaba
enmascaramiento, contesta la CURVA SOMBRA (el otro oído).

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audiometria.response import STIM_NBN, STIM_TONO, ResponseAudiometry  # noqa: E402


class FakeLabel:
    def __init__(self):
        self.style = 'background-color: rgb(255, 255, 255);'  # mano abajo

    def setStyleSheet(self, value):
        self.style = value


class FakeAudio:
    def __init__(self):
        self.lbl_response = FakeLabel()


def tabla(od, oi):
    return [[od, oi] for _ in range(15)]


def caso(aerea, osea):
    return {
        "id": 1, "gender": 0, "edad": 30, "sector": "Camara_sono",
        "Aerea": aerea, "Osea": osea, "Aerea_mkg": aerea, "Osea_mkg": osea,
        "LDL": tabla(100, 100), "SDT": [20, 20], "SRT": [25, 25],
        "UMD": [{"int": 60, "percentage": 100}] * 2, "recruit": [False, False],
    }


F1000 = 3  # atenuación interaural aérea 40 dB


class SinRuidoTest(unittest.TestCase):
    # OD anacusia, OI normal: todo lo que "oiga" el OD sobre 50 dB es sombra
    AEREA = tabla(120, 10)
    OSEA = tabla(120, 10)

    def motor(self, comando, stim_on, int_, stim=None, trans=None):
        r = ResponseAudiometry(FakeAudio())
        r.set_case(caso(self.AEREA, self.OSEA))
        r.history_command.insert(0, comando)
        r.data['audio'].update({
            'test': 'Umbrales', 'freq': F1000, 'stimOn': list(stim_on),
            'int': list(int_), 'output': [0, 1],
            'trans': list(trans or [0, 0]),
            'stim': list(stim or [STIM_TONO, STIM_NBN]),
        })
        r.response_()
        return r

    def mano_arriba(self, r):
        return r.obj_audio.lbl_response.style != 'background-color: rgb(255, 255, 255);'

    def test_aereo_sin_ruido_da_curva_sombra(self):
        """Tono 70 dB en el OD muerto: cruza (70-40=30) y lo oye el OI."""
        r = self.motor('aerea_+_ruido', [True, False], [70, 0])
        self.assertTrue(self.mano_arriba(r))

    def test_aereo_sin_ruido_bajo_la_sombra_no_responde(self):
        """40 dB no alcanzan a cruzar: no hay respuesta, pero por nivel, no
        por haber dado la instrucción."""
        r = self.motor('aerea_+_ruido', [True, False], [40, 0])
        self.assertFalse(self.mano_arriba(r))

    def test_oseo_sin_ruido_da_curva_sombra(self):
        """Vía ósea: la AI es ~0, el OI sano contesta desde su propio umbral."""
        r = self.motor('vibrador_+_ruido', [True, False], [30, 0],
                       trans=[1, 0])
        self.assertTrue(self.mano_arriba(r))

    def test_solo_el_ruido_encendido_no_levanta_la_mano(self):
        """Oye el ruido, pero no es el pitito por el que se le pidió responder."""
        r = self.motor('aerea_+_ruido', [False, True], [0, 90],
                       stim=[STIM_TONO, STIM_NBN])
        self.assertFalse(self.mano_arriba(r))

    def test_con_ruido_suficiente_no_hay_sombra(self):
        """Control: con el enmascaramiento puesto, el OD muerto no responde."""
        r = self.motor('aerea_+_ruido', [True, True], [70, 90])
        self.assertFalse(self.mano_arriba(r))


if __name__ == '__main__':
    unittest.main()
