"""
Frases que el evaluador le dice al paciente en el box, sin talkback: el
mismo panel de los comandos de voz del audiómetro (comandos_voz.py), pero
tocar la frase la dice al tiro. Lo usan el impedanciómetro
(impedanciometria/instrucciones.py), los diapasones (Acumetria.py) y el
otoscopio (Otoscopia.py), cada uno con sus frases y su carpeta de audio
(resources/audio/<carpeta>/<clave>.mp3, ver scripts/voces_comandos.py).

Volver a tocar la frase la repite; Silencio corta lo que esté sonando. Sin
el audio de una frase se elige igual, en silencio: la frase sigue valiendo
para el paciente y para el registro.
"""
import os

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from audiometria.comandos_voz import SILENCIO, ComandosVoz
from core.base import context

# La voz no tapa los sonidos del equipo pero tampoco es una alarma.
VOLUMEN = 0.8


class FrasesHabladas(ComandosVoz):
    PISTA = "Dicha al paciente."

    def __init__(self, grupos, prueba, carpeta, volumen=VOLUMEN):
        super().__init__(grupos, prueba)
        self._dir = os.path.join(context.get_resource("audio"), carpeta)
        self._salida = QAudioOutput(self)
        self._salida.setVolume(volumen)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._salida)
        self.btn_checked.connect(self._decir)

    def _elegir(self, btn):
        # Sin talkback la frase se dice al tocarla: tocarla de nuevo la
        # repite, no la suelta.
        btn.setChecked(True)
        super()._elegir(btn)

    def _decir(self, clave):
        self._player.stop()
        if clave == SILENCIO:
            return
        ruta = os.path.join(self._dir, f"{clave}.mp3")
        if os.path.exists(ruta):
            self._player.setSource(QUrl.fromLocalFile(ruta))
            self._player.play()

    def callar(self):
        self._player.stop()
