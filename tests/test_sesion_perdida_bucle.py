"""Sesión perdida (401) con un diálogo o menú abierto (main._sesion_perdida).

hilos.avisar reparte el aviso en cualquier bucle de eventos, también
dentro del exec() del diálogo de un módulo. El logout de ahí destruía el
módulo con su código todavía esperando ese diálogo: exec() volvía con 0 y
la línea siguiente daba "already deleted" (2026-11-05). Ahora se cierran
diálogos y menús y el aviso espera al bucle principal.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QMenu, QWidget  # noqa: E402

import main  # noqa: E402

APP = QApplication.instance()


class VentanaFalsa(QWidget):
    """Lo justo de MainWindow para correr su _sesion_perdida de verdad."""
    _sesion_perdida = main.MainWindow._sesion_perdida
    _esperar_bucle_principal = main.MainWindow._esperar_bucle_principal
    _sesion_perdida_diferida = main.MainWindow._sesion_perdida_diferida

    def __init__(self, modulo):
        super().__init__()
        self.data_login = {"user": "alumno"}
        self._avisando_sesion = False
        self._sesion_pendiente = None
        self.subw = None
        self.modulo = modulo
        self.traza = []

    def logout(self):
        self.traza.append("logout")
        self.data_login = None
        self.modulo.deleteLater()


def _aceptar_el_aviso():
    """El QMessageBox de sesión vencida se acepta solo."""
    def mirar():
        caja = QApplication.activeModalWidget()
        if caja is not None and caja.windowTitle() in ("Sesión vencida", "Cuenta bloqueada"):
            caja.accept()
        else:
            QTimer.singleShot(20, mirar)
    QTimer.singleShot(20, mirar)


def _correr(accion_del_modulo):
    modulo = QWidget()
    modulo.show()
    ventana = VentanaFalsa(modulo)
    traza = ventana.traza
    _aceptar_el_aviso()

    def empezar():
        accion_del_modulo(modulo, ventana, traza)
    QTimer.singleShot(0, empezar)
    QTimer.singleShot(1500, APP.quit)
    APP.exec()
    return traza


def test_logout_espera_a_que_el_dialogo_del_modulo_termine():
    def accion(modulo, ventana, traza):
        dlg = QDialog(modulo)
        # Llega el 401 con el diálogo del módulo abierto.
        QTimer.singleShot(50, lambda: ventana._sesion_perdida("vencida"))
        dlg.exec()
        try:
            modulo.setWindowTitle("sigo")
            traza.append("módulo vivo después del exec")
        except RuntimeError:
            traza.append("módulo destruido durante el exec")
    traza = _correr(accion)
    assert traza == ["módulo vivo después del exec", "logout"], traza


def test_logout_espera_a_que_el_menu_se_cierre():
    def accion(modulo, ventana, traza):
        menu = QMenu(modulo)
        menu.addAction("algo")
        QTimer.singleShot(50, lambda: ventana._sesion_perdida("vencida"))
        menu.exec(modulo.mapToGlobal(modulo.rect().center()))
        try:
            modulo.setWindowTitle("sigo")
            traza.append("módulo vivo después del menú")
        except RuntimeError:
            traza.append("módulo destruido durante el menú")
    traza = _correr(accion)
    assert traza == ["módulo vivo después del menú", "logout"], traza


def test_sin_nada_abierto_el_logout_es_inmediato():
    def accion(modulo, ventana, traza):
        ventana._sesion_perdida("vencida")
        traza.append("después del aviso")
    traza = _correr(accion)
    assert traza == ["logout", "después del aviso"], traza


def test_varios_401_seguidos_avisan_una_vez():
    def accion(modulo, ventana, traza):
        dlg = QDialog(modulo)
        for ms in (30, 40, 50):
            QTimer.singleShot(ms, lambda: ventana._sesion_perdida("vencida"))
        QTimer.singleShot(45, dlg.reject)
        dlg.exec()
    traza = _correr(accion)
    assert traza == ["logout"], traza


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
    sys.exit(1 if fallas else 0)
