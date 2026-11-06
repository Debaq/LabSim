"""
Otoscopía y diapasones: una sola pantalla con una sola cabeza (2026-11-06).

Por áreas, como el posicionamiento de electrodos (core/cabeza_electrodos.py):

- izquierda: todo lo que se le dice al paciente, de los dos exámenes
  (frases_habladas.py);
- centro: la cabeza (cabeza_examen.CabezaOtoscopia) con sus herramientas
  (Girar, Traccionar, Otoscopio, Diapasón), sus vistas y la pista;
- derecha: el panel con las secciones de cada examen (Otoscopia: espéculo,
  pabellón, otoscopio; Acumetria: diapasón y vibración) y la conversación.

La pestaña Informe tiene dos secciones: la otoscopía por cuadrantes
(OtoscopiaInforme.py) y los diapasones con símbolos y flechas
(AcumetriaInforme.py). Se suben juntas en el informe OTOSCOPIA
(Otoscopia.informe_dict).

Cada examen aparece si el curso tiene su módulo (OT, AC); la ventana se abre
con cualquiera (ui_helpers.VENTANA_DE). Un solo botón en el box ("OT/AC");
el layout del servidor no cambia, así las versiones anteriores de la app
siguen con sus dos botones. Otoscopia y Acumetria siguen siendo los módulos
que main.py carga con el caso y que suben el informe.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QTabWidget, QVBoxLayout, QWidget)

from audiometria import Acumetria as ac_mod
from audiometria import Otoscopia as ot_mod
from audiometria.AcumetriaInforme import InformeAcumetria
from audiometria.cabeza_examen import VISTA_ARRIBA, VISTA_FRENTE, CabezaOtoscopia
from audiometria.comandos_voz import SILENCIO
from audiometria.frases_habladas import FrasesHabladas
from core import iconos, tema

EXTRA_QSS = f"""
QTabWidget#otac::pane {{ border: none; background: transparent; top: 0px; }}
QTabWidget#otac > QTabBar::tab {{
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 8px 20px;
    margin-right: 6px;
    font-size: 10pt;
    font-weight: 700;
    color: {tema.TEXTO_TENUE};
}}
QTabWidget#otac > QTabBar::tab:selected {{ color: {tema.ACENTO}; border-bottom-color: {tema.ACENTO}; }}
QTabWidget#otac > QTabBar::tab:hover:!selected {{ color: {tema.TEXTO_SUAVE}; }}
QPushButton[segmento="true"] {{ padding: 4px 0px; }}
QPushButton[herramienta="true"] {{ padding: 5px 0px; font-weight: 600; }}
QPushButton[herramienta="true"]:checked {{ background: {tema.ACENTO}; border-color: {tema.ACENTO}; color: white; }}
QLabel#titulo_informe {{ font-size: 12pt; font-weight: 700; color: {tema.ACENTO}; }}
"""

HERRAMIENTAS = (("girar", "Girar", None), ("traccion", "Traccionar", "OT"),
                ("otoscopia", "Otoscopio", "OT"), ("diapason", "Diapasón", "AC"))
VISTAS = (("Frente", VISTA_FRENTE), ("Oído derecho", (90, 0)), ("Oído izquierdo", (270, 0)),
          ("Arriba", VISTA_ARRIBA), ("Atrás", (180, 20)))
PISTAS = {
    "girar": "Arrastra para girar la cabeza.",
    "traccion": "Arrastra desde la oreja hacia donde quieras tirar del pabellón.",
    "otoscopia": "Lleva el mouse al conducto: lo que se ve aparece ahí. Muévelo un poco para recorrer.",
    "diapason": "Clic en la piel: ahí se apoya el diapasón (o frente a la oreja, sin tocar).",
}
# El paciente contesta las instrucciones del otoscopio en la conversación
RESPUESTA_OT = {"explicar_otoscopia": "Bueno, ya.", "quedese_quieto": "Ya.",
                "incline_cabeza": "¿Así?", "avise_si_molesta": "Ya, bueno."}


def _grupos(con_ot, con_ac):
    """Las frases de los dos exámenes, por sección (preparar, instrucciones,
    preguntas), con las del otoscopio rotuladas."""
    fuentes = ([ot_mod.GRUPOS] if con_ot else []) + ([ac_mod.GRUPOS] if con_ac else [])
    juntas = {}
    for grupos in fuentes:
        for titulo, frases in grupos:
            juntas.setdefault(titulo, []).extend(frases)
    return tuple((t, tuple(juntas[t])) for t in ("PREPARAR", "INSTRUCCIONES", "PREGUNTAS") if t in juntas)


def _claves(grupos):
    return {clave for _t, frases in grupos for _r, clave in frases}


class OtoscopiaAcumetriaWindow(QWidget):

    def __init__(self, otoscopia, acumetria, con_otoscopia=True, con_acumetria=True):
        super().__init__()
        tema.aplicar_estilo(self, EXTRA_QSS)
        self.otoscopia = otoscopia
        self.acumetria = acumetria
        if not (con_otoscopia or con_acumetria):   # no debería pasar: el botón no se muestra
            con_otoscopia = True
        self.con_ot, self.con_ac = con_otoscopia, con_acumetria
        self._claves_ot = _claves(ot_mod.GRUPOS)

        self.cabeza = CabezaOtoscopia()
        otoscopia.conectar(self.cabeza)
        acumetria.conectar(self.cabeza)
        acumetria.pedir_herramienta = self.elegir_herramienta
        # Los informes van en la pestaña Informe; los diapasones, en el
        # informe de la otoscopía (Otoscopia.informe_dict)
        self.informe_acumetria = InformeAcumetria()
        otoscopia.informe_acumetria = self.informe_acumetria

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 8, 12, 12)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("otac")
        self.tabs.addTab(self._examen(), iconos.icono("oido", tema.ACENTO, 18), "Examen")
        self.tabs.addTab(self._informe(), iconos.icono("evolucion", tema.ACENTO, 18), "Informe")
        raiz.addWidget(self.tabs)

    # ------------------------------------------------------------ examen
    def _examen(self):
        tab = QWidget()
        fila = QHBoxLayout(tab)
        fila.setContentsMargins(0, 10, 0, 0)
        fila.setSpacing(10)

        grupos = _grupos(self.con_ot, self.con_ac)
        prueba = dict(ac_mod.PRUEBA) if self.con_ac else {}
        if self.con_ot and self.con_ac:
            prueba.update({clave: "Otoscopía" for clave in self._claves_ot if clave != "explicar_otoscopia"})
        self.frases = FrasesHabladas(grupos, prueba, ("comandos_ot", "comandos_ac"))
        self.frases.setFixedWidth(250)
        self.frases.btn_checked.connect(self._frase)
        fila.addWidget(self.frases)

        lienzo = QFrame()
        lienzo.setProperty("card", "true")
        col = QVBoxLayout(lienzo)
        col.setContentsMargins(8, 8, 8, 8)
        col.addWidget(self.cabeza, 1)
        herramientas = QHBoxLayout()
        herramientas.setSpacing(4)
        grupo = QButtonGroup(self)
        self.botones_herramienta = {}
        for clave, nombre, modulo in HERRAMIENTAS:
            if (modulo == "OT" and not self.con_ot) or (modulo == "AC" and not self.con_ac):
                continue
            b = QPushButton(nombre)
            b.setCheckable(True)
            b.setProperty("herramienta", "true")
            b.clicked.connect(lambda _c=False, k=clave: self.elegir_herramienta(k))
            grupo.addButton(b)
            herramientas.addWidget(b, 1)
            self.botones_herramienta[clave] = b
        col.addLayout(herramientas)
        vistas = QHBoxLayout()
        vistas.setSpacing(4)
        for texto, vista in VISTAS:
            b = QPushButton(texto)
            b.setProperty("segmento", "true")
            b.clicked.connect(lambda _c=False, v=vista: self.cabeza.mirar(*v))
            vistas.addWidget(b, 1)
        col.addLayout(vistas)
        self.pista = QLabel()
        self.pista.setProperty("role", "hint")
        self.pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.pista)
        fila.addWidget(lienzo, 1)

        panel = QFrame()
        panel.setProperty("card", "true")
        panel.setFixedWidth(270)
        pcol = QVBoxLayout(panel)
        pcol.setContentsMargins(12, 10, 12, 12)
        pcol.setSpacing(8)
        if self.con_ot:
            pcol.addWidget(self.otoscopia)
        else:
            self.otoscopia.setParent(self)
            self.otoscopia.hide()
        if self.con_ac:
            pcol.addWidget(self.acumetria)
            pcol.addWidget(self.acumetria.conversacion, 1)
        else:
            self.acumetria.setParent(self)
            self.acumetria.hide()
            pcol.addStretch(1)
        # Dentro del panel van sobre la tarjeta: sin el fondo del lienzo que
        # les pone tema.aplicar_estilo
        for pieza in (self.otoscopia, self.acumetria, self.acumetria.conversacion):
            pieza.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        fila.addWidget(panel)
        self.elegir_herramienta("girar")
        return tab

    def elegir_herramienta(self, clave):
        b = self.botones_herramienta.get(clave)
        if b is None:
            return
        b.setChecked(True)
        self.cabeza.poner_herramienta(clave)
        self.pista.setText(PISTAS[clave])

    def _frase(self, clave):
        """Cada frase va al examen que la tiene: las del otoscopio quedan en
        su registro (ot_instruccion) y en la conversación; las de los
        diapasones las contesta Acumetria."""
        if clave == SILENCIO:
            return
        if clave in self._claves_ot:
            self.otoscopia._frase(clave)
            if self.con_ac:
                texto = next((t for _g, frases in ot_mod.GRUPOS for t, c in frases if c == clave), clave)
                self.acumetria._decir(f"Tú: «{texto}»")
                if self.otoscopia.data:
                    self.acumetria._decir(f"Paciente: {RESPUESTA_OT.get(clave, 'Ya.')}")
            return
        self.acumetria._frase(clave)

    # ------------------------------------------------------------ informe
    def _informe(self):
        """Las dos secciones del informe, una debajo de la otra."""
        contenido = QWidget()
        col = QVBoxLayout(contenido)
        col.setContentsMargins(0, 10, 0, 0)
        col.setSpacing(12)
        if self.con_ot:
            col.addWidget(self._titulo("Otoscopía"))
            col.addWidget(self.otoscopia.informe)
        else:
            self.otoscopia.informe.setParent(contenido)
            self.otoscopia.informe.hide()
        if self.con_ac:
            col.addWidget(self._titulo("Diapasones"))
            col.addWidget(self.informe_acumetria)
        else:
            self.informe_acumetria.setParent(contenido)
            self.informe_acumetria.hide()
        col.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(contenido)
        return scroll

    @staticmethod
    def _titulo(texto):
        lbl = QLabel(texto)
        lbl.setObjectName("titulo_informe")
        return lbl

    def callar(self):
        self.frases.callar()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.frases.callar()
