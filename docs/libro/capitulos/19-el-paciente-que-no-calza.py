#!/usr/bin/env python3
"""Capítulo 19 — El paciente que no calza.

    python3 docs/libro/capitulos/19-el-paciente-que-no-calza.py              casos + figuras + PDF
    python3 docs/libro/capitulos/19-el-paciente-que-no-calza.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/19-el-paciente-que-no-calza.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
19-el-paciente-que-no-calza.md (cada caso se nombra ahí como cap19_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Objetivas: lo que no depende de que el paciente levante la mano
OBJETIVAS = [fig.timpanograma(), fig.reflejos(), fig.teoae(), fig.dpoae(),
             fig.abr(niveles=(80, 60, 40, 20))]

CASOS = [
    cuadro('unilateral', OBJETIVAS, od='normal', oi='normal', edad=44, sexo='hombre',
           anamnesis="""Tiene 44 años y trabaja de maestro de obra. Hace tres semanas, en la faena, le cayó una
           plancha de zinc desde un andamio y le pegó en el costado derecho de la cabeza; no perdió el conocimiento
           ni sangró por el oído. Desde ese día dice que "no escucha nada" por el oído derecho. Conversa en la
           consulta sin acercar la cabeza ni pedir que le repitan, aun cuando el entrevistador le habla a media voz
           desde su lado derecho. No tiene pitido, mareo ni dolor. Su empleador le pidió un certificado y la mutual
           lo derivó a evaluación auditiva.""",
           historia=[(21, 'Urgencia de la mutual: contusión parietal derecha, tomografía de cráneo normal, otoscopía normal bilateral.'),
                     (7, 'Control con médico laboral: refiere hipoacusia derecha total; se deriva a otorrinolaringología y evaluación auditiva.')],
           antecedentes=['tce']),
    cuadro('sobre_real', [fig.audiograma(), fig.timpanograma(), fig.reflejos(), fig.teoae(),
                          fig.abr(niveles=(80, 60, 40, 20))],
           od='nihl_cronica', oi='nihl_cronica', grado_od='leve', grado_oi='leve', edad=52, sexo='hombre',
           anamnesis="""Tiene 52 años y desde hace 25 maneja una grúa horquilla en una planta de aserrío, sin
           protección auditiva constante hasta hace unos años. Hace dos meses la empresa inició un proceso de
           reevaluación de su puesto y desde entonces dice oír "casi nada" por los dos oídos: pide que le escriban las
           indicaciones y no contesta si no lo miran de frente. En la sala de espera, sin embargo, atendió una
           llamada de su señora con el celular en el oído izquierdo. No tiene pitido ni mareo.""",
           historia=[(2200, 'Audiometría de ingreso a la empresa: caída en agudos bilateral compatible con ruido.'),
                     (60, 'Médico laboral: refiere empeoramiento rápido de la audición bilateral; se solicita audiometría y estudio objetivo.')],
           antecedentes=['trauma_acustico']),
    cuadro('nina', [fig.timpanograma(), fig.reflejos(), fig.teoae(), fig.dpoae()], od='normal', oi='normal',
           edad=11, sexo='mujer',
           anamnesis="""Tiene 11 años y va en sexto básico. La profesora jefe avisó a los padres que "no oye" en la
           sala: no responde cuando le hablan desde atrás y pide repetir todo. En el tamizaje del colegio no
           respondió a ningún tono. Los padres cuentan que desde hace unas semanas ella está muy angustiada: sus
           padres se están separando y cambió de curso en marzo. En la casa responde cuando la llaman desde la cocina
           y se ríe con los dibujos de la tele a volumen bajo. Nunca ha tenido dolor de oídos ni secreción; no tiene
           pitido.""",
           historia=[(25, 'Tamizaje escolar de audición: sin respuesta bilateral.'),
                     (10, 'Pediatra: otoscopía normal, sin fiebre ni otitis; se deriva a evaluación auditiva.')]),
    demo(42, [fig.audiograma(sin_enmascarar=True), fig.audiograma(), fig.logo(), fig.reflejos(), fig.teoae(),
              fig.abr(niveles=(90, 80))]),
]

if __name__ == '__main__':
    Capitulo(19).generar(CASOS)
