"""Enmascaramiento con cualquier canal y preguntas del talkback.

Regresiones cubiertas (reporte del laboratorio, 2026-10-30):
  - el motor suponía el tono en el canal 0: con el ruido en el canal 0 y el
    tono en el 1 el paciente no levantaba la mano nunca, en aérea y en ósea;
  - un tono FM en el canal 0 se tomaba por el ruido;
  - una pregunta ("¿Me escucha?") pasaba a ser la instrucción vigente y el
    paciente dejaba de responder a los tonos; las preguntas no se contestaban;
  - mover el ruido con el tono sonando no cambiaba la respuesta;
  - Simultáneo se tomaba como OI.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audiometria.response import (ESTIMULO_ENCENDIDO, STIM_FM,  # noqa: E402
                                  STIM_NBN, STIM_TONO, ResponseAudiometry)


class FakeLabel:
    def setStyleSheet(self, value):
        self.style = value


class FakeDial:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class FakeAudio:
    def __init__(self, dial=20):
        self.lbl_response = FakeLabel()
        self.dial_talkback = FakeDial(dial)


class FakeSender:
    def __init__(self, name, text):
        self._name, self._text = name, text

    def objectName(self):
        return self._name

    def text(self):
        return self._text


def tabla(od, oi):
    return [[od, oi] for _ in range(15)]


def caso(aerea, osea, sdt=(20, 20), srt=(25, 25), ldl=100):
    return {
        "id": 1, "gender": 0, "edad": 30, "sector": "Camara_sono",
        "Aerea": aerea, "Osea": osea, "Aerea_mkg": aerea, "Osea_mkg": osea,
        "LDL": tabla(ldl, ldl), "SDT": list(sdt), "SRT": list(srt),
        "UMD": [{"int": 60, "percentage": 100}] * 2, "recruit": [False, False],
    }


F1000 = 3


class Base(unittest.TestCase):
    AEREA = tabla(90, 5)    # OD neurosensorial profundo, OI normal
    OSEA = tabla(90, 5)

    def setUp(self):
        self.r = ResponseAudiometry(FakeAudio())
        self.r.set_case(caso(self.AEREA, self.OSEA))
        self.manos = []
        sube, baja = self.r.upHand, self.r.downHand
        self.r.upHand = lambda: (self.manos.append(True), sube())
        self.r.downHand = lambda: (self.manos.append(False), baja())

    def presentar(self, comando, **audio):
        self.manos.clear()
        self.r.history_command = [comando] if isinstance(comando, str) else list(comando)
        a = self.r.data['audio']
        a.update({'test': 'Umbrales', 'freq': F1000, 'trans': [0, 0]})
        a.update(audio)
        self.r.response_()
        return self.manos[0] if self.manos else None


class CanalDelTonoTest(Base):
    """El resultado depende de por dónde va cada cosa, no del número de canal."""

    def par(self, comando, ruido, tono=70, trans_tono=0):
        normal = self.presentar(comando, stimOn=[True, True], stim=[STIM_TONO, STIM_NBN],
                                output=[0, 1], int=[tono, ruido], trans=[trans_tono, 0])
        cruzado = self.presentar(comando, stimOn=[True, True], stim=[STIM_NBN, STIM_TONO],
                                 output=[1, 0], int=[ruido, tono], trans=[0, trans_tono])
        return normal, cruzado

    def test_aerea_ruido_en_canal_0(self):
        for ruido in range(0, 121, 5):
            normal, cruzado = self.par('aerea_+_ruido', ruido)
            self.assertIsNotNone(cruzado, f"ruido {ruido}: no respondió nada")
            self.assertEqual(normal, cruzado, f"ruido {ruido} dB")

    def test_osea_ruido_en_canal_0(self):
        for ruido in range(0, 121, 5):
            normal, cruzado = self.par('vibrador_+_ruido', ruido, tono=40, trans_tono=1)
            self.assertIsNotNone(cruzado, f"ruido {ruido}: no respondió nada")
            self.assertEqual(normal, cruzado, f"ruido {ruido} dB")

    def test_el_cruzado_tambien_enmascara(self):
        """Tono 70 en el OD muerto: sin ruido lo oye el OI (sombra), con 80 de
        NBN en el OI, que va por el canal 0, deja de oírlo."""
        self.assertEqual(self.par('aerea_+_ruido', 0), (True, True))
        self.assertEqual(self.par('aerea_+_ruido', 80), (False, False))

    def test_fm_en_canal_0_es_el_tono(self):
        self.assertFalse(self.presentar(
            'aerea_+_ruido', stimOn=[True, True], stim=[STIM_FM, STIM_NBN],
            output=[0, 1], int=[70, 80]))
        self.assertTrue(self.presentar(
            'aerea_+_ruido', stimOn=[True, True], stim=[STIM_FM, STIM_NBN],
            output=[0, 1], int=[70, 0]))

    def test_colocar_fonos_con_ruido_tambien_enmascara(self):
        """El paciente no sabe qué instrucción pensaba el alumno: responde a lo
        que suena."""
        self.assertFalse(self.presentar(
            'colocar_fonos', stimOn=[True, True], stim=[STIM_NBN, STIM_TONO],
            output=[1, 0], int=[80, 70]))

    def test_ruido_en_el_mismo_oido_tapa_el_tono(self):
        """Ruido en el oído del tono: no enmascara el otro (la sombra sigue) y
        tapa el tono ahí mismo."""
        self.r.set_case(caso(tabla(5, 5), tabla(5, 5)))
        self.assertTrue(self.presentar(
            'aerea_+_ruido', stimOn=[True, True], stim=[STIM_TONO, STIM_NBN],
            output=[0, 0], int=[30, 20]))
        self.assertFalse(self.presentar(
            'aerea_+_ruido', stimOn=[True, True], stim=[STIM_TONO, STIM_NBN],
            output=[0, 0], int=[30, 60]))


class SimultaneoTest(Base):
    def test_simultaneo_contesta_el_mejor_oido(self):
        self.r.set_config(FakeSender('lbl_output_ch0', 'Simultáneo'))
        self.assertEqual(self.r.data['audio']['sim'], [True, False])
        self.assertTrue(self.presentar('colocar_fonos', stimOn=[True, False],
                                       stim=[STIM_TONO, STIM_NBN], int=[10, 0]))
        self.assertFalse(self.presentar('colocar_fonos', stimOn=[True, False],
                                        stim=[STIM_TONO, STIM_NBN], int=[0, 0]))
        self.r.set_config(FakeSender('lbl_output_ch0', 'Derecha'))
        self.assertEqual(self.r.data['audio']['sim'], [False, False])


class PreguntasNoCortanTest(Base):
    def test_tras_una_pregunta_sigue_la_instruccion(self):
        for pregunta in ('escucha', 'dejo_de_escuchar', 'molesta', 'muy_fuerte',
                         'no_entiende', 'molesto_o', 'en_qué_oído'):
            self.assertFalse(self.presentar(
                [pregunta, 'aerea_+_ruido'], stimOn=[True, True],
                stim=[STIM_NBN, STIM_TONO], output=[1, 0], int=[80, 70]), pregunta)
            self.assertTrue(self.presentar(
                [pregunta, 'aerea_+_ruido'], stimOn=[True, True],
                stim=[STIM_NBN, STIM_TONO], output=[1, 0], int=[0, 70]), pregunta)

    def test_muchas_preguntas_no_borran_la_instruccion(self):
        for _ in range(8):
            self.r.rol_player('escucha')
        self.r.history_command.append('colocar_fonos')   # la dada antes
        self.r.rol_player('colocar_fonos')
        for _ in range(8):
            self.r.rol_player('escucha')
        self.assertEqual(self.r._instruccion(), 'colocar_fonos')


class RespuestasTest(Base):
    def test_me_escucha_depende_del_talkback(self):
        self.r.obj_audio.dial_talkback = FakeDial(10)        # 50 dB HL
        self.assertEqual(self.r.respuesta_a('escucha'), 'si')
        self.r.set_case(caso(self.AEREA, self.OSEA, sdt=(90, 70)))
        self.assertIsNone(self.r.respuesta_a('escucha'))     # no la oye: calla

    def test_voz_fuerte_y_molesta(self):
        self.r.obj_audio.dial_talkback = FakeDial(19)        # 95 dB HL, LDL 100
        self.assertEqual(self.r.respuesta_a('muy_fuerte'), 'si')
        self.assertEqual(self.r.respuesta_a('molesta'), 'no')
        self.r.obj_audio.dial_talkback = FakeDial(20)
        self.assertEqual(self.r.respuesta_a('molesta'), 'si')

    def test_en_que_oido_delata_la_sombra(self):
        """Sin enmascarar, el tono del OD muerto lo oye el OI."""
        self.presentar('colocar_fonos', stimOn=[False, True],
                       stim=[STIM_NBN, STIM_TONO], output=[1, 0], int=[0, 70])
        self.assertEqual(self.r.respuesta_a('en_qué_oído'), 'elizquierdo')
        self.presentar('colocar_fonos', stimOn=[False, True],
                       stim=[STIM_NBN, STIM_TONO], output=[1, 1], int=[0, 30])
        self.assertEqual(self.r.respuesta_a('en_qué_oído'), 'elizquierdo')

    def test_en_que_oido_en_pasado(self):
        """Se pregunta después de soltar el tono: contesta por lo último.
        OD leve (30), tono a 40 en el OD: no alcanza a cruzar al OI."""
        self.r.set_case(caso(tabla(30, 5), tabla(30, 5)))
        self.r.history_command = ['colocar_fonos']
        a = self.r.data['audio']
        a.update({'test': 'Umbrales', 'freq': F1000, 'stim': [STIM_NBN, STIM_TONO],
                  'output': [1, 0], 'int': [0, 40], 'trans': [0, 0]})
        self.r.set_config(FakeSender('lbl_stimOn_ch1', ESTIMULO_ENCENDIDO))
        self.r.set_config(FakeSender('lbl_stimOn_ch1', ''))
        self.assertEqual(self.r.respuesta_a('en_qué_oído'), 'elderecho')

    def test_dejo_de_escuchar(self):
        self.presentar('colocar_fonos', stimOn=[False, False])
        self.assertEqual(self.r.respuesta_a('dejo_de_escuchar'), 'si')
        self.presentar('colocar_fonos', stimOn=[True, False],
                       stim=[STIM_TONO, STIM_NBN], output=[0, 1], int=[100, 0])
        self.assertEqual(self.r.respuesta_a('dejo_de_escuchar'), 'no')

    def test_molesto_o(self):
        self.presentar('pitos_fuertes', stimOn=[True, False],
                       stim=[STIM_TONO, STIM_NBN], output=[1, 0], int=[100, 0])
        self.assertEqual(self.r.respuesta_a('molesto_o'), 'molesta')
        self.presentar('pitos_fuertes', stimOn=[True, False],
                       stim=[STIM_TONO, STIM_NBN], output=[1, 0], int=[80, 0])
        self.assertEqual(self.r.respuesta_a('molesto_o'), 'no')

    def test_solo_si_molesta_levanta_la_mano(self):
        self.assertTrue(self.presentar('solo_si_molesta', stimOn=[True, False],
                                       stim=[STIM_TONO, STIM_NBN], int=[100, 0]))
        self.assertFalse(self.presentar('solo_si_molesta', stimOn=[True, False],
                                        stim=[STIM_TONO, STIM_NBN], int=[80, 0]))

    def test_sonidos_iguales_va_al_fowler(self):
        llamadas = []
        self.r.other_response.fowler_q = lambda n, data: llamadas.append(n)
        self.r.contestar('sonidos_iguales')
        self.r.history_command = ['dos_pitos']
        self.r.contestar('en_qué_oído')
        self.assertEqual(llamadas, [1, 2])


class RecalculaTest(Base):
    def test_subir_el_ruido_con_el_tono_sonando_baja_la_mano(self):
        self.assertTrue(self.presentar(
            'aerea_+_ruido', stimOn=[True, True], stim=[STIM_NBN, STIM_TONO],
            output=[1, 0], int=[0, 70]))
        self.manos.clear()
        self.r.set_config(FakeSender('lbl_int_ch0', '80 dB HL'))
        self.assertEqual(self.manos, [False])


if __name__ == "__main__":
    unittest.main()
