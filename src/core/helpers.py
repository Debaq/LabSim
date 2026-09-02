# -*- coding: utf-8 -*-
"""
Helpers:
CasesOfline: clase para manejar los casos en modo offline
Preferences: clase para manejar las preferencias
Lang: clase para manejar los idiomas
Store: clase para crear almacenamientos
"""

#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#              VER. 0.1 - Audiometro - Herramientas             #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################
# pylint: disable=no-name-in-module, import-error

import json
import codecs
from core.base import context
import random
from datetime import datetime
from copy import deepcopy
import os

from backend.client import BackendClient
from backend.cases_sync import backend_state_to_cases, diff_and_push_cases
from backend.shedule_sync import backend_state_to_shedule, diff_and_push_shedule

# Snapshot en memoria de la última foto conocida del backend, para poder
# diffear en Shedule.set()/CasesOffline.set_cases() y empujar solo lo que
# cambió. Vive a nivel de módulo porque cada llamador crea una instancia
# nueva de Shedule()/CasesOffline() en cada lectura/escritura (ver Agenda.py,
# create_a.py, main.py): no hay una sola instancia larga donde guardarlo.
_backend_client = None
_shedule_snapshot = {"agenda_1": {}}
_cases_snapshot = {}


def _online_mode():
    """Mismo criterio que ONLINE en main.py: 'test' fuerza 'development'."""
    pref = Preferences()
    return "development" if pref.get("test") else pref.get("online")


def _is_backend_mode() -> bool:
    return _online_mode() == "backend"


def _get_backend_client() -> BackendClient:
    global _backend_client
    if _backend_client is None:
        pref = Preferences()
        session_file = context.get_resource('json/session.json')
        _backend_client = BackendClient(pref.get("BACKEND_URL"), session_file)
    return _backend_client


def chat_con_paciente(case_id, nombre, edad, procedimiento, history, message, appointment_id=None):
    """Un turno de chat con el paciente simulado por LLM.

    Solo disponible en modo backend (el LLM vive en el servidor, no en la
    app offline) -- lanza RuntimeError con mensaje para mostrar al alumno si
    no lo está. Devuelve el texto de respuesta del paciente.

    appointment_id: cita real a la que se le asocia el chat guardado (ver
    LlmChat.php) -- None cuando no corresponde dejar rastro (ej. "Atender
    (prueba)" del admin).
    """
    if not _is_backend_mode():
        raise RuntimeError("El chat con el paciente requiere conexión al servidor.")
    client = _get_backend_client()
    result = client.llm_chat(case_id, nombre, edad, procedimiento, history, message, appointment_id)
    return result["reply"]


def reset_backend_session() -> None:
    """Descarta el singleton de BackendClient y los snapshots en memoria.

    func_login.py hace login con una instancia de BackendClient propia
    (para poder devolver el resultado sync antes de tocar este módulo), así
    que si ya existía un _backend_client de una sesión anterior (login
    previo sin pasar por acá, o cambio de usuario), queda con el token
    viejo en memoria aunque session.json ya tenga el nuevo -- el próximo
    request pega con el token/rol de la sesión anterior. Llamar esto en
    cuanto llega un login nuevo fuerza a releer session.json desde cero.
    """
    global _backend_client, _shedule_snapshot, _cases_snapshot
    _backend_client = None
    _shedule_snapshot = {"agenda_1": {}}
    _cases_snapshot = {}


class CasesOffline():
    """
    Clase para manejar los casos en modo offline.
    Los casos (definición del paciente/audiometría) son una única base
    compartida por todos los usuarios: el admin los crea una vez y todos
    los alumnos leen/atienden la misma definición. Lo que sí es propio de
    cada alumno (p.ej. si ya atendió el caso) vive aparte, en la agenda
    (ver `entry_atendido_por` / `marcar_entry_atendido`).
    Func:
        get_cases: devuelve la base de casos completa
    """
    def __init__(self) -> None:
        pass

    def get_def_cases(self, case) ->dict:
        cases_file = context.get_resource('cases/labsim.json')
        with codecs.open(cases_file, 'r', 'utf-8') as json_file:
            list_data = json.load(json_file)
        return list_data

    def get_cases(self) -> dict:
        """Recupera la base de casos compartida (backend si ONLINE == 'backend', si no local)."""
        global _cases_snapshot
        if _is_backend_mode():
            client = _get_backend_client()
            data = backend_state_to_cases(client.get_full_state())
            # deepcopy: quien llama muta el dict que le devolvemos (agrega
            # casos, edita anidados) -- si _cases_snapshot compartiera
            # referencia, esa mutación también "cambiaría" el snapshot y
            # el diff de más abajo nunca vería nada distinto que subir.
            _cases_snapshot = deepcopy(data)
            return data

        cases_file = context.get_resource('cases/cases.json')
        try:
            with codecs.open(cases_file, 'r', 'utf-8') as json_file:
                list_data = json.load(json_file)
        except FileNotFoundError:
            return {}
        return list_data

    def set_cases(self, cases:dict) -> None:
        """Guarda la base de casos compartida (backend si ONLINE == 'backend', si no local)."""
        global _cases_snapshot
        if _is_backend_mode():
            client = _get_backend_client()
            diff_and_push_cases(client, cases, _cases_snapshot)
            _cases_snapshot = deepcopy(cases)
            return

        cases_file = context.get_resource('cases/cases.json')
        with codecs.open(cases_file, 'w', 'utf-8') as json_file:
            json.dump(cases, json_file, ensure_ascii=False)

