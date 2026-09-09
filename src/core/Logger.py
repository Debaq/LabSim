import sys

from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Logger(object):
    def __init__(self, filename, log_queue=None):
        self.terminal = sys.stdout
        self.log = open(filename, "a")
        # Cola local opcional (ver lib/backend/log_queue.py): junta lo que se
        # imprime para subirlo despues al backend en lotes, sin bloquear acá
        # por red -- push() solo escribe a un sqlite local.
        self.log_queue = log_queue

    def write(self, message):
        timestamped_message = f"{get_timestamp()} - {message}"
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
        self.terminal.flush()
        self.log.flush()
