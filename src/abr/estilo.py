"""Hoja de estilo propia del módulo ABR, encima del tema común (core/tema.py).

El ABR viene de un .ui de Designer: los widgets no traen propiedades `card` o
`role`, así que los selectores van por nombre de objeto y por clase.
"""
from core.tema import (ACENTO, BORDE, BORDE_FUERTE, FONDO, TARJETA, TARJETA_ALT,
                       TEXTO, TEXTO_SUAVE, TEXTO_TENUE)

QSS_ABR = f"""
QMenuBar {{ background: {FONDO}; color: {TEXTO_SUAVE}; }}
QMenuBar::item:selected {{ background: {TARJETA}; color: {ACENTO}; }}

QDockWidget {{ color: {TEXTO_TENUE}; font-weight: 700; font-size: 7.5pt; }}
QDockWidget::title {{
    background: transparent;
    padding: 6px 8px 2px 8px;
    text-align: left;
}}

QMainWindow::separator {{ background: transparent; width: 6px; height: 6px; }}

QCheckBox {{ color: {TEXTO}; spacing: 6px; }}
QCheckBox:disabled {{ color: {TEXTO_TENUE}; }}
QCheckBox::indicator {{
    width: 14px; height: 14px; border-radius: 4px;
    border: 1px solid {BORDE_FUERTE}; background: {TARJETA};
}}
QCheckBox::indicator:checked {{ background: {ACENTO}; border-color: {ACENTO}; }}

QWidget#dock_parameter_contents, QWidget#dock_values_contents, QWidget#dock_test_contents {{
    background: {TARJETA};
    border: 1px solid {BORDE};
    border-radius: 10px;
}}

QFrame#verticalFrame {{ background: transparent; border: none; }}
QFrame#verticalFrame QPushButton {{ padding: 3px 0px; min-width: 26px; font-weight: 700; }}
"""

# Contenedores de los docks que se pintan como tarjeta: un QWidget plano no
# dibuja fondo ni borde de QSS sin WA_StyledBackground.
TARJETAS = ("dock_parameter_contents", "dock_values_contents", "dock_test_contents")
