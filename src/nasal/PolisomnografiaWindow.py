"""La poligrafía y la polisomnografía de LabSim (H31 y cap. 38 del libro),
demo interna del Laboratorio de sueño.

Como se hace: el alumno elige el estudio (polisomnografía en el laboratorio
o poligrafía en la casa), monta los sensores y registra la noche. En el
laboratorio la noche corre (entera en 15 min, o ×60 a ×300; con pausa y
"Hasta la mañana"):
desde la sala de control ve al paciente por la ventanilla y la cámara
infrarroja del techo (nasal/pieza_vista.py) y puede entrar a
acomodarlo de espaldas o de lado (sueno.acomodar: se despierta un rato y la
noche se rehace desde ahí). En la casa no hay técnico: llega entera. Después
revisa el registro como en el programa del equipo: arriba la noche entera
(hipnograma en la polisomnografía, posición, eventos y SpO2), abajo la
ventana de 30 s a 5 min con cada canal. El programa propone una puntuación
automática con sus errores (sin EEG no ve despertares, se le escapa alguna
hipopnea, confunde alguna central, ve apneas donde la cánula se soltó), y el
alumno la corrige: cambia el tipo, borra, agrega con la selección y excluye
los tramos sin señal. Los índices salen de SU puntuación con la regla de
hipopnea que elija; la gravedad la escribe él.

La noche es la del modelo del libro (nasal/sueno.py): la misma para el mismo
caso. Lo que de verdad pasó (los eventos del modelo y los índices del
capítulo) va a "Lo que el equipo no sabe" (docente) y al log, con prefijo
psg_. El informe POLISOMNOGRAFIA guarda el montaje, la puntuación y los
tramos excluidos: al retomar la atención la noche se rehace igual.

Sin `cases.data['SUENO']` la noche es normal (nasal/normales.py).
"""

import os
import time

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QMainWindow, QPlainTextEdit,
                               QPushButton, QScrollArea, QSplitter, QTabWidget, QVBoxLayout, QWidget)

from core import hilos, tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import sesion as sesion_nasal
from nasal import sueno as Z
from nasal.equipos import PERMISOS_DOCENTE, QSS_NASAL, Tabla, num
from nasal.graficos import exportar
from nasal.pieza_vista import VistaPieza
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta

VENTANAS = ((30, '30 s'), (120, '2 min'), (300, '5 min'))
# La noche corre en la PSG (el técnico la vigila y puede acomodar al paciente).
# 0 = la noche entera en NOCHE_EN_MIN minutos reales, sea cual sea su largo
# (≈ ×31 en una noche de 470 min); el resto, factores fijos para ir más rápido.
NOCHE_EN_MIN = 15
VELOCIDADES = ((0, f'Noche en {NOCHE_EN_MIN} min'), (60, '×60'), (120, '×120'), (300, '×300'))
TIC_MS = 200
NOMBRE_POS = {'supino': 'de espaldas', 'izquierda': 'sobre el lado izquierdo', 'derecha': 'sobre el lado derecho'}
COLOR_TIPO = {'ao': '#C62F3A', 'am': '#8E44AD', 'ac': '#2F5D9E', 'h': '#D98E04', 'rera': '#21796C'}
ABREV_TIPO = {'ao': 'AO', 'am': 'AM', 'ac': 'AC', 'h': 'H', 'rera': 'RERA'}
COLOR_POS = {'supino': '#C62F3A', 'izquierda': '#21796C', 'derecha': '#2F5D9E'}
GRAVEDADES = (('normal', 'Normal'), ('leve', 'Leve'), ('moderada', 'Moderada'), ('grave', 'Grave'))
# Orden y alto relativo de los canales en la ventana de detalle.
# (clave, rótulo, rango fijo del eje: así se ve cuánto cae la amplitud).
CANALES = (('eeg', 'EEG', 1.3), ('eog', 'EOG', 1.3), ('emg', 'EMG', 1.2), ('termico', 'Térmico', 1.8),
           ('canula', 'Presión nasal', 1.8), ('torax', 'Tórax', 2.2), ('abd', 'Abdomen', 2.2),
           ('spo2', 'SpO₂ %', None), ('ron', 'Ronquido', 1.2))


class EjeHora(pg.AxisItem):
    """Segundos desde que se apagó la luz, como hh:mm:ss."""

    def tickStrings(self, values, scale, spacing):
        return [hhmm(v) for v in values]


def n(v, d=1):
    return '—' if v is None else num(v, d)


def hhmm(seg):
    seg = int(seg)
    return f'{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}'


class SesionSueno:
    def __init__(self, data, appointment_id):
        self.caso = Z.desde_caso(data)
        self.appointment_id = appointment_id

    @property
    def hay_paciente(self):
        return self.caso is not None

    @property
    def sueno(self):
        return self.caso['sueno']


# ── La noche entera ─────────────────────────────────────────────────────────

