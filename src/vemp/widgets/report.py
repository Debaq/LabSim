"""
Informe del VEMP.

Arriba, lo que el examen midió, en números y sin lectura: las amplitudes
corregidas de cada oído, la asimetría con su cuenta, hasta qué intensidad
hubo respuesta marcada y en qué frecuencia respondió mejor cada oído. Qué
significa eso lo escribe quien informa.

El UMBRAL se declara acá y no se deduce solo: la serie muestra hasta dónde
hubo respuesta marcada, pero decir "el umbral es 80" es una lectura, y el
que la hace es el alumno. Queda en el informe como lo que él decidió.
"""

from datetime import datetime

from PySide6.QtWidgets import (QHBoxLayout, QScrollArea, QSpinBox, QTextEdit,
                               QVBoxLayout, QWidget)

from core.estado_informe import EstadoInforme
from vemp import protocol
from vemp.widgets.kit import Campos, Dato, Tarjeta, etiqueta, etiqueta_seccion


class PanelInforme(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.evaluador = ''
        self.subtipo = protocol.CVEMP

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        raiz.addWidget(scroll)

        contenido = QWidget()
        self.cuerpo = QVBoxLayout(contenido)
        self.cuerpo.setContentsMargins(4, 4, 4, 4)
        self.cuerpo.setSpacing(10)
        scroll.setWidget(contenido)
        # Sin esto el scroll pinta el gris del sistema detrás de las tarjetas.
        scroll.viewport().setAutoFillBackground(False)
        contenido.setAutoFillBackground(False)

        # Alto antes que ancho: lo medido y el umbral lado a lado, y hallazgos
        # y conclusión en dos columnas que se llevan el alto que sobra. Uno
        # bajo el otro, a 1366x768 la conclusión quedaba fuera de vista.
        self.cuerpo.addWidget(self._caja_encabezado())
        fila = QHBoxLayout()
        fila.setSpacing(10)
        fila.addWidget(self._caja_medidas(), 1)
        fila.addWidget(self._caja_umbrales())
        self.cuerpo.addLayout(fila)
        self.cuerpo.addWidget(self._caja_texto(), 1)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _caja_encabezado(self):
        """Fecha y evaluador en una línea, sin tarjeta ni nombre del
        paciente: el alumno sabe a quién atiende y el alto es para escribir."""
        caja = QWidget()
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(4, 0, 4, 0)
        fila.setSpacing(10)
        fila.addWidget(etiqueta_seccion('Informe VEMP'))
        fila.addStretch(1)
        self.lbl_datos = etiqueta('', rol='hint')
        fila.addWidget(self.lbl_datos)
        self._refrescar_encabezado()
        return caja

    def _caja_medidas(self):
        caja = Tarjeta('Lo que midió el examen · amplitud corregida')
        fila = QHBoxLayout()
        fila.setSpacing(16)
        self.dato_od = Dato('OD')
        self.dato_oi = Dato('OI')
        self.dato_ar = Dato('Asimetría', unidad='%')
        self.dato_barridos = Dato('Curvas')
        for dato in (self.dato_od, self.dato_oi, self.dato_ar, self.dato_barridos):
            fila.addWidget(dato)
        fila.addStretch(1)
        caja.agregar_layout(fila)

        self.lbl_detalle = etiqueta('', rol='hint')
        self.lbl_detalle.setWordWrap(True)
        caja.agregar(self.lbl_detalle)
        return caja

    def _caja_umbrales(self):
        caja = Tarjeta('Umbral informado')
        campos = Campos()
        self.spins_umbral = {}
        for lado in protocol.LADOS:
            spin = QSpinBox()
            spin.setRange(0, 130)
            spin.setSingleStep(protocol.PASO_INTENSIDAD)
            spin.setSuffix(' dB')
            # 0 es "no informado": el mínimo con texto propio evita tener
            # que agregar una casilla al lado de cada spin.
            spin.setSpecialValueText('no informado')
            spin.setValue(0)
            spin.setMinimumWidth(120)
            campos.agregar(f'Umbral {lado}', spin)
            self.spins_umbral[lado] = spin
        caja.agregar(campos)
        ayuda = etiqueta(
            'La serie muestra hasta qué intensidad hubo respuesta marcada; el '
            'umbral que se informa lo decide quien informa.', rol='hint')
        ayuda.setWordWrap(True)
        caja.agregar(ayuda)
        caja.cuerpo.addStretch(1)
        caja.setFixedWidth(240)
        return caja

    def _caja_texto(self):
        caja = Tarjeta()
        columnas = QHBoxLayout()
        columnas.setSpacing(12)
        self.txt_hallazgos = QTextEdit()
        self.txt_hallazgos.setPlaceholderText(
            'Morfología, latencias, amplitudes, condiciones del registro...')
        self.txt_conclusion = QTextEdit()
        self.txt_conclusion.setPlaceholderText('Interpretación del examen...')
        for titulo, texto in (('Hallazgos', self.txt_hallazgos),
                              ('Conclusión', self.txt_conclusion)):
            texto.setMinimumHeight(110)
            columna = QVBoxLayout()
            columna.setSpacing(6)
            columna.addWidget(etiqueta_seccion(titulo))
            columna.addWidget(texto, 1)
            columnas.addLayout(columna, 1)
        caja.cuerpo.addLayout(columnas, 1)
        # Se guarda solo (core/report_autosave.py); acá se ve si quedó.
        self.estado = EstadoInforme()
        caja.agregar(self.estado)
        return caja

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def set_evaluador(self, nombre):
        self.evaluador = nombre or ''
        self._refrescar_encabezado()

    def _refrescar_encabezado(self):
        fecha = datetime.now().strftime('%d/%m/%Y')
        partes = [f'Fecha: {fecha}']
        if self.evaluador:
            partes.append(f'Evaluador: {self.evaluador}')
        self.lbl_datos.setText('   ·   '.join(partes))

    def limpiar(self):
        self.txt_hallazgos.clear()
        self.txt_conclusion.clear()
        for spin in self.spins_umbral.values():
            spin.setValue(0)

    def actualizar(self, sesion, subtipo, transductor=None, freq=None):
        self.subtipo = subtipo
        od, oi, ratio = sesion.asimetria(subtipo, transductor, freq)
        corr_od = od.p2p_corregida() if od else None
        corr_oi = oi.p2p_corregida() if oi else None

        self.dato_od.set_valor('—' if corr_od is None else f'{corr_od:.2f}')
        self.dato_oi.set_valor('—' if corr_oi is None else f'{corr_oi:.2f}')
        self.dato_ar.set_valor('—' if ratio is None else f'{ratio:.0f}')
        medidas = [r for r in sesion.registros.values() if r.completo()]
        self.dato_barridos.set_valor(f'{len(medidas)}/{len(sesion.registros)}')

        partes = []
        for lado in protocol.LADOS:
            umbral = sesion.umbral_medido(lado, subtipo, transductor, freq)
            if umbral is not None:
                partes.append(f'{lado}: respuesta marcada hasta {umbral} dB')
            sintonia = {f: v for f, v in sesion.sintonia(lado, subtipo, transductor).items()
                        if v is not None}
            if len(sintonia) > 1:
                mejor = max(sintonia, key=sintonia.get)
                partes.append(f'{lado}: mayor amplitud en {mejor}')
        if ratio is not None:
            partes.append(f'asimetría |{corr_od:.2f} − {corr_oi:.2f}| / '
                          f'({corr_od:.2f} + {corr_oi:.2f})')
        self.lbl_detalle.setText(
            '   ·   '.join(partes) if partes else
            'Todavía no hay curvas con los dos picos marcados.')

    def umbrales(self):
        """{lado: dB} con lo que el alumno declaró (0 = no informado)."""
        return {lado: (spin.value() or None)
                for lado, spin in self.spins_umbral.items()}

    def hallazgos(self):
        return self.txt_hallazgos.toPlainText()

    def conclusion(self):
        return self.txt_conclusion.toPlainText()
