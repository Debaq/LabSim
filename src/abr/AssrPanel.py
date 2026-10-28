"""Panel del ASSR: del registro al audiograma en dB eHL.

Cuatro vistas del MISMO registro, para recorrerlo de punta a punta:

- Rastro: la época cruda del EEG, el promedio y la componente de la
  portadora elegida. El promedio es una suma de senoides: eso es lo que la
  FFT separa.
- Espectro (FFT): una línea por cada modulación, con el ruido de los bins
  vecinos contra el que se compara. Un clic sobre una línea elige esa
  portadora.
- Vectores: el vector de la respuesta (módulo = amplitud, ángulo = fase), los
  sub-promedios que lo van formando y el círculo de ruido. Fuera del círculo
  hay respuesta; dentro, no se puede distinguir del ruido.
- Audiograma estimado: el menor nivel con respuesta por portadora, y ese
  mismo valor con la corrección a eHL.

El modelo vive en abr/assr.py.
"""
# pylint: disable=no-name-in-module
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters  # noqa: F401  (pg.exporters en exportar)
from PySide6.QtCore import QCoreApplication, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
                               QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QPushButton, QSpinBox,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from abr import assr
from core import tema
from abr.ABR_generator import ABRGenerator, case_quality

tr = QCoreApplication.translate

COLOR = {'OD': tema.OD, 'OI': tema.OI}
COLUMNAS = ("Oído", "Portadora", "Mod. (Hz)", "Nivel (dB HL)", "Épocas",
            "Amp. (nV)", "Ruido (nV)", "F", "p", "Estado")
EPOCAS_POR_TICK = 3
BLOQUES_POLAR = 6
VENTANA_RASTRO_S = 0.25
F_MAX_VISTA = 150.0
# Qué tan lejos del círculo cuenta como "hay respuesta" en la lectura de
# los vectores: el círculo es el 95 % del ruido del promedio.
RADIO_95 = float(np.sqrt(-np.log(0.05)))


def _etiqueta_freq(f):
    return f"{f / 1000:g} kHz" if f >= 1000 else f"{f} Hz"


def _circulo(radio, n=120):
    a = np.linspace(0, 2 * np.pi, n)
    return radio * np.cos(a), radio * np.sin(a)


