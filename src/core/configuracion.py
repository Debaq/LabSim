"""Configuración personal: atajos de teclado y mouse para zurdos.

Lo que se guarda acá va a la cuenta del usuario (ver core/preferencias.py),
no al equipo: en el laboratorio lo encuentra en cualquier computador.
"""

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QKeySequenceEdit, QLabel, QPushButton, QScrollArea,
                               QTabWidget, QVBoxLayout, QWidget)

from core import atajos, keyboard_monitor
from core.kiosko import es_kiosko
from core.preferencias import preferencias
from core.ui_helpers import style_dialog


class ConfiguracionDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.resize(520, 560)
        prefs = preferencias()

        raiz = QVBoxLayout(self)
        tabs = QTabWidget(self)
        tabs.addTab(self._pestana_atajos(prefs.atajos()), "Atajos de teclado")
        tabs.addTab(self._pestana_mouse(prefs.mouse_zurdo()), "Mouse")
        raiz.addWidget(tabs)

        self.lbl_error = QLabel(self)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet("color:#b3261e;")
        raiz.addWidget(self.lbl_error)

        self.botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                        | QDialogButtonBox.StandardButton.Cancel, self)
        self.botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.botones.accepted.connect(self._guardar)
        self.botones.rejected.connect(self.reject)
        raiz.addWidget(self.botones)

        style_dialog(self)
        self._validar()

    # -- Atajos ------------------------------------------------------------

    def _pestana_atajos(self, propios):
        pagina = QWidget(self)
        caja = QVBoxLayout(pagina)

        conectado = keyboard_monitor.monitor().is_connected()
        aviso = QLabel(
            "Estas teclas son para el teclado del computador. "
            + ("<b>El controlador LabSim está conectado:</b> mientras lo esté se usan "
               "sus teclas, que no se pueden cambiar." if conectado else
               "Con el controlador LabSim conectado se usan sus teclas, que no se pueden cambiar."),
            pagina)
        aviso.setWordWrap(True)
        caja.addWidget(aviso)

        scroll = QScrollArea(pagina)
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        lista = QVBoxLayout(contenido)
        self.editores = {}
        vigentes = atajos.teclas(False, propios)
        grupos = {}
        for accion, grupo, descripcion, _def, _ctrl in atajos.ACCIONES:
            if grupo not in grupos:
                box = QGroupBox(grupo, contenido)
                grupos[grupo] = QFormLayout(box)
                lista.addWidget(box)
            editor = QKeySequenceEdit(QKeySequence(vigentes[accion]), contenido)
            if hasattr(editor, "setMaximumSequenceLength"):
                editor.setMaximumSequenceLength(1)
            editor.keySequenceChanged.connect(self._validar)
            self.editores[accion] = editor
            grupos[grupo].addRow(descripcion, editor)
        lista.addStretch(1)
        scroll.setWidget(contenido)
        caja.addWidget(scroll, 1)

        fila = QHBoxLayout()
        fila.addStretch(1)
        restaurar = QPushButton("Restaurar teclas por defecto", pagina)
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
        self.chk_zurdo = QCheckBox("Mouse para zurdos (intercambia el botón izquierdo y el derecho)", pagina)
        self.chk_zurdo.setChecked(zurdo)
        caja.addWidget(self.chk_zurdo)
        texto = (
            "Se aplica en los computadores del laboratorio, dentro de LabSim, y te sigue a "
            "cualquiera de ellos."
            + (" <b>Este computador es del laboratorio:</b> se aplica al guardar." if es_kiosko() else
               " <b>Este computador no es del laboratorio:</b> acá no se aplica; si lo quieres, "
               "configúralo en el mouse del sistema operativo.")
        )
        nota = QLabel(texto, pagina)
        nota.setWordWrap(True)
        caja.addWidget(nota)
        caja.addStretch(1)
        return pagina

    # ----------------------------------------------------------------------

    def _validar(self, *_):
        errores = atajos.conflictos(self._mapa())
        self.lbl_error.setText("\n".join(errores))
        self.botones.button(QDialogButtonBox.StandardButton.Save).setEnabled(not errores)
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
    ConfiguracionDialog(parent).exec()
