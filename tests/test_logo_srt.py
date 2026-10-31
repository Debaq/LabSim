"""SRT con palabras compuestas (CalculateLogo.get_srt, ListWords "Compuestas").

El protocolo ORL: desde el SDT, de 5 en 5 dB, dos palabras compuestas por
nivel, hasta que perciba la mitad del mensaje. El paciente repite cada
compuesta entera, una mitad o nada: cada mitad la reconoce con la curva de
las compuestas, que pasa por el 50 % en el SRT de la ficha y es empinada
(10 %/dB). Con ese método el alumno lo encuentra en el SRT o, con mala
suerte, 5 dB arriba.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""
import json
import os
import random
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from audiometria.ListWords import GRUPOS, LETRA_SRT, MITADES, PALABRAS, ListWords  # noqa: E402
from audiometria.h_audio import normalize  # noqa: E402
from audiometria.logoaudiometry import CalculateLogo  # noqa: E402
from audiometria.masking_params import STIM_SN  # noqa: E402

with open(os.path.join(RAIZ, "docs", "manual", "capturas", "casos_demo.json"),
          encoding="utf-8") as _f:
    DEMO = json.load(_f)


def cruza(caso, side):
    """Sin SRT, o tan peor que el otro oído que la voz cruza (45 dB) antes
    de su SRT + 5: sin enmascarar contesta el otro, que es la curva sombra."""
    srt, otro = caso["SRT"][side], caso["SRT"][1 - side]
    return srt >= 130 or srt + 5 - 45 >= otro - 5


def srt_medido(logo, side, sdt, rng, mkg=0):
    """El procedimiento del protocolo, con un dado: desde el SDT, de 5 en 5,
    dos palabras por nivel; el primer nivel en que percibe la mitad del
    mensaje (2 de las 4 mitades)."""
    for nivel in range(int(sdt), 125, 5):
        pct = logo.get_srt(side, mkg > 0, nivel, mkg, STIM_SN)
        if sum(rng.random() * 100 < pct for _ in range(4)) >= 2:
            return nivel
    return 130


class CurvaSrtTest(unittest.TestCase):
    def test_50_en_el_srt_y_empinada(self):
        for clave, caso in DEMO.items():
            logo = CalculateLogo(caso, caso["UMD"])
            for side in (0, 1):
                srt = caso["SRT"][side]
                if cruza(caso, side):
                    continue   # sin enmascarar contesta el otro oído: aparte
                self.assertEqual(logo.get_srt(side, False, srt), 50.0, f"{clave}/{side}")
                self.assertEqual(logo.get_srt(side, False, srt - 5), 0.0, f"{clave}/{side}")
                self.assertEqual(logo.get_srt(side, False, srt + 5), 100.0, f"{clave}/{side}")

    def test_cofosis_sin_enmascarar_responde_el_otro_oido(self):
        # 42: OD cofótico, OI sano con SRT 0. La voz al OD cruza 45 dB: el
        # OI la repite desde 45; enmascarando el OI, el OD no repite nada.
        logo = CalculateLogo(DEMO["42"], DEMO["42"]["UMD"])
        self.assertEqual(logo.get_srt(0, False, 40), 0.0)
        self.assertEqual(logo.get_srt(0, False, 45), 50.0)
        self.assertEqual(logo.get_srt(0, True, 60, 40, STIM_SN), 0.0)

    def test_el_metodo_del_protocolo_da_el_srt_o_5_arriba(self):
        rng = random.Random(7)
        for clave, caso in DEMO.items():
            logo = CalculateLogo(caso, caso["UMD"])
            for side in (0, 1):
                srt = caso["SRT"][side]
                if cruza(caso, side):
                    continue
                medidos = {srt_medido(logo, side, caso["SDT"][side], rng) for _ in range(200)}
                self.assertEqual(medidos, {srt, srt + 5}, f"{clave}/{side}")


class ListasSrtTest(unittest.TestCase):
    def test_una_lista_de_25_compuestas_con_sus_mitades(self):
        compuestas = PALABRAS[(LETRA_SRT, "")]
        self.assertEqual(len({p.lower() for p in compuestas}), 25)
        otras = {p.lower() for (letra, _s), lista in PALABRAS.items() if letra != LETRA_SRT
                 for p in lista}
        self.assertFalse(otras & {p.lower() for p in compuestas})
        self.assertIn(("COMPUESTAS (SRT)", ((LETRA_SRT, ""),)), GRUPOS)
        self.assertEqual(set(MITADES), set(compuestas))
        for palabra, (a, b) in MITADES.items():
            # cada mitad, una palabra que empieza o termina la compuesta (al
            # escribirlas se funden: tela + araña, para + aguas, punta + pie)
            p, a, b = (normalize(x.lower()) for x in (palabra, a, b))
            self.assertTrue(p.startswith(a[:3]) and p.endswith(b[-3:]), palabra)

    def test_repite_entera_media_o_nada(self):
        caso = DEMO["40"]                                  # SRT 35 en los dos
        w = ListWords(caso)
        btn = w.findChild(type(w.grupo_listas.button(0)), f"btn_{LETRA_SRT}1")
        w.sender_btn, w.text = btn, btn.text().lower()     # "Sacapuntas"
        w.calculate(caso["SRT"][0] - 5, 0, False)
        self.assertEqual(w.pct_srt, 0.0)
        self.assertTrue(w.respuesta_srt().startswith("none"))
        w.calculate(caso["SRT"][0] + 5, 0, False)
        self.assertEqual(w.respuesta_srt(), "sacapuntas")
        w.calculate(caso["SRT"][0], 0, False)              # 50 %
        dados = iter([0.2, 0.9])                           # oye la primera, no la segunda
        self.assertEqual(w.respuesta_srt(lambda: next(dados)), "saca")
        dados = iter([0.9, 0.2])
        self.assertEqual(w.respuesta_srt(lambda: next(dados)), "puntas")


if __name__ == "__main__":
    unittest.main()
