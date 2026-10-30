"""El prick test de LabSim (H29 del libro), demo interna del Box Rinología.

Como se hace en la sala: el alumno pregunta por los fármacos, elige un
extracto y hace clic en el antebrazo volar para marcar el sitio y poner la
gota; después puncha cada gota (una lanceta nueva por gota: si no la
cambia, lleva el alérgeno anterior), seca y espera con el cronómetro. Las
pápulas crecen con el reloj: la histamina primero, los alérgenos a los
15-20 minutos. Con la lupa y la regla mide el diámetro mayor y el
perpendicular de cada pápula (la pápula, no el eritema), los anota en la
hoja y decide el resultado: primero los controles, después los alérgenos.

No hay equipo que calcule nada: la hoja es lo que el alumno midió. La piel
del caso, lo que de verdad hay en cada sitio y lo que hizo mal (punciones a
menos de 2 cm o cerca de un pliegue, lanceta reusada, orden de las gotas,
lectura fuera de tiempo) van a "Lo que el equipo no sabe" (docente) y al
log, con prefijo prick_.

El informe PRICK guarda los sitios y las lecturas: al retomar la atención
vuelven, con las pápulas como a los 20 minutos. Sin `cases.data['PRICK']`
no se hace la prueba.
"""

import math
import os
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QFrame,
                               QHBoxLayout, QHeaderView, QLineEdit, QListWidget, QListWidgetItem,
                               QMainWindow, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
                               QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget)

from core import tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import prick as P
from nasal import sesion as sesion_nasal
from nasal.equipos import PERMISOS_DOCENTE, QSS_NASAL, num
from vemp.widgets.kit import Pastilla, Tarjeta, etiqueta

MODOS = (('marcar', 'Marcar'), ('puncionar', 'Puncionar'), ('quitar', 'Quitar'))
RESULTADOS_ALERGENO = (('', '—'), ('positivo', 'Positivo'), ('negativo', 'Negativo'))
RESULTADOS_CONTROL = (('', '—'), ('valido', 'Válido'), ('no_valido', 'No válido'))
LUPA_MM = 34           # ancho de lo que muestra la lupa
PIEL = QColor('#EBC7AB')
PIEL_BORDE = QColor('#C99C7E')


def n(v, d=1):
    return num(v, d)


def _horas_texto(h):
    if h < 1:
        return 'hace menos de una hora'
    if h < 48:
        return f'hace {round(h)} horas'
    return f'hace {round(h / 24)} días'


# ── La atención ─────────────────────────────────────────────────────────────

class SesionPrick:
    def __init__(self, data, appointment_id, reloj=time.monotonic):
        self.caso = P.desde_caso(data)
        self.appointment_id = appointment_id
        self._reloj = reloj
        self.pregunto = False

    @property
    def hay_paciente(self):
        return self.caso is not None

    @property
    def piel(self):
        return self.caso['piel']

    def minuto(self):
        return self._reloj() / 60

    def respuesta_farmacos(self):
        f = self.piel['farmaco']
        if not f:
            return '«Para la alergia no tomo nada. Paracetamol de vez en cuando, nada más.»'
        nombre = P.NOMBRE_FARMACO[f['clave']]
        return f'«Tomo {nombre.lower()}; la última vez fue {_horas_texto(f["horas"])}.»'


# ── El antebrazo ────────────────────────────────────────────────────────────

def pintar_piel(p):
    """El antebrazo volar en mm (x desde la línea media, y desde el codo)."""
    camino = QPainterPath()
    arriba, abajo = -28, P.LARGO + 22
    a0, a1 = P.ANCHO_CODO / 2 + 6, P.ANCHO_MUNECA / 2 + 2
    camino.moveTo(-a0, arriba)
    camino.lineTo(a0, arriba)
    camino.cubicTo(a0, P.LARGO * 0.4, a1 + 4, P.LARGO * 0.8, a1, abajo)
    camino.lineTo(-a1, abajo)
    camino.cubicTo(-a1 - 4, P.LARGO * 0.8, -a0, P.LARGO * 0.4, -a0, arriba)
    p.setPen(QPen(PIEL_BORDE, 0.8))
    p.setBrush(PIEL)
    p.drawPath(camino)
    # Los pliegues del codo y de la muñeca.
    p.setPen(QPen(QColor(150, 105, 85, 170), 0.9))
    for y, ancho in ((0, P.ANCHO_CODO), (P.LARGO, P.ANCHO_MUNECA)):
        p.drawArc(QRectF(-ancho / 2 + 4, y - 4, ancho - 8, 8), 200 * 16, 140 * 16)


