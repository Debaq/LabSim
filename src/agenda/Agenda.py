# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 0.9 - Audiometro                   #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

import re
import requests
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import (QTableWidgetItem, QAbstractItemView,
                                QDateEdit, QPushButton, QMessageBox, QLineEdit,
                                QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox,
                                QCheckBox)
from PySide6.QtCore import QDate, QTime, QDateTime, Qt, QThread, Signal
from PySide6.QtGui import QColor
from agenda.UI.Ui_agenda import Ui_Form
from core.helpers import (Shedule, entry_estado_por, CasesOffline,
                          marcar_entry_no_show, obtener_hora_real_atencion,
                          obtener_nota_atencion, entry_esta_cancelada,
                          CreatePatient)


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


# Llaves {{N}} dentro de historia_clinica (N = offset en días respecto a la
# fecha de la cita, puede ser negativo). Ej.: "{{-5}} atendido por ORL" se
# resuelve a la fecha real 5 días antes de la cita agendada.
HISTORIA_CLINICA_FECHA_RE = re.compile(r"\{\{([+-]?\d+)\}\}")


def parse_fecha_agenda(texto):
    """Parsea una fecha en formato "dd-MM-yy" (año de 2 dígitos, como se
    guarda en la agenda). QDate::fromString con formato "yy" interpreta
    00-99 como 1900-1999, así que corregimos al siglo 2000 manualmente."""
    fecha = QDate.fromString(texto, "dd-MM-yy") if texto else QDate()
    if fecha.isValid() and fecha.year() < 2000:
        fecha = fecha.addYears(100)
    return fecha


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

        self.btn_chat = QPushButton("Conversar con paciente", self)
        self.btn_chat.clicked.connect(self._on_chat_clicked)
        layout.addWidget(self.btn_chat)

        self._on_chat = None

    def set_ficha(self, html, on_chat=None):
        self.texto.setHtml(html)
        self._on_chat = on_chat

    def _on_chat_clicked(self):
        if self._on_chat is not None:
            self._on_chat()


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
            keys = [k for k, v in rows.items() if v[0] and v[1] and not entry_esta_cancelada(v)]
            if not self._ver_todas:
                fecha_sel = self.date_selector.date().toString("dd-MM-yy")
                keys = [k for k in keys if rows[k][0] == fecha_sel]

        if self._filtro_texto:
            texto = self._filtro_texto
            keys = [
                k for k in keys
                if texto in " ".join(str(x) for x in rows[k][2:7]).lower()
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
        core_cols = 7
        for row_idx, key in enumerate(keys):
            user = rows[key]
            pendiente = not (user[0] and user[1])
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
            for col_idx in range(min(len(user), core_cols)):
                item = QTableWidgetItem(user[col_idx])
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

    def _on_selection_changed(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        if not selected_rows:
            self._reset_atender_button()
            self._selected_key = None
            self._selected_row_key = None
            return

        key = self.tableWidget.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        user = self.shedule["agenda_1"][key]
        tiene_caso = len(user) > 7 and bool(user[7])
        estado = entry_estado_por(user, self._current_username())
        pendiente = not (user[0] and user[1])

        self._selected_row_key = key
        self._selected_key = key if pendiente else None

        if self.is_admin:
            # Modo prueba: nunca queda "atendiendo", el botón solo depende de
            # si la cita tiene un caso clínico asociado (ver atender_paciente()).
            self.btn_atender.setText("Atender")
            self.btn_atender.setEnabled(tiene_caso)
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

        fecha_agendada = parse_fecha_agenda(user[0])
        hora_agendada = QTime.fromString(user[1], "HH:mm") if len(user) > 1 else QTime()
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

        if self.is_admin:
            # Admin: modo prueba -- carga el caso en los módulos sin marcar
            # "atendiendo" ni escribir attendances (ver main.atender_paciente_prueba).
            user = self.shedule["agenda_1"][self._selected_row_key]
            if not (len(user) > 7 and user[7]):
                QMessageBox.warning(self, "Atender", "Este registro no tiene un caso clínico asociado.")
                return
            if self.main_window is not None and hasattr(self.main_window, "atender_paciente_prueba"):
                self.main_window.atender_paciente_prueba(self._selected_row_key)
            return

        user = self.shedule["agenda_1"][self._selected_row_key]
        estado = entry_estado_por(user, self._current_username())

        if estado == "atendiendo" and self._es_atencion_activa(self._selected_row_key):
            self._cerrar_atencion()
            return

        if self.main_window is not None and hasattr(self.main_window, "atender_paciente"):
            self.main_window.atender_paciente(self._selected_row_key)

    def _cerrar_atencion(self):
        nota = self._pedir_nota_atencion()
        if nota is None:
            return

        if self.main_window is not None and hasattr(self.main_window, "cerrar_atencion"):
            self.main_window.cerrar_atencion(self._selected_row_key, nota)

    def _pedir_nota_atencion(self):
        """Pide al estudiante la descripción de la atención realizada. None si cancela."""
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Cerrar atención")
        layout = QVBoxLayout(dialogo)
        layout.addWidget(QLabel("Describe la atención realizada:"))

        texto = QTextEdit(dialogo)
        layout.addWidget(texto)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)

        dialogo.resize(420, 320)

        while True:
            if dialogo.exec() != QDialog.Accepted:
                return None
            nota = texto.toPlainText().strip()
            if nota:
                return nota
            QMessageBox.warning(self, "Cerrar atención", "Debes describir la atención realizada.")

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
        case_id = row[7] if len(row) > 7 else None
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
        html = self._render_ficha_html(row, caso)
        if self.main_window is not None and hasattr(self.main_window, "abrir_ficha_con"):
            self.main_window.abrir_ficha_con(
                html, lambda: self._abrir_chat_paciente(row, case_id, appointment_key)
            )

    def _abrir_chat_paciente(self, row, case_id, appointment_key):
        rut = row[2] if len(row) > 2 else ""
        nombre = f"{row[3] if len(row) > 3 else ''} {row[4] if len(row) > 4 else ''}".strip()
        procedimiento = row[6] if len(row) > 6 else ""
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

    def _resolver_fechas_historia_clinica(self, texto, fecha_cita_str):
        """Reemplaza cada {{N}} en texto por la fecha N días respecto a
        fecha_cita_str (formato "dd-MM-yy", mismo que row[0]). Si la fecha de
        la cita no es válida, deja la llave tal cual (mejor eso que una fecha
        inventada)."""
        if not texto:
            return texto
        fecha_cita = parse_fecha_agenda(fecha_cita_str)

        def _reemplazar(match):
            if not fecha_cita.isValid():
                return match.group(0)
            return fecha_cita.addDays(int(match.group(1))).toString("dd-MM-yyyy")

        return HISTORIA_CLINICA_FECHA_RE.sub(_reemplazar, texto)

    def _render_ficha_html(self, row, caso):
        rut = row[2] if len(row) > 2 else ""
        nombre = row[3] if len(row) > 3 else ""
        apellidos = row[4] if len(row) > 4 else ""
        fecha_nac = row[5] if len(row) > 5 else ""
        procedimiento = row[6] if len(row) > 6 else ""
        fecha_hora = f"{row[0]} {row[1]}".strip() if len(row) > 1 else ""

        partes = ["<h3>Datos del paciente</h3>"]
        partes.append(f"<p><b>Nombre:</b> {nombre} {apellidos}<br>"
                       f"<b>Rut:</b> {rut}<br>"
                       f"<b>Fecha de nacimiento:</b> {fecha_nac}<br>"
                       f"<b>Procedimiento:</b> {procedimiento}<br>"
                       f"<b>Cita agendada:</b> {fecha_hora or 'sin agendar'}</p>")

        username = self._current_username()
        hora_real = obtener_hora_real_atencion(row, username)
        if hora_real:
            partes.append("<h3>Puntualidad</h3>")
            hora_agendada = QTime.fromString(row[1], "HH:mm") if len(row) > 1 else QTime()
            hora_inicio = QTime.fromString(hora_real, "HH:mm:ss")
            if hora_agendada.isValid() and hora_inicio.isValid():
                minutos = hora_agendada.secsTo(hora_inicio) // 60
                if minutos <= 0:
                    resumen = "a tiempo"
                else:
                    resumen = f"{minutos} min de atraso"
            else:
                resumen = ""
            partes.append(f"<p><b>Hora agendada:</b> {row[1]}<br>"
                           f"<b>Inicio real:</b> {hora_real} ({resumen})</p>")

        partes.append("<h3>Historial de atenciones</h3>")
        items = ""

        historia_clinica = caso.get("historia_clinica", "") if isinstance(caso, dict) else ""
        if historia_clinica:
            historia_resuelta = self._resolver_fechas_historia_clinica(historia_clinica, row[0] if len(row) > 0 else "")
            items += f"<li><b>Historia clínica:</b> {historia_resuelta}</li>"

        historial = self._historial_atenciones(rut)
        items += "".join(
            f"<li><b>{fecha or 'sin fecha'} {hora}</b> — {alumno}: "
            f"{nota or 'sin comentario'}</li>"
            for fecha, hora, alumno, nota in historial
        )

        if items:
            partes.append(f"<ul>{items}</ul>")
        else:
            partes.append("<p>Sin atenciones cerradas registradas para este paciente.</p>")

        return "".join(partes)

    def _historial_atenciones(self, rut):
        """
        Recopila, para todas las citas (filas de agenda) del mismo paciente (mismo rut),
        las atenciones cerradas por cada alumno, ordenadas cronológicamente.
        Devuelve lista de tuplas (fecha, hora_real, alumno, nota).
        """
        username = self._current_username()
        historial = []
        for otra_row in self.shedule.get("agenda_1", {}).values():
            if len(otra_row) <= 2 or otra_row[2] != rut:
                continue
            atencion = otra_row[8] if len(otra_row) > 8 and isinstance(otra_row[8], dict) else {}
            fecha = otra_row[0] if len(otra_row) > 0 else ""
            for alumno, datos in atencion.items():
                if not isinstance(datos, dict) or datos.get("estado") != "atendido":
                    continue
                if not self.is_admin and alumno != username:
                    continue
                nota = datos.get("nota", "")
                hora_real = datos.get("hora_real", "")
                historial.append((fecha, hora_real, alumno, nota))

        def _orden(item):
            fecha, hora_real = item[0], item[1]
            dt = QDateTime(
                parse_fecha_agenda(fecha),
                QTime.fromString(hora_real, "HH:mm:ss") if hora_real else QTime(),
            )
            return dt

        historial.sort(key=_orden)
        return historial
