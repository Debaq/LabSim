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
from core.helpers import chat_con_paciente, foto_paciente, sala_del_caso
from core.avatar import avatar_iniciales, avatar_circular_desde_bytes, color_por_nombre


class _ChatPacienteThread(QThread):
    """Manda un turno de chat al backend (llamada de red) fuera del hilo de UI."""
    respondido = Signal(dict)
    fallo = Signal(str)

    def __init__(self, case_id, nombre, edad, procedimiento, history, message,
                 appointment_id=None, parent=None):
        super().__init__(parent)
        self._args = (case_id, nombre, edad, procedimiento, history, message, appointment_id)

    def run(self):
        try:
            resultado = chat_con_paciente(*self._args)
        except (RuntimeError, requests.RequestException) as exc:
            self.fallo.emit(str(exc))
            return
        self.respondido.emit(resultado)


class _SalaFetchThread(QThread):
    """Trae quiénes están en el box (ver Sala.php) fuera del hilo de UI. Se
    pide al abrir el chat y no después del primer mensaje: el alumno tiene
    que ver con quién viene el paciente al entrar."""
    listo = Signal(object)

    def __init__(self, case_id, nombre, edad, parent=None):
        super().__init__(parent)
        self._args = (case_id, nombre, edad)

    def run(self):
        self.listo.emit(sala_del_caso(*self._args))


class _AvatarFetchThread(QThread):
    """Trae el avatar circular de una persona de la sala (si tiene foto
    subida) fuera del hilo de UI -- ver foto_paciente() en helpers.py. Emite
    None si no tiene foto o no hay conexión, no es una falla (fallback a
    iniciales).

    `foto_key` es la clave con la que el backend guarda esa foto y no el id
    de persona: el paciente conserva la clave histórica del caso (persona
    vacía) aunque en la sala sea `p1` -- ver PatientPhoto::key y
    _foto_key() más abajo."""
    listo = Signal(str, object)

    def __init__(self, case_id, persona_id, foto_key, parent=None):
        super().__init__(parent)
        self._case_id = case_id
        self._persona_id = persona_id
        self._foto_key = foto_key

    def run(self):
        self.listo.emit(self._persona_id, foto_paciente(self._case_id, self._foto_key))


