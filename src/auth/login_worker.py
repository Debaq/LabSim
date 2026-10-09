# pylint: disable=no-name-in-module
"""Un intento de login fuera del hilo de la ventana.

Sin esto, el HTTP a /api/admin_login.php (o /api/pair_exchange.php) corre
en el thread de la GUI y la ventana de login queda congelada hasta que
responde el backend -- sensación de "no pasa nada". MainLogin lo corre con
hilos.en_fondo (hilo de Python, sin QThread ni worker de Qt: ver los
cierres del 2026-09-07 y del 2026-10-09 en core/hilos.py) y muestra un
spinner mientras dura la request.
"""
from auth.func_login import LoginConnect


def intentar_login(name: str, passw: str):
    """Lo mismo que LoginConnect.login(): dict con datos del usuario si
    todo OK, o 0 si falló red/credenciales."""
    try:
        return LoginConnect().login(name, passw)
    except Exception:  # noqa: BLE001
        # red de seguridad: LoginConnect.login() ya captura
        # RequestException/KeyError, pero cualquier otra excepción
        # inesperada debe terminar como "no se pudo loguear"
        # (mismo path que el catch interno del LoginConnect).
        return 0
