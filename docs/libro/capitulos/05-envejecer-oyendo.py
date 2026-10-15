#!/usr/bin/env python3
"""Capítulo 5 — Envejecer oyendo.

    python3 docs/libro/capitulos/05-envejecer-oyendo.py              casos + figuras + PDF
    python3 docs/libro/capitulos/05-envejecer-oyendo.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/05-envejecer-oyendo.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
05-envejecer-oyendo.md (cada caso se nombra ahí como cap05_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()]

CASOS = [
    demo(36, FIGURAS),
    cuadro('metabolica', FIGURAS, od='metabolica', oi='metabolica', edad=45),
]

if __name__ == '__main__':
    Capitulo(5).generar(CASOS)
