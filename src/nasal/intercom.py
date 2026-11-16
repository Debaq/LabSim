"""El intercomunicador de la sala de control del laboratorio de sueño: lo que
el técnico le dice al paciente desde afuera.

El mismo panel de frases de los otros equipos (audiometria/frases_habladas.py):
tocar la frase la dice (resources/audio/comandos_psg/<clave>.mp3, ver
scripts/voces_comandos.py --psg) y la ventana del PSG decide qué hace el
paciente:

- NOCHE: saludar, explicar, preguntar; "Apagar la luz" termina la calibración
  (la noche deja el tiempo real y corre).
- BIOCALIBRACIÓN: con la luz encendida y el paciente despierto, hace la
  maniobra y se ve en los canales (sueno.BIOCAL, sueno.senales). Dormido no
  la oye.
- POSICIÓN: se da vuelta al terminar la frase (sueno.acomodar: se despierta
  un rato y la noche se rehace desde ahí).

Las claves son también el nombre del audio: no se cambian aunque cambie el
rótulo.
"""
from audiometria.frases_habladas import FrasesHabladas

APAGAR_LUZ = "apagar_luz"
# Posición pedida -> sueno.POSICIONES
POSICION = {
    "pos_supino": "supino",
    "pos_izquierda": "izquierda",
    "pos_derecha": "derecha",
}
GRUPOS = (
    ("NOCHE", (
        ("Buenas noches", "buenas_noches"),
        ("Explicar la calibración", "explicar_calibracion"),
        ("¿Está cómodo?", "esta_comodo"),
        ("No se levante solo", "no_se_levante"),
        ("Apagar la luz", APAGAR_LUZ),
        ("Buenos días", "buenos_dias"),
    )),
    ("BIOCALIBRACIÓN", (
        ("Ojos abiertos 30 s", "ojos_abiertos"),
        ("Ojos cerrados 30 s", "ojos_cerrados"),
        ("Mire a los lados", "mire_a_los_lados"),
        ("Mire arriba y abajo", "mire_arriba_abajo"),
        ("Parpadee", "parpadee"),
        ("Apriete los dientes", "apriete_dientes"),
        ("Respire por la nariz", "respire_nariz"),
        ("Respire por la boca", "respire_boca"),
        ("Aguante la respiración", "aguante"),
        ("Haga como que ronca", "ronque"),
    )),
    ("POSICIÓN", (
        ("De espaldas", "pos_supino"),
        ("Sobre el lado izquierdo", "pos_izquierda"),
        ("Sobre el lado derecho", "pos_derecha"),
    )),
)
CLAVES = frozenset(clave for _, frases in GRUPOS for _, clave in frases)
# El canal en que se mira cada biocalibración, a la vista en su botón.
PRUEBA = {
    "ojos_abiertos": "EEG",
    "ojos_cerrados": "EEG: alfa",
    "mire_a_los_lados": "EOG",
    "mire_arriba_abajo": "EOG",
    "parpadee": "EOG",
    "apriete_dientes": "EMG",
    "respire_nariz": "Cánula y térmico",
    "respire_boca": "Térmico",
    "aguante": "Flujo y bandas",
    "ronque": "Ronquido",
    APAGAR_LUZ: "Empieza la noche",
}


class Intercom(FrasesHabladas):
    PISTA = "Dicha por el intercomunicador."

    def __init__(self):
        super().__init__(GRUPOS, PRUEBA, "comandos_psg")

    def decir(self, clave):
        """La dice sin tocar el panel (los botones de posición de la sala)."""
        self._decir(clave)
