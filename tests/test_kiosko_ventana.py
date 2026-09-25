"""Modo laboratorio (LABSIM_KIOSKO=1) en la ventana principal: pantalla
completa, sin botones de ventana, y el alumno no puede cerrar la app. Un
docente logueado sí (es la salida del personal)."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["LABSIM_KIOSKO"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtGui import QCloseEvent  # noqa: E402

import main  # noqa: E402

APP = main.context.app


def _ventana():
    w = main.MainWindow()
    w.showFullScreen()
    APP.processEvents()
    return w


def _cierra(w):
    ev = QCloseEvent()
    w.closeEvent(ev)
    return ev.isAccepted()


def test_pantalla_completa_y_sin_botones():
    w = _ventana()
    assert w.isFullScreen()
    assert not w.btn_min.isVisibleTo(w) and not w.btn_max.isVisibleTo(w)
    assert not w.btn_salir.isVisibleTo(w)


def test_el_alumno_no_cierra_la_app():
    w = _ventana()
    w.data_login = {"user": "al", "permission": 444}
    w._aplicar_kiosko()
    assert not _cierra(w)
    assert not w.btn_salir.isVisibleTo(w)


def test_un_docente_si():
    w = _ventana()
    w.data_login = {"user": "doc", "permission": 555}
    w._aplicar_kiosko()
    assert w.btn_salir.isVisibleTo(w)
    assert w._salida_permitida()


def test_si_la_sacan_de_pantalla_completa_vuelve():
    w = _ventana()
    w.showNormal()
    for _ in range(5):
        APP.processEvents()
    assert w.isFullScreen()


def test_al_apagar_el_equipo_cierra_aunque_sea_alumno():
    w = _ventana()
    w.data_login = {"user": "al", "permission": 444}
    w._aplicar_kiosko()
    w.cerrar_por_apagado()
    assert not w.isVisible()


def test_sigterm_llega_al_cierre_una_sola_vez():
    import signal
    import time
    from core import kiosko
    plazo = kiosko.PLAZO_APAGADO_S
    kiosko.PLAZO_APAGADO_S = 3600  # que la guardia no mate al test
    llamadas = []
    try:
        despertador = kiosko.atender_apagado(lambda: llamadas.append(1))
        assert despertador is not None
        os.kill(os.getpid(), signal.SIGTERM)
        os.kill(os.getpid(), signal.SIGTERM)
        fin = time.monotonic() + 2
        while not llamadas and time.monotonic() < fin:
            APP.processEvents()
        APP.processEvents()
        assert llamadas == [1]
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        kiosko.PLAZO_APAGADO_S = plazo


def test_en_windows_no_se_atiende_sigterm():
    from core import kiosko
    plataforma = sys.platform
    sys.platform = "win32"
    try:
        assert kiosko.atender_apagado(lambda: None) is None
    finally:
        sys.platform = plataforma


def test_fuera_del_laboratorio_todo_normal():
    os.environ["LABSIM_KIOSKO"] = "0"
    try:
        w = main.MainWindow()
        assert w.btn_salir.isVisibleTo(w) or not w.isVisible()
        assert w._salida_permitida()
    finally:
        os.environ["LABSIM_KIOSKO"] = "1"


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
    os._exit(1 if fallas else 0)
