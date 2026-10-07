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

Sin sonido a propósito: la app tiene audiometría con audífonos puestos y un
"ding" en medio de un umbral contamina la prueba.
"""

import json

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


def _defaults():
    with open(context.get_resource("json/secretaria_avisos.json"), encoding="utf-8") as archivo:
        return json.load(archivo)["avisos"]


def minutos_avisos(override=None):
    """Minutos de cada aviso, en orden: el default de la app con lo que el
    curso sobreescribió encima (override = {"avisos": {"aviso_N": {"min": x}}},
    como lo guarda CourseParams::parse). 0 apaga ese aviso."""
    avisos = _defaults()
    propios = (override or {}).get("avisos") or {}
    minutos = []
    for clave in sorted(avisos):
        valor = (propios.get(clave) or {}).get("min", avisos[clave]["min"])
        try:
            minutos.append(max(0.0, float(valor)))
        except (TypeError, ValueError):
            minutos.append(float(avisos[clave]["min"]))
    return minutos


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


def texto_aviso(indice, minutos, siguiente):
    """Lo que dice Karime en el aviso número `indice` (0, 1, 2...), cada uno
    más apurado que el anterior."""
    minutos = int(round(minutos))
    if siguiente:
        nombre, hora = siguiente["nombre"], siguiente["hora"]
        textos = (
            f"Te aviso que {nombre} ya llegó, tenía hora a las {hora}. Está en la sala de espera.",
            f"{nombre} sigue esperando en la sala. ¿Te falta mucho?",
            f"{nombre} ya lleva rato esperando y está preguntando por su hora. ¿Le digo que pase?",
        )
    else:
        textos = (
            f"Ya van {minutos} minutos de atención. Recuerda que el box se ocupa en el bloque siguiente.",
            f"Van {minutos} minutos. Voy a necesitar el box pronto.",
            f"Ya van {minutos} minutos. Por favor ve cerrando la atención.",
        )
    return textos[min(indice, len(textos) - 1)]


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
        area.installEventFilter(self)

    def iniciar(self, siguiente):
        """siguiente: {"nombre", "hora"} de siguiente_paciente(), o None."""
        self.detener()
        for indice, minutos in enumerate(minutos_avisos(app_config_store.get(CONFIG_KEY))):
            if minutos <= 0:
                continue
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(
                lambda i=indice, m=minutos: self.avisar(texto_aviso(i, m, siguiente)))
            timer.start(int(minutos * 60_000))
            self._timers.append(timer)

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
