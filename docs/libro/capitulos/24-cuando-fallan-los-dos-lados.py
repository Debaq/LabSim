#!/usr/bin/env python3
"""Capítulo 24 — Cuando fallan los dos lados.

    python3 docs/libro/capitulos/24-cuando-fallan-los-dos-lados.py              casos + figuras + PDF
    python3 docs/libro/capitulos/24-cuando-fallan-los-dos-lados.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/24-cuando-fallan-los-dos-lados.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
24-cuando-fallan-los-dos-lados.md (cada caso se nombra ahí como cap24_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

FIGURAS = [fig.audiograma()]

CASOS = [
    cuadro('gentamicina', [fig.audiograma()], od='normal', oi='normal', edad=52, sexo='hombre',
           anamnesis="""Tiene 52 años y es electricista. Hace diez meses lo operaron de urgencia por una peritonitis, estuvo
           ocho días en cuidados intensivos y tres semanas hospitalizado. Hacia el final de la segunda semana se sintió
           "mareado, flojo", y lo atribuyeron a la debilidad de haber estado tanto tiempo en cama. Salió de alta sin vértigo.
           Hoy el problema es otro: cuando camina por la calle los letreros y las caras "saltan", y no puede leer el número
           de la micro si va caminando, pero sí cuando se detiene. En la oscuridad pierde el equilibrio: de noche camina al
           baño con la mano en la pared, y una vez se cayó al entrar a una pieza sin luz. Sentado o acostado no siente nada, no
           tiene vértigo, y en la camioneta, por un camino de tierra, ve el paisaje "temblar". Oye igual que siempre y no
           tiene pitidos. Hizo tres meses de kinesiología general sin cambio, y el neurólogo le dijo que la resonancia de
           cerebro estaba normal y que podía ser "ansiedad".""",
           historia=[(300, 'Hospitalización por peritonitis postoperatoria: cuidados intensivos, antibióticos de amplio espectro, entre ellos gentamicina por 12 días. Alza transitoria de la creatinina.'),
                     (280, 'Alta con diagnóstico de polineuropatía del paciente crítico leve; se indica kinesiología.'),
                     (120, 'Neurólogo: resonancia de cerebro normal; mareo inespecífico, posible componente ansioso.'),
                     (30, 'Otorrinolaringólogo: oscilopsia al caminar con audición normal; solicita evaluación audiológica y vestibular.')],
           antecedentes=['ototoxicos'], medicamentos='Ninguno'),
    cuadro('tuberculosis', [fig.audiograma(), fig.logo(), fig.teoae()], od='ototoxica', oi='ototoxica',
           grado_od='leve', grado_oi='leve', edad=41, sexo='mujer',
           anamnesis="""Tiene 41 años y es peluquera. Hace tres años le diagnosticaron una tuberculosis resistente a los
           fármacos habituales y la trataron durante un año y medio, con una inyección diaria los primeros meses. Hoy está
           curada. Viene derivada del programa de tuberculosis porque tiene un pitido en los dos oídos, agudo y permanente,
           y no entiende bien en la peluquería con las máquinas y el secador prendidos, ni cuando hablan varias personas.
           Cuando se le pregunta por el equilibrio dice que está "débil de piernas" desde el tratamiento: se cansa al
           caminar, en el metro no se atreve a soltar el pasamanos y a oscuras se agarra de las murallas. Hace dos años le
           cambiaron los lentes porque "al caminar rápido veo los carteles movidos", y no mejoró. No ha tenido vértigo.""",
           historia=[(1100, 'Diagnóstico de tuberculosis multirresistente. Esquema con kanamicina inyectable más otros fármacos, por 18 meses en total.'),
                     (900, 'Se suspende la kanamicina a los seis meses por alza de la creatinina; sin audiometría de control durante el tratamiento.'),
                     (400, 'Alta con baciloscopias negativas.'),
                     (60, 'Control de oftalmología: lentes nuevos, sin mejoría de la visión al caminar.'),
                     (25, 'Programa de tuberculosis: acúfeno bilateral e hipoacusia referida; deriva a evaluación auditiva.')],
           medicamentos='Ninguno'),
    cuadro('sin_causa', [fig.audiograma()], od='normal', oi='normal', edad=58, sexo='mujer',
           anamnesis="""Tiene 58 años y es administrativa en un colegio. Hace unos tres años le cuesta caminar con seguridad,
           sobre todo cuando está oscuro o el piso es desparejo: en las escaleras de la micro se afirma con las dos manos y
           en la playa, con arena, camina "como si el piso se moviera". Cuando trota para alcanzar la micro ve la calle
           temblar. Sentada no tiene ningún síntoma. Tiene jaquecas desde los 20 años, que le laten de un lado, con luz y
           ruido que le molestan. Hace ocho años tuvo dos episodios de vértigo de unas horas, con náuseas, que le trataron
           como laberintitis, y después nunca más. No oye peor, no tiene pitidos ni ha tomado antibióticos fuertes, y no ha
           tenido meningitis. Hace un año se cayó una noche en el pasillo de su casa. Le dijeron que lo suyo era migraña y
           ansiedad.""",
           historia=[(2900, 'Urgencia: dos episodios de vértigo de horas con náuseas, tratados como laberintitis; sin estudio posterior.'),
                     (400, 'Videonistagmografía en otro centro: calórica mínima informada como "hipoexcitabilidad no significativa"; se concluye sin alteración vestibular.'),
                     (200, 'Neurólogo: migraña; resonancia de cerebro normal. Se indica profilaxis.'),
                     (20, 'Otorrinolaringólogo: inestabilidad crónica con oscilopsia al trotar; pide evaluación audiológica y repetir el estudio vestibular.')],
           antecedentes=[], medicamentos='Propranolol 40 mg al día'),
    cuadro('canvas', [fig.audiograma(), fig.logo()], od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve',
           edad=67, sexo='hombre',
           anamnesis="""Tiene 67 años y es carpintero jubilado. Desde hace unos cuatro años camina "como curado": abre los pies,
           se desvía y se agarra de las paredes. Con los ojos cerrados o en la oscuridad empeora mucho. Se ha caído dos veces
           en el último año. Hace años nota hormigueo y "como corcho" en los pies, y dice que a veces no siente el piso. Su
           hija cuenta que a ratos habla "arrastrado". Al caminar rápido ve la calle rebotar. Oye menos desde hace años,
           parejo de los dos lados, y tiene un pitido agudo permanente. No ha tenido vértigo. No recuerda haber tomado
           antibióticos fuertes ni haber estado grave.""",
           historia=[(1500, 'Médico general: neuropatía de los pies; glicemia, vitamina B12 y tiroides normales.'),
                     (700, 'Neurólogo: electromiografía con polineuropatía sensitiva; marcha atáxica.'),
                     (300, 'Resonancia de cerebro: atrofia del vermis cerebeloso.'),
                     (40, 'Neurólogo: solicita evaluación audiológica y vestibular por oscilopsia e inestabilidad.')],
           antecedentes=[], medicamentos='Ninguno'),
]

if __name__ == '__main__':
    Capitulo(24).generar(CASOS)
