"""Tiempos de la app en terreno: dónde se queda pegada.

Todo queda en un archivo JSONL por arranque, en la carpeta de datos
(core/rutas.py → tiempos/). No se sube a ningún lado: se retira del equipo
y se lee con scripts/resumir_tiempos.py. LABSIM_TIEMPOS=0 lo apaga.

Qué se mide:
- bloqueo: el hilo de la ventana no volvió al bucle de eventos en más de
  UMBRAL_BLOQUEO_MS. Un hilo vigía le saca la pila de Python mientras dura,
  así queda escrito qué estaba haciendo. Una pila vacía = el tiempo se fue
  adentro de Qt (pintar, layout, estilos), no en código nuestro.
- http: cada petición de `requests`, con el hilo desde el que se hizo. Una
  en el hilo "ui" congela la ventana mientras espera.
- pg …: pintar y actualizar curvas de pyqtgraph.
- resumen: cada minuto, por nombre: n, total, p50, p95 y máximo; más
  memoria, CPU y cantidad de hilos del proceso.
- hito / marca: puntos de referencia del arranque y de las acciones.

Nada de lo que se escribe lleva datos del alumno ni del paciente: las rutas
de red van sin consulta y con los números reemplazados por :n.
"""
import atexit
import functools
import json
import os
import platform
import re
import socket
import sys
import threading
import time
from collections import Counter
from datetime import datetime
from urllib.parse import urlsplit

from core import rutas

LATIDO_MS = 30            # cada cuánto el hilo de la ventana "late"
UMBRAL_BLOQUEO_MS = 120   # más que esto sin latir = bloqueo
SUSPENSION_MS = 30_000    # más que esto es el equipo dormido, no la app
UMBRAL_LENTO_MS = 150     # una operación medida más lenta que esto se escribe suelta
RESUMEN_CADA_S = 60
VACIAR_CADA_S = 2
MUESTRAS_MAX = 4000
ARCHIVOS_MAX = 40
BYTES_MAX = 8 * 1024 * 1024

_activo = False
_lock = threading.Lock()
_buffer = []
_archivo = None
_bytes = 0
_t0_perf = time.perf_counter()
_t0_wall = time.time()

_metricas = {}
_pilas = Counter()
_marca = None             # (t_ms, texto) de la última acción marcada
_hilo_ui = None
_ultimo_latido = None
_ultimo_cpu = (time.perf_counter(), time.process_time())
_pg_parchado = False


def instalar(t0_wall=None):
    """Abre el archivo y arranca el vigía. Llamar una vez, apenas está el
    registro. `t0_wall`: time.time() del primer renglón de main.py, para que
    los tiempos cuenten desde que arrancó el proceso."""
    global _activo, _archivo, _t0_perf, _t0_wall
    if _activo or os.environ.get("LABSIM_TIEMPOS", "").strip() == "0":
        return False
    if t0_wall is not None:
        _t0_perf -= max(0.0, time.time() - t0_wall)
        _t0_wall = t0_wall
    try:
        carpeta = rutas.carpeta("tiempos")
        _podar(carpeta)
        nombre = f"tiempos-{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}.jsonl"
        _archivo = open(carpeta / nombre, "a", encoding="utf-8")
    except OSError:
        return False
    _activo = True
    evento("sistema", **_info_sistema())
    _parchar_requests()
    atexit.register(_cerrar)
    threading.Thread(target=_vigia, name="tiempos", daemon=True).start()
    return True


def iniciar_ui():
    """Empieza a medir el hilo de la ventana. Llamar desde ese hilo, con la
    QApplication ya creada."""
    global _hilo_ui, _ultimo_latido
    if not _activo or _hilo_ui is not None:
        return
    from PySide6.QtCore import QTimer, Qt, qVersion
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        return
    _hilo_ui = threading.get_ident()
    _ultimo_latido = time.perf_counter()
    timer = QTimer(app)
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.setInterval(LATIDO_MS)
    timer.timeout.connect(_latir)
    timer.start()
    app._tiempos_timer = timer
    pantallas = [{"px": [s.size().width(), s.size().height()],
                  "dpr": round(s.devicePixelRatio(), 2)} for s in QGuiApplication.screens()]
    evento("pantalla", qt=qVersion(), plataforma=QGuiApplication.platformName(),
           pantallas=pantallas)