def pintar_sitio(p, s, papula, seleccionado=False, rotulo=5.0):
    """Un sitio en coordenadas de mm: rótulo (alto en mm, 0 sin rótulo),
    gota, punción, eritema y pápula."""
    x, y = s['x'], s['y']
    if papula['eritema'] > 0:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(214, 86, 80, 60))
        p.drawEllipse(QPointF(x, y), papula['eritema'] / 2, papula['eritema'] / 2 * 0.85)
    if papula['mayor'] > 0:
        p.save()
        p.translate(x, y)
        p.rotate(papula['angulo'])
        a, b = papula['menor'] / 2, papula['mayor'] / 2
        p.setPen(QPen(QColor(205, 160, 140), 0.25))
        p.setBrush(QColor(248, 232, 220))
        p.drawEllipse(QPointF(0, 0), a, b)
        for ang in papula['seudopodos']:
            r = math.radians(ang)
            p.drawEllipse(QPointF(math.cos(r) * a * 1.05, math.sin(r) * b * 1.05), a * 0.32, b * 0.22)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 90))
        p.drawEllipse(QPointF(-a * 0.25, -b * 0.3), a * 0.35, b * 0.25)
        p.restore()
    if s.get('puncion') is not None:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(120, 40, 40))
        p.drawEllipse(QPointF(x, y), 0.35, 0.35)
    if s.get('gota') and not s.get('seco'):
        p.setPen(QPen(QColor(110, 150, 190, 200), 0.25))
        p.setBrush(QColor(170, 205, 235, 150))
        p.drawEllipse(QPointF(x, y), 2.0, 2.0)
        p.setBrush(QColor(255, 255, 255, 170))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(x - 0.6, y - 0.7), 0.5, 0.4)
    if rotulo:
        f = QFont()
        f.setPixelSize(max(1, round(rotulo)))
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(40, 60, 120))
        # Al lado de la punción, como el marcador en la piel.
        p.drawText(QRectF(x - 7 - 2 * rotulo, y - rotulo, 2 * rotulo, 2 * rotulo),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, P.ABREV[s['extracto']])
    if seleccionado:
        p.setPen(QPen(QColor(tema.ACENTO), 0.5, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x, y), 7, 7)


class Brazo(QWidget):
    """El antebrazo entero, codo arriba. Clic: marcar, puncionar, quitar o
    elegir un sitio, según el modo."""

    clic = Signal(float, float)        # mm

    def __init__(self, ventana, parent=None):
        super().__init__(parent)
        self.ventana = ventana
        self.activo = False
        self.setMinimumSize(200, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def _transformacion(self):
        alto_mm = P.LARGO + 60
        ancho_mm = P.ANCHO_CODO + 40
        k = min(self.height() / alto_mm, self.width() / ancho_mm)
        return self.width() / 2, (self.height() - alto_mm * k) / 2 + 32 * k, k

    def a_mm(self, pos):
        cx, y0, k = self._transformacion()
        return (pos.x() - cx) / k, (pos.y() - y0) / k

    def mousePressEvent(self, evento):
        if self.activo and evento.button() == Qt.MouseButton.LeftButton:
            self.clic.emit(*self.a_mm(evento.position()))
        super().mousePressEvent(evento)

    def mouseMoveEvent(self, evento):
        x, y = self.a_mm(evento.position())
        self.setCursor(Qt.CursorShape.CrossCursor if self.activo and P.dentro(x, y) else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(evento)

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(tema.TARJETA))
        cx, y0, k = self._transformacion()
        p.translate(cx, y0)
        p.scale(k, k)
        pintar_piel(p)
        f = QFont()
        f.setPixelSize(6)
        p.setFont(f)
        p.setPen(QColor(tema.TEXTO_TENUE))
        p.drawText(QRectF(-60, -26, 120, 8), Qt.AlignmentFlag.AlignCenter, 'pliegue del codo')
        p.drawText(QRectF(-60, P.LARGO + 6, 120, 8), Qt.AlignmentFlag.AlignCenter, 'muñeca')
        v = self.ventana
        for i, s in enumerate(v.sitios):
            pintar_sitio(p, s, v.papula(i), seleccionado=i == v.seleccion)
        # Escala de 1 cm.
        p.setPen(QPen(QColor(tema.TEXTO), 0.6))
        x0, yb = P.ANCHO_CODO / 2 + 2, P.LARGO + 14
        p.drawLine(QPointF(x0, yb), QPointF(x0 + 10, yb))
        p.drawText(QRectF(x0 - 4, yb + 1, 18, 7), Qt.AlignmentFlag.AlignCenter, '1 cm')
        if not self.activo:
            p.resetTransform()
            p.fillRect(self.rect(), QColor(255, 255, 255, 140))
        p.end()


class Lupa(QWidget):
    """El sitio elegido de cerca, con una regla que se arrastra: lo medido
    va a la hoja con los botones de abajo."""

    medida = Signal(float)

    def __init__(self, ventana, parent=None):
        super().__init__(parent)
        self.ventana = ventana
        self._ini = self._fin = None
        self.ultima = None
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, ancho):
        return ancho

    def _transformacion(self):
        lado = min(self.width(), self.height())
        k = lado / LUPA_MM
        return self.width() / 2, self.height() / 2, k

    def _a_mm(self, pos):
        cx, cy, k = self._transformacion()
        return (pos.x() - cx) / k, (pos.y() - cy) / k

    def mousePressEvent(self, evento):
        if self.ventana.seleccion is not None and evento.button() == Qt.MouseButton.LeftButton:
            self._ini = self._fin = self._a_mm(evento.position())
            self.update()
        super().mousePressEvent(evento)

    def mouseMoveEvent(self, evento):
        if self._ini is not None:
            self._fin = self._a_mm(evento.position())
            self.update()
        super().mouseMoveEvent(evento)

    def mouseReleaseEvent(self, evento):
        if self._ini is not None:
            self._fin = self._a_mm(evento.position())
            largo = math.hypot(self._fin[0] - self._ini[0], self._fin[1] - self._ini[1])
            self.ultima = round(largo * 2) / 2      # la regla se lee al medio milímetro
            self.medida.emit(self.ultima)
            self.update()
        super().mouseReleaseEvent(evento)

    def limpiar(self):
        self._ini = self._fin = self.ultima = None
        self.update()

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(tema.TARJETA))
        v = self.ventana
        if v.seleccion is None:
            p.setPen(QColor(tema.TEXTO_TENUE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                       'Elige un sitio en el antebrazo para verlo de cerca y medir.')
            p.end()
            return
        s = v.sitios[v.seleccion]
        cx, cy, k = self._transformacion()
        p.save()
        p.translate(cx, cy)
        p.scale(k, k)
        p.translate(-s['x'], -s['y'])
        p.setClipRect(QRectF(s['x'] - LUPA_MM, s['y'] - LUPA_MM, 2 * LUPA_MM, 2 * LUPA_MM))
        pintar_piel(p)
        for i, o in enumerate(v.sitios):
            if abs(o['x'] - s['x']) < LUPA_MM and abs(o['y'] - s['y']) < LUPA_MM:
                pintar_sitio(p, o, v.papula(i), rotulo=2.2)
        p.restore()
        if self._ini is not None:
            self._pintar_regla(p, cx, cy, k)
        p.end()

    def _pintar_regla(self, p, cx, cy, k):
        (x0, y0), (x1, y1) = self._ini, self._fin
        largo = math.hypot(x1 - x0, y1 - y0)
        p.save()
        p.translate(cx + x0 * k, cy + y0 * k)
        p.rotate(math.degrees(math.atan2(y1 - y0, x1 - x0)))
        ancho = max(largo, 10) + 4
        p.setPen(QPen(QColor(90, 110, 140, 160), 1))
        p.setBrush(QColor(220, 235, 250, 90))
        p.drawRect(QRectF(-2 * k, -5 * k, ancho * k, 5 * k))
        p.setPen(QPen(QColor(30, 40, 60), 1))
        for mm in range(int(ancho - 2) + 1):
            alto = 2.4 if mm % 5 == 0 else 1.3
            p.drawLine(QPointF(mm * k, 0), QPointF(mm * k, -alto * k))
        p.setPen(QPen(QColor(tema.ALERTA), 1.6))
        p.drawLine(QPointF(0, 0), QPointF(largo * k, 0))
        p.restore()
        p.setPen(QColor(tema.TEXTO))
        f = QFont()
        f.setPixelSize(13)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(4, 4, self.width() - 8, 18), Qt.AlignmentFlag.AlignLeft,
                   f'{n(round(largo * 2) / 2)} mm')


