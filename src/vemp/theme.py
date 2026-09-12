"""
Paleta y hoja de estilo del módulo VEMP.

El .qss global de LabSim pinta la barra de la app y poco más (ver
core/base.py: dark.qss es el estilo de la app, no un tema oscuro), así que
un módulo que quiera verse como un equipo y no como un formulario tiene que
traer el suyo. Vive acá, se aplica SOLO a la ventana del VEMP
(`aplicar_estilo(widget)`) y no puede filtrarse al resto de la app.

Las mismas constantes las usan los gráficos de pyqtgraph, que no leen QSS:
por eso la paleta son colores sueltos y no una hoja de estilo y nada más.
"""

# --- Superficies -------------------------------------------------------
FONDO = '#EDF1F5'          # lienzo del módulo
TARJETA = '#FFFFFF'        # panel/card
TARJETA_ALT = '#F6F8FB'    # filas alternas, cabeceras de tabla
BORDE = '#DCE3EB'
BORDE_FUERTE = '#C3CDD9'

# --- Texto -------------------------------------------------------------
TEXTO = '#1F2933'
TEXTO_SUAVE = '#5B6672'
TEXTO_TENUE = '#8A96A3'

# --- Acentos -----------------------------------------------------------
# El morado es el de la barra de LabSim (dark.qss): el módulo tiene que
# verse parte de la misma app.
ACENTO = '#5D1049'
ACENTO_CLARO = '#7C1C63'
ACENTO_SUAVE = '#F3E9F0'

OD = '#C62828'             # oído derecho
OI = '#1565C0'             # oído izquierdo
OD_SUAVE = '#FBE9E9'
OI_SUAVE = '#E8F0FB'

OK = '#1B8A5A'
AVISO = '#D98324'
ALERTA = '#C0392B'

# --- Gráficos ----------------------------------------------------------
GRILLA = '#E6EBF1'
GRILLA_FUERTE = '#CFD8E3'
TRAZO_INACTIVO = '#9AA6B2'
BANDA_NORMATIVA = (93, 16, 73, 38)   # RGBA del relleno normativo


def color_lado(side):
    """side: 0/'OD' -> rojo, 1/'OI' -> azul."""
    return OD if side in (0, 'OD') else OI


def color_lado_suave(side):
    return OD_SUAVE if side in (0, 'OD') else OI_SUAVE


