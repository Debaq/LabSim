"""FuncLogin.py"""
# pylint: disable=no-name-in-module
import requests as http_requests
from core.helpers import Preferences
from backend.client import BackendClient
from core.base import context

pref_data = Preferences()

class LoginFallido:
    """Login que no resultó, con el motivo para mostrar. Es falso (como el 0
    de antes), así que quien solo pregunta "¿entró?" sigue funcionando."""

    def __init__(self, mensaje: str):
        self.mensaje = mensaje

    def __bool__(self) -> bool:
        return False


class LoginConnect():
    """Conecta la gui con labsim_backend."""
    def __init__(self) -> None:
        pass

    def login(self, username: str, password: str) -> dict:
        """
        Login contra labsim_backend. El admin usa usuario+contraseña; el
        alumno deja el usuario vacío y pone en la contraseña el código de
        6 dígitos que le mostró el navegador tras loguearse en Moodle (LTI).

        Args:
            username (str): usuario admin, o vacío si es login de alumno
            password (str): contraseña admin, o código de 6 dígitos
        Returns:
            dict: datos del usuario, o LoginFallido (falso) con el motivo
        """
        session_file = context.get_resource('json/session.json')
        client = BackendClient(pref_data.get("BACKEND_URL"), session_file)
        code = password.strip()
        try:
            if not username.strip() and code.isdigit() and len(code) == 6:
                result = client.pair_exchange(code)
            else:
                result = client.login_admin(username, password)
        except http_requests.HTTPError as exc:
            # El servidor dice por qué (cuenta bloqueada, contraseña o código
            # que no sirven, demasiados intentos): eso es lo que se muestra.
            return LoginFallido(str(exc) or "No es posible ingresar")
        except http_requests.RequestException:
            return LoginFallido("No hay conexión con el servidor. Revisa la red e inténtalo de nuevo.")
        except KeyError:
            return LoginFallido("No es posible ingresar")

        user = result["user"]
        return {
            'user': user["username"],
            'name': user["display_name"],
            'permission': user["permission"],
            # None = sin restricción (admin completo, ver Auth::userProfile
            # en el backend) -- "or []" acá convertiría ese None en [] y
            # bloquearía al admin, por eso se preserva tal cual.
            'modules': user.get("modules"),
            # Atajos propios y mouse para zurdos: viajan con la cuenta (ver
            # core/preferencias.py).
            'prefs': user.get("prefs") or {},
            'cases': {},
        }
