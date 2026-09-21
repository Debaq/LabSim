"""Equipo de tamizaje auditivo automatizado (AABR).

Es OTRO equipo, no un modo del ABR: comparte el generador, el criterio de
detección y el ruido del paciente, pero no deja marcar ondas ni buscar
umbrales. Se pone un nivel fijo, se aprieta Iniciar y el equipo contesta
PASA o REFIERE cuando el estadístico cruza el criterio o cuando se acaban
los barridos. Por eso no dibuja la curva: lo que se ve es lo que ve quien
tamiza -- barridos, ruido residual y el número del FSP.

El panel de configuración queda a la vista y editable a propósito. El
equipo real se configura una vez y nadie vuelve a mirarlo; acá el docente
puede mover el nivel, la tasa, los barridos máximos o el criterio delante
del curso y ver qué le pasa al resultado en la corrida siguiente.

Se monta como subventana MDI igual que ABR (botón "AABR", al lado) y se
habilita con el mismo módulo del curso: ver MODULE_ALIAS en
core/ui_helpers.py.
"""
from abr.ABR_generator import ABR_Curve
from abr.AbrAdvanceSettings import TRANSDUCERS, default_settings
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QMainWindow, QProgressBar, QPushButton,
                               QSpinBox, QVBoxLayout, QWidget)

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

# Cada tick promedia un bloque: la prueba entera dura unos segundos, que es
# lo que hace que se pueda mostrar en clase sin esperar el registro real.
TICK_MS = 250
BLOQUES = 20

LADOS = ('OD', 'OI')


