#!/usr/bin/env python3
"""Capítulo 35 — Nariz tapada.

    python3 docs/libro/capitulos/35-nariz-tapada.py              casos + figuras + PDF
    python3 docs/libro/capitulos/35-nariz-tapada.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/35-nariz-tapada.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
35-nariz-tapada.md (cada caso se nombra ahí como cap35_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401


# Un cuadro nasal no existe en LabSim: los tres pacientes son de audición normal
# ('normal') y sirven para que existan la ficha, la anamnesis y el rostro.
# Lo nasal (curvas y tablas) sale de RinoSim: ilustraciones/hacer_cap35_rinosim.sh
CASOS = [
    cuadro('desviacion', [], edad=33, sexo='hombre',
           anamnesis="""Tiene 33 años, es repartidor y juega fútbol los fines de semana. Desde que se quebró la
           nariz en una jugada, a los 19 años, siente la fosa derecha tapada casi siempre; la izquierda "a veces",
           sobre todo cuando se resfría o cuando duerme de ese lado. De noche ronca si duerme de espaldas y despierta
           con la boca seca. No tiene estornudos ni picazón, no hay una estación del año peor que otra y no ha tenido
           sangrados. Hace diez días usó por última vez un descongestionante en spray: "esa noche se abrió un poco,
           pero la derecha nunca pasa del todo". Quiere saber si su problema se arregla con remedios o con una
           operación.""",
           historia=[(5000, 'Fractura nasal jugando fútbol; no consultó ni se redujo.'),
                     (200, 'Atención primaria: "desvío de tabique"; se indica solución salina, sin mejoría. Se pide evaluación funcional de la nariz.')],
           medicamentos='Oximetazolina en spray de forma ocasional; la última vez hace diez días'),
    cuadro('valvula', [], edad=52, sexo='mujer',
           anamnesis="""Tiene 52 años y es profesora de educación física. Le hicieron una rinoplastia de reducción
           a los 27 años. Desde hace unos tres años siente que "la nariz se le pega por los lados" cuando respira
           fuerte: al correr, al subir cuestas en bicicleta y en las noches, cuando se da vuelta en la cama. Sentada
           y tranquila respira bien. Descubrió que si se jala la mejilla hacia el lado con un dedo, entra más aire, y
           que una tira nasal le ayuda de noche. No tiene estornudos ni picazón ni secreción, y no varía con las
           estaciones. Un corticoide nasal por dos meses no le cambió nada.""",
           historia=[(9500, 'Rinoplastia de reducción del dorso, sin complicaciones.'),
                     (150, 'Médico general: rinitis, corticoide nasal por 8 semanas sin cambios; se deriva a otorrinolaringología.')],
           cirugias='Rinoplastia de reducción a los 27 años',
           medicamentos='Corticoide nasal (lo dejó por no notar cambios)'),
    cuadro('discordancia', [], edad=41, sexo='mujer',
           anamnesis="""Tiene 41 años y es contadora. Hace ocho meses tuvo un resfrío fuerte, con fiebre, y desde
           entonces siente la nariz tapada "las veinticuatro horas, de los dos lados". Dice que no entra aire y que es
           lo peor que le ha pasado, aunque no respira por la boca, duerme sin ronquidos y trota tres veces por
           semana sin problema. Nota que los olores le llegan menos que antes. No tiene estornudos ni picazón, no
           ha tenido golpes ni cirugías de la nariz y no usa ningún spray nasal. Ha dejado de ir a reuniones por la
           incomodidad.""",
           historia=[(240, 'Cuadro respiratorio alto febril; recuperación completa salvo la sensación de nariz tapada.'),
                     (60, 'Médico general: examen sin hallazgos; se indican lavados nasales, sin mejoría. Se solicita evaluación funcional de la nariz.')]),
]

if __name__ == '__main__':
    Capitulo(35).generar(CASOS)
