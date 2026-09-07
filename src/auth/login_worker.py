# pylint: disable=no-name-in-module
"""Worker one-shot que ejecuta LoginConnect.login() en un hilo aparte.

Sin esto, el HTTP a /api/admin_login.php (o /api/pair_exchange.php) corre
en el thread de la GUI y la ventana de login queda congelada hasta que
responde el backend -- sensación de "no pasa nada". Con este worker +
moveToThread, la UI queda libre y MainLogin muestra un spinner mientras
dura la request.
"""
from PySide6.QtCore import QObject, Signal

from auth.func_login import LoginConnect


class LoginWorker(QObject):
    """Ejecuta un único intento de login y deja el resultado en `.result`.

    `finished` no lleva argumentos a propósito: el resultado se lee desde
    el thread de la GUI recién cuando el QThread terminó (ver
    MainLogin._on_login_finished), así no viaja un objeto Python por una
    conexión cross-thread mientras el worker todavía está vivo.

    El shape de `.result` es el mismo que devuelve LoginConnect.login():
    dict con datos del usuario si todo OK, o 0 si falló red/credenciales.
    """
    finished = Signal()

    def __init__(self, name: str, passw: str):
        super().__init__()
        self._name = name
        self._passw = passw
        self.result = 0

    def run(self) -> None:
        try:
            self.result = LoginConnect().login(self._name, self._passw)
        except Exception:
            # red de seguridad: LoginConnect.login() ya captura
            # RequestException/KeyError, pero cualquier otra excepción
            # inesperada debe terminar como "no se pudo loguear"
            # (mismo path que el catch interno del LoginConnect).
            self.result = 0
        self.finished.emit()
