"""La titulación de CPAP de LabSim (H32 del libro), demo interna del
Laboratorio de sueño.

Como se hace: el alumno elige la interfaz y la talla, parte la noche con la
presión inicial (4 cmH2O) y la vigila desde la sala de control: la noche
corre acelerada (×30 a ×300, con pausa) y él ve el hipnograma, la presión,
los eventos, el ronquido, la SpO2 y la fuga, y lo que pasó desde el último
cambio. Sube o baja de a 1 cmH2O con las reglas de Kushida y cols. (2008):
al menos 5 minutos entre cambios, y se sube con 2 apneas obstructivas, 3
hipopneas, 5 RERA o 3 minutos de ronquido. Al terminar, la tabla por
presión, la presión que indica y el grado de la titulación los escribe él.

Lo que el equipo no sabe (la presión eficaz del caso en cada posición y
etapa, si los cambios cumplían la regla, el grado que corresponde) va a la
pestaña del docente y al log, con prefijo cpap_. El informe CPAP guarda la
interfaz y los cambios de presión: al retomar la atención la noche se
rehace igual.

Sin `cases.data['SUENO']` no hay paciente.
"""

import os

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QMainWindow, QPlainTextEdit, QPushButton,
                               QScrollArea, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from core import tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import cpap as C
from nasal import sesion as sesion_nasal
from nasal import sueno as Z
from nasal.equipos import PERMISOS_DOCENTE, QSS_NASAL, Tabla, num
from nasal.PolisomnografiaWindow import COLOR_TIPO, hhmm
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta

VELOCIDADES = ((30, '×30'), (60, '×60'), (120, '×120'), (300, '×300'))
TIC_MS = 200


def n(v, d=1):
    return '—' if v is None else num(v, d)


class Monitor:
    """La noche hasta ahora: hipnograma, presión, eventos y SpO2, en horas."""

    def __init__(self):
        self.widget = pg.GraphicsLayoutWidget()
        self.widget.setBackground(tema.TARJETA)
        self.plots = {}
        for clave, rotulo in (('etapa', 'Etapa'), ('presion', 'cmH₂O'), ('eventos', 'Eventos'),
                              ('spo2', 'SpO₂')):
            p = self.widget.addPlot()
            p.setMenuEnabled(False)
            p.hideButtons()
            p.getViewBox().setMouseEnabled(x=False, y=False)
            p.showGrid(x=True, y=clave == 'presion', alpha=0.2)
            p.getAxis('left').setWidth(54)
            p.getAxis('left').setLabel(rotulo, color=tema.TEXTO_TENUE)
            for eje in ('left', 'bottom'):
                p.getAxis(eje).setPen(pg.mkPen(tema.BORDE_FUERTE))
                p.getAxis(eje).setTextPen(pg.mkPen(tema.TEXTO_TENUE))
            if self.plots:
                p.setXLink(self.plots['etapa'])
            self.plots[clave] = p
            self.widget.nextRow()
        self.plots['etapa'].getAxis('left').setTicks([[(4, 'W'), (3, 'R'), (1, 'N2'), (0, 'N3')]])
        self.plots['eventos'].getAxis('left').setTicks([[(3, 'Apn'), (2, 'Hip'), (1, 'RERA'), (0, 'Ron')]])
        self.plots['spo2'].getAxis('bottom').setLabel('horas', color=tema.TEXTO_TENUE)
        lay = self.widget.ci.layout
        for fila, k in enumerate((2, 3, 2, 2)):
            lay.setRowStretchFactor(fila, k)

    def dibujar(self, T):
        for p in self.plots.values():
            p.clear()
        if T is None:
            return
        horas = T.N / 3600
        for p in self.plots.values():
            p.setXRange(0, horas, padding=0)
        t = T.t
        xs, ys = [], []
        for e, a, b in T.S['seg']:
            if a >= t:
                break
            xs += [a / 3600, min(b, t) / 3600]
            ys += [Z.ORDEN[e]] * 2
        self.plots['etapa'].plot(xs, ys, pen=pg.mkPen(tema.TEXTO, width=1.3))
        self.plots['etapa'].setYRange(-0.5, 4.5, padding=0)
        xs, ys = [], []
        for a, b, p in T.escalones():
            xs += [a / 3600, b / 3600]
            ys += [p, p]
        self.plots['presion'].plot(xs, ys, pen=pg.mkPen(tema.ACENTO, width=2))
        self.plots['presion'].setYRange(C.P_MIN - 1, max(14, max(ys or [0]) + 2), padding=0)
        filas = {'ao': 3, 'am': 3, 'ac': 3, 'h': 2, 'rera': 1}
        for tipo, color in COLOR_TIPO.items():
            xe = [x['t'] / 3600 for x in T.eventos if x['tipo'] == tipo]
            if xe:
                self.plots['eventos'].plot(xe, [filas[tipo]] * len(xe), pen=None, symbol='|', symbolSize=9,
                                           symbolPen=pg.mkPen(color, width=1.2))
        xr = [m / 60 for m, r in T.ronquido if r]
        if xr:
            self.plots['eventos'].plot(xr, [0] * len(xr), pen=None, symbol='s', symbolSize=4,
                                       symbolBrush=pg.mkBrush(tema.TEXTO_TENUE), symbolPen=None)
        self.plots['eventos'].setYRange(-0.6, 3.6, padding=0)
        paso = 30
        if t > paso:
            self.plots['spo2'].plot([k / 3600 for k in range(0, t - paso, paso)],
                                    [min(T.spo2(j) for j in range(k, k + paso)) for k in range(0, t - paso, paso)],
                                    pen=pg.mkPen(tema.OI, width=1))
        self.plots['spo2'].setYRange(80, 100, padding=0)
        ahora = pg.InfiniteLine(pos=t / 3600, angle=90, pen=pg.mkPen(tema.ALERTA, width=1, style=Qt.PenStyle.DashLine))
        self.plots['presion'].addItem(ahora)

    def exportar(self, ruta):
        exportador = pg.exporters.ImageExporter(self.widget.scene())
        exportador.parameters()['width'] = max(1000, int(self.widget.width() * 2))
        exportador.export(ruta)


