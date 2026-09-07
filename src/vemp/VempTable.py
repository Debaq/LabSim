"""
Tabla de latencias/amplitudes para VEMP.

Adaptación de AbrTable: las filas cambian según el subtipo activo
(CVEMP/MVEMP → p13/n23, OVEMP → n10/p16). set_peak_labels() reconstruye
las filas; el alumno marca los valores haciendo click y el gráfico se los
devuelve via medida de cursores A/A'.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QLabel


COLOR_OD = QColor(255, 200, 200)  # rosa-rojo (OD)
COLOR_OI = QColor(200, 200, 255)  # lila-azul (OI)


class VempTable(QWidget):
    sig_measure_value = Signal(dict)  # {'od': {'p13_L': None}} cuando pide valor

    def __init__(self, side, parent=None):
        """
        side: 0 = OD, 1 = OI
        peak_labels: lista de nombres de picos (['p13','n23'] o ['n10','p16'])
        """
        super().__init__(parent)
        self.side = side
        self.side_text = 'OD' if side == 0 else 'OI'
        self.peak_labels = ['p13', 'n23']  # default CVEMP
        self.data = self._init_data()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'Latencias / Amplitudes ({self.side_text})'))

        self.tw_latamp = QTableWidget(len(self.peak_labels), 2)
        self.tw_latamp.setHorizontalHeaderLabels(['Latencia (ms)', 'Amplitud (µV)'])
        self.tw_latamp.verticalHeader().setVisible(False)
        self.tw_latamp.cellClicked.connect(self._on_cell_clicked)
        self._refresh_rows()
        layout.addWidget(self.tw_latamp)

    def _init_data(self):
        return [['', ''] for _ in self.peak_labels]

    def _refresh_rows(self):
        self.tw_latamp.setRowCount(len(self.peak_labels))
        for i, pico in enumerate(self.peak_labels):
            header = QTableWidgetItem(pico.upper())
            header.setFlags(header.flags() & ~Qt.ItemIsEditable)
            self.tw_latamp.setVerticalHeaderItem(i, header)
        # Restyle background
        color = COLOR_OD if self.side == 0 else COLOR_OI
        self.tw_latamp.setStyleSheet(f'QTableWidget {{ background-color: {color.name()}; }}')

    def set_peak_labels(self, labels):
        """Cambia los picos que muestra la tabla (al cambiar subtipo)."""
        if labels == self.peak_labels:
            return
        self.peak_labels = list(labels)
        self.data = self._init_data()
        self._refresh_rows()

    def _on_cell_clicked(self, row, column):
        if row < 0 or row >= len(self.peak_labels):
            return
        pico = self.peak_labels[row]
        col = 'L' if column == 0 else 'A'
        key = f'{pico}_{col}'
        self.sig_measure_value.emit({f'{self.side_text.lower()}': {key: None}})

    def set_data(self, data):
        """data: dict {pico: [lat, amp]}; actualiza la fila correspondiente."""
        if not isinstance(data, dict):
            return
        for i, pico in enumerate(self.peak_labels):
            if pico in data:
                vals = data[pico]
                if isinstance(vals, (list, tuple)) and len(vals) >= 2:
                    self.data[i][0] = str(round(vals[0], 2)) if vals[0] is not None else ''
                    self.data[i][1] = str(round(vals[1], 2)) if vals[1] is not None else ''
                    self.tw_latamp.setItem(i, 0, QTableWidgetItem(self.data[i][0]))
                    self.tw_latamp.setItem(i, 1, QTableWidgetItem(self.data[i][1]))

    def clear_all(self):
        self.data = self._init_data()
        for i in range(len(self.peak_labels)):
            for j in [0, 1]:
                self.tw_latamp.setItem(i, j, QTableWidgetItem(''))

    def request_values(self, key):
        """key: 'p13_L' etc; emite la señal que el main window conecta al gráfico."""
        self.sig_measure_value.emit({f'{self.side_text.lower()}': {key: None}})

    def update_latamp_table(self, latamp_dict):
        """latamp_dict: {'LatAmp': {'p13': [lat,amp], ...}}; actualiza filas."""
        if not isinstance(latamp_dict, dict):
            return
        la = latamp_dict.get('LatAmp', latamp_dict)
        for i, pico in enumerate(self.peak_labels):
            if pico in la:
                self.set_data({pico: la[pico]})
