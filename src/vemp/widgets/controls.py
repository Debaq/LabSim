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

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QDoubleSpinBox,
                               QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QWidget)

from core import iconos
from vemp import protocol, theme
from vemp.engine import Ajustes
from vemp.widgets.kit import Campos, ComboRecortado, Tarjeta


class PanelControl(QObject):
    """Los mandos del equipo y su estado. No es un widget: arma tres
    tarjetas (`caja_prueba`, `caja_estimulo`, `caja_registro`) y los botones
    Registrar/Detener, y la ventana los acomoda (en una o dos columnas según
    el alto, ver VempMainWindow._acomodar_mandos)."""

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

        self.caja_prueba = self._caja_prueba()
        self.caja_estimulo = self._caja_estimulo()
        self.caja_registro = self._caja_registro()
        # Los spinbox salían 3 px más altos que los combos: filas disparejas
        # y alto que en 768 px no sobra.
        alto = self.cb_freq.sizeHint().height()
        for spin in (self.sb_int, self.sb_tasa, self.sb_promedios, self.sb_rechazo,
                     self.sb_filtro_alto, self.sb_filtro_bajo):
            spin.setFixedHeight(alto)
        self.cajas = (self.caja_prueba, self.caja_estimulo, self.caja_registro)
        # Registrar y Detener son del panel (sus señales salen de acá) pero
        # van en la cabecera de la ventana, junto al avance del registro:
        # abajo de todo empujaban el alto mínimo del módulo.
        self._botones()

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

        self.cb_subtipo = ComboRecortado()
        for subtipo in protocol.SUBTIPOS:
            self.cb_subtipo.addItem(protocol.SUBTIPO_LABEL[subtipo], subtipo)
        campos.agregar('VEMP', self.cb_subtipo)

        fila = QWidget()
        lay = QHBoxLayout(fila)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.grupo_lado = QButtonGroup(fila)
        self.btn_od = QPushButton('OD')
        self.btn_oi = QPushButton('OI')
        for i, btn in enumerate((self.btn_od, self.btn_oi)):
            btn.setCheckable(True)
            btn.setProperty('lado', 'od' if i == 0 else 'oi')
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.grupo_lado.addButton(btn, i)
            lay.addWidget(btn)
        self.btn_od.setChecked(True)
        campos.agregar('Oído', fila)

        self.cb_maniobra = ComboRecortado()
        campos.agregar('Maniobra', self.cb_maniobra)
        caja.agregar(campos)
        return caja

    def _caja_estimulo(self):
        caja = Tarjeta('Estímulo')
        campos = Campos()

        self.cb_transductor = ComboRecortado()
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
        self.sb_tasa.setDecimals(1)
        self.sb_tasa.setSuffix(' /s')
        campos.agregar('Tasa', self.sb_tasa)

        caja.agregar(campos)
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
        self.sb_rechazo.setToolTip('Rechazo de artefactos: múltiplo del EMG '
                                   'tónico esperado')
        campos.agregar('Rechazo', self.sb_rechazo)

        # El filtro es una banda: pasa-alto y pasa-bajo en la misma fila,
        # como se lee (1–2000 Hz). En dos filas sumaban alto que no hay.
        self.sb_filtro_alto = QDoubleSpinBox()
        self.sb_filtro_alto.setRange(*protocol.FILTRO_PASA_ALTO)
        self.sb_filtro_alto.setSingleStep(1.0)
        self.sb_filtro_alto.setDecimals(0)
        self.sb_filtro_alto.setSuffix(' Hz')
        self.sb_filtro_alto.setToolTip('Pasa-alto')
        self.sb_filtro_alto.setMinimumWidth(64)

        self.sb_filtro_bajo = QDoubleSpinBox()
        self.sb_filtro_bajo.setRange(*protocol.FILTRO_PASA_BAJO)
        self.sb_filtro_bajo.setSingleStep(50.0)
        self.sb_filtro_bajo.setDecimals(0)
        self.sb_filtro_bajo.setSuffix(' Hz')
        self.sb_filtro_bajo.setToolTip('Pasa-bajo')
        self.sb_filtro_bajo.setMinimumWidth(72)

        banda = QWidget()
        fila = QHBoxLayout(banda)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(4)
        fila.addWidget(self.sb_filtro_alto, 1)
        guion = QLabel('–')
        guion.setProperty('role', 'campo')
        fila.addWidget(guion)
        fila.addWidget(self.sb_filtro_bajo, 1)
        campos.agregar('Filtro', banda)

        caja.agregar(campos)
        return caja

    def _botones(self):
        self.btn_registrar = QPushButton('Registrar')
        self.btn_registrar.setObjectName('btnRegistrar')
        self.btn_registrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icono_registrar = iconos.icono_boton('atender', '#FFFFFF', tam=14)
        self.btn_registrar.setIcon(self._icono_registrar)
        self.btn_detener = QPushButton('Detener')
        self.btn_detener.setObjectName('btnDetener')
        self.btn_detener.setIcon(iconos.icono_boton('detener', theme.TEXTO_SUAVE, tam=14))
        self.btn_detener.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detener.setEnabled(False)

    def _conectar(self):
        self.cb_subtipo.currentIndexChanged.connect(self._on_subtipo)
        self.grupo_lado.idClicked.connect(self._on_lado)
        self.cb_maniobra.currentTextChanged.connect(self.sig_maniobra.emit)
        self.cb_transductor.currentTextChanged.connect(self._on_transductor)
        # Todo lo que cambia la curva que saldría refresca la cabecera (la
        # condición y "Listo para registrar ...", con la duración).
        for senal in (self.cb_freq.currentTextChanged, self.cb_pol.currentTextChanged,
                      self.sb_int.valueChanged, self.sb_tasa.valueChanged,
                      self.sb_promedios.valueChanged):
            senal.connect(lambda *_: self.sig_condicion.emit())
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
        self.cb_maniobra.setToolTip(self.cb_maniobra.currentText())
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
        # La unidad va en el campo: es la escala del transductor elegido.
        self.sb_int.setSuffix(f' {unidad}')
        self.sb_int.setToolTip(f'{lo}–{hi} {unidad}')

    # ------------------------------------------------------------------
    # Señales
    # ------------------------------------------------------------------

    def _on_subtipo(self, *_):
        subtipo = self.subtipo()
        self._aplicar_subtipo(subtipo)
        self.sig_subtipo.emit(subtipo)
        self.sig_condicion.emit()

    def _on_lado(self, *_):
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

    def habilitar(self, activo):
        """Sin caso no se toca nada: ni los mandos ni Registrar."""
        for caja in self.cajas:
            caja.setEnabled(activo)
        self.btn_registrar.setEnabled(activo)
        if not activo:
            self.btn_detener.setEnabled(False)

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
        # El triángulo es "arrancar": en Pausar no va.
        self.btn_registrar.setIcon(QIcon() if registrando else self._icono_registrar)
        self.btn_registrar.setProperty('registrando', 'true' if registrando else 'false')
        theme.repintar(self.btn_registrar)
