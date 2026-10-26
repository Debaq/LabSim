"""
Piezas visuales de la agenda (ver Agenda.py): estados con icono y color,
contadores, botones de acción con icono, los tres pasos de una atención y el
panel de detalle del paciente elegido.

Acá no hay lógica de agenda: solo cómo se ve y qué le dice al alumno. Los
colores salen de core/tema.py y los dibujos de core/iconos.py.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from core import iconos, tema

# clave -> (texto, icono, color). Es el único lugar donde se decide cómo se
# llama y cómo se ve cada estado: la tabla, los contadores y el panel lo leen.
ESTADOS = {
    "por_atender": ("Por atender", "reloj", tema.ACENTO),
    "vencida": ("Hora pasada", "alerta", tema.AVISO),
    "atendiendo": ("En atención", "atender", tema.OI),
    "atendido": ("Atendido", "check", tema.OK),
    "no_show": ("No se presentó", "x", tema.ALERTA),
    "sin_fecha": ("Sin fecha", "calendario_vacio", tema.AVISO),
    "sin_cita": ("Sin cita", "sin_cita", tema.TEXTO_SUAVE),
    "practica_nuevo": ("Sin intentos", "practica", tema.TEXTO_SUAVE),
    "practica_curso": ("En curso", "atender", tema.OI),
    "practica_hecho": ("Practicado", "check", tema.OK),
}

PASOS = ("Revisa la ficha", "Atiende al paciente", "Registra la evolución")

# Qué contadores se ven en cada vista.
CONT_AGENDA = ("por_atender", "atendiendo", "atendido", "no_show")
CONT_PRACTICA = ("practica_nuevo", "practica_curso", "practica_hecho")


def icono_estado(clave, tam=18):
    _, nombre, color = ESTADOS[clave]
    return iconos.icono(nombre, color, tam)


class BotonAccion(QPushButton):
    """Botón con icono que acompaña a su texto. `principal=True` es el
    botón de color (Atender); el resto es secundario."""

    def __init__(self, texto, icono, principal=False, parent=None):
        super().__init__(parent)
        self._icono = icono
        self._principal = principal
        self.setProperty("accion", "principal" if principal else "secundaria")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(texto)

    def _color_icono(self):
        return "#FFFFFF" if self._principal and self.isEnabled() else tema.ACENTO

    def setText(self, texto):
        super().setText(texto)
        self._pintar_icono()

    def setEnabled(self, activo):
        super().setEnabled(activo)
        self._pintar_icono()

    def _pintar_icono(self):
        nombre = self._icono
        if self._principal and "cerrar/evolucionar" in self.text().lower():
            nombre = "evolucion"
        color = tema.TEXTO_TENUE if not self.isEnabled() else self._color_icono()
        self.setIcon(iconos.icono(nombre, color, 18))


class Contador(QFrame):
    """Un número con su icono y su nombre: cuántas citas hay en cada estado."""

    def __init__(self, clave, parent=None):
        super().__init__(parent)
        texto, nombre_icono, color = ESTADOS[clave]
        self.setProperty("card", "flat")
        fila = QHBoxLayout(self)
        fila.setContentsMargins(10, 6, 12, 6)
        fila.setSpacing(8)
        marca = QLabel()
        marca.setPixmap(iconos.pixmap(nombre_icono, color, 20))
        self.valor = QLabel("0")
        self.valor.setProperty("role", "dato")
        self.valor.setStyleSheet(f"color: {color};")
        nombre = QLabel(texto)
        nombre.setProperty("role", "campo")
        fila.addWidget(marca)
        fila.addWidget(self.valor)
        fila.addWidget(nombre)
        fila.addStretch(1)

    def set_valor(self, n):
        self.valor.setText(str(n))


class Pasos(QWidget):
    """Los tres pasos de una atención, con el actual resaltado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(6)
        self._etiquetas = []
        for i, texto in enumerate(PASOS):
            etiqueta = QLabel(f"{i + 1}  {texto}")
            etiqueta.setProperty("pill", "neutro")
            self._etiquetas.append(etiqueta)
            fila.addWidget(etiqueta)
            if i < len(PASOS) - 1:
                flecha = QLabel()
                flecha.setPixmap(iconos.pixmap("derecha", tema.TEXTO_TENUE, 14))
                fila.addWidget(flecha)
        fila.addStretch(1)

    def set_actual(self, actual):
        """`actual`: índice del paso en curso; los anteriores quedan hechos.
        len(PASOS) = todo hecho; None = ninguno resaltado."""
        for i, etiqueta in enumerate(self._etiquetas):
            if actual is None or i > actual:
                valor = "neutro"
            elif i == actual:
                valor = "acento"
            else:
                valor = "ok"
            etiqueta.setProperty("pill", valor)
            etiqueta.setText(("✓  " if valor == "ok" else f"{i + 1}  ") + PASOS[i])
            tema.repintar(etiqueta)


