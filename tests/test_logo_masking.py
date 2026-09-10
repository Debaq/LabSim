"""Enmascaramiento de logoaudiometría: el paciente contesta con el oído que
mejor entienda, así que el cruce interaural sólo puede mejorar el puntaje,
nunca hundir el del oído estudiado.

Regresión: un OI normal (SDT 0 dB, UMD 100% @ 40 dB) contra un OD con
componente de transmisión daba 4% a 40 dB sin ruido, porque CalculateLogo
reemplazaba la curva del oído estudiado por la curva sombra del contralateral
en vez de quedarse con la mejor. El alumno se veía obligado a enmascarar un
oído sano para que respondiera.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audiometria.logoaudiometry import CalculateLogo  # noqa: E402
from audiometria.masking_params import (CE_LOGO, STIM_NBN,  # noqa: E402
                                        STIM_PN, STIM_SN, STIM_WN,
                                        ce_logo, ce_tonal)


def flat(od, oi):
    return [[od, oi] for _ in range(15)]


CASO_TRANSMISIVA = {
    # OD con gap (aéreo ~25 dB de SDT, óseo 0), OI normal
    "Aerea_mkg": [[50, 0], [45, 5], [45, 0], [30, 5], [25, 5],
                  [30, 0], [35, 0], [40, 5], [40, 0]],
    "Osea_mkg": [[5, 0], [5, 5], [5, 0], [0, 5], [5, 5],
                 [5, 0], [5, 0], [5, 5], [5, 0]],
    "UMD": [{"int": 70, "percentage": 100}, {"int": 40, "percentage": 100}],
    "SDT": [25, 0], "recruit": [False, False],
}

CASO_ANACUSIA_OD = {
    "Aerea_mkg": flat(110, 5), "Osea_mkg": flat(110, 5),
    "UMD": [{"int": 110, "percentage": 0}, {"int": 40, "percentage": 100}],
    "SDT": [110, 5], "recruit": [False, False],
}


def logo(caso):
    return CalculateLogo(caso, caso["UMD"])


class LogoMaskingTest(unittest.TestCase):
    def test_oido_sano_responde_sin_enmascarar(self):
        """OI normal a 40 dB: su UMD es 100%, no puede hundirse por el
        contralateral peor. Sin ruido y con ruido tienen que dar lo mismo."""
        l = logo(CASO_TRANSMISIVA)
        self.assertEqual(l.get(1, False, 40, None), 100)
        self.assertEqual(l.get(1, True, 40, 30), 100)

    def test_curva_propia_sin_ruido_cuando_no_hay_cruce(self):
        """Bajo la atenuación interaural (45 dB) no hay cruce posible: el
        paciente responde exactamente su propia curva."""
        l = logo(CASO_TRANSMISIVA)
        for side in (0, 1):
            for inten in (20, 30, 40):
                self.assertEqual(l.get(side, False, inten, None),
                                 l.data[side][str(inten)],
                                 f"lado {side} a {inten} dB")

    def test_el_cruce_nunca_empeora(self):
        l = logo(CASO_TRANSMISIVA)
        for side in (0, 1):
            for inten in range(0, 105, 5):
                self.assertGreaterEqual(l.get(side, False, inten, None),
                                        l.data[side][str(inten)],
                                        f"lado {side} a {inten} dB")

    def test_curva_sombra_en_oido_anacusico(self):
        """Sin enmascarar, un OD anacúsico 'discrimina' porque cruza al OI:
        ese es el engaño que el enmascaramiento tiene que desarmar."""
        l = logo(CASO_ANACUSIA_OD)
        sin_ruido = l.get(0, False, 90, None)
        self.assertGreaterEqual(sin_ruido, 80)
        # con ruido efectivo en el OI, el cruce desaparece
        self.assertLessEqual(l.get(0, True, 90, 60), 4)

    def test_sobre_enmascaramiento_tapa_el_oido_estudiado(self):
        """Ruido por encima de at + óseo del estudiado cruza de vuelta y le
        sube el umbral: el puntaje real cae."""
        l = logo(CASO_TRANSMISIVA)
        normal = l.get(0, True, 70, 40)
        sobre = l.get(0, True, 70, 100)
        self.assertEqual(normal, 100)
        self.assertLess(sobre, normal)

    def test_meseta_estable_en_el_rango_de_enmascaramiento(self):
        """Dentro de [mkg_min, mkg_max] el puntaje no se mueve (meseta)."""
        l = logo(CASO_TRANSMISIVA)
        r = l._masking_range(0, 1, 70)
        lo = int(max(0, r["mkg_min"]) // 5 * 5)
        hi = int(r["mkg_max"] // 5 * 5)
        valores = {l.get(0, True, 70, n) for n in range(lo, hi + 1, 5)}
        self.assertEqual(valores, {l.data[0]["70"]})

    def test_intensidades_fuera_de_escala_no_rompen(self):
        l = logo(CASO_TRANSMISIVA)
        self.assertEqual(l.get(0, False, 120, None), l.data[0]["100"])
        self.assertEqual(l.get(0, False, -10, None), l.data[0]["0"])


if __name__ == "__main__":
    unittest.main()


class TipoDeRuidoLogoTest(unittest.TestCase):
    """En logoaudiometría el ruido correcto es el conformado al habla: el
    habla ocupa todo el espectro y una banda estrecha deja pasar casi todo.
    Es el orden inverso al de la vía tonal.

    Regresión: el audiómetro exigía literalmente "Speech Noise" para dar por
    activo el enmascaramiento, así que enmascarar con NBN, blanco o pink
    sonaba pero no llegaba al motor.
    """

    def setUp(self):
        # OD anacúsico, OI normal: sin enmascarar responde por curva sombra
        self.logo = logo(CASO_ANACUSIA_OD)

    def test_speech_noise_es_la_referencia(self):
        self.assertEqual(ce_logo(STIM_SN), 0)

    def test_el_nbn_es_el_peor_para_el_habla(self):
        self.assertGreater(ce_logo(STIM_NBN), ce_logo(STIM_WN))
        self.assertGreater(ce_logo(STIM_NBN), ce_logo(STIM_PN))

    def test_orden_inverso_al_tonal(self):
        """Lo que en tonal es el mejor ruido, en habla es el peor."""
        self.assertLess(ce_tonal(STIM_NBN), ce_tonal(STIM_SN))
        self.assertGreater(ce_logo(STIM_NBN), ce_logo(STIM_SN))

    def test_el_nbn_enmascara_menos_que_el_speech_noise(self):
        """Mismo nivel de dial, distinto resultado: con NBN el cruce
        sobrevive y el paciente sigue 'discriminando' con el oído sano."""
        con_sn = self.logo.get(0, True, 90, 60, STIM_SN)
        con_nbn = self.logo.get(0, True, 90, 60, STIM_NBN)
        self.assertLess(con_sn, con_nbn)

    def test_subiendo_el_nbn_se_llega_al_mismo_efecto(self):
        """El CE es una penalidad de nivel, no una inutilización: con 20 dB
        más de NBN se consigue lo mismo que con el speech noise."""
        self.assertEqual(self.logo.get(0, True, 90, 60 + CE_LOGO[STIM_NBN],
                                       STIM_NBN),
                         self.logo.get(0, True, 90, 60, STIM_SN))

    def test_sin_tipo_declarado_se_asume_el_correcto(self):
        """Los casos y llamadas viejas no pasan el tipo: no se los penaliza."""
        self.assertEqual(self.logo.get(0, True, 90, 60),
                         self.logo.get(0, True, 90, 60, STIM_SN))

    def test_el_rango_se_corre_con_el_ce(self):
        r_sn = self.logo._masking_range(0, 1, 90, STIM_SN)
        r_nbn = self.logo._masking_range(0, 1, 90, STIM_NBN)
        self.assertEqual(r_nbn['mkg_min'] - r_sn['mkg_min'],
                         CE_LOGO[STIM_NBN])


class CurvaSombraTest(unittest.TestCase):
    """La curva sombra tiene que ser progresiva: sube con la intensidad, no
    aparece entera de golpe. El paciente con un oído muerto 'discrimina' con
    el sano sólo cuando el habla supera la atenuación interaural y llega a
    ese oído con suficiente nivel de sensación."""

    def setUp(self):
        self.logo = logo(CASO_ANACUSIA_OD)

    def test_bajo_la_atenuacion_interaural_no_hay_nada(self):
        for inten in (40, 45, 50):
            self.assertEqual(self.logo.get(0, False, inten, None), 0,
                             f"a {inten} dB el habla no debería cruzar")

    def test_sube_de_a_poco_con_la_intensidad(self):
        curva = [self.logo.get(0, False, i, None) for i in range(50, 101, 10)]
        self.assertEqual(curva, sorted(curva))
        self.assertLess(curva[1], curva[-1])

    def test_la_sombra_es_la_curva_del_oido_sano_al_nivel_que_le_llega(self):
        """No es un 100% por decreto: es lo que ese oído da al nivel que
        efectivamente le llega (intensidad menos atenuación interaural)."""
        self.assertEqual(self.logo.get(0, False, 90, None),
                         self.logo.data[1]["45"])
        self.assertEqual(self.logo.get(0, False, 70, None),
                         self.logo.data[1]["25"])

    def test_el_oido_anacusico_no_discrimina_por_si_mismo(self):
        """Regresión: la escala arranca en 1 y los tramos que no se recorren
        --UMD fuera de la escala-- quedaban con ese valor crudo, así que un
        oído muerto 'discriminaba' 1% en los niveles altos."""
        self.assertEqual(set(self.logo.data[0].values()), {0})
