"""
Instrucciones del impedanciómetro: lo que el evaluador le dice al paciente
antes y durante la impedanciometría. El mismo panel de los comandos de voz
del audiómetro (audiometria/comandos_voz.py), con sus frases.

Sin talkback: en la impedanciometría se le habla al paciente en el box, así
que tocar la frase la dice (audiometria/frases_habladas.py; resources/audio/comandos_z/<clave>.mp3, ver
scripts/voces_comandos.py --z) y queda en el registro (z_instruccion): el
docente ve si el alumno preparó al paciente antes de medir. Volver a tocar
la frase la repite; Silencio corta lo que esté sonando.
"""
from audiometria.frases_habladas import FrasesHabladas

# Las claves son también el nombre del audio: no se cambian aunque cambie
# el rótulo.
GRUPOS = (
    ("PREPARAR", (
        ("Explicar el examen", "explicar_examen"),
        ("Colocar sonda", "colocar_sonda"),
        ("Colocar fono contralateral", "colocar_fono_contra"),
    )),
    ("INSTRUCCIONES", (
        ("No hablar ni tragar", "no_hablar_ni_tragar"),
        ("Sonidos fuertes", "sonidos_fuertes"),
        ("Sonido largo", "sonido_largo"),
        ("Trague tres veces", "trague_tres_veces"),
        ("Trague una vez", "trague_una_vez"),
    )),
    ("PREGUNTAS", (
        ("¿Le molesta la presión?", "le_molesta_presion"),
        ("¿Tragó recién?", "trago"),
        ("¿Está bien?", "esta_bien"),
    )),
)
# La prueba en que se usa cada frase, a la vista en su botón.
PRUEBA = {
    "colocar_sonda": "Timpanometría",
    "colocar_fono_contra": "Reflejo contra",
    "no_hablar_ni_tragar": "Timpanometría",
    "sonidos_fuertes": "Reflejos",
    "sonido_largo": "Decay",
    "trague_tres_veces": "ETF perforada",
    "trague_una_vez": "ETF íntegra",
}


class InstruccionesZ(FrasesHabladas):

    def __init__(self):
        super().__init__(GRUPOS, PRUEBA, "comandos_z")
