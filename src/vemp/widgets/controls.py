"""
Panel de control del equipo de VEMP.

Tres bloques, en el orden en que se decide un VEMP: qué prueba (qué músculo
y con qué maniobra), qué estímulo (por dónde entra, a qué frecuencia y a
cuánto) y cómo se registra (barridos, rechazo, filtros).

Dos decisiones que se ven acá:

- La MANIOBRA arranca siempre en la posición sin contracción y no se congela
  mientras se promedia. El paciente se afloja EN PLENO registro y ver la
  respuesta caerse con él --y el EMG del medidor bajando-- es parte de lo
  que hay que aprender.
- Tasa, barridos y rechazo arrancan RANDOMIZADOS en un rango realista, no en
  el valor "correcto". Son los controles que el alumno tiene que aprender a
  leer; precargados en el valor bueno no se aprenden nunca.

El SUBTIPO tampoco se preselecciona desde el caso: cuál de los tres VEMP
corresponde es la decisión clínica del examen y la toma el alumno (el caso
trae los tres armados justamente para que pueda elegir mal).
"""

import random

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QDoubleSpinBox,
                               QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout,
                               QWidget)

from vemp import protocol, theme
from vemp.engine import Ajustes
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta


class PanelControl(QWidget):
    sig_registrar = Signal()
    sig_pausar = Signal()
    sig_detener = Signal()
    sig_subtipo = Signal(str)
    sig_lado = Signal(str)
    sig_maniobra = Signal(str)
    sig_condicion = Signal()      # cambió algo que define una curva nueva

    def __init__(self, parent=None):
        super().__init__(parent)
        self.registrando = False

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(10)

        raiz.addWidget(self._caja_prueba())
        raiz.addWidget(self._caja_estimulo())
        raiz.addWidget(self._caja_registro())
        raiz.addWidget(self._caja_botones())
        raiz.addStretch(1)

        self._randomizar()
        self._aplicar_subtipo(self.subtipo())
        self._aplicar_transductor()
        self._conectar()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _caja_prueba(self):
        caja = Tarjeta('Prueba')
        campos = Campos()

        self.cb_subtipo = QComboBox()
        for subtipo in protocol.SUBTIPOS:
            self.cb_subtipo.addItem(protocol.SUBTIPO_LABEL[subtipo], subtipo)
        campos.agregar('VEMP', self.cb_subtipo)

        fila = QWidget()
        lay = QHBoxLayout(fila)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.grupo_lado = QButtonGroup(self)
        self.btn_od = QPushButton('OD')
        self.btn_oi = QPushButton('OI')
        for i, btn in enumerate((self.btn_od, self.btn_oi)):
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.grupo_lado.addButton(btn, i)
            lay.addWidget(btn)
        self.btn_od.setChecked(True)
        campos.agregar('Oído estimulado', fila)

        self.cb_maniobra = QComboBox()
        campos.agregar('Maniobra', self.cb_maniobra)
        caja.agregar(campos)

        self.lbl_montaje = etiqueta('', rol='hint')
        self.lbl_montaje.setWordWrap(True)
        caja.agregar(self.lbl_montaje)
        return caja

    def _caja_estimulo(self):
        caja = Tarjeta('Estímulo')
        campos = Campos()

        self.cb_transductor = QComboBox()
        self.cb_transductor.addItems(protocol.TRANSDUCTORES)
        campos.agregar('Transductor', self.cb_transductor)

        self.cb_freq = QComboBox()
        self.cb_freq.addItems(protocol.FRECUENCIAS)
        campos.agregar('Tone burst', self.cb_freq)

        self.cb_pol = QComboBox()
        self.cb_pol.addItems(protocol.POLARIDADES)
        campos.agregar('Polaridad', self.cb_pol)

        self.sb_int = QSpinBox()
        self.sb_int.setSingleStep(protocol.PASO_INTENSIDAD)
        self.sb_int.setSuffix(' dB')
        campos.agregar('Intensidad', self.sb_int)

        self.sb_tasa = QDoubleSpinBox()
        self.sb_tasa.setRange(*protocol.TASA_HZ)
        self.sb_tasa.setSingleStep(0.5)
        self.sb_tasa.setSuffix(' /s')
        campos.agregar('Tasa', self.sb_tasa)

        caja.agregar(campos)
        self.lbl_unidad_int = etiqueta('', rol='hint')
        caja.agregar(self.lbl_unidad_int)
        return caja

    def _caja_registro(self):
        caja = Tarjeta('Registro')
        campos = Campos()

        self.sb_promedios = QSpinBox()
        self.sb_promedios.setRange(*protocol.PROMEDIOS)
        self.sb_promedios.setSingleStep(10)
        campos.agregar('Barridos', self.sb_promedios)

        self.sb_rechazo = QDoubleSpinBox()
        self.sb_rechazo.setRange(*protocol.RECHAZO)
        self.sb_rechazo.setSingleStep(0.5)
        self.sb_rechazo.setDecimals(1)
        campos.agregar('Rechazo artefactos', self.sb_rechazo)

        self.sb_filtro_alto = QDoubleSpinBox()
        self.sb_filtro_alto.setRange(*protocol.FILTRO_PASA_ALTO)
        self.sb_filtro_alto.setSingleStep(1.0)
        self.sb_filtro_alto.setSuffix(' Hz')
        campos.agregar('Pasa-alto', self.sb_filtro_alto)

        self.sb_filtro_bajo = QDoubleSpinBox()
        self.sb_filtro_bajo.setRange(*protocol.FILTRO_PASA_BAJO)
        self.sb_filtro_bajo.setSingleStep(50.0)
        self.sb_filtro_bajo.setSuffix(' Hz')
        campos.agregar('Pasa-bajo', self.sb_filtro_bajo)

        caja.agregar(campos)
        self.lbl_duracion = etiqueta('', rol='hint')
        caja.agregar(self.lbl_duracion)
        return caja

    def _caja_botones(self):
        caja = Tarjeta(plano=True)
        caja.cuerpo.setContentsMargins(10, 10, 10, 10)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.btn_registrar = QPushButton('Registrar')
        self.btn_registrar.setObjectName('btnRegistrar')
        self.btn_registrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detener = QPushButton('Detener')
        self.btn_detener.setObjectName('btnDetener')
        self.btn_detener.setEnabled(False)
        fila.addWidget(self.btn_registrar, 2)
        fila.addWidget(self.btn_detener, 1)
        caja.agregar_layout(fila)
        return caja

    def _conectar(self):
        self.cb_subtipo.currentIndexChanged.connect(self._on_subtipo)
        self.grupo_lado.idClicked.connect(self._on_lado)
        self.cb_maniobra.currentTextChanged.connect(self.sig_maniobra.emit)
        self.cb_transductor.currentTextChanged.connect(self._on_transductor)
        self.cb_freq.currentTextChanged.connect(lambda *_: self.sig_condicion.emit())
        self.sb_promedios.valueChanged.connect(lambda *_: self._refrescar_duracion())
        self.sb_tasa.valueChanged.connect(lambda *_: self._refrescar_duracion())
        self.btn_registrar.clicked.connect(self._on_registrar)
        self.btn_detener.clicked.connect(self._on_detener)

    # ------------------------------------------------------------------
    # Estado inicial
    # ------------------------------------------------------------------

    def _randomizar(self):
        """Sin defaults "correctos" en lo que hay que aprender a ajustar.

        Los rangos son los de un registro posible, no los del control: con
        barridos en el mínimo del rango el examen no cerraría nunca, y con
        la tasa en 20 el alumno arrancaría con la respuesta ya achicada sin
        haber tocado nada.
        """
        self.sb_promedios.setValue(random.randrange(80, 401, 10))
        self.sb_tasa.setValue(round(random.uniform(3.1, 13.0), 1))
        self.sb_rechazo.setValue(round(random.uniform(2.5, 7.0), 1))
        self.sb_filtro_alto.setValue(float(random.choice([1, 3, 5, 10, 20])))
        self.sb_filtro_bajo.setValue(float(random.choice([500, 750, 1000, 1500, 2000])))

    def _aplicar_subtipo(self, subtipo):
        opciones = protocol.maniobras_de(subtipo)
        actual = self.cb_maniobra.currentText()
        self.cb_maniobra.blockSignals(True)
        self.cb_maniobra.clear()
        self.cb_maniobra.addItems(opciones)
        if actual in opciones:
            self.cb_maniobra.setCurrentText(actual)
        self.cb_maniobra.blockSignals(False)
        self._refrescar_montaje()
        self.sig_maniobra.emit(self.cb_maniobra.currentText())

    def _aplicar_transductor(self):
        """Cada transductor tiene su rango y su escala: el aéreo en dB SPL
        --la escala en la que el caso guarda el umbral-- y el óseo en dB FL,
        con el tope de salida del vibrador."""
        transductor = self.cb_transductor.currentText()
        lo, hi = protocol.RANGO_INTENSIDAD[transductor]
        self.sb_int.blockSignals(True)
        self.sb_int.setRange(lo, hi)
        # Arranca arriba, pero no en el tope: buscar un umbral es bajar, y
        # el alumno tiene que poder subir también.
        self.sb_int.setValue(hi - 2 * protocol.PASO_INTENSIDAD)
        self.sb_int.blockSignals(False)
        unidad = 'dB SPL' if transductor == protocol.AEREO else 'dB FL'
        self.lbl_unidad_int.setText(f'{lo}–{hi} {unidad}')
        self._refrescar_duracion()

    def _refrescar_montaje(self):
        subtipo = self.subtipo()
        self.lbl_montaje.setText(
            'Registro: ' + protocol.descripcion_montaje(subtipo, self.lado()))

    def _refrescar_duracion(self):
        segundos = self.sb_promedios.value() / max(self.sb_tasa.value(), 0.1)
        self.lbl_duracion.setText(
            f'{self.sb_promedios.value()} barridos a {self.sb_tasa.value():.1f}/s '
            f'≈ {int(segundos // 60):d}:{int(segundos % 60):02d} de contracción')

    # ------------------------------------------------------------------
    # Señales
    # ------------------------------------------------------------------

    def _on_subtipo(self, *_):
        subtipo = self.subtipo()
        self._aplicar_subtipo(subtipo)
        self.sig_subtipo.emit(subtipo)
        self.sig_condicion.emit()

    def _on_lado(self, *_):
        self._refrescar_montaje()
        self.sig_lado.emit(self.lado())
        self.sig_condicion.emit()

    def _on_transductor(self, *_):
        self._aplicar_transductor()
        self.sig_condicion.emit()

    def _on_registrar(self):
        if self.registrando:
            self.sig_pausar.emit()
        else:
            self.sig_registrar.emit()

    def _on_detener(self):
        self.sig_detener.emit()

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def subtipo(self):
        return self.cb_subtipo.currentData() or protocol.CVEMP

    def lado(self):
        return 'OD' if self.btn_od.isChecked() else 'OI'

    def maniobra(self):
        return self.cb_maniobra.currentText()

    def ajustes(self):
        return Ajustes(
            subtipo=self.subtipo(),
            lado=self.lado(),
            transductor=self.cb_transductor.currentText(),
            freq=self.cb_freq.currentText(),
            polaridad=self.cb_pol.currentText(),
            intensidad=self.sb_int.value(),
            tasa=self.sb_tasa.value(),
            promedios=self.sb_promedios.value(),
            filtro_alto=self.sb_filtro_alto.value(),
            filtro_bajo=self.sb_filtro_bajo.value(),
            rechazo=self.sb_rechazo.value(),
            maniobra=self.maniobra(),
        )

    def set_registrando(self, registrando, pausado=False):
        """Congela lo que define la curva mientras se promedia.

        La maniobra queda viva a propósito: es la única cosa del registro
        que el paciente puede cambiar en el medio.
        """
        self.registrando = bool(registrando)
        for widget in (self.cb_subtipo, self.btn_od, self.btn_oi,
                       self.cb_transductor, self.cb_freq, self.cb_pol,
                       self.sb_int, self.sb_tasa, self.sb_promedios,
                       self.sb_rechazo, self.sb_filtro_alto, self.sb_filtro_bajo):
            widget.setDisabled(registrando or pausado)
        self.btn_detener.setEnabled(registrando or pausado)
        if registrando:
            self.btn_registrar.setText('Pausar')
        elif pausado:
            self.btn_registrar.setText('Continuar')
        else:
            self.btn_registrar.setText('Registrar')
        self.btn_registrar.setProperty('registrando', 'true' if registrando else 'false')
        theme.repintar(self.btn_registrar)
