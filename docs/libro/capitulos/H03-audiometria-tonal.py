#!/usr/bin/env python3
"""Herramienta H3 — Audiometría tonal.

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
    # Símbolos sobre un audiograma normal, con la ósea a la vista en todo el rango
    demo(33, [fig.audiograma(estudio=False, ldl=False)]),
    # Las tres lecturas del gap: conductiva, sensorioneural y mixta
    demo(34, [fig.audiograma(ldl=False)]),
    demo(36, [fig.audiograma(ldl=False)]),
    demo(41, [fig.audiograma(ldl=False)]),
    # Sin respuesta y curva sombra (el porqué de H4)
    demo(42, [fig.audiograma(sin_enmascarar=True, ldl=False)]),
    # Ocupacional: la muesca
    demo(37, [fig.audiograma(ldl=False)]),
]

if __name__ == '__main__':
    Capitulo('H3').generar(CASOS)
