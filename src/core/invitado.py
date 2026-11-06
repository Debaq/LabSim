"""Modo invitado: practicar con los pacientes del libro sin cuenta.

Se entra desde la ventana de ingreso ("Practicar sin cuenta"). No hay token
ni se puede usar la API: los pacientes salen del catálogo que trae la app
(resources/libro/catalogo.json.gz, scripts/libro/catalogo_app.py), se atiende
como en la prueba del docente (no se escribe nada en ningún lado), no hay
chat y la ficha muestra lo que el paciente contaría y los informes que trae
desde el principio. Ver docs/roadmap_practica_libro.md, F3.
"""
import gzip
import json

from backend.shedule_sync import AgendaEntry
from core import rutas

USUARIO = "invitado"
# Lo que ve el invitado: los equipos, la agenda (solo práctica libre), la
# ficha y la evolución. Sin chat, bandeja ni "Mis pacientes": viven en el
# backend.
MODULOS = ["A", "W", "Z", "ABR", "AABR", "VEMP", "EOAS", "CVOICE", "AGENDA", "AC", "OT",
           "FICHA", "EVOLUCION"]

activo = False
_catalogo = None


def activar():
    """Entra el invitado: nada de API ni de la sesión que haya en el equipo."""
    global activo
    from backend import client
    from core import app_config_store, helpers
    activo = True
    client.sin_api = True
    helpers.reset_backend_session()
    # La config del curso del último que entró no es suya (normativa, avisos)
    app_config_store.reset()


def desactivar():
    global activo
    from backend import client
    from core import app_config_store, helpers
    activo = False
    client.sin_api = False
    helpers.reset_backend_session()
    app_config_store.reset()


def foto_otoscopia(case_id, lado, fase=0):
    """La foto de otoscopía del libro (resources/libro/otoscopias), o None."""
    ruta = rutas.recursos() / "libro" / "otoscopias" / f"{case_id}_{lado}.jpg"
    try:
        return ruta.read_bytes() if fase == 0 else None
    except OSError:
        return None


def datos_login():
    """Lo que la ventana de ingreso entrega a main._data_login."""
    return {"user": USUARIO, "name": "Invitado", "permission": 444, "modules": list(MODULOS),
            "prefs": {}, "cases": {}, "invitado": True}


# La copia que baja la app del servidor (descargar_catalogo): más nueva que
# la que viene con la versión, que solo cambia al publicar una. Es lo que
# queda para practicar si el servidor se cae (2026-11-06).
DESCARGADO = "catalogo_practica.json.gz"


def _leer_catalogo(ruta):
    try:
        cat = json.loads(gzip.decompress(ruta.read_bytes()))
    except (OSError, ValueError):
        return None
    return cat if isinstance(cat, dict) and cat.get("items") and cat.get("casos") else None


def catalogo():
    global _catalogo
    if _catalogo is None:
        _catalogo = (_leer_catalogo(rutas.datos() / DESCARGADO)
                     or _leer_catalogo(rutas.recursos() / "libro" / "catalogo.json.gz")
                     or {"carpetas": [], "items": [], "casos": {}})
    return _catalogo


def descargar_catalogo(client, estado) -> int:
    """Guarda en el equipo la práctica libre vigente (carpetas y pacientes
    de api/practica.php, con el caso completo de `estado`, el de
    helpers.estado_en_memoria), con la forma del catálogo de la app
    (scripts/libro/catalogo_app.py). Devuelve cuántos pacientes quedaron.
    Se llama al entrar con red (main.agenda_cargada), nunca con el admin:
    él ve las carpetas solo_admin, que no son para practicar sin cuenta."""
    global _catalogo
    casos_estado = {str(c["id"]): c.get("data") for c in (estado or {}).get("cases") or []}
    carpetas, items, casos = {}, [], {}
    for it in client.get_practica():
        ficha = str(it.get("case_id") or "")
        data = casos_estado.get(ficha)
        if not isinstance(data, dict):
            continue
        fid = it.get("folder_id")
        if fid not in carpetas:
            carpetas[fid] = {"id": fid, "nombre": it.get("carpeta") or "", "grupo": it.get("grupo"),
                             "orden": len(carpetas) + 1}
        data = dict(data)
        data["id"] = int(ficha) if ficha.isdigit() else ficha
        casos[ficha] = data
        items.append({k: it.get(k) for k in ("id", "folder_id", "carpeta", "grupo", "case_id", "orden",
                                              "procedimiento", "nombre", "apellido", "rut", "fecha_nac")})
    if not items:
        return 0
    texto = json.dumps({"carpetas": list(carpetas.values()), "items": items, "casos": casos},
                       ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    destino = rutas.datos() / DESCARGADO
    tmp = destino.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(texto, 6))
    tmp.replace(destino)
    _catalogo = None
    print(f"práctica: catálogo guardado en el equipo ({len(items)} pacientes, {len(casos)} casos)")
    return len(items)


def items_practica():
    """Los pacientes de la práctica libre, con la forma de api/practica.php.
    Sin intentos: el invitado no deja registro."""
    return [dict(it, show_study_sheet=False, intentos=0, alumnos=0, ultimo=None,
                 ultimo_cerrado=None, abierto=None) for it in catalogo()["items"]]


def casos():
    """{ficha: cases.data}, como CasesOffline().get_cases()."""
    return {k: dict(v) for k, v in catalogo()["casos"].items()}


def agenda():
    """La agenda del invitado: una fila sin cita por paciente del libro (la
    "case:<ficha>" con que el docente prueba un caso). No tiene citas."""
    filas = {}
    for ficha, data in catalogo()["casos"].items():
        snap = data.get("paciente_snapshot") or {}
        filas[f"case:{ficha}"] = AgendaEntry(rut=snap.get("rut", ""), nombre=snap.get("nombre", ""),
                                             apellido=snap.get("apellido", ""),
                                             fecha_nac=snap.get("fecha_nac", ""), case_id=str(ficha),
                                             sin_cita=True)
    return {"agenda_1": filas}
