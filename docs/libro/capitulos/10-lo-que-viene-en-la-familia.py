#!/usr/bin/env python3
"""Capítulo 10 — Lo que viene en la familia.

    python3 docs/libro/capitulos/10-lo-que-viene-en-la-familia.py              casos + figuras + PDF
    python3 docs/libro/capitulos/10-lo-que-viene-en-la-familia.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/10-lo-que-viene-en-la-familia.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
10-lo-que-viene-en-la-familia.md (cada caso se nombra ahí como cap10_<nombre>).

Cinco hipoacusias genéticas, de la cuna a la adolescencia: tres niños que se
estudian con las técnicas de H8 (juego condicionado, VRA y la prueba
cruzada) y dos adolescentes en que el audiograma se lee junto a un órgano que
no es el oído (el riñón en el Alport, la retina en el Usher). Jervell-Lange-
Nielsen y Stickler van en la tabla de la Patología, sin caso propio.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Ganancia funcional de los audífonos de Adrián (la declara el capítulo: el
# campo libre con audífono no sale del caso, ver figuras/motor/campo_libre.py)
GANANCIA_ADRIAN = {250: 25, 500: 35, 1000: 40, 2000: 45, 3000: 45, 4000: 50, 6000: 45}

CASOS = [
    # Adrián, 3 años: GJB2 35delG conocido, con audífonos; control por juego
    # condicionado que muestra progresión; la mamá embarazada pregunta
    cuadro('gjb2', [fig.audiograma(ldl=False), fig.timpanograma(), fig.teoae(),
                    fig.campo_libre(ganancia=GANANCIA_ADRIAN)],
           od='gjb2', oi='gjb2', grado_od='severa', grado_oi='severa', edad=3, sexo='hombre',
           anamnesis="""Adrián tiene 3 años y viene con su mamá a su control de audición. Al nacer no pasó el
           tamizaje auditivo en ninguno de los dos oídos, y a los dos meses los potenciales confirmaron una
           hipoacusia en ambos. El estudio genético mostró dos copias de la misma variante del gen de la
           conexina 26 (GJB2). Usa audífonos en los dos oídos desde los 5 meses, va a un jardín infantil y tiene
           fonoaudióloga. Dice frases de dos palabras y entiende órdenes simples. La mamá y el papá oyen bien; un
           primo de la mamá es sordo desde niño. Hace unos dos meses la mamá nota que, con los audífonos
           puestos, ya no se da vuelta cuando lo llaman desde la cocina, y la educadora dice que en el jardín
           está "más en su mundo". No ha tenido otitis ni resfríos en el último mes. La mamá está embarazada de
           14 semanas y quiere saber si su próximo hijo puede nacer igual.""",
           historia=[(1125, 'Tamizaje auditivo neonatal con emisiones otoacústicas: refiere en ambos oídos. '
                            'Repetición al mes: refiere en ambos oídos.'),
                     (1065, 'PEAT con click y tone burst: umbral de la onda V en 70 dB nHL en ambos oídos; '
                            'timpanometría con sonda de 1.000 Hz normal. Hipoacusia sensorioneural bilateral.'),
                     (1040, 'Genética: homocigoto para c.35delG en GJB2. Hipoacusia no sindrómica autosómica '
                            'recesiva. Consejo genético a los padres.'),
                     (980, 'Adaptación de audífonos retroauriculares bilaterales.'),
                     (365, 'Audiometría por refuerzo visual con insertos: niveles mínimos de respuesta de 60 a '
                           '65 dB HL de 500 a 4.000 Hz en ambos oídos.'),
                     (60, 'Pediatra: la mamá nota que responde menos con los audífonos. Deriva a control '
                          'audiológico.')],
           antecedentes=['hipoacusia_familiar']),
    # Lorena, 8 meses: Waardenburg (mechón blanco y heterocromía, como el
    # papá); refirió el tamizaje y llega tarde; la VRA no condiciona con sonido
    cuadro('waardenburg', [fig.timpanograma(), fig.reflejos(), fig.teoae(), fig.abr(niveles=(90,))],
           od='waardenburg', oi='waardenburg', grado_od='profunda', grado_oi='profunda', edad_meses=8,
           sexo='mujer',
           anamnesis="""Lorena tiene 8 meses y la trae su mamá. Nació de término, por parto normal, sin
           complicaciones ni días en neonatología. No pasó el tamizaje auditivo en ninguno de los dos oídos, ni
           al nacer ni en la repetición, y la derivaron a diagnóstico; por la lista de espera llega recién ahora.
           La mamá cuenta que Lorena no se asusta con los portazos ni con la aspiradora, y que despierta cuando la
           tocan pero no cuando la llaman. Balbucea menos que su hermano mayor a la misma edad. Se sienta sola
           desde hace un mes. Nació con un mechón de pelo blanco sobre la frente y con un ojo azul y el otro café.
           El papá tiene el mismo mechón blanco desde chico y oye bien; la abuela paterna era sorda de un oído y
           tenía canas desde los veinte años.""",
           historia=[(240, 'Tamizaje auditivo neonatal con emisiones otoacústicas: refiere en ambos oídos.'),
                     (210, 'Repetición del tamizaje con emisiones: refiere en ambos oídos. Se deriva a '
                           'diagnóstico audiológico.'),
                     (20, 'Pediatra, control de los 8 meses: no reacciona a ruidos fuertes; heterocromía de iris '
                          'y mechón blanco frontal. Solicita evaluación audiológica completa e interconsulta a '
                          'genética.')],
           antecedentes=['hipoacusia_familiar']),
    # Andrés, 6 años: acueducto vestibular dilatado; pasó el tamizaje, cae a
    # saltos (resfrío, golpe en la cabeza); gap en graves con timpanograma A
    cuadro('pendred', [fig.audiograma(ldl=False), fig.timpanograma(), fig.reflejos()],
           od='pendred', oi='pendred', grado_od='moderada', grado_oi='moderada', edad=6, sexo='hombre',
           anamnesis="""Andrés tiene 6 años y está en primero básico. Lo trae su mamá porque hace diez días se cayó
           de espaldas en el patio del colegio, se golpeó la cabeza, vomitó una vez y estuvo mareado esa tarde;
           desde entonces "no oye nada", aunque tenga puestos sus audífonos. Pasó el tamizaje auditivo al nacer.
           A los 3 años la educadora del jardín notó que no respondía cuando lo llamaban, le encontraron una
           hipoacusia en los dos oídos y usa audífonos desde los 4. La mamá cuenta que no es la primera vez: el
           año pasado, después de un resfrío fuerte, también oyó peor por unas semanas y se recuperó solo en
           parte. No ha tenido otitis. En la familia nadie es sordo. Camina y corre bien, y hace poco aprendió a
           andar en bicicleta sin rueditas.""",
           historia=[(2165, 'Tamizaje auditivo neonatal con emisiones otoacústicas: pasa en ambos oídos.'),
                     (1080, 'Audiometría condicionada por juego: hipoacusia sensorioneural moderada bilateral, '
                            '40 a 55 dB HL; gap aéreo-óseo de 20 dB en 250 Hz con timpanograma A, atribuido a la '
                            'técnica. Se indican audífonos.'),
                     (365, 'Otorrinolaringólogo: baja auditiva después de un cuadro respiratorio; al mes, '
                           'recuperación parcial.'),
                     (10, 'Servicio de urgencia: traumatismo craneano leve en el colegio, sin pérdida de '
                          'conciencia; un vómito. Observación y alta.'),
                     (3, 'Otorrinolaringólogo: baja auditiva bilateral desde el golpe. Solicita audiometría e '
                         'impedanciometría; pedirá imágenes de oídos.')],
           antecedentes=['tce']),
    # Javier, 15 años: Alport ligado al X; curva en cubeta; el tío materno se
    # dializa y usa audífonos
    cuadro('alport', [fig.audiograma(), fig.logo(), fig.dpoae()],
           od='alport', oi='alport', grado_od='moderada', grado_oi='moderada', edad=15, sexo='hombre', semilla=7,
           anamnesis="""Javier tiene 15 años y está en segundo medio. Viene con su mamá porque desde hace un año le
           cuesta seguir las clases: entiende al profesor cuando está adelante, pero no a los compañeros que
           hablan desde atrás. Sus amigos le dicen que pone el volumen del celular muy alto. A veces siente un
           pitido en los dos oídos, sobre todo en la noche, que va y viene. Desde chico tiene sangre en la orina
           en los exámenes de rutina, y hace dos años el nefrólogo le encontró además proteínas en la orina; está
           en control y toma un remedio para proteger el riñón. Un tío por parte de la mamá se dializa desde los
           30 años y usa audífonos. La mamá tiene "un poco de sangre en la orina" en los exámenes, pero el riñón
           le funciona bien y oye normal. Nunca ha tenido otitis ni ha estado expuesto a ruido fuerte.""",
           historia=[(3650, 'Pediatra: hematuria microscópica en examen de orina de rutina. Se deriva a nefrología.'),
                     (730, 'Nefrología: hematuria y proteinuria. Sospecha de síndrome de Alport por la historia '
                           'familiar; inicia enalapril y solicita estudio genético.'),
                     (30, 'Nefrología: no oye bien en clases. Solicita evaluación audiológica y control '
                          'oftalmológico.')],
           antecedentes=['hipoacusia_familiar'],
           medicamentos='Enalapril, indicado por nefrología'),
    # Carmen, 17 años: Usher tipo 2; audífonos desde los 5, ahora no ve de
    # noche; marcha y equilibrio normales desde chica (VEMP presentes)
    cuadro('usher', [fig.audiograma(), fig.logo(), fig.vemp()],
           od='usher', oi='usher', grado_od='moderada', grado_oi='moderada', edad=17, sexo='mujer',
           anamnesis="""Carmen tiene 17 años y está en cuarto medio. Usa audífonos en los dos oídos desde los 5 años,
           cuando en el jardín notaron que no oía bien; donde nació no se hacía tamizaje auditivo. Le va bien en
           el colegio y se sienta adelante para leerles los labios a los profesores. Desde hace unos dos años le
           cuesta ver de noche: en una calle oscura o al entrar al cine queda "ciega" por un rato, y se ha
           golpeado con muebles y con gente que viene por el lado. El oftalmólogo le encontró una retinosis
           pigmentaria y le dijo que la audición y la vista podían ser "parte de lo mismo". Viene a control de
           audición. Sus papás y su hermano menor oyen y ven bien. Nunca ha tenido mareos; caminó al año y aprendió
           a andar en bicicleta a los 5 sin problemas.""",
           historia=[(4380, 'Audiometría: hipoacusia sensorioneural bilateral moderada, descendente. Adaptación '
                            'de audífonos.'),
                     (2190, 'Control audiológico: sin cambios significativos respecto de la evaluación anterior.'),
                     (60, 'Oftalmología: ceguera nocturna y reducción del campo visual periférico; fondo de ojo '
                          'con retinosis pigmentaria. Sospecha síndrome de Usher; deriva a otorrinolaringología '
                          'y genética.'),
                     (20, 'Otorrinolaringólogo: solicita audiometría, logoaudiometría y evaluación de la función '
                          'vestibular.')]),
]

if __name__ == '__main__':
    Capitulo(10).generar(CASOS)
