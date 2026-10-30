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
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QFrame, QHBoxLayout, QHeaderView,
                               QMainWindow, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox,
                               QSplitter, QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

import os
import time

from core import hilos, tema
from core.base import context
from core.estado_informe import EstadoInforme
from nasal import modelo, sesion
from nasal import rinomanometria as RM
from nasal import rinometria as RA
from nasal.graficos import (GraficoResistencia, GraficoRinometria, GraficoRinomanometria,
                            GraficoTiempo)
from nasal.paciente_rm import PacienteRM
from nasal.referencias import (COREY_1997, HILBERG_1989, PROTOCOLO_REPETICION,
                               REFERENCIA_UNILATERAL_150, REN_2018, RINOMETRIA_SIN_NORMA,
                               VOGT_2016)
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta

SIGLA = modelo.SIGLA_LADO
LADOS = modelo.LADOS
NARINA = {'D': 'derecha', 'I': 'izquierda'}
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

    def __init__(self, data_login=None, parent=None):
        super().__init__(parent)
        self.data_login = data_login or {}
        self.es_docente = self.data_login.get('permission') in PERMISOS_DOCENTE
        self.setWindowTitle(self.TITULO)
        self.sesion = None
        self.res = _vacio()
        self._construir()
        self._sin_caso()

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
        caja = Tarjeta()
        caja.cuerpo.setContentsMargins(14, 10, 14, 10)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.lbl_paciente = etiqueta('Sin atención abierta', rol='titulo')
        fila.addWidget(self.lbl_paciente)
        self.pill_estado = Pastilla('reposo', 'neutro')
        fila.addWidget(self.pill_estado)
        self.pill_minuto = Pastilla('', 'neutro')
        fila.addWidget(self.pill_minuto)
        fila.addStretch(1)
        caja.agregar_layout(fila)
        self.lbl_mensaje = etiqueta('', rol='hint')
        self.lbl_mensaje.setWordWrap(True)
        caja.agregar(self.lbl_mensaje)
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
        self.lbl_paciente.setText(descripcion_paciente(data))
        self._al_entrar()
        self._mensaje(self.INDICACION)
        self.dibujar()

    def _sin_caso(self, con_paciente=False):
        for panel in self._paneles():
            panel.setEnabled(False)
        self.lbl_paciente.setText('Sin atención abierta')
        self.pill_minuto.set('')
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
            'vasoconstrictor': self.sesion.vc,
            'tabla': getattr(self.tabla, 'contenido', {}),
            'avisos': avisos + self._avisos_informe(),
            'hallazgos': self.txt_hallazgos.toPlainText(),
            'conclusion': self.txt_conclusion.toPlainText(),
        }
        data.update(self._extra_informe())
        return {'appointment_id': appointment_id, 'tipo': self.TIPO, 'data': data,
                'images': self._exportar_imagenes}

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
        if data.get('vasoconstrictor'):
            self.sesion.aplicar_vasoconstrictor()
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

    def _mensaje(self, texto, estado=None):
        self.lbl_mensaje.setText(texto)
        color = {'alerta': tema.ALERTA, 'ok': tema.OK}.get(estado, tema.TEXTO_SUAVE)
        self.lbl_mensaje.setStyleSheet(f'color: {color};')

    def _refrescar_encabezado(self):
        if self.sesion is None or not self.sesion.hay_paciente:
            self.pill_estado.set('—', 'neutro')
            return
        self.pill_estado.set('con vasoconstrictor' if self.sesion.vc else 'reposo',
                             'acento' if self.sesion.vc else 'neutro')
        self.pill_minuto.set(f'minuto {self.sesion.minuto()} del ciclo' if self.es_docente else '')
        self.btn_vc.setEnabled(not self.sesion.vc and not self.midiendo)

    def _vasoconstrictor(self):
        self.sesion.aplicar_vasoconstrictor()
        self._mensaje('Vasoconstrictor aplicado en las dos fosas (se dan por pasados los 15 '
                      'minutos de espera). Lo que midas ahora es "con VC". El vasoconstrictor '
                      'retira la mucosa y apaga el ciclo; no toca lo estructural.')
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
        sesion_de_la_medicion, fase = self.sesion, self.sesion.fase()
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
    """La rinomanometría como se hace: el alumno pone el adaptador con el
    tubo de presión en una narina y la máscara (en la ventanita del
    paciente), registra, y en la pantalla corren la presión y el flujo
    mientras el paciente respira; cada ciclo completo se suma al lazo
    presión-flujo. Mientras registra le da indicaciones al paciente (que
    cierre la boca, que respire parejo, que tome aire fuerte), que se notan
    desde la respiración siguiente. Al detener, el equipo promedia los
    últimos ciclos completos.

    Cada ciclo sale del modelo con lo que hacía el paciente en ese momento
    (rinomanometria.Registro): un registro sin cambios es mide_fosa, y la
    receta (la condición de cada ciclo y la semilla) basta para rehacerlo
    al retomar la atención."""

    TITULO = 'Rinomanometría anterior'
    EQUIPO = 'rm'
    TIPO = 'RINOMANOMETRIA'
    FUNCION = staticmethod(RM.mide_registro)
    INDICACION = ('Pon el adaptador con el tubo de presión en una narina (clic en la narina del '
                  'paciente) y después la máscara, y registra: se mide la fosa contraria. Primero '
                  'la derecha, con el adaptador en la izquierda.')

    # Segundos por ciclo respiratorio, tranquila y forzada. Del simulador.
    DURACION = {False: 4.0, True: 3.2}
    MIN_CICLOS = 3
    MAX_CICLOS = 20            # el registro se detiene solo
    TIC_MS = 40
    GUARDA_S = 20              # lo que se guarda de los trazos en el tiempo

    INDICACIONES = (
        ('tranquila', 'Respire tranquilo por la nariz'),
        ('boca', 'Cierre bien la boca'),
        ('parejo', 'Respire parejo, sin tragar ni hablar'),
        ('fuerte', 'Tome aire fuerte por la nariz'),
    )

    reg = None                 # el registro en curso (rinomanometria.Registro)
    preparando = False
    sonda = None               # narina con el adaptador
    mascara = False
    forzada = False

    def __init__(self, data_login=None, parent=None):
        self._reloj = time.monotonic
        self._redes_pedidas = set()
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
        izq.addWidget(self.panel_paciente)

        self.panel_indicaciones = Tarjeta('Indicaciones al paciente')
        for clave, texto in self.INDICACIONES:
            b = self._boton(f'«{texto}»', lambda _c=False, k=clave: self._indicar(k))
            b.setStyleSheet('text-align: left;')
            self.panel_indicaciones.agregar(b)
        izq.addWidget(self.panel_indicaciones)
        self._paneles_comunes(izq)

    def _paneles(self):
        return [self.panel_paciente, self.panel_indicaciones, self.panel_examen,
                self.panel_errores, self.panel_vista]

    def _errores(self, caja):
        self.chk_err = {}
        for clave, texto in (('mascara', 'Fuga en la máscara'), ('adaptador', 'Adaptador sin sellar'),
                             ('boca', 'Respira por la boca'), ('irregular', 'Respiración irregular')):
            self.chk_err[clave] = caja.agregar(self._check(texto, self._sync_paciente))

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
        self.btn_registro = self._boton('Iniciar registro', self._registro, True)
        self.btn_registro.setMinimumWidth(130)
        self.btn_vc = self._boton('Vasoconstrictor', self._vasoconstrictor)
        self.btn_vc.setToolTip('Aplicar vasoconstrictor en las dos fosas')
        campos = Campos()
        self.spin_ciclos = QSpinBox()
        self.spin_ciclos.setRange(3, 5)
        self.spin_ciclos.setValue(4)
        self.spin_ciclos.setToolTip('Cuántos ciclos completos promedia al detener')
        campos.agregar('Ciclos', self.spin_ciclos)
        self.pill_registro = Pastilla('', 'neutro')
        for w in (self.btn_sello, self.btn_registro, campos, self.btn_vc):
            fila.addWidget(w)
        fila.addStretch(1)
        fila.addWidget(self.pill_registro)
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
        self._cortar()
        super().la_super(data, appointment_id)
        self._sync_paciente()

    def _sin_caso(self, con_paciente=False):
        self._cortar()
        super()._sin_caso(con_paciente)
        if hasattr(self, 'vista_paciente'):
            self._sync_paciente()

    def _al_entrar(self):
        self.sonda = None
        self.mascara = False
        self.forzada = False
        for chk in self.chk_err.values():
            chk.setChecked(False)

    def _registrando(self):
        return self.reg is not None

    def _poner_sonda(self, lado):
        if self._registrando():
            self._mensaje('Detén el registro antes de cambiar el adaptador.', 'alerta')
            return
        if self.mascara:
            self._mensaje('Saca la máscara para cambiar el adaptador de narina.', 'alerta')
            return
        self.sonda = lado
        self.chk_err['adaptador'].setChecked(False)
        otro = 'I' if lado == 'D' else 'D'
        self._mensaje(f'Adaptador con el tubo de presión en la narina {NARINA[lado]}: se mide la '
                      f'{SIGLA[otro]}. Comprueba que selle y pon la máscara.')
        self._sync_paciente()

    def _mascara(self):
        if self._registrando():
            self._mensaje('Detén el registro antes de sacar la máscara.', 'alerta')
            return
        self.mascara = not self.mascara
        self.chk_err['mascara'].setChecked(False)
        if self.mascara and not self.sonda:
            self._mensaje('Máscara puesta, pero sin adaptador en ninguna narina: no hay de dónde '
                          'leer la presión.', 'alerta')
        else:
            self._mensaje('Máscara puesta, apoyada en toda la cara.' if self.mascara else 'Máscara fuera.')
        self._sync_paciente()

    def _acomodar(self):
        self.chk_err['mascara'].setChecked(False)
        self._mensaje('Acomodas la máscara y la apoyas pareja contra la cara.')
        self._sync_paciente()

    def _indicar(self, clave):
        texto = dict(self.INDICACIONES)[clave]
        if clave == 'tranquila':
            self.forzada = False
        elif clave == 'boca':
            self.chk_err['boca'].setChecked(False)
        elif clave == 'parejo':
            self.chk_err['irregular'].setChecked(False)
        elif clave == 'fuerte':
            self.forzada = True
        cuando = ' Se nota desde la respiración siguiente.' if self._registrando() else ''
        self._mensaje(f'Le dices al paciente: «{texto}».{cuando}')
        self._sync_paciente()
        if self._registrando():
            self._pedir_red(*self._condicion())

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
            otro = 'I' if self.sonda == 'D' else 'D'
            self.lbl_sonda.setText(f'Adaptador en la narina {NARINA[self.sonda]} · se mide la '
                                   f'{SIGLA[otro]}. Respira {"fuerte" if self.forzada else "tranquilo"}.')
        else:
            self.lbl_sonda.setText('Sin adaptador: clic en una narina para ponerlo.')

    def _condicion(self):
        """Lo que hace el paciente ahora (y cómo está puesto el equipo)."""
        errores = {k: True for k, c in self.chk_err.items() if c.isChecked()}
        return errores, self.forzada

    # --- El registro ----------------------------------------------------

    def _sello(self):
        if not self.sonda:
            self._mensaje('Primero pon el adaptador en una narina.', 'alerta')
        elif self.chk_err['adaptador'].isChecked():
            self._mensaje('Pasa aire por el adaptador: no sella. El tubo no va a leer la '
                          'rinofaringe. Sácalo y vuelve a ponerlo antes de medir.', 'alerta')
        else:
            self._mensaje('No pasa aire por el adaptador: sella bien.', 'ok')

    def _vasoconstrictor(self):
        if self._registrando() or self.preparando:
            self._mensaje('Detén el registro antes de poner el vasoconstrictor.', 'alerta')
            return
        super()._vasoconstrictor()

    def _registro(self):
        if self._registrando() or self.preparando:
            self._detener()
            return
        if self.sesion is None or not self.sesion.hay_paciente or self.midiendo:
            return
        if not self.sonda:
            self._mensaje('Pon el adaptador con el tubo de presión en una narina (clic en la narina).',
                          'alerta')
            return
        if not self.mascara:
            self._mensaje('Pon la máscara antes de registrar.', 'alerta')
            return
        lado = 'I' if self.sonda == 'D' else 'D'
        self.reg = RM.Registro(self.sesion.paciente, lado, self.sesion.estado(),
                               self.sesion.semilla_medicion(self.EQUIPO))
        self.reg_fase = self.sesion.fase()
        self._redes_pedidas = set()
        self._completos = []
        self._t, self._P, self._V = [], [], []
        self.g_tiempo.limpiar()
        self.preparando = True
        self.btn_registro.setText('Detener')
        self.btn_vc.setEnabled(False)
        self.pill_registro.set(f'{SIGLA[lado]} · preparando', 'acento')
        self._mensaje(f'Registrando la {SIGLA[lado]}: el paciente respira con la máscara puesta.')
        self._pedir_red(*self._condicion(), luego=self._arrancar)
        self.dibujar()

    def _pedir_red(self, errores, forzada, luego=None):
        """La red de esa condición, calculada fuera de la ventana (~1 s)."""
        reg = self.reg
        if reg is None:
            return
        if reg.red(errores, forzada) is not None:
            if luego:
                luego()
            return
        clave = RM.clave_red(errores, forzada)
        if clave in self._redes_pedidas and luego is None:
            return
        self._redes_pedidas.add(clave)

        def listo(red):
            if self.reg is not reg:
                return
            reg.poner_red(errores, forzada, red)
            if luego:
                luego()

        def fallo(exc):
            self._mensaje(f'No se pudo registrar: {exc}', 'alerta')
            self._cortar()

        self.tarea = hilos.en_fondo(reg.calcular_red, errores, forzada, listo=listo, fallo=fallo,
                                    dueno=self, nombre='red rm')

    def _arrancar(self):
        self.preparando = False
        self._t0 = self._reloj()
        self._ciclo_nuevo(0.0)
        self.timer.start()
        self.pill_registro.set(f'{SIGLA[self.reg.lado]} · 0 ciclos', 'acento')

    def _ciclo_nuevo(self, inicio):
        """El ciclo que empieza ahora, con lo que el paciente hace ahora. Si
        lo que cambió todavía no está calculado, respira una vez más como
        venía (y se calcula mientras)."""
        errores, forzada = self._condicion()
        if self.reg.red(errores, forzada) is None:
            self._pedir_red(errores, forzada)
            errores, forzada = self._ultima
        self._ultima = (errores, forzada)
        c = self.reg.siguiente(errores, forzada)
        self._actual = {'c': c, 'ini': inicio, 'dur': self.DURACION[bool(forzada)], 'hechos': 0}

    def _tic(self):
        if self.reg is None or self.preparando:
            return
        ahora = self._reloj() - self._t0
        N = RM.N_CICLO
        while True:
            a = self._actual
            frac = (ahora - a['ini']) / a['dur']
            hasta = max(a['hechos'], min(N, int(frac * N)))
            c = a['c']
            for k in range(a['hechos'], hasta):
                self._t.append(a['ini'] + k * a['dur'] / N)
                self._P.append(c['P'][k])
                self._V.append(c['V'][k])
            a['hechos'] = hasta
            if frac < 1:
                break
            self._completos.append(c)
            lado = self.reg.lado
            self.pill_registro.set(f'{SIGLA[lado]} · {len(self._completos)} ciclos', 'acento')
            if len(self._completos) >= self.MAX_CICLOS:
                self._detener()
                return
            self._ciclo_nuevo(a['ini'] + a['dur'])
            self.dibujar()
        if self._t and self._t[0] < self._t[-1] - self.GUARDA_S:
            corte = next(i for i, t in enumerate(self._t) if t >= self._t[-1] - self.GUARDA_S)
            del self._t[:corte], self._P[:corte], self._V[:corte]
        self.g_tiempo.poner(self._t, self._P, self._V, self.reg.lado)
        a = self._actual
        self.g_curva.actual(a['c']['P'][:a['hechos']], a['c']['V'][:a['hechos']])
        # El vaho en la máscara: aparece al espirar y se va al inspirar.
        v = self.vista_paciente
        flujo = self._V[-1] if self._V else 0
        v.empanado = min(1.0, max(v.empanado * 0.9, -flujo / 450))
        v.update()

    def _detener(self):
        reg, completos = self.reg, list(getattr(self, '_completos', []))
        preparando = self.preparando
        self._cortar(trazos=False)
        if reg is None or preparando:
            self._mensaje('Registro cancelado.')
            self.dibujar()
            return
        if len(completos) < self.MIN_CICLOS:
            self._mensaje(f'Registro detenido con {len(completos)} ciclos completos: hacen falta al '
                          f'menos {self.MIN_CICLOS} para promediar. No se guardó.', 'alerta')
            self.dibujar()
            return
        if len(reg.ciclos) > len(completos):
            reg.descartar_ultimo()
        n = min(self.spin_ciclos.value(), len(completos))
        r = reg.resultado(n)
        lado, fase = reg.lado, self.reg_fase
        self.res[fase][lado] = r
        receta = {'lado': lado, 'fase': fase, 'estado': dict(reg.estado), 'opciones': reg.receta(n)}
        self.mediciones = [m for m in self.mediciones if (m['lado'], m['fase']) != (lado, fase)] + [receta]
        self._al_medir(lado, r)
        self.dibujar()

    def _cortar(self, trazos=True):
        """Corta el registro en curso sin guardar nada."""
        if getattr(self, 'timer', None) is not None:
            self.timer.stop()
        self.reg = None
        self.preparando = False
        if hasattr(self, 'btn_registro'):
            self.btn_registro.setText('Iniciar registro')
            self.pill_registro.set('')
            if trazos:
                self.g_tiempo.limpiar()
            self._refrescar_encabezado()

    def _midiendo(self, si):
        """Al retomar la atención se recalcula lo guardado fuera de la ventana."""
        self.midiendo = si
        for b in (self.btn_registro, self.btn_vc):
            b.setEnabled(not si)
        if not si:
            self._refrescar_encabezado()

    def _refrescar_encabezado(self):
        super()._refrescar_encabezado()
        if self.sesion is not None and self.sesion.hay_paciente:
            self.btn_vc.setEnabled(not self.sesion.vc and not self.midiendo
                                   and not self._registrando() and not self.preparando)

    def _al_medir(self, lado, r):
        siguiente = (' Saca la máscara, cambia el adaptador a la narina derecha y registra la FNI.'
                     if lado == 'D' else '')
        self._mensaje(f'{SIGLA[lado]} {"con vasoconstrictor" if self.sesion.vc else "en reposo"}: '
                      f'promedio de los últimos {len(r["ciclos"])} ciclos.{siguiente}')

    def _dibujar_equipo(self):
        series = self._series()
        broms = self.chk_broms.isChecked()
        vivo = (self.reg.lado, self._completos) if self.reg is not None else None
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
        return (f'<p>Minuto {self.sesion.minuto()} del ciclo nasal.</p>{aviso_perf}{tabla}{texto_lect}')


