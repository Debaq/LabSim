# -*- coding: utf-8 -*-
"""Karime, la secretaria: avisos emergentes dentro del MDI durante la
atención.

Al presionar "Atender" se programan hasta tres avisos (minutos desde ese
momento, configurables por curso en admin -> Cursos, key "secretaria.avisos"
de app_config, ver CourseParams.php). Cada aviso aparece abajo a la derecha
del MDI unos segundos y se va solo: es la secretaria que asoma la cabeza
para avisar que el paciente siguiente ya llegó, y que apura al alumno.

Si el alumno tiene otra cita pendiente ese mismo día, Karime la nombra (es
un paciente real de su agenda). Si no, el aviso habla del tiempo que lleva
la atención: no se inventa un paciente que el alumno después no encuentra.
Cada aviso sortea entre muchas variantes (editables por curso, una por
línea en admin): el resto de la app conversa con IA y una secretaria que
dice siempre la misma frase se nota enseguida.

Sin sonido a propósito: la app tiene audiometría con audífonos puestos y un
"ding" en medio de un umbral contamina la prueba.
"""

import json
import random

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QToolButton, QVBoxLayout)

from core.avatar import avatar_circular_desde_bytes, avatar_iniciales
from core.base import context
from core import agenda_relativa, app_config_store
from core.borrado import borrar_luego

NOMBRE = "Karime"
# Su foto de perfil, la misma de la versión Tauri (tauri-app/public/
# img_karime.jpeg, 2026-03-22), recortada a la cara.
FOTO = "img/karime.jpg"
CONFIG_KEY = "secretaria.avisos"
DURACION_MS = 9000
FADE_MS = 350
MARGEN = 16
SEPARACION = 8
TIPOS = ("con_paciente", "sin_paciente")
# Último recurso si todas las variantes de un aviso piden datos que no hay.
_DEFAULT_SEGURO = {
    "con_paciente": ["{nombre} ya llegó y está en la sala de espera."],
    "sin_paciente": ["Ya van {minutos} minutos de atención."],
}


def foto_karime(size=40):
    """La foto de Karime en círculo, o sus iniciales si no está."""
    try:
        with open(context.get_resource(FOTO), "rb") as archivo:
            # Al doble y con devicePixelRatio 2: nítida también en pantallas
            # de alta densidad.
            foto = avatar_circular_desde_bytes(archivo.read(), size * 2)
        if foto is not None:
            foto.setDevicePixelRatio(2)
    except OSError:
        foto = None
    return foto if foto is not None else avatar_iniciales(NOMBRE, size)


def _defaults():
    with open(context.get_resource("json/secretaria_avisos.json"), encoding="utf-8") as archivo:
        return json.load(archivo)["avisos"]


def config_avisos(override=None):
    """Los avisos en orden, cada uno {"min", "con_paciente", "sin_paciente"}:
    el default de la app con lo que el curso sobreescribió encima (override
    = {"avisos": {"aviso_N": {campo: valor}}}, como lo guarda
    CourseParams::parse). min 0 apaga ese aviso. Una lista de textos vacía o
    rota no deja al aviso mudo: queda la del default."""
    avisos = _defaults()
    propios = (override or {}).get("avisos") or {}
    config = []
    for clave in sorted(avisos):
        default, curso = avisos[clave], propios.get(clave) or {}
        try:
            minutos = max(0.0, float(curso.get("min", default["min"])))
        except (TypeError, ValueError):
            minutos = float(default["min"])
        aviso = {"min": minutos}
        for tipo in TIPOS:
            textos = curso.get(tipo)
            if isinstance(textos, list):
                textos = [t.strip() for t in textos if isinstance(t, str) and t.strip()]
            aviso[tipo] = textos or default[tipo]
        config.append(aviso)
    return config


def siguiente_paciente(agenda, key_actual, username):
    """La cita pendiente más temprana del alumno el mismo día que la que
    está atendiendo -- quien "ya llegó" a la sala de espera. None si no hay
    (o si la atención actual no tiene fecha, como un caso sin agendar)."""
    actual = agenda.get(key_actual)
    if actual is None or not actual.fecha:
        return None
    if getattr(actual, "practice_id", None) is not None:
        return None   # práctica libre: nadie espera en la sala
    # Agenda relativa: solo nombra a quien ya llegó a la sala de espera, y
    # con la hora de su turno (core/agenda_relativa.py).
    pendientes = [
        e for k, e in agenda.items()
        if k != key_actual and not e.sin_cita and e.fecha == actual.fecha and e.hora
        and getattr(e, "practice_id", None) is None
        and not e.atencion.get(username)
        and not agenda_relativa.todavia_no_llega(e)
    ]
    if not pendientes:
        return None
    cita = min(pendientes, key=lambda e: agenda_relativa.hora_vista(e))
    nombre = f"{cita.nombre} {cita.apellido}".strip() or "el paciente siguiente"
    return {"nombre": nombre, "hora": agenda_relativa.hora_vista(cita)[:5]}


