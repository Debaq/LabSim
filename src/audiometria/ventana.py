"""
El audiómetro en una sola ventana a pantalla completa, con sus accesorios a
la vista: los comandos de voz a la izquierda, el equipo al centro y, a la
derecha, las listas de palabras cuando la prueba es Logoaudiometría. Antes
eran tres subventanas que se abrían con botones fuera del equipo, y los
alumnos se perdían buscándolas.

Nada se pliega ni se esconde. Si no caben los tres lado a lado (pantallas
de menos de ~1280 de ancho), los dos paneles comparten la columna de la
derecha: arriba los comandos y, con la logo, las listas debajo.

El audiómetro se escala entero (texto, perillas y botones) al espacio que
le queda y va centrado: estirar sus layouts solo abría huecos entre los
controles. Va dentro de un QGraphicsView (ver _Escalado).

Cada panel sigue siendo un módulo del curso (CVOICE y W en Layout.php):
sin el permiso, su panel no aparece.
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QTransform
from PySide6.QtWidgets import (QFrame, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel,
                               QSizePolicy, QVBoxLayout, QWidget)

from audiometria.Audiometer import Audiometer, test_list
from audiometria.ListWords import ListWords
from audiometria.comandos_voz import ComandosVoz
from audiometria.panel_ui import QWIDGETSIZE_MAX
from core import iconos, tema

LOGO = test_list[1]
# Lo mínimo que necesita cada panel al lado del audiómetro: una frase por
# fila, tres palabras por fila.
ANCHO_COMANDOS = 220
ANCHO_LISTAS = 280
# En la columna compartida con las listas, los comandos no pasan de esta
# fracción del alto: las palabras tienen que verse enteras y las frases se
# encuentran también con la búsqueda.
FRACCION_COMANDOS_COLUMNA = 0.36
# Con los comandos más anchos que esto no caben más columnas de frases: lo
# que sobra va al audiómetro.
ANCHO_MAXIMO_COMANDOS = 520
# Zoom del audiómetro: más chico se lee mal, más grande no aporta.
ESCALA_MINIMA = 0.6
ESCALA_MAXIMA = 1.8
MARGEN = 6


class AudiometriaWindow(QWidget):

    def __init__(self, data, comandos=True, listas=True):
        super().__init__()
        tema.aplicar_estilo(self)
        self.audiometro = Audiometer(data)
        self.comandos = ComandosVoz()
        self.listas = ListWords(data)
        self.aviso_listas = _aviso_listas()
        self._con_comandos = comandos
        self._con_listas = listas
        self._logo = self.audiometro.lbl_prueba.text() == LOGO
        self._modo = None
        self.escalado = _Escalado(self.audiometro)

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(MARGEN, MARGEN, MARGEN, MARGEN)
        raiz.setSpacing(MARGEN)
        self.izq = QVBoxLayout()
        self.der = QVBoxLayout()
        self.der.setSpacing(MARGEN)
        # Los paneles con ancho fijo (ver _disponer); el audiómetro, el resto.
        raiz.addLayout(self.izq, 0)
        raiz.addWidget(self.escalado, 1)
        raiz.addLayout(self.der, 0)

        # Lo que antes conectaba main.connect_signals entre las tres ventanas.
        self.comandos.btn_checked.connect(self.audiometro.supra)
        self.audiometro.signal_speech.connect(self.listas.update_state)
        self.listas.level_changed.connect(
            lambda level: self.audiometro._on_player_level(self.listas.channel, level))
        self.audiometro.prueba_cambio.connect(self._al_cambiar_prueba)

        self._disponer()

    def la_super(self, data, appointment_id=None):
        self.audiometro.la_super(data, appointment_id)
        self.listas.la_super(data, appointment_id)

    def _al_cambiar_prueba(self, prueba):
        self._logo = prueba == LOGO
        self._visibles()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._disponer()

    def _disponer(self):
        """Reparte el ancho. Los paneles van con ancho fijo y el audiómetro
        se escala al resto; como el audiómetro no tiene mínimo, la ventana
        siempre puede achicarse (el MDI no la deja bajo su mínimo, y con un
        mínimo grande nunca llegaría a la columna compartida)."""
        base = self.escalado.base.width()
        n_paneles = self._con_comandos + self._con_listas
        disponible = self.width() - 2 * MARGEN - n_paneles * MARGEN
        listas = ANCHO_LISTAS if self._con_listas else 0
        cabe = disponible >= base + listas + (ANCHO_COMANDOS if self._con_comandos else 0)
        modo = "lado" if cabe else "columna"
        if modo != self._modo:
            self._modo = modo
            for w in (self.comandos, self.listas, self.aviso_listas):
                self.izq.removeWidget(w)
                self.der.removeWidget(w)
            if modo == "lado":
                self.izq.addWidget(self.comandos)
                self.der.addWidget(self.listas)
                self.der.addWidget(self.aviso_listas)
            else:
                self.der.addWidget(self.comandos, 1)
                self.der.addWidget(self.listas, 2)
                self.der.addWidget(self.aviso_listas)
        if modo == "lado":
            # Las listas en su ancho de tres columnas; los comandos, lo que
            # deje el audiómetro en tamaño 1 (en 1366, dos columnas de
            # frases), con su tope; lo demás agranda el audiómetro.
            comandos = min(ANCHO_MAXIMO_COMANDOS,
                           max(ANCHO_COMANDOS, disponible - listas - base))
            self.comandos.setFixedWidth(comandos)
            for panel in (self.listas, self.aviso_listas):
                panel.setFixedWidth(ANCHO_LISTAS)
        else:
            columna = max(ANCHO_LISTAS, self.width() - 3 * MARGEN - base)
            for panel in (self.comandos, self.listas, self.aviso_listas):
                panel.setFixedWidth(columna)
        self._visibles()

    def _alto_comandos(self):
        alto = QWIDGETSIZE_MAX
        if self._modo == "columna" and self._con_listas and self._logo:
            alto = int(self.height() * FRACCION_COMANDOS_COLUMNA)
        self.comandos.setMaximumHeight(alto)

    def _visibles(self):
        self._alto_comandos()
        self.comandos.setVisible(self._con_comandos)
        self.listas.setVisible(self._con_listas and self._logo)
        # En la columna compartida los comandos usan el alto que dejan las
        # listas; el aviso solo marca el sitio cuando tiene uno propio.
        self.aviso_listas.setVisible(self._con_listas and not self._logo
                                     and self._modo == "lado")


class _Escalado(QGraphicsView):
    """Muestra un widget escalado entero al espacio que tiene, centrado y
    sin deformarlo. El widget sigue siendo el mismo (clics, perillas y
    teclas andan igual); solo se dibuja con zoom."""

    def __init__(self, widget):
        super().__init__()
        self._widget = widget
        self.base = widget.minimumSizeHint()
        widget.resize(self.base)
        escena = QGraphicsScene(self)
        self._proxy = escena.addWidget(widget)
        self.setScene(escena)
        self.setSceneRect(self._proxy.boundingRect())
        self.setObjectName("escalado")
        self.setStyleSheet("QGraphicsView#escalado { background: transparent; border: none; }")
        self.viewport().setAutoFillBackground(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setRenderHints(QPainter.RenderHint.Antialiasing
                            | QPainter.RenderHint.TextAntialiasing
                            | QPainter.RenderHint.SmoothPixmapTransform)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.escala = 1.0

    def sizeHint(self):
        return self.base

    def minimumSizeHint(self):
        return QSize(0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        escala = min(self.width() / self.base.width(), self.height() / self.base.height())
        self.escala = max(ESCALA_MINIMA, min(ESCALA_MAXIMA, escala))
        self.setTransform(QTransform.fromScale(self.escala, self.escala))

    # El audiómetro se muestra y se esconde con la ventana: al esconderse
    # corta el sonido y suelta sus teclas (Audiometer.hideEvent). Dentro de
    # la escena no se enteraría solo.
    def showEvent(self, event):
        super().showEvent(event)
        self._widget.show()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._widget.hide()


def _aviso_listas():
    """El lado derecho sin logoaudiometría: dice qué va ahí y cuándo."""
    caja = QFrame()
    caja.setProperty("card", "true")
    col = QVBoxLayout(caja)
    col.setContentsMargins(18, 18, 18, 18)
    col.setSpacing(8)
    col.addStretch(1)
    icono = QLabel()
    icono.setPixmap(iconos.pixmap("lista", tema.TEXTO_TENUE, 32))
    icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
    titulo = QLabel("Listas de palabras")
    titulo.setProperty("role", "titulo")
    titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pista = QLabel("Aparecen aquí al poner Habla en un canal del audiómetro "
                   "(Logoaudiometría).")
    pista.setProperty("role", "hint")
    pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pista.setWordWrap(True)
    for w in (icono, titulo, pista):
        col.addWidget(w)
    col.addStretch(2)
    return caja