# ── La ventana ──────────────────────────────────────────────────────────────

class PrickWindow(QMainWindow):
    TITULO = 'Prick test'
    TIPO = 'PRICK'
    EQUIPO = 'prick'

    def __init__(self, data_login=None, parent=None, reloj=time.monotonic):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self._reloj = reloj
        self.sesion = None
        self.data_caso = None
        self.appointment_id = None
        self.sitios = []
        self.seleccion = None
        self.lanceta = 1           # la que tiene en la mano
        self.lanceta_usada = False
        self.setWindowTitle(self.TITULO)
        self._construir()
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
        self.pill_reloj = Pastilla('', 'neutro')
        self.pill_reloj.setToolTip('Tiempo desde la última punción: se lee a los 15-20 minutos')
        fila.addWidget(self.pill_reloj)
        raiz.addLayout(fila)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)
        raiz.addLayout(cuerpo, 1)
        izquierda = QWidget()
        izq = QVBoxLayout(izquierda)
        izq.setContentsMargins(0, 0, 0, 0)
        izq.setSpacing(10)
        self._panel_paciente(izq)
        self._panel_extractos(izq)
        self._panel_errores(izq)
        izq.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidget(izquierda)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        desplazable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        desplazable.setFixedWidth(300)
        cuerpo.addWidget(desplazable)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._pantalla(), 'Antebrazo')
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
        self.btn_farmacos = self._boton('Preguntar por los fármacos', self._preguntar)
        self.btn_farmacos.setToolTip('Qué tomó en las últimas semanas y cuándo fue la última dosis')
        self.panel_paciente.agregar(self.btn_farmacos)
        self.lbl_paciente = etiqueta('', rol='hint')
        self.lbl_paciente.setWordWrap(True)
        self.panel_paciente.agregar(self.lbl_paciente)
        izq.addWidget(self.panel_paciente)

    def _panel_extractos(self, izq):
        self.panel_extractos = Tarjeta('Extractos y lanceta')
        self.lista = QListWidget()
        for clave, nombre, abrev in P.EXTRACTOS:
            item = QListWidgetItem(f'{abrev}  ·  {nombre}')
            item.setData(Qt.ItemDataRole.UserRole, clave)
            self.lista.addItem(item)
        self.lista.setCurrentRow(0)
        self.lista.setMinimumHeight(190)
        self.panel_extractos.agregar(self.lista)
        fila = QHBoxLayout()
        self.grupo_modo = QButtonGroup(self)
        self.btn_modo = {}
        for i, (clave, texto) in enumerate(MODOS):
            b = QPushButton(texto)
            b.setCheckable(True)
            b.setToolTip({'marcar': 'Clic en el antebrazo: marca el sitio y pone la gota del extracto elegido',
                          'puncionar': 'Clic en una gota: puncha con la lanceta que tienes en la mano',
                          'quitar': 'Clic en una marca sin puncionar: la saca'}[clave])
            self.grupo_modo.addButton(b, i)
            self.btn_modo[clave] = b
            fila.addWidget(b)
        self.btn_modo['marcar'].setChecked(True)
        self.panel_extractos.agregar_layout(fila)
        fila = QHBoxLayout()
        self.btn_lanceta = self._boton('Lanceta nueva', self._lanceta_nueva)
        fila.addWidget(self.btn_lanceta)
        self.btn_secar = self._boton('Secar las gotas', self._secar)
        fila.addWidget(self.btn_secar)
        self.panel_extractos.agregar_layout(fila)
        self.lbl_lanceta = etiqueta('', rol='hint')
        self.lbl_lanceta.setWordWrap(True)
        self.panel_extractos.agregar(self.lbl_lanceta)
        self.btn_saltar = self._boton('Saltar a los 15 minutos (docente)', self._saltar_espera)
        self.btn_saltar.setVisible(False)
        self.panel_extractos.agregar(self.btn_saltar)
        izq.addWidget(self.panel_extractos)

    def _panel_errores(self, izq):
        self.panel_errores = Tarjeta('Simular error de técnica')
        self.chk_arrastre = QCheckBox('Secar arrastrando la gota')
        self.panel_errores.agregar(self.chk_arrastre)
        izq.addWidget(self.panel_errores)

    def _pantalla(self):
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.brazo = Brazo(self)
        self.brazo.clic.connect(self._clic_brazo)
        caja = Tarjeta('Antebrazo volar')
        caja.agregar(self.brazo, 1)
        layout.addWidget(caja, 2)
        derecha = QSplitter(Qt.Orientation.Vertical)
        caja = Tarjeta('Lupa y regla')
        self.lupa = Lupa(self)
        self.lupa.medida.connect(self._al_medir)
        caja.agregar(self.lupa, 1)
        self.lbl_medida = etiqueta('Arrastra sobre la pápula para medir.', rol='hint')
        self.lbl_medida.setWordWrap(True)
        caja.agregar(self.lbl_medida)
        fila = QHBoxLayout()
        self.btn_mayor = self._boton('Anotar como mayor', lambda: self._anotar('mayor'))
        self.btn_perp = self._boton('Como perpendicular', lambda: self._anotar('perpendicular'))
        self.btn_sin = self._boton('Sin pápula', lambda: self._anotar('sin'))
        for b in (self.btn_mayor, self.btn_perp, self.btn_sin):
            fila.addWidget(b)
        caja.agregar_layout(fila)
        derecha.addWidget(caja)
        hoja = Tarjeta('Hoja de registro')
        self.tabla = QTableWidget(0, 0)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.itemSelectionChanged.connect(self._al_seleccionar_fila)
        hoja.agregar(self.tabla, 1)
        derecha.addWidget(hoja)
        derecha.setStretchFactor(0, 3)
        derecha.setStretchFactor(1, 2)
        layout.addWidget(derecha, 3)
        return contenedor

    def _pestana_informe(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        caja = Tarjeta('Informe')
        caja.agregar(etiqueta('Fármacos: último antihistamínico (cuál, fecha y hora)', rol='campo'))
        self.txt_farmacos = QLineEdit()
        caja.agregar(self.txt_farmacos)
        self.lbl_resumen = etiqueta('', rol='hint')
        self.lbl_resumen.setWordWrap(True)
        caja.agregar(self.lbl_resumen)
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
        return [self.panel_paciente, self.panel_extractos, self.panel_errores]

    # --- Ciclo de vida (API que llama main.py) --------------------------

    def la_super(self, data, appointment_id=None):
        self.sesion = SesionPrick(data, appointment_id, self._reloj) if data is not None else None
        self.data_caso = data
        self.appointment_id = appointment_id
        self.sitios = []
        self.seleccion = None
        self.lanceta = 1
        self.lanceta_usada = False
        self.chk_arrastre.setChecked(False)
        self.lbl_paciente.setText('')
        for w in (self.txt_farmacos, self.txt_hallazgos, self.txt_conclusion):
            w.clear()
        self.estado_informe.limpiar()
        self.lupa.limpiar()
        hay = self.sesion is not None and self.sesion.hay_paciente
        for w in self._paneles():
            w.setEnabled(hay)
        self.brazo.activo = hay
        if hay:
            self._mensaje('Pregunta por los fármacos. Elige un extracto y marca el sitio con un clic en el '
                          'antebrazo (a 2,5 cm entre sí y a 3 cm o más de los pliegues); puncha cada gota con una '
                          'lanceta nueva y lee a los 15-20 minutos.')
        elif data is not None:
            self._mensaje('Este paciente no tiene prick test cargado en el caso: no se puede hacer. '
                          'Hace falta el bloque PRICK del caso.', 'alerta')
        else:
            self._mensaje('Abre una atención para hacer la prueba.')
        self.dibujar()

    def report_job(self):
        if not self.data_login or not self.sitios or self.sesion is None:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        caso = self.sesion.caso
        punciones = [s['puncion'] for s in self.sitios if s['puncion'] is not None]
        primera = min(punciones) if punciones else None
        sitios = []
        for s in self.sitios:
            sitios.append({'extracto': s['extracto'], 'nombre': P.NOMBRES[s['extracto']],
                           'x': round(s['x'], 1), 'y': round(s['y'], 1), 'orden': s['orden'],
                           'puncion_min': None if s['puncion'] is None else round(s['puncion'] - primera, 2),
                           'lanceta': s['lanceta'], 'arrastre': s['arrastre'],
                           'lectura': dict(s['lectura']), 'resultado': s['resultado']})
        data = {
            'paciente': {'edad': caso['edad'], 'sexo': caso['sexo']},
            'pregunto_farmacos': self.sesion.pregunto,
            'farmacos': self.txt_farmacos.text(),
            'sitios': sitios,
            'lectura_min': self._lectura_min(),
            'hallazgos': self.txt_hallazgos.toPlainText(),
            'conclusion': self.txt_conclusion.toPlainText(),
        }
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data,
                'images': self._exportar_imagenes}

    def submit_report(self):
        return sesion_nasal.subir_al_cerrar(self)

    def restore_report(self, data):
        """Retomar la atención: los sitios vuelven con su punción corrida para
        que la última quede a los 20 minutos, y las lecturas y el texto."""
        if self.sesion is None or not self.sesion.hay_paciente or self.sitios:
            return False
        guardados = [s for s in data.get('sitios') or []
                     if isinstance(s, dict) and s.get('extracto') in P.NOMBRES]
        pun = [s['puncion_min'] for s in guardados if isinstance(s.get('puncion_min'), (int, float))]
        ahora = self.sesion.minuto()
        ultima = max(pun) if pun else 0
        for s in sorted(guardados, key=lambda s: s.get('orden') or 0):
            lectura = s.get('lectura') if isinstance(s.get('lectura'), dict) else {}
            p = s.get('puncion_min')
            self.sitios.append({
                'extracto': s['extracto'], 'x': float(s.get('x') or 0), 'y': float(s.get('y') or 0),
                'orden': len(self.sitios) + 1, 'gota': True, 'seco': True,
                'puncion': None if not isinstance(p, (int, float)) else ahora - 20 - (ultima - p),
                'lanceta': s.get('lanceta'), 'arrastre': bool(s.get('arrastre')),
                'lectura': {'mayor': lectura.get('mayor'), 'perpendicular': lectura.get('perpendicular'),
                            'min': lectura.get('min')},
                'resultado': s.get('resultado') or ''})
        self.lanceta = max([s['lanceta'] or 0 for s in self.sitios] + [0]) + 1
        self.sesion.pregunto = bool(data.get('pregunto_farmacos'))
        self.txt_farmacos.setText(data.get('farmacos') or '')
        self.txt_hallazgos.setPlainText(data.get('hallazgos') or '')
        self.txt_conclusion.setPlainText(data.get('conclusion') or '')
        if self.sitios:
            self._mensaje('Se recuperó la hoja de esta atención.', 'ok')
        self.dibujar()
        return True

    def showEvent(self, evento):
        self._cada_segundo()
        super().showEvent(evento)

    # --- El modelo, para los dibujos ------------------------------------

    def _semilla(self, i):
        return f'prick/{self.appointment_id}/{self.sitios[i]["orden"]}'

    def papula(self, i, minuto=None):
        s = self.sitios[i]
        if s['puncion'] is None:
            return P.papula(self.sesion.piel, self.sitios, i, 0, self._semilla(i))
        ahora = self.sesion.minuto() if minuto is None else minuto
        return P.papula(self.sesion.piel, self.sitios, i, ahora - s['puncion'], self._semilla(i))

    def _ultima_puncion(self):
        pun = [s['puncion'] for s in self.sitios if s['puncion'] is not None]
        return max(pun) if pun else None

    def _lectura_min(self):
        """Minutos desde la última punción a la primera lectura de un alérgeno."""
        ms = [s['lectura']['min'] for s in self.sitios
              if s['extracto'] not in ('neg', 'his') and s['lectura'].get('min') is not None]
        return None if not ms else min(ms)

    # --- Acciones del alumno -------------------------------------------

    def _log(self, accion, **payload):
        if self.sesion is None or not self.sesion.hay_paciente:
            return
        sesion_nasal.registrar(f'{self.EQUIPO}_{accion}', self.data_caso, self.appointment_id, **payload)

    def _mensaje(self, texto, estado=None):
        self.lbl_mensaje.setText(texto)
        color = {'alerta': tema.ALERTA, 'ok': tema.OK}.get(estado, tema.TEXTO_SUAVE)
        self.lbl_mensaje.setStyleSheet(f'color: {color};')

    def _modo(self):
        return MODOS[self.grupo_modo.checkedId()][0]

    def _preguntar(self):
        self.sesion.pregunto = True
        self.lbl_paciente.setText(self.sesion.respuesta_farmacos())
        f = self.sesion.piel['farmaco']
        self._log('preguntar_farmacos', farmaco=f, supresion=P.supresion(f))

    def _cercano(self, x, y, radio=6):
        mejor = None
        for i, s in enumerate(self.sitios):
            d = math.hypot(s['x'] - x, s['y'] - y)
            if d <= radio and (mejor is None or d < mejor[1]):
                mejor = (i, d)
        return None if mejor is None else mejor[0]

    def _clic_brazo(self, x, y):
        i = self._cercano(x, y)
        modo = self._modo()
        if modo == 'marcar':
            if i is not None:
                self._seleccionar(i)
                return
            self._marcar(x, y)
        elif i is None:
            return
        elif modo == 'puncionar':
            self._seleccionar(i)
            self._puncionar(i)
        else:
            self._quitar(i)

    def _marcar(self, x, y):
        if not P.dentro(x, y):
            return
        item = self.lista.currentItem()
        if item is None:
            return
        clave = item.data(Qt.ItemDataRole.UserRole)
        if any(s['extracto'] == clave for s in self.sitios):
            self._mensaje(f'{P.NOMBRES[clave]} ya tiene su sitio.', 'alerta')
            return
        self.sitios.append({'extracto': clave, 'x': x, 'y': y, 'orden': len(self.sitios) + 1, 'gota': True,
                            'seco': False, 'puncion': None, 'lanceta': None, 'arrastre': False,
                            'lectura': {'mayor': None, 'perpendicular': None, 'min': None}, 'resultado': ''})
        i = len(self.sitios) - 1
        avisos = P.avisos_sitio(self.sitios, i)
        self._log('marcar', extracto=clave, x=x, y=y, orden=i + 1, avisos=avisos)
        if 'cerca' in avisos:
            self._mensaje('Quedó a menos de 2 cm de otra punción.', 'alerta')
        elif 'pliegue' in avisos:
            self._mensaje('Quedó a menos de 3 cm de un pliegue.', 'alerta')
        else:
            self._mensaje(f'Marcado: {P.NOMBRES[clave]}.')
        # El siguiente extracto de la lista, para seguir marcando.
        fila = self.lista.currentRow()
        if fila < self.lista.count() - 1:
            self.lista.setCurrentRow(fila + 1)
        self.seleccion = i
        self.dibujar()

    def _quitar(self, i):
        s = self.sitios[i]
        if s['puncion'] is not None:
            self._mensaje('Ese sitio ya está puncionado: no se puede quitar.', 'alerta')
            return
        self.sitios.pop(i)
        for k, o in enumerate(self.sitios):
            o['orden'] = k + 1
        self.seleccion = None
        self._log('quitar', extracto=s['extracto'])
        self.dibujar()

    def _puncionar(self, i):
        s = self.sitios[i]
        if s['puncion'] is not None:
            self._mensaje('Ese sitio ya está puncionado.', 'alerta')
            return
        reusada = self.lanceta_usada
        s['puncion'] = self.sesion.minuto()
        s['lanceta'] = self.lanceta
        self.lanceta_usada = True
        self._log('puncionar', extracto=s['extracto'], orden=s['orden'], lanceta=self.lanceta, reusada=reusada,
                  contaminantes=[c[0] for c in P.contaminantes(self.sitios, i)])
        self._mensaje('Lanceta usada otra vez: lleva lo de la punción anterior.' if reusada
                      else f'Puncionado: {P.NOMBRES[s["extracto"]]}.', 'alerta' if reusada else None)
        self.dibujar()

    def _lanceta_nueva(self):
        self.lanceta += 1
        self.lanceta_usada = False
        self._log('lanceta', lanceta=self.lanceta)
        self.dibujar()

    def _secar(self):
        arrastre = self.chk_arrastre.isChecked()
        secados = []
        for s in self.sitios:
            if s['puncion'] is not None and not s['seco']:
                s['seco'] = True
                s['arrastre'] = s['arrastre'] or arrastre
                secados.append(s['extracto'])
        self._log('secar', sitios=secados, arrastre=arrastre)
        self.dibujar()

    def _saltar_espera(self):
        ultima = self._ultima_puncion()
        if ultima is None:
            return
        corrida = max(0.0, 15 - (self.sesion.minuto() - ultima))
        for s in self.sitios:
            if s['puncion'] is not None:
                s['puncion'] -= corrida
        self._log('saltar_espera', minutos=corrida)
        self.dibujar()

    def _seleccionar(self, i):
        self.seleccion = i
        self.lupa.limpiar()
        self.tabla.blockSignals(True)
        self.tabla.selectRow(i)
        self.tabla.blockSignals(False)
        self.dibujar()

    def _al_seleccionar_fila(self):
        filas = self.tabla.selectionModel().selectedRows()
        if filas:
            self.seleccion = filas[0].row()
            self.lupa.limpiar()
            self.brazo.update()
            self._pintar_medida()

    def _al_medir(self, mm):
        self._pintar_medida()

    def _anotar(self, que):
        if self.seleccion is None:
            return
        s = self.sitios[self.seleccion]
        ultima = self._ultima_puncion()
        minuto = None if s['puncion'] is None else self.sesion.minuto() - s['puncion']
        if que == 'sin':
            s['lectura'].update(mayor=0.0, perpendicular=0.0)
        else:
            if self.lupa.ultima is None:
                return
            s['lectura'][que] = self.lupa.ultima
        s['lectura']['min'] = None if ultima is None else round(self.sesion.minuto() - ultima, 1)
        v = self.papula(self.seleccion)
        self._log('medir', extracto=s['extracto'], eje=que, mm=s['lectura'].get('mayor' if que == 'sin' else que),
                  minuto=minuto, verdad={'mayor': v['mayor'], 'menor': v['menor'], 'eritema': v['eritema']})
        self.dibujar()

    def _al_resultado(self, i, combo):
        s = self.sitios[i]
        s['resultado'] = combo.currentData()
        correcto = self._correctos().get(i)
        self._log('resultado', extracto=s['extracto'], resultado=s['resultado'], correcto=correcto)
        self._pintar_resumen()
        self._pintar_verdad()

    def _correctos(self):
        mayores = [self.papula(i)['mayor'] for i in range(len(self.sitios))]
        return P.resultado_correcto(self.sitios, mayores)

    # --- Reloj ----------------------------------------------------------

    def _cada_segundo(self):
        hay = self.sesion is not None and self.sesion.hay_paciente
        ultima = self._ultima_puncion() if hay else None
        if ultima is None:
            self.pill_reloj.setVisible(False)
            self.btn_saltar.setVisible(False)
            return
        m = self.sesion.minuto() - ultima
        seg = int(m * 60)
        self.pill_reloj.setVisible(True)
        tipo = 'ok' if P.LECTURA_MIN[0] <= m <= P.LECTURA_MIN[1] else 'neutro'
        self.pill_reloj.set(f'Desde la última punción: {seg // 60}:{seg % 60:02d}', tipo)
        self.btn_saltar.setVisible(self.es_docente and m < 15)
        self.brazo.update()
        self.lupa.update()

    # --- Dibujo ---------------------------------------------------------

    def dibujar(self):
        hay = self.sesion is not None and self.sesion.hay_paciente
        self.brazo.update()
        self.lupa.update()
        if hay:
            self.lbl_lanceta.setText(f'Lanceta en la mano: n.° {self.lanceta}, '
                                     + ('ya usada.' if self.lanceta_usada else 'nueva.'))
        else:
            self.lbl_lanceta.setText('')
        self._cada_segundo()
        self._pintar_tabla()
        self._pintar_medida()
        self._pintar_resumen()
        self._pintar_verdad()

    def _pintar_medida(self):
        hay = self.seleccion is not None and self.sesion is not None and self.sesion.hay_paciente
        for b in (self.btn_mayor, self.btn_perp, self.btn_sin):
            b.setEnabled(hay)
        if not hay:
            self.lbl_medida.setText('Elige un sitio y arrastra sobre la pápula para medir.')
            return
        s = self.sitios[self.seleccion]
        medida = '' if self.lupa.ultima is None else f' Regla: {n(self.lupa.ultima)} mm.'
        self.lbl_medida.setText(f'{P.NOMBRES[s["extracto"]]}.{medida}')

    def _pintar_tabla(self):
        cab = ['N.°', 'Alérgeno / control', 'Punción', 'Mayor (mm)', 'Perpendicular (mm)', 'Resultado']
        self.tabla.blockSignals(True)
        self.tabla.clear()
        self.tabla.setColumnCount(len(cab))
        self.tabla.setHorizontalHeaderLabels(cab)
        self.tabla.setRowCount(len(self.sitios))
        for i, s in enumerate(self.sitios):
            lec = s['lectura']
            celdas = [str(s['orden']), P.NOMBRES[s['extracto']],
                      '✓' if s['puncion'] is not None else '—',
                      '—' if lec['mayor'] is None else n(lec['mayor']),
                      '—' if lec['perpendicular'] is None else n(lec['perpendicular'])]
            for j, texto in enumerate(celdas):
                self.tabla.setItem(i, j, QTableWidgetItem(texto))
            combo = QComboBox()
            for clave, nombre in (RESULTADOS_CONTROL if s['extracto'] in ('neg', 'his') else RESULTADOS_ALERGENO):
                combo.addItem(nombre, clave)
            combo.setCurrentIndex(max(0, combo.findData(s['resultado'])))
            combo.currentIndexChanged.connect(lambda _k, i=i, c=combo: self._al_resultado(i, c))
            self.tabla.setCellWidget(i, 5, combo)
        cab_h = self.tabla.horizontalHeader()
        cab_h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab_h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(5, 118)
        if self.seleccion is not None and self.seleccion < len(self.sitios):
            self.tabla.selectRow(self.seleccion)
        self.tabla.blockSignals(False)

    def _pintar_resumen(self):
        if self.sesion is None or not self.sesion.hay_paciente or not self.sitios:
            self.lbl_resumen.setText('')
            return
        m = self._lectura_min()
        partes = [f'{len(self.sitios)} sitios, {sum(s["puncion"] is not None for s in self.sitios)} puncionados.']
        if m is not None:
            partes.append(f'Primera lectura de un alérgeno a los {n(m)} minutos de la última punción.')
        self.lbl_resumen.setText(' '.join(partes))

    def _pintar_verdad(self):
        if self.verdad is None:
            return
        hay = self.sesion is not None and self.sesion.hay_paciente
        self.verdad.setText(self._texto_verdad() if hay else '')

    def _exportar_imagenes(self):
        temp = context.get_resource('local_cache/nasal/temp')
        os.makedirs(temp, exist_ok=True)
        ruta = os.path.join(temp, 'upload_prick_brazo.jpg')
        try:
            seleccion, self.seleccion = self.seleccion, None
            self.brazo.resize(max(self.brazo.width(), 360), max(self.brazo.height(), 640))
            ok = self.brazo.grab().save(ruta, 'JPG', 90)
            self.seleccion = seleccion
        except Exception as exc:  # noqa: BLE001 -- sin imagen el informe sube igual
            print(f'{self.TIPO}: no se pudo exportar el antebrazo: {exc}')
            return {}
        return {'prick_brazo': ruta} if ok else {}

    def _texto_verdad(self):
        piel = self.sesion.piel
        f = piel['farmaco']
        sup = P.supresion(f)
        filas = [f'<b>Piel</b>: histamina {n(piel["histamina"])} mm; dermografismo '
                 f'{n(piel["dermografismo"])} mm; fármaco: '
                 + ('ninguno' if not f else f'{P.NOMBRE_FARMACO[f["clave"]].lower()} hace {n(f["horas"], 0)} h '
                    f'(achica las pápulas un {sup * 100:.0f} %)') + '.']
        sens = [f'{P.NOMBRES[k]} {n(v)} mm' for k, v in piel['alergenos'].items() if v > 0]
        filas.append('<b>Sensibilizado a</b>: ' + (', '.join(sens) if sens else 'nada') + '.')
        if self.sitios:
            orden = [s['extracto'] for s in self.sitios]
            if orden[0] != 'neg':
                filas.append('El control negativo no fue el primero.')
            if 'his' in orden and orden[-1] != 'his':
                filas.append('La histamina no fue la última.')
            for falta in ('neg', 'his'):
                if falta not in orden:
                    filas.append(f'Falta el {P.NOMBRES[falta].lower()}: sin él no se puede informar.')
        correctos = self._correctos()
        for i, s in enumerate(self.sitios):
            v = self.papula(i)
            cosas = [f'ahora {n(v["mayor"])} × {n(v["menor"])} mm' if v['mayor'] else 'sin pápula ahora']
            avisos = P.avisos_sitio(self.sitios, i)
            if 'cerca' in avisos:
                cosas.append('a menos de 2 cm de otro')
            if 'pliegue' in avisos:
                cosas.append('cerca de un pliegue')
            for ext, _f, causa in P.contaminantes(self.sitios, i):
                cosas.append(f'contaminado con {P.NOMBRES[ext].lower()} ({"lanceta reusada" if causa == "lanceta" else "arrastre"})')
            if s['puncion'] is None:
                cosas.append('sin puncionar')
            lec = s['lectura']
            if lec['mayor'] is not None:
                cosas.append(f'midió {n(lec["mayor"])} × {n(lec["perpendicular"]) if lec["perpendicular"] is not None else "—"}'
                             + ('' if lec['min'] is None else f' a los {n(lec["min"])} min'))
            esperado = {'positivo': 'positivo', 'negativo': 'negativo', 'valido': 'válido',
                        'no_valido': 'no válido'}[correctos[i]]
            cosas.append(f'resultado con lo que hay ahora: {esperado}'
                         + (f' (anotó {s["resultado"].replace("_", " ")})' if s['resultado'] else ''))
            filas.append(f'<b>{s["orden"]}. {P.NOMBRES[s["extracto"]]}</b>: ' + '; '.join(cosas) + '.')
        return '<br>'.join(filas)
