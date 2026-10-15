#!/usr/bin/env python3
"""Herramienta H8 — Audiometría pediátrica y campo libre.

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
    # Audiometría condicionada por juego en un niño de 5 años (OME bilateral)
    demo(35, [fig.audiograma(ldl=False)]),
    # Por qué el campo libre solo mide el oído mejor: hipoacusia unilateral
    # que un campo libre "normal" no vio
    cuadro('unilateral', [fig.audiograma(ldl=False)],
           oi='cmv_congenito', grado_oi='severa', edad=4, sexo='mujer',
           anamnesis="""Aurora tiene 4 años y va al jardín infantil. A los 2 años decía pocas palabras y la
           llevaron a una fonoaudióloga, que le hizo un examen de audición "con parlantes y unos juguetes que
           se prendían" y salió normal; hoy habla bien para su edad. Este año la educadora notó que, cuando la
           llaman desde su izquierda, mira hacia el lado contrario. Para hablar por teléfono con su abuela se
           pone el celular siempre en la oreja derecha. Nunca ha tenido otitis ni dolor de oídos. En el
           embarazo, a los tres meses, la mamá tuvo fiebre y mucho cansancio por unos días, "como una gripe".""",
           historia=[(1460, 'Tamizaje auditivo neonatal con emisiones otoacústicas: pasa en ambos oídos.'),
                     (730, 'Fonoaudióloga, por retraso del lenguaje: audiometría por refuerzo visual en campo '
                           'libre, respuestas en 20 a 25 dB HL de 500 a 4.000 Hz. Se informa "audición normal".'),
                     (45, 'Pediatra, control sano: la educadora refiere que no localiza cuando la llaman por la '
                          'izquierda. Deriva a evaluación auditiva.')]),
]

if __name__ == '__main__':
    Capitulo('H8').generar(CASOS)
