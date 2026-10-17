#!/usr/bin/env python3
"""Capítulo 31 — Compensar una neuritis.

    python3 docs/libro/capitulos/31-compensar-una-neuritis.py              casos + figuras + PDF
    python3 docs/libro/capitulos/31-compensar-una-neuritis.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/31-compensar-una-neuritis.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
31-compensar-una-neuritis.md (cada caso se nombra ahí como cap31_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo vestibular del capítulo (vHIT, DHI, agudeza visual dinámica, batería de H19) no es de LabSim: son las
# tablas con "cifras inventadas para el libro" y las hojas de seguimiento de ilustraciones/hacer_cap31.py.
# De LabSim salen la ficha, la anamnesis, el audiograma y el VEMP de cada caso (audición normal: la neuritis
# no toca la cóclea).
CASOS = [
    cuadro('buena', [fig.audiograma(), fig.vemp()], od='normal', oi='normal', edad=41, sexo='hombre',
           anamnesis="""Tiene 41 años y es conductor de un camión de reparto de bebidas. Hace dos semanas despertó con la pieza
           girando, vomitó cuatro veces y no pudo ponerse de pie sin agarrarse. En urgencia le dijeron que era un cuadro del
           nervio del equilibrio del lado derecho. El giro se fue en cuatro días; hoy, en reposo, no gira nada. Pero al
           mover la cabeza rápido "las cosas se corren", camina como "pisando algodón", se marea al agacharse y no se atreve
           a subir la escalerilla del camión. Lo primero que quiere saber es cuándo puede volver a manejar. Hizo reposo los
           primeros tres días y desde el quinto camina por la casa y por la cuadra. No ha tenido pitido ni cambio de la
           audición, ni dolor de cabeza, ni visión doble.""",
           historia=[(14, 'Servicio de urgencia: vértigo con vómitos, nistagmo hacia la izquierda; diagnóstico de neuritis vestibular derecha. Antiemético por tres días.'),
                     (4, 'Otorrinolaringólogo: confirma la hipofunción vestibular derecha con el examen y lo deriva a rehabilitación vestibular.')],
           medicamentos='Ninguno (el antiemético lo terminó a los tres días)'),
    cuadro('lenta', [fig.audiograma()], od='normal', oi='normal', edad=63, sexo='mujer',
           anamnesis="""Tiene 63 años y es costurera jubilada. Hace cinco semanas despertó con la pieza girando y vomitando; en
           urgencia le dijeron que era un problema del nervio del equilibrio del lado izquierdo, le dieron unas pastillas
           para el mareo y le recomendaron reposo. Las sigue tomando tres veces al día "porque si no, me marea", y casi no
           sale del sillón: su hijo hace las compras, y para ir al baño usa un bastón que era de su marido. Cuando tiene que
           mirar hacia un lado, gira todo el cuerpo. Hace unos diez días se cayó de noche al levantarse al baño, sin lesión,
           y desde entonces tiene más miedo. Dice que ya no gira nada, pero que "no se siente firme" y que ver la televisión
           con la cabeza movida la marea. Oye igual que siempre, sin pitido ni dolor.""",
           historia=[(35, 'Servicio de urgencia: vértigo con vómitos; diagnóstico de neuritis vestibular izquierda. Se indican dimenhidrinato cada 8 horas y reposo.'),
                     (10, 'Caída nocturna sin lesión.'),
                     (5, 'Médico de familia: persiste inestabilidad; solicita examen vestibular y deriva a rehabilitación vestibular.')],
           medicamentos='Dimenhidrinato 50 mg cada 8 horas (desde hace cinco semanas); losartán 50 mg al día', antecedentes=['hta']),
    cuadro('meseta', [fig.audiograma()], od='normal', oi='normal', edad=33, sexo='hombre',
           anamnesis="""Tiene 33 años y es diseñador de software; trabaja frente a dos pantallas. Hace diez semanas tuvo un vértigo
           muy intenso con vómitos, que le diagnosticaron como neuritis vestibular derecha. Empezó los ejercicios a las dos
           semanas y al principio mejoró bastante. Pero desde hace unas cuatro semanas siente que no avanza: un mareo suave
           y constante, "como flotando", que no gira. Es peor frente a las pantallas, en el supermercado, en el metro lleno
           y en una calle con mucho tráfico, y mejora acostado o cuando se concentra en algo. Dejó de tomar el metro, trabaja
           desde la casa y cada vez que se marea piensa que va a volver el vértigo. Hace los ejercicios "cuando me siento
           bien", porque los días malos lo marean más. Duerme mal. Oye igual que siempre, sin pitido.""",
           historia=[(70, 'Servicio de urgencia: vértigo intenso con vómitos y nistagmo; diagnóstico de neuritis vestibular derecha. Antiemético por tres días.'),
                     (56, 'Inicia rehabilitación vestibular con ejercicios en la casa.'),
                     (10, 'Otorrinolaringólogo: sin vértigo; refiere mareo persistente; solicita control del examen vestibular.')],
           medicamentos='Ninguno'),
]

if __name__ == '__main__':
    Capitulo(31).generar(CASOS)