def hito(nombre):
    """Punto de referencia: cuánto tardó el proceso en llegar hasta acá."""
    evento("hito", nombre=nombre)


def marca(texto):
    """Anota una acción (abrir módulo, cambiar de pestaña) para poder
    cruzarla después con los bloqueos que vinieron justo detrás."""
    global _marca
    if _activo:
        _marca = (_ms(), texto)
        evento("marca", nombre=texto)


class medir:
    """`with tiempos.medir("nombre"):` o `@tiempos.medir("nombre")`."""

    def __init__(self, nombre, **extra):
        self.nombre = nombre
        self.extra = extra

    def __enter__(self):
        self._t = time.perf_counter()
        return self

    def __exit__(self, *exc):
        registrar(self.nombre, (time.perf_counter() - self._t) * 1000, **self.extra)
        return False

    def __call__(self, funcion):
        @functools.wraps(funcion)
        def envuelta(*args, **kwargs):
            with medir(self.nombre, **self.extra):
                return funcion(*args, **kwargs)
        return envuelta


def registrar(nombre, ms, siempre=False, **extra):
    """Suma una medición al resumen del minuto. Si fue lenta (o `siempre`),
    además queda escrita sola."""
    if not _activo:
        return
    _sumar(nombre, ms)
    if siempre or ms >= UMBRAL_LENTO_MS:
        evento("lento", nombre=nombre, ms=round(ms, 1), **extra)


def _sumar(nombre, ms):
    with _lock:
        m = _metricas.get(nombre)
        if m is None:
            m = _metricas[nombre] = {"n": 0, "tot": 0.0, "max": 0.0, "v": []}
        m["n"] += 1
        m["tot"] += ms
        if ms > m["max"]:
            m["max"] = ms
        if len(m["v"]) < MUESTRAS_MAX:
            m["v"].append(ms)
        else:
            m["v"][m["n"] % MUESTRAS_MAX] = ms


