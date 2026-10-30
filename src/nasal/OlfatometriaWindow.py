"""La olfatometría de LabSim (H28 del libro), demo interna del Box Rinología.

Como se hace en la sala, con la batería completa de bolígrafos: el alumno
le pregunta al paciente si comió, fumó o se perfumó en la última hora (y
espera si hace falta), le venda los ojos para el umbral y la
discriminación (clic en los ojos), elige la narina y presenta tríos e
ítems. En el umbral elige él el paso de cada trío: seguir la escalera es
lo que se aprende. El paciente contesta en elección forzada; si dice «no
huelo nada», el alumno le pide que elija igual o lo anota como error (y
el puntaje sale más bajo, como en H28).

La hoja se llena sola con lo presentado y lo que contestó; la escalera se
dibuja. Los aciertos de D e I se cuentan; el T lo calcula el alumno con las
inversiones y lo escribe en el informe, junto con la categoría. Lo que el
paciente es de verdad, el T que da la regla con sus tríos y lo que hizo
mal van a "Lo que el equipo no sabe" (docente) y al log, con prefijo olf_.

El informe OLFATOMETRIA guarda los ensayos tal cual: al retomar la
atención vuelven igual. Sin `cases.data['OLFATO']` no se mide.
"""

import os
import random
import time

import pyqtgraph as pg
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout,
                               QHeaderView, QMainWindow, QPlainTextEdit, QPushButton, QScrollArea,
                               QSizePolicy, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

from core import tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import olfatometria as O
from nasal import sesion as sesion_nasal
from nasal.equipos import PERMISOS_DOCENTE, QSS_NASAL, Tabla, num
from nasal.graficos import _plot, exportar
from nasal.paciente_rm import RECORTE
from nasal.RinoscopiaWindow import cara
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta

NOMBRE_PRUEBA = dict(O.PRUEBAS)
NOMBRE_NARINA = dict(O.NARINAS)
COLOR_NARINA = {'ambas': tema.ACENTO, 'D': tema.OD, 'I': tema.OI}
POSICIONES = ('el primero', 'el segundo', 'el tercero')
RESPUESTA_PREPARACION = {
    'ok': '«No, no he comido ni fumado nada desde el almuerzo, y no me puse perfume.»',
    'fumo': '«Me fumé un cigarro antes de entrar, hace unos diez minutos.»',
    'comio': '«Me tomé un café con un sándwich en la cafetería, recién.»',
    'perfume': '«No comí nada, pero me puse perfume en la mañana… ¿se nota mucho?»',
}


def n(v, d=2):
    return num(v, d)


# ── La atención ─────────────────────────────────────────────────────────────

class SesionOlf:
    """El paciente de esta atención y el reloj de la batería: cuándo fue el
    último trío y desde cuándo espera por la preparación."""

    def __init__(self, data, appointment_id, reloj=time.monotonic):
        self.caso = O.desde_caso(data)
        self.appointment_id = appointment_id
        self._reloj = reloj
        self.n = 0
        self.t_ultimo = None          # reloj del último trío o ítem
        self.espera_desde = None      # reloj en que se le pidió esperar
        self.pregunto = False

    @property
    def hay_paciente(self):
        return self.caso is not None

    @property
    def olfato(self):
        return self.caso['olfato']

    def ahora(self):
        return self._reloj()

    def semilla(self):
        self.n += 1
        return f'olf/{self.appointment_id}/{self.n}'

    def desde_ultimo(self):
        return None if self.t_ultimo is None else self._reloj() - self.t_ultimo

    def falta_espera(self):
        if self.espera_desde is None:
            return None
        return max(0.0, O.ESPERA_PREPARACION_S - (self._reloj() - self.espera_desde))

    def preparado(self):
        """Viene sin comer, fumar ni perfume, o ya esperó la hora."""
        return self.olfato['preparacion'] == 'ok' or self.falta_espera() == 0

    def saltar_espera(self):
        if self.espera_desde is not None:
            self.espera_desde = min(self.espera_desde, self._reloj() - O.ESPERA_PREPARACION_S)
        if self.t_ultimo is not None:
            self.t_ultimo = min(self.t_ultimo, self._reloj() - O.INTERVALO_S)


# ── El paciente ─────────────────────────────────────────────────────────────

OJOS = ((262, 262), (338, 262))      # en el cuadro de la cara (RECORTE)


