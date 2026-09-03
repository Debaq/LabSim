# -*- coding: utf-8 -*-
"""Bandeja de entrada de la app de escritorio.

Botón "Bandeja de entrada" que vive al lado del botón de Agenda (ver
ui_helpers.ToolBar.chargeBtnsArea) -- visible para cualquier rol logueado
(alumno o docente/admin, este último para poder probarla sin necesitar un
usuario alumno aparte). Lee/marca-leído contra inbox_messages en el backend
(ver core.helpers.inbox_list/inbox_marcar_leido -> public/api/inbox.php):
mensajes automáticos sobre el trato a pacientes (ver OirsEvaluator.php) y
mensajes que un docente mandó a mano desde Admin -> Bandeja de entrada.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QPushButton, QDialog, QVBoxLayout, QTextEdit,
                                QDialogButtonBox, QListWidget, QListWidgetItem)

from core.helpers import inbox_list, inbox_marcar_leido

BTN_OBJECT_NAME = "btn_bandeja_oirs"


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
    """Diálogo de lectura: lista de mensajes a la izquierda, cuerpo del
    seleccionado abajo. Marca como leído al abrir uno."""
    items = inbox_list()

    dialogo = QDialog(main_window)
    dialogo.setWindowTitle("Bandeja de entrada")
    layout = QVBoxLayout(dialogo)

    lista = QListWidget(dialogo)
    layout.addWidget(lista)

    cuerpo = QTextEdit(dialogo)
    cuerpo.setReadOnly(True)
    layout.addWidget(cuerpo)

    def _etiqueta(it):
        marca = "● " if not it.get("leido") else ""
        return f"{marca}{it.get('asunto', '')} -- {it.get('created_at', '')}"

    for it in items:
        entry = QListWidgetItem(_etiqueta(it))
        entry.setData(Qt.UserRole, it)
        if not it.get("leido"):
            fuente = entry.font()
            fuente.setBold(True)
            entry.setFont(fuente)
        lista.addItem(entry)

    def _mostrar(entry):
        it = entry.data(Qt.UserRole)
        cuerpo.setPlainText(f"Asunto: {it.get('asunto', '')}\n\n{it.get('cuerpo', '')}")
        if not it.get("leido"):
            inbox_marcar_leido(int(it["id"]))
            it["leido"] = 1
            entry.setData(Qt.UserRole, it)
            fuente = entry.font()
            fuente.setBold(False)
            entry.setFont(fuente)
            entry.setText(_etiqueta(it))
            actualizar_badge(main_window)

    lista.itemClicked.connect(_mostrar)

    if not items:
        cuerpo.setPlainText("Sin mensajes todavía.")

    botones = QDialogButtonBox(QDialogButtonBox.Ok)
    botones.accepted.connect(dialogo.accept)
    layout.addWidget(botones)

    dialogo.resize(520, 480)
    dialogo.exec()
