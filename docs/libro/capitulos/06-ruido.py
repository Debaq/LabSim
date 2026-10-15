#!/usr/bin/env python3
"""Capítulo 6 — Ruido.

    python3 docs/libro/capitulos/06-ruido.py              casos + figuras + PDF
    python3 docs/libro/capitulos/06-ruido.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/06-ruido.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
06-ruido.md (cada caso se nombra ahí como cap06_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()]

CASOS = [
    demo(33, FIGURAS),
    demo(37, FIGURAS),
    cuadro('trauma_acustico_agudo', FIGURAS, od='trauma_acustico_agudo', edad=45),
    cuadro('muesca_4k', FIGURAS, od='muesca_4k', oi='muesca_4k', edad=45),
]

if __name__ == '__main__':
    Capitulo(6).generar(CASOS)
