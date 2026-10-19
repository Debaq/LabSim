#!/usr/bin/env python3
"""Herramienta H21 — Prueba de audífonos.

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
    # Presbiacusia descendente: el campo libre con una ganancia funcional que declara el libro
    # (ilustrativa, NO una prescripcion): 250:5, 500:10, 1000:20, 2000:30, 3000:35, 4000:35, 6000:30
    demo(36, [fig.campo_libre(ganancia={250: 5, 500: 10, 1000: 20, 2000: 30, 3000: 35, 4000: 35, 6000: 30})]),
]

if __name__ == '__main__':
    Capitulo('H21').generar(CASOS)
