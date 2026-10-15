"""De dónde sale cada caso del libro y cómo se fija el azar.

El caso es siempre un `cases.data` como el que usa la app: así las figuras
salen de los mismos datos y generadores que ve el alumno.
"""
import hashlib
import json
import pathlib
import random
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[4]          # raíz del repo
SRC = RAIZ / 'src'
CASOS_DEMO = RAIZ / 'docs' / 'manual' / 'capturas' / 'casos_demo.json'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def semilla(*partes):
    """Semilla estable entre procesos (hash() no lo es: ver stable_seed de la app)."""
    h = hashlib.blake2b('|'.join(map(str, partes)).encode(), digest_size=8)
    return int.from_bytes(h.digest(), 'big') % (2 ** 32)


def fijar_azar(*partes):
    """Fija random y numpy antes de cada figura: misma semilla, misma figura."""
    s = semilla(*partes)
    random.seed(s)
    try:
        import numpy as np
        np.random.seed(s)
    except ImportError:
        pass
    return s


def cargar_caso(origen):
    """`demo:39` -> paciente de práctica 39. Devuelve el cases.data."""
    tipo, _, clave = str(origen).partition(':')
    if tipo == 'demo':
        todos = json.loads(CASOS_DEMO.read_text(encoding='utf-8'))
        if clave not in todos:
            raise KeyError(f'No hay paciente demo {clave!r} en {CASOS_DEMO.name}')
        caso = todos[clave]
        return dict(caso.get('data', caso))
    if tipo == 'cuadro':
        raise NotImplementedError(
            'Generar un caso desde un cuadro con semilla todavía no existe fuera del navegador '
            '(public/js/case/generator.js). Usar un paciente demo o un JSON de caso completo.')
    if tipo == 'archivo':
        ruta = (RAIZ / clave) if not pathlib.Path(clave).is_absolute() else pathlib.Path(clave)
        caso = json.loads(ruta.read_text(encoding='utf-8'))
        return dict(caso.get('data', caso))
    raise ValueError(f'Origen de caso desconocido: {origen!r} (demo:N, archivo:ruta)')


def por_oido(pares):
    """[[od, oi], ...] -> {'OD': [...], 'OI': [...]}, como lo guarda cases.data."""
    return {'OD': [p[0] for p in pares], 'OI': [p[1] for p in pares]}


class en_raiz:
    """La app abre resources/ con rutas relativas a la raíz del repo."""

    def __enter__(self):
        import os
        self.antes = os.getcwd()
        os.chdir(RAIZ)

    def __exit__(self, *exc):
        import os
        os.chdir(self.antes)
