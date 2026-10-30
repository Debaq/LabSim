"""
El audiómetro en una sola ventana a pantalla completa, con sus accesorios a
la vista: los comandos de voz a la izquierda, el equipo al centro y, a la
derecha, las listas de palabras cuando la prueba es Logoaudiometría. Antes
eran tres subventanas que se abrían con botones fuera del equipo, y los
alumnos se perdían buscándolas.

El audiómetro tiene ancho fijo y va siempre al centro de la pantalla (y al
medio en vertical): los dos laterales se reparten por igual el ancho que
sobra, cada uno a lo más la mitad, aunque uno de los dos esté vacío.

Nada se pliega ni se esconde. Si los laterales quedan más angostos que
LATERAL_MINIMO (pantallas de menos de ~1250 de ancho), los dos paneles
comparten la columna de la derecha: arriba los comandos y, con la logo, las
listas debajo. Ahí el audiómetro ya no va centrado.

Cada panel sigue siendo un módulo del curso (CVOICE y W en Layout.php):
sin el permiso, su panel no aparece.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from audiometria.Audiometer import Audiometer, test_list
from audiometria.ListWords import ListWords
from audiometria.comandos_voz import ComandosVoz
from audiometria.panel_ui import QWIDGETSIZE_MAX
from core import iconos, tema

LOGO = test_list[1]
# Lo mínimo de cada lateral: una frase por fila, tres palabras por fila.
LATERAL_MINIMO = 250
# En la columna compartida con las listas, los comandos no pasan de esta
# fracción del alto: las palabras tienen que verse enteras y las frases se
# encuentran también con la búsqueda.
FRACCION_COMANDOS_COLUMNA = 0.36
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
        self.audiometro.setFixedSize(self.audiometro.minimumSizeHint())

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(MARGEN, MARGEN, MARGEN, MARGEN)
        raiz.setSpacing(MARGEN)
        self.col_izq, self.izq = _columna()
        self.col_der, self.der = _columna()
        centro = QVBoxLayout()
        centro.addStretch(1)
        centro.addWidget(self.audiometro, 0, Qt.AlignmentFlag.AlignHCenter)
        centro.addStretch(1)
        # Laterales con el mismo estiramiento y el mismo tope (ver _disponer):
        # el audiómetro, de ancho fijo, queda justo al medio.
        raiz.addWidget(self.col_izq, 1)
        raiz.addLayout(centro, 0)
        raiz.addWidget(self.col_der, 1)

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
        lateral = (self.width() - 4 * MARGEN - self.audiometro.width()) // 2
        modo = "lado" if lateral >= LATERAL_MINIMO else "columna"
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
        # Tope y no ancho fijo: con un mínimo así la ventana no podría
        # achicarse (el MDI no la deja bajo su mínimo) y nunca llegaría a la
        # columna compartida.
        self.col_izq.setVisible(modo == "lado")
        self.col_der.setMaximumWidth(max(lateral, 0) if modo == "lado" else QWIDGETSIZE_MAX)
        self.col_izq.setMaximumWidth(max(lateral, 0))
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


def _columna():
    """Un lateral: sin mínimo propio (ver _disponer)."""
    col = QWidget()
    col.setMinimumWidth(1)
    lay = QVBoxLayout(col)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(MARGEN)
    return col, lay


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
