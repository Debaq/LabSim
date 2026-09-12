"""
Análisis: las tres lecturas que un VEMP tiene y una sola curva no muestra.

- CRECIMIENTO / UMBRAL. La amplitud corregida contra la intensidad, un trazo
  por oído. Es la serie con la que se busca el umbral: la respuesta se
  achica hasta desaparecer, y la intensidad más baja que todavía tiene
  respuesta marcada es lo que el gráfico señala.
- SINTONÍA FRECUENCIAL. La mejor amplitud corregida en cada tone burst. En
  qué frecuencia responde mejor un oído es un dato del examen, y hasta acá
  la frecuencia era solo un combo que cambiaba la tabla normativa.
- LATENCIA / INTENSIDAD. Con la referencia normativa de cada pico dibujada.
  En el VEMP la latencia casi no se mueve (~0.06 ms/10 dB), así que lo que
  este gráfico muestra es sobre todo si los picos están donde se los espera.

Las amplitudes son las CORREGIDAS: son las únicas comparables entre
registros, porque el paciente no contrae igual dos veces.
"""

import pyqtgraph as pg
import pyqtgraph.exporters  # noqa: F401
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QVBoxLayout, QWidget

from vemp import protocol, theme
from vemp.widgets.kit import etiqueta, etiqueta_seccion

SIMBOLOS = {'p13': 'o', 'n23': 's', 'n10': 't', 'p16': 'd'}


