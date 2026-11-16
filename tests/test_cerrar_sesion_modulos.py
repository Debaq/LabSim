"""
Cerrar sesión suelta el frame de TODOS los módulos (main.MainWindow
._close_sub_windows), no solo los de audiología.

Ticket #64: tras atender en el PSG y cerrar sesión, subw_psg seguía apuntando
al frame ya destruido; el siguiente ingreso le conectaba visibility_changed
en load_sub_windows y reventaba con "Signal source has been deleted"
("Se inició sesión, pero no se pudo cargar la información...").
"""

import os
import re
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import main  # noqa: E402

FUENTE = os.path.join(os.path.dirname(__file__), "..", "src", "main.py")


class _Storage:
    def length(self, _x):
        return []


class _Main:
    """Lo que _close_sub_windows le pide a la ventana."""
    _ATTRS_MODULOS = main.MainWindow._ATTRS_MODULOS

    def __init__(self):
        self.apps = {"LOGIN": (None, None, 0)}
        self.modules = _Storage()
        self.subw = {"LOGIN": object()}


def test_cerrar_sesion_suelta_los_modulos_nasales():
    m = _Main()
    for attr in main.MainWindow._ATTRS_MODULOS:
        setattr(m, attr, object())
    main.MainWindow._close_sub_windows(m)
    quedan = [a for a in main.MainWindow._ATTRS_MODULOS if hasattr(m, a)]
    assert quedan == []


def test_todo_modulo_que_se_arma_esta_en_la_lista():
    """Un módulo nuevo en load_sub_windows sin entrar en _ATTRS_MODULOS
    repetiría el ticket #64."""
    with open(FUENTE, encoding="utf-8") as f:
        fuente = f.read()
    armados = set(re.findall(r'_modulo_diferido\("\w+", "(subw_\w+)"', fuente))
    armados |= set(main.MainWindow._ATTRS_EXAMEN)
    assert armados, "no se encontraron módulos en load_sub_windows"
    assert armados <= set(main.MainWindow._ATTRS_MODULOS), armados - set(main.MainWindow._ATTRS_MODULOS)


if __name__ == "__main__":
    test_cerrar_sesion_suelta_los_modulos_nasales()
    test_todo_modulo_que_se_arma_esta_en_la_lista()
    print("ok")
