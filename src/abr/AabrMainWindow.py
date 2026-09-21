"""Equipo de tamizaje auditivo automatizado (AABR).

Es OTRO equipo, no un modo del ABR: comparte el generador, el criterio de
detección y el ruido del paciente, pero no deja marcar ondas ni buscar
umbrales. Se pone un nivel fijo y el equipo contesta PASA o REFIERE cuando
el estadístico cruza el criterio o cuando se acaban los barridos.

Lo que lo define es el ORDEN, que es el del equipo real y no se puede
saltear:

    1. Chequeo de sonda -- la comparte con el equipo de EOA, así que es la
       misma pantalla de probe fit (ver oae/widgets/probe_check.py).
    2. Chequeo de impedancias -- con los electrodos fuera de norma el
       equipo no deja lanzar, y ahí se acomodan.
    3. Estímulo: promedia mostrando la curva, que sí se ve (los equipos de
       tamizaje la muestran mientras registran).
    4. Resultado: PASA o REFIERE.

El panel de configuración queda a la vista y editable a propósito. El
equipo real se configura una vez y nadie vuelve a mirarlo; acá el docente
puede mover el nivel, la tasa, los barridos máximos o el criterio delante
del curso y ver qué le pasa al resultado en la corrida siguiente.

Se monta como subventana MDI igual que ABR (botón "AABR", al lado) y se
habilita con el mismo módulo del curso: ver MODULE_ALIAS en
core/ui_helpers.py.
"""
import numpy as np
import pyqtgraph as pg

from abr.ABR_generator import (ABR_Curve, ABRGenerator, IMPEDANCE_BALANCE_LIMIT_KOHM,
                               IMPEDANCE_LIMIT_KOHM)
from abr.AbrAdvanceSettings import ELECTRODES, TRANSDUCERS, default_settings
from oae.generators.base import oae_probe_fit
from oae.widgets.probe_check import ProbeCheckWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QMainWindow, QProgressBar, QPushButton,
                               QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

# Protocolo de tamizaje de rutina. Son los defaults del equipo, no una
# recomendación: el docente los mueve en pantalla.
NIVEL_DB = 35            # dB nHL: el nivel al que tamiza un AABR
TASA_HZ = 90.0           # estímulos/s -- muy por encima del ABR diagnóstico
BARRIDOS_MAX = 6000
CRITERIO_FSP = 3.1
RECHAZO_UV = 25.0
FILTRO_ALTO = 100.0      # pasa-alto (Hz)
FILTRO_BAJO = 3000.0     # pasa-bajo (Hz)
ESTIMULOS = ('CE-Chirp', 'Click')

# Sello mínimo para dar la sonda por puesta. Por debajo de esto el equipo
# no deja avanzar: entra menos estímulo del que dice el dial.
SELLO_MINIMO = 0.60
# Cuánto dura el chequeo de sonda antes de poder seguir (ms).
SONDA_MS = 2500

# Cada tick promedia un bloque: la prueba entera dura unos segundos, que es
# lo que hace que se pueda mostrar en clase sin esperar el registro real.
TICK_MS = 250
BLOQUES = 20

LADOS = ('OD', 'OI')
PASOS = ("1 · Sonda", "2 · Impedancias", "3 · Registro", "4 · Resultado")


