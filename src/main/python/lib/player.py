import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


def _player(Url):
    app = QGuiApplication(sys.argv)

    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    player.setSource(Url)
    audio_output.setVolume(50)
    player.play()

    sys.exit(app.exec())


URL = QUrl.fromLocalFile("/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/resources/base/audio/molesta_feme2.mp3")
_player(URL)
    