def evento(tipo, **datos):
    global _bytes
    if not _activo:
        return
    registro = {"t": _ms(), "ts": datetime.now().strftime("%H:%M:%S.%f")[:-3], "tipo": tipo}
    registro.update(datos)
    try:
        linea = json.dumps(registro, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return
    with _lock:
        if _bytes + len(linea) > BYTES_MAX and tipo not in ("resumen", "fin"):
            return
        _buffer.append(linea)
        _bytes += len(linea) + 1


def _ms():
    return round((time.perf_counter() - _t0_perf) * 1000, 1)


# -- hilo de la ventana ------------------------------------------------

def _latir():
    """Corre en el hilo de la ventana cada LATIDO_MS. Si llega tarde, el
    bucle de eventos estuvo ocupado (o bloqueado) ese rato."""
    global _ultimo_latido
    ahora = time.perf_counter()
    retraso = (ahora - _ultimo_latido) * 1000 - LATIDO_MS
    _ultimo_latido = ahora
    if retraso < 0:
        retraso = 0.0
    _sumar("bucle: retraso", retraso)
    with _lock:
        total = sum(_pilas.values())
        top = _pilas.most_common(3)
        _pilas.clear()
    if retraso < UMBRAL_BLOQUEO_MS:
        return
    if retraso >= SUSPENSION_MS:
        evento("suspension", ms=round(retraso))
        return
    datos = {"ms": round(retraso), "muestras": total,
             "pilas": [{"n": n, "pila": p} for p, n in top]}
    if _marca is not None and _ms() - _marca[0] < 4000:
        datos["tras"] = _marca[1]
    evento("bloqueo", **datos)


def _pila(frame, limite=14):
    partes = []
    while frame is not None and len(partes) < limite:
        codigo = frame.f_code
        archivo = codigo.co_filename.replace("\\", "/").split("/")
        partes.append(f"{'/'.join(archivo[-2:])}:{frame.f_lineno} {codigo.co_name}")
        frame = frame.f_back
    return " < ".join(partes) if partes else "(dentro de Qt)"


def _vigia():
    """Hilo aparte: mientras la ventana no late, le saca la pila; cada
    VACIAR_CADA_S escribe lo pendiente; cada RESUMEN_CADA_S el resumen."""
    ultimo_vaciado = ultimo_resumen = time.monotonic()
    while True:
        time.sleep(0.04)
        try:
            if _ultimo_latido is not None:
                atraso = (time.perf_counter() - _ultimo_latido) * 1000
                if LATIDO_MS + UMBRAL_BLOQUEO_MS < atraso < SUSPENSION_MS:
                    frame = sys._current_frames().get(_hilo_ui)
                    clave = _pila(frame)
                    with _lock:
                        _pilas[clave] += 1
            ahora = time.monotonic()
            if ahora - ultimo_resumen >= RESUMEN_CADA_S:
                ultimo_resumen = ahora
                _resumen()
            if ahora - ultimo_vaciado >= VACIAR_CADA_S:
                ultimo_vaciado = ahora
                _vaciar()
        except Exception:  # noqa: BLE001 -- medir nunca tira abajo a la app
            pass


def _percentil(ordenados, p):
    return ordenados[min(len(ordenados) - 1, int(len(ordenados) * p))]


def _resumen():
    global _metricas, _ultimo_cpu
    with _lock:
        actual, _metricas = _metricas, {}
    salida = {}
    for nombre, m in actual.items():
        v = sorted(m["v"])
        salida[nombre] = {"n": m["n"], "tot": round(m["tot"], 1), "p50": round(_percentil(v, 0.5), 1),
                          "p95": round(_percentil(v, 0.95), 1), "max": round(m["max"], 1)}
    ahora, cpu = time.perf_counter(), time.process_time()
    pct = round(100 * (cpu - _ultimo_cpu[1]) / max(1e-6, ahora - _ultimo_cpu[0]), 1)
    _ultimo_cpu = (ahora, cpu)
    evento("resumen", ventana_s=RESUMEN_CADA_S, metricas=salida,
           proceso={"rss_mb": _rss_mb(), "cpu_pct": pct, "hilos": threading.active_count()})
    _parchar_pyqtgraph()


def _vaciar():
    global _buffer
    with _lock:
        lineas, _buffer = _buffer, []
    if lineas and _archivo is not None:
        try:
            _archivo.write("\n".join(lineas) + "\n")
            _archivo.flush()
        except (OSError, ValueError):
            pass


def _cerrar():
    if not _activo:
        return
    evento("fin", segundos=round(_ms() / 1000, 1))
    _resumen()
    _vaciar()


# -- red ---------------------------------------------------------------

def _ruta(url):
    """Ruta sin consulta ni host, con los números como :n (ids)."""
    try:
        return re.sub(r"/\d+(?=/|$)", "/:n", urlsplit(str(url)).path) or "/"
    except ValueError:
        return "?"


def _parchar_requests():
    try:
        import requests
    except ImportError:
        return
    original = requests.Session.request
    if getattr(original, "_labsim_tiempos", False):
        return

    def request(self, method, url, *args, **kwargs):
        t = time.perf_counter()
        hilo = ("ui" if threading.current_thread() is threading.main_thread()
                else threading.current_thread().name)
        estado, nbytes, espera = None, None, None
        try:
            resp = original(self, method, url, *args, **kwargs)
            estado = resp.status_code
            espera = round(resp.elapsed.total_seconds() * 1000, 1)
            if not kwargs.get("stream"):
                nbytes = len(resp.content)
            return resp
        except Exception as exc:
            estado = type(exc).__name__
            raise
        finally:
            ms = (time.perf_counter() - t) * 1000
            registrar(f"http {str(method).upper()} {_ruta(url)}", ms, siempre=(hilo == "ui"),
                      hilo=hilo, estado=estado, bytes=nbytes, hasta_cabeceras_ms=espera)
            if hilo == "ui":
                registrar("http en hilo ui", ms)

    request._labsim_tiempos = True
    requests.Session.request = request


# -- pyqtgraph ---------------------------------------------------------

_PG_OBJETIVOS = (
    ("PlotCurveItem", "paint"), ("PlotCurveItem", "setData"),
    ("PlotDataItem", "setData"), ("ScatterPlotItem", "paint"),
    ("ScatterPlotItem", "setData"), ("ViewBox", "setRange"),
)


def _parchar_pyqtgraph():
    """pyqtgraph se importa tarde (precarga); se engancha cuando ya está."""
    global _pg_parchado
    pg = sys.modules.get("pyqtgraph")
    if _pg_parchado or pg is None:
        return
    _pg_parchado = True
    for clase, metodo in _PG_OBJETIVOS:
        cls = getattr(pg, clase, None)
        original = getattr(cls, metodo, None)
        if original is None:
            continue
        nombre = f"pg {clase}.{metodo}"

        def envolver(original=original, nombre=nombre):
            @functools.wraps(original)
            def medido(*args, **kwargs):
                t = time.perf_counter()
                try:
                    return original(*args, **kwargs)
                finally:
                    registrar(nombre, (time.perf_counter() - t) * 1000)
            return medido

        setattr(cls, metodo, envolver())


# -- sistema -----------------------------------------------------------

def _rss_mb():
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class Contadores(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

            c = Contadores()
            c.cb = ctypes.sizeof(c)
            ctypes.windll.psapi.GetProcessMemoryInfo(
                ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
            return round(c.WorkingSetSize / 1048576, 1)
        with open("/proc/self/statm") as f:
            return round(int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") / 1048576, 1)
    except (OSError, ValueError, AttributeError, IndexError):
        return None


def _info_sistema():
    from core import equipo
    try:
        from core.kiosko import es_kiosko
        kiosko = es_kiosko()
    except Exception:  # noqa: BLE001
        kiosko = None
    cpu, ram = platform.processor() or None, None
    try:
        if sys.platform.startswith("linux"):
            with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as f:
                cpu = next((l.split(":", 1)[1].strip() for l in f if l.startswith("model name")), cpu)
            with open("/proc/meminfo") as f:
                ram = round(int(f.readline().split()[1]) / 1024)
        elif sys.platform == "win32":
            import ctypes

            class Memoria(ctypes.Structure):
                _fields_ = [("largo", ctypes.c_ulong), ("carga", ctypes.c_ulong),
                            ("fisica", ctypes.c_ulonglong), ("libre", ctypes.c_ulonglong),
                            ("p1", ctypes.c_ulonglong), ("p2", ctypes.c_ulonglong),
                            ("v1", ctypes.c_ulonglong), ("v2", ctypes.c_ulonglong),
                            ("e", ctypes.c_ulonglong)]

            m = Memoria()
            m.largo = ctypes.sizeof(m)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            ram = round(m.fisica / 1048576)
    except (OSError, ValueError, StopIteration, AttributeError):
        pass
    try:
        host = socket.gethostname()
    except OSError:
        host = "?"
    return {"version": equipo.version or "?", "host": host,
            "so": f"{platform.system()} {platform.release()}", "python": platform.python_version(),
            "cpu": cpu, "nucleos": os.cpu_count(), "ram_mb": ram, "kiosko": kiosko,
            "congelado": bool(getattr(sys, "frozen", False)), "inicio": datetime.fromtimestamp(_t0_wall).isoformat(timespec="seconds")}


def _podar(carpeta):
    archivos = sorted(carpeta.glob("tiempos-*.jsonl"))
    for viejo in archivos[:max(0, len(archivos) - ARCHIVOS_MAX + 1)]:
        try:
            viejo.unlink()
        except OSError:
            pass
