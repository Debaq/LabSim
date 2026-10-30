"""Los equipos de la nariz dentro de LabSim: rinomanometría anterior (H26) y
rinometría acústica (H27).

Las dos ventanas miden la misma nariz (nasal/sesion.py): el vasoconstrictor
que se pone en una vale para la otra, y el ciclo nasal corre con el reloj.
El modelo es el de RinoSim portado (nasal/modelo.py, rinomanometria.py,
rinometria.py): la misma nariz da las mismas curvas que las figuras del
libro.

Demo interna (docs/roadmap_nasal.md): solo el admin abre estos equipos. Los
errores de técnica se ponen a mano ("Simular"), como en RinoSim: el alumno
todavía no los comete con sus manos.

El informe (RINOMANOMETRIA / RINOMETRIA) se sube solo como los demás (ver
core/report_autosave.py). Guarda la tabla tal como se vio, para el PDF, y
CÓMO se tomó cada medición (lado, estado, opciones, semilla): al retomar la
atención se vuelven a calcular con el modelo y salen idénticas, en vez de
guardar miles de puntos de cada curva.

Sin `cases.data['NASAL']` el equipo no mide.
"""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFrame, QHBoxLayout,
                               QHeaderView, QMainWindow, QPlainTextEdit, QPushButton, QScrollArea,
                               QSpinBox,
                               QSplitter, QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

import os
import random
import time

from core import hilos, tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import modelo, sesion
from nasal import rinomanometria as RM
from nasal import rinometria as RA
from nasal.azar import generador
from nasal.graficos import (GraficoResistencia, GraficoRinometria, GraficoRinomanometria,
                            GraficoTiempo, curva_media)
from nasal.paciente_rm import PacienteRM
from nasal.referencias import (COREY_1997, HILBERG_1989, PROTOCOLO_REPETICION,
                               REFERENCIA_UNILATERAL_150, REN_2018, RINOMETRIA_SIN_NORMA,
                               VOGT_2016)
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta

SIGLA = modelo.SIGLA_LADO
LADOS = modelo.LADOS
NARINA = {'D': 'derecha', 'I': 'izquierda'}


def otro_lado(lado):
    return 'I' if lado == 'D' else 'D'
PERMISOS_DOCENTE = (555, 777)

QSS_NASAL = f"""
QPushButton#btnPrincipal {{
    background: {tema.ACENTO};
    border: 1px solid {tema.ACENTO};
    color: #FFFFFF;
    font-weight: 600;
    padding: 7px 12px;
}}
QPushButton#btnPrincipal:hover {{ background: {tema.ACENTO_CLARO}; color: #FFFFFF; }}
QPushButton#btnPrincipal:disabled {{ background: {tema.TRAZO_INACTIVO}; border-color: {tema.TRAZO_INACTIVO}; }}
"""


def num(v, d=2):
    """Coma decimal y raya si no hay dato, como RinoSim."""
    if v is None or v != v or v in (float('inf'), float('-inf')):
        return '—'
    return f'{v:.{d}f}'.replace('.', ',')


def pct_o_raya(v):
    return '—' if v is None else f'{num(v, 1)} %'


def pct(v):
    if v is None or v != v:
        return '—'
    return f'{"+" if v > 0 else ""}{v * 100:.0f} %'


def _vacio():
    return {'reposo': {'D': None, 'I': None}, 'vc': {'D': None, 'I': None}}


class Tabla(QTableWidget):
    """Tabla de solo lectura con filas de color por fosa."""

    def __init__(self):
        super().__init__(0, 0)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.setWordWrap(False)

    def poblar(self, cabeceras, filas):
        """filas: [(celdas, lado o None, {columna: 'fuera'|'ok'})]."""
        # Lo que se ve, en texto: es lo que va al PDF del informe.
        self.contenido = {'cabeceras': list(cabeceras), 'filas': [list(c) for c, _, _ in filas]}
        self.clear()
        self.setColumnCount(len(cabeceras))
        self.setHorizontalHeaderLabels(cabeceras)
        self.setRowCount(len(filas))
        for i, (celdas, lado, marcas) in enumerate(filas):
            for j, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if j else
                                      Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if j == 0 and lado:
                    item.setForeground(QColor(tema.OD if lado == 'D' else tema.OI))
                marca = (marcas or {}).get(j)
                if marca == 'fuera':
                    item.setForeground(QColor(tema.ALERTA))
                elif marca == 'ok':
                    item.setForeground(QColor(tema.OK))
                self.setItem(i, j, item)
        tema.ajustar_alto(self)


