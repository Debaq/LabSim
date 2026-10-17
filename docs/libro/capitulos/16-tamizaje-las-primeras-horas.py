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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

TAMIZ = [fig.teoae(), fig.abr(niveles=(35,))]
TAMIZ_Y_ABR = [fig.teoae(), fig.abr(niveles=(80, 35))]

CASOS = [
    cuadro('normal', TAMIZ, od='normal', oi='normal', edad_horas=10, sexo='mujer',
           anamnesis="""Recién nacida de 10 horas, primera hija de una mujer de 28 años, en la sala de maternidad.
           Embarazo controlado de 39 semanas, parto vaginal sin complicaciones, 3.350 g, Apgar 9 y 9. La madre
           no tuvo fiebre ni infecciones en el embarazo y no tomó medicamentos. No hay sordera en la familia.
           La enfermera cuenta que la niña lleva un rato tranquila después de mamar y que el equipo de
           tamizaje está listo en la sala.""",
           antecedentes=[]),
    cuadro('uci', TAMIZ_Y_ABR, od='kernicterus', oi='kernicterus', grado_od='moderada', grado_oi='moderada',
           edad_horas=168, sexo='hombre',
           anamnesis="""Recién nacido de 7 días, hospitalizado en la unidad de cuidados intensivos neonatales desde
           su segundo día de vida. Nació a las 34 semanas, con 2.280 g. A los tres días tuvo una ictericia muy
           intensa que no cedió con fototerapia y se le hizo una exanguinotransfusión. Recibió gentamicina por
           una sospecha de infección, que se descartó. Hoy está estable, se alimenta bien y está en la cuna
           por primera vez, a dos días del alta. La madre, de 31 años, pregunta si el examen "duele".""",
           historia=[(7, 'Nacimiento a las 34 semanas, 2.280 g, ingreso a UCI neonatal.'),
                     (4, 'Hiperbilirrubinemia severa: exanguinotransfusión.')],
           antecedentes=['ototoxicos'], medicamentos='Gentamicina por 7 días, ya suspendida'),
    cuadro('riesgo', TAMIZ, od='normal', oi='normal', edad_horas=50, sexo='hombre',
           anamnesis="""Recién nacido de 50 horas, listo para el alta. Nació a las 40 semanas, parto vaginal, 3.620 g,
           sin problemas. Su madre, de 26 años, tuvo una infección por citomegalovirus en el segundo trimestre,
           documentada con una seroconversión en los exámenes del embarazo. A él se le tomó hoy una muestra de
           saliva para buscar el virus; el resultado todavía no llega. Está tranquilo y mamó hace una hora.""",
           historia=[(0, 'Muestra de saliva para PCR de citomegalovirus, resultado pendiente.')]),
    cuadro('efusion', TAMIZ_Y_ABR + [fig.timpanograma(sonda=1000)], od='efusion_neonatal', oi='efusion_neonatal',
           edad_horas=480, sexo='mujer',
           anamnesis="""Lactante de 20 días que viene de su casa con su madre. Nació a las 38 semanas por cesárea, sin
           complicaciones, y se fue de alta a los dos días. En la maternidad el tamizaje con emisiones
           otoacústicas "no pasó" en el oído derecho y le dijeron que volviera. Hace una semana la ven en el
           consultorio: tuvo congestión nasal, pero sin fiebre ni secreción por los oídos. Se alimenta bien y
           se sobresalta con los ruidos fuertes. No hay sordera en la familia.""",
           historia=[(18, 'Alta de la maternidad; tamizaje con OEA: refiere en el oído derecho.'),
                     (7, 'Control en consultorio: congestión nasal leve, sin fiebre.')]),
]

if __name__ == '__main__':
    Capitulo(16).generar(CASOS)
