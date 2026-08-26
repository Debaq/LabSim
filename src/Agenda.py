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
                                QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox)
from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtGui import QColor
from UI.Ui_agenda import Ui_Form
from lib.helpers import Shedule, entry_estado_por


PENDIENTE_COLOR = QColor(255, 244, 200)
ATENDIENDO_COLOR = QColor(200, 224, 247)
ATENDIDO_COLOR = QColor(210, 235, 210)


NOTE_COL = 7


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

        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._configurar_edicion()

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
        self.btn_atender = QPushButton("Atender", self)
        self.btn_atender.setEnabled(False)
        self.btn_atender.clicked.connect(self.atender_paciente)
        self.horizontalLayout.insertWidget(0, self.btn_atender)
        if self.is_admin:
            # El admin no atiende pacientes: para probar la atención se usa un usuario básico.
            self.btn_atender.setVisible(False)

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

        self.horizontalLayout.insertWidget(1, self.date_habilitar)
        self.horizontalLayout.insertWidget(2, self.time_habilitar)
        self.horizontalLayout.insertWidget(3, self.btn_habilitar)
        self.horizontalLayout.insertWidget(4, self.btn_eliminar)
        self.horizontalLayout.insertWidget(5, self.btn_ver_editar)
        self.horizontalLayout.insertWidget(6, self.led_nota)
        self.horizontalLayout.insertWidget(7, self.btn_guardar_nota)

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
            return list(rows.keys())
        return [k for k, v in rows.items() if v[0] and v[1]]

    def populate_shedule(self, agenda="agenda_1"):
        rows = self.shedule.get(agenda, {})
        keys = self._visible_keys(agenda)

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
            if pendiente:
                color = PENDIENTE_COLOR
            elif estado == "atendiendo":
                color = ATENDIENDO_COLOR
            elif estado == "atendido":
                color = ATENDIDO_COLOR
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

        self._reset_atender_button()
        if self.is_admin:
            self.btn_habilitar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            self.btn_ver_editar.setEnabled(False)
            self.led_nota.setEnabled(False)
            self.led_nota.clear()
            self.btn_guardar_nota.setEnabled(False)
        self._selected_key = None
        self._selected_row_key = None

    def _reset_atender_button(self):
        self.btn_atender.setText("Atender")
        self.btn_atender.setEnabled(False)

    def _on_selection_changed(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        if not selected_rows:
            self._reset_atender_button()
            if self.is_admin:
                self.btn_habilitar.setEnabled(False)
                self.btn_eliminar.setEnabled(False)
                self.btn_ver_editar.setEnabled(False)
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
        elif estado == "atendiendo":
            self.btn_atender.setText("Cerrar atención")
            self.btn_atender.setEnabled(tiene_caso)
        elif estado == "atendido":
            self.btn_atender.setText("Atender")
            self.btn_atender.setEnabled(False)
        else:
            self.btn_atender.setText("Atender")
            self.btn_atender.setEnabled(tiene_caso and not pendiente)

        if self.is_admin:
            self.btn_habilitar.setEnabled(pendiente)
            self.btn_eliminar.setEnabled(True)
            self.btn_ver_editar.setEnabled(tiene_caso)
            self.led_nota.setEnabled(True)
            self.led_nota.setText(user[9] if len(user) > 9 else "")
            self.btn_guardar_nota.setEnabled(True)

    def habilitar_paciente(self):
        if self._selected_key is None:
            return

        fecha = self.date_habilitar.date().toString("dd-MM-yy")
        hora = self.time_habilitar.time().toString("HH:mm")

        row = self.shedule["agenda_1"][self._selected_key]
        row[0] = fecha
        row[1] = hora

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

        row[col] = item.text()
        Shedule().set(self.shedule)

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
            self._editar_fecha(row)
        else:
            self._editar_hora(row)

    def _editar_fecha(self, row):
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

        row[0] = date_edit.date().toString("dd-MM-yy")
        Shedule().set(self.shedule)
        self.refresh()

    def _editar_hora(self, row):
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

        row[1] = time_edit.time().toString("HH:mm")
        Shedule().set(self.shedule)
        self.refresh()

    def atender_paciente(self):
        if self.is_admin or self._selected_row_key is None:
            return

        user = self.shedule["agenda_1"][self._selected_row_key]
        estado = entry_estado_por(user, self._current_username())

        if estado == "atendiendo":
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
