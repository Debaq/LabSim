"""
El audiómetro en una sola ventana a pantalla completa, con sus accesorios a
la vista: los comandos de voz a la izquierda, el equipo al centro y, a la
derecha, las listas de palabras cuando la prueba es Logoaudiometría. Antes
eran tres subventanas que se abrían con botones fuera del equipo, y los
alumnos se perdían buscándolas.

Reparto 1:3:1 en cualquier pantalla, con el audiómetro escalado al centro
(ver core/reparto.py).

Cada panel sigue siendo un módulo del curso (CVOICE y W en Layout.php):
sin el permiso, su panel no aparece y su quinto queda vacío.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QStackedLayout, QVBoxLayout, QWidget

from audiometria.Audiometer import Audiometer, test_list
from audiometria.ListWords import ListWords
from audiometria.comandos_voz import ComandosVoz
from audiometria import no_realizable
from core import iconos, tema
from core.reparto import Reparto

LOGO = test_list[1]


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
        # Con un bebé, en lugar del equipo va el aviso (ver no_realizable)
        self.aviso_bebe = no_realizable.AvisoNoRealizable("Audiometría no realizable")
        self._bebe_registrado = None   # caso cuyo intento ya quedó en el registro

        self.equipo = Reparto(self.audiometro)
        self.escalado = self.equipo.escalado
        self.col_izq, self.col_der = self.equipo.col_izq, self.equipo.col_der
        self.equipo.izq.addWidget(self.comandos)
        self.equipo.der.addWidget(self.listas)
        self.equipo.der.addWidget(self.aviso_listas)
        self.pila = QStackedLayout(self)
        self.pila.addWidget(self.equipo)
        self.pila.addWidget(self.aviso_bebe)

        # Lo que antes conectaba main.connect_signals entre las tres ventanas.
        self.comandos.btn_checked.connect(self.audiometro.supra)
        self.audiometro.signal_speech.connect(self.listas.update_state)
        self.listas.level_changed.connect(
            lambda level: self.audiometro._on_player_level(self.listas.channel, level))
        self.audiometro.prueba_cambio.connect(self._al_cambiar_prueba)

        self._visibles()
        self._data = None
        self._revisar_edad(data)

    def la_super(self, data, appointment_id=None):
        self.audiometro.la_super(data, appointment_id)
        self.listas.la_super(data, appointment_id)
        self._revisar_edad(data)

    def _revisar_edad(self, data):
        self._data = data
        motivo = no_realizable.motivo(data, "audiometría")
        if motivo:
            self.aviso_bebe.texto.setText(motivo)
        self.pila.setCurrentWidget(self.aviso_bebe if motivo else self.equipo)
        if motivo:
            # dentro de la escena el audiómetro no se entera de que su página
            # se tapó: escondido suelta las teclas y corta el sonido
            # (Audiometer.hideEvent); Escalado lo vuelve a mostrar
            self.audiometro.hide()
        elif self.escalado.isVisible():
            self.audiometro.show()
        if self.isVisible():
            self._registrar_bebe()

    def showEvent(self, event):
        super().showEvent(event)
        self._registrar_bebe()

    def _registrar_bebe(self):
        """Abrir el audiómetro con un bebé queda en el registro, una vez por
        caso: el docente ve que se intentó."""
        data = self._data
        if not no_realizable.es_bebe(data) or self._bebe_registrado is data:
            return
        self._bebe_registrado = data
        self.audiometro._log("audio_no_realizable", motivo="bebe",
                             edad=data.get("edad"), edad_horas=data.get("edad_horas"))

    def _al_cambiar_prueba(self, prueba):
        self._logo = prueba == LOGO
        self._visibles()

    def _visibles(self):
        self.comandos.setVisible(self._con_comandos)
        self.listas.setVisible(self._con_listas and self._logo)
        self.aviso_listas.setVisible(self._con_listas and not self._logo)


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
    titulo.setWordWrap(True)
    pista = QLabel("Aparecen aquí al poner Habla en un canal del audiómetro "
                   "(Logoaudiometría).")
    pista.setProperty("role", "hint")
    pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pista.setWordWrap(True)
    for w in (icono, titulo, pista):
        col.addWidget(w)
    col.addStretch(2)
    return caja
