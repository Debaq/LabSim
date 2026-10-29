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


def catalogo():
    global _catalogo
    if _catalogo is None:
        try:
            _catalogo = json.loads(gzip.decompress((rutas.recursos() / "libro" / "catalogo.json.gz").read_bytes()))
        except (OSError, ValueError):
            _catalogo = {"carpetas": [], "items": [], "casos": {}}
    return _catalogo


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
