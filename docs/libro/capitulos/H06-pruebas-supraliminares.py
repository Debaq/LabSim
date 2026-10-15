#!/usr/bin/env python3
"""Herramienta H6 — Pruebas supraliminares.

    python3 docs/libro/capitulos/<este archivo>.py              figuras + PDF
    python3 docs/libro/capitulos/<este archivo>.py --solo-pdf   solo el PDF

Una herramienta no necesita pacientes, pero puede ilustrar con algunos
(demo() o cuadro(), igual que un capítulo clínico; ver libro.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

CASOS = [
    # Reclutamiento presente: Ménière del OI (Fowler completo, SISI alto)
    demo(38, [fig.audiograma()]),
    # Sin reclutamiento y con deterioro: schwannoma del OD
    demo(39, [fig.audiograma()]),
]

if __name__ == '__main__':
    Capitulo('H6').generar(CASOS)
