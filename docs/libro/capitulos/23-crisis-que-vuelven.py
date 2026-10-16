#!/usr/bin/env python3
"""Capítulo 23 — Crisis que vuelven.

    python3 docs/libro/capitulos/23-crisis-que-vuelven.py              casos + figuras + PDF
    python3 docs/libro/capitulos/23-crisis-que-vuelven.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/23-crisis-que-vuelven.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
23-crisis-que-vuelven.md (cada caso se nombra ahí como cap23_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma()]

CASOS = [

]

if __name__ == '__main__':
    Capitulo(23).generar(CASOS)
