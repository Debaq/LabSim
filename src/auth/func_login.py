"""FuncLogin.py"""
# pylint: disable=no-name-in-module
import requests as http_requests
from core.helpers import Preferences
from backend.client import BackendClient
from core.base import context

pref_data = Preferences()

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
            dict: datos del usuario, o 0 si falló el login/la conexión
        """
        session_file = context.get_resource('json/session.json')
        client = BackendClient(pref_data.get("BACKEND_URL"), session_file)
        code = password.strip()
        try:
            if not username.strip() and code.isdigit() and len(code) == 6:
                result = client.pair_exchange(code)
            else:
                result = client.login_admin(username, password)
        except (http_requests.RequestException, KeyError):
            return 0

        user = result["user"]
        return {
            'user': user["username"],
            'name': user["display_name"],
            'permission': user["permission"],
            'modules': user.get("modules") or [],
            'cases': {},
        }
