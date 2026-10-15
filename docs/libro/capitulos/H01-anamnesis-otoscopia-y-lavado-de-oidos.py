#!/usr/bin/env python3
"""Herramienta H1 — Anamnesis, otoscopía y lavado de oídos.

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
    demo(35, []),   # Benjamín, 5 años, con su mamá: ejemplo de anamnesis de un niño (sin figuras)
]

if __name__ == '__main__':
    Capitulo('H1').generar(CASOS)
