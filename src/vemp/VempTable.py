"""
Tabla de latencias/amplitudes para VEMP.

Las filas cambian con el subtipo activo (CVEMP/MVEMP -> p13/n23, OVEMP ->
n10/p16) más una fila que el alumno no llena: la AMPLITUD PICO-PICO, que es
la que se informa en un VEMP y la que entra en la razón de asimetría. Se
calcula sola en cuanto los dos picos están marcados -- pedirla a mano
invitaba a informar la amplitud absoluta de un solo pico, que no se usa.

El alumno llena las otras celdas como en el ABR: pone el cursor A sobre el
pico, hace clic en la celda y el gráfico devuelve el valor y dibuja la marca.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QHeaderView, QLabel, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

COLOR_OD = QColor(255, 200, 200)  # rosa-rojo (OD)
COLOR_OI = QColor(200, 200, 255)  # lila-azul (OI)

FILA_P2P = 'p2p'


class VempTable(QWidget):
    # {'side': 0|1, 'pico': 'p13', 'campo': 'L'|'A'}
    sig_measure_value = Signal(dict)

    def __init__(self, side, peak_labels=None, parent=None):
        """side: 0 = OD, 1 = OI"""
        super().__init__(parent)
        self.side = side
        self.side_text = 'OD' if side == 0 else 'OI'
        self.peak_labels = list(peak_labels or ['p13', 'n23'])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self.lbl_titulo = QLabel(f'{self.side_text} -- sin curva')
        layout.addWidget(self.lbl_titulo)

        self.tw_latamp = QTableWidget(0, 2)
        self.tw_latamp.setHorizontalHeaderLabels(['Latencia (ms)', 'Amplitud (µV)'])
        self.tw_latamp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tw_latamp.cellClicked.connect(self._on_cell_clicked)
        color = COLOR_OD if self.side == 0 else COLOR_OI
        self.tw_latamp.setStyleSheet(
            f'QTableWidget {{ background-color: {color.name()}; }}')
        layout.addWidget(self.tw_latamp)
        self._refresh_rows()

    # =====================================================================
    # Filas
    # =====================================================================

    def _filas(self):
        return self.peak_labels + [FILA_P2P]

    def _etiqueta(self, fila):
        if fila == FILA_P2P:
            return '-'.join(p.upper() for p in self.peak_labels)
        return fila.upper()

    def _refresh_rows(self):
        filas = self._filas()
        self.tw_latamp.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            header = QTableWidgetItem(self._etiqueta(fila))
            header.setFlags(header.flags() & ~Qt.ItemIsEditable)
            self.tw_latamp.setVerticalHeaderItem(i, header)
            for col in (0, 1):
                item = QTableWidgetItem('')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tw_latamp.setItem(i, col, item)
        # La fila pico-pico no tiene latencia y no se pide a mano.
        self.tw_latamp.item(len(filas) - 1, 0).setText('--')

    def set_peak_labels(self, labels):
        """Cambia los picos que muestra la tabla (al cambiar subtipo)."""
        if list(labels) == self.peak_labels:
            return
        self.peak_labels = list(labels)
        self._refresh_rows()

    def set_titulo(self, curva=None, intensidad=None, subtipo=None):
        if curva is None:
            self.lbl_titulo.setText(f'{self.side_text} -- sin curva')
            return
        partes = [self.side_text, str(curva)]
        if intensidad is not None:
            partes.append(f'{intensidad} dB')
        if subtipo:
            partes.append(subtipo)
        self.lbl_titulo.setText(' · '.join(partes))

    # =====================================================================
    # Datos
    # =====================================================================

    def _on_cell_clicked(self, row, column):
        filas = self._filas()
        if row < 0 or row >= len(filas):
            return
        fila = filas[row]
        if fila == FILA_P2P:
            return   # se calcula sola con las dos marcas
        self.sig_measure_value.emit({
            'side': self.side,
            'pico': fila,
            'campo': 'L' if column == 0 else 'A',
        })

    def set_latamp(self, latamp):
        """latamp: {pico: [lat, amp]}. Rellena filas y la pico-pico."""
        latamp = latamp or {}
        filas = self._filas()
        for i, fila in enumerate(filas):
            if fila == FILA_P2P:
                continue
            vals = latamp.get(fila) or [None, None]
            lat, amp = (list(vals) + [None, None])[:2]
            self.tw_latamp.item(i, 0).setText('' if lat is None else f'{lat:.2f}')
            self.tw_latamp.item(i, 1).setText('' if amp is None else f'{amp:.1f}')
        p2p = self.peak_to_peak(latamp)
        self.tw_latamp.item(len(filas) - 1, 1).setText(
            '' if p2p is None else f'{p2p:.1f}')

    def peak_to_peak(self, latamp):
        """Amplitud pico-pico entre los dos picos del subtipo, si están los dos.

        Es una resta con signo (P13 arriba, N23 abajo): el valor absoluto de
        la diferencia, no la suma de dos módulos.
        """
        latamp = latamp or {}
        amps = []
        for pico in self.peak_labels:
            vals = latamp.get(pico)
            if not vals or vals[1] is None:
                return None
            amps.append(float(vals[1]))
        if len(amps) < 2:
            return None
        return abs(amps[0] - amps[1])

    def clear_all(self):
        for i in range(self.tw_latamp.rowCount()):
            for col in (0, 1):
                item = self.tw_latamp.item(i, col)
                if item is not None:
                    item.setText('')
        if self.tw_latamp.rowCount():
            self.tw_latamp.item(self.tw_latamp.rowCount() - 1, 0).setText('--')
        self.set_titulo(None)
