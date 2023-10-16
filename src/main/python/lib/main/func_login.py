"""FuncLogin.py"""
# pylint: disable=no-name-in-module
import requests as http_requests
import cryptocode as crypto
from lib.helpers import Preferences, CasesOffline

pref_data = Preferences()

class LoginConnect():
    """
    Conecta la gui con la api service en modo online,
    en modo offline se usa una base de datos local guardada en un archivo json
    """
    def __init__(self) -> None:
        pass

    def login(self, username:str, password:str, online:bool) -> dict:
        
        """
        recibe el usuario y contraseña y devuelve un 
        diccionario con los datos del caso
        Args:
            username (str): username del login
            password (str): password del login
            online (bool): True si se quiere conectar en modo online
        returns:
            dict: datos del caso        
        """
        data =  {'user': username, 'password': password, 'request': 'login'}
        print(f"login_in : {username},{password},{online}")
        print(f"data_login:{data}")
        test = self.request_api(data) if online else self.request_offline(data)
        print(f"test:{test}")
        return test

    def request_api(self, data):
        """
        conecta con la api service en modo online o devuelve error
        de conexion 0 si no responde el servidor.
        NOTA: deberia devolver diferentes tipos de errores además deberia
        poder ser capas de obtener la dirección desde un json almacenado
        
        Args:
            data (dict): datos del login
        Returns:
            dict: datos del caso
        """
        _url = self._get_url_api()
        try:
            response = http_requests.post(_url, data=data)
            response.raise_for_status()
        except Exception:
            return 0
        return response.text

    def _get_url_api(self) -> str:
        """devuelve la url de la api service"""
        return pref_data.get("API_URL")

    def request_offline(self, data) -> dict:
        """
        verifica si el usuario y contraseña son correctos
        y devuelve los datos del caso

        Args:
            data (dict): datos del login
        Returns:
            dict: datos del caso
        """
        print("request is offline")
        verify = self._verify_key(data['user'], data['password'])
        print(f"verify:{verify}")
        if verify and verify[0]:
            return {'user': data['user'],
                    'name': verify[0],
                    'permission':verify[1],
                    'modules':verify[2],
                    'cases': self._get_data_case_offline(data)
                    }
        return 0

    def _verify_key(self, username:str, password:str) -> tuple:
        """
        verifica si la llave es valida

        Args:
            username (str): username del login
            password (str): password del login

        Returns:
            tuple: devuelve una tupla con el resultado de la verificacion
            bool: 0 en caso de error

        """
        keys = pref_data.get("keys_app")
        print(f"keys:{keys}")
        if username in keys:
            print(f"key:{keys[username]['key']}")
            verify = crypto.decrypt(keys[username]["key"], password)
            permission = keys[username]["permission"]
            modules = keys[username]["modules"]
            return [verify, permission, modules]
        return 0

    def _get_data_case_offline(self, data:dict) -> dict:
        """
        Devuelve los datos del caso offline
        Args:
            data (dict): datos del login
        Returns:
            dict: datos del caso
        ojo: aca hay que poner la logica para desencriptar los caso, 
        por ahora estan en un json sin encriptación
        
        """
        return CasesOffline().get_cases(data["user"])
