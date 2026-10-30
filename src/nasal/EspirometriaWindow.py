"""El espirómetro de LabSim (H30 del libro), demo interna del Box Rinología.

Como se hace en la sala: el alumno pone la pinza nasal y la boquilla con
filtro, anota los datos del paciente (la talla la mide), verifica el equipo
con la jeringa de 3 L y, maniobra por maniobra, aprieta Iniciar y le habla
al paciente: «respire tranquilo», «tome todo el aire», «¡sople de golpe!»,
«¡siga, siga!», «¡tome aire rápido!». El paciente obedece con su demora y
su esfuerzo (nasal/espirometria.Registro); si nadie lo anima, deja de soplar
antes de vaciar. Las curvas se dibujan en vivo.

Al terminar, el equipo calcula lo que puede con la señal (tiempo cero, BEV,
FEV1, FVC, PEF, TEF, meseta, CVIF) y califica la maniobra. Lo que el equipo
no ve (una tos, una fuga, la boquilla mordida) lo marca el alumno en la
tabla: con esa marca se aplica la tabla de H30 "Qué aprovecha cada hallazgo".
Con las maniobras de cada fase salen los grados A-F, la mayor FVC y el mayor
FEV1 de las aceptables, y la tabla del informe en el formato del manual SER
2024 con GLI-2012 (previsto, LIN, z-score, cambio sobre el teórico).

El broncodilatador se da desde el paciente y tiene su espera (15 min el
salbutamol, 30 el ipratropio); lo que se mida antes es "post" con el efecto
a medias, como en la sala.

El informe ESPIROMETRIA guarda la receta de cada maniobra (semilla e
indicaciones con su muestra): al retomar la atención se rehacen idénticas.
Cada acción va a action_logs con prefijo esp_ (nasal/sesion.registrar).

Sin `cases.data['ESPIRO']` el equipo no mide.
"""

import math
import os
import random
import time

import pyqtgraph as pg
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFrame,
                               QHBoxLayout, QHeaderView, QLineEdit, QMainWindow, QPlainTextEdit,
                               QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from core import hilos, tema
from core.base import context
from core.estado_informe import EstadoInforme
from core.rng import stable_seed
from nasal import espirometria as E
from nasal import sesion as sesion_nasal
from nasal.equipos import PERMISOS_DOCENTE, QSS_NASAL, Tabla, num
from nasal.graficos import _plot, exportar
from nasal.paciente_rm import BOCA, RECORTE
from nasal.RinoscopiaWindow import cara
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta

PRE, POST = tema.OI, tema.OD          # como el informe del manual: antes azul, después rojo
FASES = {'pre': 'Pre', 'post': 'Post'}
MAX_MANIOBRAS = 8                     # por fase (manual SER 2024)

# (clave, nombre, minutos de espera) del protocolo nacional (H30).
BRONCODILATADORES = (
    ('salbutamol', 'Salbutamol 400 µg con aerocámara', 15),
    ('ipratropio', 'Bromuro de ipratropio 80 µg con aerocámara', 30),
)
ERRORES_EQUIPO = (('cero', 'Corriente de aire al poner el cero'),
                  ('descalibrado', 'Equipo descalibrado'))


def l(v, d=2):
    return num(v, d)


# ── La atención ─────────────────────────────────────────────────────────────

class SesionEspiro:
    """El paciente de espirometría en esta atención y el estado del equipo:
    calibración, cero y broncodilatador."""

    def __init__(self, data, appointment_id, reloj=time.monotonic):
        self.caso = E.desde_caso(data)
        self.appointment_id = appointment_id
        self._reloj = reloj
        semilla = stable_seed('espiro', appointment_id)
        r = random.Random(semilla)
        self.calibracion = 1 + r.gauss(0, 0.006)
        self.cero = 0.0
        self.bd = None             # {'farmaco', 't'}
        self.n = 0
        self._ambiente = (20.0 + (semilla % 400) / 100, 35 + (semilla // 400) % 26,
                          1005 + (semilla // 10400) % 16)

    @property
    def hay_paciente(self):
        return self.caso is not None

    def ahora(self):
        return self._reloj()

    def semilla(self):
        self.n += 1
        return f'esp/{self.appointment_id}/{self.n}'

    def fase(self):
        return 'post' if self.bd else 'pre'

    def espera_bd(self):
        return dict((k, m) for k, _n, m in BRONCODILATADORES)[self.bd['farmaco']] * 60 if self.bd else 0

    def desde_bd(self):
        return None if not self.bd else self._reloj() - self.bd['t']

    def falta_bd(self):
        return None if not self.bd else max(0.0, self.espera_bd() - self.desde_bd())

    def frac_bd(self):
        """Cuánto del efecto pleno hay ahora: 95 % al cumplirse la espera."""
        if not self.bd:
            return 0.0
        return 1 - math.exp(-3 * self.desde_bd() / self.espera_bd())

    def dar_bd(self, farmaco, ya=False):
        self.bd = {'farmaco': farmaco, 't': self._reloj() - (dict(
            (k, m) for k, _n, m in BRONCODILATADORES)[farmaco] * 60 if ya else 0)}

    def saltar_espera(self):
        if self.bd:
            self.bd['t'] = min(self.bd['t'], self._reloj() - self.espera_bd())

    def ambiente(self):
        """Temperatura (°C), humedad (%) y presión (hPa) de la sala, para BTPS."""
        return self._ambiente


# ── El paciente ─────────────────────────────────────────────────────────────

ESTADOS_PACIENTE = {
    'corriente': 'Respira tranquilo', 'vuelve': 'Vuelve a respirar tranquilo',
    'inspira_max': 'Toma aire…', 'tlc': 'Aguanta el aire', 'espira': 'Sopla',
    'rv': 'Sin aire', 'inspira_forzada': 'Toma aire rápido',
}


class PacienteEspiro(QWidget):
    """El paciente de frente (la cara de la rinoscopía): clic en la nariz pone
    o saca la pinza; clic en la boca, la boquilla con el filtro. La fuga se
    ve: la boquilla queda corrida y el labio no la sella."""

    pinza_clic = Signal()
    boquilla_clic = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.activo = False
        self.pinza = False
        self.boquilla = False
        self.fuga = False
        self.soplando = False
        self._foto = None
        self.setMinimumSize(180, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMouseTracking(True)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, ancho):
        return ancho

    def _pixmap(self):
        if self._foto is None:
            d = cara()
            ini, largo = d['indice']['0']
            self._foto = QPixmap.fromImage(QImage.fromData(d['bin'][ini:ini + largo], 'WEBP'))
        return self._foto

    def _escala(self):
        lado = min(self.width(), self.height())
        k = lado / RECORTE.width()
        return (self.width() - lado) / 2 - RECORTE.x() * k, (self.height() - lado) / 2 - RECORTE.y() * k, k

    def _nariz(self):
        fila = cara()['cuadros']['0']
        (dx, dy), (ix, iy) = fila['D'], fila['I']
        return (dx + ix) / 2, (dy + iy) / 2, abs(ix - dx)

    def _zona(self, pos):
        x0, y0, k = self._escala()
        x, y = (pos.x() - x0) / k, (pos.y() - y0) / k
        nx, ny, ancho = self._nariz()
        if abs(x - nx) < ancho * 0.9 and -28 < y - ny < 12:
            return 'nariz'
        if (x - BOCA[0]) ** 2 + (y - BOCA[1]) ** 2 < 26 ** 2:
            return 'boca'
        return None

    def mouseMoveEvent(self, evento):
        sobre = self.activo and self._zona(evento.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if sobre else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(evento)

    def mousePressEvent(self, evento):
        zona = self._zona(evento.position()) if self.activo else None
        if evento.button() == Qt.MouseButton.LeftButton:
            if zona == 'nariz':
                self.pinza_clic.emit()
            elif zona == 'boca':
                self.boquilla_clic.emit()
        super().mousePressEvent(evento)

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor('#FFFFFF'))
        x0, y0, k = self._escala()
        lado = RECORTE.width() * k
        destino = QRectF((self.width() - lado) / 2, (self.height() - lado) / 2, lado, lado)
        p.drawPixmap(destino, self._pixmap(), RECORTE)
        if not self.activo:
            p.fillRect(destino, QColor(255, 255, 255, 150))
            p.end()
            return
        p.save()
        p.translate(x0, y0)
        p.scale(k, k)
        if self.boquilla:
            self._pintar_boquilla(p)
        if self.pinza:
            self._pintar_pinza(p)
        p.restore()
        p.end()

    def _pintar_pinza(self, p):
        nx, ny, ancho = self._nariz()
        y = ny - 8
        p.setPen(QPen(QColor('#3F5E7A'), 2.4))
        p.setBrush(QColor('#6C8FB0'))
        for lado in (-1, 1):
            p.drawRoundedRect(QRectF(nx + lado * (ancho / 2 + 6) - 6, y - 7, 12, 14), 4, 4)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor('#3F5E7A'), 3))
        p.drawArc(QRectF(nx - ancho / 2 - 6, y - 30, ancho + 12, 40), 20 * 16, 140 * 16)

    def _pintar_boquilla(self, p):
        x, y = BOCA
        if self.fuga:
            x += 9
            # El labio no sella: la comisura queda abierta.
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(46, 20, 24, 220))
            p.drawEllipse(QPointF(x - 21, y + 1), 6, 4)
            if self.soplando:
                p.setPen(QPen(QColor(150, 180, 200, 200), 1.6))
                for i in range(3):
                    p.drawLine(QPointF(x - 28 - i * 5, y - 4 + i * 4), QPointF(x - 36 - i * 5, y - 6 + i * 4))
        # El filtro, de frente: un disco grande; la boquilla, entre los labios.
        p.setPen(QPen(QColor('#7D838C'), 2))
        p.setBrush(QColor(228, 232, 236, 235))
        p.drawEllipse(QPointF(x, y + 2), 24, 24)
        p.setBrush(QColor(196, 202, 210, 240))
        p.drawEllipse(QPointF(x, y + 2), 15, 15)
        p.setBrush(QColor(92, 98, 108, 240))
        p.drawEllipse(QPointF(x, y + 2), 8, 8)


