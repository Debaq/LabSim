#!/usr/bin/env python3
"""Capítulo 25 — Lo que viene de arriba.

    python3 docs/libro/capitulos/25-lo-que-viene-de-arriba.py              casos + figuras + PDF
    python3 docs/libro/capitulos/25-lo-que-viene-de-arriba.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/25-lo-que-viene-de-arriba.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
25-lo-que-viene-de-arriba.md (cada caso se nombra ahí como cap25_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo oculomotor y lo vestibular del capítulo (mirada, seguimiento, sacadas, vHIT) no es de LabSim: son las
# trazas de labyrinthus3d en ilustraciones/hacer_cap25.py y las cifras de estos pacientes inventados. De
# LabSim salen la ficha, la anamnesis y el audiograma de cada caso.
CASOS = [
    cuadro('canvas', [fig.audiograma()], od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve',
           edad=64, sexo='hombre', semilla=25,
           anamnesis="""Tiene 64 años y es electricista jubilado. Hace unos cinco años empezó a andar inseguro: en el
           baño de noche, sin luz, tiene que agarrarse de las paredes, y en el pasto o en una vereda en mal estado
           "se le van los pies". No siente que todo gire: es inestabilidad. Cuando camina rápido o va en auto por
           un camino con baches, las letras de los letreros "saltan" y no las puede leer. Hace unos dos años se le
           duermen y le hormiguean los pies. Tiene una tos seca desde los 40 años, que nadie le explicó. Oye algo
           menos que antes, sobre todo en grupos, como casi todos los de su edad, y tiene un pitido agudo en los
           dos oídos, permanente, que ya no le molesta; no tiene mareos giratorios. Un hermano mayor "camina raro" y se mueve con bastón. Toma un vaso de vino los fines de
           semana.""",
           historia=[(1100, 'Médico general: "mareo del adulto mayor"; betahistina por tres meses, sin mejoría.'),
                     (200, 'Neurología: marcha atáxica y reflejos aquilianos ausentes; solicita resonancia y estudio vestibular.')],
           medicamentos='Ninguno de forma permanente'),
    cuadro('esclerosis', [fig.audiograma()], od='esclerosis_multiple', oi='esclerosis_multiple', edad=31, sexo='mujer',
           semilla=26,
           anamnesis="""Tiene 31 años y es cajera en una farmacia. Hace tres semanas, al mirar hacia el lado derecho,
           empezó a ver doble: las dos imágenes están una al lado de la otra y se juntan cuando mira al frente. A
           veces siente que el cuadro que mira "tiembla". No tiene mareo giratorio, ni pitido, ni cambios en la
           audición. A los 27 años perdió la visión del ojo derecho durante diez días, con dolor al mover el ojo;
           se recuperó con tratamiento y no volvió a pensar en eso. Desde hace unos meses un hormigueo en la mano
           izquierda que va y viene. Su neuróloga sospecha una enfermedad desmielinizante y le pidió que se evalúen
           los movimientos de los ojos mientras llega la resonancia.""",
           historia=[(1500, 'Oftalmología: neuritis óptica del ojo derecho, corticoide endovenoso con recuperación.'),
                     (25, 'Neurología: diplopía horizontal a la derecha y hormigueo de la mano izquierda; solicita resonancia y registro de movimientos oculares de los dos ojos.')]),
    cuadro('chiari', [fig.audiograma()], oi='chiari_hic', grado_oi='leve', edad=38, sexo='mujer', semilla=27,
           anamnesis="""Tiene 38 años y trabaja en una oficina de partes. Desde hace dos años tiene un dolor de cabeza
           en la nuca que le sube al toser, estornudar o reírse fuerte. Se siente inestable, "como si el piso se
           moviera", sobre todo al bajar escaleras mirando los peldaños y al leer: dice que las líneas del texto
           saltan un poco. No gira nada. Por el oído izquierdo oye menos, aunque no tiene pitido. Hace seis meses
           le hicieron en otro servicio un examen del equilibrio con videonistagmografía: el informe dice "sin
           nistagmo, calórica simétrica". Le hormiguean a veces las manos.""",
           historia=[(180, 'Otorrinolaringología (otro servicio): mareo inespecífico y videonistagmografía sin hallazgos. Se indica observación.'),
                     (30, 'Neurología: cefalea occipital con maniobra de Valsalva; solicita resonancia y repetir el estudio vestibular con registro vertical.')]),
    cuadro('farmaco', [fig.audiograma()], od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve',
           edad=71, sexo='hombre', semilla=28,
           anamnesis="""Tiene 71 años y es jubilado de la construcción. Desde un golpe en la cabeza a los 45 años tiene
           epilepsia, controlada. Hace cuatro meses tuvo una convulsión y su neurólogo le subió la dosis de la
           fenitoína. Desde entonces anda "mareado, como curado": no gira nada, pero camina con los pies
           separados, ve doble o borroso al mirar hacia los lados y le cuesta leer. Oye menos que antes, parejo
           en los dos oídos, y no tiene pitido. Toma dos o tres vasos de vino al día con la comida. El médico
           general pensó en un problema del oído interno y lo envía a estudio.""",
           historia=[(125, 'Neurología: convulsión tónico-clónica; se sube la dosis de fenitoína.'),
                     (20, 'Médico general: "mareo", betahistina por tres semanas sin mejoría.')],
           medicamentos='Fenitoína 100 mg cada 8 horas; clonazepam 0,5 mg en la noche'),
]

if __name__ == '__main__':
    Capitulo(25).generar(CASOS)
