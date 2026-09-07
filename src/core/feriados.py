"""
Feriados legales de Chile para pintarlos en el calendario de la agenda.

Fuente: https://feriados-cl.netlify.app/api/holidays/<año> (solo responde
para el año en curso en adelante: un año pasado devuelve 400).

Tres capas, de más a menos fresca, y ninguna puede voltear la app -- un
calendario sin feriados marcados es un detalle visual, no un error:

  1. resources/local_cache/feriados_<año>.json -- lo que ya se bajó alguna
     vez. Si existe se usa tal cual y NO se vuelve a pedir por red: la lista
     de un año no cambia (salvo ley nueva, ver refrescar()).
  2. la API, en un hilo aparte (ver FeriadosThread) para no congelar la
     ventana si netlify no responde.
  3. resources/json/feriados_backup.json -- copia versionada en el repo,
     para una instalación nueva sin red.

El formato normalizado es {"MM-DD": "descripción"} por año; el backup es
{"<año>": {...}} con esos mismos diccionarios adentro.
"""
import json
import os
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal

FERIADOS_URL = "https://feriados-cl.netlify.app/api/holidays/{year}"
FERIADOS_TIMEOUT = 5

_RESOURCES = Path(__file__).resolve().parents[2] / 'resources'
# Misma convención que core/app_layout.py: local_cache/ es data dinámica del
# usuario y el updater la preserva entre versiones.
CACHE_DIR = _RESOURCES / 'local_cache'
BACKUP_PATH = _RESOURCES / 'json' / 'feriados_backup.json'


def _cache_path(year: int) -> Path:
    return CACHE_DIR / f'feriados_{year}.json'


def _es_mapa_feriados(data) -> bool:
    return (isinstance(data, dict)
            and all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()))


def _parse_respuesta(data) -> dict:
    """{"feriados": {"enero": [{"mes": 1, "dia": 1, "descripcion": ...}]}}
    -> {"01-01": "Año Nuevo"}. Devuelve {} si el JSON no tiene esa forma."""
    feriados = data.get("feriados") if isinstance(data, dict) else None
    if not isinstance(feriados, dict):
        return {}

    mapa = {}
    for dias in feriados.values():
        if not isinstance(dias, list):
            continue
        for dia in dias:
            if not isinstance(dia, dict):
                continue
            try:
                mes, num = int(dia["mes"]), int(dia["dia"])
            except (KeyError, TypeError, ValueError):
                continue
            if not (1 <= mes <= 12 and 1 <= num <= 31):
                continue
            mapa[f"{mes:02d}-{num:02d}"] = str(dia.get("descripcion") or "Feriado")
    return mapa


def _leer_json(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def load_cache(year: int) -> dict | None:
    """Feriados del año ya guardados en disco, o None si no hay/está roto."""
    data = _leer_json(_cache_path(year))
    return data if _es_mapa_feriados(data) else None


def save_cache(year: int, mapa: dict) -> None:
    """Escritura atómica (tmp + replace): un json a medio escribir sería
    justo el que se lee en el próximo arranque sin red."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _cache_path(year).with_suffix('.json.tmp')
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(mapa, fh, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, _cache_path(year))
    except OSError:
        pass  # disco lleno / permisos: no es motivo para romper la agenda


def load_backup(year: int) -> dict:
    """Copia versionada en el repo. {} si no trae ese año."""
    data = _leer_json(BACKUP_PATH)
    if not isinstance(data, dict):
        return {}
    mapa = data.get(str(year))
    return mapa if _es_mapa_feriados(mapa) else {}


def fetch_from_network(year: int) -> dict:
    """Un intento contra la API. {} ante cualquier falla (red, 400 de un año
    pasado, JSON raro) -- nunca lanza. Si trae algo, refresca la cache."""
    try:
        resp = requests.get(FERIADOS_URL.format(year=year), timeout=FERIADOS_TIMEOUT)
    except requests.RequestException:
        return {}
    if resp.status_code >= 400:
        return {}
    try:
        mapa = _parse_respuesta(resp.json())
    except ValueError:
        return {}
    if mapa:
        save_cache(year, mapa)
    return mapa


def feriados_offline(year: int) -> dict:
    """Lo que se puede saber sin tocar la red: cache, o el backup del repo."""
    return load_cache(year) or load_backup(year)


def refrescar(year: int) -> dict:
    """Feriados del año pidiéndolos por red solo si no hay cache. Bloquea:
    llamar desde FeriadosThread, no desde el hilo de UI.

    Sin TTL a propósito: los feriados de un año ya bajado no cambian. Si
    algún año se agrega uno por ley, basta borrar resources/local_cache/
    feriados_<año>.json (o actualizar el backup del repo)."""
    cache = load_cache(year)
    if cache:
        return cache
    return fetch_from_network(year) or load_backup(year)


class FeriadosThread(QThread):
    """Trae los feriados de varios años fuera del hilo de UI (netlify caído
    congelaría la agenda hasta FERIADOS_TIMEOUT por año). Emite una sola vez
    con {año: {"MM-DD": descripción}}; si no consiguió nada, no emite."""

    listo = Signal(dict)

    def __init__(self, years, parent=None):
        super().__init__(parent)
        self._years = list(years)

    def run(self) -> None:
        resultado = {}
        for year in self._years:
            if self.isInterruptionRequested():
                return
            mapa = refrescar(year)
            if mapa:
                resultado[year] = mapa
        if resultado:
            self.listo.emit(resultado)
