# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 0.9 - Audiometro                   #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

import re

from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)
from PySide6.QtCore import QEvent, Qt, QTimer
from agenda.vista import BotonAccion
from core.helpers import chat_con_paciente, foto_paciente, sala_del_caso
from core import hilos, iconos, tema
from core.avatar import avatar_iniciales, avatar_circular_desde_bytes, color_por_nombre


# Las tres consultas corren con hilos.en_fondo (sin QThread: ver los
# cierres del 2026-10-09 en core/hilos.py). chat_con_paciente lanza
# RuntimeError o requests.RequestException si no hubo respuesta; la sala y
# las fotos devuelven vacío/None sin conexión (no es una falla).


QSS_CHAT = f"""
QWidget#listaChat {{ background: {tema.FONDO}; }}
QFrame#burbujaPropia {{
    background: {tema.ACENTO_SUAVE}; border: 1px solid #E3CFDD; border-radius: 12px;
}}
QFrame#burbujaOtro {{
    background: {tema.TARJETA}; border: 1px solid {tema.BORDE}; border-radius: 12px;
}}
QFrame#burbujaPropia QLabel, QFrame#burbujaOtro QLabel {{ background: transparent; border: none; }}
QLabel#vacioChat {{
    color: {tema.TEXTO_SUAVE}; font-size: 9pt; background: {tema.TARJETA};
    border: 1px dashed {tema.BORDE_FUERTE}; border-radius: 12px; padding: 18px;
}}
QLineEdit#entradaChat {{
    background: {tema.TARJETA}; border: 1px solid {tema.BORDE_FUERTE}; border-radius: 19px;
    padding: 8px 14px; font-size: 10pt;
}}
QLineEdit#entradaChat:focus {{ border-color: {tema.ACENTO}; }}
QLineEdit#entradaChat:disabled {{ background: {tema.TARJETA_ALT}; color: {tema.TEXTO_TENUE}; }}
QPushButton#btnEnviar {{
    background: {tema.ACENTO}; border: none; border-radius: 19px; padding: 0;
}}
QPushButton#btnEnviar:hover {{ background: {tema.ACENTO_CLARO}; }}
QPushButton#btnEnviar:disabled {{ background: {tema.BORDE_FUERTE}; }}
QLabel#estadoChat {{ color: {tema.TEXTO_SUAVE}; font-size: 8.5pt; }}
"""

# Las burbujas ocupan como mucho esta fracción del ancho visible.
FRACCION_BURBUJA = 0.72


