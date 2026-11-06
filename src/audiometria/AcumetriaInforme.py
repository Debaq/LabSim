"""Informe de diapasones: símbolos y flechas por diapasón, como se anota a
mano y como lo dibuja la ficha del caso (CaseSheetPdf::acumetria).

- Rinne: (+), (−) o FN (falso negativo) en cada oído, por diapasón. Cada
  casilla pasa de vacía a (+), a (−), a FN y vuelve a vacía.
- Weber: una flecha hacia el lado al que lateraliza (izquierda = OD, roja;
  derecha = OI, azul) o las dos si no lateraliza. Los colores son de la
  posición, no del resultado (labsim_weber_flechas_color_por_lado).

Va dentro del informe de otoscopía (tipo OTOSCOPIA, clave "acumetria"): es
la misma pantalla y así no hace falta un tipo nuevo en la base. Sin texto:
la lectura la hace el alumno.
"""
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from audiometria.diapasones import DIAPASONES
from core import tema

RINNE = ("", "positivo", "negativo", "falso_negativo")   # el ciclo de cada casilla
# El falso negativo no lleva signo: no es un resultado de ese oído (lo oye
# el otro), y como (−) desaparecería entre los negativos de verdad
SIMBOLO_RINNE = {"": "", "positivo": "(+)", "negativo": "(−)", "falso_negativo": "FN"}
WEBER = ("od", "centrado", "oi")


class _Flechas(QWidget):
    """Las flechas del Weber dibujadas (como en la ficha)."""

    def __init__(self, lado, parent=None):
        super().__init__(parent)
        self.lado = lado
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() / 2
        medio = self.width() / 2
        if self.lado in ("od", "centrado"):
            self._flecha(p, medio - 4, y, -1, QColor(tema.OD))
        if self.lado in ("oi", "centrado"):
            self._flecha(p, medio + 4, y, 1, QColor(tema.OI))
        p.end()

    @staticmethod
    def _flecha(p, x, y, hacia, color):
        largo = 18
        p.setPen(QPen(color, 2.4))
        p.drawLine(QPointF(x, y), QPointF(x + hacia * largo, y))
        punta = x + hacia * (largo + 2)
        p.setBrush(color)
        p.drawPolygon(QPolygonF([QPointF(punta, y), QPointF(punta - hacia * 7, y - 5),
                                 QPointF(punta - hacia * 7, y + 5)]))


class InformeAcumetria(QWidget):
    cambio = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(8)
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(8)
        grilla.setVerticalSpacing(6)
        for col, (texto, color) in enumerate((("OD", tema.OD), ("", None), ("OI", tema.OI)), start=1):
            if texto:
                lbl = QLabel(texto)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet(f"color: {color}; font-weight: 700;")
                grilla.addWidget(lbl, 0, col)
        titulo = QLabel("RINNE")
        titulo.setProperty("role", "seccion")
        grilla.addWidget(titulo, 0, 0)
        titulo_w = QLabel("WEBER")
        titulo_w.setProperty("role", "seccion")
        grilla.addWidget(titulo_w, 0, 5, 1, 3)
        self.rinne = {}       # (hz, oido) -> botón que cicla
        self.weber = {}       # hz -> {lado: botón}
        self._grupos = []
        for fila, (hz, texto) in enumerate(DIAPASONES, start=1):
            etiqueta = QLabel(texto)
            etiqueta.setStyleSheet("font-weight: 600;")
            grilla.addWidget(etiqueta, fila, 0)
            for col, oido in ((1, "od"), (3, "oi")):
                b = QPushButton("")
                b.setFixedSize(52, 30)
                b.setProperty("valor", "")
                color = tema.OD if oido == "od" else tema.OI
                b.setStyleSheet(f"QPushButton {{ color: {color}; font-weight: 700; font-size: 11pt; }}")
                b.setToolTip("Clic: (+), otra vez (−), otra vez FN (falso negativo), otra vez vacío")
                b.clicked.connect(lambda _c=False, k=(hz, oido): self._ciclar(k))
                grilla.addWidget(b, fila, col)
                self.rinne[(hz, oido)] = b
            grupo = QButtonGroup(self)
            grupo.setExclusive(False)
            self.weber[hz] = {}
            for col, lado in zip((5, 6, 7), WEBER):
                b = QPushButton()
                b.setCheckable(True)
                b.setFixedSize(64, 30)
                flechas = _Flechas(lado, b)
                flechas.resize(64, 30)
                b.clicked.connect(lambda marcado, h=hz, l=lado: self._weber(h, l, marcado))
                grilla.addWidget(b, fila, col)
                self.weber[hz][lado] = b
            self._grupos.append(grupo)
        grilla.setColumnStretch(8, 1)
        raiz.addLayout(grilla)
        raiz.addStretch(1)

    def _ciclar(self, clave):
        b = self.rinne[clave]
        valor = RINNE[(RINNE.index(b.property("valor")) + 1) % len(RINNE)]
        self._poner_rinne(clave, valor)
        self.cambio.emit()

    def _poner_rinne(self, clave, valor):
        b = self.rinne[clave]
        b.setProperty("valor", valor)
        b.setText(SIMBOLO_RINNE[valor])

    def _weber(self, hz, lado, marcado):
        # Una sola flecha por diapasón (o ninguna)
        for otro, b in self.weber[hz].items():
            if otro != lado:
                b.setChecked(False)
        self.weber[hz][lado].setChecked(marcado)
        self.cambio.emit()

    # ------------------------------------------------------------ datos
    def to_dict(self):
        rinne = {}
        for (hz, oido), b in self.rinne.items():
            if b.property("valor"):
                rinne.setdefault(hz, {})[oido] = b.property("valor")
        weber = {hz: lado for hz, botones in self.weber.items()
                 for lado, b in botones.items() if b.isChecked()}
        return {"rinne": rinne, "weber": weber}

    def tiene_algo(self):
        d = self.to_dict()
        return bool(d["rinne"] or d["weber"])

    def from_dict(self, d):
        self.limpiar()
        for hz, oidos in ((d or {}).get("rinne") or {}).items():
            for oido, valor in (oidos or {}).items():
                if (hz, oido) in self.rinne and valor in RINNE:
                    self._poner_rinne((hz, oido), valor)
        for hz, lado in ((d or {}).get("weber") or {}).items():
            if hz in self.weber and lado in self.weber[hz]:
                self.weber[hz][lado].setChecked(True)

    def limpiar(self):
        for clave in self.rinne:
            self._poner_rinne(clave, "")
        for botones in self.weber.values():
            for b in botones.values():
                b.setChecked(False)
