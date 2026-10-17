#!/usr/bin/env python3
"""Capítulo 12 — El tronco.

    python3 docs/libro/capitulos/12-el-tronco.py              casos + figuras + PDF
    python3 docs/libro/capitulos/12-el-tronco.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/12-el-tronco.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
12-el-tronco.md (cada caso se nombra ahí como cap12_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Lo que se mira en los casos: el PEAT a la tasa de rutina y, aparte, a tasa alta
TASA_ALTA = fig.abr(niveles=(80,), tasa=81.1)
BASE = [fig.audiograma(), fig.reflejos(), fig.abr(niveles=(80, 60, 40)), TASA_ALTA]

CASOS = [
    cuadro('esclerosis_multiple', BASE, od='esclerosis_multiple', oi='esclerosis_multiple', edad=34, sexo='mujer',
           semilla=11,
           anamnesis="""Tiene 34 años y es educadora de párvulos. Hace ocho meses vio doble durante tres semanas y
           se le durmió la pierna izquierda; se le pasó sola y no volvió a consultar. Hace poco, después de un turno
           largo, le volvió un hormigueo en la mano derecha y una fatiga que no se le quita con el descanso. Dice que
           oye bien, que no tiene pitidos ni mareos: viene porque la neuróloga, que sospecha una enfermedad
           desmielinizante, le pidió potenciales evocados mientras se consigue hora para la resonancia, que tiene lista
           de espera de varios meses.""",
           historia=[(240, 'Urgencia: visión doble y adormecimiento de la pierna izquierda; se indica observación y control.'),
                     (45, 'Neurología: examen con signos piramidales leves; solicita resonancia y potenciales evocados visuales, auditivos de tronco y somatosensoriales.')]),
    cuadro('infarto_aica', BASE + [fig.logo(), fig.vemp()], od='infarto_aica', grado_od='moderada', edad=63,
           antecedentes=['hta', 'diabetes'], medicamentos='Enalapril 10 mg cada 12 horas; metformina 850 mg cada 12 horas',
           anamnesis="""Tiene 63 años y es taxista. Hace seis días, al levantarse, sintió que la pieza giraba, vomitó
           varias veces y notó que el oído derecho "se había apagado". Se agarraba de las paredes para caminar y la
           comisura derecha de la boca le quedó caída. El mareo fuerte cedió en un par de días, pero la audición del
           derecho no volvió y sigue inestable al caminar. No tiene pitido. Lo atendieron en un servicio de urgencia
           como "sordera súbita con laberintitis" y lo derivan con prioridad.""",
           historia=[(6, 'Urgencia: vértigo intenso, vómitos, hipoacusia derecha y parálisis facial derecha de inicio brusco. Se indica corticoide oral y reposo.'),
                     (2, 'Otorrinolaringología: solicita audiometría y potenciales evocados con prioridad.')]),
    cuadro('glioma_tronco', BASE, od='glioma_tronco', oi='glioma_tronco', grado_od='leve', grado_oi='leve', edad=7, sexo='mujer',
           anamnesis="""Es una niña de 7 años que cursa segundo básico. Su mamá cuenta que desde hace unas seis semanas
           se tropieza y se le caen las cosas, que se queja de dolor de cabeza al despertar y que a veces "se le va
           un ojo hacia adentro". En la sala la profesora dice que "no escucha cuando la llaman". La pediatra pidió
           una resonancia, que está en lista de espera porque necesita sedación, y adelantó la evaluación auditiva.""",
           historia=[(40, 'Pediatría: torpeza progresiva, cefalea matinal y desviación ocular intermitente; solicita resonancia con sedación y evaluación auditiva.')]),
    cuadro('siderosis', BASE + [fig.logo(), fig.vemp()], od='siderosis', oi='siderosis', grado_od='leve', grado_oi='leve', edad=58,
           antecedentes=['tce'], cirugias='Drenaje de hematoma subdural hace 24 años',
           anamnesis="""Tiene 58 años y es contador. Hace unos tres años nota que oye menos por los dos oídos y que en
           las reuniones "oye pero no entiende". Tiene un zumbido agudo permanente en ambos oídos. Su señora dice que
           camina como "pisando algodón" y que se le ha enredado la letra. A los 34 años se cayó de un andamio, estuvo
           dos días inconsciente y lo operaron de un hematoma en la cabeza; después no tuvo secuelas. No toma
           medicamentos y nunca ha trabajado con ruido.""",
           historia=[(900, 'Médico general: hipoacusia bilateral, se atribuye a la edad.'),
                     (60, 'Otorrinolaringología: hipoacusia bilateral progresiva con inestabilidad; solicita evaluación auditiva completa.')]),
    cuadro('hic_idiopatica', BASE, od='hic_idiopatica', oi='hic_idiopatica', edad=29, sexo='mujer',
           anamnesis="""Tiene 29 años y es diseñadora gráfica. Hace cuatro meses le apareció un zumbido grave en los dos
           oídos que "late" con el pulso y que se calma cuando se tiende de lado. Oye como si tuviera los oídos tapados,
           sobre todo en las mañanas. Tiene dolor de cabeza casi todos los días y, de vez en cuando, la vista se le
           nubla unos segundos al agacharse. En el último año subió 15 kilos. Sin vértigo ni crisis de horas.
           El médico general pensó en Ménière y la envía a evaluación auditiva.""",
           historia=[(120, 'Médico general: acúfeno bilateral y sensación de oído tapado; se indica betahistina.'),
                     (30, 'Médico general: sin mejoría; deriva a evaluación auditiva por sospecha de hidrops.')],
           medicamentos='Betahistina 16 mg cada 8 horas (sin mejoría)'),
]

if __name__ == '__main__':
    Capitulo(12).generar(CASOS)
