"""
Layout de la app (módulos / sectores / boxes) pedido al backend al
arrancar. Antes vivía en resources/json/apps.json; ahora viene por
GET /api/layout.php.

Si la red no responde o el backend falla, devolvemos None y la app abre
solo con la ventana de login (sin toolbar). Es el comportamiento pedido
para instalaciones sin conectividad: el usuario ve el aviso y nada más.
"""
import requests

LAYOUT_TIMEOUT = 3


def fetch_layout(backend_url: str) -> dict | None:
    """Trae {APP, SECTORS, BOXS} del backend. None si no responde a tiempo
    o devuelve algo que no parece layout. Timeout corto a propósito:
    preferimos abrir sin toolbar a colgarnos esperando."""
    url = backend_url.rstrip("/") + "/api/layout.php"
    try:
        resp = requests.get(url, timeout=LAYOUT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None
    if not isinstance(data, dict) or "APP" not in data or "BOXS" not in data:
        return None
    return data
