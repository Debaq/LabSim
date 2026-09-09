"""
Tema claro forzado (core/base.py).

En Windows con el modo oscuro del sistema, la ventana salía texto oscuro
sobre fondo oscuro: dark.qss es el estilo de LabSim (la barra morada), no un
tema oscuro, así que todo lo que el qss no pinta lo pone la paleta del
sistema. Acá se prueba lo único que no depende del plugin de Qt: que una
paleta oscura se detecte y se reemplace por una clara legible.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtGui import QColor, QPalette

from core import base
from core.base import context  # crea la QApplication


def paleta_oscura():
    """Lo que entrega Windows en modo oscuro: fondo casi negro, texto claro."""
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor("#202020"))
    pal.setColor(QPalette.WindowText, QColor("#ffffff"))
    pal.setColor(QPalette.Base, QColor("#2b2b2b"))
    pal.setColor(QPalette.Text, QColor("#ffffff"))
    pal.setColor(QPalette.Button, QColor("#2b2b2b"))
    pal.setColor(QPalette.ButtonText, QColor("#ffffff"))
    return pal


def con_paleta(pal):
    """Corre aplicar_tema_claro con esa paleta puesta y restaura al salir."""
    original_pal = context.app.palette()
    original_style = context.app.style().objectName()
    context.app.setPalette(pal)
    try:
        cambio = base.aplicar_tema_claro(context.app)
        return cambio, context.app.palette()
    finally:
        context.app.setStyle(original_style)
        context.app.setPalette(original_pal)


def test_detecta_la_paleta_oscura():
    assert base.es_paleta_oscura(paleta_oscura())
    assert not base.es_paleta_oscura(base.paleta_clara())


def test_una_paleta_oscura_se_reemplaza_por_la_clara():
    cambio, pal = con_paleta(paleta_oscura())
    assert cambio
    assert pal.window().color().name() == "#efefef"
    assert pal.windowText().color().name() == "#000000"
    assert pal.base().color().name() == "#ffffff"


def test_una_paleta_clara_no_se_toca():
    """En Linux con tema claro la app tiene que quedar como estaba: forzar
    Fusion ahí cambiaría el aspecto sin ningún motivo."""
    cambio, _ = con_paleta(base.paleta_clara())
    assert not cambio


def test_todo_lo_escrito_se_lee_sobre_su_fondo():
    """Ningún par texto/fondo de la paleta clara queda con contraste bajo --
    que es exactamente el síntoma que esto viene a arreglar."""
    pal = base.paleta_clara()
    pares = [
        (pal.windowText().color(), pal.window().color()),
        (pal.text().color(), pal.base().color()),
        (pal.buttonText().color(), pal.button().color()),
        (pal.highlightedText().color(), pal.highlight().color()),
        (pal.toolTipText().color(), pal.toolTipBase().color()),
        (pal.color(QPalette.Disabled, QPalette.WindowText), pal.window().color()),
        (pal.color(QPalette.Disabled, QPalette.Text), pal.base().color()),
    ]
    for texto, fondo in pares:
        assert abs(texto.lightness() - fondo.lightness()) > 60, (
            f"{texto.name()} sobre {fondo.name()} no se lee"
        )


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
