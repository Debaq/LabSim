"""Estilo compartido de gráficos pyqtgraph para el módulo OAE.

pyqtgraph guarda foreground/background como opciones de configuración
GLOBALES (pg.setConfigOption), no por widget. Otro módulo ya instanciado
en la misma app (impedanciometria, ver Z*screen.py) las deja en
foreground='w' porque su fondo es oscuro -- si no fijamos el pen de cada
eje acá de forma explícita, nuestros gráficos (fondo blanco) heredan ese
blanco y el grid queda invisible (blanco sobre blanco).
"""
import pyqtgraph as pg

GRID_ALPHA = 0.4


def style_plot(plot_item, grid_alpha: float = GRID_ALPHA) -> None:
    """Fuerza grid visible + ejes negros, sin depender de la config global."""
    plot_item.showGrid(x=True, y=True, alpha=grid_alpha)
    for axis_name in ("left", "bottom"):
        axis = plot_item.getAxis(axis_name)
        axis.setPen(pg.mkPen("k"))
        axis.setTextPen("k")


def black_title(text: str) -> str:
    """addPlot(title=...) renderiza HTML -- forzar color acá evita heredar
    el foreground global blanco en el título."""
    return f"<span style='color:#000000'>{text}</span>"
