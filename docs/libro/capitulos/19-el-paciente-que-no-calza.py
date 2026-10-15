#!/usr/bin/env python3
"""Capítulo 19 — El paciente que no calza.

    python3 docs/libro/capitulos/19-el-paciente-que-no-calza.py              casos + figuras + PDF
    python3 docs/libro/capitulos/19-el-paciente-que-no-calza.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/19-el-paciente-que-no-calza.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
19-el-paciente-que-no-calza.md (cada caso se nombra ahí como cap19_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.abr()]

CASOS = [

]

if __name__ == '__main__':
    Capitulo(19).generar(CASOS)
