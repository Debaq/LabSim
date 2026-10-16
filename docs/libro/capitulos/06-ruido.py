#!/usr/bin/env python3
"""Capítulo 6 — Ruido.

    python3 docs/libro/capitulos/06-ruido.py              casos + figuras + PDF
    python3 docs/libro/capitulos/06-ruido.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/06-ruido.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
06-ruido.md (cada caso se nombra ahí como cap06_<nombre>).

Cuatro oídos frente al ruido: la línea de base de un joven sano (33), el
daño crónico de años de faena (37), el trauma de un solo disparo y la
muesca de quien trabaja de noche con música fuerte. En todos se lee el
audiograma junto a las emisiones, frecuencia por frecuencia.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402

# Lo que se mira en todos: el audiograma y las dos emisiones evocadas
OEA = [fig.audiograma(), fig.teoae(), fig.dpoae()]

CASOS = [
    # Tomás: audiometría y emisiones de base antes de entrar a la mina
    demo(33, OEA),
    # Jorge: muesca ensanchada de 22 años de chancador; la TEOAE "pasa" igual
    demo(37, [fig.audiograma(), fig.logo(), fig.teoae(), fig.dpoae()]),
    # Un disparo a la izquierda: muesca profunda de un solo oído; Weber mudo
    cuadro('trauma_acustico_agudo', [fig.audiograma(), fig.acumetria(), fig.teoae(), fig.dpoae()],
           oi='trauma_acustico_agudo', edad=19,
           anamnesis="""Tiene 19 años y está haciendo el servicio militar. Hace cuatro días, en una práctica de
           tiro, un compañero disparó a su izquierda justo cuando él se estaba acomodando el protector auditivo.
           Desde ese momento siente el oído izquierdo "tapado", como con algodón, y tiene un pitido agudo de ese
           lado que no se le quita y que lo molesta más en la noche, cuando está todo en silencio. Conversa bien,
           pero dice que por la izquierda los sonidos le llegan "como apagados". No tuvo dolor, sangre ni mareos.
           Antes de esto nunca había tenido problemas de oído.""",
           historia=[(4, 'Enfermería del regimiento: oído izquierdo tapado y pitido tras práctica de tiro; otoscopía sin perforación. Se deriva a otorrinolaringología.'),
                     (2, 'Otorrinolaringólogo: trauma acústico agudo OI. Indica tratamiento y solicita audiometría y emisiones otoacústicas.')],
           antecedentes=['trauma_acustico'],
           medicamentos='Prednisona oral desde hace dos días, indicada por el otorrinolaringólogo'),
    # Diez años de barra en una discoteca: muesca bilateral profunda con recuperación en 8 kHz
    cuadro('muesca_4k', [fig.audiograma(), fig.dpoae()], od='muesca_4k', oi='muesca_4k', edad=32, sexo='mujer',
           anamnesis="""Tiene 32 años y hace diez trabaja en la barra de una discoteca, cuatro noches por semana. No
           usa protección auditiva porque "tiene que escuchar los pedidos". Desde hace años sale del turno con
           los oídos silbando, pero antes se le pasaba al día siguiente. Hace como un año el silbido de los dos
           oídos ya no se le quita, y lo nota más al acostarse. Le cuesta entender a los clientes y a sus amigas
           cuando salen a comer a un lugar con ruido; conversando de a dos, en la casa, oye bien. No ha tenido
           mareos ni dolor de oídos. Su último turno fue hace tres días.""",
           historia=[(365, 'Médico general: acúfeno bilateral persistente; otoscopía normal. Se indica evitar el ruido y control.'),
                     (20, 'Otorrinolaringólogo: acúfeno bilateral y dificultad para entender en ruido; solicita evaluación audiológica con emisiones otoacústicas.')],
           antecedentes=['trauma_acustico']),
]

if __name__ == '__main__':
    Capitulo(6).generar(CASOS)
