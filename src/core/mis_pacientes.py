# -*- coding: utf-8 -*-
"""Historial de pacientes atendidos por el alumno (vista propia).

Botón "Mis pacientes" al lado de Agenda/Bandeja (ver
ui_helpers.ToolBar.chargeBtnsArea), visible solo para alumnos (el admin/
docente ya tiene su propia vista equivalente y más completa en el portal
web: admin/student.php + admin/chat_detail.php). Lista los pacientes que el
alumno ha atendido; al seleccionar uno, muestra en pestañas:
  - Resumen: stats de comportamiento de esa atención puntual.
  - Conversación: el chat con el paciente simulado, con la retroalimentación
    que el docente haya dejado turno a turno (ver chat_comments).
  - Ficha clínica: misma ficha que agenda.Agenda muestra al atender (motor
    compartido, ver core.ficha), acá en modo solo-lectura histórico.

Vive como subventana única del MDI (ver main.py: self.subw["MIS_PACIENTES"]),
igual que Agenda o la Bandeja de entrada."""

import html as html_lib
from types import SimpleNamespace

import shiboken6
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSplitter, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QAbstractItemView, QTextEdit, QTabWidget)

from core.helpers import mis_atenciones, mi_conversacion, CasesOffline, Shedule
from core.ficha import render_ficha_html

BTN_OBJECT_NAME = "btn_mis_pacientes"
COLUMNAS = ("Fecha", "Paciente", "Procedimiento")


def _fmt_duracion(segundos):
    segundos = int(segundos or 0)
    minutos, seg = divmod(segundos, 60)
    return f"{minutos} min {seg}s" if minutos else f"{seg}s"


