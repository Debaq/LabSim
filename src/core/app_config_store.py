"""
Cache en memoria de la config sincronizada desde app_config (backend, ver
labsim_backend/src/AppConfig.php). El backend ya resuelve el valor efectivo
por curso (override si la sesion viene de un contexto LTI con override, si
no el default global) -- este modulo solo guarda lo que llega y lo sirve, sin
resolver nada de nuevo.

Pensado para tablas normativas de examenes editables por el docente sin
recompilar la app: "normative_data.abr" primero, "normative_data.p300"/
"normative_data.ecochg" despues siguen la misma key generica
"normative_data.<examen>". Si no hay fila (ni override ni default) para una
key, get() devuelve el default y quien llama sigue usando su propio bundle
local (resources/.../normative_data.json) tal cual.
"""

_config: dict = {}


def update_from_sync(rows) -> None:
    """rows: lista de {'k':..., 'v':...} como llega en result['config']."""
    for row in rows or []:
        k = row.get("k")
        if k is not None:
            _config[k] = row.get("v")


def get(key: str, default=None):
    return _config.get(key, default)


def reset() -> None:
    """Limpia el cache -- usar al cerrar sesion, para no arrastrar config
    de un curso a la sesion siguiente si el proceso no se reinicia."""
    _config.clear()
