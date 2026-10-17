#!/usr/bin/env python3
"""Capítulo 18 — El ABR que engaña.

    python3 docs/libro/capitulos/18-el-abr-que-engana.py              casos + figuras + PDF
    python3 docs/libro/capitulos/18-el-abr-que-engana.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/18-el-abr-que-engana.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
18-el-abr-que-engana.md (cada caso se nombra ahí como cap18_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Cada caso de este capítulo es un paciente de práctica corriente: lo que engaña no es el oído,
# es el registro. Las figuras del motor son el ABR limpio de ese paciente (la referencia); los
# registros mal tomados están en ilustraciones/hacer_cap18.py, calculados con el generador de LabSim.
CASOS = [
    demo(33, [fig.audiograma(), fig.abr(niveles=(80, 40, 20, 10))]),
    demo(37, [fig.audiograma(), fig.abr(niveles=(100, 80, 60))]),
    demo(36, [fig.audiograma(), fig.abr(niveles=(90, 70, 50))]),
    demo(42, [fig.audiograma(), fig.abr(niveles=(100, 80))]),
    demo(38, [fig.audiograma(), fig.abr(niveles=(80, 50, 30))]),
]

if __name__ == '__main__':
    Capitulo(18).generar(CASOS)
