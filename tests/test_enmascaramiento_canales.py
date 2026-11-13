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


# Enmascarar = la instrucción de la prueba + el aviso del ruido (el más
# reciente primero, como history_command).
AEREA_RUIDO = ['ruido_otro_oido', 'colocar_fonos']
OSEA_RUIDO = ['ruido_otro_oido', 'colocar_vibrador']

class Base(unittest.TestCase):
    AEREA = tabla(90, 5)    # OD neurosensorial profundo, OI normal
    OSEA = tabla(90, 5)

    def setUp(self):
        self.r = ResponseAudiometry(FakeAudio())
        self.r.set_case(caso(self.AEREA, self.OSEA))
        self.r.LDL_FALSO_PROB = 0   # el falso aviso tiene sus propios tests
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
            normal, cruzado = self.par(AEREA_RUIDO, ruido)
            self.assertIsNotNone(cruzado, f"ruido {ruido}: no respondió nada")
            self.assertEqual(normal, cruzado, f"ruido {ruido} dB")

    def test_osea_ruido_en_canal_0(self):
        for ruido in range(0, 121, 5):
            normal, cruzado = self.par(OSEA_RUIDO, ruido, tono=40, trans_tono=1)
            self.assertIsNotNone(cruzado, f"ruido {ruido}: no respondió nada")
            self.assertEqual(normal, cruzado, f"ruido {ruido} dB")

    def test_el_cruzado_tambien_enmascara(self):
        """Tono 70 en el OD muerto: sin ruido lo oye el OI (sombra), con 80 de
        NBN en el OI, que va por el canal 0, deja de oírlo."""
        self.assertEqual(self.par(AEREA_RUIDO, 0), (True, True))
        self.assertEqual(self.par(AEREA_RUIDO, 80), (False, False))

    def test_fm_en_canal_0_es_el_tono(self):
        self.assertFalse(self.presentar(
            AEREA_RUIDO, stimOn=[True, True], stim=[STIM_FM, STIM_NBN],
            output=[0, 1], int=[70, 80]))
        self.assertTrue(self.presentar(
            AEREA_RUIDO, stimOn=[True, True], stim=[STIM_FM, STIM_NBN],
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
            AEREA_RUIDO, stimOn=[True, True], stim=[STIM_TONO, STIM_NBN],
            output=[0, 0], int=[30, 20]))
        self.assertFalse(self.presentar(
            AEREA_RUIDO, stimOn=[True, True], stim=[STIM_TONO, STIM_NBN],
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
        for pregunta in ('escucha', 'dejo_de_escuchar', 'muy_fuerte',
                         'molesto_o', 'en_qué_oído'):
            self.assertFalse(self.presentar(
                [pregunta, 'ruido_otro_oido', 'colocar_fonos'], stimOn=[True, True],
                stim=[STIM_NBN, STIM_TONO], output=[1, 0], int=[80, 70]), pregunta)
            self.assertTrue(self.presentar(
                [pregunta, 'ruido_otro_oido', 'colocar_fonos'], stimOn=[True, True],
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

    def test_voz_muy_fuerte(self):
        # ¿Molesta? se fusionó con ¿Muy fuerte? (2026-11-13): sí desde 10 dB
        # bajo su LDL (100)
        self.r.obj_audio.dial_talkback = FakeDial(17)        # 85 dB HL
        self.assertEqual(self.r.respuesta_a('muy_fuerte'), 'no')
        self.r.obj_audio.dial_talkback = FakeDial(18)        # 90 dB HL
        self.assertEqual(self.r.respuesta_a('muy_fuerte'), 'si')

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

    def test_pitos_fuertes_levanta_la_mano(self):
        self.assertTrue(self.presentar('pitos_fuertes', stimOn=[True, False],
                                       stim=[STIM_TONO, STIM_NBN], int=[100, 0]))
        self.assertFalse(self.presentar('pitos_fuertes', stimOn=[True, False],
                                        stim=[STIM_TONO, STIM_NBN], int=[80, 0]))

    def test_en_que_oido_con_dos_pitos_va_al_fowler(self):
        llamadas = []
        self.r.other_response.fowler_q = lambda n, data: llamadas.append(n)
        self.r.history_command = ['dos_pitos']
        self.r.contestar('en_qué_oído')
        self.assertEqual(llamadas, [2])


class LdlConLaManoTest(Base):
    """Pitos fuertes: con el tono sostenido, la mano sube al llegar a su LDL
    (100) y no dice nada (2026-11-13: "Solo si molesta" salió)."""

    def setUp(self):
        super().setUp()
        self.dichas = []
        self.r.other_response.create_voice_ = self.dichas.append
        self.r.history_command = ['pitos_fuertes']
        self.r.data['audio'].update({'test': 'Umbrales', 'freq': F1000, 'trans': [0, 0],
                                     'stim': [STIM_TONO, STIM_NBN], 'output': [0, 1],
                                     'int': [90, 0]})

    def nivel(self, db):
        self.r.set_config(FakeSender('lbl_int_ch0', f'{db} dB HL'))

    def test_subiendo_con_el_tono_sostenido_sube_la_mano(self):
        self.r.set_config(FakeSender('lbl_stimOn_ch0', ESTIMULO_ENCENDIDO))
        self.nivel(95)
        self.assertFalse(self.r.mano)
        self.nivel(100)
        self.assertTrue(self.r.mano)
        self.assertEqual(self.dichas, [])


class LdlFalsoAvisoTest(Base):
    """30 % de las veces avisa entre 80 y 90 dB, bajo su LDL (100):
    preguntándole "Molesto ¿o?" dice que solo sonó fuerte (2026-11-13)."""

    def setUp(self):
        super().setUp()
        self.r.LDL_FALSO_PROB = 1
        self.r.LDL_FALSO_DB = (85,)
        self.registro = []
        self.r.obj_audio._log = lambda accion, **p: self.registro.append((accion, p))

    def mano(self, db):
        return self.presentar('pitos_fuertes', stimOn=[True, False],
                              stim=[STIM_TONO, STIM_NBN], output=[0, 1], int=[db, 0])

    def test_avisa_en_falso_y_al_preguntar_solo_sono_fuerte(self):
        self.assertFalse(self.mano(80))
        self.assertTrue(self.mano(85))          # se equivoca
        self.assertTrue(self.mano(95))          # sin preguntarle sigue avisando
        self.assertEqual(self.r.respuesta_a('molesto_o'), 'solofuerte')
        self.assertFalse(self.r.mano)           # baja la mano
        self.assertFalse(self.mano(95))         # ya no se equivoca en esta frecuencia
        self.assertTrue(self.mano(100))         # avisa en su LDL real
        self.assertEqual(self.r.respuesta_a('molesto_o'), 'molesta')
        acciones = [a for a, _p in self.registro]
        self.assertEqual(acciones.count('audio_ldl_falso'), 1)
        self.assertEqual(acciones.count('audio_ldl_aclarado'), 1)

    def test_con_ldl_entre_80_y_90_no_es_un_error(self):
        self.r.set_case(caso(self.AEREA, self.OSEA, ldl=85))
        self.r.LDL_FALSO_DB = (85, 90)          # ninguno bajo su LDL
        self.assertFalse(self.mano(80))
        self.assertTrue(self.mano(85))          # es su LDL de verdad
        self.assertEqual(self.r.respuesta_a('molesto_o'), 'molesta')

    def test_sin_sorteo_no_se_equivoca(self):
        self.r.LDL_FALSO_PROB = 0
        self.assertFalse(self.mano(90))
        self.assertEqual(self.r.respuesta_a('molesto_o'), 'no')



class RecalculaTest(Base):
    def test_subir_el_ruido_con_el_tono_sonando_baja_la_mano(self):
        self.assertTrue(self.presentar(
            AEREA_RUIDO, stimOn=[True, True], stim=[STIM_NBN, STIM_TONO],
            output=[1, 0], int=[0, 70]))
        self.manos.clear()
        self.r.set_config(FakeSender('lbl_int_ch0', '80 dB HL'))
        self.assertEqual(self.manos, [False])


if __name__ == "__main__":
    unittest.main()
