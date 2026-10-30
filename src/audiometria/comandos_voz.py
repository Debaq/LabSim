"""
Comandos de voz del audiómetro: la frase que el evaluador le dice al
paciente por el talkback.

Se elige la frase acá y se dice con Talkback en el audiómetro. Cada frase
emite su clave (`btn_checked`), que es a la vez el nombre del audio
(resources/audio/comandos/<clave>.mp3) y lo que lee ResponseAudiometry.history_command
para decidir cómo responde el paciente: las claves no se cambian aunque
cambie el rótulo.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
                               QWidget)

from core import iconos, tema

SILENCIO = "silencio"

# (título, [(rótulo, clave)]). El orden es el de una sesión: primero se
# prepara al paciente, después se le explica qué hacer y se le pregunta.
GRUPOS = (
    ("PREPARAR", (
        ("Colocar fonos", "colocar_fonos"),
        ("Colocar vibrador", "colocar_vibrador"),
        ("Aérea + ruido", "aerea_+_ruido"),
        ("Vibrador + ruido", "vibrador_+_ruido"),
    )),
    ("INSTRUCCIONES", (
        ("Mano levantada", "mano_levantada"),
        ("Mano levantada en ruido", "mano_levantada_en_ruido"),
        ("Escuche mi voz", "escuche_mi_voz"),
        ("Dictar palabras", "dictar_palabras"),
        ("Pitos fuertes", "pitos_fuertes"),
        ("Solo si molesta", "solo_si_molesta"),
        ("Dos pitos", "dos_pitos"),
        ("Cambie de volumen", "cambie_de_volumen"),
        ("Ruido blanco contralateral", "ruido_blanco_contralateral"),
        ("Rosemberg bilateral", "rosemberg_bilateral"),
        ("Pa pa pa", "pa_pa_pa"),
    )),
    ("PREGUNTAS", (
        ("¿Escucha?", "escucha"),
        ("¿Dejó de escuchar?", "dejo_de_escuchar"),
        ("¿En qué oído?", "en_qué_oído"),
        ("¿Sonidos iguales?", "sonidos_iguales"),
        ("¿No entiende?", "no_entiende"),
        ("¿Molesta?", "molesta"),
        ("Molesto ¿o?", "molesto_o"),
        ("¿Muy fuerte?", "muy_fuerte"),
    )),
)
# La prueba en que se usa cada frase, a la vista en su botón: los alumnos
# no sabían qué instrucción iba con qué prueba. Lo mismo que la tabla de la
# sección 16 del manual del estudiante. Las preguntas que no son de una sola
# prueba (¿Escucha?, ¿Molesta?...) van sin rótulo.
PRUEBA = {
    "colocar_fonos": "Vía aérea",
    "colocar_vibrador": "Vía ósea",
    "aerea_+_ruido": "Aérea enmascarada",
    "vibrador_+_ruido": "Ósea enmascarada",
    "mano_levantada": "Carhart",
    "mano_levantada_en_ruido": "Carhart con ruido",
    "escuche_mi_voz": "Detección de la voz",
    "dictar_palabras": "Logoaudiometría",
    "pitos_fuertes": "LDL",
    "dos_pitos": "Fowler",
    "cambie_de_volumen": "SISI",
    "ruido_blanco_contralateral": "STAT",
    "rosemberg_bilateral": "Rosemberg",
    "pa_pa_pa": "Detección de la voz",
    "sonidos_iguales": "Fowler",
    "en_qué_oído": "Fowler",
}
# Columnas como máximo; con menos ancho se reacomodan (ver resizeEvent).
COLUMNAS = 3
ANCHO_FRASE = 155

EXTRA_QSS = f"""
QPushButton[frase="true"] {{ text-align: left; padding: 5px 9px; }}
QPushButton[frase="true"]:checked {{
    background: {tema.ACENTO};
    border-color: {tema.ACENTO};
}}
QLabel#rotulo {{ color: {tema.TEXTO}; background: transparent; }}
QLabel#prueba {{
    color: {tema.ACENTO}; background: transparent;
    font-size: 8pt; font-weight: 600;
}}
QLabel#rotulo[activa="true"], QLabel#prueba[activa="true"] {{ color: white; }}
QLabel#rotulo[activa="true"] {{ font-weight: 600; }}
QFrame#elegida {{
    background: {tema.ACENTO_SUAVE};
    border: 1px solid {tema.BORDE};
    border-radius: 10px;
}}
QFrame#elegida[vacia="true"] {{ background: {tema.TARJETA_ALT}; }}
QLabel#frase {{ font-size: 12pt; font-weight: 700; color: {tema.ACENTO}; }}
QFrame#elegida[vacia="true"] QLabel#frase {{ color: {tema.TEXTO_TENUE}; }}
QLineEdit {{
    background: {tema.TARJETA};
    border: 1px solid {tema.BORDE_FUERTE};
    border-radius: 7px;
    padding: 5px 8px;
}}
QLineEdit:focus {{ border-color: {tema.ACENTO}; }}
QWidget#lista {{ background: transparent; }}
"""


class ComandosVoz(QWidget):
    btn_checked = Signal(str)

    def __init__(self):
        super().__init__()
        tema.aplicar_estilo(self, EXTRA_QSS)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(8)

        raiz.addWidget(self._elegida())

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar frase…")
        self.buscar.addAction(iconos.icono("buscar", tema.TEXTO_TENUE, 16),
                              QLineEdit.ActionPosition.LeadingPosition)
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self._filtrar)
        # Enter elige la primera que coincide: escribir "mano" + Enter.
        self.buscar.returnPressed.connect(self._elegir_primera)
        # Silencio al lado de la búsqueda y no en la caja de la frase: en la
        # columna angosta junto al audiómetro ahí no cabía.
        fila = QHBoxLayout()
        fila.setSpacing(6)
        fila.addWidget(self.buscar, 1)
        fila.addWidget(self.btn_silencio)
        raiz.addLayout(fila)

        self.grupo = QButtonGroup(self)
        self.grupo.setExclusive(False)   # Silencio = ninguna marcada
        self.grupo.buttonClicked.connect(self._elegir)
        self.botones = {}        # clave -> botón
        self.secciones = []      # (rótulo de sección, [botones])

        lista = QWidget()
        lista.setObjectName("lista")
        col = QVBoxLayout(lista)
        col.setContentsMargins(0, 0, 4, 0)
        col.setSpacing(4)
        for titulo, frases in GRUPOS:
            rotulo = QLabel(titulo)
            rotulo.setProperty("role", "seccion")
            col.addSpacing(4)
            col.addWidget(rotulo)
            grilla = QGridLayout()
            grilla.setSpacing(5)
            botones = []
            for texto, clave in frases:
                btn = _boton_frase(texto, clave)
                self.grupo.addButton(btn)
                self.botones[clave] = btn
                botones.append(btn)
            col.addLayout(grilla)
            self.secciones.append((rotulo, grilla, botones))
        self.sin_resultados = QLabel("Ninguna frase coincide.")
        self.sin_resultados.setProperty("role", "hint")
        self.sin_resultados.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sin_resultados.hide()
        col.addWidget(self.sin_resultados)
        col.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(lista)
        raiz.addWidget(scroll, 1)

        self.columnas = COLUMNAS
        self.filtradas = set()   # las que esconde la búsqueda
        self._reacomodar()
        self._pintar(None)

    def resizeEvent(self, event):
        """En una columna angosta (pantallas chicas) las frases van de a una
        o dos por fila, sin cortarse."""
        super().resizeEvent(event)
        columnas = max(1, min(COLUMNAS, self.width() // ANCHO_FRASE))
        if columnas != self.columnas:
            self.columnas = columnas
            self._reacomodar()

    def _reacomodar(self):
        """Pone en la grilla las frases que no esconde la búsqueda, sin
        dejar huecos. Se mira `filtradas` y no isHidden(): antes de mostrarse
        la ventana todas cuentan como escondidas."""
        for _rotulo, grilla, botones in self.secciones:
            for b in botones:
                grilla.removeWidget(b)
            for i, b in enumerate(b for b in botones if b not in self.filtradas):
                grilla.addWidget(b, i // self.columnas, i % self.columnas)
            for c in range(COLUMNAS):
                grilla.setColumnStretch(c, 1 if c < self.columnas else 0)

    def _elegida(self):
        """La frase que se va a decir. Silencio (no decir nada) se arma acá
        y va junto a la búsqueda."""
        caja = QFrame()
        caja.setObjectName("elegida")
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(12, 8, 8, 8)
        fila.setSpacing(10)
        icono = QLabel()
        icono.setPixmap(iconos.pixmap("microfono", tema.ACENTO, 22))
        fila.addWidget(icono)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.lbl_frase = QLabel()
        self.lbl_frase.setObjectName("frase")
        self.lbl_pista = QLabel()
        self.lbl_pista.setProperty("role", "hint")
        # En la columna angosta junto al audiómetro el texto se parte en líneas.
        self.lbl_frase.setWordWrap(True)
        self.lbl_pista.setWordWrap(True)
        textos.addWidget(self.lbl_frase)
        textos.addWidget(self.lbl_pista)
        fila.addLayout(textos, 1)
        self.btn_silencio = QPushButton(" Silencio")
        self.btn_silencio.setIcon(iconos.icono_boton("x", tema.TEXTO_SUAVE, tam=14))
        self.btn_silencio.clicked.connect(self.silencio)
        self.btn_silencio.setMinimumWidth(self.btn_silencio.sizeHint().width())
        self.caja_elegida = caja
        return caja

    def _elegir(self, btn):
        if not btn.isChecked():
            # Volver a tocar la frase elegida la suelta: es Silencio.
            self.silencio()
            return
        for otro in self.grupo.buttons():
            if otro is not btn:
                otro.setChecked(False)
        self._pintar(btn)
        self.btn_checked.emit(btn.property("clave"))

    def _elegir_primera(self):
        for _rotulo, _grilla, botones in self.secciones:
            for b in botones:
                if not b.isHidden():
                    if not b.isChecked():
                        b.click()
                    return

    def silencio(self):
        for btn in self.grupo.buttons():
            btn.setChecked(False)
        self._pintar(None)
        self.btn_checked.emit(SILENCIO)

    def _pintar(self, btn):
        if btn is None:
            self.lbl_frase.setText("Silencio")
            self.lbl_pista.setText("Elige una frase para decírsela al paciente.")
        else:
            self.lbl_frase.setText(btn.property("rotulo"))
            prueba = PRUEBA.get(btn.property("clave"))
            pista = "Presiona Talkback en el audiómetro para decirla."
            self.lbl_pista.setText(f"{prueba} · {pista}" if prueba else pista)
        self.btn_silencio.setEnabled(btn is not None)
        self.caja_elegida.setProperty("vacia", "true" if btn is None else "false")
        tema.repintar(self.caja_elegida)
        tema.repintar(self.lbl_frase)

    def _filtrar(self, texto):
        """Muestra las frases que contienen lo escrito (sin tildes ni
        signos), en el rótulo o en la prueba: "sisi" encuentra Cambie de
        volumen."""
        buscado = _plano(texto)
        alguna = False
        for rotulo, _grilla, botones in self.secciones:
            visibles = [b for b in botones if buscado in _plano(_buscable(b))]
            for b in botones:
                b.setVisible(b in visibles)
                if b in visibles:
                    self.filtradas.discard(b)
                else:
                    self.filtradas.add(b)
            rotulo.setVisible(bool(visibles))
            alguna = alguna or bool(visibles)
        self._reacomodar()
        self.sin_resultados.setVisible(not alguna)


class _BotonFrase(QPushButton):
    """QPushButton mide su alto por su texto, no por su layout: con las dos
    etiquetas adentro, las líneas se encimaban."""

    def sizeHint(self):
        return self.layout().sizeHint()

    def minimumSizeHint(self):
        return self.layout().minimumSize()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, ancho):
        return self.layout().totalHeightForWidth(ancho)


def _boton_frase(texto, clave):
    """Botón de una frase: el rótulo y, debajo, la prueba en que se usa.
    Sin texto propio (lo pintan las etiquetas); el rótulo queda en la
    propiedad `rotulo`."""
    btn = _BotonFrase()
    btn.setCheckable(True)
    btn.setProperty("frase", "true")
    btn.setProperty("clave", clave)
    btn.setProperty("rotulo", texto)
    btn.setAccessibleName(texto)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    col = QVBoxLayout(btn)
    col.setContentsMargins(9, 4, 9, 4)
    col.setSpacing(0)
    etiquetas = [QLabel(texto)]
    etiquetas[0].setObjectName("rotulo")
    etiquetas[0].setWordWrap(True)
    prueba = PRUEBA.get(clave)
    if prueba:
        etiquetas.append(QLabel(prueba))
        etiquetas[1].setObjectName("prueba")
    for lbl in etiquetas:
        lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        col.addWidget(lbl)
    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def marcar(activa):
        for lbl in etiquetas:
            lbl.setProperty("activa", "true" if activa else "false")
            tema.repintar(lbl)
    btn.toggled.connect(marcar)
    return btn


def _buscable(btn):
    return f"{btn.property('rotulo')} {PRUEBA.get(btn.property('clave'), '')}"


def _plano(texto):
    tabla = str.maketrans("áéíóúü", "aeiouu", "¿?")
    return texto.lower().translate(tabla).strip()
