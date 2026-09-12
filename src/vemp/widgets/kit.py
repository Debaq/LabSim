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
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QSizePolicy, QVBoxLayout, QWidget)

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


class Campos(QWidget):
    """Rejilla rótulo/control, más compacta que un QFormLayout y con los
    rótulos en el mismo gris que el resto del módulo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(6)
        self.grid.setColumnStretch(1, 1)
        self._fila = 0

    def agregar(self, rotulo, widget):
        lbl = etiqueta(rotulo, rol='campo')
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
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
