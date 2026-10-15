#!/usr/bin/env python3
"""Capítulo 2 — Líquido detrás del tímpano.

    python3 docs/libro/capitulos/02-liquido-detras-del-timpano.py              casos + figuras + PDF
    python3 docs/libro/capitulos/02-liquido-detras-del-timpano.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/02-liquido-detras-del-timpano.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
02-liquido-detras-del-timpano.md (cada caso se nombra ahí como cap02_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.timpanograma(), fig.reflejos()]

CASOS = [
    demo(35, FIGURAS),
    cuadro('otitis_media_aguda', FIGURAS, od='otitis_media_aguda', edad=45),
    cuadro('disfuncion_tubaria', FIGURAS, od='disfuncion_tubaria', oi='disfuncion_tubaria', edad=45),
    cuadro('barotrauma', FIGURAS, od='barotrauma', edad=45),
]

if __name__ == '__main__':
    Capitulo(2).generar(CASOS)
