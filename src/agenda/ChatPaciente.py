# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 0.9 - Audiometro                   #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

import requests
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
from PySide6.QtCore import QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QTextDocument
from core.helpers import chat_con_paciente, foto_paciente
from core.avatar import avatar_iniciales, avatar_circular_desde_bytes


class _ChatPacienteThread(QThread):
    """Manda un turno de chat al backend (llamada de red) fuera del hilo de UI."""
    respondido = Signal(str)
    fallo = Signal(str)

    def __init__(self, case_id, nombre, edad, procedimiento, history, message, appointment_id=None, parent=None):
        super().__init__(parent)
        self._args = (case_id, nombre, edad, procedimiento, history, message, appointment_id)

    def run(self):
        try:
            reply = chat_con_paciente(*self._args)
        except (RuntimeError, requests.RequestException) as exc:
            self.fallo.emit(str(exc))
            return
        self.respondido.emit(reply)


class _AvatarFetchThread(QThread):
    """Trae el avatar circular del paciente (si tiene foto subida) fuera del
    hilo de UI -- ver foto_paciente() en helpers.py. Emite None si no tiene
    foto o no hay conexión, no es una falla (fallback a iniciales)."""
    listo = Signal(object)

    def __init__(self, case_id, parent=None):
        super().__init__(parent)
        self._case_id = case_id

    def run(self):
        self.listo.emit(foto_paciente(self._case_id))


