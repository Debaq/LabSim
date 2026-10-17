#!/usr/bin/env python3
"""Capítulo 36 — Rinitis y vasoconstrictor.

    python3 docs/libro/capitulos/36-rinitis-y-vasoconstrictor.py              casos + figuras + PDF
    python3 docs/libro/capitulos/36-rinitis-y-vasoconstrictor.py --solo-pdf   solo el PDF (cambió el texto)
    python3 docs/libro/capitulos/36-rinitis-y-vasoconstrictor.py --rearmar    vuelve a armar los casos por cuadro

Acá se deciden los pacientes y las figuras del capítulo; el texto está en
36-rinitis-y-vasoconstrictor.md (cada caso se nombra ahí como cap36_<nombre>).
Cuadros y grados: claves de CaseProfile::SCENARIOS. Un cuadro() acepta
od=, oi=, grado_od=, grado_oi=, edad=, sexo='hombre'|'mujer', semilla=.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'herramientas'))
from libro import Capitulo, cuadro, demo, fig  # noqa: E402,F401

# Un cuadro nasal no existe en LabSim: los tres pacientes son de audición normal
# ('normal') y sirven para que existan la ficha, la anamnesis y el rostro.
# Lo nasal (curvas y tablas) sale de RinoSim: ilustraciones/hacer_cap36_rinosim.sh
CASOS = [
    cuadro('alergica', [], edad=22, sexo='mujer',
           anamnesis="""Tiene 22 años y estudia kinesiología. Desde la adolescencia se le tapa la nariz casi todos los
           años entre septiembre y diciembre: estornuda en tandas de cinco o seis seguidas, le pica la nariz y los
           ojos y le gotea agua clara. También le pasa, sin ser primavera, cuando ordena el clóset o cuando duerme
           con su perra en la cama. De noche "se tapa un lado y después el otro", y a veces despierta con la boca
           seca. En invierno mejora a medias, pero nunca queda del todo bien. Nunca ha tenido silbidos en el pecho.
           Cuando está mal toma un antihistamínico; hace tres días que lo dejó, como le pidieron al darle la hora.
           No ha usado gotas ni sprays para la nariz. Hace unos dos años un alergólogo le hizo pruebas en la piel
           del antebrazo y le dijo que reaccionaba a los ácaros y al pasto.""",
           historia=[(3000, 'Control por estornudos y picazón en primavera; se indica un antihistamínico oral cuando hay síntomas.'),
                     (700, 'Pruebas cutáneas en el antebrazo con alérgenos inhalantes: reacciona a ácaros y a pasto (según relata; no trajo el informe).'),
                     (45, 'Médico general: rinitis alérgica; se solicita evaluación funcional de la nariz.')],
           medicamentos='Antihistamínico oral cuando hay síntomas (lo dejó hace tres días, como se le pidió)'),
    cuadro('medicamentosa', [], edad=29, sexo='hombre',
           anamnesis="""Tiene 29 años y trabaja en un call center. Hace unos ocho meses tuvo un resfrío fuerte y desde
           entonces la nariz no se le ha destapado. Compró un spray descongestionante en la farmacia y le funcionó
           tan bien que lo sigue usando: hoy se le acaba un frasco por semana, con un par de disparos en cada fosa
           cada cuatro a seis horas, incluso de madrugada. "Al principio me duraba toda la noche; ahora me dura dos
           horas." Sin el spray se queda sin aire por los dos lados y duerme con la boca abierta. No tiene estornudos
           ni picazón, no cambia con las estaciones ni con los animales y nadie en su familia es alérgico. Para este
           examen aguantó dos días sin el spray: durmió sentado, con la boca seca, y llegó "desesperado". Pregunta
           si después del examen le van a dejar usarlo otra vez.""",
           historia=[(240, 'Cuadro respiratorio alto con fiebre; empieza a usar un descongestionante nasal en spray comprado sin receta.'),
                     (60, 'Médico general: nariz tapada persistente; se le pide no usar el spray 48 horas antes del examen y se solicita evaluación funcional de la nariz.')],
           medicamentos='Oximetazolina en spray nasal, varias veces al día (la última vez hace dos días, por el examen)'),
    cuadro('mixta', [], edad=37, sexo='hombre',
           anamnesis="""Tiene 37 años y es técnico eléctrico. A los 12 años se cayó de la bicicleta y se golpeó la nariz;
           no lo atendieron. Desde hace años siente la fosa derecha más tapada que la izquierda: la derecha casi nunca
           "pasa"; la izquierda se tapa y se destapa, sobre todo en primavera y cuando se resfría, y en esa época
           estornuda un poco y le pica la nariz, aunque no tanto como para tomar remedios. Ronca. Probó un corticoide
           nasal por seis semanas: "me abrió el lado izquierdo, el derecho siguió igual". Usa un descongestionante en
           spray solo cuando duerme muy mal, unas pocas veces al mes; la última vez fue hace una semana.""",
           historia=[(9000, 'Caída en bicicleta con golpe en la nariz; no consultó.'),
                     (120, 'Médico general: rinitis; corticoide nasal por seis semanas con mejoría solo del lado izquierdo; se solicita evaluación funcional de la nariz.')],
           medicamentos='Oximetazolina en spray de forma ocasional (la última vez hace una semana); corticoide nasal por seis semanas, ya terminado'),
]

if __name__ == '__main__':
    Capitulo(36).generar(CASOS)