class Noche:
    """Arriba: hipnograma (PSG), posición, eventos y SpO2 de toda la noche,
    en horas. Un clic lleva la ventana de detalle ahí; la selección gris
    sirve para excluir tramos largos."""

    def __init__(self, al_clic):
        self.widget = pg.GraphicsLayoutWidget()
        self.widget.setBackground(tema.TARJETA)
        # Chico a propósito: a 1366×768 el detalle (9 canales) necesita el
        # resto del alto, si no el SpO₂ y el ronquido quedan fuera.
        self.widget.setMinimumHeight(175)
        self.al_clic = al_clic
        self.p_etapa = self._plot('Etapa')
        self.p_etapa.getAxis('left').setTicks([[(4, 'W'), (3, 'R'), (2, 'N1'), (1, 'N2'), (0, 'N3')]])
        self.widget.nextRow()
        self.p_ev = self._plot('Eventos')
        self.p_ev.getAxis('left').setTicks([[]])
        self.widget.nextRow()
        self.p_sp = self._plot('SpO₂')
        for p in (self.p_ev, self.p_sp):
            p.setXLink(self.p_etapa)
        # Las horas, una sola vez (abajo, en la SpO₂): el alto va a los trazos.
        for p in (self.p_etapa, self.p_ev):
            p.getAxis('bottom').setStyle(showValues=False)
            p.getAxis('bottom').setHeight(4)
        self.widget.ci.layout.setRowStretchFactor(0, 3)
        self.widget.ci.layout.setRowStretchFactor(1, 2)
        self.widget.ci.layout.setRowStretchFactor(2, 2)
        self.ventana = {}
        self.seleccion = pg.LinearRegionItem(values=(0, 0.5), brush=pg.mkBrush(120, 120, 120, 50),
                                             pen=pg.mkPen(tema.TEXTO_TENUE))
        self.seleccion.setVisible(False)
        self.p_ev.addItem(self.seleccion)
        self.widget.scene().sigMouseClicked.connect(self._clic)

    def _plot(self, rotulo):
        p = self.widget.addPlot()
        p.setMenuEnabled(False)
        p.hideButtons()
        p.getViewBox().setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=False, alpha=0.2)
        p.getAxis('left').setWidth(34)
        for eje in ('left', 'bottom'):
            p.getAxis(eje).setPen(pg.mkPen(tema.BORDE_FUERTE))
            p.getAxis(eje).setTextPen(pg.mkPen(tema.TEXTO_TENUE))
        return p

    def _clic(self, evento):
        if evento.button() != Qt.MouseButton.LeftButton:
            return
        for p in (self.p_etapa, self.p_ev, self.p_sp):
            if p.sceneBoundingRect().contains(evento.scenePos()):
                x = p.getViewBox().mapSceneToView(evento.scenePos()).x()
                self.al_clic(x * 3600)
                return

    def dibujar(self, S, eventos, excluidos, t0, dur, hasta=None):
        """`hasta`: mientras la noche corre, lo que va registrado (s)."""
        for p in (self.p_etapa, self.p_ev, self.p_sp):
            for item in list(p.items):
                if item is not self.seleccion:
                    p.removeItem(item)
        if S is None:
            return
        horas = S['N'] / 3600
        for p in (self.p_etapa, self.p_ev, self.p_sp):
            p.setXRange(0, horas, padding=0)
        hasta = S['N'] if hasta is None else max(0, min(S['N'], int(hasta)))
        if hasta <= 0:
            return
        if S['estudio'] == 'psg':
            self.p_etapa.getAxis('left').setTicks([[(4, 'W'), (3, 'R'), (2, 'N1'), (1, 'N2'), (0, 'N3')]])
            xs, ys = [], []
            for e, a, b in S['seg']:
                if a >= hasta:
                    break
                xs += [a / 3600, min(b, hasta) / 3600]
                ys += [Z.ORDEN[e], Z.ORDEN[e]]
            self.p_etapa.plot(xs, ys, pen=pg.mkPen(tema.TEXTO, width=1.4))
            self.p_etapa.setYRange(-0.5, 4.5, padding=0)
        else:
            self.p_etapa.getAxis('left').setTicks([[(1, 'Sup'), (0, 'Lat')]])
            xs, ys = [], []
            for a, b, p in Z.tramos_posicion(S):
                y = 1 if p == 'supino' else 0
                xs += [a / 3600, b / 3600]
                ys += [y, y]
            self.p_etapa.plot(xs, ys, pen=pg.mkPen(tema.TEXTO, width=1.4))
            self.p_etapa.setYRange(-0.5, 1.5, padding=0)
        # La posición (la de verdad, con los acomodos), como una franja de
        # color bajo el hipnograma; cada acomodo, una línea.
        for a, b, p in Z.tramos_posicion(S):
            if a >= hasta:
                break
            color = QColor(COLOR_POS[p])
            color.setAlpha(45)
            r = pg.LinearRegionItem(values=(a / 3600, min(b, hasta) / 3600), movable=False,
                                    brush=pg.mkBrush(color))
            r.setZValue(-20)
            for linea in r.lines:
                linea.setPen(pg.mkPen(None))
            self.p_etapa.addItem(r)
        for a, b in excluidos:
            for p in (self.p_ev, self.p_sp):
                r = pg.LinearRegionItem(values=(a / 3600, b / 3600), movable=False,
                                        brush=pg.mkBrush(90, 90, 90, 70))
                r.setZValue(-10)
                p.addItem(r)
        for tipo, color in COLOR_TIPO.items():
            xs = [e['t'] / 3600 for e in eventos if e['tipo'] == tipo]
            if xs:
                y = {'ao': 4, 'am': 3, 'ac': 2, 'h': 1, 'rera': 0}[tipo]
                self.p_ev.plot(xs, [y] * len(xs), pen=None, symbol='|', symbolSize=9,
                               symbolPen=pg.mkPen(color, width=1.2))
        self.p_ev.setYRange(-0.8, 4.8, padding=0)
        for t, _p in S.get('acomodos') or ():
            if t < hasta:
                self.p_etapa.addItem(pg.InfiniteLine(t / 3600, pen=pg.mkPen(tema.ACENTO, width=1.5)))
        paso = 30
        self.p_sp.plot([k / 3600 for k in range(0, hasta, paso)],
                       [min(S['sp'][k:min(k + paso, hasta)]) for k in range(0, hasta, paso)],
                       pen=pg.mkPen(tema.OI, width=1))
        self.p_sp.setYRange(min(80, min(S['sp'][:hasta]) - 1), 100, padding=0)
        self.p_sp.getAxis('left').setTicks([[(90, '90')]])
        r = pg.LinearRegionItem(values=(t0 / 3600, (t0 + dur) / 3600), movable=False,
                                brush=pg.mkBrush(QColor(tema.ACENTO).lighter(150)))
        r.setZValue(-5)
        self.p_ev.addItem(r)

    def exportar(self, ruta):
        exportador = pg.exporters.ImageExporter(self.widget.scene())
        exportador.parameters()['width'] = max(1000, int(self.widget.width() * 2))
        exportador.export(ruta)


# ── La ventana de detalle ───────────────────────────────────────────────────

class Detalle:
    """Los canales de la ventana, uno bajo otro, con los eventos sombreados y
    la selección (para agregar un evento o excluir un tramo)."""

    def __init__(self, al_clic):
        self.widget = pg.GraphicsLayoutWidget()
        self.widget.setBackground(tema.TARJETA)
        self.al_clic = al_clic
        self.plots = {}
        primero = None
        self.rangos = {}
        for clave, rotulo, rango in CANALES:
            self.widget.addLabel(rotulo, color=tema.TEXTO_TENUE, size='8pt', justify='right')
            ejes = {'bottom': EjeHora(orientation='bottom')} if clave == 'ron' else {}
            p = self.widget.addPlot(axisItems=ejes)
            p.setMenuEnabled(False)
            p.hideButtons()
            p.getViewBox().setMouseEnabled(x=False, y=False)
            p.getAxis('left').setWidth(30)
            p.getAxis('left').setTicks([[(90, '90')]] if clave == 'spo2' else [[]])
            if clave != 'ron':
                p.getAxis('bottom').setStyle(showValues=False)
                p.getAxis('bottom').setHeight(2)
            self.rangos[clave] = rango
            for eje in ('left', 'bottom'):
                p.getAxis(eje).setPen(pg.mkPen(tema.BORDE_FUERTE))
                p.getAxis(eje).setTextPen(pg.mkPen(tema.TEXTO_TENUE))
            if primero is None:
                primero = p
            else:
                p.setXLink(primero)
            self.plots[clave] = p
            self.widget.nextRow()
        self.widget.ci.layout.setColumnFixedWidth(0, 92)
        # El ronquido lleva además el eje de las horas: sin un mínimo propio
        # queda en una línea (y la SpO₂ casi plana).
        self.plots['ron'].setMinimumHeight(46)
        self.plots['spo2'].setMinimumHeight(28)
        self.widget.ci.layout.setVerticalSpacing(0)
        # Lo que piden los 9 canales: el divisor no lo achica más (si no, se
        # cortan los de abajo sin aviso).
        self.widget.setMinimumHeight(250)
        self.seleccion = pg.LinearRegionItem(values=(0, 10), brush=pg.mkBrush(120, 120, 120, 45),
                                             pen=pg.mkPen(tema.TEXTO, width=1.2))
        self.plots['canula'].addItem(self.seleccion)
        self.widget.scene().sigMouseClicked.connect(self._clic)

    def _clic(self, evento):
        if evento.button() != Qt.MouseButton.LeftButton:
            return
        for p in self.plots.values():
            if p.sceneBoundingRect().contains(evento.scenePos()):
                self.al_clic(p.getViewBox().mapSceneToView(evento.scenePos()).x())
                return

    def dibujar(self, sen, eventos, excluidos, t0, dur, elegido):
        for clave, p in self.plots.items():
            for item in list(p.items):
                if item is not self.seleccion:
                    p.removeItem(item)
            p.setXRange(t0, t0 + dur, padding=0)
        if sen is None:
            return
        xs = sen['t']
        for clave, p in self.plots.items():
            y = sen.get(clave)
            if y is None:
                txt = pg.TextItem('sin sensor', color=tema.TEXTO_TENUE, anchor=(0.5, 0.5))
                txt.setPos(t0 + dur / 2, 0)
                p.addItem(txt)
                p.setYRange(-1, 1, padding=0)
                continue
            if not y:      # la noche que corre todavía no llega aquí
                p.setYRange(-1, 1, padding=0)
                continue
            p.plot(xs, y, pen=pg.mkPen(tema.TEXTO if clave != 'spo2' else tema.OI, width=1))
            if clave == 'spo2':
                p.setYRange(min(85, min(y) - 1), 100, padding=0)
            else:
                p.setYRange(-self.rangos[clave], self.rangos[clave], padding=0)
        for e in eventos:
            if e['t'] + e['dur'] < t0 or e['t'] > t0 + dur:
                continue
            color = QColor(COLOR_TIPO[e['tipo']])
            color.setAlpha(110 if e is elegido else 45)
            for clave in ('termico', 'canula', 'torax', 'abd'):
                r = pg.LinearRegionItem(values=(e['t'], e['t'] + e['dur']), movable=False, brush=pg.mkBrush(color))
                for linea in r.lines:
                    linea.setPen(pg.mkPen(COLOR_TIPO[e['tipo']], width=2 if e is elegido else 0.8))
                r.setZValue(-10)
                self.plots[clave].addItem(r)
            txt = pg.TextItem(ABREV_TIPO[e['tipo']], color=COLOR_TIPO[e['tipo']], anchor=(0, 1))
            txt.setPos(e['t'], self.rangos['termico'])
            self.plots['termico'].addItem(txt)
        for a, b in excluidos:
            if b < t0 or a > t0 + dur:
                continue
            for p in self.plots.values():
                r = pg.LinearRegionItem(values=(max(a, t0), min(b, t0 + dur)), movable=False,
                                        brush=pg.mkBrush(90, 90, 90, 60))
                r.setZValue(-12)
                p.addItem(r)