class AabrMainWindow(QMainWindow):
    def __init__(self, data_login=None) -> None:
        QMainWindow.__init__(self)
        self.data_login = data_login
        self.setWindowTitle("AABR")
        self.data_current = None
        self.appointment_id = None
        # Sin datos reales no se tamiza nada: ni un ejemplo sintético.
        self.abr = {'OD': None, 'OI': None}
        self.resultado = {'OD': None, 'OI': None}
        self.lado_activo = 'OD'
        self.barridos = 0
        self.corriendo = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        self._build()
        self._set_enabled(False)

    # ------------------------------------------------------------------ UI
    def _build(self):
        central = QWidget()
        raiz = QHBoxLayout(central)
        raiz.addWidget(self._panel_config(), 0)
        raiz.addWidget(self._panel_registro(), 1)
        self.setCentralWidget(central)

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
        self.cb_transducer.setToolTip(
            "Transductor con el que se presenta el estímulo. Cambia la "
            "atenuación interaural, el retardo y el tamaño del artefacto.")
        form.addRow("Transductor", self.cb_transducer)

        self.cb_stim = QComboBox()
        self.cb_stim.addItems(ESTIMULOS)
        self.cb_stim.setToolTip(
            "Estímulo. El chirp compensa el retardo de la onda viajera, así "
            "que sincroniza más fibras que el click al mismo nivel.")
        form.addRow("Estímulo", self.cb_stim)

        self.sb_nivel = QSpinBox()
        self.sb_nivel.setRange(0, 70)
        self.sb_nivel.setSingleStep(5)
        self.sb_nivel.setValue(NIVEL_DB)
        self.sb_nivel.setSuffix(" dB nHL")
        self.sb_nivel.setToolTip(
            "Nivel fijo al que tamiza el equipo. No hay búsqueda de umbral: "
            "el resultado es si a ESE nivel hay respuesta o no.")
        form.addRow("Nivel", self.sb_nivel)

        self.sb_tasa = QDoubleSpinBox()
        self.sb_tasa.setRange(5.0, 100.0)
        self.sb_tasa.setDecimals(1)
        self.sb_tasa.setValue(TASA_HZ)
        self.sb_tasa.setSuffix(" /s")
        self.sb_tasa.setToolTip(
            "Estímulos por segundo. Más alta junta barridos más rápido y "
            "alarga las latencias; el equipo no las mide, pero la respuesta "
            "se achica.")
        form.addRow("Tasa", self.sb_tasa)

        self.sb_barridos = QSpinBox()
        self.sb_barridos.setRange(200, 20000)
        self.sb_barridos.setSingleStep(500)
        self.sb_barridos.setValue(BARRIDOS_MAX)
        self.sb_barridos.setToolTip(
            "Tope de barridos. Si el criterio no se cruza antes de llegar "
            "acá, el equipo informa REFIERE.")
        form.addRow("Barridos máximos", self.sb_barridos)

        self.sb_criterio = QDoubleSpinBox()
        self.sb_criterio.setRange(1.5, 10.0)
        self.sb_criterio.setDecimals(1)
        self.sb_criterio.setSingleStep(0.1)
        self.sb_criterio.setValue(CRITERIO_FSP)
        self.sb_criterio.setToolTip(
            "Valor de FSP con el que el equipo declara respuesta presente.")
        form.addRow("Criterio FSP", self.sb_criterio)

        self.sb_rechazo = QDoubleSpinBox()
        self.sb_rechazo.setRange(0.0, 100.0)
        self.sb_rechazo.setDecimals(1)
        self.sb_rechazo.setValue(RECHAZO_UV)
        self.sb_rechazo.setSuffix(" µV")
        self.sb_rechazo.setToolTip(
            "Rechazo de artefacto. Los barridos que cruzan esta barra no "
            "entran al promedio: el contador sigue, el promedio no avanza.")
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
        self.sb_pasa_bajo.setToolTip(
            "Banda de registro. Abrirla deja entrar más ruido en cada "
            "barrido, así que hacen falta más para llegar al criterio.")
        form.addRow("Filtro pasa-bajo", self.sb_pasa_bajo)

        self.chk_auto = QCheckBox("Parar al cruzar el criterio")
        self.chk_auto.setChecked(True)
        self.chk_auto.setToolTip(
            "Como trabaja el equipo: en cuanto cruza, corta y declara PASA. "
            "Destildado sigue promediando hasta el tope, que sirve para ver "
            "cómo se sigue moviendo el FSP después del cruce.")
        form.addRow(self.chk_auto)

        self.btn_protocolo = QPushButton("Volver al protocolo de tamizaje")
        self.btn_protocolo.clicked.connect(self.restore_protocol)
        form.addRow(self.btn_protocolo)

        return caja

    def _panel_registro(self):
        caja = QGroupBox("Registro")
        vbox = QVBoxLayout(caja)

        self.lbl_paciente = QLabel("Sin atención abierta")
        self.lbl_paciente.setStyleSheet("color:#666;")
        vbox.addWidget(self.lbl_paciente)

        self.lbl_veredicto = QLabel("—")
        self.lbl_veredicto.setAlignment(Qt.AlignCenter)
        self.lbl_veredicto.setMinimumHeight(90)
        self._pintar_veredicto(None)
        vbox.addWidget(self.lbl_veredicto)

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

        botones = QHBoxLayout()
        self.btn_start = QPushButton("Iniciar")
        self.btn_start.clicked.connect(self.start)
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        botones.addWidget(self.btn_start)
        botones.addWidget(self.btn_stop)
        vbox.addLayout(botones)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setStyleSheet("color:#444;")
        vbox.addWidget(self.lbl_resumen)
        vbox.addStretch(1)
        return caja

    # -------------------------------------------------------------- estado
    def restore_protocol(self):
        """Vuelve el equipo a como viene de fábrica."""
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
        for w in (self.btn_start, self.cb_lado):
            w.setEnabled(on)

    def la_super(self, data, appointment_id=None):
        """Caso del paciente en atención, o None al cerrarla.

        Mismo patrón que AbrMainWindow: sin datos reales no se tamiza, ni
        siquiera con atención abierta pero sin ABR configurado en ese lado.
        """
        self.stop()
        self.appointment_id = appointment_id
        self.data_current = data
        abr_data = (data or {}).get('ABR') or {}
        self.abr = {'OD': abr_data.get('OD'), 'OI': abr_data.get('OI')}
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
        self._reset_lectura()

    def _reset_lectura(self):
        self.barridos = 0
        self.barra.setRange(0, int(self.sb_barridos.value()))
        self.barra.setValue(0)
        self.lbl_fsp.setText("—")
        self.lbl_ruido.setText("—")
        self.lbl_aceptados.setText("—")
        self._pintar_veredicto(self.resultado.get(self.lado_activo))
        self._pintar_resumen()

    def _pintar_veredicto(self, veredicto):
        colores = {
            'PASA': ("#1b5e20", "#c8e6c9"),
            'REFIERE': ("#b71c1c", "#ffcdd2"),
            None: ("#555", "#eceff1"),
        }
        texto = veredicto or "—"
        if self.corriendo:
            texto = "PROMEDIANDO…"
        color, fondo = colores.get(veredicto, colores[None])
        self.lbl_veredicto.setText(texto)
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

    # ------------------------------------------------------------- captura
    def start(self):
        if self.corriendo or self.abr.get(self.lado_activo) is None:
            if self.abr.get(self.lado_activo) is None:
                self.lbl_resumen.setText(
                    f"Este paciente no tiene ABR configurado en {self.lado_activo}.")
            return
        self.barridos = 0
        self.resultado[self.lado_activo] = None
        self.barra.setRange(0, int(self.sb_barridos.value()))
        self.barra.setValue(0)
        self.corriendo = True
        self._pintar_veredicto(None)
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
        tech = default_settings('ABR')
        tech['transducer'] = self._transducer_keys[self.cb_transducer.currentIndex()]
        tech['artifact_reject_uv'] = float(self.sb_rechazo.value())
        tech['fsp_criterion'] = float(self.sb_criterio.value())
        return tech

    def _tick(self):
        total = int(self.sb_barridos.value())
        self.barridos = min(total, self.barridos + max(1, total // BLOQUES))
        caso = self.abr.get(self.lado_activo)
        contra = self.abr.get('OI' if self.lado_activo == 'OD' else 'OD')
        _, _, _, _, _, meta = ABR_Curve(
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
        fsp = float(meta.get('fsp') or 1.0)
        criterio = float(self.sb_criterio.value())
        self.barra.setValue(int(self.barridos))
        self.lbl_fsp.setText(f"{fsp:.2f}")
        self.lbl_ruido.setText(f"{meta.get('residual_noise_nv', 0):.0f} nV")
        self.lbl_aceptados.setText(f"{int(meta.get('accepted_sweeps') or 0)}")
        self._pintar_veredicto(None)

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
        self._pintar_resumen()

    def submit_report(self):
        """El tamizaje no sube informe.

        Existe para que la ventana principal pueda llamarlo igual que a los
        otros módulos de examen sin preguntar: un AABR no produce curvas
        marcadas ni conclusión, produce PASA o REFIERE y eso lo escribe el
        alumno en su registro.
        """
        return

    def closeEvent(self, event):
        self.stop()
        event.accept()
