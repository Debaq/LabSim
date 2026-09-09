"""Diálogo de Parámetros Avanzados del equipo de potenciales evocados.

Reemplaza a UI/AbrAdvanceSettings_ui.py, que dibujaba estos campos pero no
los leía nadie: el generador quedaba fijo en fono de inserción, impedancia
3 kOhm y ventana de 12 ms pasara lo que pasara en este diálogo.

Se arma a mano (no desde .ui) porque el contenido depende del protocolo
activo: la ventana de un ECochG y la de un P300 no se parecen en nada, y
los rangos salen de abr/protocols.py. get_data() devuelve directamente el
`technical_config` que consume ABR_generator.generate_curve.

Lo que el alumno puede romper acá es a propósito, y el diálogo NO se lo
avisa: ni mensajes, ni valores en rojo, ni notas de qué conviene usar. Lo
tiene que reconocer en el trazo y corregirlo, que es el ejercicio.
- Electrodo activo o las dos referencias desconectadas: no hay registro.
- Sin tierra: entra la red eléctrica (50 Hz).
- Impedancia alta: ruido de fondo. Desbalanceada: zumbido de 50 Hz.
- Rechazo de artefacto muy estrecho: el promedio no avanza.
- Rechazo apagado: entra basura al promedio.
"""
# pylint: disable=no-name-in-module
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QGridLayout, QGroupBox, QLabel,
                               QVBoxLayout)

from abr.ABR_generator import DISCONNECTED
from abr.ABR_generator import default_settings as _generator_defaults
from abr.protocols import get_protocol

tr = QCoreApplication.translate


# Rótulo visible -> clave que entiende el generador.
TRANSDUCERS = {
    "Fono de inserción": 'insert_earphone',
    "Fono de copa (TDH-39)": 'TDH39_headphone',
    "Vibrador óseo": 'bone_vibrator',
}

MONTAGES = {
    "Cz - mastoides": 'vertex_mastoid',
    "Fz - mastoides": 'forehead_mastoid',
    "Cz - lóbulo": 'vertex_earlobe',
    "Timpánico (ECochG)": 'tympanic',
}

# Posiciones de electrodo. La ultima sale del generador para que
# "desconectado" signifique lo mismo de los dos lados.
POSITIONS = ("A1", "A2", "Cz", "Fz", "Fpz", "Ceja izquierda", DISCONNECTED)

ARTIFACT_REJECT = {
    "±10 µV": 10.0,
    "±15 µV": 15.0,
    "±20 µV": 20.0,
    "±25 µV": 25.0,
    "±40 µV": 40.0,
    "Desactivado": 0.0,
}

RESIDUAL_NOISE = {f"{nv} nV": float(nv) for nv in (40, 60, 80, 100, 120)}

# Criterio de detección: el equipo declara "respuesta presente" cuando el
# FSP supera este valor. Los porcentajes son la confianza asociada.
FSP_CRITERIA = {
    "Deshabilitado": 0.0,
    "Detección 95% (FSP 2.0)": 2.0,
    "Detección 97% (FSP 2.5)": 2.5,
    "Detección 99% (FSP 3.1)": 3.1,
    "Detección 99.5% (FSP 3.5)": 3.5,
    "Detección 99.9% (FSP 4.0)": 4.0,
}

ELECTRODES = (
    ('vertex', "Electrodo activo (vértex)", "Cz"),
    ('right', "Referencia derecha", "A2"),
    ('left', "Referencia izquierda", "A1"),
    ('ground', "Tierra", "Fpz"),
)


def default_settings(test: str = 'ABR') -> dict:
    """technical_config de rutina para el protocolo pedido.

    La tabla vive en el generador (ABR_generator.default_settings) porque
    ahi la necesita ABR_Curve cuando nadie abrio este dialogo todavia; acá
    solo se reexporta para que la UI no dependa del orden de imports.
    """
    return _generator_defaults(test)


def _combo(mapping, current):
    """Combo de rótulo->valor, posicionado en `current`."""
    box = QComboBox()
    for label, value in mapping.items():
        box.addItem(label, value)
    idx = box.findData(current)
    box.setCurrentIndex(idx if idx >= 0 else 0)
    return box


