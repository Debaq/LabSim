#!/usr/bin/env python3
"""Capítulo 16 — Tamizaje: las primeras horas.

    python3 docs/libro/capitulos/16-tamizaje-las-primeras-horas.py              casos + figuras + PDF
    python3 docs/libro/capitulos/16-tamizaje-las-primeras-horas.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/16-tamizaje-las-primeras-horas.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
16-tamizaje-las-primeras-horas.md (cada caso se nombra ahí como cap16_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.timpanograma(sonda=1000), fig.teoae(), fig.abr(niveles=(80, 60, 40, 20))]

CASOS = [
    cuadro('normal', FIGURAS, od='normal', oi='normal', edad_horas=24),
]

if __name__ == '__main__':
    Capitulo(16).generar(CASOS)
