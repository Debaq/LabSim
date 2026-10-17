#!/usr/bin/env python3
"""Capítulo 23 — Crisis que vuelven.

    python3 docs/libro/capitulos/23-crisis-que-vuelven.py              casos + figuras + PDF
    python3 docs/libro/capitulos/23-crisis-que-vuelven.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/23-crisis-que-vuelven.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
23-crisis-que-vuelven.md (cada caso se nombra ahí como cap23_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.

LabSim no hace examen vestibular: lo que el libro entrega de calórica, vHIT y
VNG de cada caso está escrito en el .md. Del oído, LabSim da audiograma,
logoaudiometría, electrococleografía y VEMP. Un Ménière con 'meniere' lleva
la curva ascendente de la etapa inicial; el avanzado se arma con
'coclear_plana' (el motor no modela el hidrops en esa etapa). Las
audiometrías anteriores de Ignacio van en la historia y en el esquema
ilustraciones/cap23-evolucion.svg (hacer_cap23.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, fig  # noqa: E402

CASOS = [
    cuadro('meniere_avanzado', [fig.audiograma(), fig.logo(), fig.ecochg(), fig.vemp()],
           od='coclear_plana', grado_od='moderada', edad=63, sexo='hombre',
           anamnesis="""Tiene 63 años y es jubilado de una empresa de buses, donde fue jefe de taller. Hace seis años
           tuvo su primera crisis: de un momento a otro todo giró, vomitó y estuvo cuatro horas sin poder levantarse;
           antes sintió el oído derecho "tapado" y un zumbido grave. Siguieron varias crisis iguales en los meses
           siguientes, con la audición del derecho que subía y bajaba. Hoy las crisis son más espaciadas, una cada dos
           o tres meses, pero la audición ya no vuelve: oye menos por el derecho todo el tiempo y el zumbido, que antes
           era un motor lejano, es hoy más bien un pito agudo que va y viene. Hace catorce meses, sin aviso, cayó dos
           veces al suelo estando de pie en la cocina: "como si me tiraran de las piernas", sin perder el conocimiento,
           sin mareo antes ni después y sin dolor de cabeza. Se levantó solo a los segundos. Desde entonces camina
           pendiente del piso y ya no sube a escalas. Le han indicado dieta baja en sal y no ha recibido tratamientos
           en el oído.""",
           historia=[(2190, 'Urgencia: primera crisis de vértigo con vómitos y oído derecho tapado; se trata con antieméticos.'),
                     (1800, 'Otorrinolaringología: audiometría con hipoacusia sensorioneural OD ascendente, promedio de 500 a 3.000 Hz de 24 dB. Se diagnostica enfermedad de Ménière y se indica dieta baja en sal y betahistina.'),
                     (1100, 'Control: crisis frecuentes; audiometría con la curva aplanada, promedio de 40 dB.'),
                     (420, 'Urgencia: dos caídas bruscas sin pérdida de conciencia; tomografía de cerebro sin hallazgos.'),
                     (30, 'Otorrinolaringología: audiometría con promedio de 55 dB en el OD. Se solicita evaluación audiológica completa y vestibular.')],
           antecedentes=['hta'], medicamentos='Betahistina 24 mg cada 12 horas; hidroclorotiazida 25 mg al día'),
    cuadro('meniere_bilateral', [fig.audiograma(), fig.logo(), fig.ecochg(), fig.vemp()],
           od='meniere', grado_od='leve', oi='coclear_plana', grado_oi='moderada', edad=58, sexo='mujer', semilla=5,
           anamnesis="""Tiene 58 años y es profesora de básica. Desde hace doce años tiene crisis de vértigo con el oído
           izquierdo tapado y un zumbido grave; con los años ese oído oye cada vez menos y ya no se recupera. Hace dos
           años empezó a notar lo mismo en el derecho: plenitud, un zumbido grave que ahora es permanente y días en que
           "se apaga" la audición. Las crisis duran entre dos y cuatro horas y en el último año han vuelto a ser más
           frecuentes. Hace tres meses cayó de golpe al suelo en el patio del colegio, sin aviso y sin perder el
           conocimiento. En otro centro le propusieron una inyección de gentamicina en el oído izquierdo y ella no sabe
           si aceptar: "si ya oigo poco por ese lado, ¿qué me pasa si me lo apagan?". Le molestan los ruidos fuertes
           en los dos oídos.""",
           historia=[(4380, 'Otorrinolaringología: Ménière OI; hipoacusia sensorioneural OI de graves y medias.'),
                     (730, 'Control: fluctuación de la audición también en el OD; audiometría con 30 a 40 dB en el OD.'),
                     (90, 'Urgencia: caída brusca sin pérdida de conciencia; sin hallazgos neurológicos.'),
                     (20, 'Otorrinolaringología: se plantea gentamicina intratimpánica OI; solicita evaluación audiológica y vestibular antes de decidir.')],
           medicamentos='Betahistina 24 mg cada 12 horas'),
    cuadro('migrana_vestibular', [fig.audiograma(), fig.teoae(), fig.ecochg(), fig.vemp()],
           od='normal', oi='normal', edad=34, sexo='mujer',
           anamnesis="""Tiene 34 años y es diseñadora gráfica. Desde los 16 años tiene jaquecas que le laten de un lado,
           con luz y ruido que le molestan, y a veces ve luces en zigzag antes. Hace cinco años empezó con otro tipo de
           crisis: una sensación de mareo, como estar en un barco, a veces con giro, que dura desde una hora hasta dos
           días y se acompaña de náuseas. En algunas le duele la cabeza y en otras no, pero en todas le molesta la luz y
           no soporta el ruido. Las desencadenan la falta de sueño, la regla y los olores fuertes; los pasillos del
           supermercado y las pantallas con movimiento le dan malestar entre crisis. En los episodios no ha notado
           pérdida de audición, tapón ni zumbido. Tres veces le dijeron "laberintitis" y le dieron antivertiginosos,
           sin efecto. Ha tenido unas veinte crisis en total.""",
           historia=[(1800, 'Urgencia: mareo intenso con vómitos, tratado como laberintitis; alta con dimenhidrinato.'),
                     (700, 'Médico general: nuevo episodio de mareo; otoscopía normal.'),
                     (60, 'Neurólogo: jaqueca recurrente; deriva a evaluación auditiva y vestibular por los episodios de mareo.')],
           medicamentos='Ibuprofeno 400 mg cuando tiene jaqueca'),
    cuadro('meniere_migrana', [fig.audiograma(), fig.logo(), fig.ecochg(), fig.vemp()],
           od='normal', oi='meniere', grado_oi='leve', edad=45, sexo='mujer',
           anamnesis="""Tiene 45 años y es contadora. Desde los 20 tiene migraña con aura visual: unas luces que se
           corren por el campo de visión y después dolor pulsátil de un lado. Hace dos años y medio empezó a tener dos
           clases de crisis. La primera es corta: dura dos o tres horas, con todo girando y vómitos; antes se le tapa el
           oído izquierdo y le aparece un zumbido grave, y oye menos por ese lado unos días. Ha tenido cuatro. La
           segunda es larga: uno o dos días de inestabilidad, "como caminar sobre goma", con dolor de cabeza que late,
           luz y ruido insoportables, y casi siempre cerca de la regla. De esas ha tenido más de diez y nunca le
           cambia el oído.""",
           historia=[(900, 'Urgencia: vértigo de dos horas con vómitos y oído izquierdo tapado.'),
                     (400, 'Otorrinolaringología: audiometría con hipoacusia sensorioneural OI de graves; se sospecha Ménière.'),
                     (120, 'Neurología: migraña con aura; se plantea que parte de las crisis largas son migraña vestibular.'),
                     (25, 'Otorrinolaringología: solicita evaluación audiológica completa y vestibular.')],
           antecedentes=[], medicamentos='Sumatriptán 50 mg en las jaquecas'),
]

if __name__ == '__main__':
    Capitulo(23).generar(CASOS)
