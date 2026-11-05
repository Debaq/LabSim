"""Mouse de zurdos en el servidor X (core/mouse_zurdo.py, MapeoX11).

En los kioskos (X11 + Openbox) los botones se invierten en el servidor X con
XSetPointerMapping: LabSim no toca eventos. Dos niveles de prueba:

- la lógica, con un servidor X de mentira;
- de punta a punta, en un Xvfb PROPIO (nunca en la pantalla de quien corre
  la prueba: le invertiría el mouse) con LabSim en xcb y un clic "físico"
  hecho con XTest.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from core import mouse_zurdo  # noqa: E402
from core.preferencias import preferencias  # noqa: E402


class XFalso:
    """Un servidor X de mentira: el mapeo de 5 botones y, si se pide, unas
    cuantas respuestas 'ocupado' (un botón apretado)."""

    def __init__(self, mapa=(1, 2, 3, 4, 5), ocupado=0):
        self.mapa = list(mapa)
        self.ocupado = ocupado
        self.cambios = 0

    def leer(self):
        return list(self.mapa)

    def invertido(self):
        return self.mapa[0] == 3 and self.mapa[2] == 1

    def poner(self, invertir):
        if self.ocupado:
            self.ocupado -= 1
            return 'ocupado'
        self.mapa[0], self.mapa[2] = (3, 1) if invertir else (1, 3)
        self.cambios += 1
        return 'ok'


def _con_x(x, kiosko, zurdo):
    os.environ["LABSIM_KIOSKO"] = "1" if kiosko else "0"
    mouse_zurdo._x11 = x
    mouse_zurdo._x11_invertido = False
    preferencias().cargar({"mouse_zurdo": zurdo})
    mouse_zurdo.aplicar()


def _limpiar():
    os.environ["LABSIM_KIOSKO"] = "0"
    preferencias().cargar({})
    mouse_zurdo._sacar_filtro()
    mouse_zurdo._x11 = None
    mouse_zurdo._x11_invertido = False


def test_kiosko_zurdo_invierte_en_x_sin_filtro():
    x = XFalso()
    _con_x(x, kiosko=True, zurdo=True)
    assert x.mapa == [3, 2, 1, 4, 5]
    assert mouse_zurdo._filtro is None, "con X no hace falta el filtro"
    assert mouse_zurdo.activo()
    _limpiar()


def test_cerrar_sesion_vuelve_a_lo_normal():
    x = XFalso()
    _con_x(x, kiosko=True, zurdo=True)
    preferencias().limpiar()          # lo que hace logout()
    mouse_zurdo.aplicar()             # en la app lo llama la señal (conectar())
    assert x.mapa == [1, 2, 3, 4, 5]
    assert not mouse_zurdo.activo()
    _limpiar()


def test_al_salir_de_labsim_vuelve_a_lo_normal():
    x = XFalso()
    _con_x(x, kiosko=True, zurdo=True)
    mouse_zurdo._al_salir()
    assert x.mapa == [1, 2, 3, 4, 5]
    _limpiar()


def test_fuera_del_kiosko_no_toca_el_servidor_x():
    """En un computador personal un zurdo ya lo tiene invertido en su
    sistema: LabSim no lo deshace."""
    x = XFalso(mapa=(3, 2, 1, 4, 5))
    _con_x(x, kiosko=False, zurdo=False)
    mouse_zurdo._al_salir()
    assert x.mapa == [3, 2, 1, 4, 5] and x.cambios == 0
    _limpiar()


def test_tras_una_caida_lo_corrige_al_abrir():
    """LabSim se cayó con un zurdo: al volver a abrir (sin nadie logueado)
    los botones vuelven a lo normal."""
    x = XFalso(mapa=(3, 2, 1, 4, 5))
    _con_x(x, kiosko=True, zurdo=False)
    assert x.mapa == [1, 2, 3, 4, 5]
    _limpiar()


def test_con_un_boton_apretado_reintenta():
    from PySide6.QtTest import QTest
    x = XFalso(ocupado=3)
    _con_x(x, kiosko=True, zurdo=True)
    assert not x.invertido()
    QTest.qWait(mouse_zurdo._REINTENTO_MS * 5)
    assert x.invertido(), x.mapa
    _limpiar()


def test_sin_cambios_no_vuelve_a_mandar_el_mapeo():
    x = XFalso()
    _con_x(x, kiosko=True, zurdo=True)
    mouse_zurdo.aplicar()
    mouse_zurdo.aplicar()
    assert x.cambios == 1
    _limpiar()


# --- De punta a punta, en un Xvfb propio -------------------------------------

HIJO = r'''
import os, sys, ctypes, time
sys.path.insert(0, sys.argv[1])
os.environ["LABSIM_KIOSKO"] = "1"
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtTest import QTest
app = QApplication([])
assert QApplication.platformName() == "xcb", QApplication.platformName()
from core import mouse_zurdo
from core.preferencias import preferencias
mouse_zurdo.conectar()
inicial = mouse_zurdo._mapeo_x11().leer()[:3]
preferencias().cargar({"mouse_zurdo": True})
zurdo = mouse_zurdo._mapeo_x11().leer()[:3]

b = QPushButton("x"); b.resize(200, 100); b.move(0, 0); b.show()
QTest.qWaitForWindowExposed(b); QTest.qWait(200)
clics = []
b.clicked.connect(lambda: clics.append(1))
xt = ctypes.CDLL("libXtst.so.6"); x = ctypes.CDLL("libX11.so.6")
x.XOpenDisplay.restype = ctypes.c_void_p; x.XOpenDisplay.argtypes = [ctypes.c_char_p]
dpy = x.XOpenDisplay(None)
xt.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
xt.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
x.XFlush.argtypes = [ctypes.c_void_p]
c = b.mapToGlobal(b.rect().center())
def clic_fisico(boton):
    xt.XTestFakeMotionEvent(dpy, -1, c.x(), c.y(), 0)
    xt.XTestFakeButtonEvent(dpy, boton, 1, 0); xt.XTestFakeButtonEvent(dpy, boton, 0, 0)
    x.XFlush(dpy); QTest.qWait(300)
clic_fisico(1); con_izquierdo = len(clics)
clic_fisico(3); con_derecho = len(clics) - con_izquierdo
preferencias().cargar({})
final = mouse_zurdo._mapeo_x11().leer()[:3]
print("RESULTADO", inicial, zurdo, con_izquierdo, con_derecho, final, flush=True)
'''


def test_de_punta_a_punta_en_xvfb():
    if not shutil.which("Xvfb"):
        print("     (sin Xvfb: no se prueba de punta a punta)")
        return
    pantalla = ":%d" % (90 + os.getpid() % 9)
    xvfb = subprocess.Popen(["Xvfb", pantalla, "-screen", "0", "1024x768x24", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.0)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(HIJO)
            script = f.name
        entorno = dict(os.environ, DISPLAY=pantalla, QT_QPA_PLATFORM="xcb")
        entorno.pop("WAYLAND_DISPLAY", None)
        r = subprocess.run([sys.executable, script, os.path.join(RAIZ, "src")],
                           env=entorno, capture_output=True, text=True, timeout=90)
        os.unlink(script)
        linea = next((l for l in r.stdout.splitlines() if "RESULTADO" in l), None)
        assert linea, r.stdout[-2000:] + r.stderr[-2000:]
        print("     " + linea.split("RESULTADO", 1)[1].strip())
        # mapeo al abrir, con el zurdo, clics con el izquierdo físico, con
        # el derecho físico, y mapeo al cerrar su sesión
        partes = linea.split("RESULTADO", 1)[1].strip()
        assert partes == "[1, 2, 3] [3, 2, 1] 0 1 [1, 2, 3]", partes
    finally:
        xvfb.terminate()
        xvfb.wait(5)


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    _limpiar()
    sys.exit(1 if fallas else 0)
