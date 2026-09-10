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


class CoherenciaTest(unittest.TestCase):
    """El panel tiene que delatar las fichas que contradicen la fisiología:
    de eso vive el docente cuando arma un caso y el paciente simulado no se
    comporta como esperaba."""

    def setUp(self):
        self.r = ResponseAudiometry(FakeAudio())

    def reporte(self, **over):
        data = caso(**over)
        self.r.set_case(data)
        return build_report(self.r, case=data)

    def test_oseo_peor_que_aereo_es_imposible(self):
        texto = self.reporte(Aerea_mkg=flat(20), Osea_mkg=flat(50))
        self.assertIn("PEOR que el", texto)

    def test_gap_sobre_el_techo_de_transmision(self):
        texto = self.reporte(Aerea_mkg=flat(80), Osea_mkg=flat(0))
        self.assertIn("techo de transmisión", texto)

    def test_reflejo_presente_con_gap(self):
        texto = self.reporte(
            Aerea_mkg=flat(60), Osea_mkg=flat(10),
            Reflex={"ipsi": [[85, 85]] * 4, "contra": [[130, 130]] * 5})
        self.assertIn("abole el reflejo", texto)

    def test_weber_al_oido_equivocado(self):
        # gap grande en OD pero el Weber lateraliza al OI
        texto = self.reporte(
            Aerea_mkg=[[60, 20] for _ in range(15)],
            Osea_mkg=[[10, 20] for _ in range(15)],
            Weber={"1000": "oi"})
        self.assertIn("Weber 1000 Hz lateraliza a OI", texto)

    def test_rinne_positivo_con_gap_grande(self):
        texto = self.reporte(
            Aerea_mkg=[[60, 20] for _ in range(15)],
            Osea_mkg=[[10, 20] for _ in range(15)],
            Rinne={"1000": {"od": "positivo"}})
        self.assertIn("Rinne positivo en OD", texto)

    def test_eoa_normales_con_gap(self):
        texto = self.reporte(
            Aerea_mkg=[[60, 20] for _ in range(15)],
            Osea_mkg=[[10, 20] for _ in range(15)],
            EOAS={"OD": {"type": "normal"}, "OI": {"type": "normal"}})
        self.assertIn("EOA OD normales con gap", texto)

    def test_ldl_bajo_el_umbral(self):
        texto = self.reporte(Aerea_mkg=flat(70), Osea_mkg=flat(70),
                             LDL=flat(50))
        self.assertIn("LDL", texto)
        self.assertIn("bajo el umbral", texto)

    def test_ficha_coherente_no_inventa_avisos(self):
        """Transmisiva pura de un lado: reflejo abolido de ese lado, Weber y
        Rinne acordes, EOA ausentes por el oído medio. No debe avisar nada."""
        texto = self.reporte(
            Aerea_mkg=[[45, 5] for _ in range(15)],
            Osea_mkg=[[5, 5] for _ in range(15)],
            Aerea=[[45, 5] for _ in range(15)],
            Osea=[[5, 5] for _ in range(15)],
            SDT=[45, 5], SRT=[45, 5],
            UMD=[{"int": 80, "percentage": 100},
                 {"int": 40, "percentage": 100}],
            LDL=flat(110),
            Reflex={"ipsi": [[130, 85]] * 4, "contra": [[130, 130]] * 5},
            Weber={"1000": "od"},
            Rinne={"1000": {"od": "negativo", "oi": "positivo"}},
            EOAS={"OD": {"type": "transmission"}, "OI": {"type": "normal"}})
        self.assertIn("sin contradicciones detectadas", texto)

    def test_dilema_de_enmascaramiento(self):
        """Gap grande bilateral: no existe ruido que enmascare al contrario
        sin cruzar de vuelta al oído estudiado."""
        texto = self.reporte(Aerea_mkg=flat(65), Osea_mkg=flat(10))
        self.assertIn("DILEMA", texto)

    def test_avisa_cuando_no_hace_falta_enmascarar(self):
        texto = self.reporte(Aerea_mkg=flat(10), Osea_mkg=flat(10))
        self.assertIn("no hace falta enmascarar", texto)


class TipoDeRuidoTest(unittest.TestCase):
    """El equipo tiene NBN, ruido blanco, speech noise y pink noise. Los
    cuatro enmascaran, pero no con la misma eficiencia: lo que tapa un tono
    es la energía dentro de su banda crítica, y sólo el NBN la concentra
    ahí. El panel tiene que mostrar el CE que se aplicó."""

    def setUp(self):
        self.r = ResponseAudiometry(FakeAudio())
        self.data = caso(Aerea_mkg=[[70, 10] for _ in range(15)],
                         Osea_mkg=[[70, 10] for _ in range(15)])
        self.r.set_case(self.data)

    def montar(self, stim_ruido):
        a = self.r.data['audio']
        a['freq'] = 3
        a['stim'] = [0, stim_ruido]
        a['output'] = [0, 1]
        a['trans'] = [0, 0]
        a['int'] = [70, 40]
        a['stimOn'] = [True, True]
        return build_report(self.r, case=self.data)

    def test_nbn_no_paga_penalidad(self):
        texto = self.montar(3)
        self.assertIn("Narrow Band Noise 40 dB en OI", texto)
        self.assertNotIn("enmascara peor que el NBN", texto)

    def test_ruido_blanco_enmascara_con_ce(self):
        texto = self.montar(4)
        self.assertIn("Withe Noise 40 dB en OI", texto)
        self.assertIn("CE +10 dB", texto)

    def test_pink_noise_enmascara_con_ce_menor(self):
        texto = self.montar(6)
        self.assertIn("Pink Noise 40 dB en OI", texto)
        self.assertIn("CE +5 dB", texto)

    def test_speech_noise_en_tonal_paga_como_el_blanco(self):
        self.assertIn("CE +10 dB", self.montar(5))

    def test_ningun_ruido_queda_sin_usarse(self):
        for stim in (3, 4, 5, 6):
            self.assertNotIn("SIN ruido contralateral", self.montar(stim),
                             f"el motor ignoró el stim {stim}")