class EquipoNasal(QMainWindow):
    """Lo común a los dos equipos: el paciente, el encabezado, el panel de la
    izquierda y los mensajes. Cada equipo pone sus botones y su pantalla."""

    TITULO = ''
    EQUIPO = ''      # prefijo de la semilla de cada medición
    PILL_VC = True   # el estado del vasoconstrictor junto a los mensajes

    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self.setWindowTitle(self.TITULO)
        self.sesion = None
        self.res = _vacio()
        self._construir()
        self._sin_caso()
        # El encabezado cuenta el tiempo de acción del vasoconstrictor.
        self.timer_segundo = QTimer(self)
        self.timer_segundo.setInterval(1000)
        self.timer_segundo.timeout.connect(self._cada_segundo)
        self.timer_segundo.start()

    # --- UI -----------------------------------------------------------------

    def _construir(self):
        central = QWidget()
        tema.aplicar_estilo(central, QSS_NASAL)
        self.setCentralWidget(central)
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(10)
        raiz.addWidget(self._encabezado())

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)
        raiz.addLayout(cuerpo, 1)

        izquierda = QWidget()
        izq = QVBoxLayout(izquierda)
        izq.setContentsMargins(0, 0, 0, 0)
        izq.setSpacing(10)
        self._paneles_izquierda(izq)
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
        if self.es_docente:
            self.verdad = etiqueta('', rol='hint')
            self.verdad.setWordWrap(True)
            self.verdad.setTextFormat(Qt.TextFormat.RichText)
            self.verdad.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            caja = QScrollArea()
            caja.setWidgetResizable(True)
            caja.setWidget(self.verdad)
            self.tabs.addTab(caja, 'Lo que el equipo no sabe')
        else:
            self.verdad = None
        cuerpo.addWidget(self.tabs, 1)

    def _paneles_izquierda(self, izq):
        self.panel_examen = Tarjeta('Examen')
        izq.addWidget(self.panel_examen)
        self._botones(self.panel_examen)
        self._paneles_comunes(izq)

    def _paneles_comunes(self, izq):
        self.panel_errores = Tarjeta('Simular error de técnica')
        izq.addWidget(self.panel_errores)
        self._errores(self.panel_errores)
        self.panel_vista = Tarjeta('Pantalla')
        izq.addWidget(self.panel_vista)
        self._opciones(self.panel_vista)

    def _paneles(self):
        """Lo que se apaga sin paciente con nariz."""
        return [self.panel_examen, self.panel_errores, self.panel_vista]

    def _pestana_informe(self):
        caja = Tarjeta('Informe')
        caja.agregar(etiqueta('Hallazgos', rol='campo'))
        self.txt_hallazgos = QPlainTextEdit()
        caja.agregar(self.txt_hallazgos, 1)
        caja.agregar(etiqueta('Conclusión', rol='campo'))
        self.txt_conclusion = QPlainTextEdit()
        caja.agregar(self.txt_conclusion, 1)
        self.estado_informe = EstadoInforme()
        caja.agregar(self.estado_informe)
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(caja)
        return contenedor

    def _encabezado(self):
        """Una línea: lo que va pasando y, si hay, el vasoconstrictor. El
        paciente ya está en la atención; el minuto del ciclo nasal, en "Lo
        que el equipo no sabe"."""
        caja = QWidget()
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(4, 0, 4, 0)
        fila.setSpacing(8)
        self.lbl_mensaje = etiqueta('', rol='hint')
        self.lbl_mensaje.setWordWrap(True)
        fila.addWidget(self.lbl_mensaje, 1)
        self.pill_estado = Pastilla('', 'neutro')
        self.pill_estado.setVisible(False)
        fila.addWidget(self.pill_estado)
        return caja

    def _boton(self, texto, accion, principal=False):
        b = QPushButton(texto)
        if principal:
            b.setObjectName('btnPrincipal')
        b.clicked.connect(accion)
        return b

    def _check(self, texto, accion, marcado=False):
        c = QCheckBox(texto)
        c.setChecked(marcado)
        c.toggled.connect(lambda _v: accion())
        return c

    def _bloque_tabla(self, titulo):
        """Resultados: tabla, avisos y pie, con barra si no caben (a 1366×768
        no caben: la curva manda en el alto)."""
        caja = Tarjeta(titulo)
        interior = QWidget()
        self.resultados = QVBoxLayout(interior)
        self.resultados.setContentsMargins(0, 0, 4, 0)
        self.resultados.setSpacing(6)
        tabla = Tabla()
        self.resultados.addWidget(tabla)
        avisos = etiqueta('', rol='hint')
        avisos.setWordWrap(True)
        avisos.setStyleSheet(f'color: {tema.AVISO};')
        self.resultados.addWidget(avisos)
        pie = etiqueta('', rol='hint')
        pie.setWordWrap(True)
        self.resultados.addWidget(pie)
        self.resultados.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidget(interior)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        caja.agregar(desplazable, 1)
        caja.setMinimumHeight(150)
        return caja, tabla, pie, avisos

    # --- Ciclo de vida (API que llama main.py) ---------------------------

    def la_super(self, data, appointment_id=None):
        """Entra (o sale) el paciente en atención."""
        self.sesion = sesion.para(data, appointment_id)
        self.appointment_id = appointment_id
        self.data_caso = data
        self.res = _vacio()
        self.mediciones = []
        self.txt_hallazgos.clear()
        self.txt_conclusion.clear()
        self.estado_informe.limpiar()
        if self.sesion is None or not self.sesion.hay_paciente:
            self._sin_caso(con_paciente=data is not None)
            return
        for panel in self._paneles():
            panel.setEnabled(True)
        self._al_entrar()
        self._mensaje(self.INDICACION)
        self.dibujar()

    def _sin_caso(self, con_paciente=False):
        for panel in self._paneles():
            panel.setEnabled(False)
        if con_paciente:
            self._mensaje('Este paciente no tiene la nariz cargada en el caso: el equipo no '
                          'mide. Hace falta el bloque NASAL del caso.', 'alerta')
        else:
            self._mensaje('Abre una atención para medir.')
        self.dibujar()

    # --- Informe (contrato de core/report_autosave.py) -----------------

    def report_job(self):
        """El informe tal como se sube, o None si no hay nada medido."""
        if not self.data_login or not self.mediciones or self.sesion is None:
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        avisos = [a.lstrip('• ') for a in self.avisos.text().split('\n') if a.strip()]
        data = {
            'mediciones': self.mediciones,
            'vasoconstrictor': self.sesion.vc_informe(),
            'tabla': getattr(self.tabla, 'contenido', {}),
            'avisos': avisos + self._avisos_informe(),
            'hallazgos': self.txt_hallazgos.toPlainText(),
            'conclusion': self.txt_conclusion.toPlainText(),
        }
        data.update(self._extra_informe())
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data,
                'images': self._exportar_imagenes}

    def submit_report(self):
        return sesion.subir_al_cerrar(self)

    def _avisos_informe(self):
        return []

    def _extra_informe(self):
        return {}

    def restore_report(self, data):
        """Retomar la atención: las mediciones guardadas se vuelven a
        calcular (fuera de la ventana) y vuelve el texto del informe. Solo si
        en esta vuelta todavía no se midió nada."""
        if self.sesion is None or not self.sesion.hay_paciente or self.mediciones:
            return False
        recetas = [m for m in (data.get('mediciones') or []) if isinstance(m, dict)
                   and m.get('lado') in LADOS and m.get('fase') in ('reposo', 'vc')]
        self.txt_hallazgos.setPlainText(data.get('hallazgos') or '')
        self.txt_conclusion.setPlainText(data.get('conclusion') or '')
        self.sesion.restaurar_vc(data.get('vasoconstrictor'))
        self._restaurar_extra(data)
        if not recetas:
            self.dibujar()
            return False
        paciente, funcion, sesion_actual = self.sesion.paciente, self.FUNCION, self.sesion

        def calcular():
            return [(m, funcion(paciente, m['lado'], m.get('estado') or {}, m.get('opciones') or {}))
                    for m in recetas]

        def listo(resultados):
            self._midiendo(False)
            if self.sesion is not sesion_actual or self.mediciones:
                return
            for m, r in resultados:
                self.res[m['fase']][m['lado']] = r
            self.mediciones = [m for m, _ in resultados]
            self._mensaje('Se recuperaron las mediciones guardadas de esta atención.', 'ok')
            self.dibujar()

        self._midiendo(True)
        self.tarea = hilos.en_fondo(calcular, listo=listo, fallo=lambda _e: self._midiendo(False),
                                    dueno=self, nombre=f'recuperar {self.EQUIPO}')
        return True

    def _restaurar_extra(self, data):
        pass

    def _registrar_medicion(self, lado, fase, r, receta):
        pass

    def _exportar_imagenes(self):
        temp = context.get_resource('local_cache/nasal/temp')
        os.makedirs(temp, exist_ok=True)
        imagenes = {}
        for sufijo, grafico in self._graficos_informe():
            ruta = os.path.join(temp, f'upload_{sufijo}.jpg')
            try:
                grafico.exportar(ruta)
            except Exception as exc:  # noqa: BLE001 -- sin imagen el informe sube igual
                print(f'{self.TIPO}: no se pudo exportar {sufijo}: {exc}')
                continue
            imagenes[sufijo] = ruta
        return imagenes

    def showEvent(self, evento):
        # El vasoconstrictor pudo ponerse desde el otro equipo.
        self._refrescar_encabezado()
        super().showEvent(evento)

    # --- Común ---------------------------------------------------------

    data_caso = None

    def _log(self, accion, **payload):
        """Una acción del alumno a action_logs, con el prefijo del equipo
        (rm_, ra_): ver sesion.registrar."""
        if self.sesion is None or not self.sesion.hay_paciente:
            return
        payload.setdefault('minuto_ciclo', self.sesion.minuto())
        sesion.registrar(f'{self.EQUIPO}_{accion}', self.data_caso, self.appointment_id, **payload)

    def _log_error_simulado(self, chk, clave):
        """Solo lo que se marca a mano (clicked): lo que corrige una
        indicación o una acción no es "simular"."""
        chk.clicked.connect(lambda activo, k=clave: self._log('error_simulado', error=k, activo=activo))

    def _mensaje(self, texto, estado=None):
        self.lbl_mensaje.setText(texto)
        color = {'alerta': tema.ALERTA, 'ok': tema.OK}.get(estado, tema.TEXTO_SUAVE)
        self.lbl_mensaje.setStyleSheet(f'color: {color};')

    def _refrescar_encabezado(self):
        if self.sesion is None or not self.sesion.hay_paciente:
            self.pill_estado.setVisible(False)
            return
        texto = texto_vc(self.sesion)
        self.pill_estado.set(texto, 'acento')
        self.pill_estado.setVisible(bool(texto) and self.PILL_VC)
        self.btn_vc.setEnabled(not all(l in self.sesion.vc_puesto for l in LADOS) and not self.midiendo)

    def _cada_segundo(self):
        if self.sesion is not None and self.sesion.hay_paciente and self.sesion.vc:
            self._refrescar_encabezado()

    def _vasoconstrictor(self):
        self.sesion.aplicar_vasoconstrictor()
        self._log('vasoconstrictor', lados=list(LADOS), farmaco='oximetazolina', puff=2)
        self._mensaje('Vasoconstrictor puesto en las dos fosas (oximetazolina, 2 puff). Hace efecto '
                      'a los 15 minutos: lo que midas desde ahora es "con VC", pero antes de ese '
                      'tiempo la mucosa sigue igual. Retira la mucosa y apaga el ciclo; no toca lo '
                      'estructural.')
        self.dibujar()

    def _medir(self, lado):
        """La medición corre fuera de la ventana (una fosa de rinomanometría
        tarda ~0,7 s): mientras, los botones de medir quedan apagados."""
        if self.sesion is None or not self.sesion.hay_paciente or self.midiendo:
            return
        pedido = self._pedido(lado)
        if pedido is None:
            return
        funcion, args = pedido
        sesion_de_la_medicion, fase = self.sesion, self.sesion.fase(lado)
        # Cómo se tomó: con esto restore_report la vuelve a calcular igual.
        _p, _lado, estado, opciones = args
        receta = {'lado': lado, 'fase': fase, 'estado': dict(estado), 'opciones': opciones}
        self._midiendo(True)
        self._mensaje(f'Midiendo la {SIGLA[lado]}…')

        def listo(r):
            self._midiendo(False)
            if self.sesion is not sesion_de_la_medicion:
                return   # cambió la atención mientras medía
            self.res[fase][lado] = r
            self.mediciones = [m for m in self.mediciones
                               if (m['lado'], m['fase']) != (lado, fase)] + [receta]
            self._registrar_medicion(lado, fase, r, receta)
            self._al_medir(lado, r)
            self.dibujar()

        def fallo(exc):
            self._midiendo(False)
            self._mensaje(f'No se pudo medir: {exc}', 'alerta')

        self.tarea = hilos.en_fondo(funcion, *args, listo=listo, fallo=fallo, dueno=self,
                                    nombre=f'medir {self.EQUIPO}')

    midiendo = False
    tarea = None

    def _midiendo(self, si):
        self.midiendo = si
        for b in (self.btn_d, self.btn_i, self.btn_vc):
            b.setEnabled(not si)
        if not si:
            self._refrescar_encabezado()

    def _series(self):
        return [(self.res[f], f == 'vc') for f in ('reposo', 'vc')
                if self.res[f]['D'] or self.res[f]['I']]

    def _hay_vc(self):
        return bool(self.res['vc']['D'] or self.res['vc']['I'])

    def _lista_avisos(self):
        lineas = []
        for nombre, fase in (('reposo', 'reposo'), ('con vasoconstrictor', 'vc')):
            for lado in LADOS:
                for a in (self.res[fase][lado] or {}).get('avisos', []):
                    lineas.append(f'• {SIGLA[lado]} ({nombre}): {a}')
        return '\n'.join(lineas)

    def dibujar(self):
        self._refrescar_encabezado()
        self._dibujar_equipo()
        if self.verdad is not None:
            self.verdad.setText(self._texto_verdad() if self.sesion and self.sesion.hay_paciente else '')


