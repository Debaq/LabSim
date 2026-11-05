"""Recolección de ciclos solo en el hilo de la ventana.

Python corre el recolector en el hilo que esté reservando memoria en ese
momento. Si es un hilo de fondo (red, tiempos, pyudev) y el ciclo tiene
objetos de PySide, los borra fuera del hilo de Qt y la app cae
(ticket 33, 2026-11-05: "Garbage-collecting" en el hilo `tiempos`, segfault
en ~QMetaObject::Connection). Se apaga el automático y se recolecta desde un
QTimer, que siempre corre en el hilo de la ventana.
"""
import gc
import time

from PySide6.QtCore import QTimer

CADA_MS = 500
COMPLETA_CADA_S = 300

_timer = None
_ultima_completa = 0.0


def _pasada():
    global _ultima_completa
    ahora = time.monotonic()
    if ahora - _ultima_completa >= COMPLETA_CADA_S:
        _ultima_completa = ahora
        gc.collect()
    elif gc.get_count()[0] > gc.get_threshold()[0]:
        # 3.14: jóvenes + un tramo de la generación vieja, igual que el
        # automático. En versiones anteriores, generaciones 0 y 1.
        gc.collect(1)


def iniciar():
    """Llamar una vez, con la QApplication ya creada."""
    global _timer, _ultima_completa
    if _timer is not None:
        return
    gc.disable()
    _ultima_completa = time.monotonic()
    _timer = QTimer()
    _timer.setObjectName("recolector")
    _timer.timeout.connect(_pasada)
    _timer.start(CADA_MS)
