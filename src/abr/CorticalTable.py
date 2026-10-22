"""Tabla de medidas de los potenciales de latencia media y tardía.

Una por oído, como la del ECochG. Las columnas son los canales de la
captura seleccionada (C3/Cz/C4 en el MLR, Fz/Cz/Pz en los tardíos) y las
filas, las latencias de cada componente y la amplitud que se informa en la
prueba (Na-Pa, N1-P2, P3 o MMN).

Se marca como en el ABR: se lleva la bandera A al componente, se elige el
canal haciendo clic en su etiqueta y se aprieta el botón del componente
(barra de arriba). Las marcas se pegan al pico o al valle más cercano.

Abajo van las comparaciones, que no son de una curva: el efecto electrodo
(C3 contra C4) y el efecto oído (OD contra OI) del MLR, que es lo que
localiza; la tarea que se le dio al paciente en el oddball, y su respuesta
en la P300 (conteo o botón), que valida la tarea.
"""
# pylint: disable=no-name-in-module
from PySide6.QtCore import QCoreApplication, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QToolButton,
                               QVBoxLayout, QWidget)

from abr import cortical

tr = QCoreApplication.translate

# Amplitud que se informa en cada prueba: (clave en measure, rótulo).
AMPLITUDES = {
    'MLR': (('Na-Pa', "Amplitud Na-Pa"),),
    'CAEP': (('N1-P2', "Amplitud N1-P2"),),
    'P300': (('N1-P2', "Amplitud N1-P2"), ('P3', "Amplitud P3")),
    'MMN': (('MMN', "Amplitud MMN"),),
}