def _rellenar(plantilla, valores):
    """Reemplaza {nombre}/{hora}/{minutos} a mano y no con str.format: el
    texto lo escribe el docente y una llave suelta no puede romper el
    aviso. None si la plantilla pide un dato que no hay (un {nombre} sin
    paciente siguiente)."""
    for clave in ("nombre", "hora", "minutos"):
        marca = "{" + clave + "}"
        if marca in plantilla:
            if valores.get(clave) is None:
                return None
            plantilla = plantilla.replace(marca, str(valores[clave]))
    return plantilla


def texto_aviso(aviso, minutos, siguiente, rng=random, evitar=None):
    """Lo que dice Karime: una variante al azar de las del aviso (ver
    config_avisos), con o sin paciente siguiente. `evitar` es la frase que
    dijo la vez anterior en este mismo aviso, para no repetirla seguido."""
    tipo = "con_paciente" if siguiente else "sin_paciente"
    valores = {"minutos": int(round(minutos))}
    if siguiente:
        valores.update(nombre=siguiente["nombre"], hora=siguiente["hora"])
    textos = [t for t in (_rellenar(p, valores) for p in aviso[tipo]) if t]
    if not textos:
        # El docente dejó solo plantillas con datos que acá no hay.
        textos = [t for t in (_rellenar(p, valores) for p in _DEFAULT_SEGURO[tipo]) if t]
    candidatos = [t for t in textos if t != evitar] or textos
    return rng.choice(candidatos)


# ---------------------------------------------------------------------------
# Agenda relativa (core/agenda_relativa.py): Karime sigue el horario del
# alumno, no los minutos desde "Atender". Anuncia cada llegada, apura al que
# deja esperar a un paciente pasado su turno, al que se pasa de la duración
# de la atención y al que se queda en el box después de su bloque.
# ---------------------------------------------------------------------------
CONFIG_AGENDA_KEY = "secretaria.agenda"
TIPOS_AGENDA = ("llegada", "atrasado", "pasado", "box")
# Umbrales en minutos (desde el inicio del turno, desde que se cumple la
# duración, desde el fin del bloque). Después del último se repite cada
# tanto. Solo se dice el umbral más alto cruzado: quien abre la app tarde no
# recibe la cola entera de avisos viejos.
UMBRALES = {"atrasado": ((5, 15), 15), "pasado": ((0,), 10), "box": ((0,), 10)}
TIC_AGENDA_MS = 20_000


def _defaults_agenda():
    with open(context.get_resource("json/secretaria_agenda.json"), encoding="utf-8") as archivo:
        return json.load(archivo)["avisos"]


def config_agenda(override=None):
    """{tipo: [frases]}: las de la app con las del curso encima (override =
    {"avisos": {tipo: {"textos": [...]}}}, como lo guarda CourseParams)."""
    defaults = _defaults_agenda()
    propios = (override or {}).get("avisos") or {}
    config = {}
    for tipo in TIPOS_AGENDA:
        textos = (propios.get(tipo) or {}).get("textos")
        if isinstance(textos, list):
            textos = [t.strip() for t in textos if isinstance(t, str) and t.strip()]
        config[tipo] = textos or defaults[tipo]["textos"]
    return config


