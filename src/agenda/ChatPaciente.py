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
from PySide6.QtWidgets import QWidget, QComboBox, QMenu
from PySide6.QtWidgets import QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
from PySide6.QtCore import QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QTextDocument
from core.helpers import chat_con_paciente, foto_paciente, sala_del_caso
from core.avatar import avatar_iniciales, avatar_circular_desde_bytes, color_por_nombre


class _ChatPacienteThread(QThread):
    """Manda un turno de chat al backend (llamada de red) fuera del hilo de UI."""
    respondido = Signal(dict)
    fallo = Signal(str)

    def __init__(self, case_id, nombre, edad, procedimiento, history, message, appointment_id=None,
                 dirigido_a="", silenciados=None, fuera=None, salida_solicitada="", parent=None):
        super().__init__(parent)
        self._args = (case_id, nombre, edad, procedimiento, history, message, appointment_id)
        self._kwargs = {
            "dirigido_a": dirigido_a,
            "silenciados": silenciados or {},
            "fuera": fuera or [],
            "salida_solicitada": salida_solicitada,
        }

    def run(self):
        try:
            resultado = chat_con_paciente(*self._args, **self._kwargs)
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
    iniciales)."""
    listo = Signal(str, object)

    def __init__(self, case_id, persona_id, parent=None):
        super().__init__(parent)
        self._case_id = case_id
        self._persona_id = persona_id

    def run(self):
        # El paciente conserva la clave histórica del caso (persona vacía);
        # cada acompañante cuelga de su id -- ver PatientPhoto::key.
        persona = "" if self._persona_id == "__paciente__" else self._persona_id
        self.listo.emit(self._persona_id, foto_paciente(self._case_id, persona))


class ChatPacienteWidget(QWidget):
    """Chat de entrevista con la sala del caso: el paciente y quienes lo
    acompañan, todos simulados por LLM (ver Sala.php y LlmChat.php).

    No es un chat 1 a 1 con etiquetas: un lactante no cuenta su historia y
    la cuenta la madre, y un adulto que niega su hipoacusia es desmentido
    por quien vive con él. El alumno elige a quién le pregunta, pero los
    demás pueden meterse igual -- aprender a manejar eso (contener al que
    contesta por el otro, preguntarle al que sí puede saber) es parte de lo
    que se está evaluando.

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

        # Estado de la sala. El endpoint del chat no tiene sesión (cada turno
        # manda el historial completo), así que esto vive acá y viaja en cada
        # turno: a quién se contuvo y por cuántos turnos, quién quedó fuera.
        self._sala = []
        self._silenciados = {}
        self._fuera = []
        self._avatares = set()  # personas que ya tienen imagen cargada en el documento

        layout = QVBoxLayout(self)

        self.lbl_paciente = QLabel(self)
        self.lbl_paciente.setStyleSheet("font-weight: bold;")
        self.lbl_paciente.setWordWrap(True)
        layout.addWidget(self.lbl_paciente)

        fila_sala = QHBoxLayout()
        fila_sala.addWidget(QLabel("Le hablo a:", self))
        self.combo_destino = QComboBox(self)
        self.combo_destino.setMinimumWidth(200)
        fila_sala.addWidget(self.combo_destino)

        self.btn_salir = QPushButton("Pedir que salga…", self)
        self.btn_salir.setToolTip(
            "Pedirle a un acompañante que espere afuera del box.\n"
            "Al padre y a la madre no se les puede impedir estar presentes."
        )
        self.btn_salir.clicked.connect(self._menu_salida)
        fila_sala.addWidget(self.btn_salir)
        fila_sala.addStretch()
        layout.addLayout(fila_sala)
        self._fila_sala_widgets = (self.combo_destino, self.btn_salir)

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
        self._silenciados = {}
        self._fuera = []
        self._avatares = set()  # transcript.clear() más abajo borra también los avatares
        self.transcript.clear()  # ¡también borra los recursos (avatares) del documento, no solo el texto!
        self._ocultar_estado()
        self._actualizar_encabezado()
        self._registrar_avatar_usuario()
        # Respaldo mientras no llega la sala: el paciente con sus iniciales,
        # que es exactamente el chat 1 a 1 de antes.
        self._asegurar_avatar(self._PACIENTE_ID, self._nombre)
        self._poblar_destinos()
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
        for persona in self._presentes():
            self._asegurar_avatar(persona["id"], persona["etiqueta"])

    def _aplicar_sala(self, sala):
        """Guarda la sala que devolvió el backend y repinta el encabezado y
        el selector. El backend es la autoridad: si el alumno pidió sacar a
        alguien que no se puede sacar, esa persona vuelve marcada como
        presente."""
        if not sala:
            return
        self._sala = sala
        self._fuera = [p["id"] for p in sala if not p["presente"]]
        self._actualizar_encabezado()
        self._poblar_destinos()

    def _presentes(self):
        return [p for p in self._sala if p["presente"]]

    def _persona(self, persona_id):
        for p in self._sala:
            if p["id"] == persona_id:
                return p
        return None

    def _poblar_destinos(self):
        """Selector de a quién le habla el alumno. Con una sola persona en
        la sala (el caso de siempre) no hay nada que elegir, así que la fila
        entera se esconde en vez de dejar un combo de un solo ítem."""
        presentes = self._presentes()
        anterior = self.combo_destino.currentData()

        self.combo_destino.blockSignals(True)
        self.combo_destino.clear()
        self.combo_destino.addItem("A la sala (a quien corresponda)", "")
        for p in presentes:
            etiqueta = p["etiqueta"]
            if not p["habla"]:
                etiqueta += " — no habla todavía"
            elif p["informante"]:
                etiqueta += " — cuenta la historia"
            self.combo_destino.addItem(etiqueta, p["id"])
        idx = self.combo_destino.findData(anterior)
        self.combo_destino.setCurrentIndex(max(0, idx))
        self.combo_destino.blockSignals(False)

        hay_sala = len(presentes) > 1 or len(self._sala) > 1
        for w in self._fila_sala_widgets:
            w.setVisible(hay_sala)
        self.btn_salir.setEnabled(any(not p["obligatorio"] for p in presentes))

    def _menu_salida(self):
        """A quién se le puede pedir que espere afuera. El paciente y sus
        padres no aparecen: no es una opción que el alumno tenga."""
        menu = QMenu(self)
        for p in self._presentes():
            if p["obligatorio"]:
                continue
            accion = menu.addAction(p["etiqueta"])
            accion.triggered.connect(lambda _=False, pid=p["id"]: self._pedir_salida(pid))
        if menu.isEmpty():
            menu.addAction("Nadie puede salir del box").setEnabled(False)
        menu.exec(self.btn_salir.mapToGlobal(self.btn_salir.rect().bottomLeft()))

    def _pedir_salida(self, persona_id):
        if self._thread is not None or not self._case_id:
            return
        persona = self._persona(persona_id)
        if persona is None:
            return
        self._agregar_sistema(f"Le pides a {persona['etiqueta']} que espere afuera del box.")
        self._despachar("", salida_solicitada=persona_id)

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
        self._set_avatar(persona_id, avatar_iniciales(etiqueta, self.AVATAR_SIZE))
        self._pedir_avatar(persona_id)

    def _set_avatar(self, persona_id, pixmap):
        self.transcript.document().addResource(
            QTextDocument.ImageResource, QUrl(self._avatar_url(persona_id)), pixmap.toImage()
        )

    def _pedir_avatar(self, persona_id):
        """Foto real de esa persona si tiene una subida (ver
        PatientPhoto.php) -- mientras tanto (o si no hay), queda el círculo
        con iniciales."""
        hilo = _AvatarFetchThread(self._case_id, persona_id, parent=self)
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
            self._set_avatar(persona_id, pixmap)

    # -----------------------------------------------------------------
    # Transcripción
    # -----------------------------------------------------------------

    def _actualizar_encabezado(self):
        presentes = self._presentes()
        if len(presentes) > 1:
            quienes = ", ".join(p["etiqueta"] for p in presentes)
            texto = f"En el box: {quienes} ({self._procedimiento or 'sin motivo registrado'})"
            fuera = [p["etiqueta"] for p in self._sala if not p["presente"]]
            if fuera:
                texto += " — esperando afuera: " + ", ".join(fuera)
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

    def _agregar_sistema(self, texto):
        """Lo que pasa en el box y no lo dice nadie: alguien sale, o el
        backend rechaza sacar a un padre."""
        self.transcript.append(
            f'<p align="center" style="color:#7a7a7a; font-size:8pt; margin:6px 0;"><i>{texto}</i></p>'
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

    def _despachar(self, mensaje, salida_solicitada=""):
        """Manda `mensaje` al backend -- puede ser el recién escrito o un reintento
        del último que falló (mismo texto, no se duplica burbuja de usuario)."""
        self._mensaje_pendiente = mensaje or None
        self.btn_reintentar.hide()
        if not salida_solicitada:
            self._mostrar_estado("Están pensando su respuesta…")
        self.input.setEnabled(False)
        self.btn_enviar.setEnabled(False)

        case_id_solicitado = self._case_id
        self._thread = _ChatPacienteThread(
            self._case_id, self._nombre, self._edad, self._procedimiento,
            list(self._history), mensaje, appointment_id=self._appointment_id,
            dirigido_a=self.combo_destino.currentData() or "",
            silenciados=dict(self._silenciados), fuera=list(self._fuera),
            salida_solicitada=salida_solicitada, parent=self,
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
        self._silenciados = resultado.get("silenciados") or {}

        for aviso in resultado.get("avisos") or []:
            self._agregar_sistema(aviso)

        if mensaje:
            self._history.append({"role": "user", "content": mensaje})
        for r in resultado.get("respuestas") or []:
            etiqueta = r.get("etiqueta") or self._nombre
            persona_id = r.get("persona_id") or self._PACIENTE_ID
            texto = r.get("texto", "")
            # El historial va rotulado: el backend se lo pasa así a cada
            # personaje para que sepa quién dijo qué (ver llm_chat.php).
            self._history.append({
                "role": "assistant", "content": texto, "speaker_label": etiqueta,
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
        if mensaje and self._intentos < self.REINTENTOS_AUTOMATICOS:
            self._intentos += 1
            self._mostrar_estado("Sin respuesta todavía, reintentando…")
            QTimer.singleShot(1500, lambda: self._despachar(mensaje))
        else:
            self._mostrar_estado("No hubo respuesta. Puedes reintentar.")
            self.btn_reintentar.show()

    def _on_thread_finished(self):
        self._thread = None
        self.input.setFocus()
