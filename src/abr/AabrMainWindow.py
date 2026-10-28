"""Equipo de tamizaje auditivo automatizado (AABR).

Es OTRO equipo, no un modo del ABR: comparte el generador, el criterio de
detección y el ruido del paciente, pero no deja marcar ondas ni buscar
umbrales. Se pone un nivel fijo y el equipo contesta PASA o REFIERE.

Hay UN botón y una sola pantalla. La secuencia la corre el equipo solo, en
el orden en que se toma de verdad, y se detiene donde falla:

    1. Sonda -- la comparte con el equipo de EOA, así que es la misma
       pantalla de probe fit (ver oae/widgets/probe_check.py). Sello flojo:
       se detiene ahí.
    2. Impedancias -- se muestran y listo. En tamizaje el límite es mucho
       más ancho que en el ABR diagnóstico (20 kΩ), así que no frenan nada
       y no se modelan: el ejercicio del AABR no es el montaje.
    3. Estímulo -- promedia mostrando la curva, que sí se ve (los equipos
       de tamizaje la muestran mientras registran), y al ritmo real: unos
       30 segundos cada 900 barridos.
    4. Resultado -- PASA o REFIERE, y el informe.

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

from abr.ABR_generator import ABR_Curve
from abr.AbrAdvanceSettings import TRANSDUCERS, default_settings
from backend.client import BackendClient
from core import iconos, tema
from core.base import context
from core.estado_informe import EstadoInforme
from core.helpers import Preferences
from core.report_autosave import subir_ahora
from oae.generators.base import oae_probe_fit
from oae.widgets.probe_check import ProbeCheckWidget
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox,
                               QFormLayout, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QMainWindow, QPlainTextEdit, QProgressBar,
                               QPushButton, QSpinBox, QVBoxLayout, QWidget)

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

# Impedancia que muestra el equipo. En tamizaje el límite es mucho más
# ancho que en el ABR diagnóstico --hasta 20 kΩ se acepta-- así que acá no
# frena nada ni se modela.
IMPEDANCIA_KOHM = 20.0

# Sello mínimo para dar la sonda por puesta. Por debajo de esto el equipo
# se detiene: entra menos estímulo del que dice el dial.
SELLO_MINIMO = 0.60
SONDA_MS = 2500          # cuánto dura el chequeo de sonda
PASO_MS = 900            # pausa del chequeo de impedancias, para que se vea

# Ritmo del registro. 900 barridos toman unos 30 segundos: entre el rechazo
# de artefacto y las pausas del propio equipo entra cerca de un tercio de
# lo que la tasa promete, así que el tiempo sale de la tasa y no de un
# número fijo. Subir la tasa acorta la prueba, que es la razón por la que
# los equipos de tamizaje estimulan tan rápido.
TICK_MS = 250
EFICIENCIA_BARRIDOS = 0.35

LADOS = ('OD', 'OI')
PASOS = ("Sonda", "Impedancias", "Registro", "Resultado")

# Reglas propias de la ventana (el resto sale de core/tema.py).
EXTRA_QSS = f"""
QFrame#panelConfig {{ background: {tema.TARJETA_ALT}; }}
QPushButton[lado="od"]:checked {{ background: {tema.OD_SUAVE}; border-color: {tema.OD}; color: {tema.OD}; }}
QPushButton[lado="oi"]:checked {{ background: {tema.OI_SUAVE}; border-color: {tema.OI}; color: {tema.OI}; }}
QPushButton[lado] {{ font-weight: 700; padding: 6px 0px; }}
QPushButton[primario="true"] {{
    background: {tema.ACENTO};
    border-color: {tema.ACENTO};
    color: white;
    font-weight: 600;
    padding: 6px 16px;
}}
QPushButton[primario="true"]:hover {{ background: {tema.ACENTO_CLARO}; color: white; }}
QPushButton[primario="true"]:disabled {{
    background: {tema.TARJETA_ALT};
    border-color: {tema.BORDE};
    color: {tema.TEXTO_TENUE};
}}
QCheckBox {{ color: {tema.TEXTO}; spacing: 6px; }}
QCheckBox::indicator {{
    width: 14px; height: 14px; border-radius: 4px;
    border: 1px solid {tema.BORDE_FUERTE}; background: {tema.TARJETA};
}}
QCheckBox::indicator:checked {{ background: {tema.ACENTO}; border-color: {tema.ACENTO}; }}
QLabel[paso="pendiente"] {{ color: {tema.TEXTO_TENUE}; font-weight: 600; }}
QLabel[paso="activo"] {{ color: {tema.ACENTO}; font-weight: 700; }}
QLabel[paso="hecho"] {{ color: {tema.OK}; font-weight: 600; }}
QFrame#pasoLinea {{ background: {tema.BORDE_FUERTE}; border: none; }}
QFrame#panelConfig QLabel#paciente {{ font-weight: 600; color: {tema.TEXTO}; }}
QProgressBar {{
    background: {tema.GRILLA};
    border: none;
    border-radius: 5px;
    min-height: 14px;
    max-height: 14px;
    text-align: center;
    color: {tema.TEXTO_SUAVE};
    font-size: 7.5pt;
}}
QProgressBar::chunk {{ background: {tema.ACENTO_SUAVE}; border-radius: 5px; }}
QProgressBar#barraBarridos {{ min-height: 8px; max-height: 8px; border-radius: 4px; }}
QProgressBar#barraBarridos::chunk {{ background: {tema.ACENTO}; border-radius: 4px; }}
QPlainTextEdit {{
    background: {tema.TARJETA};
    border: 1px solid {tema.BORDE_FUERTE};
    border-radius: 8px;
    padding: 4px;
}}
QPlainTextEdit:focus {{ border-color: {tema.ACENTO}; }}
QFrame#veredicto {{
    background: {tema.TARJETA_ALT};
    border: 1px solid {tema.BORDE};
    border-radius: 10px;
}}
QFrame#veredicto[resultado="pasa"] {{ background: #E3F3EA; border-color: {tema.OK}; }}
QFrame#veredicto[resultado="refiere"] {{ background: #FBE6E3; border-color: {tema.ALERTA}; }}
QLabel#veredictoTexto {{ font-size: 11pt; font-weight: 600; color: {tema.TEXTO_TENUE}; }}
QFrame#veredicto[resultado="pasa"] QLabel#veredictoTexto {{ font-size: 20pt; font-weight: 700; color: {tema.OK}; }}
QFrame#veredicto[resultado="refiere"] QLabel#veredictoTexto {{ font-size: 20pt; font-weight: 700; color: {tema.ALERTA}; }}
QLabel#veredictoLado {{ font-size: 8pt; color: {tema.TEXTO_SUAVE}; }}
"""


def _numero(n, color, relleno, tam=16):
    """Círculo con el número del paso: relleno si es el paso en curso."""
    escala = 2
    pm = QPixmap(tam * escala, tam * escala)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(1.5, 1.5, tam * escala - 3, tam * escala - 3)
    if relleno:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
    else:
        p.setPen(QColor(color))
        p.setBrush(Qt.NoBrush)
    p.drawEllipse(r)
    fuente = QFont()
    fuente.setPixelSize(int(tam * escala * 0.58))
    fuente.setBold(True)
    p.setFont(fuente)
    p.setPen(QColor("white") if relleno else QColor(color))
    p.drawText(r, Qt.AlignCenter, str(n))
    p.end()
    pm.setDevicePixelRatio(escala)
    return pm


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
        self.barridos = 0.0
        self.corriendo = False
        self.paso = 0
        self.sonda_ok = False
        self.technical = default_settings('ABR')
        tema.aplicar_estilo(self, EXTRA_QSS)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer_sonda = QTimer(self)
        self.timer_sonda.setSingleShot(True)
        self.timer_sonda.timeout.connect(self._sonda_lista)
        self.timer_paso = QTimer(self)
        self.timer_paso.setSingleShot(True)
        self.timer_paso.timeout.connect(self._fase_registro)

        self._build()
        self._set_enabled(False)
        self._ir_a(0)

    # ------------------------------------------------------------------ UI
    def _build(self):
        central = QWidget()
        raiz = QHBoxLayout(central)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(10)
        raiz.addWidget(self._panel_config(), 0)

        derecha = QVBoxLayout()
        derecha.setSpacing(8)
        derecha.addLayout(self._cabecera())
        derecha.addWidget(self._pantalla(), 1)
        derecha.addWidget(self._lectura())
        derecha.addWidget(self._informe())
        raiz.addLayout(derecha, 1)
        self.setCentralWidget(central)

    @staticmethod
    def _tarjeta(tipo="true"):
        tarjeta = QFrame()
        tarjeta.setProperty("card", tipo)
        col = QVBoxLayout(tarjeta)
        col.setContentsMargins(12, 10, 12, 12)
        col.setSpacing(6)
        return tarjeta, col

    @staticmethod
    def _seccion(texto):
        lbl = QLabel(texto)
        lbl.setProperty("role", "seccion")
        return lbl

    def _cabecera(self):
        """La fase en curso y el único botón de la prueba."""
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.lbl_pasos = []
        for i, texto in enumerate(PASOS):
            if i:
                linea = QFrame()
                linea.setObjectName("pasoLinea")
                linea.setFixedHeight(2)
                linea.setMinimumWidth(10)
                fila.addWidget(linea, 1)
            marca = QLabel()
            nombre = QLabel(texto)
            nombre.setProperty("paso", "pendiente")
            fila.addWidget(marca)
            fila.addWidget(nombre)
            self.lbl_pasos.append((marca, nombre))
        fila.addSpacing(6)

        # UN botón: la secuencia la corre el equipo. Detener es para
        # abortarla a mitad de camino.
        self.btn_start = QPushButton(" Iniciar")
        self.btn_start.setIcon(iconos.icono_boton("atender", "white", tam=14))
        self.btn_start.setProperty("primario", "true")
        self.btn_start.clicked.connect(self.start)
        self.btn_stop = QPushButton(" Detener")
        self.btn_stop.setIcon(iconos.icono_boton("detener", tema.TEXTO_SUAVE, tam=14))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.abortar)
        fila.addWidget(self.btn_start)
        fila.addWidget(self.btn_stop)
        return fila

    def _panel_config(self):
        panel, col = self._tarjeta()
        panel.setObjectName("panelConfig")
        panel.setFixedWidth(242)

        col.addWidget(self._seccion("PACIENTE"))
        self.lbl_paciente = QLabel("Sin atención abierta")
        self.lbl_paciente.setObjectName("paciente")
        self.lbl_paciente.setWordWrap(True)
        col.addWidget(self.lbl_paciente)
        col.addSpacing(4)

        col.addWidget(self._seccion("OÍDO"))
        fila = QHBoxLayout()
        fila.setSpacing(6)
        grupo = QButtonGroup(self)
        self.btn_lado = {}
        for lado in LADOS:
            btn = QPushButton(lado)
            btn.setCheckable(True)
            btn.setProperty("lado", lado.lower())
            btn.clicked.connect(lambda _=False, l=lado: self._cambiar_lado(l))
            grupo.addButton(btn)
            fila.addWidget(btn, 1)
            self.btn_lado[lado] = btn
        self.btn_lado['OD'].setChecked(True)
        col.addLayout(fila)

        def formulario():
            form = QFormLayout()
            form.setContentsMargins(0, 0, 0, 0)
            form.setHorizontalSpacing(8)
            form.setVerticalSpacing(5)
            form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            return form

        def fila_form(form, texto, widget):
            lbl = QLabel(texto)
            lbl.setProperty("role", "campo")
            # Mismo ancho en los dos bloques: cada QFormLayout mide el suyo.
            lbl.setFixedWidth(74)
            form.addRow(lbl, widget)

        col.addSpacing(4)
        col.addWidget(self._seccion("ESTÍMULO"))
        form = formulario()
        # TRANSDUCERS es {etiqueta: clave} (ver AbrAdvanceSettings).
        self.cb_transducer = QComboBox()
        self.cb_transducer.addItems(list(TRANSDUCERS.keys()))
        self._transducer_keys = list(TRANSDUCERS.values())
        self.cb_transducer.setCurrentIndex(
            self._transducer_keys.index('insert_earphone'))
        fila_form(form, "Transductor", self.cb_transducer)

        self.cb_stim = QComboBox()
        self.cb_stim.addItems(ESTIMULOS)
        fila_form(form, "Estímulo", self.cb_stim)

        self.sb_nivel = QSpinBox()
        self.sb_nivel.setRange(0, 70)
        self.sb_nivel.setSingleStep(5)
        self.sb_nivel.setValue(NIVEL_DB)
        self.sb_nivel.setSuffix(" dB nHL")
        fila_form(form, "Nivel", self.sb_nivel)

        self.sb_tasa = QDoubleSpinBox()
        self.sb_tasa.setRange(5.0, 100.0)
        self.sb_tasa.setDecimals(1)
        self.sb_tasa.setValue(TASA_HZ)
        self.sb_tasa.setSuffix(" /s")
        fila_form(form, "Tasa", self.sb_tasa)
        col.addLayout(form)

        col.addSpacing(4)
        col.addWidget(self._seccion("REGISTRO"))
        form = formulario()
        self.sb_barridos = QSpinBox()
        self.sb_barridos.setRange(200, 20000)
        self.sb_barridos.setSingleStep(500)
        self.sb_barridos.setValue(BARRIDOS_MAX)
        fila_form(form, "Barridos máx.", self.sb_barridos)

        self.sb_criterio = QDoubleSpinBox()
        self.sb_criterio.setRange(1.5, 10.0)
        self.sb_criterio.setDecimals(1)
        self.sb_criterio.setSingleStep(0.1)
        self.sb_criterio.setValue(CRITERIO_FSP)
        fila_form(form, "Criterio FSP", self.sb_criterio)

        self.sb_rechazo = QDoubleSpinBox()
        self.sb_rechazo.setRange(0.0, 100.0)
        self.sb_rechazo.setDecimals(1)
        self.sb_rechazo.setValue(RECHAZO_UV)
        self.sb_rechazo.setSuffix(" µV")
        fila_form(form, "Rechazo", self.sb_rechazo)

        self.sb_pasa_alto = QDoubleSpinBox()
        self.sb_pasa_alto.setRange(0.5, 500.0)
        self.sb_pasa_alto.setDecimals(1)
        self.sb_pasa_alto.setValue(FILTRO_ALTO)
        self.sb_pasa_alto.setSuffix(" Hz")
        fila_form(form, "Pasa-alto", self.sb_pasa_alto)

        self.sb_pasa_bajo = QDoubleSpinBox()
        self.sb_pasa_bajo.setRange(200.0, 6000.0)
        self.sb_pasa_bajo.setDecimals(0)
        self.sb_pasa_bajo.setValue(FILTRO_BAJO)
        self.sb_pasa_bajo.setSuffix(" Hz")
        fila_form(form, "Pasa-bajo", self.sb_pasa_bajo)
        col.addLayout(form)

        self.chk_auto = QCheckBox("Parar al cruzar el criterio")
        self.chk_auto.setChecked(True)
        col.addWidget(self.chk_auto)
        col.addStretch(1)

        # Devuelve los controles de arriba a como vienen de fábrica.
        self.btn_protocolo = QPushButton(" Valores de fábrica")
        self.btn_protocolo.setIcon(iconos.icono_boton("practica", tema.TEXTO_SUAVE, tam=14))
        self.btn_protocolo.clicked.connect(self.restore_protocol)
        col.addWidget(self.btn_protocolo)
        return panel

    def _pantalla(self):
        """Todo en una sola pantalla: sonda a un lado, curva al otro."""
        caja, col = self._tarjeta()
        fila = QHBoxLayout()
        fila.setSpacing(12)

        sonda = QVBoxLayout()
        sonda.setSpacing(4)
        self.probe = ProbeCheckWidget()
        self.probe.setFixedWidth(240)
        # El estado de la sonda lo dice lbl_sonda, con el resultado del
        # chequeo: el del widget se queda en "sin chequear" al detenerlo.
        self.probe.status_label.hide()
        self.probe.layout().setContentsMargins(0, 0, 0, 0)
        sonda.addWidget(self.probe, 1)
        self.lbl_sonda = QLabel("Sonda: sin chequear")
        self.lbl_impedancias = QLabel(
            f"Impedancias: OK (≤ {IMPEDANCIA_KOHM:.0f} kΩ)")
        for lbl in (self.lbl_sonda, self.lbl_impedancias):
            lbl.setProperty("role", "hint")
            sonda.addWidget(lbl)
        fila.addLayout(sonda)

        # La curva SÍ se ve: los equipos de tamizaje la muestran mientras
        # promedian. Lo que no hay es marcado de ondas ni escala de
        # intensidades: una sola curva, al nivel del tamizaje.
        self.plot = pg.PlotWidget()
        self.plot.setBackground(tema.TARJETA)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.hideButtons()
        item = self.plot.getPlotItem()
        item.showGrid(x=True, y=True, alpha=0.35)
        for eje in ("left", "bottom"):
            axis = item.getAxis(eje)
            axis.setPen(pg.mkPen(tema.GRILLA_FUERTE))
            axis.setTextPen(pg.mkPen(tema.TEXTO_SUAVE))
        item.setLabel("bottom", "Tiempo", units="ms", color=tema.TEXTO_SUAVE)
        item.setLabel("left", "µV", color=tema.TEXTO_SUAVE)
        # Sin el prefijo automático el eje dice "µV (x0.001)".
        item.getAxis("left").enableAutoSIPrefix(False)
        # La ventana del registro, también antes de que haya curva.
        item.setXRange(0, 12, padding=0.02)
        self.curva = self.plot.plot(pen=pg.mkPen(tema.color_lado(self.lado_activo), width=2))
        fila.addWidget(self.plot, 1)
        col.addLayout(fila, 1)
        return caja

    def _lectura(self):
        """Barridos, lo que mide el equipo y el veredicto."""
        caja = QWidget()
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)

        datos, col = self._tarjeta()
        avance = QHBoxLayout()
        avance.setSpacing(10)
        self.barra = QProgressBar()
        self.barra.setRange(0, BARRIDOS_MAX)
        self.barra.setTextVisible(False)
        self.barra.setObjectName("barraBarridos")
        self.lbl_barridos = QLabel()
        self.lbl_barridos.setProperty("role", "hint")
        self.barra.valueChanged.connect(self._pintar_barridos)
        avance.addWidget(self.barra, 1)
        avance.addWidget(self.lbl_barridos)
        col.addLayout(avance)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(0)
        self.lbl_fsp = QLabel("—")
        self.lbl_ruido = QLabel("—")
        self.lbl_aceptados = QLabel("—")
        self.lbl_tiempo = QLabel("—")
        for c, (titulo, widget) in enumerate((
                ("FSP", self.lbl_fsp),
                ("RUIDO RESIDUAL", self.lbl_ruido),
                ("ACEPTADOS", self.lbl_aceptados),
                ("TIEMPO", self.lbl_tiempo))):
            grid.addWidget(self._seccion(titulo), 0, c)
            widget.setProperty("role", "dato")
            grid.addWidget(widget, 1, c)
        self.lbl_criterio = QLabel()
        self.lbl_criterio.setProperty("role", "unidad")
        grid.addWidget(self.lbl_criterio, 2, 0)
        col.addLayout(grid)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setProperty("role", "hint")
        col.addWidget(self.lbl_resumen)
        fila.addWidget(datos, 1)

        # El veredicto, grande: es lo único que entrega el equipo.
        self.caja_veredicto = QFrame()
        self.caja_veredicto.setObjectName("veredicto")
        self.caja_veredicto.setFixedWidth(170)
        vcol = QVBoxLayout(self.caja_veredicto)
        vcol.setContentsMargins(10, 10, 10, 10)
        vcol.setSpacing(2)
        self.ico_veredicto = QLabel()
        self.ico_veredicto.setAlignment(Qt.AlignCenter)
        self.lbl_veredicto = QLabel("—")
        self.lbl_veredicto.setObjectName("veredictoTexto")
        self.lbl_veredicto.setAlignment(Qt.AlignCenter)
        self.lbl_veredicto_lado = QLabel()
        self.lbl_veredicto_lado.setObjectName("veredictoLado")
        self.lbl_veredicto_lado.setAlignment(Qt.AlignCenter)
        vcol.addStretch(1)
        vcol.addWidget(self.ico_veredicto)
        vcol.addWidget(self.lbl_veredicto)
        vcol.addWidget(self.lbl_veredicto_lado)
        vcol.addStretch(1)
        fila.addWidget(self.caja_veredicto)
        self._pintar_veredicto(None)
        self._pintar_criterio()
        self.sb_criterio.valueChanged.connect(self._pintar_criterio)
        return caja

    def _informe(self):
        """Un tamizaje no informa morfología, informa PASA o REFIERE. Pero
        algo hay que dejar escrito: sin esto el alumno tamizaba y no quedaba
        nada --ni el resultado, ni con qué nivel, ni qué decidió-- cuando se
        cerraba la atención."""
        caja, col = self._tarjeta()
        cab = QHBoxLayout()
        cab.setSpacing(8)
        cab.addWidget(self._seccion("INFORME"))
        cab.addStretch(1)
        self.cb_informe = {}
        for lado in LADOS:
            pill = QLabel(lado)
            tema.pastilla_lado(pill, lado)
            combo = QComboBox()
            combo.addItems(["No realizado", "PASA", "REFIERE"])
            combo.setMinimumWidth(120)
            cab.addWidget(pill)
            cab.addWidget(combo)
            cab.addSpacing(6)
            self.cb_informe[lado] = combo
        col.addLayout(cab)

        self.lbl_condiciones = QLabel("")
        self.lbl_condiciones.setWordWrap(True)
        self.lbl_condiciones.setProperty("role", "hint")
        col.addWidget(self.lbl_condiciones)

        textos = QHBoxLayout()
        textos.setSpacing(8)
        self.txt_observaciones = QPlainTextEdit()
        self.txt_observaciones.setPlaceholderText("Observaciones del registro")
        self.txt_conducta = QPlainTextEdit()
        self.txt_conducta.setPlaceholderText("Conducta")
        for txt in (self.txt_observaciones, self.txt_conducta):
            txt.setFixedHeight(50)
            textos.addWidget(txt)
        col.addLayout(textos)
        # Se guarda solo (core/report_autosave.py); acá se ve si quedó.
        self.estado_informe = EstadoInforme()
        col.addWidget(self.estado_informe)
        return caja

    # -------------------------------------------------------------- pasos
    def _ir_a(self, paso):
        """Pinta el indicador de fase. No es navegación: la secuencia la
        mueve el equipo, no el alumno."""
        self.paso = paso
        for i, (marca, nombre) in enumerate(self.lbl_pasos):
            if i < paso:
                marca.setPixmap(iconos.pixmap("check", tema.OK, 16))
                estado = "hecho"
            else:
                activo = i == paso
                marca.setPixmap(_numero(i + 1, tema.ACENTO if activo else tema.TEXTO_TENUE, activo))
                estado = "activo" if activo else "pendiente"
            nombre.setProperty("paso", estado)
            tema.repintar(nombre)

    # ------------------------------------------------------ la secuencia
    def start(self):
        """El único botón: corre la prueba entera, en orden."""
        if self.corriendo or self.data_current is None:
            return
        if self.abr.get(self.lado_activo) is None:
            self.lbl_resumen.setText(
                f"Este paciente no tiene ABR configurado en {self.lado_activo}.")
            return
        self.corriendo = True
        self.sonda_ok = False
        self.resultado[self.lado_activo] = None
        self.barridos = 0.0
        self.barra.setRange(0, int(self.sb_barridos.value()))
        self.barra.setValue(0)
        self._pintar_barridos()
        self.curva.clear()
        self.lbl_tiempo.setText("0 s")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._pintar_veredicto(None)
        self.lbl_resumen.setText("")
        self._fase_sonda()

    def abortar(self):
        """Detener a mano, sin veredicto: la prueba no se tomó."""
        self._detener("Detenido por el operador: la prueba no se completó.")

    def _detener(self, motivo=""):
        """Corta la secuencia donde esté y dice por qué."""
        self.timer.stop()
        self.timer_sonda.stop()
        self.timer_paso.stop()
        self.probe.stop()
        self.corriendo = False
        if hasattr(self, 'btn_start'):
            self.btn_start.setEnabled(self.data_current is not None)
            self.btn_stop.setEnabled(False)
        if motivo:
            self.lbl_resumen.setText(motivo)

    # La ventana principal llama stop() al cerrar la atención.
    def stop(self):
        self._detener()

    # ---- 1. sonda
    def _fase_sonda(self):
        self._ir_a(0)
        self.lbl_sonda.setText("Sonda: chequeando…")
        self.probe.start(60.0, oae_probe_fit(self.eoas.get(self.lado_activo)))
        self.timer_sonda.start(SONDA_MS)

    def _sonda_lista(self):
        sello = float(getattr(self.probe, 'fit_quality', 0.0))
        self.probe.stop()
        self.sonda_ok = sello >= SELLO_MINIMO
        if not self.sonda_ok:
            self.lbl_sonda.setText(f"Sonda: sello {sello * 100:.0f} %")
            self._detener("Detenido en el chequeo de sonda: sello insuficiente.")
            return
        self.lbl_sonda.setText(f"Sonda: OK ({sello * 100:.0f} %)")
        self._fase_impedancias()

    # ---- 2. impedancias
    def _fase_impedancias(self):
        """Se muestran y listo: en tamizaje el límite es ancho y no frenan."""
        self._ir_a(1)
        self.lbl_impedancias.setText(
            f"Impedancias: OK (≤ {IMPEDANCIA_KOHM:.0f} kΩ)")
        # Una pausa corta para que el chequeo se vea, como en el equipo.
        self.timer_paso.start(PASO_MS)

    # ---- 3. registro
    def _fase_registro(self):
        self._ir_a(2)
        self.timer.start(TICK_MS)

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
        return tech

    def _barridos_por_tick(self):
        """Cuántos barridos entran en un tick, al ritmo real del equipo."""
        return float(self.sb_tasa.value()) * EFICIENCIA_BARRIDOS * (TICK_MS / 1000.0)

    def _segundos(self):
        """Cuánto lleva este registro en el equipo real."""
        tasa = float(self.sb_tasa.value()) * EFICIENCIA_BARRIDOS
        return self.barridos / tasa if tasa else 0.0

    def _tick(self):
        total = int(self.sb_barridos.value())
        self.barridos = min(float(total), self.barridos + self._barridos_por_tick())
        caso = self.abr.get(self.lado_activo)
        contra = self.abr.get('OI' if self.lado_activo == 'OD' else 'OD')
        try:
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
        except Exception as exc:
            # Un dato del caso que el generador no puede leer: se corta acá
            # en vez de reventar cada 250 ms sin llegar nunca al veredicto.
            print(f"AABR: no se pudo generar el registro: {exc!r}")
            self._detener("Detenido: el caso no tiene datos de ABR válidos para este oído.")
            return
        self.curva.setData(np.asarray(x), np.asarray(y))
        fsp = float(meta.get('fsp') or 1.0)
        criterio = float(self.sb_criterio.value())
        self.barra.setValue(int(self.barridos))
        self.lbl_fsp.setText(f"{fsp:.2f}")
        self.lbl_ruido.setText(f"{meta.get('residual_noise_nv', 0):.0f} nV")
        self.lbl_aceptados.setText(f"{int(meta.get('accepted_sweeps') or 0)}")
        self.lbl_tiempo.setText(f"{self._segundos():.0f} s")

        if fsp >= criterio and self.chk_auto.isChecked():
            self._cerrar('PASA', fsp)
        elif self.barridos >= total:
            self._cerrar('PASA' if fsp >= criterio else 'REFIERE', fsp)

    def _cerrar(self, veredicto, fsp):
        self._detener()
        self._ir_a(3)
        self.resultado[self.lado_activo] = {
            'veredicto': veredicto,
            'barridos': int(round(self.barridos)),
            'segundos': int(round(self._segundos())),
            'fsp': fsp,
            'nivel': int(self.sb_nivel.value()),
            'estimulo': self.cb_stim.currentText(),
        }
        # El informe se precarga con lo que dio, y queda EDITABLE: informar
        # distinto de lo que salió también es un error, y corregirlo es
        # parte del ejercicio.
        combo = self.cb_informe.get(self.lado_activo)
        if combo is not None:
            idx = combo.findText(veredicto)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        self._pintar_veredicto(veredicto)
        self._pintar_condiciones()
        self._pintar_resumen()

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
        for w in (self.btn_start, *self.btn_lado.values()):
            w.setEnabled(on)

    def la_super(self, data, appointment_id=None):
        """Caso del paciente en atención, o None al cerrarla.

        Mismo patrón que AbrMainWindow: sin datos reales no se tamiza, ni
        siquiera con atención abierta pero sin ABR configurado en ese lado.
        """
        self._detener()
        self.appointment_id = appointment_id
        self.data_current = data
        abr_data = (data or {}).get('ABR') or {}
        eoas_data = (data or {}).get('EOAS') or {}
        self.abr = {'OD': abr_data.get('OD'), 'OI': abr_data.get('OI')}
        self.eoas = {'OD': eoas_data.get('OD'), 'OI': eoas_data.get('OI')}
        self.resultado = {'OD': None, 'OI': None}
        for combo in self.cb_informe.values():
            combo.setCurrentIndex(0)
        self.txt_observaciones.setPlainText("")
        self.txt_conducta.setPlainText("")
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
        self._ir_a(0)

    def _cambiar_lado(self, lado):
        if lado == self.lado_activo:
            return
        self._detener()
        self.lado_activo = lado
        self.btn_lado[lado].setChecked(True)
        self.curva.setPen(pg.mkPen(tema.color_lado(lado), width=2))
        # Oído nuevo, sonda nueva: la oliva se saca y se pone del otro lado.
        self.sonda_ok = False
        self._reset_lectura()
        self._ir_a(0)

    def _reset_lectura(self):
        self.barridos = 0.0
        self.barra.setRange(0, int(self.sb_barridos.value()))
        self.barra.setValue(0)
        self._pintar_barridos()
        self.curva.clear()
        for lbl in (self.lbl_fsp, self.lbl_ruido, self.lbl_aceptados,
                    self.lbl_tiempo):
            lbl.setText("—")
        self.lbl_sonda.setText("Sonda: sin chequear")
        # El veredicto, no el dict del resultado: con el dict revienta
        # (unhashable) al volver a un oido ya tamizado.
        self._pintar_veredicto((self.resultado.get(self.lado_activo) or {}).get('veredicto'))
        self._pintar_condiciones()
        self._pintar_resumen()

    def _pintar_veredicto(self, veredicto):
        icono, color = {'PASA': ("check", tema.OK),
                        'REFIERE': ("x", tema.ALERTA)}.get(veredicto, ("onda_check", tema.TEXTO_TENUE))
        self.ico_veredicto.setPixmap(iconos.pixmap(icono, color, 30))
        self.lbl_veredicto.setText(veredicto or "Sin resultado")
        self.lbl_veredicto_lado.setText(f"Oído {'derecho' if self.lado_activo == 'OD' else 'izquierdo'}")
        self.caja_veredicto.setProperty("resultado", (veredicto or "").lower())
        for w in (self.caja_veredicto, self.lbl_veredicto):
            tema.repintar(w)

    def _pintar_barridos(self, *_):
        self.lbl_barridos.setText(f"{self.barra.value()} de {self.barra.maximum()} barridos")

    def _pintar_criterio(self, *_):
        self.lbl_criterio.setText(f"criterio ≥ {self.sb_criterio.value():.1f}")

    def _pintar_resumen(self):
        partes = []
        for lado in LADOS:
            r = self.resultado.get(lado)
            partes.append(
                f"{lado}: {r['veredicto']} ({r['barridos']} barridos, {r['segundos']} s)"
                if r else f"{lado}: sin tamizar")
        self.lbl_resumen.setText(" · ".join(partes))

    def _pintar_condiciones(self):
        """Las condiciones se escriben solas: son del equipo, no del alumno."""
        partes = []
        for lado in LADOS:
            r = self.resultado.get(lado)
            if r:
                partes.append(f"{lado}: {r['estimulo']} a {r['nivel']} dB nHL, "
                              f"{r['barridos']} barridos en {r['segundos']} s, "
                              f"FSP {r['fsp']:.2f}")
        partes.append(f"impedancias ≤ {IMPEDANCIA_KOHM:.0f} kΩ")
        self.lbl_condiciones.setText(" · ".join(partes))

    # ------------------------------------------------------------- informe
    def report_data(self):
        """Lo que se guarda del tamizaje.

        `resultados` sale de los combos, no de lo que midió el equipo: si el
        alumno informa otra cosa, se guarda lo que informó. Las condiciones
        sí salen del registro, porque es el procedimiento lo que se evalúa.
        """
        resultados = {}
        for lado in LADOS:
            combo = self.cb_informe.get(lado)
            informado = combo.currentText() if combo is not None else 'No realizado'
            medido = self.resultado.get(lado) or {}
            resultados[lado] = {
                'veredicto': informado,
                'nivel': medido.get('nivel'),
                'estimulo': medido.get('estimulo'),
                'barridos': medido.get('barridos'),
                'segundos': medido.get('segundos'),
                'fsp': medido.get('fsp'),
            }
        tech = self._technical()
        return {
            'resultados': resultados,
            'tecnica': {
                'transductor': tech.get('transducer'),
                'criterio_fsp': tech.get('fsp_criterion'),
                'rechazo_uv': tech.get('artifact_reject_uv'),
                'tasa': float(self.sb_tasa.value()),
                'banda_hz': [float(self.sb_pasa_alto.value()),
                             float(self.sb_pasa_bajo.value())],
                'barridos_maximos': int(self.sb_barridos.value()),
                'impedancia_kohm': IMPEDANCIA_KOHM,
                'sello_sonda_ok': bool(self.sonda_ok),
            },
            'hallazgos': self.txt_observaciones.toPlainText(),
            'conclusion': self.txt_conducta.toPlainText(),
        }

    def restore_report(self, data):
        """Retomar la atención: vuelve el tamizaje ya guardado (ver
        core/report_autosave.py), si todavía no se tamizó nada."""
        if self.data_current is None or any(self.resultado.values()):
            return False
        recuperado = False
        for lado, r in (data.get('resultados') or {}).items():
            if lado not in self.resultado or not r:
                continue
            combo = self.cb_informe.get(lado)
            if combo is not None:
                idx = combo.findText(r.get('veredicto') or '')
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            # Solo se reconstruye lo medido si hubo registro (barridos):
            # 'veredicto' es lo que el alumno informó en el combo.
            if r.get('barridos') is not None and r.get('fsp') is not None:
                self.resultado[lado] = {
                    'veredicto': r.get('veredicto'),
                    'barridos': r.get('barridos'),
                    'segundos': r.get('segundos'),
                    'fsp': r.get('fsp'),
                    'nivel': r.get('nivel'),
                    'estimulo': r.get('estimulo'),
                }
                recuperado = True
        if data.get('hallazgos'):
            self.txt_observaciones.setPlainText(data['hallazgos'])
            recuperado = True
        if data.get('conclusion'):
            self.txt_conducta.setPlainText(data['conclusion'])
            recuperado = True
        self._pintar_veredicto((self.resultado.get(self.lado_activo) or {}).get('veredicto'))
        self._pintar_condiciones()
        self._pintar_resumen()
        return recuperado

    def submit_report(self):
        """Sube el informe del tamizaje al cerrar la atención.

        Mismo camino que los otros módulos de examen (ver
        AbrMainWindow.submit_report): best-effort, sin imágenes --un
        tamizaje no informa curvas-- y con tipo 'AABR'.
        """
        job = self.report_job()
        if job is None:
            return True
        client = BackendClient(Preferences().get("BACKEND_URL"),
                               context.get_resource('json/session.json'))
        ok, error = subir_ahora(job, client)
        if not ok:
            print(f"AABR: no se pudo subir el informe: {error}")
        return ok

    def report_job(self):
        """El informe tal como se sube (ver core/report_autosave.py), o None."""
        if not self.data_login:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        data = self.report_data()
        vacio = all(r['veredicto'] == 'No realizado'
                    for r in data['resultados'].values())
        if vacio and not data['hallazgos'].strip() and not data['conclusion'].strip():
            return None
        return {"appointment_id": appointment_id, "tipo": 'AABR', "data": data,
                "images": None}

    def closeEvent(self, event):
        self._detener()
        event.accept()
