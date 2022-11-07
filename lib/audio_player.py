from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtCore import QUrl

class Player():
    def __init__(self, channels:int) -> None:
        self.channels, self.outputs = self.create_channels(channels)
    
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
        self.channels[ch].stop()
        
    
    def play(self, ch:int, source:QUrl)->None:
        self.channels[ch].setSource(source)
        self.channels[ch].play()

    def volume(self, ch:int, value:int) -> None:
        self.outputs[ch].setVolume(value)
    
    def status(self, ch:int)->int:
        return self.channels[ch].mediaStatus()
        
        

