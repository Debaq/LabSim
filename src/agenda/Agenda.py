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
from PySide6.QtCore import QDate, QTime, QDateTime, Qt, QThread, Signal
from PySide6.QtGui import QColor
from agenda.UI.Ui_agenda import Ui_Form
from core.helpers import (Shedule, entry_estado_por, CasesOffline,
                          marcar_entry_no_show,
                          obtener_nota_atencion, entry_esta_cancelada,
                          CreatePatient)
from core.ficha import parse_fecha_agenda, render_ficha_html


class _SheduleFetchThread(QThread):
    """Trae Shedule() (llamada de red) fuera del hilo de UI.

    Mismo patrón silencioso que SyncThread.sync_failed: si el backend no
    responde, no hay diálogo ni excepción -- se reintenta en el próximo
    ciclo de polling."""
    fetched = Signal(dict)
    failed = Signal(str)

    def run(self):
        try:
            data = Shedule().get()
        except requests.RequestException as exc:
            self.failed.emit(str(exc))
            return
        self.fetched.emit(data)


PENDIENTE_COLOR = QColor(255, 244, 200)
ATENDIENDO_COLOR = QColor(200, 224, 247)
ATENDIDO_COLOR = QColor(210, 235, 210)
NO_SHOW_COLOR = QColor(235, 190, 190)
CANCELADA_COLOR = QColor(225, 225, 225)


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

    def set_contexto(self, nombre_paciente, on_guardar):
        self.lbl_paciente.setText(f"Paciente: {nombre_paciente}")
        self.texto.clear()
        self._on_guardar = on_guardar

    def _on_guardar_clicked(self):
        nota = self.texto.toPlainText().strip()
        if not nota:
            QMessageBox.warning(self, "Evolución", "Debes describir la evolución del paciente.")
            return

        if self._on_guardar is not None:
            self._on_guardar(nota)
        self.texto.clear()

        padre = self.parent()
        if padre is not None and hasattr(padre, "hide_window"):
            padre.hide_window()


