# Runtime hook de PyInstaller para macOS (ver LabSim.spec): corre antes que
# main.py, solo en el .app.
#
# La app abre y escribe resources/ con rutas relativas a la carpeta de
# trabajo (cachés de audio, local_cache, el layout). Dentro de un .app eso
# rompe la firma (y en /Applications no se puede escribir), así que el .app
# trae resources/ de solo lectura y, una vez por versión, se copia a la
# carpeta de datos del usuario, donde se trabaja. Lo que es del usuario
# (local_cache/, json/session.json) no viene en el .app y no se toca.
import os
import shutil
import sys
from pathlib import Path

if sys.platform == "darwin" and getattr(sys, "frozen", False):
    origen = Path(sys._MEIPASS) / "resources"
    trabajo = Path.home() / "Library" / "Application Support" / "LabSim" / "app"
    marca_origen = origen / "version_build.txt"
    marca_trabajo = trabajo / "resources" / "version_build.txt"
    try:
        nueva = marca_origen.read_text() if marca_origen.exists() else "?"
        vieja = marca_trabajo.read_text() if marca_trabajo.exists() else ""
        if nueva != vieja:
            shutil.copytree(origen, trabajo / "resources", dirs_exist_ok=True)
        os.chdir(trabajo)
        # Los módulos que ubican resources/ junto al programa (core/rutas.recursos)
        os.environ["LABSIM_RECURSOS"] = str(trabajo / "resources")
    except OSError as exc:
        print(f"macOS: no se pudo preparar la carpeta de trabajo: {exc}")
