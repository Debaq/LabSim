#!/usr/bin/env python3
"""Capítulo 27 — Mareo que no se va.

    python3 docs/libro/capitulos/27-mareo-que-no-se-va.py              casos + figuras + PDF
    python3 docs/libro/capitulos/27-mareo-que-no-se-va.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/27-mareo-que-no-se-va.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
27-mareo-que-no-se-va.md (cada caso se nombra ahí como cap27_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# LabSim da solo el lado auditivo: lo vestibular y lo postural de cada caso está escrito en el .md
# ("cifras inventadas para el libro") o sale de los esquemas de ilustraciones/cap27-*.svg
# (hacer_cap27.py) y del modelo postural de labyrinthus3d (hacer_cap27_simulador.py).
CASOS = [
    cuadro('neuritis', [fig.audiograma(), fig.vemp()], od='normal', oi='normal', edad=47, sexo='mujer',
           anamnesis="""Tiene 47 años y es analista de crédito en un banco. Hace nueve meses despertó con el mundo girando:
           vértigo intenso, vómitos y dos días sin poder ponerse de pie; en urgencia le dijeron que era una neuritis
           vestibular del lado izquierdo. El giro se fue en unos días, pero no volvió a sentirse firme: desde entonces
           tiene un mareo suave todos los días, como si flotara o el piso fuera blando, sin giro. Es peor de pie, en la
           fila del banco, en el supermercado, frente a la pantalla del computador y en el auto cuando hay mucho tráfico;
           mejora acostada y cuando está en una conversación que la entretiene. Se le nota más al final del día. No se
           ha caído, pero evita los centros comerciales y camina con anteojos de sol. Su familia piensa que son "los
           nervios" y a ella le preocupa si "quedó dañada". No tiene dolor de cabeza, pitido ni pérdida de audición.""",
           historia=[(270, 'Urgencia: vértigo intenso con nistagmo; diagnóstico de neuritis vestibular izquierda, tratada y dada de alta a los cuatro días.'),
                     (240, 'Control: sin vértigo; persiste mareo al caminar. Se indica seguir con sus actividades.'),
                     (60, 'Neurólogo: resonancia de cerebro normal; deriva a evaluación auditiva y vestibular por mareo persistente.')],
           medicamentos='Ninguno; paracetamol ocasional'),
    cuadro('vppb', [fig.audiograma(), fig.logo()], od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve', edad=64, sexo='mujer',
           anamnesis="""Tiene 64 años y está jubilada de una tienda de ropa, donde fue vendedora. Hace cinco meses, al darse
           vuelta en la cama, todo giró unos segundos; le pasaba cada vez que se acostaba o se levantaba. Le dijeron que
           eran "cristales" y le hicieron dos maniobras; el giro se acabó a las dos semanas. Pero desde entonces el piso
           "no está firme": se siente inestable todos los días, más en el supermercado, en la micro y entre mucha gente, y
           mejor cuando se sienta en casa. Hace dos meses, en el supermercado, tuvo una crisis: el corazón se le aceleró,
           sintió que le faltaba el aire y que se caía, y tuvo que salir. Desde entonces no sale sola. En urgencia le dijeron
           que era ansiedad y le dieron un ansiolítico, que toma a veces de noche. Ella no está de acuerdo: "antes no era
           nerviosa; el mareo partió primero". Hace años oye menos los agudos y no usa audífono; en los lugares ruidosos
           se le hace todavía más difícil.""",
           historia=[(150, 'Urgencia: vértigo posicional; Dix-Hallpike positivo derecho; diagnóstico de VPPB del canal posterior derecho.'),
                     (140, 'Dos maniobras de reposición con resolución del vértigo.'),
                     (60, 'Urgencia: crisis de angustia en el supermercado; electrocardiograma normal; alta con clonazepam.'),
                     (20, 'Médico de familia: mareo persistente; deriva a otorrinolaringología y evaluación audiovestibular.')],
           antecedentes=['hta'], medicamentos='Losartán 50 mg al día; clonazepam 0,5 mg de noche, a veces'),
    cuadro('schwannoma', [fig.audiograma(), fig.logo(), fig.reflejos(), fig.abr(niveles=(80, 60, 40)), fig.vemp()],
           oi='schwannoma', grado_oi='leve', edad=58, sexo='hombre',
           anamnesis="""Tiene 58 años y es técnico en refrigeración. Hace diez meses empezó, sin ningún evento que él recuerde,
           a sentirse inestable: "como caminar sobre un colchón". No ha tenido vértigo ni crisis. Es peor de noche, cuando
           va al baño a oscuras, y al girar rápido; en el supermercado o frente a la pantalla no nota diferencia, y mejora
           sentado. Ha tropezado dos veces de noche. Desde hace más o menos un año tiene un pitido agudo en el oído
           izquierdo y le cuesta entender por teléfono con ese lado, por lo que se lo pasa al derecho. Su señora cree que es
           "la edad"; su médico le dijo que era estrés por el trabajo y le recomendó ejercicios de respiración. Él está
           preocupado porque no mejora.""",
           historia=[(300, 'Médico general: inestabilidad crónica; diagnóstico de "estrés"; se indica respiración y pausas.'),
                     (150, 'Segundo control: sin cambios; se sugiere consulta con psicología.'),
                     (45, 'Otorrinolaringólogo: solicita evaluación audiológica y vestibular por inestabilidad y acúfeno izquierdo.')],
           antecedentes=['hta'], medicamentos='Enalapril 10 mg cada 12 horas'),
]

if __name__ == '__main__':
    Capitulo(27).generar(CASOS)
