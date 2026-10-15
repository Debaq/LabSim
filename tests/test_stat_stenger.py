"""
Stat y Stenger contra la clínica (2026-10-15).

1. STAT (Jerger y Jerger 1975): a 100 dB HL durante un minuto, positivo (el
   tono se pierde antes) en el oído retrococlear y negativo en el coclear o
   normal. El valor del caso es el deterioro en la escala del Carhart; antes
   se leía como margen sobre el umbral y a 100 dB HL casi ningún oído
   retrococlear quedaba positivo (paciente demo 39: Stat 30, umbrales de
   15-30 dB HL, daba negativo).
2. STENGER: de dos tonos iguales y simultáneos se percibe solo el de mayor
   nivel de sensación contra los umbrales VERDADEROS. Con la técnica clásica
   (+10 dB sobre el umbral del oído bueno, -10 dB bajo el que el paciente dio
   en el malo) una pérdida orgánica da negativo y una no orgánica positivo.
   Antes la no orgánica daba negativo.
3. Instrucción: el Stenger se instruye como los umbrales ("colocar_fonos");
   "Mano levantada en ruido" es el Carhart con ruido contralateral.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import copy
import json
import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from audiometria.response import ResponseAudiometry  # noqa: E402

DEMO = os.path.join(RAIZ, "docs", "manual", "capturas", "casos_demo.json")
HAND_UP = "background-color: rgb(170, 170, 255);"
STAT_FREQS = [2, 3, 4]   # 500, 1000, 2000 Hz


class FakeLabel:
    def __init__(self):
        self.style = ""

    def setStyleSheet(self, value):
        self.style = value


class FakeAudio:
    def __init__(self):
        self.lbl_response = FakeLabel()


def demo(caso_id):
    with open(DEMO, encoding="utf-8") as f:
        return json.load(f)[str(caso_id)]


class Base(unittest.TestCase):
    def nuevo(self, caso):
        self.audio = FakeAudio()
        self.r = ResponseAudiometry(self.audio)
        self.r.set_case(caso)

    def hand_up(self):
        return self.audio.lbl_response.style == HAND_UP

    def presentar(self, comando, **kw):
        base = {"trans": [0, 0], "contin": ["Continuo", "Continuo"],
                "test": "Umbrales", "step": 5}
        base.update(kw)
        self.r.data["audio"].update(base)
        self.r.history_command = [comando]
        self.r.response_()


class StatTest(Base):
    def stat(self, caso, oido, freq):
        """Stat en `oido`: tono a 100 dB HL y ruido blanco a 90 en el otro.
        Devuelve 'positivo' (se pierde antes del minuto) o 'negativo'."""
        self.nuevo(caso)
        self.presentar("ruido_blanco_contralateral", freq=freq,
                       stimOn=[True, True], stim=[0, 4],
                       output=[oido, 1 - oido], int=[100, 90])
        self.assertTrue(self.hand_up(), "a 100 dB HL el tono se oye al empezar")
        if self.r.decay_timer.isActive():
            self.assertLess(self.r.decay_timer.interval(), self.r.DECAY_HOLD_MS)
            return "positivo"
        return "negativo"

    def test_demo_39_schwannoma_od_positivo_oi_negativo(self):
        caso = demo(39)
        for f in STAT_FREQS:
            self.assertEqual(self.stat(caso, 0, f), "positivo", f)
            self.assertEqual(self.stat(caso, 1, f), "negativo", f)

    def test_demo_39_coherente_con_carhart_y_rosemberg(self):
        # el mismo oído que el Stat da positivo es el que deteriora en las
        # otras dos (>= 30 dB en la escala del Carhart)
        caso = demo(39)
        for clave in ("Carhart", "Rosemberg", "Stat"):
            self.assertTrue(all(par[0] >= ResponseAudiometry.STAT_POSITIVO_DB
                                for par in caso[clave]), clave)
            self.assertTrue(all(par[1] < ResponseAudiometry.STAT_POSITIVO_DB
                                for par in caso[clave]), clave)

    def test_demo_36_y_38_cocleares_negativos(self):
        for caso_id in (36, 38):
            caso = demo(caso_id)
            for oido in (0, 1):
                for f in STAT_FREQS:
                    self.assertEqual(self.stat(caso, oido, f), "negativo",
                                     (caso_id, oido, f))

    def test_retrococlear_con_umbral_normal_es_positivo(self):
        # schwannoma chico: umbral de 5 dB HL, deterioro de 30
        caso = demo(39)
        caso = copy.deepcopy(caso)
        caso["Aerea_mkg"][3] = [5, 5]
        caso["Aerea"][3] = [5, 5]
        self.assertEqual(self.stat(caso, 0, 3), "positivo")

    def test_mas_deterioro_se_pierde_antes(self):
        caso = copy.deepcopy(demo(39))
        self.stat(caso, 0, 3)
        con_30 = self.r.decay_timer.interval()
        caso["Stat"][1] = [60, 0]
        self.stat(caso, 0, 3)
        self.assertLess(self.r.decay_timer.interval(), con_30)

    def test_coclear_sin_margen_a_100_db_sigue_positivo(self):
        # regla vieja intacta: deterioro coclear de 20 dB en un oído de
        # 85 dB HL -- a 100 dB HL solo le quedan 15 dB y no le alcanza
        caso = copy.deepcopy(demo(36))
        caso["Aerea_mkg"][3] = [85, 30]
        caso["Aerea"][3] = [85, 30]
        caso["Stat"][1] = [20, 5]
        self.assertEqual(self.stat(caso, 0, 3), "positivo")

    def test_fuera_de_nivel_sigue_sin_resultado(self):
        self.nuevo(demo(39))
        self.presentar("ruido_blanco_contralateral", freq=3,
                       stimOn=[True, True], stim=[0, 4], output=[0, 1],
                       int=[80, 90])
        self.assertTrue(self.hand_up())
        self.assertFalse(self.r.decay_timer.isActive())


class StengerTest(Base):
    """Caso demo 38: OD normal (5 dB HL en 1 kHz), OI 40 dB HL."""

    def stenger(self, caso, nivel_od, nivel_oi, comando="colocar_fonos",
                freq=3):
        self.nuevo(caso)
        self.presentar(comando, freq=freq, stimOn=[True, True], stim=[0, 0],
                       output=[0, 1], int=[nivel_od, nivel_oi])
        return self.hand_up()

    def no_organico_oi(self):
        caso = copy.deepcopy(demo(38))
        caso["Stenger"] = [False, True]
        return caso

    def test_organico_tecnica_clasica_negativo(self):
        # +10 sobre el OD (5) y -10 bajo el OI (40): oye el del OD, responde
        self.assertTrue(self.stenger(demo(38), 15, 30))

    def test_no_organico_tecnica_clasica_positivo(self):
        # el OI oye de verdad como el OD: el tono de 30 tiene más nivel de
        # sensación, lo oye solo en el OI y, como dice no oír por ahí, calla
        self.assertFalse(self.stenger(self.no_organico_oi(), 15, 30))

    def test_no_organico_si_el_oido_bueno_gana_responde(self):
        # el tono del OI todavía por debajo del del OD en nivel de sensación
        self.assertTrue(self.stenger(self.no_organico_oi(), 25, 10))

    def test_no_organico_sobre_el_umbral_que_dio_responde(self):
        # a 45 en el OI ya está sobre los 40 que dio: no tiene que fingir
        self.assertTrue(self.stenger(self.no_organico_oi(), 15, 45))

    def test_ningun_tono_audible_no_responde(self):
        self.assertFalse(self.stenger(demo(38), 0, 30))

    def test_canales_cruzados(self):
        # el tono del OD en el canal 1: lo que importa es el oído, no el canal
        self.nuevo(self.no_organico_oi())
        self.presentar("colocar_fonos", freq=3, stimOn=[True, True],
                       stim=[0, 0], output=[1, 0], int=[30, 15])
        self.assertFalse(self.hand_up())

    def test_tono_y_ruido_no_es_stenger(self):
        # con colocar_fonos, tono + ruido no cambia la mano (como antes)
        self.nuevo(self.no_organico_oi())
        self.r.mano = True
        self.r.data["audio"].update({
            "test": "Umbrales", "freq": 3, "stimOn": [True, True],
            "stim": [0, 3], "output": [0, 1], "int": [15, 30], "trans": [0, 0]})
        self.r.history_command = ["colocar_fonos"]
        self.r.response_()
        self.assertTrue(self.r.mano)

    def test_mano_levantada_en_ruido_es_carhart_enmascarado(self):
        # ya no rutea al Stenger: con dos tonos no hay tono único que
        # cronometrar y la mano baja
        self.assertFalse(self.stenger(self.no_organico_oi(), 15, 45,
                                      comando="mano_levantada_en_ruido"))
        # con tono en el OD y ruido en el OI corre el Carhart: OD sano,
        # deterioro 0 -> sostiene el minuto
        self.nuevo(demo(38))
        self.presentar("mano_levantada_en_ruido", freq=3,
                       stimOn=[True, True], stim=[0, 3], output=[0, 1],
                       int=[25, 40])
        self.assertTrue(self.hand_up())
        self.assertFalse(self.r.decay_timer.isActive())


if __name__ == "__main__":
    unittest.main()
