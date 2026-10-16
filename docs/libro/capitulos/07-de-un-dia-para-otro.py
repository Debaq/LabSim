#!/usr/bin/env python3
"""Capítulo 7 — De un día para otro.

    python3 docs/libro/capitulos/07-de-un-dia-para-otro.py              casos + figuras + PDF
    python3 docs/libro/capitulos/07-de-un-dia-para-otro.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/07-de-un-dia-para-otro.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
07-de-un-dia-para-otro.md (cada caso se nombra ahí como cap07_<nombre>).

Pérdidas bruscas: la súbita de un oído (con su curva sombra, sin y con
ruido), la laberintitis (cóclea y sáculo a la vez), la conmoción de los dos
oídos tras un golpe, la cófosis antigua por paperas (42) y la bilateral
rápidamente progresiva. La técnica en foco es el enmascaramiento.

Ojo al armar: pedir un grado DISTINTO en cada oído de un cuadro bilateral
(autoinmune severa/leve, conmoción moderada/leve) dejó el formulario sin
enviar; se pide solo el grado del oído peor y el otro lo sortea el editor.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402

CASOS = [
    # Pablo: súbita severa del OI; sin ruido parece una conductiva (curva sombra)
    cuadro('subita', [fig.acumetria(), fig.audiograma(sin_enmascarar=True), fig.audiograma(), fig.logo()],
           oi='subita', grado_oi='severa', edad=52,
           anamnesis="""Tiene 52 años y es profesor de historia en un liceo. Hace cuatro días despertó con el oído
           izquierdo tapado, "como con agua", y con un pitido agudo de ese lado que no se le ha quitado. Pensó que
           era cera y se echó unas gotas que tenía en la casa, pero siguió igual. Por la izquierda no entiende el
           celular y tuvo que cambiárselo al otro oído; en la sala de clases le cuesta saber qué alumno le está
           hablando. No tuvo dolor, secreción ni mareos. La semana anterior estuvo resfriado. Es hipertenso desde
           hace seis años y toma su remedio todos los días. Antes de esto nunca había tenido problemas de oído.""",
           historia=[(3, 'Médico general: oído izquierdo tapado y pitido desde ayer. Otoscopía normal, sin tapón de cera. Weber con diapasón lateralizado a la derecha. Se sospecha hipoacusia súbita y se deriva con urgencia a otorrinolaringología.'),
                     (1, 'Otorrinolaringólogo: probable hipoacusia súbita del OI. Inicia prednisona oral y solicita audiometría con enmascaramiento, logoaudiometría e impedanciometría. Resonancia magnética en trámite.')],
           antecedentes=['hta'],
           medicamentos='Losartán 50 mg al día. Prednisona oral desde ayer, indicada por el otorrinolaringólogo.'),
    # Irene: vértigo y pérdida profunda del OD el mismo día; VEMP del OD casi ausente
    cuadro('laberintitis', [fig.audiograma(), fig.timpanograma(), fig.vemp()],
           od='laberintitis', edad=34, sexo='mujer',
           anamnesis="""Tiene 34 años y es enfermera en un hospital. Hace tres semanas, unos días después de un
           resfrío fuerte, despertó con todo girando a su alrededor: no se podía levantar de la cama, vomitó toda la
           mañana y la llevaron a urgencias. Ese mismo día notó que el oído derecho no oía nada y que tenía un
           pitido de ese lado. El vértigo fuerte le duró unos tres días y fue pasando de a poco; hoy está mucho
           mejor, pero se siente insegura cuando gira rápido la cabeza o camina a oscuras. El pitido ahora va y
           viene. No tuvo dolor de oído, fiebre alta ni secreción, no le dolió la cabeza y no se le durmió ni se le
           debilitó ninguna parte de la cara o del cuerpo. Antes oía bien de los dos lados.""",
           historia=[(21, 'Servicio de urgencia: vértigo intenso con vómitos e hipoacusia del oído derecho desde la mañana. Nistagmo espontáneo horizontal hacia la izquierda. Otoscopía normal. Examen neurológico sin otros hallazgos. Se hospitaliza para hidratación y manejo sintomático.'),
                     (19, 'Alta: vértigo en disminución, camina sin ayuda. Se deriva a otorrinolaringología.'),
                     (12, 'Otorrinolaringólogo: probable laberintitis viral del OD. Indica tratamiento y solicita audiometría, impedanciometría y VEMP; evaluación vestibular completa en el control.')],
           medicamentos='Tomó un medicamento para el mareo los primeros días; ya no lo usa.'),
    # Juan: golpe en bicicleta, pérdida bilateral simétrica con muesca; audiometría previa normal
    cuadro('conmocion_laberintica', [fig.audiograma(), fig.timpanograma(), fig.dpoae()],
           od='conmocion_laberintica', oi='conmocion_laberintica', edad=19,
           anamnesis="""Tiene 19 años y estudia diseño. Hace tres semanas se cayó de la bicicleta de montaña bajando un
           cerro y se golpeó fuerte la cabeza contra una roca, con el casco puesto. Perdió el conocimiento unos
           segundos. Desde que despertó en la ambulancia siente los dos oídos "apagados" y un zumbido parejo en
           ambos, que no se le quita. Los primeros días andaba algo mareado, pero eso se le pasó. Le cuesta
           entender a sus compañeros en la cafetería y en las clases con ruido; en la casa, conversando, oye bien.
           No le salió sangre ni líquido por los oídos. No trabaja con ruido, no usa audífonos a volumen alto y no
           dispara. El verano pasado le hicieron una audiometría para un trabajo de temporada y salió normal.""",
           historia=[(21, 'Servicio de urgencia: traumatismo encefalocraneano por caída en bicicleta, con pérdida de conciencia breve. Tomografía de cerebro y de peñascos sin fractura ni sangrado. Otoscopía sin sangre en el conducto ni detrás del tímpano. Observación por 24 horas.'),
                     (8, 'Médico general: oídos "apagados" y zumbido bilateral desde el accidente; otoscopía normal. Se deriva a otorrinolaringología.'),
                     (2, 'Otorrinolaringólogo: probable conmoción laberíntica bilateral. Solicita audiometría, impedanciometría y emisiones otoacústicas, y la audiometría del año pasado para comparar.')],
           antecedentes=['tce']),
    # Matías: cófosis del OD por paperas a los 6 años; reflejos diagonales y VEMP del OD ausente
    demo(42, [fig.acumetria(), fig.audiograma(), fig.reflejos(), fig.vemp()]),
    # Pilar: bilateral asimétrica que avanza en semanas y responde a corticoides
    cuadro('autoinmune', [fig.audiograma(), fig.logo(), fig.dpoae()],
           od='autoinmune', oi='autoinmune', grado_od='severa', edad=41, sexo='mujer',
           anamnesis="""Tiene 41 años y es contadora. Hace unos tres meses empezó a sentir el oído derecho tapado, con
           días mejores y días peores, y pensó que era por un resfrío. En pocas semanas dejó de oír el teléfono por
           ese lado. Con unos corticoides que le dio el otorrinolaringólogo mejoró un poco, pero al terminarlos
           volvió a empeorar, y hace un mes nota que el oído izquierdo también está más tapado. Ahora le cuesta
           seguir las reuniones de trabajo y les pide a todos que le hablen más fuerte. No tiene pitidos. A veces
           se siente un poco inestable al caminar rápido. Tiene hipotiroidismo por una tiroiditis de Hashimoto y
           toma levotiroxina. En su familia nadie es sordo. No ha tenido infecciones de oído ni ha trabajado con
           ruido.""",
           historia=[(95, 'Médico general: oído derecho tapado de una semana; otoscopía normal, sin tapón. Indica descongestionante nasal y control.'),
                     (70, 'Otorrinolaringólogo: audiometría con hipoacusia sensorioneural moderada del OD y OI normal. Indica prednisona oral por dos semanas.'),
                     (40, 'Control: mejoría parcial del OD con los corticoides, que empeora al suspenderlos. Empieza a notar el OI tapado.'),
                     (6, 'Otorrinolaringólogo: hipoacusia sensorioneural bilateral, asimétrica y rápidamente progresiva. Sospecha enfermedad autoinmune del oído interno; descartar otosífilis. Solicita serología (incluida la de sífilis), exámenes inmunológicos, resonancia magnética y nueva evaluación audiológica completa. Deriva a reumatología.')],
           medicamentos='Levotiroxina 75 µg al día. Terminó hace casi dos meses un curso de prednisona de dos semanas.'),
]

if __name__ == '__main__':
    Capitulo(7).generar(CASOS)
