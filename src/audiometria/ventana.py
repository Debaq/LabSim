"""
El audiómetro en una sola ventana a pantalla completa, con sus accesorios a
la vista: los comandos de voz a la izquierda, el equipo al centro y, a la
derecha, las listas de palabras cuando la prueba es Logoaudiometría. Antes
eran tres subventanas que se abrían con botones fuera del equipo, y los
alumnos se perdían buscándolas.

Nada se pliega ni se esconde. Si no caben los tres lado a lado (pantallas
de menos de ~1280 de ancho), los dos paneles comparten la columna de la
derecha: arriba los comandos y, con la logo, las listas debajo.

Cada panel sigue siendo un módulo del curso (CVOICE y W en Layout.php):
sin el permiso, su panel no aparece.
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

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
# Mínimo fijo de los paneles, menor que los de arriba: si la ventana no
# pudiera achicarse bajo el ancho de los tres lado a lado, nunca pasaría a
# la columna compartida (el MDI no la deja más chica que su mínimo).
ANCHO_MINIMO_PANEL = 120
# En la columna compartida con las listas, los comandos no pasan de esta
# fracción del alto: las palabras tienen que verse enteras y las frases se
# encuentran también con la búsqueda.
FRACCION_COMANDOS_COLUMNA = 0.36
# Con los comandos más anchos que esto no caben más columnas de frases: lo
# que sobra va a las listas.
ANCHO_MAXIMO_COMANDOS = 520
MARGEN = 6


class AudiometriaWindow(QWidget):

    def __init__(self, data, comandos=True, listas=True):
        super().__init__()
        tema.aplicar_estilo(self)
        self.audiometro = Audiometer(data)
        self.comandos = ComandosVoz()
        self.listas = ListWords(data)
        self.aviso_listas = _AvisoListas(self.listas)
        self._con_comandos = comandos
        self._con_listas = listas
        self._logo = self.audiometro.lbl_prueba.text() == LOGO
        self._modo = None
        for panel in (self.comandos, self.listas, self.aviso_listas):
            panel.setMinimumWidth(ANCHO_MINIMO_PANEL)

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(MARGEN, MARGEN, MARGEN, MARGEN)
        raiz.setSpacing(MARGEN)
        self.izq = QVBoxLayout()
        centro = QVBoxLayout()
        centro.addWidget(self.audiometro)
        centro.addStretch(1)
        self.der = QVBoxLayout()
        self.der.setSpacing(MARGEN)
        # El audiómetro en su ancho natural; los comandos crecen hasta su
        # tope y el resto queda para las listas (ver _disponer).
        raiz.addLayout(self.izq, 1)
        raiz.addLayout(centro, 0)
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

    def _ancho_lado_a_lado(self):
        ancho = self.audiometro.minimumSizeHint().width() + 2 * MARGEN
        if self._con_comandos:
            ancho += ANCHO_COMANDOS + MARGEN
        if self._con_listas:
            ancho += ANCHO_LISTAS + MARGEN
        return ancho

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._disponer()

    def _disponer(self):
        modo = "lado" if self.width() >= self._ancho_lado_a_lado() else "columna"
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
        # Lado a lado, los comandos se quedan con todo lo que no necesitan
        # las listas (en 1366 les alcanza para dos columnas de frases). Es
        # un máximo y no un mínimo de las listas: un mínimo no dejaría
        # achicar la ventana bajo el ancho de los tres, y nunca pasaría a
        # la columna compartida.
        tope = QWIDGETSIZE_MAX
        if modo == "lado" and self._con_listas:
            libre = (self.width() - self.audiometro.minimumSizeHint().width()
                     - 4 * MARGEN)
            tope = max(ANCHO_COMANDOS, min(ANCHO_MAXIMO_COMANDOS, libre - ANCHO_LISTAS))
        self.comandos.setMaximumWidth(tope)
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


class _AvisoListas(QFrame):
    """El lado derecho sin logoaudiometría: dice qué va ahí y cuándo. Pide
    el mismo ancho que las listas: si no, al entrar a la logo el audiómetro
    se corría."""

    def __init__(self, listas):
        super().__init__()
        self._listas = listas
        self.setProperty("card", "true")
        _armar_aviso(self)

    def sizeHint(self):
        return QSize(self._listas.sizeHint().width(), super().sizeHint().height())


def _armar_aviso(caja):
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
