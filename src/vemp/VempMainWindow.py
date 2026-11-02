"""
VempMainWindow — el equipo de VEMP dentro de LabSim.

Orquesta las piezas: el panel de control y el medidor de EMG a la izquierda,
las trazas de los dos oídos en el centro, y las lecturas del examen (tabla,
comparación entre oídos, análisis, informe) alrededor.

Cómo corre el examen:

1. El alumno elige subtipo, oído, maniobra, estímulo y registro, y da
   Registrar. Ahí se crea UNA curva con esas condiciones congeladas.
2. Cada tick se generan barridos nuevos: el equipo acepta los que entran en
   banda y tira los otros, y la curva dibujada es el promedio acumulado de
   los aceptados (ver engine.MotorVemp.lote). Por eso pedir 600 barridos
   dura de verdad más que pedir 100 y un paciente que no contrae no limpia
   nunca.
3. Con los dos picos marcados, la curva entra en las cuentas: pico-pico,
   corregida por EMG, asimetría, umbral y sintonía (ver session.Sesion).

Sin caso no se registra nada. Si el paciente en atención no tiene VEMP
cargado, el módulo lo dice y no deja registrar: no hay respuesta sintética
"normal" de relleno.
"""

import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QMainWindow, QProgressBar,
                               QScrollArea, QSplitter, QTabWidget, QVBoxLayout,
                               QWidget)

from backend.client import BackendClient
from core import iconos
from core.base import context
from core.helpers import Preferences
from core.report_autosave import subir_ahora
from vemp import engine, patient, protocol, theme
from vemp.norms import normativa
from vemp.session import Registro, Sesion
from vemp.widgets.analysis import PanelAnalisis
from vemp.widgets.controls import PanelControl
from vemp.widgets.emg import MedidorEmg
from vemp.widgets.kit import Pastilla, Tarjeta, etiqueta
from vemp.widgets.measures import PanelAsimetria, TablaMedidas
from vemp.widgets.report import PanelInforme
from vemp.widgets.traces import PanelTrazas

# Columna de mandos: ancho de cada una, separación, y desde qué ancho de
# ventana se pasa a dos cuando en una no caben a lo alto (en una de 1024 las
# trazas quedarían demasiado angostas: ahí, scroll).
COLUMNA_ANCHO = 262
COLUMNA_SEP = 10
ANCHO_DOS_COLUMNAS = 1180

# Ritmo del reloj de promediación (ms). No es tiempo del paciente: el
# tiempo del paciente lo marca la tasa de estímulo y se muestra aparte.
TICK_MS = 220
# Cuántos ticks dura una promediación completa. Se escala con los barridos
# pedidos --acotado-- para que 600 barridos se sientan mucho más largos que
# 100 sin que 1000 vuelvan el examen ineludible.
TICKS_MIN, TICKS_MAX = 14, 70
# Refresco del medidor de EMG: corre siempre que haya paciente, se esté
# promediando o no. Ahí se ve si el paciente está contrayendo ANTES de
# gastar barridos en descubrirlo.
TICK_EMG_MS = 300
# Ticks seguidos sin un solo barrido aceptado antes de cortar el registro.
TICKS_SIN_AVANCE = 8
# Cuánto más rápido se recupera el músculo descansando de lo que se cansa
# contrayendo.
RECUPERACION = 2.0


