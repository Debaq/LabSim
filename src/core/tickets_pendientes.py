"""Tickets que no se pudieron enviar: quedan en el equipo y salen solos.

Nace del 2026-11-06: con el servidor perdiendo paquetes, el reporte que
más sirve (el del equipo que no conecta) es justo el que no sale. Ahora se
guarda en la carpeta de datos (core/rutas.py, tickets_pendientes/) y se
reintenta al arrancar la app y al iniciar sesión (ver main.py), con la
sesión si la hay y si no sin ella (ticket.php acepta sin sesión los de
cierre inesperado y los de la ventana de ingreso, con tope por equipo).

Sin Qt: corre en hilos.en_fondo.
"""
import json
import threading
import uuid
from datetime import datetime

import requests

from core import rutas

# Más que esto y se botan los más viejos: un equipo sin red por semanas no
# tiene por qué juntar cientos.
MAX_PENDIENTES = 20

_enviando = threading.Lock()


def _carpeta():
    return rutas.carpeta("tickets_pendientes")


def mandar(client, descripcion, equipo_info, detalle, log_gz, cierre_inesperado=False):
    """Manda un ticket: con la sesión si hay una y sigue valiendo; si no,
    sin sesión (marcado como cierre inesperado o como enviado sin sesión)."""
    args = (descripcion, equipo_info, detalle, log_gz)
    if client.is_logged_in():
        try:
            if cierre_inesperado:
                return client.send_ticket(*args, cierre_inesperado=True)
            return client.send_ticket(*args)
        except requests.HTTPError as exc:
            if getattr(exc.response, "status_code", None) != 401:
                raise
    if cierre_inesperado:
        return client.send_ticket(*args, cierre_inesperado=True, anonimo=True)
    return client.send_ticket(*args, anonimo=True, sin_sesion=True)


def se_puede_guardar(exc) -> bool:
    """¿Vale la pena guardarlo para después? No, si el servidor lo rechazó
    por cómo viene (400, 413): repetirlo daría lo mismo."""
    if isinstance(exc, requests.HTTPError):
        return getattr(exc.response, "status_code", None) not in (400, 413)
    return isinstance(exc, (requests.RequestException, RuntimeError, OSError))


def guardar(descripcion, equipo_info, detalle, log_gz, cierre_inesperado=False):
    carpeta = _carpeta()
    nombre = f"{datetime.now():%Y%m%d-%H%M%S-%f}-{uuid.uuid4().hex[:4]}"
    meta = {"descripcion": descripcion, "equipo": equipo_info or {}, "detalle": detalle or {},
            "cierre_inesperado": bool(cierre_inesperado),
            "guardado": datetime.now().strftime("%Y-%m-%d %H:%M")}
    if log_gz:
        (carpeta / f"{nombre}.log.gz").write_bytes(log_gz)
    (carpeta / f"{nombre}.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    sobran = pendientes()[:-MAX_PENDIENTES]
    for viejo in sobran:
        _borrar(viejo)
    print(f"tickets: guardado para enviar después ({nombre})")
    return nombre


def pendientes():
    """Los .json guardados, del más viejo al más nuevo."""
    return sorted(_carpeta().glob("*.json"))


def _log_de(ruta_json):
    return ruta_json.parent / f"{ruta_json.stem}.log.gz"


def _borrar(ruta_json):
    ruta_json.unlink(missing_ok=True)
    _log_de(ruta_json).unlink(missing_ok=True)


def enviar(client=None):
    """Manda los guardados, del más viejo al más nuevo. Para al primer error
    de red (el resto saldría igual de mal). Devuelve los números de ticket.
    Si ya hay un envío en curso, no hace nada."""
    if not _enviando.acquire(blocking=False):
        return []
    try:
        lista = pendientes()
        if not lista:
            return []
        if client is None:
            from backend.client import BackendClient
            from core.base import context
            from core.helpers import Preferences
            client = BackendClient(Preferences().get("BACKEND_URL"),
                                   context.get_resource("json/session.json"))
        enviados = []
        for ruta in lista:
            try:
                meta = json.loads(ruta.read_text("utf-8"))
            except (OSError, ValueError):
                _borrar(ruta)
                continue
            log = _log_de(ruta)
            detalle = dict(meta.get("detalle") or {}, enviado_tarde=f"guardado el {meta.get('guardado', '?')}")
            try:
                respuesta = mandar(client, meta.get("descripcion", ""), meta.get("equipo"), detalle,
                                   log.read_bytes() if log.exists() else None,
                                   cierre_inesperado=meta.get("cierre_inesperado", False))
            except Exception as exc:  # noqa: BLE001 -- se anota y se sigue otro día
                print(f"tickets: no se pudo enviar {ruta.stem}: {exc}")
                if not se_puede_guardar(exc):
                    _borrar(ruta)
                    continue
                break
            _borrar(ruta)
            enviados.append(respuesta.get("id"))
            print(f"tickets: enviado {ruta.stem} como ticket #{respuesta.get('id')}")
        return enviados
    finally:
        _enviando.release()
