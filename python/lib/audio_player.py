from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtCore import QUrl
from functools import partial

class Player():
    def __init__(self, channels:int) -> None:
        self.players, self.channels = self.create_channels(channels)
        self.loop_media = {}  # Diccionario para medios que deben estar en bucle.
        self.current_medias = {}  # Diccionario para el medio actual en cada reproductor.
        
    def create_channels(self, ch:int) ->list:

        players = []
        outputs = []
        for _ in range(ch):
            outputs.append(QAudioOutput())
            player = QMediaPlayer()
            player.mediaStatusChanged.connect(partial(self.check_end_of_media, player))
            players.append(player)
            
        for i in range(len(players)):
            players[i].setAudioOutput(outputs[i])
        
        return players, outputs
    
    def check_end_of_media(self, player, status: int):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            current_media = self.current_medias.get(player, None)
            if current_media and self.loop_media.get(current_media, False):
                player.setPosition(0)
                player.play()

    def stop(self, ch:int)->None:
        self.players[ch].stop()
        
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
        
        
        

