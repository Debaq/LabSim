#!/usr/bin/env python3
"""Capítulo 12 — El tronco.

    python3 docs/libro/capitulos/12-el-tronco.py              casos + figuras + PDF
    python3 docs/libro/capitulos/12-el-tronco.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/12-el-tronco.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
12-el-tronco.md (cada caso se nombra ahí como cap12_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma(), fig.logo(), fig.reflejos(), fig.abr()]

CASOS = [
    cuadro('esclerosis_multiple', FIGURAS, od='esclerosis_multiple', oi='esclerosis_multiple', edad=45),
    cuadro('infarto_pontino', FIGURAS, od='infarto_pontino', edad=45),
    cuadro('infarto_aica', FIGURAS, od='infarto_aica', edad=45),
    cuadro('glioma_tronco', FIGURAS, od='glioma_tronco', oi='glioma_tronco', edad=45),
    cuadro('chiari_hic', FIGURAS, od='chiari_hic', edad=45),
    cuadro('hic_idiopatica', FIGURAS, od='hic_idiopatica', oi='hic_idiopatica', edad=45),
    cuadro('siderosis', FIGURAS, od='siderosis', oi='siderosis', edad=45),
    cuadro('tec_tronco', FIGURAS, od='tec_tronco', edad=45),
]

if __name__ == '__main__':
    Capitulo(12).generar(CASOS)
