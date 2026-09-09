"""
Deterioro tonal: las tres pruebas se administran distinto y el motor las
tenía todas iguales al Carhart.

1. El STAT es a NIVEL FIJO (110 dB SPL ~ 100 dB HL), no se sube de a 5 dB.
   Administrado a otro nivel no entrega resultado.
2. El STAT exige ruido blanco contralateral a nivel de protocolo, y su umbral
   es el real del oído: la fórmula de enmascaramiento daba sobre-enmascarado
   con un ruido de 90 dB y el paciente no respondía nunca.
3. El ROSEMBERG cronometra el minuto COMPLETO: subir el nivel no devuelve
   tiempo. Antes cada subida regalaba 60 s nuevos, o sea era un Carhart.
4. El canal del tono no es "el primer canal encendido": con ruido
   contralateral el tono puede ir en ch1 y el motor leía el ruido como tono.
5. El reloj es TIEMPO REAL y corre por presentación, no por llamada al motor.
   El alumno cronometra por fuera, con un reloj manual que nadie sincroniza
   con esto (btn_time_start/stop del audiómetro, o el de pulsera), así que
   mover otra perilla no puede re-armar el minuto entero y regalarle tono de
   más: lo que él mide y lo que corre acá tienen que ser el mismo minuto.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import time
import unittest

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


HAND_UP = "background-color: rgb(170, 170, 255);"


def flat(value):
    return [[value, value] for _ in range(15)]


class ToneDecayTest(unittest.TestCase):
    def setUp(self):
        self.audio = FakeAudio()
        self.r = ResponseAudiometry(self.audio)
        self.r.set_case({
            "Aerea": flat(20), "Osea": flat(20),
            "Aerea_mkg": flat(20), "Osea_mkg": flat(20),
            "LDL": flat(110),
            # dB sobre el umbral que hacen falta para sostener el minuto
            "Carhart": [[0, 0], [40, 0], [0, 0], [0, 0]],
            "Stat":    [[0, 0], [40, 0], [0, 0]],
            "Rosemberg": [[0, 0], [40, 0], [0, 0], [0, 0]],
        })

    def hand_up(self):
        return self.audio.lbl_response.style == HAND_UP

    def set_audio(self, **kw):
        self.r.data["audio"].update(kw)

    def run_test(self, command, **kw):
        self.r.history_command = [command]
        base = {"freq": 3, "trans": [0, 0], "contin": ["Continuo", "Continuo"],
                "test": "Umbrales", "step": 5}
        base.update(kw)
        self.set_audio(**base)
        self.r.response_tone_decay(command)

    # ---------- Stat ----------
    def test_stat_a_nivel_sostiene_el_minuto_si_el_oido_no_decae(self):
        # OI (decay 0): a 100 dB HL con ruido contralateral aguanta
        self.run_test("ruido_blanco_contralateral", stimOn=[True, True],
                      stim=[0, 4], output=[1, 0], int=[100, 90])
        self.assertTrue(self.hand_up())
        self.assertFalse(self.r.decay_timer.isActive())

    def test_stat_positivo_suelta_antes_del_minuto(self):
        # OD necesita 40 dB sobre umbral (20) = 60 dB de margen; a 100 dB HL
        # el margen es 80... se sostiene. Con umbral 20 y decay 40 el extra es
        # 80 >= 40 -> aguanta. Se fuerza un decay mayor al margen disponible.
        self.r.dbdata["Stat"] = [[0, 0], [200, 0], [0, 0]]
        self.run_test("ruido_blanco_contralateral", stimOn=[True, True],
                      stim=[0, 4], output=[0, 1], int=[100, 90])
        self.assertTrue(self.hand_up())
        self.assertTrue(self.r.decay_timer.isActive())
        self.assertLess(self.r.decay_timer.interval(), self.r.DECAY_HOLD_MS)

    def test_stat_fuera_de_nivel_no_cronometra(self):
        self.r.dbdata["Stat"] = [[0, 0], [200, 0], [0, 0]]
        self.run_test("ruido_blanco_contralateral", stimOn=[True, True],
                      stim=[0, 4], output=[0, 1], int=[60, 90])
        self.assertTrue(self.hand_up())          # oye el tono
        self.assertFalse(self.r.decay_timer.isActive())  # pero no es el test

    def test_stat_sin_ruido_contralateral_no_responde(self):
        self.run_test("ruido_blanco_contralateral", stimOn=[True, False],
                      stim=[0, 4], output=[0, 1], int=[100, 90])
        self.assertFalse(self.hand_up())

    def test_stat_con_ruido_muy_bajo_no_responde(self):
        self.run_test("ruido_blanco_contralateral", stimOn=[True, True],
                      stim=[0, 4], output=[0, 1], int=[100, 40])
        self.assertFalse(self.hand_up())

    def test_stat_con_el_tono_en_el_segundo_canal(self):
        # ruido en ch0, tono en ch1: antes stimOn.index(True) leia el ruido
        self.run_test("ruido_blanco_contralateral", stimOn=[True, True],
                      stim=[4, 0], output=[1, 0], int=[90, 100])
        self.assertTrue(self.hand_up())

    def test_stat_fuera_del_protocolo_de_frecuencias(self):
        # 4000 Hz (indice 6) no es frecuencia de Stat
        self.run_test("ruido_blanco_contralateral", freq=6, stimOn=[True, True],
                      stim=[0, 4], output=[0, 1], int=[100, 90])
        self.assertFalse(self.hand_up())

    # ---------- Rosemberg vs Carhart ----------
    def test_rosemberg_no_devuelve_tiempo_al_subir_el_nivel(self):
        self.run_test("rosemberg_bilateral", stimOn=[True, False],
                      stim=[0, 3], output=[0, 1], int=[30, 0])
        primero = self.r.decay_timer.interval()
        self.assertTrue(self.hand_up())
        self.assertGreater(primero, 0)

        # pasan 20 s reales y el alumno sube 10 dB
        self.r._decay_run["start"] -= 20
        self.set_audio(int=[40, 0])
        self.r.response_tone_decay("rosemberg_bilateral")
        segundo = self.r.decay_timer.interval()

        # a 40 dB el hold "bruto" es mayor que a 30, pero se le descuentan
        # los 20 s ya corridos
        bruto_40 = self.r.DECAY_HOLD_MS * (40 - 20) / 40
        self.assertAlmostEqual(segundo, bruto_40 - 20000, delta=1500)

    def test_carhart_reinicia_el_minuto_en_cada_subida(self):
        self.run_test("mano_levantada", stimOn=[True, False],
                      stim=[0, 3], output=[0, 1], int=[30, 0])
        self.set_audio(int=[40, 0])
        self.r.response_tone_decay("mano_levantada")
        bruto_40 = self.r.DECAY_HOLD_MS * (40 - 20) / 40
        self.assertAlmostEqual(self.r.decay_timer.interval(), bruto_40, delta=1)

    def test_rosemberg_agotado_el_minuto_ya_no_sostiene(self):
        self.run_test("rosemberg_bilateral", stimOn=[True, False],
                      stim=[0, 3], output=[0, 1], int=[30, 0])
        self.r._decay_run["start"] -= 120
        self.set_audio(int=[35, 0])
        self.r.response_tone_decay("rosemberg_bilateral")
        self.assertFalse(self.hand_up())

    def test_rosemberg_reinicia_al_cambiar_de_oido(self):
        self.run_test("rosemberg_bilateral", stimOn=[True, False],
                      stim=[0, 3], output=[0, 1], int=[30, 0])
        self.r._decay_run["start"] -= 30
        self.set_audio(output=[1, 0])   # ahora OI, que no decae
        self.r.response_tone_decay("rosemberg_bilateral")
        self.assertTrue(self.hand_up())
        self.assertFalse(self.r.decay_timer.isActive())

    # ---------- el reloj contra el cronómetro del alumno ----------
    def test_mover_otra_perilla_no_alarga_el_tono(self):
        # Carhart corriendo, mano arriba con un hold ya calculado
        self.run_test("mano_levantada", stimOn=[True, False],
                      stim=[0, 3], output=[0, 1], int=[30, 0])
        inicial = self.r.decay_timer.interval()

        # pasan 5 s y el alumno toca algo que no es el nivel (aca se simula
        # el recalculo que dispara cualquier cambio del equipo)
        self.r._decay_run["start"] -= 5
        self.r.response_tone_decay("mano_levantada")
        restante = self.r.decay_timer.interval()

        self.assertTrue(self.hand_up())
        self.assertAlmostEqual(restante, inicial - 5000, delta=1500)

    def test_subir_el_nivel_si_reinicia_el_minuto_en_carhart(self):
        self.run_test("mano_levantada", stimOn=[True, False],
                      stim=[0, 3], output=[0, 1], int=[30, 0])
        self.r._decay_run["start"] -= 15
        self.set_audio(int=[35, 0])
        self.r.response_tone_decay("mano_levantada")
        bruto_35 = self.r.DECAY_HOLD_MS * (35 - 20) / 40
        self.assertAlmostEqual(self.r.decay_timer.interval(), bruto_35, delta=1)

    def test_apagar_el_estimulo_reinicia_la_cuenta(self):
        self.run_test("mano_levantada", stimOn=[True, False],
                      stim=[0, 3], output=[0, 1], int=[30, 0])
        self.r._decay_run["start"] -= 30
        self.set_audio(stimOn=[False, False])
        self.r.response_tone_decay("mano_levantada")
        self.assertFalse(self.hand_up())
        self.assertEqual(self.r._decay_run, {})

        self.set_audio(stimOn=[True, False])
        self.r.response_tone_decay("mano_levantada")
        bruto_30 = self.r.DECAY_HOLD_MS * (30 - 20) / 40
        self.assertAlmostEqual(self.r.decay_timer.interval(), bruto_30, delta=1)

    def test_stat_recalculado_no_estira_el_minuto(self):
        self.r.dbdata["Stat"] = [[0, 0], [200, 0], [0, 0]]
        self.run_test("ruido_blanco_contralateral", stimOn=[True, True],
                      stim=[0, 4], output=[0, 1], int=[100, 90])
        inicial = self.r.decay_timer.interval()
        self.r._decay_run["start"] -= 10
        self.r.response_tone_decay("ruido_blanco_contralateral")
        self.assertAlmostEqual(self.r.decay_timer.interval(), inicial - 10000,
                               delta=1500)

    def test_stat_corregir_el_nivel_dentro_de_la_tolerancia_no_reinicia(self):
        self.r.dbdata["Stat"] = [[0, 0], [200, 0], [0, 0]]
        self.run_test("ruido_blanco_contralateral", stimOn=[True, True],
                      stim=[0, 4], output=[0, 1], int=[100, 90])
        self.r._decay_run["start"] -= 10
        self.set_audio(int=[105, 90])   # sigue dentro de +-5
        self.r.response_tone_decay("ruido_blanco_contralateral")
        self.assertLess(self.r.decay_timer.interval(),
                        self.r.DECAY_HOLD_MS - 9000)

    # ---------- comunes ----------
    def test_pulsado_no_sirve_para_deterioro_tonal(self):
        self.run_test("mano_levantada", stimOn=[True, False], stim=[0, 3],
                      output=[0, 1], int=[100, 0], contin=["Pulsado", "Continuo"])
        self.assertFalse(self.hand_up())

    def test_bajo_umbral_no_responde(self):
        self.run_test("mano_levantada", stimOn=[True, False], stim=[0, 3],
                      output=[0, 1], int=[10, 0])
        self.assertFalse(self.hand_up())


if __name__ == "__main__":
    unittest.main()