def _umbral(tipo, minutos):
    """El umbral más alto cruzado con `minutos`, o None si no cruzó ninguno."""
    fijos, cada = UMBRALES[tipo]
    if minutos < fijos[0]:
        return None
    if minutos < fijos[-1] + cada:
        return max(u for u in fijos if u <= minutos)
    return fijos[-1] + int((minutos - fijos[-1]) // cada) * cada


def _estado(entry, username):
    return (entry.atencion.get(username) or {}).get("estado")


def eventos_agenda(agenda, username, ahora, key_activa=None, segundos_atencion=0.0):
    """Lo que Karime tendría para decir ahora, en orden de prioridad:
    [(clave_unica, tipo, valores)]. Quien llama descarta las claves ya
    dichas. Solo mira las citas con turno calculado (agenda relativa)."""
    turnos = [(k, e) for k, e in agenda.items() if getattr(e, "turno_inicio", None) is not None]
    if not turnos:
        return []
    eventos = []

    def nombre(e):
        return f"{e.nombre} {e.apellido}".strip() or "tu paciente"

    pendientes = [(k, e) for k, e in turnos if _estado(e, username) not in ("atendiendo", "atendido", "no_show")]
    for k, e in sorted(pendientes, key=lambda par: par[1].llegada):
        if e.llegada <= ahora:
            eventos.append((("llegada", k), "llegada", {"nombre": nombre(e), "hora": f"{e.turno_inicio:%H:%M}"}))

    fin_box = max(e.turno_fin for _, e in turnos)
    activa = agenda.get(key_activa) if key_activa is not None else None
    activa_relativa = activa is not None and getattr(activa, "turno_inicio", None) is not None
    if ahora >= fin_box and (pendientes or activa_relativa):
        u = _umbral("box", (ahora - fin_box).total_seconds() / 60)
        eventos.append((("box", u), "box", {"hora": f"{fin_box:%H:%M}"}))

    if activa_relativa and activa.duracion_min:
        u = _umbral("pasado", segundos_atencion / 60 - activa.duracion_min)
        if u is not None:
            eventos.append((("pasado", key_activa, u), "pasado",
                            {"nombre": nombre(activa), "minutos": int(activa.duracion_min)}))

    for k, e in sorted(pendientes, key=lambda par: par[1].turno_inicio):
        if k == key_activa:
            continue
        tarde = (ahora - e.turno_inicio).total_seconds() / 60
        u = _umbral("atrasado", tarde)
        if u is not None:
            eventos.append((("atrasado", k, u), "atrasado",
                            {"nombre": nombre(e), "hora": f"{e.turno_inicio:%H:%M}", "minutos": int(tarde)}))
    return eventos


def texto_agenda(frases, valores, rng=random, evitar=None):
    textos = [t for t in (_rellenar(f, valores) for f in frases) if t] or ["Te aviso desde recepción."]
    return rng.choice([t for t in textos if t != evitar] or textos)


class AvisoSecretaria(QFrame):
    """Un aviso flotante. Hijo del QMdiArea (no del viewport): así queda
    encima de todas las subventanas aunque el alumno active otra mientras
    está a la vista. Se cierra solo o con la ✕."""

    def __init__(self, area, texto, al_cerrar):
        super().__init__(area)
        self._al_cerrar = al_cerrar
        self._cerrando = False
        self.setObjectName("aviso_secretaria")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedWidth(340)
        self.setStyleSheet("""
            #aviso_secretaria { background: #ffffff; border: 1px solid #c9d3e0;
                                border-left: 4px solid #E0679B; border-radius: 6px; }
            #aviso_secretaria QLabel { background: transparent; border: none; color: #1f2933; }
            #aviso_titulo { font-weight: bold; }
            #aviso_cerrar { border: none; background: transparent; color: #6b7785; }
        """)

        avatar = QLabel(self)
        avatar.setPixmap(foto_karime(40))
        avatar.setFixedSize(40, 40)

        titulo = QLabel(f"{NOMBRE} · Secretaría", self)
        titulo.setObjectName("aviso_titulo")
        cuerpo = QLabel(texto, self)
        cuerpo.setObjectName("aviso_texto")
        cuerpo.setWordWrap(True)

        cerrar = QToolButton(self)
        cerrar.setObjectName("aviso_cerrar")
        cerrar.setText("✕")
        cerrar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cerrar.clicked.connect(self.cerrar)

        textos = QVBoxLayout()
        textos.setSpacing(2)
        textos.addWidget(titulo)
        textos.addWidget(cuerpo)

        fila = QHBoxLayout(self)
        fila.setContentsMargins(10, 10, 6, 10)
        fila.setSpacing(10)
        fila.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
        fila.addLayout(textos, 1)
        fila.addWidget(cerrar, 0, Qt.AlignmentFlag.AlignTop)

        self._opacidad = QGraphicsOpacityEffect(self)
        self._opacidad.setOpacity(0.0)
        self.setGraphicsEffect(self._opacidad)
        self._anim = QPropertyAnimation(self._opacidad, b"opacity", self)
        self._anim.setDuration(FADE_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._vida = QTimer(self)
        self._vida.setSingleShot(True)
        self._vida.timeout.connect(self.cerrar)

        self.adjustSize()

    def mostrar(self):
        self.show()
        self.raise_()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._vida.start(DURACION_MS)

    def cerrar(self):
        if self._cerrando:
            return
        self._cerrando = True
        self._vida.stop()
        self._anim.stop()
        self._anim.setStartValue(self._opacidad.opacity())
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._terminar)
        self._anim.start()

    def _terminar(self):
        self.hide()
        self._al_cerrar(self)
        borrar_luego([self], "aviso de la secretaria")


class Secretaria(QObject):
    """Programa los avisos de una atención. iniciar() al presionar
    "Atender", detener() al cerrarla (o al salir de la sesión): los avisos
    pendientes se cancelan y el que esté a la vista se va."""

    def __init__(self, area):
        super().__init__(area)
        self._area = area
        self._timers = []
        self._avisos = []
        # Última frase de cada aviso en esta sesión de la app: con varias
        # atenciones seguidas, Karime no abre dos veces igual.
        self._ultimos = {}
        area.installEventFilter(self)

    def iniciar(self, siguiente, relativa=False):
        """siguiente: {"nombre", "hora"} de siguiente_paciente(), o None.
        relativa: la cita es de la agenda relativa; esos avisos los dice
        Recepcion según el horario, no por minutos desde "Atender"."""
        self.detener()
        if relativa:
            return
        for indice, aviso in enumerate(config_avisos(app_config_store.get(CONFIG_KEY))):
            if aviso["min"] <= 0:
                continue
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(
                lambda i=indice, a=aviso: self._decir(i, a, siguiente))
            timer.start(int(aviso["min"] * 60_000))
            self._timers.append(timer)

    def _decir(self, indice, aviso, siguiente):
        texto = texto_aviso(aviso, aviso["min"], siguiente, evitar=self._ultimos.get(indice))
        self._ultimos[indice] = texto
        self.avisar(texto)

    def detener(self):
        for timer in self._timers:
            timer.stop()
            timer.deleteLater()
        self._timers = []
        for aviso in list(self._avisos):
            aviso.cerrar()

    def avisar(self, texto):
        aviso = AvisoSecretaria(self._area, texto, self._quitar)
        self._avisos.append(aviso)
        self._ubicar()
        aviso.mostrar()
        return aviso

    def _quitar(self, aviso):
        if aviso in self._avisos:
            self._avisos.remove(aviso)
            self._ubicar()

    def _ubicar(self):
        """Abajo a la derecha del área visible del MDI; si hay más de uno
        se apilan hacia arriba, el más nuevo abajo."""
        zona = self._area.viewport().geometry()
        y = zona.bottom() - MARGEN
        for aviso in reversed(self._avisos):
            y -= aviso.height()
            aviso.move(zona.right() - MARGEN - aviso.width(), y)
            y -= SEPARACION

    def eventFilter(self, obj, event):
        if obj is self._area and event.type() == QEvent.Type.Resize and self._avisos:
            self._ubicar()
        return False


class Recepcion(QObject):
    """Karime mirando la agenda relativa del alumno (ver eventos_agenda).
    Cada TIC_AGENDA_MS dice a lo más una cosa nueva; lo ya dicho no se
    repite en esta sesión de la app. Las funciones de `fuentes` las pone
    main: agenda() -> dict de AgendaEntry, usuario() -> username o None (el
    docente no recibe estos avisos), activa() -> key de la atención abierta
    y segundos() -> segundos de esa atención."""

    def __init__(self, secretaria, agenda, usuario, activa, segundos):
        super().__init__(secretaria)
        self._secretaria = secretaria
        self._fuentes = (agenda, usuario, activa, segundos)
        self._dichos = set()
        self._ultimos = {}
        self._timer = QTimer(self)
        self._timer.setInterval(TIC_AGENDA_MS)
        self._timer.timeout.connect(self.tic)
        self._timer.start()

    def reiniciar(self):
        """Al cambiar de sesión: lo dicho era de otro alumno."""
        self._dichos.clear()

    def tic(self, ahora=None):
        from datetime import datetime
        agenda_de, usuario_de, activa_de, segundos_de = self._fuentes
        username = usuario_de()
        if not username:
            return None
        agenda = agenda_de() or {}
        eventos = eventos_agenda(agenda, username, ahora or datetime.now(), activa_de(), segundos_de())
        for clave, tipo, valores in eventos:
            if clave in self._dichos:
                continue
            self._dichos.add(clave)
            frases = config_agenda(app_config_store.get(CONFIG_AGENDA_KEY))[tipo]
            texto = texto_agenda(frases, valores, evitar=self._ultimos.get(tipo))
            self._ultimos[tipo] = texto
            self._secretaria.avisar(texto)
            return texto
        return None
