#!/usr/bin/env python3
"""Capítulo 33 — El trabajador expuesto a ruido.

    python3 docs/libro/capitulos/33-el-trabajador-expuesto-a-ruido.py              casos + figuras + PDF
    python3 docs/libro/capitulos/33-el-trabajador-expuesto-a-ruido.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/33-el-trabajador-expuesto-a-ruido.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
33-el-trabajador-expuesto-a-ruido.md (cada caso se nombra ahí como cap33_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

CASOS = [
    # Control atrasado: la base (0 dB HL a los 33 años) está en la ficha, no en el motor
    cuadro('control', [fig.audiograma(), fig.timpanograma()], od='muesca_4k', oi='muesca_4k', edad=41, semilla=3301,
           anamnesis="""Tiene 41 años y hace ocho trabaja de operario en un aserradero, en la línea de corte. Entró a los 33
           y su audiometría de ingreso fue normal. El primer año lo controlaron, pero después cambió de empresa
           contratista y de turno, y nadie más le pidió el examen hasta ahora. Usa tapones de espuma, "cuando se
           acuerda": a veces se los saca para hablar con el compañero o porque le pican. Fuera del trabajo no tiene
           ruido: no dispara, no va a recitales y no escucha música con audífonos. No tiene pitido ni mareos, y
           dice que oye bien; su señora le comenta que sube la tele. La audiometría de hoy se tomó en cámara, con
           más de doce horas sin ruido y la última exposición anotada en la ficha.""",
           historia=[(2920, 'Audiometría de ingreso a la empresa: umbrales de 0 dB HL en todas las frecuencias, los dos oídos.'),
                     (2555, 'Control anual: sin cambios respecto de la base.'),
                     (30, 'Control periódico en terreno: cambio en 3, 4 y 6 kHz de los dos oídos; se cita a confirmación en cámara.')],
           antecedentes=['trauma_acustico']),
    # Cambio al final del turno que desaparece con el reposo: el motor solo muestra el reposo
    cuadro('reposo', [fig.audiograma()], edad=29, semilla=3302,
           anamnesis="""Tiene 29 años y hace tres es operador de un molino de bolas en una planta de molienda. Su
           audiometría de ingreso fue normal. Usa orejeras y tapones juntos "cuando el jefe pasa", y a veces solo
           las orejeras. En el control de este mes, tomado en la sala de la planta al terminar el turno, salió con
           cambio en los dos oídos; se repitió al tiro, reinstruido y con los fonos recolocados, y el cambio siguió.
           Hoy vuelve a la cámara a las 8 de la mañana: su último turno terminó anoche a las 18 horas y desde
           entonces estuvo en su casa, sin ruido. Hace unos meses le apareció un siseo en los dos oídos que antes
           se le iba en la noche; ahora lo nota también en la mañana. Entiende bien en silencio, pero en la
           planta, con todo andando, le cuesta seguir a los compañeros.""",
           historia=[(1095, 'Audiometría de ingreso: 0 dB HL en todas las frecuencias, los dos oídos.'),
                     (365, 'Control anual en cámara: sin cambios respecto de la base.'),
                     (14, 'Control en terreno al final del turno: cambio en 2, 3, 4 y 6 kHz de los dos oídos; se repite y persiste. Se cita a confirmación en cámara con reposo.')],
           antecedentes=['trauma_acustico']),
    # Ingreso con la audiometría alterada y asimétrica
    cuadro('ingreso', [fig.audiograma()], oi='muesca_4k', edad=27, semilla=3303,
           anamnesis="""Tiene 27 años y postula a un puesto de mecánico en una faena minera. Es tirador deportivo desde
           los 17 y sale a cazar con escopeta un par de veces al año; durante años disparó sin protección, y
           ahora usa tapones "a veces". Es diestro. Hace cinco años, tras una temporada de tiro, quedó con un
           pitido agudo en el oído izquierdo que no se le ha ido; nunca consultó. Dice que oye perfecto: en
           conversación no tiene problemas, aunque por teléfono usa el oído derecho. No ha tenido mareos, dolor ni
           secreción. En el examen de ingreso de hoy, hecho con reposo de más de doce horas, el oído izquierdo
           salió muy distinto del derecho.""",
           historia=[(1825, 'Temporada de tiro con pitido persistente en el oído izquierdo; no consultó.'),
                     (1, 'Examen de ingreso a la faena: audiometría de vía aérea con diferencia marcada entre los dos oídos; se deriva a evaluación diagnóstica.')],
           antecedentes=['trauma_acustico']),
]

if __name__ == '__main__':
    Capitulo(33).generar(CASOS)
