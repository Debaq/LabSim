"""Reportar un problema: manda el registro de la app al servidor como ticket.

Pestaña de Configuración. Antes de mandar nada se muestra exactamente qué
sale del equipo (versión, nombre del equipo, sistema, el registro) y el
usuario tiene que aceptarlo; el servidor también exige esa aceptación (ver
labsim_backend/public/api/ticket.php). Al usuario no se le contesta: el
ticket es para que el equipo de LabSim abra un issue.
"""
import gzip

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
                               QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)

from core import equipo, hilos, registro
from core.base import context
from core.helpers import Preferences
from core.ui_helpers import style_dialog

# Rótulos de detalle_sistema() para mostrar.
_ROTULOS = {"so_version": "Sistema operativo", "distribucion": "Distribución",
            "arquitectura": "Arquitectura", "python": "Python", "qt": "Qt",
            "pantalla": "Pantalla", "kiosko": "Equipo del laboratorio"}


class _Envio(QThread):
    listo = Signal(bool, str)   # ok, número de ticket o motivo

    def __init__(self, descripcion, equipo_info, detalle):
        super().__init__()
        self.descripcion = descripcion
        self.equipo_info = equipo_info
        self.detalle = detalle

    def run(self):
        from backend.client import BackendClient
        try:
            log_gz = gzip.compress(registro.cola())
            client = BackendClient(Preferences().get("BACKEND_URL"),
                                   context.get_resource("json/session.json"))
            if not client.is_logged_in():
                raise RuntimeError("no hay sesión iniciada con el servidor")
            respuesta = client.send_ticket(self.descripcion, self.equipo_info,
                                           self.detalle, log_gz or None)
        except Exception as exc:  # noqa: BLE001 -- se le muestra al usuario
            print(f"soporte: no se pudo enviar el reporte: {exc}")
            self.listo.emit(False, str(exc))
            return
        print(f"soporte: reporte enviado, ticket #{respuesta.get('id')}")
        self.listo.emit(True, str(respuesta.get("id", "")))


class PaginaSoporte(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._equipo = equipo.identidad()
        self._detalle = registro.detalle_sistema()
        self._envio = None

        caja = QVBoxLayout(self)
        intro = QLabel(
            "Si LabSim se cerró solo, se colgó o algo no funcionó, cuéntanos qué pasó y envía "
            "el registro de este equipo. Se crea un ticket para el equipo de LabSim. No vas a "
            "recibir respuesta, pero nos sirve para encontrar y corregir el problema.", self)
        intro.setWordWrap(True)
        caja.addWidget(intro)

        caja.addWidget(QLabel("¿Qué estabas haciendo y qué pasó? (opcional)", self))
        self.txt_descripcion = QPlainTextEdit(self)
        self.txt_descripcion.setPlaceholderText(
            "Ej.: estaba en el ABR, se cortó internet y la ventana se cerró.")
        self.txt_descripcion.setMaximumHeight(90)
        caja.addWidget(self.txt_descripcion)

        caja.addWidget(self._caja_que_se_envia())

        self.chk_acepto = QCheckBox(
            "Acepto enviar al servidor de LabSim la información de este equipo que aparece "
            "arriba y el registro de la aplicación.", self)
        self.chk_acepto.toggled.connect(self._actualizar_boton)
        caja.addWidget(self.chk_acepto)

        self.btn_enviar = QPushButton("Enviar reporte", self)
        self.btn_enviar.clicked.connect(self._enviar)
        caja.addWidget(self.btn_enviar)

        self.lbl_estado = QLabel(self)
        self.lbl_estado.setWordWrap(True)
        caja.addWidget(self.lbl_estado)
        caja.addStretch(1)
        self._actualizar_boton()

    def _caja_que_se_envia(self):
        box = QGroupBox("Qué se envía", self)
        form = QFormLayout(box)
        e = self._equipo or {}
        form.addRow("Versión de LabSim:", QLabel(e.get("version") or equipo.version or "?", box))
        form.addRow("Nombre del equipo:", QLabel(e.get("nombre", "?"), box))
        for clave, valor in self._detalle.items():
            if isinstance(valor, bool):
                valor = "sí" if valor else "no"
            etiqueta = QLabel(str(valor), box)
            etiqueta.setWordWrap(True)
            form.addRow(f"{_ROTULOS.get(clave, clave)}:", etiqueta)
        kb = len(registro.cola()) // 1024
        btn_ver = QPushButton(f"Ver el registro ({kb} KB)", box)
        btn_ver.clicked.connect(self._ver_registro)
        form.addRow("Registro de la app:", btn_ver)
        form.addRow("", QLabel(f"Se guarda en: {registro.archivo()}", box))
        return box

    def _ver_registro(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Registro de LabSim")
        dlg.resize(760, 520)
        caja = QVBoxLayout(dlg)
        texto = QPlainTextEdit(dlg)
        texto.setReadOnly(True)
        texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        texto.setPlainText(registro.cola().decode("utf-8", errors="replace")
                           or "(el registro está vacío)")
        texto.moveCursor(texto.textCursor().MoveOperation.End)
        caja.addWidget(texto)
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, dlg)
        botones.rejected.connect(dlg.reject)
        caja.addWidget(botones)
        style_dialog(dlg)
        dlg.exec()

    def _actualizar_boton(self, *_):
        enviando = self._envio is not None
        self.btn_enviar.setEnabled(self.chk_acepto.isChecked() and not enviando)

    def _enviar(self):
        if not self.chk_acepto.isChecked() or self._envio is not None:
            return
        self.lbl_estado.setStyleSheet("color:#666666;")
        self.lbl_estado.setText("Enviando…")
        self._envio = _Envio(self.txt_descripcion.toPlainText().strip(),
                             self._equipo, self._detalle)
        self._envio.listo.connect(self._enviado)
        self._envio.start()
        # Si se cierra Configuración mientras sube, el hilo sigue solo
        # (ver core/hilos.py) en vez de destruirse corriendo.
        hilos.soltar(self._envio)
        self._actualizar_boton()

    def _enviado(self, ok, detalle):
        self._envio = None
        if ok:
            self.lbl_estado.setStyleSheet("color:#27ae60;")
            self.lbl_estado.setText(f"Reporte enviado. Ticket #{detalle}. ¡Gracias!")
            self.txt_descripcion.clear()
            self.chk_acepto.setChecked(False)
        else:
            self.lbl_estado.setStyleSheet("color:#c0392b;")
            self.lbl_estado.setText(
                "No se pudo enviar el reporte. Revisa la conexión e inténtalo de nuevo; "
                f"el registro sigue guardado en este equipo.\n({detalle[:160]})")
        self._actualizar_boton()