# ── Las curvas ──────────────────────────────────────────────────────────────

class GraficosEspiro:
    """Flujo-volumen y volumen-tiempo. Las maniobras guardadas se dibujan
    referidas a su inicio (el punto de máxima inspiración) y a su tiempo
    cero; la que está en curso, en vivo."""

    def __init__(self):
        self.fv = _plot('Volumen (L)', 'Flujo (L/s)')
        self.vt = _plot('Tiempo (s)', 'Volumen (L)')
        self.fv.setMinimumSize(260, 220)
        self.vt.setMinimumSize(220, 220)
        self._items = []
        self.vivo_fv = self.fv.plot([], [], pen=pg.mkPen(tema.ACENTO, width=2.2))
        self.vivo_vt = self.vt.plot([], [], pen=pg.mkPen(tema.ACENTO, width=2.2))
        self._limites(6, 10, 10)

    def _limites(self, vmax, fmax, tmax):
        self.fv.setXRange(0, vmax, padding=0.02)
        self.fv.setYRange(-fmax * 0.8, fmax, padding=0.02)
        self.vt.setXRange(-1, tmax, padding=0.02)
        self.vt.setYRange(0, vmax, padding=0.02)

    def limpiar_vivo(self):
        self.vivo_fv.setData([], [])
        self.vivo_vt.setData([], [])

    def dibujar(self, curvas, vmax=None, fmax=None, tmax=None):
        """curvas: [(maniobra, color, guiones, ancho)]; maniobra con 'flujos' y 'r'."""
        for plot, item in self._items:
            plot.removeItem(item)
        self._items = []
        vmax_d, fmax_d, tmax_d = 2.0, 4.0, 6.0
        for m, color, guiones, ancho in curvas:
            x, y, tx, vy = trazos(m)
            estilo = Qt.PenStyle.DashLine if guiones else Qt.PenStyle.SolidLine
            pluma = pg.mkPen(color, width=ancho, style=estilo)
            self._items.append((self.fv, self.fv.plot(x, y, pen=pluma)))
            self._items.append((self.vt, self.vt.plot(tx, vy, pen=pluma)))
            r = m['r']
            punto = pg.ScatterPlotItem([1.0], [r['fev1']], size=7, brush=pg.mkBrush(color), pen=None)
            self.vt.addItem(punto)
            self._items.append((self.vt, punto))
            vmax_d = max(vmax_d, max(x) if x else 0, r.get('cvif') or 0)
            fmax_d = max(fmax_d, r['pef'])
            tmax_d = max(tmax_d, r['tef'])
        self._limites(vmax or math.ceil(vmax_d + 0.5), fmax or math.ceil(fmax_d + 1),
                      tmax or min(16, math.ceil(tmax_d + 1)))

    def vivo(self, flujos):
        """La maniobra en curso: el lazo referido al punto de mayor
        inspiración hasta ahora; la curva volumen-tiempo, desde que el flujo
        pasa de 1 L/s (el gatillo del equipo)."""
        if not flujos:
            self.limpiar_vivo()
            return
        vol = [0.0]
        for i in range(1, len(flujos)):
            vol.append(vol[-1] + (flujos[i - 1] + flujos[i]) / 2 * E.DT)
        base = min(vol)
        self.vivo_fv.setData([v - base for v in vol], flujos)
        gatillo = next((i for i, f in enumerate(flujos) if f > 1.0), None)
        if gatillo is None:
            self.vivo_vt.setData([], [])
            return
        i_s = gatillo
        while i_s > 0 and flujos[i_s - 1] > 0:
            i_s -= 1
        self.vivo_vt.setData([(i - i_s) * E.DT for i in range(i_s, len(vol))],
                             [vol[i] - vol[i_s] for i in range(i_s, len(vol))])

    def exportar(self, sufijo, ruta):
        exportar(self.fv if sufijo == 'esp_fv' else self.vt, ruta)


