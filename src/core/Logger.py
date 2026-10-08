import sys

from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Sin stream explícito sale por stdout (ver Logger.__init__).
_STDOUT = object()


class _Archivo:
    """El archivo del registro, compartido por stdout y stderr: al rotar
    (ver Logger.rotar_si_hace_falta) los dos pasan juntos al nuevo."""

    def __init__(self, filename):
        self.filename = filename
        self.abrir()

    def abrir(self):
        # utf-8 explícito: en Windows el default es cp1252 y un carácter
        # fuera de esa tabla hacía fallar el print() mismo.
        self.f = open(self.filename, "a", encoding="utf-8", errors="replace")


_archivos = {}


class Logger(object):
    # Cada cuántas escrituras se mira el tamaño del registro.
    REVISAR_CADA = 500

    def __init__(self, filename, log_queue=None, stream=_STDOUT, max_bytes=None, rotar=None):
        # stream: a donde sigue saliendo lo que se escribe, ademas del
        # archivo. Por defecto stdout; para stderr hay que pasarlo, si no
        # los errores terminaban mezclados en la salida estandar. En un
        # build sin consola (PyInstaller windowed) es None y ahi solo queda
        # el archivo. (Antes un None caía a sys.stdout, que a esa altura ya
        # era el Logger de stdout: cada error quedaba dos veces.)
        self.terminal = sys.stdout if stream is _STDOUT else stream
        self._archivo = _archivos.setdefault(str(filename), _Archivo(filename))
        # Cola local opcional (ver lib/backend/log_queue.py): junta lo que se
        # imprime para subirlo despues al backend en lotes, sin bloquear acá
        # por red -- push() solo escribe a un sqlite local.
        self.log_queue = log_queue
        self._linea_nueva = True
        # Un kiosko pasa días sin reiniciar: rotar solo al arrancar dejaba
        # crecer el registro sin tope. `rotar(ruta)` es core/registro.rotar.
        self._max_bytes = max_bytes
        self._rotar = rotar
        self._escrituras = 0

    @property
    def log(self):
        return self._archivo.f

    def write(self, message):
        # La hora va solo al empezar una linea: un traceback llega en
        # varios write() sueltos (uno por pedazo) y antes quedaba con dos o
        # tres marcas de hora metidas en medio de la misma linea.
        prefijo = f"{get_timestamp()} - " if self._linea_nueva else ""
        timestamped_message = f"{prefijo}{message}"
        self._linea_nueva = message.endswith("\n")
        # Escribir el registro nunca puede tirar abajo a quien imprime.
        if self.terminal is not None:
            try:
                self.terminal.write(timestamped_message)
            except (OSError, ValueError, UnicodeError):
                pass
        try:
            self.log.write(timestamped_message)
            # Sin flush acá, esto queda en el buffer de Python hasta que se
            # llene o el proceso cierre -- print() no hace flush solo porque
            # este objeto no es un TTY real (no tiene isatty()).
            self.log.flush()
        except (OSError, ValueError):
            pass
        if self.log_queue is not None and message.strip():
            self.log_queue.push("console", {"message": message.strip()})
        self._escrituras += 1
        if self._escrituras % self.REVISAR_CADA == 0 and self._linea_nueva:
            self.rotar_si_hace_falta()

    def rotar_si_hace_falta(self):
        if self._max_bytes is None or self._rotar is None:
            return
        try:
            if self.log.tell() < self._max_bytes:
                return
            self.log.close()
        except (OSError, ValueError):
            return
        # En Windows no se puede renombrar un archivo abierto por otro
        # proceso: rotar() lo ataja y se sigue en el mismo.
        self._rotar(self._archivo.filename)
        try:
            self._archivo.abrir()
        except OSError:
            pass

    def flush(self):
        # Esta función es necesaria para la compatibilidad con el flujo stdout.
        try:
            if self.terminal is not None:
                self.terminal.flush()
            self.log.flush()
        except (OSError, ValueError):
            pass
