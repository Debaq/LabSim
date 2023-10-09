import sys
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QAudio
from PySide6.QtCore import QByteArray, QBuffer
from scipy.signal import butter, lfilter

class NoisePlayer:
    def __init__(self, duration=1.0, sample_rate=44100, channel="both"):
        format = QAudioFormat()
        format.setSampleRate(sample_rate)
        format.setChannelCount(2)  # Estéreo
        format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        self.audio_sink = QAudioSink(format)
        self.duration = duration
        self.sample_rate = sample_rate
        self.channel = channel  # "left", "right", o "both"

    def get_noise_filename(self, noise_type):
        return f"{noise_type}_{self.sample_rate}_{self.duration}.dat"
    
    def play(self, noise_type="white"):
        
        if noise_type == "white":
            data = self.generate_white_noise()
        elif noise_type == "pink":
            data = self.generate_pink_noise()
        elif noise_type == "nbn":
            data = self.generate_nbn()
        elif noise_type == "tone":
            data = self.generate_tone()
        else:
            raise ValueError("Invalid noise type")

        # Ajustar el canal de salida
        if self.channel == "left":
            data = np.column_stack((data, np.zeros_like(data)))
        elif self.channel == "right":
            data = np.column_stack((np.zeros_like(data), data))
        elif self.channel == "both":
            data = np.column_stack((data, data))
        else:
            raise ValueError("Invalid channel")

        # Convertir a QByteArray
        byte_data = QByteArray(data.tobytes())

        # Usar QBuffer para leer los datos
        audio_buffer = QBuffer()
        audio_buffer.setData(byte_data)
        audio_buffer.open(QBuffer.ReadOnly)
        audio_buffer.seek(0)

        # Reproducir
        self.audio_sink.start(audio_buffer)


    def generate_white_noise(self):
        white_noise = np.random.randn(int(self.sample_rate * self.duration))
        max_val = np.iinfo(np.int16).max
        return (white_noise * max_val).astype(np.int16)

    def generate_pink_noise(self):
        # Voss-McCartney algorithm
        num_samples = int(self.sample_rate * self.duration)
        num_rows = 16
        array = np.random.randn(num_rows, num_samples // num_rows + 1)
        reshaped_array = np.reshape(array, (num_rows, -1), order='F')
        reshaped_array = reshaped_array[:, :num_samples]
        pink_noise = np.cumsum(reshaped_array)
        pink_noise = pink_noise[-1, :]
        max_val = np.iinfo(np.int16).max
        return (pink_noise * max_val / np.max(np.abs(pink_noise))).astype(np.int16)

    def generate_nbn(self, center_freq=1000):
        white_noise = np.random.randn(int(self.sample_rate * self.duration))
        b, a = butter(1, [(center_freq - center_freq/3)/(self.sample_rate/2), (center_freq + center_freq/3)/(self.sample_rate/2)], btype='band')
        nbn = lfilter(b, a, white_noise)
        max_val = np.iinfo(np.int16).max
        return (nbn * max_val).astype(np.int16)

    def generate_tone(self, frequency=1000):
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration), endpoint=False)
        tone = np.sin(2 * np.pi * frequency * t)
        max_val = np.iinfo(np.int16).max
        return (tone * max_val).astype(np.int16)
    
    def stop_playback(self):
        self.audio_sink.stop()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = NoisePlayer(duration=5, channel="left")  # Sonará solo en el canal izquierdo
    player.play(noise_type="tone")  # Change to "white", "pink", or "nbn" as needed
    sys.exit(app.exec())
