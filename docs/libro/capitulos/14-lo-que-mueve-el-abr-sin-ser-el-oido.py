#!/usr/bin/env python3
"""Capítulo 14 — Lo que mueve el ABR sin ser el oído.

    python3 docs/libro/capitulos/14-lo-que-mueve-el-abr-sin-ser-el-oido.py              casos + figuras + PDF
    python3 docs/libro/capitulos/14-lo-que-mueve-el-abr-sin-ser-el-oido.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/14-lo-que-mueve-el-abr-sin-ser-el-oido.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
14-lo-que-mueve-el-abr-sin-ser-el-oido.md (cada caso se nombra ahí como cap14_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

ABR_X = fig.abr(niveles=(80, 60, 40))


CASOS = [
    cuadro('toxico_metabolico', [fig.audiograma(), fig.timpanograma(), fig.teoae(), fig.abr(niveles=(90, 80, 60))],
           od='toxico_metabolico', oi='toxico_metabolico', grado_od='leve', grado_oi='leve', edad=45, sexo='mujer',
           anamnesis="""Tiene 45 años y es profesora de enseñanza básica. Hace como un año que oye menos por los dos
           oídos, parejo: dice que es "como tener algodón" y que en el recreo le cuesta entender a los niños. No
           tiene pitidos ni mareos, nunca ha tenido dolor ni secreción de oídos, no ha estado expuesta a ruido y en
           su familia nadie oye mal. Cuenta que en el último año está "apagada": se cansa con todo, tiene frío
           cuando los demás no, ha subido seis kilos sin comer más, tiene la piel seca, el pelo quebradizo, está
           estreñida y le notan la voz más ronca. Atribuye todo al trabajo y al estrés.""",
           historia=[(400, 'Consulta a médico general por cansancio y aumento de peso; se indican exámenes de sangre que no se retiró.'),
                     (60, 'Médico general: hipoacusia bilateral referida; otoscopía normal. Se deriva a evaluación auditiva.')],
           medicamentos='Ninguno'),
    cuadro('hipotermia_farmacos', [fig.teoae(), fig.abr(niveles=(80, 60, 40))],
           od='hipotermia_farmacos', oi='hipotermia_farmacos', edad=45,
           anamnesis="""Tiene 45 años y es chofer de camión. No puede contestar: informa su esposa y la ficha de la
           unidad de cuidados intensivos. Hace 18 horas sufrió un paro cardiorrespiratorio en su casa; su señora
           inició las compresiones y los paramédicos lo recuperaron a los 12 minutos. Está intubado, con enfriamiento
           controlado a 33,0 °C de temperatura central según el protocolo de la unidad, y sedado con infusión de
           propofol y fentanilo. Antes del paro oía bien, no usaba audífonos y no tomaba medicamentos. El equipo
           médico pide un ABR en la cama para ver cómo está el tronco.""",
           historia=[(1, 'Ingreso a UCI tras paro cardiorrespiratorio recuperado; inicia enfriamiento controlado a 33 °C y sedoanalgesia continua.')],
           medicamentos='Propofol y fentanilo en infusión (UCI)'),
    cuadro('bloqueo_proximal', [fig.teoae(), fig.abr(niveles=(80, 60, 40))],
           od='bloqueo_proximal', oi='bloqueo_proximal', edad=45,
           anamnesis="""Tiene 45 años y es soldador. No puede contestar: informa su hermana y la ficha de la unidad de
           cuidados intensivos. Hace cuatro días, en el trabajo, se quejó de un dolor de cabeza "como un golpe" y cayó
           inconsciente; la tomografía mostró una hemorragia cerebral masiva. Es hipertenso y dejó el enalapril hace
           un año. Lleva cuatro días intubado, sin respuesta a ningún estímulo. Los sedantes están suspendidos hace más
           de 24 horas y la temperatura central es de 36,8 °C. El equipo médico evalúa el cuadro y pide un ABR en la
           cama como examen complementario. Antes oía normal.""",
           historia=[(4, 'Ingreso por hemorragia intracerebral masiva; intubado en UCI.'),
                     (1, 'Sedación suspendida; temperatura central 36,8 °C.')],
           antecedentes=['hta'], medicamentos='Ninguno (dejó el enalapril)'),
    cuadro('prematuro', [fig.timpanograma(sonda=1000), fig.teoae(), fig.abr(niveles=(80, 60, 40))],
           od='prematuro', oi='prematuro', edad_horas=1344,
           anamnesis="""Tiene 8 semanas de vida y viene con su mamá. Nació a las 32 semanas, con 1.700 g, tras un
           trabajo de parto prematuro; el embarazo había sido normal y la mamá no tuvo infecciones ni tomó
           medicamentos. Estuvo cuatro semanas en la unidad de neonatología por inmadurez respiratoria: recibió
           cafeína por las apneas y no recibió antibióticos aminoglucósidos. Antes del alta, el tamizaje automático
           (AABR) refirió en el oído derecho. Hoy viene a la evaluación de seguimiento: llegó despierto, comió
           justo antes del examen y se durmió en brazos de su mamá. Nadie en la familia tiene problemas de audición.""",
           historia=[(28, 'Alta de neonatología a las 36 semanas de edad corregida; AABR refiere OD y pasa OI.')],
           medicamentos='Ninguno actual'),
]

if __name__ == '__main__':
    Capitulo(14).generar(CASOS)
