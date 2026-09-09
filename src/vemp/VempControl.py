"""
Panel de control del equipo VEMP.

Mismo patrón que AbrControl: los parámetros del estímulo y del registro, y
los botones iniciar/pausar/detener que emiten `capture`. Lo propio del VEMP:

- LADO. El VEMP es monoaural: se estimula un oído y se registra el músculo
  de ese lado. El módulo capturaba los dos oídos a la vez con la misma
  intensidad, que no es un examen que exista.
- MANIOBRA del paciente. Es la que decide si hay respuesta: sin ECM
  contraído no hay cVEMP, sin mirada superior no hay oVEMP. Las opciones
  cambian con el subtipo y arrancan SIEMPRE en la posición sin contracción
  -- no es un default "correcto" precargado, es lo que el alumno tiene que
  darse cuenta de que falta (ver VEMP_generator_v1.MANIOBRAS).
- FRECUENCIA del tone burst (500/1000 Hz): la normativa trae las dos y el
  umbral del VEMP se busca en 500, donde la respuesta es más grande.

Sin botón de randomizar el subtipo a propósito: cuál de los tres VEMP
corresponde es la decisión clínica principal del examen, la toma el alumno.
"""

import random

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout,
                               QGroupBox, QHBoxLayout, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from vemp.VEMP_generator_v1 import SUBTIPOS, maniobras_de

# Etiqueta legible de cada subtipo (las mismas de
# CaseBuilder::VEMP_SUBTIPO_LABELS, para que la ficha del docente y el
# equipo del alumno nombren lo mismo).
SUBTIPO_LABELS = {
    'CVEMP': 'cVEMP -- cervical (ECM)',
    'OVEMP': 'oVEMP -- ocular (oblicuo inferior)',
    'MVEMP': 'mVEMP -- masetero',
}

FRECUENCIAS = ['500Hz', '1000Hz']


