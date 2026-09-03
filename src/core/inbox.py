# -*- coding: utf-8 -*-
"""Bandeja de entrada de la app de escritorio.

Botón "Bandeja de entrada" que vive al lado del botón de Agenda (ver
ui_helpers.ToolBar.chargeBtnsArea) -- visible para cualquier rol logueado
(alumno o docente/admin, este último para poder probarla sin necesitar un
usuario alumno aparte). Lee/marca-leído contra inbox_messages en el backend
(ver core.helpers.inbox_list/inbox_marcar_leido -> public/api/inbox.php):
mensajes automáticos sobre el trato a pacientes (ver OirsEvaluator.php) y
mensajes que un docente mandó a mano desde Admin -> Bandeja de entrada.

Vive como subventana del MDI (ver main.py: self.subw["INBOX"]), igual que
Agenda o el chat con el paciente, en vez de un diálogo emergente."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QPushButton, QWidget, QVBoxLayout, QTextEdit,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QAbstractItemView)

from core.helpers import inbox_list, inbox_marcar_leido

BTN_OBJECT_NAME = "btn_bandeja_oirs"
COLUMNAS = ("De", "Asunto", "Fecha y hora")


class InboxWidget(QWidget):
    """Tabla de mensajes (remitente/asunto/fecha) arriba, cuerpo del
    seleccionado abajo. refresh() recarga la lista contra el backend --
    se llama cada vez que se abre la subventana, no solo al crearla."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._main_window = main_window

        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, len(COLUMNAS), self)
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self._mostrar_seleccion)
        layout.addWidget(self.tabla)

        self.cuerpo = QTextEdit(self)
        self.cuerpo.setReadOnly(True)
        layout.addWidget(self.cuerpo)

    def refresh(self):
        """Recarga los mensajes desde el backend y repuebla la tabla."""
        items = inbox_list()
        self.cuerpo.clear()
        self.tabla.setRowCount(len(items))
        for row, it in enumerate(items):
            self._llenar_fila(row, it)
        self.tabla.resizeColumnsToContents()
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        if not items:
            self.cuerpo.setPlainText("Sin mensajes todavía.")
        if self._main_window is not None:
            actualizar_badge(self._main_window)

    def _llenar_fila(self, row, it):
        remitente = it.get("remitente") or "Sistema"
        marca = "● " if not it.get("leido") else ""
        de_item = QTableWidgetItem(f"{marca}{remitente}")
        asunto_item = QTableWidgetItem(it.get("asunto", ""))
        fecha_item = QTableWidgetItem(it.get("created_at", ""))
        for item in (de_item, asunto_item, fecha_item):
            item.setData(Qt.UserRole, it)
            if not it.get("leido"):
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)
        self.tabla.setItem(row, 0, de_item)
        self.tabla.setItem(row, 1, asunto_item)
        self.tabla.setItem(row, 2, fecha_item)

    def _mostrar_seleccion(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return
        row = filas[0].row()
        it = self.tabla.item(row, 0).data(Qt.UserRole)
        self.cuerpo.setPlainText(f"Asunto: {it.get('asunto', '')}\n\n{it.get('cuerpo', '')}")
        if not it.get("leido"):
            inbox_marcar_leido(int(it["id"]))
            it["leido"] = 1
            self._llenar_fila(row, it)
            self.tabla.selectRow(row)
            if self._main_window is not None:
                actualizar_badge(self._main_window)


def crear_boton(main_window, layout):
    """Crea el botón y lo agrega a `layout` -- se llama cada vez que
    ui_helpers.chargeBtnsArea reconstruye la sección "Sala de Espera" (cambia
    de sección = destruye y recrea los botones), por eso guarda la
    referencia en main_window para poder refrescar el contador después."""
    btn = QPushButton("Bandeja de entrada")
    btn.setObjectName(BTN_OBJECT_NAME)
    btn.setToolTip("Bandeja de entrada")
    btn.setMaximumHeight(25)
    btn.clicked.connect(lambda: abrir(main_window))
    layout.addWidget(btn)
    main_window.btn_bandeja_oirs = btn
    btn.setMinimumWidth(btn.sizeHint().width())
    actualizar_badge(main_window)
    return btn


def actualizar_badge(main_window):
    """Refresca el contador de no leídos en el botón y lo resalta con color
    si hay algo nuevo -- llamar en cada ciclo de sync y al cerrar la
    bandeja (por si se marcó algo como leído)."""
    btn = getattr(main_window, "btn_bandeja_oirs", None)
    if btn is None:
        return
    no_leidos = sum(1 for it in inbox_list() if not it.get("leido"))
    if no_leidos:
        btn.setText(f"Bandeja de entrada ({no_leidos})")
        btn.setStyleSheet(
            "QPushButton { background-color:#e67e22; color:white; font-weight:600; "
            "border-radius:4px; padding:2px 8px; }"
            "QPushButton:hover { background-color:#d35400; }"
        )
    else:
        btn.setText("Bandeja de entrada")
        btn.setStyleSheet("")
    btn.setMinimumWidth(btn.sizeHint().width())


def abrir(main_window):
    """Abre (o trae al frente) la subventana MDI de la bandeja, refrescando
    su contenido contra el backend -- a diferencia del antiguo diálogo, esta
    ventana persiste entre aperturas (ver main.py: self.subw["INBOX"])."""
    subw = main_window.subw.get("INBOX") if main_window.subw else None
    if subw is not None:
        subw.obj.refresh()
    main_window.activate_auto("INBOX")
