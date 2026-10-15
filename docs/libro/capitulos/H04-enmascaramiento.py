#!/usr/bin/env python3
"""Herramienta H4 — Enmascaramiento.

    python3 docs/libro/capitulos/H04-enmascaramiento.py              figuras + PDF
    python3 docs/libro/capitulos/H04-enmascaramiento.py --solo-pdf   solo el PDF

La pieza central es el par "sin enmascarar / enmascarado" del mismo paciente:
lo que anota quien no enmascara (la curva sombra) al lado de los umbrales
reales. En el .md, la segunda figura del mismo tipo se nombra con un 2
(:::figura h4_p42 audiograma 2).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

PAR = [fig.audiograma(sin_enmascarar=True), fig.audiograma()]

CASOS = [
    # Cófosis OD: la curva sombra pura, en tonos y en palabras
    demo(42, PAR + [fig.logo(enmascarado=False), fig.logo()]),
    # Otitis crónica mixta OI: sin enmascarar la ósea, la mixta parece conductiva
    demo(41, PAR),
    # Otoesclerosis bilateral con gaps grandes: el dilema
    cuadro('dilema', [fig.audiograma()], od='otoesclerosis', oi='otoesclerosis',
           grado_od='moderada', grado_oi='moderada', edad=38, sexo='mujer'),
]

if __name__ == '__main__':
    Capitulo('H4').generar(CASOS)
