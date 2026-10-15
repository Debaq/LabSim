#!/usr/bin/env python3
"""Capítulo 9 — Hidrops.

    python3 docs/libro/capitulos/09-hidrops.py              casos + figuras + PDF
    python3 docs/libro/capitulos/09-hidrops.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/09-hidrops.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
09-hidrops.md (cada caso se nombra ahí como cap09_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()]

CASOS = [
    demo(38, FIGURAS),
    cuadro('hidrops_retardado', FIGURAS, od='hidrops_retardado', edad=45),
]

if __name__ == '__main__':
    Capitulo(9).generar(CASOS)
