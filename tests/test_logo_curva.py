"""La curva de logoaudiometría que mide el alumno (CalculateLogo, sobre
audiometria.logo_curva) con los pacientes de práctica 33-42.

Regresión de dos bugs (decisiones.md, "Logoaudiometría: la curva anclada al
SRT", 2026-10-15):
  - el 50 % caía ~22 dB sobre el umbral: un oído sano daba un SRT medido de
    20-25 dB HL con PTA 0, contra una ficha que guarda SRT = PTA;
  - el rollover colgaba del reclutamiento y era un espejo de la subida (el 37
    caía de 100 % a 0 %, el coclear 36 tenía RI 0,61) mientras el
    retrococlear 39 no tenía ninguno.

Los números de RI y los puntos de la curva están también en
labsim_backend/tests/test_case_profile.php y test_charts_vs_js.php: la app,
el PDF y el editor tienen que dar la MISMA curva para el mismo caso.
"""

import json
import os
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from audiometria.logo_curva import (cfg_oido, pct_logo,  # noqa: E402
                                    ri_medido, rollover_de_caso)
from audiometria.logoaudiometry import CalculateLogo  # noqa: E402

with open(os.path.join(RAIZ, "docs", "manual", "capturas", "casos_demo.json"),
          encoding="utf-8") as _f:
    DEMO = json.load(_f)

# RI que da el perfil de cada paciente [OD, OI]. Mismos números en
# labsim_backend/tests/test_case_profile.php (CaseProfile::rolloverDeCaso).
RI_DEMO = {
    "33": [0.0, 0.0], "34": [0.0, 0.0], "35": [0.0, 0.0],
    "36": [0.13, 0.13], "37": [0.14, 0.14], "38": [0.0, 0.15],
    "39": [0.62, 0.0], "40": [0.76, 0.76], "41": [0.0, 0.14],
    "42": [0.0, 0.0],
}

# Puntos de la curva (dB -> %) del OI del 36 (coclear, RI 0,13). Mismos
# números en test_charts_vs_js.php (PHP y el JS del editor con node).
PUNTOS_36_OI = {0: 0.0, 12.5: 0.0, 30: 57.097394, 47: 82.125125,
                70: 88.0, 90: 77.74976, 100: 76.56}


def pta(caso, side):
    """Promedio tonal del sistema: mejores 2 de 500/1000/2000 Hz, vía aérea
    (el que llena el SRT/SDT "auto" de la ficha; decisiones.md, tabla de
    parámetros clínicos)."""
    return sum(sorted(p[side] for p in caso["Aerea"][2:5])[:2]) / 2.0


def srt_medido(curva):
    """Nivel donde la curva {dB: %} pasa el 50 %, interpolado; None si no
    llega. Si ya arranca en 50 % o más, el primer nivel."""
    niveles = sorted(curva)
    if curva[niveles[0]] >= 50:
        return float(niveles[0])
    for a, b in zip(niveles, niveles[1:]):
        if curva[a] < 50 <= curva[b]:
            return a + (50 - curva[a]) / (curva[b] - curva[a]) * (b - a)
    return None


def curva_app(caso, side):
    logo = CalculateLogo(caso, caso["UMD"])
    return {int(k): v for k, v in logo.data[side].items()}


class RolloverDelPerfilTest(unittest.TestCase):
    def test_ri_de_los_pacientes_demo(self):
        for clave, esperado in RI_DEMO.items():
            self.assertEqual(rollover_de_caso(DEMO[clave]), esperado, f"paciente {clave}")

    def test_puntos_de_la_curva_iguales_al_php_y_al_js(self):
        caso = DEMO["36"]
        cfg = cfg_oido(caso, 1, rollover_de_caso(caso)[1])
        for db, pct in PUNTOS_36_OI.items():
            self.assertAlmostEqual(pct_logo(cfg, db), pct, places=5, msg=f"{db} dB")


