#!/usr/bin/env python3
"""Capítulo 17 — El lactante que se estudia.

    python3 docs/libro/capitulos/17-el-lactante-que-se-estudia.py              casos + figuras + PDF
    python3 docs/libro/capitulos/17-el-lactante-que-se-estudia.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/17-el-lactante-que-se-estudia.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
17-el-lactante-que-se-estudia.md (cada caso se nombra ahí como cap17_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.timpanograma(sonda=1000), fig.teoae(), fig.abr(niveles=(80, 60, 40, 20))]

CASOS = [
    cuadro('cmv_congenito', FIGURAS, od='cmv_congenito', edad_meses=4),
    cuadro('rubeola_congenita', FIGURAS, od='rubeola_congenita', oi='rubeola_congenita', edad_meses=4),
    cuadro('asfixia_perinatal', FIGURAS, od='asfixia_perinatal', oi='asfixia_perinatal', edad_meses=4),
]

if __name__ == '__main__':
    Capitulo(17).generar(CASOS)
