"""Borrar widgets con deleteLater dejando rastro en el registro.

El 2026-10-30 (labsim3, ticket 30) la app se cayó dentro de Qt al borrar
un árbol de widgets pedido con deleteLater: el volcado de faulthandler no
tiene ninguna línea de Python (el borrado corre después, en el loop) y no
quedó cómo saber qué ventana era. Cada borrado pedido desde acá anota antes
una línea con qué se borra y desde dónde; print() hace flush en cada línea
(core/Logger.py), así que si el proceso revienta, la última "borrar luego"
del registro dice qué se estaba destruyendo.
"""
from collections import Counter


def _nombre(w) -> str:
    nombre = type(w).__name__
    # QMdiSubWindow, QScrollArea, QDockWidget: lo que importa es lo de adentro
    # (y en las subventanas del MDI, el módulo que carga su marco: .obj).
    interior = getattr(w, "widget", None)
    if callable(interior):
        try:
            x = interior()
        except (RuntimeError, TypeError):
            x = None
        if x is not None:
            nombre += f"[{type(getattr(x, 'obj', None) or x).__name__}]"
    try:
        if w.objectName():
            nombre += f" '{w.objectName()}'"
    except RuntimeError:
        pass
    return nombre


def describir(widgets) -> str:
    cuenta = Counter(_nombre(w) for w in widgets)
    return ", ".join(n if c == 1 else f"{n} ×{c}" for n, c in cuenta.items())


def borrar_luego(widgets, donde: str) -> None:
    """deleteLater de cada widget, con una línea en el registro antes."""
    widgets = [w for w in widgets if w is not None]
    if not widgets:
        return
    try:
        print(f"borrar luego ({donde}): {describir(widgets)}")
    except RuntimeError:
        print(f"borrar luego ({donde}): {len(widgets)} widgets")
    for w in widgets:
        w.deleteLater()
