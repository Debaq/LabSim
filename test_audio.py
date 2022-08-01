import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


def main():
    app = QGuiApplication(sys.argv)

    filename = "/home/nick/Escritorio/Proyectos/LabSim/software/LabSim/src/main/resources/base/audio/NBN_1000_OI.mp3"
    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    player.setSource(QUrl.fromLocalFile(filename))
    audio_output.setVolume(50)
    player.play()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    
    