class MisPacientesWidget(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._items = []
        self._shedule = {}
        self._cases = {}

        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal, self)
        layout.addWidget(splitter)

        self.tabla = QTableWidget(0, len(COLUMNAS), self)
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self._on_seleccion)
        splitter.addWidget(self.tabla)

        self.tabs = QTabWidget(self)

        self.texto_resumen = QTextEdit(self)
        self.texto_resumen.setReadOnly(True)
        self.tabs.addTab(self.texto_resumen, "Resumen")

        self.texto_conversacion = QTextEdit(self)
        self.texto_conversacion.setReadOnly(True)
        self.texto_conversacion.setStyleSheet("background-color: #e9e2d6;")
        self.tabs.addTab(self.texto_conversacion, "Conversación")

        self.texto_ficha = QTextEdit(self)
        self.texto_ficha.setReadOnly(True)
        self.tabs.addTab(self.texto_ficha, "Ficha clínica")

        splitter.addWidget(self.tabs)
        splitter.setSizes([260, 560])

        self._mostrar_vacio()

    def _mostrar_vacio(self):
        self.texto_resumen.setHtml("<p style='color:#888;'>Selecciona un paciente de la lista.</p>")
        self.texto_conversacion.setHtml("<p style='color:#888;'>Selecciona un paciente de la lista.</p>")
        self.texto_ficha.setHtml("<p style='color:#888;'>Selecciona un paciente de la lista.</p>")

    def refresh(self):
        """Recarga la lista de pacientes atendidos y el estado local
        (agenda/casos) necesario para renderizar la ficha clínica."""
        self._items = mis_atenciones()
        try:
            self._shedule = Shedule().get()
        except Exception:
            self._shedule = {}
        try:
            self._cases = CasesOffline().get_cases()
        except Exception:
            self._cases = {}

        self.tabla.setRowCount(len(self._items))
        for row, it in enumerate(self._items):
            paciente = f"{it.get('nombre', '')} {it.get('apellido', '')}".strip() or "Paciente sin nombre"
            fecha_item = QTableWidgetItem(f"{it.get('fecha', '') or '—'} {it.get('hora', '')}".strip())
            paciente_item = QTableWidgetItem(paciente)
            proc_item = QTableWidgetItem(it.get("procedimiento", ""))
            for item in (fecha_item, paciente_item, proc_item):
                item.setData(Qt.UserRole, it)
            self.tabla.setItem(row, 0, fecha_item)
            self.tabla.setItem(row, 1, paciente_item)
            self.tabla.setItem(row, 2, proc_item)

        if not self._items:
            self._mostrar_vacio()

    def _on_seleccion(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            self._mostrar_vacio()
            return
        it = self.tabla.item(filas[0].row(), 0).data(Qt.UserRole)
        self._mostrar_resumen(it)
        self._mostrar_conversacion(it)
        self._mostrar_ficha(it)

    def _mostrar_resumen(self, it):
        stats = it.get("stats") or {}
        paciente = f"{it.get('nombre', '')} {it.get('apellido', '')}".strip() or "Paciente sin nombre"
        partes = [
            f"<h3>{html_lib.escape(paciente)}</h3>",
            f"<p><b>Procedimiento:</b> {html_lib.escape(it.get('procedimiento') or '—')}<br>"
            f"<b>Cita:</b> {html_lib.escape(it.get('fecha') or '—')} {html_lib.escape(it.get('hora') or '')}<br>"
            f"<b>Inicio real:</b> {html_lib.escape(it.get('hora_real') or '—')}<br>"
            f"<b>Cerrada:</b> {html_lib.escape(it.get('updated_at') or '—')}</p>",
            "<h3>Comportamiento durante la atención</h3>",
            "<table cellspacing='4'>"
            f"<tr><td>Bloques de actividad</td><td><b>{stats.get('n_sessions', 0)}</b></td></tr>"
            f"<tr><td>Duración total</td><td><b>{_fmt_duracion(stats.get('total_duration_s'))}</b></td></tr>"
            f"<tr><td>Delta promedio entre acciones</td><td><b>{stats.get('avg_delta_s') if stats.get('avg_delta_s') is not None else '—'}"
            f"{'s' if stats.get('avg_delta_s') is not None else ''}</b></td></tr>"
            f"<tr><td>Pausas largas (&ge;30s)</td><td><b style='color:{'#a33' if stats.get('long_pauses') else 'inherit'};'>"
            f"{stats.get('long_pauses', 0)}</b></td></tr>"
            f"<tr><td>Acciones sin pausa (0s)</td><td><b>{stats.get('no_pause_actions', 0)}</b></td></tr>"
            f"<tr><td>Mensajes con el paciente</td><td><b>{it.get('n_chat_messages', 0)}</b></td></tr>"
            "</table>",
        ]
        if it.get("nota"):
            partes.append(
                "<h3>Tu evolución registrada</h3>"
                f"<p>{html_lib.escape(it['nota']).replace(chr(10), '<br>')}</p>"
            )
        self.texto_resumen.setHtml("".join(partes))

    def _mostrar_conversacion(self, it):
        appointment_id = it.get("appointment_id")
        turnos = mi_conversacion(appointment_id) if appointment_id else []
        if not turnos:
            self.texto_conversacion.setHtml(
                "<p style='color:#888;'>Sin conversación registrada para esta atención.</p>"
            )
            return

        partes = [
            "<p style='color:#7a7f8c; font-size:8pt;'>Los globos amarillos son retroalimentación "
            "de tu docente sobre ese turno puntual.</p>"
        ]
        for turno in turnos:
            contenido = html_lib.escape(turno.get("content", "")).replace("\n", "<br>")
            ts = html_lib.escape(turno.get("created_at", ""))
            if turno.get("role") == "user":
                partes.append(
                    '<table width="100%" cellspacing="0"><tr><td></td><td align="right">'
                    '<div style="display:inline-block; background:#dcf8c6; border:1px solid #cdeeb5; '
                    'border-radius:9px; padding:6px 10px; max-width:360px; text-align:left; margin:3px 0;">'
                    f'<span style="color:#3a7d3a; font-size:8pt; font-weight:bold;">Tú · {ts}</span><br>'
                    f'{contenido}</div></td></tr></table>'
                )
            else:
                partes.append(
                    '<table width="100%" cellspacing="0"><tr><td align="left">'
                    '<div style="display:inline-block; background:#ffffff; border:1px solid #e2e2e2; '
                    'border-radius:9px; padding:6px 10px; max-width:360px; text-align:left; margin:3px 0;">'
                    f'<span style="color:#888; font-size:8pt; font-weight:bold;">Paciente · {ts}</span><br>'
                    f'{contenido}</div></td><td></td></tr></table>'
                )
            for c in turno.get("comments", []):
                comentario = html_lib.escape(c.get("comment", "")).replace("\n", "<br>")
                cts = html_lib.escape(c.get("created_at", ""))
                docente = html_lib.escape(c.get("teacher_name", "Docente"))
                partes.append(
                    '<table width="100%" cellspacing="0"><tr><td align="center">'
                    '<div style="display:inline-block; background:#fff9ea; border:1px solid #f3dfa0; '
                    'border-radius:8px; padding:5px 10px; max-width:420px; text-align:left; margin:2px 0;">'
                    f'<span style="color:#a3822f; font-size:8pt; font-weight:bold;">{docente} (docente) · {cts}</span><br>'
                    f'{comentario}</div></td></tr></table>'
                )
        self.texto_conversacion.setHtml("".join(partes))

    def _mostrar_ficha(self, it):
        case_id = it.get("case_id")
        appointment_id = it.get("appointment_id")
        if not case_id:
            self.texto_ficha.setHtml(
                "<p style='color:#888;'>Este registro no tiene un caso clínico asociado.</p>"
            )
            return

        row = self._shedule.get("agenda_1", {}).get(str(appointment_id))
        if row is None:
            # Cita ya no está en la agenda en memoria (poco frecuente) --
            # arma una fila mínima con lo que devolvió my_attendances.php,
            # mejor una ficha parcial que una vacía.
            row = SimpleNamespace(
                fecha=it.get("fecha", ""), hora=it.get("hora", ""), rut="",
                nombre=it.get("nombre", ""), apellido=it.get("apellido", ""),
                fecha_nac="", procedimiento=it.get("procedimiento", ""), atencion={},
            )

        caso = self._cases.get(case_id, {})
        username = (self._main_window.data_login.get("user") if self._main_window and self._main_window.data_login else None)
        html_ficha = render_ficha_html(row, caso, self._shedule, username, False)
        self.texto_ficha.setHtml(html_ficha)


def crear_boton(main_window, layout):
    """Crea el botón y lo agrega a `layout` -- se llama cada vez que
    ui_helpers.chargeBtnsArea reconstruye la sección "Sala de Espera" (cambia
    de sección = destruye y recrea los botones)."""
    btn = QPushButton("Mis pacientes")
    btn.setObjectName(BTN_OBJECT_NAME)
    btn.setToolTip("Pacientes que has atendido")
    btn.setMaximumHeight(25)
    btn.clicked.connect(lambda: abrir(main_window))
    layout.addWidget(btn)
    btn.setMinimumWidth(btn.sizeHint().width())
    return btn


def abrir(main_window):
    """Abre (o trae al frente) la subventana MDI del historial propio,
    refrescando su contenido contra el backend."""
    subw = main_window.subw.get("MIS_PACIENTES") if main_window.subw else None
    if subw is not None and shiboken6.isValid(subw.obj):
        subw.obj.refresh()
    main_window.activate_auto("MIS_PACIENTES")
