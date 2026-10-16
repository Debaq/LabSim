#!/usr/bin/env python3
"""Capítulo 3 — Membrana y cadena.

    python3 docs/libro/capitulos/03-membrana-y-cadena.py              casos + figuras + PDF
    python3 docs/libro/capitulos/03-membrana-y-cadena.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/03-membrana-y-cadena.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
03-membrana-y-cadena.md (cada caso se nombra ahí como cap03_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.

La fractura longitudinal del peñasco y la fractura de cadena no tienen caso
propio: la primera es la historia del caso de disyunción (3.3) y la segunda
su diagnóstico diferencial. El glomus timpánico va solo en el texto (no hay
otoscopía de banco y el capítulo ya era largo).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo que se mira en todo oído medio: el gap y la curva con su volumen. Los
# reflejos van como figura solo en la perforación; en el resto, en el texto.
OIDO_MEDIO = [fig.audiograma(), fig.timpanograma()]

CASOS = [
    cuadro('perforacion', OIDO_MEDIO + [fig.reflejos()], od='perforacion', edad=36, sexo='mujer', semilla=11,
           anamnesis="""Lucía tiene 36 años y es técnica en enfermería en un CESFAM. De niña tuvo muchas otitis y
           el oído derecho le "supuraba" cada invierno. De adulta le ha supurado tres o cuatro veces, siempre
           después de que le entra agua; la última fue hace más de un año y se le pasó con gotas. Desde entonces
           el oído está seco. Siente que por el derecho oye menos, sobre todo cuando le hablan bajo o por
           teléfono, que siempre se pone en el izquierdo. No le zumban los oídos, no le duelen y no se ha
           mareado. Viene porque el otorrino le propuso operarse para cerrar el tímpano y quiere saber cuánto
           oye antes de decidir. Le gustaría volver a nadar con sus hijos.""",
           historia=[(400, 'Médico general: otorrea derecha después de bañarse en piscina. Gotas óticas con antibiótico por siete días.'),
                     (30, 'Otorrinolaringólogo: perforación central amplia de la membrana derecha, seca, sin colesteatoma. Membrana izquierda normal. Plantea timpanoplastia; solicita audiometría e impedanciometría con función tubaria.')],
           antecedentes=['otitis']),
    cuadro('timpanoesclerosis', OIDO_MEDIO, oi='timpanoesclerosis', edad=31, sexo='mujer', semilla=12,
           anamnesis="""Daniela tiene 31 años y trabaja en un call center con un audífono de diadema. Hace dos o
           tres años se dio cuenta de que por el oído izquierdo oye "más lejos", y por eso se pone el auricular
           en el derecho. No sabe decir cuándo empezó: cree que ha ido de a poco. De niña tuvo otitis a
           repetición y le pusieron tubos en los dos oídos a los 4 años. Desde entonces no ha tenido dolor ni
           secreción. No le zumban los oídos ni se marea.""",
           historia=[(60, 'Otorrinolaringólogo: membrana derecha normal; membrana izquierda íntegra, con una placa blanca extensa en su mitad posterior. Solicita audiometría e impedanciometría.')],
           antecedentes=['otitis'], cirugias='Tubos de ventilación en los dos oídos a los 4 años.'),
    cuadro('disyuncion_cadena', OIDO_MEDIO, od='disyuncion_cadena', grado_od='moderada', edad=23, semilla=16,
           anamnesis="""Diego tiene 23 años y estudia ingeniería. Hace cuatro meses se cayó de la bicicleta y se
           golpeó el lado derecho de la cabeza; estuvo inconsciente unos minutos y le salió sangre por el oído
           derecho. Lo hospitalizaron dos días. Le dijeron que tenía una fisura en el hueso del oído y que oiría
           mejor cuando se reabsorbiera la sangre, pero sigue oyendo "como con algodón" por el derecho. A veces
           le zumba ese oído, un ruido grave que va y viene. No ha tenido vértigo, la cara se le mueve bien y no
           le ha vuelto a salir nada del oído.""",
           historia=[(120, 'Servicio de urgencia: traumatismo encefalocraneano con pérdida de conciencia breve y otorragia derecha. TC: fractura longitudinal del temporal derecho que respeta la cápsula ótica; hemotímpano. Sin parálisis facial.'),
                     (90, 'Otorrinolaringólogo: hemotímpano derecho en reabsorción. Control en dos meses.'),
                     (14, 'Otorrinolaringólogo: membrana derecha íntegra, sin sangre detrás. Persiste la hipoacusia derecha. Solicita audiometría e impedanciometría.')],
           antecedentes=['tce']),
    cuadro('colesteatoma', OIDO_MEDIO, oi='colesteatoma', edad=19, semilla=14,
           anamnesis="""Sergio tiene 19 años y trabaja como garzón. Desde los 15 años le sale de vez en cuando una
           secreción del oído izquierdo, espesa y con muy mal olor, que se le pasa con gotas y vuelve a los
           meses. La última vez fue hace tres semanas y ya está seco. Siente que cada año oye un poco menos por
           ese lado, y a veces le zumba, un ruido grave que va y viene. No le duele, no ha tenido vértigo y la
           cara se le mueve bien. Le da vergüenza el olor y por eso nunca había consultado en serio.""",
           historia=[(21, 'Médico general: otorrea fétida izquierda. Gotas óticas con antibiótico; deriva a otorrinolaringología.'),
                     (7, 'Otorrinolaringólogo: oído izquierdo seco; costra y material blanco en el ático, con el resto de la membrana retraído. Membrana derecha normal. Solicita audiometría, impedanciometría y TC de oídos.')],
           antecedentes=['otitis']),
    demo(41, OIDO_MEDIO),
]

if __name__ == '__main__':
    Capitulo(3).generar(CASOS)
