#!/usr/bin/env python3
"""Capítulo 11 — Asimetría que no cierra.

    python3 docs/libro/capitulos/11-asimetria-que-no-cierra.py              casos + figuras + PDF
    python3 docs/libro/capitulos/11-asimetria-que-no-cierra.py --solo-pdf   solo el PDF

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
11-asimetria-que-no-cierra.md (cada caso se nombra ahí como cap11_<nombre>).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402

# Lo que se mira en todos los casos retrococleares del capítulo
RETRO = [fig.audiograma(), fig.logo(), fig.reflejos(), fig.abr(niveles=(80, 60, 40))]

CASOS = [
    demo(39, [fig.audiograma(), fig.logo(), fig.timpanograma(), fig.reflejos(),
              fig.teoae(), fig.dpoae(), fig.abr(niveles=(80, 60, 40, 20))]),
    cuadro('schwannoma', RETRO + [fig.vemp()], od='schwannoma', grado_od='moderada', edad=52, sexo='mujer',
           anamnesis="""Tiene 52 años y es secretaria en un juzgado. Hace unos dos años nota que por el oído
           derecho "oye pero no entiende": al principio pensó que era el teléfono de la oficina, y ahora se
           cambia el celular al izquierdo sin darse cuenta. No tiene pitido en los oídos. A veces, al darse
           vuelta rápido en la cama, siente un mareo de segundos que se le pasa solo. Nunca ha tenido dolor
           ni secreción de oídos.""",
           historia=[(730, 'Control con médico general por "baja audición OD"; otoscopía normal, se indica observar.'),
                     (60, 'Otorrinolaringólogo: otoscopía normal bilateral. Se solicita audiometría e impedanciometría.')],
           antecedentes=['hta'], medicamentos='Losartán 50 mg al día'),
    cuadro('nf2', RETRO, od='nf2', oi='nf2', grado_od='moderada', grado_oi='leve', edad=24,
           anamnesis="""Tiene 24 años y estudia mecánica en un instituto. Desde los 20 nota que oye menos, sobre
           todo por el derecho: en clases se sienta adelante y aun así se pierde. Tiene un pitido en los dos
           oídos todo el día. Últimamente se tropieza más al caminar de noche. Su mamá perdió la audición de un
           oído cuando era joven y la operaron "de algo en la cabeza" a los 35 años.""",
           historia=[(1460, 'Control de salud: dificultad para oír en clases; otoscopía normal.'),
                     (30, 'Neurólogo: inestabilidad de la marcha y antecedente familiar; deriva a evaluación auditiva.')],
           antecedentes=['hipoacusia_familiar']),
    cuadro('angulo', RETRO, oi='tumor_angulo', grado_oi='leve', edad=61,
           anamnesis="""Tiene 61 años y fue chofer de buses interurbanos hasta que jubiló el año pasado. Su señora
           le dice que sube mucho el volumen de la tele; él cree que oye bien "por el derecho". Hace unos meses
           le zumba a ratos el oído izquierdo, sobre todo en la noche. No ha tenido mareos.""",
           historia=[(120, 'Médico general: hipoacusia OI referida por la familia; otoscopía normal. Se deriva a otorrinolaringología.')],
           antecedentes=['hta'], medicamentos='Enalapril 10 mg cada 12 horas'),
    cuadro('microvascular', RETRO, od='compresion_microvascular', edad=47, sexo='mujer',
           anamnesis="""Tiene 47 años y es contadora. Hace un año le apareció un zumbido en el oído derecho que va y
           viene y que empeora en el silencio de la noche. Ha tenido tres o cuatro mareos de segundos, "como un
           golpe", sin náuseas. Nota que por el derecho los sonidos agudos "suenan raro", como metálicos.""",
           historia=[(300, 'Médico general: acúfeno OD, otoscopía normal. Se indica betahistina, sin mejoría.'),
                     (40, 'Otorrinolaringólogo: solicita evaluación audiológica completa.')],
           medicamentos='Betahistina (la dejó por no notar cambios)'),
    cuadro('retrococlear', RETRO, oi='sensorioneural', grado_oi='moderada', edad=66,
           anamnesis="""Tiene 66 años, trabajó 30 años en un aserradero y hoy cuida su huerto. Hace tiempo oye
           menos por el izquierdo y tiene un pitido constante de ese lado. Hace un año compró un audífono para el
           izquierdo en una óptica, pero lo dejó en el cajón: "se oye fuerte, pero no se entiende nada".""",
           historia=[(400, 'Compra de audífono OI sin evaluación audiológica previa.'),
                     (45, 'Médico general: hipoacusia OI asimétrica con acúfeno; deriva a evaluación auditiva.')],
           antecedentes=['trauma_acustico']),
]

if __name__ == '__main__':
    Capitulo(11).generar(CASOS)
