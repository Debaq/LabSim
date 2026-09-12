"""
Panel de trazas de un oído: donde se ve crecer el promedio y se marcan los picos.

Lo que cambia respecto del gráfico anterior, y por qué:

- SE MARCA HACIENDO CLIC EN LA CURVA. Antes había que dejar un cursor
  vertical sobre el pico y después hacer clic en una celda de la tabla; el
  alumno medía a ciegas. Acá se elige el pico en la barra de arriba, se hace
  clic cerca y la marca SE PEGA al extremo de la polaridad que corresponde
  (un P13 no puede quedar marcado en un valle).
- LA ESCALA SE ACOMODA SOLA a lo que hay dibujado. Un cVEMP ronda los
  100 µV y un oVEMP los 10: con una escala fija, uno de los dos siempre
  quedaba en una raya plana.
- LA VENTANA EMPIEZA ANTES DEL ESTÍMULO. La línea de base pre-estímulo es
  contra lo que se lee la respuesta, y sin ella dibujada la traza parecía
  empezar a existir en el cero.

Cada curva se apila bajo la anterior con su intensidad al costado, que es
como se lee una serie de umbral: la más intensa arriba, bajando.
"""

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters  # noqa: F401  (registra ImageExporter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QMenu, QPushButton,
                               QVBoxLayout, QWidget)

from vemp import protocol, theme
from vemp.widgets.kit import Pastilla, etiqueta