# ── La ventana ──────────────────────────────────────────────────────────────

class PolisomnografiaWindow(QMainWindow):
    TITULO = 'Polisomnografía y poligrafía'
    TIPO = 'POLISOMNOGRAFIA'
    EQUIPO = 'psg'

    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self.sesion = None
        self.data_caso = None
        self.appointment_id = None
        self.S = None              # la noche registrada
        self.montaje = []
        self.eventos = []          # la puntuación del alumno: {'t', 'dur', 'tipo', 'auto'}
        self.excluidos = []        # [(desde, hasta)] s
        self.t0 = 0
        self.elegido = None
        self.tarea = None
        # La noche en la PSG corre: hasta dónde va (s; None = sin noche) y si
        # está corriendo. Llegada la mañana, t_actual = N.
        self.t_actual = None
        self.corriendo = False
        self.recalculando = False
        self.setWindowTitle(self.TITULO)
        self._construir()
        self.timer = QTimer(self)
        self.timer.setInterval(TIC_MS)
        self.timer.timeout.connect(self._tic)
        self.la_super(None)

    # --- UI -------------------------------------------------------------

    def _construir(self):
        central = QWidget()
        tema.aplicar_estilo(central, QSS_NASAL)
        self.setCentralWidget(central)
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(10)
        fila = QHBoxLayout()
        self.lbl_mensaje = etiqueta('', rol='hint')
        self.lbl_mensaje.setWordWrap(True)
        fila.addWidget(self.lbl_mensaje, 1)
        self.pill_estudio = Pastilla('', 'neutro')
        fila.addWidget(self.pill_estudio)
        raiz.addLayout(fila)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)
        raiz.addLayout(cuerpo, 1)
        izquierda = QWidget()
        izq = QVBoxLayout(izquierda)
        izq.setContentsMargins(0, 0, 0, 0)
        izq.setSpacing(10)
        self._panel_estudio(izq)
        self._panel_sala(izq)
        self._panel_puntuacion(izq)
        izq.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidget(izquierda)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        desplazable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        desplazable.setFixedWidth(300)
        cuerpo.addWidget(desplazable)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._pantalla(), 'Registro')
        self.tabs.addTab(self._pestana_informe(), 'Informe')
        self.verdad = None
        if self.es_docente:
            self.verdad = etiqueta('', rol='hint')
            self.verdad.setWordWrap(True)
            self.verdad.setTextFormat(Qt.TextFormat.RichText)
            self.verdad.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            caja = QScrollArea()
            caja.setWidgetResizable(True)
            caja.setWidget(self.verdad)
            self.tabs.addTab(caja, 'Lo que el equipo no sabe')
        cuerpo.addWidget(self.tabs, 1)

    def _boton(self, texto, accion, principal=False):
        b = QPushButton(texto)
        if principal:
            b.setObjectName('btnPrincipal')
        b.clicked.connect(lambda _c=False: accion())
        return b

    def _panel_estudio(self, izq):
        self.panel_estudio = Tarjeta('Estudio y montaje')
        campos = Campos()
        self.cmb_estudio = QComboBox()
        for clave, nombre in Z.ESTUDIOS:
            self.cmb_estudio.addItem(nombre, clave)
        self.cmb_estudio.currentIndexChanged.connect(self._al_cambiar_estudio)
        self.cmb_estudio.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_estudio.setMinimumContentsLength(10)
        campos.agregar('Estudio', self.cmb_estudio)
        self.panel_estudio.agregar(campos)
        self.chk_sensor = {}
        for clave, nombre, _pg in Z.SENSORES:
            c = QCheckBox(nombre)
            c.clicked.connect(lambda activo, k=clave: self._log('sensor', sensor=k, puesto=activo))
            self.chk_sensor[clave] = c
            self.panel_estudio.agregar(c)
        self.btn_registrar = self._boton('Registrar la noche', self._registrar, True)
        self.btn_registrar.setToolTip('Apagar la luz y registrar la noche con los sensores montados')
        self.panel_estudio.agregar(self.btn_registrar)
        izq.addWidget(self.panel_estudio)

    def _panel_sala(self, izq):
        """Mientras la noche corre: la cámara de la pieza y lo que hace el
        técnico (entrar a acomodar al paciente, pausar, adelantar)."""
        self.panel_sala = Tarjeta('Sala de control')
        # La pieza por la ventanilla (y la cámara del techo): doble clic la amplía.
        self.camara = VistaPieza()
        self.camara.ampliar.connect(self._ampliar_pieza)
        self.pieza_grande = None
        self.panel_sala.agregar(self.camara)
        self.lbl_camara = etiqueta('', rol='hint')
        self.lbl_camara.setWordWrap(True)
        self.panel_sala.agregar(self.lbl_camara)
        self.panel_sala.agregar(etiqueta('Entrar a acomodarlo', rol='campo'))
        fila = QHBoxLayout()
        self.btn_acomodar = {}
        for pos, texto in (('supino', 'De espaldas'), ('izquierda', 'Lado izq.'), ('derecha', 'Lado der.')):
            b = self._boton(texto, lambda p=pos: self._acomodar(p))
            b.setToolTip(f'Entrar a la pieza y acomodar al paciente {NOMBRE_POS[pos]} (se despierta un rato)')
            b.setStyleSheet('min-width: 0px; padding: 4px 2px;')
            self.btn_acomodar[pos] = b
            fila.addWidget(b)
        self.panel_sala.agregar_layout(fila)
        fila = QHBoxLayout()
        self.cmb_velocidad = QComboBox()
        for v, nombre in VELOCIDADES:
            self.cmb_velocidad.addItem(nombre, v)
        self.cmb_velocidad.setCurrentIndex(0)
        self.btn_pausa = self._boton('Pausa', self._pausa)
        fila.addWidget(self.cmb_velocidad)
        fila.addWidget(self.btn_pausa)
        self.panel_sala.agregar_layout(fila)
        self.btn_manana = self._boton('Hasta la mañana', self._manana)
        self.btn_manana.setToolTip('Adelantar hasta que se enciende la luz')
        self.panel_sala.agregar(self.btn_manana)
        izq.addWidget(self.panel_sala)

    def _ampliar_pieza(self):
        """La pieza en grande, en su propia ventana (sigue a la noche mientras esté abierta)."""
        if self.pieza_grande is None:
            self.pieza_grande = VistaPieza(grande=True)
            self.pieza_grande.setParent(self, Qt.WindowType.Window)
            self.pieza_grande.setWindowTitle('Sala de control: la pieza')
            self.pieza_grande.resize(960, 600)
        c = self.camara
        self.pieza_grande.principal = c.principal
        self.pieza_grande.poner(c.pos, c.despierto, c.hora)
        self.pieza_grande.show()
        self.pieza_grande.raise_()
        self._log('ver_pieza')

    def _panel_puntuacion(self, izq):
        self.panel_puntuacion = Tarjeta('Puntuación')
        self.cmb_regla = QComboBox()
        for clave, nombre in Z.REGLAS:
            self.cmb_regla.addItem(nombre, clave)
        self.cmb_regla.currentIndexChanged.connect(self._al_cambiar_regla)
        self.cmb_regla.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_regla.setMinimumContentsLength(12)
        self.panel_puntuacion.agregar(etiqueta('Regla de hipopnea', rol='campo'))
        self.panel_puntuacion.agregar(self.cmb_regla)
        self.lbl_elegido = etiqueta('', rol='hint')
        self.lbl_elegido.setWordWrap(True)
        self.panel_puntuacion.agregar(self.lbl_elegido)
        grilla = QHBoxLayout()
        self.btn_tipo = {}
        for tipo in ('ao', 'am', 'ac', 'h', 'rera'):
            b = self._boton(ABREV_TIPO[tipo], lambda t=tipo: self._poner_tipo(t))
            b.setToolTip(Z.NOMBRE_TIPO[tipo].capitalize())
            b.setStyleSheet(f'color: {COLOR_TIPO[tipo]}; font-weight: 700; min-width: 0px; padding: 4px 2px;')
            self.btn_tipo[tipo] = b
            grilla.addWidget(b)
        self.panel_puntuacion.agregar_layout(grilla)
        fila = QHBoxLayout()
        self.btn_borrar = self._boton('Borrar', self._borrar)
        self.btn_excluir = self._boton('Excluir', self._excluir)
        self.btn_excluir.setToolTip('Saca del análisis la selección (la de abajo o la de la noche)')
        fila.addWidget(self.btn_borrar)
        fila.addWidget(self.btn_excluir)
        self.panel_puntuacion.agregar_layout(fila)
        self.btn_auto = self._boton('Volver a la automática', self._volver_auto)
        self.btn_auto.setToolTip('Descarta tus cambios y los tramos excluidos')
        self.panel_puntuacion.agregar(self.btn_auto)
        ayuda = etiqueta(
            'Clic en un evento para elegirlo y cambiarle el tipo. Sin evento elegido, el tipo agrega uno con la '
            'selección gris (arrastra sus bordes). "Excluir" saca del análisis la selección de abajo o, si está '
            'visible, la de la noche.', rol='hint')
        ayuda.setWordWrap(True)
        self.panel_puntuacion.agregar(ayuda)
        izq.addWidget(self.panel_puntuacion)

    def _pantalla(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.noche = Noche(self._ir_a)
        caja = Tarjeta('La noche')
        caja.agregar(self.noche.widget, 1)
        # La casilla va en la barra de abajo: en "La noche" el alto es para
        # el hipnograma (pantallas de 768 px).
        self.chk_sel_noche = QCheckBox('Selección en la noche')
        self.chk_sel_noche.setToolTip('Muestra una selección en la noche entera para excluir tramos largos')
        self.chk_sel_noche.toggled.connect(self._al_sel_noche)
        abajo = Tarjeta()
        barra = QHBoxLayout()
        self.btn_atras = self._boton('◀', lambda: self._mover(-1))
        self.btn_adelante = self._boton('▶', lambda: self._mover(1))
        self.cmb_ventana = QComboBox()
        for seg, nombre in VENTANAS:
            self.cmb_ventana.addItem(nombre, seg)
        self.cmb_ventana.setCurrentIndex(1)
        self.cmb_ventana.currentIndexChanged.connect(lambda _i: self._dibujar_detalle())
        self.lbl_donde = etiqueta('', rol='hint')
        barra.addWidget(self.btn_atras)
        barra.addWidget(self.btn_adelante)
        barra.addWidget(self.cmb_ventana)
        barra.addWidget(self.lbl_donde, 1)
        barra.addWidget(self.chk_sel_noche)
        abajo.agregar_layout(barra)
        self.detalle = Detalle(self._clic_detalle)
        abajo.agregar(self.detalle.widget, 1)
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(caja)
        vertical.addWidget(abajo)
        vertical.setStretchFactor(0, 2)
        vertical.setStretchFactor(1, 5)
        vertical.setChildrenCollapsible(False)
        layout.addWidget(vertical, 1)
        return contenedor

    def _pestana_informe(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        resultados = Tarjeta('Resultados (con tu puntuación)')
        self.tabla_informe = Tabla()
        resultados.agregar(self.tabla_informe)
        self.lbl_avisos = etiqueta('', rol='hint')
        self.lbl_avisos.setWordWrap(True)
        self.lbl_avisos.setStyleSheet(f'color: {tema.AVISO};')
        resultados.agregar(self.lbl_avisos)
        campos = Campos()
        self.cmb_gravedad = QComboBox()
        self.cmb_gravedad.addItem('—', '')
        for clave, nombre in GRAVEDADES:
            self.cmb_gravedad.addItem(nombre, clave)
        self.cmb_gravedad.currentIndexChanged.connect(self._al_gravedad)
        campos.agregar('Gravedad por el índice', self.cmb_gravedad)
        resultados.agregar(campos)
        layout.addWidget(resultados)
        caja = Tarjeta('Informe')
        caja.agregar(etiqueta('Hallazgos', rol='campo'))
        self.txt_hallazgos = QPlainTextEdit()
        caja.agregar(self.txt_hallazgos, 1)
        caja.agregar(etiqueta('Conclusión', rol='campo'))
        self.txt_conclusion = QPlainTextEdit()
        caja.agregar(self.txt_conclusion, 1)
        for txt in (self.txt_hallazgos, self.txt_conclusion):
            txt.setMinimumHeight(110)
        self.estado_informe = EstadoInforme()
        caja.agregar(self.estado_informe)
        layout.addWidget(caja, 1)
        desplazable = QScrollArea()
        desplazable.setWidget(contenedor)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        return desplazable

    # --- Ciclo de vida (API que llama main.py) --------------------------

    def la_super(self, data, appointment_id=None):
        self.timer.stop()
        self.corriendo = False
        self.recalculando = False
        self.t_actual = None
        self.sesion = SesionSueno(data, appointment_id) if data is not None else None
        self.data_caso = data
        self.appointment_id = appointment_id
        self.S = None
        self.montaje = []
        self.eventos = []
        self.excluidos = []
        self.t0 = 0
        self.elegido = None
        self.chk_sel_noche.setChecked(False)
        self.cmb_estudio.blockSignals(True)
        self.cmb_estudio.setCurrentIndex(0)
        self.cmb_estudio.blockSignals(False)
        self.cmb_regla.blockSignals(True)
        self.cmb_regla.setCurrentIndex(0)
        self.cmb_regla.blockSignals(False)
        self.cmb_gravedad.blockSignals(True)
        self.cmb_gravedad.setCurrentIndex(0)
        self.cmb_gravedad.blockSignals(False)
        for c in self.chk_sensor.values():
            c.setChecked(False)
        for w in (self.txt_hallazgos, self.txt_conclusion):
            w.clear()
        self.estado_informe.limpiar()
        hay = self.sesion is not None and self.sesion.hay_paciente
        self.panel_estudio.setEnabled(hay)
        self._pintar_sensores()
        if hay:
            self._mensaje('Elige el estudio, monta los sensores y registra la noche. Después revisa la puntuación '
                          'automática y corrígela: los índices salen de lo que tú puntúes.')
        else:
            self._mensaje('Abre una atención para registrar.')
        self.dibujar()

    def report_job(self):
        if not self.data_login or self.S is None or self.sesion is None:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        r = self._indices()
        data = {
            'estudio': self.S['estudio'],
            'montaje': list(self.montaje),
            'regla': self.cmb_regla.currentData(),
            'eventos': [{'t': e['t'], 'dur': e['dur'], 'tipo': e['tipo'], 'auto': bool(e.get('auto'))}
                        for e in self.eventos],
            'excluidos': [[a, b] for a, b in self.excluidos],
            'acomodos': [[t, p] for t, p in self.S.get('acomodos') or []],
            't_actual': None if self._de_dia() else int(self.t_actual),
            'indices': {k: v for k, v in r.items() if isinstance(v, (int, float)) or v is None},
            'tabla': getattr(self.tabla_informe, 'contenido', {}),
            'avisos': [a.lstrip('• ') for a in self.lbl_avisos.text().split('\n') if a.strip()],
            'gravedad': self.cmb_gravedad.currentData() or '',
            'hallazgos': self.txt_hallazgos.toPlainText(),
            'conclusion': self.txt_conclusion.toPlainText(),
        }
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data,
                'images': self._exportar_imagenes}

    def submit_report(self):
        return sesion_nasal.subir_al_cerrar(self)

    def restore_report(self, data):
        """Retomar la atención: la noche se rehace (es la misma) y vuelven la
        puntuación, los tramos excluidos y el texto."""
        if self.sesion is None or not self.sesion.hay_paciente or self.S is not None:
            return False
        estudio = data.get('estudio')
        if estudio not in dict(Z.ESTUDIOS):
            return False
        self.cmb_estudio.blockSignals(True)
        self.cmb_estudio.setCurrentIndex(self.cmb_estudio.findData(estudio))
        self.cmb_estudio.blockSignals(False)
        self.montaje = [k for k in data.get('montaje') or [] if k in Z.NOMBRE_SENSOR]
        self._pintar_sensores()
        for k, c in self.chk_sensor.items():
            c.setChecked(k in self.montaje)
        acomodos = [(int(t), p) for t, p in data.get('acomodos') or [] if p in Z.POSICIONES]
        self.S = Z.noche(self.sesion.sueno, estudio, acomodos)
        # A medio correr: queda en pausa donde iba (se sigue con "Seguir").
        t = data.get('t_actual')
        self.t_actual = self.S['N'] if t is None else max(0, min(self.S['N'], int(t)))
        self.corriendo = False
        self.eventos = [{'t': int(e['t']), 'dur': int(e['dur']), 'tipo': e['tipo'], 'auto': bool(e.get('auto'))}
                        for e in data.get('eventos') or []
                        if isinstance(e, dict) and e.get('tipo') in Z.NOMBRE_TIPO] if self._de_dia() else []
        self.excluidos = [(int(a), int(b)) for a, b in data.get('excluidos') or []]
        i = self.cmb_regla.findData(data.get('regla'))
        self.cmb_regla.blockSignals(True)
        self.cmb_regla.setCurrentIndex(max(0, i))
        self.cmb_regla.blockSignals(False)
        i = self.cmb_gravedad.findData(data.get('gravedad') or '')
        self.cmb_gravedad.blockSignals(True)
        self.cmb_gravedad.setCurrentIndex(max(0, i))
        self.cmb_gravedad.blockSignals(False)
        self.txt_hallazgos.setPlainText(data.get('hallazgos') or '')
        self.txt_conclusion.setPlainText(data.get('conclusion') or '')
        self._mensaje('Se recuperó el registro de esta atención.', 'ok')
        self.dibujar()
        return True

    # --- Acciones del alumno -------------------------------------------

    def _log(self, accion, **payload):
        if self.sesion is None or not self.sesion.hay_paciente:
            return
        sesion_nasal.registrar(f'{self.EQUIPO}_{accion}', self.data_caso, self.appointment_id, **payload)

    def _mensaje(self, texto, estado=None):
        self.lbl_mensaje.setText(texto)
        color = {'alerta': tema.ALERTA, 'ok': tema.OK}.get(estado, tema.TEXTO_SUAVE)
        self.lbl_mensaje.setStyleSheet(f'color: {color};')

    def _estudio(self):
        return self.cmb_estudio.currentData()

    def _al_cambiar_estudio(self, _i):
        self._pintar_sensores()
        self._log('estudio', estudio=self._estudio())

    def _pintar_sensores(self):
        validos = Z.sensores_del_estudio(self._estudio())
        for k, c in self.chk_sensor.items():
            c.setVisible(k in validos)
            if k not in validos:
                c.setChecked(False)

    def _registrar(self):
        if self.S is not None:
            return
        montados = [k for k, c in self.chk_sensor.items() if c.isChecked() and not c.isHidden()]
        estudio = self._estudio()
        faltan = [k for k in Z.sensores_del_estudio(estudio) if k not in montados]
        self.montaje = montados
        sueno, sesion = self.sesion.sueno, self.sesion
        semilla = f'psg/{self.appointment_id}'
        self._mensaje('Registrando la noche…')
        self.btn_registrar.setEnabled(False)

        def calcular():
            S = Z.noche(sueno, estudio)
            return S, Z.auto_puntuar(S, montados, semilla)

        def listo(res):
            if self.sesion is not sesion or self.S is not None:
                return
            self.S, auto = res
            verdad = Z.resumen(self.S, estudio)
            self._log('registrar', estudio=estudio, montaje=montados, faltan=faltan, n_auto=len(auto),
                      canula_suelta=self.S.get('canula_suelta'),
                      verdad={'IAH': verdad['IAH'], 'REI': verdad['REI'], 'IDO3': verdad['IDO3']})
            sin = ('Sin ' + ', '.join(Z.NOMBRE_SENSOR[k].lower() for k in faltan) + '. ') if faltan else ''
            if estudio == 'psg':
                # En el laboratorio la noche corre: el técnico la vigila y
                # puede entrar a acomodar al paciente.
                self.eventos = []
                self.t_actual = 0
                self.t0 = 0
                self.corriendo = True
                self.timer.start()
                self._mensaje(sin + 'Se apagó la luz y la noche corre. Desde la sala de control puedes entrar a '
                              'acomodar al paciente; la puntuación automática está lista al encender la luz.',
                              'alerta' if faltan else 'ok')
            else:
                # En la casa no hay técnico: llega la noche entera.
                self.t_actual = self.S['N']
                self.eventos = auto
                self.t0 = self._primer_sueno()
                self._mensaje(sin + 'Noche registrada en la casa (sin técnico: el paciente durmió como quiso). '
                              'Revisa la puntuación automática ventana por ventana.', 'alerta' if faltan else 'ok')
            self.dibujar()

        self.tarea = hilos.en_fondo(calcular, listo=listo, dueno=self, nombre='noche de sueño')

    def _primer_sueno(self):
        S = self.S
        return next((s for s in range(S['N']) if S['etapa'][s] != 'W'), 0) // 30 * 30

    def _dur(self):
        return self.cmb_ventana.currentData()

    # --- La noche que corre (PSG) ----------------------------------------

    def _de_dia(self):
        """La noche terminó (o no corre: la poligrafía llega entera)."""
        return self.S is not None and (self.t_actual is None or self.t_actual >= self.S['N'])

    def _en_vivo(self):
        return self.S is not None and not self._de_dia()

    def _hasta(self):
        return self.S['N'] if self._de_dia() else int(self.t_actual)

    def _tic(self):
        if not self._en_vivo() or not self.corriendo or self.recalculando:
            return
        avance = self.t_actual + self._velocidad() * TIC_MS / 1000
        if avance >= self.S['N']:
            # La luz se enciende con la noche todavía en vivo: con t_actual
            # ya en el final, _manana no hacía nada (sin puntuación ni
            # resultados, ticket #65).
            self._manana(por_reloj=True)
            return
        self.t_actual = avance
        # Corriendo, el detalle sigue lo último registrado.
        self.t0 = max(0, int(self.t_actual) - self._dur())
        self.dibujar()

    def _velocidad(self):
        """Segundos de noche por segundo real."""
        v = self.cmb_velocidad.currentData()
        return v if v else self.S['N'] / (NOCHE_EN_MIN * 60)

    def _pausa(self):
        if not self._en_vivo():
            return
        self.corriendo = not self.corriendo
        self.timer.start() if self.corriendo else self.timer.stop()
        self._log('pausa', pausa=not self.corriendo, t=int(self.t_actual))
        self.dibujar()

    def _manana(self, por_reloj=False):
        """Se enciende la luz: la noche termina y el programa propone su
        puntuación automática. por_reloj: llegó al final sola (no con
        "Hasta la mañana")."""
        if not self._en_vivo() or self.recalculando:
            return
        self.timer.stop()
        self.corriendo = False
        adelantada = not por_reloj and self.t_actual < self.S['N'] - 1
        self.t_actual = self.S['N']
        self.eventos = Z.auto_puntuar(self.S, self.montaje, f'psg/{self.appointment_id}')
        self.t0 = self._primer_sueno()
        self.elegido = None
        self._log('manana', adelantada=adelantada, acomodos=[[t, p] for t, p in self.S.get('acomodos') or []],
                  n_auto=len(self.eventos))
        n_ac = len(self.S.get('acomodos') or [])
        self._mensaje('Se encendió la luz' + (f' ({n_ac} acomodo{"s" if n_ac != 1 else ""} en la noche)' if n_ac else '')
                      + '. Revisa la puntuación automática ventana por ventana.', 'ok')
        self.dibujar()

    def _acomodar(self, pos):
        """El técnico entra a la pieza y acomoda al paciente: la noche se
        rehace desde ahora (lo anterior no cambia)."""
        if not self._en_vivo() or self.recalculando:
            return
        t = int(self.t_actual)
        antes = self.S['pos'][min(self.S['N'] - 1, t)]
        if pos == antes:
            self._mensaje(f'Ya está {NOMBRE_POS[pos]}.')
            return
        etapa = self.S['etapa'][min(self.S['N'] - 1, t)]
        acomodos = list(self.S.get('acomodos') or []) + [(t, pos)]
        sueno, sesion, seguia = self.sesion.sueno, self.sesion, self.corriendo
        self.timer.stop()
        self.recalculando = True
        sup_antes = sum(1 for k in range(t) if self.S['pos'][k] == 'supino' and self.S['etapa'][k] != 'W') / 60

        def listo(S):
            if self.sesion is not sesion:
                return
            self.recalculando = False
            self.S = S
            self._log('acomodar', t=t, de=antes, a=pos, etapa=etapa,
                      verdad={'min_sueno_supino_hasta_ahora': round(sup_antes, 1)})
            self._mensaje(f'Entraste a la pieza: el paciente quedó {NOMBRE_POS[pos]}'
                          + (' y se despertó un rato.' if etapa != 'W' else '.'))
            if seguia:
                self.timer.start()
            self.dibujar()

        def fallo(_exc):
            self.recalculando = False
            if seguia:
                self.timer.start()

        self.tarea = hilos.en_fondo(Z.noche, sueno, 'psg', acomodos, listo=listo, fallo=fallo, dueno=self,
                                    nombre='noche acomodada')

    def _mover(self, signo):
        if self.S is None:
            return
        self.t0 = max(0, min(self._hasta() - self._dur(), self.t0 + signo * self._dur()))
        self.elegido = None
        self._dibujar_detalle()
        self._dibujar_noche()

    def _ir_a(self, t):
        if self.S is None:
            return
        self.t0 = int(max(0, min(self._hasta() - self._dur(), t - self._dur() / 2)) // 10 * 10)
        self.elegido = None
        self._dibujar_detalle()
        self._dibujar_noche()

    def _clic_detalle(self, x):
        en = [e for e in self.eventos if e['t'] <= x <= e['t'] + e['dur']]
        self.elegido = en[0] if en else None
        if self.elegido is None:
            # Sin evento ahí: la selección salta al clic.
            a, b = self.detalle.seleccion.getRegion()
            ancho = max(10, b - a)
            self.detalle.seleccion.setRegion((x - ancho / 2, x + ancho / 2))
        self._dibujar_detalle()

    def _poner_tipo(self, tipo):
        if self.S is None:
            return
        if self.elegido is not None:
            antes = self.elegido['tipo']
            self.elegido['tipo'] = tipo
            self.elegido['auto'] = False
            self._log('cambiar', t=self.elegido['t'], dur=self.elegido['dur'], de=antes, a=tipo,
                      verdad=self._verdad_en(self.elegido))
        else:
            a, b = self.detalle.seleccion.getRegion()
            a, b = int(round(a)), int(round(b))
            if b - a < 3:
                return
            e = {'t': a, 'dur': b - a, 'tipo': tipo, 'auto': False}
            self.eventos.append(e)
            self.eventos.sort(key=lambda x: x['t'])
            self.elegido = e
            self._log('agregar', t=a, dur=b - a, tipo=tipo, verdad=self._verdad_en(e))
        self._despues_de_editar()

    def _borrar(self):
        if self.elegido is None:
            return
        e, self.elegido = self.elegido, None
        self.eventos.remove(e)
        self._log('borrar', t=e['t'], dur=e['dur'], tipo=e['tipo'], auto=bool(e.get('auto')),
                  verdad=self._verdad_en(e))
        self._despues_de_editar()

    def _excluir(self):
        if self.S is None:
            return
        if self.chk_sel_noche.isChecked():
            a, b = (x * 3600 for x in self.noche.seleccion.getRegion())
        else:
            a, b = self.detalle.seleccion.getRegion()
        a, b = int(max(0, a)), int(min(self.S['N'], b))
        if b - a < 5:
            return
        self.excluidos.append((a, b))
        suelta = self.S.get('canula_suelta')
        self._log('excluir', desde=a, hasta=b, canula_suelta=suelta)
        self._despues_de_editar()

    def _volver_auto(self):
        if self.S is None:
            return
        self.eventos = Z.auto_puntuar(self.S, self.montaje, f'psg/{self.appointment_id}')
        self.excluidos = []
        self.elegido = None
        self._log('volver_auto')
        self._despues_de_editar()

    def _al_cambiar_regla(self, _i):
        self._log('regla', regla=self.cmb_regla.currentData())
        self._pintar_informe()

    def _al_gravedad(self, _i):
        r = self._indices() if self.S is not None else {}
        indice = r.get('IAH')
        self._log('gravedad', gravedad=self.cmb_gravedad.currentData(), indice=indice,
                  correcta=Z.gravedad_clave(indice))
        self._pintar_verdad()

    def _al_sel_noche(self, activo):
        self.noche.seleccion.setVisible(activo)
        if activo and self.S is not None:
            self.noche.seleccion.setRegion((self.t0 / 3600, (self.t0 + 1800) / 3600))

    def _verdad_en(self, e):
        """El evento del modelo que se cruza con este (o None)."""
        if self.S is None:
            return None
        for x in self.S['ev']:
            if x['t'] < e['t'] + e['dur'] and e['t'] < x['t'] + x['dur']:
                return {'tipo': x['tipo'], 't': x['t'], 'dur': x['dur'], 'caida': round(x['drop'], 1),
                        'despertar': x['arousal']}
        return None

    def _despues_de_editar(self):
        self._dibujar_detalle()
        self._dibujar_noche()
        self._pintar_informe()

    # --- Dibujo ---------------------------------------------------------

    def dibujar(self):
        hay = self.sesion is not None and self.sesion.hay_paciente
        registrado = self.S is not None
        self.panel_estudio.setEnabled(hay and not registrado)
        # Registrada la noche, los sensores ya no se tocan: se esconden para que
        # la puntuación (tipos, Borrar, Excluir) quede a la vista en pantallas
        # bajas. La pastilla de arriba dice el estudio; el informe, lo que faltó.
        validos = Z.sensores_del_estudio(self._estudio())
        for k, c in self.chk_sensor.items():
            c.setVisible(not registrado and k in validos)
        self.btn_registrar.setEnabled(hay and not registrado)
        vivo = self._en_vivo()
        self.btn_registrar.setText('La noche corre…' if vivo else 'Noche registrada' if registrado
                                   else 'Registrar la noche')
        self.panel_puntuacion.setEnabled(registrado and not vivo)
        for b in (self.btn_atras, self.btn_adelante, self.cmb_ventana):
            b.setEnabled(registrado)
        self.panel_sala.setVisible(vivo)
        if not vivo and self.pieza_grande is not None:
            self.pieza_grande.hide()
        if vivo:
            t = min(self.S['N'] - 1, int(self.t_actual))
            pos, etapa = self.S['pos'][t], self.S['etapa'][t]
            self.camara.poner(pos, etapa == 'W', hhmm(t))
            if self.pieza_grande is not None:
                self.pieza_grande.poner(pos, etapa == 'W', hhmm(t))
            estado = 'Despierto' if etapa == 'W' else 'Duerme'
            self.lbl_camara.setText(f'{hhmm(t)} · {estado} {NOMBRE_POS[pos]}'
                                    + ('' if etapa == 'W' else f' ({Z.NOM_ETAPA[etapa]})'))
            for p_, b in self.btn_acomodar.items():
                b.setEnabled(not self.recalculando and p_ != pos)
            self.btn_pausa.setText('Pausa' if self.corriendo else 'Seguir')
        self.pill_estudio.setVisible(registrado)
        if registrado:
            self.pill_estudio.set(dict(Z.ESTUDIOS)[self.S['estudio']], 'acento')
        self._dibujar_noche()
        self._dibujar_detalle()
        self._pintar_informe()

    def _dibujar_noche(self):
        self.noche.dibujar(self.S, self.eventos, self.excluidos, self.t0, self._dur(),
                           None if self.S is None else self._hasta())

    def _dibujar_detalle(self):
        if self.S is None:
            self.detalle.dibujar(None, [], [], 0, self._dur(), None)
            self.lbl_donde.setText('')
            self.lbl_elegido.setText('')
            return
        dur = self._dur()
        self.t0 = max(0, min(self._hasta() - dur, self.t0))
        sen = Z.senales(self.S, self.t0, dur, self.montaje)
        if self._en_vivo():
            # Lo que todavía no pasa no se ve.
            corte = max(0, int((self._hasta() - self.t0) * len(sen['t']) / dur))
            sen = {k: (None if v is None else v[:corte]) for k, v in sen.items()}
        a, b = self.detalle.seleccion.getRegion()
        if not (self.t0 <= a and b <= self.t0 + dur):
            mitad = self.t0 + dur / 2
            self.detalle.seleccion.setRegion((mitad - 7, mitad + 7))
        self.detalle.dibujar(sen, self.eventos, self.excluidos, self.t0, dur, self.elegido)
        medio = self.t0 + dur / 2
        partes = [hhmm(self.t0) + ' – ' + hhmm(self.t0 + dur)]
        if self.S['estudio'] == 'psg':
            partes.append(Z.NOM_ETAPA[Z.etapa_en(self.S, medio)])
        if 'pos' in self.montaje:
            partes.append(Z.posicion_en(self.S, medio))
        self.lbl_donde.setText(' · '.join(partes))
        if self.elegido is not None:
            e = self.elegido
            self.lbl_elegido.setText(f'Elegido: {Z.NOMBRE_TIPO[e["tipo"]]} de {e["dur"]} s a las {hhmm(e["t"])}'
                                     f' (caída de SpO₂ {n(Z.caida(self.S, e))} puntos)'
                                     + (', de la puntuación automática.' if e.get('auto') else '.'))
        else:
            self.lbl_elegido.setText('Sin evento elegido: el tipo agrega uno con la selección.')

    def _indices(self):
        return Z.indices(self.S, [dict(e) for e in self.eventos], self.cmb_regla.currentData(), self.excluidos)

    def _pintar_informe(self):
        if self.S is None or self._en_vivo():
            self.tabla_informe.poblar(['Parámetro', 'Valor'], [])
            self.lbl_avisos.setText('La noche está corriendo: los resultados salen de la puntuación, que está lista '
                                    'al encender la luz.' if self.S is not None else '')
            self._pintar_verdad()
            return
        r = self._indices()
        psg = self.S['estudio'] == 'psg'
        m = self.montaje
        nombre = 'IAH (por hora de sueño)' if psg else 'REI (por hora de registro válido)'
        filas = []
        if psg and 'eeg' not in m:
            filas.append(('Arquitectura del sueño', 'sin EEG'))
        elif psg:
            filas += [('Tiempo en cama', f'{n(r["TIB"], 0)} min'), ('Tiempo total de sueño', f'{n(r["TST"], 0)} min'),
                      ('Eficiencia del sueño', f'{n(r["eficiencia"])} %'), ('Latencia de sueño', f'{n(r["latencia"], 0)} min'),
                      ('Latencia REM', f'{n(r["latencia REM"], 0)} min'), ('Vigilia tras el inicio del sueño', f'{n(r["WASO"], 0)} min'),
                      ('N1 / N2 / N3 / REM', ' / '.join(f'{n(r["% " + e])} %' for e in ('N1', 'N2', 'N3', 'R')))]
        else:
            filas += [('Tiempo de registro', f'{n(r["min registro"], 0)} min'),
                      ('Registro válido', f'{n(r["min validos"], 0)} min')]
        c = r['n']
        filas += [('Apneas obstructivas / mixtas / centrales', f'{c["ao"]} / {c["am"]} / {c["ac"]}'),
                  ('Hipopneas (puntuadas / contadas con la regla)', f'{c["h"]} / {r["hipopneas contadas"]}')]
        if psg:
            filas.append(('RERA', str(c['rera'])))
        filas.append((nombre, n(r['IAH'])))
        if psg:
            filas.append(('IDR (por hora de sueño)', n(r['IDR'])))
        ox = 'spo2' in m
        filas += [('IDO ≥ 3 % / ≥ 4 %', f'{n(r["IDO3"])} / {n(r["IDO4"])}' if ox else 'sin oxímetro'),
                  ('SpO₂ media / mínima', f'{n(r["SpO2 media"])} % / {n(r["SpO2 min"], 0)} %' if ox else 'sin oxímetro'),
                  ('Tiempo con SpO₂ < 90 %', f'{n(r["T90"])} %' if ox else 'sin oxímetro'),
                  ('Índice en supino / lateral izq. / lateral der.',
                   ' / '.join(n(r['IAH ' + p]) for p in ('supino', 'izquierda', 'derecha'))
                   if 'pos' in m else 'sin sensor de posición')]
        if psg:
            filas.append(('Índice en REM / NREM', f'{n(r["IAH REM"])} / {n(r["IAH NREM"])}'
                          if 'eeg' in m else 'sin EEG'))
        filas.append(('Ronquido', f'{n(r["ronquido %"], 0)} % del registro' if 'ron' in m else 'sin micrófono'))
        self.tabla_informe.poblar(['Parámetro', 'Valor'], [([a, b], None, {}) for a, b in filas])
        avisos = []
        if not psg and r['min validos'] < 240:
            avisos.append('• Menos de 4 horas de registro válido: la poligrafía no alcanza para informar.')
        faltan = [k for k in Z.sensores_del_estudio(self.S['estudio']) if k not in self.montaje]
        if faltan:
            avisos.append('• Sin ' + ', '.join(Z.NOMBRE_SENSOR[k].lower() for k in faltan) + '.')
        self.lbl_avisos.setText('\n'.join(avisos))
        self._pintar_verdad()

    def _pintar_verdad(self):
        if self.verdad is None:
            return
        hay = self.sesion is not None and self.sesion.hay_paciente
        self.verdad.setText(self._texto_verdad() if hay else '')

    def _exportar_imagenes(self):
        temp = context.get_resource('local_cache/nasal/temp')
        os.makedirs(temp, exist_ok=True)
        ruta = os.path.join(temp, 'upload_psg_noche.jpg')
        try:
            self.noche.exportar(ruta)
        except Exception as exc:  # noqa: BLE001 -- sin imagen el informe sube igual
            print(f'{self.TIPO}: no se pudo exportar la noche: {exc}')
            return {}
        return {'psg_noche': ruta}

    def _sueno_supino(self, acomodos):
        """(min de sueño de espaldas, de esos en REM, IAH de espaldas bien
        puntuado) de la noche con esos acomodos; se guarda por acomodos."""
        cache = self.__dict__.setdefault('_cache_supino', {})
        clave = (self.appointment_id, acomodos)
        if clave not in cache:
            S = self.S if acomodos == tuple(self.S.get('acomodos') or ()) else \
                Z.noche(self.sesion.sueno, self.S['estudio'], acomodos)
            sup = [k for k in range(S['N']) if S['pos'][k] == 'supino' and S['etapa'][k] != 'W']
            ideal = [{'t': x['t'], 'dur': x['dur'], 'tipo': x['tipo']} for x in S['ev']]
            cache[clave] = (len(sup) / 60, sum(1 for k in sup if S['etapa'][k] == 'R') / 60,
                            Z.indices(S, ideal, '3')['IAH supino'])
        return cache[clave]

    def _texto_verdad(self):
        s = self.sesion.sueno
        perfil = dict(Z.PERFILES_LIBRO).get(s['perfil'], 'Perfil personalizado')
        filas = [f'<b>Paciente</b>: {perfil}.']
        if s['canula_suelta']:
            filas.append(f'En la poligrafía de la casa la cánula se suelta de {hhmm(s["canula_suelta"]["desde"] * 60)} '
                         f'a {hhmm(s["canula_suelta"]["hasta"] * 60)}.')
        if self.S is None:
            return '<br>'.join(filas)
        acomodos = self.S.get('acomodos') or []
        if acomodos:
            filas.append('<b>Acomodos</b>: ' + '; '.join(
                f'{hhmm(t)} {NOMBRE_POS[p]}' for t, p in acomodos) + '.')
        if self._en_vivo():
            filas.append(f'La noche corre ({hhmm(self.t_actual)}): el resto se calcula al encender la luz.')
            return '<br>'.join(filas)
        if acomodos:
            sin, con = self._sueno_supino(()), self._sueno_supino(tuple(acomodos))
            filas.append(f'Sueño de espaldas: {n(con[0], 0)} min (REM {n(con[1], 0)}); sin acomodarlo habría sido '
                         f'{n(sin[0], 0)} min (REM {n(sin[1], 0)}). IAH de espaldas con lo que pasó: {n(con[2])}; '
                         f'sin acomodarlo: {n(sin[2])}.')
        R = Z.resumen(self.S, self.S['estudio'])
        c = R['n']
        filas.append(f'<b>La noche de verdad</b>: {c["ao"]} obstructivas, {c["am"]} mixtas, {c["ac"]} centrales, '
                     f'{c["h"]} hipopneas ({R["hip con desaturación"]} con desaturación ≥ 3 %, '
                     f'{R["hip solo despertar"]} solo con despertar), {c["rera"]} RERA.')
        filas.append(f'IAH {n(R["IAH"])} (con 4 %: {n(R["IAH4"])}); lo que ve una poligrafía: REI {n(R["REI"])} '
                     f'por hora de registro; IDO3 {n(R["IDO3"])}. Gravedad por el IAH: {Z.gravedad(R["IAH"])}.')
        auto = Z.auto_puntuar(self.S, self.montaje, f'psg/{self.appointment_id}')
        ra = Z.indices(self.S, auto, self.cmb_regla.currentData())
        rr = self._indices()
        filas.append(f'<b>La puntuación automática sin tocar</b> daba {n(ra["IAH"])}; <b>la tuya</b>, {n(rr["IAH"])}.')
        verdaderos = {(x['t'], x['tipo']) for x in self.S['ev']}
        cambios = sum(1 for e in self.eventos if not e.get('auto'))
        falsos = sum(1 for e in self.eventos if e.get('falso'))
        mal = 0
        for e in self.eventos:
            v = self._verdad_en(e)
            if v is None or v['tipo'] != e['tipo']:
                mal += 1
        perdidos = sum(1 for x in self.S['ev'] if x['tipo'] != 'rera'
                       and not any(e['t'] < x['t'] + x['dur'] and x['t'] < e['t'] + e['dur'] for e in self.eventos))
        filas.append(f'Tus eventos: {len(self.eventos)} ({cambios} tocados por ti); {mal} no calzan con un evento '
                     f'de ese tipo (incluye {falsos} falsos de la cánula suelta); {perdidos} eventos de verdad sin '
                     f'puntuar (de {len(verdaderos)}).')
        if self.S.get('canula_suelta'):
            a, b = self.S['canula_suelta']
            cubierto = sum(max(0, min(b, y) - max(a, x)) for x, y in self.excluidos)
            filas.append(f'Cánula suelta {hhmm(a)}–{hhmm(b)}: excluiste {cubierto // 60} de {(b - a) // 60} min.')
        g = self.cmb_gravedad.currentData()
        if g:
            filas.append(f'Gravedad elegida: {g}; por tu índice corresponde: {Z.gravedad_clave(rr["IAH"])}.')
        return '<br>'.join(filas)
