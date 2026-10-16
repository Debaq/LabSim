#!/usr/bin/env python3
"""Capítulo 5 — Envejecer oyendo.

    python3 docs/libro/capitulos/05-envejecer-oyendo.py              casos + figuras + PDF
    python3 docs/libro/capitulos/05-envejecer-oyendo.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/05-envejecer-oyendo.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
05-envejecer-oyendo.md (cada caso se nombra ahí como cap05_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# La cóclea que envejece: el umbral con su LDL, la palabra y lo que queda de las CCE
COCLEA = [fig.audiograma(), fig.logo(), fig.dpoae()]

CASOS = [
    demo(36, COCLEA),
    # Semilla 1: la curva sale casi igual a la de Hernán (74 años) en una mujer
    # de 56, simétrica (diferencias de 10 dB como máximo) y con roll-over leve.
    # El logo sin enmascarar muestra la curva sombra al buscar el roll-over.
    cuadro('metabolica', [fig.audiograma(), fig.logo(), fig.logo(enmascarado=False), fig.dpoae()],
           od='metabolica', oi='metabolica', grado_od='leve', grado_oi='leve',
           edad=56, sexo='mujer', semilla=1,
           anamnesis="""Tiene 56 años y es secretaria en la oficina de un colegio. Tiene diabetes tipo 2 desde
           los 41 años; los primeros años no se cuidó mucho y hoy se pone insulina en la noche. Hace dos años
           le trataron la retina con láser y el año pasado el nefrólogo le dijo que los riñones le están
           funcionando "a medias". Desde hace unos dos años siente un siseo en los dos oídos, parejo, todo el
           día, que nota más en la noche. Le cuesta entender en las reuniones de apoderados y cuando hablan
           varios a la vez; por teléfono se arregla bien. Cree que "es la edad", porque su mamá usó audífonos
           desde los 80. Nunca ha trabajado con ruido, no ha tenido mareos ni otitis y no recuerda haber
           estado hospitalizada.""",
           historia=[(730, 'Oftalmólogo: retinopatía diabética no proliferativa en ambos ojos; fotocoagulación con láser.'),
                     (300, 'Nefrólogo: enfermedad renal crónica etapa 3a por nefropatía diabética. Ajusta la dosis de metformina y mantiene losartán.'),
                     (60, 'Médico de familia, control cardiovascular: refiere zumbido en ambos oídos y dificultad para entender en grupo. Otoscopía normal. Deriva a otorrinolaringología.'),
                     (15, 'Otorrinolaringólogo: otoscopía normal bilateral. Solicita audiometría con logoaudiometría y emisiones otoacústicas.')],
           antecedentes=['diabetes', 'hta'],
           medicamentos='Metformina 850 mg al día; insulina glargina 22 unidades en la noche; losartán 50 mg cada 12 horas'),
]

if __name__ == '__main__':
    Capitulo(5).generar(CASOS)
