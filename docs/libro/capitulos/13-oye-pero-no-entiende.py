#!/usr/bin/env python3
"""Capítulo 13 — Oye pero no entiende.

    python3 docs/libro/capitulos/13-oye-pero-no-entiende.py              casos + figuras + PDF
    python3 docs/libro/capitulos/13-oye-pero-no-entiende.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/13-oye-pero-no-entiende.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
13-oye-pero-no-entiende.md (cada caso se nombra ahí como cap13_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.reflejos(), fig.abr()]

CASOS = [
    demo(40, FIGURAS),
    cuadro('neuropatia_hereditaria', FIGURAS, od='neuropatia_hereditaria', oi='neuropatia_hereditaria', edad=45),
    cuadro('kernicterus', FIGURAS, od='kernicterus', oi='kernicterus', edad=45),
    cuadro('leucodistrofia', FIGURAS, od='leucodistrofia', oi='leucodistrofia', edad=45),
]

if __name__ == '__main__':
    Capitulo(13).generar(CASOS)
