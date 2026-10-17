#!/usr/bin/env python3
"""Capítulo 15 — Cuando también cae la ósea.

    python3 docs/libro/capitulos/15-cuando-tambien-cae-la-osea.py              casos + figuras + PDF
    python3 docs/libro/capitulos/15-cuando-tambien-cae-la-osea.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/15-cuando-tambien-cae-la-osea.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
15-cuando-tambien-cae-la-osea.md (cada caso se nombra ahí como cap15_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# El ABR por vía ósea llega al tope del vibrador (55 dB nHL en la app): 50, 30 y 10
ABR_AEREO = fig.abr(niveles=(80, 60, 40))
ABR_OSEO = fig.abr(niveles=(50, 30, 10), transductor='oseo')

CASOS = [
    cuadro('mixta_otitis_cronica',
           [fig.audiograma(), fig.acumetria(), fig.timpanograma(), ABR_AEREO, ABR_OSEO],
           od='mixta_otitis_cronica', grado_od='moderada', edad=52, sexo='mujer',
           anamnesis="""Tiene 52 años y trabaja de costurera. Desde niña le supura el oído derecho cada vez que se
           resfría; hace tres años la secreción no se ha cortado del todo. Con ese oído casi no oye: habla por
           teléfono con el izquierdo y la familia se queja de que sube la tele. No tiene pitido ni mareos. Hoy la
           deriva el cirujano que le propone cerrar la perforación, y quiere saber cuánto oído "de verdad" le queda
           antes de operar.""",
           historia=[(1500, 'Otorrinolaringología: perforación central amplia del tímpano derecho con otorrea mucosa; se indican gotas y control.'),
                     (60, 'Control: otoscopía con perforación seca y oído medio húmedo. Se solicita audiometría e impedanciometría antes de decidir una timpanoplastia.')],
           antecedentes=['otitis']),
    cuadro('mixta_otoesclerosis',
           [fig.audiograma(), fig.audiograma(sin_enmascarar=True), fig.timpanograma(), fig.reflejos()],
           od='mixta_otoesclerosis', oi='mixta_otoesclerosis', grado_od='moderada', grado_oi='moderada',
           edad=48, sexo='mujer',
           anamnesis="""Tiene 48 años y es profesora de básica. Hace unos quince años empezó a oír menos, primero por
           un lado y después por los dos, y notó que empeoró después de sus dos embarazos. Dice que en la sala
           de profesores, con ruido, entiende mejor que en la calma. Tiene un zumbido grave en los dos oídos, todo
           el día. Su madre y una tía usaron audífonos desde los cuarenta. Nunca ha tenido secreción ni dolor, ni mareos.""",
           historia=[(1800, 'Audiometría de salud ocupacional: hipoacusia bilateral, sin seguimiento.'),
                     (45, 'Otorrinolaringólogo: otoscopía normal bilateral y Rinne negativo en los dos oídos. Se solicita audiometría con vía ósea e impedanciometría para decidir entre cirugía y audífonos.')],
           antecedentes=['hipoacusia_familiar']),
    cuadro('colesteatoma_fistula',
           [fig.audiograma(), ABR_AEREO, ABR_OSEO],
           od='colesteatoma_fistula', grado_od='moderada', edad=38,
           anamnesis="""Tiene 38 años y es técnico en refrigeración. Desde los quince le sale pus de mal olor por el
           oído derecho de vez en cuando, y nunca se lo siguió. Hace dos semanas, al sonarse con fuerza, sintió que la
           pieza giraba unos segundos; le ha pasado de nuevo al apretarse el trago del oído y al toser. Con ese oído
           oye cada vez menos. No tiene pitido y la cara se le mueve normal.""",
           historia=[(3650, 'Otitis media crónica derecha con otorrea; tratamiento con gotas, sin control posterior.'),
                     (10, 'Servicio de urgencia: vértigo breve al sonarse la nariz y al presionar el trago. Otoscopía con secreción fétida y masa blanquecina en el cuadrante posterosuperior derecho. Se deriva a otorrinolaringología con audiometría.')],
           antecedentes=['otitis']),
    cuadro('trauma_craneal_completo',
           [fig.audiograma(), fig.acumetria(), fig.timpanograma()],
           od='trauma_craneal_completo', grado_od='moderada', edad=29,
           anamnesis="""Tiene 29 años y es repartidor en moto. Hace seis semanas chocó, sin casco, y se golpeó el lado
           derecho de la cabeza. Estuvo dos días hospitalizado; le sangró el oído derecho y desde entonces oye mucho
           menos por ahí. Dice que el sonido le llega "como con algodón" y que las voces agudas, las de mujeres y niños,
           le cuestan más. No ha tenido mareos que recuerde ni la cara caída.""",
           historia=[(45, 'Urgencia: traumatismo craneoencefálico en accidente de moto. TAC: fractura del hueso temporal derecho que respeta el laberinto; otorragia derecha, sin parálisis facial.'),
                     (10, 'Control otorrinolaringológico: hemotímpano residual derecho. Se solicita audiometría.')],
           antecedentes=['tce']),
    cuadro('fractura_transversal',
           [fig.audiograma(), fig.audiograma(sin_enmascarar=True), fig.acumetria(), fig.reflejos(), fig.abr(niveles=(100, 80, 60))],
           od='fractura_transversal', grado_od='profunda', edad=34,
           anamnesis="""Tiene 34 años y es pintor de edificios. Hace tres semanas cayó de un andamio de unos tres metros y se
           golpeó la parte de atrás de la cabeza. Desde ese día no oye nada por el oído derecho. Los primeros cinco días
           tuvo un mareo giratorio muy intenso con vómitos, que fue cediendo. Le quedó un zumbido agudo permanente en ese oído y
           algo de inestabilidad al caminar rápido.""",
           historia=[(25, 'Urgencia: caída de altura con traumatismo craneoencefálico. TAC: fractura del peñasco derecho que cruza el laberinto. Hospitalizado seis días.'),
                     (7, 'Control: otoscopía normal, membrana timpánica íntegra. Se solicita audiometría e impedanciometría.')],
           antecedentes=['tce']),
]

if __name__ == '__main__':
    Capitulo(15).generar(CASOS)
