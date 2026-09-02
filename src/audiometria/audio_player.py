import numpy as np
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import (QAudioBufferOutput, QAudioFormat,
                                   QAudioOutput, QMediaPlayer)
from functools import partial

from audiometria.audio_synth import PEAK_REF

# RMS de un tono puro sintetizado a PEAK_REF (ver audio_synth.py): seno de
# pico PEAK_REF tiene RMS = PEAK_REF/sqrt(2). Se usa como referencia para que
# un tono a nivel nominal marque 50% en el vúmetro (ver vu_meters_colors en
# Audiometer.py). Si un tono calibrado marca mas que eso (zona roja), la
# salida de audio esta descalibrada.
_TONE_RMS_REF = PEAK_REF / np.sqrt(2.0)
_LEVEL_GAIN = 0.5 / _TONE_RMS_REF

_SAMPLE_DTYPE = {
    QAudioFormat.SampleFormat.UInt8: np.uint8,
    QAudioFormat.SampleFormat.Int16: np.int16,
    QAudioFormat.SampleFormat.Int32: np.int32,
    QAudioFormat.SampleFormat.Float: np.float32,
}


def audio_buffer_level(buffer) -> float:
    """
    Nivel RMS normalizado (0.0-1.0) del audio real contenido en un QAudioBuffer.
    Se usa para mover los vúmetro con la señal de audio que efectivamente suena,
    en vez de un valor fijo simulado.
    """
    if buffer is None or not buffer.isValid():
        return 0.0

    dtype = _SAMPLE_DTYPE.get(buffer.format().sampleFormat())
    if dtype is None:
        return 0.0

    samples = np.frombuffer(bytes(buffer.constData()), dtype=dtype)
    if samples.size == 0:
        return 0.0

    if dtype == np.uint8:
        normalized = (samples.astype(np.float32) - 128.0) / 128.0
    elif dtype == np.float32:
        normalized = samples
    else:
        normalized = samples.astype(np.float32) / np.iinfo(dtype).max

    rms = float(np.sqrt(np.mean(np.square(normalized))))
    return min(rms * _LEVEL_GAIN, 1.0)


class Player(QObject):
    # canal (int), nivel normalizado 0.0-1.0 de la señal que realmente está sonando
    level_changed = Signal(int, float)

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.players, self.channels, self.buffer_outputs = self.create_channels(channels)
        self.loop_media = {}  # Diccionario para medios que deben estar en bucle.
        self.current_medias = {}  # Diccionario para el medio actual en cada reproductor.

    def create_channels(self, ch: int) -> list:

        players = []
        outputs = []
        buffer_outputs = []
        for _ in range(ch):
            outputs.append(QAudioOutput())
            player = QMediaPlayer()
            player.mediaStatusChanged.connect(partial(self.check_end_of_media, player))
            players.append(player)

        for i in range(len(players)):
            players[i].setAudioOutput(outputs[i])
            buffer_output = QAudioBufferOutput()
            buffer_output.audioBufferReceived.connect(partial(self._on_audio_buffer, i))
            players[i].setAudioBufferOutput(buffer_output)
            buffer_outputs.append(buffer_output)

        return players, outputs, buffer_outputs

    def _on_audio_buffer(self, ch, buffer):
        self.level_changed.emit(ch, audio_buffer_level(buffer))

    def check_end_of_media(self, player, status: int):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            current_media = self.current_medias.get(player, None)
            if current_media and self.loop_media.get(current_media, False):
                player.setPosition(0)
                player.play()

    def stop(self, ch: int) -> None:
        self.players[ch].stop()
        self.level_changed.emit(ch, 0.0)

    def stop_all(self):
        for i in range(len(self.players)):
            self.stop(i)


    def play(self, ch: int, source: QUrl, loop: bool = False) -> None:
        if source is not None:
            source_str = source.toString()
            self.players[ch].setSource(source)
            self.players[ch].play()
            self.loop_media[source_str] = loop
            self.current_medias[self.players[ch]] = source_str  # Establecer el medio actual para este reproductor.


    def volume(self, ch:int, value:int) -> None:
        self.channels[ch].setVolume(value)

    def status(self, ch:int)->int:
        return self.players[ch].mediaStatus()

    def play_status(self, ch:int):
        state = self.players[ch].playbackState()

        if state == QMediaPlayer.PlaybackState.StoppedState:
            return False
        if state == QMediaPlayer.PlaybackState.PlayingState:
            return True
