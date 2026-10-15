#!/usr/bin/env python3
"""Capítulo 8 — Lo que deja un tratamiento.

    python3 docs/libro/capitulos/08-lo-que-deja-un-tratamiento.py              casos + figuras + PDF
    python3 docs/libro/capitulos/08-lo-que-deja-un-tratamiento.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/08-lo-que-deja-un-tratamiento.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
08-lo-que-deja-un-tratamiento.md (cada caso se nombra ahí como cap08_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()]

CASOS = [
    cuadro('ototoxica', FIGURAS, od='ototoxica', oi='ototoxica', edad=45),
    cuadro('salicilatos', FIGURAS, od='salicilatos', oi='salicilatos', edad=45),
    cuadro('post_radioterapia', FIGURAS, od='post_radioterapia', edad=45),
]

if __name__ == '__main__':
    Capitulo(8).generar(CASOS)
