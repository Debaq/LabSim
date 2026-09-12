"""
Lo medido: la tabla de registros y la comparación entre oídos.

La tabla lista TODAS las curvas del examen, no la seleccionada: un VEMP se
lee como serie (la misma condición a varias intensidades, los dos oídos a la
misma intensidad) y con una tabla por curva eso no se ve.

Las tres columnas de amplitud dicen cosas distintas y por eso están las tres:
la pico-pico CRUDA es lo que mide la pantalla, el EMG es con cuánta
contracción se midió, y la CORREGIDA (cruda/EMG) es la única que se puede
comparar con el otro oído. La asimetría de abajo se calcula con la corregida.

No hay veredicto en ninguna de las dos: se muestran el número y la cuenta.
Qué asimetría es patológica lo dice quien informa.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from vemp import protocol, theme
from vemp.widgets.kit import Dato, Tarjeta, etiqueta

COLUMNAS = ['Curva', 'Oído', 'dB', 'Tone burst', 'Lat 1', 'Lat 2',
            'p-p µV', 'EMG µV', 'p-p corr.', 'Barridos']


class TablaMedidas(QWidget):
    sig_seleccion = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.subtipo = protocol.CVEMP
        self._nombres = []

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setShowGrid(False)
        self.tabla.setAlternatingRowColors(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.itemSelectionChanged.connect(self._on_seleccion)
        raiz.addWidget(self.tabla)

    def set_subtipo(self, subtipo):
        self.subtipo = subtipo
        picos = protocol.PEAKS[subtipo]
        cabeceras = list(COLUMNAS)
        cabeceras[4] = f'{picos[0].upper()} ms'
        cabeceras[5] = f'{picos[1].upper()} ms'
        self.tabla.setHorizontalHeaderLabels(cabeceras)

    def poblar(self, registros, activa=None):
        """registros: lista de Registro, en el orden en que se tomaron."""
        self.tabla.blockSignals(True)
        self._nombres = [r.nombre for r in registros]
        self.tabla.setRowCount(len(registros))
        for fila, registro in enumerate(registros):
            self._fila(fila, registro)
        if activa in self._nombres:
            self.tabla.selectRow(self._nombres.index(activa))
        self.tabla.blockSignals(False)

    def _fila(self, fila, registro):
        picos = registro.picos_esperados
        marcas = registro.marcas
        p2p = registro.p2p()
        corregida = registro.p2p_corregida()
        emg = registro.emg_medio
        unidad = 'SPL' if registro.ajustes.transductor == protocol.AEREO else 'FL'

        valores = [
            registro.nombre,
            registro.lado,
            f'{registro.intensidad} {unidad}',
            registro.ajustes.freq,
            self._num(marcas.get(picos[0], [None])[0], 2),
            self._num(marcas.get(picos[1], [None])[0], 2),
            self._num(p2p, 1),
            self._num(emg, 0),
            self._num(corregida, 2),
            f'{registro.aceptados}' + (f' (−{registro.rechazados})'
                                       if registro.rechazados else ''),
        ]
        color = QColor(theme.color_lado(registro.lado))
        for col, valor in enumerate(valores):
            item = QTableWidgetItem(str(valor))
            if col in (4, 5, 6, 7, 8, 9):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight |
                                      Qt.AlignmentFlag.AlignVCenter)
            if col == 1:
                item.setForeground(QBrush(color))
                fuente = QFont()
                fuente.setBold(True)
                item.setFont(fuente)
            if col == 7 and emg and not protocol.emg_en_banda(registro.subtipo, emg):
                item.setForeground(QBrush(QColor(theme.ALERTA)))
            self.tabla.setItem(fila, col, item)

    @staticmethod
    def _num(valor, decimales):
        if valor is None:
            return '—'
        return f'{valor:.{decimales}f}'

    def _on_seleccion(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return
        indice = filas[0].row()
        if 0 <= indice < len(self._nombres):
            self.sig_seleccion.emit(self._nombres[indice])


class BarraAsimetria(QWidget):
    """Las dos amplitudes corregidas, una contra otra.

    El dibujo es la cuenta: dos barras desde el centro, cada una
    proporcional a su oído. Que una sea la mitad de la otra se ve antes de
    leer el porcentaje.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.od = None
        self.oi = None
        self.setMinimumHeight(46)

    def set_valores(self, od, oi):
        self.od = od
        self.oi = oi
        self.update()

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ancho = self.width()
        alto = self.height()
        centro = ancho / 2
        margen = 6
        h = 16
        y = (alto - h) / 2 - 4

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(theme.TARJETA_ALT)))
        p.drawRoundedRect(margen, int(y), int(ancho - 2 * margen), h, 4, 4)

        fuente = QFont(self.font())
        fuente.setPointSizeF(7.0)
        p.setFont(fuente)
        p.setPen(QColor(theme.TEXTO_TENUE))
        p.drawText(margen, alto - 2, 'OD')
        p.drawText(ancho - margen - 16, alto - 2, 'OI')

        maximo = max([v for v in (self.od, self.oi) if v] or [0])
        if maximo <= 0:
            p.end()
            return
        util = centro - margen - 4
        p.setPen(Qt.PenStyle.NoPen)
        if self.od:
            largo = util * (self.od / maximo)
            p.setBrush(QBrush(QColor(theme.OD)))
            p.drawRoundedRect(int(centro - 2 - largo), int(y), int(largo), h, 3, 3)
        if self.oi:
            largo = util * (self.oi / maximo)
            p.setBrush(QBrush(QColor(theme.OI)))
            p.drawRoundedRect(int(centro + 2), int(y), int(largo), h, 3, 3)
        p.setPen(QColor(theme.BORDE_FUERTE))
        p.drawLine(int(centro), int(y) - 3, int(centro), int(y) + h + 3)
        p.end()


