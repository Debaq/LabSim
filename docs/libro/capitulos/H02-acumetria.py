#!/usr/bin/env python3
"""Herramienta H2 — Acumetría.

    python3 docs/libro/capitulos/H02-acumetria.py              figuras + PDF
    python3 docs/libro/capitulos/H02-acumetria.py --solo-pdf   solo el PDF

Cada paciente lleva la acumetría junto a su audiograma: el diapasón se
entiende mirando los umbrales que lo producen. Los casos se nombran en el
.md como h2_<nombre>.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

DIAPASON = [fig.acumetria(), fig.audiograma(ldl=False)]

CASOS = [
    demo(34, DIAPASON),     # otoesclerosis OD: Weber al OD, Rinne OD negativo
    demo(39, DIAPASON),     # sensorioneural OD: Weber al OI, Rinne positivo en los dos
    demo(42, DIAPASON),     # cófosis OD: Rinne falso negativo, Weber al OI
]

if __name__ == '__main__':
    Capitulo('H2').generar(CASOS)
