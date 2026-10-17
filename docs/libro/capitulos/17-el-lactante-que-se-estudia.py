#!/usr/bin/env python3
"""Capítulo 17 — El lactante que se estudia.

    python3 docs/libro/capitulos/17-el-lactante-que-se-estudia.py              casos + figuras + PDF
    python3 docs/libro/capitulos/17-el-lactante-que-se-estudia.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/17-el-lactante-que-se-estudia.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
17-el-lactante-que-se-estudia.md (cada caso se nombra ahí como cap17_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

TIMP = fig.timpanograma(sonda=1000)

CASOS = [
    cuadro('efusion_neonatal', [TIMP, fig.teoae(), fig.abr(niveles=(80, 60, 40, 20)),
                                fig.abr(niveles=(55, 40, 20), transductor='oseo', marcar=('V',))],
           od='efusion_neonatal', oi='efusion_neonatal', sexo='mujer', edad_meses=4,
           anamnesis="""Tiene 4 meses y viene con su mamá. Nació de término, con 3.350 g, por parto vaginal; el
           embarazo y el parto fueron normales, la mamá no tuvo infecciones ni tomó medicamentos y la guagua no
           estuvo en neonatología. El tamizaje automático del alta (AABR) refirió en los dos oídos y el retamizaje
           del primer mes también. Desde el segundo mes tiene la nariz tapada, hace ruido al mamar y toma la
           mamadera casi acostada. No ha tenido fiebre, secreción por los oídos ni llanto al tocarlos. Se
           sobresalta con los ruidos fuertes y se calma con la voz de su mamá. Nadie en la familia tiene problemas
           de audición. Llegó despierta, comió justo antes del examen y se durmió en brazos de su mamá.""",
           historia=[(115, 'Alta de la maternidad: AABR refiere OD y OI.'),
                     (90, 'Retamizaje a los 30 días: refiere en ambos oídos. Se agenda evaluación diagnóstica.')]),
    cuadro('cmv_congenito', [TIMP, fig.teoae(), fig.abr(niveles=(80, 60, 40, 20)),
                             fig.abr(niveles=(60, 40, 20), estimulo='Burst 500 Hz', marcar=('V',)),
                             fig.abr(niveles=(80, 60, 40), estimulo='Burst 2 kHz', marcar=('V',))],
           od='cmv_congenito', grado_od='moderada', edad_meses=4,
           anamnesis="""Tiene 4 meses y viene con su papá y su mamá. Nació a las 38 semanas, con 3.100 g, sin
           ningún signo al examen. Durante el embarazo la mamá tuvo, a las 14 semanas, unos días de fiebre y dolor de
           garganta que se estudiaron con exámenes de sangre compatibles con una infección reciente por citomegalovirus
           (CMV). En la maternidad se confirmó la infección congénita: PCR de CMV positiva en orina en la primera
           semana. El tamizaje automático del alta (AABR) pasó en los dos oídos, y por la infección lo citan a un
           control audiológico a los 4 meses. Mama bien, sigue la mirada y sonríe. Los papás no han notado que oiga
           peor de un lado. Nadie en la familia tiene problemas de audición.""",
           historia=[(115, 'Nacimiento a las 38 semanas; AABR del alta: pasa OD y OI.'),
                     (108, 'PCR de CMV en orina positiva: infección congénita sin síntomas. Se indica seguimiento audiológico y del desarrollo.')]),
    cuadro('rubeola_congenita', [TIMP, fig.teoae(), fig.abr(niveles=(100, 90, 80)),
                                 fig.abr(niveles=(100, 90, 80), estimulo='Burst 500 Hz', marcar=('V',)),
                                 fig.abr(niveles=(55, 40), transductor='oseo', marcar=('V',))],
           od='rubeola_congenita', oi='rubeola_congenita', grado_od='severa', grado_oi='severa',
           sexo='mujer', edad_meses=4,
           anamnesis="""Tiene 4 meses y viene con su mamá. Nació a las 37 semanas, con 2.450 g, más chica de lo
           esperado. Su mamá, que llegó hace poco al país, no estaba vacunada contra la rubéola: a las 9 semanas
           de embarazo tuvo fiebre y un sarpullido de tres días que no se estudió. Al nacer se encontraron
           cataratas en los dos ojos y un soplo del corazón (ductus arterioso persistente), y la IgM para
           rubéola salió positiva. Estuvo 9 días en neonatología. El tamizaje automático (AABR) refirió en los dos
           oídos. Los papás cuentan que no se asusta con los portazos ni gira la cabeza cuando le hablan; sí
           responde al tacto y al balanceo. Nadie en la familia tiene problemas de audición.""",
           historia=[(115, 'Nacimiento a las 37 semanas, 2.450 g; cataratas bilaterales y ductus arterioso. IgM de rubéola positiva.'),
                     (105, 'AABR refiere OD y OI. Se deriva a evaluación audiológica diagnóstica.')]),
    cuadro('asfixia_perinatal', [TIMP, fig.teoae(), fig.abr(niveles=(90, 80, 60)),
                                 fig.abr(niveles=(80,), polaridad='condensacion', marcar=('I', 'III', 'V')),
                                 fig.abr(niveles=(80,), polaridad='rarefaccion', marcar=('I', 'III', 'V'))],
           od='asfixia_perinatal', oi='asfixia_perinatal', grado_od='moderada', grado_oi='moderada', edad_meses=4,
           anamnesis="""Tiene 4 meses y viene con su mamá. Nació a las 39 semanas, con 3.200 g, por un parto vaginal
           con fórceps, tras un sufrimiento fetal agudo en el período expulsivo. Al nacer no respiraba: Apgar 2 al minuto y 4 a los 5 minutos,
           pH del cordón 6,9; lo intubaron y lo reanimaron. Por encefalopatía hipóxico-isquémica moderada recibió
           hipotermia terapéutica durante 72 horas, tuvo convulsiones que se trataron con fenobarbital y estuvo
           14 días en neonatología, 7 de ellos con gentamicina. El tamizaje automático (AABR) refirió en los dos
           oídos. Hoy toma pecho, sostiene la cabeza con dificultad y lo controla neurología por el tono
           muscular. La mamá dice que se sobresalta con los ruidos fuertes, pero que "a veces parece no escuchar".
           Nadie en la familia tiene problemas de audición.""",
           historia=[(118, 'Nacimiento por parto con fórceps tras sufrimiento fetal agudo; Apgar 2/4; hipotermia terapéutica 72 h; fenobarbital por convulsiones.'),
                     (100, 'Alta de neonatología; AABR refiere OD y OI.')],
           medicamentos='Ninguno actual'),
]

if __name__ == '__main__':
    Capitulo(17).generar(CASOS)
