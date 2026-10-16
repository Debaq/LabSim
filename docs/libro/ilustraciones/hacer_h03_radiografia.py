#!/usr/bin/env python3
"""Dibuja ilustraciones/h3radiografia_audiograma.svg: la "radiografía de un
audiograma" de H3. No es de un paciente: los umbrales están elegidos para que
aparezca cada elemento que se nombra (aérea y ósea con y sin enmascarar en
los dos oídos, sin respuesta, gap y LDL con y sin molestia). Lo dibuja el
motor del libro con las mismas reglas de enmascaramiento que los casos, así
que los símbolos son los de siempre.

    python3 docs/libro/ilustraciones/hacer_h03_radiografia.py
"""
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'figuras'))
from motor import audiograma  # noqa: E402

N = None
#            125  250  500  1k   2k   3k   4k   6k   8k
AEREA_OD = [20, 25, 55, 60, 65, 70, 70, 90, 130]
AEREA_OI = [10, 10, 15, 20, 60, 70, 70, 75, 80]
OSEA_OD = [N, 20, 20, 20, 20, 65, 65, N, N]
OSEA_OI = [N, 5, 10, 15, 50, 65, 65, N, N]
LDL_OD = [N, 100, 105, 110, 115, 120, 130, N, N]
LDL_OI = [N, 95, 95, 100, 100, 105, 105, N, N]

caso = {'Aerea': [list(p) for p in zip(AEREA_OD, AEREA_OI)],
        'Osea': [list(p) for p in zip(OSEA_OD, OSEA_OI)],
        'LDL': [list(p) for p in zip(LDL_OD, LDL_OI)]}
svg = audiograma.dibujar(caso, estudio=False, ldl=True)
(AQUI / 'h3radiografia_audiograma.svg').write_text(svg, encoding='utf-8')
print('h3radiografia_audiograma.svg')
