# -*- coding: utf-8 -*-
"""Audio de estimulos del impedanciometro: tono de sonda (timpanograma) y
tono/ruido activador (reflejos), con fundido de entrada/salida por volumen.

Reusa la sintesis de audiometria/audio_synth.py (mismo cache en disco, misma
logica de "Tono"/"NBN" periodicos) en vez de duplicarla; solo agrega el
fundido, que aca hace falta porque el estimulo se prende/apaga a mitad de
pista -- la sonda real nunca arranca ni corta en seco, eso clickearia.

Usa QMediaPlayer + QAudioOutput (igual que audiometria/audio_player.Player),
NO QSoundEffect: en Linux/PipeWire, QSoundEffect marca el stream con
media.role="event" (la categoria de sonidos de sistema/notificaciones), que
en muchos equipos esta silenciada por el mixer del SO aunque Qt reporte
"reproduciendo" -- confirmado con pactl (Mute: yes en esa categoria). Con
QAudioOutput el stream queda en role="music" (reproduccion normal), la
misma categoria que ya usa el audiometro y que si suena."""

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from audiometria import audio_synth
from core.base import context

FADE_MS = 25       # duracion total del fundido de volumen, en ms
FADE_TICK_MS = 5   # resolucion del timer que arma la rampa

_AUDIO_DIR = context.get_resource("audio")

# self.reflex_freq_labels ('500'..'4000') + 'NBN' -> (estimulo, freq) de audio_synth.
_REFLEX_STIM = {
    '500': ('Tono', '500'),
    '1000': ('Tono', '1000'),
    '2000': ('Tono', '2000'),
    '4000': ('Tono', '4000'),
    'NBN': ('NBN', '2000'),
}

# El alumno es el examinador, no el paciente: en un box real sin ruido se
# escucha el tono por ambos oidos (no hay panneo OD/OI, eso seria simular
# lo que oye el paciente). Y nunca a todo volumen -- son estimulos de fondo
# para dar ambiente, no una alarma: techo duro en el 50% de la salida.
_BOTH_EARS = 'sim'
_MAX_VOLUME = 0.5


def _source_for(stim, freq, ch):
    path = audio_synth.stimulus_file(stim, freq, ch, _AUDIO_DIR)
    return QUrl.fromLocalFile(path)


class _FadingPlayer(QObject):
    """QMediaPlayer en loop + rampa de volumen manual para el fundido."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output = QAudioOutput(self)
        self._output.setVolume(0.0)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._output)
        self._player.mediaStatusChanged.connect(self._on_status)
        self._timer = QTimer(self)
        self._timer.setInterval(FADE_TICK_MS)
        self._timer.timeout.connect(self._tick)
        self._target = 0.0
        self._direction = 0
        self._current_key = None

    def _on_status(self, status):
        # bucle manual: el archivo dura unos segundos (audio_synth.DURATION)
        # y se repite mientras el estimulo siga activo, como en audio_player.Player.
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._player.setPosition(0)
            self._player.play()

    def _is_active(self):
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def start(self, key, url, volume):
        if self._current_key == key and self._is_active():
            # mismo estimulo ya sonando (ej. se reafirma el mismo tono):
            # solo actualiza el objetivo del fundido, no reinicia la pista
            self._target = volume
            self._direction = +1
            self._timer.start()
            return
        if self._is_active():
            self._player.stop()
        self._current_key = key
        self._player.setSource(url)
        self._output.setVolume(0.0)
        self._player.play()
        self._target = volume
        self._direction = +1
        self._timer.start()

    def stop(self):
        if not self._is_active():
            self._timer.stop()
            return
        self._direction = -1
        self._timer.start()

    def _tick(self):
        step = self._target * (FADE_TICK_MS / FADE_MS)
        vol = self._output.volume() + self._direction * step
        if self._direction > 0:
            if vol >= self._target:
                vol = self._target
                self._timer.stop()
            self._output.setVolume(vol)
        else:
            if vol <= 0.0:
                self._timer.stop()
                self._output.setVolume(0.0)
                self._player.stop()
                self._current_key = None
            else:
                self._output.setVolume(vol)


class ProbeTone(_FadingPlayer):
    """Tono continuo de la sonda (226/1000 Hz) durante el barrido del
    timpanograma. Cambia de tono en caliente si se cambia de sonda
    mientras esta sonando, en vez de cortar y perder el fundido."""

    def play(self, freq):
        url = _source_for('Tono', freq, _BOTH_EARS)
        self.start(freq, url, volume=0.15)


class ReflexTone(QObject):
    """Rafaga de tono/ruido activador de reflejos, sincronizada con la
    ventana del estimulo que dibuja Z_reflex (ver Z.reflex_stimulus):
    aparece y desaparece con fundido, nunca en seco."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = _FadingPlayer(self)
        self._off_timer = QTimer(self)
        self._off_timer.setSingleShot(True)
        self._off_timer.timeout.connect(self._player.stop)
        self._on_timer = QTimer(self)
        self._on_timer.setSingleShot(True)
        self._on_timer.timeout.connect(self._start_pending)
        self._pending = None

    def _start_pending(self):
        if self._pending is not None:
            key, url, volume = self._pending
            self._player.start(key, url, volume)

    def burst(self, freq_label, delay_ms, duration_ms, volume=_MAX_VOLUME):
        stim, synth_freq = _REFLEX_STIM.get(freq_label, ('Tono', freq_label))
        url = _source_for(stim, synth_freq, _BOTH_EARS)
        volume = min(volume, _MAX_VOLUME)

        self._on_timer.stop()
        self._off_timer.stop()
        self._pending = ((stim, synth_freq), url, volume)
        self._on_timer.start(delay_ms)
        self._off_timer.start(delay_ms + duration_ms)

    def stop(self):
        self._on_timer.stop()
        self._off_timer.stop()
        self._player.stop()
