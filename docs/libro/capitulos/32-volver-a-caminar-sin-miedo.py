#!/usr/bin/env python3
"""Capítulo 32 — Volver a caminar sin miedo.

    python3 docs/libro/capitulos/32-volver-a-caminar-sin-miedo.py              casos + figuras + PDF
    python3 docs/libro/capitulos/32-volver-a-caminar-sin-miedo.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/32-volver-a-caminar-sin-miedo.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
32-volver-a-caminar-sin-miedo.md (cada caso se nombra ahí como cap32_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# LabSim da solo el lado auditivo: lo vestibular, lo funcional y lo postural de cada caso está escrito en el .md
# ("cifras inventadas para el libro") o sale de los esquemas de ilustraciones/cap32-*.svg (hacer_cap32.py,
# hacer_cap32.mjs con el modelo postural de labyrinthus3d).
OIDO = [fig.audiograma(), fig.logo()]

CASOS = [
    # 32.1 Un VPPB escondido en una persona que se cae: no dice "vértigo", dice "se me va el piso".
    cuadro('vppb', OIDO, od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve', edad=79, sexo='mujer',
           anamnesis="""Tiene 79 años, es profesora básica jubilada y vive con su hija. En los últimos cuatro meses se ha
           caído dos veces. La primera fue de noche: se levantó de la cama para ir al baño, "se me fue el piso", se agarró
           del velador y terminó sentada en el suelo, sin golpe. La segunda fue hace cuatro semanas, en la cocina, al estirar
           el cuello para mirar una repisa alta: cayó de lado y se fracturó la muñeca izquierda. Insiste en que no gira nada:
           "no es vértigo, es que se me va el piso un ratito"; son unos segundos y después queda bien. Le pasa también al
           agacharse a atarse los zapatos y al darse vuelta en la cama, donde a veces se marea sin caerse. Sentada o caminando
           no se siente mareada. No ha perdido el conocimiento ni tiene palpitaciones ni dolor de pecho. Oye menos desde hace
           años, sobre todo en grupos y con la televisión, y tiene un siseo en los dos oídos que va y viene; nunca ha usado audífono.
           Desde la fractura no sale sola: "me da miedo que me pase en la calle". Su médico le dijo que era "la edad".""",
           historia=[(28, 'Urgencia: caída en la cocina con fractura de radio distal izquierdo; yeso por seis semanas; alta.'),
                     (10, 'Médico de familia: "caída por mareo, propio de la edad". Se solicita evaluación audiológica y del equilibrio.')],
           antecedentes=['hta'],
           medicamentos='Enalapril 10 mg al día; alendronato 70 mg a la semana; carbonato de calcio con vitamina D'),
    # 32.2 La fragilidad: varias causas a la vez, ninguna vestibular, y el miedo.
    cuadro('fragil', OIDO, od='presbiacusia', oi='presbiacusia', grado_od='moderada', grado_oi='moderada', edad=86, sexo='hombre',
           anamnesis="""Tiene 86 años, es electricista jubilado y vive solo desde que enviudó hace tres años; una hija lo llama
           cada noche. En el último año se ha caído tres veces. Dos fueron en la casa: de noche, camino al baño, y al
           pararse del excusado. La tercera fue en el jardín, hace dos meses: se cayó al agacharse a arrancar una maleza y no
           pudo levantarse por unas dos horas, hasta que un vecino lo oyó. No perdió el conocimiento que él recuerde. Cuenta
           que "se le nubla la vista y se le va la fuerza de las piernas" cuando se pone de pie, sobre todo en la mañana y en
           la noche, y que tiene que esperar agarrado a algo. Ya casi no sale: el vecino le hace las compras y desde la última
           caída le tiene miedo al jardín y a la calle. Ve mal por cataratas en los dos ojos, en lista de espera hace dos años,
           y usa anteojos bifocales. Oye mal desde hace muchos años: dice que "todos murmuran", pide repetir por teléfono y
           no escucha el timbre; probó un audífono hace tiempo y lo dejó en el cajón porque "silbaba". Tiene un pitido en
           los dos oídos. Toma siete remedios y de algunos no sabe para qué son. Dice que no es vértigo: "es que el cuerpo
           ya no me responde".""",
           historia=[(400, 'Control de hipertensión: se agrega furosemida por edema de tobillos.'),
                     (60, 'Urgencia: caída en el jardín con erosiones; permaneció dos horas en el suelo; alta sin estudio.'),
                     (30, 'Médico de familia: "caídas a repetición"; se deriva a evaluación audiológica y del equilibrio.')],
           antecedentes=['hta', 'diabetes'],
           medicamentos='Amlodipino 5 mg, enalapril 10 mg y furosemida 20 mg en la mañana; tamsulosina 0,4 mg y clonazepam 0,5 mg '
                        'en la noche; metformina 850 mg dos veces al día; paracetamol cuando le duele la rodilla'),
    # 32.3 Dos sentidos caídos (vestíbulo y pies) y la luz que falta: neuropatía diabética + hipofunción bilateral.
    cuadro('bilateral', OIDO, od='presbiacusia', oi='presbiacusia', grado_od='leve', grado_oi='leve', edad=74, sexo='mujer',
           anamnesis="""Tiene 74 años, trabajó como costurera y vive con su marido. Hace unos ocho meses empezó a sentirse
           insegura al caminar: "voy sobre algodón", dice, y no siente bien el piso. No tiene vértigo ni lo ha tenido. De
           noche, para ir al baño, se agarra de las murallas, y en esos ocho meses se cayó tres veces, siempre a oscuras o con
           poca luz: en el pasillo, y en el jardín al anochecer, la última con una costilla fracturada. En la micro, cuando el
           vehículo va saltando, "la calle se me mueve" y no puede leer los letreros; sentada, leyendo, no tiene problema.
           Hace años tiene hormigueo y ardor en los pies, peor de noche. No recuerda haber recibido gentamicina ni haber tenido
           meningitis. Ve bien con sus lentes y la oftalmóloga le controla la retina cada año. Oye menos los agudos desde hace
           años y no usa audífono; no tiene pitido. No ha notado temblor ni dificultad para hablar. Está muy asustada: desde la
           costilla casi no camina sola.""",
           historia=[(240, 'Médico de familia: neuropatía diabética sensitiva; se indica gabapentina para el ardor de los pies.'),
                     (90, 'Urgencia: caída en el jardín al anochecer con fractura de costilla; alta con analgesia.'),
                     (30, 'Neurólogo: polineuropatía sensitiva distal simétrica compatible con diabética; resonancia de cerebro sin '
                          'atrofia cerebelosa; sugiere evaluación vestibular por inestabilidad y oscilopsia.')],
           antecedentes=['diabetes', 'hta'],
           medicamentos='Metformina 850 mg dos veces al día; enalapril 10 mg al día; atorvastatina 20 mg; gabapentina 300 mg en la noche'),
]

if __name__ == '__main__':
    Capitulo(32).generar(CASOS)
