#!/usr/bin/env python3
"""Capítulo 3 — Membrana y cadena.

    python3 docs/libro/capitulos/03-membrana-y-cadena.py              casos + figuras + PDF
    python3 docs/libro/capitulos/03-membrana-y-cadena.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/03-membrana-y-cadena.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
03-membrana-y-cadena.md (cada caso se nombra ahí como cap03_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.timpanograma(), fig.reflejos()]

CASOS = [
    cuadro('perforacion', FIGURAS, od='perforacion', edad=45),
    cuadro('timpanoesclerosis', FIGURAS, od='timpanoesclerosis', edad=45),
    cuadro('disyuncion_cadena', FIGURAS, od='disyuncion_cadena', edad=45),
    cuadro('fractura_cadena', FIGURAS, od='fractura_cadena', edad=45),
    cuadro('fractura_longitudinal', FIGURAS, od='fractura_longitudinal', edad=45),
    cuadro('colesteatoma', FIGURAS, od='colesteatoma', edad=45),
    cuadro('glomus_timpanico', FIGURAS, od='glomus_timpanico', edad=45),
    demo(41, FIGURAS),
]

if __name__ == '__main__':
    Capitulo(3).generar(CASOS)
