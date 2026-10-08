"""Hilos de red que sobreviven a quien los lanzó.

Qt aborta el proceso entero ("QThread: Destroyed while thread is still
running") si se destruye un QThread que sigue corriendo. Con la red lenta
pasaba seguido: cerrar sesión borra los módulos, y con ellos los hilos hijos
que todavía esperaban al servidor (la agenda, el chat, la otoscopia); o un
stop() que esperaba 2 s soltaba la última referencia a un hilo que seguía
en una petición de 10. Desde afuera se veía como "sin internet, LabSim se
cierra".

`soltar(hilo)` lo desengancha de su dueño y lo guarda acá hasta que
termine solo; recién ahí se borra. Lo que el hilo emita después ya no le
llega a nadie (el dueño no existe) o le llega a quien siga vivo.
"""
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

_sueltos = set()


def soltar(hilo):
    """Que `hilo` siga hasta terminar sin depender de su dueño."""
    if hilo is None:
        return
    try:
        corriendo = hilo.isRunning()
    except RuntimeError:   # el objeto de Qt ya no existe
        return
    if not corriendo:
        return
    if hilo in _sueltos:
        return
    hilo.requestInterruption()
    hilo.setParent(None)
    _sueltos.add(hilo)
    hilo.finished.connect(lambda h=hilo: _terminado(h))
    _esperar_al_salir()


def soltar_hijos(objeto):
    """Suelta los hilos hijos de `objeto` que sigan corriendo; llamar antes
    de borrarlo (deleteLater)."""
    try:
        hilos = objeto.findChildren(QThread)
    except RuntimeError:
        return
    for hilo in hilos:
        soltar(hilo)


def _terminado(hilo):
    _sueltos.discard(hilo)
    hilo.deleteLater()


_conectado = False


def _esperar_al_salir():
    """Al cerrar la app, los que sigan esperando a la red tienen un rato
    para terminar; si no, se destruirían corriendo al salir del intérprete."""
    global _conectado
    app = QApplication.instance()
    if _conectado or app is None:
        return
    _conectado = True
    app.aboutToQuit.connect(_al_salir)


def _al_salir():
    for hilo in list(_sueltos):
        try:
            hilo.wait(3000)
        except RuntimeError:
            pass
