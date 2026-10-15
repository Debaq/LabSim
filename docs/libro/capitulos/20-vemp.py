#!/usr/bin/env python3
"""Capítulo 20 — VEMP.

    python3 docs/libro/capitulos/20-vemp.py              casos + figuras + PDF
    python3 docs/libro/capitulos/20-vemp.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/20-vemp.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
20-vemp.md (cada caso se nombra ahí como cap20_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.vemp(), fig.vemp(subtipo="ovemp")]

CASOS = [
    cuadro('meniere', FIGURAS, od='meniere', edad=45),
    cuadro('laberintitis', FIGURAS, od='laberintitis', edad=45),
    cuadro('schwannoma', FIGURAS, od='schwannoma', edad=45),
    cuadro('infarto_aica', FIGURAS, od='infarto_aica', edad=45),
    cuadro('otoesclerosis', FIGURAS, od='otoesclerosis', oi='otoesclerosis', edad=45),
]

if __name__ == '__main__':
    Capitulo(20).generar(CASOS)