class CpapWindow(QMainWindow):
    TITULO = 'Titulación de CPAP'
    TIPO = 'CPAP'
    EQUIPO = 'cpap'

    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self.caso = None
        self.data_caso = None
        self.appointment_id = None
        self.T = None
        self.ultimo_cambio = 0
        self.corriendo = False
        self.cortada = False
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
        self.pill_hora = Pastilla('', 'neutro')
        fila.addWidget(self.pill_hora)
        raiz.addLayout(fila)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)
        raiz.addLayout(cuerpo, 1)
        izquierda = QWidget()
        izq = QVBoxLayout(izquierda)
        izq.setContentsMargins(0, 0, 0, 0)
        izq.setSpacing(10)
        self._panel_interfaz(izq)
        self._panel_presion(izq)
        izq.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidget(izquierda)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        desplazable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        desplazable.setFixedWidth(300)
        cuerpo.addWidget(desplazable)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._pantalla(), 'Monitor')
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

    def _panel_interfaz(self, izq):
        self.panel_interfaz = Tarjeta('Interfaz')
        campos = Campos()
        self.cmb_interfaz = QComboBox()
        for clave, nombre in C.INTERFACES:
            self.cmb_interfaz.addItem(nombre, clave)
        self.cmb_interfaz.currentIndexChanged.connect(lambda _i: self._al_interfaz())
        campos.agregar('Interfaz', self.cmb_interfaz)
        self.cmb_talla = QComboBox()
        for t in C.TALLAS:
            self.cmb_talla.addItem(t, t)
        self.cmb_talla.setCurrentIndex(1)
        self.cmb_talla.currentIndexChanged.connect(lambda _i: self._al_interfaz())
        campos.agregar('Talla', self.cmb_talla)
        self.spin_inicial = QSpinBox()
        self.spin_inicial.setRange(C.P_MIN, C.P_MAX)
        self.spin_inicial.setSuffix(' cmH₂O')
        campos.agregar('Presión inicial', self.spin_inicial)
        self.panel_interfaz.agregar(campos)
        self.lbl_fuga = etiqueta('', rol='hint')
        self.lbl_fuga.setWordWrap(True)
        self.panel_interfaz.agregar(self.lbl_fuga)
        self.btn_empezar = self._boton('Apagar la luz y empezar', self._empezar, True)
        self.panel_interfaz.agregar(self.btn_empezar)
        izq.addWidget(self.panel_interfaz)

    def _panel_presion(self, izq):
        self.panel_presion = Tarjeta('Presión')
        self.lbl_presion = etiqueta('', rol='dato')
        self.panel_presion.agregar(self.lbl_presion)
        fila = QHBoxLayout()
        self.btn_bajar = self._boton('▼ 1 cmH₂O', lambda: self._cambiar(-1))
        self.btn_subir = self._boton('▲ 1 cmH₂O', lambda: self._cambiar(1))
        fila.addWidget(self.btn_bajar)
        fila.addWidget(self.btn_subir)
        self.panel_presion.agregar_layout(fila)
        self.lbl_periodo = etiqueta('', rol='hint')
        self.lbl_periodo.setWordWrap(True)
        self.lbl_periodo.setTextFormat(Qt.TextFormat.RichText)
        self.panel_presion.agregar(self.lbl_periodo)
        campos = Campos()
        self.cmb_velocidad = QComboBox()
        for v, nombre in VELOCIDADES:
            self.cmb_velocidad.addItem(nombre, v)
        self.cmb_velocidad.setCurrentIndex(1)
        self.cmb_velocidad.currentIndexChanged.connect(
            lambda _i: self._log('velocidad', velocidad=self.cmb_velocidad.currentData()))
        campos.agregar('Velocidad', self.cmb_velocidad)
        self.panel_presion.agregar(campos)
        fila = QHBoxLayout()
        self.btn_pausa = self._boton('Pausa', self._pausa)
        self.btn_terminar = self._boton('Terminar la noche', self._terminar)
        fila.addWidget(self.btn_pausa)
        fila.addWidget(self.btn_terminar)
        self.panel_presion.agregar_layout(fila)
        izq.addWidget(self.panel_presion)

    def _pantalla(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        caja = Tarjeta('La noche de titulación')
        self.monitor = Monitor()
        caja.agregar(self.monitor.widget, 1)
        layout.addWidget(caja, 1)
        return contenedor

    def _pestana_informe(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        resultados = Tarjeta('Por presión')
        self.tabla_informe = Tabla()
        resultados.agregar(self.tabla_informe)
        self.lbl_resumen = etiqueta('', rol='hint')
        self.lbl_resumen.setWordWrap(True)
        resultados.agregar(self.lbl_resumen)
        campos = Campos()
        self.spin_indicada = QSpinBox()
        self.spin_indicada.setRange(0, C.P_MAX)
        self.spin_indicada.setSpecialValueText('—')
        self.spin_indicada.setSuffix(' cmH₂O')
        self.spin_indicada.valueChanged.connect(lambda _v: self._al_indicar())
        campos.agregar('Presión indicada', self.spin_indicada)
        self.cmb_grado = QComboBox()
        self.cmb_grado.addItem('—', '')
        for clave, nombre in C.GRADOS:
            self.cmb_grado.addItem(nombre, clave)
        self.cmb_grado.currentIndexChanged.connect(lambda _i: self._al_indicar())
        campos.agregar('Grado de la titulación', self.cmb_grado)
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
        self.caso = Z.desde_caso(data) if data is not None else None
        self.data_caso = data
        self.appointment_id = appointment_id
        self.T = None
        self.ultimo_cambio = 0
        self.cortada = False
        for w, v in ((self.cmb_interfaz, 0), (self.cmb_talla, 1), (self.cmb_grado, 0)):
            w.blockSignals(True)
            w.setCurrentIndex(v)
            w.blockSignals(False)
        self.spin_inicial.setValue(C.P_MIN)
        self.spin_indicada.blockSignals(True)
        self.spin_indicada.setValue(0)
        self.spin_indicada.blockSignals(False)
        for w in (self.txt_hallazgos, self.txt_conclusion):
            w.clear()
        self.estado_informe.limpiar()
        hay = self.caso is not None
        self.panel_interfaz.setEnabled(hay)
        if hay:
            self._mensaje('Elige la interfaz y la talla, y empieza con la presión inicial. Sube de a 1 cmH₂O, '
                          'con 5 minutos o más entre cambios, mientras haya eventos o ronquido.')
        elif data is not None:
            self._mensaje('Este paciente no tiene estudio de sueño cargado en el caso: no se puede titular. '
                          'Hace falta el bloque SUENO del caso.', 'alerta')
        else:
            self._mensaje('Abre una atención para titular.')
        self.dibujar()

    def report_job(self):
        if not self.data_login or self.T is None:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        data = {
            'interfaz': self.T.interfaz, 'talla': self.T.talla,
            'cambios': [[t, p] for t, p in self.T.cambios], 't_fin': self.T.t,
            'terminada': self._terminado(),
            'tabla': getattr(self.tabla_informe, 'contenido', {}),
            'idr_basal': self.T.idr_basal(),
            'nota': self.lbl_resumen.text(),
            'presion_indicada': self.spin_indicada.value() or None,
            'grado': self.cmb_grado.currentData() or '',
            'hallazgos': self.txt_hallazgos.toPlainText(),
            'conclusion': self.txt_conclusion.toPlainText(),
        }
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data,
                'images': self._exportar_imagenes}

    def submit_report(self):
        return sesion_nasal.subir_al_cerrar(self)

    def restore_report(self, data):
        """Retomar: la noche se rehace con los mismos cambios de presión."""
        if self.caso is None or self.T is not None:
            return False
        cambios = [(int(t), int(p)) for t, p in data.get('cambios') or []]
        if not cambios or data.get('interfaz') not in dict(C.INTERFACES):
            return False
        self.T = C.Titulacion(self.caso['sueno'], self.appointment_id, data['interfaz'],
                              data.get('talla') if data.get('talla') in C.TALLAS else 'M', cambios[0][1])
        for t, p in cambios[1:]:
            self.T.avanzar(t - self.T.t)
            self.T.cambiar(p)
        self.T.avanzar(int(data.get('t_fin') or 0) - self.T.t)
        self.ultimo_cambio = cambios[-1][0]
        # Terminada, o en pausa donde quedó (se sigue con "Seguir").
        self.cortada = bool(data.get('terminada'))
        for w, v in ((self.cmb_interfaz, self.T.interfaz), (self.cmb_talla, self.T.talla),
                     (self.cmb_grado, data.get('grado') or '')):
            w.blockSignals(True)
            w.setCurrentIndex(max(0, w.findData(v)))
            w.blockSignals(False)
        self.spin_indicada.blockSignals(True)
        self.spin_indicada.setValue(data.get('presion_indicada') or 0)
        self.spin_indicada.blockSignals(False)
        self.txt_hallazgos.setPlainText(data.get('hallazgos') or '')
        self.txt_conclusion.setPlainText(data.get('conclusion') or '')
        self._mensaje('Se recuperó la titulación de esta atención.', 'ok')
        self.dibujar()
        return True

    # --- Acciones del alumno -------------------------------------------

    def _log(self, accion, **payload):
        if self.caso is None:
            return
        sesion_nasal.registrar(f'{self.EQUIPO}_{accion}', self.data_caso, self.appointment_id, **payload)

    def _mensaje(self, texto, estado=None):
        self.lbl_mensaje.setText(texto)
        color = {'alerta': tema.ALERTA, 'ok': tema.OK}.get(estado, tema.TEXTO_SUAVE)
        self.lbl_mensaje.setStyleSheet(f'color: {color};')

    def _al_interfaz(self):
        self._log('interfaz', interfaz=self.cmb_interfaz.currentData(), talla=self.cmb_talla.currentData())
        self._pintar_fuga()

    def _empezar(self):
        if self.caso is None or self.T is not None:
            return
        self.T = C.Titulacion(self.caso['sueno'], self.appointment_id, self.cmb_interfaz.currentData(),
                              self.cmb_talla.currentData(), self.spin_inicial.value())
        self.ultimo_cambio = 0
        cp = self.T.cp
        self._log('empezar', interfaz=self.T.interfaz, talla=self.T.talla, presion=self.T.presion,
                  verdad={**cp, 'talla_ok': self.T.talla == cp['talla'],
                          'boca_fuga': cp['boca'] and self.T.interfaz != 'oronasal'})
        self.corriendo = True
        self.timer.start()
        self._mensaje('La noche empezó. Vigila el período desde el último cambio.')
        self.dibujar()

    def _tic(self):
        if self.T is None or not self.corriendo:
            return
        self.T.avanzar(self.cmb_velocidad.currentData() * TIC_MS / 1000)
        if self.T.terminada:
            self._terminar(auto=True)
            return
        self.dibujar()

    def _pausa(self):
        if self.T is None or self.T.terminada:
            return
        self.corriendo = not self.corriendo
        self.timer.start() if self.corriendo else self.timer.stop()
        self._log('pausa', pausa=not self.corriendo, t=self.T.t)
        self.dibujar()

    def _cambiar(self, delta):
        if self.T is None or self.T.terminada:
            return
        antes = self.T.presion
        desde = self.T.t - self.ultimo_cambio
        periodo = self.T.periodo(self.ultimo_cambio)
        criterio = self.T.cumple_criterio(self.ultimo_cambio)
        self.T.cambiar(antes + delta)
        if self.T.presion == antes:
            return
        s = min(self.T.N - 1, self.T.t)
        self._log('presion', de=antes, a=self.T.presion, t=self.T.t, min_desde_cambio=round(desde / 60, 1),
                  periodo=periodo, criterio=criterio, p_eficaz_ahora=self.T.p_eficaz(s),
                  etapa=self.T.S['etapa'][s], pos=self.T.S['pos'][s])
        self.ultimo_cambio = self.T.t
        self.dibujar()

    def _terminar(self, auto=False):
        if self.T is None:
            return
        self.timer.stop()
        self.corriendo = False
        self.cortada = True
        self._log('terminar', t=self.T.t, presion=self.T.presion, completa=self.T.terminada, auto=auto)
        self._mensaje('Noche terminada. En el informe: la presión que indicas y el grado de la titulación.', 'ok')
        self.dibujar()

    def _al_indicar(self):
        if self.T is None:
            return
        p = self.spin_indicada.value() or None
        self._log('indicar', presion=p, grado=self.cmb_grado.currentData(),
                  grado_correcto=None if p is None else self.T.grado(p))
        self._pintar_verdad()

    # --- Dibujo ---------------------------------------------------------

    def _terminado(self):
        return self.T is not None and (self.T.terminada or self.cortada)

    def dibujar(self):
        hay = self.caso is not None
        empezado = self.T is not None
        fin = self._terminado()
        self.panel_interfaz.setEnabled(hay and not empezado)
        self.btn_empezar.setText('Noche en curso' if empezado else 'Apagar la luz y empezar')
        self.panel_presion.setEnabled(empezado and not fin)
        self.btn_pausa.setText('Seguir' if empezado and not self.corriendo and not fin else 'Pausa')
        self.pill_hora.setVisible(empezado)
        if empezado:
            s = min(self.T.N - 1, self.T.t)
            e = Z.NOM_ETAPA[self.T.S['etapa'][s]]
            self.pill_hora.set(f'{hhmm(self.T.t)} · {e} · {self.T.S["pos"][s]}', 'acento')
            self.lbl_presion.setText(f'{self.T.presion} cmH₂O')
        else:
            self.lbl_presion.setText('—')
        self._pintar_fuga()
        self._pintar_periodo()
        self.monitor.dibujar(self.T)
        self._pintar_informe()

    def _pintar_fuga(self):
        if self.caso is None:
            self.lbl_fuga.setText('')
            return
        if self.T is None:
            self.lbl_fuga.setText('La fuga se ve cuando empieza la noche.')
            return
        f = self.T.fugas[-1] if self.T.fugas else C.fuga(self.T.presion, self.T.interfaz, self.T.talla, self.T.cp)
        self.lbl_fuga.setText(f'Fuga no intencional: {n(f, 0)} L/min.')
        self.lbl_fuga.setStyleSheet(f'color: {tema.ALERTA if f > 24 else tema.TEXTO_SUAVE};')

    def _pintar_periodo(self):
        if self.T is None:
            self.lbl_periodo.setText('')
            return
        p = self.T.periodo(self.ultimo_cambio)
        minutos = (self.T.t - self.ultimo_cambio) / 60
        self.lbl_periodo.setText(
            f'<b>Desde el último cambio</b> ({n(minutos, 0)} min): {p["obstructivas"]} apneas obstructivas o '
            f'mixtas, {p["centrales"]} centrales, {p["hipopneas"]} hipopneas, {p["rera"]} RERA y '
            f'{p["ronquido_min"]} min de ronquido.')

    def _pintar_informe(self):
        if self.T is None:
            self.tabla_informe.poblar(['Presión'], [])
            self.lbl_resumen.setText('')
            self._pintar_verdad()
            return
        # Cortas: caben en el PDF; las unidades van en el resumen de abajo.
        cab = ['cmH₂O', 'Min', 'Sueño', 'REM sup.', 'Apn O/M/C', 'Hip', 'RERA', 'IDR', 'SpO₂ mín', 'Ronq.',
               'Fuga']
        filas = []
        for f in self.T.por_presion():
            filas.append(([str(f['presion']), n(f['seg'] / 60, 0), n(f['sueno'] / 60, 0),
                           n(f['rem_supino'] / 60, 0), f'{f["ao"]}/{f["am"]}/{f["ac"]}', str(f['h']),
                           str(f['rera']), n(f['IDR']), n(f['spo2_min'], 0), str(f['ron']), n(f['fuga'], 0)],
                          None, {}))
        self.tabla_informe.poblar(cab, filas)
        self.lbl_resumen.setText('Minutos en cada presión, de sueño, de REM en supino y de ronquido; apneas '
                                 'obstructivas, mixtas y centrales; IDR por hora de sueño; fuga en L/min. '
                                 f'Interfaz: {dict(C.INTERFACES)[self.T.interfaz].lower()}, talla {self.T.talla}. '
                                 f'IDR de la polisomnografía diagnóstica: {n(self.T.idr_basal())} por hora. '
                                 'Grados (Kushida 2008): óptima, IDR < 5 con REM en supino; buena, ≤ 10 (o la '
                                 'mitad si el basal era < 15) con REM en supino; adecuada, reducción de 75 %.')
        self._pintar_verdad()

    def _pintar_verdad(self):
        if self.verdad is None:
            return
        self.verdad.setText(self._texto_verdad() if self.caso is not None else '')

    def _exportar_imagenes(self):
        temp = context.get_resource('local_cache/nasal/temp')
        os.makedirs(temp, exist_ok=True)
        ruta = os.path.join(temp, 'upload_cpap_noche.jpg')
        try:
            self.monitor.exportar(ruta)
        except Exception as exc:  # noqa: BLE001 -- sin imagen el informe sube igual
            print(f'{self.TIPO}: no se pudo exportar la noche: {exc}')
            return {}
        return {'cpap_noche': ruta}

    def _texto_verdad(self):
        cp = C.parametros(self.caso['sueno'])
        filas = [f'<b>Presión eficaz</b>: {n(cp["p_eficaz"])} cmH₂O en lateral NREM; '
                 f'+{n(cp["supino"])} en supino, +{n(cp["rem"])} en REM (en REM supino: '
                 f'{n(cp["p_eficaz"] + cp["supino"] + cp["rem"])}). Talla que le calza: {cp["talla"]}. '
                 + ('Respira por la boca: con mascarilla nasal o almohadillas, fuga.' if cp['boca'] else '')]
        if self.T is None:
            return '<br>'.join(filas)
        if self.T.talla != cp['talla']:
            filas.append(f'La talla elegida ({self.T.talla}) no le calza: más fuga y menos presión real.')
        if cp['boca'] and self.T.interfaz != 'oronasal':
            filas.append('Con esta interfaz el aire sale por la boca: la presión real queda bajo la del equipo.')
        malos = []
        ult = 0
        for i, (t, p) in enumerate(self.T.cambios[1:], start=1):
            anterior = self.T.cambios[i - 1][1]
            if t - ult < C.INTERVALO_MIN_S:
                malos.append(f'{hhmm(t)}: a {n((t - ult) / 60, 0)} min del anterior')
            elif p > anterior and not self.T.cumple_criterio(ult, t):
                malos.append(f'{hhmm(t)}: subió sin criterio')
            ult = t
        filas.append('<b>Cambios fuera de la regla</b>: ' + ('; '.join(malos) if malos else 'ninguno') + '.')
        grados = ', '.join(f'{f["presion"]}: {dict(C.GRADOS)[self.T.grado(f["presion"])].lower()}'
                           for f in self.T.por_presion())
        filas.append(f'<b>Grado por presión</b> (con lo medido): {grados}.')
        p = self.spin_indicada.value()
        if p:
            filas.append(f'Indicó {p} cmH₂O; grado que corresponde: '
                         f'{dict(C.GRADOS)[self.T.grado(p)].lower()}; elegido: {self.cmb_grado.currentText().lower()}.')
        return '<br>'.join(filas)
