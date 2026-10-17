#!/usr/bin/env python3
"""Capítulo 26 — Una tercera ventana.

    python3 docs/libro/capitulos/26-una-tercera-ventana.py              casos + figuras + PDF
    python3 docs/libro/capitulos/26-una-tercera-ventana.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/26-una-tercera-ventana.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
26-una-tercera-ventana.md (cada caso se nombra ahí como cap26_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# CASO 26.1: LabSim NO puede escribir una dehiscencia (su motor recorta la vía ósea en 0 dB y apaga el
# reflejo con cualquier gap; ver docs/decisiones.md, "Reflejo presente con gap" y "Ósea supranormal").
# Por eso la paciente del 26.1 va como cuadro 'normal' solo para la entrevista y el rostro; su audiograma,
# su reflejo y su VEMP son el esquema propio ilustraciones/hacer_cap26.py, hecho con cifras de la literatura.
# Los casos 26.2 (otoesclerosis, el patrón contrario) y 26.3 (acueducto dilatado) salen del motor.
OIDO = [fig.audiograma(), fig.timpanograma(), fig.reflejos()]

CASOS = [
    cuadro('dehiscencia', [], od='normal', oi='normal', edad=41, sexo='mujer', semilla=27,
           anamnesis="""Tiene 41 años y es diseñadora gráfica. Hace dos años, después de una gripe fuerte, empezó a sentir
           el oído derecho "tapado" y a oír su propia voz demasiado fuerte, "como hablar dentro de un tambor". Al masticar
           una manzana el ruido le retumba en la cabeza y, de noche, con la oreja en la almohada, oye los latidos del
           corazón y hasta "el ruido de los ojos" cuando los mueve. Con la bocina de un bus o la sirena de una
           ambulancia siente que el piso se mueve un instante; cuando tose fuerte o se suena la nariz, la imagen se
           le "salta" unos segundos. Por el teléfono oye bien, y la conversación en un lugar con ruido no le cuesta más
           que antes. No ha tenido secreción ni dolor de oídos, ni golpes en la cabeza.""",
           historia=[(700, 'Gripe fuerte; desde entonces, sensación de oído derecho tapado y autofonía.'),
                     (120, 'Otorrinolaringólogo: audiometría con gap aéreo-óseo en los graves del OD y otoscopía normal; se plantea otoesclerosis y se agenda una estapedotomía.'),
                     (10, 'Antes de la cirugía, el mismo médico pide impedanciometría con reflejos y VEMP.')]),
    cuadro('otoesclerosis', OIDO + [fig.vemp()], od='otoesclerosis', edad=47, sexo='mujer', semilla=26,
           antecedentes=['hipoacusia_familiar'],
           anamnesis="""Tiene 47 años y es asistente de párvulos. Hace unos tres años nota que por el oído derecho oye
           menos: pasa el teléfono al otro lado y en la sala de clases se sienta de modo que su oído izquierdo mire al
           grupo. Su propia voz le suena "apagada", y al masticar no le hace ruido. No tiene pitido, mareos ni
           sensibilidad a los sonidos fuertes; la sirena de una ambulancia no le molesta más que a nadie. No ha tenido
           secreción ni dolor de oídos ni golpes en la cabeza. Su hermana mayor usa audífono desde los 40 años.""",
           historia=[(1100, 'Primera vez que nota que oye menos por el oído derecho.'),
                     (60, 'Otorrinolaringólogo: otoscopía normal; se piden audiometría, impedanciometría y VEMP antes de decidir tratamiento.')]),
    cuadro('pendred', OIDO, od='pendred', oi='pendred', grado_od='moderada', grado_oi='moderada',
           edad=11, sexo='hombre', semilla=26,
           anamnesis="""Tiene 11 años y está en sexto básico. Su mamá lo trae porque la profesora dice que "no escucha" y
           porque en el último año le pide que repita más. A los seis años
           le pusieron tubos de ventilación por "pérdida conductiva" y, según la mamá, no cambió nada. No ha tenido
           secreción de oídos y los resfríos le duran lo mismo que a sus hermanos. No tiene mareos ni zumbido. En
           los recreos juega a la pelota y es de los que se queda atrás de la conversación.""",
           historia=[(1800, 'Colocación de tubos de ventilación bilaterales por hipoacusia atribuida a oído medio; sin mejoría.'),
                     (30, 'Pediatra: la profesora informa que no responde cuando se le habla desde atrás; se deriva a evaluación auditiva.')]),
]

if __name__ == '__main__':
    Capitulo(26).generar(CASOS)
