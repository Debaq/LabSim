from numpy import linspace,sin,pi,int16
from scipy.io.wavfile import write
from scipy.signal import chirp

# tone synthesis
def note(freq, len, amp=1, rate=44100):
 t = linspace(0,len,len*rate)
 data = sin(2*pi*freq*t)*amp
 return data.astype(int16) # two byte integers


# A tone, 2 seconds, 44100 samples per second

tones = [500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000]

for i in tones:
    tone = note(i,10,amp=10000)
    name = f"{i}.wav"
    write(name,44100,tone) # writing the sound to a file
