

class CircularListIterator:
    def __init__(self, lst):
        self.lst = lst
        self.current_index = 0
    
    def next(self):
        value = self.lst[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.lst)
        return value
    
    def prev(self):
        value = self.lst[self.current_index]
        self.current_index = (self.current_index - 1) % len(self.lst)
        return value
    
    
class VerificadorDeNumero:
    def __init__(self, list_number):
        self.anterior = 0
        self.list_iterator = CircularListIterator(list_number)
    
    def verificar(self, numero):
        if numero == 0 and self.anterior == 100:
            return self.list_iterator.next()
        elif numero == 100 and self.anterior == 0:
            return self.list_iterator.prev()
        elif numero > self.anterior:
            return self.list_iterator.next()
        elif numero < self.anterior:
            return self.list_iterator.prev()
        else:
            print("nada que hacer")
        self.anterior = numero
        
"""    
list_db = list(range(0,125,5))
    
verificador = VerificadorDeNumero(list_db)

for i in range(100):
    print(verificador.verificar(i))
"""  
import numpy as np
import simpleaudio as sa
import threading
import time

class TonoReproductor:
    def __init__(self, frecuencia, amplitud, tasa_muestreo, tipo='tono_puro'):
        self.frecuencia = frecuencia
        self.amplitud = amplitud
        self.tasa_muestreo = tasa_muestreo
        self.tipo = tipo
        self.generar_senal()
        self.reproduciendo = False
        self.thread_reproducir = None
        self.thread_temporizador = None

    def generar_senal(self):
        if self.tipo == 'tono_puro':
            self.senal = self.generar_tono_puro()
        elif self.tipo == 'white_noise':
            self.senal = self.generar_white_noise()
        elif self.tipo == 'narrow_band':
            self.senal = self.generar_narrow_band()
        else:
            raise ValueError("Tipo de señal desconocido")

    def generar_tono_puro(self):
        tiempo = np.linspace(0, 1, self.tasa_muestreo, False)
        tono = self.amplitud * np.sin(2 * np.pi * self.frecuencia * tiempo)
        return tono.astype(np.float32)

    def generar_white_noise(self):
        ruido_blanco = np.random.normal(0, self.amplitud, self.tasa_muestreo*20)
        return ruido_blanco.astype(np.float32)

    def generar_narrow_band(self):
        anchura_banda = ((self.frecuencia*2)-self.frecuencia)/6
        ruido_blanco = np.random.normal(0, self.amplitud/2, self.tasa_muestreo*20)
        filtro = np.sinc(2 * anchura_banda * (np.arange(self.tasa_muestreo) - self.tasa_muestreo // 2) / self.tasa_muestreo)
        banda_estrecha = np.convolve(ruido_blanco, filtro, mode='same')
        return banda_estrecha.astype(np.float32)

    def reproducir_senal(self):
        while self.reproduciendo:
            stream = sa.play_buffer(self.senal, 1, 4, self.tasa_muestreo)
            #stream.wait_done()
            return stream
        stream.stop()
        print("se termino")

    def temporizador(self):
        inicio = time.time()
        while self.reproduciendo:
            tiempo_actual = time.time() - inicio
            print(f"Tiempo transcurrido: {int(tiempo_actual)} segundos")
            time.sleep(1)

    def play(self):
        if not self.reproduciendo:
            self.reproduciendo = True
            self.thread_reproducir = threading.Thread(target=self.reproducir_senal)
            self.thread_reproducir.start()
            self.thread_temporizador = threading.Thread(target=self.temporizador)
            self.thread_temporizador.start()

    def stop(self):
        self.reproduciendo = False
        if self.thread_reproducir:
            self.thread_reproducir.join()
            self.thread_reproducir = None
        if self.thread_temporizador:
            self.thread_temporizador.join()
            self.thread_temporizador = None


"""
# Parámetros
# Parámetros
frecuencia = 1000  # Frecuencia en Hz (ejemplo: 440 Hz es la nota La)
amplitud = 0.5    # Amplitud (entre 0 y 1)
tasa_muestreo = 44100  # Tasa de muestreo en Hz (ejemplo: 44100 Hz es calidad de CD)

# Crear y reproducir un tono puro
reproductor_tono_puro = TonoReproductor(frecuencia, amplitud, tasa_muestreo, tipo='tono_puro')
reproductor_tono_puro.play()

# Detener la reproducción después de un tiempo (por ejemplo, 5 segundos)
time.sleep(5)
reproductor_tono_puro.stop()

# Crear y reproducir ruido blanco
reproductor_white_noise = TonoReproductor(frecuencia, amplitud, tasa_muestreo, tipo='white_noise')
reproductor_white_noise.play()

# Detener la reproducción después de un tiempo (por ejemplo, 5 segundos)
time.sleep(5)
reproductor_white_noise.stop()

# Crear y reproducir una banda estrecha
reproductor_narrow_band = TonoReproductor(frecuencia, amplitud, tasa_muestreo, tipo='narrow_band')
reproductor_narrow_band.play()

# Detener la reproducción después de un tiempo (por ejemplo, 5 segundos)
time.sleep(5)
reproductor_narrow_band.stop()
"""