class Shedule:
    def __init__(self):
        global _shedule_snapshot
        if _is_backend_mode():
            client = _get_backend_client()
            own_id = (client.user or {}).get("id")
            own_username = (client.user or {}).get("username", "")
            state = client.get_full_state()
            print(f"[shedule_fetch] own_id={own_id!r} own_username={own_username!r} "
                  f"appointments={len(state.get('appointments', []))} keys={list(state.keys())}")
            for appt in state.get("appointments", []):
                print(f"[shedule_fetch]   cita id={appt.get('id')} fecha={appt.get('fecha')!r} "
                      f"hora={appt.get('hora')!r} cancelada={appt.get('cancelada')!r}")
            data = backend_state_to_shedule(state, own_id, own_username)
            # deepcopy por la misma razón que en CasesOffline.get_cases():
            # self.data se muta en el sitio (nuevas citas, edición de filas)
            # y sin esto esa mutación se filtraba también al snapshot.
            _shedule_snapshot = deepcopy(data)
            self.data = data
            return

        preferences_file = context.get_resource('json/schedule.json')
        with codecs.open(preferences_file, 'r', 'utf-8') as json_file:
            list_data = json.load(json_file)
        self.data = list_data


    def get(self):
        """recupera las prefernecias desde un archivo *.json"""
        #print(self.data[pref])
        return self.data

    def set(self, data:dict) -> None:
        """guarda la agenda (backend si ONLINE == 'backend', si no en *.json local)"""
        global _shedule_snapshot
        self.data = data
        if _is_backend_mode():
            client = _get_backend_client()
            own_username = (client.user or {}).get("username", "")
            diff_and_push_shedule(client, data, _shedule_snapshot, own_username)
            _shedule_snapshot = deepcopy(data)
            return

        preferences_file = context.get_resource('json/schedule.json')
        with codecs.open(preferences_file, 'w', 'utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False)


def _asegurar_dict_atencion(entry) -> dict:
    """Garantiza que entry[8] sea un dict {username: {"estado":..., "nota":...}}."""
    if len(entry) <= 8:
        entry.append({})
    elif not isinstance(entry[8], dict):
        entry[8] = {}
    return entry[8]


def entry_estado_por(entry, username: str) -> str | None:
    """
    Estado de atención de `username` sobre esta fila: None, "atendiendo" o "atendido".
    Formato legado: entry[8][username] == True (o entry[8] bool plano) se lee como "atendido".
    """
    if len(entry) <= 8:
        return None
    atencion = entry[8]
    if isinstance(atencion, dict):
        valor = atencion.get(username)
        if isinstance(valor, dict):
            return valor.get("estado")
        return "atendido" if valor else None
    return "atendido" if atencion else None


def entry_atendido_por(entry, username: str) -> bool:
    """Indica si `username` ya cerró (atendió por completo) esta fila de agenda."""
    return entry_estado_por(entry, username) == "atendido"


def obtener_nota_atencion(entry, username: str) -> str:
    """Devuelve el texto de atención registrado por `username` al cerrar la atención."""
    if len(entry) <= 8 or not isinstance(entry[8], dict):
        return ""
    valor = entry[8].get(username)
    return valor.get("nota", "") if isinstance(valor, dict) else ""


def obtener_hora_real_atencion(entry, username: str) -> str:
    """Devuelve la hora real (HH:mm:ss) en que `username` comenzó a atender esta fila."""
    if len(entry) <= 8 or not isinstance(entry[8], dict):
        return ""
    valor = entry[8].get(username)
    return valor.get("hora_real", "") if isinstance(valor, dict) else ""


def marcar_entry_atendiendo(entry, username: str, hora_real: str | None = None) -> None:
    """Marca la fila de agenda como en curso de atención por `username`."""
    atencion = _asegurar_dict_atencion(entry)
    nota_previa = obtener_nota_atencion(entry, username)
    hora_previa = obtener_hora_real_atencion(entry, username)
    atencion[username] = {
        "estado": "atendiendo",
        "nota": nota_previa,
        "hora_real": hora_previa or hora_real or datetime.now().strftime("%H:%M:%S"),
    }


def marcar_entry_atendido(entry, username: str, nota: str = "") -> None:
    """Cierra la atención de la fila de agenda por `username`, guardando la nota clínica."""
    atencion = _asegurar_dict_atencion(entry)
    hora_real = obtener_hora_real_atencion(entry, username)
    atencion[username] = {"estado": "atendido", "nota": nota, "hora_real": hora_real}


def marcar_entry_no_show(entry, username: str, nota: str = "") -> None:
    """Marca que, según `username`, el paciente no se presentó a la hora agendada."""
    atencion = _asegurar_dict_atencion(entry)
    atencion[username] = {"estado": "no_show", "nota": nota}


def entry_esta_cancelada(row) -> bool:
    """Indica si el admin canceló esta cita (estado global, no por-alumno)."""
    return len(row) > 10 and row[10] == "cancelada"


def marcar_entry_cancelada(row, cancelada: bool = True) -> None:
    """Cancela o restaura una cita, conservando el registro y el caso asociado."""
    _asegurar_dict_atencion(row)
    while len(row) <= 9:
        row.append("")
    while len(row) <= 10:
        row.append("")
    row[10] = "cancelada" if cancelada else ""


class Preferences:
    """
    Preferencias del programa
    __init__ : inicializa las preferencias
    get: recupera una preferencia
    set: modifica una preferencia
    get_all: recupera todas las preferencias
    get_all_keys: recupera todas las claves de las preferencias
    get_style: recupera el estilo de un widget
    """

    def __init__(self):
        preferences_file = context.get_resource('json/json_list.json')
        with codecs.open(preferences_file, 'r', 'utf-8') as json_file:
            list_data = json.load(json_file)
        self.data = {}
        for i in list_data:
            file = context.get_resource(f'json/{list_data[i]}')
            with codecs.open(file, 'r', 'utf-8') as json_file:
                data = json.load(json_file)
            self.data.update(data)

    def get(self, pref):
        """recupera las prefernecias desde un archivo *.json"""
        #print(self.data[pref])
        return self.data[pref]

    def set(self, pref, var):
        """modifica una configuración"""

    def get_all(self) -> dict:
        """
        devuelve todas las preferencias
        Returns:
            dict : diccionario de preferencias
        """
        return self.data

    def get_all_keys(self) -> list:
        """devuelve todas las claves de las preferencias

        Returns:
            list: claves de las preferencias
        """
        return list(self.data)

    def get_style(self, wid):
        """permite cambiar el estilo del widget"""
        #####ESTO NO DEBERIA ESTAR AQUI, hay que cambiarlo a un gui_helpers#####
        style_pred = self.data["styles"][0]
        style = self.data["styles"][1][style_pred]
        style = context.get_resource(f'styles/{style}.qss')
        with open(style,"r",encoding="utf8") as f_h:
            wid.setStyleSheet(f_h.read())

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
        file_po = context.get_resource(f'json/{lang}.json')
        with codecs.open(file_po, 'r', 'utf-8') as json_file:
            self.lng_po = json.load(json_file)

    def get(self, request):
        """obtiene la traducción del objeto"""
        try:
            get_str = self.lng_po[request]
            if len(get_str) > 1:
                result = self._list_to_string(get_str)
        except KeyError:
            result = request
        return result

    def _list_to_string(self, string:list) -> str:
        return "".join(string)


class Storage:
    """
    Storage
    Crea una lista en forma de almacenamiento
    _init_: inicializa el almacenamiento y llama a la funcion create
    create: crea una lista de longitud number_object
    clean: limpia el almacenamiento manteniendo la longitud
    get: recupera un elemento del almacenamiento
    """
    def __init__(self, number:int)->None:
        self.number_object = number
        self.data = []
        self.create(number)

    def length(self, ran= False) -> int:
        """
        Devuelve el largo o rango del almacenamiento
        Args:
            ran (bool, optional): si es True devuelve el rango, si no el largo.
            Defaults to False.

        Returns:
            int: largo o rango del almacenamiento
        """
        return range(len(self.data)) if ran else len(self.data)


    def create(self,number:int) -> None:
        """
        Crea los espacios de la memoria
        Args:
            n (int): numero de espacios a crear
        """
        for _ in range(number):
            self.data.append(None)

    def clean(self) -> None:
        """Limpia el almacenamiento y vstruelve a crear los espacion de la memoria"""
        self.data = []
        self.create(self.number_object)

    def get(self, idx:int) -> object:
        """
        Devuelve el objeto en la posición idx

        Args:
            idx (int): posición del objeto

        Returns:
            object: objeto guardado en la posición idx
        """
        return self.data[idx]

    def set(self, idx:int, dat:any) -> None:
        """
        Modifica un objeto almacenado en la posición idx
        Args:
            idx (int): posición del objeto
            dat (any): objeto a guardar en la posición idx
        """
        self.data[idx] = dat

    def list_set(self, dat:any, no_rework = True) -> None:
        ###CREO QUE ACA PUEDE HABER UN ERROR: quizas se debe hacer una copia de la lista original
        """setea todos los elementos de la lista

        Args:
            dat (any): elementos a guardar en el almacenamiento
            no_rework (bool, optional): _description_. Defaults to True.
        """
        if no_rework:
            if len(dat) == self.length():
                for idx in dat:
                    self.data[idx] = dat[idx]
        else:
            self.number_object = len(dat)
            self.clean()
            for idx in enumerate(dat):
                self.data[idx] = dat[idx]

    def agrege(self, idx:int, dat:any) -> None:
        """
        agrega un objeto en la lista de posición idx,
        si el objeto en la posición idx no es una lista la transforma
        en una y agrega el objeto

        Args:
            idx (_type_): posición del objeto en el Store
            dat (_type_): dato a almacenar en la lista
        """
        if isinstance(self.data[idx], list):
            self.data[idx].append(dat)
        else:
            self.data[idx] = [dat]


    def is_full(self, idx:int) -> bool:
        """
        Verifica si la posición idx esta llena

        Args:
            idx (int): posición del objeto en el Store

        Returns:
            bool: True si la posición esta llena, False si no
        """
        return self.data[idx] is not None

    def is_null(self, idx:int) -> bool:
        """regresa lo contrario a is_full

        Args:
            idx (int): posición del objeto en el Store

        Returns:
            bool: True si la posición esta vacia, False si no
        """
        return not self.is_full(idx)

    def is_empty(self) -> bool:
        """devuelve True si el almacenamiento esta vacio, False si no"""
        return any(i is None for i in self.data)

    def get_all(self) -> list:
        """
        Devuelve todos los objetos almacenados en el Store

        Returns:
            list: lista de objetos almacenados en el Store
        """
        return self.data
class CreatePatient():
    def __init__(self):
            pass
        
    def get_age_from_rut(self, rut):
        today_date = datetime.now()
        slope = 3.3363697569700348e-06
        intercept = 1932.2573852507373
        birth_date_float = rut * slope + intercept
        birth_date_year = int(birth_date_float)
        birth_date_month = round((birth_date_float - birth_date_year) * 12)
        birth_date = datetime(birth_date_year, birth_date_month, 1)
        age = (today_date - birth_date).days // 365
        return age, birth_date_month, birth_date_year

    def ear_volume(self, age, gender=0):
        """
        Volumen del canal auditivo (Vea) en cm3, según rango etario clínico
        (Katz, Handbook of Clinical Audiology). En adultos se aplica un
        rango levemente distinto por sexo (diferencia menor, tamaño de
        canal promedio algo mayor en hombres).
        gender: 0 = hombre, 1 = mujer (misma convención usada en create_a.py)
        """
        if age <= 5:
            low, high = 0.30, 0.90
        elif age <= 12:
            low, high = 0.40, 1.00
        elif age <= 17:
            low, high = 0.60, 1.30
        else:
            low, high = (0.9, 2.0) if gender == 0 else (0.8, 1.8)
        return round(random.uniform(low, high), 2)

    def rut_from_age(self, age):
        """
        Rut falso para el paciente sintético. Se agrega azar en el día de
        nacimiento dentro del año: si dos pacientes distintos tienen la misma
        edad y quedaran con el mismo rut, _historial_atenciones (Agenda.py)
        los trataría como el mismo paciente y mezclaría sus notas de atención.
        """
        today_date = datetime.now()
        slope = 3.3363697569700348e-06
        intercept = 1932.2573852507373
        birth_year = today_date.year - age
        dia_aleatorio = random.randint(0, 364)
        birth_date_float = birth_year + (dia_aleatorio / 365)
        rut_approx = (birth_date_float - intercept) / slope
        return int(rut_approx)

    def generar_nombre(self, gender: str, social_name: bool = False) -> str:
        class_pref = Preferences()

        lastname = class_pref.get("apellidos")
        
        if gender == "men":
            nombres = class_pref.get("nombres_hombres")
            nombres_sociales = class_pref.get("nombres_mujeres")
        else:
            nombres = class_pref.get("nombres_mujeres")
            nombres_sociales = class_pref.get("nombres_hombres")

        nombre1 = random.choice(nombres)
        nombre2 = random.choice([n for n in nombres if n != nombre1])
        apellido1 = random.choice(lastname)
        apellido2 = random.choice([a for a in lastname if a != apellido1])

        if social_name:
            social_name = random.choice(nombres_sociales)
        else:
            social_name = 0

        return [nombre1, nombre2, apellido1, apellido2, social_name]