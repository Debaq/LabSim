"""Trabajo de red fuera del hilo de la ventana, sin QThread.

Historia corta: con QThread de Python pasaron tres cosas. Qt aborta el
proceso ("QThread: Destroyed while thread is still running") si se destruye
uno que sigue corriendo: cerrar sesión con la red lenta borraba los módulos
con sus hilos hijos esperando al servidor (2026-10-08, "sin internet LabSim
se cierra"). finished -> deleteLater lo destruía mientras el hilo todavía
tocaba su objeto de Python (2026-10-08, tickets 1 y 2). Y aun borrándolo
recién después de wait(), en el laboratorio (2026-10-09, tickets 3 a 14,
0.9.9-rc84c5553) LabSim se siguió cerrando solo en los cinco equipos, más o
menos una vez por hora en cada uno, haciendo cualquier examen. Los volcados
son siempre memoria corrupta en el hilo de la ventana: un free() inválido
al borrar un QObject (DeferredDelete -> Shiboken::Object::destroy) o un
segfault del recolector de Python, casi siempre con el hilo de la agenda a
mitad de una consulta. La agenda y la subida de pendientes creaban y
borraban un QThread cada 15 s y, como el sync, pasaban objetos de Python
por señales encoladas: miles de ciclos de vida de envoltorios de Shiboken
entre dos hilos por jornada.

Acá no se crea ningún objeto de Qt por trabajo:

- en_fondo(funcion, ...): una consulta suelta en un hilo de Python
  (threading). El resultado vuelve al hilo de la ventana por una cola de
  Python; a Qt solo le llega un aviso sin datos (_Correo.hay).
- Ciclo: un hilo de Python que repite algo cada N segundos (sync, logs,
  reintento del layout); lo que tenga que mostrar va con avisar().

No hay nada que borrar con deleteLater ni nada que Qt pueda destruir
corriendo. Si quien lo pidió (`dueno`) ya no existe cuando llega el
resultado, no se le avisa. Los hilos son daemon; al salir se espera un rato
a los que siguen (ver _al_salir y quedan_vivos).
"""
import queue
import threading
import time
import traceback
import weakref

import shiboken6
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QApplication

# Lo que se espera al cerrar la app a que terminen los hilos de red.
ESPERA_AL_SALIR_S = 4

_tareas = set()
_ciclos = weakref.WeakSet()
_conectado = False


def _esperar_al_salir():
    """Al cerrar la app, los que sigan esperando a la red tienen un rato
    para terminar (una subida a medias, el último lote de logs)."""
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
    for hilo in [t for t in list(_tareas)] + [c for c in list(_ciclos)]:
        resto = int((limite - time.monotonic()) * 1000)
        if resto <= 0:
            return
        if isinstance(hilo, Ciclo):
            hilo.requestInterruption()
            hilo.wait(resto)
        else:
            hilo.esperar(resto)


def quedan_vivos() -> bool:
    """Si algún hilo de red sigue corriendo (ver __main__ en main.py: se
    sale con os._exit en vez de dejar que el intérprete los congele a mitad
    de una petición mientras desarma Qt)."""
    return (any(t.corriendo() for t in list(_tareas))
            or any(c.isRunning() for c in list(_ciclos)))


