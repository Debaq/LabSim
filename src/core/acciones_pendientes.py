"""Abrir y cerrar atenciones sin red: la cola de lo que falta avisar.

Parte 2 y 3 de docs/roadmap_sin_servidor.md ("Servidor lento o
intermitente", 2026-11-06). Abrir una atención ya no espera al servidor:
marcar "atendiendo" queda acá. Cerrarla sin red tampoco: la atención se
cierra en el equipo y "atendido" queda acá. Se envía sola cuando hay red
(al encolar, con cada sync y al iniciar sesión, ver main.py), en orden.

Reglas:

- Un "atendido" sube ANTES los informes de esa cita que quedaron en el
  equipo (core/respaldo_informes.py): con la atención cerrada el servidor
  ya no los acepta (report_upload.php responde 409).
- Cada acción guarda el token de quien la hizo. En los equipos del
  laboratorio otro alumno puede entrar antes de que vuelva la red: lo
  pendiente del anterior sale igual, con su token y no con el del que está
  ahora. Ese pedido va marcado "ajeno" (BackendClient.ajeno) para que un
  401 suyo no saque de la sesión al que está trabajando. Si el token del
  anterior ya venció, espera a que ese alumno vuelva a entrar.
- La agenda del equipo muestra lo encolado como si ya hubiera llegado
  (ultimas(), ver helpers.Shedule y aplicar_delta): si no, la cita
  cerrada sin red volvía a aparecer "atendiendo" con el siguiente sync.

Sin Qt: corre en hilos.en_fondo.
"""
import json
import re
import threading
from datetime import datetime

import requests

from core import rutas

_archivo_lock = threading.Lock()
_enviando = threading.Lock()


def _carpeta():
    return rutas.carpeta("acciones_pendientes")


def _clave(user) -> str:
    valor = str((user or {}).get("id") or (user or {}).get("username") or "")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", valor)


def _ruta(clave):
    return _carpeta() / f"{clave}.json"


def _leer(clave) -> list:
    try:
        return json.loads(_ruta(clave).read_text("utf-8"))
    except (OSError, ValueError):
        return []


def _escribir(clave, lista) -> None:
    ruta = _ruta(clave)
    if not lista:
        ruta.unlink(missing_ok=True)
        return
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(lista, ensure_ascii=False), "utf-8")
    tmp.replace(ruta)


def encolar(client, appointment_id, accion, nota="") -> None:
    """Agrega una acción de `client` (su usuario y su token) a la cola."""
    user = dict(client.user or {})
    clave = _clave(user)
    if not clave:
        raise RuntimeError("no hay sesión: no hay a nombre de quién guardar la acción")
    with _archivo_lock:
        lista = _leer(clave)
        lista.append({"appointment_id": int(appointment_id), "accion": accion, "nota": nota or "",
                      "cuando": datetime.now().isoformat(timespec="seconds"),
                      "token": client.token, "user": user})
        _escribir(clave, lista)
    print(f"atención: {accion} de la cita {appointment_id} en cola")


def ultimas(user) -> dict:
    """{appointment_id (str): la última acción encolada} del usuario."""
    return {str(a["appointment_id"]): a for a in _leer(_clave(user))}


def hay_pendientes(user=None) -> bool:
    if user is not None:
        return bool(_leer(_clave(user)))
    return any(_carpeta().glob("*.json"))


def es_de_red(exc) -> bool:
    """Un error que se arregla solo cuando vuelve la red (o el servidor)."""
    if isinstance(exc, requests.HTTPError):
        return (getattr(exc.response, "status_code", 0) or 0) >= 500
    return isinstance(exc, (requests.ConnectionError, requests.Timeout))


def subir_informes_de(client, appointment_id) -> list:
    """Sube lo que quedó en el equipo de esa cita. Lanza si es la red;
    devuelve lo que el servidor rechazó por otra cosa (tipo: motivo). Una
    atención ya cerrada (409) no cuenta: no hay nada más que hacer."""
    from core import report_autosave, respaldo_informes
    usuario = respaldo_informes.usuario_de(client)
    rechazados = []
    for registro in respaldo_informes.pendientes(usuario, appointment_id):
        job = {"appointment_id": registro["appointment_id"], "tipo": registro["tipo"],
               "data": registro["data"],
               "images_listas": respaldo_informes.imagenes(usuario, registro["appointment_id"],
                                                           registro["tipo"])}
        try:
            report_autosave.subir(job, client)
        except Exception as exc:  # noqa: BLE001 -- se clasifica
            if es_de_red(exc):
                raise
            if getattr(getattr(exc, "response", None), "status_code", None) != 409:
                rechazados.append(f"{registro['tipo']}: {str(exc)[:150]}")
    return rechazados


def _cliente_para(item, actual):
    """El cliente con que se envía `item`: el de la sesión actual si es del
    mismo usuario; si no, uno con el token guardado, marcado ajeno."""
    if actual is not None and _clave(actual.user) == _clave(item.get("user")) and actual.is_logged_in():
        return actual
    if not item.get("token"):
        return None
    from backend.client import BackendClient
    from core.base import context
    from core.helpers import Preferences
    cliente = BackendClient(Preferences().get("BACKEND_URL"),
                            context.get_resource("json/acciones_pendientes_sin_archivo.json"))
    cliente.token = item["token"]
    cliente.user = item.get("user")
    cliente.ajeno = True
    return cliente


def vaciar(actual=None) -> int:
    """Envía todo lo encolado, de todos los usuarios del equipo, en orden.
    Por usuario, para en el primer error de red. Devuelve cuántas
    acciones quedan. Si ya hay un envío en curso, no hace nada (-1)."""
    if not _enviando.acquire(blocking=False):
        return -1
    try:
        quedan = 0
        for archivo in sorted(_carpeta().glob("*.json")):
            quedan += _vaciar_usuario(archivo.stem, actual)
        return quedan
    finally:
        _enviando.release()


def _vaciar_usuario(clave, actual) -> int:
    with _archivo_lock:
        lista = _leer(clave)
    hechas = 0
    for item in lista:
        cliente = _cliente_para(item, actual)
        if cliente is None:
            break
        cita = item["appointment_id"]
        try:
            if item["accion"] == "atendido":
                rechazados = subir_informes_de(cliente, cita)
                if rechazados:
                    print(f"atención: informes de la cita {cita} rechazados al cerrar: {rechazados}")
            cliente.post_attendance_action(cita, item["accion"], nota=item.get("nota") or None)
        except Exception as exc:  # noqa: BLE001 -- se decide si esperar o botar
            estado = getattr(getattr(exc, "response", None), "status_code", None)
            if es_de_red(exc) or estado == 401 or not isinstance(exc, requests.RequestException):
                # Red, servidor caído o token vencido: se espera
                print(f"atención: {item['accion']} de la cita {cita} sigue en cola: {exc}")
                break
            # El servidor la rechazó (cita borrada, sin nota...): no va a
            # pasar nunca, se bota para no trabar las que siguen.
            print(f"atención: {item['accion']} de la cita {cita} rechazado ({estado}), se descarta: {exc}")
        else:
            print(f"atención: {item['accion']} de la cita {cita} enviado")
        hechas += 1
    with _archivo_lock:
        # Lo que se encoló mientras tanto queda al final
        restantes = _leer(clave)[hechas:]
        _escribir(clave, restantes)
    return len(restantes)
