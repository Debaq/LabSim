#!/usr/bin/env python3
"""Herramienta H5 — Logoaudiometría y campo dinámico.

    python3 docs/libro/capitulos/H05-logoaudiometria-y-campo-dinamico.py              figuras + PDF
    python3 docs/libro/capitulos/H05-logoaudiometria-y-campo-dinamico.py --solo-pdf   solo el PDF

Cuatro pacientes de práctica, uno por forma de curva: la normal y la
conductiva en la misma figura (34: OI normal, OD con otoesclerosis), la
coclear con caída pasado el máximo y campo dinámico estrecho (36), la
retrococlear con discriminación desproporcionada (39) y el par sin
enmascarar / enmascarado de una mixta (41). La cófosis (42) ya la usa H4.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

CASOS = [
    # Otoesclerosis OD: el OI normal es la curva de referencia y el OD, la misma corrida a la derecha
    demo(34, [fig.logo()]),
    # Presbiacusia: máximo bajo el 100 %, caída pasado el máximo, LDL cerca del umbral en agudos
    demo(36, [fig.audiograma(), fig.logo()]),
    # Schwannoma OD: discriminación desproporcionada para la pérdida
    demo(39, [fig.audiograma(), fig.logo()]),
    # Otitis crónica mixta OI: lo que anota quien no enmascara la logo
    demo(41, [fig.logo(enmascarado=False), fig.logo()]),
]

if __name__ == '__main__':
    Capitulo('H5').generar(CASOS)