class PanelDetalle(QFrame):
    """El paciente elegido: quién es, en qué estado está, qué sigue y los
    botones para hacerlo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(14, 10, 14, 10)
        raiz.setSpacing(16)

        izq = QVBoxLayout()
        izq.setSpacing(4)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.icono = QLabel()
        self.nombre = QLabel("Elige un paciente de la lista")
        self.nombre.setProperty("role", "titulo")
        self.estado = QLabel()
        self.estado.setProperty("pill", "neutro")
        self.estado.hide()
        fila.addWidget(self.icono)
        fila.addWidget(self.nombre)
        fila.addWidget(self.estado)
        fila.addStretch(1)
        izq.addLayout(fila)
        self.datos = QLabel("")
        self.datos.setProperty("role", "campo")
        izq.addWidget(self.datos)
        self.pasos = Pasos()
        self.pasos.hide()
        izq.addWidget(self.pasos)
        self.pista = QLabel("Selecciona una fila para ver su ficha y atenderlo.")
        self.pista.setProperty("role", "hint")
        self.pista.setWordWrap(True)
        izq.addWidget(self.pista)
        izq.addStretch(1)
        raiz.addLayout(izq, 1)

        self.acciones = QGridLayout()
        self.acciones.setHorizontalSpacing(8)
        self.acciones.setVerticalSpacing(6)
        raiz.addLayout(self.acciones, 0)

    def vacio(self, pista):
        self.icono.setPixmap(iconos.pixmap("persona", tema.TEXTO_TENUE, 26))
        self.nombre.setText("Elige un paciente de la lista")
        self.estado.hide()
        self.datos.setText("")
        self.pasos.hide()
        self.pista.setText(pista)

    def mostrar(self, nombre, datos, clave_estado, pista, paso=None, texto_estado=None):
        texto, nombre_icono, color = ESTADOS[clave_estado]
        self.icono.setPixmap(iconos.pixmap("persona", tema.ACENTO, 26))
        self.nombre.setText(nombre or "Paciente")
        self.estado.setText(texto_estado or texto)
        self.estado.setStyleSheet(
            f"background: {tema.TARJETA_ALT}; border: 1px solid {color}; border-radius: 9px;"
            f"padding: 2px 10px; color: {color}; font-size: 8pt; font-weight: 700;")
        self.estado.show()
        self.datos.setText(datos)
        if paso is None:
            self.pasos.hide()
        else:
            self.pasos.set_actual(paso)
            self.pasos.show()
        self.pista.setText(pista)


QSS_AGENDA = f"""
QFrame#cabeceraAgenda {{ background: {tema.TARJETA}; border: 1px solid {tema.BORDE}; border-radius: 10px; }}
QLabel#tituloAgenda {{ font-size: 15pt; font-weight: 700; color: {tema.TEXTO}; }}
QLabel#subtituloAgenda {{ font-size: 8.5pt; color: {tema.TEXTO_SUAVE}; }}

