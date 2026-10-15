#!/usr/bin/env python3
"""Capítulo 11 — Asimetría que no cierra.

    python3 docs/libro/capitulos/11-asimetria-que-no-cierra.py              casos + figuras + PDF
    python3 docs/libro/capitulos/11-asimetria-que-no-cierra.py --solo-pdf   solo el PDF

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
11-asimetria-que-no-cierra.md (cada caso se nombra ahí como cap11_<nombre>).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402

# Lo que se mira en todos los casos retrococleares del capítulo
RETRO = [fig.audiograma(), fig.logo(), fig.reflejos(), fig.abr(niveles=(80, 60, 40))]

CASOS = [
    demo(39, [fig.audiograma(), fig.logo(), fig.timpanograma(), fig.reflejos(),
              fig.teoae(), fig.dpoae(), fig.abr(niveles=(80, 60, 40, 20))]),
    cuadro('schwannoma', RETRO + [fig.vemp()], od='schwannoma', grado_od='moderada', edad=52, sexo='mujer'),
    cuadro('nf2', RETRO, od='nf2', oi='nf2', grado_od='moderada', grado_oi='leve', edad=24),
    cuadro('angulo', RETRO, oi='tumor_angulo', grado_oi='leve', edad=61),
    cuadro('microvascular', RETRO, od='compresion_microvascular', edad=47, sexo='mujer'),
    cuadro('retrococlear', RETRO, oi='sensorioneural', grado_oi='moderada', edad=66),
]

if __name__ == '__main__':
    Capitulo(11).generar(CASOS)
