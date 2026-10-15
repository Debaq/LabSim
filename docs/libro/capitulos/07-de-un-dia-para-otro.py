#!/usr/bin/env python3
"""Capítulo 7 — De un día para otro.

    python3 docs/libro/capitulos/07-de-un-dia-para-otro.py              casos + figuras + PDF
    python3 docs/libro/capitulos/07-de-un-dia-para-otro.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/07-de-un-dia-para-otro.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
07-de-un-dia-para-otro.md (cada caso se nombra ahí como cap07_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()]

CASOS = [
    cuadro('subita', FIGURAS, od='subita', edad=45),
    cuadro('laberintitis', FIGURAS, od='laberintitis', edad=45),
    cuadro('conmocion_laberintica', FIGURAS, od='conmocion_laberintica', oi='conmocion_laberintica', edad=45),
    demo(42, FIGURAS),
    cuadro('autoinmune', FIGURAS, od='autoinmune', oi='autoinmune', edad=45),
]

if __name__ == '__main__':
    Capitulo(7).generar(CASOS)