class CorticalTable(QWidget):
    """Medidas de un oído para MLR, CAEP, P300 o MMN."""

    # Marca pedida con su botón: se pone en la bandera A del gráfico.
    sig_mark = Signal(int, str)

    OUT_COLOR = QColor(255, 120, 120, 170)

    def __init__(self, side) -> None:
        QWidget.__init__(self)
        self.side = side
        self.side_text = 'OD' if side == 0 else 'OI'
        self.test = 'MLR'
        self.norms = {}
        self.medidas = {}       # {canal: cortical.measure(...)}
        self.grupo = None
        self.efectos = {}
        self.conteo = None
        self.tarea = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.cabecera = QHBoxLayout()
        self.label = QLabel(self.side_text)
        self.cabecera.addWidget(self.label)
        self.cabecera.addStretch(1)
        layout.addLayout(self.cabecera)
        self.botones = []
        self.tabla = QTableWidget(0, 3, self)
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        color = 'rgba(255, 0, 127, 30)' if self.side == 0 else '#9965f4'
        self.tabla.setStyleSheet(
            f"QTableWidget::item{{ background-color:{color}; }}")
        layout.addWidget(self.tabla)
        self.lbl_extra = QLabel("")
        self.lbl_extra.setWordWrap(True)
        layout.addWidget(self.lbl_extra)
        self.set_test('MLR')

    # ------------------------------------------------------------ prueba

    def set_test(self, test) -> None:
        """Botones y filas de la prueba."""
        if test not in cortical.TESTS:
            return
        self.test = test
        for btn in self.botones:
            self.cabecera.removeWidget(btn)
            btn.deleteLater()
        self.botones = []
        for marca in cortical.MARKS[test]:
            btn = QToolButton(self)
            btn.setText(marca)
            btn.setToolTip(f"{marca}: se pone en la curva seleccionada, donde "
                           "está la bandera A (se pega al "
                           + ("valle" if cortical.mark_polarity(marca) < 0
                              else "pico") + " más cercano)")
            btn.clicked.connect(
                lambda _=False, m=marca: self.sig_mark.emit(self.side, m))
            self.botones.append(btn)
            self.cabecera.addWidget(btn)
        canales = cortical.CHANNELS[test]
        self.filas = ([('lat', m, f"Latencia {m}", "ms", 0 if test != 'MLR' else 1)
                       for m in cortical.MARKS[test]]
                      + [('amp', clave, rotulo, "µV", 2)
                         for clave, rotulo in AMPLITUDES[test]])
        self.tabla.setColumnCount(len(canales))
        self.tabla.setHorizontalHeaderLabels(list(canales))
        self.tabla.setRowCount(len(self.filas))
        self.tabla.setVerticalHeaderLabels([f[2] for f in self.filas])
        self.clear_all()

    # ------------------------------------------------------------ valores

    def set_norms(self, norms) -> None:
        self.norms = norms or {}
        self._pintar()

    def set_medidas(self, grupo, medidas) -> None:
        """Medidas de los canales de la captura seleccionada."""
        self.grupo = grupo
        self.medidas = dict(medidas or {})
        self._pintar()

    def set_efectos(self, efectos) -> None:
        """Efecto electrodo y oído del MLR (ver AbrMainWindow)."""
        self.efectos = dict(efectos or {})
        self._pintar()

    def set_conteo(self, conteo) -> None:
        self.conteo = conteo
        self._pintar()

    def set_tarea(self, tarea) -> None:
        """Instrucción con que se registró la captura (P300 y MMN)."""
        self.tarea = tarea
        self._pintar()

    def clear_all(self) -> None:
        self.grupo = None
        self.medidas = {}
        self._pintar()

    # ------------------------------------------------------------ pintado

    def _pintar(self) -> None:
        canales = cortical.CHANNELS[self.test]
        for fila, (tipo, clave, _, unidad, dec) in enumerate(self.filas):
            for col, canal in enumerate(canales):
                valor = (self.medidas.get(canal) or {}).get(tipo, {}).get(clave)
                item = QTableWidgetItem("" if valor is None
                                        else f"{valor:.{dec}f} {unidad}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if valor is not None:
                    self._flag(item, tipo, clave, valor)
                self.tabla.setItem(fila, col, item)
        self.label.setText(self.side_text + (f" · {self.grupo}" if self.grupo else ""))
        self.lbl_extra.setText(self._texto_extra())

    def _texto_extra(self) -> str:
        partes = []
        if self.test == 'MLR':
            limite = self.norms.get('electrode_effect')
            for clave, rotulo, donde in (
                    ('electrodo', "Efecto electrodo (C3/C4)", 'hemisferio'),
                    ('oido', "Efecto oído (OD/OI)", 'oído')):
                dif, lado = self.efectos.get(clave, (None, None))
                if dif is None:
                    partes.append(f"{rotulo}: falta Na-Pa "
                                  + ("en C3 y C4" if clave == 'electrodo'
                                     else "de los dos oídos"))
                    continue
                texto = f"{rotulo}: {dif * 100:.0f}% menor {donde} {lado}"
                if limite and dif >= limite:
                    texto = f"<b style='color:#b00'>{texto}</b>"
                partes.append(texto)
        if self.test in cortical.ODDBALL_TESTS and self.tarea and self.medidas:
            partes.append("Tarea: " + cortical.TAREA_LABELS.get(self.tarea, self.tarea))
        if self.test == 'P300' and self.conteo:
            if self.conteo.get('tarea') == 'boton':
                partes.append(f"Botón: {self.conteo['aciertos']} aciertos de "
                              f"{self.conteo['reales']} raros, "
                              f"{self.conteo['falsas']} falsas alarmas")
            else:
                partes.append(f"Conteo del paciente: {self.conteo['dice']} raros "
                              f"(presentados {self.conteo['reales']})")
        elif self.test == 'P300' and self.conteo is None and self.medidas:
            partes.append("El paciente no informó raros")
        return "<br>".join(partes)

    def _flag(self, item, tipo, clave, valor) -> None:
        rango = (self.norms.get(tipo) or {}).get(clave)
        if not rango:
            return
        lo, hi = rango
        # La amplitud se compara sin signo: la MMN se informa negativa.
        medido = abs(valor) if tipo == 'amp' else valor
        if lo <= medido <= hi:
            return
        item.setBackground(self.OUT_COLOR)
        item.setToolTip(f"Fuera de rango: esperado {lo:.1f} – {hi:.1f}")