class _ListaMensajes(QScrollArea):
    """Lista de burbujas con scroll. Ninguna fila ocupa más de
    FRACCION_BURBUJA del ancho, así que el texto se parte solo cuando la
    ventana es angosta en vez de salirse o quedar apretado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.contenido = QWidget()
        self.contenido.setObjectName("listaChat")
        self.fila = QVBoxLayout(self.contenido)
        self.fila.setContentsMargins(12, 12, 12, 12)
        self.fila.setSpacing(10)
        self.fila.addStretch(1)
        self.setWidget(self.contenido)
        self._burbujas = []
        # Cada vez que crece el contenido, se baja al último mensaje.
        self._pegado = True
        self.verticalScrollBar().rangeChanged.connect(self._al_cambiar_rango)

    def ancho_maximo(self):
        return max(160, int(self.viewport().width() * FRACCION_BURBUJA))

    def agregar(self, fila, burbuja=None):
        self.fila.insertWidget(self.fila.count() - 1, fila)
        if burbuja is not None:
            _ajustar(burbuja, self.ancho_maximo())
            self._burbujas.append(burbuja)
        self._pegado = True

    def vaciar(self):
        self._burbujas = []
        # El aviso de "conversación vacía" se queda: solo se esconde y se muestra.
        for i in reversed(range(self.fila.count())):
            w = self.fila.itemAt(i).widget()
            if w is not None and w.objectName() != "vacioChat":
                self.fila.takeAt(i)
                w.hide()
                w.deleteLater()

    def _al_cambiar_rango(self, _minimo, maximo):
        if self._pegado:
            self.verticalScrollBar().setValue(maximo)

    def wheelEvent(self, event):
        # Si el alumno sube a leer, no se le baja de vuelta con cada mensaje.
        super().wheelEvent(event)
        barra = self.verticalScrollBar()
        self._pegado = barra.value() >= barra.maximum() - 4

    def resizeEvent(self, event):
        super().resizeEvent(event)
        ancho = self.ancho_maximo()
        for burbuja in self._burbujas:
            _ajustar(burbuja, ancho)


def _ajustar(burbuja, ancho_disponible):
    """Ancho de la burbuja y alto exacto de su texto a ese ancho. Sin fijar el
    alto, un QLabel con saltos de línea automáticos le pide al scroll el alto
    de su peor caso (angosto) y quedaba un hueco bajo el último mensaje."""
    ancho = min(burbuja.ancho_natural, ancho_disponible)
    burbuja.setFixedWidth(ancho)
    burbuja.cuerpo.setFixedHeight(burbuja.cuerpo.heightForWidth(ancho - 12 - 12 - 2))


def _burbuja(texto, propia, etiqueta=None, color=None):
    """Una burbuja redondeada: texto plano (lo que dice el modelo no se
    interpreta como HTML), seleccionable, con el nombre arriba si habla otro."""
    marco = QFrame()
    marco.setObjectName("burbujaPropia" if propia else "burbujaOtro")
    col = QVBoxLayout(marco)
    col.setContentsMargins(12, 8, 12, 9)
    col.setSpacing(2)
    if etiqueta:
        nombre = QLabel(etiqueta)
        nombre.setStyleSheet(f"color: {color}; font-size: 8pt; font-weight: 700;")
        col.addWidget(nombre)
    # Una palabra sin espacios (un enlace, "jajajaja...") no se parte sola y
    # se salía de la burbuja: se le dan puntos de corte invisibles.
    cuerpo = QLabel(re.sub(r"(\S{24})", "\\1\u200b", texto))
    cuerpo.setTextFormat(Qt.TextFormat.PlainText)
    cuerpo.setWordWrap(True)
    cuerpo.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    cuerpo.setStyleSheet(f"color: {tema.TEXTO}; font-size: 10pt;")
    col.addWidget(cuerpo)
    marco.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
    # Ancho que ocuparía el texto sin partirlo: un QLabel con saltos de línea
    # automáticos pide poco ancho y la burbuja salía angosta y alta.
    metricas = cuerpo.fontMetrics()
    lineas = (texto.splitlines() or [""]) + ([etiqueta] if etiqueta else [])
    marco.cuerpo = cuerpo
    marco.ancho_natural = max(metricas.horizontalAdvance(linea) for linea in lineas) + 12 + 12 + 6
    return marco


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
    _PACIENTE_ID = "__paciente__"  # id de respaldo mientras no se sabe quién es quién en la sala

    def __init__(self, usuario_nombre=None, parent=None):
        super().__init__(parent)
        self._case_id = None
        self._appointment_id = None
        self._nombre = "el paciente"
        self._usuario_nombre = usuario_nombre or "Tú"
        self._edad = 0
        self._procedimiento = ""
        self._trae_audiometria = False
        self._history = []
        self._thread = None
        self._sala_thread = None
        self._mensaje_pendiente = None  # último mensaje enviado, para reintentar sin retipear
        self._intentos = 0

        # Quiénes están en la consulta. Solo se usa para mostrar: la cara y
        # el nombre de cada burbuja, y el encabezado. Quién contesta cada
        # pregunta lo decide el modelo, no el cliente.
        self._sala = []
        self._avatares = set()  # personas que ya tienen su cara lista
        self._fotos = {}  # clave de foto -> pixmap ya traído (el paciente aparece como __paciente__ y como p1)
        self._caras = {}  # persona_id -> pixmap que se muestra hoy
        self._etiquetas_cara = {}  # persona_id -> los QLabel que la muestran (burbujas y encabezado)

        tema.aplicar_estilo(self, QSS_CHAT)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Encabezado: la cara del paciente, con quién se habla y por qué consulta.
        cabecera = QFrame(self)
        cabecera.setProperty("card", "true")
        fila_cab = QHBoxLayout(cabecera)
        fila_cab.setContentsMargins(14, 10, 14, 10)
        fila_cab.setSpacing(12)
        self.cara_encabezado = QLabel()
        self.cara_encabezado.setFixedSize(40, 40)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.lbl_paciente = QLabel(self)
        self.lbl_paciente.setProperty("role", "titulo")
        self.lbl_paciente.setWordWrap(True)
        self.lbl_motivo = QLabel(self)
        self.lbl_motivo.setProperty("role", "campo")
        self.lbl_motivo.setWordWrap(True)
        textos.addWidget(self.lbl_paciente)
        textos.addWidget(self.lbl_motivo)
        fila_cab.addWidget(self.cara_encabezado)
        fila_cab.addLayout(textos, 1)
        layout.addWidget(cabecera)

        self.lista = _ListaMensajes(self)
        layout.addWidget(self.lista, 1)
        self.vacio = QLabel(
            "Aquí aparecerá la conversación.\nEscribe tu primera pregunta; si hay acompañantes, "
            "di a quién te diriges («señora, ¿desde cuándo lo nota?»).", self)
        self.vacio.setObjectName("vacioChat")
        self.vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vacio.setWordWrap(True)
        self.vacio.setMinimumHeight(96)
        self.vacio.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.lista.fila.insertWidget(0, self.vacio)

        fila_estado = QHBoxLayout()
        fila_estado.setSpacing(6)
        self.icono_estado = QLabel()
        self.icono_estado.setPixmap(iconos.pixmap("reloj", tema.TEXTO_SUAVE, 16))
        self.lbl_estado = QLabel(self)
        self.lbl_estado.setObjectName("estadoChat")
        self.btn_reintentar = BotonAccion("Reintentar", "practica", parent=self)
        self.btn_reintentar.clicked.connect(self._reintentar_manual)
        fila_estado.addWidget(self.icono_estado)
        fila_estado.addWidget(self.lbl_estado, 1)
        fila_estado.addWidget(self.btn_reintentar)
        self._fila_estado = (self.icono_estado, self.lbl_estado)
        for w in (*self._fila_estado, self.btn_reintentar):
            w.hide()
        layout.addLayout(fila_estado)

        fila_input = QHBoxLayout()
        fila_input.setSpacing(8)
        self.input = QLineEdit(self)
        self.input.setObjectName("entradaChat")
        self.input.setPlaceholderText("Escribe tu pregunta al paciente...")
        self.input.returnPressed.connect(self._enviar)
        fila_input.addWidget(self.input, 1)

        self.btn_enviar = QPushButton(self)
        self.btn_enviar.setObjectName("btnEnviar")
        self.btn_enviar.setToolTip("Enviar (Enter)")
        self.btn_enviar.setFixedSize(38, 38)
        self.btn_enviar.setIcon(iconos.icono("enviar", "#FFFFFF", 20))
        self.btn_enviar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enviar.clicked.connect(self._enviar)
        fila_input.addWidget(self.btn_enviar)
        layout.addLayout(fila_input)

        self._actualizar_encabezado()

    def set_paciente(self, case_id, nombre, edad, procedimiento, appointment_id=None,
                     trae_audiometria=False):
        """Reapunta el chat a otro caso -- descarta la conversación anterior.

        appointment_id: cita real a la que se asocia lo que se guarde del
        chat (ver LlmChat.php) -- None = no se guarda nada (p.ej. "Atender
        (prueba)" del admin, que no debe dejar rastro).
        trae_audiometria: el paciente llega con la audiometría hecha (la
        ficha la muestra, ver core.ficha.audiometria_previa) y lo sabe."""
        self._case_id = case_id
        self._trae_audiometria = bool(trae_audiometria)
        self._appointment_id = appointment_id
        self._nombre = nombre or "el paciente"
        self._edad = edad
        self._procedimiento = procedimiento
        self._history = []
        self._mensaje_pendiente = None
        self._intentos = 0
        self._sala = []
        self._avatares = set()
        self._fotos = {}
        self._caras = {}
        self._etiquetas_cara = {}
        self.lista.vaciar()
        self.vacio.show()
        self._ocultar_estado()
        self._actualizar_encabezado()
        # Respaldo mientras no llega la sala: el paciente con sus iniciales,
        # que es exactamente el chat 1 a 1 de antes.
        self._asegurar_avatar(self._PACIENTE_ID, self._nombre)
        self._poner_cara(self.cara_encabezado, self._PACIENTE_ID, 40)
        self._pedir_sala()
        self.input.setFocus()

    # -----------------------------------------------------------------
    # Sala
    # -----------------------------------------------------------------

    def _pedir_sala(self):
        self._sala_thread = hilos.en_fondo(
            sala_del_caso, self._case_id, self._nombre, self._edad, dueno=self, nombre="sala",
            listo=lambda sala, cid=self._case_id: self._on_sala_lista(cid, sala))

    def _on_sala_lista(self, case_id_solicitado, sala):
        if case_id_solicitado != self._case_id:
            return  # el alumno cambió de paciente mientras se pedía
        self._aplicar_sala(sala)
        for persona in self._sala:
            self._asegurar_avatar(persona["id"], persona["etiqueta"])
            if persona.get("es_paciente"):
                self._poner_cara(self.cara_encabezado, persona["id"], 40)

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

    _CARA_USUARIO = "__usuario__"

    def _poner_cara(self, etiqueta_qlabel, persona_id, lado):
        """Muestra la cara de `persona_id` en un QLabel y lo anota para
        cambiarla si después llega la foto real."""
        pixmap = self._caras.get(persona_id)
        if pixmap is not None:
            etiqueta_qlabel.setPixmap(pixmap.scaled(
                lado, lado, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        # El encabezado puede cambiar de persona (respaldo -> p1): se saca de
        # las demás listas para que no lo pise una cara que ya no le toca.
        for pid, lista in self._etiquetas_cara.items():
            if pid != persona_id:
                lista[:] = [(e, l) for e, l in lista if e is not etiqueta_qlabel]
        lista = self._etiquetas_cara.setdefault(persona_id, [])
        if not any(e is etiqueta_qlabel for e, _ in lista):
            lista.append((etiqueta_qlabel, lado))

    def _cara_nueva(self, persona_id):
        """Un QLabel redondo con la cara de esa persona, para una burbuja."""
        etiqueta = QLabel()
        etiqueta.setFixedSize(self.AVATAR_SIZE, self.AVATAR_SIZE)
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._poner_cara(etiqueta, persona_id, self.AVATAR_SIZE)
        return etiqueta

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
        self._caras[persona_id] = pixmap
        # Si la foto llegó después de la burbuja, se cambia la cara ya mostrada.
        for etiqueta, lado in self._etiquetas_cara.get(persona_id, []):
            etiqueta.setPixmap(pixmap.scaled(
                lado, lado, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

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
        hilos.en_fondo(
            foto_paciente, self._case_id, self._foto_key(persona_id), dueno=self, nombre="avatar",
            listo=lambda data, pid=persona_id, cid=self._case_id: self._on_avatar_listo(cid, pid, data))

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
        motivo = self._procedimiento or "sin motivo registrado"
        if len(self._sala) > 1:
            quienes = ", ".join(p["etiqueta"] for p in self._sala)
            self.lbl_paciente.setText(f"Atendiendo a {quienes}")
        else:
            self.lbl_paciente.setText(f"Conversando con {self._nombre}")
        self.lbl_motivo.setText(f"Motivo: {motivo}")

    def _agregar_fila(self, burbuja, propia, persona_id):
        """Pone una burbuja con su cara en la lista: las propias a la derecha
        y las de los demás a la izquierda."""
        self.vacio.hide()
        self.lista.fila.invalidate()
        fila = QWidget()
        h = QHBoxLayout(fila)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        cara = self._cara_nueva(persona_id)
        if propia:
            h.addStretch(1)
            h.addWidget(burbuja, 0, Qt.AlignmentFlag.AlignTop)
            h.addWidget(cara, 0, Qt.AlignmentFlag.AlignTop)
        else:
            h.addWidget(cara, 0, Qt.AlignmentFlag.AlignTop)
            h.addWidget(burbuja, 0, Qt.AlignmentFlag.AlignTop)
            h.addStretch(1)
        self.lista.agregar(fila, burbuja)

    def _burbuja_usuario(self, texto):
        if self._CARA_USUARIO not in self._caras:
            self._caras[self._CARA_USUARIO] = avatar_iniciales(self._usuario_nombre, self.AVATAR_SIZE)
        self._agregar_fila(_burbuja(texto, True), True, self._CARA_USUARIO)

    def _burbuja_persona(self, persona_id, etiqueta, texto):
        """Burbuja de quien habla, estilo WhatsApp de grupo: cara a la
        izquierda y el nombre arriba en su color. Con varias personas en la
        sala el color es lo que deja seguir quién dijo qué sin leer cada
        etiqueta."""
        self._asegurar_avatar(persona_id, etiqueta)
        color = color_por_nombre(etiqueta).darker(140).name()
        self._agregar_fila(_burbuja(texto, False, etiqueta, color), False, persona_id)

    def _mostrar_estado(self, texto):
        self.lbl_estado.setText(texto)
        for w in self._fila_estado:
            w.show()

    def _ocultar_estado(self):
        for w in (*self._fila_estado, self.btn_reintentar):
            w.hide()

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
        self._thread = hilos.en_fondo(
            chat_con_paciente, self._case_id, self._nombre, self._edad, self._procedimiento,
            list(self._history), mensaje, self._appointment_id, self._trae_audiometria,
            dueno=self, nombre="chat",
            listo=lambda r: self._on_thread_finished(
                self._on_respuesta, case_id_solicitado, mensaje, r),
            fallo=lambda e: self._on_thread_finished(
                self._on_fallo, case_id_solicitado, mensaje, str(e)))

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
            # Con self de contexto: si la ventana se borra (cierre de
            # sesión) el reintento no corre sobre un widget destruido.
            QTimer.singleShot(1500, self, lambda: self._despachar(mensaje))
        else:
            self._mostrar_estado("No hubo respuesta. Puedes reintentar.")
            self.btn_reintentar.show()

    def _on_thread_finished(self, aviso, *args):
        aviso(*args)
        self._thread = None
        self.input.setFocus()
