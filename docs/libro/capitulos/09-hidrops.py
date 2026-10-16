#!/usr/bin/env python3
"""Capítulo 9 — Hidrops.

    python3 docs/libro/capitulos/09-hidrops.py              casos + figuras + PDF
    python3 docs/libro/capitulos/09-hidrops.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/09-hidrops.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
09-hidrops.md (cada caso se nombra ahí como cap09_<nombre>).

Dos oídos con hidrops: el Ménière de una profesora (38), con el otro oído
sano para comparar, y el hidrops retardado de quien quedó sordo de un oído
en la infancia y ahora enferma el único que oye. En los dos se lee la curva
ascendente, el reclutamiento, la electrococleografía y el VEMP cervical.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402

# Lo que se mira en un hidrops: la curva, la palabra, el reflejo (Metz),
# la electrococleografía y el sáculo
HIDROPS = [fig.audiograma(), fig.logo(), fig.reflejos(), fig.ecochg(), fig.vemp()]

CASOS = [
    # Patricia: Ménière del OI con el OD sano para comparar (Fowler, Metz,
    # electrococleografía y VEMP cervical de los dos lados)
    demo(38, HIDROPS + [fig.dpoae()]),
    # Samuel: sordo del OD desde las paperas; años después el hidrops toma el
    # único oído que oye. La ECochG del OD cofótico sale como trazo sin complejo.
    cuadro('hidrops_retardado', [fig.audiograma(), fig.acumetria(), fig.logo(), fig.reflejos(), fig.ecochg(), fig.vemp()],
           od='parotiditis', oi='hidrops_retardado', edad=54, semilla=3,
           anamnesis="""Tiene 54 años y atiende el mesón de una ferretería. Por el oído derecho no oye desde los seis
           años, cuando tuvo paperas; siempre se las arregló con el izquierdo y nunca usó audífono. Hace unos ocho
           meses tuvo la primera crisis: despertó con todo girando, vomitó y estuvo dos horas sin poder levantarse.
           Desde entonces ha tenido otras dos. Lo que más lo asusta es que, antes y después de cada crisis, el oído
           izquierdo se le tapa "como en un avión" y por unos días no entiende a los clientes ni el teléfono;
           después vuelve a oír, pero no sabe si tan bien como antes. No le zumba ningún oído. Entre crisis anda
           bien, pero ya no maneja de noche por miedo a que le dé una.""",
           historia=[(240, 'Servicio de urgencia: vértigo rotatorio de 2 horas con vómitos; se trata con antieméticos, alta al ceder.'),
                     (150, 'Médico general: oído izquierdo tapado de varios días y "oye menos"; otoscopía normal. Antecedente de sordera derecha desde la infancia (parotiditis). Se deriva a otorrinolaringología.'),
                     (45, 'Nueva crisis de vértigo de 3 horas, con el oído izquierdo tapado.'),
                     (15, 'Otorrinolaringólogo: otoscopía normal. Solicita evaluación auditiva completa, electrococleografía y evaluación vestibular.')],
           medicamentos='Dimenhidrinato 50 mg cuando tiene crisis'),
]

if __name__ == '__main__':
    Capitulo(9).generar(CASOS)
