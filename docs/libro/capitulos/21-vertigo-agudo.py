#!/usr/bin/env python3
"""Capítulo 21 — Vértigo agudo.

    python3 docs/libro/capitulos/21-vertigo-agudo.py              casos + figuras + PDF
    python3 docs/libro/capitulos/21-vertigo-agudo.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/21-vertigo-agudo.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
21-vertigo-agudo.md (cada caso se nombra ahí como cap21_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo vestibular del capítulo (nistagmo, impulso cefálico, skew) no es de LabSim: son las hojas de
# cabecera de ilustraciones/hacer_cap21.py, con las cifras de estos pacientes inventados. De LabSim
# salen la ficha, la anamnesis, el audiograma, la logoaudiometría y el VEMP de cada caso.
CASOS = [
    cuadro('neuritis', [fig.audiograma()], od='normal', oi='normal', edad=46, sexo='mujer',
           anamnesis="""Tiene 46 años y es profesora de básica. Hace dos días, al levantarse, sintió que la pieza
           giraba, vomitó tres veces y no pudo ponerse de pie sin agarrarse de la pared. Con los ojos cerrados y
           acostada de lado mejora; al mover la cabeza, el giro vuelve. Camina "yéndose hacia la derecha". Una
           semana antes tuvo un resfrío con tos. Oye igual que siempre: sin pitido, sin oído tapado, sin dolor.
           No ha tenido dolor de cabeza, visión doble, dificultad para hablar o tragar, ni debilidad en brazos o
           piernas. Nunca había tenido un episodio así.""",
           historia=[(2, 'Servicio de urgencia: examen neurológico sin focalidad, antiemético. Se indica reposo y evaluación vestibular.'),
                     (9, 'Resfrío con tos y fiebre baja, sin tratamiento.')]),
    cuadro('laberintitis', [fig.audiograma(), fig.vemp(), fig.vemp(subtipo='ovemp')], od='laberintitis',
           grado_od='severa', edad=39, sexo='hombre',
           anamnesis="""Tiene 39 años y trabaja en una bodega. Hace tres días, después de una semana con resfrío, se
           despertó con el oído derecho "tapado, como con agua" y un zumbido a ratos. A las pocas horas
           empezó un vértigo intenso con vómitos. Hoy el giro bajó, pero por el derecho "es como si hablaran
           lejos": en el teléfono no entiende nada. No ha tenido fiebre alta, dolor ni secreción del oído, dolor
           de cabeza, visión doble ni trastornos del habla. No fuma y no toma medicamentos. Nunca había tenido
           vértigo ni problemas de oído.""",
           historia=[(3, 'Servicio de urgencia: otoscopía normal, sin signos neurológicos; antiemético y reposo.'),
                     (10, 'Resfrío con congestión y tos, sin tratamiento.')]),
    cuadro('pseudoneuritis', [fig.audiograma()], od='normal', oi='normal', edad=67, sexo='hombre',
           anamnesis="""Tiene 67 años y es jubilado de la construcción. Ayer a media tarde, viendo televisión, sintió un
           mareo intenso con vómitos. Esta mañana no pudo sentarse en la cama sin irse hacia la derecha y su hija lo
           trajo al servicio de urgencia. Tiene un dolor de cabeza leve en la nuca desde ayer. No ha notado cambio
           en la audición ni pitido. Fumó 30 años y dejó hace cinco. Está en tratamiento por presión alta y
           diabetes.""",
           historia=[(1, 'Mareo súbito con vómitos, sin pérdida de conciencia ni traumatismo.')],
           antecedentes=['hta', 'diabetes'],
           medicamentos='Losartán 50 mg cada 12 horas; metformina 850 mg cada 12 horas; atorvastatina 20 mg en la noche'),
    cuadro('aica', [fig.audiograma(), fig.logo(), fig.vemp()], oi='infarto_aica', grado_oi='moderada', edad=58,
           sexo='mujer',
           anamnesis="""Tiene 58 años y es cajera de un supermercado. Hace dos días, en plena atención, sintió que
           todo giraba y vomitó. Dice que el oído izquierdo "se le apagó de golpe". Desde entonces no puede caminar
           sin que la sostengan: si suelta la camilla, se cae hacia la izquierda. No tiene pitido, dolor de oído ni
           fiebre. Tiene la presión alta, que controla "cuando se acuerda" de tomar el remedio, y fuma una cajetilla
           al día. En urgencia le dijeron que era un cuadro del oído interno y la derivaron a estudio auditivo.""",
           historia=[(2, 'Servicio de urgencia: presión 190/100, antiemético y derivación a estudio auditivo.')],
           antecedentes=['hta'], medicamentos='Enalapril 10 mg al día (irregular)'),
]

if __name__ == '__main__':
    Capitulo(21).generar(CASOS)
