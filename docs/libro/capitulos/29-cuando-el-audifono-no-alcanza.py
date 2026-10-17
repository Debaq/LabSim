#!/usr/bin/env python3
"""Capítulo 29 — Cuando el audífono no alcanza.

    python3 docs/libro/capitulos/29-cuando-el-audifono-no-alcanza.py              casos + figuras + PDF
    python3 docs/libro/capitulos/29-cuando-el-audifono-no-alcanza.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/29-cuando-el-audifono-no-alcanza.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
29-cuando-el-audifono-no-alcanza.md (cada caso se nombra ahí como cap29_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Ganancia funcional que declara el capítulo (el campo libre con audífono no sale
# del caso, ver figuras/motor/campo_libre.py): audífonos retroauriculares potentes
GANANCIA_AUTOINMUNE = {250: 30, 500: 35, 1000: 35, 2000: 30, 3000: 25, 4000: 20, 6000: 10}
# audífonos retroauriculares de potencia media, ajustados por comodidad
GANANCIA_AUN_NO = {250: 15, 500: 25, 1000: 30, 2000: 30, 3000: 25, 4000: 20, 6000: 10}

CASOS = [
    # Candidata a implante: severa bilateral con discriminación tope de 56-60 %
    cuadro('autoinmune', [fig.audiograma(), fig.logo(), fig.reflejos(), fig.teoae(),
                          fig.campo_libre(ganancia=GANANCIA_AUTOINMUNE)],
           od='autoinmune', oi='autoinmune', grado_od='severa', grado_oi='severa', edad=58, sexo='mujer',
           anamnesis="""Tiene 58 años y era profesora de enseñanza básica; hoy está con licencia. Hace tres años notó
           que oía menos por los dos oídos, y en pocas semanas ya no entendía a los alumnos del fondo de la sala. El
           otorrinolaringólogo le indicó corticoides por vía oral y mejoró un poco, pero la pérdida siguió bajando
           durante el año siguiente. Usa audífonos retroauriculares potentes en los dos oídos desde hace catorce
           meses, controlados con medición en oído real, y los usa todo el día. Aun así no sigue una conversación sin
           mirar la cara de quien le habla, no puede usar el teléfono y en la mesa familiar "se queda afuera". Dejó de
           ir a las reuniones del colegio. No tiene acúfeno ni vértigo, y nunca tuvo secreción de oídos. Su hermana
           mayor también perdió la audición en la adultez. Pregunta si existe algo más que un audífono más fuerte.""",
           historia=[(1100, 'Hipoacusia sensorioneural bilateral de progresión rápida; se solicita estudio y se indican corticoides orales en pauta decreciente.'),
                     (1000, 'Control: mejoría parcial de umbrales; se mantiene observación.'),
                     (420, 'Adaptación de audífonos retroauriculares bilaterales, con verificación en oído real.')],
           medicamentos='Levotiroxina 75 mcg al día'),
    # El caso del "aún no": moderada-severa con muy buen rendimiento con audífono
    cuadro('aun_no', [fig.audiograma(), fig.logo(), fig.campo_libre(ganancia=GANANCIA_AUN_NO)],
           od='coclear_plana', oi='coclear_plana', grado_od='moderada', grado_oi='moderada', edad=74, sexo='hombre',
           anamnesis="""Tiene 74 años y es jubilado de la minería. Hace unos diez años le dijeron que oía menos y
           hace tres meses se compró un par de audífonos en una óptica. Dice que "no le sirven": en casa, con su
           señora, se las arregla, pero en el restaurante con los hijos no sigue la conversación y el volumen del
           televisor no se arregla con el audífono. Le dijeron que "ya no hay nada más fuerte". No tiene acúfeno ni
           vértigo y no ha tenido secreción de oídos. Quiere saber si tiene que operarse de algo. Las gafas y la
           dentadura le quedan bien; se pone y se saca el audífono sin problema.""",
           historia=[(90, 'Adaptación de audífonos retroauriculares bilaterales en un comercio; ajuste por comodidad, sin medición en oído real.')],
           medicamentos='Atorvastatina 20 mg al día'),
    # Otitis crónica mixta del OI (paciente 41): dispositivo de conducción ósea
    demo(41, [fig.audiograma(), fig.logo(), fig.timpanograma()]),
    # Cófosis del OD tras paperas (paciente 42): sordera unilateral
    demo(42, [fig.audiograma(), fig.logo(), fig.reflejos(), fig.teoae()]),
]

if __name__ == '__main__':
    Capitulo(29).generar(CASOS)