class VempMainWindow(QMainWindow):
    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.setWindowTitle('VEMP')

        self.data_current = None
        self.appointment_id = None
        self.caso = None
        self.motor = None
        self.sesion = Sesion()

        self.estado = 'detenido'        # detenido | registrando | pausado
        self.registro_actual = None
        self.barridos_por_tick = 10
        self.ticks_sin_aceptar = 0
        self.segundos_sostenido = 0.0
        self.maniobra_previa = None

        self.timer_captura = QTimer(self)
        self.timer_captura.timeout.connect(self._tick)
        self.timer_emg = QTimer(self)
        self.timer_emg.timeout.connect(self._tick_emg)
        # Timers parados por hideEvent, para reanudarlos en showEvent
        self._emg_pausado = False
        self._captura_pausada = False

        self._construir()
        self._conectar()
        self._sin_caso()

    # =====================================================================
    # UI
    # =====================================================================

    def _construir(self):
        """Los mandos en una columna angosta a todo el alto y, al lado, la
        cabecera (paciente, Registrar, avance) sobre las pestañas.

        El alto es lo que falta en los PC del laboratorio (1280x720 deja
        ~610 px de área): la cabecera a todo el ancho y Registrar abajo de
        los mandos llevaban el mínimo del módulo a ~990 px.
        """
        central = QWidget()
        theme.aplicar_estilo(central)
        self.setCentralWidget(central)

        raiz = QHBoxLayout(central)
        self._raiz = raiz
        raiz.setContentsMargins(10, 8, 10, 10)
        raiz.setSpacing(10)

        self.control = PanelControl(self)
        self.medidor = MedidorEmg()
        self.caja_emg = Tarjeta('Contracción · EMG rectificado')
        self.caja_emg.cuerpo.setSpacing(6)
        self.caja_emg.agregar(self.medidor)

        # Dos columnas de tarjetas; la segunda solo se usa si en una no
        # caben a lo alto (ver _acomodar_mandos).
        mandos = QWidget()
        fila = QHBoxLayout(mandos)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(COLUMNA_SEP)
        self.col_mandos = []
        for _ in range(2):
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(8)
            fila.addLayout(col, 1)
            self.col_mandos.append(col)
        self.dos_columnas = None
        # Con scroll solo por si ni en dos columnas cabe: los mandos no
        # pueden quedar cortados abajo.
        self.izquierda = QScrollArea()
        self.izquierda.setFrameShape(QFrame.Shape.NoFrame)
        self.izquierda.setWidgetResizable(True)
        self.izquierda.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.izquierda.setWidget(mandos)
        self.izquierda.viewport().setAutoFillBackground(False)
        mandos.setAutoFillBackground(False)
        for tarjeta in self._tarjetas_mandos():
            tarjeta.cuerpo.setContentsMargins(12, 8, 12, 10)
        self._acomodar_mandos(False)
        raiz.addWidget(self.izquierda)

        derecha = QVBoxLayout()
        derecha.setSpacing(8)
        derecha.addWidget(self._encabezado())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._pestana_registro(),
                         iconos.icono('onda_abr', theme.TEXTO_TENUE, 16), 'Registro')
        self.analisis = PanelAnalisis()
        self.tabs.addTab(self._envolver(self.analisis),
                         iconos.icono('barras', theme.TEXTO_TENUE, 16), 'Análisis')
        self.informe = PanelInforme()
        self.estado_informe = self.informe.estado
        if self.data_login.get('name'):
            self.informe.set_evaluador(self.data_login['name'])
        self.tabs.addTab(self._envolver(self.informe),
                         iconos.icono('evolucion', theme.TEXTO_TENUE, 16), 'Informe')
        derecha.addWidget(self.tabs, 1)
        raiz.addLayout(derecha, 1)

    def _tarjetas_mandos(self):
        c = self.control
        return (c.caja_prueba, self.caja_emg, c.caja_estimulo, c.caja_registro)

    def _alto_una_columna(self):
        tarjetas = self._tarjetas_mandos()
        return (sum(t.sizeHint().height() for t in tarjetas)
                + self.col_mandos[0].spacing() * (len(tarjetas) - 1))

    def _acomodar_mandos(self, dos):
        """Una columna angosta si los mandos caben a lo alto; si no, dos
        (Prueba y EMG | Estímulo y Registro). En los PC del laboratorio sobra
        ancho y falta alto: a 1280x720 la columna sola quedaba con scroll y
        el EMG --lo que hay que mirar mientras se registra-- fuera de vista."""
        if dos == self.dos_columnas:
            return
        self.dos_columnas = dos
        prueba, emg, estimulo, registro = self._tarjetas_mandos()
        for col in self.col_mandos:
            while col.count():
                col.takeAt(0)
        izq, der = self.col_mandos
        orden = ((izq, (prueba, emg)), (der, (estimulo, registro))) if dos else \
            ((izq, (prueba, estimulo, registro, emg)),)
        for col, tarjetas in orden:
            for tarjeta in tarjetas:
                col.addWidget(tarjeta)
            col.addStretch(1)
        ancho = COLUMNA_ANCHO * (2 if dos else 1) + (COLUMNA_SEP if dos else 0)
        self.izquierda.setFixedWidth(ancho)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        # El alto disponible no depende de cuántas columnas haya: no oscila.
        # Se mide de la ventana y no del scroll, que en el primer resize
        # todavía no tiene su alto.
        margenes = self._raiz.contentsMargins()
        alto = self.height() - margenes.top() - margenes.bottom()
        self._acomodar_mandos(self._alto_una_columna() > alto
                              and self.width() >= ANCHO_DOS_COLUMNAS)

    @staticmethod
    def _envolver(widget):
        """Las pestañas traen su propio margen: el panel no toca el borde."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(widget)
        return contenedor

    def _encabezado(self):
        """Paciente y condición a la izquierda, Registrar/Detener a la
        derecha; debajo el avance y qué está pasando.

        Sin píldora de estado: Registrar ya lo dice (Pausar en rojo mientras
        promedia, Continuar en pausa)."""
        caja = Tarjeta()
        caja.cuerpo.setContentsMargins(14, 8, 10, 8)
        caja.cuerpo.setSpacing(5)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.lbl_paciente = etiqueta('Sin atención abierta', rol='titulo')
        fila.addWidget(self.lbl_paciente)
        self.pill_subtipo = Pastilla('cVEMP', 'acento')
        fila.addWidget(self.pill_subtipo)
        self.pill_lado = Pastilla('OD', 'od')
        fila.addWidget(self.pill_lado)
        fila.addStretch(1)
        fila.addWidget(self.control.btn_registrar)
        fila.addWidget(self.control.btn_detener)
        caja.agregar_layout(fila)

        self.barra = QProgressBar()
        self.barra.setObjectName('barraRegistro')
        self.barra.setTextVisible(False)
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        caja.agregar(self.barra)

        # La condición va con el mensaje y no en la fila del título: ahí,
        # con Registrar y Detener, el encabezado no cabía en 1024 px.
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.pill_condicion = Pastilla('', 'neutro')
        fila.addWidget(self.pill_condicion, 0, Qt.AlignmentFlag.AlignTop)
        self.lbl_estado = etiqueta('', rol='hint')
        self.lbl_estado.setWordWrap(True)
        fila.addWidget(self.lbl_estado, 1)
        caja.agregar_layout(fila)
        return caja

    def _pestana_registro(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        trazas = QHBoxLayout()
        trazas.setSpacing(10)
        self.trazas = {}
        for lado in protocol.LADOS:
            caja = Tarjeta()
            caja.cuerpo.setContentsMargins(10, 8, 10, 10)
            panel = PanelTrazas(lado)
            caja.agregar(panel, 1)
            self.trazas[lado] = panel
            trazas.addWidget(caja, 1)

        abajo = QSplitter(Qt.Orientation.Horizontal)
        caja_tabla = Tarjeta('Medidas')
        self.tabla = TablaMedidas()
        caja_tabla.agregar(self.tabla, 1)
        abajo.addWidget(caja_tabla)
        self.asimetria = PanelAsimetria()
        abajo.addWidget(self.asimetria)
        # La tabla se lleva el ancho; la comparación no lo necesita.
        self.asimetria.setMaximumWidth(300)
        abajo.setStretchFactor(0, 1)
        abajo.setStretchFactor(1, 0)
        abajo.setMinimumHeight(150)

        arriba = QWidget()
        arriba.setLayout(trazas)
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(arriba)
        vertical.addWidget(abajo)
        vertical.setStretchFactor(0, 4)
        vertical.setStretchFactor(1, 1)
        vertical.setChildrenCollapsible(False)
        layout.addWidget(vertical)
        return contenedor

    def _conectar(self):
        self.control.sig_registrar.connect(self.iniciar)
        self.control.sig_pausar.connect(self.pausar)
        self.control.sig_detener.connect(self.detener)
        self.control.sig_subtipo.connect(self._cambiar_subtipo)
        self.control.sig_lado.connect(self._cambiar_lado)
        self.control.sig_maniobra.connect(self._cambiar_maniobra)
        self.control.sig_condicion.connect(self._refrescar_encabezado)

        for panel in self.trazas.values():
            panel.sig_marca.connect(self._marcar)
            panel.sig_desmarca.connect(self._desmarcar)
            panel.sig_seleccion.connect(self._seleccionar)
            panel.sig_borrar.connect(self._borrar_curva)
        self.tabla.sig_seleccion.connect(self._seleccionar_desde_tabla)
        self.analisis.sig_condicion.connect(self._refrescar_analisis)
        self.tabs.currentChanged.connect(self._cambiar_pestana)

    # =====================================================================
    # Ciclo de vida (API que llama main.py)
    # =====================================================================

    def la_super(self, data, appointment_id=None):
        """Entra (o sale) el paciente en atención."""
        self.detener()
        self.data_current = data
        self.appointment_id = appointment_id
        self.caso = patient.desde_caso(data) if data else None
        self.motor = engine.MotorVemp(self.caso) if self.caso else None
        self.sesion.limpiar()
        self._limpiar_vistas()

        if self.caso is None:
            self._sin_caso(con_paciente=data is not None)
            return

        self.control.habilitar(True)
        if self.isVisible():
            self.timer_emg.start(TICK_EMG_MS)
        else:
            self._emg_pausado = True  # arranca al mostrarse (showEvent)
        self.medidor.set_activo(True)
        descripcion = f'Paciente · {self.caso.descripcion}'
        self.lbl_paciente.setText(descripcion)
        self.informe.set_paciente(descripcion)
        self._cambiar_subtipo(self.control.subtipo())
        self._cambiar_maniobra(self.control.maniobra())
        self._mensaje('')

    def _sin_caso(self, con_paciente=False):
        self.control.habilitar(False)
        self.timer_emg.stop()
        self.medidor.set_activo(False)
        self.lbl_paciente.setText('Sin atención abierta')
        self.informe.set_paciente('')
        if con_paciente:
            self._mensaje('Este paciente no tiene VEMP cargado en el caso: '
                          'el equipo no registra. Cargalo en la ficha VEMP del '
                          'editor de casos.', 'alerta')
        else:
            self._mensaje('Abrí una atención para registrar.')

    def _limpiar_vistas(self):
        for panel in self.trazas.values():
            panel.limpiar()
        self.tabla.poblar([])
        self.asimetria.set_resumen(self.control.subtipo(), None, None, None)
        self.informe.limpiar()
        self.barra.setValue(0)

    # =====================================================================
    # Captura
    # =====================================================================

    def iniciar(self):
        if self.caso is None or self.motor is None:
            return
        ajustes = self.control.ajustes()
        oido = self.caso.oido(ajustes.lado)
        if oido is None:
            self._mensaje(f'{ajustes.lado}: este oído no tiene VEMP cargado '
                          'en el caso.', 'alerta')
            return

        if self.estado == 'pausado' and self.registro_actual is not None:
            self.estado = 'registrando'
            self.control.set_registrando(True)
            self.timer_captura.start(TICK_MS)
            self._refrescar_encabezado()
            return

        x = self.motor.eje(ajustes.subtipo)
        self.registro_actual = self.sesion.nuevo(ajustes, x)
        self.barridos_por_tick = self._barridos_por_tick(ajustes.promedios)
        self.ticks_sin_aceptar = 0
        self.estado = 'registrando'
        self.control.set_registrando(True)
        self.trazas[ajustes.lado].agregar(self.registro_actual)
        self.analisis.sincronizar(ajustes.transductor, ajustes.freq)
        self.timer_captura.start(TICK_MS)
        self._refrescar_encabezado()

    @staticmethod
    def _barridos_por_tick(promedios):
        ticks = min(max(promedios / 12.0, TICKS_MIN), TICKS_MAX)
        return max(int(round(promedios / ticks)), 1)

    def pausar(self):
        if self.estado != 'registrando':
            return
        self.estado = 'pausado'
        self.timer_captura.stop()
        self.control.set_registrando(False, pausado=True)
        self._refrescar_encabezado()

    def detener(self):
        self.timer_captura.stop()
        if self.registro_actual is not None:
            self.registro_actual.terminado = True
        self.registro_actual = None
        self.estado = 'detenido'
        self.control.set_registrando(False)
        self._refrescar_encabezado()

    def _tick(self):
        try:
            self._tick_registro()
        except Exception as exc:
            # Sin esto el timer seguía reventando y el equipo quedaba en
            # 'registrando' para siempre
            print(f'VEMP: falló el registro: {exc!r}')
            self.detener()
            self._mensaje('Registro detenido: el equipo no pudo seguir '
                          'promediando con los datos de este caso.', 'alerta')

    def _tick_registro(self):
        registro = self.registro_actual
        if registro is None:
            self.detener()
            return

        ajustes = registro.ajustes
        # La maniobra se relee en cada tick aunque el resto del registro esté
        # congelado: el paciente se afloja EN PLENA promediación y ver la
        # respuesta caerse con él es parte de lo que hay que aprender.
        ajustes.maniobra = self.control.maniobra()
        emg = self.motor.emg_instantaneo(ajustes.subtipo, ajustes.maniobra,
                                         self.segundos_sostenido)
        self.medidor.push(emg)

        faltan = max(ajustes.promedios - registro.aceptados, 0)
        pedidos = min(self.barridos_por_tick, faltan) if faltan else 0
        if pedidos <= 0:
            self._terminar_registro(registro)
            return

        lote = self.motor.lote(ajustes, emg, pedidos)
        registro.acumular(lote)
        # Tiempo del paciente: los barridos presentados, a la tasa elegida.
        # Se cuentan los presentados y no los aceptados: el estímulo sonó y
        # el paciente estuvo contrayendo igual.
        self.segundos_sostenido += engine.duracion_segundos(pedidos, ajustes.tasa)

        # Registro que no avanza: el equipo está tirando todo lo que entra.
        # Se corta en vez de dejarlo girando para siempre.
        self.ticks_sin_aceptar = 0 if lote.aceptados else self.ticks_sin_aceptar + 1
        if self.ticks_sin_aceptar >= TICKS_SIN_AVANCE:
            self._abortar_registro(registro)
            return

        self.trazas[registro.lado].refrescar(registro.nombre)
        self._refrescar_tabla()
        self._refrescar_encabezado()

        if registro.aceptados >= ajustes.promedios:
            self._terminar_registro(registro)

    def _abortar_registro(self, registro):
        estado = protocol.estado_emg(registro.subtipo, self.medidor.nivel)
        self.detener()
        self.trazas[registro.lado].seleccionar(registro.nombre)
        self._refrescar_tabla()
        musculo, _via = protocol.MUSCULO[registro.subtipo]
        self._mensaje(
            f'Registro detenido: el equipo rechazó todos los barridos '
            f'(contracción {estado}). El {musculo} tiene que estar en la banda '
            f'del medidor para que un barrido entre al promedio.', 'alerta')

    def _terminar_registro(self, registro):
        registro.terminado = True
        self.registro_actual = None
        self.estado = 'detenido'
        self.timer_captura.stop()
        self.control.set_registrando(False)
        self.trazas[registro.lado].seleccionar(registro.nombre)
        self._refrescar_tabla()
        self._refrescar_encabezado()
        if registro.aceptados == 0:
            self._mensaje('Ningún barrido entró al promedio: el equipo los '
                          'rechazó todos. Mirá el EMG.', 'alerta')

    # =====================================================================
    # EMG
    # =====================================================================

    def _tick_emg(self):
        if self.caso is None or self.motor is None:
            return
        subtipo = self.control.subtipo()
        maniobra = self.control.maniobra()
        if self.estado != 'registrando':
            # Entre registro y registro el paciente descansa, y el músculo
            # se recupera más rápido de lo que se cansó. Sin esto, un examen
            # largo terminaba midiendo un paciente cada vez más flojo aunque
            # el alumno le diera tiempo entre curva y curva.
            self.segundos_sostenido = max(
                0.0, self.segundos_sostenido - (TICK_EMG_MS / 1000.0) * RECUPERACION)
            emg = self.motor.emg_instantaneo(subtipo, maniobra,
                                             self.segundos_sostenido)
            self.medidor.push(emg)

    def _cambiar_maniobra(self, maniobra):
        """Cambiar de maniobra descansa el músculo: el reloj de fatiga
        arranca de nuevo."""
        if maniobra != self.maniobra_previa:
            self.segundos_sostenido = 0.0
            self.maniobra_previa = maniobra
        subtipo = self.control.subtipo()
        if self.motor is not None:
            self.medidor.push(self.motor.emg_instantaneo(subtipo, maniobra,
                                                         self.segundos_sostenido))

    # =====================================================================
    # Subtipo / lado / selección
    # =====================================================================

    def _cambiar_subtipo(self, subtipo):
        base = self._baseline(subtipo)
        for panel in self.trazas.values():
            panel.set_subtipo(subtipo)
            panel.set_normativa(base)
        self.medidor.set_subtipo(subtipo)
        self.tabla.set_subtipo(subtipo)
        self.analisis.set_subtipo(subtipo, base)
        self._cambiar_maniobra(self.control.maniobra())
        self._refrescar_tabla()
        self._refrescar_encabezado()

    def _baseline(self, subtipo):
        if self.caso is None:
            return {}
        try:
            return normativa().baseline(self.caso.poblacion, subtipo,
                                        self.control.cb_freq.currentText())
        except Exception as exc:                       # normativa incompleta
            print(f'VEMP: sin normativa para {subtipo} ({exc})')
            return {}

    def _cambiar_lado(self, lado):
        self._refrescar_encabezado()

    def _seleccionar(self, nombre):
        self._refrescar_tabla(activa=nombre)

    def _seleccionar_desde_tabla(self, nombre):
        registro = self.sesion.get(nombre)
        if registro is None:
            return
        panel = self.trazas[registro.lado]
        if panel.activa != nombre:
            panel.seleccionar(nombre)

    # =====================================================================
    # Marcas
    # =====================================================================

    def _marcar(self, nombre, pico, lat, amp):
        registro = self.sesion.get(nombre)
        if registro is None:
            return
        registro.marcar(pico, lat, amp)
        self.trazas[registro.lado].dibujar_marca(nombre, pico, lat, amp)
        self._refrescar_tabla(activa=nombre)
        self._refrescar_analisis()

    def _desmarcar(self, nombre, pico):
        registro = self.sesion.get(nombre)
        if registro is None:
            return
        registro.desmarcar(pico)
        self.trazas[registro.lado]._quitar_marca_items(nombre, pico)
        self._refrescar_tabla(activa=nombre)
        self._refrescar_analisis()

    def _borrar_curva(self, nombre):
        registro = self.sesion.get(nombre)
        if registro is None:
            return
        if self.registro_actual is registro:
            self.detener()
        self.sesion.borrar(nombre)
        self.trazas[registro.lado].borrar(nombre)
        self._refrescar_tabla()
        self._refrescar_analisis()

    # =====================================================================
    # Refrescos
    # =====================================================================

    def _refrescar_tabla(self, activa=None):
        registros = list(self.sesion.registros.values())
        if activa is None:
            for panel in self.trazas.values():
                if panel.activa:
                    activa = panel.activa
        self.tabla.poblar(registros, activa)
        subtipo = self.control.subtipo()
        ajustes = self.control.ajustes()
        od, oi, ratio = self.sesion.asimetria(subtipo, ajustes.transductor,
                                              ajustes.freq)
        self.asimetria.set_resumen(subtipo, od, oi, ratio)

    def _refrescar_analisis(self, sincronizar=False):
        ajustes = self.control.ajustes()
        if sincronizar:
            # Una curva nueva mueve la condición que se está revisando; una
            # vez ahí, el alumno la cambia a mano sin tocar el equipo.
            self.analisis.sincronizar(ajustes.transductor, ajustes.freq)
        self.analisis.set_subtipo(ajustes.subtipo, self._baseline(ajustes.subtipo))
        self.analisis.actualizar(self.sesion)
        transductor, freq = self.analisis.condicion()
        self.informe.actualizar(self.sesion, ajustes.subtipo, transductor, freq)

    def _cambiar_pestana(self, indice):
        if indice in (1, 2):
            self._refrescar_analisis()

    def _refrescar_encabezado(self):
        ajustes = self.control.ajustes()
        self.pill_subtipo.set(protocol.SUBTIPO_CORTO[ajustes.subtipo], 'acento')
        self.pill_lado.set(ajustes.lado, 'od' if ajustes.lado == 'OD' else 'oi')
        unidad = 'SPL' if ajustes.transductor == protocol.AEREO else 'FL'
        via = 'aéreo' if ajustes.transductor == protocol.AEREO else 'óseo'
        self.pill_condicion.set(f'{ajustes.intensidad} dB {unidad} · '
                                f'{ajustes.freq} · {via}')

        registro = self.registro_actual
        if registro is None:
            self.barra.setValue(0)
            if self.caso is not None and self.estado == 'detenido':
                self._mensaje(self._mensaje_listo(ajustes))
            return

        pedidos = max(registro.ajustes.promedios, 1)
        self.barra.setValue(int(100 * min(registro.aceptados / pedidos, 1.0)))
        segundos = engine.duracion_segundos(registro.aceptados,
                                            registro.ajustes.tasa)
        partes = [f'{registro.nombre}',
                  f'{registro.aceptados}/{pedidos} barridos',
                  f'{registro.rechazados} rechazados',
                  f'{int(segundos // 60)}:{int(segundos % 60):02d} de registro',
                  f'EMG {registro.emg_medio:.0f} µV']
        if self.estado == 'pausado':
            partes.insert(0, 'En pausa')
        estado_emg = protocol.estado_emg(registro.subtipo, self.medidor.nivel)
        nivel = 'alerta' if estado_emg != 'ok' else None
        if estado_emg != 'ok':
            partes.append(f'contracción {estado_emg}: el equipo está rechazando barridos')
        self._mensaje('   ·   '.join(partes), nivel)

    def _mensaje_listo(self, ajustes):
        """Qué va a pasar si aprieta Registrar ahora."""
        segundos = engine.duracion_segundos(ajustes.promedios, ajustes.tasa)
        return (f'Listo para registrar {protocol.SUBTIPO_CORTO[ajustes.subtipo]} '
                f'{ajustes.lado}: {ajustes.promedios} barridos a {ajustes.tasa:.1f}/s '
                f'({int(segundos // 60)}:{int(segundos % 60):02d}) · '
                f'{protocol.descripcion_montaje(ajustes.subtipo, ajustes.lado)}')

    def _mensaje(self, texto, estado=None):
        self.lbl_estado.setText(texto)
        self.lbl_estado.setProperty('estado', estado or '')
        theme.repintar(self.lbl_estado)

    # =====================================================================
    # Informe
    # =====================================================================

    def submit_report(self):
        """Sube el informe al cerrar la atención.

        Best-effort, igual que el ABR: sin conexión no puede romper el
        cierre de la atención.
        """
        job = self.report_job()
        if job is None:
            return True
        cliente = BackendClient(
            Preferences().get('BACKEND_URL'),
            context.get_resource('json/session.json'),
        )
        ok, error = subir_ahora(job, cliente)
        if not ok:
            print(f'VEMP: no se pudo subir el informe: {error}')
        return ok

    def report_job(self):
        """El informe tal como se sube (ver core/report_autosave.py), o None."""
        if not self.data_login or not self.sesion.registros:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        ajustes = self.control.ajustes()
        resumen = self.sesion.resumen(ajustes.subtipo, ajustes.transductor,
                                      ajustes.freq)
        data = {
            'curvas': self.sesion.curvas_dict(),
            'subtipo': ajustes.subtipo,
            'waves': list(protocol.PEAKS[ajustes.subtipo]),
            'asimetria': resumen,
            'umbral_informado': self.informe.umbrales(),
            'hallazgos': self.informe.hallazgos(),
            'conclusion': self.informe.conclusion(),
        }
        return {"appointment_id": appointment_id, "tipo": 'VEMP', "data": data,
                "images": self._exportar_imagenes}

    def restore_report(self, data):
        """Retomar la atención: vuelven las curvas y el informe que ya se
        habían guardado (ver core/report_autosave.py). Solo si todavía no
        se registró nada en esta vuelta."""
        if self.caso is None or self.sesion.registros:
            return False
        for nombre, curva in (data.get('curvas') or {}).items():
            registro = Registro.desde_dict(nombre, curva)
            if registro is None:
                continue
            self.sesion.registros[nombre] = registro
            panel = self.trazas.get(registro.lado)
            if panel is None:
                continue
            panel.agregar(registro)
            for pico, (lat, amp) in registro.marcas.items():
                panel.dibujar_marca(nombre, pico, lat, amp)
        for lado, db in (data.get('umbral_informado') or {}).items():
            spin = self.informe.spins_umbral.get(lado)
            if spin is not None and db:
                spin.setValue(int(db))
        self.informe.txt_hallazgos.setPlainText(data.get('hallazgos') or '')
        self.informe.txt_conclusion.setPlainText(data.get('conclusion') or '')
        self._refrescar_tabla()
        self._refrescar_analisis()
        return bool(self.sesion.registros)

    def _exportar_imagenes(self):
        temp = context.get_resource('local_cache/vemp/temp')
        os.makedirs(temp, exist_ok=True)
        imagenes = {}
        exportables = [('0', self.trazas['OD']), ('1', self.trazas['OI']),
                       ('lat_int', self.analisis)]
        for sufijo, widget in exportables:
            path = os.path.join(temp, f'upload_{sufijo}.jpg')
            try:
                widget.exportar(path)
            except Exception as exc:
                print(f'VEMP: no se pudo exportar {sufijo}: {exc}')
                continue
            imagenes[sufijo] = path
        return imagenes

    def hideEvent(self, evento):
        # Ventana escondida: ni el EMG de fondo ni la captura siguen
        # corriendo. El registro queda donde iba y sigue al volver.
        self._emg_pausado = self._emg_pausado or self.timer_emg.isActive()
        self._captura_pausada = self._captura_pausada or self.timer_captura.isActive()
        self.timer_emg.stop()
        self.timer_captura.stop()
        super().hideEvent(evento)

    def showEvent(self, evento):
        super().showEvent(evento)
        if self._emg_pausado and self.caso is not None:
            self.timer_emg.start(TICK_EMG_MS)
        if self._captura_pausada and self.estado == 'registrando':
            self.timer_captura.start(TICK_MS)
        self._emg_pausado = False
        self._captura_pausada = False

    def closeEvent(self, evento):
        self.timer_captura.stop()
        self.timer_emg.stop()
        evento.accept()
