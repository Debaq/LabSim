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

from core.avatar import avatar_iniciales
from core.base import context
from core import app_config_store

NOMBRE = "Karime"
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
    pendientes = [
        e for k, e in agenda.items()
        if k != key_actual and not e.sin_cita and e.fecha == actual.fecha and e.hora
        and not e.atencion.get(username)
    ]
    if not pendientes:
        return None
    cita = min(pendientes, key=lambda e: e.hora)
    nombre = f"{cita.nombre} {cita.apellido}".strip() or "el paciente siguiente"
    return {"nombre": nombre, "hora": cita.hora[:5]}


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
        avatar.setPixmap(avatar_iniciales(NOMBRE, 40))
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
        self.deleteLater()


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

    def iniciar(self, siguiente):
        """siguiente: {"nombre", "hora"} de siguiente_paciente(), o None."""
        self.detener()
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
