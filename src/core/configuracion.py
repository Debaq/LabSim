"""Configuración personal: atajos de teclado y mouse para zurdos. Además,
reportar un problema con el registro del equipo (ver core/soporte.py).

Lo que se guarda acá va a la cuenta del usuario (ver core/preferencias.py),
no al equipo: en el laboratorio lo encuentra en cualquier computador.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import (QCheckBox, QDialog, QFrame, QGridLayout, QHBoxLayout,
                               QKeySequenceEdit, QLabel, QListWidget, QListWidgetItem, QScrollArea,
                               QStackedWidget, QVBoxLayout, QWidget)

from agenda.vista import BotonAccion
from core import atajos, iconos, invitado, keyboard_monitor, soporte, tema
from core.kiosko import es_kiosko
from core.preferencias import preferencias

# Lo propio de esta ventana; lo demás es el estilo común (tema.QSS): tarjetas,
# roles de texto, botones. La lista de secciones es la de las carpetas de la
# práctica libre (agenda/vista.py).
QSS_CONFIG = f"""
QFrame#cabeceraConfig {{ background: {tema.TARJETA}; border: 1px solid {tema.BORDE}; border-radius: 10px; }}
QListWidget#navConfig {{
    background: {tema.TARJETA}; border: 1px solid {tema.BORDE}; border-radius: 10px;
    outline: none; font-size: 9pt; padding: 4px;
}}
QListWidget#navConfig::item {{ padding: 8px 6px; border-radius: 6px; color: {tema.TEXTO}; }}
QListWidget#navConfig::item:selected {{ background: {tema.ACENTO}; color: white; }}
QListWidget#navConfig::item:hover:!selected {{ background: {tema.TARJETA_ALT}; }}
QLineEdit, QPlainTextEdit {{
    background: {tema.TARJETA}; border: 1px solid {tema.BORDE_FUERTE}; border-radius: 6px;
    padding: 3px 8px; selection-background-color: {tema.ACENTO_SUAVE}; selection-color: {tema.TEXTO};
}}
QLineEdit {{ min-height: 20px; }}
QLineEdit:focus, QPlainTextEdit:focus {{ border-color: {tema.ACENTO}; }}
QGroupBox {{
    background: {tema.TARJETA_ALT}; border: 1px solid {tema.BORDE}; border-radius: 8px;
    margin-top: 16px; padding: 12px 8px 6px; font-size: 8.5pt; font-weight: 700; color: {tema.TEXTO_SUAVE};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QGroupBox QLabel {{ font-weight: 400; color: {tema.TEXTO}; }}
QCheckBox {{ spacing: 8px; color: {tema.TEXTO}; }}
QCheckBox::indicator {{
    width: 15px; height: 15px; border: 1px solid {tema.BORDE_FUERTE}; border-radius: 4px; background: {tema.TARJETA};
}}
QCheckBox::indicator:checked {{ background: {tema.ACENTO}; border-color: {tema.ACENTO}; }}
QCheckBox::indicator:hover {{ border-color: {tema.ACENTO}; }}
QLabel#errorConfig {{ color: {tema.ALERTA}; font-size: 8.5pt; }}
QPushButton[accion="principal"] {{
    background: {tema.ACENTO}; border: 1px solid {tema.ACENTO}; color: #FFFFFF;
    font-weight: 700; padding: 6px 20px; border-radius: 8px;
}}
QPushButton[accion="principal"]:hover {{ background: {tema.ACENTO_CLARO}; border-color: {tema.ACENTO_CLARO}; color: #FFFFFF; }}
QPushButton[accion="principal"]:disabled {{ background: {tema.TARJETA_ALT}; border-color: {tema.BORDE}; color: {tema.TEXTO_TENUE}; }}
"""


def _tarjeta(parent, titulo=None):
    """Una tarjeta del estilo común, con su rótulo de sección arriba."""
    marco = QFrame(parent)
    marco.setProperty("card", "true")
    caja = QVBoxLayout(marco)
    caja.setContentsMargins(14, 12, 14, 14)
    caja.setSpacing(8)
    if titulo:
        rotulo = QLabel(titulo.upper(), marco)
        rotulo.setProperty("role", "seccion")
        caja.addWidget(rotulo)
    return marco, caja


class ConfiguracionDialog(QDialog):

    # Secciones: (título, ícono, constructor). Atajos y mouse se guardan en la
    # cuenta; reportar un problema tiene su propio botón de envío.
    ATAJOS, MOUSE, SOPORTE = range(3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.resize(680, 600)
        tema.aplicar_estilo(self, QSS_CONFIG)
        prefs = preferencias()

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(14, 14, 14, 12)
        raiz.setSpacing(10)
        raiz.addWidget(self._cabecera())

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(10)
        self.nav = QListWidget(self)
        self.nav.setObjectName("navConfig")
        self.nav.setFixedWidth(190)
        self.nav.setIconSize(QSize(18, 18))
        self.paginas = QStackedWidget(self)
        for titulo, icono, pagina in (
                ("Atajos de teclado", "lista", self._pestana_atajos(prefs.atajos())),
                ("Mouse", "persona", self._pestana_mouse(prefs.mouse_zurdo())),
                ("Reportar un problema", "alerta", self._pestana_soporte())):
            # Blanco en la sección elegida: el morado sobre el fondo morado no se veía
            icon = iconos.icono(icono, tema.ACENTO, 18)
            icon.addPixmap(iconos.pixmap(icono, "#FFFFFF", 18), QIcon.Mode.Selected)
            item = QListWidgetItem(icon, titulo)
            self.nav.addItem(item)
            self.paginas.addWidget(pagina)
        self.nav.currentRowChanged.connect(self._cambiar_seccion)
        cuerpo.addWidget(self.nav, 0, Qt.AlignmentFlag.AlignTop)
        cuerpo.addWidget(self.paginas, 1)
        raiz.addLayout(cuerpo, 1)

        self.lbl_error = QLabel(self)
        self.lbl_error.setObjectName("errorConfig")
        self.lbl_error.setWordWrap(True)
        raiz.addWidget(self.lbl_error)

        pie = QHBoxLayout()
        pie.addStretch(1)
        self.btn_cancelar = BotonAccion("Cancelar", "x", parent=self)
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar = BotonAccion("Guardar", "check", principal=True, parent=self)
        self.btn_guardar.clicked.connect(self._guardar)
        pie.addWidget(self.btn_cancelar)
        pie.addWidget(self.btn_guardar)
        raiz.addLayout(pie)

        self.nav.setCurrentRow(self.ATAJOS)
        self._validar()

    def _cabecera(self):
        marco = QFrame(self)
        marco.setObjectName("cabeceraConfig")
        fila = QHBoxLayout(marco)
        fila.setContentsMargins(14, 10, 14, 10)
        fila.setSpacing(12)
        marca = QLabel(marco)
        marca.setPixmap(iconos.pixmap("engranaje", tema.ACENTO, 30))
        textos = QVBoxLayout()
        textos.setSpacing(0)
        titulo = QLabel("Configuración", marco)
        titulo.setProperty("role", "titulo")
        sub = QLabel("Sin cuenta no se guardan: valen mientras practicas en este computador."
                     if invitado.activo else
                     "Tus preferencias viajan con tu cuenta: las encuentras en cualquier computador "
                     "del laboratorio.", marco)
        sub.setProperty("role", "hint")
        sub.setWordWrap(True)
        textos.addWidget(titulo)
        textos.addWidget(sub)
        fila.addWidget(marca, 0, Qt.AlignmentFlag.AlignTop)
        fila.addLayout(textos, 1)
        return marco

    def _cambiar_seccion(self, fila):
        self.paginas.setCurrentIndex(fila)
        # Reportar un problema no guarda nada: tiene su propio "Enviar reporte"
        guarda = fila != self.SOPORTE
        self.btn_guardar.setVisible(guarda)
        self.btn_cancelar.setText("Cancelar" if guarda else "Cerrar")
        self.lbl_error.setVisible(guarda)

    # -- Atajos ------------------------------------------------------------

    def _pestana_atajos(self, propios):
        pagina = QWidget(self)
        caja = QVBoxLayout(pagina)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(8)

        conectado = keyboard_monitor.monitor().is_connected()
        aviso = QLabel(
            "Estas teclas son para el teclado del computador. "
            + ("<b>El controlador LabSim está conectado:</b> mientras lo esté se usan "
               "sus teclas, que no se pueden cambiar." if conectado else
               "Con el controlador LabSim conectado se usan sus teclas, que no se pueden cambiar."),
            pagina)
        aviso.setProperty("role", "hint")
        aviso.setWordWrap(True)
        caja.addWidget(aviso)

        scroll = QScrollArea(pagina)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        contenido = QWidget()
        contenido.setObjectName("listaAtajos")
        contenido.setStyleSheet("QWidget#listaAtajos { background: transparent; }")
        lista = QVBoxLayout(contenido)
        lista.setContentsMargins(0, 0, 6, 0)
        lista.setSpacing(10)
        self.editores = {}
        vigentes = atajos.teclas(False, propios)
        grupos = {}
        for accion, grupo, descripcion, _def, _ctrl in atajos.ACCIONES:
            if grupo not in grupos:
                tarjeta, caja_tarjeta = _tarjeta(contenido, grupo)
                grilla = QGridLayout()
                grilla.setHorizontalSpacing(12)
                grilla.setVerticalSpacing(6)
                grilla.setColumnStretch(0, 1)
                caja_tarjeta.addLayout(grilla)
                grupos[grupo] = grilla
                lista.addWidget(tarjeta)
            editor = QKeySequenceEdit(QKeySequence(vigentes[accion]), contenido)
            if hasattr(editor, "setMaximumSequenceLength"):
                editor.setMaximumSequenceLength(1)
            editor.setFixedWidth(120)
            editor.keySequenceChanged.connect(self._validar)
            self.editores[accion] = editor
            grilla = grupos[grupo]
            fila = grilla.rowCount()
            texto = QLabel(descripcion, contenido)
            texto.setWordWrap(True)
            grilla.addWidget(texto, fila, 0)
            grilla.addWidget(editor, fila, 1)
        lista.addStretch(1)
        scroll.setWidget(contenido)
        caja.addWidget(scroll, 1)

        fila = QHBoxLayout()
        fila.addStretch(1)
        restaurar = BotonAccion("Restaurar teclas por defecto", "flecha", parent=pagina)
        restaurar.clicked.connect(self._restaurar)
        fila.addWidget(restaurar)
        caja.addLayout(fila)
        return pagina

    def _tecla(self, accion):
        return self.editores[accion].keySequence().toString(
            QKeySequence.SequenceFormat.PortableText)

    def _mapa(self):
        return {accion: self._tecla(accion) for accion in self.editores}

    def _restaurar(self):
        for accion, editor in self.editores.items():
            editor.setKeySequence(QKeySequence(atajos.POR_DEFECTO[accion]))
        self._validar()

    # -- Mouse -------------------------------------------------------------

    def _pestana_mouse(self, zurdo):
        pagina = QWidget(self)
        caja = QVBoxLayout(pagina)
        caja.setContentsMargins(0, 0, 0, 0)
        tarjeta, caja_tarjeta = _tarjeta(pagina, "Mouse")
        self.chk_zurdo = QCheckBox("Mouse para zurdos (intercambia el botón izquierdo y el derecho)", tarjeta)
        self.chk_zurdo.setChecked(zurdo)
        caja_tarjeta.addWidget(self.chk_zurdo)
        texto = (
            "Se aplica en los computadores del laboratorio, dentro de LabSim, y te sigue a "
            "cualquiera de ellos."
            + (" <b>Este computador es del laboratorio:</b> se aplica al guardar." if es_kiosko() else
               " <b>Este computador no es del laboratorio:</b> acá no se aplica; si lo quieres, "
               "configúralo en el mouse del sistema operativo.")
        )
        nota = QLabel(texto, tarjeta)
        nota.setProperty("role", "hint")
        nota.setWordWrap(True)
        caja_tarjeta.addWidget(nota)
        caja.addWidget(tarjeta)
        caja.addStretch(1)
        return pagina

    def _pestana_soporte(self):
        """Reportar un problema (core/soporte.py), dentro de una tarjeta."""
        pagina = QWidget(self)
        caja = QVBoxLayout(pagina)
        caja.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(pagina)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # Al ancho de la ventana: los textos largos (el sistema operativo) se parten
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tarjeta, caja_tarjeta = _tarjeta(None, "Reportar un problema")
        caja_tarjeta.addWidget(soporte.PaginaSoporte(tarjeta))
        scroll.setWidget(tarjeta)
        caja.addWidget(scroll, 1)
        return pagina

    # ----------------------------------------------------------------------

    def _validar(self, *_):
        errores = atajos.conflictos(self._mapa())
        self.lbl_error.setText("\n".join(errores))
        # Sin cuenta no hay dónde guardar (core/invitado.py)
        self.btn_guardar.setEnabled(not errores and not invitado.activo)
        return not errores

    def _guardar(self):
        if not self._validar():
            return
        # Solo lo que cambió respecto de la tecla por defecto: si mañana
        # cambia un valor por defecto, al alumno que no lo tocó le llega.
        propios = {a: t for a, t in self._mapa().items() if t != atajos.POR_DEFECTO[a]}
        ok, mensaje = preferencias().guardar({"mouse_zurdo": self.chk_zurdo.isChecked(),
                                             "atajos": propios})
        if not ok:
            self.lbl_error.setText(mensaje)
            return
        self.accept()


def abrir(parent=None):
    dialogo = ConfiguracionDialog(parent)
    dialogo.exec()
    # Con padre quedaba vivo uno por cada vez que se abría.
    dialogo.deleteLater()
