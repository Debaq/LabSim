"""
Otoscopía y diapasones en una sola ventana a pantalla completa, con un solo
botón en el box (2026-11-06; antes eran dos ventanas chicas, OT y AC).

Cada parte se muestra si el curso tiene su módulo (OT, AC en
course_modules): con los dos, una pestaña para cada uno; con uno, solo ese,
sin pestañas. El botón es el de "AC" (ui_helpers.chargeBtnsArea lo muestra
si el curso tiene cualquiera de los dos, con los dos íconos); el layout del
servidor no cambia, así las versiones anteriores de la app siguen con sus
dos botones.

Otoscopia y Acumetria siguen siendo los mismos módulos: main.py los carga
con el caso (la_super) y sube sus informes igual que antes.
"""
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from core import iconos, tema

EXTRA_QSS = f"""
QTabWidget#otac::pane {{ border: none; background: transparent; top: 0px; }}
QTabWidget#otac > QTabBar::tab {{
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 8px 20px;
    margin-right: 6px;
    font-size: 10pt;
    font-weight: 700;
    color: {tema.TEXTO_TENUE};
}}
QTabWidget#otac > QTabBar::tab:selected {{ color: {tema.ACENTO}; border-bottom-color: {tema.ACENTO}; }}
QTabWidget#otac > QTabBar::tab:hover:!selected {{ color: {tema.TEXTO_SUAVE}; }}
"""


class OtoscopiaAcumetriaWindow(QWidget):

    def __init__(self, otoscopia, acumetria, con_otoscopia=True, con_acumetria=True):
        super().__init__()
        tema.aplicar_estilo(self, EXTRA_QSS)
        self.otoscopia = otoscopia
        self.acumetria = acumetria
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        partes = []
        if con_otoscopia:
            partes.append((otoscopia, "otoscopio", "Otoscopía"))
        if con_acumetria:
            partes.append((acumetria, "diapason", "Diapasones"))
        if not partes:   # no debería pasar: el botón no se muestra
            partes.append((otoscopia, "otoscopio", "Otoscopía"))
        self.tabs = None
        if len(partes) == 1:
            raiz.addWidget(partes[0][0])
        else:
            self.tabs = QTabWidget()
            self.tabs.setObjectName("otac")
            for widget, icono, texto in partes:
                self.tabs.addTab(widget, iconos.icono(icono, tema.ACENTO, 18), texto)
            raiz.addWidget(self.tabs)
        # Lo que no se muestra igual existe (main lo carga con el caso), sin
        # quedar suelto como ventana propia
        for widget in (otoscopia, acumetria):
            if widget.parent() is None:
                widget.setParent(self)
                widget.hide()

    def hideEvent(self, event):
        super().hideEvent(event)
        for widget in (self.otoscopia, self.acumetria):
            callar = getattr(widget, "callar", None)
            if callar is not None:
                callar()
