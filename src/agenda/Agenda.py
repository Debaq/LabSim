# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 0.9 - Audiometro                   #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

import requests
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import (QTableWidgetItem, QAbstractItemView,
                                QDateEdit, QPushButton, QMessageBox, QLineEdit,
                                QVBoxLayout, QLabel, QTextEdit,
                                QCheckBox)
from PySide6.QtCore import QDate, QTime, QDateTime, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QTextCharFormat
from agenda.UI.Ui_agenda import Ui_Form
from core import feriados as feriados_cl
from core import hilos, respaldo_informes
from core.helpers import (Shedule, aplicar_delta, entry_estado_por, CasesOffline, debug_print,
                          es_docente, lista_practica, iniciar_practica,
                          marcar_entry_no_show,
                          obtener_nota_atencion,
                          CreatePatient)
from core.ficha import parse_fecha_agenda, render_ficha_html
from core.practica import abrir_ficha_estudio


def _traer_agenda(con_practica):
    """Shedule() (llamada de red) fuera del hilo de UI: (agenda, práctica).

    Silencioso como el sync (backend/sync_thread.py): si el backend no responde, no
    hay diálogo -- se reintenta en el próximo ciclo de polling. Corre en
    otro hilo (hilos.en_fondo): nada de widgets acá."""
    try:
        data = Shedule().get()
    except requests.RequestException as exc:
        print(f"agenda: sin respuesta del servidor: {exc}")
        return None, None
    practica = None
    if con_practica:
        try:
            practica = lista_practica()
        except requests.RequestException as exc:
            print(f"agenda: sin lista de práctica: {exc}")
    return data, practica


PENDIENTE_COLOR = QColor(255, 244, 200)
ATENDIENDO_COLOR = QColor(200, 224, 247)
ATENDIDO_COLOR = QColor(210, 235, 210)
NO_SHOW_COLOR = QColor(235, 190, 190)
# Caso sin ninguna cita en la agenda (AgendaEntry.sin_cita) -- distinto del
# amarillo PENDIENTE, que es una cita creada pero todavía sin fecha/hora.
SIN_CITA_COLOR = QColor(232, 224, 240)
# Feriados legales en el calendario del filtro por fecha (ver core/feriados.py).
FERIADO_COLOR = QColor(176, 0, 32)
FERIADO_FONDO = QColor(255, 228, 228)


class FichaClinicaWidget(QWidget):
    """Ficha clínica del paciente. Vive como subventana única del MDI (ver
    main.py: self.subw["FICHA"]) en vez de un diálogo emergente -- set_ficha()
    la reapunta a otro paciente cada vez que se abre desde la agenda."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.texto = QTextEdit(self)
        self.texto.setReadOnly(True)
        layout.addWidget(self.texto)

        self._on_chat = None

    def set_ficha(self, html, on_chat=None):
        self.texto.setHtml(html)
        self._on_chat = on_chat


class EvolucionWidget(QWidget):
    """Registro de evolución al cerrar una atención. Vive como subventana
    única del MDI (ver main.py: self.subw["EVOLUCION"]) en vez de un diálogo
    emergente -- set_contexto() la reapunta a otro paciente/callback cada vez
    que se abre desde la agenda (atención real o de prueba)."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.lbl_paciente = QLabel(self)
        layout.addWidget(self.lbl_paciente)

        layout.addWidget(QLabel("Describe la evolución del paciente:", self))

        self.texto = QTextEdit(self)
        layout.addWidget(self.texto)

        self.btn_guardar = QPushButton("Guardar evolución", self)
        self.btn_guardar.clicked.connect(self._on_guardar_clicked)
        layout.addWidget(self.btn_guardar)

        self._on_guardar = None
        # (usuario, appointment_id) del borrador en el equipo, o None
        # (prueba del docente: no se guarda nada).
        self._borrador = None
        # Lo escrito va al disco poco después de cada cambio (ver
        # respaldo_informes.guardar_borrador).
        self._timer_borrador = QTimer(self)
        self._timer_borrador.setSingleShot(True)
        self._timer_borrador.setInterval(1500)
        self._timer_borrador.timeout.connect(self.guardar_borrador)
        self.texto.textChanged.connect(self._timer_borrador.start)

    def set_contexto(self, nombre_paciente, on_guardar, borrador=None):
        """`borrador`: (usuario, appointment_id) de una atención real. Lo
        escrito antes para esa misma atención vuelve, aunque la ventana se
        haya cerrado, se haya cerrado sesión o la app se haya caído."""
        self.guardar_borrador()   # lo pendiente del contexto anterior
        mismo = borrador is not None and borrador == self._borrador
        self.lbl_paciente.setText(f"Paciente: {nombre_paciente}")
        self._on_guardar = on_guardar
        self._borrador = borrador
        if mismo and self.texto.toPlainText().strip():
            return
        texto = respaldo_informes.leer_borrador(*borrador) if borrador else ""
        self.texto.blockSignals(True)
        self.texto.setPlainText(texto)
        self.texto.blockSignals(False)

    def guardar_borrador(self):
        self._timer_borrador.stop()
        if self._borrador is not None:
            respaldo_informes.guardar_borrador(*self._borrador, self.texto.toPlainText())

    def hideEvent(self, event):
        self.guardar_borrador()
        super().hideEvent(event)

    def _on_guardar_clicked(self):
        nota = self.texto.toPlainText().strip()
        if not nota:
            QMessageBox.warning(self, "Evolución", "Debes describir la evolución del paciente.")
            return

        self.guardar_borrador()
        # Solo True es "cerrada": False (sin conexión) o None (no se pudo)
        # dejan la nota escrita para volver a intentarlo.
        if self._on_guardar is not None and self._on_guardar(nota) is not True:
            return
        if self._borrador is not None:
            respaldo_informes.borrar_borrador(*self._borrador)
        self.texto.blockSignals(True)
        self.texto.clear()
        self.texto.blockSignals(False)

        padre = self.parent()
        if padre is not None and hasattr(padre, "hide_window"):
            padre.hide_window()