class AssrPanel(QWidget):
    """Registro, análisis y audiograma del ASSR."""

    # Se emite cuando el registro no puede seguir (todas las portadoras
    # terminaron en automático, o se llenó el límite de épocas).
    finished = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rec = None
        self.docente = False
        self.canal = ('OD', 1000)
        self._sin_eventos = False
        self.data = None
        self.technical = {}
        self.abr_casos = None
        self._vivo = None
        self.correccion = dict(assr.DEFAULT_EHL_CORRECTION)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(4, 4, 4, 4)
        self.lbl_estado = QLabel("")
        self.lbl_estado.setWordWrap(True)
        raiz.addWidget(self.lbl_estado)

        # --- tabla de portadoras y controles ---------------------------
        arriba = QHBoxLayout()
        self.tabla = QTableWidget(8, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(
            [tr("AssrPanel", c) for c in COLUMNAS])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setMaximumHeight(300)
        self.tabla.itemSelectionChanged.connect(self._fila_elegida)
        arriba.addWidget(self.tabla, 3)

        lateral = QVBoxLayout()
        self.chk_auto = QCheckBox(tr("AssrPanel", "Niveles automáticos"))
        self.chk_auto.setToolTip(tr(
            "AssrPanel",
            "Como un equipo clínico: baja 10 dB después de una respuesta y "
            "sube 10 dB después de un 'sin respuesta' concluyente, por "
            "portadora"))
        lateral.addWidget(self.chk_auto)
        self.btn_reiniciar = QPushButton(tr("AssrPanel", "Reiniciar registro"))
        self.btn_reiniciar.clicked.connect(self.reiniciar)
        lateral.addWidget(self.btn_reiniciar)
        caja = QGroupBox(tr("AssrPanel", "Corrección a eHL (dB)"))
        caja.setToolTip(tr(
            "AssrPanel",
            "Lo que el equipo resta al menor nivel con respuesta para "
            "informar el umbral estimado. Es calibrable"))
        cl = QGridLayout(caja)
        self.sb_corr = {}
        for i, f in enumerate(assr.CARRIERS):
            cl.addWidget(QLabel(_etiqueta_freq(f)), i // 2, (i % 2) * 2)
            sb = QSpinBox()
            sb.setRange(0, 30)
            sb.setValue(int(self.correccion[f]))
            sb.valueChanged.connect(self._corregir)
            self.sb_corr[f] = sb
            cl.addWidget(sb, i // 2, (i % 2) * 2 + 1)
        lateral.addWidget(caja)
        lateral.addStretch(1)
        arriba.addLayout(lateral, 1)
        raiz.addLayout(arriba)

        # --- los cuatro gráficos ---------------------------------------
        grilla = QGridLayout()
        raiz.addLayout(grilla, 1)
        self.p_rastro = self._plot("Rastro", "Tiempo (ms)", "µV")
        self.p_fft = self._plot("Espectro (FFT)", "Frecuencia (Hz)", "nV")
        self.p_polar = self._plot("Vectores de la portadora elegida", "", "")
        self.p_audio = self._plot("Audiograma estimado (dB eHL)",
                                  "Frecuencia", "dB")
        cab = QHBoxLayout()
        cab.addWidget(QLabel(tr("AssrPanel", "Rastro")))
        self.cb_rastro = QComboBox()
        self.cb_rastro.addItems([
            tr("AssrPanel", "Promedio y componente"),
            tr("AssrPanel", "Época cruda (última)")])
        self.cb_rastro.currentIndexChanged.connect(self.refrescar)
        cab.addWidget(self.cb_rastro)
        cab.addStretch(1)
        col1 = QVBoxLayout()
        col1.addLayout(cab)
        col1.addWidget(self.p_rastro, 1)
        grilla.addLayout(col1, 0, 0)
        grilla.addWidget(self.p_fft, 0, 1)
        grilla.addWidget(self.p_polar, 1, 0)
        grilla.addWidget(self.p_audio, 1, 1)
        self.lbl_polar = QLabel("")
        self.lbl_polar.setAlignment(Qt.AlignCenter)
        self.lbl_polar.setWordWrap(True)
        raiz.addWidget(self.lbl_polar)

        self.p_polar.setAspectLocked(True)
        self.p_polar.hideAxis('bottom')
        self.p_polar.hideAxis('left')
        self._formato_audiograma(self.p_audio)
        self.p_fft.scene().sigMouseClicked.connect(self._clic_fft)
        self.limpiar()

    def _plot(self, titulo, etiqueta_x, etiqueta_y):
        w = pg.PlotWidget(background='w')
        w.setTitle(tr("AssrPanel", titulo), size='9pt', color='#333')
        w.showGrid(x=True, y=True, alpha=0.15)
        w.setMenuEnabled(False)
        for lado, txt in (('bottom', etiqueta_x), ('left', etiqueta_y)):
            if txt:
                w.setLabel(lado, tr("AssrPanel", txt))
        for lado in ('bottom', 'left'):
            w.getAxis(lado).enableAutoSIPrefix(False)
        return w

    @staticmethod
    def _formato_audiograma(plot):
        """Como un audiograma: frecuencias ARRIBA, 0 dB arriba y la pérdida
        hacia abajo."""
        plot.showAxis('top')
        plot.hideAxis('bottom')
        eje = plot.getAxis('top')
        eje.setTicks([[(i, _etiqueta_freq(f))
                       for i, f in enumerate(assr.CARRIERS)]])
        plot.setXRange(-0.5, 3.5)
        plot.setYRange(-10, 120)
        plot.invertY(True)
        plot.setMouseEnabled(x=False, y=False)

    # ------------------------------------------------------------------
    # caso y registro
    # ------------------------------------------------------------------
    def set_case(self, data, abr_od, abr_oi, technical, docente=False):
        """Recibe el caso del paciente (None = sin atención)."""
        self.docente = docente
        self._vivo = None
        self.technical = technical or {}
        self.data = data
        if data is None or (abr_od is None and abr_oi is None):
            self.rec = None
            self.limpiar()
            self.lbl_estado.setText(tr(
                "AssrPanel", "SIN REGISTRO (el caso no trae ABR para estimar "
                "umbrales por frecuencia)") if data is not None else "")
            return
        self.abr_casos = {'OD': abr_od, 'OI': abr_oi}
        self.reiniciar()

    def reiniciar(self):
        if self.abr_casos is None or self.data is None:
            return
        casos = self.abr_casos
        caso_ref = casos['OD'] or casos['OI'] or {}
        peor, _desbalance, _ok = ABRGenerator.impedance_report(self.technical)
        self.rec = assr.Recording(
            casos, patient=self.data,
            quality=case_quality(caso_ref),
            inquietud=float(caso_ref.get('inquietud') or 0.0),
            reject_uv=float(self.technical.get('artifact_reject_uv') or 25.0),
            impedance_kohm=peor,
            transducer=self.technical.get('transducer') or 'insert_earphone')
        self.canal = next((c for c in assr.channels() if self.rec.active(c)),
                          ('OD', 1000))
        self._armar_tabla()
        self._bloquear(False)
        self.refrescar()

    def limpiar(self):
        self.tabla.clearContents()
        for p in (self.p_rastro, self.p_fft, self.p_polar, self.p_audio):
            p.clear()
        self.lbl_polar.setText("")

    def _armar_tabla(self):
        self._sin_eventos = True
        self.tabla.clearContents()
        for fila, canal in enumerate(assr.channels()):
            side, f = canal
            activo = self.rec.active(canal)
            items = [side, _etiqueta_freq(f), f"{assr.fm_hz(side, f):.1f}"]
            for col, texto in enumerate(items):
                it = QTableWidgetItem(texto)
                it.setForeground(QColor(COLOR[side]))
                it.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(fila, col, it)
            sb = QSpinBox()
            sb.setRange(assr.LEVEL_MIN, assr.LEVEL_MAX)
            sb.setSingleStep(assr.LEVEL_STEP)
            sb.setValue(self.rec.levels[canal])
            sb.setEnabled(activo)
            sb.valueChanged.connect(
                lambda v, c=canal: self._cambiar_nivel(c, v))
            self.tabla.setCellWidget(fila, 3, sb)
        self._sin_eventos = False
        self.tabla.selectRow(assr.channels().index(self.canal))

    def _cambiar_nivel(self, canal, valor):
        if self._sin_eventos or self.rec is None:
            return
        self.rec.set_level(canal, valor)
        self.refrescar()

    def _fila_elegida(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas or self.rec is None:
            return
        self.canal = assr.channels()[filas[0].row()]
        self.refrescar()

    def _corregir(self, _valor):
        for f, sb in self.sb_corr.items():
            self.correccion[f] = float(sb.value())
        self.dibujar_audiograma()

    def _clic_fft(self, evento):
        if self.rec is None:
            return
        pos = self.p_fft.getViewBox().mapSceneToView(evento.scenePos())
        mejor, dist = None, 3.0
        for c in assr.channels():
            d = abs(assr.fm_hz(*c) - pos.x())
            if d < dist and self.rec.active(c):
                mejor, dist = c, d
        if mejor is not None:
            self.tabla.selectRow(assr.channels().index(mejor))

    # ------------------------------------------------------------------
    # tick del registro
    # ------------------------------------------------------------------
    def tick(self, epocas=EPOCAS_POR_TICK):
        """Un paso del registro. Devuelve el texto de estado."""
        if self.rec is None:
            return ""
        hay_registro = ABRGenerator.electrode_state(self.technical)[0] if self.technical else True
        if not hay_registro:
            # Entradas abiertas (sin activo o sin referencia): el rechazo
            # descarta todo y no entra ninguna época, como en el ABR.
            self.lbl_estado.setText(tr("AssrPanel", "SIN ELECTRODOS · no entra ninguna época"))
            return self.lbl_estado.text()
        self.rec.step(epocas)
        motivo = None
        if self.chk_auto.isChecked():
            self.rec.auto_step()
            self._sincronizar_niveles()
            if self.rec.all_done():
                motivo = tr("AssrPanel", "todas las portadoras terminaron")
        if self.rec.n >= assr.MAX_EPOCHS:
            motivo = tr("AssrPanel", "se llegó al límite de épocas")
        self.refrescar()
        if motivo:
            self.detener()
            self.finished.emit(motivo)
        return self.lbl_estado.text()

    # ------------------------------------------------------------------
    # guardado, informe y sesiones anteriores
    # ------------------------------------------------------------------
    def hay_registro(self):
        return self.rec is not None and self.rec.n > 0

    def en_vivo(self):
        """Hay un registro que se puede seguir (no uno guardado)."""
        return self.rec is not None and not getattr(self.rec, 'guardado', False)

    def snapshot(self):
        if not self.hay_registro():
            return None
        if getattr(self.rec, 'guardado', False):
            return dict(self.rec.snap, correccion={
                str(f): v for f, v in self.correccion.items()})
        return self.rec.snapshot(self.correccion)

    def cargar_snapshot(self, snap):
        """Muestra un registro guardado (el informe, una sesión anterior).

        Si había uno en vivo se aparta: al volver a la atención actual se
        sigue registrando donde se había quedado (ver volver_vivo)."""
        if self.en_vivo():
            self._vivo = self.rec
        self.rec = assr.RecordingGuardado(snap)
        for f, v in (snap.get('correccion') or {}).items():
            if int(f) in self.sb_corr:
                self.correccion[int(f)] = float(v)
                self.sb_corr[int(f)].blockSignals(True)
                self.sb_corr[int(f)].setValue(int(v))
                self.sb_corr[int(f)].blockSignals(False)
        self.canal = next((c for c in assr.channels() if self.rec.active(c)),
                          ('OD', 1000))
        self._armar_tabla()
        self._bloquear(True)
        self.refrescar()

    def volver_vivo(self):
        """Vuelve al registro que se apartó al mirar una sesión anterior."""
        if self._vivo is None:
            return False
        self.rec, self._vivo = self._vivo, None
        self.canal = next((c for c in assr.channels() if self.rec.active(c)),
                          ('OD', 1000))
        self._armar_tabla()
        self._bloquear(False)
        self.refrescar()
        return True

    def set_read_only(self, on):
        """Sesión anterior: se mira, no se registra ni se cambian niveles."""
        self._bloquear(on or not self.en_vivo())

    def _bloquear(self, on):
        for fila in range(self.tabla.rowCount()):
            sb = self.tabla.cellWidget(fila, 3)
            if sb is not None:
                sb.setEnabled(not on and self.rec is not None
                              and self.rec.active(assr.channels()[fila]))
        self.chk_auto.setEnabled(not on)
        self.btn_reiniciar.setEnabled(not on and self.abr_casos is not None)

    def exportar(self, prefijo, carpeta):
        """JPEG de las cuatro vistas para el informe: {sufijo: ruta}.

        Rastro y espectro salen como están en pantalla. Los vectores y el
        audiograma se dibujan aparte con su proporción propia (cuadrado y
        alto): en el panel son apaisados porque comparten la grilla, y en el
        papel quedaban aplastados.
        """
        import os
        salida = {}
        for sufijo, plot in (('assr_rastro', self.p_rastro),
                             ('assr_fft', self.p_fft)):
            ruta = os.path.join(carpeta, f'{prefijo}_{sufijo}.jpg')
            try:
                pg.exporters.ImageExporter(plot.getPlotItem()).export(ruta)
            except Exception as exc:  # noqa: BLE001
                print(f"ASSR: no se pudo exportar {sufijo}: {exc}")
                continue
            if os.path.isfile(ruta):
                salida[sufijo] = ruta
        aparte = (('assr_polar', self.dibujar_polar, None, 560, 560),
                  ('assr_audio', self.dibujar_audiograma,
                   self._formato_audiograma, 620, 560))
        for sufijo, dibujar, formato, ancho, alto in aparte:
            ruta = os.path.join(carpeta, f'{prefijo}_{sufijo}.jpg')
            try:
                w = pg.PlotWidget(background='w')
                w.resize(ancho, alto)
                w.showGrid(x=True, y=True, alpha=0.15)
                w.setMenuEnabled(False)
                for lado in ('bottom', 'left'):
                    w.getAxis(lado).enableAutoSIPrefix(False)
                if sufijo == 'assr_polar':
                    w.setAspectLocked(True)
                    w.hideAxis('bottom')
                    w.hideAxis('left')
                else:
                    w.setLabel('left', 'dB eHL')
                    w.setTitle(tr("AssrPanel", "Audiograma estimado (dB eHL)"),
                               size='10pt', color='#333')
                if formato:
                    formato(w)
                dibujar(w)
                w.grab().save(ruta, 'JPG', 92)
            except Exception as exc:  # noqa: BLE001
                print(f"ASSR: no se pudo exportar {sufijo}: {exc}")
                continue
            if os.path.isfile(ruta):
                salida[sufijo] = ruta
        return salida

    def actualizar_equipo(self, technical):
        """El equipo pudo cambiar (rechazo, impedancias): vale desde ya."""
        self.technical = technical or {}
        if self.rec is None:
            return
        peor, _d, _ok = ABRGenerator.impedance_report(self.technical)
        self.rec.impedance_kohm = peor
        self.rec.reject_uv = float(
            self.technical.get('artifact_reject_uv') or 25.0)
        self.rec.transducer = (self.technical.get('transducer')
                               or 'insert_earphone')

    def detener(self):
        """Detener es una pausa: el tramo de cada portadora sigue abierto."""
        if self.rec is not None:
            self.refrescar()

    def _sincronizar_niveles(self):
        self._sin_eventos = True
        for fila, canal in enumerate(assr.channels()):
            sb = self.tabla.cellWidget(fila, 3)
            if sb is not None and sb.value() != self.rec.levels[canal]:
                sb.setValue(self.rec.levels[canal])
        self._sin_eventos = False

    # ------------------------------------------------------------------
    # dibujo
    # ------------------------------------------------------------------
    def refrescar(self, *_):
        if self.rec is None:
            return
        rec = self.rec
        seg = rec.n * assr.EPOCH_S
        aviso = (tr("AssrPanel", "Registro guardado, solo lectura · ")
                 if getattr(rec, 'guardado', False) else "")
        self.lbl_estado.setText(aviso + tr(
            "AssrPanel",
            "{n} épocas aceptadas ({t:02d}:{s:02d}) · {r} rechazadas por "
            "artefacto").format(n=rec.n, t=int(seg // 60), s=int(seg % 60),
                                r=rec.rejected))
        for fila, canal in enumerate(assr.channels()):
            st = rec.stats(canal)
            valores = (str(st['n']), f"{st['amp_nv']:.0f}",
                       f"{st['noise_nv']:.0f}", f"{st['f_ratio']:.1f}",
                       f"{st['p']:.3f}" if st['p'] >= 0.001 else "<0.001",
                       st['estado'] if rec.active(canal) else "sin datos")
            for col, texto in enumerate(valores, start=4):
                it = QTableWidgetItem(texto)
                it.setTextAlignment(Qt.AlignCenter)
                if col == 9 and st['estado'] == 'respuesta':
                    it.setForeground(QColor(tema.OK))
                self.tabla.setItem(fila, col, it)
        self.dibujar_rastro()
        self.dibujar_fft()
        self.dibujar_polar()
        self.dibujar_audiograma()

    def dibujar_rastro(self):
        p, rec = self.p_rastro, self.rec
        p.clear()
        if rec.n == 0:
            return
        if self.cb_rastro.currentIndex() == 1 and rec.last_epoch is not None:
            t, y = rec.trace(rec.last_epoch, window=VENTANA_RASTRO_S)
            p.plot(t * 1000.0, y, pen=pg.mkPen('#777', width=1))
            return
        medio, _n = rec.mean_spectrum(self.canal)
        t, y = rec.trace(medio, window=VENTANA_RASTRO_S)
        p.plot(t * 1000.0, y, pen=pg.mkPen('#222', width=1.5))
        k = assr.FM_BIN[self.canal[0]][assr.CARRIERS.index(self.canal[1])]
        t, c = rec.trace(medio, only_bin=k, window=VENTANA_RASTRO_S)
        p.plot(t * 1000.0, c, pen=pg.mkPen(COLOR[self.canal[0]], width=2.5))

    def dibujar_fft(self):
        p, rec = self.p_fft, self.rec
        p.clear()
        medio, n = rec.mean_spectrum(self.canal)
        if n == 0:
            return
        sel = (rec.freqs <= F_MAX_VISTA)
        f, amp = rec.freqs[sel], np.abs(medio[sel]) * 1000.0
        p.plot(f, amp, pen=pg.mkPen('#555', width=1),
               fillLevel=0, brush=pg.mkBrush(150, 150, 150, 70))
        st = rec.stats(self.canal)
        k = assr.FM_BIN[self.canal[0]][assr.CARRIERS.index(self.canal[1])]
        vec = rec.neighbor_bins(self.canal)
        if len(vec):
            region = pg.LinearRegionItem(
                (vec.min() * assr.DF, vec.max() * assr.DF), movable=False,
                brush=pg.mkBrush(255, 235, 59, 40))
            region.setZValue(-10)
            for linea in region.lines:
                linea.setPen(pg.mkPen(None))
            p.addItem(region)
        p.addItem(pg.InfiniteLine(
            pos=st['noise_nv'], angle=0,
            pen=pg.mkPen(tema.AVISO, width=1.2, style=Qt.DashLine)))
        for canal in assr.channels():
            if not rec.active(canal):
                continue
            kc = assr.FM_BIN[canal[0]][assr.CARRIERS.index(canal[1])]
            sel_c = canal == self.canal
            p.addItem(pg.InfiniteLine(
                pos=kc * assr.DF, angle=90,
                pen=pg.mkPen(COLOR[canal[0]], width=2.5 if sel_c else 0.8,
                             style=Qt.SolidLine if sel_c else Qt.DotLine)))
            # El OD arriba y el OI abajo: las modulaciones de los dos oídos
            # están a 2 bins y los rótulos se pisaban.
            txt = pg.TextItem(f"{canal[1] / 1000:g}", color=COLOR[canal[0]],
                              anchor=(0.5, 1.0))
            txt.setFont(pg.QtGui.QFont('', 7))
            alto = max(float(amp.max()) * 1.25, 60.0)
            txt.setPos(kc * assr.DF, alto * (0.99 if canal[0] == 'OD' else 0.91))
            p.addItem(txt)
        p.setXRange(40, 130)
        p.setYRange(0, max(float(amp.max()) * 1.25, 60.0))

    def dibujar_polar(self, plot=None):
        p, rec = plot or self.p_polar, self.rec
        p.clear()
        st = rec.stats(self.canal)
        if st['n'] < 2:
            if plot is None:
                self.lbl_polar.setText("")
            return
        # Sub-promedios: cada punto es el promedio de un bloque de épocas;
        # el vector final es el promedio de todas.
        medio, bloques, camino = rec.polar_data(self.canal, BLOQUES_POLAR)
        radio_ruido = RADIO_95 * st['noise_nv']
        radios = [abs(b) for b in bloques] or [0.0]
        lim = max(abs(medio) * 1.3, radio_ruido * 1.6,
                  0.9 * float(np.percentile(radios, 90)), 25.0)
        # Rejilla: anillos y ejes.
        paso = 10.0 ** np.floor(np.log10(lim))
        for mult in (1, 2, 5):
            if lim / (paso * mult) <= 6:
                paso *= mult
                break
        r = paso
        while r <= lim * 1.05:
            x, y = _circulo(r)
            p.plot(x, y, pen=pg.mkPen('#ddd', width=1))
            tx = pg.TextItem(f"{r:g} nV", color='#999', anchor=(0, 1))
            tx.setPos(r * 0.71, r * 0.71)
            p.addItem(tx)
            r += paso
        p.addItem(pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('#ccc')))
        p.addItem(pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('#ccc')))
        # Círculo de ruido (95 %).
        x, y = _circulo(radio_ruido)
        color = tema.OK if st['detected'] else tema.AVISO
        p.plot(x, y, pen=pg.mkPen(color, width=1.5, style=Qt.DashLine))
        # Camino de la punta del vector medio. Los primeros puntos (pocas
        # épocas) caen lejos y emborronan la escala: solo se dibuja lo que
        # cabe en la vista.
        camino = [v for v in camino if abs(v) <= 2.0 * lim]
        if len(camino) > 1:
            p.plot([v.real for v in camino], [v.imag for v in camino],
                   pen=pg.mkPen(COLOR[self.canal[0]] + '66', width=1.2))
        p.addItem(pg.ScatterPlotItem(
            [b.real for b in bloques], [b.imag for b in bloques], size=6,
            brush=pg.mkBrush(120, 120, 120, 140), pen=pg.mkPen(None)))
        p.plot([0, medio.real], [0, medio.imag],
               pen=pg.mkPen(COLOR[self.canal[0]], width=3))
        p.addItem(pg.ScatterPlotItem(
            [medio.real], [medio.imag], size=11, symbol='o',
            brush=pg.mkBrush(COLOR[self.canal[0]]), pen=pg.mkPen('w')))
        p.setXRange(-lim, lim)
        p.setYRange(-lim, lim)
        texto = tr(
            "AssrPanel",
            "{o} {f}: vector {a:.0f} nV a {fi:.0f}° · círculo de ruido "
            "(95 %) {rr:.0f} nV · coherencia de fase {c:.2f} · F {fr:.1f} "
            "(p {pp}) → {e}").format(
                o=self.canal[0], f=_etiqueta_freq(self.canal[1]),
                a=st['amp_nv'], fi=st['phase_deg'], rr=radio_ruido,
                c=st['coherence'], fr=st['f_ratio'],
                pp=f"{st['p']:.3f}" if st['p'] >= 0.001 else "<0.001",
                e=st['estado'])
        if plot is None:
            self.lbl_polar.setText(texto)
        else:
            p.setTitle(texto, size='7pt', color='#333')

    def dibujar_audiograma(self, plot=None):
        p, rec = plot or self.p_audio, self.rec
        if rec is None:
            return
        p.clear()
        p.addItem(pg.InfiniteLine(pos=20, angle=0,
                                  pen=pg.mkPen('#bbb', style=Qt.DashLine)))
        for side, simbolo in (('OD', 'o'), ('OI', 'x')):
            if not rec.has_ear(side):
                continue
            color = COLOR[side]
            xs, bruto, ehl, sin_resp = [], [], [], []
            for i, f in enumerate(assr.CARRIERS):
                canal = (side, f)
                thr = rec.threshold_hl(canal)
                if thr is not None:
                    xs.append(i)
                    bruto.append(thr)
                    ehl.append(rec.threshold_ehl(canal, self.correccion))
                else:
                    # Sin respuesta concluyente al mayor nivel probado.
                    mayor = [h['level'] for h in rec.history[canal]
                             if h['conclusive'] and not h['detected']]
                    st = rec.stats(canal)
                    if st['conclusive'] and not st['detected']:
                        mayor.append(rec.levels[canal])
                    if mayor:
                        sin_resp.append((i, max(mayor)))
            if len(xs) > 1:
                p.plot(xs, ehl, pen=pg.mkPen(color, width=1.5))
            p.addItem(pg.ScatterPlotItem(
                xs, bruto, size=6, symbol='d', brush=pg.mkBrush(None),
                pen=pg.mkPen(color + '99', width=1)))
            p.addItem(pg.ScatterPlotItem(
                xs, ehl, size=13, symbol=simbolo,
                brush=pg.mkBrush(None), pen=pg.mkPen(color, width=2)))
            if sin_resp:
                p.addItem(pg.ScatterPlotItem(
                    [x for x, _ in sin_resp], [y for _, y in sin_resp],
                    size=11, symbol='t1', brush=pg.mkBrush(color),
                    pen=pg.mkPen(color)))
            if self.docente:
                # Lo que el caso realmente tiene: solo lo ve el docente.
                real = [(i, rec.hl[(side, f)])
                        for i, f in enumerate(assr.CARRIERS)
                        if rec.hl[(side, f)] is not None]
                if real:
                    p.plot([x for x, _ in real], [y for _, y in real],
                           pen=pg.mkPen(color + '55', width=1,
                                        style=Qt.DashLine),
                           symbol='s', symbolSize=6,
                           symbolBrush=pg.mkBrush(color + '55'),
                           symbolPen=pg.mkPen(None))
        p.setXRange(-0.5, 3.5)
        p.setYRange(-10, 120)
        p.getAxis('left').setTickSpacing(20, 10)
