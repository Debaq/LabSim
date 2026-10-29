"""
Paleta y hoja de estilo común de los módulos de LabSim (nació en el VEMP).

El .qss global de LabSim pinta la barra de la app y poco más (ver
core/base.py: dark.qss es el estilo de la app, no un tema oscuro), así que
un módulo que quiera verse como un equipo y no como un formulario tiene que
traer el suyo. Vive acá, se aplica SOLO a la ventana del módulo
(`aplicar_estilo(widget, extra)`) y no puede filtrarse al resto de la app.

Las mismas constantes las usan los gráficos de pyqtgraph, que no leen QSS:
por eso la paleta son colores sueltos y no una hoja de estilo y nada más.
"""

# --- Superficies -------------------------------------------------------
FONDO = '#ECE6EC'          # lienzo del módulo
LIENZO_APP = '#E6DFE5'     # fondo del MDI y barras de la app (más oscuro que FONDO)
TARJETA = '#FFFFFF'        # panel/card
TARJETA_ALT = '#FAF8FA'    # filas alternas, cabeceras de tabla
BORDE = '#E4DCE3'
BORDE_FUERTE = '#D2C7D1'

# --- Texto -------------------------------------------------------------
TEXTO = '#2A2229'
TEXTO_SUAVE = '#5E5360'
TEXTO_TENUE = '#8F8391'

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

# Comentario del docente (notas amarillas sobre la conversación, la evolución...).
NOTA_DOCENTE = '#FFF9EA'
NOTA_DOCENTE_BORDE = '#F3DFA0'
NOTA_DOCENTE_TEXTO = '#A3822F'

# --- Gráficos ----------------------------------------------------------
GRILLA = '#EAE4EA'
GRILLA_FUERTE = '#D9CFD8'
TRAZO_INACTIVO = '#A89DAA'
OD_INACTIVO = '#D99A9A'      # curva de OD no seleccionada
OI_INACTIVO = '#93B4DD'      # curva de OI no seleccionada
BANDA_NORMATIVA = (93, 16, 73, 38)   # RGBA del relleno normativo


def color_lado(side):
    """side: 0/'OD' -> rojo, 1/'OI' -> azul."""
    return OD if side in (0, 'OD') else OI


def color_lado_suave(side):
    return OD_SUAVE if side in (0, 'OD') else OI_SUAVE


