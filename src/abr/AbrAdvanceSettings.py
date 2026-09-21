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
                               QTabWidget, QVBoxLayout, QWidget)

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

# Los tres primeros son montajes de superficie (el ABR y los corticales); los
# tres últimos son los del ECochG, y no son "otra posición de electrodo" sino
# otra distancia a la cóclea: cuanto más cerca, más grande la respuesta y más
# bajo el límite de la razón PS/PA (ver abr/ecochg.py). Elegir ECochG deja el
# equipo en el timpánico, que es el de rutina; las otras dos posiciones se
# eligen acá.
MONTAGES = {
    "Cz - mastoides": 'vertex_mastoid',
    "Fz - mastoides": 'forehead_mastoid',
    "Cz - lóbulo": 'vertex_earlobe',
    "Conducto / TipTrode (ECochG)": 'extratympanic',
    "Timpánico (ECochG)": 'tympanic',
    "Transtimpánico / promontorio (ECochG)": 'transtympanic',
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

# ---------------------------------------------------------------------
# Parámetros que el equipo real tiene y el modelo todavía NO usa.
#
# Estaban faltando y los alumnos los buscaban --el 2-1-2 del tone burst es
# el ejemplo que se repite--. Se dibujan y viajan en el technical_config,
# pero el generador todavía no los lee (ver UNCONNECTED_SETTINGS en el
# generador). En pantalla NO se distinguen de los demás: es un equipo
# simulado, y un equipo no le avisa al operador cuáles de sus perillas
# están implementadas.
# ---------------------------------------------------------------------

# Duración del click. 100 µs es el de rutina; los otros existen y cambian
# el espectro (más corto = más agudo, más largo = más grave).
CLICK_US = {"50 µs": 50.0, "100 µs": 100.0, "200 µs": 200.0, "500 µs": 500.0}

# Envolvente del tone burst en CICLOS de la frecuencia del tono:
# subida - meseta - bajada. El 2-1-2 es el de rutina para umbrales por
# frecuencia; sin meseta (2-0-2) el estímulo es más corto y sincroniza
# mejor, con meseta larga es más específico en frecuencia y peor
# sincronizado.
BURST_ENVELOPES = {
    "2-1-2 ciclos": '2-1-2',
    "2-0-2 ciclos": '2-0-2',
    "1-0-1 ciclos": '1-0-1',
    "2-2-2 ciclos": '2-2-2',
    "5-0-5 ciclos": '5-0-5',
    "1 ms - 1 ms - 1 ms": 'ms-1-1-1',
}

# Forma de la rampa de subida y bajada.
BURST_WINDOWS = {
    "Blackman": 'blackman',
    "Hanning": 'hanning',
    "Gaussiana": 'gauss',
    "Lineal (trapezoidal)": 'linear',
}

# Unidad en la que el equipo muestra el nivel.
LEVEL_UNITS = {"dB nHL": 'nHL', "dB peSPL": 'peSPL', "dB HL": 'HL',
               "dB SL": 'SL'}

# Aleatorización del intervalo entre estímulos: rompe la periodicidad para
# que el artefacto del transductor no se sume en fase con la respuesta.
RATE_JITTER = {"Sin jitter": 0.0, "± 5 %": 5.0, "± 10 %": 10.0, "± 20 %": 20.0}

PRESENTATION = {
    "Monoaural": 'monaural',
    "Binaural": 'binaural',
    "Alternando oídos": 'alternating',
}

MASKING_NOISE = {
    "Ruido blanco": 'white',
    "Banda estrecha": 'narrow',
    "Ruido de habla": 'speech',
}

CHANNELS = {"1 canal (ipsi)": 1, "2 canales (ipsi + contra)": 2}

GAINS = {"×10.000": 10000.0, "×50.000": 50000.0, "×100.000": 100000.0,
         "×150.000": 150000.0}

# Filtro de red. En Chile la red es de 50 Hz; el de 60 está porque los
# equipos lo traen y porque el mismo caso se puede correr en otro país.
NOTCH = {"Desactivado": 0.0, "50 Hz": 50.0, "60 Hz": 60.0}

FILTER_SLOPES = {"6 dB/oct": 6.0, "12 dB/oct": 12.0, "24 dB/oct": 24.0,
                 "48 dB/oct": 48.0}

SAMPLE_RATES = {"20 kHz": 20000.0, "30 kHz": 30000.0, "44,1 kHz": 44100.0,
                "48 kHz": 48000.0}

WEIGHTED_AVERAGING = {"Promedio simple": False, "Promedio ponderado por ruido": True}

# Qué hace el equipo cuando se cumple el criterio.
AUTO_STOP = {
    "Al cruzar el FSP o llegar al ruido objetivo": 'ambos',
    "Solo al cruzar el FSP": 'fsp',
    "Solo al llegar al ruido objetivo": 'ruido',
    "No parar solo": 'no',
}

SMOOTHING = {"Sin suavizado": 0.0, "3 puntos": 3.0, "5 puntos": 5.0,
             "7 puntos": 7.0}


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
        tabs = QTabWidget()
        tabs.addTab(self._tab_estimulo(settings), "Estímulo")
        tabs.addTab(self._tab_registro(settings), "Registro")
        tabs.addTab(self._tab_promediacion(settings), "Promediación")
        layout.addWidget(tabs)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel
                                   | QDialogButtonBox.StandardButton.RestoreDefaults)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        botones.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self.restore_defaults)
        layout.addWidget(botones)

    @staticmethod
    def _fila(grid, row, texto, widget, pendiente=False):
        """Una fila etiqueta/control.

        `pendiente` marca los que el modelo todavía no lee (ver
        UNCONNECTED_SETTINGS en el generador), pero NO se nota en pantalla:
        es un equipo simulado y un equipo no avisa cuáles de sus perillas
        están implementadas. El alumno ve el mismo panel que en el equipo
        real; qué mueve el trazo y qué no es parte de lo que descubre.
        """
        grid.addWidget(QLabel(texto), row, 0)
        grid.addWidget(widget, row, 1)

    def _tab_estimulo(self, settings):
        caja = QGroupBox()
        grid = QGridLayout(caja)
        self.cb_click_us = _combo(CLICK_US, settings.get('click_us'))
        self.cb_burst_env = _combo(BURST_ENVELOPES, settings.get('burst_envelope'))
        self.cb_burst_win = _combo(BURST_WINDOWS, settings.get('burst_window'))
        self.cb_level_unit = _combo(LEVEL_UNITS, settings.get('level_unit'))
        self.cb_jitter = _combo(RATE_JITTER, settings.get('rate_jitter_pct'))
        self.cb_presentation = _combo(PRESENTATION, settings.get('presentation'))
        self.cb_masking_noise = _combo(MASKING_NOISE, settings.get('masking_noise'))
        self.sb_masking_offset = QDoubleSpinBox()
        self.sb_masking_offset.setRange(-40.0, 40.0)
        self.sb_masking_offset.setDecimals(0)
        self.sb_masking_offset.setSuffix(" dB")
        self.sb_masking_offset.setValue(float(settings.get('masking_offset_db') or 0.0))
        filas = (
            ("Duración del click", self.cb_click_us),
            ("Envolvente del tone burst", self.cb_burst_env),
            ("Ventana del tone burst", self.cb_burst_win),
            ("Unidad de nivel", self.cb_level_unit),
            ("Jitter de la tasa", self.cb_jitter),
            ("Presentación", self.cb_presentation),
            ("Ruido de enmascaramiento", self.cb_masking_noise),
            ("Offset del enmascaramiento", self.sb_masking_offset),
        )
        for row, (texto, widget) in enumerate(filas):
            self._fila(grid, row, texto, widget, pendiente=True)
        return caja

    def _tab_registro(self, settings):
        caja = QGroupBox()
        grid = QGridLayout(caja)
        self.cb_transducer = _combo(TRANSDUCERS, settings.get('transducer'))
        self.cb_montage = _combo(MONTAGES, settings.get('montage'))
        self.sb_window = QDoubleSpinBox()
        lo, hi = self.protocol.window_range
        self.sb_window.setRange(lo, hi)
        self.sb_window.setDecimals(1)
        self.sb_window.setSuffix(" ms")
        self.sb_window.setValue(float(settings.get('window_ms', self.protocol.window_ms)))
        self._fila(grid, 0, "Transductor", self.cb_transducer)
        self._fila(grid, 1, "Montaje", self.cb_montage)
        self._fila(grid, 2, "Ventana", self.sb_window)

        self.cb_channels = _combo(CHANNELS, settings.get('channels'))
        self.cb_gain = _combo(GAINS, settings.get('gain'))
        self.cb_notch = _combo(NOTCH, settings.get('notch_hz'))
        self.cb_slope = _combo(FILTER_SLOPES, settings.get('filter_slope'))
        self.cb_sample_rate = _combo(SAMPLE_RATES, settings.get('sample_rate_hz'))
        for row, (texto, widget) in enumerate((
                ("Canales", self.cb_channels),
                ("Ganancia del amplificador", self.cb_gain),
                ("Filtro de red (notch)", self.cb_notch),
                ("Pendiente del filtro", self.cb_slope),
                ("Frecuencia de muestreo", self.cb_sample_rate)), start=3):
            self._fila(grid, row, texto, widget, pendiente=True)

        electrodos = QGroupBox("Electrodos (posición e impedancia)")
        egrid = QGridLayout(electrodos)
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
            egrid.addWidget(QLabel(label), row, 0)
            egrid.addWidget(combo, row, 1)
            egrid.addWidget(spin, row, 2)
            self.electrode_widgets[key] = (combo, spin)

        envoltorio = QWidget()
        vbox = QVBoxLayout(envoltorio)
        vbox.addWidget(caja)
        vbox.addWidget(electrodos)
        vbox.addStretch(1)
        return envoltorio

    def _tab_promediacion(self, settings):
        caja = QGroupBox()
        grid = QGridLayout(caja)
        self.cb_reject = _combo(ARTIFACT_REJECT, settings.get('artifact_reject_uv'))
        self.cb_noise = _combo(RESIDUAL_NOISE, settings.get('residual_noise_nv'))
        self.cb_fsp = _combo(FSP_CRITERIA, settings.get('fsp_criterion'))
        self._fila(grid, 0, "Rechazo de artefacto", self.cb_reject)
        self._fila(grid, 1, "Ruido residual objetivo", self.cb_noise)
        self._fila(grid, 2, "Criterio de detección", self.cb_fsp)

        self.cb_weighted = _combo(WEIGHTED_AVERAGING, settings.get('weighted_averaging'))
        self.cb_auto_stop = _combo(AUTO_STOP, settings.get('auto_stop'))
        self.sb_fsp_window = QDoubleSpinBox()
        self.sb_fsp_window.setRange(0.0, 50.0)
        self.sb_fsp_window.setDecimals(1)
        self.sb_fsp_window.setSuffix(" ms")
        self.sb_fsp_window.setSpecialValueText("Automática (por edad)")
        self.sb_fsp_window.setValue(float(settings.get('fsp_window_ms') or 0.0))
        self.cb_smoothing = _combo(SMOOTHING, settings.get('smoothing'))
        for row, (texto, widget) in enumerate((
                ("Tipo de promediación", self.cb_weighted),
                ("Parada automática", self.cb_auto_stop),
                ("Ventana de análisis del FSP", self.sb_fsp_window),
                ("Suavizado del trazo", self.cb_smoothing)), start=3):
            self._fila(grid, row, texto, widget, pendiente=True)
        return caja

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
            # Sin efecto todavía, pero viajan en el technical_config con la
            # clave con la que se van a leer: conectar uno es leerlo en el
            # generador y sacarlo de UNCONNECTED_SETTINGS.
            'click_us': float(self.cb_click_us.currentData()),
            'burst_envelope': self.cb_burst_env.currentData(),
            'burst_window': self.cb_burst_win.currentData(),
            'level_unit': self.cb_level_unit.currentData(),
            'rate_jitter_pct': float(self.cb_jitter.currentData()),
            'presentation': self.cb_presentation.currentData(),
            'masking_noise': self.cb_masking_noise.currentData(),
            'masking_offset_db': float(self.sb_masking_offset.value()),
            'channels': int(self.cb_channels.currentData()),
            'gain': float(self.cb_gain.currentData()),
            'notch_hz': float(self.cb_notch.currentData()),
            'filter_slope': float(self.cb_slope.currentData()),
            'sample_rate_hz': float(self.cb_sample_rate.currentData()),
            'weighted_averaging': bool(self.cb_weighted.currentData()),
            'auto_stop': self.cb_auto_stop.currentData(),
            # 0 = automática (la ventana por edad que usa el generador).
            'fsp_window_ms': float(self.sb_fsp_window.value()) or None,
            'smoothing': float(self.cb_smoothing.currentData()),
        }

    def set_data(self, settings: dict) -> None:
        for combo, key in ((self.cb_transducer, 'transducer'),
                           (self.cb_montage, 'montage'),
                           (self.cb_reject, 'artifact_reject_uv'),
                           (self.cb_noise, 'residual_noise_nv'),
                           (self.cb_fsp, 'fsp_criterion'),
                           (self.cb_click_us, 'click_us'),
                           (self.cb_burst_env, 'burst_envelope'),
                           (self.cb_burst_win, 'burst_window'),
                           (self.cb_level_unit, 'level_unit'),
                           (self.cb_jitter, 'rate_jitter_pct'),
                           (self.cb_presentation, 'presentation'),
                           (self.cb_masking_noise, 'masking_noise'),
                           (self.cb_channels, 'channels'),
                           (self.cb_gain, 'gain'),
                           (self.cb_notch, 'notch_hz'),
                           (self.cb_slope, 'filter_slope'),
                           (self.cb_sample_rate, 'sample_rate_hz'),
                           (self.cb_weighted, 'weighted_averaging'),
                           (self.cb_auto_stop, 'auto_stop'),
                           (self.cb_smoothing, 'smoothing')):
            valor = settings.get(key)
            idx = combo.findData(valor if valor is not None else 0.0)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        if 'window_ms' in settings:
            self.sb_window.setValue(float(settings['window_ms']))
        if 'masking_offset_db' in settings:
            self.sb_masking_offset.setValue(float(settings['masking_offset_db'] or 0.0))
        if 'fsp_window_ms' in settings:
            self.sb_fsp_window.setValue(float(settings['fsp_window_ms'] or 0.0))
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
