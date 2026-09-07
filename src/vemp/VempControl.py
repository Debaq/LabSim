"""
Panel de control del equipo VEMP.

Replica el patrón de AbrControl: combo subtipo (CVEMP/OVEMP/MVEMP), spinboxes
de intensidad/rate/promediaciones/filtros, botones start/stop. Sin botón
"Randomize initial values" porque el alumno SIEMPRE debe elegir el subtipo
explícitamente (no es un valor "neutral" que se pueda randomizar -- es la
decisión clínica principal del examen).
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton


SUBTIPOS = ['CVEMP', 'OVEMP', 'MVEMP']


class VempControl(QWidget):
    capture = Signal(str)  # 'record' | 'pause' | 'stopped'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEnabled(False)  # gate por la_super(data != None)

        layout = QVBoxLayout(self)

        # Subtipo
        row = QHBoxLayout()
        row.addWidget(QLabel('Subtipo:'))
        self.cb_subtipo = QComboBox()
        self.cb_subtipo.addItems(SUBTIPOS)
        self.cb_subtipo.setCurrentText('CVEMP')
        row.addWidget(self.cb_subtipo)
        layout.addLayout(row)

        # Polaridad (casi siempre rarefacción; dejamos opción igual que ABR)
        row = QHBoxLayout()
        row.addWidget(QLabel('Polaridad:'))
        self.cb_pol = QComboBox()
        self.cb_pol.addItems(['Rarefacción', 'Condensación', 'Alternante'])
        row.addWidget(self.cb_pol)
        layout.addLayout(row)

        # Intensidad (dB SPL)
        row = QHBoxLayout()
        row.addWidget(QLabel('Intensidad (dB):'))
        self.sb_int = QSpinBox()
        self.sb_int.setRange(0, 100)
        self.sb_int.setValue(80)
        row.addWidget(self.sb_int)
        layout.addLayout(row)

        # Tasa de estímulo (Hz)
        row = QHBoxLayout()
        row.addWidget(QLabel('Tasa (Hz):'))
        self.sb_rate = QDoubleSpinBox()
        self.sb_rate.setRange(1.0, 50.0)
        self.sb_rate.setSingleStep(0.5)
        self.sb_rate.setValue(5.0)
        row.addWidget(self.sb_rate)
        layout.addLayout(row)

        # Promediaciones
        row = QHBoxLayout()
        row.addWidget(QLabel('Promediaciones:'))
        self.sb_prom = QSpinBox()
        self.sb_prom.setRange(50, 1000)
        self.sb_prom.setSingleStep(50)
        self.sb_prom.setValue(200)
        row.addWidget(self.sb_prom)
        layout.addLayout(row)

        # Filtros (pasa-bajo / pasa-alto)
        row = QHBoxLayout()
        row.addWidget(QLabel('Filtro pasa-bajo (Hz):'))
        self.sb_filter_down = QDoubleSpinBox()
        self.sb_filter_down.setRange(100, 5000)
        self.sb_filter_down.setValue(1500)
        row.addWidget(self.sb_filter_down)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel('Filtro pasa-alto (Hz):'))
        self.sb_filter_up = QDoubleSpinBox()
        self.sb_filter_up.setRange(0.5, 100)
        self.sb_filter_up.setValue(10)
        row.addWidget(self.sb_filter_up)
        layout.addLayout(row)

        # Botones start/stop
        row = QHBoxLayout()
        self.btn_start = QPushButton('Iniciar')
        self.btn_stop = QPushButton('Detener')
        self.btn_stop.setEnabled(False)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        layout.addLayout(row)

        self.btn_start.clicked.connect(lambda: self._emit_state('record'))
        self.btn_stop.clicked.connect(lambda: self._emit_state('stopped'))

    def _emit_state(self, state):
        if state == 'record':
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        elif state == 'stopped':
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
        self.capture.emit(state)

    def get_data(self):
        return {
            'subtipo': self.cb_subtipo.currentText(),
            'pol': self.cb_pol.currentText(),
            'int': self.sb_int.value(),
            'rate': self.sb_rate.value(),
            'average': self.sb_prom.value(),
            'filter_down': self.sb_filter_down.value(),
            'filter_passhigh': self.sb_filter_up.value(),
        }

    def get_subtipo(self):
        return self.cb_subtipo.currentText()
