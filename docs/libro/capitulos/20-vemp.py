#!/usr/bin/env python3
"""Capítulo 20 — VEMP.

    python3 docs/libro/capitulos/20-vemp.py              casos + figuras + PDF
    python3 docs/libro/capitulos/20-vemp.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/20-vemp.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
20-vemp.md (cada caso se nombra ahí como cap20_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

VEMPS = [fig.vemp(), fig.vemp(subtipo="ovemp")]

# Cuatro pacientes, cada uno enseña algo distinto del VEMP. El infarto de la AICA
# (cap. 12, caso 12.2) no se repite: da el mismo VEMP que la laberintitis y se discute
# en el texto. La neuritis de la rama superior no es un cuadro de LabSim: la figura
# "ramas" (ilustraciones/hacer_cap20.py) la arma con el motor del VEMP.
CASOS = [
    cuadro('meniere', [fig.audiograma()] + VEMPS, od='meniere', edad=45, semilla=3,
           anamnesis="""Tiene 45 años y es chofer de buses interurbanos. Hace cinco meses empezó con crisis: primero
           siente el oído derecho "tapado" y un zumbido grave, como de motor; después todo gira, con náuseas y
           vómitos, durante unas tres horas. Al terminar queda agotado y el oído derecho oye menos; en los días
           siguientes mejora en parte. Lleva cuatro crisis y la última fue hace tres semanas. Entre una y otra oye
           casi igual, pero el zumbido grave no se le ha ido. No tiene dolor ni secreción de oídos, no ha tenido
           golpes en la cabeza y le da miedo manejar por si una crisis lo pilla en la ruta.""",
           historia=[(150, 'Primera crisis: tapazón y zumbido del oído derecho, giro de unas tres horas con vómitos.'),
                     (21, 'Cuarta crisis, la última; el oído derecho quedó más sordo unos días.'),
                     (14, 'Otorrinolaringólogo: otoscopía normal; se piden audiometría y VEMP entre crisis.')]),
    cuadro('laberintitis', [fig.audiograma()] + VEMPS, od='laberintitis', grado_od='severa',
           edad=34, sexo='mujer',
           anamnesis="""Tiene 34 años y es contadora. Hace doce días tuvo un resfrío con fiebre baja. Al quinto día
           despertó con el cuarto girando y vómitos, y no pudo levantarse por dos días. Desde esa mañana oye muy
           poco por el oído derecho, "como si lo tuviera tapado con algodón", y el teléfono por ese lado no le sirve.
           El giro cedió, pero camina "como en un barco" y se marea si gira rápido la cabeza. No tiene dolor ni
           secreción de oídos, no tiene zumbido, y no ha tenido dolor de cabeza intenso, visión doble ni
           dificultad para hablar o para tragar. Nunca había tenido algo parecido.""",
           historia=[(12, 'Resfrío con fiebre baja durante tres días.'),
                     (7, 'Servicio de urgencia: vértigo intenso con vómitos y sordera del oído derecho; se trata el síntoma y se indica reposo.'),
                     (3, 'Control: persiste la sordera; se deriva a otorrinolaringología con audiometría y VEMP.')]),
    cuadro('schwannoma', [fig.audiograma(), fig.timpanograma()] + VEMPS, od='schwannoma', grado_od='leve',
           edad=41, sexo='mujer',
           anamnesis="""Tiene 41 años y es profesora de enseñanza básica. Hace más de un año nota que por el oído
           derecho la voz del teléfono "suena menos nítida" y se cambia de lado. De noche, o al girar rápido en
           el patio del colegio, se siente "un poco inestable", sin giros ni vómitos. No tiene zumbido, ni
           plenitud, ni dolor de oídos. Nunca ha tenido crisis de vértigo, golpes en la cabeza ni exposición a ruido.""",
           historia=[(400, 'Primera vez que nota la voz menos nítida por el oído derecho.'),
                     (45, 'Médico general: otoscopía normal; se solicita audiometría.')]),
    cuadro('otoesclerosis', [fig.audiograma(), fig.timpanograma()] + VEMPS, od='otoesclerosis', oi='otoesclerosis',
           edad=38, sexo='mujer', antecedentes=['hipoacusia_familiar'],
           anamnesis="""Tiene 38 años y es cajera de supermercado. Hace unos cuatro años, poco después de su segundo
           embarazo, empezó a oír menos por los dos oídos, un poco más por el derecho; con ruido de fondo se defiende
           mejor que en silencio. Tiene un zumbido constante en los dos oídos. Desde hace unos meses, al agacharse
           y levantarse rápido o al caminar entre mucha gente, se siente "inestable" por unos segundos. No ha
           tenido crisis de vértigo ni secreción de oídos. Su madre usa audífonos desde los 40 años.""",
           historia=[(1500, 'Primera vez que nota que oye menos, después del segundo embarazo.'),
                     (30, 'Médico general: por la inestabilidad se solicita un VEMP; no hay audiometría reciente.')]),
]

if __name__ == '__main__':
    Capitulo(20).generar(CASOS)
