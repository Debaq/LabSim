"""Abre el panel de montaje solo, para probar la cabeza con el mouse.

    python3 scripts/cabeza_electrodos/probar.py      (desde la raíz de LabSim)
"""
import os
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
os.chdir(RAIZ)

from core.base import context  # noqa: E402  (crea el QApplication)
from core.cabeza_electrodos import MontajeElectrodos  # noqa: E402

ventana = MontajeElectrodos()
ventana.setWindowTitle("Montaje de electrodos (prueba)")
ventana.resize(820, 600)
ventana.montaje_cambio.connect(lambda m: print("montaje:", m))
ventana.show()
sys.exit(context.app.exec())
