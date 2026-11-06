"""Ingreso con código (2026-11-06): con el usuario de un ingreso anterior
escrito, la página del código mandaba ese usuario sin contraseña y decía
"El código tiene 6 dígitos"; y un código pegado con espacios quedaba vacío.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from auth.login import MainLogin  # noqa: E402


def _ventana():
    l = MainLogin()
    l.enviados = []
    l._start_login = lambda n, p: l.enviados.append((n, p))
    return l


def test_el_codigo_sale_aunque_haya_un_usuario_escrito():
    l = _ventana()
    l.Le_name.setText("admin")              # quedó del ingreso del docente
    l.mostrar_pagina(l.PAGINA_CODIGO)
    l.Le_codigo.insert("519988")
    assert l.enviados == [("", "519988")], l.enviados


def test_un_codigo_pegado_con_espacios_o_guiones_sirve():
    for pegado in (" 519988", "519 988", "51-99-88\n"):
        l = _ventana()
        l.Le_codigo.insert(pegado)
        assert l.enviados == [("", "519988")], (pegado, l.enviados)


def test_incompleto_no_se_manda():
    l = _ventana()
    l.Le_codigo.insert("12345")
    assert l.enviados == []


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