class AabrMainWindow(QMainWindow):
    def __init__(self, data_login=None) -> None:
        QMainWindow.__init__(self)
        self.data_login = data_login
        self.setWindowTitle("AABR")
        self.data_current = None
        self.appointment_id = None
        # Sin datos reales no se tamiza nada: ni un ejemplo sintético.
        self.abr = {'OD': None, 'OI': None}
        self.eoas = {'OD': None, 'OI': None}
        self.resultado = {'OD': None, 'OI': None}
        self.lado_activo = 'OD'
        self.barridos = 0
        self.corriendo = False
        self.paso = 0
        self.sonda_ok = False
        self.impedancias_ok = False
        self.technical = default_settings('ABR')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer_sonda = QTimer(self)
        self.timer_sonda.setSingleShot(True)
        self.timer_sonda.timeout.connect(self._sonda_lista)

        self._build()
        self._set_enabled(False)
        self._ir_a(0)

    # ------------------------------------------------------------------ UI
    def _build(self):
        central = QWidget()
        raiz = QHBoxLayout(central)
        raiz.addWidget(self._panel_config(), 0)

        derecha = QVBoxLayout()
        self.lbl_paciente = QLabel("Sin atención abierta")
        self.lbl_paciente.setStyleSheet("color:#666;")
        derecha.addWidget(self.lbl_paciente)
        derecha.addLayout(self._barra_pasos())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._paso_sonda())
        self.stack.addWidget(self._paso_impedancias())
        self.stack.addWidget(self._paso_registro())
        self.stack.addWidget(self._paso_resultado())
        derecha.addWidget(self.stack, 1)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setStyleSheet("color:#444;")
        derecha.addWidget(self.lbl_resumen)
        raiz.addLayout(derecha, 1)
        self.setCentralWidget(central)

    def _barra_pasos(self):
        fila = QHBoxLayout()
        self.lbl_pasos = []
        for texto in PASOS:
            lbl = QLabel(texto)
            lbl.setAlignment(Qt.AlignCenter)
            fila.addWidget(lbl)
            self.lbl_pasos.append(lbl)
        return fila

    def _panel_config(self):
        caja = QGroupBox("Configuración del equipo")
        form = QFormLayout(caja)

        self.cb_lado = QComboBox()
        self.cb_lado.addItems(LADOS)
        self.cb_lado.currentTextChanged.connect(self._cambiar_lado)
        form.addRow("Oído", self.cb_lado)

        # TRANSDUCERS es {etiqueta: clave} (ver AbrAdvanceSettings).
        self.cb_transducer = QComboBox()
        self.cb_transducer.addItems(list(TRANSDUCERS.keys()))
        self._transducer_keys = list(TRANSDUCERS.values())
        self.cb_transducer.setCurrentIndex(
            self._transducer_keys.index('insert_earphone'))
        form.addRow("Transductor", self.cb_transducer)

        self.cb_stim = QComboBox()
        self.cb_stim.addItems(ESTIMULOS)
        form.addRow("Estímulo", self.cb_stim)

        self.sb_nivel = QSpinBox()
        self.sb_nivel.setRange(0, 70)
        self.sb_nivel.setSingleStep(5)
        self.sb_nivel.setValue(NIVEL_DB)
        self.sb_nivel.setSuffix(" dB nHL")
        form.addRow("Nivel", self.sb_nivel)

        self.sb_tasa = QDoubleSpinBox()
        self.sb_tasa.setRange(5.0, 100.0)
        self.sb_tasa.setDecimals(1)
        self.sb_tasa.setValue(TASA_HZ)
        self.sb_tasa.setSuffix(" /s")
        form.addRow("Tasa", self.sb_tasa)

        self.sb_barridos = QSpinBox()
        self.sb_barridos.setRange(200, 20000)
        self.sb_barridos.setSingleStep(500)
        self.sb_barridos.setValue(BARRIDOS_MAX)
        form.addRow("Barridos máximos", self.sb_barridos)

        self.sb_criterio = QDoubleSpinBox()
        self.sb_criterio.setRange(1.5, 10.0)
        self.sb_criterio.setDecimals(1)
        self.sb_criterio.setSingleStep(0.1)
        self.sb_criterio.setValue(CRITERIO_FSP)
        form.addRow("Criterio FSP", self.sb_criterio)

        self.sb_rechazo = QDoubleSpinBox()
        self.sb_rechazo.setRange(0.0, 100.0)
        self.sb_rechazo.setDecimals(1)
        self.sb_rechazo.setValue(RECHAZO_UV)
        self.sb_rechazo.setSuffix(" µV")
        form.addRow("Rechazo de artefacto", self.sb_rechazo)

        self.sb_pasa_alto = QDoubleSpinBox()
        self.sb_pasa_alto.setRange(0.5, 500.0)
        self.sb_pasa_alto.setDecimals(1)
        self.sb_pasa_alto.setValue(FILTRO_ALTO)
        self.sb_pasa_alto.setSuffix(" Hz")
        form.addRow("Filtro pasa-alto", self.sb_pasa_alto)

        self.sb_pasa_bajo = QDoubleSpinBox()
        self.sb_pasa_bajo.setRange(200.0, 6000.0)
        self.sb_pasa_bajo.setDecimals(0)
        self.sb_pasa_bajo.setValue(FILTRO_BAJO)
        self.sb_pasa_bajo.setSuffix(" Hz")
        form.addRow("Filtro pasa-bajo", self.sb_pasa_bajo)

        self.chk_auto = QCheckBox("Parar al cruzar el criterio")
        self.chk_auto.setChecked(True)
        form.addRow(self.chk_auto)

        # Lo que hace es devolver los controles de arriba a como vienen de
        # fábrica: es el "restaurar predeterminados" del equipo, no otro
        # protocolo que haya que elegir.
        self.btn_protocolo = QPushButton("Restaurar valores de fábrica")
        self.btn_protocolo.clicked.connect(self.restore_protocol)
        form.addRow(self.btn_protocolo)
        return caja

    # ------------------------------------------------------------- paso 1
    def _paso_sonda(self):
        caja = QWidget()
        vbox = QVBoxLayout(caja)
        # La misma pantalla del equipo de EOA: los dos comparten la sonda,
        # y el sello sale del mismo campo del caso (EOAS['sello_pct']).
        self.probe = ProbeCheckWidget()
        vbox.addWidget(self.probe)
        self.lbl_sonda = QLabel("Poné la sonda y verificá el ajuste.")
        self.lbl_sonda.setWordWrap(True)
        vbox.addWidget(self.lbl_sonda)

        fila = QHBoxLayout()
        self.btn_sonda = QPushButton("Verificar sonda")
        self.btn_sonda.clicked.connect(self.verificar_sonda)
        self.btn_sonda_ok = QPushButton("Siguiente →")
        self.btn_sonda_ok.setEnabled(False)
        self.btn_sonda_ok.clicked.connect(lambda: self._ir_a(1))
        fila.addWidget(self.btn_sonda)
        fila.addWidget(self.btn_sonda_ok)
        vbox.addLayout(fila)
        return caja

    # ------------------------------------------------------------- paso 2
    def _paso_impedancias(self):
        caja = QWidget()
        vbox = QVBoxLayout(caja)
        grupo = QGroupBox("Impedancia de los electrodos")
        grid = QGridLayout(grupo)
        self.imp_spins = {}
        self.imp_labels = {}
        impedancias = self.technical.get('impedance') or {}
        for row, (key, label, _default) in enumerate(ELECTRODES):
            spin = QDoubleSpinBox()
            spin.setRange(0.5, 20.0)
            spin.setSingleStep(0.5)
            spin.setDecimals(1)
            spin.setSuffix(" kΩ")
            spin.setValue(float(impedancias.get(key, 2.0)))
            spin.valueChanged.connect(self.medir_impedancias)
            estado = QLabel("—")
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(spin, row, 1)
            grid.addWidget(estado, row, 2)
            self.imp_spins[key] = spin
            self.imp_labels[key] = estado
        vbox.addWidget(grupo)

        self.lbl_impedancias = QLabel("")
        self.lbl_impedancias.setWordWrap(True)
        vbox.addWidget(self.lbl_impedancias)

        fila = QHBoxLayout()
        self.btn_imp_medir = QPushButton("Medir impedancias")
        self.btn_imp_medir.clicked.connect(self.medir_impedancias)
        self.btn_imp_ok = QPushButton("Siguiente →")
        self.btn_imp_ok.setEnabled(False)
        self.btn_imp_ok.clicked.connect(lambda: self._ir_a(2))
        fila.addWidget(QPushButton("← Sonda", clicked=lambda: self._ir_a(0)))
        fila.addWidget(self.btn_imp_medir)
        fila.addWidget(self.btn_imp_ok)
        vbox.addLayout(fila)
        vbox.addStretch(1)
        return caja

    # ------------------------------------------------------------- paso 3
    def _paso_registro(self):
        caja = QWidget()
        vbox = QVBoxLayout(caja)
        # La curva SÍ se ve: los equipos de tamizaje la muestran mientras
        # promedian. Lo que no hay es marcado de ondas ni escala de
        # intensidades: es una sola curva, al nivel del tamizaje.
        self.plot = pg.PlotWidget()
        self.plot.setBackground((255, 255, 255))
        self.plot.setLabel("bottom", "Tiempo", units="ms")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.curva = self.plot.plot(pen=pg.mkPen((41, 128, 185), width=2))
        vbox.addWidget(self.plot, 1)

        self.barra = QProgressBar()
        self.barra.setRange(0, BARRIDOS_MAX)
        self.barra.setFormat("%v de %m barridos")
        vbox.addWidget(self.barra)

        grid = QGridLayout()
        self.lbl_fsp = QLabel("—")
        self.lbl_ruido = QLabel("—")
        self.lbl_aceptados = QLabel("—")
        for col, (titulo, widget) in enumerate((
                ("FSP", self.lbl_fsp),
                ("Ruido residual", self.lbl_ruido),
                ("Barridos aceptados", self.lbl_aceptados))):
            titulo_lbl = QLabel(titulo)
            titulo_lbl.setStyleSheet("color:#666;")
            grid.addWidget(titulo_lbl, 0, col)
            widget.setStyleSheet("font-size:15px; font-weight:bold;")
            grid.addWidget(widget, 1, col)
        vbox.addLayout(grid)

        fila = QHBoxLayout()
        self.btn_start = QPushButton("Iniciar")
        self.btn_start.clicked.connect(self.start)
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop)
        fila.addWidget(QPushButton("← Impedancias", clicked=lambda: self._ir_a(1)))
        fila.addWidget(self.btn_start)
        fila.addWidget(self.btn_stop)
        vbox.addLayout(fila)
        return caja

    # ------------------------------------------------------------- paso 4
    def _paso_resultado(self):
        caja = QWidget()
        vbox = QVBoxLayout(caja)
        self.lbl_veredicto = QLabel("—")
        self.lbl_veredicto.setAlignment(Qt.AlignCenter)
        self.lbl_veredicto.setMinimumHeight(110)
        self._pintar_veredicto(None)
        vbox.addWidget(self.lbl_veredicto)

        self.lbl_detalle = QLabel("")
        self.lbl_detalle.setWordWrap(True)
        self.lbl_detalle.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl_detalle)

        fila = QHBoxLayout()
        fila.addWidget(QPushButton("Repetir este oído", clicked=lambda: self._ir_a(2)))
        fila.addWidget(QPushButton("Otro oído (desde la sonda)",
                                   clicked=self._otro_oido))
        vbox.addLayout(fila)
        vbox.addStretch(1)
        return caja

    # -------------------------------------------------------------- pasos
    def _ir_a(self, paso):
        """Cambia de paso. Hacia adelante solo si el anterior está hecho."""
        if paso >= 1 and not self.sonda_ok:
            paso = 0
        if paso >= 2 and not self.impedancias_ok:
            paso = 1
        self.paso = paso
        self.stack.setCurrentIndex(paso)
        for i, lbl in enumerate(self.lbl_pasos):
            activo = i == paso
            hecho = ((i == 0 and self.sonda_ok) or (i == 1 and self.impedancias_ok)
                     or (i == 3 and self.resultado.get(self.lado_activo)))
            color = "#1b5e20" if hecho else ("#000" if activo else "#999")
            peso = "bold" if activo else "normal"
            lbl.setStyleSheet(f"color:{color}; font-weight:{peso};")
        if paso != 0:
            self.probe.stop()
        if paso != 2:
            self.stop()

    def _otro_oido(self):
        self.cb_lado.setCurrentText('OI' if self.lado_activo == 'OD' else 'OD')

    # -------------------------------------------------------------- paso 1
    def verificar_sonda(self):
        """Chequeo de sonda, el mismo del equipo de EOA."""
        caso = self.eoas.get(self.lado_activo)
        if self.data_current is None:
            return
        self.sonda_ok = False
        self.btn_sonda_ok.setEnabled(False)
        self.lbl_sonda.setText("Acomodando la sonda…")
        self.probe.start(60.0, oae_probe_fit(caso))
        self.timer_sonda.start(SONDA_MS)

    def _sonda_lista(self):
        sello = float(getattr(self.probe, 'fit_quality', 0.0))
        self.sonda_ok = sello >= SELLO_MINIMO
        self.btn_sonda_ok.setEnabled(self.sonda_ok)
        if self.sonda_ok:
            self.lbl_sonda.setText(f"Sello {sello * 100:.0f} %: la sonda está puesta.")
        else:
            self.lbl_sonda.setText(
                f"Sello {sello * 100:.0f} %: el equipo no deja seguir. "
                "Volvé a poner la sonda.")
        self._ir_a(self.paso)

    # -------------------------------------------------------------- paso 2
    def medir_impedancias(self):
        """Pantalla de impedancias: con los electrodos fuera de norma el
        equipo no deja lanzar el estímulo."""
        impedancias = {k: float(spin.value()) for k, spin in self.imp_spins.items()}
        self.technical['impedance'] = impedancias
        peor, desbalance, ok = ABRGenerator.impedance_report(self.technical)
        for key, spin in self.imp_spins.items():
            valor = float(spin.value())
            bien = valor <= IMPEDANCE_LIMIT_KOHM
            self.imp_labels[key].setText("OK" if bien else "ALTA")
            self.imp_labels[key].setStyleSheet(
                f"color:{'#1b5e20' if bien else '#b71c1c'}; font-weight:bold;")
        self.impedancias_ok = bool(ok)
        self.btn_imp_ok.setEnabled(self.impedancias_ok)
        self.lbl_impedancias.setText(
            f"Peor electrodo {peor:.1f} kΩ (límite {IMPEDANCE_LIMIT_KOHM:.0f}) · "
            f"desbalance {desbalance:.1f} kΩ (límite {IMPEDANCE_BALANCE_LIMIT_KOHM:.0f})")
        self._ir_a(self.paso)

    # -------------------------------------------------------------- paso 3
    def start(self):
        if self.corriendo or self.abr.get(self.lado_activo) is None:
            if self.abr.get(self.lado_activo) is None:
                self.lbl_resumen.setText(
                    f"Este paciente no tiene ABR configurado en {self.lado_activo}.")
            return
        if not (self.sonda_ok and self.impedancias_ok):
            self._ir_a(0 if not self.sonda_ok else 1)
            return
        self.barridos = 0
        self.resultado[self.lado_activo] = None
        self.barra.setRange(0, int(self.sb_barridos.value()))
        self.barra.setValue(0)
        self.corriendo = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.timer.start(TICK_MS)

    def stop(self):
        self.timer.stop()
        self.corriendo = False
        if hasattr(self, 'btn_start'):
            self.btn_start.setEnabled(self.data_current is not None)
            self.btn_stop.setEnabled(False)

    def _control_setting(self):
        return {
            'test': 'ABR',
            'stim': self.cb_stim.currentText(),
            'pol': 'Alternada',
            'int': int(self.sb_nivel.value()),
            'rate': float(self.sb_tasa.value()),
            'filter_down': float(self.sb_pasa_bajo.value()),
            'filter_passhigh': float(self.sb_pasa_alto.value()),
            'average': int(self.sb_barridos.value()),
            'side': self.lado_activo,
            'mkg': 0,
        }

    def _technical(self):
        tech = dict(self.technical)
        tech['transducer'] = self._transducer_keys[self.cb_transducer.currentIndex()]
        tech['artifact_reject_uv'] = float(self.sb_rechazo.value())
        tech['fsp_criterion'] = float(self.sb_criterio.value())
        tech['impedance'] = {k: float(s.value()) for k, s in self.imp_spins.items()}
        return tech

    def _tick(self):
        total = int(self.sb_barridos.value())
        self.barridos = min(total, self.barridos + max(1, total // BLOQUES))
        caso = self.abr.get(self.lado_activo)
        contra = self.abr.get('OI' if self.lado_activo == 'OD' else 'OD')
        x, y, _, _, _, meta = ABR_Curve(
            int(self.sb_nivel.value()), self._control_setting(), caso, 0,
            # prom = [fracción promediada, total]: por debajo de 1.0 el
            # generador lo toma como fracción exacta (ver ABR_Curve).
            [self.barridos / float(total), total],
            done=False,
            patient=self.data_current,
            contra=contra,
            capture_id=f"AABR-{self.lado_activo}",
            technical=self._technical(),
        )
        self.curva.setData(np.asarray(x), np.asarray(y))
        fsp = float(meta.get('fsp') or 1.0)
        criterio = float(self.sb_criterio.value())
        self.barra.setValue(int(self.barridos))
        self.lbl_fsp.setText(f"{fsp:.2f}")
        self.lbl_ruido.setText(f"{meta.get('residual_noise_nv', 0):.0f} nV")
        self.lbl_aceptados.setText(f"{int(meta.get('accepted_sweeps') or 0)}")

        if fsp >= criterio and self.chk_auto.isChecked():
            self._cerrar('PASA', fsp)
        elif self.barridos >= total:
            self._cerrar('PASA' if fsp >= criterio else 'REFIERE', fsp)

    def _cerrar(self, veredicto, fsp):
        self.stop()
        self.resultado[self.lado_activo] = {
            'veredicto': veredicto,
            'barridos': self.barridos,
            'fsp': fsp,
            'nivel': int(self.sb_nivel.value()),
            'estimulo': self.cb_stim.currentText(),
        }
        self._pintar_veredicto(veredicto)
        self.lbl_detalle.setText(
            f"{self.lado_activo} · {self.cb_stim.currentText()} a "
            f"{int(self.sb_nivel.value())} dB nHL · {int(self.barridos)} barridos "
            f"· FSP {fsp:.2f}")
        self._pintar_resumen()
        self._ir_a(3)

    # -------------------------------------------------------------- estado
    def restore_protocol(self):
        """Devuelve los controles a como vienen de fábrica."""
        self.sb_nivel.setValue(NIVEL_DB)
        self.sb_tasa.setValue(TASA_HZ)
        self.sb_barridos.setValue(BARRIDOS_MAX)
        self.sb_criterio.setValue(CRITERIO_FSP)
        self.sb_rechazo.setValue(RECHAZO_UV)
        self.sb_pasa_alto.setValue(FILTRO_ALTO)
        self.sb_pasa_bajo.setValue(FILTRO_BAJO)
        self.chk_auto.setChecked(True)
        self.cb_stim.setCurrentText(ESTIMULOS[0])
        self.cb_transducer.setCurrentIndex(
            self._transducer_keys.index('insert_earphone'))

    def _set_enabled(self, on):
        for w in (self.btn_start, self.cb_lado, self.btn_sonda):
            w.setEnabled(on)

    def la_super(self, data, appointment_id=None):
        """Caso del paciente en atención, o None al cerrarla.

        Mismo patrón que AbrMainWindow: sin datos reales no se tamiza, ni
        siquiera con atención abierta pero sin ABR configurado en ese lado.
        """
        self.stop()
        self.probe.stop()
        self.appointment_id = appointment_id
        self.data_current = data
        abr_data = (data or {}).get('ABR') or {}
        eoas_data = (data or {}).get('EOAS') or {}
        self.abr = {'OD': abr_data.get('OD'), 'OI': abr_data.get('OI')}
        self.eoas = {'OD': eoas_data.get('OD'), 'OI': eoas_data.get('OI')}
        self.resultado = {'OD': None, 'OI': None}
        self._set_enabled(data is not None)
        if data is None:
            self.lbl_paciente.setText("Sin atención abierta")
        else:
            edad = data.get('edad_horas')
            detalle = f"{edad:g} horas de vida" if edad not in (None, '') \
                else f"{data.get('edad', '?')} años"
            self.lbl_paciente.setText(
                f"{data.get('nombre', 'Paciente')} · {detalle}")
        self._reset_lectura()

    def _cambiar_lado(self, lado):
        self.stop()
        self.lado_activo = lado
        # Oído nuevo, sonda nueva: se vuelve al primer paso, como en el
        # equipo real -- la oliva se saca y se pone del otro lado.
        self.sonda_ok = False
        self.impedancias_ok = False
        self._reset_lectura()
        self._ir_a(0)

    def _reset_lectura(self):
        self.barridos = 0
        self.barra.setRange(0, int(self.sb_barridos.value()))
        self.barra.setValue(0)
        self.curva.clear()
        self.lbl_fsp.setText("—")
        self.lbl_ruido.setText("—")
        self.lbl_aceptados.setText("—")
        self.lbl_sonda.setText("Poné la sonda y verificá el ajuste.")
        self.btn_sonda_ok.setEnabled(False)
        self.btn_imp_ok.setEnabled(self.impedancias_ok)
        self._pintar_veredicto(self.resultado.get(self.lado_activo))
        self.lbl_detalle.setText("")
        self._pintar_resumen()

    def _pintar_veredicto(self, veredicto):
        colores = {
            'PASA': ("#1b5e20", "#c8e6c9"),
            'REFIERE': ("#b71c1c", "#ffcdd2"),
            None: ("#555", "#eceff1"),
        }
        color, fondo = colores.get(veredicto, colores[None])
        self.lbl_veredicto.setText(veredicto or "—")
        self.lbl_veredicto.setStyleSheet(
            f"font-size:34px; font-weight:bold; color:{color};"
            f"background:{fondo}; border-radius:8px;")

    def _pintar_resumen(self):
        partes = []
        for lado in LADOS:
            r = self.resultado.get(lado)
            partes.append(f"{lado}: {r['veredicto']} ({int(r['barridos'])} barridos)"
                          if r else f"{lado}: sin tamizar")
        self.lbl_resumen.setText(" · ".join(partes))

    def submit_report(self):
        """El tamizaje no sube informe.

        Existe para que la ventana principal pueda llamarlo igual que a los
        otros módulos de examen sin preguntar: un AABR no produce curvas
        marcadas ni conclusión, produce PASA o REFIERE.
        """
        return

    def closeEvent(self, event):
        self.stop()
        self.probe.stop()
        event.accept()
