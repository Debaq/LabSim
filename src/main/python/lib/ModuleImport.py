import json
import importlib
import sys
from lib.ContextManager import AppContextManager

# Función para importar un módulo por su nombre
def importar_modulo(nombre):
    appctxt = AppContextManager.get_context()
    # Obtener la ruta del recurso donde se encuentran tus módulos
    ruta_modulos = appctxt.get_resource('modules/')

    # Agregar la ruta al sys.path si aún no está incluida
    if ruta_modulos not in sys.path:
        sys.path.append(ruta_modulos)

    try:
        modulo = importlib.import_module(nombre)
        print(f"¡Módulo {nombre} importado con éxito!")
        return modulo
    except ImportError:
        print(f"Error al importar el módulo {nombre}")
        return None
    
def importar_ui(nombre):
    appctxt = AppContextManager.get_context()
    nombre = f"ui/{nombre}.ui"
    try:
        return appctxt.get_resource(nombre)
    except FileNotFoundError:
        return None

def main():
    # Leer el archivo JSON para obtener la lista de módulos
    with open('config.json', 'r') as file:
        data = json.load(file)
        plugins = data.get('plugins', [])

    # Añadir la ruta de los plugins al path
    sys.path.append('./plugins')

    # Importar módulos según lo especificado en config.json
    modulos_cargados = {plugin: importar_modulo(plugin) for plugin in plugins}

    # Aquí puedes usar modulos_cargados para acceder a los módulos que has importado

if __name__ == "__main__":
    main()
