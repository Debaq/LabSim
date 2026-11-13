"""Configuración común de pytest para los tests de LabSim.

Al terminar, si se cargó Qt, pytest sale con os._exit, igual que la app
(main.py): sin desarmar el intérprete. Las ventanas que los tests dejan
vivas (pyqtgraph, módulos ABR, rinoscopía...) se destruirían ahí en
cualquier orden, con Qt mandando eventos a objetos de Python ya liberados:
pytest pasaba todos los tests y terminaba con violación de segmento.

Cerrar o borrar las ventanas entre tests no sirve: cambia lo que prueban
(test_abr_montaje falla) y el borrado final igual se cae con pyqtgraph.
Los tests que se corren como script (`python tests/test_x.py`) no pasan
por acá.
"""
import os
import sys

import pytest

_estado = 0


def pytest_sessionfinish(session, exitstatus):
    global _estado
    _estado = int(exitstatus)


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config):
    """Después del resumen de pytest y del resto de los plugins."""
    if "PySide6.QtCore" not in sys.modules:
        return
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_estado)
