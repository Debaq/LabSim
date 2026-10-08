"""Carpetas de datos que sobreviven a las actualizaciones.

Lo que vive al lado del programa (resources/local_cache, el log viejo en
_internal/) se reemplaza entero cada vez que se actualiza la app. El
registro y el respaldo de los informes no pueden irse con eso: van a la
carpeta de datos del usuario del sistema.

- Windows: %LOCALAPPDATA%\\LabSim
- Linux/macOS: $XDG_DATA_HOME/LabSim (~/.local/share/LabSim)

LABSIM_DATA_DIR la reemplaza (tests, o un laboratorio que quiera otra).
"""
import os
import sys
from pathlib import Path


def datos() -> Path:
    propia = os.environ.get("LABSIM_DATA_DIR", "").strip()
    if propia:
        base = Path(propia)
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "LabSim"
    else:
        xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        base = (Path(xdg) if xdg else Path.home() / ".local" / "share") / "LabSim"
    base.mkdir(parents=True, exist_ok=True)
    return base


def carpeta(nombre: str) -> Path:
    ruta = datos() / nombre
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta
