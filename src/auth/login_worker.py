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
    """Ejecuta un único intento de login y emite el resultado.

    El shape del resultado es el mismo que devuelve LoginConnect.login():
    dict con datos del usuario si todo OK, o 0 si falló red/credenciales.
    Eso permite que MainLogin._verify_result(result) se reuse sin cambios.
    """
    finished = Signal(object)

    def __init__(self, name: str, passw: str):
        super().__init__()
        self._name = name
        self._passw = passw

    def run(self) -> None:
        try:
            result = LoginConnect().login(self._name, self._passw)
        except Exception:
            # red de seguridad: LoginConnect.login() ya captura
            # RequestException/KeyError, pero cualquier otra excepción
            # inesperada debe terminar como "no se pudo loguear"
            # (mismo path que el catch interno del LoginConnect).
            result = 0
        self.finished.emit(result)