QSS = f"""
QWidget#vempRoot {{
    background: {FONDO};
    color: {TEXTO};
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 9pt;
}}

/* ---- Tarjetas ---------------------------------------------------- */
QFrame[card="true"] {{
    background: {TARJETA};
    border: 1px solid {BORDE};
    border-radius: 10px;
}}
QFrame[card="flat"] {{
    background: {TARJETA_ALT};
    border: 1px solid {BORDE};
    border-radius: 8px;
}}

/* ---- Textos por rol ---------------------------------------------- */
QLabel[role="titulo"] {{
    font-size: 13pt;
    font-weight: 600;
    color: {TEXTO};
}}
QLabel[role="seccion"] {{
    font-size: 7.5pt;
    font-weight: 700;
    color: {TEXTO_TENUE};
    letter-spacing: 1.2px;
}}
QLabel[role="dato"] {{
    font-size: 15pt;
    font-weight: 600;
    color: {TEXTO};
}}
QLabel[role="unidad"] {{
    font-size: 8pt;
    color: {TEXTO_TENUE};
}}
QLabel[role="hint"] {{
    font-size: 8pt;
    color: {TEXTO_SUAVE};
}}
QLabel[role="campo"] {{
    font-size: 8.5pt;
    color: {TEXTO_SUAVE};
}}
QLabel[estado="ok"]    {{ color: {OK}; font-weight: 600; }}
QLabel[estado="aviso"] {{ color: {AVISO}; font-weight: 600; }}
QLabel[estado="alerta"]{{ color: {ALERTA}; font-weight: 600; }}

/* ---- Píldoras (oído, subtipo, estado) ----------------------------- */
QLabel[pill="neutro"] {{
    background: {TARJETA_ALT};
    border: 1px solid {BORDE};
    border-radius: 9px;
    padding: 2px 10px;
    color: {TEXTO_SUAVE};
    font-size: 8pt;
    font-weight: 600;
}}
QLabel[pill="acento"] {{
    background: {ACENTO_SUAVE};
    border: 1px solid {ACENTO};
    border-radius: 9px;
    padding: 2px 10px;
    color: {ACENTO};
    font-size: 8pt;
    font-weight: 600;
}}
QLabel[pill="od"] {{
    background: {OD_SUAVE};
    border: 1px solid {OD};
    border-radius: 9px;
    padding: 2px 10px;
    color: {OD};
    font-size: 8pt;
    font-weight: 700;
}}
QLabel[pill="oi"] {{
    background: {OI_SUAVE};
    border: 1px solid {OI};
    border-radius: 9px;
    padding: 2px 10px;
    color: {OI};
    font-size: 8pt;
    font-weight: 700;
}}

/* ---- Controles ---------------------------------------------------- */
QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {TARJETA};
    border: 1px solid {BORDE_FUERTE};
    border-radius: 6px;
    padding: 3px 6px;
    min-height: 20px;
    selection-background-color: {ACENTO};
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {ACENTO};
}}
QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background: {TARJETA_ALT};
    color: {TEXTO_TENUE};
}}
QComboBox::drop-down {{ border: none; width: 16px; }}
QComboBox QAbstractItemView {{
    background: {TARJETA};
    border: 1px solid {BORDE_FUERTE};
    selection-background-color: {ACENTO_SUAVE};
    selection-color: {ACENTO};
    outline: none;
}}

QPushButton {{
    background: {TARJETA};
    border: 1px solid {BORDE_FUERTE};
    border-radius: 7px;
    padding: 5px 12px;
    color: {TEXTO};
}}
QPushButton:hover {{ border-color: {ACENTO}; color: {ACENTO}; }}
QPushButton:disabled {{ color: {TEXTO_TENUE}; border-color: {BORDE}; }}
QPushButton:checked {{
    background: {ACENTO_SUAVE};
    border-color: {ACENTO};
    color: {ACENTO};
    font-weight: 600;
}}
QPushButton#btnRegistrar {{
    background: {ACENTO};
    border: 1px solid {ACENTO};
    color: #FFFFFF;
    font-weight: 600;
    padding: 7px 12px;
}}
QPushButton#btnRegistrar:hover {{ background: {ACENTO_CLARO}; color: #FFFFFF; }}
QPushButton#btnRegistrar[registrando="true"] {{
    background: {ALERTA};
    border-color: {ALERTA};
}}
QPushButton#btnDetener {{ padding: 7px 12px; }}
QPushButton#btnEscala {{
    padding: 0px;
    font-weight: 700;
    color: {TEXTO_SUAVE};
}}

/* ---- Pestañas ----------------------------------------------------- */
QTabWidget::pane {{
    border: 1px solid {BORDE};
    border-radius: 10px;
    background: {TARJETA};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    border: none;
    padding: 6px 16px;
    margin-right: 4px;
    color: {TEXTO_SUAVE};
    font-weight: 600;
    font-size: 8.5pt;
}}
QTabBar::tab:selected {{
    color: {ACENTO};
    border-bottom: 2px solid {ACENTO};
}}
QTabBar::tab:hover {{ color: {ACENTO}; }}

/* ---- Tablas ------------------------------------------------------- */
QTableWidget {{
    background: {TARJETA};
    border: none;
    gridline-color: {GRILLA};
    selection-background-color: {ACENTO_SUAVE};
    selection-color: {TEXTO};
    font-size: 8.5pt;
}}
QHeaderView::section {{
    background: {TARJETA_ALT};
    border: none;
    border-bottom: 1px solid {BORDE};
    padding: 5px 4px;
    color: {TEXTO_TENUE};
    font-size: 7.5pt;
    font-weight: 700;
}}
QTableWidget::item {{ padding: 3px 4px; }}

/* ---- Texto largo -------------------------------------------------- */
QTextEdit {{
    background: {TARJETA};
    border: 1px solid {BORDE_FUERTE};
    border-radius: 8px;
    padding: 6px;
    selection-background-color: {ACENTO_SUAVE};
}}
QTextEdit:focus {{ border-color: {ACENTO}; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDE_FUERTE}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background: {BORDE_FUERTE}; border-radius: 5px; min-width: 30px;
}}
"""


def aplicar_estilo(widget):
    """Aplica el QSS del módulo a `widget` y a todo lo que cuelgue de él."""
    widget.setObjectName('vempRoot')
    widget.setStyleSheet(QSS)


def repintar(widget):
    """Vuelve a resolver el QSS de un widget cuyo `property` cambió.

    Qt no reevalúa los selectores por propiedad solo: sin esto, marcar
    `estado="alerta"` en una etiqueta ya mostrada no cambia nada.
    """
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
