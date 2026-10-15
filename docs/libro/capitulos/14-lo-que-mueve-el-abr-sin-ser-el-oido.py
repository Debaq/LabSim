#!/usr/bin/env python3
"""Capítulo 14 — Lo que mueve el ABR sin ser el oído.

    python3 docs/libro/capitulos/14-lo-que-mueve-el-abr-sin-ser-el-oido.py              casos + figuras + PDF
    python3 docs/libro/capitulos/14-lo-que-mueve-el-abr-sin-ser-el-oido.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/14-lo-que-mueve-el-abr-sin-ser-el-oido.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
14-lo-que-mueve-el-abr-sin-ser-el-oido.md (cada caso se nombra ahí como cap14_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.reflejos(), fig.abr()]

CASOS = [
    cuadro('toxico_metabolico', FIGURAS, od='toxico_metabolico', oi='toxico_metabolico', edad=45),
    cuadro('hipotermia_farmacos', FIGURAS, od='hipotermia_farmacos', oi='hipotermia_farmacos', edad=45),
    cuadro('bloqueo_proximal', FIGURAS, od='bloqueo_proximal', oi='bloqueo_proximal', edad=45),
    cuadro('prematuro', FIGURAS, od='prematuro', oi='prematuro', edad=2),
]

if __name__ == '__main__':
    Capitulo(14).generar(CASOS)
