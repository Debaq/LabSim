#!/usr/bin/env python3
"""Herramienta H12 — VEMP.

    python3 docs/libro/capitulos/<este archivo>.py              figuras + PDF
    python3 docs/libro/capitulos/<este archivo>.py --solo-pdf   solo el PDF

Una herramienta no necesita pacientes, pero puede ilustrar con algunos
(demo() o cuadro(), igual que un capítulo clínico; ver libro.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

CASOS = [
    # Normal: cVEMP y oVEMP de los dos oídos, simétricos
    demo(33, [fig.vemp(), fig.vemp(subtipo='ovemp')]),
    # Ménière del OI: el cVEMP (sáculo) cae y el oVEMP (utrículo) se conserva
    demo(38, [fig.vemp(), fig.vemp(subtipo='ovemp')]),
    # Cófosis del OD tras parotiditis: VEMP del OD casi plano
    demo(42, [fig.vemp()]),
    # Otoesclerosis del OD: el gap aéreo-óseo apaga el VEMP por vía aérea
    demo(34, [fig.vemp(), fig.audiograma()]),
]

if __name__ == '__main__':
    Capitulo('H12').generar(CASOS)
