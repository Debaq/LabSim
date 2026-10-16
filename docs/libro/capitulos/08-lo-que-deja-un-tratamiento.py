#!/usr/bin/env python3
"""Capítulo 8 — Lo que deja un tratamiento.

    python3 docs/libro/capitulos/08-lo-que-deja-un-tratamiento.py              casos + figuras + PDF
    python3 docs/libro/capitulos/08-lo-que-deja-un-tratamiento.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/08-lo-que-deja-un-tratamiento.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
08-lo-que-deja-un-tratamiento.md (cada caso se nombra ahí como cap08_<nombre>).

Tres oídos que cambiaron por un tratamiento: el cisplatino que se lleva la
base de la cóclea (sin controles a mitad de camino), la aspirina que apaga el
amplificador y se va, y la radioterapia de la parótida que deja una mixta de
un solo lado. El motor entrega una foto: la línea de base y la evolución
van en la historia (TODO 41, "Eje temporal").
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

CASOS = [
    # Semilla 3: la más suave de seis (todas caen fuerte desde 2 kHz porque el
    # cuadro es solo 'leve' con 500 y 1000 en 0) y con acúfeno (siseo).
    cuadro('ototoxica', [fig.audiograma(), fig.teoae(), fig.dpoae()],
           od='ototoxica', oi='ototoxica', edad=31, semilla=3,
           anamnesis="""Tiene 31 años y es profesor de educación física. Hace cinco meses le encontraron un tumor
           en el testículo izquierdo; lo operaron y después recibió cuatro ciclos de quimioterapia, uno cada tres
           semanas. Antes del primer ciclo le hicieron una audiometría y le dijeron que oía bien. Fue al control
           de audición antes del segundo ciclo, pero no a los siguientes: vive lejos del hospital y se sentía bien.
           Durante el tercer ciclo empezó a sentir un siseo en los dos oídos, parejo, que ahora tiene todo el día.
           Terminó la quimioterapia hace diez semanas. Desde entonces le cuesta entender a los alumnos cuando
           hablan todos a la vez en el gimnasio, y ya no oye el pitido del microondas ni el canto de los pájaros
           en la mañana. Conversando de a dos, en silencio, se arregla bien. No ha tenido mareos ni dolor de
           oídos. Nunca ha trabajado con ruido y nadie en su familia es sordo.""",
           historia=[(155, 'Urólogo: tumor testicular izquierdo. Orquiectomía izquierda; biopsia: tumor germinal no seminomatoso. Deriva a oncología.'),
                     (140, 'Oncólogo: indica cuatro ciclos de bleomicina, etopósido y cisplatino, cada 21 días. Solicita evaluación audiológica de base antes del primer ciclo.'),
                     (138, 'Audiometría de base con alta frecuencia: umbrales de 0 a 10 dB HL de 125 a 8.000 Hz en ambos oídos, con respuesta hasta 16 kHz. DPOAE presentes de 1 a 8 kHz en ambos oídos.'),
                     (116, 'Control audiológico antes del segundo ciclo: sin cambio significativo respecto de la base.'),
                     (95, 'Tercer ciclo de quimioterapia. No asiste al control audiológico programado.'),
                     (74, 'Cuarto y último ciclo. Refiere siseo en ambos oídos desde el ciclo anterior. No asiste al control audiológico.'),
                     (20, 'Oncólogo, control al terminar el tratamiento: en remisión. Refiere siseo bilateral y dificultad para entender en grupo. Deriva a otorrinolaringología.'),
                     (8, 'Otorrinolaringólogo: otoscopía normal bilateral. Solicita audiometría con alta frecuencia y emisiones otoacústicas para comparar con la base.')],
           antecedentes=['ototoxicos'],
           medicamentos='Ninguno. Terminó hace diez semanas cuatro ciclos de bleomicina, etopósido y cisplatino',
           cirugias='Orquiectomía izquierda hace cinco meses'),
    # Aspirina en dosis altas por dolor de rodillas: plana, leve, con silbido;
    # la última dosis fue ayer. El motor no modela la recuperación (TODO 41).
    cuadro('salicilatos', [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()],
           od='salicilatos', oi='salicilatos', edad=57, sexo='mujer',
           anamnesis="""Tiene 57 años y es dueña de un almacén de barrio, donde pasa el día de pie. Tiene artrosis en
           las dos rodillas. Hace tres semanas el dolor empeoró y, como el antiinflamatorio que le habían dado le
           caía mal al estómago, empezó a tomar aspirina por su cuenta: dos comprimidos de 500 mg cada seis horas,
           todos los días. Hace unos diez días le apareció un silbido agudo en los dos oídos, parejo, que no se le
           quita en todo el día, y siente que oye "como con algodones": tiene que pedir que le repitan en el
           almacén y subió el volumen de la radio. No ha tenido mareos, dolor ni secreción de oídos. Antes de esto
           oía bien; nunca ha trabajado con ruido. Ayer el otorrinolaringólogo le suspendió la aspirina y se tomó
           la última dosis en la mañana.""",
           historia=[(1095, 'Medicina del trabajo, operativo preventivo: audiometría de tamizaje normal en ambos oídos.'),
                     (400, 'Traumatólogo: gonartrosis bilateral. Indica ibuprofeno y kinesiterapia; suspende el ibuprofeno por dolor epigástrico.'),
                     (5, 'Médico general: acúfeno bilateral y sensación de oído tapado de una semana. Otoscopía normal. Deriva a otorrinolaringología.'),
                     (1, 'Otorrinolaringólogo: otoscopía normal. Consumo de ácido acetilsalicílico de 4 g al día por tres semanas, sin indicación médica. Sospecha ototoxicidad por salicilatos: suspende la aspirina. Solicita audiometría y emisiones otoacústicas ahora y control en una semana.')],
           antecedentes=['ototoxicos', 'hta'],
           medicamentos='Ácido acetilsalicílico 500 mg, dos comprimidos cada 6 horas por tres semanas, por su cuenta (suspendido ayer); losartán 50 mg al día'),
    # Semilla 5: mixta franca del OD (gap de 20-30 dB en graves sobre una caída
    # coclear de agudos) con curva B; las otras dejaban un gap de 5 dB con una B.
    cuadro('post_radioterapia', [fig.audiograma(), fig.timpanograma(), fig.reflejos(), fig.dpoae()],
           od='post_radioterapia', edad=63, semilla=5,
           anamnesis="""Tiene 63 años y es jubilado; trabajó como chofer de micro. Hace dos años le operaron un cáncer
           de la parótida derecha y después recibió seis semanas de radioterapia en ese lado de la cara y el
           cuello. Hacia el final de la radioterapia empezó a sentir el oído derecho tapado, "como en el avión", y
           eso nunca se le pasó del todo. Desde hace unos meses siente que por ese oído oye cada vez menos: ya no
           contesta el celular por la derecha. No tiene pitidos ni mareos. Le quedó la boca seca y la piel del
           lado derecho del cuello más dura y oscura; la cara la mueve bien. Del oído izquierdo oye bien. Nunca
           tuvo otitis de adulto.""",
           historia=[(760, 'Cirujano de cabeza y cuello: carcinoma de parótida derecha. Parotidectomía total derecha con preservación del nervio facial.'),
                     (700, 'Radioterapeuta: radioterapia postoperatoria de la región parotídea y el cuello derechos, seis semanas. Sin quimioterapia.'),
                     (660, 'Control al terminar la radioterapia: radiodermitis cervical derecha, xerostomía. Refiere oído derecho tapado.'),
                     (180, 'Oncólogo, control semestral: sin recidiva. Refiere que oye menos por el oído derecho. Deriva a otorrinolaringología.'),
                     (12, 'Otorrinolaringólogo: membrana timpánica derecha opaca y retraída, sin perforación; nasofibroscopía sin lesiones. Solicita audiometría e impedanciometría.')],
           antecedentes=['hta'],
           medicamentos='Enalapril 10 mg cada 12 horas; saliva artificial',
           cirugias='Parotidectomía total derecha hace dos años'),
]

if __name__ == '__main__':
    Capitulo(8).generar(CASOS)
