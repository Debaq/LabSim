"""Carpetas de datos que sobreviven a las actualizaciones.

Lo que vive al lado del programa (resources/local_cache, el log viejo en
_internal/) se reemplaza entero cada vez que se actualiza la app. El
registro y el respaldo de los informes no pueden irse con eso: van a la
carpeta de datos del usuario del sistema.

- Windows: %LOCALAPPDATA%\\LabSim
- macOS: ~/Library/Application Support/LabSim
- Linux: $XDG_DATA_HOME/LabSim (~/.local/share/LabSim)

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
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "LabSim"
    else:
        xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        base = (Path(xdg) if xdg else Path.home() / ".local" / "share") / "LabSim"
    base.mkdir(parents=True, exist_ok=True)
    return base


def recursos() -> Path:
    """resources/ del programa, para quien la ubica junto al código en vez de
    por la carpeta de trabajo. En el .app de macOS es la copia de trabajo
    (ver installer/hooks/rth_macos.py): dentro del .app no se escribe."""
    propia = os.environ.get("LABSIM_RECURSOS", "").strip()
    return Path(propia) if propia else Path(__file__).resolve().parents[2] / "resources"


def carpeta(nombre: str) -> Path:
    ruta = datos() / nombre
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta
