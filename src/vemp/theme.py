"""
Hoja de estilo del módulo VEMP. La paleta, el QSS común y los helpers viven en
core/tema.py (compartido con los demás módulos); acá solo queda lo que es del
VEMP y la re-exportación, para que `from vemp import theme` siga igual.
"""
from core import tema
from core.tema import *  # noqa: F401,F403
from core.tema import FONDO, ACENTO, ACENTO_CLARO, ALERTA, TEXTO_SUAVE  # noqa: F401

QSS_VEMP = f"""
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
"""

QSS = tema.QSS + QSS_VEMP


def aplicar_estilo(widget):
    """Aplica el QSS común más el del VEMP a `widget` y a todo lo que cuelgue de él."""
    tema.aplicar_estilo(widget, QSS_VEMP)


repintar = tema.repintar