def descripcion_paciente(data):
    snap = data.get('paciente_snapshot') if isinstance(data.get('paciente_snapshot'), dict) else {}
    nombre = ' '.join(x for x in (snap.get('nombre'), snap.get('apellido')) if x) or 'Paciente'
    edad = data.get('edad')
    return f'{nombre} · {edad} años' if isinstance(edad, (int, float)) else nombre


def series_con_datos(res):
    return any(res[f][l] for f in ('reposo', 'vc') for l in LADOS)


class RinometriaWindow(EquipoNasal):
    TITULO = 'Rinometría acústica'
    EQUIPO = 'ra'
    TIPO = 'RINOMETRIA'
    FUNCION = staticmethod(RA.mide_fosa)

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
    INDICACION = ('Calibra con el tubo calibrador y mide cada fosa: primero la derecha. Tres '
                  'registros en apnea por fosa.')

    CAMPOS = ['dist1', 'mca1', 'dist2', 'mca2', 'vol1', 'vol05', 'vol25']

    calibrado = False

    def _botones(self, caja):
        self.btn_calibrar = caja.agregar(self._boton('Calibrar', self._calibrar))
        self.btn_d = caja.agregar(self._boton('Medir FND', lambda: self._medir('D'), True))
        self.btn_i = caja.agregar(self._boton('Medir FNI', lambda: self._medir('I'), True))
        self.btn_vc = caja.agregar(self._boton('Aplicar vasoconstrictor', self._vasoconstrictor))

    def _errores(self, caja):
        self.chk_err = {}
        for clave, texto in (('fuga', 'Fuga en el adaptador'), ('aprieta', 'Adaptador que aprieta la narina'),
                             ('respira', 'Respira o traga en el registro')):
            self.chk_err[clave] = caja.agregar(QCheckBox(texto))

    def _opciones(self, caja):
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

    def _al_entrar(self):
        self.calibrado = False
        for chk in self.chk_err.values():
            chk.setChecked(False)

    def _calibrar(self):
        self.calibrado = True
        self._mensaje('Equipo calibrado con el tubo calibrador.', 'ok')
        self.dibujar()

    def _pedido(self, lado):
        if not self.calibrado:
            self._mensaje('Primero calibra el equipo con el tubo calibrador (H27).', 'alerta')
            return None
        return RA.mide_fosa, (self.sesion.paciente, lado, self.sesion.estado(), {
            'semilla': self.sesion.semilla_medicion(self.EQUIPO),
            'errores': {k: True for k, c in self.chk_err.items() if c.isChecked()},
        })

    def _al_medir(self, lado, r):
        vc = ', con vasoconstrictor' if self.sesion.vc else ''
        if r['repetible']:
            self._mensaje(f'{SIGLA[lado]}: tres registros en apnea{vc}. Se parecen entre sí.', 'ok')
        else:
            self._mensaje(f'{SIGLA[lado]}: tres registros en apnea{vc}. No se parecen: revisa y repite.',
                          'alerta')

    def _dibujar_equipo(self):
        self.g_curva.dibujar(self._series(), log=self.chk_log.isChecked(),
                             registros=self.chk_registros.isChecked(),
                             verdad=bool(self.chk_verdad and self.chk_verdad.isChecked()))
        self._tabla()
        avisos = self._lista_avisos()
        if self.sesion and self.sesion.hay_paciente and not self.calibrado:
            avisos = '• Equipo sin calibrar.' + ('\n' + avisos if avisos else '')
        self.avisos.setText(avisos)

    def _celdas(self, m):
        return [num(m[c]) for c in self.CAMPOS]

    def _tabla(self):
        if not series_con_datos(self.res):
            self.tabla.poblar([], [])
            self.tabla_vc.poblar([], [])
            self.tabla_vc.setVisible(False)
            self.pie.setText('')
            return
        cab = ['', 'Dist 1 (cm)', 'MCA1 (cm²)', 'Dist 2 (cm)', 'MCA2 (cm²)', 'Vol 1 (cm³)',
               'Vol 0-5 (cm³)', 'Vol 2-5 (cm³)', f'≤ {num(PROTOCOLO_REPETICION["valor"])}']
        filas = []
        for lado in LADOS:
            for nombre, fase in (('reposo', 'reposo'), ('con VC', 'vc')):
                f = self.res[fase][lado]
                if not f:
                    continue
                for k, r in enumerate(f['registros'] if self.chk_registros.isChecked() else []):
                    filas.append(([f'{SIGLA[lado]} {nombre} · registro {k + 1}'] + self._celdas(r['medidas']) + [''],
                                  lado, {}))
                filas.append(([f'{SIGLA[lado]} {nombre} · promedio'] + self._celdas(f['promedio'])
                              + ['sí' if f['repetible'] else 'no'],
                              lado, {8: 'ok' if f['repetible'] else 'fuera'}))
        filas.append((['Normal del modelo (no es norma)'] + self._celdas(normal_modelo()) + [''], None, {}))
        self.tabla.poblar(cab, filas)
        self.pie.setText('Vol 1: de la narina al segundo mínimo; Vol 0-5: el «Vol 2» del libro; '
                         'Vol 2-5: el de los cambios de la mucosa. Última columna: '
                         f'{PROTOCOLO_REPETICION["texto"]} {RINOMETRIA_SIN_NORMA} {HILBERG_1989["texto"]}')

        cambios = []
        for lado in LADOS:
            a, b = self.res['reposo'][lado], self.res['vc'][lado]
            if a and b:
                pa, pb = a['promedio'], b['promedio']
                cambios.append(([SIGLA[lado]] + [pct((pb[k] - pa[k]) / pa[k]) for k in ('mca1', 'mca2', 'vol05', 'vol25')],
                                lado, {}))
        self.tabla_vc.setVisible(bool(cambios))
        if cambios:
            self.tabla_vc.poblar(['Cambio con vasoconstrictor', 'MCA1', 'MCA2', 'Vol 0-5', 'Vol 2-5'], cambios)
            self.pie.setText(self.pie.text() + ' ' + COREY_1997['texto'])

    def _texto_verdad(self):
        filas = []
        for nombre, fase in (('Reposo', 'reposo'), ('Con VC', 'vc')):
            for lado in LADOS:
                f = self.res[fase][lado]
                if not f:
                    continue
                v, m = f['verdad']['medidas'], f['promedio']
                filas.append(f'<tr><td>{SIGLA[lado]}</td><td>{nombre}</td>'
                             f'<td>{num(v["mca1"])} (medida {num(m["mca1"])})</td>'
                             f'<td>{num(v["mca2"])} (medida {num(m["mca2"])})</td>'
                             f'<td>{num(v["vol05"])} (medida {num(m["vol05"])})</td></tr>')
        return ('<p>En el gráfico, "Área verdadera" dibuja en puntos el área de cada fosa. La curva '
                'del equipo se aparta de ella detrás de un estrechamiento marcado, pasados ~5 cm '
                '(senos y rinofaringe), con perforación y con los errores de técnica.</p>'
                '<table cellpadding="4"><tr><th>Fosa</th><th>Estado</th><th>MCA1 verdadera</th>'
                '<th>MCA2 verdadera</th><th>Vol 0-5 verdadero</th></tr>'
                + (''.join(filas) or '<tr><td colspan="5">Sin mediciones.</td></tr>') + '</table>'
                f'<p>Minuto {self.sesion.minuto()} del ciclo nasal.</p>')


_normal = None


def normal_modelo():
    """La fosa normal del modelo, para comparar: orden de magnitud, no norma."""
    global _normal
    if _normal is None:
        n = RA.I_CURVA + 1
        p = modelo.paciente('normal')
        _normal = RA.medidas(modelo.REJILLA[:n], modelo.perfil(p, 'D', {})[:n])
    return _normal
