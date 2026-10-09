"""Registro de la app en el equipo (lo que se imprime + errores + cuelgues).

Antes vivía al lado del programa (en el build, dentro de _internal/): cada
actualización lo borraba y crecía sin límite. Ahora va a la carpeta de
datos (core/rutas.py) y se rota al arrancar. Desde Configuración →
Reportar un problema se manda al servidor (ver core/soporte.py).

Corriendo desde el código sigue en src/log_file.txt, donde siempre estuvo.
"""
import os
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
        glibc = _glibc()
        if glibc:
            info["glibc"] = glibc
    return info


def _glibc() -> str:
    """glibc del equipo y la que pide el build (glibc_minima.txt, lo deja
    LabSim.spec): las libs empaquetadas se copian del PC donde se compila y
    no abren con una glibc más vieja."""
    try:
        equipo_glibc = os.confstr("CS_GNU_LIBC_VERSION") or ""
    except (ValueError, OSError):
        return ""
    minima = ""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        try:
            with open(os.path.join(base, "glibc_minima.txt"), encoding="utf-8") as f:
                minima = f.read().strip()
        except OSError:
            pass
    return f"{equipo_glibc} (el build pide {minima})" if minima else equipo_glibc


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


# -- Cierre inesperado ------------------------------------------------------------
# Al arrancar se deja una marca al lado del registro y al salir bien se
# borra. Si al arrancar la marca sigue ahí, la vez anterior LabSim se cayó
# (o lo mataron) y se ofrece mandar el registro (ver core/soporte.py).
# Sin esto el registro de una caída solo llegaba si alguien se acordaba de
# ir a Configuración → Reportar un problema.

_marca = None
_pendiente = None


def marcar_inicio(ruta_log: Path):
    """Deja la marca de "corriendo". Devuelve la hora de arranque de una
    vez anterior que no terminó bien y que todavía no se ofreció reportar,
    o None.

    Lo pendiente va en un archivo aparte que solo se borra al responder el
    aviso (cierre_atendido): en el kiosko, al reabrir tras una caída, la
    actualización obligatoria puede reiniciar antes de mostrar nada, y esa
    salida limpia borraba la marca y con ella el aviso."""
    global _marca, _pendiente
    _marca = Path(str(ruta_log) + ".en_curso")
    _pendiente = Path(str(ruta_log) + ".cierre_pendiente")
    try:
        if _marca.exists() and not _pendiente.exists():
            hora = _marca.read_text("utf-8").strip() or "?"
            _pendiente.write_text(hora, "utf-8")
    except OSError:
        pass
    try:
        _marca.write_text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "utf-8")
    except OSError:
        pass
    try:
        return _pendiente.read_text("utf-8").strip() or "?" if _pendiente.exists() else None
    except OSError:
        return None


def cierre_atendido() -> None:
    """Ya se ofreció mandar el registro de la caída (se mandó o no)."""
    if _pendiente is None:
        return
    try:
        _pendiente.unlink(missing_ok=True)
    except OSError:
        pass


def marcar_salida() -> None:
    """Salida en orden (cerrar, actualizar, reiniciar): no es una caída."""
    if _marca is None:
        return
    try:
        _marca.unlink(missing_ok=True)
    except OSError:
        pass