class RinomanometriaWindow(EquipoNasal):
    """La rinomanometría como se hace. Apenas el paciente tiene el adaptador
    con el tubo de presión en una narina o la máscara puesta, la pantalla
    muestra su respiración en vivo: la presión si hay adaptador, el flujo si
    hay máscara (el neumotacógrafo va en ella), y el lazo presión-flujo con
    los dos. El alumno le da indicaciones hasta que respire parejo (cada una
    tarda una o dos respiraciones en notarse) y recién ahí graba: lo
    anterior se descarta y el equipo graba el tiempo elegido (10 a 60 s),
    cuenta los ciclos completos y los promedia.

    El vasoconstrictor se pone desde el paciente (sin máscara ni adaptador):
    fármaco, fosa y puff, y hay que esperar su tiempo de acción (nasal/sesion.py).

    Cada ciclo sale del modelo con lo que hacía el paciente en ese momento
    (rinomanometria.Registro). La grabación tiene su propio Registro: la
    receta (la condición de cada ciclo y la semilla) basta para rehacerla al
    retomar la atención. Lo que se ve en vivo antes de grabar no se guarda."""

    TITULO = 'Rinomanometría anterior'
    EQUIPO = 'rm'
    PILL_VC = False            # ya lo cuenta el paciente
    TIPO = 'RINOMANOMETRIA'
    FUNCION = staticmethod(RM.mide_registro)
    INDICACION = ('Pon el adaptador con el tubo de presión en una narina (clic en la narina del '
                  'paciente) y la máscara: verás su respiración. Cuando respire parejo, graba. Se '
                  'mide la fosa contraria al adaptador; primero la derecha.')

    # Segundos por ciclo respiratorio, tranquila y forzada (~19 por minuto). Del simulador.
    DURACION = {False: 3.2, True: 2.8}
    TIEMPOS = (10, 15, 20, 30, 60)
    MIN_CICLOS = 3
    TIC_MS = 40
    GUARDA_S = 70              # lo que se guarda de los trazos en el tiempo
    RECIENTES = 3              # ciclos en vivo que quedan en el lazo

    INDICACIONES = (
        ('tranquila', 'Respire tranquilo por la nariz'),
        ('boca', 'Cierre bien la boca'),
        ('parejo', 'Respire parejo, sin tragar ni hablar'),
        ('fuerte', 'Tome aire fuerte por la nariz'),
    )

    mon = None                 # el paciente en vivo (Registro que no se guarda)
    _mon_nuevo = None          # el que lo reemplaza, mientras se calcula
    rec = None                 # la grabación en curso
    sonda = None               # narina con el adaptador
    mascara = False
    forzada = False

    def __init__(self, data_login=None, parent=None):
        self._reloj = time.monotonic
        self._azar = random.Random()
        self._pedidas = set()
        self._pendientes = []
        self._n_mon = 0
        super().__init__(data_login, parent)
        self.timer = QTimer(self)
        self.timer.setInterval(self.TIC_MS)
        self.timer.timeout.connect(self._tic)

    def _graficos_informe(self):
        return [('rm_curva', self.g_curva), ('rm_resistencia', self.g_resistencia)]

    # --- UI -------------------------------------------------------------

    def _paneles_izquierda(self, izq):
        self.panel_paciente = Tarjeta('Paciente')
        self.vista_paciente = PacienteRM()
        self.vista_paciente.setFixedHeight(250)
        self.vista_paciente.narina.connect(self._poner_sonda)
        self.panel_paciente.agregar(self.vista_paciente)
        self.lbl_sonda = etiqueta('', rol='hint')
        self.lbl_sonda.setWordWrap(True)
        self.panel_paciente.agregar(self.lbl_sonda)
        fila = QHBoxLayout()
        fila.setSpacing(6)
        self.btn_mascara = self._boton('Poner la máscara', self._mascara)
        self.btn_acomodar = self._boton('Acomodarla', self._acomodar)
        fila.addWidget(self.btn_mascara, 1)
        fila.addWidget(self.btn_acomodar)
        self.panel_paciente.agregar_layout(fila)
        self._caja_vc(self.panel_paciente)
        izq.addWidget(self.panel_paciente)

        self.panel_indicaciones = Tarjeta('Indicaciones al paciente')
        for clave, texto in self.INDICACIONES:
            b = self._boton(f'«{texto}»', lambda _c=False, k=clave: self._indicar(k))
            b.setStyleSheet('text-align: left;')
            self.panel_indicaciones.agregar(b)
        izq.addWidget(self.panel_indicaciones)
        self._paneles_comunes(izq)

    def _caja_vc(self, caja):
        """El vasoconstrictor: se elige y se pone en el paciente."""
        self.btn_vc = caja.agregar(self._boton('Vasoconstrictor…', self._abrir_vc))
        self.caja_vc = QFrame()
        interior = QVBoxLayout(self.caja_vc)
        interior.setContentsMargins(0, 0, 0, 0)
        campos = Campos()
        self.cmb_farmaco = QComboBox()
        for clave, nombre in sesion.VASOCONSTRICTORES:
            self.cmb_farmaco.addItem(nombre, clave)
        campos.agregar('Fármaco', self.cmb_farmaco)
        self.cmb_fosa_vc = QComboBox()
        for texto, lados in (('Derecha', ('D',)), ('Izquierda', ('I',)), ('Las dos', LADOS)):
            self.cmb_fosa_vc.addItem(texto, lados)
        campos.agregar('Fosa', self.cmb_fosa_vc)
        self.spin_puff = QSpinBox()
        self.spin_puff.setRange(1, 3)
        self.spin_puff.setValue(2)
        campos.agregar('Puff', self.spin_puff)
        interior.addWidget(campos)
        interior.addWidget(self._boton('Aplicar', self._vasoconstrictor, True))
        self.caja_vc.setVisible(False)
        caja.agregar(self.caja_vc)
        self.lbl_vc = caja.agregar(etiqueta('', rol='hint'))
        self.lbl_vc.setWordWrap(True)
        self.btn_saltar = caja.agregar(self._boton('Saltar la espera (docente)', self._saltar_espera))
        self.btn_saltar.setVisible(False)

    def _paneles(self):
        return [self.panel_paciente, self.panel_indicaciones, self.panel_examen,
                self.panel_errores, self.panel_vista]

    def _errores(self, caja):
        self.chk_err = {}
        for clave, texto in (('mascara', 'Fuga en la máscara'), ('adaptador', 'Adaptador sin sellar'),
                             ('boca', 'Respira por la boca'), ('irregular', 'Respiración irregular')):
            self.chk_err[clave] = caja.agregar(self._check(texto, self._sync_paciente))
            self._log_error_simulado(self.chk_err[clave], clave)

    def _opciones(self, caja):
        self.chk_ciclos = caja.agregar(self._check('Ver los ciclos', self.dibujar, True))
        self.chk_referencia = caja.agregar(self._check('Recta de referencia (0,4)', self.dibujar, True))
        self.chk_broms = caja.agregar(self._check('Lectura de Broms (radio 200)', self.dibujar))

    def _barra_examen(self):
        self.panel_examen = Tarjeta()
        self.panel_examen.cuerpo.setContentsMargins(10, 8, 10, 8)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.btn_sello = self._boton('Comprobar sello', self._sello)
        self.btn_registro = self._boton('Grabar', self._registro, True)
        self.btn_registro.setMinimumWidth(120)
        campos = Campos()
        self.cmb_tiempo = QComboBox()
        for s in self.TIEMPOS:
            self.cmb_tiempo.addItem(f'{s} s', s)
        self.cmb_tiempo.setCurrentIndex(self.TIEMPOS.index(20))
        self.cmb_tiempo.setToolTip('Cuánto graba; promedia los ciclos completos de ese tiempo')
        campos.agregar('Tiempo', self.cmb_tiempo)
        self.pill_registro = Pastilla('', 'neutro')
        self.pill_ambiente = Pastilla('', 'neutro')
        self.pill_ambiente.setToolTip('Temperatura y humedad relativa de la sala, del sensor del equipo')
        for w in (self.btn_sello, self.btn_registro, campos):
            fila.addWidget(w)
        fila.addStretch(1)
        fila.addWidget(self.pill_registro)
        fila.addWidget(self.pill_ambiente)
        self.panel_examen.agregar_layout(fila)
        return self.panel_examen

    def _pantalla(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(self._barra_examen())
        self.g_tiempo = GraficoTiempo()
        self.g_curva = GraficoRinomanometria()
        self.g_resistencia = GraficoResistencia()
        caja_tiempo = Tarjeta('Presión y flujo')
        caja_tiempo.agregar(self.g_tiempo.widget, 1)
        # La curva y la resistencia, una a la vez: la tabla necesita el ancho.
        curvas = QTabWidget()
        curvas.addTab(self.g_curva.widget, 'Presión-flujo')
        curvas.addTab(self.g_resistencia.widget, 'Resistencia según la presión')
        self.tabs_curvas = curvas
        arriba = QSplitter(Qt.Orientation.Horizontal)
        arriba.addWidget(caja_tiempo)
        arriba.addWidget(curvas)
        arriba.setStretchFactor(0, 1)
        arriba.setStretchFactor(1, 1)
        arriba.setMinimumHeight(280)
        caja, self.tabla, self.pie, self.avisos = self._bloque_tabla('Resultados')
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(arriba)
        vertical.addWidget(caja)
        vertical.setStretchFactor(0, 3)
        vertical.setStretchFactor(1, 2)
        layout.addWidget(vertical, 1)
        return contenedor

    # --- El paciente ----------------------------------------------------

    def la_super(self, data, appointment_id=None):
        self._parar()
        super().la_super(data, appointment_id)
        self._sync_paciente()
        self._cada_segundo()

    def _sin_caso(self, con_paciente=False):
        self._parar()
        super()._sin_caso(con_paciente)
        if hasattr(self, 'vista_paciente'):
            self._sync_paciente()

    def _al_entrar(self):
        self.sonda = None
        self.mascara = False
        self.forzada = False
        self._pendientes = []
        self.caja_vc.setVisible(False)
        for chk in self.chk_err.values():
            chk.setChecked(False)

    def _poner_sonda(self, lado):
        if self.rec is not None:
            self._log('adaptador', narina=lado, rechazado='grabando')
            self._mensaje('Termina o cancela la grabación antes de cambiar el adaptador.', 'alerta')
            return
        if self.mascara:
            self._log('adaptador', narina=lado, rechazado='con_mascara')
            self._mensaje('Saca la máscara para cambiar el adaptador de narina.', 'alerta')
            return
        self._log('adaptador', narina=None if self.sonda == lado else lado)
        if self.sonda == lado:
            self.sonda = None
            self._mensaje('Adaptador fuera.')
        else:
            self.sonda = lado
            self.chk_err['adaptador'].setChecked(False)
            self._mensaje(f'Adaptador con el tubo de presión en la narina {NARINA[lado]}: se mide la '
                          f'{SIGLA[otro_lado(lado)]}. Comprueba que selle y pon la máscara.')
        self._sync_paciente()
        self._sync_monitor()

    def _mascara(self):
        if self.rec is not None:
            self._log('mascara', puesta=False, rechazado='grabando')
            self._mensaje('Termina o cancela la grabación antes de sacar la máscara.', 'alerta')
            return
        self.mascara = not self.mascara
        self._log('mascara', puesta=self.mascara, con_adaptador=self.sonda)
        self.chk_err['mascara'].setChecked(False)
        if self.mascara and not self.sonda:
            self._mensaje('Máscara puesta: se ve el flujo, pero sin adaptador no hay presión y '
                          'respira por las dos fosas.')
        else:
            self._mensaje('Máscara puesta, apoyada en toda la cara.' if self.mascara else 'Máscara fuera.')
        self._sync_paciente()
        self._sync_monitor()

    def _acomodar(self):
        self._log('acomodar_mascara', tenia_fuga=self.chk_err['mascara'].isChecked(),
                  grabando=self.rec is not None)
        self.chk_err['mascara'].setChecked(False)
        self._mensaje('Acomodas la máscara y la apoyas pareja contra la cara.')
        self._sync_paciente()

    def _indicar(self, clave):
        """La indicación se nota en la primera o la segunda respiración que
        sigue: hay que esperar a que se regule."""
        texto = dict(self.INDICACIONES)[clave]
        # ¿Hacía falta? Lo que el paciente hacía cuando se lo dijeron.
        necesaria = {'boca': self.chk_err['boca'].isChecked(),
                     'parejo': self.chk_err['irregular'].isChecked(),
                     'tranquila': self.forzada, 'fuerte': not self.forzada}[clave]
        self._log('indicacion', indicacion=clave, necesaria=necesaria, en_vivo=self.timer.isActive(),
                  grabando=self.rec is not None)
        if self.timer.isActive():
            self._pendientes.append([self._azar.choice((1, 2)), clave])
            cuando = ' Espera a que se regule.'
            errores, forzada = self._condicion(despues=True)
            if self.mon is not None:
                self._pedir_red(self.mon, errores, forzada)
        else:
            self._obedecer(clave)
            cuando = ''
        self._mensaje(f'Le dices al paciente: «{texto}».{cuando}')

    def _obedecer(self, clave):
        if clave == 'tranquila':
            self.forzada = False
        elif clave == 'boca':
            self.chk_err['boca'].setChecked(False)
        elif clave == 'parejo':
            self.chk_err['irregular'].setChecked(False)
        elif clave == 'fuerte':
            self.forzada = True
        self._sync_paciente()

    def _abrir_vc(self):
        self.caja_vc.setVisible(not self.caja_vc.isVisible())

    def _vasoconstrictor(self):
        lados = self.cmb_fosa_vc.currentData()
        if self.sonda or self.mascara:
            self._log('vasoconstrictor', lados=list(lados), rechazado='con_mascara_o_adaptador')
            self._mensaje('Saca la máscara y el adaptador para poner el vasoconstrictor.', 'alerta')
            return
        ya = [l for l in lados if l in self.sesion.vc_puesto]
        if len(ya) == len(lados):
            self._log('vasoconstrictor', lados=list(lados), rechazado='ya_tenia')
            self._mensaje('Esa fosa ya tiene vasoconstrictor.', 'alerta')
            return
        puff = self.spin_puff.value()
        self._log('vasoconstrictor', lados=[l for l in lados if l not in ya],
                  farmaco=self.cmb_farmaco.currentData(), puff=puff,
                  resistencia_reposo_150={l: r150(self.res['reposo'][l]) for l in LADOS})
        self.sesion.aplicar_vasoconstrictor(lados, self.cmb_farmaco.currentData(), puff)
        self.caja_vc.setVisible(False)
        fosas = ' y '.join(SIGLA[l] for l in lados if l not in ya)
        self._mensaje(f'{self.cmb_farmaco.currentText()}, {puff} puff en {fosas}. Hace efecto a los '
                      f'{sesion.ESPERA_VC_S // 60} minutos: lo que midas antes sigue con la mucosa '
                      'como estaba.')
        self._cada_segundo()
        self.dibujar()

    def _saltar_espera(self):
        self._log('saltar_espera', faltaba={l: self.sesion.falta_vc(l) for l in LADOS
                                            if self.sesion.falta_vc(l) is not None})
        self.sesion.saltar_espera()
        self._mensaje('Se da por pasado el tiempo de acción del vasoconstrictor.')
        self._cada_segundo()

    def _cada_segundo(self):
        super()._cada_segundo()
        hay = bool(self.sesion and self.sesion.hay_paciente)
        if hay:
            temp, hr = self.sesion.ambiente()
            self.pill_ambiente.set(f'{num(temp, 1)} °C · HR {hr} %')
        else:
            self.pill_ambiente.set('')
        texto = texto_vc(self.sesion) if hay else ''
        self.lbl_vc.setText(texto)
        self.lbl_vc.setVisible(bool(texto))
        self.btn_saltar.setVisible(self.es_docente and hay and any(
            (self.sesion.falta_vc(l) or 0) > 0 for l in LADOS))

    def _sync_paciente(self):
        v = self.vista_paciente
        hay = bool(self.sesion and self.sesion.hay_paciente)
        v.activo = hay
        v.sonda, v.mascara = self.sonda, self.mascara
        v.boca = self.chk_err['boca'].isChecked()
        v.fuga = self.mascara and self.chk_err['mascara'].isChecked()
        v.suelto = bool(self.sonda) and self.chk_err['adaptador'].isChecked()
        if not self.mascara:
            v.empanado = 0.0
        v.update()
        self.btn_mascara.setText('Sacar la máscara' if self.mascara else 'Poner la máscara')
        self.btn_acomodar.setEnabled(self.mascara)
        if not hay:
            self.lbl_sonda.setText('')
        elif self.sonda:
            self.lbl_sonda.setText(f'Adaptador en la narina {NARINA[self.sonda]} · se mide la '
                                   f'{SIGLA[otro_lado(self.sonda)]}.')
        else:
            self.lbl_sonda.setText('Sin adaptador: clic en una narina para ponerlo.')

    def _condicion(self, despues=False):
        """Lo que hace el paciente ahora (o cuando obedezca lo pedido) y
        cómo está puesto el equipo."""
        errores = {k: True for k, c in self.chk_err.items() if c.isChecked()}
        forzada = self.forzada
        if despues:
            for _n, clave in self._pendientes:
                errores.pop({'boca': 'boca', 'parejo': 'irregular'}.get(clave, ''), None)
                forzada = {'tranquila': False, 'fuerte': True}.get(clave, forzada)
        if not self.mascara:
            errores.pop('mascara', None)
        if not self.sonda:
            errores.pop('adaptador', None)
            errores['abierta'] = True
        return errores, forzada

    # --- En vivo --------------------------------------------------------

    def _lado_medido(self):
        return otro_lado(self.sonda) if self.sonda else 'D'

    def _sync_monitor(self):
        """Con adaptador o máscara el paciente se ve respirar. Un cambio de
        lado, de adaptador o del vasoconstrictor arma otro paciente en vivo
        (mientras se calcula, sigue el de antes)."""
        if not (self.sesion and self.sesion.hay_paciente and (self.sonda or self.mascara)):
            self._parar()
            return
        lado = self._lado_medido()
        estado = self.sesion.estado(lado)
        abierta = not self.sonda
        mon = self.mon
        if mon is not None and (mon.lado, mon.estado['vc'], mon.abierta) == (lado, estado['vc'], abierta):
            return
        pendiente = getattr(self, '_mon_nuevo', None)
        if pendiente is not None and (pendiente.lado, pendiente.estado['vc'], pendiente.abierta) == \
                (lado, estado['vc'], abierta):
            return
        self._n_mon += 1
        nuevo = RM.Registro(self.sesion.paciente, lado, estado,
                            f'vivo/{self.sesion.appointment_id}/{self._n_mon}')
        nuevo.abierta = abierta
        nuevo.ultima = self._condicion()
        self._mon_nuevo = nuevo

        def listo():
            if self._mon_nuevo is not nuevo:
                return
            self._mon_nuevo = None
            self.mon = nuevo
            self._vivo_desde = self._reloj()      # cuánto lo miró así antes de grabar
            if not self.timer.isActive():
                self._t0 = self._reloj()
                self._t, self._P, self._V = [], [], []
                self._recientes = []
                self._ciclo_nuevo(0.0)
                self.timer.start()
                self.dibujar()

        self._pedir_red(nuevo, *nuevo.ultima, luego=listo)

    def _pedir_red(self, reg, errores, forzada, luego=None):
        """La red de esa condición, calculada fuera de la ventana (~1 s)."""
        if reg.red(errores, forzada) is not None:
            if luego:
                luego()
            return
        clave = (id(reg), RM.clave_red(errores, forzada))
        if clave in self._pedidas and luego is None:
            return
        self._pedidas.add(clave)

        def listo(red):
            reg.poner_red(errores, forzada, red)
            if luego:
                luego()

        def fallo(exc):
            self._mensaje(f'No se pudo calcular la respiración: {exc}', 'alerta')

        self.tarea = hilos.en_fondo(reg.calcular_red, errores, forzada, listo=listo, fallo=fallo,
                                    dueno=self, nombre='red rm')

    def _ciclo_nuevo(self, inicio):
        """El ciclo que empieza ahora, con lo que el paciente hace ahora. Si
        lo que cambió todavía no está calculado, respira una vez más como
        venía (y se calcula mientras)."""
        for p in self._pendientes:
            p[0] -= 1
        for _n, clave in [p for p in self._pendientes if p[0] <= 0]:
            self._obedecer(clave)
        self._pendientes = [p for p in self._pendientes if p[0] > 0]
        if self.rec is None:
            self._sync_monitor()          # p. ej., el vasoconstrictor ya hizo efecto
        fuente = self.rec or self.mon
        errores, forzada = self._condicion()
        if fuente.red(errores, forzada) is None:
            # Lo que cambia la red espera; lo que no (fuga, respiración
            # irregular) ya vale en este ciclo.
            self._pedir_red(fuente, errores, forzada)
            antes, forzada = fuente.ultima
            errores = {k: v for k, v in errores.items() if k not in RM.ERRORES_DE_RED}
            errores.update({k: v for k, v in antes.items() if k in RM.ERRORES_DE_RED})
        fuente.ultima = (errores, forzada)
        c = fuente.siguiente(errores, forzada)
        if fuente is self.mon and len(fuente.ciclos) > 4:
            del fuente.ciclos[:-4], fuente.condiciones[:-4]   # lo en vivo no se guarda
        self._actual = {'c': c, 'fuente': fuente, 'ini': inicio, 'dur': self.DURACION[bool(forzada)],
                        'hechos': 0, 'P': [], 'V': []}

    def _muestra(self, c, k):
        """Lo que lee el equipo: sin adaptador no hay presión, sin máscara no
        hay flujo (queda el ruido del transductor)."""
        P = c['P'][k] if self.sonda else self._azar.gauss(0, 1.2)
        V = c['V'][k] if self.mascara else self._azar.gauss(0, 4)
        return P, V

    def _tic(self):
        if self.mon is None and self.rec is None:
            return
        ahora = self._reloj() - self._t0
        N = RM.N_CICLO
        while True:
            a = self._actual
            frac = (ahora - a['ini']) / a['dur']
            hasta = max(a['hechos'], min(N, int(frac * N)))
            for k in range(a['hechos'], hasta):
                P, V = self._muestra(a['c'], k)
                self._t.append(a['ini'] + k * a['dur'] / N)
                self._P.append(P)
                self._V.append(V)
                a['P'].append(P)
                a['V'].append(V)
            a['hechos'] = hasta
            if frac < 1:
                break
            fin = a['ini'] + a['dur']
            if self.rec is not None and a['fuente'] is self.rec and fin <= self._grab_fin + 1e-9:
                self._rec_completos.append(a['c'])
            else:
                self._recientes = (self._recientes + [{'P': a['P'], 'V': a['V']}])[-self.RECIENTES:]
            if self.rec is not None and fin >= self._grab_fin - 1e-9:
                self._terminar_grabacion()
            self._ciclo_nuevo(fin)
            self.dibujar()
        if self.rec is not None and ahora >= self._grab_fin:
            self._terminar_grabacion()
            self.dibujar()
        if self._t and self._t[0] < self._t[-1] - self.GUARDA_S:
            corte = next(i for i, t in enumerate(self._t) if t >= self._t[-1] - self.GUARDA_S)
            del self._t[:corte], self._P[:corte], self._V[:corte]
        lado = (self.rec or self.mon).lado
        self.g_tiempo.poner(self._t, self._P, self._V, lado, grabado=self._ventana_grabada())
        a = self._actual
        self.g_curva.actual(a['P'], a['V'])
        if self.rec is not None:
            self.pill_registro.set(f'Grabando {min(ahora, self._grab_fin):.0f} / {self._grab_fin:.0f} s · '
                                   f'{len(self._rec_completos)} ciclos', 'acento')
        # El vaho en la máscara: aparece al espirar y se va al inspirar.
        v = self.vista_paciente
        if self.mascara:
            v.empanado = min(1.0, max(v.empanado * 0.9, -(self._V[-1] if self._V else 0) / 450))
            v.update()

    def _ventana_grabada(self):
        if self.rec is not None:
            return (0.0, self._grab_fin)
        return getattr(self, '_ultima_grabada', None)

    # --- La grabación ---------------------------------------------------

    def _sello(self):
        self._log('sello', con_adaptador=self.sonda,
                  sella=bool(self.sonda) and not self.chk_err['adaptador'].isChecked())
        if not self.sonda:
            self._mensaje('Primero pon el adaptador en una narina.', 'alerta')
        elif self.chk_err['adaptador'].isChecked():
            self._mensaje('Pasa aire por el adaptador: no sella. El tubo no va a leer la '
                          'rinofaringe. Sácalo y vuelve a ponerlo antes de medir.', 'alerta')
        else:
            self._mensaje('No pasa aire por el adaptador: sella bien.', 'ok')

    def _registro(self):
        if self.rec is not None:
            self._cancelar()
            return
        if self.sesion is None or not self.sesion.hay_paciente or self.midiendo:
            return
        if not self.sonda:
            self._mensaje('Pon el adaptador con el tubo de presión en una narina (clic en la narina).',
                          'alerta')
            return
        if not self.mascara:
            self._mensaje('Pon la máscara antes de grabar.', 'alerta')
            return
        if self.mon is None or not self.timer.isActive() or self._mon_nuevo is not None \
                or self.mon.lado != self._lado_medido():
            self._mensaje('Espera a ver respirar al paciente.', 'alerta')
            return
        mon = self.mon
        errores, forzada = self._condicion()
        self._log('grabar', lado=mon.lado, segundos=self.cmb_tiempo.currentData(),
                  en_vivo_s=self._reloj() - self._vivo_desde, errores=errores, forzada=forzada,
                  pendientes=[c for _n, c in self._pendientes], vc_puesto=mon.lado in self.sesion.vc_puesto,
                  vc_activo=bool(mon.estado.get('vc')), falta_vc=self.sesion.falta_vc(mon.lado))
        self.rec = RM.Registro(self.sesion.paciente, mon.lado, mon.estado,
                               self.sesion.semilla_medicion(self.EQUIPO))
        self.rec.redes = dict(mon.redes)
        self.rec.ultima = mon.ultima
        self.rec_fase = self.sesion.fase(mon.lado)
        self._rec_completos = []
        self._ultima_grabada = None
        self._grab_fin = float(self.cmb_tiempo.currentData())
        # Lo de antes se descarta: la pantalla y el lazo vuelven a cero.
        self._t0 = self._reloj()
        self._t, self._P, self._V = [], [], []
        self._recientes = []
        self._ciclo_nuevo(0.0)
        self.btn_registro.setText('Cancelar')
        self._refrescar_encabezado()
        self._mensaje(f'Grabando la {SIGLA[mon.lado]} durante {self._grab_fin:.0f} s.')
        self.dibujar()

    def _cancelar(self):
        self._log('cancelar', lado=self.rec.lado, segundos=self._grab_fin,
                  transcurrido=self._reloj() - self._t0, ciclos=len(self._rec_completos))
        self.rec = None
        self._fin_grabacion()
        self._mensaje('Grabación cancelada: no se guardó. El paciente sigue en vivo.')
        self.dibujar()

    def _fin_grabacion(self):
        self.btn_registro.setText('Grabar')
        self.pill_registro.set('')
        self._refrescar_encabezado()

    def _terminar_grabacion(self):
        """Pasó el tiempo: promedia los ciclos completos de la grabación."""
        rec, completos = self.rec, list(self._rec_completos)
        self.rec = None
        self._ultima_grabada = (0.0, self._grab_fin)
        self._fin_grabacion()
        while len(rec.ciclos) > len(completos):
            rec.descartar_ultimo()
        self._registrar_grabacion(rec, completos)
        if len(completos) < self.MIN_CICLOS:
            self._mensaje(f'En {self._grab_fin:.0f} s entraron {len(completos)} ciclos completos: hacen '
                          f'falta al menos {self.MIN_CICLOS} para promediar. No se guardó; graba más '
                          'tiempo.', 'alerta')
            return
        r = rec.resultado(len(completos))
        lado, fase = rec.lado, self.rec_fase
        temp, hr = self.sesion.ambiente()
        self.res[fase][lado] = r
        receta = {'lado': lado, 'fase': fase, 'estado': dict(rec.estado), 'opciones': rec.receta(len(completos)),
                  'segundos': self._grab_fin, 'ambiente': {'temperatura': temp, 'humedad': hr}}
        self.mediciones = [m for m in self.mediciones if (m['lado'], m['fase']) != (lado, fase)] + [receta]
        self._al_medir(lado, r)

    def _parar(self):
        """Sin adaptador ni máscara: no hay nada que ver."""
        if getattr(self, 'timer', None) is not None:
            self.timer.stop()
        self.mon = self.rec = None
        self._mon_nuevo = None
        self._ultima_grabada = None
        if hasattr(self, 'btn_registro'):
            self._fin_grabacion()
            self.g_tiempo.limpiar()
            self.vista_paciente.empanado = 0.0
            self.dibujar()

    def _registrar_grabacion(self, rec, completos):
        """Todo lo de la grabación, también lo que el equipo no sabe."""
        lado, fase = rec.lado, self.rec_fase
        temp, hr = self.sesion.ambiente()
        conds = rec.condiciones
        datos = {'lado': lado, 'fase': fase, 'segundos': self._grab_fin, 'ciclos': len(completos),
                 'guardada': len(completos) >= self.MIN_CICLOS, 'semilla': rec.semilla,
                 'minuto_ciclo': rec.estado.get('minuto'), 'vc_activo': bool(rec.estado.get('vc')),
                 'ciclos_con': {k: sum(1 for c in conds if c['errores'].get(k))
                                for k in ('boca', 'irregular', 'mascara', 'adaptador')},
                 'ciclos_forzados': sum(1 for c in conds if c['forzada']),
                 'ambiente': {'temperatura': temp, 'humedad': hr}}
        if completos and len(completos) >= self.MIN_CICLOS:
            r = rec.resultado(len(completos))
            l150 = r['lecturas'][150]['insp']
            datos.update({
                'medido': {str(P): (r['lecturas'][P]['insp'] or {}).get('R') for P in RM.PRESIONES},
                'verdad': {str(P): r['verdad'][P] for P in RM.PRESIONES},
                'error_150': (l150['R'] - r['verdad'][150]) / r['verdad'][150] if l150 else None,
                'pico_insp': r['pico']['insp'], 'congestion': r['congestion'],
                'cv_entre_ciclos': r['cv_entre_ciclos'], 'avisos': r['avisos'],
            })
            if fase == 'vc':
                lec = RM.lectura_vasoconstrictor(r150(self.res['reposo'][lado]), l150['R'] if l150 else None)
                if lec:
                    datos['lectura_h26'] = {'tipo': lec['tipo'], 'cambio': lec['cambio']}
        self._log('grabacion', **datos)

    def _midiendo(self, si):
        """Al retomar la atención se recalcula lo guardado fuera de la ventana."""
        self.midiendo = si
        self.btn_registro.setEnabled(not si)
        if not si:
            self._refrescar_encabezado()

    def _refrescar_encabezado(self):
        super()._refrescar_encabezado()
        if self.sesion is not None and self.sesion.hay_paciente:
            self.btn_vc.setEnabled(self.btn_vc.isEnabled() and self.rec is None)

    def _extra_informe(self):
        ultima = self.mediciones[-1] if self.mediciones else {}
        return {'ambiente': ultima.get('ambiente'), 'segundos': ultima.get('segundos')}

    def _al_medir(self, lado, r):
        siguiente = (' Saca la máscara, cambia el adaptador a la narina derecha y graba la FNI.'
                     if lado == 'D' else '')
        con = 'con vasoconstrictor' if self.sesion.fase(lado) == 'vc' else 'en reposo'
        self._mensaje(f'{SIGLA[lado]} {con}: promedio de {len(r["ciclos"])} ciclos en '
                      f'{self._grab_fin:.0f} s.{siguiente}', 'ok')

    def _dibujar_equipo(self):
        series = self._series()
        broms = self.chk_broms.isChecked()
        vivo = None
        if self.rec is not None:
            vivo = (self.rec.lado, self._rec_completos)
        elif self.mon is not None:
            vivo = (self.mon.lado, getattr(self, '_recientes', []))
        self.g_curva.dibujar(series, ciclos=self.chk_ciclos.isChecked(),
                             referencia=self.chk_referencia.isChecked(), broms=broms, vivo=vivo)
        self.g_resistencia.dibujar(series)
        self._tabla()
        self.avisos.setText(self._lista_avisos())

    def _tabla(self):
        reposo, vc = self.res['reposo'], self.res['vc']
        if not series_con_datos(self.res):
            self.tabla.poblar([], [])
            self.pie.setText('')
            return
        ref = REFERENCIA_UNILATERAL_150['valor']
        broms = self.chk_broms.isChecked()
        hay_vc = self._hay_vc()
        cab = ['Fosa', 'Pico insp. (Pa)', 'V̇ 75 (cm³/s)', 'R 75', 'V̇ 150 (cm³/s)', 'R 150']
        if broms:
            cab.append('R Broms')
        if hay_vc:
            cab += ['R 150 con VC', 'Cambio']

        def r150(f):
            return ((f or {}).get('lecturas', {}).get(150, {}).get('insp') or {}).get('R')

        def fuera(R):
            return None if R is None else ('fuera' if R > ref else None)

        filas = []
        for lado in LADOS:
            f, fv = reposo[lado], vc[lado]
            l75 = f['lecturas'][75]['insp'] if f else None
            l150 = f['lecturas'][150]['insp'] if f else None
            celdas = [SIGLA[lado], num(f['pico']['insp'], 0) if f else '—',
                      num(l75['V'], 0) if l75 else '—', num(l75['R']) if l75 else '—',
                      num(l150['V'], 0) if l150 else ('no llega' if f else '—'),
                      num(l150['R']) if l150 else '—']
            marcas = {5: fuera(l150['R'] if l150 else None)}
            if broms:
                b = (f or {}).get('broms')
                celdas.append(f'{num(b["R"])} a {num(b["P"], 0)} Pa' if b else '—')
            if hay_vc:
                rv = r150(fv)
                marcas[len(celdas)] = fuera(rv)
                celdas += [num(rv), pct((rv - l150['R']) / l150['R'] if l150 and rv is not None else None)]
            filas.append((celdas, lado, marcas))

        def total(fs, P):
            return RM.resistencia_total(((fs['D'] or {}).get('lecturas', {}).get(P, {}).get('insp') or {}).get('R'),
                                        ((fs['I'] or {}).get('lecturas', {}).get(P, {}).get('insp') or {}).get('R'))

        fila_total = ['Total', '', '', num(total(reposo, 75)), '', num(total(reposo, 150))]
        if broms:
            fila_total.append('')
        if hay_vc:
            t0, t1 = total(reposo, 150), total(vc, 150)
            fila_total += [num(t1), pct((t1 - t0) / t0 if t0 and t1 else None)]
        filas.append((fila_total, None, {}))
        self.tabla.poblar(cab, filas)
        self.pie.setText('Resistencias en Pa/(cm³/s), rama inspiratoria. Total: 1/RT = 1/RD + 1/RI, '
                         'con las dos fosas leídas a la misma presión. Referencia de trabajo del '
                         f'libro: ≤ {num(ref, 1)} por fosa a 150 Pa (en rojo lo que la supera). '
                         f'{REN_2018["texto"]} {VOGT_2016["texto"]}')

    def _texto_verdad(self):
        filas = []
        for nombre, fase in (('Reposo', 'reposo'), ('Con vasoconstrictor', 'vc')):
            for lado in LADOS:
                f = self.res[fase][lado]
                if not f:
                    continue
                m75 = (f['lecturas'][75]['insp'] or {}).get('R')
                m150 = (f['lecturas'][150]['insp'] or {}).get('R')
                if m150 is not None:
                    error = (m150 - f['verdad'][150]) / f['verdad'][150]
                elif m75 is not None:
                    error = (m75 - f['verdad'][75]) / f['verdad'][75]
                else:
                    error = None
                filas.append(f'<tr><td>{SIGLA[lado]}</td><td>{nombre}</td><td>{num(f["congestion"])}</td>'
                             f'<td>{num(f["verdad"][75])}</td><td>{num(m75)}</td>'
                             f'<td>{num(f["verdad"][150])}</td><td>{num(m150)}</td><td>{pct(error)}</td></tr>')
        lecturas = []
        for lado in LADOS:
            lec = RM.lectura_vasoconstrictor(
                ((self.res['reposo'][lado] or {}).get('lecturas', {}).get(150, {}).get('insp') or {}).get('R'),
                ((self.res['vc'][lado] or {}).get('lecturas', {}).get(150, {}).get('insp') or {}).get('R'))
            if lec:
                lecturas.append(f'<li>{SIGLA[lado]}: {lec["texto"]} ({pct(lec["cambio"])}).</li>')
        perf = self.sesion.paciente.get('perforacion', {})
        aviso_perf = (f'<p><b>Perforación septal</b> de {num(perf["area"])} cm² a {num(perf["pos"])} cm: '
                      'el tubo de presión no lee la rinofaringe, la técnica anterior no es válida.</p>'
                      if perf.get('area', 0) > 0 else '')
        tabla = ('<table cellpadding="4"><tr><th>Fosa</th><th>Estado</th><th>Congestión</th>'
                 '<th>R 75 verdadera</th><th>R 75 medida</th><th>R 150 verdadera</th>'
                 '<th>R 150 medida</th><th>Error</th></tr>'
                 + (''.join(filas) or '<tr><td colspan="8">Sin mediciones.</td></tr>') + '</table>')
        umbral = pct(RM.UMBRAL_SIN_CAMBIO).replace('+', '±')
        texto_lect = (f'<p>Lectura según la tabla de H26 (umbral de "sin cambio": {umbral}, criterio '
                      f'del simulador a partir de {HILBERG_1989["texto"].split(":")[0]}):</p>'
                      f'<ul>{"".join(lecturas)}</ul>') if lecturas else ''
        vc = texto_vc(self.sesion)
        vc = f'<p>{vc}. Lo medido antes de que haga efecto sale como en reposo.</p>' if vc else ''
        return (f'<p>Minuto {self.sesion.minuto()} del ciclo nasal.</p>{vc}{aviso_perf}{tabla}{texto_lect}')


def texto_vc(sesion):
    """'VC FND: faltan 12:04 · VC FNI: en acción', o '' sin vasoconstrictor."""
    partes = []
    for lado in LADOS:
        falta = sesion.falta_vc(lado)
        if falta is None:
            continue
        cuando = 'en acción' if falta == 0 else f'faltan {int(falta // 60)}:{int(falta % 60):02d}'
        partes.append(f'VC {SIGLA[lado]}: {cuando}')
    return ' · '.join(partes)


def r150(f):
    """Resistencia inspiratoria a 150 Pa de una fosa medida, o None."""
    return ((f or {}).get('lecturas', {}).get(150, {}).get('insp') or {}).get('R')


def series_con_datos(res):
    return any(res[f][l] for f in ('reposo', 'vc') for l in LADOS)


class Baremo(QWidget):
    """Una barra con tres zonas (verde, ámbar, roja) y una marca en el valor:
    de un vistazo, si la variación entre pulsos está dentro de lo esperable."""

    def __init__(self, titulo, verde, ambar, tope, ayuda):
        super().__init__()
        self.titulo, self.verde, self.ambar, self.tope = titulo, verde, ambar, tope
        self.valor = None
        self.setToolTip(ayuda)
        self.setMinimumSize(150, 40)

    def poner(self, valor):
        self.valor = valor
        self.update()

    def zona(self):
        if self.valor is None:
            return None
        return 'ok' if self.valor <= self.verde else 'aviso' if self.valor <= self.ambar else 'fuera'

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        texto = '—' if self.valor is None else f'± {num(self.valor, 1)} %'
        color = {'ok': tema.OK, 'aviso': tema.AVISO, 'fuera': tema.ALERTA}.get(self.zona(), tema.TEXTO_SUAVE)
        p.setPen(QColor(tema.TEXTO_SUAVE))
        p.drawText(0, 0, w, 18, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), self.titulo)
        p.setPen(QColor(color))
        p.drawText(0, 0, w, 18, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), texto)
        y, h = 24, 8
        x = 0
        for hasta, c in ((self.verde, tema.OK), (self.ambar, tema.AVISO), (self.tope, tema.ALERTA)):
            fin = w * hasta / self.tope
            relleno = QColor(c)
            relleno.setAlphaF(0.35)
            p.fillRect(int(x), y, int(fin - x), h, relleno)
            x = fin
        if self.valor is not None:
            mx = int(min(w - 2, w * self.valor / self.tope))
            p.fillRect(mx - 1, y - 4, 3, h + 8, QColor(tema.TEXTO))
        p.end()