class AbrAdvanceSettings(QDialog):
    """Parámetros del equipo, no del paciente. Modal, con Aceptar/Cancelar."""

    def __init__(self, settings=None, test='ABR', parent=None):
        super().__init__(parent)
        self.test = test
        self.protocol = get_protocol(test)
        self.setWindowTitle(f"Parámetros avanzados — {self.protocol.name}")
        self._build(settings or default_settings(test))

    # ------------------------------------------------------------------ UI
    def _build(self, settings):
        layout = QVBoxLayout(self)

        registro = QGroupBox("Registro")
        grid = QGridLayout(registro)
        self.cb_transducer = _combo(TRANSDUCERS, settings.get('transducer'))
        self.cb_montage = _combo(MONTAGES, settings.get('montage'))
        self.sb_window = QDoubleSpinBox()
        lo, hi = self.protocol.window_range
        self.sb_window.setRange(lo, hi)
        self.sb_window.setDecimals(1)
        self.sb_window.setSuffix(" ms")
        self.sb_window.setValue(float(settings.get('window_ms', self.protocol.window_ms)))
        grid.addWidget(QLabel("Transductor"), 0, 0)
        grid.addWidget(self.cb_transducer, 0, 1)
        grid.addWidget(QLabel("Montaje"), 1, 0)
        grid.addWidget(self.cb_montage, 1, 1)
        grid.addWidget(QLabel("Ventana"), 2, 0)
        grid.addWidget(self.sb_window, 2, 1)
        layout.addWidget(registro)

        electrodos = QGroupBox("Electrodos (posición e impedancia)")
        grid = QGridLayout(electrodos)
        self.electrode_widgets = {}
        posiciones = settings.get('electrodes') or {}
        impedancias = settings.get('impedance')
        if not isinstance(impedancias, dict):
            impedancias = {}
        for row, (key, label, default) in enumerate(ELECTRODES):
            combo = QComboBox()
            combo.addItems(POSITIONS)
            actual = posiciones.get(key, default)
            idx = combo.findText(actual)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            spin = QDoubleSpinBox()
            spin.setRange(0.5, 20.0)
            spin.setSingleStep(0.5)
            spin.setDecimals(1)
            spin.setSuffix(" kΩ")
            spin.setValue(float(impedancias.get(key, 2.0)))
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(combo, row, 1)
            grid.addWidget(spin, row, 2)
            self.electrode_widgets[key] = (combo, spin)
        layout.addWidget(electrodos)

        promedio = QGroupBox("Promediación")
        grid = QGridLayout(promedio)
        self.cb_reject = _combo(ARTIFACT_REJECT, settings.get('artifact_reject_uv'))
        self.cb_noise = _combo(RESIDUAL_NOISE, settings.get('residual_noise_nv'))
        self.cb_fsp = _combo(FSP_CRITERIA, settings.get('fsp_criterion'))
        grid.addWidget(QLabel("Rechazo de artefacto"), 0, 0)
        grid.addWidget(self.cb_reject, 0, 1)
        grid.addWidget(QLabel("Ruido residual objetivo"), 1, 0)
        grid.addWidget(self.cb_noise, 1, 1)
        grid.addWidget(QLabel("Criterio de detección"), 2, 0)
        grid.addWidget(self.cb_fsp, 2, 1)
        layout.addWidget(promedio)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel
                                   | QDialogButtonBox.StandardButton.RestoreDefaults)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        botones.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self.restore_defaults)
        layout.addWidget(botones)

    # --------------------------------------------------------------- datos
    def restore_defaults(self):
        """Vuelve a lo de rutina para este protocolo."""
        self.set_data(default_settings(self.test))

    def get_data(self) -> dict:
        """technical_config listo para ABR_generator.generate_curve."""
        electrodes, impedance = {}, {}
        for key, (combo, spin) in self.electrode_widgets.items():
            electrodes[key] = combo.currentText()
            impedance[key] = float(spin.value())
        return {
            'transducer': self.cb_transducer.currentData(),
            'montage': self.cb_montage.currentData(),
            'window_ms': float(self.sb_window.value()),
            'electrodes': electrodes,
            'impedance': impedance,
            # 0 = rechazo desactivado; el generador lo trata como "sin rechazo".
            'artifact_reject_uv': float(self.cb_reject.currentData()) or 0.0,
            'residual_noise_nv': float(self.cb_noise.currentData()),
            'fsp_criterion': float(self.cb_fsp.currentData()) or None,
        }

    def set_data(self, settings: dict) -> None:
        for combo, key in ((self.cb_transducer, 'transducer'),
                           (self.cb_montage, 'montage'),
                           (self.cb_reject, 'artifact_reject_uv'),
                           (self.cb_noise, 'residual_noise_nv'),
                           (self.cb_fsp, 'fsp_criterion')):
            valor = settings.get(key)
            idx = combo.findData(valor if valor is not None else 0.0)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        if 'window_ms' in settings:
            self.sb_window.setValue(float(settings['window_ms']))
        posiciones = settings.get('electrodes') or {}
        impedancias = settings.get('impedance')
        if not isinstance(impedancias, dict):
            impedancias = {}
        for key, (combo, spin) in self.electrode_widgets.items():
            if key in posiciones:
                idx = combo.findText(posiciones[key])
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            if key in impedancias:
                spin.setValue(float(impedancias[key]))
