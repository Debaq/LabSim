# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : AudioSim                   #
#                       VER. 0.9 - Audiometro                   #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#   NOTA: si no hablas español, no es mi culpa, aprende         #
#################################################################

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import (QTableWidgetItem, QAbstractItemView,
                                QDateEdit, QTimeEdit, QPushButton, QMessageBox, QLineEdit,
                                QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox,
                                QCheckBox)
from PySide6.QtCore import QDate, QTime, QDateTime, Qt
from PySide6.QtGui import QColor
from UI.Ui_agenda import Ui_Form
from lib.helpers import (Shedule, entry_estado_por, CasesOffline,
                          marcar_entry_no_show, obtener_hora_real_atencion,
                          obtener_nota_atencion, entry_esta_cancelada, marcar_entry_cancelada)


PENDIENTE_COLOR = QColor(255, 244, 200)
ATENDIENDO_COLOR = QColor(200, 224, 247)
ATENDIDO_COLOR = QColor(210, 235, 210)
NO_SHOW_COLOR = QColor(235, 190, 190)
CANCELADA_COLOR = QColor(225, 225, 225)


NOTE_COL = 7

ANTECEDENTES_LABELS = {
    "hipoacusia_familiar": "Hipoacusia familiar",
    "ototoxicos": "Uso de ototóxicos",
    "trauma_acustico": "Trauma acústico",
    "otitis": "Otitis",
    "meningitis": "Meningitis",
    "tce": "TCE (traumatismo craneoencefálico)",
    "diabetes": "Diabetes",
    "hta": "Hipertensión arterial (HTA)",
}


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
        self._configurar_edicion()

        self.led_buscar = QLineEdit(self)
        self.led_buscar.setPlaceholderText("Buscar por RUT, nombre o apellido...")
        self.led_buscar.textChanged.connect(self._on_filtro_changed)
        self.horizontalLayout.insertWidget(0, self.led_buscar)

        self._build_atender_control()
        if self.is_admin:
            self._build_admin_controls()

        self.tableWidget.itemSelectionChanged.connect(self._on_selection_changed)
        self.tableWidget.itemChanged.connect(self._on_item_changed)
        self.tableWidget.cellDoubleClicked.connect(self._on_cell_double_clicked)

        self.read_shedule()
        self.populate_shedule()

        if self.is_admin:
            self.pushButton.setEnabled(True)
            self.pushButton.clicked.connect(lambda:self.create_case(obj))
        else:
            self.pushButton.setEnabled(False)

    def _configurar_edicion(self):
        """Solo el admin puede editar celdas de la tabla; el resto solo mira."""
        if self.is_admin:
            self.tableWidget.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        else:
            self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

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
            # El admin no atiende pacientes: para probar la atención se usa un usuario básico.
            self.date_selector.setVisible(False)
            self.chk_ver_todas.setVisible(False)
            self.btn_ver_ficha.setVisible(False)
            self.btn_atender.setVisible(False)
            self.btn_no_show.setVisible(False)

    def _on_toggle_ver_todas(self, checked):
        self._ver_todas = checked
        self.date_selector.setEnabled(not checked)
        self.populate_shedule()

    def _on_fecha_seleccionada(self, _qdate):
        self.populate_shedule()

    def _on_filtro_changed(self, texto):
        self._filtro_texto = texto.strip().lower()
        self.populate_shedule()

    def _build_admin_controls(self):
        self.date_habilitar = QDateEdit(self)
        self.date_habilitar.setCalendarPopup(True)
        self.date_habilitar.setDate(QDate.currentDate())

        self.time_habilitar = QTimeEdit(self)
        self.time_habilitar.setTime(QTime.currentTime())

        self.btn_habilitar = QPushButton("Habilitar", self)
        self.btn_habilitar.setEnabled(False)
        self.btn_habilitar.clicked.connect(self.habilitar_paciente)

        self.btn_eliminar = QPushButton("Eliminar", self)
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.clicked.connect(self.eliminar_paciente)

        self.btn_ver_editar = QPushButton("Ver/Editar", self)
        self.btn_ver_editar.setEnabled(False)
        self.btn_ver_editar.clicked.connect(self.ver_editar_paciente)

        self.led_nota = QLineEdit(self)
        self.led_nota.setPlaceholderText("Nota interna (solo admin)")
        self.led_nota.setEnabled(False)

        self.btn_guardar_nota = QPushButton("Guardar nota", self)
        self.btn_guardar_nota.setEnabled(False)
        self.btn_guardar_nota.clicked.connect(self.guardar_nota)

        self.btn_cancelar_restaurar = QPushButton("Cancelar cita", self)
        self.btn_cancelar_restaurar.setEnabled(False)
        self.btn_cancelar_restaurar.clicked.connect(self._toggle_cancelada)

        self.horizontalLayout.insertWidget(6, self.date_habilitar)
        self.horizontalLayout.insertWidget(7, self.time_habilitar)
        self.horizontalLayout.insertWidget(8, self.btn_habilitar)
        self.horizontalLayout.insertWidget(9, self.btn_eliminar)
        self.horizontalLayout.insertWidget(10, self.btn_ver_editar)
        self.horizontalLayout.insertWidget(11, self.btn_cancelar_restaurar)
        self.horizontalLayout.insertWidget(12, self.led_nota)
        self.horizontalLayout.insertWidget(13, self.btn_guardar_nota)

        self.tableWidget.setColumnCount(8)
        self.tableWidget.setHorizontalHeaderItem(NOTE_COL, QTableWidgetItem("Nota (solo admin)"))

    def create_case(self,obj):
        create_win = obj.subw.get("CREATE_A")
        if create_win is not None:
            create_win.obj.reset_form()
        obj.activate_auto("CREATE_A")

    def ver_editar_paciente(self):
        if self._selected_row_key is None:
            return

        row = self.shedule["agenda_1"][self._selected_row_key]
        case_id = row[7] if len(row) > 7 else None
        if not case_id:
            QMessageBox.warning(self, "Ver/Editar paciente", "Este registro no tiene un caso asociado.")
            return

        self.main_window.activate_auto("CREATE_A")
        create_win = self.main_window.subw.get("CREATE_A")
        if create_win is not None:
            create_win.obj.load_for_edit(case_id, self._selected_row_key, row)

    def guardar_nota(self):
        if self._selected_row_key is None:
            return

        row = self.shedule["agenda_1"][self._selected_row_key]
        while len(row) <= 8:
            row.append({})
        while len(row) <= 9:
            row.append("")
        row[9] = self.led_nota.text()

        Shedule().set(self.shedule)
        self.refresh()


    def read_shedule(self):
        shedule = Shedule()
        self.shedule = shedule.get()

    def refresh(self):
        self.read_shedule()
        self.populate_shedule()

    def _current_username(self):
        data_login = getattr(self.main_window, "data_login", None) or {}
        return data_login.get("user")

    def _visible_keys(self, agenda="agenda_1"):
        rows = self.shedule.get(agenda, {})
        if self.is_admin:
            keys = list(rows.keys())
        else:
            keys = [k for k, v in rows.items() if v[0] and v[1] and not entry_esta_cancelada(v)]
            if not self._ver_todas:
                fecha_sel = self.date_selector.date().toString("dd-MM-yy")
                print(f"[agenda_filter] total_rows={len(rows)} con_fecha_hora={len(keys)} "
                      f"fecha_sel={fecha_sel!r} ver_todas={self._ver_todas}")
                for k in keys:
                    print(f"[agenda_filter]   key={k!r} fecha_fila={rows[k][0]!r} match={rows[k][0] == fecha_sel}")
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
        # Fecha y Hora se editan solo con los widgets emergentes (doble click), nunca en línea.
        cols_no_editables_inline = {0, 1}
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
                if not self.is_admin or col_idx in cols_no_editables_inline:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tableWidget.setItem(row_idx, col_idx, item)

            if self.is_admin:
                nota = user[9] if len(user) > 9 else ""
                nota_item = QTableWidgetItem(nota)
                nota_item.setData(Qt.UserRole, key)
                if color is not None:
                    nota_item.setBackground(color)
                # La nota interna se edita solo vía led_nota/Guardar nota, no en línea.
                nota_item.setFlags(nota_item.flags() & ~Qt.ItemIsEditable)
                self.tableWidget.setItem(row_idx, NOTE_COL, nota_item)
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
            if self.is_admin:
                self.btn_habilitar.setEnabled(False)
                self.btn_eliminar.setEnabled(False)
                self.btn_ver_editar.setEnabled(False)
                self.btn_cancelar_restaurar.setText("Cancelar cita")
                self.btn_cancelar_restaurar.setEnabled(False)
                self.led_nota.setEnabled(False)
                self.led_nota.clear()
                self.btn_guardar_nota.setEnabled(False)
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
            if self.is_admin:
                self.btn_habilitar.setEnabled(False)
                self.btn_eliminar.setEnabled(False)
                self.btn_ver_editar.setEnabled(False)
                self.btn_cancelar_restaurar.setText("Cancelar cita")
                self.btn_cancelar_restaurar.setEnabled(False)
                self.led_nota.setEnabled(False)
                self.led_nota.clear()
                self.btn_guardar_nota.setEnabled(False)
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
            pass  # el admin no atiende pacientes; btn_atender queda oculto/deshabilitado
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

        if not self.is_admin:
            self.btn_ver_ficha.setEnabled(tiene_caso)

            fecha_agendada = QDate.fromString(user[0], "dd-MM-yy") if user[0] else QDate()
            hora_agendada = QTime.fromString(user[1], "HH:mm") if len(user) > 1 else QTime()
            hora_vencida = (
                not pendiente and fecha_agendada.isValid() and hora_agendada.isValid()
                and QDateTime(fecha_agendada, hora_agendada) < QDateTime.currentDateTime()
            )
            self.btn_no_show.setEnabled(hora_vencida and estado is None)

        if self.is_admin:
            cancelada = entry_esta_cancelada(user)
            self.btn_habilitar.setEnabled(pendiente)
            self.btn_eliminar.setEnabled(True)
            self.btn_ver_editar.setEnabled(tiene_caso)
            self.btn_cancelar_restaurar.setText("Restaurar cita" if cancelada else "Cancelar cita")
            self.btn_cancelar_restaurar.setEnabled(not pendiente)
            self.led_nota.setEnabled(True)
            self.led_nota.setText(user[9] if len(user) > 9 else "")
            self.btn_guardar_nota.setEnabled(True)

    def _existe_choque_horario(self, fecha, hora, excluir_key=None):
        rows = self.shedule.get("agenda_1", {})
        for k, v in rows.items():
            if k == excluir_key or entry_esta_cancelada(v):
                continue
            if len(v) > 1 and v[0] == fecha and v[1] == hora:
                return True
        return False

    def habilitar_paciente(self):
        if self._selected_key is None:
            return

        fecha = self.date_habilitar.date().toString("dd-MM-yy")
        hora = self.time_habilitar.time().toString("HH:mm")

        if self._existe_choque_horario(fecha, hora, excluir_key=self._selected_key):
            QMessageBox.warning(self, "Habilitar paciente", "Ya existe una cita agendada en esa fecha y hora.")
            return

        row = self.shedule["agenda_1"][self._selected_key]
        row[0] = fecha
        row[1] = hora

        Shedule().set(self.shedule)
        self.refresh()

    def _toggle_cancelada(self):
        if self._selected_row_key is None:
            return

        row = self.shedule["agenda_1"][self._selected_row_key]
        cancelar = not entry_esta_cancelada(row)
        if cancelar:
            resp = QMessageBox.question(
                self, "Cancelar cita",
                "¿Cancelar esta cita? El registro y el caso asociado se conservan; "
                "el alumno dejará de verla hasta que se restaure."
            )
            if resp != QMessageBox.Yes:
                return

        marcar_entry_cancelada(row, cancelar)
        Shedule().set(self.shedule)
        self.refresh()

    def eliminar_paciente(self):
        if self._selected_row_key is None:
            return

        user = self.shedule["agenda_1"][self._selected_row_key]
        nombre = f"{user[3]} {user[4]}".strip()
        resp = QMessageBox.question(
            self, "Eliminar paciente",
            f"¿Eliminar a {nombre or 'este paciente'} de la agenda? Esta acción no se puede deshacer."
        )
        if resp != QMessageBox.Yes:
            return

        del self.shedule["agenda_1"][self._selected_row_key]
        Shedule().set(self.shedule)
        self.refresh()

    def _on_item_changed(self, item):
        """Persiste en la base (schedule.json) una celda editada en línea por el admin."""
        if self._loading or not self.is_admin:
            return
        col = item.column()
        if col in (0, 1, NOTE_COL):
            return  # fecha/hora usan widgets emergentes; nota usa led_nota

        key = item.data(Qt.UserRole)
        row = self.shedule.get("agenda_1", {}).get(key) if key is not None else None
        if row is None or col >= len(row):
            return

        valor_anterior = row[col]
        row[col] = item.text()
        try:
            Shedule().set(self.shedule)
        except Exception as e:
            # En modo backend esto empuja por red (appointment_upsert.php) --
            # sin este catch, un timeout o un 401 revienta el slot en
            # silencio: la celda queda mostrando el valor editado pero nunca
            # llegó al servidor, y el próximo refresh la pisa con el valor
            # viejo sin que el admin entienda por qué.
            row[col] = valor_anterior
            QMessageBox.critical(self, "Editar cita", f"No se pudo guardar en el servidor:\n{e}")
            self.refresh()
            return

        self.refresh()

    def _on_cell_double_clicked(self, row_idx, col_idx):
        """Doble click en Fecha/Hora abre un selector en vez de edición de texto."""
        if not self.is_admin or col_idx not in (0, 1):
            return

        item = self.tableWidget.item(row_idx, col_idx)
        key = item.data(Qt.UserRole) if item is not None else None
        row = self.shedule.get("agenda_1", {}).get(key) if key is not None else None
        if row is None:
            return

        if col_idx == 0:
            self._editar_fecha(row, key)
        else:
            self._editar_hora(row, key)

    def _editar_fecha(self, row, key):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Editar fecha")
        layout = QVBoxLayout(dialogo)

        date_edit = QDateEdit(dialogo)
        date_edit.setCalendarPopup(True)
        actual = QDate.fromString(row[0], "dd-MM-yy") if row[0] else QDate()
        date_edit.setDate(actual if actual.isValid() else QDate.currentDate())
        layout.addWidget(date_edit)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        nueva_fecha = date_edit.date().toString("dd-MM-yy")
        if self._existe_choque_horario(nueva_fecha, row[1], excluir_key=key):
            QMessageBox.warning(self, "Editar fecha", "Ya existe otra cita en esa fecha y hora.")
            return

        row[0] = nueva_fecha
        Shedule().set(self.shedule)
        self.refresh()

    def _editar_hora(self, row, key):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Editar hora")
        layout = QVBoxLayout(dialogo)

        time_edit = QTimeEdit(dialogo)
        actual = QTime.fromString(row[1], "HH:mm") if row[1] else QTime()
        time_edit.setTime(actual if actual.isValid() else QTime.currentTime())
        layout.addWidget(time_edit)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        nueva_hora = time_edit.time().toString("HH:mm")
        if self._existe_choque_horario(row[0], nueva_hora, excluir_key=key):
            QMessageBox.warning(self, "Editar hora", "Ya existe otra cita en esa fecha y hora.")
            return

        row[1] = nueva_hora
        Shedule().set(self.shedule)
        self.refresh()

    def _es_atencion_activa(self, key):
        """True si `key` es el paciente que está cargado ahora mismo en los módulos."""
        return getattr(self.main_window, "data_current_key", None) == key

    def atender_paciente(self):
        if self.is_admin or self._selected_row_key is None:
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
        if self.is_admin or self._selected_row_key is None:
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

        caso = CasesOffline().get_cases().get(case_id, {})
        self._mostrar_dialogo_ficha(row, caso)

    def _mostrar_dialogo_ficha(self, row, caso):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Ficha del paciente")
        layout = QVBoxLayout(dialogo)

        texto = QTextEdit(dialogo)
        texto.setReadOnly(True)
        texto.setHtml(self._render_ficha_html(row, caso))
        layout.addWidget(texto)

        botones = QDialogButtonBox(QDialogButtonBox.Ok)
        botones.accepted.connect(dialogo.accept)
        layout.addWidget(botones)

        dialogo.resize(480, 520)
        dialogo.exec()

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

        anamnesis = caso.get("Anamnesis", {}) if isinstance(caso, dict) else {}
        antecedentes = anamnesis.get("antecedentes", {}) if isinstance(anamnesis, dict) else {}
        activos = [label for key, label in ANTECEDENTES_LABELS.items() if antecedentes.get(key)]

        partes.append("<h3>Anamnesis</h3>")
        if activos:
            items = "".join(f"<li>{label}</li>" for label in activos)
            partes.append(f"<p><b>Antecedentes:</b></p><ul>{items}</ul>")
        else:
            partes.append("<p><b>Antecedentes:</b> sin antecedentes relevantes.</p>")

        medicamentos = anamnesis.get("medicamentos", "") if isinstance(anamnesis, dict) else ""
        cirugias = anamnesis.get("cirugias", "") if isinstance(anamnesis, dict) else ""
        otros = anamnesis.get("otros", "") if isinstance(anamnesis, dict) else ""
        partes.append(f"<p><b>Medicamentos:</b> {medicamentos or 'No refiere'}<br>"
                       f"<b>Cirugías:</b> {cirugias or 'No refiere'}</p>")
        partes.append(f"<p><b>Motivo de consulta / relato clínico:</b><br>{otros or 'Sin registro.'}</p>")

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
        historial = self._historial_atenciones(rut)
        if historial:
            items = "".join(
                f"<li><b>{fecha or 'sin fecha'} {hora}</b> — {alumno}: "
                f"{nota or 'sin comentario'}</li>"
                for fecha, hora, alumno, nota in historial
            )
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
                QDate.fromString(fecha, "dd-MM-yy") if fecha else QDate(),
                QTime.fromString(hora_real, "HH:mm:ss") if hora_real else QTime(),
            )
            return dt

        historial.sort(key=_orden)
        return historial