class ChatPacienteWidget(QWidget):
    """Chat de entrevista con el paciente y quienes lo acompañan, todos
    simulados por LLM (ver Sala.php y LlmChat.php).

    No es un chat 1 a 1 con etiquetas: un lactante no cuenta su historia y
    la cuenta la madre, y un adulto que niega su hipoacusia es desmentido
    por quien vive con él. El alumno no elige a quién le habla con un
    control aparte: lo dice escribiendo ("mamita, ¿su hijo escucha bien?")
    y contesta quien corresponda, igual que en una consulta. Manejar eso
    -- contener al que responde por el otro, preguntarle al que sí puede
    saber -- es parte de lo que se está evaluando.

    Vive como subventana única del MDI (ver main.py: self.subw["CHAT"]) en
    vez de un diálogo emergente -- set_paciente() la reapunta a otro caso
    cada vez que se abre desde una ficha distinta, reseteando la
    conversación anterior."""

    REINTENTOS_AUTOMATICOS = 1  # 1 reintento silencioso antes de pedirle al alumno que reintente a mano
    AVATAR_SIZE = 32
    _AVATAR_USER_URL = "avatar:user"
    _PACIENTE_ID = "__paciente__"  # id de respaldo mientras no se sabe quién es quién en la sala

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
        self._avatar_threads = []
        self._sala_thread = None
        self._mensaje_pendiente = None  # último mensaje enviado, para reintentar sin retipear
        self._intentos = 0

        # Quiénes están en la consulta. Solo se usa para mostrar: la cara y
        # el nombre de cada burbuja, y el encabezado. Quién contesta cada
        # pregunta lo decide el modelo, no el cliente.
        self._sala = []
        self._avatares = set()  # personas que ya tienen imagen cargada en el documento
        self._fotos = {}  # clave de foto -> pixmap ya traído (el paciente aparece como __paciente__ y como p1)

        layout = QVBoxLayout(self)

        self.lbl_paciente = QLabel(self)
        self.lbl_paciente.setStyleSheet("font-weight: bold;")
        self.lbl_paciente.setWordWrap(True)
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
        self._sala = []
        self._avatares = set()  # transcript.clear() más abajo borra también los avatares
        self._fotos = {}
        self.transcript.clear()  # ¡también borra los recursos (avatares) del documento, no solo el texto!
        self._ocultar_estado()
        self._actualizar_encabezado()
        self._registrar_avatar_usuario()
        # Respaldo mientras no llega la sala: el paciente con sus iniciales,
        # que es exactamente el chat 1 a 1 de antes.
        self._asegurar_avatar(self._PACIENTE_ID, self._nombre)
        self._pedir_sala()
        self.input.setFocus()

    # -----------------------------------------------------------------
    # Sala
    # -----------------------------------------------------------------

    def _pedir_sala(self):
        self._sala_thread = _SalaFetchThread(self._case_id, self._nombre, self._edad, parent=self)
        self._sala_thread.listo.connect(lambda sala, cid=self._case_id: self._on_sala_lista(cid, sala))
        self._sala_thread.start()

    def _on_sala_lista(self, case_id_solicitado, sala):
        if case_id_solicitado != self._case_id:
            return  # el alumno cambió de paciente mientras se pedía
        self._aplicar_sala(sala)
        for persona in self._sala:
            self._asegurar_avatar(persona["id"], persona["etiqueta"])

    def _aplicar_sala(self, sala):
        """Guarda quiénes están en la consulta, para poder ponerle cara y
        nombre a cada burbuja."""
        if not sala:
            return
        self._sala = sala
        self._actualizar_encabezado()

    def _persona(self, persona_id):
        for p in self._sala:
            if p["id"] == persona_id:
                return p
        return None

    # -----------------------------------------------------------------
    # Avatares
    # -----------------------------------------------------------------

    def _avatar_url(self, persona_id):
        return f"avatar:{persona_id}"

    def _registrar_avatar_usuario(self):
        self.transcript.document().addResource(
            QTextDocument.ImageResource, QUrl(self._AVATAR_USER_URL),
            avatar_iniciales(self._usuario_nombre, self.AVATAR_SIZE).toImage(),
        )

    def _asegurar_avatar(self, persona_id, etiqueta):
        """Deja lista la cara de esa persona: primero el círculo con sus
        iniciales, y en paralelo se pide la foto real si tiene una subida.

        Se llama también al pintar una burbuja y no solo al llegar la sala:
        si la sala no se pudo traer (red caída), igual hay que mostrar una
        cara y no un ícono de imagen rota."""
        if persona_id in self._avatares:
            return
        self._avatares.add(persona_id)
        # El paciente se pinta dos veces: primero como __paciente__ (respaldo
        # mientras no llega la sala) y después como p1. Es la misma foto y la
        # misma clave, así que la segunda vez no se vuelve a pedir ni pasa
        # por las iniciales.
        foto = self._fotos.get(self._foto_key(persona_id))
        if foto is not None:
            self._set_avatar(persona_id, foto)
            return
        self._set_avatar(persona_id, avatar_iniciales(etiqueta, self.AVATAR_SIZE))
        self._pedir_avatar(persona_id)

    def _set_avatar(self, persona_id, pixmap):
        self.transcript.document().addResource(
            QTextDocument.ImageResource, QUrl(self._avatar_url(persona_id)), pixmap.toImage()
        )
        # Reemplazar el recurso no repinta solo: si la foto llegó después de
        # la burbuja, sin esto la cara se sigue viendo con iniciales hasta
        # que el alumno scrollea.
        self.transcript.viewport().update()

    def _foto_key(self, persona_id):
        """Con qué clave pedirle al backend la foto de esa persona.

        El paciente es `p1` en la sala pero su foto se sigue subiendo y
        guardando con la clave histórica del caso (persona vacía, ver
        _paciente.php y PatientPhoto::key), así que pedirla como `p1` daba
        404 y el paciente quedaba con iniciales aunque tuviera foto."""
        if persona_id == self._PACIENTE_ID:
            return ""
        persona = self._persona(persona_id)
        if persona is not None and persona.get("es_paciente"):
            return ""
        return persona_id

    def _pedir_avatar(self, persona_id):
        """Foto real de esa persona si tiene una subida (ver
        PatientPhoto.php) -- mientras tanto (o si no hay), queda el círculo
        con iniciales."""
        hilo = _AvatarFetchThread(self._case_id, persona_id, self._foto_key(persona_id), parent=self)
        hilo.listo.connect(lambda pid, data, cid=self._case_id: self._on_avatar_listo(cid, pid, data))
        # Se guardan todos: son varios en paralelo (uno por persona) y si se
        # pierde la referencia, Qt puede destruir el QThread a mitad de la
        # llamada de red.
        self._avatar_threads.append(hilo)
        hilo.finished.connect(lambda h=hilo: self._avatar_threads.remove(h) if h in self._avatar_threads else None)
        hilo.start()

    def _on_avatar_listo(self, case_id_solicitado, persona_id, data):
        if case_id_solicitado != self._case_id or not data:
            return  # sin foto, o el alumno ya cambió de paciente mientras se pedía
        pixmap = avatar_circular_desde_bytes(data, self.AVATAR_SIZE)
        if pixmap is not None:
            self._fotos[self._foto_key(persona_id)] = pixmap
            self._set_avatar(persona_id, pixmap)

    # -----------------------------------------------------------------
    # Transcripción
    # -----------------------------------------------------------------

    def _actualizar_encabezado(self):
        if len(self._sala) > 1:
            quienes = ", ".join(p["etiqueta"] for p in self._sala)
            texto = f"Atendiendo a {quienes} ({self._procedimiento or 'sin motivo registrado'})"
        else:
            texto = f"Conversando con {self._nombre} ({self._procedimiento or 'sin motivo registrado'})"
        self.lbl_paciente.setText(texto)

    def _burbuja_usuario(self, texto):
        texto_html = texto.replace("\n", "<br>")
        size = self.AVATAR_SIZE
        self.transcript.append(
            f'<table align="right" cellspacing="0" cellpadding="0" style="margin:3px 0;"><tr>'
            f'<td valign="top" style="background-color:#dcf8c6; border:1px solid #cdeeb5; '
            f'border-radius:9px; padding:6px 10px; max-width:340px;">{texto_html}</td>'
            f'<td valign="top" style="padding-left:6px;">'
            f'<img src="{self._AVATAR_USER_URL}" width="{size}" height="{size}"></td>'
            f'</tr></table>'
        )
        self._al_final()

    def _burbuja_persona(self, persona_id, etiqueta, texto):
        """Burbuja de quien habla, estilo WhatsApp de grupo: cara a la
        izquierda y el nombre arriba en su color. Con varias personas en la
        sala el color es lo que deja seguir quién dijo qué sin leer cada
        etiqueta."""
        self._asegurar_avatar(persona_id, etiqueta)
        texto_html = texto.replace("\n", "<br>")
        size = self.AVATAR_SIZE
        color = color_por_nombre(etiqueta).darker(140).name()
        self.transcript.append(
            f'<table align="left" cellspacing="0" cellpadding="0" style="margin:3px 0;"><tr>'
            f'<td valign="top" style="padding-right:6px;">'
            f'<img src="{self._avatar_url(persona_id)}" width="{size}" height="{size}"></td>'
            f'<td valign="top" style="background-color:#ffffff; border:1px solid #e2e2e2; '
            f'border-radius:9px; padding:6px 10px; max-width:340px;">'
            f'<span style="color:{color}; font-size:8pt; font-weight:bold;">{etiqueta}</span><br>'
            f'{texto_html}</td>'
            f'</tr></table>'
        )
        self._al_final()

    def _al_final(self):
        barra = self.transcript.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _mostrar_estado(self, texto):
        self.lbl_estado.setText(texto)
        self.lbl_estado.show()

    def _ocultar_estado(self):
        self.lbl_estado.hide()
        self.btn_reintentar.hide()

    # -----------------------------------------------------------------
    # Turnos
    # -----------------------------------------------------------------

    def _enviar(self):
        mensaje = self.input.text().strip()
        if not mensaje or self._thread is not None or not self._case_id:
            return
        self.input.clear()
        self._burbuja_usuario(mensaje)
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
        self._mostrar_estado("Pensando la respuesta…")
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

    def _on_respuesta(self, case_id_solicitado, mensaje, resultado):
        self.input.setEnabled(True)
        self.btn_enviar.setEnabled(True)
        self._mensaje_pendiente = None
        self._intentos = 0
        self._ocultar_estado()
        if case_id_solicitado != self._case_id:
            return  # el usuario cambió de paciente mientras esperaba la respuesta

        self._aplicar_sala(resultado.get("sala") or [])
        self._history.append({"role": "user", "content": mensaje})
        for r in resultado.get("respuestas") or []:
            etiqueta = r.get("etiqueta") or self._nombre
            persona_id = r.get("persona_id") or self._PACIENTE_ID
            texto = r.get("texto", "")
            # El historial va rotulado: el backend se lo pasa así a cada
            # personaje para que sepa quién dijo qué (ver llm_chat.php). Va
            # el id además de la etiqueta porque es lo que el modelo tiene
            # que escribir para decir quién habla; con solo el nombre volvía
            # a contestar rotulando el texto y las frases quedaban sin dueño.
            self._history.append({
                "role": "assistant", "content": texto,
                "speaker_label": etiqueta, "speaker_id": r.get("persona_id", ""),
            })
            self._burbuja_persona(persona_id, etiqueta, texto)

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
            self._mostrar_estado("No hubo respuesta. Puedes reintentar.")
            self.btn_reintentar.show()

    def _on_thread_finished(self):
        self._thread = None
        self.input.setFocus()