class ChatPacienteWidget(QWidget):
    """Chat de prueba/entrevista con el paciente simulado por LLM (ver
    LlmChat.php) -- el alumno conversa para levantar antecedentes/motivo de
    consulta, igual que haría con un paciente real antes del examen.

    Vive como subventana única del MDI (ver main.py: self.subw["CHAT"]) en
    vez de un diálogo emergente -- set_paciente() la reapunta a otro caso
    cada vez que se abre desde una ficha distinta, reseteando la
    conversación anterior."""

    REINTENTOS_AUTOMATICOS = 1  # 1 reintento silencioso antes de pedirle al alumno que reintente a mano
    AVATAR_SIZE = 32
    _AVATAR_USER_URL = "avatar:user"
    _AVATAR_PACIENTE_URL = "avatar:paciente"

    def __init__(self, usuario_nombre=None, parent=None):
        super().__init__(parent)
        self._case_id = None
        self._appointment_id = None
        self._nombre = "el paciente"
        self._usuario_nombre = usuario_nombre or "Tú"
        self._edad = 0
        self._procedimiento = ""
        self._history = []
        self._thread = None
        self._avatar_thread = None
        self._mensaje_pendiente = None  # último mensaje enviado, para reintentar sin retipear
        self._intentos = 0

        layout = QVBoxLayout(self)

        self.lbl_paciente = QLabel(self)
        self.lbl_paciente.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_paciente)

        self.transcript = QTextEdit(self)
        self.transcript.setReadOnly(True)
        self.transcript.setStyleSheet("background-color: #e9e2d6;")  # fondo tipo wsp, para que las burbujas blancas resalten
        layout.addWidget(self.transcript)

        self._registrar_avatar_usuario()

        self.lbl_estado = QLabel(self)
        self.lbl_estado.setStyleSheet("color: #888;")
        self.lbl_estado.hide()
        layout.addWidget(self.lbl_estado)

        fila_input = QHBoxLayout()
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Escribe tu pregunta al paciente...")
        self.input.returnPressed.connect(self._enviar)
        fila_input.addWidget(self.input)

        self.btn_enviar = QPushButton("➤", self)
        self.btn_enviar.setToolTip("Enviar")
        self.btn_enviar.setFixedSize(36, 36)
        self.btn_enviar.setStyleSheet(
            "QPushButton { background-color: #25d366; color: white; border: none; "
            "border-radius: 18px; font-size: 14pt; padding-bottom: 2px; }"
            "QPushButton:hover { background-color: #20bd5a; }"
            "QPushButton:disabled { background-color: #a8dfb8; }"
        )
        self.btn_enviar.clicked.connect(self._enviar)
        fila_input.addWidget(self.btn_enviar)

        self.btn_reintentar = QPushButton("Reintentar", self)
        self.btn_reintentar.clicked.connect(self._reintentar_manual)
        self.btn_reintentar.hide()
        fila_input.addWidget(self.btn_reintentar)

        layout.addLayout(fila_input)

        self._actualizar_encabezado()

    def set_paciente(self, case_id, nombre, edad, procedimiento, appointment_id=None):
        """Reapunta el chat a otro caso -- descarta la conversación anterior.

        appointment_id: cita real a la que se asocia lo que se guarde del
        chat (ver LlmChat.php) -- None = no se guarda nada (p.ej. "Atender
        (prueba)" del admin, que no debe dejar rastro)."""
        self._case_id = case_id
        self._appointment_id = appointment_id
        self._nombre = nombre or "el paciente"
        self._edad = edad
        self._procedimiento = procedimiento
        self._history = []
        self._mensaje_pendiente = None
        self._intentos = 0
        self.transcript.clear()  # ¡también borra los recursos (avatares) del documento, no solo el texto!
        self._ocultar_estado()
        self._actualizar_encabezado()
        self._registrar_avatar_usuario()
        self._set_avatar_paciente(avatar_iniciales(self._nombre, self.AVATAR_SIZE))
        self._pedir_avatar_paciente(case_id)
        self.input.setFocus()

    def _actualizar_encabezado(self):
        self.lbl_paciente.setText(f"Conversando con {self._nombre} ({self._procedimiento or 'sin motivo registrado'})")

    def _registrar_avatar_usuario(self):
        self.transcript.document().addResource(
            QTextDocument.ImageResource, QUrl(self._AVATAR_USER_URL),
            avatar_iniciales(self._usuario_nombre, self.AVATAR_SIZE).toImage(),
        )

    def _set_avatar_paciente(self, pixmap):
        self.transcript.document().addResource(
            QTextDocument.ImageResource, QUrl(self._AVATAR_PACIENTE_URL), pixmap.toImage()
        )

    def _pedir_avatar_paciente(self, case_id):
        """Foto real del paciente si tiene una subida (ver PatientPhoto.php)
        -- mientras tanto (o si no hay), queda el círculo con iniciales que
        ya dejó set_paciente()."""
        self._avatar_thread = _AvatarFetchThread(case_id, parent=self)
        self._avatar_thread.listo.connect(lambda data, cid=case_id: self._on_avatar_listo(cid, data))
        self._avatar_thread.start()

    def _on_avatar_listo(self, case_id_solicitado, data):
        if case_id_solicitado != self._case_id or not data:
            return  # sin foto, o el alumno ya cambió de paciente mientras se pedía
        pixmap = avatar_circular_desde_bytes(data, self.AVATAR_SIZE)
        if pixmap is not None:
            self._set_avatar_paciente(pixmap)

    def _agregar_burbuja(self, rol, texto):
        """Burbuja estilo WhatsApp: el usuario a la derecha (verde), el
        paciente a la izquierda (blanco) -- el lado + color ya dicen quién
        habla, así que solo el paciente lleva etiqueta con su nombre (el
        usuario nunca se etiqueta a sí mismo en un chat 1 a 1, como en wsp)."""
        texto_html = texto.replace("\n", "<br>")
        avatar_size = self.AVATAR_SIZE
        if rol == "user":
            self.transcript.append(
                f'<table align="right" cellspacing="0" cellpadding="0" style="margin:3px 0;"><tr>'
                f'<td valign="top" style="background-color:#dcf8c6; border:1px solid #cdeeb5; '
                f'border-radius:9px; padding:6px 10px; max-width:340px;">{texto_html}</td>'
                f'<td valign="top" style="padding-left:6px;">'
                f'<img src="{self._AVATAR_USER_URL}" width="{avatar_size}" height="{avatar_size}"></td>'
                f'</tr></table>'
            )
        else:
            self.transcript.append(
                f'<table align="left" cellspacing="0" cellpadding="0" style="margin:3px 0;"><tr>'
                f'<td valign="top" style="padding-right:6px;">'
                f'<img src="{self._AVATAR_PACIENTE_URL}" width="{avatar_size}" height="{avatar_size}"></td>'
                f'<td valign="top" style="background-color:#ffffff; border:1px solid #e2e2e2; '
                f'border-radius:9px; padding:6px 10px; max-width:340px;">'
                f'<span style="color:#3a7d3a; font-size:8pt; font-weight:bold;">{self._nombre}</span><br>'
                f'{texto_html}</td>'
                f'</tr></table>'
            )
        barra = self.transcript.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _mostrar_estado(self, texto):
        self.lbl_estado.setText(texto)
        self.lbl_estado.show()

    def _ocultar_estado(self):
        self.lbl_estado.hide()
        self.btn_reintentar.hide()

    def _enviar(self):
        mensaje = self.input.text().strip()
        if not mensaje or self._thread is not None or not self._case_id:
            return
        self.input.clear()
        self._agregar_burbuja("user", mensaje)
        self._intentos = 0
        self._despachar(mensaje)

    def _reintentar_manual(self):
        if self._mensaje_pendiente is None or self._thread is not None:
            return
        self._intentos = 0
        self._despachar(self._mensaje_pendiente)

    def _despachar(self, mensaje):
        """Manda `mensaje` al backend -- puede ser el recién escrito o un reintento
        del último que falló (mismo texto, no se duplica burbuja de usuario)."""
        self._mensaje_pendiente = mensaje
        self.btn_reintentar.hide()
        self._mostrar_estado("El paciente está pensando su respuesta…")
        self.input.setEnabled(False)
        self.btn_enviar.setEnabled(False)

        case_id_solicitado = self._case_id
        self._thread = _ChatPacienteThread(
            self._case_id, self._nombre, self._edad, self._procedimiento,
            list(self._history), mensaje, appointment_id=self._appointment_id, parent=self,
        )
        self._thread.respondido.connect(lambda r: self._on_respuesta(case_id_solicitado, mensaje, r))
        self._thread.fallo.connect(lambda e: self._on_fallo(case_id_solicitado, mensaje, e))
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.start()

    def _on_respuesta(self, case_id_solicitado, mensaje, reply):
        self.input.setEnabled(True)
        self.btn_enviar.setEnabled(True)
        self._mensaje_pendiente = None
        self._intentos = 0
        self._ocultar_estado()
        if case_id_solicitado != self._case_id:
            return  # el usuario cambió de paciente mientras esperaba la respuesta
        self._history.append({"role": "user", "content": mensaje})
        self._history.append({"role": "assistant", "content": reply})
        self._agregar_burbuja("assistant", reply)

    def _on_fallo(self, case_id_solicitado, mensaje, error):
        self.input.setEnabled(True)
        self.btn_enviar.setEnabled(True)
        if case_id_solicitado != self._case_id:
            self._ocultar_estado()
            return

        # Silencioso: nada de diálogos emergentes -- reintenta solo una vez y,
        # si sigue fallando, deja el mensaje "guardado" en btn_reintentar en
        # vez de obligar al alumno a retipearlo.
        print(f"[chat_paciente] fallo (intento {self._intentos + 1}): {error}")
        if self._intentos < self.REINTENTOS_AUTOMATICOS:
            self._intentos += 1
            self._mostrar_estado("Sin respuesta todavía, reintentando…")
            QTimer.singleShot(1500, lambda: self._despachar(mensaje))
        else:
            self._mostrar_estado("El paciente no respondió. Puedes reintentar.")
            self.btn_reintentar.show()

    def _on_thread_finished(self):
        self._thread = None
        self.input.setFocus()
