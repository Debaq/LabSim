# -*- coding: utf-8 -*-

#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#              VER. 0.1 - Audiometro - Herramientas             #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

import json
import codecs
from fbs_runtime.application_context.PyQt5 import ApplicationContext

appctxt = ApplicationContext()


class Preferences:
    """preferencias del programa"""

    def __init__(self):
        preferences_file = appctxt.get_resource('json/json_list.json')
        with codecs.open(preferences_file, 'r', 'utf-8') as json_file:
            list_data = json.load(json_file)
        self.data = {}
        for i in list_data:
            file = appctxt.get_resource('json/{}'.format(list_data[i]))
            with codecs.open(file, 'r', 'utf-8') as json_file:
                data = json.load(json_file)
            self.data.update(data)

    def get(self, pref):
        """recupera las prefernecias desde un archivo *.json"""
        #print(self.data[pref])
        return self.data[pref]

    def set(self, pref, var):
        """modifica una configuración"""


# keyboard_shortcuts : [up_dial_izq,down_dial_izq,up_dial_der,down_dial_der],

# frecuency_dict:
#             {"Nombre de la prueba":[[aérea],[ósea],[campo libre]]}
#             {"Nombre de la prueba": [[min,max],[add_others list], [high_f list]],....}
#             transductor 0 : aérea
#             transductor 1 : óseo
#             transductor 2 : Campo Libre

# intency_dict:
#             { "nombre del estimulo": [[aerea],[osea],[campo libre]]}
#             { "nombre del estimulo": [[[min , max],[extend]],....
#             transductor 0 : aérea
#             transductor 1 : óseo
#             transductor 2 : Campo Libre

class Lang:
    """lenguaje del software"""
    def __init__(self):
        class_pref = Preferences()
        lang = class_pref.get("Lang")
        file_po = appctxt.get_resource('json/{}.json'.format(lang))
        with codecs.open(file_po, 'r', 'utf-8') as json_file:
            self.lng_po = json.load(json_file)


    def get(self, request):
        """obtiene la traducción del objeto"""
        try:
            get_str = self.lng_po[request]
            if len(get_str) > 1:
                result = self._listToString(get_str)
        except KeyError:
            result = request
        return result

    def _listToString(self, s):
        str1 = ""
        for ele in s:
            str1 += ele
        return str1
