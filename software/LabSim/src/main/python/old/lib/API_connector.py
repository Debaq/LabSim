# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 1.0 - CONECTOR API                 #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

import json
import requests

## URL donde esta alojada la API

class API:
    """
    conector con la API del servidor
    Para iniciarla es necesario la url del php receptor
    en formato str.
    EJ.: URL = 'https://tmeduca.cl/AudioSim/lib/API.php'
    """
    def __init__(self, URL):
        self.URL = URL
        
    def send_requests(self, data):
        """
        Envia solicitudes mediante POST a la API correspondiente.

        Args:
            data (dict): diccionario con la info que se enviará.

        Returns:
            json : diccionario con la info retornada desde la API.
        """
        response = requests.post(self.URL, data=data)
        string_response=(response.text)
       # print(string_response)

        try:
            result = json.loads(string_response)
            return result
        except:
            pass
            #print(string_response)

    def exit(self, user):
        t_request = "close_session"
        request_array = {'request':t_request, 'user':user}
        return self.send_requests(request_array)
        
    def send_requests_s(self, data):
        """
        Envia solicitudes mediante POST a la API correspondiente.

        Args:
            data (dict): diccionario con la info que se enviará.

        Returns:
            json : diccionario con la info retornada desde la API.
        """
        response = requests.post(self.URL, data=data)
        string_response=(response.text)
    
        #result = json.loads(string_response)
        
        #print(string_response)
        return string_response

    def r_key(self, **kwargs):
        """conexión a la APi con un código predefinido"""

        t_request = "login"

        if "name" in kwargs:
            name_user = kwargs['name']
            password = kwargs['pasw']
            code = "None"
        else:
            code = kwargs['code']
            name_user = "code3216"
            password = "00000"

        request_array = {'request':t_request, 'user':name_user, 'password':password, 'code':code}
        
        return self.send_requests(request_array)
    


    def read_data(self, code):
        """
        Solicitud de la información mediante código de sesión.

        Args:
            code (str): el código de la sesión.

        Returns:
            json: diccionario con los datos.
        """
        t_request = "read_data"
        request_array = {'request':t_request, 'code':code}
        result = self.send_requests(request_array)
        #result = result[0]
        return result


    def create_session(self, **kwargs):
        """
        Crea una sesión, retorna el código de la sesión"""
        t_request = "create_session"
        if "code" in kwargs:
            code = kwargs['code']

            request_array = {'request':t_request, 'code':code}
            self.send_requests(request_array)


    def write_data(self, code, data, user):
        """
        Envia información a la APi para que actualice la sesión y el log.

        Args:
            code (str): codigo de la sesión
            data (dict): diccionario con la información a modificar.

        Returns:
            json: diccionario actualizado
        """
        t_request = "write_data"
        data = json.dumps(data)
        request_array = {'request':t_request,'user': user, 'code':code, 'data':data}
        result = self.send_requests(request_array)
        #result = result[0]
        return result


class PostData:
    """POSTDATA
    exporta los datos de estado en el display de de botones al
    archivo de intercambio en el servidor principal
    """

    def __init__(self, session, user, API):
        self.request = API
        self.session = session
        self.user = user
        self.data_old = self.request.read_data(self.session)

    def send(self, data, online=True):
        
        #data = data
        if online:
            for key, value in data.items():
                if key in self.data_old:
                    if data[key] != self.data_old[key]:
                        datum = {key: value}
                        self.data_old = self.request.write_data(
                            self.session, datum, self.user)
                    else:
                        pass
                else:
                    datum = {key: value}
                    self.data_old = self.request.write_data(
                        self.session, datum, self.user)
                #print(self.data_old)