QSS = f"""
QWidget#labsimRoot {{
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


def _flecha(ruta, hacia_abajo, color):
    """Dibuja un chevron en un PNG (el QSS solo acepta imágenes de archivo)."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QColor, QImage, QPainter, QPen
    img = QImage(32, 32, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 4.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    y0, y1 = (11, 21) if hacia_abajo else (21, 11)
    p.drawPolyline([QPointF(7, y0), QPointF(16, y1), QPointF(25, y0)])
    p.end()
    img.save(str(ruta))


_flechas_qss = None


def qss_flechas():
    """Flechas de los spinbox y los combos. Los PNG se dibujan una vez en la
    carpeta de datos (core/rutas.py) y el QSS los apunta por ruta."""
    global _flechas_qss
    if _flechas_qss is None:
        from core import rutas
        carpeta = rutas.carpeta("tema")
        rutas_png = {}
        for nombre, abajo, color in (("abajo", True, TEXTO_SUAVE), ("arriba", False, TEXTO_SUAVE),
                                     ("abajo_off", True, BORDE_FUERTE), ("arriba_off", False, BORDE_FUERTE)):
            ruta = carpeta / f"flecha_{nombre}_{color.lstrip('#')}.png"
            if not ruta.exists():
                _flecha(ruta, abajo, color)
            rutas_png[nombre] = ruta.as_posix()
        r = rutas_png
        _flechas_qss = f"""
QSpinBox, QDoubleSpinBox {{ padding-right: 20px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: padding; subcontrol-position: top right;
    width: 18px; border-left: 1px solid {BORDE}; border-bottom: 1px solid {BORDE};
    border-top-right-radius: 5px; background: {TARJETA_ALT};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: padding; subcontrol-position: bottom right;
    width: 18px; border-left: 1px solid {BORDE};
    border-bottom-right-radius: 5px; background: {TARJETA_ALT};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{ background: {ACENTO_SUAVE}; }}
QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled,
QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled {{ background: {TARJETA_ALT}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({r["arriba"]}); width: 8px; height: 8px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({r["abajo"]}); width: 8px; height: 8px; }}
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled {{ image: url({r["arriba_off"]}); }}
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {{ image: url({r["abajo_off"]}); }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url({r["abajo"]}); width: 8px; height: 8px; }}
QComboBox::down-arrow:disabled {{ image: url({r["abajo_off"]}); }}
"""
    return _flechas_qss


# Formularios: campos de texto, cajas de grupo, casillas y el botón principal.
# Lo usan Configuración y los diálogos (ui_helpers.style_dialog).
QSS_FORM = f"""
QLineEdit, QPlainTextEdit {{
    background: {TARJETA}; border: 1px solid {BORDE_FUERTE}; border-radius: 6px;
    padding: 3px 8px; selection-background-color: {ACENTO_SUAVE}; selection-color: {TEXTO};
}}
QLineEdit {{ min-height: 20px; }}
QLineEdit:focus, QPlainTextEdit:focus {{ border-color: {ACENTO}; }}
QGroupBox {{
    background: {TARJETA_ALT}; border: 1px solid {BORDE}; border-radius: 8px;
    margin-top: 16px; padding: 12px 8px 6px; font-size: 8.5pt; font-weight: 700; color: {TEXTO_SUAVE};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QGroupBox QLabel {{ font-weight: 400; color: {TEXTO}; }}
QCheckBox {{ spacing: 8px; color: {TEXTO}; }}
QCheckBox::indicator {{
    width: 15px; height: 15px; border: 1px solid {BORDE_FUERTE}; border-radius: 4px; background: {TARJETA};
}}
QCheckBox::indicator:checked {{ background: {ACENTO}; border-color: {ACENTO}; }}
QCheckBox::indicator:hover {{ border-color: {ACENTO}; }}
QPushButton[accion="principal"] {{
    background: {ACENTO}; border: 1px solid {ACENTO}; color: #FFFFFF;
    font-weight: 700; padding: 6px 20px; border-radius: 8px;
}}
QPushButton[accion="principal"]:hover {{ background: {ACENTO_CLARO}; border-color: {ACENTO_CLARO}; color: #FFFFFF; }}
QPushButton[accion="principal"]:disabled {{ background: {TARJETA_ALT}; border-color: {BORDE}; color: {TEXTO_TENUE}; }}
QFrame#cabeceraDialogo {{ background: {TARJETA}; border: 1px solid {BORDE}; border-radius: 10px; }}
"""

# Los avisos (QMessageBox, QProgressDialog, QDialog): el estilo común sobre el
# lienzo, el botón por defecto como principal y la barra de progreso del color
# de la app.
QSS_DIALOGO = f"""
QDialog, QMessageBox, QProgressDialog {{
    background: {FONDO}; color: {TEXTO};
    font-family: "Noto Sans", "DejaVu Sans", sans-serif; font-size: 9pt;
}}
QMessageBox QLabel {{ color: {TEXTO}; font-size: 9.5pt; }}
QDialogButtonBox QPushButton, QMessageBox QPushButton {{ min-width: 84px; padding: 6px 14px; }}
QMessageBox QPushButton:default, QDialogButtonBox QPushButton:default {{
    background: {ACENTO}; border: 1px solid {ACENTO}; color: #FFFFFF; font-weight: 700;
}}
QMessageBox QPushButton:default:hover, QDialogButtonBox QPushButton:default:hover {{
    background: {ACENTO_CLARO}; border-color: {ACENTO_CLARO}; color: #FFFFFF;
}}
QProgressBar {{
    border: 1px solid {BORDE}; border-radius: 6px; background: {TARJETA};
    min-height: 16px; text-align: center; color: {TEXTO}; font-size: 8pt;
}}
QProgressBar::chunk {{ background: {ACENTO}; border-radius: 5px; }}
"""


def qss_dialogo():
    return QSS + QSS_FORM + QSS_DIALOGO + qss_flechas()


def aplicar_estilo(widget, extra=""):
    """Aplica el QSS común a `widget` y a todo lo que cuelgue de él. `extra`:
    reglas propias del módulo, que se suman al final."""
    from PySide6.QtCore import Qt
    widget.setObjectName('labsimRoot')
    # Un QWidget suelto no pinta el fondo del QSS sin esto: el módulo quedaba
    # con el gris del sistema en vez del lienzo.
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setStyleSheet(QSS + extra + qss_flechas())


def ajustar_alto(tabla):
    """La tabla al alto exacto de sus filas, sin barra: en el panel angosto la
    barra se comía el ancho y dejaba filas fuera de vista."""
    from PySide6.QtCore import Qt
    tabla.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    tabla.resizeRowsToContents()
    alto = (tabla.horizontalHeader().sizeHint().height() + tabla.verticalHeader().length()
            + 2 * tabla.frameWidth())
    tabla.setFixedHeight(alto)


def pastilla_lado(etiqueta, side):
    """Deja una QLabel como la píldora del oído (OD rojo, OI azul)."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QSizePolicy
    etiqueta.setProperty('pill', 'od' if side in (0, 'OD') else 'oi')
    etiqueta.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)


def repintar(widget):
    """Vuelve a resolver el QSS de un widget cuyo `property` cambió.

    Qt no reevalúa los selectores por propiedad solo: sin esto, marcar
    `estado="alerta"` en una etiqueta ya mostrada no cambia nada.
    """
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