class Tarea:
    """Un trabajo lanzado con en_fondo(). Al terminar, en el hilo de la
    ventana se llama `listo(resultado)` o, si lanzó, `fallo(excepcion)`."""

    def __init__(self, funcion, args, kwargs, listo, fallo, dueno, nombre):
        self._funcion = funcion
        self._args = args
        self._kwargs = kwargs
        self._listo = listo
        self._fallo = fallo
        self._dueno = _referencia(dueno)
        self._fin = threading.Event()
        self._cortar = threading.Event()
        self.resultado = None
        self.error = None
        self._hilo = threading.Thread(target=self._correr, name=nombre, daemon=True)

    def _correr(self):
        try:
            self.resultado = self._funcion(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 -- lo atiende `fallo`
            self.error = exc
        finally:
            self._fin.set()
            _buzon.put(self)
            correo = _correo
            if correo is not None:
                correo.hay.emit()

    def corriendo(self) -> bool:
        return not self._fin.is_set()

    def esperar(self, ms=None) -> bool:
        """True si terminó (dentro de `ms`, o sin plazo con None)."""
        return self._fin.wait(None if ms is None else max(ms, 0) / 1000)

    def cortar(self):
        """Pide que termine antes (la función lo mira con `cortada()`)."""
        self._cortar.set()

    def cortada(self) -> bool:
        return self._cortar.is_set()

    def descartar(self):
        """Que el resultado ya no le llegue a nadie (el trabajo sigue)."""
        self._listo = self._fallo = None

    def _entregar(self):
        _tareas.discard(self)
        dueno = self._dueno() if self._dueno is not None else None
        if self._dueno is not None and (dueno is None or not shiboken6.isValid(dueno)):
            return   # quien lo pidió ya no existe
        if self.error is None:
            aviso, valor = self._listo, self.resultado
        else:
            aviso, valor = self._fallo, self.error
            if aviso is None:
                print(f"{self._hilo.name}: {type(self.error).__name__}: {self.error}")
        self._listo = self._fallo = None
        if aviso is None:
            return
        try:
            aviso(valor)
        except Exception:  # noqa: BLE001 -- un aviso roto no tira la app
            traceback.print_exc()


class _Aviso:
    """Una llamada que un hilo de fondo le deja al hilo de la ventana."""

    def __init__(self, funcion, args, dueno):
        self._funcion = funcion
        self._args = args
        self._dueno = _referencia(dueno)

    def _entregar(self):
        if self._dueno is not None:
            dueno = self._dueno()
            if dueno is None or not shiboken6.isValid(dueno):
                return
        try:
            self._funcion(*self._args)
        except Exception:  # noqa: BLE001 -- un aviso roto no tira la app
            traceback.print_exc()


def avisar(funcion, *args, dueno=None):
    """Desde cualquier hilo: que `funcion(*args)` corra en el hilo de la
    ventana (si `dueno` sigue existiendo). Los datos no pasan por Qt: van
    por una cola de Python y a Qt solo le llega un aviso sin argumentos.
    Requiere preparar() antes, desde el hilo de la ventana."""
    _buzon.put(_Aviso(funcion, args, dueno))
    correo = _correo
    if correo is not None:
        correo.hay.emit()


def _referencia(dueno):
    if dueno is None:
        return None
    try:
        return weakref.ref(dueno)
    except TypeError:
        return lambda: dueno


class _Correo(QObject):
    """Vive en el hilo de la ventana. Los hilos de en_fondo() dejan la
    tarea en `_buzon` y emiten `hay` (sin argumentos): acá se reparte."""

    hay = Signal()

    def __init__(self):
        super().__init__()
        self.hay.connect(self.repartir, Qt.ConnectionType.QueuedConnection)

    @Slot()
    def repartir(self):
        # Solo lo que ya estaba: si un aviso lanza otra tarea que termina
        # enseguida, esa trae su propio `hay`. Vaciar hasta que no quede
        # nada dejaba a la ventana sin volver nunca al bucle de eventos.
        for _ in range(_buzon.qsize()):
            try:
                item = _buzon.get_nowait()
            except queue.Empty:
                return
            item._entregar()


_buzon = queue.SimpleQueue()
_correo = None


def en_fondo(funcion, *args, listo=None, fallo=None, dueno=None, nombre="fondo", **kwargs):
    """Corre `funcion(*args, **kwargs)` fuera del hilo de la ventana y
    devuelve la Tarea. Llamar desde el hilo de la ventana.

    `listo(resultado)` / `fallo(excepcion)` se llaman después en el hilo de
    la ventana. Con `dueno` (un QObject), si para entonces ya no existe no
    se avisa. Sin `fallo`, la excepción solo queda en el registro. La
    función no puede tocar widgets: corre en otro hilo."""
    preparar()
    tarea = Tarea(funcion, args, kwargs, listo, fallo, dueno, nombre)
    _tareas.add(tarea)
    _esperar_al_salir()
    tarea._hilo.start()
    return tarea


def preparar():
    """Crea el correo (desde el hilo de la ventana) antes de que un hilo de
    fondo quiera avisar algo."""
    global _correo
    if _correo is None:
        _correo = _Correo()
        app = QApplication.instance()
        if app is not None and _correo.thread() is not app.thread():
            _correo.moveToThread(app.thread())


class Ciclo:
    """Hilo de Python que repite `paso()` cada `intervalo_s` hasta que se
    lo para (sync, subida de logs, reintento del layout). Misma interfaz
    que tenían como QThread (start/stop/wait/isRunning/
    isInterruptionRequested), sin objeto de Qt: lo que tenga que llegar a
    la ventana va con avisar(). Es daemon: al salir no aborta nada."""

    def __init__(self, intervalo_s, nombre):
        self._intervalo_s = intervalo_s
        self._nombre = nombre
        self._parar = threading.Event()
        self._despertar = threading.Event()
        self._hilo = None

    def start(self):
        preparar()
        _ciclos.add(self)
        _esperar_al_salir()
        self._hilo = threading.Thread(target=self.run, name=self._nombre, daemon=True)
        self._hilo.start()

    def run(self):
        while not self._parar.is_set():
            self.paso()
            self._esperar_turno()

    def _esperar_turno(self) -> bool:
        """Espera el intervalo o hasta ahora()/stop(). False si lo pararon."""
        self._despertar.wait(self._intervalo_s)
        self._despertar.clear()
        return not self._parar.is_set()

    def ahora(self):
        """Que el próximo paso sea ya, sin esperar el intervalo (después de
        un evento importante: atender, cerrar la atención, salir)."""
        self._despertar.set()

    def paso(self):
        raise NotImplementedError

    def requestInterruption(self):
        self._parar.set()
        self._despertar.set()

    def isInterruptionRequested(self) -> bool:
        return self._parar.is_set()

    def isRunning(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    def wait(self, ms=None) -> bool:
        if self._hilo is not None:
            self._hilo.join(None if ms is None else ms / 1000)
        return not self.isRunning()

    def stop(self):
        self.requestInterruption()
        self.wait(2000)


def entregar_pendientes():
    """Reparte ya los resultados que llegaron (sin esperar al bucle de
    eventos): para quien acaba de esperar una tarea y necesita su aviso
    procesado antes de seguir."""
    if _correo is not None:
        _correo.repartir()
