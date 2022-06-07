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
from base import context


class Preferences:
    """preferencias del programa"""

    def __init__(self):
        preferences_file = context.get_resource('json/json_list.json')
        with codecs.open(preferences_file, 'r', 'utf-8') as json_file:
            list_data = json.load(json_file)
        self.data = {}
        for i in list_data:
            file = context.get_resource('json/{}'.format(list_data[i]))
            with codecs.open(file, 'r', 'utf-8') as json_file:
                data = json.load(json_file)
            self.data.update(data)

    def get(self, pref):
        """recupera las prefernecias desde un archivo *.json"""
        #print(self.data[pref])
        return self.data[pref]

    def set(self, pref, var):
        """modifica una configuración"""
    
    def getAll(self, p =False):
        if p == False:
            return self.data
        else:
            print("estoy aquí")
            print(self.data)
    
    def getAllKeys(self):
        data = list()
        for i in self.data:
            data.append(i)
        return data

    def getStyle(self, wid):
        stylePred = self.data["styles"][0]
        style = self.data["styles"][1][stylePred]
        style = context.get_resource('styles/{}.qss'.format(style))
        with open(style,"r") as fh:
            wid.setStyleSheet(fh.read())

# keyboard_shortcuts : [up_dial_izq,down_dial_izq,up_dial_der,down_dial_der],

# frecuency_dict:
#             {"Nombre de la prueba":[[Aerea],[Osea],[campo libre]]}
#             {"Nombre de la prueba": [[min,max],[add_others list], [high_f list]],....}
#             transductor 0 : Aerea
#             transductor 1 : óseo
#             transductor 2 : Campo Libre

# intency_dict:
#             { "nombre del estimulo": [[aerea],[osea],[campo libre]]}
#             { "nombre del estimulo": [[[min , max],[extend]],....
#             transductor 0 : Aerea
#             transductor 1 : óseo
#             transductor 2 : Campo Libre

class Lang:
    """lenguaje del software"""
    def __init__(self):
        class_pref = Preferences()
        lang = class_pref.get("Lang")
        file_po = context.get_resource('json/{}.json'.format(lang))
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
        return "".join(s)


class Storage:
    def __init__(self, n):
        self.n = n
        self.data = []
        self.create(n)

    def length(self, ran= False):
        if ran == False:
            return len(self.data)
        else:
            return range(len(self.data))

    def create(self,n):
        for _ in range(n):
            self.data.append(None)

    def clean(self):
        self.data = []
        self.create(self.n)

    def get(self, idx):
        return self.data[idx]

    def set(self, idx, dat):
        self.data[idx] = dat

    def listSet(self, dat, noRe = True):
        if noRe:
            if len(dat) == len(self.data):
                for idx in dat:
                    self.data[idx] = dat[idx]
        else:
            self.n = len(dat)
            self.clean()
            for idx in range(len(dat)):
                self.data[idx] = dat[idx]

    def agrege(self, idx, dat):
        try:
            self.data[idx].append(dat)
        except:
            self.data[idx] = list()
            self.data[idx].append(dat)

    def isFull(self, idx):
        return self.data[idx] is not None
    
    def isNull(self, idx):
        return not self.isFull(idx)

    def isEmpty(self):
        return any(i is None for i in self.data)
    
    def getAll(self, p =False):
        if p == False:
            return self.data
        else:
            print("estoy aca")
            print(self.data)