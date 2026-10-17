#!/usr/bin/env python3
"""Capítulo 28 — El primer audífono.

    python3 docs/libro/capitulos/28-el-primer-audifono.py              casos + figuras + PDF
    python3 docs/libro/capitulos/28-el-primer-audifono.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/28-el-primer-audifono.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
28-el-primer-audifono.md (cada caso se nombra ahí como cap28_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo que se mira en todo candidato: audiograma con LDL y discriminacion
BASE = [fig.audiograma(), fig.logo()]

# Ganancia funcional ILUSTRATIVA que declara el libro (no es una prescripcion ni un audifono real).
GANANCIA = {250: 5, 500: 10, 1000: 20, 2000: 30, 3000: 35, 4000: 30, 6000: 15}

CASOS = [
    cuadro('primera_vez', BASE + [fig.campo_libre(ganancia=GANANCIA)], od='presbiacusia', oi='presbiacusia',
           grado_od='moderada', grado_oi='moderada', edad=73, sexo='mujer', semilla=4213838778,
           anamnesis="""Tiene 73 años, es viuda desde hace tres y vive con su hija y su nieta de nueve años. Fue
           secretaria hasta jubilar. Hace unos cinco años sube el volumen de la tele y pide que le repitan, sobre
           todo en la mesa familiar y en el consultorio, donde "hablan muy bajito". Por teléfono entiende si está
           tranquila. Vino porque su hija le dijo "abuela, no me escuchas". Quiere probar, pero duda: su hermana
           tiene audífonos y "no los usa". Lo que más desea es entender a su nieta cuando le cuenta del colegio.
           No tiene pitidos ni mareos, ni ha tenido dolor ni secreción de oídos.""",
           historia=[(500, 'Médico general: "hipoacusia de la edad"; otoscopía normal, se sugiere observar.'),
                     (45, 'Otorrinolaringólogo: otoscopía normal bilateral. Se solicita audiometría y prueba de audífonos.')],
           antecedentes=['hta'], medicamentos='Losartán 50 mg al día'),
    cuadro('reacio', BASE, od='presbiacusia', oi='presbiacusia', grado_od='moderada', grado_oi='moderada',
           edad=68, sexo='hombre', semilla=4084779212,
           anamnesis="""Tiene 68 años y es mecánico jubilado: 35 años en un taller con herramientas neumáticas. Lo trajo
           su señora: "le tengo que repetir todo dos veces". Él dice que oye bien, que "ahora todos hablan bajito",
           y que los audífonos "son para viejos" y "suenan a lata": su cuñado tiene unos y se la pasa ajustándolos.
           Lo que sí le molesta son los ruidos fuertes: "se me clava el oído" con el golpe de una olla o cuando
           gritan los nietos. Tiene un pitido agudo en los dos oídos que va y viene, más en la noche, y teme que
           "algo en el oído" se lo empeore.""",
           historia=[(200, 'Médico general: hipoacusia bilateral referida por la esposa; otoscopía normal. Se deriva a otorrinolaringología.'),
                     (30, 'Otorrinolaringólogo: solicita audiometría con umbral de molestia y prueba de audífonos.')],
           antecedentes=['trauma_acustico']),
    cuadro('leve', BASE, od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve',
           edad=64, sexo='mujer', semilla=2453875140,
           anamnesis="""Tiene 64 años y es profesora de enseñanza media: todavía trabaja. Su pareja le insistió en venir
           porque "a veces no escucha" cuando le habla de espaldas. Ella cree que oye bien: solo le cuesta en los
           restaurantes con mucho ruido y cuando un alumno habla bajito al fondo de la sala. En casa no se pierde
           las conversaciones ni sube la tele. No tiene pitidos ni mareos, y nunca ha tenido infecciones de oído.""",
           historia=[(60, 'Médico general, control de salud: dificultad referida en ambientes ruidosos; otoscopía normal. Se solicita audiometría.')]),
    cuadro('un_oido', BASE + [fig.campo_libre()], od='parotiditis', grado_od='profunda', edad=47, sexo='hombre',
           semilla=1263824184,
           anamnesis="""Tiene 47 años y maneja un taxi. A los nueve años tuvo paperas con fiebre alta y desde entonces
           no oye por el oído derecho: "siempre fue así". Con el izquierdo la vida en casa no le cuesta. Lo que sí le
           cuesta es oír al pasajero que va a su derecha, las conversaciones en una mesa con ruido si la gente está
           de ese lado, y saber de dónde viene una bocina o quién lo llama en la calle. Gira la cabeza para poner el
           oído sano y al final del día termina agotado. No tiene pitidos, mareos ni dolor. Un colega le contó que
           "hay audífonos para el que oye de un solo oído" y quiere saber si le servirían.""",
           historia=[(13700, 'Parotiditis (paperas) con fiebre alta; desde entonces no oye por el oído derecho.'),
                     (60, 'Médico general: hipoacusia OD antigua, otoscopía normal. Se deriva a evaluación audiológica y de audífonos.')]),
]

if __name__ == '__main__':
    Capitulo(28).generar(CASOS)
