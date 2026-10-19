#!/usr/bin/env python3
"""Herramienta H23 — Audiometría ocupacional y vigilancia del ruido.

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
    # La base ideal: audición normal de un trabajador que todavía no entra a la faena
    demo(33, [fig.audiograma(ldl=False)]),
    # La muesca de veintidós años de ruido, para leer qué es un cambio y qué es una base
    demo(37, [fig.audiograma(ldl=False)]),
]

if __name__ == '__main__':
    Capitulo('H23').generar(CASOS)
