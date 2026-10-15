#!/usr/bin/env python3
"""Capítulo 15 — Cuando también cae la ósea.

    python3 docs/libro/capitulos/15-cuando-tambien-cae-la-osea.py              casos + figuras + PDF
    python3 docs/libro/capitulos/15-cuando-tambien-cae-la-osea.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/15-cuando-tambien-cae-la-osea.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
15-cuando-tambien-cae-la-osea.md (cada caso se nombra ahí como cap15_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.timpanograma(), fig.reflejos(), fig.abr()]

CASOS = [
    cuadro('mixta_otitis_cronica', FIGURAS, od='mixta_otitis_cronica', edad=45),
    cuadro('mixta_otoesclerosis', FIGURAS, od='mixta_otoesclerosis', oi='mixta_otoesclerosis', edad=45),
    cuadro('colesteatoma_fistula', FIGURAS, od='colesteatoma_fistula', edad=45),
    cuadro('fractura_transversal', FIGURAS, od='fractura_transversal', edad=45),
    cuadro('trauma_craneal_completo', FIGURAS, od='trauma_craneal_completo', edad=45),
    cuadro('osificacion_coclear', FIGURAS, od='osificacion_coclear', oi='osificacion_coclear', edad=45),
]

if __name__ == '__main__':
    Capitulo(15).generar(CASOS)
