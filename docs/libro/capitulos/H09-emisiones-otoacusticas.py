#!/usr/bin/env python3
"""Herramienta H9 — Emisiones otoacústicas.

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
    # Cómo se ve una emisión presente, en los dos registros
    demo(33, [fig.teoae()]),
    # Coclear de agudos: la DPOAE se apaga donde cae el audiograma
    demo(36, [fig.dpoae()]),
    # Oído medio ocupado: la emisión no vuelve
    demo(35, [fig.dpoae()]),
    # Tamizaje en la UCIN: la TEOAE pasa y no basta
    cuadro('rn', [fig.teoae()], od='neuropatia', oi='neuropatia', grado_od='severa', grado_oi='severa',
           edad_horas=120, sexo='mujer',
           anamnesis="""Aurora nació hace cinco días, de término y por parto normal. Al segundo día se puso muy
           amarilla y la bilirrubina siguió subiendo pese a la fototerapia, así que la pasaron a la UCI neonatal y
           le hicieron una exanguinotransfusión. Hoy está estable, toma pecho y duerme bien. Antes del alta, la
           matrona pide el tamizaje auditivo. La mamá pregunta si "lo de la amarilla" le puede haber hecho algo
           en los oídos.""",
           historia=[(3, 'UCI neonatal: hiperbilirrubinemia grave sin respuesta a fototerapia; exanguinotransfusión.'),
                     (0, 'Neonatología: estable, en preparación para el alta. Solicita tamizaje auditivo.')]),
    # Emisiones presentes con ABR ausente: neuropatía (-> H10)
    demo(40, [fig.teoae(), fig.abr(niveles=(80, 60))]),
]

if __name__ == '__main__':
    Capitulo('H9').generar(CASOS)
