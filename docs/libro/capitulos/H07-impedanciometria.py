#!/usr/bin/env python3
"""Herramienta H7 — Impedanciometría.

    python3 docs/libro/capitulos/<este archivo>.py              figuras + PDF
    python3 docs/libro/capitulos/<este archivo>.py --solo-pdf   solo el PDF

Una herramienta no necesita pacientes, pero puede ilustrar con algunos
(demo() o cuadro(), igual que un capítulo clínico; ver libro.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# La sonda va como texto ('226', '1000'), igual que en la app (Z.probe_freq):
# así la semilla del timpanograma es la misma que ve el alumno y la sonda de
# 1000 Hz entra por su rama en map_letter_for_probe (que compara con '1000').
Z = [fig.timpanograma(sonda='226')]
ZR = Z + [fig.reflejos()]

CASOS = [
    # Las letras de Jerger, una por paciente
    demo(34, ZR),                      # As OD (otoesclerosis): patrón conductivo
    demo(35, Z),                       # B con volumen normal (efusión)
    cuadro('retraccion', Z, od='disfuncion_tubaria', grado_od='leve', edad=29, sexo='mujer', semilla=1,
           anamnesis="""Tiene 29 años y es profesora de básica. Hace tres semanas tuvo un resfrío fuerte: el
           resfrío pasó, pero el oído derecho le quedó tapado, "como con agua", y siente que su propia voz le
           retumba. A ratos, al bostezar, se le destapa un segundo y se vuelve a tapar. Tiene rinitis alérgica
           desde chica. No le duele, no le ha salido nada del oído y no tiene zumbido.""",
           historia=[(20, 'SAPU: cuadro respiratorio alto; se indica reposo y paracetamol.'),
                     (6, 'Médico general: tímpano derecho retraído, sin líquido evidente. Indica corticoide nasal y '
                         'deriva a evaluación auditiva.')],
           medicamentos='Loratadina 10 mg cuando tiene alergia; mometasona nasal desde hace 6 días'),
    cuadro('disyuncion', Z, od='disyuncion_cadena', grado_od='moderada', edad=33,
           anamnesis="""Tiene 33 años y es repartidor en moto. Hace cuatro meses chocó y se golpeó el lado
           derecho de la cabeza; estuvo inconsciente unos minutos y lo dejaron un día en observación. Desde el
           accidente oye menos por el oído derecho, "como con algodón", y no ha mejorado. No tiene zumbido ni
           mareos. Le preocupa porque en el trabajo usa el manos libres en ese oído.""",
           historia=[(120, 'Urgencia: TEC leve por accidente de tránsito en moto; TAC de cerebro sin lesiones '
                           'agudas. Alta a las 24 horas.'),
                     (20, 'Otorrinolaringólogo: tímpano derecho íntegro, sin hemotímpano. Solicita audiometría e '
                          'impedanciometría.')],
           antecedentes=['tce']),
    # Lactante: la sonda de 226 Hz engaña, la de 1000 Hz no
    cuadro('lactante', [fig.timpanograma(sonda='226'), fig.timpanograma(sonda='1000')],
           od='efusion_neonatal', oi='normal', edad_meses=2, sexo='mujer',
           anamnesis="""Sara tiene dos meses y viene con su mamá, Esther. Nació de término, por parto normal y
           sin complicaciones, y se fue de alta a los dos días. En el tamizaje auditivo de la maternidad el
           oído derecho "no pasó" y el izquierdo sí; en el control de las tres semanas volvió a no pasar el
           derecho. Hace una semana estuvo resfriada, con mocos. La mamá cuenta que se asusta con los portazos
           y se calma cuando le habla.""",
           historia=[(58, 'Tamizaje auditivo neonatal: refiere OD, pasa OI.'),
                     (38, 'Rescreening: refiere OD, pasa OI. Se deriva a evaluación audiológica.')]),
]

if __name__ == '__main__':
    Capitulo('H7').generar(CASOS)
