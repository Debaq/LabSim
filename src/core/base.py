#from fbs_runtime.application_context.PySide6 import ApplicationContext

#context = ApplicationContext()

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# Paleta clara de LabSim, rol por rol. Es la paleta con la que se dibujaron
# los .ui y contra la que se escribió dark.qss (que es el estilo de la app
# --barra morada--, NO un tema oscuro): el qss pinta la barra y poco más, así
# que todo lo demás lo pone la paleta del sistema. Con Windows en modo
# oscuro eso deja texto oscuro sobre fondo oscuro y la ventana no se lee.
PALETA_CLARA = {
    QPalette.Window: "#efefef",
    QPalette.WindowText: "#000000",
    QPalette.Base: "#ffffff",
    QPalette.AlternateBase: "#f7f7f7",
    QPalette.ToolTipBase: "#ffffdc",
    QPalette.ToolTipText: "#000000",
    QPalette.Text: "#000000",
    QPalette.PlaceholderText: "#808080",
    QPalette.Button: "#efefef",
    QPalette.ButtonText: "#000000",
    QPalette.BrightText: "#ff0000",
    QPalette.Link: "#0000ff",
    QPalette.Highlight: "#308cc6",
    QPalette.HighlightedText: "#ffffff",
}

# Lo que se ve deshabilitado tiene que seguir viéndose: gris sobre claro.
PALETA_CLARA_DESHABILITADA = {
    QPalette.WindowText: "#787878",
    QPalette.Text: "#787878",
    QPalette.ButtonText: "#787878",
    QPalette.HighlightedText: "#787878",
}


def paleta_clara() -> QPalette:
    """La paleta de PALETA_CLARA, armada de cero (no derivada de la del
    sistema: si esa viene oscura, los roles que no se pisen quedan oscuros)."""
    pal = QPalette()
    for rol, color in PALETA_CLARA.items():
        pal.setColor(rol, QColor(color))
    for rol, color in PALETA_CLARA_DESHABILITADA.items():
        pal.setColor(QPalette.Disabled, rol, QColor(color))
    return pal


def es_paleta_oscura(pal: QPalette) -> bool:
    """El fondo de ventana es más oscuro que el texto que va encima."""
    return pal.window().color().lightness() < pal.windowText().color().lightness()


def aplicar_tema_claro(app) -> bool:
    """Deja la app en tema claro si el sistema la arrancó en oscuro.

    Devuelve True si hubo que pisar la paleta. Se fuerza también el estilo
    Fusion: el estilo nativo de Windows dibuja partes del control (fondos de
    combos, headers, scrollbars) con los colores del tema del SO y no con la
    paleta, así que cambiar la paleta sola deja la mitad oscura igual.
    """
    if not es_paleta_oscura(app.palette()):
        return False
    app.setStyle("Fusion")
    app.setPalette(paleta_clara())
    return True


class ApplicationContext():

    def __init__(self) -> None:
        # Tres vías, porque atacan momentos distintos: el argumento de
        # plataforma evita que el plugin de Windows siga el tema del sistema
        # desde el arranque; setColorScheme fija el esquema con la app ya
        # creada (Qt 6.8+, no existe antes); y aplicar_tema_claro pisa la
        # paleta si igual llegó oscura, que es lo único que no depende de la
        # versión de Qt ni del plugin.
        args = ["LabSim"]
        if sys.platform.startswith("win"):
            args += ["-platform", "windows:darkmode=0"]
        self.app = QApplication(args)

        hints = self.app.styleHints()
        if hasattr(hints, "setColorScheme"):
            hints.setColorScheme(Qt.ColorScheme.Light)
        aplicar_tema_claro(self.app)

    def get_resource(self, path):
        return f"resources/{path}"


context = ApplicationContext()