def trazos(m):
    """(x, y) del lazo flujo-volumen y (t, V) de la curva volumen-tiempo de
    una maniobra guardada."""
    f, r = m['flujos'], m['r']
    i_s, i_e, i_fin = r['i_inicio'], r['i_fin'], r['i_fin_insp']
    v, x = 0.0, [0.0]
    for i in range(i_s + 1, i_fin + 1):
        v += (f[i - 1] + f[i]) / 2 * E.DT
        x.append(v)
    y = list(f[i_s:i_fin + 1])
    tx = [(k) * E.DT - r['t0'] for k in range(i_e - i_s + 1)]
    return x, y, tx, x[:i_e - i_s + 1]


# ── La ventana ──────────────────────────────────────────────────────────────

class EspirometriaWindow(QMainWindow):
    TITULO = 'Espirometría'
    TIPO = 'ESPIROMETRIA'
    EQUIPO = 'esp'
    TIC_MS = 50

    def __init__(self, data_login=None, parent=None, reloj=time.monotonic):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self._reloj = reloj
        self.sesion = None
        self.data_caso = None
        self.appointment_id = None
        self.maniobras = []        # {'receta', 'fase', 'marca', 'flujos', 'r', 'verdad'}
        self.registro = None       # la maniobra en curso
        self.verificacion = None
        self.talla_medida = None
        self.seleccion = None
        self.tarea = None
        self.setWindowTitle(self.TITULO)
        self._construir()
        self.timer = QTimer(self)
        self.timer.setInterval(self.TIC_MS)
        self.timer.timeout.connect(self._tic)
        self.timer_segundo = QTimer(self)
        self.timer_segundo.setInterval(1000)
        self.timer_segundo.timeout.connect(self._cada_segundo)
        self.timer_segundo.start()
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
        self.pill_fase = Pastilla('', 'neutro')
        fila.addWidget(self.pill_fase)
        raiz.addLayout(fila)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)
        raiz.addLayout(cuerpo, 1)
        izquierda = QWidget()
        izq = QVBoxLayout(izquierda)
        izq.setContentsMargins(0, 0, 0, 0)
        izq.setSpacing(10)
        self._panel_paciente(izq)
        self._panel_equipo(izq)
        self._panel_errores(izq)
        izq.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidget(izquierda)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
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

    def _panel_paciente(self, izq):
        self.panel_paciente = Tarjeta('Paciente')
        self.vista = PacienteEspiro()
        self.vista.setFixedHeight(200)
        self.vista.pinza_clic.connect(self._pinza)
        self.vista.boquilla_clic.connect(self._boquilla)
        self.panel_paciente.agregar(self.vista)
        self.lbl_paciente = etiqueta('', rol='hint')
        self.lbl_paciente.setWordWrap(True)
        self.panel_paciente.agregar(self.lbl_paciente)
        campos = Campos()
        self.cmb_sexo = QComboBox()
        self.cmb_sexo.addItem('Masculino', 'M')
        self.cmb_sexo.addItem('Femenino', 'F')
        campos.agregar('Sexo de nacimiento', self.cmb_sexo)
        self.spin_edad = self._spin(0, 99, 1, ' años')
        campos.agregar('Edad', self.spin_edad)
        self.spin_talla = self._spin(0, 230, 0, ' cm')
        campos.agregar('Talla', self.spin_talla)
        self.spin_peso = self._spin(0, 250, 0, ' kg')
        campos.agregar('Peso', self.spin_peso)
        self.cmb_etnia = QComboBox()
        for clave, nombre in E.ETNIAS:
            self.cmb_etnia.addItem(f'GLI-2012 {nombre.lower()}', clave)
        campos.agregar('Valores teóricos', self.cmb_etnia)
        self.panel_paciente.agregar(campos)
        for w in (self.cmb_sexo, self.cmb_etnia):
            w.currentIndexChanged.connect(lambda _i: self.dibujar())
        for w in (self.spin_edad, self.spin_talla, self.spin_peso):
            w.valueChanged.connect(lambda _v: self.dibujar())
        self.panel_paciente.agregar(self._boton('Medir talla y peso', self._medir_talla))
        # El broncodilatador, en el paciente.
        fila = QHBoxLayout()
        self.cmb_bd = QComboBox()
        for clave, nombre, minutos in BRONCODILATADORES:
            self.cmb_bd.addItem(f'{nombre} ({minutos} min)', clave)
        self.cmb_bd.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_bd.setMinimumContentsLength(14)
        fila.addWidget(self.cmb_bd, 1)
        self.btn_bd = self._boton('Dar', self._dar_bd)
        fila.addWidget(self.btn_bd)
        self.panel_paciente.agregar(etiqueta('Broncodilatador', rol='campo'))
        self.panel_paciente.agregar_layout(fila)
        self.lbl_bd = etiqueta('', rol='hint')
        self.lbl_bd.setWordWrap(True)
        self.panel_paciente.agregar(self.lbl_bd)
        self.btn_saltar = self._boton('Saltar la espera (docente)', self._saltar_espera)
        self.btn_saltar.setVisible(False)
        self.panel_paciente.agregar(self.btn_saltar)
        izq.addWidget(self.panel_paciente)

    def _spin(self, lo, hi, dec, sufijo):
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(dec)
        s.setSuffix(sufijo)
        s.setSpecialValueText('—')
        return s

    def _panel_equipo(self, izq):
        self.panel_equipo = Tarjeta('Equipo')
        self.panel_equipo.agregar(self._boton('Verificar con la jeringa de 3 L', self._verificar))
        self.panel_equipo.agregar(self._boton('Calibrar', self._calibrar))
        self.lbl_equipo = etiqueta('', rol='hint')
        self.lbl_equipo.setWordWrap(True)
        self.panel_equipo.agregar(self.lbl_equipo)
        izq.addWidget(self.panel_equipo)

    def _panel_errores(self, izq):
        self.panel_errores = Tarjeta('Simular error de técnica')
        self.chk_err = {}
        for clave, texto in E.ERRORES + ERRORES_EQUIPO:
            c = QCheckBox(texto)
            c.clicked.connect(lambda activo, k=clave: self._error_simulado(k, activo))
            self.chk_err[clave] = c
            self.panel_errores.agregar(c)
        izq.addWidget(self.panel_errores)

    def _pantalla(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        barra = Tarjeta()
        barra.cuerpo.setContentsMargins(10, 8, 10, 8)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.btn_iniciar = self._boton('Iniciar', self._iniciar, True)
        self.btn_terminar = self._boton('Terminar', self._terminar)
        self.btn_cancelar = self._boton('Cancelar', self._cancelar)
        self.btn_cero = self._boton('Cero de flujo', self._cero)
        self.btn_cero.setToolTip('Con el sensor quieto y sin corrientes de aire')
        for b in (self.btn_iniciar, self.btn_terminar, self.btn_cancelar, self.btn_cero):
            fila.addWidget(b)
        fila.addStretch(1)
        self.pill_ambiente = Pastilla('', 'neutro')
        self.pill_ambiente.setToolTip('Temperatura, humedad y presión de la sala: el equipo corrige a BTPS')
        fila.addWidget(self.pill_ambiente)
        barra.agregar_layout(fila)
        fila2 = QHBoxLayout()
        fila2.setSpacing(6)
        self.btn_ind = {}
        for i, (clave, texto) in enumerate(E.INDICACIONES, start=1):
            b = self._boton(f'{i} · «{texto}»', lambda k=clave: self._indicar(k))
            b.setToolTip(f'Atajo: tecla {i}')
            self.btn_ind[clave] = b
            fila2.addWidget(b)
            atajo = QShortcut(QKeySequence(str(i)), self)
            atajo.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            atajo.activated.connect(lambda k=clave: self._indicar(k))
        barra.agregar_layout(fila2)
        layout.addWidget(barra)

        self.graficos = GraficosEspiro()
        curvas = QSplitter(Qt.Orientation.Horizontal)
        for titulo, w in (('Flujo-volumen', self.graficos.fv), ('Volumen-tiempo', self.graficos.vt)):
            caja = Tarjeta(titulo)
            caja.agregar(w, 1)
            curvas.addWidget(caja)
        curvas.setStretchFactor(0, 3)
        curvas.setStretchFactor(1, 2)

        abajo = Tarjeta('Maniobras')
        self.tabla = QTableWidget(0, 0)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.itemSelectionChanged.connect(self._al_seleccionar)
        abajo.agregar(self.tabla, 1)
        self.lbl_calidad = etiqueta('', rol='hint')
        self.lbl_calidad.setWordWrap(True)
        abajo.agregar(self.lbl_calidad)
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(curvas)
        vertical.addWidget(abajo)
        vertical.setStretchFactor(0, 3)
        vertical.setStretchFactor(1, 2)
        layout.addWidget(vertical, 1)
        return contenedor

    def _pestana_informe(self):
        """La tabla entera y, debajo, el texto: con barra si no cabe (a
        1366×768 no cabe)."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        resultados = Tarjeta('Resultados (formato del manual SER 2024)')
        self.tabla_informe = Tabla()
        resultados.agregar(self.tabla_informe)
        self.lbl_informe = etiqueta('', rol='hint')
        self.lbl_informe.setWordWrap(True)
        resultados.agregar(self.lbl_informe)
        self.lbl_avisos = etiqueta('', rol='hint')
        self.lbl_avisos.setWordWrap(True)
        self.lbl_avisos.setStyleSheet(f'color: {tema.AVISO};')
        resultados.agregar(self.lbl_avisos)
        layout.addWidget(resultados)
        caja = Tarjeta('Informe')
        caja.agregar(etiqueta('Última dosis de broncodilatador del paciente (cuál y hace cuántas horas)', rol='campo'))
        self.txt_bd_previo = QLineEdit()
        caja.agregar(self.txt_bd_previo)
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

    def _paneles(self):
        return [self.panel_paciente, self.panel_equipo, self.panel_errores, self.btn_iniciar, self.btn_cero]

    # --- Ciclo de vida (API que llama main.py) --------------------------

    def la_super(self, data, appointment_id=None):
        self._parar()
        self.sesion = SesionEspiro(data, appointment_id, self._reloj) if data is not None else None
        self.data_caso = data
        self.appointment_id = appointment_id
        self.maniobras = []
        self.verificacion = None
        self.talla_medida = None
        self.seleccion = None
        self.vista.pinza = self.vista.boquilla = False
        for c in self.chk_err.values():
            c.setChecked(False)
        for w in (self.txt_bd_previo, self.txt_hallazgos, self.txt_conclusion):
            w.clear()
        self.estado_informe.limpiar()
        hay = self.sesion is not None and self.sesion.hay_paciente
        for w in self._paneles():
            w.setEnabled(hay)
        self.vista.activo = hay
        self.spin_talla.setValue(0)
        self.spin_peso.setValue(0)
        if hay:
            caso = self.sesion.caso
            self.cmb_sexo.setCurrentIndex(self.cmb_sexo.findData(caso['sexo']))
            self.spin_edad.setValue(caso['edad'])
            self.cmb_etnia.setCurrentIndex(0)
            self._mensaje('Pon la pinza nasal (clic en la nariz) y la boquilla con filtro (clic en la boca), '
                          'mide la talla y verifica el equipo. Cada maniobra: Iniciar y las indicaciones '
                          '(teclas 1 a 5).')
        elif data is not None:
            self._mensaje('Este paciente no tiene espirometría cargada en el caso: el equipo no mide. '
                          'Hace falta el bloque ESPIRO del caso.', 'alerta')
        else:
            self._mensaje('Abre una atención para medir.')
        self.dibujar()

    def report_job(self):
        if not self.data_login or not self.maniobras or self.sesion is None:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        data = {
            'paciente': self._datos(),
            'talla_medida': self.talla_medida,
            'maniobras': [{**m['receta'], 'fase': m['fase'], 'marca': m['marca']} for m in self.maniobras],
            'broncodilatador': self._bd_informe(),
            'verificacion': self.verificacion,
            'ambiente': dict(zip(('temperatura', 'humedad', 'presion'), self.sesion.ambiente())),
            'ecuacion': self._ecuacion(),
            'calidad': getattr(self, '_calidad_texto', {}),
            'tabla': getattr(self.tabla_informe, 'contenido', {}),
            'avisos': [a.lstrip('• ') for a in self.lbl_avisos.text().split('\n') if a.strip()],
            'bd_previo': self.txt_bd_previo.text(),
            'hallazgos': self.txt_hallazgos.toPlainText(),
            'conclusion': self.txt_conclusion.toPlainText(),
        }
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data,
                'images': self._exportar_imagenes}

    def submit_report(self):
        return sesion_nasal.subir_al_cerrar(self)

    def restore_report(self, data):
        """Retomar la atención: las maniobras se rehacen desde su receta
        (fuera de la ventana) y vuelven los datos y el texto."""
        if self.sesion is None or not self.sesion.hay_paciente or self.maniobras or self.registro:
            return False
        p = data.get('paciente') or {}
        if p.get('sexo') in ('M', 'F'):
            self.cmb_sexo.setCurrentIndex(self.cmb_sexo.findData(p['sexo']))
        for spin, k in ((self.spin_edad, 'edad'), (self.spin_talla, 'talla'), (self.spin_peso, 'peso')):
            if isinstance(p.get(k), (int, float)):
                spin.setValue(p[k])
        i = self.cmb_etnia.findData(p.get('etnia'))
        if i >= 0:
            self.cmb_etnia.setCurrentIndex(i)
        self.talla_medida = data.get('talla_medida')
        self.verificacion = data.get('verificacion')
        bd = data.get('broncodilatador')
        if isinstance(bd, dict) and bd.get('clave') in dict((k, n) for k, n, _m in BRONCODILATADORES):
            self.sesion.dar_bd(bd['clave'], ya=True)
        self.txt_bd_previo.setText(data.get('bd_previo') or '')
        self.txt_hallazgos.setPlainText(data.get('hallazgos') or '')
        self.txt_conclusion.setPlainText(data.get('conclusion') or '')
        recetas = [m for m in (data.get('maniobras') or [])
                   if isinstance(m, dict) and m.get('semilla') and m.get('muestras')]
        if not recetas:
            self.dibujar()
            return True
        pulmon, sesion_actual = self.sesion.caso['pulmon'], self.sesion

        def calcular():
            return [(m, E.rehace(pulmon, m)) for m in recetas]

        def listo(hechas):
            if self.sesion is not sesion_actual or self.maniobras:
                return
            for receta, reg in hechas:
                r = E.analizar(reg.flujos)
                if r is None:
                    continue
                self.maniobras.append({'receta': {k: v for k, v in receta.items() if k not in ('fase', 'marca')},
                                       'fase': receta.get('fase', 'pre'), 'marca': receta.get('marca', ''),
                                       'flujos': reg.flujos, 'r': r, 'verdad': reg.verdad})
            self.sesion.n = max(self.sesion.n, len(recetas))
            self._mensaje('Se recuperaron las maniobras guardadas de esta atención.', 'ok')
            self.dibujar()

        self.tarea = hilos.en_fondo(calcular, listo=listo, dueno=self, nombre='recuperar espirometría')
        return True

    def showEvent(self, evento):
        self._cada_segundo()
        super().showEvent(evento)

    # --- Acciones del alumno -------------------------------------------

    def _log(self, accion, **payload):
        if self.sesion is None or not self.sesion.hay_paciente:
            return
        sesion_nasal.registrar(f'{self.EQUIPO}_{accion}', self.data_caso, self.appointment_id, **payload)

    def _mensaje(self, texto, estado=None):
        self.lbl_mensaje.setText(texto)
        color = {'alerta': tema.ALERTA, 'ok': tema.OK}.get(estado, tema.TEXTO_SUAVE)
        self.lbl_mensaje.setStyleSheet(f'color: {color};')

    def _datos(self):
        return {'sexo': self.cmb_sexo.currentData(), 'edad': self.spin_edad.value(),
                'talla': self.spin_talla.value(), 'peso': self.spin_peso.value(),
                'etnia': self.cmb_etnia.currentData()}

    def _ecuacion(self):
        return f'GLI-2012, grupo {dict(E.ETNIAS)[self.cmb_etnia.currentData()].lower()}'

    def _pinza(self):
        if self.registro is not None:
            return
        self.vista.pinza = not self.vista.pinza
        self._log('pinza', puesta=self.vista.pinza)
        self.dibujar()

    def _boquilla(self):
        if self.registro is not None:
            return
        self.vista.boquilla = not self.vista.boquilla
        self._log('boquilla', puesta=self.vista.boquilla)
        self.dibujar()

    def _medir_talla(self):
        b = self.sesion.caso['bloque']
        self.spin_talla.setValue(b['talla'])
        self.spin_peso.setValue(b['peso'])
        self.talla_medida = {'talla': b['talla'], 'peso': b['peso']}
        self._log('medir', talla=b['talla'], peso=b['peso'])
        self._mensaje(f'Tallímetro, sin zapatos: {l(b["talla"], 0)} cm. Pesa: {l(b["peso"], 0)} kg.')

    def _verificar(self):
        resultados, ok = E.verificar(self.sesion.calibracion, f'esp-jeringa/{self.appointment_id}/{time.time()}')
        self.verificacion = {'ok': ok, 'descargas': resultados}
        self._log('verificar', ok=ok, descargas=resultados, calibracion=self.sesion.calibracion)
        self.dibujar()

    def _calibrar(self):
        anterior = self.sesion.calibracion
        self.sesion.calibracion = 1 + random.gauss(0, 0.003)
        self.chk_err['descalibrado'].setChecked(False)
        self.verificacion = None
        self._log('calibrar', antes=anterior, despues=self.sesion.calibracion)
        self._mensaje('Equipo calibrado con la jeringa de 3 L. Verifícalo antes de seguir.', 'ok')
        self.dibujar()

    def _cero(self):
        if self.registro is not None:
            return
        self._log('cero', habia=self.sesion.cero)
        self.sesion.cero = 0.0
        self.chk_err['cero'].setChecked(False)
        self._mensaje('Flujo en cero, con el sensor quieto.', 'ok')
        self.dibujar()

    def _error_simulado(self, clave, activo):
        if clave == 'cero':
            self.sesion.cero = random.choice((-1, 1)) * random.uniform(0.03, 0.06) if activo else 0.0
        elif clave == 'descalibrado':
            self.sesion.calibracion = random.choice((0.94, 1.06)) if activo else 1 + random.gauss(0, 0.003)
        self._log('error_simulado', error=clave, activo=activo)
        self.dibujar()

    def _dar_bd(self):
        if self.sesion.bd or self.registro is not None:
            return
        if not any(m['fase'] == 'pre' for m in self.maniobras):
            self._mensaje('Primero la espirometría basal: el broncodilatador va después.', 'alerta')
            return
        clave = self.cmb_bd.currentData()
        self.sesion.dar_bd(clave)
        self._log('broncodilatador', farmaco=clave)
        nombre, minutos = next((n, m) for k, n, m in BRONCODILATADORES if k == clave)
        self._mensaje(f'{nombre}. Las maniobras que siguen son post broncodilatador; el efecto pleno '
                      f'llega a los {minutos} minutos.')
        self.dibujar()

    def _saltar_espera(self):
        self.sesion.saltar_espera()
        self._log('saltar_espera')
        self._cada_segundo()

    def _bd_informe(self):
        bd = self.sesion.bd if self.sesion else None
        if not bd:
            return None
        clave, nombre, minutos = next(x for x in BRONCODILATADORES if x[0] == bd['farmaco'])
        posts = [m['receta'].get('s_desde_bd') for m in self.maniobras if m['fase'] == 'post']
        primera = min((s for s in posts if s is not None), default=None)
        return {'clave': clave, 'nombre': nombre, 'espera_min': minutos,
                'minutos_primera': None if primera is None else round(primera / 60)}

    # --- La maniobra ----------------------------------------------------

    def _iniciar(self):
        if self.registro is not None or self.sesion is None or not self.sesion.hay_paciente:
            return
        if not self.vista.boquilla:
            self._mensaje('Falta la boquilla con el filtro (clic en la boca del paciente).', 'alerta')
            return
        d = self._datos()
        if not d['talla'] or not d['edad']:
            self._mensaje('Faltan la edad o la talla del paciente: sin ellas no hay valores teóricos.', 'alerta')
            return
        fase = self.sesion.fase()
        if sum(1 for m in self.maniobras if m['fase'] == fase) >= MAX_MANIOBRAS:
            self._mensaje(f'Ya van {MAX_MANIOBRAS} maniobras {FASES[fase].lower()}: es el máximo del manual.',
                          'alerta')
            return
        errores = [k for k, _t in E.ERRORES if self.chk_err[k].isChecked()]
        receta = {'semilla': self.sesion.semilla(), 'frac_bd': self.sesion.frac_bd(), 'errores': errores,
                  'cero': self.sesion.cero, 'calibracion': self.sesion.calibracion,
                  'pinza': self.vista.pinza, 'comandos': []}
        if self.sesion.bd:
            receta['s_desde_bd'] = self.sesion.desde_bd()
        self.registro = E.Registro(self.sesion.caso['pulmon'], receta)
        self.registro_fase = fase
        self._t_inicio = self._reloj()
        self.vista.fuga = 'fuga' in self.registro.errores
        self._log('iniciar', fase=fase, n=self.sesion.n, datos=d, errores=errores, pinza=self.vista.pinza,
                  cero=self.sesion.cero, calibracion=self.sesion.calibracion, frac_bd=receta['frac_bd'])
        self.timer.start()
        self._mensaje('Registrando. Que respire tranquilo unas veces antes de pedirle el aire.')
        self.dibujar()

    def _indicar(self, clave):
        if self.registro is None:
            return
        self._tic()
        self.registro.indicar(clave)
        self._log('indicacion', clave=clave, t=round(self.registro.i * E.DT, 2))

    def _tic(self):
        reg = self.registro
        if reg is None:
            return
        objetivo = int((self._reloj() - self._t_inicio) * E.HZ)
        if objetivo > reg.i:
            reg.avanzar(min(objetivo - reg.i, E.HZ))
        self.vista.soplando = reg.estado == 'espira'
        self.lbl_paciente.setText(ESTADOS_PACIENTE.get(reg.estado, ''))
        self.vista.update()
        self.graficos.vivo(reg.flujos)
        if reg.terminada:
            self._terminar()

    def _terminar(self):
        reg = self.registro
        if reg is None:
            return
        self._parar()
        r = E.analizar(reg.flujos)
        if r is None:
            self._log('cancelar', motivo='sin espiración forzada', t=round(reg.i * E.DT, 2))
            self._mensaje('No hubo espiración forzada: la maniobra no se guarda.', 'alerta')
            self.dibujar()
            return
        reg.receta['muestras'] = reg.i
        m = {'receta': reg.receta, 'fase': self.registro_fase, 'marca': '', 'flujos': reg.flujos,
             'r': r, 'verdad': reg.verdad}
        self.maniobras.append(m)
        self.seleccion = None
        fase = [x for x in self.maniobras if x['fase'] == m['fase']]
        cal = E.resumen_fase(fase)['calificacion'][-1]
        self._log('maniobra', fase=m['fase'], n=len(fase), resultado={k: v for k, v in r.items()
                                                                       if not k.startswith('i_')},
                  calificacion={'fev1': cal[0], 'fvc': cal[1], 'motivos': cal[2]}, verdad=reg.verdad,
                  receta=reg.receta)
        texto = f'Maniobra {len(fase)} {FASES[m["fase"]].lower()}: FEV1 {E.NOMBRE_CAL[cal[0]]}, FVC {E.NOMBRE_CAL[cal[1]]}.'
        if cal[2]:
            texto += ' ' + '; '.join(cal[2]).capitalize() + '.'
        self._mensaje(texto, 'ok' if cal[0] == cal[1] == 'aceptable' else None)
        self.dibujar()

    def _cancelar(self):
        if self.registro is None:
            return
        self._log('cancelar', motivo='alumno', t=round(self.registro.i * E.DT, 2))
        self._parar()
        self._mensaje('Maniobra cancelada: no se guarda.')
        self.dibujar()

    def _parar(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.registro = None
        if hasattr(self, 'graficos'):
            self.graficos.limpiar_vivo()
            self.vista.soplando = False
            self.lbl_paciente.setText('')

    def _marcar(self, i, marca):
        if not 0 <= i < len(self.maniobras) or self.maniobras[i]['marca'] == marca:
            return
        m = self.maniobras[i]
        m['marca'] = marca
        n = sum(1 for x in self.maniobras[:i + 1] if x['fase'] == m['fase'])
        self._log('marca', fase=m['fase'], n=n, marca=marca, verdad=m['verdad'])
        self.dibujar()

    def _al_seleccionar(self):
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.selectionModel() else []
        nueva = filas[0].row() if filas else None
        if nueva != self.seleccion:
            self.seleccion = nueva
            self._dibujar_curvas()

    def _cada_segundo(self):
        if self.sesion is None or not self.sesion.hay_paciente:
            self.pill_ambiente.setVisible(False)
            return
        t, h, pr = self.sesion.ambiente()
        self.pill_ambiente.set(f'{l(t, 1)} °C · {h} % · {pr} hPa')
        self.pill_ambiente.setVisible(True)
        self._pintar_bd()

    def _pintar_bd(self):
        bd = self.sesion.bd if self.sesion else None
        self.btn_bd.setEnabled(not bd)
        self.cmb_bd.setEnabled(not bd)
        if not bd:
            self.lbl_bd.setText('')
            self.btn_saltar.setVisible(False)
            self.pill_fase.set('Pre broncodilatador', 'neutro')
            return
        falta = self.sesion.falta_bd()
        nombre = next(n for k, n, _m in BRONCODILATADORES if k == bd['farmaco'])
        if falta > 0:
            self.lbl_bd.setText(f'{nombre}: faltan {int(falta // 60)}:{int(falta % 60):02d} para el efecto pleno.')
        else:
            self.lbl_bd.setText(f'{nombre}: ya pasó el tiempo de espera.')
        self.btn_saltar.setVisible(self.es_docente and falta > 0)
        self.pill_fase.set('Post broncodilatador', 'acento')

    # --- Dibujo ---------------------------------------------------------

    def dibujar(self):
        hay = self.sesion is not None and self.sesion.hay_paciente
        grabando = self.registro is not None
        self.btn_iniciar.setEnabled(hay and not grabando)
        self.btn_terminar.setEnabled(grabando)
        self.btn_cancelar.setEnabled(grabando)
        self.btn_cero.setEnabled(hay and not grabando)
        for b in self.btn_ind.values():
            b.setEnabled(grabando)
        self.vista.update()
        self._cada_segundo()
        self._pintar_equipo()
        self._pintar_tabla()
        self._dibujar_curvas()
        self._pintar_informe()
        if self.verdad is not None:
            self.verdad.setText(self._texto_verdad() if hay else '')

    def _pintar_equipo(self):
        if self.sesion is None or not self.sesion.hay_paciente:
            self.lbl_equipo.setText('')
            return
        v = self.verificacion
        if not v:
            self.lbl_equipo.setText('Sin verificar en esta atención.')
            self.lbl_equipo.setStyleSheet(f'color: {tema.AVISO};')
            return
        partes = [f'{d["flujo"]} ({l(d["l_s"], 1)} L/s): {l(d["medido"], 3)} L ({d["error_pct"]:+.1f} %)'.replace('.', ',')
                  for d in v['descargas']]
        self.lbl_equipo.setText(('Verificación correcta (±3 %): ' if v['ok'] else 'Fuera de ±3 %: calibrar. ')
                                + '; '.join(partes) + '.')
        self.lbl_equipo.setStyleSheet(f'color: {tema.OK if v["ok"] else tema.ALERTA};')

    def _fases(self):
        """{fase: (maniobras, resumen)} de las fases con maniobras."""
        out = {}
        for fase in FASES:
            ms = [m for m in self.maniobras if m['fase'] == fase]
            if ms:
                out[fase] = (ms, E.resumen_fase(ms))
        return out

    def _pintar_tabla(self):
        cab = ['Fase', 'N°', 'FVC', 'FEV1', 'FEV1/FVC', 'PEF', 'TEF', 'BEV', 'CVIF', 'FEV1', 'FVC', 'Lo que viste']
        self.tabla.blockSignals(True)
        self.tabla.clear()
        self.tabla.setColumnCount(len(cab))
        self.tabla.setHorizontalHeaderLabels(cab)
        self.tabla.setRowCount(len(self.maniobras))
        fases = self._fases()
        cuenta = {f: 0 for f in FASES}
        for i, m in enumerate(self.maniobras):
            ms, res = fases[m['fase']]
            k = next(j for j, x in enumerate(ms) if x is m)
            cuenta[m['fase']] += 1
            cal = res['calificacion'][k]
            r = m['r']
            celdas = [FASES[m['fase']], str(cuenta[m['fase']]), l(r['fvc']), l(r['fev1']),
                      l(r['fev1'] / r['fvc'] * 100, 1) if r['fvc'] else '—', l(r['pef'], 1), l(r['tef'], 1),
                      f'{r["bev"] * 1000:.0f} mL', l(r['cvif']), E.NOMBRE_CAL[cal[0]], E.NOMBRE_CAL[cal[1]]]
            for j, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j in (9, 10):
                    c = cal[j - 9]
                    item.setForeground(QColor(tema.OK if c == 'aceptable' else
                                              tema.AVISO if c == 'utilizable' else tema.ALERTA))
                if j == 0:
                    item.setForeground(QColor(PRE if m['fase'] == 'pre' else POST))
                if cal[2]:
                    item.setToolTip('; '.join(cal[2]))
                self.tabla.setItem(i, j, item)
            combo = QComboBox()
            for clave, texto in E.MARCAS:
                combo.addItem(texto, clave)
            combo.setCurrentIndex(combo.findData(m['marca']))
            combo.currentIndexChanged.connect(lambda _x, fila=i, c=combo: self._marcar(fila, c.currentData()))
            self.tabla.setCellWidget(i, len(cab) - 1, combo)
        if self.seleccion is not None and self.seleccion < len(self.maniobras):
            self.tabla.selectRow(self.seleccion)
        self.tabla.blockSignals(False)
        lineas = []
        self._calidad_texto = {}
        for fase, (ms, res) in fases.items():
            texto = f'VEF1 {res["grado_fev1"]}, CVF {res["grado_fvc"]}'
            self._calidad_texto[fase] = texto
            dif = '; '.join(f'{nombre} {l(res[f"dif_{par}"])} L' for par, nombre in (('fev1', 'FEV1'), ('fvc', 'FVC'))
                            if res[f'dif_{par}'] is not None)
            lineas.append(f'{FASES[fase]}: {texto} ({res["n_fev1"]} con FEV1 aceptable, {res["n_fvc"]} con FVC '
                          f'aceptable{"; diferencia de las dos mayores: " + dif if dif else ""}).')
        self.lbl_calidad.setText(' '.join(lineas) or 'Todavía no hay maniobras.')

    def _mejores(self):
        out = {}
        for fase, (ms, res) in self._fases().items():
            if res['mejor'] is not None:
                out[fase] = (ms[res['mejor']], res)
        return out

    def _dibujar_curvas(self, para_informe=False):
        curvas = []
        mejores = self._mejores()
        for fase, (m, _res) in mejores.items():
            curvas.append((m, PRE if fase == 'pre' else POST, fase == 'post', 2.4))
        if not para_informe and self.seleccion is not None and self.seleccion < len(self.maniobras):
            m = self.maniobras[self.seleccion]
            if all(m is not c[0] for c in curvas):
                curvas.append((m, tema.ACENTO, False, 1.8))
        self.graficos.dibujar(curvas)

    def _exportar_imagenes(self):
        temp = context.get_resource('local_cache/nasal/temp')
        os.makedirs(temp, exist_ok=True)
        self._dibujar_curvas(para_informe=True)
        imagenes = {}
        for sufijo in ('esp_fv', 'esp_vt'):
            ruta = os.path.join(temp, f'upload_{sufijo}.jpg')
            try:
                self.graficos.exportar(sufijo, ruta)
            except Exception as exc:  # noqa: BLE001 -- sin imagen el informe sube igual
                print(f'{self.TIPO}: no se pudo exportar {sufijo}: {exc}')
                continue
            imagenes[sufijo] = ruta
        self._dibujar_curvas()
        return imagenes

    def _pintar_informe(self):
        """La tabla del manual SER 2024: teórico, pre, % teórico, LIN, z,
        post, % teórico, z y cambio (en litros y sobre el teórico)."""
        d = self._datos()
        cab = ['', 'Teór.', 'Pre', '% Teór.', 'LIN', 'z', 'Post', '% Teór.', 'z', 'Cambio (L)', 'Cambio (% teór.)']
        mejores = self._mejores()
        fases = self._fases()
        if not fases or not d['talla'] or not d['edad']:
            self.tabla_informe.poblar(cab, [])
            self.lbl_informe.setText('Sin maniobras.' if not fases else 'Faltan la edad o la talla.')
            self.lbl_avisos.setText('')
            return
        s, e, t, et = d['sexo'], d['edad'], d['talla'], d['etnia']
        prev = {par: E.previsto(s, par, e, t, et) for par in E.PARES}
        lin = {par: E.lin(s, par, e, t, et) for par in E.PARES}
        val = {}
        for fase, (ms, res) in fases.items():
            fev1, fvc = res['fev1'], res['fvc']
            mejor = mejores.get(fase, (None,))[0]
            val[fase] = {'FVC': fvc, 'FEV1': fev1,
                         'FEV1FVC': fev1 / fvc if fev1 and fvc else None,
                         'PEF': mejor['r']['pef'] if mejor else None,
                         'TEF': mejor['r']['tef'] if mejor else None,
                         'CVIF': mejor['r']['cvif'] if mejor else None,
                         'FIF50': mejor['r']['fif50'] if mejor else None,
                         'FEF50': mejor['r']['fef50'] if mejor else None}

        def z(par, fase):
            v = val.get(fase, {}).get(par)
            return E.zscore(s, par, v, e, t, et) if v else None

        def pc(par, fase, ref='FVC'):
            v = val.get(fase, {}).get(par)
            return v / prev[ref] * 100 if v else None

        filas = []
        for par, nombre, factor, dec in (('FVC', 'CVF (L)', 1, 2), ('FEV1', 'VEF1 (L)', 1, 2),
                                         ('FEV1FVC', 'VEF1/CVF (%)', 100, 1)):
            pre_v, post_v = val.get('pre', {}).get(par), val.get('post', {}).get(par)
            cambio_l, cambio_pc = (E.respuesta_bd(pre_v, post_v, prev[par]) if par != 'FEV1FVC' else (None, None))
            celdas = [nombre, l(prev[par] * factor, dec), l(pre_v * factor if pre_v else None, dec),
                      l(pc(par, 'pre', par), 0) if par != 'FEV1FVC' else '', l(lin[par] * factor, dec),
                      l(z(par, 'pre')), l(post_v * factor if post_v else None, dec),
                      l(pc(par, 'post', par), 0) if par != 'FEV1FVC' else '', l(z(par, 'post')),
                      f'{cambio_l:+.2f}'.replace('.', ',') if cambio_l is not None else '',
                      f'{cambio_pc:+.1f}'.replace('.', ',') if cambio_pc is not None else '']
            marcas = {}
            for col, fase in ((2, 'pre'), (6, 'post')):
                zz = z(par, fase)
                if zz is not None and zz < E.Z_LIN:
                    marcas[col] = 'fuera'
            if cambio_pc is not None and cambio_pc > 10:
                marcas[10] = 'ok'
            filas.append((celdas, None, marcas))
        filas.append((['FEM (L/s)', '', l(val.get('pre', {}).get('PEF'), 1), '', '', '',
                       l(val.get('post', {}).get('PEF'), 1), '', '', '', ''], None, {}))
        filas.append((['TEF (s)', '', l(val.get('pre', {}).get('TEF'), 1), '', '', '',
                       l(val.get('post', {}).get('TEF'), 1), '', '', '', ''], None, {}))
        filas.append((['CVIF (L)', l(prev['FVC']), l(val.get('pre', {}).get('CVIF')),
                       l(pc('CVIF', 'pre'), 0), l(lin['FVC']), '', l(val.get('post', {}).get('CVIF')),
                       l(pc('CVIF', 'post'), 0), '', '', ''], None, {}))
        # Para sospechar una obstrucción de la vía aérea superior (H30).
        ovas = {}
        for fase in val:
            v = val[fase]
            ovas[fase] = (v['FIF50'], v['FEF50'] / v['FIF50'] if v['FEF50'] and v['FIF50'] else None,
                          v['FEV1'] * 1000 / (v['PEF'] * 60) if v['FEV1'] and v['PEF'] else None)
        for k, nombre, dec in ((0, 'FIF50 (L/s)', 2), (1, 'FEF50/FIF50', 2), (2, 'VEF1 (mL)/FEM (L/min)', 1)):
            filas.append(([nombre, '', l(ovas.get('pre', (None,) * 3)[k], dec), '', '', '',
                           l(ovas.get('post', (None,) * 3)[k], dec), '', '', '', ''], None, {}))
        self.tabla_informe.poblar(cab, filas)
        partes = [f'Valores teóricos: {self._ecuacion()}.']
        bd = self._bd_informe()
        if bd:
            partes.append(f'Broncodilatador: {bd["nombre"]}' + (f'; primera maniobra post a los '
                                                               f'{bd["minutos_primera"]} min.' if bd['minutos_primera'] is not None else '.'))
        partes.append('Calidad: ' + '; '.join(f'{FASES[f].lower()} {txt}' for f, txt in self._calidad_texto.items()) + '.')
        self.lbl_informe.setText(' '.join(partes))
        self.lbl_avisos.setText('\n'.join(f'• {a}' for a in self._avisos(fases)))

    def _avisos(self, fases):
        avisos = []
        if not self.verificacion:
            avisos.append('El equipo no se verificó con la jeringa de 3 L en esta atención.')
        elif not self.verificacion['ok']:
            avisos.append('La última verificación con la jeringa quedó fuera de ±3 %.')
        for fase, (ms, res) in fases.items():
            n_ok = min(res['n_fev1'], res['n_fvc'])
            if n_ok < 3:
                avisos.append(f'{FASES[fase]}: {n_ok} maniobras aceptables (se buscan 3).')
            for k, m in enumerate(ms, start=1):
                r = m['r']
                if r['corrientes'] < 3:
                    avisos.append(f'{FASES[fase]} {k}: {r["corrientes"]} respiraciones tranquilas antes de la '
                                  'inspiración máxima (se piden 3 a 5).')
                if r['deriva'] is not None and abs(r['deriva']) > 0.08:
                    avisos.append(f'{FASES[fase]} {k}: la línea de base de las respiraciones tranquilas se '
                                  'corre (¿cero de flujo?).')
                if r['cvif'] is not None and r['cvif'] < 0.7 * r['fvc']:
                    avisos.append(f'{FASES[fase]} {k}: sin inspiración forzada completa al final.')
        bd = self._bd_informe()
        if bd and bd['minutos_primera'] is not None and bd['minutos_primera'] < bd['espera_min']:
            avisos.append(f'La primera maniobra post fue a los {bd["minutos_primera"]} min '
                          f'(el protocolo espera {bd["espera_min"]}).')
        return avisos

    def _texto_verdad(self):
        caso = self.sesion.caso
        b, p = caso['bloque'], caso['pulmon']
        filas = [f'<b>Paciente</b>: {"hombre" if caso["sexo"] == "M" else "mujer"}, {caso["edad"]:.0f} años, '
                 f'talla real {b["talla"]:.0f} cm (escrita: {self.spin_talla.value():.0f}), colaboración '
                 f'{p.colaboracion}.']
        for nombre, d in (('Antes del broncodilatador', p.pre), ('Con efecto pleno', p.bd)):
            filas.append(f'<b>{nombre}</b>, maniobra perfecta: FVC {l(d["fvc"])} L, FEV1 {l(d["fev1"])} L '
                         f'({l(d["fev1"] / d["fvc"] * 100, 0)} %), PEF {l(d["pef"], 1)} L/s.')
        if p.tope_e or p.tope_i:
            filas.append(f'<b>Obstrucción de la vía aérea superior</b>: tope espiratorio '
                         f'{l(p.tope_e, 1) if p.tope_e else "no"}, inspiratorio {l(p.tope_i, 1) if p.tope_i else "no"} L/s.')
        filas.append(f'<b>Equipo</b>: calibración ×{l(self.sesion.calibracion, 3)}; cero corrido '
                     f'{l(self.sesion.cero, 3)} L/s.')
        if self.sesion.bd:
            filas.append(f'<b>Broncodilatador</b>: efecto ahora {self.sesion.frac_bd() * 100:.0f} %.')
        for fase, (ms, _res) in self._fases().items():
            for k, m in enumerate(ms, start=1):
                v = m['verdad']
                cosas = [f'esfuerzo {v["esfuerzo"] * 100:.0f} %']
                if v.get('pausa_tlc') is not None:
                    cosas.append(f'pausa en TLC {l(v["pausa_tlc"], 1)} s')
                if not v.get('parto_tlc'):
                    cosas.append('no partió de TLC')
                if v['f_tlc'] < 0.98:
                    cosas.append(f'inspiró {v["f_tlc"] * 100:.0f} % de la capacidad vital')
                if v['errores']:
                    cosas.append('errores: ' + ', '.join(dict(E.ERRORES)[e].lower() for e in v['errores'])
                                 + (' (propio del paciente)' if v.get('error_propio') else ''))
                if v.get('fin'):
                    cosas.append(f'terminó: {v["fin"]}')
                if not v.get('cvif_forzada'):
                    cosas.append('sin inspiración forzada al final')
                if not m['receta'].get('pinza', True):
                    cosas.append('sin pinza nasal')
                filas.append(f'<b>{FASES[fase]} {k}</b>: ' + '; '.join(cosas) + '.')
        return '<br>'.join(filas)