class PanelAnalisis(QWidget):
    sig_condicion = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.subtipo = protocol.CVEMP
        self.baseline = {}
        self.transductor = protocol.AEREO

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(6)
        raiz.addLayout(self._filtros())

        self.lienzo = pg.GraphicsLayoutWidget()
        self.lienzo.setBackground(theme.TARJETA)
        raiz.addWidget(self.lienzo, 1)

        self.p_crecimiento = self._plot(0, 0, 'Amplitud corregida', 'Intensidad (dB)',
                                        colspan=2, titulo='Crecimiento y umbral')
        self.p_sintonia = self._plot(1, 0, 'Amplitud corregida', 'Tone burst',
                                     titulo='Sintonía frecuencial')
        # Sin grilla: pyqtgraph la dibuja POR ENCIMA de los items, y sobre
        # las barras se ve como si estuvieran rayadas.
        self.p_sintonia.showGrid(x=False, y=False)
        self.p_latencia = self._plot(1, 1, 'Latencia (ms)', 'Intensidad (dB)',
                                     titulo='Latencia de los picos')

        self.leyenda = etiqueta('', rol='hint')
        self.leyenda.setWordWrap(True)
        raiz.addWidget(self.leyenda)

    def _filtros(self):
        """Qué condición se está mirando.

        No es el equipo: acá se revisa lo YA registrado, y revisar el óseo o
        el otro tone burst no puede obligar a tocar los controles del
        registro. Arranca en la condición del equipo y se mueve sola cuando
        entra una curva nueva.
        """
        fila = QHBoxLayout()
        fila.setSpacing(8)
        fila.addWidget(etiqueta_seccion('Condición'))
        self.cb_transductor = QComboBox()
        self.cb_transductor.addItems(protocol.TRANSDUCTORES)
        fila.addWidget(self.cb_transductor)
        self.cb_freq = QComboBox()
        self.cb_freq.addItems(protocol.FRECUENCIAS)
        fila.addWidget(self.cb_freq)
        fila.addStretch(1)
        for combo in (self.cb_transductor, self.cb_freq):
            combo.currentTextChanged.connect(lambda *_: self.sig_condicion.emit())
        return fila

    def sincronizar(self, transductor, freq):
        for combo, valor in ((self.cb_transductor, transductor),
                             (self.cb_freq, freq)):
            combo.blockSignals(True)
            combo.setCurrentText(valor)
            combo.blockSignals(False)

    def condicion(self):
        return self.cb_transductor.currentText(), self.cb_freq.currentText()

    def _plot(self, fila, col, titulo_y, titulo_x, colspan=1, titulo=None):
        plot = self.lienzo.addPlot(row=fila, col=col, colspan=colspan)
        if titulo:
            plot.setTitle(titulo, color=theme.TEXTO_SUAVE, size='8pt')
        plot.setLabel('left', titulo_y, color=theme.TEXTO_TENUE)
        plot.setLabel('bottom', titulo_x, color=theme.TEXTO_TENUE)
        plot.showGrid(x=True, y=True, alpha=0.18)
        plot.setMenuEnabled(False)
        plot.hideButtons()
        plot.getViewBox().setMouseEnabled(x=False, y=False)
        for nombre in ('bottom', 'left'):
            eje = plot.getAxis(nombre)
            eje.setPen(pg.mkPen(theme.BORDE_FUERTE))
            eje.setTextPen(pg.mkPen(theme.TEXTO_TENUE))
        # Ejes quietos: con el autorango, dos puntos medidos a la misma
        # intensidad dejaban el eje entre 99.6 y 100.4 dB.
        plot.enableAutoRange(x=False, y=False)
        return plot

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------

    def set_subtipo(self, subtipo, baseline=None):
        self.subtipo = subtipo
        self.baseline = baseline or {}

    def actualizar(self, sesion):
        transductor, freq = self.condicion()
        self.transductor = transductor
        self._crecimiento(sesion, transductor, freq)
        self._sintonia(sesion, transductor)
        self._latencia(sesion, transductor, freq)
        self._leyenda(sesion, transductor, freq)

    def _rango_intensidad(self):
        """El eje es el rango del transductor, no el de lo medido: así se ve
        cuánto le queda de recorrido a la serie hacia el umbral."""
        lo, hi = protocol.RANGO_INTENSIDAD.get(
            self.transductor, protocol.RANGO_INTENSIDAD[protocol.AEREO])
        return lo - 2, hi + 2

    def _crecimiento(self, sesion, transductor, freq):
        plot = self.p_crecimiento
        plot.clear()
        maximo = 0.0
        hay = False
        for lado in protocol.LADOS:
            serie = sesion.serie(lado, self.subtipo, transductor, freq)
            if not serie:
                continue
            hay = True
            xs = [punto[0] for punto in serie]
            ys = [punto[1] for punto in serie]
            maximo = max(maximo, max(ys))
            color = theme.color_lado(lado)
            plot.plot(xs, ys, pen=pg.mkPen(color, width=2), symbol='o',
                      symbolSize=8, symbolBrush=pg.mkBrush(color),
                      symbolPen=pg.mkPen(theme.TARJETA, width=1.2))
            # El umbral que muestra la serie: la intensidad más baja con
            # respuesta marcada. No es el umbral informado -- ese lo escribe
            # el alumno en el informe.
            marca = pg.InfiniteLine(pos=xs[0], angle=90,
                                    pen=pg.mkPen(color, width=1,
                                                 style=pg.QtCore.Qt.PenStyle.DotLine))
            plot.addItem(marca)
        plot.setXRange(*self._rango_intensidad(), padding=0)
        plot.setYRange(0, max(maximo * 1.2, 1.0), padding=0)
        if not hay:
            plot.setTitle('Crecimiento y umbral — sin amplitudes marcadas',
                          color=theme.TEXTO_TENUE, size='8pt')
        else:
            plot.setTitle('Crecimiento y umbral', color=theme.TEXTO_SUAVE, size='8pt')

    def _sintonia(self, sesion, transductor):
        plot = self.p_sintonia
        plot.clear()
        maximo = 0.0
        frecuencias = list(protocol.FRECUENCIAS)
        ticks = [(i, f.replace(' ', '')) for i, f in enumerate(frecuencias)]
        plot.getAxis('bottom').setTicks([ticks])
        ancho = 0.32
        for j, lado in enumerate(protocol.LADOS):
            valores = sesion.sintonia(lado, self.subtipo, transductor)
            if not valores:
                continue
            xs, ys = [], []
            for i, f in enumerate(frecuencias):
                if valores.get(f) is None:
                    continue
                xs.append(i + (j - 0.5) * ancho)
                ys.append(valores[f])
            if not xs:
                continue
            color = pg.mkColor(theme.color_lado(lado))
            barras = pg.BarGraphItem(x=xs, height=ys, width=ancho * 0.9,
                                     brush=pg.mkBrush(color),
                                     pen=pg.mkPen(color))
            # Por encima de la grilla: si no, las líneas la cruzan y las
            # barras se ven rayadas.
            barras.setZValue(10)
            plot.addItem(barras)
            maximo = max(maximo, max(ys))
        plot.setXRange(-0.5, len(frecuencias) - 0.5, padding=0)
        plot.setYRange(0, max(maximo * 1.25, 1.0), padding=0)

    def _latencia(self, sesion, transductor, freq):
        plot = self.p_latencia
        plot.clear()
        picos = protocol.PEAKS[self.subtipo]

        for pico in picos:
            base = self.baseline.get(pico)
            if not base or base.get('lat') is None:
                continue
            linea = pg.InfiniteLine(pos=base['lat'], angle=0,
                                    pen=pg.mkPen(theme.ACENTO, width=1,
                                                 style=pg.QtCore.Qt.PenStyle.DashLine),
                                    label=pico.upper(),
                                    labelOpts={'color': theme.ACENTO, 'position': 0.05})
            plot.addItem(linea)

        lats = [b['lat'] for b in self.baseline.values() if b.get('lat') is not None]
        for lado in protocol.LADOS:
            for registro in sesion.por_condicion(lado, self.subtipo, transductor, freq):
                color = theme.color_lado(lado)
                for pico, (lat, _amp) in registro.marcas.items():
                    lats.append(lat)
                    plot.plot([registro.intensidad], [lat], pen=None,
                              symbol=SIMBOLOS.get(pico, 'o'), symbolSize=9,
                              symbolBrush=pg.mkBrush(color),
                              symbolPen=pg.mkPen(theme.TARJETA, width=1))
        plot.setXRange(*self._rango_intensidad(), padding=0)
        if lats:
            plot.setYRange(min(lats) - 4, max(lats) + 4, padding=0)
        else:
            plot.setYRange(0, protocol.VENTANA[self.subtipo][1] / 2, padding=0)

    def _leyenda(self, sesion, transductor, freq):
        partes = []
        for lado in protocol.LADOS:
            umbral = sesion.umbral_medido(lado, self.subtipo, transductor, freq)
            if umbral is not None:
                partes.append(f'{lado}: respuesta marcada hasta {umbral} dB')
        picos = ' / '.join(p.upper() for p in protocol.PEAKS[self.subtipo])
        base = (f'Amplitudes corregidas por EMG · símbolos de latencia: {picos} · '
                f'la punteada vertical marca la intensidad más baja con '
                f'respuesta marcada')
        self.leyenda.setText('   ·   '.join(partes + [base]))

    def exportar(self, path):
        pg.exporters.ImageExporter(self.lienzo.scene()).export(path)