class SrtAncladoAlPtaTest(unittest.TestCase):
    def test_oido_sano_srt_sobre_el_pta(self):
        """Paciente 33, normal: el 50 % de palabras cae en el PTA (0 dB),
        no 20-25 dB más arriba como antes."""
        for side in (0, 1):
            srt = srt_medido(curva_app(DEMO["33"], side))
            self.assertIsNotNone(srt)
            self.assertLessEqual(abs(srt - pta(DEMO["33"], side)), 6)

    def test_todo_oido_con_maximo_alto_mide_el_srt_cerca_del_pta(self):
        for clave, caso in DEMO.items():
            for side in (0, 1):
                if caso["UMD"][side]["percentage"] < 80:
                    continue
                srt = srt_medido(curva_app(caso, side))
                self.assertIsNotNone(srt, f"{clave}/{side}")
                self.assertLessEqual(abs(srt - pta(caso, side)), 6,
                                     f"paciente {clave} oído {side}: SRT {srt} vs PTA {pta(caso, side)}")

    def test_el_maximo_se_alcanza_en_la_umd_del_caso(self):
        for clave, caso in DEMO.items():
            for side in (0, 1):
                umd = caso["UMD"][side]
                if umd["int"] > 100:
                    continue
                curva = curva_app(caso, side)
                self.assertEqual(curva[umd["int"]], umd["percentage"], f"{clave}/{side}")
                self.assertEqual(max(curva.values()), umd["percentage"], f"{clave}/{side}")

    def test_conductiva_corre_la_curva_sin_bajar_el_maximo(self):
        """Paciente 34: OD con gap de ~35 dB, OI sano."""
        od, oi = curva_app(DEMO["34"], 0), curva_app(DEMO["34"], 1)
        self.assertGreaterEqual(srt_medido(od) - srt_medido(oi), 35)
        self.assertEqual(max(od.values()), 100)
        self.assertEqual(ri_medido(od, 0), 0)

    def test_por_debajo_del_sdt_no_hay_palabras(self):
        cfg = {"sdt": 10, "srt": 25, "umd_int": 55, "umd_pct": 100, "ri": 0}
        self.assertEqual(pct_logo(cfg, 10), 0)
        self.assertAlmostEqual(pct_logo(cfg, 25), 50)


class RolloverTest(unittest.TestCase):
    def test_coclear_rollover_leve(self):
        """Paciente 36, coclear con reclutamiento: antes RI 0,61."""
        for side in (0, 1):
            ri = ri_medido(curva_app(DEMO["36"], side), DEMO["36"]["UMD"][side]["int"])
            self.assertGreater(ri, 0)
            self.assertLess(ri, 0.3)

    def test_reclutamiento_no_hunde_la_curva(self):
        """Paciente 37: antes caía de 100 % a 0 % a 85 dB."""
        for side in (0, 1):
            curva = curva_app(DEMO["37"], side)
            self.assertGreater(min(v for db, v in curva.items() if db >= 45), 70)

    def test_retrococlear_rollover_y_maximo_desproporcionado(self):
        """Paciente 39 OD: máximo 52 % con PTA 17,5 dB, y RI sobre el corte
        de Jerger & Jerger (0,45)."""
        curva = curva_app(DEMO["39"], 0)
        self.assertGreaterEqual(ri_medido(curva, 55), 0.45)
        self.assertLessEqual(max(curva.values()), 60)

    def test_nunca_colapsa_a_cero(self):
        for clave, caso in DEMO.items():
            for side in (0, 1):
                umd = caso["UMD"][side]
                if umd["percentage"] <= 0:
                    continue
                curva = curva_app(caso, side)
                self.assertGreater(curva[100], 0, f"{clave}/{side}")

    def test_sin_componente_retro_ni_perdida_no_hay_rollover(self):
        for clave in ("33", "35"):
            for side in (0, 1):
                self.assertEqual(ri_medido(curva_app(DEMO[clave], side), 0), 0)


if __name__ == "__main__":
    unittest.main()
