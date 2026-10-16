#!/usr/bin/env python3
"""Herramienta H10 — Potenciales evocados auditivos de tronco.

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
    # Normal: la búsqueda de umbral tal como se hace (80-60-40-20-0 y +10 a 10)
    demo(33, [fig.abr(niveles=(80, 60, 40, 20, 10, 0))]),
    # Conductiva: todo corrido, interpicos normales
    demo(34, [fig.abr(niveles=(80, 60))]),
    # Coclear de agudos: umbral del click alto, tone burst de 1 kHz casi normal
    demo(36, [fig.abr(niveles=(80, 60)),
              fig.abr(niveles=(60, 40, 20), estimulo='Burst 1', marcar=('V',))]),
    # Retrococlear: I-III y III-V largos, diferencia interaural de la V
    demo(39, [fig.abr(niveles=(80, 60))]),
    # Neuropatía: sin ABR con emisiones presentes
    demo(40, [fig.abr(niveles=(80, 60)), fig.teoae()]),
]

if __name__ == '__main__':
    Capitulo('H10').generar(CASOS)