class PanelAsimetria(Tarjeta):
    """Resumen del subtipo activo: las dos amplitudes y su asimetría."""

    def __init__(self, parent=None):
        super().__init__('Comparación entre oídos', parent=parent)
        fila = QHBoxLayout()
        fila.setSpacing(16)
        self.dato_od = Dato('OD corregida')
        self.dato_oi = Dato('OI corregida')
        self.dato_ar = Dato('Asimetría', unidad='%')
        for dato in (self.dato_od, self.dato_oi, self.dato_ar):
            fila.addWidget(dato)
        fila.addStretch(1)
        self.agregar_layout(fila)

        self.barra = BarraAsimetria()
        self.agregar(self.barra)

        self.lbl_cuenta = etiqueta('', rol='hint')
        self.lbl_cuenta.setWordWrap(True)
        self.agregar(self.lbl_cuenta)

    def set_resumen(self, subtipo, od, oi, ratio):
        """od/oi: Registro elegido de cada oído (o None)."""
        corr_od = od.p2p_corregida() if od else None
        corr_oi = oi.p2p_corregida() if oi else None
        self.set_titulo(f'Comparación entre oídos · {protocol.SUBTIPO_CORTO[subtipo]}')
        self.dato_od.set_valor('—' if corr_od is None else f'{corr_od:.2f}')
        self.dato_oi.set_valor('—' if corr_oi is None else f'{corr_oi:.2f}')
        self.dato_ar.set_valor('—' if ratio is None else f'{ratio:.0f}')
        self.barra.set_valores(corr_od, corr_oi)

        if ratio is None:
            faltan = []
            if corr_od is None:
                faltan.append('OD')
            if corr_oi is None:
                faltan.append('OI')
            self.lbl_cuenta.setText(
                'Falta una amplitud pico-pico marcada en ' + ' y '.join(faltan or ['los dos oídos'])
                + '. La asimetría necesita los dos oídos medidos en la misma condición.')
            return
        self.lbl_cuenta.setText(
            f'|{corr_od:.2f} − {corr_oi:.2f}| / ({corr_od:.2f} + {corr_oi:.2f}) × 100  '
            f'·  crudas: OD {od.p2p():.1f} µV con EMG {od.emg_medio:.0f} µV, '
            f'OI {oi.p2p():.1f} µV con EMG {oi.emg_medio:.0f} µV')