class Agenda(QWidget, Ui_Form):
    def __init__(self, permissions, obj):
        # Inicialización de la ventana y propiedades
        #super(Audiometer, self).__init__()
        super().__init__()
        self.setupUi(self)

        # Admin (777) y docente (555) comparten la misma vista de agenda:
        # ven TODAS las citas (sin filtro por fecha) más los casos que aún no
        # tienen cita (filas sin_cita, ver backend_state_to_shedule).
        self.is_admin = es_docente(permissions)
        self.main_window = obj
        self._selected_key = None
        self._selected_row_key = None
        self._loading = False
        self._ver_todas = False
        self._filtro_texto = ""
        self._prueba_atendiendo_key = None
        self._guardar_base = False
        # Práctica libre (solo alumno): la tabla muestra la lista de práctica
        # deliberada del curso en vez de la agenda. Filas con key
        # "practica:<id>"; los intentos (citas con practice_id) nunca se
        # muestran como filas de agenda. Ver core/practica.py.
        self._modo_practica = False
        self._practica = {}

        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Agenda admin y estudiante son la misma vista: la gestión de citas
        # (agendar/editar/cancelar/eliminar) vive solo en el backend web
        # (labsim_backend/public/admin/agenda.php); la app queda de solo
        # lectura para todos los roles, con "Atender" como única acción, que
        # en el admin corre en modo prueba (ver atender_paciente()).
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.led_buscar = QLineEdit(self)
        self.led_buscar.setPlaceholderText("Buscar por RUT, nombre o apellido...")
        self.led_buscar.textChanged.connect(self._on_filtro_changed)
        self.horizontalLayout.insertWidget(0, self.led_buscar)

        self._build_atender_control()

        self.tableWidget.itemSelectionChanged.connect(self._on_selection_changed)

        self.read_shedule()
        self.populate_shedule()

        self.pushButton.setVisible(False)

    def _build_atender_control(self):
        self.date_selector = QDateEdit(self)
        self.date_selector.setCalendarPopup(True)
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.dateChanged.connect(self._on_fecha_seleccionada)
        self.horizontalLayout.insertWidget(1, self.date_selector)
        self._init_feriados()

        self.chk_ver_todas = QCheckBox("Ver todas las citas habilitadas", self)
        self.chk_ver_todas.toggled.connect(self._on_toggle_ver_todas)
        self.horizontalLayout.insertWidget(2, self.chk_ver_todas)

        self.btn_practica = QPushButton("Práctica libre", self)
        self.btn_practica.setCheckable(True)
        self.btn_practica.setToolTip("Pacientes que tu docente dejó para practicar cuando quieras, "
                                     "las veces que quieras")
        self.btn_practica.toggled.connect(self._on_toggle_practica)
        self.horizontalLayout.insertWidget(3, self.btn_practica)
        self._encabezados_agenda = [
            self.tableWidget.horizontalHeaderItem(i).text()
            for i in range(self.tableWidget.columnCount())
        ]

        self.btn_ver_ficha = QPushButton("Ver ficha", self)
        self.btn_ver_ficha.setEnabled(False)
        self.btn_ver_ficha.clicked.connect(self._ver_ficha_paciente)
        self.horizontalLayout.insertWidget(4, self.btn_ver_ficha)

        self.btn_atender = QPushButton("Atender", self)
        self.btn_atender.setEnabled(False)
        self.btn_atender.clicked.connect(self.atender_paciente)
        self.horizontalLayout.insertWidget(5, self.btn_atender)

        self.btn_no_show = QPushButton("No se presentó", self)
        self.btn_no_show.setEnabled(False)
        self.btn_no_show.clicked.connect(self._marcar_no_show)
        self.horizontalLayout.insertWidget(6, self.btn_no_show)

        self.btn_ficha_estudio = QPushButton("Ficha de estudio", self)
        self.btn_ficha_estudio.setToolTip("Los resultados del caso, para comparar con tu último intento cerrado")
        self.btn_ficha_estudio.setVisible(False)
        self.btn_ficha_estudio.clicked.connect(self._ver_ficha_estudio)
        self.horizontalLayout.insertWidget(7, self.btn_ficha_estudio)

        if self.is_admin:
            # El admin ve todos los pacientes siempre (ver _visible_keys):
            # el filtro por fecha / "ver todas" es solo para el estudiante.
            # La práctica libre también: el docente prueba los casos desde
            # sus filas de siempre.
            self.date_selector.setVisible(False)
            self.chk_ver_todas.setVisible(False)
            self.btn_practica.setVisible(False)

            # Solo admin/docente: elegir si su "Atender" es una prueba sin
            # rastro (por defecto, ver atender_paciente_prueba) o si queda
            # guardado de verdad con su propia cuenta (attendances + chat) --
            # para armar una atención base con la que comparar a los
            # alumnos después (ver main.atender_paciente_base). Deshabilitado
            # mientras hay una atención en curso para no cambiar de modo a
            # mitad de camino.
            self.chk_guardar_base = QCheckBox("Guardar esta atención (base para comparar)", self)
            self.chk_guardar_base.toggled.connect(self._on_toggle_guardar_base)
            self.horizontalLayout.insertWidget(8, self.chk_guardar_base)

    def _on_toggle_guardar_base(self, checked):
        self._guardar_base = checked

    def _on_toggle_ver_todas(self, checked):
        self._ver_todas = checked
        self.date_selector.setEnabled(not checked)
        self.populate_shedule()

    def _on_toggle_practica(self, checked):
        self._modo_practica = checked
        self.date_selector.setVisible(not checked)
        self.chk_ver_todas.setVisible(not checked)
        self.btn_no_show.setVisible(not checked)
        self.btn_ficha_estudio.setVisible(checked)
        if checked:
            self.tableWidget.setHorizontalHeaderLabels(
                ["Intentos", "Último", "RUT", "Nombre", "Apellido", "Fecha nac.", "Procedimiento"])
            self._pedir_practica()
        else:
            self.tableWidget.setHorizontalHeaderLabels(self._encabezados_agenda)
        self._selected_row_key = None
        self.tableWidget.blockSignals(True)
        self.tableWidget.clearSelection()
        self.tableWidget.setRowCount(0)
        self.tableWidget.blockSignals(False)
        self.populate_shedule()

    def _on_practica_fetched(self, items):
        self._practica = {f"practica:{it['id']}": it for it in items}
        if self._modo_practica:
            self.populate_shedule()

    def _on_fecha_seleccionada(self, qdate):
        self._actualizar_tooltip_fecha(qdate)
        self.populate_shedule()

    # -- Feriados -----------------------------------------------------------
    # Marcarlos es puro adorno útil (saber que la fecha que se está mirando
    # es feriado): si la API no responde y no hay cache ni backup, la agenda
    # funciona igual, solo que sin colores.

    def _init_feriados(self):
        """Pinta los feriados que ya se conocen sin tocar la red y, solo si
        falta alguno, los pide en un hilo aparte."""
        self._feriados = {}
        anio = QDate.currentDate().year()
        self._anios_feriados = (anio, anio + 1)

        conocidos = {}
        for year in self._anios_feriados:
            mapa = feriados_cl.feriados_offline(year)
            if mapa:
                conocidos[year] = mapa
        self._aplicar_feriados(conocidos)

        faltantes = [y for y in self._anios_feriados if feriados_cl.load_cache(y) is None]
        if not faltantes:
            return
        hilos.en_fondo(feriados_cl.refrescar_varios, faltantes, dueno=self,
                       listo=lambda por_anio: por_anio and self._aplicar_feriados(por_anio),
                       nombre="feriados")

    def _aplicar_feriados(self, por_anio):
        """Pinta {año: {"MM-DD": descripción}} en el calendario emergente."""
        calendario = self.date_selector.calendarWidget()
        if calendario is None:
            return

        base = QTextCharFormat()
        base.setForeground(QBrush(FERIADO_COLOR))
        base.setBackground(QBrush(FERIADO_FONDO))
        base.setFontWeight(QFont.Bold)

        for year, mapa in por_anio.items():
            self._feriados.setdefault(year, {}).update(mapa)
            for mmdd, descripcion in mapa.items():
                fecha = QDate.fromString(f"{year}-{mmdd}", "yyyy-MM-dd")
                if not fecha.isValid():
                    continue
                formato = QTextCharFormat(base)
                formato.setToolTip(descripcion)
                calendario.setDateTextFormat(fecha, formato)

        self._actualizar_tooltip_fecha(self.date_selector.date())
        # La primera pasada corre desde _build_atender_control, antes de que
        # exista self.shedule; la que llega por red sí tiene que repintar la
        # tabla para marcar las citas que caen en feriado.
        if getattr(self, "shedule", None) is not None:
            self.populate_shedule()

    def _descripcion_feriado(self, qdate):
        if not qdate.isValid():
            return None
        return self._feriados.get(qdate.year(), {}).get(qdate.toString("MM-dd"))

    def _actualizar_tooltip_fecha(self, qdate):
        descripcion = self._descripcion_feriado(qdate)
        self.date_selector.setToolTip(f"Feriado: {descripcion}" if descripcion else "")

    def _on_filtro_changed(self, texto):
        self._filtro_texto = texto.strip().lower()
        self.populate_shedule()

    def read_shedule(self):
        shedule = Shedule()
        self.shedule = shedule.get()

    def refresh(self):
        self.read_shedule()
        self.populate_shedule()

    def refresh_async(self):
        """Como refresh(), pero la llamada de red corre en un hilo aparte.

        Baja la agenda entera (Shedule() -> get_full_state): solo cuando el
        delta del sync no alcanza (ver aplicar_delta) o sin sync. En el hilo
        de UI, un backend caído congelaba la ventana completa (timeout SSL
        de hasta 10s)."""
        if getattr(self, "_shedule_fetch", None) is not None:
            # Hay una en curso, quizás de antes del cambio que hay que
            # mostrar (atender/cerrar): se repite al terminar.
            self._refrescar_otra_vez = True
            return
        self._refrescar_otra_vez = False
        # Sin QThread por consulta: ver hilos.en_fondo (cierres del
        # 2026-10-09, uno cada 15 s durante toda la jornada).
        self._shedule_fetch = hilos.en_fondo(
            _traer_agenda, self._modo_practica, dueno=self,
            listo=self._on_refresh_async_done, fallo=self._on_refresh_async_fallo,
            nombre="agenda")

    def aplicar_delta(self, delta):
        """Lo que trajo un ciclo de sync (main._on_backend_sync): se arma la
        agenda en memoria y solo se baja entera si hace falta (ver
        helpers.aplicar_delta)."""
        que, data = aplicar_delta(delta)
        if que == "completo":
            self.refresh_async()
            return
        if que == "nuevo":
            self.shedule = data
            self.populate_shedule()
            if self._modo_practica:
                self._pedir_practica()

    def _pedir_practica(self):
        hilos.en_fondo(lista_practica, dueno=self, nombre="practica",
                       listo=self._on_practica_fetched)

    def actualizar(self):
        """Tras una acción propia (atender, inasistencia, práctica): que el
        sync pregunte ya, en vez de bajar la agenda entera."""
        pedir = getattr(self.main_window, "sync_ahora", None)
        if pedir is None or not pedir():
            self.refresh_async()

    def _on_refresh_async_done(self, resultado):
        self._shedule_fetch = None
        data, practica = resultado
        if data is not None:
            self.shedule = data
            self.populate_shedule()
        if practica is not None:
            self._on_practica_fetched(practica)
        if getattr(self, "_refrescar_otra_vez", False):
            self.refresh_async()

    def _on_refresh_async_fallo(self, exc):
        # Una respuesta rara (no de red) no puede dejar la agenda sin
        # refrescar para siempre: se sigue en el próximo ciclo.
        print(f"agenda: no se pudo refrescar: {type(exc).__name__}: {exc}")
        self._on_refresh_async_done((None, None))

    def _current_username(self):
        data_login = getattr(self.main_window, "data_login", None) or {}
        return data_login.get("user")

    def _visible_keys(self, agenda="agenda_1"):
        rows = self.shedule.get(agenda, {})
        if self.is_admin:
            # Única diferencia con la vista de estudiante: el admin ve TODOS
            # los pacientes/citas (sin filtro por fecha ni por estado).
            keys = list(rows.keys())
        else:
            # Los intentos de práctica no son citas de la agenda: se ven y se
            # retoman desde "Práctica libre".
            keys = [k for k, v in rows.items() if v.fecha and v.hora and v.practice_id is None]
            if not self._ver_todas:
                fecha_sel = self.date_selector.date().toString("dd-MM-yy")
                keys = [k for k in keys if rows[k].fecha == fecha_sel]

        if self._filtro_texto:
            texto = self._filtro_texto
            keys = [
                k for k in keys
                if texto in " ".join((rows[k].rut, rows[k].nombre, rows[k].apellido,
                                       rows[k].fecha_nac, rows[k].procedimiento)).lower()
            ]
        return keys

    def populate_shedule(self, agenda="agenda_1"):
        if self._modo_practica:
            self._populate_practica()
            return
        rows = self.shedule.get(agenda, {})
        keys = self._visible_keys(agenda)
        prev_key = self._selected_row_key

        self._loading = True
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setRowCount(len(keys))

        username = self._current_username()
        for row_idx, key in enumerate(keys):
            user = rows[key]
            pendiente = not (user.fecha and user.hora)
            estado = entry_estado_por(user, username)
            color = None
            tooltip = ""
            if user.sin_cita:
                # Caso creado en el panel que todavía no se agendó a nadie:
                # el docente lo ve para poder probarlo, pero no se puede
                # atender de verdad (no hay cita a la que colgar la atención).
                color = SIN_CITA_COLOR
                tooltip = "Caso sin cita: solo se puede probar, no queda registro."
            elif pendiente:
                color = PENDIENTE_COLOR
                tooltip = "Cita creada sin fecha ni hora."
            elif estado == "atendiendo":
                color = ATENDIENDO_COLOR
            elif estado == "atendido":
                color = ATENDIDO_COLOR
            elif estado == "no_show":
                color = NO_SHOW_COLOR
            # Cita agendada en feriado: se avisa en la celda de la fecha (no
            # en toda la fila) para no tapar el color de estado. Es un error
            # del docente al agendar, no del alumno -- nadie va a atender ese
            # día, así que tiene que saltar a la vista en la tabla, que es lo
            # único que ve el docente (su vista esconde el date_selector).
            feriado = self._descripcion_feriado(parse_fecha_agenda(user.fecha))

            columnas = (user.fecha or "sin agendar", user.hora, user.rut, user.nombre,
                        user.apellido, user.fecha_nac, user.procedimiento)
            for col_idx, valor in enumerate(columnas):
                item = QTableWidgetItem(valor)
                item.setData(Qt.UserRole, key)
                if color is not None:
                    item.setBackground(color)
                if tooltip:
                    item.setToolTip(tooltip)
                if feriado and col_idx == 0:
                    item.setText(f"⚠ {valor}")
                    item.setBackground(FERIADO_FONDO)
                    item.setForeground(FERIADO_COLOR)
                    item.setToolTip(f"Agendada en feriado: {feriado}")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tableWidget.setItem(row_idx, col_idx, item)
        self.tableWidget.setSortingEnabled(True)
        self._loading = False

        if prev_key is not None and prev_key in keys:
            # Re-seleccionar la misma fila tras reconstruir la tabla. Si el índice
            # de fila no cambió (ej. un solo paciente), itemSelectionChanged no
            # dispara solo, así que forzamos el recálculo del estado del botón.
            row_idx = keys.index(prev_key)
            self.tableWidget.blockSignals(True)
            self.tableWidget.selectRow(row_idx)
            self.tableWidget.blockSignals(False)
            self._on_selection_changed()
        else:
            self._reset_atender_button()
            self._selected_key = None
            self._selected_row_key = None

    def _populate_practica(self):
        """Llena la tabla con la lista de práctica (ver _on_toggle_practica)."""
        keys = list(self._practica.keys())
        if self._filtro_texto:
            texto = self._filtro_texto
            keys = [
                k for k in keys
                if texto in " ".join(str(self._practica[k].get(c) or "") for c in
                                     ("rut", "nombre", "apellido", "procedimiento", "curso")).lower()
            ]
        prev_key = self._selected_row_key

        self._loading = True
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setRowCount(len(keys))
        for row_idx, key in enumerate(keys):
            it = self._practica[key]
            intentos = int(it.get("intentos") or 0)
            ultimo = (it.get("ultimo") or "")[:10]
            color = ATENDIENDO_COLOR if it.get("abierto") else (ATENDIDO_COLOR if intentos else None)
            columnas = (str(intentos), ultimo or "—", it.get("rut") or "", it.get("nombre") or "",
                        it.get("apellido") or "", it.get("fecha_nac") or "", it.get("procedimiento") or "")
            for col_idx, valor in enumerate(columnas):
                item = QTableWidgetItem(valor)
                item.setData(Qt.UserRole, key)
                if color is not None:
                    item.setBackground(color)
                if it.get("curso"):
                    item.setToolTip(f"Curso: {it['curso']}")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tableWidget.setItem(row_idx, col_idx, item)
        self.tableWidget.setSortingEnabled(True)
        self._loading = False

        if prev_key is not None and prev_key in keys:
            self.tableWidget.blockSignals(True)
            for fila in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(fila, 0).data(Qt.UserRole) == prev_key:
                    self.tableWidget.selectRow(fila)
                    break
            self.tableWidget.blockSignals(False)
            self._on_selection_changed()
        else:
            self._reset_atender_button()
            self._selected_key = None
            self._selected_row_key = None

    def _intento_abierto(self, key):
        """Key de agenda del intento que el alumno dejó abierto en este
        paciente de práctica, o None."""
        abierto = self._practica.get(key, {}).get("abierto")
        return str(abierto) if abierto else None

    def _on_practica_selected(self, key):
        it = self._practica[key]
        self._selected_row_key = key
        self._selected_key = None
        intento = self._intento_abierto(key)
        if intento is not None and self._es_atencion_activa(intento):
            self.btn_atender.setText("Cerrar/Evolucionar")
        elif intento is not None:
            self.btn_atender.setText("Retomar")
        else:
            self.btn_atender.setText("Practicar")
        self.btn_atender.setEnabled(True)
        # La ficha clínica cuelga de la cita: recién existe con el intento.
        self.btn_ver_ficha.setEnabled(intento is not None)
        self.btn_ficha_estudio.setEnabled(bool(it.get("show_study_sheet") and it.get("ultimo_cerrado")))
        self.btn_no_show.setEnabled(False)

    def _atender_practica(self, key):
        it = self._practica.get(key)
        if it is None or self.main_window is None:
            return
        intento = self._intento_abierto(key)
        if intento is not None and self._es_atencion_activa(intento):
            self._cerrar_practica(intento, it)
            return
        if intento is None:
            try:
                cita = iniciar_practica(int(it["id"]))
            except requests.RequestException as exc:
                QMessageBox.warning(self, "Práctica libre",
                                    f"No se pudo abrir el paciente de práctica.\n\n{exc}")
                return
            intento = str(cita["id"])
            it["abierto"] = cita["id"]
        if hasattr(self.main_window, "atender_paciente"):
            self.main_window.atender_paciente(intento)
        self._on_selection_changed()

    def _cerrar_practica(self, intento, it):
        """Como _cerrar_atencion(), para el intento abierto de un paciente
        de práctica (la fila seleccionada no es la cita)."""
        if not hasattr(self.main_window, "abrir_evolucion"):
            return
        nombre = f"{it.get('nombre') or ''} {it.get('apellido') or ''}".strip()

        def _guardar(nota):
            return self.main_window.cerrar_atencion(intento, nota)

        self.main_window.abrir_evolucion(nombre or "el paciente", _guardar, intento)

    def _ver_ficha_estudio(self):
        it = self._practica.get(self._selected_row_key or "")
        if it and it.get("ultimo_cerrado"):
            abrir_ficha_estudio(self, it["ultimo_cerrado"])

    def _reset_atender_button(self):
        self.btn_atender.setText("Practicar" if self._modo_practica else "Atender")
        self.btn_atender.setEnabled(False)
        self.btn_ver_ficha.setEnabled(False)
        self.btn_no_show.setEnabled(False)
        self.btn_ficha_estudio.setEnabled(False)
        if self.is_admin:
            self.chk_guardar_base.setEnabled(True)

    def _on_selection_changed(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        if not selected_rows:
            self._reset_atender_button()
            self._selected_key = None
            self._selected_row_key = None
            return

        key = self.tableWidget.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        if key in self._practica and self._modo_practica:
            self._on_practica_selected(key)
            return
        if key not in self.shedule.get("agenda_1", {}):
            # Fila de la otra vista a medio reemplazar (al cambiar entre
            # agenda y práctica libre).
            self._reset_atender_button()
            return
        user = self.shedule["agenda_1"][key]
        tiene_caso = bool(user.case_id)
        estado = entry_estado_por(user, self._current_username())
        pendiente = not (user.fecha and user.hora)

        self._selected_row_key = key
        self._selected_key = key if pendiente else None

        if self.is_admin and user.sin_cita:
            # Sin cita no hay appointment_id: attendances no lo puede
            # referenciar, así que "guardar base" no aplica y el único ciclo
            # posible es el de prueba (ver atender_paciente()).
            self.chk_guardar_base.setEnabled(False)
            self.chk_guardar_base.setToolTip(
                "Este caso no está agendado: solo se puede probar, no se guarda la atención."
            )
        elif self.is_admin:
            self.chk_guardar_base.setToolTip("")

        if self.is_admin and self._guardar_base and not user.sin_cita:
            # Guardar base: mismo ciclo real que el alumno (marca "atendiendo"/
            # "atendido" de verdad, con la propia cuenta del docente) -- ver
            # main.atender_paciente_base/cerrar_atencion_base.
            if estado == "atendiendo" and self._es_atencion_activa(key):
                self.btn_atender.setText("Cerrar/Evolucionar")
                self.btn_atender.setEnabled(tiene_caso)
            elif estado == "atendiendo":
                self.btn_atender.setText("Atender")
                self.btn_atender.setEnabled(tiene_caso)
            elif estado == "atendido":
                self.btn_atender.setText("Atender")
                self.btn_atender.setEnabled(False)
            else:
                self.btn_atender.setText("Atender")
                self.btn_atender.setEnabled(tiene_caso)
            self.chk_guardar_base.setEnabled(not (estado == "atendiendo" and self._es_atencion_activa(key)))
        elif self.is_admin and user.sin_cita:
            # Modo prueba forzado (ver arriba): el checkbox ya quedó
            # deshabilitado, acá solo se decide el botón.
            if self._prueba_atendiendo_key == key and self._es_atencion_activa(key):
                self.btn_atender.setText("Cerrar/Evolucionar")
            else:
                self.btn_atender.setText("Atender (prueba)")
            self.btn_atender.setEnabled(tiene_caso)
        elif self.is_admin:
            # Modo prueba (por defecto): no queda "atendiendo" en la agenda ni
            # se escribe en red, pero el botón sí simula el ciclo completo
            # atender/cerrar (ver atender_paciente() y _cerrar_atencion_prueba()).
            if self._prueba_atendiendo_key == key and self._es_atencion_activa(key):
                self.btn_atender.setText("Cerrar/Evolucionar")
                self.btn_atender.setEnabled(tiene_caso)
            else:
                self.btn_atender.setText("Atender")
                self.btn_atender.setEnabled(tiene_caso)
            self.chk_guardar_base.setEnabled(
                not (self._prueba_atendiendo_key == key and self._es_atencion_activa(key))
            )
        elif estado == "atendiendo" and self._es_atencion_activa(key):
            self.btn_atender.setText("Cerrar/Evolucionar")
            self.btn_atender.setEnabled(tiene_caso)
        elif estado == "atendiendo":
            # Quedó "atendiendo" pero no está cargado en memoria (reinicio de la app
            # o el alumno está atendiendo a otro paciente): retomar, no cerrar.
            self.btn_atender.setText("Atender")
            self.btn_atender.setEnabled(tiene_caso)
        elif estado == "atendido":
            self.btn_atender.setText("Atender")
            self.btn_atender.setEnabled(False)
        else:
            self.btn_atender.setText("Atender")
            self.btn_atender.setEnabled(tiene_caso and not pendiente)

        self.btn_ver_ficha.setEnabled(tiene_caso)

        fecha_agendada = parse_fecha_agenda(user.fecha)
        hora_agendada = QTime.fromString(user.hora, "HH:mm")
        hora_vencida = (
            not pendiente and fecha_agendada.isValid() and hora_agendada.isValid()
            and QDateTime(fecha_agendada, hora_agendada) < QDateTime.currentDateTime()
        )
        self.btn_no_show.setEnabled(hora_vencida and estado is None)

    def _es_atencion_activa(self, key):
        """True si `key` es el paciente que está cargado ahora mismo en los módulos."""
        return getattr(self.main_window, "data_current_key", None) == key

    def atender_paciente(self):
        if self._selected_row_key is None:
            return

        if self._modo_practica:
            self._atender_practica(self._selected_row_key)
            return

        sin_cita = self.shedule["agenda_1"][self._selected_row_key].sin_cita

        if self.is_admin and self._guardar_base and not sin_cita:
            self._atender_paciente_admin_real()
            return

        if self.is_admin:
            # Admin/profe: modo prueba -- carga el caso en los módulos sin marcar
            # "atendiendo" ni escribir attendances (ver main.atender_paciente_prueba),
            # pero el botón simula igual el ciclo completo hasta "Cerrar atención"
            # para poder probar el flujo del estudiante sin dejar rastro en red.
            if self._prueba_atendiendo_key == self._selected_row_key and self._es_atencion_activa(self._selected_row_key):
                self._cerrar_atencion_prueba()
                return

            user = self.shedule["agenda_1"][self._selected_row_key]
            if not user.case_id:
                QMessageBox.warning(self, "Atender", "Este registro no tiene un caso clínico asociado.")
                return
            if self.main_window is not None and hasattr(self.main_window, "atender_paciente_prueba"):
                self.main_window.atender_paciente_prueba(self._selected_row_key)
                self._prueba_atendiendo_key = self._selected_row_key
                self._on_selection_changed()
            return

        user = self.shedule["agenda_1"][self._selected_row_key]
        estado = entry_estado_por(user, self._current_username())

        if estado == "atendiendo" and self._es_atencion_activa(self._selected_row_key):
            self._cerrar_atencion()
            return

        if self.main_window is not None and hasattr(self.main_window, "atender_paciente"):
            self.main_window.atender_paciente(self._selected_row_key)

    def _cerrar_atencion(self):
        """Abre la subventana MDI de evolución; al guardar, cierra la
        atención real (ver main.abrir_evolucion / main.cerrar_atencion)."""
        if self.main_window is None or not hasattr(self.main_window, "abrir_evolucion"):
            return

        user = self.shedule["agenda_1"][self._selected_row_key]
        nombre = f"{user.nombre} {user.apellido}".strip()
        key = self._selected_row_key

        def _guardar(nota):
            return self.main_window.cerrar_atencion(key, nota)

        self.main_window.abrir_evolucion(nombre or "el paciente", _guardar, key)

    def _cerrar_atencion_prueba(self):
        """Admin/profe: misma subventana de evolución, pero sin marcar
        "atendido" ni escribir nada en red (ver main.cerrar_atencion_prueba)."""
        if self.main_window is None or not hasattr(self.main_window, "abrir_evolucion"):
            return

        user = self.shedule["agenda_1"][self._selected_row_key]
        nombre = f"{user.nombre} {user.apellido}".strip()

        def _guardar(nota):
            self._prueba_atendiendo_key = None
            self.main_window.cerrar_atencion_prueba(nota)
            self._on_selection_changed()
            return True

        self.main_window.abrir_evolucion(nombre or "el paciente", _guardar)

    def _atender_paciente_admin_real(self):
        """Admin/docente con "Guardar esta atención" marcado: mismo ciclo
        real que el alumno (marca "atendiendo"/"atendido" de verdad, guarda
        el chat con el paciente) pero bajo la propia cuenta del docente --
        ver main.atender_paciente_base/cerrar_atencion_base."""
        user = self.shedule["agenda_1"][self._selected_row_key]
        estado = entry_estado_por(user, self._current_username())

        if estado == "atendiendo" and self._es_atencion_activa(self._selected_row_key):
            self._cerrar_atencion_admin_real()
            return

        if not user.case_id:
            QMessageBox.warning(self, "Atender", "Este registro no tiene un caso clínico asociado.")
            return

        if self.main_window is not None and hasattr(self.main_window, "atender_paciente_base"):
            self.main_window.atender_paciente_base(self._selected_row_key)
            self._on_selection_changed()

    def _cerrar_atencion_admin_real(self):
        """Contraparte de _cerrar_atencion() para el docente en modo
        "guardar base" (ver main.cerrar_atencion_base)."""
        if self.main_window is None or not hasattr(self.main_window, "abrir_evolucion"):
            return

        user = self.shedule["agenda_1"][self._selected_row_key]
        nombre = f"{user.nombre} {user.apellido}".strip()
        key = self._selected_row_key

        def _guardar(nota):
            return self.main_window.cerrar_atencion_base(key, nota)

        self.main_window.abrir_evolucion(nombre or "el paciente", _guardar, key)

    def _marcar_no_show(self):
        if self._selected_row_key is None:
            return

        resp = QMessageBox.question(
            self, "Marcar inasistencia",
            "¿Confirmas que el paciente no se presentó a la hora agendada?"
        )
        if resp != QMessageBox.Yes:
            return

        row = self.shedule["agenda_1"][self._selected_row_key]
        marcar_entry_no_show(row, self._current_username())
        try:
            Shedule().set(self.shedule)
        except requests.RequestException as exc:
            QMessageBox.warning(self, "Marcar inasistencia",
                                f"No hay conexión con el servidor. Inténtalo de nuevo.\n\n{exc}")
        self.actualizar()

    def _ver_ficha_paciente(self):
        if self._selected_row_key is None:
            return

        appointment_key = self._selected_row_key
        if self._modo_practica:
            appointment_key = self._intento_abierto(self._selected_row_key)
            if appointment_key is None or appointment_key not in self.shedule.get("agenda_1", {}):
                return
        row = self.shedule["agenda_1"][appointment_key]
        case_id = row.case_id or None
        if not case_id:
            QMessageBox.information(
                self, "Ver ficha", "Este registro no tiene un caso clínico asociado todavía."
            )
            return

        try:
            cases = CasesOffline().get_cases()
        except requests.RequestException as exc:
            QMessageBox.warning(self, "Ver ficha",
                                f"No hay conexión con el servidor. Inténtalo de nuevo.\n\n{exc}")
            return
        caso = cases.get(case_id, {})
        debug_print(f"[agenda_ficha] case_id={case_id!r} (type={type(case_id).__name__}) "
              f"cases_keys_sample={list(cases.keys())[:10]!r} "
              f"historia_clinica={caso.get('historia_clinica')!r}")

        html = render_ficha_html(row, caso, self.shedule, self._current_username(), self.is_admin)
        if self.main_window is not None and hasattr(self.main_window, "abrir_ficha_con"):
            self.main_window.abrir_ficha_con(
                html, lambda: self._abrir_chat_paciente(row, case_id, appointment_key)
            )

    def _abrir_chat_paciente(self, row, case_id, appointment_key):
        rut = row.rut
        nombre = f"{row.nombre} {row.apellido}".strip()
        procedimiento = row.procedimiento
        try:
            edad, _, _ = CreatePatient().get_age_from_rut(int(rut))
        except (TypeError, ValueError):
            edad = 0
        try:
            appointment_id = int(appointment_key)
        except (TypeError, ValueError):
            appointment_id = None

        if self.main_window is not None and hasattr(self.main_window, "abrir_chat_con"):
            self.main_window.abrir_chat_con(case_id, nombre or "el paciente", edad, procedimiento, appointment_id)

