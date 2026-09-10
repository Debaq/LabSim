"""Enmascaramiento tonal: rango de ruido útil por vía.

Regresiones cubiertas:
  - el máximo tolerable en vía ósea usaba la atenuación interaural del TONO
    (0 dB) en vez de la del RUIDO, que entra por auricular y cruza por vía
    aérea. El máximo quedaba igual al umbral óseo del oído estudiado, casi
    siempre por debajo del mínimo, y sólo funcionaban ruidos absurdamente
    bajos (5 dB);
  - el efecto oclusivo se evaluaba en el oído estudiado y con la condición
    invertida (lo daba cuando había gap, que es justo cuando no existe).

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audiometria.DebugMkg import _terminos  # noqa: E402
from audiometria.response import (CE_TONAL, STIM_NBN, STIM_PN,  # noqa: E402
                                  STIM_WN, ResponseAudiometry)


class FakeLabel:
    def setStyleSheet(self, value):
        pass


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


F1000 = 3  # índice de 1000 Hz; atenuación interaural aérea 40 dB
AT_1000 = 40


class MaskingOseoTest(unittest.TestCase):
    def motor(self, aerea, osea):
        r = ResponseAudiometry(FakeAudio())
        r.set_case(caso(aerea, osea))
        return r

    def test_maximo_oseo_usa_la_atenuacion_del_ruido(self):
        """El ruido entra por auricular: para volver a tapar al oído
        estudiado tiene que cruzar perdiendo la AI aérea."""
        r = self.motor(tabla(45, 5), tabla(5, 5))
        calc = r._masking_calc('osea', F1000, 0, 1)
        self.assertEqual(calc['mkg_max'], 5 + AT_1000)

    def test_el_rango_oseo_no_queda_invertido(self):
        """Regresión: con el máximo mal calculado el rango salía invertido y
        sólo servían ruidos de 5 dB."""
        r = self.motor(tabla(45, 5), tabla(5, 5))
        for o_e in (0, 1):
            calc = r._masking_calc('osea', F1000, o_e, 1 - o_e)
            self.assertGreaterEqual(calc['mkg_max'], calc['mkg_min'],
                                    f"rango invertido estudiando {o_e}")

    def test_ruido_razonable_deja_el_umbral_real(self):
        """Enmascarando el OI sano para medir el óseo del OD: un ruido en la
        meseta tiene que devolver el umbral real, no 130 ni la sombra."""
        r = self.motor(tabla(45, 5), tabla(5, 5))
        calc = r._masking_calc('osea', F1000, 0, 1)
        medio = (calc['mkg_min'] + calc['mkg_max']) / 2
        self.assertEqual(r._resolve_masked_threshold('osea', F1000, 0, 1, medio),
                         calc['real'])

    def test_cinco_dB_ya_no_es_lo_unico_que_sirve(self):
        r = self.motor(tabla(45, 5), tabla(5, 5))
        calc = r._masking_calc('osea', F1000, 0, 1)
        self.assertGreater(calc['mkg_max'] - calc['mkg_min'], 5)


class EfectoOclusivoTest(unittest.TestCase):
    def motor(self, aerea, osea):
        r = ResponseAudiometry(FakeAudio())
        r.set_case(caso(aerea, osea))
        return r

    def test_oido_sano_ocluido_tiene_efecto(self):
        r = self.motor(tabla(10, 10), tabla(10, 10))
        self.assertEqual(r.oclusive_efect(F1000, 0), 10)

    def test_gap_abole_el_efecto_oclusivo(self):
        """Un oído con patología de transmisión ya se comporta como ocluido
        (es el Bing negativo): taparlo no le agrega nada."""
        r = self.motor(tabla(50, 10), tabla(5, 10))
        self.assertEqual(r.oclusive_efect(F1000, 0), 0)

    def test_no_hay_efecto_en_agudos(self):
        r = self.motor(tabla(10, 10), tabla(10, 10))
        self.assertEqual(r.oclusive_efect(4, 0), 0)   # 2000 Hz

    def test_se_aplica_al_oido_ocluido_no_al_estudiado(self):
        """Estudiando el óseo del OD (gap) enmascarando el OI (sano): el
        ocluido es el OI, así que el efecto oclusivo entra en el mínimo.

        Se lee con _terminos (el desglose del panel) y no con _masking_calc
        porque este último ordena el rango, y con eso el mínimo de la
        fórmula puede terminar publicado como máximo."""
        aerea, osea = tabla(50, 10), tabla(5, 10)
        t = _terminos(self.motor(aerea, osea), 'osea', F1000, 0, 1)
        uoe, uone, uane = osea[F1000][0], osea[F1000][1], aerea[F1000][1]
        self.assertEqual(t['eo'], 10)
        self.assertEqual(t['mkg_min'], uoe - uone + uane + 10)

    def test_ocluido_con_gap_no_suma_efecto(self):
        """Al revés: si el oído que lleva el auricular tiene gap, no hay
        efecto oclusivo que corregir."""
        aerea, osea = tabla(60, 30), tabla(10, 10)
        t = _terminos(self.motor(aerea, osea), 'osea', F1000, 0, 1)
        uoe, uone, uane = osea[F1000][0], osea[F1000][1], aerea[F1000][1]
        self.assertEqual(t['eo'], 0)
        self.assertEqual(t['mkg_min'], uoe - uone + uane)

    def test_el_dilema_no_se_ve_en_el_rango_ordenado(self):
        """Documenta el comportamiento actual del motor: cuando el mínimo
        supera al máximo, _masking_calc los ordena y publica un rango que
        parece válido. Ver la nota del dilema en TODO.md."""
        aerea, osea = tabla(10, 50), tabla(10, 5)
        r = self.motor(aerea, osea)
        t = _terminos(r, 'osea', F1000, 0, 1)
        calc = r._masking_calc('osea', F1000, 0, 1)
        self.assertGreater(t['mkg_min'], t['mkg_max'])          # dilema real
        self.assertLessEqual(calc['mkg_min'], calc['mkg_max'])  # el motor lo tapa


class MaskingAereoTest(unittest.TestCase):
    def test_sin_cruce_el_sub_enmascarado_da_el_umbral_real(self):
        """Sin cruce posible el paciente responde su propio umbral: la
        sombra nunca puede empeorar el resultado."""
        r = ResponseAudiometry(FakeAudio())
        r.set_case(caso(tabla(30, 5), tabla(5, 5)))
        calc = r._masking_calc('aerea', F1000, 0, 1)
        self.assertEqual(calc['shadow'], calc['real'])
        self.assertEqual(r._resolve_masked_threshold('aerea', F1000, 0, 1, 0),
                         calc['real'])

    def test_con_cruce_la_sombra_es_mejor_que_el_umbral_real(self):
        r = ResponseAudiometry(FakeAudio())
        r.set_case(caso(tabla(90, 5), tabla(90, 5)))
        calc = r._masking_calc('aerea', F1000, 0, 1)
        self.assertLess(calc['shadow'], calc['real'])
        self.assertEqual(calc['shadow'], AT_1000 + 5)


if __name__ == "__main__":
    unittest.main()


class TablaOclusivaTest(unittest.TestCase):
    """El efecto oclusivo crece hacia los graves y desaparece sobre 2000 Hz:
    lo que la oclusión atrapa es energía de baja frecuencia que con el
    conducto abierto se disipa hacia afuera."""

    def setUp(self):
        r = ResponseAudiometry(FakeAudio())
        r.set_case(caso(tabla(10, 10), tabla(10, 10)))  # sin gap: hay efecto
        self.r = r

    def test_decrece_hacia_los_agudos(self):
        valores = [self.r.oclusive_efect(f, 0) for f in range(9)]
        self.assertEqual(valores, sorted(valores, reverse=True))

    def test_graves_pesan_mas_que_1000(self):
        self.assertGreater(self.r.oclusive_efect(1, 0),   # 250 Hz
                           self.r.oclusive_efect(3, 0))   # 1000 Hz

    def test_sin_efecto_desde_2000(self):
        for f in range(4, 9):
            self.assertEqual(self.r.oclusive_efect(f, 0), 0,
                             f"índice {f} debería no tener efecto oclusivo")

    def test_alta_frecuencia_no_rompe(self):
        self.assertEqual(self.r.oclusive_efect(12, 0), 0)   # 12500 Hz

    def test_son_los_valores_que_ensena_la_docente(self):
        """Candado a propósito: la tabla es la que enseña la docente y no se
        cambia sin hablarlo con ella. Si este test falla, alguien la
        "corrigió" con una tabla de manual -- ver TODO.md, sección del
        efecto oclusivo."""
        self.assertEqual([self.r.oclusive_efect(f, 0) for f in range(9)],
                         [15, 15, 15, 10, 0, 0, 0, 0, 0])


class TipoDeRuidoMotorTest(unittest.TestCase):
    """Regresión grave: el motor sólo entraba en la rama de enmascaramiento
    con NBN (`if 3 in stim`). Enmascarar con ruido blanco o pink sonaba pero
    no hacía nada, y el paciente respondía como sin enmascarar."""

    def setUp(self):
        self.r = ResponseAudiometry(FakeAudio())
        # OD sordo profundo, OI normal: sin enmascarar hay curva sombra
        self.r.set_case(caso(tabla(90, 5), tabla(90, 5)))
        self.mano = []
        self.r.upHand = lambda: self.mano.append(True)
        self.r.downHand = lambda: self.mano.append(False)

    def presentar(self, stim_ruido, int_mkg, int_tono=70):
        self.mano.clear()
        a = self.r.data['audio']
        a.update({'test': 'Umbrales', 'freq': F1000, 'stim': [0, stim_ruido],
                  'output': [0, 1], 'trans': [0, 0], 'int': [int_tono, int_mkg],
                  'stimOn': [True, True]})
        self.r.response_aerea_w_msk()
        return self.mano[-1] if self.mano else None

    def test_todos_los_ruidos_entran_en_la_formula(self):
        """Con ruido de sobra en el OI, el OD sordo deja de responder,
        cualquiera sea el ruido elegido."""
        for stim in (3, 4, 5, 6):
            self.assertIs(self.presentar(stim, 80), False,
                          f"el stim {stim} no enmascaró")

    def test_sin_ruido_responde_por_curva_sombra(self):
        self.assertIs(self.presentar(3, 0), True)

    def test_el_blanco_necesita_mas_nivel_que_el_nbn(self):
        """El CE en acción: un nivel que con NBN ya enmascara, con ruido
        blanco todavía no alcanza."""
        calc_nbn = self.r._masking_calc('aerea', F1000, 0, 1, 0)
        calc_wn = self.r._masking_calc('aerea', F1000, 0, 1, CE_TONAL[STIM_WN])
        self.assertEqual(calc_wn['mkg_min'] - calc_nbn['mkg_min'],
                         CE_TONAL[STIM_WN])

    def test_el_orden_de_eficiencia_es_nbn_pink_blanco(self):
        self.assertLess(CE_TONAL[STIM_NBN], CE_TONAL[STIM_PN])
        self.assertLess(CE_TONAL[STIM_PN], CE_TONAL[STIM_WN])

    def test_la_via_osea_tambien_acepta_los_cuatro(self):
        for stim in (3, 4, 5, 6):
            self.mano.clear()
            a = self.r.data['audio']
            a.update({'test': 'Umbrales', 'freq': F1000, 'stim': [0, stim],
                      'output': [0, 1], 'trans': [1, 0], 'int': [70, 80],
                      'stimOn': [True, True]})
            self.r.response_osea_w_msk()
            self.assertTrue(self.mano, f"el stim {stim} no entró en la ósea")

    def test_un_ruido_en_el_mismo_oido_no_enmascara(self):
        """El ruido tiene que estar en el oído contrario para servir."""
        a = self.r.data['audio']
        a.update({'stimOn': [True, True], 'output': [0, 0],
                  'stim': [0, 4], 'int': [70, 80]})
        self.assertIsNone(self.r._canal_ruido(1))
