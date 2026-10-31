"""
Audiometría y acumetría en un bebé: no se pueden hacer.

Las dos piden una respuesta del paciente -- levantar la mano, repetir una
palabra, decir dónde suena el diapasón -- y un bebé no la da. Si el alumno
abre el audiómetro con un bebé, en vez del equipo ve el aviso de por qué no
corresponde, y el intento queda registrado.

El corte es EDAD_MINIMA (3 años): antes de eso la audición se mide con otras
técnicas que LabSim no simula. La edad del caso viene en años ('edad'); en
el primer año, además, en horas de vida ('edad_horas', ver CaseBuilder.php).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from core import iconos, tema

EDAD_MINIMA = 3   # años


def _horas(caso):
    try:
        horas = caso.get("edad_horas")
        return None if horas in (None, "") else int(horas)
    except (TypeError, ValueError):
        return None


def _anios(caso):
    try:
        return int(caso.get("edad"))
    except (TypeError, ValueError):
        return None


def edad_texto(caso):
    """La edad como se dice de un bebé: horas, días, meses o años."""
    horas = _horas(caso)
    if horas is not None and horas < 8760:
        if horas < 48:
            return f"{horas} {'hora' if horas == 1 else 'horas'} de vida"
        if horas < 1080:   # mes y medio, como CaseBuilder
            return f"{round(horas / 24)} días"
        meses = round(horas / 720)
        return f"{meses} {'mes' if meses == 1 else 'meses'}"
    anios = _anios(caso)
    if anios is None:
        return None
    if anios == 0:
        return "menos de un año"
    return f"{anios} {'año' if anios == 1 else 'años'}"


def es_bebe(caso):
    """True si el paciente del caso es menor que EDAD_MINIMA. Sin edad en el
    caso no se bloquea nada."""
    if not caso:
        return False
    anios = _anios(caso)
    return anios is not None and anios < EDAD_MINIMA


def motivo(caso, prueba):
    """Texto del aviso, o None si la prueba se puede hacer."""
    if not es_bebe(caso):
        return None
    return (f"El paciente tiene {edad_texto(caso)}. Un bebé no levanta la mano "
            f"ni repite palabras ni dice dónde escucha un sonido: la {prueba} "
            "no se puede realizar.")


class AvisoNoRealizable(QFrame):
    """Lo que se ve en lugar del equipo cuando la prueba no se puede hacer."""

    def __init__(self, titulo):
        super().__init__()
        self.setProperty("card", "true")
        col = QVBoxLayout(self)
        col.setContentsMargins(32, 32, 32, 32)
        col.setSpacing(10)
        col.addStretch(1)
        icono = QLabel()
        icono.setPixmap(iconos.pixmap("alerta", tema.ALERTA, 48))
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo = QLabel(titulo)
        self.titulo.setProperty("role", "titulo")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto = QLabel()
        self.texto.setWordWrap(True)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setMaximumWidth(560)
        for w in (icono, self.titulo):
            col.addWidget(w)
        # entre estiramientos y no con AlignHCenter: alineada, la etiqueta
        # con ajuste de línea no pide el alto que necesita y se corta
        fila = QHBoxLayout()
        fila.addStretch(1)
        fila.addWidget(self.texto, 4)
        fila.addStretch(1)
        col.addLayout(fila)
        col.addStretch(2)
