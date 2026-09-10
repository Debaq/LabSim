"""Panel de depuración de enmascaramiento (solo docente): el reporte tiene
que armarse sobre el motor real, mostrar las tablas *_mkg que usa el motor
(no las que ve el alumno), los rangos de la frecuencia actual y el % de
discriminación que devuelve CalculateLogo con el estado del audiómetro.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audiometria.DebugMkg import SIN_CASO, build_report  # noqa: E402
from audiometria.logoaudiometry import CalculateLogo  # noqa: E402
from audiometria.response import ResponseAudiometry  # noqa: E402


class FakeLabel:
    def setStyleSheet(self, value):
        pass


class FakeAudio:
    def __init__(self):
        self.lbl_response = FakeLabel()


def flat(value):
    return [[value, value] for _ in range(15)]


def caso(**over):
    data = {
        "id": 1, "gender": 0, "edad": 30, "sector": "Camara_sono",
        "Aerea": flat(20), "Osea": flat(20),
        "Aerea_mkg": flat(20), "Osea_mkg": flat(20),
        "LDL": flat(100), "SDT": [20, 20], "SRT": [25, 25],
        "UMD": [{"int": 60, "percentage": 100}, {"int": 60, "percentage": 100}],
        "recruit": [False, False],
    }
    data.update(over)
    return data


class DebugMkgTest(unittest.TestCase):
    def setUp(self):
        self.r = ResponseAudiometry(FakeAudio())

    def test_sin_caso_no_rompe(self):
        self.assertEqual(build_report(self.r), SIN_CASO)

    def test_muestra_tablas_mkg_y_avisa_cuando_difieren(self):
        data = caso(Aerea=flat(20), Aerea_mkg=flat(60))
        self.r.set_case(data)
        texto = build_report(self.r, case=data)
        self.assertIn("Aerea_mkg", texto)
        # 500 Hz es la tercera fila: tiene que salir marcada como distinta
        self.assertIn("! Aerea/Osea != *_mkg en:", texto)
        self.assertIn("500", texto)

    def test_rango_tonal_de_la_frecuencia_actual(self):
        data = caso(Aerea_mkg=[[60, 10] for _ in range(15)],
                    Osea_mkg=[[60, 10] for _ in range(15)])
        self.r.set_case(data)
        self.r.data['audio']['freq'] = 3          # 1000 Hz, at = 40
        esperado = self.r._masking_calc('aerea', 3, 0, 1)
        texto = build_report(self.r, case=data)
        self.assertIn("=== ENMASCARAMIENTO TONAL", texto)
        self.assertIn(f"{esperado['mkg_min']:g} .. {esperado['mkg_max']:g} dB", texto)

    def test_logo_reporta_el_porcentaje_que_responde_el_paciente(self):
        data = caso()
        self.r.set_case(data)
        self.r.data['audio']['test'] = 'Logoaudiometría'
        logo = CalculateLogo(data, data["UMD"])
        # habla a 60 dB en OD, sin ruido contralateral
        estado = [True, 60, 0, False, None]
        texto = build_report(self.r, logo, estado, data)
        pct = logo.get(0, False, 60, None)
        self.assertIn("=== LOGOAUDIOMETRÍA", texto)
        self.assertIn(f"{pct}%", texto)
        self.assertIn("Curva de discriminación", texto)

    def test_logo_sobre_enmascarado_se_reporta_como_tal(self):
        data = caso()
        self.r.set_case(data)
        logo = CalculateLogo(data, data["UMD"])
        # ruido muy por encima de at + umbral óseo -> sobre-enmascarado
        estado = [True, 60, 0, True, 110]
        texto = build_report(self.r, logo, estado, data)
        self.assertIn("SOBRE-ENMASCARADO", texto)
        self.assertIn("0%", texto)


if __name__ == "__main__":
    unittest.main()
