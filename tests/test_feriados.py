"""
Feriados del calendario de la agenda (core/feriados.py).

Lo que importa acá no es el color: es que NINGÚN camino pueda voltear la
agenda. La API (feriados-cl.netlify.app) responde 400 para años pasados y
puede estar caída, así que se prueban las tres capas -- cache, red, backup
del repo -- y que un fallo devuelva {} en vez de lanzar.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import requests

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core import feriados


RESPUESTA_API = {
    "year": 2026,
    "feriados": {
        "enero": [{"mes": 1, "dia": 1, "descripcion": "Año Nuevo", "tipo": "civil"}],
        "septiembre": [
            {"mes": 9, "dia": 18, "descripcion": "Independencia Nacional"},
            {"mes": 9, "dia": 19, "descripcion": "Día de las Glorias del Ejército"},
        ],
    },
}


class _Resp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


_CACHE_DIR_REAL = feriados.CACHE_DIR
_BACKUP_PATH_REAL = feriados.BACKUP_PATH


def _aislar(tmp, backup=None):
    """Apunta cache y backup a un directorio temporal. Devuelve el
    restaurador -- si un test dejara los paths pisados, el siguiente estaría
    leyendo/escribiendo el repo de verdad."""
    feriados.CACHE_DIR = Path(tmp) / "local_cache"
    feriados.BACKUP_PATH = Path(tmp) / "feriados_backup.json"
    if backup is not None:
        feriados.BACKUP_PATH.write_text(json.dumps(backup), encoding="utf-8")

    def _restaurar():
        feriados.CACHE_DIR = _CACHE_DIR_REAL
        feriados.BACKUP_PATH = _BACKUP_PATH_REAL

    return _restaurar


def _con_get(fn):
    """requests.get parcheado; devuelve un restaurador."""
    original = requests.get
    requests.get = fn
    return lambda: setattr(requests, "get", original)


def test_parse_de_la_respuesta_real():
    mapa = feriados._parse_respuesta(RESPUESTA_API)
    assert mapa == {
        "01-01": "Año Nuevo",
        "09-18": "Independencia Nacional",
        "09-19": "Día de las Glorias del Ejército",
    }


def test_backup_del_repo_cubre_el_anio_en_curso():
    """El archivo versionado tiene que servir en una instalación sin red."""
    assert len(feriados.load_backup(2026)) >= 15


def test_la_red_se_consulta_una_sola_vez_y_queda_en_cache():
    with tempfile.TemporaryDirectory() as tmp:
        restaurar_paths = _aislar(tmp)
        llamadas = []

        def _get(url, timeout=None):
            llamadas.append(url)
            return _Resp(RESPUESTA_API)

        restaurar = _con_get(_get)
        try:
            assert feriados.refrescar(2026)["09-18"] == "Independencia Nacional"
            # Segunda vuelta: ya hay cache, no se vuelve a pedir.
            assert feriados.refrescar(2026)["01-01"] == "Año Nuevo"
            assert len(llamadas) == 1
            assert feriados.load_cache(2026) is not None
        finally:
            restaurar()
            restaurar_paths()


def test_sin_red_cae_al_backup_versionado():
    with tempfile.TemporaryDirectory() as tmp:
        restaurar_paths = _aislar(tmp, backup={"2026": {"01-01": "Año Nuevo"}})

        def _get(url, timeout=None):
            raise requests.ConnectionError("sin red")

        restaurar = _con_get(_get)
        try:
            assert feriados.refrescar(2026) == {"01-01": "Año Nuevo"}
        finally:
            restaurar()
            restaurar_paths()


def test_ningun_fallo_lanza():
    """400 (año pasado), JSON roto y respuesta con forma inesperada."""
    with tempfile.TemporaryDirectory() as tmp:
        restaurar_paths = _aislar(tmp)
        casos = [
            _Resp({}, status=400),
            _Resp(ValueError("no es json")),
            _Resp({"feriados": "chao"}),
            _Resp({"feriados": {"enero": [{"mes": 13, "dia": 99}]}}),
        ]
        for resp in casos:
            restaurar = _con_get(lambda url, timeout=None, _r=resp: _r)
            try:
                assert feriados.refrescar(2020) == {}
            finally:
                restaurar()
        assert feriados.load_cache(2020) is None
        restaurar_paths()
