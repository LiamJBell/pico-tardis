from audiomp3 import MP3Decoder
import audiobusio
import board

class mp3Player:
    
    def __init__(self, BCLK_PIN, LRC_PIN, DIN_PIN) -> None:
        self.BLCK_PIN = BCLK_PIN
        self.LRC_PIN = LRC_PIN
        self.DIN_PIN = DIN_PIN
        self.decoder = MP3Decoder()
        self.audioOut = audiobusio.I2SOut(self.BLCK_PIN, self.LRC_PIN, self.DIN_PIN)
        

    def setSoundsFolder(self, dir) -> None:
        self.soundsFolder = dir
    
    def isPlaying(self) -> bool:
        return self.audioOut.playing
    
    def playMp3(self,filename) -> None:
        if self.isPlaying:
            return False
        else:
            self.decoder.file = open(filename, "rb")
            self.audioOut.play(self.decoder)