class VempControl(QWidget):
    capture = Signal(str)          # 'record' | 'pause' | 'stopped'
    sig_subtipo = Signal(str)      # subtipo activo (CVEMP/OVEMP/MVEMP)
    sig_maniobra = Signal(str)     # maniobra del paciente

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEnabled(False)  # gate por la_super(data != None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # --- Prueba -------------------------------------------------------
        caja_prueba = QGroupBox('Prueba')
        form = QFormLayout(caja_prueba)
        self.cb_subtipo = QComboBox()
        for subtipo in SUBTIPOS:
            self.cb_subtipo.addItem(SUBTIPO_LABELS.get(subtipo, subtipo), subtipo)
        form.addRow('VEMP:', self.cb_subtipo)

        self.cb_side = QComboBox()
        self.cb_side.addItems(['OD', 'OI'])
        form.addRow('Oído:', self.cb_side)

        self.cb_maniobra = QComboBox()
        form.addRow('Maniobra:', self.cb_maniobra)
        layout.addWidget(caja_prueba)

        # --- Estímulo -----------------------------------------------------
        caja_estimulo = QGroupBox('Estímulo')
        form = QFormLayout(caja_estimulo)
        self.cb_freq = QComboBox()
        self.cb_freq.addItems(FRECUENCIAS)
        form.addRow('Tone burst:', self.cb_freq)

        self.cb_pol = QComboBox()
        self.cb_pol.addItems(['Rarefacción', 'Condensación', 'Alternante'])
        form.addRow('Polaridad:', self.cb_pol)

        self.sb_int = QSpinBox()
        # Hasta 110 dB SPL: los casos traen umbrales de hasta 95 dB (ver
        # CaseProfile), y con el tope en 100 una respuesta de umbral alto no
        # se podía sacar del piso de ruido en ninguna intensidad.
        self.sb_int.setRange(40, 110)
        self.sb_int.setSingleStep(5)
        self.sb_int.setValue(100)
        self.sb_int.setSuffix(' dB SPL')
        form.addRow('Intensidad:', self.sb_int)

        self.sb_rate = QDoubleSpinBox()
        self.sb_rate.setRange(1.0, 50.0)
        self.sb_rate.setSingleStep(0.5)
        self.sb_rate.setSuffix(' Hz')
        form.addRow('Tasa:', self.sb_rate)
        layout.addWidget(caja_estimulo)

        # --- Registro -----------------------------------------------------
        caja_registro = QGroupBox('Registro')
        form = QFormLayout(caja_registro)
        self.sb_prom = QSpinBox()
        self.sb_prom.setRange(20, 1000)
        self.sb_prom.setSingleStep(10)
        form.addRow('Promediaciones:', self.sb_prom)

        self.sb_filter_down = QDoubleSpinBox()
        self.sb_filter_down.setRange(100, 5000)
        self.sb_filter_down.setSingleStep(50)
        self.sb_filter_down.setValue(1500)
        self.sb_filter_down.setSuffix(' Hz')
        form.addRow('Filtro pasa-bajo:', self.sb_filter_down)

        self.sb_filter_up = QDoubleSpinBox()
        self.sb_filter_up.setRange(0.5, 100)
        self.sb_filter_up.setSingleStep(1)
        self.sb_filter_up.setValue(10)
        self.sb_filter_up.setSuffix(' Hz')
        form.addRow('Filtro pasa-alto:', self.sb_filter_up)
        layout.addWidget(caja_registro)

        # --- Botones ------------------------------------------------------
        fila = QHBoxLayout()
        self.btn_start = QPushButton('Iniciar')
        self.btn_stop = QPushButton('Detener')
        fila.addWidget(self.btn_start)
        fila.addWidget(self.btn_stop)
        layout.addLayout(fila)

        self.randomize_initial_values()
        self.apply_subtipo(self.get_subtipo())

        self.cb_subtipo.currentIndexChanged.connect(self._on_subtipo_changed)
        self.cb_maniobra.currentTextChanged.connect(self.sig_maniobra.emit)
        self.btn_start.clicked.connect(self.start_capture)
        self.btn_stop.clicked.connect(self.stop_capture)

    # =====================================================================
    # Estado inicial
    # =====================================================================

    def randomize_initial_values(self):
        """Tasa y promediaciones sin default "correcto" precargado.

        Mismo criterio que AbrControl.randomize_initial_values: son los
        controles que el alumno tiene que aprender a leer y ajustar. Se
        randomiza en un rango realista (el VEMP se registra entre 3 y 20 Hz
        y con 100-300 barridos) para que nunca arranque en 0 -- con
        promediaciones 0 el generador queda en puro ruido para siempre.
        """
        self.sb_prom.setValue(random.randrange(60, 601, 10))
        self.sb_rate.setValue(round(random.uniform(3.1, 20.1), 1))

    def apply_subtipo(self, subtipo):
        """Las maniobras posibles dependen del músculo que se registra."""
        opciones = maniobras_de(subtipo)
        actual = self.cb_maniobra.currentText()
        self.cb_maniobra.blockSignals(True)
        self.cb_maniobra.clear()
        self.cb_maniobra.addItems(opciones)
        # Si la maniobra elegida existe también en el subtipo nuevo se
        # respeta; si no, vuelve a la primera (sin contracción).
        if actual in opciones:
            self.cb_maniobra.setCurrentText(actual)
        self.cb_maniobra.blockSignals(False)
        self.sig_maniobra.emit(self.cb_maniobra.currentText())

    def _on_subtipo_changed(self, *_):
        subtipo = self.get_subtipo()
        self.apply_subtipo(subtipo)
        self.sig_subtipo.emit(subtipo)

    # =====================================================================
    # API
    # =====================================================================

    def get_subtipo(self):
        return self.cb_subtipo.currentData() or 'CVEMP'

    def get_side(self):
        return self.cb_side.currentText()

    def get_maniobra(self):
        return self.cb_maniobra.currentText()

    def get_data(self):
        return {
            'subtipo': self.get_subtipo(),
            'side': self.cb_side.currentText(),
            'maniobra': self.cb_maniobra.currentText(),
            'freq': self.cb_freq.currentText(),
            'pol': self.cb_pol.currentText(),
            'int': self.sb_int.value(),
            'rate': self.sb_rate.value(),
            'average': self.sb_prom.value(),
            'filter_down': self.sb_filter_down.value(),
            'filter_passhigh': self.sb_filter_up.value(),
        }

    def disabled_all(self, value=True):
        """Congela los parámetros del registro mientras se promedia.

        La maniobra NO se congela a propósito: el paciente se relaja o
        corrige la contracción EN PLENA promediación, y ver caerse la
        respuesta cuando eso pasa es justamente lo que hay que aprender.
        """
        for widget in (self.cb_subtipo, self.cb_side, self.cb_freq, self.cb_pol,
                       self.sb_int, self.sb_rate, self.sb_prom,
                       self.sb_filter_down, self.sb_filter_up):
            widget.setDisabled(value)

    # =====================================================================
    # Captura
    # =====================================================================

    def start_capture(self):
        self.btn_start.setText('Pausar')
        self.btn_start.clicked.disconnect()
        self.btn_start.clicked.connect(self.pause_capture)
        self.disabled_all(True)
        self.capture.emit('record')

    def pause_capture(self):
        self.btn_start.setText('Continuar')
        self.btn_start.clicked.disconnect()
        self.btn_start.clicked.connect(self.start_capture)
        self.capture.emit('pause')

    def stop_capture(self):
        self.btn_start.setText('Iniciar')
        try:
            self.btn_start.clicked.disconnect()
        except RuntimeError:
            pass
        self.btn_start.clicked.connect(self.start_capture)
        self.disabled_all(False)
        self.capture.emit('stopped')
