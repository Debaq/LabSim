"""
Panel del impedanciómetro: la pantalla del equipo y sus mandos.

La pantalla (frame_screen y las cuatro pantallas que se montan en
Screen_Layout) es la del equipo y no se toca: azul, con sus rótulos. Lo que
la rodea va con la paleta de LabSim (core/tema.py): un bisel oscuro con las
teclas blandas debajo, como en el equipo, y los mandos en tres tarjetas.

Reemplaza a UI/Ui_Z_control.py (Designer): los nombres de los widgets son
los mismos que usa Z.py.
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout)

from core import iconos, tema
from core.perilla import Perilla

BISEL = '#2E2730'
TECLA = '#5A4F5B'
TECLA_HOVER = '#7A6D7B'

EXTRA_QSS = f"""
QFrame#bisel {{ background: {BISEL}; border-radius: 12px; }}
QPushButton[tecla="true"] {{
    background: {TECLA};
    border: none;
    border-radius: 5px;
    min-height: 14px;
    max-height: 14px;
    padding: 0px;
}}
QPushButton[tecla="true"]:hover {{ background: {TECLA_HOVER}; }}
QPushButton[tecla="true"]:pressed {{ background: {tema.ACENTO_CLARO}; }}
QPushButton[tecla="true"]:disabled {{ background: #403841; }}
QPushButton[prueba="true"] {{ text-align: left; padding: 4px 10px; }}
QPushButton[lado="od"]:checked {{ background: {tema.OD_SUAVE}; border-color: {tema.OD}; color: {tema.OD}; }}
QPushButton[lado="oi"]:checked {{ background: {tema.OI_SUAVE}; border-color: {tema.OI}; color: {tema.OI}; }}
QPushButton[segmento="true"] {{ padding: 4px 0px; font-weight: 600; }}
QPushButton[primario="true"] {{
    background: {tema.ACENTO};
    border-color: {tema.ACENTO};
    color: white;
    font-weight: 600;
    padding: 6px 12px;
}}
QPushButton[primario="true"]:hover {{ background: {tema.ACENTO_CLARO}; color: white; }}
QPushButton[primario="true"]:pressed {{ background: {tema.ACENTO}; }}
QLabel#leak {{
    border-radius: 6px;
    color: white;
    font-weight: 700;
    padding: 2px 0px;
}}
"""


def _tarjeta(titulo):
    tarjeta = QFrame()
    tarjeta.setProperty("card", "true")
    col = QVBoxLayout(tarjeta)
    col.setContentsMargins(12, 8, 12, 10)
    col.setSpacing(5)
    col.addWidget(_seccion(titulo))
    return tarjeta, col


def _seccion(texto):
    lbl = QLabel(texto)
    lbl.setProperty("role", "seccion")
    return lbl


def _segmentado(w, opciones, prop=None):
    """Botones marcables excluyentes en fila; devuelve la fila y los botones."""
    fila = QHBoxLayout()
    fila.setSpacing(4)
    grupo = QButtonGroup(w)
    botones = []
    for texto in opciones:
        btn = QPushButton(texto)
        btn.setCheckable(True)
        btn.setProperty("segmento", "true")
        if prop:
            btn.setProperty("lado", texto.lower())
        grupo.addButton(btn)
        fila.addWidget(btn, 1)
        botones.append(btn)
    botones[0].setChecked(True)
    return fila, botones


class UiControlZ:

    def setupUi(self, w):
        tema.aplicar_estilo(w, EXTRA_QSS)
        raiz = QVBoxLayout(w)
        raiz.setContentsMargins(12, 8, 12, 10)
        raiz.setSpacing(8)

        # --- La pantalla del equipo, con las teclas blandas debajo ---------
        self.bisel = QFrame()
        self.bisel.setObjectName("bisel")
        self.bisel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bisel = QVBoxLayout(self.bisel)
        bisel.setContentsMargins(8, 8, 8, 7)
        bisel.setSpacing(6)

        self.frame_screen = QFrame()
        self.frame_screen.setObjectName("frame_screen")
        self.frame_screen.setMinimumSize(QSize(600, 280))
        self.frame_screen.setMaximumSize(QSize(600, 300))
        self.frame_screen.setStyleSheet("background-color: rgb(85, 170, 255);")
        self.frame_screen.setFrameShape(QFrame.Shape.Box)
        self.frame_screen.setFrameShadow(QFrame.Shadow.Sunken)
        self.frame_screen.setLineWidth(3)
        self.Screen_Layout = QHBoxLayout(self.frame_screen)
        self.Screen_Layout.setSpacing(0)
        self.Screen_Layout.setContentsMargins(0, 0, 0, 0)
        bisel.addWidget(self.frame_screen)

        # Seis teclas sin rótulo: su función la dice la fila de abajo de la
        # pantalla y cambia con cada pantalla.
        teclas = QHBoxLayout()
        teclas.setContentsMargins(14, 0, 14, 0)
        teclas.setSpacing(22)
        for i in range(1, 7):
            btn = QPushButton()
            btn.setProperty("tecla", "true")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            teclas.addWidget(btn, 1)
            setattr(self, f"btn_{i}", btn)
        bisel.addLayout(teclas)

        fila_pantalla = QHBoxLayout()
        fila_pantalla.addStretch(1)
        fila_pantalla.addWidget(self.bisel)
        fila_pantalla.addStretch(1)
        raiz.addLayout(fila_pantalla)

        # --- Mandos --------------------------------------------------------
        mandos = QHBoxLayout()
        mandos.setSpacing(10)
        mandos.addWidget(self._tarjeta_pruebas(w))
        mandos.addWidget(self._tarjeta_perilla(), 1)
        mandos.addWidget(self._tarjeta_equipo(w))
        raiz.addLayout(mandos)
        raiz.addStretch(1)

    def _tarjeta_pruebas(self, w):
        tarjeta, col = _tarjeta("PRUEBA")
        tarjeta.setFixedWidth(140)
        grupo = QButtonGroup(w)
        for attr, texto in (("btn_tymp", "Timpanograma"), ("btn_reflex_test", "Reflejos"),
                            ("btn_toneDecay", "Tone Decay"), ("btn_etf", "ETF")):
            btn = QPushButton(texto)
            btn.setCheckable(True)
            btn.setProperty("prueba", "true")
            grupo.addButton(btn)
            col.addWidget(btn)
            setattr(self, attr, btn)
        self.btn_tymp.setChecked(True)
        col.addStretch(1)
        return tarjeta

    def _tarjeta_perilla(self):
        tarjeta, col = _tarjeta("MANDOS")
        fila = QHBoxLayout()
        fila.setSpacing(12)

        self.dial = Perilla()
        self.dial.setFixedSize(QSize(84, 84))
        self.dial.setMinimum(1)
        self.dial.setMaximum(20)
        self.dial.setTracking(False)
        self.dial.setWrapping(True)
        fila.addWidget(self.dial)

        der = QGridLayout()
        der.setHorizontalSpacing(6)
        der.setVerticalSpacing(6)
        lbl_leak = QLabel("Leak")
        lbl_leak.setProperty("role", "campo")
        self.label = QLabel()
        self.label.setObjectName("leak")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedWidth(42)
        der.addWidget(lbl_leak, 0, 0)
        der.addWidget(self.label, 0, 1)

        # Presión del conducto en reflejos y Tone Decay (de a 10 daPa).
        self.btn_up = QPushButton(" Presión")
        self.btn_up.setIcon(iconos.icono_boton("arriba", tema.TEXTO_SUAVE, tam=14))
        self.btn_down = QPushButton(" Presión")
        self.btn_down.setIcon(iconos.icono_boton("abajo", tema.TEXTO_SUAVE, tam=14))
        der.addWidget(self.btn_up, 1, 0, 1, 2)
        der.addWidget(self.btn_down, 2, 0, 1, 2)
        fila.addLayout(der, 1)
        col.addLayout(fila)
        col.addStretch(1)

        self.btn_stimulus = QPushButton(" Estímulo")
        self.btn_stimulus.setIcon(iconos.icono_boton("atender", "white", tam=14))
        self.btn_stimulus.setProperty("primario", "true")
        col.addWidget(self.btn_stimulus)
        return tarjeta

    def _tarjeta_equipo(self, w):
        tarjeta, col = _tarjeta("EQUIPO")
        tarjeta.setFixedWidth(226)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        filas = (("Oído", ("OD", "OI"), "lado", ("btn_od", "btn_oi")),
                 ("Sonda", ("226 Hz", "1000 Hz"), None, ("btn_226", "btn_1000")),
                 ("Reflejo", ("IPSI", "CONTRA"), None, ("btn_ipsi", "btn_contra")))
        for i, (rotulo, opciones, prop, attrs) in enumerate(filas):
            lbl = QLabel(rotulo)
            lbl.setProperty("role", "campo")
            fila, botones = _segmentado(w, opciones, prop)
            grid.addWidget(lbl, i, 0)
            grid.addLayout(fila, i, 1)
            for attr, btn in zip(attrs, botones):
                setattr(self, attr, btn)
        col.addLayout(grid)
        col.addStretch(1)
        self.btn_print = QPushButton(" Imprimir")
        self.btn_print.setIcon(iconos.icono_boton("impresora", tema.TEXTO_SUAVE, tam=14))
        col.addWidget(self.btn_print)
        return tarjeta
