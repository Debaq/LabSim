"""
Layout de la app (módulos / sectores / boxes) pedido al backend al
arrancar. Antes vivía en resources/json/apps.json; ahora viene por
GET /api/layout.php.

El layout casi nunca cambia (es la lista de módulos y su geometría), así
que no tiene sentido que una caída de red deje la app inservible: cada
respuesta buena se guarda en resources/local_cache/layout.json y, si el
backend no responde, se abre con esa copia. La app queda operativa en
modo offline en vez de mostrar solo el login.

Solo cuando no hay red NI cache (instalación nueva que nunca llegó a
conectarse) se devuelve None y el caller muestra el aviso duro.

`last_source` dice de dónde salió el layout devuelto ('network' | 'cache'
| None) y `last_error` el detalle del fallo de red, si lo hubo.
"""
import json
import os
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal

# Primer intento corto: si hay cache preferimos abrir ya y reintentar en
# background. Sin cache no hay alternativa, así que damos un segundo
# intento más largo antes de rendirnos.
LAYOUT_TIMEOUT = 3
LAYOUT_TIMEOUT_RETRY = 8

# Misma convención que backend/log_queue.py: resources/local_cache/ es la
# data dinámica del usuario, y updater.apply_update_and_restart() la
# preserva al actualizar (no la pisa con la del release).
CACHE_PATH = Path(__file__).resolve().parents[2] / 'resources' / 'local_cache' / 'layout.json'

last_error: "LayoutFetchError | None" = None
last_source: "str | None" = None


class LayoutFetchError(Exception):
    """Detalle del fallo al pedir /api/layout.php para mostrar al usuario."""
    def __init__(self, phase: str, detail: str):
        super().__init__(f"{phase}: {detail}")
        self.phase = phase   # "conexión", "timeout", "http", "json", "estructura"
        self.detail = detail


def _is_layout(data) -> bool:
    return isinstance(data, dict) and "APP" in data and "BOXS" in data


def load_cache() -> dict | None:
    """Último layout bueno guardado en disco. None si no hay o está roto."""
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if _is_layout(data) else None


def save_cache(data: dict) -> None:
    """Guarda el layout de forma atómica (tmp + replace) para no dejar un
    json a medio escribir si la app muere en el medio -- ese archivo
    corrupto sería justo el que se lee en el próximo arranque sin red."""
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_PATH.with_suffix('.json.tmp')
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False)
        os.replace(tmp, CACHE_PATH)
    except OSError:
        # Disco lleno / permisos: no es motivo para no abrir la app.
        pass


def _request(url: str, timeout: int) -> dict:
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.ConnectionError as exc:
        raise LayoutFetchError("conexión", str(exc)) from exc
    except requests.Timeout:
        raise LayoutFetchError("timeout", f"sin respuesta en {timeout}s")
    except requests.RequestException as exc:
        raise LayoutFetchError("red", str(exc)) from exc
    if resp.status_code >= 400:
        raise LayoutFetchError("http", f"{resp.status_code} {resp.reason}")
    try:
        data = resp.json()
    except ValueError:
        raise LayoutFetchError("json", "respuesta no es JSON válido")
    if not _is_layout(data):
        raise LayoutFetchError("estructura", "falta APP o BOXS en la respuesta")
    return data


def fetch_from_network(backend_url: str, timeout: int = LAYOUT_TIMEOUT) -> dict:
    """Un solo intento contra el backend. Lanza LayoutFetchError si falla.
    Si funciona, refresca la cache. Lo usa también el reintento en
    background (LayoutRetryThread)."""
    if not backend_url:
        raise LayoutFetchError("config", "BACKEND_URL vacío")
    data = _request(backend_url.rstrip("/") + "/api/layout.php", timeout)
    save_cache(data)
    return data


def fetch_layout(backend_url: str) -> dict | None:
    """Trae {APP, SECTORS, BOXS}: del backend si responde, si no de la
    cache local. None solo si no hay ninguna de las dos.

    Deja `last_error` (detalle del fallo de red) y `last_source`
    ('network' | 'cache' | None) para que el caller decida qué avisar."""
    global last_error, last_source
    last_error = None
    last_source = None

    cached = load_cache()
    # Con cache no hacemos esperar al usuario más de un intento corto: el
    # reintento sigue en background una vez abierta la ventana.
    timeouts = (LAYOUT_TIMEOUT,) if cached else (LAYOUT_TIMEOUT, LAYOUT_TIMEOUT_RETRY)
    for timeout in timeouts:
        try:
            data = fetch_from_network(backend_url, timeout)
        except LayoutFetchError as exc:
            last_error = exc
            continue
        last_source = "network"
        return data

    if cached:
        last_source = "cache"
        return cached
    return None


class LayoutRetryThread(QThread):
    """Reintenta el layout cada `interval` segundos mientras la app corre
    en modo offline (abierta con cache, o sin layout). Emite `recovered`
    con el layout fresco la primera vez que el backend responde; el caller
    decide si basta con sacar el aviso o hay que reiniciar (cuando el
    layout nuevo no coincide con el que se está usando)."""

    recovered = Signal(dict)

    def __init__(self, backend_url: str, interval: int = 60, parent=None):
        super().__init__(parent)
        self._backend_url = backend_url
        self._interval = interval
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        while not self._stop:
            # Espera troceada para poder cortar rápido al cerrar la app.
            for _ in range(self._interval):
                if self._stop:
                    return
                self.msleep(1000)
            if self._stop:
                return
            try:
                data = fetch_from_network(self._backend_url, LAYOUT_TIMEOUT_RETRY)
            except LayoutFetchError:
                continue
            self.recovered.emit(data)
            return
