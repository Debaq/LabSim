#!/usr/bin/env python3
"""Capítulo 4 — Rigidez.

    python3 docs/libro/capitulos/04-rigidez.py              casos + figuras + PDF
    python3 docs/libro/capitulos/04-rigidez.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/04-rigidez.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
04-rigidez.md (cada caso se nombra ahí como cap04_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Un oído rígido se mira con el gap, el diapasón, la curva y los reflejos
RIGIDEZ = [fig.audiograma(), fig.acumetria(), fig.timpanograma(), fig.reflejos()]
SIN_ACUMETRIA = [fig.audiograma(), fig.timpanograma(), fig.reflejos()]

CASOS = [
    demo(34, RIGIDEZ),
    cuadro('fijacion_congenita_estribo', RIGIDEZ, od='fijacion_congenita_estribo', oi='fijacion_congenita_estribo',
           grado_od='moderada', grado_oi='leve', semilla=2, edad=9, sexo='hombre',
           anamnesis="""Pepe tiene 9 años y está en cuarto básico. Viene con su papá, porque en el control de
           audición que hicieron en el colegio no pasó por ninguno de los dos oídos. La profesora jefe dice que
           se distrae cuando le hablan desde atrás y que siempre pide que le repitan. En la casa ven la tele
           fuerte desde que el papá se acuerda: dice que Pepe "siempre ha sido así", desde chiquito, y que no lo
           ha notado peor con los años. Empezó a hablar a la misma edad que su hermana, pero en el kínder fue a
           fonoaudiólogo porque le costaban algunos sonidos. Nunca ha tenido otitis ni le ha salido líquido de
           los oídos, y no se queja de zumbidos ni de mareos. Nació de término, sin complicaciones; los papás no
           recuerdan si le hicieron un examen de audición al nacer. En la familia nadie usa audífonos ni se ha
           operado de los oídos.""",
           historia=[(60, 'Control de audición escolar: no pasa en el oído derecho ni en el izquierdo. Se deriva a otorrinolaringología.'),
                     (14, 'Otorrinolaringólogo: conductos limpios y tímpanos de aspecto normal en los dos lados. Solicita audiometría e impedanciometría.')]),
    cuadro('paget', SIN_ACUMETRIA, od='paget', oi='paget', grado_od='moderada', grado_oi='moderada', edad=71, sexo='hombre',
           semilla=1,
           anamnesis="""Adrián tiene 71 años y es contador jubilado. Hace unos diez años empezó a oír menos de los
           dos oídos, de a poco, y ahora le cuesta seguir la conversación en la mesa cuando están todos los
           nietos; su señora dice que pone la tele demasiado fuerte. A ratos le zumban los dos oídos, con un ruido
           grave. Hace seis años consultó por dolor en la cadera derecha y dolores de cabeza, y el internista le
           encontró una enfermedad de Paget en la pelvis y en el cráneo; por esos años se dio cuenta de que los
           sombreros ya no le quedaban. Lo trataron con una infusión de ácido zoledrónico y el dolor mejoró. No ha
           tenido vértigo ni otitis, no ha trabajado en ruido y nunca ha usado audífonos. Viene porque su hija
           insistió.""",
           historia=[(2190, 'Medicina interna: dolor de cadera derecha y cefalea. Fosfatasa alcalina elevada; cintigrafía ósea con captación en pelvis y cráneo. Enfermedad de Paget ósea; se indica ácido zoledrónico endovenoso.'),
                     (30, 'Otorrinolaringólogo: hipoacusia bilateral lentamente progresiva. Conductos y tímpanos normales. Solicita audiometría e impedanciometría.')],
           antecedentes=['hta'], medicamentos='Losartán 50 mg al día. Ácido zoledrónico endovenoso, una dosis hace seis años.'),
]

if __name__ == '__main__':
    Capitulo(4).generar(CASOS)