class PacienteOlf(QWidget):
    """El paciente de frente: clic en los ojos pone o saca la venda. Al
    presentar, el bolígrafo pasa bajo la nariz."""

    venda_clic = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.activo = False
        self.venda = False
        self.boligrafo = None        # 'ambas' | 'D' | 'I' mientras se presenta
        self._foto = None
        self.setMinimumSize(180, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMouseTracking(True)

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

    def _en_ojos(self, pos):
        x0, y0, k = self._escala()
        x, y = (pos.x() - x0) / k, (pos.y() - y0) / k
        return 236 < x < 364 and 238 < y < 286

    def mouseMoveEvent(self, evento):
        sobre = self.activo and self._en_ojos(evento.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if sobre else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(evento)

    def mousePressEvent(self, evento):
        if self.activo and evento.button() == Qt.MouseButton.LeftButton and self._en_ojos(evento.position()):
            self.venda_clic.emit()
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
        if self.venda:
            self._pintar_venda(p)
        if self.boligrafo:
            self._pintar_boligrafo(p)
        p.restore()
        p.end()

    def _pintar_venda(self, p):
        (xa, ya), (xb, _yb) = OJOS
        p.setPen(QPen(QColor('#1F2733'), 1.6))
        p.setBrush(QColor(40, 48, 60, 235))
        p.drawRoundedRect(QRectF(RECORTE.x() + 22, ya - 17, RECORTE.width() - 44, 32), 10, 10)
        p.setPen(QPen(QColor(90, 100, 115), 1))
        p.drawLine(QPointF(RECORTE.x() + 30, ya + 8), QPointF(RECORTE.right() - 30, ya + 8))

    def _pintar_boligrafo(self, p):
        fila = cara()['cuadros']['0']
        (dx, dy), (ix, _iy) = fila['D'], fila['I']
        x = {'D': dx, 'I': ix}.get(self.boligrafo, (dx + ix) / 2)
        y = dy + 10
        p.setPen(QPen(QColor('#5A6270'), 1.4))
        p.setBrush(QColor('#F4F1EA'))
        p.drawRoundedRect(QRectF(x - 70, y - 5, 66, 10), 4, 4)
        p.setBrush(QColor('#C9B48A'))
        p.drawRoundedRect(QRectF(x - 6, y - 4, 7, 8), 3, 3)


# ── La escalera ─────────────────────────────────────────────────────────────

class Escalera:
    """El paso de cada trío del umbral, por narina, como la figura de H28:
    paso 1 (4 %) arriba, 16 abajo; ✓ verde, ✗ rojo."""

    def __init__(self):
        self.widget = _plot('trío', 'paso (1 = 4 %)')
        self.widget.setMinimumHeight(170)
        self.widget.getPlotItem().invertY(True)
        self.widget.setYRange(0.5, 16.5, padding=0)
        self.widget.addLegend(offset=(-8, 8))

    def dibujar(self, series):
        """series: {narina: [(paso, ok), ...]}."""
        plot = self.widget
        plot.clear()
        largo = max([len(s) for s in series.values()] + [10])
        plot.setXRange(0.5, largo + 0.5, padding=0)
        for narina, ens in series.items():
            if not ens:
                continue
            xs = list(range(1, len(ens) + 1))
            ys = [p for p, _ok in ens]
            color = COLOR_NARINA[narina]
            plot.plot(xs, ys, pen=pg.mkPen(color, width=1.6), name=NOMBRE_NARINA[narina])
            for ok in (True, False):
                pts = [(x, y) for x, (y, o) in zip(xs, ens) if o == ok]
                if pts:
                    plot.plot([a for a, _ in pts], [b for _, b in pts], pen=None,
                              symbol='o' if ok else 'x', symbolSize=8 if ok else 10,
                              symbolBrush=pg.mkBrush(tema.OK if ok else tema.ALERTA),
                              symbolPen=pg.mkPen(tema.OK if ok else tema.ALERTA, width=1.4))

    def exportar(self, ruta):
        exportar(self.widget, ruta)


# ── La ventana ──────────────────────────────────────────────────────────────

class OlfatometriaWindow(QMainWindow):
    TITULO = 'Olfatometría'
    TIPO = 'OLFATOMETRIA'
    EQUIPO = 'olf'

    def __init__(self, data_login=None, parent=None, reloj=time.monotonic):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self._reloj = reloj
        self.sesion = None
        self.data_caso = None
        self.appointment_id = None
        self.ensayos = []          # ver report_job
        self.pendiente = None      # el trío cuya respuesta fue «no huelo nada»
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
        self.pill_reloj.setToolTip('Tiempo desde el último trío o ítem: entre uno y otro, 20 s o más')
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
        self._panel_bateria(izq)
        izq.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidget(izquierda)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        desplazable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        desplazable.setFixedWidth(310)
        cuerpo.addWidget(desplazable)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._hoja(), 'Hoja')
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
        self.vista = PacienteOlf()
        self.vista.setFixedHeight(200)
        self.vista.venda_clic.connect(self._venda)
        self.panel_paciente.agregar(self.vista)
        self.lbl_paciente = etiqueta('', rol='hint')
        self.lbl_paciente.setWordWrap(True)
        self.panel_paciente.agregar(self.lbl_paciente)
        self.btn_preguntar = self._boton('Preguntar qué hizo en la última hora', self._preguntar)
        self.btn_preguntar.setToolTip('¿Comió, bebió, fumó o se perfumó en la última hora?')
        self.panel_paciente.agregar(self.btn_preguntar)
        self.btn_esperar = self._boton('Esperar una hora antes de empezar', self._esperar)
        self.panel_paciente.agregar(self.btn_esperar)
        self.lbl_espera = etiqueta('', rol='hint')
        self.lbl_espera.setWordWrap(True)
        self.panel_paciente.agregar(self.lbl_espera)
        self.btn_saltar = self._boton('Saltar la espera (docente)', self._saltar_espera)
        self.btn_saltar.setVisible(False)
        self.panel_paciente.agregar(self.btn_saltar)
        izq.addWidget(self.panel_paciente)

    def _panel_bateria(self, izq):
        self.panel_bateria = Tarjeta('Bolígrafos')
        campos = Campos()
        self.cmb_prueba = QComboBox()
        for clave, nombre in O.PRUEBAS:
            self.cmb_prueba.addItem(nombre, clave)
        self.cmb_prueba.currentIndexChanged.connect(self._al_cambiar_prueba)
        campos.agregar('Prueba', self.cmb_prueba)
        self.cmb_narina = QComboBox()
        for clave, nombre in O.NARINAS:
            self.cmb_narina.addItem(nombre, clave)
        self.cmb_narina.currentIndexChanged.connect(self._al_cambiar_narina)
        campos.agregar('Narina', self.cmb_narina)
        self.spin_paso = QSpinBox()
        self.spin_paso.setRange(1, O.PASOS)
        self.spin_paso.setValue(O.PASOS)
        self.spin_paso.valueChanged.connect(lambda _v: self._pintar_paso())
        campos.agregar('Paso del trío', self.spin_paso)
        self.panel_bateria.agregar(campos)
        self.lbl_paso = etiqueta('', rol='hint')
        self.lbl_paso.setWordWrap(True)
        self.panel_bateria.agregar(self.lbl_paso)
        self.btn_presentar = self._boton('Presentar', self._presentar, True)
        self.panel_bateria.agregar(self.btn_presentar)
        self.lbl_respuesta = etiqueta('', rol='hint')
        self.lbl_respuesta.setWordWrap(True)
        self.lbl_respuesta.setTextFormat(Qt.TextFormat.RichText)
        self.panel_bateria.agregar(self.lbl_respuesta)
        fila = QHBoxLayout()
        self.btn_elegir = self._boton('Pedirle que elija igual', self._elegir_igual)
        self.btn_error = self._boton('Anotar como error', self._anotar_error)
        fila.addWidget(self.btn_elegir)
        fila.addWidget(self.btn_error)
        self.panel_bateria.agregar_layout(fila)
        izq.addWidget(self.panel_bateria)

    def _hoja(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.escalera = Escalera()
        caja = Tarjeta('Umbral: la escalera')
        caja.agregar(self.escalera.widget, 1)
        abajo = Tarjeta('Hoja de registro')
        self.tabla = QTableWidget(0, 0)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        abajo.agregar(self.tabla, 1)
        fila = QHBoxLayout()
        self.lbl_cuentas = etiqueta('', rol='hint')
        self.lbl_cuentas.setWordWrap(True)
        fila.addWidget(self.lbl_cuentas, 1)
        self.btn_borrar = self._boton('Borrar el último', self._borrar_ultimo)
        fila.addWidget(self.btn_borrar)
        abajo.agregar_layout(fila)
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(caja)
        vertical.addWidget(abajo)
        vertical.setStretchFactor(0, 2)
        vertical.setStretchFactor(1, 3)
        layout.addWidget(vertical, 1)
        return contenedor

    def _pestana_informe(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        resultados = Tarjeta('Puntajes')
        resultados.agregar(etiqueta('El umbral (T) es el promedio de los pasos de las últimas cuatro '
                                    'inversiones de la escalera: lo calculas tú.', rol='hint'))
        self.campos_t = Campos()
        self.spin_t = {}
        for clave, nombre in O.NARINAS:
            s = QDoubleSpinBox()
            s.setRange(0, 16)
            s.setDecimals(2)
            s.setSingleStep(0.25)
            s.setSpecialValueText('—')
            s.setMaximumWidth(130)
            s.valueChanged.connect(lambda _v, k=clave: self._al_escribir_t(k))
            self.spin_t[clave] = s
            self.campos_t.agregar(f'T, {nombre.lower()}', s)
        resultados.agregar(self.campos_t)
        self.tabla_informe = Tabla()
        resultados.agregar(self.tabla_informe)
        self.lbl_norma = etiqueta('', rol='hint')
        self.lbl_norma.setWordWrap(True)
        resultados.agregar(self.lbl_norma)
        campos = Campos()
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItem('—', '')
        for clave, nombre in O.CATEGORIAS:
            self.cmb_categoria.addItem(nombre, clave)
        self.cmb_categoria.currentIndexChanged.connect(self._al_categoria)
        campos.agregar('Categoría', self.cmb_categoria)
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

    def _paneles(self):
        return [self.panel_paciente, self.panel_bateria]

    # --- Ciclo de vida (API que llama main.py) --------------------------

    def la_super(self, data, appointment_id=None):
        self.sesion = SesionOlf(data, appointment_id, self._reloj) if data is not None else None
        self.data_caso = data
        self.appointment_id = appointment_id
        self.ensayos = []
        self.pendiente = None
        self.vista.venda = False
        self.vista.boligrafo = None
        self.lbl_paciente.setText('')
        self.lbl_respuesta.setText('')
        for s in self.spin_t.values():
            s.blockSignals(True)
            s.setValue(0)
            s.blockSignals(False)
        self.cmb_categoria.blockSignals(True)
        self.cmb_categoria.setCurrentIndex(0)
        self.cmb_categoria.blockSignals(False)
        for w in (self.txt_hallazgos, self.txt_conclusion):
            w.clear()
        self.estado_informe.limpiar()
        self.cmb_prueba.setCurrentIndex(0)
        self.cmb_narina.setCurrentIndex(0)
        self.spin_paso.setValue(O.PASOS)
        hay = self.sesion is not None and self.sesion.hay_paciente
        for w in self._paneles():
            w.setEnabled(hay)
        self.vista.activo = hay
        if hay:
            self._mensaje('Prepara al paciente, véndale los ojos (clic en los ojos) para el umbral y la '
                          'discriminación, y presenta los bolígrafos. Entre un trío y otro, 20 s.')
        elif data is not None:
            self._mensaje('Este paciente no tiene olfatometría cargada en el caso: no se puede medir. '
                          'Hace falta el bloque OLFATO del caso.', 'alerta')
        else:
            self._mensaje('Abre una atención para medir.')
        self.dibujar()

    def report_job(self):
        if not self.data_login or not self.ensayos or self.sesion is None:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        caso = self.sesion.caso
        grupo = O.grupo_edad(caso['edad'])
        data = {
            'paciente': {'edad': caso['edad'], 'sexo': caso['sexo']},
            'preparacion': {'pregunto': self.sesion.pregunto,
                            'respuesta': RESPUESTA_PREPARACION[self.sesion.olfato['preparacion']]
                            if self.sesion.pregunto else '',
                            'espero': self.sesion.espera_desde is not None},
            'ensayos': [{k: v for k, v in e.items() if k != 'verdad'} for e in self.ensayos],
            'puntajes': self._puntajes(),
            'p10': None if grupo is None else grupo[3],
            'grupo_edad': '' if grupo is None else (f'{grupo[0]}–{grupo[1]}' if grupo[1] < 120 else f'≥ {grupo[0]}'),
            'categoria': self.cmb_categoria.currentData() or '',
            'hallazgos': self.txt_hallazgos.toPlainText(),
            'conclusion': self.txt_conclusion.toPlainText(),
        }
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data,
                'images': self._exportar_imagenes}

    def submit_report(self):
        return sesion_nasal.subir_al_cerrar(self)

    def restore_report(self, data):
        """Retomar la atención: vuelven los ensayos, los T y el texto."""
        if self.sesion is None or not self.sesion.hay_paciente or self.ensayos:
            return False
        claves = {'prueba', 'narina', 'paso', 'item', 'correcta', 'eleccion', 'ok', 'venda', 'dt',
                  'dijo_nada', 'forzada', 'anotado_error', 'semilla', 'opciones'}
        for e in data.get('ensayos') or []:
            if isinstance(e, dict) and e.get('prueba') in NOMBRE_PRUEBA and e.get('narina') in NOMBRE_NARINA:
                self.ensayos.append({k: e.get(k) for k in claves})
        prep = data.get('preparacion') or {}
        self.sesion.pregunto = bool(prep.get('pregunto'))
        if prep.get('espero'):
            self.sesion.espera_desde = self._reloj() - O.ESPERA_PREPARACION_S
        self.sesion.n = len(self.ensayos)
        for narina, p in (data.get('puntajes') or {}).items():
            if narina in self.spin_t and isinstance((p or {}).get('T'), (int, float)):
                self.spin_t[narina].blockSignals(True)
                self.spin_t[narina].setValue(p['T'])
                self.spin_t[narina].blockSignals(False)
        i = self.cmb_categoria.findData(data.get('categoria') or '')
        self.cmb_categoria.blockSignals(True)
        self.cmb_categoria.setCurrentIndex(max(0, i))
        self.cmb_categoria.blockSignals(False)
        self.txt_hallazgos.setPlainText(data.get('hallazgos') or '')
        self.txt_conclusion.setPlainText(data.get('conclusion') or '')
        if self.ensayos:
            self._mensaje('Se recuperó la hoja de esta atención.', 'ok')
        self.dibujar()
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

    def _prueba(self):
        return self.cmb_prueba.currentData()

    def _narina(self):
        return self.cmb_narina.currentData()

    def _venda(self):
        self.vista.venda = not self.vista.venda
        self._log('venda', puesta=self.vista.venda, prueba=self._prueba())
        self.dibujar()

    def _al_cambiar_prueba(self, _i):
        if self.sesion and self.sesion.hay_paciente:
            self._log('prueba', prueba=self._prueba())
        self.pendiente = None
        self.lbl_respuesta.setText('')
        self.dibujar()

    def _al_cambiar_narina(self, _i):
        if self.sesion and self.sesion.hay_paciente:
            self._log('narina', narina=self._narina())
        self.pendiente = None
        self.lbl_respuesta.setText('')
        self.dibujar()

    def _preguntar(self):
        self.sesion.pregunto = True
        prep = self.sesion.olfato['preparacion']
        self.lbl_paciente.setText(RESPUESTA_PREPARACION[prep])
        self._log('preguntar_preparacion', preparacion=prep)
        self.dibujar()

    def _esperar(self):
        if self.sesion.espera_desde is None:
            self.sesion.espera_desde = self.sesion.ahora()
        self._log('esperar_preparacion', preparacion=self.sesion.olfato['preparacion'])
        self.dibujar()

    def _saltar_espera(self):
        self.sesion.saltar_espera()
        self._log('saltar_espera')
        self.dibujar()

    def _siguiente_item(self, prueba, narina):
        hechos = {e['item'] for e in self.ensayos if e['prueba'] == prueba and e['narina'] == narina}
        for i in range(O.N_ITEMS):
            if i not in hechos:
                return i
        return None

    def _escalera_de(self, narina):
        return [(e['paso'], e['ok']) for e in self.ensayos if e['prueba'] == 'T' and e['narina'] == narina]

    def _presentar(self):
        if self.pendiente is not None:
            return
        prueba, narina = self._prueba(), self._narina()
        semilla = self.sesion.semilla()
        r = random.Random(semilla + '/orden')
        venda = self.vista.venda
        dt = self.sesion.desde_ultimo()
        if prueba == 'I':
            item = self._siguiente_item('I', narina)
            if item is None:
                self._mensaje('Ya se presentaron los 16 ítems de identificación por esta narina.', 'alerta')
                return
            if venda:
                self.lbl_paciente.setText('«Con la venda no puedo leer las opciones.»')
                self._log('presentar', prueba=prueba, narina=narina, item=item, venda=True, leyo=False)
                self.dibujar()
                return
            opciones, correcta = O.opciones_item(item, semilla)
            paso = None
        else:
            correcta = r.randrange(3)
            opciones = None
            if prueba == 'D':
                item = self._siguiente_item('D', narina)
                if item is None:
                    self._mensaje('Ya se presentaron los 16 tríos de discriminación por esta narina.', 'alerta')
                    return
                paso = None
            else:
                item, paso = None, self.spin_paso.value()
        resp = O.responder(self.sesion.olfato, prueba, narina, paso=paso, correcta=correcta,
                           n_opciones=4 if prueba == 'I' else 3, semilla=semilla, venda=venda, dt=dt,
                           preparado=self.sesion.preparado())
        self.sesion.t_ultimo = self.sesion.ahora()
        ensayo = {'prueba': prueba, 'narina': narina, 'paso': paso, 'item': item, 'correcta': correcta,
                  'eleccion': resp['eleccion'], 'ok': resp['eleccion'] == correcta, 'venda': venda,
                  'dt': None if dt is None else round(dt, 1), 'dijo_nada': resp['dice_nada'],
                  'forzada': False, 'anotado_error': False, 'semilla': semilla, 'opciones': opciones,
                  'verdad': {'detecto': resp['detecto'], 'vio': resp['vio'], 'p': resp['p'],
                             'preparado': self.sesion.preparado()}}
        regla = O.escalera(self._escalera_de(narina))['siguiente'] if prueba == 'T' else None
        self._log('presentar', **{k: v for k, v in ensayo.items() if k not in ('opciones', 'verdad')},
                  **ensayo['verdad'], paso_regla=regla)
        self.vista.boligrafo = narina
        QTimer.singleShot(1200, self._bajar_boligrafo)
        if resp['dice_nada']:
            self.pendiente = ensayo
            self.lbl_respuesta.setText('<b>Paciente:</b> «No huelo nada en ninguno.»'
                                       if prueba != 'I' else '<b>Paciente:</b> «No huelo nada.»')
        else:
            self._anotar(ensayo)
        self.dibujar()

    def _bajar_boligrafo(self):
        self.vista.boligrafo = None
        self.vista.update()

    def _texto_respuesta(self, e):
        if e['prueba'] == 'I':
            return f'«{e["opciones"][e["eleccion"]]}.»'
        return f'«{POSICIONES[e["eleccion"]].capitalize()}.»'

    def _anotar(self, ensayo):
        self.ensayos.append(ensayo)
        if ensayo['anotado_error']:
            self.lbl_respuesta.setText('Anotado como error: sin respuesta.')
        else:
            previo = 'Elige igual: ' if ensayo['forzada'] else ''
            self.lbl_respuesta.setText(f'<b>Paciente:</b> {previo}{self._texto_respuesta(ensayo)}')

    def _elegir_igual(self):
        e, self.pendiente = self.pendiente, None
        if e is None:
            return
        e['forzada'] = True
        self._log('elegir_igual', prueba=e['prueba'], narina=e['narina'], ok=e['ok'])
        self._anotar(e)
        self.dibujar()

    def _anotar_error(self):
        e, self.pendiente = self.pendiente, None
        if e is None:
            return
        e['anotado_error'] = True
        e['ok'] = False
        self._log('anotar_sin_eleccion', prueba=e['prueba'], narina=e['narina'], hubiera_acertado=e['eleccion'] == e['correcta'])
        self._anotar(e)
        self.dibujar()

    def _borrar_ultimo(self):
        if not self.ensayos:
            return
        e = self.ensayos.pop()
        self._log('borrar_ensayo', prueba=e['prueba'], narina=e['narina'], paso=e['paso'], item=e['item'])
        self.lbl_respuesta.setText('')
        self.dibujar()

    def _al_escribir_t(self, narina):
        v = self.spin_t[narina].value()
        regla = O.umbral_regla(self._escalera_de(narina))
        self._log('puntaje', narina=narina, T=v or None, T_regla=regla)
        self._pintar_informe()

    def _al_categoria(self, _i):
        tdi = self._puntajes().get('ambas', {}).get('TDI')
        correcta = None if tdi is None else O.categoria(tdi)
        self._log('categoria', categoria=self.cmb_categoria.currentData(), TDI=tdi, correcta=correcta)
        self._pintar_verdad()

    # --- Reloj ----------------------------------------------------------

    def _cada_segundo(self):
        hay = self.sesion is not None and self.sesion.hay_paciente
        if not hay:
            self.pill_reloj.setVisible(False)
            return
        dt = self.sesion.desde_ultimo()
        self.pill_reloj.setVisible(True)
        if dt is None:
            self.pill_reloj.set('Sin tríos todavía', 'neutro')
        else:
            seg = int(dt)
            texto = f'Último hace {seg // 60}:{seg % 60:02d}' if seg >= 60 else f'Último hace {seg} s'
            self.pill_reloj.set(texto, 'ok' if dt >= O.INTERVALO_S else 'neutro')
        falta = self.sesion.falta_espera()
        if falta is None:
            self.lbl_espera.setText('')
        elif falta > 0:
            self.lbl_espera.setText(f'Esperando: faltan {int(falta // 60)}:{int(falta % 60):02d}.')
        else:
            self.lbl_espera.setText('Ya pasó la hora de espera.')
        self.btn_esperar.setEnabled(self.sesion.espera_desde is None)
        self.btn_saltar.setVisible(self.es_docente and (bool(falta) or (dt is not None and dt < O.INTERVALO_S)))

    # --- Dibujo ---------------------------------------------------------

    def dibujar(self):
        hay = self.sesion is not None and self.sesion.hay_paciente
        self.vista.update()
        prueba = self._prueba()
        self.spin_paso.setEnabled(hay and prueba == 'T')
        esperando = self.pendiente is not None
        self.btn_presentar.setEnabled(hay and not esperando)
        self.btn_elegir.setVisible(esperando)
        self.btn_error.setVisible(esperando)
        self.btn_borrar.setEnabled(hay and bool(self.ensayos) and not esperando)
        self._pintar_paso()
        self._cada_segundo()
        self._pintar_tabla()
        self.escalera.dibujar({k: self._escalera_de(k) for k in NOMBRE_NARINA})
        self._pintar_informe()

    def _pintar_paso(self):
        if self.sesion is None or not self.sesion.hay_paciente:
            self.lbl_paso.setText('')
            return
        prueba, narina = self._prueba(), self._narina()
        if prueba == 'T':
            paso = self.spin_paso.value()
            conc = f'{O.concentracion(paso):.6f}'.rstrip('0').rstrip('.').replace('.', ',')
            self.lbl_paso.setText(f'Paso {paso}: {conc} %. Un bolígrafo con olor y dos con solvente; el '
                                  f'paciente elige cuál huele.')
        else:
            item = self._siguiente_item(prueba, narina)
            nombre = 'Trío' if prueba == 'D' else 'Ítem'
            if item is None:
                self.lbl_paso.setText(f'{NOMBRE_PRUEBA[prueba]}: completa por esta narina.')
            elif prueba == 'D':
                self.lbl_paso.setText(f'{nombre} {item + 1} de {O.N_ITEMS}: dos iguales y uno distinto; '
                                      'el paciente elige el distinto.')
            else:
                self.lbl_paso.setText(f'{nombre} {item + 1} de {O.N_ITEMS} ({O.IDENTIFICACION[item][0].lower()}): '
                                      'el paciente elige el nombre entre cuatro opciones escritas.')

    def _pintar_tabla(self):
        cab = ['N.°', 'Prueba', 'Narina', 'Paso / ítem', 'Correcto', 'Eligió', '', 'Observación']
        self.tabla.clear()
        self.tabla.setColumnCount(len(cab))
        self.tabla.setHorizontalHeaderLabels(cab)
        self.tabla.setRowCount(len(self.ensayos))
        for i, e in enumerate(self.ensayos):
            if e['prueba'] == 'I':
                correcto, eligio = e['opciones'][e['correcta']], e['opciones'][e['eleccion']]
            else:
                correcto, eligio = str(e['correcta'] + 1), str(e['eleccion'] + 1)
            if e['anotado_error']:
                eligio = '—'
            obs = []
            if e['dijo_nada']:
                obs.append('«no huelo nada»' + (', eligió igual' if e['forzada'] else ''))
            if e['prueba'] in ('T', 'D') and not e['venda']:
                obs.append('sin venda')
            if e['dt'] is not None and e['dt'] < O.INTERVALO_S:
                obs.append(f'a {e["dt"]:.0f} s del anterior')
            paso = str(e['paso']) if e['prueba'] == 'T' else str(e['item'] + 1)
            celdas = [str(i + 1), NOMBRE_PRUEBA[e['prueba']], NOMBRE_NARINA[e['narina']].replace('Narina ', ''),
                      paso, correcto, eligio, '✓' if e['ok'] else '✗', '; '.join(obs)]
            for j, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                if j == 6:
                    item.setForeground(QColor(tema.OK if e['ok'] else tema.ALERTA))
                self.tabla.setItem(i, j, item)
        if self.ensayos:
            self.tabla.scrollToBottom()
        partes = []
        for narina in NOMBRE_NARINA:
            for prueba in ('D', 'I'):
                es = [e for e in self.ensayos if e['prueba'] == prueba and e['narina'] == narina]
                if es:
                    partes.append(f'{NOMBRE_PRUEBA[prueba]}, {NOMBRE_NARINA[narina].lower()}: '
                                  f'{sum(e["ok"] for e in es)} aciertos en {len(es)}')
            t = self._escalera_de(narina)
            if t:
                partes.append(f'Umbral, {NOMBRE_NARINA[narina].lower()}: {len(t)} tríos')
        self.lbl_cuentas.setText('. '.join(partes) + ('.' if partes else ''))

    def _puntajes(self):
        """{narina: {'T', 'D', 'I', 'TDI'}} de las narinas con algo medido;
        D e I solo con los 16 completos."""
        out = {}
        for narina in NOMBRE_NARINA:
            t = self.spin_t[narina].value() or None
            fila = {'T': t}
            for prueba in ('D', 'I'):
                es = [e for e in self.ensayos if e['prueba'] == prueba and e['narina'] == narina]
                fila[prueba] = sum(e['ok'] for e in es) if len(es) == O.N_ITEMS else None
            hay = self._escalera_de(narina) or any(
                e['narina'] == narina for e in self.ensayos if e['prueba'] != 'T')
            if not hay and t is None:
                continue
            fila['TDI'] = (None if None in (fila['T'], fila['D'], fila['I'])
                           else fila['T'] + fila['D'] + fila['I'])
            out[narina] = fila
        return out

    def _pintar_informe(self):
        hay = self.sesion is not None and self.sesion.hay_paciente
        p = self._puntajes() if hay else {}
        filas = []
        for narina, d in p.items():
            celdas = [NOMBRE_NARINA[narina], '—' if d['T'] is None else n(d['T']),
                      '—' if d['D'] is None else f'{d["D"]}/16', '—' if d['I'] is None else f'{d["I"]}/16',
                      '—' if d['TDI'] is None else n(d['TDI'])]
            filas.append((celdas, narina if narina in O.LADOS else None, {}))
        self.tabla_informe.poblar(['Narina', 'Umbral (T)', 'Discriminación (D)', 'Identificación (I)', 'TDI'], filas)
        if hay:
            g = O.grupo_edad(self.sesion.caso['edad'])
            if g is None:
                self.lbl_norma.setText('Sin datos normativos para menores de 5 años.')
            else:
                rango = f'{g[0]} a {g[1]}' if g[1] < 120 else f'{g[0]} o más'
                self.lbl_norma.setText(
                    f'Percentil 10 del TDI de su grupo de edad ({rango} años): {n(g[3])}; promedio {n(g[2], 1)} '
                    '(Oleszkiewicz y cols., 2019). Cortes del TDI: 16 o menos, anosmia funcional; 16,25 a 30,5, '
                    'hiposmia; 30,75 a 41,25, normosmia; 41,5 o más, olfato superior. D e I cuentan cuando están '
                    'los 16.')
        else:
            self.lbl_norma.setText('')
        self._pintar_verdad()

    def _pintar_verdad(self):
        if self.verdad is None:
            return
        hay = self.sesion is not None and self.sesion.hay_paciente
        self.verdad.setText(self._texto_verdad() if hay else '')

    def _exportar_imagenes(self):
        temp = context.get_resource('local_cache/nasal/temp')
        os.makedirs(temp, exist_ok=True)
        if not any(e['prueba'] == 'T' for e in self.ensayos):
            return {}
        ruta = os.path.join(temp, 'upload_olf_umbral.jpg')
        try:
            self.escalera.exportar(ruta)
        except Exception as exc:  # noqa: BLE001 -- sin imagen el informe sube igual
            print(f'{self.TIPO}: no se pudo exportar la escalera: {exc}')
            return {}
        return {'olf_umbral': ruta}

    def _texto_verdad(self):
        olf = self.sesion.olfato
        caso = self.sesion.caso
        filas = [f'<b>Paciente</b>: {"hombre" if caso["sexo"] == "M" else "mujer"}, {caso["edad"]:.0f} años; '
                 f'{dict(O.CONDUCTAS)[olf["conducta"]].lower()}; {dict(O.PREPARACIONES)[olf["preparacion"]].lower()}'
                 + ('' if self.sesion.preparado() else ' (todavía huele menos)') + '.']
        b = O.verdad_binasal(olf)
        for clave, nombre in O.NARINAS:
            d = b if clave == 'ambas' else olf['lados'][clave]
            tdi = d['T'] + d['D'] + d['I']
            filas.append(f'<b>{nombre}</b>, de verdad: T {n(d["T"], 1)}, D {n(d["D"], 1)}, I {n(d["I"], 1)}; '
                         f'TDI {n(tdi, 1)} ({O.nombre_categoria(O.categoria(tdi)).lower()}).')
        for clave, nombre in O.NARINAS:
            esc = self._escalera_de(clave)
            if not esc:
                continue
            regla = O.umbral_regla(esc)
            esc_info = O.escalera(esc)
            fuera = 0
            for k in range(1, len(esc)):
                if esc[k][0] != O.escalera(esc[:k])['siguiente']:
                    fuera += 1
            if esc[0][0] != O.PASOS:
                fuera += 1
            escrito = self.spin_t[clave].value() or None
            filas.append(f'<b>Umbral, {nombre.lower()}</b>: {len(esc)} tríos, {len(esc_info["inversiones"])} '
                         f'inversiones; T por la regla: {"—" if regla is None else n(regla)} (escrito: '
                         f'{"—" if escrito is None else n(escrito)}); tríos fuera de la regla: {fuera}.')
        cortos = sum(1 for e in self.ensayos if e['dt'] is not None and e['dt'] < O.INTERVALO_S)
        sin_venda = sum(1 for e in self.ensayos if e['prueba'] in ('T', 'D') and not e['venda'])
        vio = sum(1 for e in self.ensayos if e.get('verdad', {}).get('vio'))
        sin_eleccion = sum(1 for e in self.ensayos if e['anotado_error'])
        filas.append(f'<b>Técnica</b>: {cortos} con menos de 20 s del anterior; {sin_venda} sin venda en umbral o '
                     f'discriminación ({vio} en que vio el bolígrafo); {sin_eleccion} anotados como error sin pedir '
                     f'que eligiera; preguntó por la preparación: {"sí" if self.sesion.pregunto else "no"}.')
        tdi = self._puntajes().get('ambas', {}).get('TDI')
        if tdi is not None:
            filas.append(f'<b>Categoría</b> que corresponde al TDI escrito ({n(tdi)}): '
                         f'{O.nombre_categoria(O.categoria(tdi)).lower()}; elegida: '
                         f'{(self.cmb_categoria.currentText() or "—").lower()}.')
        return '<br>'.join(filas)
