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

# Último error (si lo hubo) de la última llamada a fetch_layout. Lo lee
# main.py para mostrar el detalle en el QMessageBox de "Sin conexión".
last_error: "LayoutFetchError | None" = None


class LayoutFetchError(Exception):
    """Detalle del fallo al pedir /api/layout.php para mostrar al usuario."""
    def __init__(self, phase: str, detail: str):
        super().__init__(f"{phase}: {detail}")
        self.phase = phase   # "conexión", "timeout", "http", "json", "estructura"
        self.detail = detail


def fetch_layout(backend_url: str) -> dict | None:
    """Trae {APP, SECTORS, BOXS} del backend. None si no responde a tiempo
    o devuelve algo que no parece layout. Timeout corto a propósito:
    preferimos abrir sin toolbar a colgarnos esperando.

    Si falla, guarda el error en `app_layout.last_error` para que el
    caller lo muestre al usuario sin tener que cambiar la firma."""
    global last_error
    last_error = None
    if not backend_url:
        return None
    url = backend_url.rstrip("/") + "/api/layout.php"
    try:
        try:
            resp = requests.get(url, timeout=LAYOUT_TIMEOUT)
        except requests.ConnectionError as exc:
            raise LayoutFetchError("conexión", str(exc)) from exc
        except requests.Timeout:
            raise LayoutFetchError("timeout", f"sin respuesta en {LAYOUT_TIMEOUT}s")
        except requests.RequestException as exc:
            raise LayoutFetchError("red", str(exc)) from exc
        if resp.status_code >= 400:
            raise LayoutFetchError("http", f"{resp.status_code} {resp.reason}")
        try:
            data = resp.json()
        except ValueError:
            raise LayoutFetchError("json", "respuesta no es JSON válido")
        if not isinstance(data, dict) or "APP" not in data or "BOXS" not in data:
            raise LayoutFetchError("estructura", "falta APP o BOXS en la respuesta")
        return data
    except LayoutFetchError as exc:
        last_error = exc
        return None
