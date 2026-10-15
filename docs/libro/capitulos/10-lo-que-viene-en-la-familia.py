#!/usr/bin/env python3
"""Capítulo 10 — Lo que viene en la familia.

    python3 docs/libro/capitulos/10-lo-que-viene-en-la-familia.py              casos + figuras + PDF
    python3 docs/libro/capitulos/10-lo-que-viene-en-la-familia.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/10-lo-que-viene-en-la-familia.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
10-lo-que-viene-en-la-familia.md (cada caso se nombra ahí como cap10_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()]

CASOS = [
    cuadro('gjb2', FIGURAS, od='gjb2', oi='gjb2', edad=45),
    cuadro('waardenburg', FIGURAS, od='waardenburg', oi='waardenburg', edad=45),
    cuadro('usher', FIGURAS, od='usher', oi='usher', edad=45),
    cuadro('alport', FIGURAS, od='alport', oi='alport', edad=45),
    cuadro('jervell_lange_nielsen', FIGURAS, od='jervell_lange_nielsen', oi='jervell_lange_nielsen', edad=45),
    cuadro('stickler', FIGURAS, od='stickler', oi='stickler', edad=45),
    cuadro('pendred', FIGURAS, od='pendred', oi='pendred', edad=45),
]

if __name__ == '__main__':
    Capitulo(10).generar(CASOS)
