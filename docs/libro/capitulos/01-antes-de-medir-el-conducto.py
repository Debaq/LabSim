#!/usr/bin/env python3
"""Capítulo 1 — Antes de medir: el conducto.

    python3 docs/libro/capitulos/01-antes-de-medir-el-conducto.py              casos + figuras + PDF
    python3 docs/libro/capitulos/01-antes-de-medir-el-conducto.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/01-antes-de-medir-el-conducto.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
01-antes-de-medir-el-conducto.md (cada caso se nombra ahí como cap01_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.timpanograma(), fig.reflejos()]

CASOS = [
    cuadro('tapon_cerumen', FIGURAS, od='tapon_cerumen', edad=45),
    cuadro('cuerpo_extrano_cae', FIGURAS, od='cuerpo_extrano_cae', edad=45),
    cuadro('otitis_externa', FIGURAS, od='otitis_externa', edad=45),
    cuadro('estenosis_atresia_cae', FIGURAS, od='estenosis_atresia_cae', edad=45),
    cuadro('carcinoma_cae', FIGURAS, od='carcinoma_cae', edad=45),
]

if __name__ == '__main__':
    Capitulo(1).generar(CASOS)
