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
import time

from PySide6.QtCore import QObject, QThread, Slot
from PySide6.QtWidgets import QApplication

_sueltos = set()

# Lo que se espera al cerrar la app a que terminen los hilos de red.
ESPERA_AL_SALIR_S = 4


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
    borrar_al_terminar(hilo)
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


class _Borrador(QObject):
    """Vive en el hilo de la ventana: lo que llega por `finished` se
    atiende acá, no en el hilo que está terminando."""

    @Slot()
    def terminado(self):
        hilo = self.sender()
        if isinstance(hilo, QThread):
            borrar(hilo)


_borrador = None


def borrar_al_terminar(hilo):
    """Borra `hilo` cuando terminó del todo. Reemplaza a
    `finished.connect(hilo.deleteLater)`, que en PySide no es seguro: Qt
    emite `finished` desde el hilo que termina y, mientras ese hilo
    todavía toca su objeto de Python, el principal podía estar
    destruyéndolo. La memoria quedaba corrupta y la app abortaba después,
    en cualquier otro borrado (Shiboken::Object::destroy; laboratorio,
    2026-10-08, tickets 1 y 2)."""
    global _borrador
    if _borrador is None:
        _borrador = _Borrador()
    hilo.finished.connect(_borrador.terminado)


def borrar(hilo):
    """Desde el hilo de la ventana: espera a que `hilo` haya salido del
    todo (wait vuelve enseguida después de `finished`) y recién ahí lo
    borra."""
    try:
        hilo.wait()
        _sueltos.discard(hilo)
        hilo.deleteLater()
    except RuntimeError:   # el objeto de Qt ya no existe
        _sueltos.discard(hilo)


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
    # Plazo total, no por hilo: con la red colgada varios hilos esperando
    # sumaban medio minuto con la ventana ya cerrada.
    limite = time.monotonic() + ESPERA_AL_SALIR_S
    for hilo in list(_sueltos):
        resto = int((limite - time.monotonic()) * 1000)
        if resto <= 0:
            break
        try:
            hilo.wait(resto)
        except RuntimeError:
            pass


def quedan_vivos() -> bool:
    """Si algún hilo soltado sigue corriendo (ver __main__ en main.py: no
    se puede dejar que el intérprete lo destruya al terminar)."""
    for hilo in list(_sueltos):
        try:
            if hilo.isRunning():
                return True
        except RuntimeError:
            continue
    return False
