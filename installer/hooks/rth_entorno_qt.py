# Runtime hook de PyInstaller (ver LabSim.spec): corre antes que main.py.
#
# Sin integración GL de xcb: la app es todo Widgets (raster) y no usa
# OpenGL, pero con la integración GLX Qt abre el driver de video del
# equipo (Mesa, con su LLVM y sus libs del sistema) y lo mezcla con las
# libs empaquetadas del PC donde se compiló. Así lo único que se carga del
# sistema es glibc, el despachador GL (glvnd, que no se usa) y libpipewire
# (ver docs/decisiones.md, "Build encapsulado").
import os
import sys

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_XCB_GL_INTEGRATION", "none")