class RinometriaWindow(EquipoNasal):
    """La rinometría acústica como se ve en el equipo: Iniciar y manda un
    pulso tras otro. Cada pulso se dibuja lento, de izquierda a derecha;
    adelante los pulsos caen casi encima, atrás se mueven mucho. Sobre ellos,
    tres curvas: el promedio de los últimos pulsos y sus límites (promedio ±
    2 DE), que se mueven con lo que va midiendo, y abajo los baremos del
    ancho de la banda. El alumno detiene cuando la banda queda angosta
    (paciente en apnea, adaptador sellado): el promedio queda como un
    registro. Tres registros por fosa; si se toman más, quedan los tres
    últimos.

    Cada pulso sale del modelo con el estado de la nariz y los errores de
    ese momento (rinometria.pulso). Lo que se ve en vivo no se guarda: solo
    la receta de los pulsos de cada registro, que basta para rehacerlo al
    retomar la atención."""

    TITULO = 'Rinometría acústica'
    EQUIPO = 'ra'
    TIPO = 'RINOMETRIA'
    FUNCION = staticmethod(RA.rehace_fosa)
    TIC_MS = 40
    PASOS_PULSO = 20           # tics que tarda un pulso en cruzar la pantalla (0,8 s)
    # Los baremos, en % del promedio (semiancho de la banda): verde, ámbar, tope.
    BAREMOS = (('mca1', 'Banda en MCA1', 4, 8, 16),
               ('mca2', 'Banda en MCA2', 4, 8, 16),
               ('banda05', 'Banda 0-5 cm', 4, 8, 16))

    def __init__(self, data_login=None, parent=None):
        self.vivo = None
        self.marcas = {}
        super().__init__(data_login, parent)
        self.timer = QTimer(self)
        self.timer.setInterval(self.TIC_MS)
        self.timer.timeout.connect(self._tic)

    def _graficos_informe(self):
        return [('ra_curva', self.g_curva)]

    def _avisos_informe(self):
        """El cambio con vasoconstrictor va como línea: el PDF lleva una tabla."""
        contenido = getattr(self.tabla_vc, 'contenido', None)
        if not contenido or not contenido['filas']:
            return []
        cab = contenido['cabeceras'][1:]
        return [f'Cambio con vasoconstrictor {fila[0]}: '
                + ', '.join(f'{c} {v}' for c, v in zip(cab, fila[1:])) for fila in contenido['filas']]

    def _extra_informe(self):
        return {'calibrado': self.calibrado}

    def _restaurar_extra(self, data):
        self.calibrado = bool(data.get('calibrado')) or bool(data.get('mediciones'))
        for m in data.get('mediciones') or []:
            marcas = (m.get('opciones') or {}).get('marcas') if isinstance(m, dict) else None
            if marcas and m.get('lado') in LADOS and m.get('fase') in ('reposo', 'vc'):
                self.marcas[(m['fase'], m['lado'])] = dict(marcas)
                self.marcando = (m['fase'], m['lado'])

    INDICACION = ('Calibra con el tubo calibrador y mide cada fosa, primero la derecha: Iniciar, '
                  'el paciente en apnea, y Detener cuando la banda quede angosta. Tres registros '
                  'por fosa.')

    calibrado = False
    marcando = None            # (fase, lado) de la curva que lleva los cursores

    def _botones(self, caja):
        self.btn_calibrar = caja.agregar(self._boton('Calibrar', self._calibrar))
        self.btn_d = caja.agregar(self._boton('Iniciar FND', lambda: self._medir('D'), True))
        self.btn_i = caja.agregar(self._boton('Iniciar FNI', lambda: self._medir('I'), True))
        self.btn_vc = caja.agregar(self._boton('Aplicar vasoconstrictor', self._vasoconstrictor))

    def _errores(self, caja):
        self.chk_err = {}
        for clave, texto in (('fuga', 'Fuga en el adaptador'), ('aprieta', 'Adaptador que aprieta la narina'),
                             ('respira', 'Respira o traga en el registro')):
            self.chk_err[clave] = caja.agregar(QCheckBox(texto))
            self._log_error_simulado(self.chk_err[clave], clave)

    def _opciones(self, caja):
        caja.agregar(etiqueta('Cursores MCA1 y MCA2 en', rol='campo'))
        self.cmb_marcar = caja.agregar(QComboBox())
        self.cmb_marcar.activated.connect(self._elegir_marcar)
        ayuda = etiqueta('Arrastra cada cursor hasta su valle: el equipo lee el área donde lo '
                         'dejes.', rol='hint')
        ayuda.setWordWrap(True)
        caja.agregar(ayuda)
        self.chk_log = caja.agregar(self._check('Área en escala logarítmica', self.dibujar, True))
        self.chk_registros = caja.agregar(self._check('Ver los tres registros', self.dibujar, True))
        self.chk_verdad = None
        if self.es_docente:
            self.chk_verdad = caja.agregar(self._check('Área verdadera (docente)', self.dibujar))

    def _pantalla(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        self.g_curva = GraficoRinometria()
        caja_curva = Tarjeta('Área-distancia')
        caja_curva.agregar(self.g_curva.widget, 1)
        fila = QHBoxLayout()
        fila.setSpacing(16)
        ayuda = (f'Semiancho de la banda (promedio ± {RA.DE_LIMITES} DE de los últimos '
                 f'{RA.VENTANA_PULSOS} pulsos), en % del promedio. Verde hasta 4 %: un coeficiente '
                 'de variación del 2 % (Hilberg y cols., 1989); ámbar hasta 8 %.')
        self.baremos = {}
        for clave, titulo, verde, ambar, tope in self.BAREMOS:
            self.baremos[clave] = Baremo(titulo, verde, ambar, tope, ayuda)
            fila.addWidget(self.baremos[clave], 1)
        self.lbl_pulsos = etiqueta('', rol='hint')
        self.lbl_pulsos.setMinimumWidth(110)
        fila.addWidget(self.lbl_pulsos)
        contenedor_baremos = QWidget()
        contenedor_baremos.setLayout(fila)
        caja_curva.agregar(contenedor_baremos)
        caja, self.tabla, self.pie, self.avisos = self._bloque_tabla('Resultados')
        self.tabla_vc = Tabla()
        self.resultados.insertWidget(1, self.tabla_vc)
        caja_curva.setMinimumHeight(300)
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(caja_curva)
        vertical.addWidget(caja)
        vertical.setStretchFactor(0, 3)
        vertical.setStretchFactor(1, 1)
        layout.addWidget(vertical)
        return contenedor

    def la_super(self, data, appointment_id=None):
        self._parar()
        self.marcas = {}
        self.marcando = None
        super().la_super(data, appointment_id)

    def _sin_caso(self, con_paciente=False):
        self._parar()
        self.marcas = {}
        self.marcando = None
        super()._sin_caso(con_paciente)

    def _al_entrar(self):
        self.calibrado = False
        for chk in self.chk_err.values():
            chk.setChecked(False)
        self._poner_baremos(None)

    def _calibrar(self):
        self._log('calibrar')
        self.calibrado = True
        self._mensaje('Equipo calibrado con el tubo calibrador.', 'ok')
        self.dibujar()

    def _medir(self, lado):
        """Iniciar o detener la toma de esa fosa."""
        if self.sesion is None or not self.sesion.hay_paciente:
            return
        if self.vivo is not None:
            if self.vivo['lado'] == lado:
                self._detener()
            return
        if self.midiendo:
            return
        if not self.calibrado:
            self._log('iniciar', lado=lado, rechazado='sin_calibrar')
            self._mensaje('Primero calibra el equipo con el tubo calibrador (H27).', 'alerta')
            return
        self.vivo = {'lado': lado, 'fase': self.sesion.fase(lado),
                     'semilla': self.sesion.semilla_medicion(self.EQUIPO),
                     'k': 0, 'paso': 0, 'actual': None, 'pulsos': [], 'banda': None,
                     'bases': {}}
        self._log('iniciar', lado=lado, fase=self.vivo['fase'], semilla=self.vivo['semilla'],
                  registro=self._n_registros(lado, self.vivo['fase']) + 1, errores=self._errores_puestos())
        self._midiendo(True)
        self._poner_baremos(None)
        self._tic()
        self.timer.start()

    def _errores_puestos(self):
        return {k: True for k, c in self.chk_err.items() if c.isChecked()}

    def _n_registros(self, lado, fase):
        r = self.res[fase][lado]
        return len(r['registros']) if r else 0

    def _tic(self):
        """El pulso en curso avanza de izquierda a derecha; al llegar al
        final entra al promedio y sale el siguiente, con el estado de la
        nariz y los errores de ese momento."""
        v = self.vivo
        if v is None:
            return
        if v['paso'] == 0:
            estado, errores = self.sesion.estado(v['lado']), self._errores_puestos()
            receta = {'k': v['k'], 'estado': dict(estado), 'errores': errores}
            clave = (repr(sorted(estado.items())), tuple(sorted(errores)))
            if clave not in v['bases']:
                v['bases'] = {clave: RA.curva_del_equipo(self.sesion.paciente, v['lado'], estado, errores)}
            v['actual'] = (RA.pulso(self.sesion.paciente, v['lado'], v['semilla'], receta, v['bases'][clave]),
                           receta)
            v['k'] += 1
        v['paso'] += 1
        curva = v['actual'][0]
        hasta = max(2, round(len(curva['x']) * v['paso'] / self.PASOS_PULSO))
        self.g_curva.en_vivo({'x': curva['x'][:hasta], 'A': curva['A'][:hasta]}, v['banda'], v['lado'])
        if v['paso'] < self.PASOS_PULSO:
            return
        v['paso'] = 0
        v['pulsos'] = (v['pulsos'] + [v['actual']])[-RA.VENTANA_PULSOS:]
        b = RA.banda([c for c, _ in v['pulsos']])
        b['medidas'] = RA.medidas(b['x'], b['A'])
        v['banda'] = b
        self._poner_baremos(b)
        m = b['medidas']
        n = self._n_registros(v['lado'], v['fase']) + 1
        self._mensaje(f'{SIGLA[v["lado"]]} en vivo · registro {min(n, RA.REGISTROS_PROTOCOLO)} de '
                      f'{RA.REGISTROS_PROTOCOLO} · MCA1 {num(m["mca1"])} cm² · MCA2 {num(m["mca2"])} cm². '
                      'Detén cuando la banda quede angosta.')

    def _poner_baremos(self, b):
        q = RA.calidad(b, b['medidas']) if b is not None else {}
        for clave, baremo in self.baremos.items():
            baremo.poner(q.get(clave))
        self.lbl_pulsos.setText('' if b is None else
                                f'{b["n"]} de {RA.VENTANA_PULSOS} pulsos')
        return q

    def _detener(self):
        """El promedio de los pulsos de la ventana queda como registro (el que
        va por la mitad no cuenta); de la fosa quedan los tres últimos."""
        v, self.vivo = self.vivo, None
        self.timer.stop()
        self._midiendo(False)
        lado, fase = v['lado'], v['fase']
        if v['banda'] is None:
            self._log('detener', lado=lado, fase=fase, pulsos=0)
            self._mensaje('Detenido antes de terminar el primer pulso: no queda registro.', 'alerta')
            self.dibujar()
            return
        previa = next((m for m in self.mediciones if (m['lado'], m['fase']) == (lado, fase)), None)
        antes = self.res[fase][lado]
        tomados = list(zip(antes['registros'], previa['opciones'].get('registros') or [])) \
            if antes and previa else []
        toma = {'semilla': v['semilla'], 'pulsos': [rc for _, rc in v['pulsos']]}
        tomados = (tomados + [(v['banda'], toma)])[-RA.REGISTROS_PROTOCOLO:]
        estado = toma['pulsos'][-1]['estado']
        marcas = self.marcas.setdefault((fase, lado), self._cursores_iniciales(v['semilla']))
        self.marcando = (fase, lado)
        r = RA.fosa(self.sesion.paciente, lado, estado, [c for c, _ in tomados], RA.REGISTROS_PROTOCOLO,
                    marcas)
        receta = {'lado': lado, 'fase': fase, 'estado': dict(estado),
                  'opciones': {'registros': [t for _, t in tomados], 'marcas': dict(marcas)}}
        self.res[fase][lado] = r
        self.mediciones = [m for m in self.mediciones if (m['lado'], m['fase']) != (lado, fase)] + [receta]
        self._registrar_medicion(lado, fase, r, receta, pulsos=v['k'],
                                 calidad=RA.calidad(v['banda'], v['banda']['medidas']))
        self._al_medir(lado, r)
        self.dibujar()

    @staticmethod
    def _cursores_iniciales(semilla):
        """Dónde aparecen los cursores la primera vez: al azar (con la semilla
        de la toma), no en los valles; ponerlos es del evaluador."""
        r = generador(f'ra-cursores/{semilla}')
        d1 = r.entre(0.5, 2.5)
        d2 = min(5.5, d1 + r.entre(0.8, 2.5))
        return {'d1': round(round(d1 / modelo.DX) * modelo.DX, 4), 'd2': round(round(d2 / modelo.DX) * modelo.DX, 4)}

    def _elegir_marcar(self, _i=None):
        # El dato va como texto "fase:lado": findData no reconoce tuplas.
        dato = self.cmb_marcar.currentData()
        self.marcando = tuple(dato.split(':')) if dato else None
        self.dibujar()

    def _poblar_marcar(self):
        self.cmb_marcar.blockSignals(True)
        self.cmb_marcar.clear()
        for fase, nombre in (('reposo', 'reposo'), ('vc', 'con VC')):
            for lado in LADOS:
                if self.res[fase][lado] and (fase, lado) in self.marcas:
                    self.cmb_marcar.addItem(f'{SIGLA[lado]} {nombre}', f'{fase}:{lado}')
        i = self.cmb_marcar.findData(':'.join(self.marcando)) if self.marcando else -1
        if i < 0 and self.cmb_marcar.count():
            i = self.cmb_marcar.count() - 1
            self.marcando = tuple(self.cmb_marcar.itemData(i).split(':'))
        self.cmb_marcar.setCurrentIndex(i)
        self.cmb_marcar.setEnabled(self.cmb_marcar.count() > 0)
        self.cmb_marcar.blockSignals(False)

    def _soltar_cursor(self, cual, d):
        # Fuera de la señal del cursor: dibujar() borra el gráfico, cursor incluido.
        QTimer.singleShot(0, lambda: self._mover_cursor(cual, d))

    def _mover_cursor(self, cual, d):
        """El evaluador soltó un cursor: la fosa se vuelve a leer ahí."""
        if self.marcando is None or self.sesion is None or not self.sesion.hay_paciente:
            return
        fase, lado = self.marcando
        f = self.res[fase][lado]
        if not f:
            return
        marcas = self.marcas[(fase, lado)]
        marcas['d1' if cual == 'mca1' else 'd2'] = d
        r = RA.fosa(self.sesion.paciente, lado, f['estado'], f['registros'], RA.REGISTROS_PROTOCOLO, marcas)
        self.res[fase][lado] = r
        for m in self.mediciones:
            if (m['lado'], m['fase']) == (lado, fase):
                m['opciones']['marcas'] = dict(marcas)
        verdad = r['verdad']['medidas']
        self._log('marcar', lado=lado, fase=fase, cursor=cual, dist=d, area=r['promedio'][cual],
                  valle_dist=r['auto']['dist1' if cual == 'mca1' else 'dist2'], valle_area=r['auto'][cual],
                  verdad_dist=verdad['dist1' if cual == 'mca1' else 'dist2'], verdad_area=verdad[cual])
        self.dibujar()

    def _parar(self):
        """Cambió la atención: lo que estaba en vivo no se guarda."""
        if getattr(self, 'timer', None) is not None:
            self.timer.stop()
        if self.vivo is not None:
            self._log('cancelar', lado=self.vivo['lado'], pulsos=self.vivo['k'])
            self.vivo = None
            self._midiendo(False)

    def _midiendo(self, si):
        """En vivo, el botón de la fosa que se mide es el de detener; lo
        demás espera."""
        super()._midiendo(si)
        self.btn_calibrar.setEnabled(not si)
        for lado, b in (('D', self.btn_d), ('I', self.btn_i)):
            mide = self.vivo is not None and self.vivo['lado'] == lado
            b.setText('Detener' if mide else f'Iniciar {SIGLA[lado]}')
            if mide:
                b.setEnabled(True)

    def _al_medir(self, lado, r):
        vc = ', con vasoconstrictor' if self.sesion.fase(lado) == 'vc' else ''
        n = len(r['registros'])
        if n < RA.REGISTROS_PROTOCOLO:
            self._mensaje(f'{SIGLA[lado]}{vc}: registro {n} de {RA.REGISTROS_PROTOCOLO} guardado. Inicia '
                          'el siguiente.', 'ok')
        elif r['repetible']:
            self._mensaje(f'{SIGLA[lado]}{vc}: tres registros en apnea. Se parecen entre sí.', 'ok')
        else:
            self._mensaje(f'{SIGLA[lado]}{vc}: tres registros en apnea. No se parecen donde están los '
                          'cursores: revisa los cursores y, si siguen sin parecerse, repite (quedan los '
                          'tres últimos).', 'alerta')

    def _dibujar_equipo(self):
        self._poblar_marcar()
        f = self.res[self.marcando[0]][self.marcando[1]] if self.marcando else None
        marca = f is not None and self.vivo is None and self.marcando in self.marcas
        self.g_curva.dibujar(self._series(), log=self.chk_log.isChecked(),
                             registros=self.chk_registros.isChecked(),
                             verdad=bool(self.chk_verdad and self.chk_verdad.isChecked()),
                             sin_rotulo=(self.marcando[1], self.marcando[0] == 'vc') if marca else None)
        if marca:
            media = curva_media(f)
            self.g_curva.cursores({'x': [x for x, _ in media], 'A': [a for _, a in media]},
                                  self.marcas[self.marcando], self.marcando[1], self._soltar_cursor)
        self._tabla()
        avisos = self._lista_avisos()
        if self.sesion and self.sesion.hay_paciente and not self.calibrado:
            avisos = '• Equipo sin calibrar.' + ('\n' + avisos if avisos else '')
        self.avisos.setText(avisos)

    def _registrar_medicion(self, lado, fase, r, receta, pulsos=None, calidad=None):
        toma = receta['opciones']['registros'][-1]
        errores = sorted({e for rc in toma['pulsos'] for e in rc['errores']})
        self._log('registro', lado=lado, fase=fase, vc_activo=bool(receta['estado'].get('vc')),
                  errores=errores, semilla=toma['semilla'], pulsos=pulsos,
                  promediados=len(toma['pulsos']), calidad=calidad,
                  registros=len(r['registros']),
                  registro={c: r['registros'][-1]['medidas'][c] for c in RA.PARAMETROS},
                  medido={c: r['promedio'][c] for c in RA.PARAMETROS},
                  valle=r.get('auto'), marcas=r.get('marcas'), cv=r.get('cv'),
                  verdad=RA.parametros(r['verdad']['x'], r['verdad']['A']),
                  repetible=r['repetible'], avisos=r['avisos'])

    def _celdas(self, m):
        return [num(m.get(c)) for c in RA.PARAMETROS]

    def _tabla(self):
        if not series_con_datos(self.res):
            self.tabla.poblar([], [])
            self.tabla_vc.poblar([], [])
            self.tabla_vc.setVisible(False)
            self.pie.setText('')
            return
        # Cabeceras cortas: el PDF reparte el ancho por igual entre columnas.
        cab = ['', 'D1', 'MCA1', 'D2', 'MCA2', 'V1', 'V0-2', 'V0-5', 'V2-5', 'V0-7', 'CV MCA1', 'CV MCA2',
               f'≤ {num(PROTOCOLO_REPETICION["valor"])}']
        col_criterio = len(cab) - 1
        filas = []
        for nombre, fase in (('reposo', 'reposo'), ('con VC', 'vc')):
            for lado in LADOS:
                f = self.res[fase][lado]
                if not f:
                    continue
                for k, r in enumerate(f['registros'] if self.chk_registros.isChecked() else []):
                    filas.append(([f'{SIGLA[lado]} {nombre} · registro {k + 1}'] + self._celdas(r['medidas'])
                                  + ['', '', ''], lado, {}))
                n = len(f['registros'])
                if n < RA.REGISTROS_PROTOCOLO:
                    criterio, marca = f'{n} de {RA.REGISTROS_PROTOCOLO}', {}
                else:
                    criterio = 'sí' if f['repetible'] else 'no'
                    marca = {col_criterio: 'ok' if f['repetible'] else 'fuera'}
                cv = f.get('cv') or {}
                filas.append(([f'{SIGLA[lado]} {nombre} · promedio'] + self._celdas(f['promedio'])
                              + [pct_o_raya(cv.get('mca1')), pct_o_raya(cv.get('mca2')), criterio],
                              lado, marca))
            d, i = self.res[fase]['D'], self.res[fase]['I']
            if d and i:
                # La nariz entera: la suma de las dos fosas (las distancias no se suman).
                total = {c: None if c.startswith('dist') else
                         (d['promedio'].get(c) or 0) + (i['promedio'].get(c) or 0) for c in RA.PARAMETROS}
                filas.append(([f'Nariz {nombre} (D + I)'] + self._celdas(total) + ['', '', ''], None, {}))
        filas.append((['Normal del modelo (no es norma)'] + self._celdas(normal_modelo()) + ['', '', ''],
                      None, {}))
        self.tabla.poblar(cab, filas)
        self.pie.setText('D1, D2: distancia de la narina a cada cursor (cm). MCA1, MCA2: área donde '
                         'está cada cursor (cm²). Volúmenes en cm³: V1 de la narina a MCA2; V0-2 el '
                         'vestíbulo y la válvula; V0-5 el «Vol 2» del libro; V2-5 el de los cambios de '
                         'la mucosa; V0-7 la fosa entera, pasada la zona confiable. CV: coeficiente de '
                         'variación entre los registros (%). Nariz: suma de las dos fosas. Última '
                         f'columna: {PROTOCOLO_REPETICION["texto"]} {RINOMETRIA_SIN_NORMA} '
                         f'{HILBERG_1989["texto"]}')

        cambios = []
        for lado in LADOS:
            a, b = self.res['reposo'][lado], self.res['vc'][lado]
            if a and b:
                pa, pb = a['promedio'], b['promedio']
                cambios.append(([SIGLA[lado]] + [pct((pb[k] - pa[k]) / pa[k]) if pa.get(k) and pb.get(k) is not None
                                                 else '—' for k in ('mca1', 'mca2', 'vol05', 'vol25', 'vol07')],
                                lado, {}))
        self.tabla_vc.setVisible(bool(cambios))
        if cambios:
            self.tabla_vc.poblar(['Cambio con vasoconstrictor', 'MCA1', 'MCA2', 'V0-5', 'V2-5', 'V0-7'], cambios)
            self.pie.setText(self.pie.text() + ' ' + COREY_1997['texto'])

    def _texto_verdad(self):
        filas = []
        for nombre, fase in (('Reposo', 'reposo'), ('Con VC', 'vc')):
            for lado in LADOS:
                f = self.res[fase][lado]
                if not f:
                    continue
                v, m, auto = f['verdad']['medidas'], f['promedio'], f.get('auto') or f['promedio']

                def celda(c, dist):
                    return (f'{num(v[c])} a {num(v[dist])} cm · valle {num(auto[c])} a {num(auto[dist])} '
                            f'· marcada {num(m[c])} a {num(m[dist])}')
                filas.append(f'<tr><td>{SIGLA[lado]}</td><td>{nombre}</td>'
                             f'<td>{celda("mca1", "dist1")}</td><td>{celda("mca2", "dist2")}</td>'
                             f'<td>{num(v["vol05"])} (medida {num(m["vol05"])})</td></tr>')
        return ('<p>En el gráfico, "Área verdadera" dibuja en puntos el área de cada fosa. La curva '
                'del equipo se aparta de ella detrás de un estrechamiento marcado, pasados ~5 cm '
                '(senos y rinofaringe), con perforación y con los errores de técnica.</p>'
                '<p>MCA1 y MCA2: la verdadera (cm², cm), el valle de la curva del equipo y dónde '
                'dejó los cursores el evaluador.</p>'
                '<table cellpadding="4"><tr><th>Fosa</th><th>Estado</th><th>MCA1</th>'
                '<th>MCA2</th><th>Vol 0-5 verdadero</th></tr>'
                + (''.join(filas) or '<tr><td colspan="5">Sin mediciones.</td></tr>') + '</table>'
                f'<p>Minuto {self.sesion.minuto()} del ciclo nasal.</p>')


_normal = None


def normal_modelo():
    """La fosa normal del modelo, para comparar: orden de magnitud, no norma."""
    global _normal
    if _normal is None:
        n = RA.I_CURVA + 1
        p = modelo.paciente('normal')
        _normal = RA.parametros(modelo.REJILLA[:n], modelo.perfil(p, 'D', {})[:n])
    return _normal
