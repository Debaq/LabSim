"""Los equipos de la nariz dentro de LabSim: rinomanometría anterior (H26) y
rinometría acústica (H27).

Las dos ventanas miden la misma nariz (nasal/sesion.py): el vasoconstrictor
que se pone en una vale para la otra, y el ciclo nasal corre con el reloj.
El modelo es el de RinoSim portado (nasal/modelo.py, rinomanometria.py,
rinometria.py): la misma nariz da las mismas curvas que las figuras del
libro.

Demo interna (docs/roadmap_nasal.md): solo el admin abre estos equipos. Los
errores de técnica se ponen a mano ("Simular"), como en RinoSim: el alumno
todavía no los comete con sus manos. Sin subida de informe todavía:
`reports.tipo` tiene un CHECK en la base y sumar tipos es una migración (ver
docs/decisiones.md, el incidente de reports_old); va con la ficha Nariz.

Sin `cases.data['NASAL']` el equipo no mide.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QFrame, QHBoxLayout, QHeaderView,
                               QMainWindow, QPushButton, QScrollArea, QSpinBox,
                               QSplitter, QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from core import hilos, tema
from nasal import modelo, sesion
from nasal import rinomanometria as RM
from nasal import rinometria as RA
from nasal.graficos import GraficoResistencia, GraficoRinometria, GraficoRinomanometria
from nasal.referencias import (COREY_1997, HILBERG_1989, PROTOCOLO_REPETICION,
                               REFERENCIA_UNILATERAL_150, REN_2018, RINOMETRIA_SIN_NORMA,
                               VOGT_2016)
from vemp.widgets.kit import Campos, Pastilla, Tarjeta, etiqueta

SIGLA = modelo.SIGLA_LADO
LADOS = modelo.LADOS
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
        self.panel_examen = Tarjeta('Examen')
        izq.addWidget(self.panel_examen)
        self._botones(self.panel_examen)
        self.panel_errores = Tarjeta('Simular error de técnica')
        izq.addWidget(self.panel_errores)
        self._errores(self.panel_errores)
        self.panel_vista = Tarjeta('Pantalla')
        izq.addWidget(self.panel_vista)
        self._opciones(self.panel_vista)
        izq.addStretch(1)
        desplazable = QScrollArea()
        desplazable.setWidget(izquierda)
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QFrame.Shape.NoFrame)
        desplazable.setFixedWidth(300)
        cuerpo.addWidget(desplazable)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._pantalla(), 'Registro')
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
        self.res = _vacio()
        if self.sesion is None or not self.sesion.hay_paciente:
            self._sin_caso(con_paciente=data is not None)
            return
        for panel in (self.panel_examen, self.panel_errores, self.panel_vista):
            panel.setEnabled(True)
        self.lbl_paciente.setText(descripcion_paciente(data))
        self._al_entrar()
        self._mensaje(self.INDICACION)
        self.dibujar()

    def _sin_caso(self, con_paciente=False):
        for panel in (self.panel_examen, self.panel_errores, self.panel_vista):
            panel.setEnabled(False)
        self.lbl_paciente.setText('Sin atención abierta')
        self.pill_minuto.set('')
        if con_paciente:
            self._mensaje('Este paciente no tiene la nariz cargada en el caso: el equipo no '
                          'mide. Hace falta el bloque NASAL del caso.', 'alerta')
        else:
            self._mensaje('Abre una atención para medir.')
        self.dibujar()

    def report_job(self):
        return None   # sin informe todavía (ver el docstring del módulo)

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
        self._midiendo(True)
        self._mensaje(f'Midiendo la {SIGLA[lado]}…')

        def listo(r):
            self._midiendo(False)
            if self.sesion is not sesion_de_la_medicion:
                return   # cambió la atención mientras medía
            self.res[fase][lado] = r
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
    TITULO = 'Rinomanometría anterior'
    EQUIPO = 'rm'
    INDICACION = ('Comprueba el sello y mide cada fosa: primero la derecha (adaptador en la '
                  'izquierda), después la izquierda.')

    def _botones(self, caja):
        self.btn_sello = caja.agregar(self._boton('Comprobar sello', self._sello))
        self.btn_d = caja.agregar(self._boton('Medir FND', lambda: self._medir('D'), True))
        self.btn_i = caja.agregar(self._boton('Medir FNI', lambda: self._medir('I'), True))
        self.btn_vc = caja.agregar(self._boton('Aplicar vasoconstrictor', self._vasoconstrictor))
        campos = Campos()
        self.spin_ciclos = QSpinBox()
        self.spin_ciclos.setRange(3, 5)
        self.spin_ciclos.setValue(4)
        campos.agregar('Ciclos', self.spin_ciclos)
        caja.agregar(campos)
        self.chk_forzada = caja.agregar(QCheckBox('Inspiración forzada'))

    def _errores(self, caja):
        self.chk_err = {}
        for clave, texto in (('mascara', 'Fuga en la máscara'), ('adaptador', 'Adaptador sin sellar'),
                             ('boca', 'Respira por la boca'), ('irregular', 'Respiración irregular')):
            self.chk_err[clave] = caja.agregar(QCheckBox(texto))

    def _opciones(self, caja):
        self.chk_ciclos = caja.agregar(self._check('Ver los ciclos', self.dibujar, True))
        self.chk_referencia = caja.agregar(self._check('Recta de referencia (0,4)', self.dibujar, True))
        self.chk_broms = caja.agregar(self._check('Lectura de Broms (radio 200)', self.dibujar))

    def _pantalla(self):
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(10, 10, 10, 10)
        arriba = QSplitter(Qt.Orientation.Horizontal)
        self.g_curva = GraficoRinomanometria()
        self.g_resistencia = GraficoResistencia()
        caja_curva = Tarjeta('Presión-flujo')
        caja_curva.agregar(self.g_curva.widget, 1)
        caja_r = Tarjeta('Resistencia según la presión')
        caja_r.agregar(self.g_resistencia.widget, 1)
        arriba.setMinimumHeight(300)
        arriba.addWidget(caja_curva)
        arriba.addWidget(caja_r)
        arriba.setStretchFactor(0, 3)
        arriba.setStretchFactor(1, 2)
        caja, self.tabla, self.pie, self.avisos = self._bloque_tabla('Resultados')
        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(arriba)
        vertical.addWidget(caja)
        vertical.setStretchFactor(0, 3)
        vertical.setStretchFactor(1, 1)
        layout.addWidget(vertical)
        return contenedor

    def _al_entrar(self):
        for chk in self.chk_err.values():
            chk.setChecked(False)
        self.chk_forzada.setChecked(False)

    def _errores_puestos(self):
        return {k: True for k, c in self.chk_err.items() if c.isChecked()}

    def _sello(self):
        if self.chk_err['adaptador'].isChecked():
            self._mensaje('Pasa aire por el adaptador: no sella. El tubo no va a leer la '
                          'rinofaringe. Corrígelo antes de medir.', 'alerta')
        else:
            self._mensaje('No pasa aire por el adaptador: sella bien.', 'ok')

    def _pedido(self, lado):
        return RM.mide_fosa, (self.sesion.paciente, lado, self.sesion.estado(), {
            'ciclos': self.spin_ciclos.value(),
            'semilla': self.sesion.semilla_medicion(self.EQUIPO),
            'errores': self._errores_puestos(),
            'forzada': self.chk_forzada.isChecked(),
        })

    def _al_medir(self, lado, r):
        siguiente = ' Cambia el adaptador a la derecha y mide la FNI.' if lado == 'D' else ''
        self._mensaje(f'{SIGLA[lado]} medida {"con vasoconstrictor" if self.sesion.vc else "en reposo"}: '
                      f'{len(r["ciclos"])} ciclos promediados.{siguiente}')

    def _dibujar_equipo(self):
        series = self._series()
        broms = self.chk_broms.isChecked()
        self.g_curva.dibujar(series, ciclos=self.chk_ciclos.isChecked(),
                             referencia=self.chk_referencia.isChecked(), broms=broms)
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
