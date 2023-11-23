import sys

from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        timestamped_message = f"{get_timestamp()} - {message}"
        self.terminal.write(timestamped_message)
        self.log.write(timestamped_message)

    def flush(self):
        # Esta función es necesaria para la compatibilidad con el flujo stdout.
        self.terminal.flush()
        self.log.flush()