class Agenda(QWidget, Ui_Form):
    def __init__(self, permissions, obj):
        # Inicialización de la ventana y propiedades
        #super(Audiometer, self).__init__()
        super().__init__()
        self.setupUi(self)

        self.is_admin = permissions == 777
        self.main_window = obj
        self._selected_key = None
        self._selected_row_key = None
        self._loading = False
        self._ver_todas = False
        self._filtro_texto = ""
        self._prueba_atendiendo_key = None
        self._guardar_base = False

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

        self.chk_ver_todas = QCheckBox("Ver todas las citas habilitadas", self)
        self.chk_ver_todas.toggled.connect(self._on_toggle_ver_todas)
        self.horizontalLayout.insertWidget(2, self.chk_ver_todas)

        self.btn_ver_ficha = QPushButton("Ver ficha", self)
        self.btn_ver_ficha.setEnabled(False)
        self.btn_ver_ficha.clicked.connect(self._ver_ficha_paciente)
        self.horizontalLayout.insertWidget(3, self.btn_ver_ficha)

        self.btn_atender = QPushButton("Atender", self)
        self.btn_atender.setEnabled(False)
        self.btn_atender.clicked.connect(self.atender_paciente)
        self.horizontalLayout.insertWidget(4, self.btn_atender)

        self.btn_no_show = QPushButton("No se presentó", self)
        self.btn_no_show.setEnabled(False)
        self.btn_no_show.clicked.connect(self._marcar_no_show)
        self.horizontalLayout.insertWidget(5, self.btn_no_show)

        if self.is_admin:
            # El admin ve todos los pacientes siempre (ver _visible_keys):
            # el filtro por fecha / "ver todas" es solo para el estudiante.
            self.date_selector.setVisible(False)
            self.chk_ver_todas.setVisible(False)

            # Solo admin/docente: elegir si su "Atender" es una prueba sin
            # rastro (por defecto, ver atender_paciente_prueba) o si queda
            # guardado de verdad con su propia cuenta (attendances + chat) --
            # para armar una atención base con la que comparar a los
            # alumnos después (ver main.atender_paciente_base). Deshabilitado
            # mientras hay una atención en curso para no cambiar de modo a
            # mitad de camino.
            self.chk_guardar_base = QCheckBox("Guardar esta atención (base para comparar)", self)
            self.chk_guardar_base.toggled.connect(self._on_toggle_guardar_base)
            self.horizontalLayout.insertWidget(6, self.chk_guardar_base)

    def _on_toggle_guardar_base(self, checked):
        self._guardar_base = checked

    def _on_toggle_ver_todas(self, checked):
        self._ver_todas = checked
        self.date_selector.setEnabled(not checked)
        self.populate_shedule()

    def _on_fecha_seleccionada(self, _qdate):
        self.populate_shedule()

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

        Usado por el polling de fondo (main._on_backend_sync): ese refresh
        dispara SIEMPRE una consulta nueva a Shedule() (get_full_state), y si
        se hacía en el hilo de UI, un backend caído congelaba la ventana
        completa (timeout SSL de hasta 10s, cada ciclo de sync)."""
        if getattr(self, "_shedule_fetch_thread", None) is not None and self._shedule_fetch_thread.isRunning():
            return
        self._shedule_fetch_thread = _SheduleFetchThread(self)
        self._shedule_fetch_thread.fetched.connect(self._on_refresh_async_done)
        self._shedule_fetch_thread.start()

    def _on_refresh_async_done(self, data):
        self.shedule = data
        self.populate_shedule()

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
            keys = [k for k, v in rows.items() if v.fecha and v.hora and not entry_esta_cancelada(v)]
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
            if entry_esta_cancelada(user):
                color = CANCELADA_COLOR
            elif pendiente:
                color = PENDIENTE_COLOR
            elif estado == "atendiendo":
                color = ATENDIENDO_COLOR
            elif estado == "atendido":
                color = ATENDIDO_COLOR
            elif estado == "no_show":
                color = NO_SHOW_COLOR
            columnas = (user.fecha, user.hora, user.rut, user.nombre,
                        user.apellido, user.fecha_nac, user.procedimiento)
            for col_idx, valor in enumerate(columnas):
                item = QTableWidgetItem(valor)
                item.setData(Qt.UserRole, key)
                if color is not None:
                    item.setBackground(color)
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

    def _reset_atender_button(self):
        self.btn_atender.setText("Atender")
        self.btn_atender.setEnabled(False)
        self.btn_ver_ficha.setEnabled(False)
        self.btn_no_show.setEnabled(False)
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
        user = self.shedule["agenda_1"][key]
        tiene_caso = bool(user.case_id)
        estado = entry_estado_por(user, self._current_username())
        pendiente = not (user.fecha and user.hora)

        self._selected_row_key = key
        self._selected_key = key if pendiente else None

        if self.is_admin and self._guardar_base:
            # Guardar base: mismo ciclo real que el alumno (marca "atendiendo"/
            # "atendido" de verdad, con la propia cuenta del docente) -- ver
            # main.atender_paciente_base/cerrar_atencion_base.
            if estado == "atendiendo" and self._es_atencion_activa(key):
                self.btn_atender.setText("Cerrar atención")
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
        elif self.is_admin:
            # Modo prueba (por defecto): no queda "atendiendo" en la agenda ni
            # se escribe en red, pero el botón sí simula el ciclo completo
            # atender/cerrar (ver atender_paciente() y _cerrar_atencion_prueba()).
            if self._prueba_atendiendo_key == key and self._es_atencion_activa(key):
                self.btn_atender.setText("Cerrar atención")
                self.btn_atender.setEnabled(tiene_caso)
            else:
                self.btn_atender.setText("Atender")
                self.btn_atender.setEnabled(tiene_caso)
            self.chk_guardar_base.setEnabled(
                not (self._prueba_atendiendo_key == key and self._es_atencion_activa(key))
            )
        elif estado == "atendiendo" and self._es_atencion_activa(key):
            self.btn_atender.setText("Cerrar atención")
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

        if self.is_admin and self._guardar_base:
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
            self.main_window.cerrar_atencion(key, nota)

        self.main_window.abrir_evolucion(nombre or "el paciente", _guardar)

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
            self.main_window.cerrar_atencion_base(key, nota)

        self.main_window.abrir_evolucion(nombre or "el paciente", _guardar)

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
        Shedule().set(self.shedule)
        self.refresh()

    def _ver_ficha_paciente(self):
        if self._selected_row_key is None:
            return

        row = self.shedule["agenda_1"][self._selected_row_key]
        case_id = row.case_id or None
        if not case_id:
            QMessageBox.information(
                self, "Ver ficha", "Este registro no tiene un caso clínico asociado todavía."
            )
            return

        cases = CasesOffline().get_cases()
        caso = cases.get(case_id, {})
        print(f"[agenda_ficha] case_id={case_id!r} (type={type(case_id).__name__}) "
              f"cases_keys_sample={list(cases.keys())[:10]!r} "
              f"historia_clinica={caso.get('historia_clinica')!r}")

        appointment_key = self._selected_row_key
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

