"""
Identidad de este equipo, que viaja con el login para que el backend sepa
qué versión de la app hay en cada máquina (admin/versiones.php del backend,
ver Equipos.php).

El id sale del machine-id (Linux) o del MachineGuid (Windows), hasheado:
las máquinas del laboratorio salen de la misma imagen y pueden compartir
nombre, y el valor crudo no tiene por qué salir del equipo.
"""
import hashlib
import platform
import socket
import sys
import uuid
from pathlib import Path

# La fija main.py al arrancar (el build id, igual que el título de la ventana).
version = ""


def _id_crudo() -> str:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography") as key:
                return str(winreg.QueryValueEx(key, "MachineGuid")[0])
        except OSError:
            pass
    else:
        for ruta in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                valor = Path(ruta).read_text("utf-8").strip()
            except OSError:
                continue
            if valor:
                return valor
    return f"{uuid.getnode():012x}"


def identidad() -> dict | None:
    """Bloque "equipo" del login. None si algo falla: el login no puede
    caerse por esto."""
    if not version:
        return None
    try:
        return {
            "id": hashlib.blake2b(_id_crudo().encode(), digest_size=8).hexdigest(),
            "nombre": socket.gethostname(),
            "so": platform.system(),
            "version": version,
            "empaquetada": bool(getattr(sys, "frozen", False)),
        }
    except Exception:
        return None
