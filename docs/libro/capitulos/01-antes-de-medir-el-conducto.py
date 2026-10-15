#!/usr/bin/env python3
"""Capítulo 1 — Antes de medir: el conducto.

    python3 docs/libro/capitulos/01-antes-de-medir-el-conducto.py              casos + figuras + PDF
    python3 docs/libro/capitulos/01-antes-de-medir-el-conducto.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/01-antes-de-medir-el-conducto.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
01-antes-de-medir-el-conducto.md (cada caso se nombra ahí como cap01_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo que se mira en este capítulo: acumetría (el diapasón no entra al conducto)
# y la audiometría por vía aérea con fonos supraaurales y por vía ósea. La otitis
# externa no lleva figuras: hoy no se mide (la acumetría va en el texto). Sin
# reflejos: en estos oídos la sonda no se pone (conducto ocluido, inflamado,
# con un cuerpo extraño, sin conducto o con una masa). El tapón sí lleva su
# timpanograma: es lo que se obtiene si igual se mide (plano con volumen
# bajo), y enseña a leer el volumen antes que la letra.
ACU_AUDIO = [fig.acumetria(), fig.audiograma()]
TAPON = ACU_AUDIO + [fig.timpanograma(sonda='226')]

CASOS = [
    cuadro('tapon_cerumen', TAPON, od='tapon_cerumen', edad=58,
           anamnesis="""Tiene 58 años y es profesor de historia en un liceo. Hace tres semanas, al salir de la ducha,
           sintió el oído derecho "tapado", y así sigue: oye su propia voz como dentro de un tarro. Se limpia los
           oídos con cotonitos todos los días "porque le pica". Fue a una tienda que hacía audiometrías gratis; le
           dijeron que había perdido audición del oído derecho y le ofrecieron un audífono. Antes de comprarlo
           consultó a su médico. No le duele, no le supura y nunca lo han operado de los oídos.""",
           historia=[(18, 'Tienda de audífonos: audiometría "hipoacusia OD, se sugiere adaptación de audífono". No registra otoscopía.'),
                     (6, 'Médico general: deriva a evaluación auditiva antes de adaptar un audífono.')],
           antecedentes=['hta'], medicamentos='Losartán 50 mg al día'),
    cuadro('cuerpo_extrano_cae', ACU_AUDIO, oi='cuerpo_extrano_cae', edad=31,
           anamnesis="""Tiene 31 años y trabaja en el aserradero de una planta de paneles. En la faena usa tapones de
           espuma. Hace una semana, al sacárselos después del turno, sintió que en el oído izquierdo "quedó algo";
           desde entonces lo siente lleno, como con agua, y al masticar le cruje. Intentó sacárselo con un cotonito y
           después con un clip, sin resultado. No le duele ni le supura. Lo mandaron de la empresa porque salió mal
           en la audiometría anual.""",
           historia=[(5, 'Vigilancia por ruido (audiometría en la empresa): "OI alterado; derivar a evaluación". No registra otoscopía.')]),
    cuadro('otitis_externa', [], od='otitis_externa', edad=22, sexo='mujer',
           anamnesis="""Tiene 22 años, estudia pedagogía en educación física y nada en la piscina universitaria cuatro
           veces por semana. Hace cinco días le empezó a picar el oído derecho; desde hace tres le duele, sobre todo
           al masticar y al apoyar ese lado en la almohada, y lo siente tapado. Ayer en la mañana tenía la almohada
           manchada con un líquido amarillento. Viene a la hora de audiometría que le dejaron en el servicio de
           urgencia.""",
           historia=[(2, 'Servicio de urgencia: otalgia OD. Se indican gotas óticas antibióticas e ibuprofeno; se deja hora de audiometría por "oído tapado".')],
           medicamentos='Gotas óticas antibióticas (desde hace dos días); ibuprofeno si duele'),
    cuadro('estenosis_atresia_cae', ACU_AUDIO, od='estenosis_atresia_cae', grado_od='moderada', edad=8,
           anamnesis="""Ramón tiene 8 años y viene con su mamá, Rocío. Nació con la oreja derecha pequeña y sin el
           agujero del oído. El tamizaje auditivo lo pasó por el izquierdo; por el derecho no se pudo hacer. Habla
           bien y le va bien en el colegio, pero se sienta con el oído izquierdo hacia la profesora y en el patio no
           sabe de dónde lo llaman. Su otorrinolaringólogo lo deriva para una audiometría antes de decidir el
           tratamiento del oído derecho.""",
           historia=[(2900, 'Maternidad: microtia y ausencia de conducto auditivo derecho. Tamizaje auditivo: pasa OI, OD no evaluable. Se deriva a otorrinolaringología.'),
                     (45, 'Otorrinolaringólogo: control; solicita audiometría con vía ósea para definir el tratamiento del OD.')]),
    cuadro('carcinoma_cae', ACU_AUDIO, oi='carcinoma_cae', grado_oi='moderada', edad=69,
           anamnesis="""Tiene 69 años y es agricultor jubilado. Desde joven le supura el oído izquierdo de vez en
           cuando. Hace cuatro meses le empezó a doler, cada vez más y sobre todo de noche; ahora la secreción viene
           con sangre y tiene mal olor. Lo han tratado dos veces con gotas por una otitis externa, sin mejoría. Oye
           menos por el izquierdo y a ratos le sisean los dos oídos.""",
           historia=[(120, 'Médico general: otitis externa OI. Gotas óticas antibióticas.'),
                     (50, 'Médico general: otorrea OI persistente; segundo curso de gotas. Sin mejoría.'),
                     (12, 'Médico general: otalgia nocturna y otorrea con sangre; deriva a otorrinolaringología y solicita audiometría.')],
           antecedentes=['otitis', 'diabetes'], medicamentos='Metformina 850 mg dos veces al día'),
]

if __name__ == '__main__':
    Capitulo(1).generar(CASOS)
