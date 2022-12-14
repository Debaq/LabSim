from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtCore import QUrl

class Player():
    def __init__(self, channels:int) -> None:
        self.players, self.channels = self.create_channels(channels)
    
    def create_channels(self, ch:int) ->list:

        players = []
        outputs = []
        for _ in range(ch):
            outputs.append(QAudioOutput())
            players.append(QMediaPlayer())
            
        for i in range(len(players)):
            players[i].setAudioOutput(outputs[i])
        
        return players, outputs
    def stop(self, ch:int)->None:
        self.players[ch].stop()
        
    def stop_all(self):
        for i in range(len(self.players)):
            self.stop(i)
        
    
    def play(self, ch:int, source:QUrl)->None:
        self.players[ch].setSource(source)
        self.players[ch].play()

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
        
        
        

