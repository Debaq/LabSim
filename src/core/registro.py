"""Registro de la app en el equipo (lo que se imprime + errores + cuelgues).

Antes vivía al lado del programa (en el build, dentro de _internal/): cada
actualización lo borraba y crecía sin límite. Ahora va a la carpeta de
datos (core/rutas.py) y se rota al arrancar. Desde Configuración →
Reportar un problema se manda al servidor (ver core/soporte.py).

Corriendo desde el código sigue en src/log_file.txt, donde siempre estuvo.
"""
import platform
import socket
import sys
from datetime import datetime
from pathlib import Path

from core import equipo, rutas

# Al arrancar, si el registro pasó este tamaño se rota (labsim.log ->
# labsim.1.log -> ... -> labsim.<COPIAS>.log, el más viejo se pierde).
MAX_BYTES = 5 * 1024 * 1024
COPIAS = 3

# Lo que se manda en un reporte: la cola, que es donde está el problema.
MAX_ENVIO = 4 * 1024 * 1024

_DEV = Path(__file__).resolve().parents[1] / "log_file.txt"


def archivo() -> Path:
    if getattr(sys, "frozen", False):
        return rutas.carpeta("logs") / "labsim.log"
    return _DEV


def _copia(ruta: Path, n: int) -> Path:
    return ruta.with_name(f"{ruta.stem}.{n}{ruta.suffix}")


def rotar(ruta: Path, max_bytes=MAX_BYTES, copias=COPIAS) -> None:
    """Rota si hace falta. Antes de abrir el archivo: en Windows no se
    puede renombrar uno abierto."""
    try:
        if not ruta.exists() or ruta.stat().st_size < max_bytes:
            return
        _copia(ruta, copias).unlink(missing_ok=True)
        for n in range(copias - 1, 0, -1):
            if _copia(ruta, n).exists():
                _copia(ruta, n).replace(_copia(ruta, n + 1))
        ruta.replace(_copia(ruta, 1))
    except OSError:
        pass  # otra instancia lo tiene abierto: se sigue agregando


def detalle_sistema() -> dict:
    """Lo que ayuda a reproducir un problema, más allá de la versión. Se le
    muestra al usuario antes de mandarlo."""
    from core.kiosko import es_kiosko
    info = {
        "so_version": f"{platform.system()} {platform.release()} ({platform.version()})",
        "arquitectura": platform.machine(),
        "python": platform.python_version(),
        "kiosko": es_kiosko(),
    }
    try:
        from PySide6 import __version__ as pyside
        from PySide6.QtCore import qVersion
        info["qt"] = f"Qt {qVersion()} / PySide6 {pyside}"
    except Exception:  # noqa: BLE001
        pass
    try:
        from PySide6.QtGui import QGuiApplication
        pantalla = QGuiApplication.primaryScreen()
        if pantalla is not None:
            g = pantalla.geometry()
            info["pantalla"] = f"{g.width()}x{g.height()} @ {pantalla.devicePixelRatio():g}x"
    except Exception:  # noqa: BLE001
        pass
    if sys.platform.startswith("linux"):
        try:
            info["distribucion"] = platform.freedesktop_os_release().get("PRETTY_NAME", "")
        except (OSError, AttributeError):
            pass
    return info


def encabezado() -> str:
    """Primera línea de cada arranque: separa una sesión de la anterior."""
    try:
        nombre = socket.gethostname()
    except OSError:
        nombre = "?"
    return (f"===== LabSim {equipo.version or '?'} arranca "
            f"{datetime.now():%Y-%m-%d %H:%M:%S} · {nombre} · "
            f"{platform.system()} {platform.release()} · Python {platform.python_version()} =====")


def cola(max_bytes=MAX_ENVIO) -> bytes:
    """Los últimos `max_bytes` del registro, empezando por la copia
    anterior si el actual es corto (el problema pudo ser antes de
    reiniciar la app)."""
    ruta = archivo()
    partes = []
    restante = max_bytes
    for r in (ruta, _copia(ruta, 1)):
        if restante <= 0:
            break
        try:
            with open(r, "rb") as f:
                f.seek(0, 2)
                tam = f.tell()
                f.seek(max(0, tam - restante))
                trozo = f.read()
        except OSError:
            continue
        partes.insert(0, trozo)
        restante -= len(trozo)
    return b"".join(partes)
