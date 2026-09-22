import sys

from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Logger(object):
    def __init__(self, filename, log_queue=None, stream=None):
        # stream: a donde sigue saliendo lo que se escribe, ademas del
        # archivo. Por defecto stdout; para stderr hay que pasarlo, si no
        # los errores terminaban mezclados en la salida estandar. En un
        # build sin consola (PyInstaller windowed) puede ser None y ahi
        # solo queda el archivo.
        self.terminal = stream if stream is not None else sys.stdout
        self.log = open(filename, "a")
        # Cola local opcional (ver lib/backend/log_queue.py): junta lo que se
        # imprime para subirlo despues al backend en lotes, sin bloquear acá
        # por red -- push() solo escribe a un sqlite local.
        self.log_queue = log_queue
        self._linea_nueva = True

    def write(self, message):
        # La hora va solo al empezar una linea: un traceback llega en
        # varios write() sueltos (uno por pedazo) y antes quedaba con dos o
        # tres marcas de hora metidas en medio de la misma linea.
        prefijo = f"{get_timestamp()} - " if self._linea_nueva else ""
        timestamped_message = f"{prefijo}{message}"
        self._linea_nueva = message.endswith("\n")
        if self.terminal is not None:
            self.terminal.write(timestamped_message)
        self.log.write(timestamped_message)
        # Sin flush acá, esto queda en el buffer de Python hasta que se
        # llene o el proceso cierre -- print() no hace flush solo porque
        # este objeto no es un TTY real (no tiene isatty()).
        self.log.flush()
        if self.log_queue is not None and message.strip():
            self.log_queue.push("console", {"message": message.strip()})

    def flush(self):
        # Esta función es necesaria para la compatibilidad con el flujo stdout.
        if self.terminal is not None:
            self.terminal.flush()
        self.log.flush()
