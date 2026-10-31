"""El SDT "auto" va 5 dB bajo el SRT, y la mano del SDT responde en el SDT.

Regresión del TODO 66 (decisiones.md, "Logoaudiometría: el SDT auto 5 dB
bajo el SRT", 2026-10-15): el SDT auto de la ficha era el mismo Fletcher que
el SRT, así que la mano levantada del SDT (response.py) subía en el SRT.
Clínicamente el SDT queda 8-9 dB bajo el SRT (ASHA 1988, por Chaiklin 1959).

Con los pacientes de práctica 33-42 (docs/manual/capturas/casos_demo.json):
  - SDT = Fletcher - 5 (CaseBuilder::sdtAuto), SRT = Fletcher;
  - la mano sube en el SDT, por debajo del SRT;
  - la curva de palabras no cambia (su pie va 10 dB bajo el SRT);
  - el gap de habla y el rango de enmascaramiento se miden con el SRT, así
    que bajar el SDT no los mueve;
  - la curva sombra del SDT (sub-enmascarado) también baja esos 5 dB.

Desde el 2026-10-30 la mano la decide CalculateLogo.detecta_sdt, el modelo
de las dos vías de las palabras (TODO 1): cualquier ruido enmascara, con su
CE, y el ruido de más sobreenmascara de a poco en vez de apagar la mano.

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

from audiometria.logo_curva import cfg_oido, pct_logo, rollover_de_caso  # noqa: E402
from audiometria.logoaudiometry import CalculateLogo  # noqa: E402
from audiometria.masking_params import STIM_NBN, STIM_SN, STIM_WN  # noqa: E402
from audiometria.response import ResponseAudiometry  # noqa: E402

with open(os.path.join(RAIZ, "docs", "manual", "capturas", "casos_demo.json"),
          encoding="utf-8") as _f:
    DEMO = json.load(_f)

# Espejo de CaseBuilder::SDT_BAJO_SRT_DB / SDT_MIN_DB / sdtAuto().
SDT_BAJO_SRT_DB = 5
SDT_MIN_DB = -10


def fletcher(caso, side):
    return int(sum(sorted(p[side] for p in caso["Aerea"][2:5])[:2]) / 2 // 5 * 5)


def sdt_auto(f):
    return f if f >= 130 else max(SDT_MIN_DB, f - SDT_BAJO_SRT_DB)


class FakeLabel:
    def setStyleSheet(self, value):
        pass


class FakeAudio:
    def __init__(self):
        self.lbl_response = FakeLabel()


def respuesta(caso):
    r = ResponseAudiometry(FakeAudio())
    r.set_case(caso)
    return r


def umbral(r, side, mkg=0, stim=STIM_SN):
    """Desde qué nivel (grilla de 5) levanta la mano; 130 si nunca."""
    return next((i for i in range(-10, 121, 5) if r._detecta_sdt(side, i, mkg, stim)), 130)


class SdtAutoDemoTest(unittest.TestCase):
    def test_sdt_5_bajo_el_fletcher(self):
        for clave, caso in DEMO.items():
            for side in (0, 1):
                f = fletcher(caso, side)
                self.assertEqual(caso["SRT"][side], f, f"SRT {clave}/{side}")
                self.assertEqual(caso["SDT"][side], sdt_auto(f), f"SDT {clave}/{side}")

    def test_la_mano_sube_en_el_sdt_y_no_en_el_srt(self):
        for clave, caso in DEMO.items():
            r = respuesta(caso)
            for side in (0, 1):
                if caso["SRT"][side] >= 130:
                    continue
                # con el ruido en la meseta: responde el oído estudiado
                rango = CalculateLogo(caso, caso["UMD"])._masking_range(
                    side, 1 - side, caso["SDT"][side])
                # + lo que el otro oído detecta bajo su SRT (response.py)
                det = caso["SRT"][1 - side] - caso["SDT"][1 - side]
                mkg = max(5, rango["mkg_min"] + det)
                self.assertLessEqual(mkg, rango["mkg_max"], f"paciente {clave}/{side}")
                sdt = caso["SDT"][side]
                self.assertTrue(r._detecta_sdt(side, sdt, mkg, STIM_SN), f"paciente {clave}/{side}")
                self.assertFalse(r._detecta_sdt(side, sdt - 5, mkg, STIM_SN),
                                 f"paciente {clave}/{side}")
                self.assertLess(sdt, caso["SRT"][side], f"paciente {clave}/{side}")

    def test_sombra_de_la_cofosis_baja_con_el_sdt_del_sano(self):
        # 42: OD cofótico, OI sano (SRT 0, SDT -5, óseo 0). Sin enmascarar,
        # la voz al OD la detecta el OI cuando cruza 45 dB menos lo que el
        # OI detecta bajo su umbral de habla: 45 + 0 - 5 = 40 dB.
        caso = DEMO["42"]
        r = respuesta(caso)
        self.assertEqual(umbral(r, 0), 40)
        # el sano (OI) solo: responde en su SDT, no en su SRT
        self.assertEqual(umbral(r, 1), -5)
        # con el ruido justo en el mínimo (45 - 45 - 0 + 0 + 5 = 5 a 45 dB)
        # el OD cofótico ya no responde; con menos, la sombra sí
        self.assertFalse(r._detecta_sdt(0, 45, 5, STIM_SN))
        self.assertTrue(r._detecta_sdt(0, 45, 4, STIM_SN))

    def test_cualquier_ruido_enmascara_con_su_ce(self):
        # Antes solo el Speech Noise: con otro ruido la mano bajaba siempre.
        caso = DEMO["42"]
        r = respuesta(caso)
        self.assertTrue(r._detecta_sdt(1, -5, 20, STIM_WN))     # el sano, enmascarado
        # el NBN rinde 20 dB menos que el SN (CE_LOGO): 5 no alcanza a tapar
        # la sombra del cofótico a 45, hacen falta 25
        self.assertTrue(r._detecta_sdt(0, 45, 5, STIM_NBN))
        self.assertFalse(r._detecta_sdt(0, 45, 25, STIM_NBN))

    def test_el_ruido_de_mas_sobreenmascara_de_a_poco(self):
        # 33: SDT -5 y óseo 0 en los dos. El ruido cruza al oído estudiado
        # sobre 45 + 0: el SDT sube con él, no deja de responder de golpe.
        r = respuesta(DEMO["33"])
        self.assertEqual(umbral(r, 0, 45), -5)
        self.assertEqual(umbral(r, 0, 50), 5)
        self.assertEqual(umbral(r, 0, 70), 25)

    def test_sin_sdt_en_la_ficha_no_responde(self):
        caso = copy.deepcopy(DEMO["33"])
        del caso["SDT"]
        self.assertEqual(umbral(respuesta(caso), 0), 130)

    def test_la_curva_no_depende_del_sdt_auto(self):
        for clave, caso in DEMO.items():
            ri = rollover_de_caso(caso)
            viejo = copy.deepcopy(caso)
            viejo["SDT"] = list(caso["SRT"])
            for side in (0, 1):
                nuevo_cfg = cfg_oido(caso, side, ri[side])
                viejo_cfg = cfg_oido(viejo, side, ri[side])
                for db in range(-10, 121):
                    self.assertAlmostEqual(pct_logo(nuevo_cfg, db), pct_logo(viejo_cfg, db),
                                           places=9, msg=f"paciente {clave}/{side} a {db} dB")

    def test_gap_y_enmascaramiento_no_se_mueven_con_el_sdt(self):
        for clave, caso in DEMO.items():
            viejo = copy.deepcopy(caso)
            viejo["SDT"] = list(caso["SRT"])
            a = CalculateLogo(caso, caso["UMD"])
            b = CalculateLogo(viejo, viejo["UMD"])
            self.assertEqual(a._air_bone_gap(), b._air_bone_gap(), f"paciente {clave}")
            for side in (0, 1):
                for inten in (40, 60, 80, 100):
                    self.assertEqual(a._masking_range(side, 1 - side, inten),
                                     b._masking_range(side, 1 - side, inten),
                                     f"paciente {clave}/{side} a {inten} dB")
                    self.assertEqual(a.get(side, False, inten), b.get(side, False, inten),
                                     f"paciente {clave}/{side} a {inten} dB")


if __name__ == "__main__":
    unittest.main()
