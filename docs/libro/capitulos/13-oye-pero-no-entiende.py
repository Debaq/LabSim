#!/usr/bin/env python3
"""Capítulo 13 — Oye pero no entiende.

    python3 docs/libro/capitulos/13-oye-pero-no-entiende.py              casos + figuras + PDF
    python3 docs/libro/capitulos/13-oye-pero-no-entiende.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/13-oye-pero-no-entiende.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
13-oye-pero-no-entiende.md (cada caso se nombra ahí como cap13_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo que se mira en todos los casos: lo tonal, lo suprasliminar y lo electrofisiológico
BASE = [fig.audiograma(), fig.logo(), fig.reflejos(), fig.teoae()]

CASOS = [
    demo(40, BASE + [fig.abr(niveles=(80, 60, 40)),                        # alternada: la microfónica se cancela
                     fig.abr(niveles=(90,), polaridad='rarefaccion', marcar=()),
                     fig.abr(niveles=(90,), polaridad='condensacion', marcar=())]),
    cuadro('neuropatia_hereditaria', BASE + [fig.abr(niveles=(80, 60, 40)), fig.vemp()],
           od='neuropatia_hereditaria', oi='neuropatia_hereditaria', edad=28, sexo='mujer',
           anamnesis="""Tiene 28 años y es técnica en enfermería. Desde que se acuerda oye bien "pero no entiende" cuando hay
           ruido: en el casino del hospital, en las reuniones o con la mascarilla puesta se pierde, y por teléfono
           entiende menos aún. En silencio, cara a cara, conversa sin problema. No tiene pitidos ni mareos. De
           adolescente le salieron los pies arqueados, se tuerce los tobillos con facilidad y le cuesta correr; su
           padre y una tía camina con bastón. El neurólogo le dijo que "los nervios de las piernas conducen lento" y
           la mandó a control auditivo.""",
           historia=[(900, 'Neurólogo: debilidad distal en piernas, pies cavos y arreflexia aquileana; estudio de conducción nerviosa lento.'),
                     (30, 'Neurólogo: solicita evaluación auditiva por dificultad para entender en ruido.')],
           medicamentos='Ninguno'),
    cuadro('kernicterus', BASE + [fig.abr(niveles=(80, 60, 40))],
           od='kernicterus', oi='kernicterus', grado_od='moderada', grado_oi='moderada', edad=11, sexo='hombre',
           anamnesis="""Tiene 11 años y viene con su mamá, que cuenta la historia. Nació de término en un hospital rural; al tercer día
           estaba "amarillo hasta los pies", lo trasladaron tarde y estuvo varios días en fototerapia. El tamizaje de oído
           del recién nacido no se hizo. Desde bebé tiene movimientos involuntarios de brazos y cara, le cuesta mirar hacia
           arriba sin mover la cabeza y los dientes de leche le salieron con el esmalte amarillo verdoso. Va a una escuela
           especial. Se asusta con los ruidos y se da vuelta cuando lo llaman, pero "no entiende lo que se le dice": se
           comunica con gestos y pocas palabras, y a veces se entiende mejor en la casa que en la escuela.""",
           historia=[(4015, 'Hospital rural: hiperbilirrubinemia neonatal al tercer día, fototerapia.'),
                     (1500, 'Neurología infantil: trastorno del movimiento de tipo atetósico.'),
                     (60, 'Fonoaudiología escolar: no responde de forma confiable a la audiometría de tamizaje; se deriva a evaluación auditiva.')]),
    cuadro('leucodistrofia', BASE + [fig.abr(niveles=(80, 60, 40))],
           od='leucodistrofia', oi='leucodistrofia', edad=8, sexo='hombre',
           anamnesis="""Tiene 8 años y viene con su mamá. Hasta hace unos meses era buen alumno. Desde el otoño, dice la mamá, "no oye":
           no responde cuando lo llaman, en la sala no sigue las instrucciones y la profesora cree que es distraído. Ella
           nota que además tropieza más, la letra le empeoró y se queja de que "ve borroso" el pizarrón. Está más irritable
           y llorón. Hace años que se broncea muy rápido y la piel de los codos se le ve oscura. Un tío materno murió
           joven de una "enfermedad de los nervios".""",
           historia=[(90, 'Profesora jefe: baja de rendimiento y falta de atención desde marzo.'),
                     (40, 'Pediatra: descarta cerumen, otoscopía normal; sospecha de hipoacusia y déficit atencional, solicita audiometría.')]),
]

if __name__ == '__main__':
    Capitulo(13).generar(CASOS)
