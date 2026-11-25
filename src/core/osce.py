"""Estación OSCE: el PC rinde una estación del OSCE (paso 4 de docs/osce_plan.md).

Se entra desde la ventana de ingreso ("Estación OSCE") con el código corto de
la estación que muestra el panel (admin/osce_estacion.php). No hay cuenta: se
entra como el invitado (sin la API normal, ver core/invitado.py) y solo se
habla con api/osce_app.php y api/osce_reloj.php, que no piden sesión. Cada
alumno escribe su código; el servidor decide si le toca (reloj) y manda el
caso; al entregar se sube la sesión del ABR (AbrMainWindow.osce_entrega).

Una entrega que no sale (sin red) queda en el equipo (carpeta de datos,
osce/) y se reintenta sola: lo hecho por un alumno no se pierde aunque el
servidor esté caído al sonar el timbre.

Todo lo de red corre fuera del hilo de la ventana (core.hilos.en_fondo).
"""
import json
import time
from pathlib import Path

import requests

from core import rutas

RUTA_API = "/api/osce_app.php"
RUTA_RELOJ = "/api/osce_reloj.php"
TIMEOUT = (5, 30)

activo = False
estacion = None        # lo que respondió "estacion": titulo, tipo, osce, reloj, codigo


class ErrorOsce(Exception):
    """El servidor respondió con un motivo legible (código malo, no le toca...)."""


def _base_url():
    from core.helpers import Preferences
    return (Preferences().get("BACKEND_URL") or "").rstrip("/")


def _post(datos):
    try:
        resp = requests.post(_base_url() + RUTA_API, json=datos, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise ConnectionError(f"sin conexión con el servidor ({type(exc).__name__})") from exc
    try:
        cuerpo = resp.json()
    except ValueError:
        cuerpo = {}
    if resp.status_code >= 400 or not cuerpo.get("ok"):
        if resp.status_code >= 500 or not cuerpo.get("error"):
            raise ConnectionError(f"el servidor respondió {resp.status_code}")
        raise ErrorOsce(cuerpo["error"])
    return cuerpo


def normalizar(codigo):
    """'k7f 3qm' -> 'K7F-3QM' (como Osce::normalizarCodigo). El número de la
    tarjeta ('7', ' 07 ') queda en cifras: el servidor acepta los dos."""
    texto = str(codigo).strip()
    if texto.isdigit():
        return str(int(texto))
    limpio = "".join(ch for ch in texto.upper() if ch.isalnum())
    return f"{limpio[:3]}-{limpio[3:]}" if len(limpio) == 6 else limpio


def consultar_estacion(codigo):
    """La estación de ese código (para entrar como estación)."""
    codigo = normalizar(codigo)
    datos = _post({"accion": "estacion", "estacion": codigo})
    datos["codigo"] = codigo
    return datos


def entrar(codigo_alumno):
    """El caso y lo que hay que preparar para este alumno, si le toca."""
    return _post({"accion": "entrar", "estacion": estacion["codigo"], "codigo": normalizar(codigo_alumno)})


def entregar(codigo_alumno, entrega):
    return _post({"accion": "entregar", "estacion": estacion["codigo"],
                  "codigo": normalizar(codigo_alumno), "entrega": entrega})


def corregir(codigo_alumno):
    """Pide al servidor que corrija con IA la conclusión entregada (no se
    espera: la app ya pasó al alumno siguiente)."""
    return _post({"accion": "corregir", "estacion": estacion["codigo"], "codigo": normalizar(codigo_alumno)})


def reloj():
    """Estado del reloj del OSCE (api/osce_reloj.php) y cuándo se pidió."""
    try:
        resp = requests.get(_base_url() + RUTA_RELOJ, params={"r": estacion["reloj"]}, timeout=TIMEOUT)
        datos = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise ConnectionError(str(exc)) from exc
    if resp.status_code >= 400:
        raise ConnectionError(datos.get("error") or str(resp.status_code))
    datos["_pedido"] = time.monotonic()
    return datos


def transcurrido(datos_reloj):
    """Segundos de reloj del OSCE ahora, con lo último que dijo el servidor."""
    if not datos_reloj or datos_reloj.get("transcurrido_s") is None:
        return None
    base = float(datos_reloj["transcurrido_s"])
    if datos_reloj.get("pausado") or datos_reloj.get("estado") != "en_curso":
        return base
    return base + (time.monotonic() - datos_reloj["_pedido"])


def activar(info):
    global activo, estacion
    activo = True
    estacion = dict(info)


def desactivar():
    global activo, estacion
    activo = False
    estacion = None


def datos_login(info):
    """Lo que la ventana de ingreso entrega a main._data_login: como el
    invitado (sin API normal) y con solo el ABR."""
    return {"user": "osce", "name": f"Estación OSCE · {info.get('titulo', '')}", "permission": 444,
            "modules": [info.get("modulo") or "ABR"], "prefs": {}, "cases": {}, "invitado": True,
            "osce": info}


# -- Entregas que no alcanzaron a salir ------------------------------------------

def _carpeta() -> Path:
    return rutas.carpeta("osce")


def _archivo(estacion_codigo, alumno):
    return _carpeta() / f"pendiente_{estacion_codigo}_{normalizar(alumno)}.json"


def guardar_pendiente(alumno, entrega):
    """Antes de mandar: si no sale, queda acá."""
    ruta = _archivo(estacion["codigo"], alumno)
    ruta.write_text(json.dumps({"estacion": estacion["codigo"], "alumno": normalizar(alumno),
                                "entrega": entrega}), encoding="utf-8")
    return ruta


def borrar_pendiente(alumno, estacion_codigo=None):
    try:
        _archivo(estacion_codigo or estacion["codigo"], alumno).unlink()
    except FileNotFoundError:
        pass


def pendientes():
    """Entregas guardadas en el equipo que todavía no llegan al servidor."""
    out = []
    for ruta in sorted(_carpeta().glob("pendiente_*.json")):
        try:
            out.append(json.loads(ruta.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def enviar_pendientes():
    """Reintenta las guardadas (en un hilo de fondo). Devuelve cuántas salieron.
    Las que el servidor rechaza con motivo (ya entregada, OSCE publicado) se
    descartan: reintentarlas no cambia nada."""
    enviadas = 0
    for p in pendientes():
        try:
            _post({"accion": "entregar", "estacion": p["estacion"], "codigo": p["alumno"],
                   "entrega": p["entrega"]})
        except ErrorOsce:
            pass
        except ConnectionError:
            continue
        borrar_pendiente(p["alumno"], p["estacion"])
        enviadas += 1
    return enviadas
