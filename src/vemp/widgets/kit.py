"""
Piezas de UI compartidas del módulo VEMP.

Qt no trae "tarjeta", "dato grande" ni "píldora", y sin eso un módulo
clínico termina siendo una pila de QGroupBox con el título en negrita. Acá
están las cuatro piezas con las que está armado todo el VEMP, para que las
pantallas se escriban en términos del examen y no de layouts.

El estilo sale de vemp.theme (QSS por propiedad): estas clases solo ponen la
propiedad y el layout.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QSizePolicy, QStyle,
                               QStyleOptionComboBox, QStylePainter,
                               QVBoxLayout, QWidget)

from vemp import theme


class Tarjeta(QFrame):
    """Panel blanco con borde y radio. `cuerpo` es su layout vertical."""

    def __init__(self, titulo=None, plano=False, parent=None):
        super().__init__(parent)
        self.setProperty('card', 'flat' if plano else 'true')
        self.cuerpo = QVBoxLayout(self)
        self.cuerpo.setContentsMargins(12, 10, 12, 12)
        self.cuerpo.setSpacing(8)
        self.lbl_titulo = None
        if titulo:
            self.lbl_titulo = etiqueta_seccion(titulo)
            self.cuerpo.addWidget(self.lbl_titulo)

    def set_titulo(self, texto):
        if self.lbl_titulo is not None:
            self.lbl_titulo.setText(texto.upper())

    def agregar(self, widget, *args):
        self.cuerpo.addWidget(widget, *args)
        return widget

    def agregar_layout(self, layout):
        self.cuerpo.addLayout(layout)
        return layout


def etiqueta_seccion(texto):
    lbl = QLabel(texto.upper())
    lbl.setProperty('role', 'seccion')
    return lbl


def etiqueta(texto, rol=None, estado=None):
    lbl = QLabel(texto)
    if rol:
        lbl.setProperty('role', rol)
    if estado:
        lbl.setProperty('estado', estado)
    return lbl


class Pastilla(QLabel):
    """Etiqueta chica con fondo: oído, subtipo, estado del registro."""

    def __init__(self, texto='', tipo='neutro', parent=None):
        super().__init__(texto, parent)
        self.setProperty('pill', tipo)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def set_tipo(self, tipo):
        if self.property('pill') == tipo:
            return
        self.setProperty('pill', tipo)
        theme.repintar(self)

    def set(self, texto, tipo=None):
        self.setText(texto)
        if tipo:
            self.set_tipo(tipo)


class Dato(QWidget):
    """Un número grande con su unidad y su rótulo: la unidad de lectura de
    todos los paneles de resultado del módulo."""

    def __init__(self, rotulo, valor='--', unidad='', parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(4)
        self.lbl_valor = etiqueta(valor, rol='dato')
        fila.addWidget(self.lbl_valor)
        self.lbl_unidad = etiqueta(unidad, rol='unidad')
        self.lbl_unidad.setAlignment(Qt.AlignmentFlag.AlignBottom)
        fila.addWidget(self.lbl_unidad)
        fila.addStretch(1)
        layout.addLayout(fila)

        self.lbl_rotulo = etiqueta_seccion(rotulo)
        layout.addWidget(self.lbl_rotulo)

    def set_valor(self, valor, estado=None):
        self.lbl_valor.setText(str(valor))
        self.lbl_valor.setProperty('estado', estado or '')
        theme.repintar(self.lbl_valor)

    def set_unidad(self, unidad):
        self.lbl_unidad.setText(unidad)


class EtiquetaRecortada(QLabel):
    """QLabel de una línea que se achica con puntos suspensivos en vez de
    empujar el layout: en la barra de cada traza, a 1024 px, el texto de la
    curva se metía debajo de los botones de pico."""

    def __init__(self, texto='', rol=None, parent=None):
        super().__init__(parent)
        if rol:
            self.setProperty('role', rol)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(20)
        self._completo = ''
        self.setText(texto)

    def setText(self, texto):
        self._completo = texto or ''
        self.setToolTip(self._completo)
        self._recortar()

    def text(self):
        return self._completo

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._recortar()

    def _recortar(self):
        recortado = self.fontMetrics().elidedText(
            self._completo, Qt.TextElideMode.ElideRight, max(self.width(), 0))
        super().setText(recortado)


class ComboRecortado(QComboBox):
    """Combo que muestra la opción con puntos suspensivos si no cabe, con la
    lista desplegada al ancho del texto entero.

    Las maniobras y los transductores son textos largos ('Presión contra la
    mano del examinador') y también son la clave con la que el motor y el
    informe los leen: no se pueden acortar. Un QComboBox común los cortaba
    a la mitad de una letra.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(8)
        self.currentTextChanged.connect(self.setToolTip)

    def showPopup(self):
        ancho = max((self.fontMetrics().horizontalAdvance(self.itemText(i))
                     for i in range(self.count())), default=0)
        self.view().setMinimumWidth(max(ancho + 32, self.width()))
        super().showPopup()

    def paintEvent(self, _evento):
        pintor = QStylePainter(self)
        opcion = QStyleOptionComboBox()
        self.initStyleOption(opcion)
        pintor.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opcion)
        texto = self.style().subControlRect(
            QStyle.ComplexControl.CC_ComboBox, opcion,
            QStyle.SubControl.SC_ComboBoxEditField, self)
        opcion.currentText = self.fontMetrics().elidedText(
            opcion.currentText, Qt.TextElideMode.ElideRight, texto.width())
        pintor.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opcion)


class Campos(QWidget):
    """Rejilla rótulo/control, más compacta que un QFormLayout y con los
    rótulos en el mismo gris que el resto del módulo.

    La columna de rótulos tiene el mismo ancho en todas las tarjetas: cada
    rejilla mide la suya y los campos de Prueba, Estímulo y Registro
    quedaban cada uno empezando en otra x."""

    ANCHO_ROTULO = 74

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(5)
        self.grid.setColumnMinimumWidth(0, self.ANCHO_ROTULO)
        self.grid.setColumnStretch(1, 1)
        self._fila = 0

    def agregar(self, rotulo, widget):
        lbl = etiqueta(rotulo, rol='campo')
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.grid.addWidget(lbl, self._fila, 0)
        self.grid.addWidget(widget, self._fila, 1)
        self._fila += 1
        return widget

    def agregar_ancho(self, widget):
        self.grid.addWidget(widget, self._fila, 0, 1, 2)
        self._fila += 1
        return widget


def separador():
    linea = QFrame()
    linea.setFrameShape(QFrame.Shape.HLine)
    linea.setFixedHeight(1)
    linea.setStyleSheet(f'background: {theme.BORDE}; border: none;')
    return linea
