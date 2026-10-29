"""Los cuadros de RinoSim para la ficha "Nariz" del editor de casos.

Lee `src/nasal/modelo.py` (la fuente de los números) y escribe un JSON que
el backend lee del disco, sin servirlo por HTTP: lo carga
`CaseBuilder::nasalCuadros()` para validar `nasal_json` en `CaseForm` y para
pasárselo al JS de la ficha como `window.CASE_CONST.nasalCuadros`.

Contenido:
  - `parametros`: los de cada lado (ruta, nombre, min, max, paso).
  - `extras`: ciclo nasal y perforación septal, que en RinoSim son filas
    aparte de la tabla (no tienen FND/FNI). Los pasos son los de
    `dibujaPaciente` (rinosim/js/app.js); los rangos, los de la validación.
  - `cuadros`: por cada uno, nombre, descripción, el paciente tipo
    (`semilla=None`) y 8 variantes (semillas 1 a 8) ya calculadas, para que
    "Otra variante" del editor no necesite Python.

Si cambia el modelo, se regenera:
    python3 scripts/nasal/cuadros_backend.py            # escribe el JSON
    python3 scripts/nasal/cuadros_backend.py --stdout   # lo imprime
"""

import json
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(RAIZ, 'src'))

from nasal import modelo  # noqa: E402

DESTINO = os.path.join(RAIZ, 'labsim_backend', 'resources', 'nasal', 'cuadros.json')
VARIANTES = 8

# Ciclo y perforación: ruta, nombre, mínimo, máximo, paso. La amplitud tiene
# techo (0,5: más que eso la congestión sale de 0-1); el periodo y la
# perforación solo piden no ser negativos, así que el máximo es un tope
# holgado para el input, no un límite del modelo.
EXTRAS = [
    {'ruta': 'ciclo.amplitud', 'nombre': 'Ciclo nasal: amplitud (0-0,5)', 'min': 0, 'max': 0.5, 'paso': 0.01},
    {'ruta': 'ciclo.periodo', 'nombre': 'Ciclo nasal: periodo (min)', 'min': 1, 'max': 600, 'paso': 5},
    {'ruta': 'perforacion.pos', 'nombre': 'Perforación septal: distancia (cm)', 'min': 0, 'max': 10, 'paso': 0.05},
    {'ruta': 'perforacion.area', 'nombre': 'Perforación septal: área (cm²; 0 = sin)', 'min': 0, 'max': 5, 'paso': 0.05},
]


def _ajusta(p):
    """Redondea a 4 decimales y recorta al rango de la ficha.

    Las variantes con semilla corren cada parámetro al azar y algunas pasan
    del máximo de la tabla (la mucosa del cornete hasta 2,4 con tope 2,2; los
    pólipos hasta 2,9 con tope 2,5). El modelo no tiene tope y no se toca;
    acá se recorta para que lo que el editor propone sea algo que él mismo
    acepta al guardar. El tipo (sin semilla) ya viene dentro del rango.
    """
    for lado in p['lados'].values():
        for d in modelo.PARAMETROS:
            v = min(max(round(modelo.lee(lado, d['ruta']), 4), d['min']), d['max'])
            modelo.escribe(lado, d['ruta'], v)
    for d in EXTRAS:
        v = min(max(round(modelo.lee(p, d['ruta']), 4), d['min']), d['max'])
        modelo.escribe(p, d['ruta'], v)
    return p


def exportable(p):
    """Lo que viaja en `cases.data['NASAL']` (mismo recorte que RinoSim)."""
    p = _ajusta(modelo.clona(p))
    return {
        'nombre': p['nombre'],
        'cuadro': p['cuadro'],
        'semilla': p['semilla'],
        'lados': p['lados'],
        'ciclo': p['ciclo'],
        'perforacion': p['perforacion'],
    }


def arma():
    cuadros = {}
    for clave, c in modelo.CUADROS.items():
        cuadros[clave] = {
            'nombre': c['nombre'],
            'descripcion': c['descripcion'],
            'tipo': exportable(modelo.paciente(clave, None)),
            'variantes': [exportable(modelo.paciente(clave, s)) for s in range(1, VARIANTES + 1)],
        }
    return {'parametros': modelo.PARAMETROS, 'extras': EXTRAS, 'cuadros': cuadros}


if __name__ == '__main__':
    texto = json.dumps(arma(), ensure_ascii=False, indent=1) + '\n'
    if '--stdout' in sys.argv:
        sys.stdout.write(texto)
    else:
        os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
        with open(DESTINO, 'w', encoding='utf-8') as f:
            f.write(texto)
        print(os.path.normpath(DESTINO))
