#!/usr/bin/env python3
"""Capítulo 2 — Líquido detrás del tímpano.

    python3 docs/libro/capitulos/02-liquido-detras-del-timpano.py              casos + figuras + PDF
    python3 docs/libro/capitulos/02-liquido-detras-del-timpano.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/02-liquido-detras-del-timpano.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
02-liquido-detras-del-timpano.md (cada caso se nombra ahí como cap02_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo que se mira en todo oído medio: el umbral con su gap, la curva y los reflejos
OIDO_MEDIO = [fig.audiograma(), fig.acumetria(), fig.timpanograma(), fig.reflejos()]
SIN_ACUMETRIA = [fig.audiograma(), fig.timpanograma(), fig.reflejos()]

CASOS = [
    demo(35, OIDO_MEDIO),
    cuadro('otitis_media_aguda', OIDO_MEDIO, od='otitis_media_aguda', edad=8, sexo='mujer',
           anamnesis="""Aurora tiene 8 años y está en tercero básico. La semana pasada se resfrió y hace cinco
           días, en la noche, se despertó llorando con dolor fuerte en el oído derecho y fiebre de 38,5 °C. La
           llevaron al servicio de urgencia y está con antibiótico desde ese día. El dolor y la fiebre se le
           pasaron al segundo día, pero sigue diciendo que por el derecho oye "como dentro de una pecera". No le
           zumban los oídos ni se ha mareado. Es la primera vez que tiene una otitis. Viene con su mamá, que
           quiere saber si va a poder dar la prueba de dictado del lunes.""",
           historia=[(5, 'Servicio de urgencia: otalgia derecha y fiebre. Tímpano derecho abombado y opaco, sin perforación. Otitis media aguda derecha; se indica amoxicilina por 10 días y paracetamol.'),
                     (1, 'Otorrinolaringólogo: ya sin dolor ni fiebre; tímpano derecho todavía abombado. Solicita audiometría e impedanciometría.')],
           medicamentos='Amoxicilina (día 5 de 10); paracetamol si hay dolor'),
    cuadro('disfuncion_tubaria', SIN_ACUMETRIA, od='disfuncion_tubaria', oi='disfuncion_tubaria', edad=34, sexo='mujer', semilla=3,
           anamnesis="""Irene tiene 34 años y es profesora de básica. Tiene rinitis alérgica desde chica y vive con
           la nariz tapada. Hace unos cuatro meses, después de un resfrío, siente los dos oídos tapados, "como al
           bajar del cerro en auto", más el derecho. Al tragar le crujen y a veces se le destapan un rato si se
           sopla con la nariz apretada, pero vuelven a taparse. En la sala de clases le cuesta entender a los
           niños del fondo. No ha tenido dolor, secreción, zumbidos ni mareos. No escucha su propia voz más
           fuerte de lo normal.""",
           historia=[(120, 'Médico general: rinitis alérgica y sensación de oídos tapados. Tímpanos retraídos. Indica corticoide nasal.'),
                     (20, 'Otorrinolaringólogo: tímpanos retraídos en los dos lados, sin líquido visible; mucosa nasal pálida y edematosa. Solicita audiometría e impedanciometría con función tubaria.')],
           medicamentos='Mometasona nasal, un disparo en cada fosa al día (la usa a ratos)'),
    cuadro('barotrauma', SIN_ACUMETRIA, oi='barotrauma', edad=29, semilla=3,
           anamnesis="""Ricardo tiene 29 años y trabaja en una faena minera en turnos de siete por siete, así que
           viaja en avión cada semana. Hace tres días volvió a Santiago resfriado y en el descenso sintió un dolor
           muy fuerte en el oído izquierdo que no se le pasó tragando ni bostezando. Desde entonces tiene ese oído
           tapado y oye "apagado". El dolor ya bajó. A ratos le zumba ese oído, con un ruido grave "como de
           motor" que va y viene. No ha tenido mareo ni vértigo, y no le ha salido líquido ni sangre del oído. Nunca había tenido problemas de oídos.""",
           historia=[(3, 'Servicio de urgencia: otalgia izquierda después de un vuelo. Tímpano izquierdo violáceo, con sangre detrás de la membrana (hemotímpano), sin perforación. Analgesia y descongestionante.'),
                     (1, 'Otorrinolaringólogo: hemotímpano izquierdo, sin nistagmo ni vértigo. Solicita audiometría e impedanciometría.')],
           medicamentos='Paracetamol si hay dolor; descongestionante nasal por tres días'),
]

if __name__ == '__main__':
    Capitulo(2).generar(CASOS)