QPushButton[vista="true"] {{
    border: 1px solid {tema.BORDE_FUERTE}; border-radius: 0; padding: 5px 14px;
    background: {tema.TARJETA}; color: {tema.TEXTO_SUAVE}; font-weight: 600;
}}
QPushButton[lado="izq"] {{ border-top-left-radius: 7px; border-bottom-left-radius: 7px; }}
QPushButton[lado="der"] {{ border-top-right-radius: 7px; border-bottom-right-radius: 7px; margin-left: -1px; }}
QPushButton[vista="true"]:checked {{ background: {tema.ACENTO}; color: #FFFFFF; border-color: {tema.ACENTO}; }}
QPushButton[vista="true"]:hover:!checked {{ color: {tema.ACENTO}; border-color: {tema.ACENTO}; }}

QPushButton[nav="true"] {{ padding: 4px 8px; min-height: 20px; }}

QPushButton[accion="principal"] {{
    background: {tema.ACENTO}; border: 1px solid {tema.ACENTO}; color: #FFFFFF;
    font-weight: 700; padding: 8px 20px; border-radius: 8px; font-size: 10pt;
}}
QPushButton[accion="principal"]:hover {{ background: {tema.ACENTO_CLARO}; border-color: {tema.ACENTO_CLARO}; color: #FFFFFF; }}
QPushButton[accion="principal"]:disabled {{ background: {tema.TARJETA_ALT}; border-color: {tema.BORDE}; color: {tema.TEXTO_TENUE}; }}

QLineEdit#buscarAgenda {{
    background: {tema.TARJETA_ALT}; border: 1px solid {tema.BORDE_FUERTE}; border-radius: 8px;
    padding: 5px 8px; min-width: 220px;
}}
QLineEdit#buscarAgenda:focus {{ background: {tema.TARJETA}; border-color: {tema.ACENTO}; }}

QDateEdit {{ background: {tema.TARJETA}; border: 1px solid {tema.BORDE_FUERTE}; border-radius: 6px;
    padding: 4px 8px; min-height: 20px; }}
QDateEdit:focus {{ border-color: {tema.ACENTO}; }}
QDateEdit::drop-down {{ border: none; width: 20px; }}

QTableWidget {{
    background: {tema.TARJETA}; border: 1px solid {tema.BORDE}; border-radius: 10px;
    gridline-color: transparent; outline: none; font-size: 9pt;
}}
QTableWidget::item {{ padding: 4px 8px; border-bottom: 1px solid {tema.GRILLA}; }}
QTableWidget::item:selected {{ background: {tema.ACENTO_SUAVE}; color: {tema.TEXTO}; }}
QTableWidget::item:hover {{ background: {tema.TARJETA_ALT}; }}
QHeaderView::section {{ padding: 7px 8px; }}

QFrame#vacioAgenda {{ background: {tema.TARJETA}; border: 1px dashed {tema.BORDE_FUERTE}; border-radius: 10px; }}
QLabel[pill="ok"] {{
    background: #E6F4EC; border: 1px solid {tema.OK}; border-radius: 9px;
    padding: 2px 10px; color: {tema.OK}; font-size: 8pt; font-weight: 600;
}}
QCheckBox {{ spacing: 6px; color: {tema.TEXTO_SUAVE}; font-size: 8.5pt; }}
"""


# Ficha clínica y evolución: mismo lienzo y tarjetas que la agenda.
QSS_FICHA = f"""
QTextEdit#textoFicha {{ background: {tema.FONDO}; border: none; padding: 0; }}
QTextEdit#textoEvolucion {{
    background: {tema.TARJETA}; border: 1px solid {tema.BORDE_FUERTE}; border-radius: 10px;
    padding: 10px; font-size: 10pt;
}}
QTextEdit#textoEvolucion:focus {{ border-color: {tema.ACENTO}; }}
QPushButton[accion="principal"] {{
    background: {tema.ACENTO}; border: 1px solid {tema.ACENTO}; color: #FFFFFF;
    font-weight: 700; padding: 8px 20px; border-radius: 8px; font-size: 10pt;
}}
QPushButton[accion="principal"]:hover {{ background: {tema.ACENTO_CLARO}; border-color: {tema.ACENTO_CLARO}; }}
QLabel[pill="ok"] {{
    background: #E6F4EC; border: 1px solid {tema.OK}; border-radius: 9px;
    padding: 2px 10px; color: {tema.OK}; font-size: 8pt; font-weight: 600;
}}
"""
