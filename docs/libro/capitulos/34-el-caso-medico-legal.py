#!/usr/bin/env python3
"""Capítulo 34 — El caso médico-legal.

    python3 docs/libro/capitulos/34-el-caso-medico-legal.py              casos + figuras + PDF
    python3 docs/libro/capitulos/34-el-caso-medico-legal.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/34-el-caso-medico-legal.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
34-el-caso-medico-legal.md (cada caso se nombra ahí como cap34_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

CASOS = [
    cuadro('exagera', [fig.audiograma(), fig.timpanograma(), fig.reflejos(), fig.teoae(),
                       fig.abr(niveles=(80, 60, 40, 20)),
                       fig.abr(niveles=(60, 40, 20), estimulo='Burst 500 Hz')],
           od='nihl_cronica', oi='nihl_cronica', grado_od='leve', grado_oi='leve', edad=51, sexo='hombre',
           anamnesis="""Tiene 51 años y hace 24 opera una chancadora en una cantera. Hasta hace unos años usó protección
           auditiva solo a ratos. Cuenta que hace tres meses, durante una tronadura, "se le fue el oído derecho" y
           desde entonces dice no oír nada por ese lado y muy poco por el izquierdo. En la sala de espera contestó
           sin dificultad cuando lo llamaron de espaldas y en la entrevista no pide que le repitan las preguntas.
           Tiene un siseo en los dos oídos, que viene y va desde hace años. No tiene mareo, dolor ni secreción. Su
           caso está en trámite en la mutual y el médico laboral solicitó una evaluación audiológica médico-legal.""",
           historia=[(2200, 'Audiometría de ingreso al programa de vigilancia: caída en agudos bilateral compatible con ruido.'),
                     (90, 'Urgencia de la mutual tras una tronadura: otoscopía normal bilateral, sin otorragia; se indica control.'),
                     (20, 'Médico laboral: refiere sordera total derecha; se solicita evaluación audiológica médico-legal.')],
           antecedentes=['trauma_acustico']),
    cuadro('hidrops', [fig.audiograma(), fig.logo(), fig.timpanograma(), fig.teoae(), fig.ecochg(),
                       fig.abr(niveles=(80, 60, 40))],
           od='normal', oi='meniere', grado_oi='moderada', edad=54, sexo='hombre',
           anamnesis="""Tiene 54 años y hace 26 trabaja como operador de prensa en una metalmecánica, con protección
           auditiva a ratos. Desde hace año y medio tiene episodios de vértigo con náuseas que duran horas, con
           sensación de oído tapado y un zumbido grave, siempre en el oído izquierdo; entre episodios la audición
           de ese lado "sube y baja". El derecho lo oye bien. Atribuye todo al ruido de la planta: "la empresa me dejó
           sordo de este oído", y solicita que se le califique como enfermedad profesional.""",
           historia=[(1100, 'Audiometría de vigilancia: umbrales normales en ambos oídos con leve caída en 6 y 8 kHz.'),
                     (120, 'Primera crisis de vértigo con náuseas, unas tres horas; urgencia sin focalidad neurológica.'),
                     (30, 'Audiometría de control con pérdida de graves en el OI; se solicita evaluación audiológica médico-legal.')],
           antecedentes=['hta'], medicamentos='Enalapril 10 mg al día'),
    cuadro('honesto', [fig.audiograma(), fig.logo(), fig.timpanograma(), fig.teoae(), fig.dpoae()],
           od='nihl_cronica', oi='nihl_cronica', grado_od='leve', grado_oi='leve', edad=63, sexo='hombre',
           anamnesis="""Tiene 63 años y trabajó 31 años en una fundición, junto a los hornos y las moldeadoras, hasta que
           se jubiló hace ocho. Usó protección auditiva de forma irregular. Dice que ahora entiende mal en reuniones
           familiares y en la televisión, y que nunca ha usado audífonos. No tiene pitido, mareo, dolor ni secreción
           de oídos. Pide una reevaluación de su audición porque su mutual le reconoció una incapacidad al jubilar y
           quiere saber si hoy es mayor.""",
           historia=[(2920, 'Audiometría de egreso al jubilar: caída bilateral en agudos, compatible con ruido.'),
                     (1500, 'Sin controles audiológicos desde entonces.'),
                     (30, 'Solicitud de reevaluación a la mutual: se pide audiometría con estudio objetivo.')],
           antecedentes=['trauma_acustico']),
]

if __name__ == '__main__':
    Capitulo(34).generar(CASOS)
