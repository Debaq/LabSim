#!/usr/bin/env python3
"""Capítulo 30 — Oír y no entender.

    python3 docs/libro/capitulos/30-oir-y-no-entender.py              casos + figuras + PDF
    python3 docs/libro/capitulos/30-oir-y-no-entender.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/30-oir-y-no-entender.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
30-oir-y-no-entender.md (cada caso se nombra ahí como cap30_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo periférico que se cierra antes de cualquier batería central (→ H14)
PERIFERIA = [fig.audiograma(), fig.logo(), fig.timpanograma(), fig.dpoae()]

CASOS = [
    cuadro('nino_tpa', PERIFERIA, od='normal', oi='normal', edad=9, sexo='hombre', semilla=3,
           anamnesis="""Tiene 9 años y está en cuarto básico. La profesora dice que "se va" cuando hay ruido en la sala,
           que pide repetir las instrucciones largas y que en el dictado cambia palabras parecidas. En el recreo y en
           el comedor del colegio casi no entiende lo que le dicen. En la casa, con la tele baja, se las arregla bien.
           Es bueno para armar cosas y para los juegos de mesa. La madre cuenta que "oye cuando quiere", pero que en
           el auto no entiende a quien le habla desde atrás. Lee más lento que sus compañeros. No ha tenido dolor de
           oídos desde los 3 años.""",
           historia=[(300, 'Fonoaudióloga: lenguaje comprensivo y expresivo en rango esperado; conciencia fonológica algo baja para la edad.'),
                     (200, 'Psicóloga: capacidad cognitiva en rango medio; atención sin hallazgos importantes.'),
                     (30, 'Médico general: otoscopía normal bilateral. Se deriva a audiología por sospecha de trastorno de procesamiento auditivo.')],
           antecedentes=['otitis'], medicamentos='', cirugias=''),
    cuadro('mayor_ruido', [fig.audiograma(), fig.logo(), fig.dpoae(), fig.reflejos()],
           od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve', edad=71, sexo='mujer', semilla=2,
           anamnesis="""Tiene 71 años, es profesora jubilada y vive con su marido. Desde hace unos tres años le cuesta
           seguir las conversaciones en los almuerzos familiares y en el almacén. En silencio, en una conversación
           de a dos y por teléfono se las arregla. Dice: "oigo, pero no entiendo", y que sus nietos "hablan muy
           rápido". Se cansa al final del día de tanto esforzarse y ya evita las reuniones. Tiene un pitido leve en
           los dos oídos, a ratos. No ha tenido mareos ni asimetría. El marido nota que olvida más los nombres,
           aunque ella lo atribuye a la edad.""",
           historia=[(90, 'Médico general: otoscopía normal; audiometría de pesquisa con "audición casi normal". Se deriva a evaluación audiológica completa.')],
           antecedentes=['hta'], medicamentos='Losartán 50 mg al día'),
    cuadro('nino_otitis', [fig.audiograma(), fig.logo(), fig.timpanograma(), fig.reflejos()],
           od='disfuncion_tubaria', oi='disfuncion_tubaria', grado_od='leve', grado_oi='leve', edad=7, sexo='mujer', semilla=7,
           anamnesis="""Tiene 7 años y está en segundo básico. La profesora jefe la describe como "en las nubes": no
           responde cuando se le habla desde lejos, pide repetir y se distrae en las clases. Sugiere evaluar si tiene un
           trastorno de procesamiento auditivo. La madre cuenta que en la casa sube el volumen de la tele, que ronca
           y duerme con la boca abierta, y que se resfría seguido; en los últimos dos meses está peor. Habla bien, con
           alguna "s" poco clara. Nunca le han hecho una audiometría.""",
           historia=[(60, 'Consulta por resfrío: tímpanos "opacos", sin antibiótico; se indica control que no se hizo.'),
                     (20, 'Profesora jefe: sugiere evaluación auditiva y de "procesamiento".')],
           antecedentes=['otitis'], medicamentos='', cirugias=''),
]

if __name__ == '__main__':
    Capitulo(30).generar(CASOS)