class PanelTrazas(QWidget):
    """Las curvas de UN oído."""

    sig_marca = Signal(str, str, float, float)   # curva, pico, lat, amp
    sig_desmarca = Signal(str, str)
    sig_seleccion = Signal(str)
    sig_borrar = Signal(str)

    def __init__(self, lado, parent=None):
        super().__init__(parent)
        self.lado = lado
        self.subtipo = protocol.CVEMP
        self.registros = {}       # nombre -> Registro
        self.trazas = {}          # nombre -> PlotDataItem
        self.etiquetas = {}       # nombre -> TextItem
        self.marcas = {}          # (nombre, pico) -> [TextItem, ScatterPlotItem]
        self.activa = None
        self.pico_activo = None
        self.escala = 100.0       # µV de media ventana
        self.escala_manual = False

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(6)
        raiz.addLayout(self._barra())
        self.plot = self._construir_plot()
        raiz.addWidget(self.plot, 1)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _barra(self):
        fila = QHBoxLayout()
        fila.setSpacing(6)
        self.pastilla = Pastilla(self.lado, 'od' if self.lado == 'OD' else 'oi')
        fila.addWidget(self.pastilla)

        self.lbl_curva = etiqueta('sin registros', rol='hint')
        fila.addWidget(self.lbl_curva)
        fila.addStretch(1)

        # Los botones de pico viven en su propio contenedor: cambian con el
        # subtipo y así se rehacen sin tocar el resto de la barra.
        self.caja_picos = QWidget()
        self.fila_picos = QHBoxLayout(self.caja_picos)
        self.fila_picos.setContentsMargins(0, 0, 0, 0)
        self.fila_picos.setSpacing(6)
        self.grupo_picos = QButtonGroup(self)
        self.grupo_picos.setExclusive(True)
        self.botones_pico = {}
        fila.addWidget(self.caja_picos)
        self._rehacer_botones_pico()

        self.btn_menos = QPushButton('−')
        self.btn_mas = QPushButton('+')
        for btn in (self.btn_menos, self.btn_mas):
            btn.setObjectName('btnEscala')
            btn.setFixedSize(26, 24)
            btn.setToolTip('Escala vertical')
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            fila.addWidget(btn)
        self.btn_menos.clicked.connect(lambda: self.cambiar_escala(2.0))
        self.btn_mas.clicked.connect(lambda: self.cambiar_escala(0.5))
        return fila

    def _rehacer_botones_pico(self):
        """Un botón por pico del subtipo activo: con cuál se marca."""
        for btn in self.botones_pico.values():
            self.grupo_picos.removeButton(btn)
            self.fila_picos.removeWidget(btn)
            btn.deleteLater()
        self.botones_pico = {}
        self.pico_activo = None
        for pico in protocol.PEAKS[self.subtipo]:
            btn = QPushButton(pico.upper())
            btn.setCheckable(True)
            btn.setFixedWidth(48)
            btn.setToolTip(f'Marcar {pico.upper()}: clic sobre la curva')
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.toggled.connect(lambda activo, p=pico: self._on_pico(p, activo))
            self.grupo_picos.addButton(btn)
            self.fila_picos.addWidget(btn)
            self.botones_pico[pico] = btn

    def _construir_plot(self):
        plot = pg.PlotWidget()
        plot.setBackground(theme.TARJETA)
        vb = plot.getViewBox()
        vb.setMouseEnabled(x=False, y=False)
        vb.setMenuEnabled(False)
        plot.hideButtons()
        plot.showGrid(x=True, y=True, alpha=0.18)
        plot.setLabel('bottom', 'ms', color=theme.TEXTO_TENUE)
        eje_x = plot.getAxis('bottom')
        eje_y = plot.getAxis('left')
        for eje in (eje_x, eje_y):
            eje.setPen(pg.mkPen(theme.BORDE_FUERTE))
            eje.setTextPen(pg.mkPen(theme.TEXTO_TENUE))
        eje_y.setStyle(showValues=False)
        eje_y.setWidth(12)
        plot.setMenuEnabled(False)

        # Estímulo en t=0 y zona pre-estímulo sombreada.
        self.linea_estimulo = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen(theme.ACENTO, width=1,
                                          style=Qt.PenStyle.DashLine))
        plot.addItem(self.linea_estimulo)
        inicio, _fin = protocol.VENTANA[self.subtipo]
        self.zona_pre = pg.LinearRegionItem(values=(inicio, 0), movable=False,
                                            brush=pg.mkBrush(220, 226, 234, 70))
        _sin_bordes(self.zona_pre)
        self.zona_pre.setZValue(-10)
        plot.addItem(self.zona_pre)

        self.separador = pg.InfiniteLine(
            pos=inicio, angle=90, pen=pg.mkPen(theme.BORDE, width=1))
        plot.addItem(self.separador)

        self.bandas_norma = []
        # Referencia de amplitud: las curvas van apiladas, así que el eje
        # vertical no tiene valores -- la escala la dice esta barra.
        self.barra_escala = pg.PlotDataItem(pen=pg.mkPen(theme.TEXTO_SUAVE, width=2))
        plot.addItem(self.barra_escala)
        self.texto_escala = pg.TextItem('', color=theme.TEXTO_SUAVE, anchor=(1, 0.5))
        fuente_escala = QFont()
        fuente_escala.setPointSizeF(7.5)
        self.texto_escala.setFont(fuente_escala)
        plot.addItem(self.texto_escala)
        plot.scene().sigMouseClicked.connect(self._on_click)
        # El rango se aplica con el plot ya asignado: _aplicar_rango() lee
        # self.plot, que todavía no existe mientras se construye.
        self.plot = plot
        self._aplicar_rango()
        return plot

    # ------------------------------------------------------------------
    # Subtipo / normativa / escala
    # ------------------------------------------------------------------

    def set_subtipo(self, subtipo):
        """Cambia los picos marcables y qué curvas se ven.

        Las curvas de los otros subtipos no se borran: se ocultan y vuelven
        al cambiar el combo. Un cVEMP y un oVEMP no comparten ni picos ni
        escala, así que no pueden dibujarse juntos.
        """
        self.subtipo = subtipo
        self._rehacer_botones_pico()

        inicio, fin = protocol.VENTANA[subtipo]
        self.zona_pre.setRegion((inicio, 0))
        self.separador.setPos(inicio)
        self._actualizar_visibles()
        self._reacomodar()

    def set_normativa(self, baseline):
        """Dibuja dónde se espera cada pico en este paciente.

        Es una referencia de lectura, no un criterio: la tabla del JSON no
        trae desviación estándar por pico, así que la banda es un ancho
        declarado (`ANCHO_BANDA_MS`) y se dibuja como tal.
        """
        for item in self.bandas_norma:
            self.plot.removeItem(item)
        self.bandas_norma = []
        if not baseline:
            return
        for pico, valores in baseline.items():
            if pico not in protocol.PEAKS[self.subtipo]:
                continue
            lat = valores.get('lat')
            if lat is None:
                continue
            banda = pg.LinearRegionItem(
                values=(lat - ANCHO_BANDA_MS, lat + ANCHO_BANDA_MS),
                movable=False, brush=pg.mkBrush(*theme.BANDA_NORMATIVA))
            _sin_bordes(banda)
            banda.setZValue(-9)
            self.plot.addItem(banda)
            self.bandas_norma.append(banda)

    def cambiar_escala(self, factor):
        self.escala = float(np.clip(self.escala * factor, 2.0, 4000.0))
        self.escala_manual = True
        self._reacomodar()

    def _autoescala(self):
        if self.escala_manual:
            return
        picos = [float(np.max(np.abs(r.y))) for r in self._visibles() if r.y.size]
        if not picos:
            return
        self.escala = max(max(picos) * 1.25, 2.0)

    def _canaleta(self):
        """Ancho del margen izquierdo donde van las intensidades.

        Generoso a propósito: ahí entran dos líneas de texto ('100 dB SPL' y
        '500Hz · n=200') y si la canaleta queda corta el borde de la vista
        las corta por la mitad.
        """
        inicio, fin = protocol.VENTANA[self.subtipo]
        return (fin - inicio) * 0.34

    def _aplicar_rango(self):
        inicio, fin = protocol.VENTANA[self.subtipo]
        self.plot.setXRange(inicio - self._canaleta(), fin, padding=0.005)
        visibles = self._visibles()
        piso = -self.escala * (0.6 * max(len(visibles) - 1, 0) + 1.0)
        self.plot.setYRange(piso, self.escala, padding=0.02)
        self._dibujar_barra_escala(fin, piso)

    def _dibujar_barra_escala(self, fin, piso):
        alto = self._paso_escala()
        inicio, _fin = protocol.VENTANA[self.subtipo]
        x = fin - (fin - inicio) * 0.03
        y0 = piso + self.escala * 0.18
        self.barra_escala.setData([x, x], [y0, y0 + alto])
        self.texto_escala.setText(f'{alto:.0f} µV' if alto >= 1 else f'{alto:.1f} µV')
        # A la izquierda de la barra: pegada al borde derecho se cortaba.
        self.texto_escala.setPos(x - (fin - inicio) * 0.015, y0 + alto / 2)

    def _paso_escala(self):
        """Un valor redondo cercano a media ventana: 100 µV, 20 µV, 5 µV."""
        objetivo = self.escala / 2.0
        for paso in (0.5, 1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000):
            if objetivo <= paso:
                return float(paso)
        return float(objetivo)

    # ------------------------------------------------------------------
    # Curvas
    # ------------------------------------------------------------------

    def agregar(self, registro):
        """Alta de una curva nueva (o refresco de una que se está promediando)."""
        nombre = registro.nombre
        self.registros[nombre] = registro
        if nombre not in self.trazas:
            color = theme.color_lado(self.lado)
            traza = self.plot.plot(pen=pg.mkPen(color, width=2))
            traza.setZValue(5)
            self.trazas[nombre] = traza
            self.etiquetas[nombre] = self._etiqueta_curva(registro)
            self.plot.addItem(self.etiquetas[nombre])
            self.seleccionar(nombre)
            self.escala_manual = False
        self.refrescar(nombre)

    def _etiqueta_curva(self, registro):
        # En la canaleta de la izquierda, fuera de la ventana de registro:
        # encima del trazo tapaban justo la parte que hay que mirar, y
        # contra el borde derecho las cortaba el eje. Ancladas a la derecha,
        # así crecen hacia afuera y nunca entran al trazo.
        item = pg.TextItem(anchor=(1, 0.5), color=theme.TEXTO_SUAVE)
        fuente = QFont()
        fuente.setPointSizeF(7.5)
        item.setFont(fuente)
        return item

    def refrescar(self, nombre):
        registro = self.registros.get(nombre)
        traza = self.trazas.get(nombre)
        if registro is None or traza is None:
            return
        self._autoescala()
        self._reacomodar()

    def _visibles(self):
        return [r for r in self.registros.values() if r.subtipo == self.subtipo]

    def _actualizar_visibles(self):
        for nombre, registro in self.registros.items():
            visible = registro.subtipo == self.subtipo
            self.trazas[nombre].setVisible(visible)
            self.etiquetas[nombre].setVisible(visible)
            for pico in protocol.PEAKS.get(registro.subtipo, ()):
                for item in self.marcas.get((nombre, pico), ()):
                    item.setVisible(visible)
        if self.activa is not None:
            registro = self.registros.get(self.activa)
            if registro is None or registro.subtipo != self.subtipo:
                visibles = self._visibles()
                self.seleccionar(visibles[-1].nombre if visibles else None)

    def _reacomodar(self):
        """Reparte las curvas visibles en ranuras, de la más intensa a la
        menos: es como se lee una serie de umbral."""
        visibles = sorted(self._visibles(),
                          key=lambda r: (-r.intensidad, r.nombre))
        paso = self.escala * 0.6
        inicio, fin = protocol.VENTANA[self.subtipo]
        for i, registro in enumerate(visibles):
            offset = -paso * i
            traza = self.trazas[registro.nombre]
            traza.setData(registro.x, registro.y + offset)
            activa = registro.nombre == self.activa
            color = theme.color_lado(self.lado) if activa else theme.TRAZO_INACTIVO
            if registro.aceptados:
                traza.setPen(pg.mkPen(color, width=2.2 if activa else 1.3))
            else:
                # Registro sin un solo barrido aceptado: es una línea recta y
                # punteada para que no se confunda con una respuesta ausente.
                traza.setPen(pg.mkPen(color, width=1.0,
                                      style=Qt.PenStyle.DashLine))
            traza.setZValue(6 if activa else 4)

            etiqueta_item = self.etiquetas[registro.nombre]
            etiqueta_item.setText(self._texto_etiqueta(registro))
            etiqueta_item.setColor(color)
            etiqueta_item.setPos(inicio - (fin - inicio) * 0.012, offset)
            self._reubicar_marcas(registro, offset)
        self._aplicar_rango()

    @staticmethod
    def _texto_etiqueta(registro):
        """Dos líneas: la intensidad --que es como se lee la serie-- y
        abajo con qué se registró."""
        unidad = 'SPL' if registro.ajustes.transductor == protocol.AEREO else 'FL'
        segunda = [registro.ajustes.freq.replace(' ', '')]
        if registro.ajustes.transductor != protocol.AEREO:
            segunda.append('óseo')
        segunda.append(f'n={registro.aceptados}' if registro.aceptados else 'sin barridos')
        return f'{registro.intensidad} dB {unidad}\n' + ' · '.join(segunda)

    def _offset(self, nombre):
        visibles = sorted(self._visibles(), key=lambda r: (-r.intensidad, r.nombre))
        paso = self.escala * 0.6
        for i, registro in enumerate(visibles):
            if registro.nombre == nombre:
                return -paso * i
        return 0.0

    def seleccionar(self, nombre):
        self.activa = nombre
        registro = self.registros.get(nombre)
        if registro is None:
            self.lbl_curva.setText('sin registros')
        else:
            self.lbl_curva.setText(
                f'{registro.nombre} · {registro.intensidad} dB · '
                f'{registro.aceptados} barridos')
            self.sig_seleccion.emit(nombre)
        self._reacomodar()

    def borrar(self, nombre):
        registro = self.registros.pop(nombre, None)
        if registro is None:
            return
        self.plot.removeItem(self.trazas.pop(nombre))
        self.plot.removeItem(self.etiquetas.pop(nombre))
        for pico in list(protocol.PEAKS.get(registro.subtipo, ())):
            self._quitar_marca_items(nombre, pico)
        if self.activa == nombre:
            visibles = self._visibles()
            self.activa = visibles[-1].nombre if visibles else None
        self.escala_manual = False
        self._autoescala()
        self._reacomodar()

    def limpiar(self):
        for nombre in list(self.registros):
            self.borrar(nombre)
        self.registros = {}
        self.activa = None
        self.escala_manual = False
        self.escala = 100.0
        self._aplicar_rango()

    # ------------------------------------------------------------------
    # Marcas
    # ------------------------------------------------------------------

    def _on_pico(self, pico, activo):
        self.pico_activo = pico if activo else None
        if activo:
            self.lbl_curva.setText(f'clic sobre la curva para marcar {pico.upper()}')
        else:
            self.seleccionar(self.activa)

    def _on_click(self, evento):
        if evento.button() != Qt.MouseButton.LeftButton:
            return
        vb = self.plot.getViewBox()
        punto = vb.mapSceneToView(evento.scenePos())
        x = float(punto.x())
        y = float(punto.y())

        if self.pico_activo is None:
            nombre = self._curva_mas_cercana(x, y)
            if nombre:
                self.seleccionar(nombre)
            return

        nombre = self.activa or self._curva_mas_cercana(x, y)
        registro = self.registros.get(nombre)
        if registro is None:
            return
        lat, amp = registro.pico_cercano(x, self.pico_activo)
        self.sig_marca.emit(nombre, self.pico_activo, lat, amp)

    def _curva_mas_cercana(self, x, y):
        """La curva cuyo trazo pasa más cerca del clic."""
        mejor, distancia = None, None
        for registro in self._visibles():
            offset = self._offset(registro.nombre)
            valor = registro.valor_en(x) + offset
            d = abs(valor - y)
            if distancia is None or d < distancia:
                mejor, distancia = registro.nombre, d
        return mejor

    def dibujar_marca(self, nombre, pico, lat, amp):
        registro = self.registros.get(nombre)
        if registro is None:
            return
        self._quitar_marca_items(nombre, pico)
        offset = self._offset(nombre)
        arriba = protocol.signo_pico(pico) > 0
        color = theme.color_lado(self.lado)

        punto = pg.ScatterPlotItem(
            x=[lat], y=[amp + offset], size=9, symbol='o',
            pen=pg.mkPen(color, width=1.5), brush=pg.mkBrush(theme.TARJETA))
        punto.setZValue(10)
        self.plot.addItem(punto)

        texto = pg.TextItem(pico.upper(), color=color,
                            anchor=(0.5, 1.25 if arriba else -0.25))
        fuente = QFont()
        fuente.setPointSizeF(7.5)
        fuente.setBold(True)
        texto.setFont(fuente)
        texto.setPos(lat, amp + offset)
        texto.setZValue(10)
        self.plot.addItem(texto)

        self.marcas[(nombre, pico)] = [punto, texto]

    def _quitar_marca_items(self, nombre, pico):
        for item in self.marcas.pop((nombre, pico), ()):
            self.plot.removeItem(item)

    def _reubicar_marcas(self, registro, offset):
        for pico, (lat, amp) in registro.marcas.items():
            if (registro.nombre, pico) in self.marcas:
                self._quitar_marca_items(registro.nombre, pico)
            if registro.subtipo != self.subtipo:
                continue
            self.dibujar_marca(registro.nombre, pico, lat, amp)

    # ------------------------------------------------------------------
    # Menú contextual / export
    # ------------------------------------------------------------------

    def contextMenuEvent(self, evento):
        if not self.registros:
            return
        menu = QMenu(self)
        borrar = menu.addAction('Eliminar curva seleccionada')
        sub = menu.addMenu('Borrar marca')
        acciones = {sub.addAction(p.upper()): p for p in protocol.PEAKS[self.subtipo]}
        todas = sub.addAction('Todas')
        ajustar = menu.addAction('Ajustar escala a la señal')

        accion = menu.exec_(evento.globalPos())
        if accion is None:
            return
        if accion == borrar and self.activa:
            self.sig_borrar.emit(self.activa)
        elif accion in acciones and self.activa:
            self.sig_desmarca.emit(self.activa, acciones[accion])
        elif accion == todas and self.activa:
            for pico in protocol.PEAKS[self.subtipo]:
                self.sig_desmarca.emit(self.activa, pico)
        elif accion == ajustar:
            self.escala_manual = False
            self._autoescala()
            self._reacomodar()

    def exportar(self, path):
        exportador = pg.exporters.ImageExporter(self.plot.plotItem)
        exportador.export(path)


def _sin_bordes(region):
    """Las LinearRegionItem traen dos líneas amarillas de agarre; acá las
    regiones son fondo, no controles."""
    for linea in region.lines:
        linea.setPen(pg.mkPen(None))
        linea.setHoverPen(pg.mkPen(None))


# Ancho de la banda que marca dónde se espera cada pico. Valor declarado --
# el JSON normativo no trae desviación estándar por pico.
ANCHO_BANDA_MS = 2.0
