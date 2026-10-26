"""Tabla de marcas del ABR: los dos oídos en una sola grilla.

    |        |   OD    |   OI    |
    |        | Lat Amp | Lat Amp |
    | Onda I |         |         |
    |  ...   |         |         |
    | Interpicos                 |
    | I–V    |  (2 col)|  (2 col)|

Cada AbrTable (uno por oído) sigue siendo quien guarda los datos y marca lo
que cae fuera de norma; acá solo se dibuja. Le ve esta grilla a través de
`Vista`, que se porta como la QTableWidget chica que tenía antes (item,
setItem, rowCount, columnCount), así su lógica no cambió.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

from core import tema

ONDAS = ('Onda I', 'Onda II', 'Onda III', 'Onda IV', 'Onda V')
INTERPICOS = ('I–V', 'III–V', 'I–III', 'V / I')

FILA_TITULO = 0
FILA_SUBTITULO = 1
FILA_ONDA0 = 2
FILA_INTERPICOS = FILA_ONDA0 + len(ONDAS)
FILA_INTER0 = FILA_INTERPICOS + 1
FILAS = FILA_INTER0 + len(INTERPICOS)

ANCHO_NOMBRE = 74
ANCHO_VALOR = 54
ALTO_FILA = 28
# Primera columna de cada oído (OD, OI) dentro de la grilla.
COLUMNA_OIDO = (1, 3)


class Vista:
    """Un pedazo de la grilla, con la interfaz de una QTableWidget."""

    def __init__(self, tabla, fila0, col0, filas, columnas):
        self._tabla = tabla
        self._fila0 = fila0
        self._col0 = col0
        self._filas = filas
        self._columnas = columnas

    def rowCount(self):
        return self._filas

    def columnCount(self):
        return self._columnas

    def item(self, fila, columna):
        return self._tabla.item(self._fila0 + fila, self._col0 + columna)

    def setItem(self, fila, columna, item):
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self._tabla.setItem(self._fila0 + fila, self._col0 + columna, item)


class MarcasAbr(QTableWidget):
    def __init__(self):
        super().__init__(FILAS, 5)
        self.setObjectName('marcasAbr')
        self._al_clic = {}
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(ALTO_FILA)
        self.verticalHeader().setMinimumSectionSize(ALTO_FILA)
        self.setColumnWidth(0, ANCHO_NOMBRE)
        for columna in range(1, 5):
            self.setColumnWidth(columna, ANCHO_VALOR)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        ancho = ANCHO_NOMBRE + 4 * ANCHO_VALOR + 2 * self.frameWidth()
        alto = FILAS * ALTO_FILA + 2 * self.frameWidth()
        self.setFixedSize(ancho, alto)
        self._rotular()
        self.cellClicked.connect(self._clic)

    # ------------------------------------------------------------ armado
    def _rotulo(self, fila, columna, texto, fondo=tema.TARJETA_ALT, color=tema.TEXTO_TENUE,
                negrita=True, puntos=7.5, alinear=Qt.AlignmentFlag.AlignCenter):
        item = QTableWidgetItem(texto)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setBackground(QBrush(QColor(fondo)))
        item.setForeground(QBrush(QColor(color)))
        item.setTextAlignment(alinear)
        letra = QFont(self.font())
        letra.setPointSizeF(puntos)
        letra.setBold(negrita)
        item.setFont(letra)
        self.setItem(fila, columna, item)

    def _rotular(self):
        izquierda = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        self._rotulo(FILA_TITULO, 0, '')
        self._rotulo(FILA_SUBTITULO, 0, '')
        for lado, (texto, fondo, color) in enumerate((('OD', tema.OD_SUAVE, tema.OD),
                                                       ('OI', tema.OI_SUAVE, tema.OI))):
            col = COLUMNA_OIDO[lado]
            self._rotulo(FILA_TITULO, col, texto, fondo, color, puntos=8.5)
            self.setSpan(FILA_TITULO, col, 1, 2)
            self._rotulo(FILA_SUBTITULO, col, 'Lat ms')
            self._rotulo(FILA_SUBTITULO, col + 1, 'Amp µV')
            for i in range(len(INTERPICOS)):
                self.setSpan(FILA_INTER0 + i, col, 1, 2)
        for i, nombre in enumerate(ONDAS):
            self._rotulo(FILA_ONDA0 + i, 0, nombre, color=tema.TEXTO_SUAVE, puntos=8.5,
                         alinear=izquierda)
        self._rotulo(FILA_INTERPICOS, 0, 'INTERPICOS', alinear=izquierda)
        self.setSpan(FILA_INTERPICOS, 0, 1, 5)
        for i, nombre in enumerate(INTERPICOS):
            self._rotulo(FILA_INTER0 + i, 0, nombre, color=tema.TEXTO_SUAVE, puntos=8.5,
                         alinear=izquierda)

    # ------------------------------------------------------------- vistas
    def ondas(self, lado):
        """Latencia y amplitud de las cinco ondas de ese oído."""
        return Vista(self, FILA_ONDA0, COLUMNA_OIDO[lado], len(ONDAS), 2)

    def interpicos(self, lado):
        """Interpicos y razón V/I de ese oído (una columna)."""
        return Vista(self, FILA_INTER0, COLUMNA_OIDO[lado], len(INTERPICOS), 1)

    def al_clic_en_onda(self, lado, funcion):
        self._al_clic[lado] = funcion

    def _clic(self, fila, columna):
        if not FILA_ONDA0 <= fila < FILA_ONDA0 + len(ONDAS):
            return
        for lado, col0 in enumerate(COLUMNA_OIDO):
            if col0 <= columna < col0 + 2 and lado in self._al_clic:
                self._al_clic[lado](fila - FILA_ONDA0, columna - col0)
