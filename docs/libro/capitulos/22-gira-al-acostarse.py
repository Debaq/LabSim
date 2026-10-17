#!/usr/bin/env python3
"""Capítulo 22 — Gira al acostarse.

    python3 docs/libro/capitulos/22-gira-al-acostarse.py              casos + figuras + PDF
    python3 docs/libro/capitulos/22-gira-al-acostarse.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/22-gira-al-acostarse.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
22-gira-al-acostarse.md (cada caso se nombra ahí como cap22_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

AUDIO = [fig.audiograma()]

CASOS = [
    cuadro('posterior', AUDIO, od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve', edad=58, sexo='mujer',
           anamnesis="""Tiene 58 años y es profesora de básica. Hace seis días, al acostarse en la noche y girar hacia
           el lado derecho, sintió que la pieza le daba vueltas por unos 20 segundos, con náuseas, y le pasó otra vez
           al levantarse a media noche y al mirar hacia arriba para sacar un pañuelo de un estante. Cuando está
           sentada o caminando se siente bien. Hace años oye menos en los lugares con ruido y tiene un siseo parejo
           en los dos oídos que no ha cambiado; no ha tenido dolor de cabeza intenso, visión doble ni dificultad
           para hablar. No se golpeó la cabeza. Dejó de agacharse a
           recoger cosas del suelo "por si acaso".""",
           historia=[(6, 'Primer episodio de giro al acostarse sobre el lado derecho.')],
           antecedentes=['hta'], medicamentos='Enalapril 10 mg al día'),
    cuadro('geotropico', AUDIO, edad=44, sexo='hombre',
           anamnesis="""Tiene 44 años y trabaja como técnico de refrigeración. Hace diez días lo trataron en un
           centro por un vértigo posicional "de oído izquierdo" con una maniobra de acostarlo y girarlo; esa noche
           mejoró. Hace tres días volvió a molestarle: ya no le pasa al mirar hacia arriba, sino al darse vuelta en la
           cama, y sobre todo cuando se da vuelta hacia el lado izquierdo, que le da un giro intenso de casi un
           minuto con náuseas, aunque ahora no vomitó. Sentado está bien. No oye menos ni tiene pitido.""",
           historia=[(10, 'Vértigo posicional del oído izquierdo; tratado con una maniobra de reposición, mejoría esa noche.'),
                     (3, 'Reaparece el vértigo al darse vuelta en la cama, sobre todo hacia la izquierda.')]),
    cuadro('apogeotropico', AUDIO, od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve', edad=67, sexo='mujer',
           anamnesis="""Tiene 67 años y es dueña de casa. Hace dos semanas, al darse vuelta en la cama, empezó a
           sentir que todo gira y le dura todo el tiempo que se queda de lado: si se queda mirando hacia la
           derecha o la izquierda la sensación sigue por uno o dos minutos y solo cede cuando se pone boca arriba.
           Dice que "es peor para el lado izquierdo". Oye menos desde hace años y tiene un pitido parejo en los
           dos oídos que no ha cambiado con el mareo. Se levanta con cuidado y ya no duerme de costado.""",
           historia=[(14, 'Primer episodio al darse vuelta en la cama.')],
           antecedentes=['hta'], medicamentos='Losartán 50 mg al día'),
    cuadro('central', AUDIO, edad=54, sexo='hombre',
           anamnesis="""Tiene 54 años y es transportista. Hace tres meses siente un mareo que empieza apenas se
           acuesta y dura mientras está acostado, como si la cama "se hundiera"; no se le pasa en 20 segundos
           como a su cuñado, que tiene "vértigo de oído". Camina abriendo las piernas para no irse de lado, ha
           notado que la letra le sale temblorosa y esta semana le dolió la parte de atrás de la cabeza. Es
           hipertenso y diabético, con control irregular. No oye menos ni tiene pitido.""",
           historia=[(90, 'Mareo al acostarse; consultó por urgencia, se le indicó betahistina sin mejoría.')],
           antecedentes=['hta', 'diabetes'], medicamentos='Enalapril 20 mg, metformina 850 mg, betahistina'),
]

if __name__ == '__main__':
    Capitulo(22).generar(CASOS)
