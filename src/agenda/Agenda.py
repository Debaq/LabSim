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
from PySide6.QtWidgets import (QTableWidgetItem, QAbstractItemView, QAbstractScrollArea,
                                QButtonGroup, QDateEdit, QFrame, QHBoxLayout, QHeaderView,
                                QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
                                QStackedWidget, QTextBrowser, QTextEdit, QVBoxLayout, QCheckBox)
from PySide6.QtCore import QDate, QSize, QTime, QDateTime, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QTextCharFormat
from agenda.UI.Ui_agenda import Ui_Form
from agenda import vista
from agenda.vista import BotonAccion, Contador, PanelDetalle
from core import feriados as feriados_cl
from core import hilos, iconos, respaldo_informes, tema
from core.helpers import (Shedule, aplicar_delta, entry_estado_por, CasesOffline, debug_print,
                          es_docente, lista_practica, iniciar_practica,
                          marcar_entry_no_show,
                          obtener_nota_atencion,
                          CreatePatient)
from core.ficha import (audiometria_previa, fila_de_practica, parse_fecha_agenda, poner_html,
                        render_ficha_html)
from core.practica import abrir_ficha_estudio

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")

# Columnas de la tabla. 0 es siempre el estado, solo el icono (el texto va en
# el tooltip y en los contadores); Nombre es siempre la 4.
ENCABEZADOS_AGENDA = ["", "Fecha", "Hora", "RUT", "Nombre", "Apellidos",
                      "Nacimiento", "Procedimiento"]
# Práctica libre: el procedimiento primero (angosto, completo en el
# tooltip). N° = el lugar del paciente en su carpeta: oculto, solo da el
# orden del libro (la tabla llega ordenada por él).
ENCABEZADOS_PRACTICA = ["", "Procedimiento", "Intentos", "RUT", "Nombre", "Apellidos",
                        "Nacimiento", "N°"]
COL_N_PRACTICA = 7
ANCHO_ESTADO = 40
ANCHO_PROCEDIMIENTO = 210
ANCHO_INTENTOS = 72


def _plural(n, uno, varios):
    return f"{n} {uno if n == 1 else varios}"


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


# Feriados legales en el calendario del filtro por fecha (ver core/feriados.py).
FERIADO_COLOR = QColor(176, 0, 32)
FERIADO_FONDO = QColor(255, 228, 228)


class FichaClinicaWidget(QWidget):
    """Ficha clínica del paciente. Vive como subventana única del MDI (ver
    main.py: self.subw["FICHA"]) en vez de un diálogo emergente -- set_ficha()
    la reapunta a otro paciente cada vez que se abre desde la agenda."""

    def __init__(self):
        super().__init__()
        tema.aplicar_estilo(self, vista.QSS_FICHA)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 12, 12, 12)
        raiz.setSpacing(10)

        cabecera = QFrame(self)
        cabecera.setProperty("card", "true")
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(14, 10, 14, 10)
        fila.setSpacing(12)
        marca = QLabel()
        marca.setPixmap(iconos.pixmap("persona", tema.ACENTO, 34))
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.lbl_nombre = QLabel("Ficha clínica")
        self.lbl_nombre.setProperty("role", "titulo")
        self.lbl_datos = QLabel("")
        self.lbl_datos.setProperty("role", "campo")
        self.lbl_datos.setWordWrap(True)
        textos.addWidget(self.lbl_nombre)
        textos.addWidget(self.lbl_datos)
        fila.addWidget(marca)
        fila.addLayout(textos, 1)
        self.btn_chat = BotonAccion("Hablar con el paciente", "mensaje", parent=self)
        self.btn_chat.setToolTip("Abre el chat con el paciente de este caso")
        self.btn_chat.clicked.connect(self._on_chat_clicked)
        self.btn_chat.hide()
        fila.addWidget(self.btn_chat)
        raiz.addWidget(cabecera)

        # QTextBrowser y no QTextEdit: la audiometría que trae el paciente se
        # abre con un enlace del historial (ver core/ficha.poner_html)
        self.texto = QTextBrowser(self)
        self.texto.setObjectName("textoFicha")
        self.texto.setReadOnly(True)
        raiz.addWidget(self.texto, 1)

        self._on_chat = None

    def set_ficha(self, html, on_chat=None, cabecera=None):
        """`cabecera`: (nombre, línea de datos) del paciente para el encabezado."""
        poner_html(self.texto, html)
        self._on_chat = on_chat
        self.btn_chat.setVisible(on_chat is not None)
        nombre, datos = cabecera or ("Ficha clínica", "")
        self.lbl_nombre.setText(nombre or "Paciente")
        self.lbl_datos.setText(datos)
        self.texto.verticalScrollBar().setValue(0)

    def _on_chat_clicked(self):
        if self._on_chat is not None:
            self._on_chat()


class EvolucionWidget(QWidget):
    """Registro de evolución al cerrar una atención. Vive como subventana
    única del MDI (ver main.py: self.subw["EVOLUCION"]) en vez de un diálogo
    emergente -- set_contexto() la reapunta a otro paciente/callback cada vez
    que se abre desde la agenda (atención real o de prueba)."""

    def __init__(self):
        super().__init__()
        tema.aplicar_estilo(self, vista.QSS_FICHA)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        cabecera = QFrame(self)
        cabecera.setProperty("card", "true")
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(14, 10, 14, 10)
        fila.setSpacing(12)
        marca = QLabel()
        marca.setPixmap(iconos.pixmap("evolucion", tema.ACENTO, 30))
        textos = QVBoxLayout()
        textos.setSpacing(0)
        titulo = QLabel("Evolución del paciente")
        titulo.setProperty("role", "titulo")
        self.lbl_paciente = QLabel(self)
        self.lbl_paciente.setProperty("role", "campo")
        textos.addWidget(titulo)
        textos.addWidget(self.lbl_paciente)
        fila.addWidget(marca)
        fila.addLayout(textos, 1)
        layout.addWidget(cabecera)

        pasos = vista.Pasos()
        pasos.set_actual(len(vista.PASOS) - 1)
        layout.addWidget(pasos)

        self.texto = QTextEdit(self)
        self.texto.setObjectName("textoEvolucion")
        self.texto.setPlaceholderText("Describe la evolución del paciente...")
        layout.addWidget(self.texto, 1)

        pie = QHBoxLayout()
        ayuda = QLabel("Lo que escribes se guarda como borrador en este equipo mientras trabajas.")
        ayuda.setProperty("role", "hint")
        ayuda.setWordWrap(True)
        pie.addWidget(ayuda, 1)
        self.btn_guardar = BotonAccion("Guardar evolución", "check", principal=True, parent=self)
        self.btn_guardar.clicked.connect(self._on_guardar_clicked)
        pie.addWidget(self.btn_guardar)
        layout.addLayout(pie)

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
        self.lbl_paciente.setText(nombre_paciente)
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
        # Práctica libre: la tabla muestra los pacientes de una carpeta (una
        # por capítulo del libro, ver labsim_backend/src/Practica.php) en vez
        # de la agenda. Filas con key "practica:<id>"; los intentos (citas
        # con practice_id) nunca se muestran como filas de agenda. El docente
        # la ve igual y la abre en modo prueba; en su agenda no salen esos
        # pacientes. Ver core/practica.py.
        self._modo_practica = False
        self._practica = {}
        self._carpetas = []      # [(clave, nombre, n)] en el orden del backend
        self._carpeta = None     # la elegida en la lista de la izquierda

        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Agenda admin y estudiante son la misma vista: la gestión de citas
        # (agendar/editar/cancelar/eliminar) vive solo en el backend web
        # (labsim_backend/public/admin/agenda.php); la app queda de solo
        # lectura para todos los roles, con "Atender" como única acción, que
        # en el admin corre en modo prueba (ver atender_paciente()).
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self._construir_vista()

        self.tableWidget.itemSelectionChanged.connect(self._on_selection_changed)

        # Arranca vacía y baja la agenda en segundo plano. Antes se bajaba
        # acá (Shedule() -> el estado completo, ~450 KB) y el login quedaba
        # con la ventana congelada mientras llegaba. Con la primera carga se
        # avisa a main (agenda_cargada) para retomar la atención abierta.
        self.shedule = {}
        self._cargando = True
        self._carga_fallo = False
        self.populate_shedule()
        self.refresh_async()

        self.pushButton.setVisible(False)

    def _construir_vista(self):
        """Arma la pantalla: cabecera (título, vista, día, búsqueda), contadores
        por estado, la tabla y, abajo, el panel del paciente elegido con sus
        botones. Los textos de los botones los sigue cambiando la lógica de
        selección (Atender, Retomar, Practicar, Cerrar/Evolucionar...)."""
        tema.aplicar_estilo(self, vista.QSS_AGENDA)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        tabla = self.tableWidget
        tabla.insertColumn(0)
        tabla.setHorizontalHeaderLabels(ENCABEZADOS_AGENDA)
        tabla.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        tabla.setShowGrid(False)
        tabla.setIconSize(QSize(18, 18))
        tabla.setWordWrap(False)
        tabla.verticalHeader().setDefaultSectionSize(38)
        tabla.horizontalHeader().setHighlightSections(False)
        tabla.horizontalHeader().setStretchLastSection(False)
        self._poner_anchos()

        raiz = self.verticalLayout
        raiz.removeItem(self.horizontalLayout)
        raiz.removeWidget(tabla)
        raiz.setContentsMargins(12, 12, 12, 12)
        raiz.setSpacing(10)

        # -- Cabecera ---------------------------------------------------
        cabecera = QFrame(self)
        cabecera.setObjectName("cabeceraAgenda")
        col = QVBoxLayout(cabecera)
        col.setContentsMargins(14, 10, 14, 10)
        col.setSpacing(8)

        fila_titulo = QHBoxLayout()
        fila_titulo.setSpacing(10)
        marca = QLabel()
        marca.setPixmap(iconos.pixmap("calendario", tema.ACENTO, 30))
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.lbl_titulo = QLabel("Agenda")
        self.lbl_titulo.setObjectName("tituloAgenda")
        self.lbl_subtitulo = QLabel("")
        self.lbl_subtitulo.setObjectName("subtituloAgenda")
        textos.addWidget(self.lbl_titulo)
        textos.addWidget(self.lbl_subtitulo)
        fila_titulo.addWidget(marca)
        fila_titulo.addLayout(textos, 1)

        self.btn_vista_agenda = QPushButton(" Mi agenda", self)
        self.btn_vista_agenda.setIcon(iconos.icono("calendario", tema.ACENTO, 18))
        self.btn_vista_agenda.setToolTip("Las citas que te programó tu docente, por día")
        self.btn_practica = QPushButton(" Práctica libre", self)
        self.btn_practica.setIcon(iconos.icono("practica", tema.ACENTO, 18))
        self.btn_practica.setToolTip("Pacientes que tu docente dejó para practicar cuando quieras, "
                                     "las veces que quieras")
        for boton, lado in ((self.btn_vista_agenda, "izq"), (self.btn_practica, "der")):
            boton.setCheckable(True)
            boton.setProperty("vista", "true")
            boton.setProperty("lado", lado)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_vista_agenda.setChecked(True)
        self._grupo_vista = QButtonGroup(self)
        self._grupo_vista.setExclusive(True)
        self._grupo_vista.addButton(self.btn_vista_agenda)
        self._grupo_vista.addButton(self.btn_practica)
        self.btn_practica.toggled.connect(self._on_toggle_practica)
        self._icono_vista_activa()
        self.btn_practica.toggled.connect(lambda _c: self._icono_vista_activa())
        fila_titulo.addWidget(self.btn_vista_agenda)
        fila_titulo.addWidget(self.btn_practica)
        col.addLayout(fila_titulo)

        fila_filtros = QHBoxLayout()
        fila_filtros.setSpacing(8)
        self.led_buscar = QLineEdit(self)
        self.led_buscar.setObjectName("buscarAgenda")
        self.led_buscar.setPlaceholderText("Buscar por RUT, nombre, apellido o examen (ASSR, EOA, VEMP...)")
        self.led_buscar.setClearButtonEnabled(True)
        self.led_buscar.addAction(iconos.icono("buscar", tema.TEXTO_TENUE, 18),
                                  QLineEdit.ActionPosition.LeadingPosition)
        self.led_buscar.textChanged.connect(self._on_filtro_changed)
        fila_filtros.addWidget(self.led_buscar, 1)

        self.btn_dia_ant = QPushButton(self)
        self.btn_dia_ant.setIcon(iconos.icono("izquierda", tema.TEXTO_SUAVE, 18))
        self.btn_dia_ant.setToolTip("Día anterior")
        self.date_selector = QDateEdit(self)
        self.date_selector.setCalendarPopup(True)
        self.date_selector.setDisplayFormat("dd-MM-yyyy")
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.dateChanged.connect(self._on_fecha_seleccionada)
        self.btn_dia_sig = QPushButton(self)
        self.btn_dia_sig.setIcon(iconos.icono("derecha", tema.TEXTO_SUAVE, 18))
        self.btn_dia_sig.setToolTip("Día siguiente")
        self.btn_hoy = QPushButton("Hoy", self)
        self.btn_dia_ant.clicked.connect(lambda: self.date_selector.setDate(self.date_selector.date().addDays(-1)))
        self.btn_dia_sig.clicked.connect(lambda: self.date_selector.setDate(self.date_selector.date().addDays(1)))
        self.btn_hoy.clicked.connect(lambda: self.date_selector.setDate(QDate.currentDate()))
        self._nav_dia = (self.btn_dia_ant, self.date_selector, self.btn_dia_sig, self.btn_hoy)
        for boton in (self.btn_dia_ant, self.btn_dia_sig, self.btn_hoy):
            boton.setProperty("nav", "true")
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
        for w in self._nav_dia:
            fila_filtros.addWidget(w)
        self._init_feriados()

        self.chk_ver_todas = QCheckBox("Ver todas las citas habilitadas", self)
        self.chk_ver_todas.setToolTip("Todas las citas que ya tienen fecha y hora, sin filtrar por día")
        self.chk_ver_todas.toggled.connect(self._on_toggle_ver_todas)
        fila_filtros.addWidget(self.chk_ver_todas)
        col.addLayout(fila_filtros)
        raiz.addWidget(cabecera)

        # -- Contadores -------------------------------------------------
        self._contadores = {clave: Contador(clave, self) for clave in
                            ("por_atender", "atendiendo", "atendido", "no_show",
                             "practica_nuevo", "practica_curso", "practica_hecho")}
        fila_cont = QHBoxLayout()
        fila_cont.setSpacing(8)
        for contador in self._contadores.values():
            fila_cont.addWidget(contador)
        self._fila_contadores = fila_cont
        raiz.addLayout(fila_cont)

        # -- Tabla / estado vacío ---------------------------------------
        self._pila = QStackedWidget(self)
        self._pila.addWidget(tabla)
        vacio = QFrame(self)
        vacio.setObjectName("vacioAgenda")
        col_vacio = QVBoxLayout(vacio)
        col_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_vacio = QLabel()
        icono_vacio.setPixmap(iconos.pixmap("calendario_vacio", tema.TEXTO_TENUE, 44))
        icono_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio = QLabel("")
        self.lbl_vacio.setProperty("role", "titulo")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio_ayuda = QLabel("")
        self.lbl_vacio_ayuda.setProperty("role", "hint")
        self.lbl_vacio_ayuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio_ayuda.setWordWrap(True)
        col_vacio.addWidget(icono_vacio)
        col_vacio.addWidget(self.lbl_vacio)
        col_vacio.addWidget(self.lbl_vacio_ayuda)
        self._pila.addWidget(vacio)
        self._pila.setMinimumHeight(110)
        # Práctica libre: las carpetas a la izquierda de la tabla. Angosta:
        # en los PC del laboratorio sobra ancho y falta alto.
        self.lista_carpetas = QListWidget(self)
        self.lista_carpetas.setObjectName("carpetasPractica")
        self.lista_carpetas.setFixedWidth(220)
        self.lista_carpetas.setWordWrap(True)
        self.lista_carpetas.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Un nombre de capítulo largo pasa a dos líneas, no se corta con "…"
        self.lista_carpetas.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.lista_carpetas.setVisible(False)
        self.lista_carpetas.currentItemChanged.connect(self._on_carpeta_elegida)
        fila_tabla = QHBoxLayout()
        fila_tabla.setSpacing(10)
        fila_tabla.addWidget(self.lista_carpetas)
        fila_tabla.addWidget(self._pila, 1)
        raiz.addLayout(fila_tabla, 1)

        # -- Detalle y acciones -----------------------------------------
        self.detalle = PanelDetalle(self)
        self.btn_atender = BotonAccion("Atender", "atender", principal=True, parent=self)
        self.btn_atender.setMinimumWidth(200)
        self.btn_atender.setEnabled(False)
        self.btn_atender.clicked.connect(self.atender_paciente)

        self.btn_ver_ficha = BotonAccion("Ver ficha", "ficha", parent=self)
        self.btn_ver_ficha.setToolTip("Antecedentes y motivo de consulta del paciente. "
                                      "Revísala antes de atender.")
        self.btn_ver_ficha.setEnabled(False)
        self.btn_ver_ficha.clicked.connect(self._ver_ficha_paciente)

        self.btn_no_show = BotonAccion("No se presentó", "x", parent=self)
        self.btn_no_show.setToolTip("Disponible cuando la hora de la cita ya pasó y no atendiste al paciente")
        self.btn_no_show.setEnabled(False)
        self.btn_no_show.clicked.connect(self._marcar_no_show)

        self.btn_ficha_estudio = BotonAccion("Ficha de estudio", "libro", parent=self)
        self.btn_ficha_estudio.setToolTip("Los resultados del caso, para comparar con tu último intento cerrado")
        self.btn_ficha_estudio.setVisible(False)
        self.btn_ficha_estudio.clicked.connect(self._ver_ficha_estudio)

        acciones = self.detalle.acciones
        acciones.addWidget(self.btn_atender, 0, 0, 1, 2)
        acciones.addWidget(self.btn_ver_ficha, 1, 0)
        acciones.addWidget(self.btn_no_show, 1, 1)
        acciones.addWidget(self.btn_ficha_estudio, 2, 0, 1, 2)
        raiz.addWidget(self.detalle)

        self._edades = {}

        if self.is_admin:
            # El admin ve todos los pacientes siempre (ver _visible_keys):
            # el filtro por fecha / "ver todas" es solo para el estudiante.
            # La práctica libre sí la tiene, aparte (ver _populate_practica).
            for w in (*self._nav_dia, self.chk_ver_todas):
                w.setVisible(False)
            self.btn_practica.setToolTip("Los pacientes de la práctica libre, en sus carpetas, como los ven "
                                         "tus alumnos. Se abren en modo prueba: no queda registro.")
            # El docente ve siempre la ficha de estudio del caso elegido, en la
            # agenda y en la práctica libre (la del alumno depende de su intento).
            self.btn_ficha_estudio.setVisible(True)
            self.btn_ficha_estudio.setToolTip("La ficha de estudio del caso: la que ve el alumno al cerrar "
                                              "un intento de práctica")
            for contador in self._contadores.values():
                contador.setVisible(False)

            # Solo admin/docente: elegir si su "Atender" es una prueba sin
            # rastro (por defecto, ver atender_paciente_prueba) o si queda
            # guardado de verdad con su propia cuenta (attendances + chat) --
            # para armar una atención base con la que comparar a los
            # alumnos después (ver main.atender_paciente_base). Deshabilitado
            # mientras hay una atención en curso para no cambiar de modo a
            # mitad de camino.
            self.chk_guardar_base = QCheckBox("Guardar esta atención (base para comparar)", self)
            self.chk_guardar_base.toggled.connect(self._on_toggle_guardar_base)
            acciones.addWidget(self.chk_guardar_base, 3, 0, 1, 2)
        else:
            self._mostrar_contadores(vista.CONT_AGENDA)

    def _icono_vista_activa(self):
        """El icono de la vista elegida va en blanco, sobre el fondo morado."""
        for boton, nombre in ((self.btn_vista_agenda, "calendario"), (self.btn_practica, "practica")):
            color = "#FFFFFF" if boton.isChecked() else tema.ACENTO
            boton.setIcon(iconos.icono(nombre, color, 18))

    def _mostrar_contadores(self, claves):
        for clave, contador in self._contadores.items():
            contador.setVisible(clave in claves)

    def _on_toggle_guardar_base(self, checked):
        self._guardar_base = checked

    def _on_toggle_ver_todas(self, checked):
        self._ver_todas = checked
        for w in self._nav_dia:
            w.setEnabled(not checked)
        self.populate_shedule()

    def _on_toggle_practica(self, checked):
        self._modo_practica = checked
        if not self.is_admin:
            for w in (*self._nav_dia, self.chk_ver_todas):
                w.setVisible(not checked)
        else:
            # Siempre en modo prueba: guardar una atención base pide una cita
            self.chk_guardar_base.setVisible(not checked)
        self.btn_no_show.setVisible(not checked)
        self.btn_ficha_estudio.setVisible(checked or self.is_admin)
        # Sin "No se presentó", "Ver ficha" ocupa todo el ancho.
        self.detalle.acciones.removeWidget(self.btn_ver_ficha)
        self.detalle.acciones.addWidget(self.btn_ver_ficha, 1, 0, 1, 2 if checked else 1)
        if checked:
            self._mostrar_contadores(vista.CONT_PRACTICA)
        else:
            self._mostrar_contadores(() if self.is_admin else vista.CONT_AGENDA)
        self.tableWidget.setHorizontalHeaderLabels(ENCABEZADOS_PRACTICA if checked else ENCABEZADOS_AGENDA)
        self.lista_carpetas.setVisible(checked and bool(self._carpetas))
        # Sin columna de orden la tabla queda como la manda el backend (el
        # orden de la carpeta); si no, se ordenaba sola por Estado, al revés.
        # Un clic en el encabezado la sigue ordenando.
        self.tableWidget.horizontalHeader().setSortIndicator(-1 if checked else 0, Qt.DescendingOrder)
        if checked:
            self._pedir_practica()
        self._selected_row_key = None
        self.tableWidget.blockSignals(True)
        self.tableWidget.clearSelection()
        sueltos = self._vaciar_tabla(0)
        self.tableWidget.blockSignals(False)
        self.populate_shedule()
        del sueltos

    def _on_practica_fetched(self, items):
        self._practica = {f"practica:{it['id']}": it for it in items}
        self._armar_carpetas()
        # Al docente también le cambia la agenda: los saca de ahí
        if self._modo_practica or self.is_admin:
            self.populate_shedule()

    def _armar_carpetas(self):
        """La lista de carpetas, en el orden en que vienen sus pacientes.
        Un backend de antes de las carpetas no manda folder_id: queda todo
        en una sola, sin nombre."""
        carpetas = {}
        for it in self._practica.values():
            clave = it.get("folder_id")
            if clave not in carpetas:
                carpetas[clave] = [clave, it.get("carpeta") or "Práctica libre", 0]
            carpetas[clave][2] += 1
        self._carpetas = [tuple(c) for c in carpetas.values()]
        if self._carpeta not in carpetas:
            self._carpeta = self._carpetas[0][0] if self._carpetas else None

        lista = self.lista_carpetas
        lista.blockSignals(True)
        lista.clear()
        # Sin número adelante: el nombre ya dice el capítulo ("Cap. 7 · ...")
        for clave, nombre, cuantos in self._carpetas:
            item = QListWidgetItem(f"{nombre}  ({cuantos})")
            item.setData(Qt.UserRole, clave)
            item.setToolTip(f"{nombre}: {_plural(cuantos, 'paciente', 'pacientes')}")
            lista.addItem(item)
            if clave == self._carpeta:
                lista.setCurrentItem(item)
        lista.blockSignals(False)
        lista.setVisible(self._modo_practica and bool(self._carpetas))

    def _on_carpeta_elegida(self, actual, _anterior=None):
        if actual is None:
            return
        self._carpeta = actual.data(Qt.UserRole)
        self._selected_row_key = None
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
        self._filtro_texto = vista.sin_tildes(texto.strip())
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
            _traer_agenda, self._modo_practica or self.is_admin, dueno=self,
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
        primera = data is not None and self._cargando
        if data is not None:
            self._cargando = False
            self.shedule = data
            self.populate_shedule()
        elif self._cargando:
            # Se reintenta solo con el sync (aplicar_delta pide completo)
            self._carga_fallo = True
            self.populate_shedule()
        if practica is not None:
            self._on_practica_fetched(practica)
        if getattr(self, "_refrescar_otra_vez", False):
            self.refresh_async()
        if primera:
            aviso = getattr(self.main_window, "agenda_cargada", None)
            if aviso is not None:
                aviso()

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
            # los pacientes/citas (sin filtro por fecha ni por estado), menos
            # los de práctica, que tienen su lista aparte: los intentos de
            # los alumnos y la fila "sin cita" de cada paciente de práctica.
            casos_practica = {str(it.get("case_id")) for it in self._practica.values()}
            keys = [k for k, v in rows.items()
                    if v.practice_id is None and not (v.sin_cita and v.case_id in casos_practica)]
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
                if texto in vista.texto_busqueda(rows[k].rut, rows[k].nombre, rows[k].apellido,
                                                 rows[k].fecha_nac, procedimiento=rows[k].procedimiento)
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
        sueltos = self._vaciar_tabla(len(keys))

        username = self._current_username()
        conteo = {}
        for row_idx, key in enumerate(keys):
            user = rows[key]
            estado = entry_estado_por(user, username)
            clave = self._clave_estado(user, estado)
            conteo[clave] = conteo.get(clave, 0) + 1
            tooltip = {
                "sin_cita": "Caso sin cita: solo se puede probar, no queda registro.",
                "sin_fecha": "Cita creada sin fecha ni hora.",
                "vencida": "La hora de la cita ya pasó.",
            }.get(clave, "")
            # Cita agendada en feriado: se avisa en la celda de la fecha (no
            # en toda la fila). Es un error del docente al agendar, no del
            # alumno -- nadie va a atender ese día, así que tiene que saltar
            # a la vista en la tabla, que es lo único que ve el docente (su
            # vista esconde el date_selector).
            feriado = self._descripcion_feriado(parse_fecha_agenda(user.fecha))

            columnas = (user.fecha or "sin agendar", user.hora, user.rut, user.nombre,
                        user.apellido, user.fecha_nac, user.procedimiento)
            self._poner_fila(row_idx, key, clave, columnas, tooltip)
            if feriado:
                item = self.tableWidget.item(row_idx, 1)
                item.setText(f"⚠ {user.fecha}")
                item.setBackground(FERIADO_FONDO)
                item.setForeground(FERIADO_COLOR)
                item.setToolTip(f"Agendada en feriado: {feriado}")
        self._terminar_llenado()
        del sueltos
        self._loading = False
        self._actualizar_resumen(len(keys), conteo)

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
            self._actualizar_detalle()

    def _clave_estado(self, user, estado):
        """Cómo se ve esta fila (ver vista.ESTADOS)."""
        if user.sin_cita:
            return "sin_cita"
        if not (user.fecha and user.hora):
            return "sin_fecha"
        if estado in ("atendiendo", "atendido", "no_show"):
            return estado
        return "vencida" if self._hora_vencida(user) else "por_atender"

    @staticmethod
    def _hora_vencida(user):
        fecha = parse_fecha_agenda(user.fecha)
        hora = QTime.fromString(user.hora, "HH:mm")
        return (fecha.isValid() and hora.isValid()
                and QDateTime(fecha, hora) < QDateTime.currentDateTime())

    def _poner_fila(self, row_idx, key, clave, columnas, tooltip=""):
        """Una fila: la celda de estado (icono + texto de color) y las demás.
        Un int va como número, para que ordenar por esa columna no ponga el
        10 antes que el 2."""
        texto, _, _color = vista.ESTADOS[clave]
        celdas = [("", True)] + [(valor, False) for valor in columnas]
        for col_idx, (valor, es_estado) in enumerate(celdas):
            if isinstance(valor, int):
                item = QTableWidgetItem()
                item.setData(Qt.DisplayRole, valor)
            else:
                item = QTableWidgetItem(valor)
            item.setData(Qt.UserRole, key)
            if es_estado:
                # Solo el icono: el estado se lee en el tooltip
                item.setIcon(vista.icono_estado(clave))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setToolTip(texto + (f" · {tooltip}" if tooltip else ""))
            elif self._modo_practica and col_idx == 1:
                # El procedimiento va angosto: completo al pasar el mouse
                item.setToolTip(str(valor) + (f"\n{tooltip}" if tooltip else ""))
            elif tooltip:
                item.setToolTip(tooltip)
            if self._modo_practica and col_idx == 2:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tableWidget.setItem(row_idx, col_idx, item)

    def _actualizar_resumen(self, total, conteo):
        """Subtítulo, contadores y el aviso de "no hay nada" tras llenar la tabla."""
        for clave, contador in self._contadores.items():
            contador.set_valor(conteo.get(clave, 0))
        self.lbl_subtitulo.setText(self._subtitulo(total))
        self.lbl_titulo.setText("Práctica libre" if self._modo_practica else "Agenda")
        self._pila.setCurrentIndex(0 if total else 1)
        if total:
            return
        if self._cargando and not self._modo_practica:
            titulo = "Cargando la agenda…"
            ayuda = ("El servidor no responde; se vuelve a intentar solo." if self._carga_fallo
                     else "Trayendo tus citas del servidor.")
        elif self._filtro_texto:
            titulo, ayuda = "Nada coincide con tu búsqueda", "Prueba con otro nombre, apellido o RUT."
        elif self._modo_practica and self.is_admin:
            titulo = "No hay pacientes de práctica"
            ayuda = "Arma las carpetas en el panel web: Docencia → Práctica libre."
        elif self._modo_practica:
            titulo = "Aún no hay pacientes para practicar"
            ayuda = "Todavía no hay pacientes en la práctica libre."
        elif self.is_admin:
            titulo, ayuda = "No hay citas ni casos", "Crea un caso o agenda una cita desde el panel web."
        elif self._ver_todas:
            titulo = "No tienes citas habilitadas"
            ayuda = "Cuando tu docente te agende una cita con fecha y hora, aparecerá aquí."
        else:
            titulo = "No tienes citas para este día"
            ayuda = "Cambia de día con las flechas, o marca «Ver todas las citas habilitadas»."
        self.lbl_vacio.setText(titulo)
        self.lbl_vacio_ayuda.setText(ayuda)

    def _subtitulo(self, n):
        if self._modo_practica and self.is_admin:
            return f"{_plural(n, 'paciente', 'pacientes')} de práctica · vista docente, en modo prueba"
        if self._modo_practica:
            return (f"{_plural(n, 'paciente', 'pacientes')} para practicar · "
                    "sin horario, las veces que quieras")
        if self.is_admin:
            return f"{_plural(n, 'cita o caso', 'citas y casos')} · vista docente"
        if self._ver_todas:
            return f"{_plural(n, 'cita habilitada', 'citas habilitadas')} con fecha y hora"
        fecha = self.date_selector.date()
        texto = f"{DIAS[fecha.dayOfWeek() - 1].capitalize()} {fecha.day()} de {MESES[fecha.month() - 1]}"
        if fecha == QDate.currentDate():
            texto = f"Hoy · {texto}"
        feriado = self._descripcion_feriado(fecha)
        if feriado:
            texto += f" · Feriado: {feriado}"
        return f"{texto} · {_plural(n, 'cita', 'citas')}"

    def _edad(self, rut):
        if rut not in self._edades:
            try:
                self._edades[rut] = CreatePatient().get_age_from_rut(int(rut))[0]
            except (TypeError, ValueError):
                self._edades[rut] = None
        return self._edades[rut]

    def _actualizar_detalle(self):
        """El panel de abajo: quién es el paciente elegido y qué sigue."""
        key = self._selected_row_key
        if self._modo_practica:
            it = self._practica.get(key) if key else None
            if it is None:
                self.detalle.vacio("Elige un paciente para practicar. Puedes repetirlo las veces que quieras.")
                return
            if self.is_admin:
                self._detalle_practica_docente(key, it)
                return
            intentos = int(it.get("intentos") or 0)
            abierto = self._intento_abierto(key)
            if abierto is not None and self._es_atencion_activa(abierto):
                clave, paso = "practica_curso", 2
                pista = "Cuando termines, presiona «Cerrar/Evolucionar» para registrar tu nota y cerrar el intento."
            elif abierto is not None:
                clave, paso = "practica_curso", 1
                pista = "Dejaste este intento abierto. Presiona «Retomar» para seguir donde quedaste."
            elif intentos:
                clave, paso = "practica_hecho", None
                pista = ("Ya lo practicaste. Puedes repetirlo cuando quieras"
                         + ("; la ficha de estudio compara con tu último intento." if it.get("show_study_sheet") else "."))
            else:
                clave, paso = "practica_nuevo", 1
                pista = "Presiona «Practicar» para abrir al paciente; después podrás revisar su ficha."
            nombre = f"{it.get('nombre') or ''} {it.get('apellido') or ''}".strip()
            ultimo = (it.get("ultimo") or "")[:10]
            extra = _plural(intentos, "intento", "intentos") + (f", el último el {ultimo}" if ultimo else "")
            datos = self._datos_paciente(it.get("rut"), it.get("procedimiento"), extra)
            self.detalle.mostrar(nombre, datos, clave, pista, paso)
            return

        user = self.shedule.get("agenda_1", {}).get(key) if key else None
        if user is None:
            self.detalle.vacio("Selecciona una fila para ver su ficha y atender al paciente."
                               if self._pila.currentIndex() == 0 else "")
            return
        estado = entry_estado_por(user, self._current_username())
        clave = self._clave_estado(user, estado)
        activa = self._es_atencion_activa(key)
        paso = None
        if clave in ("por_atender", "vencida"):
            paso = 0
            pista = "Antes de atender, revisa su ficha (antecedentes y motivo de consulta). Luego presiona «Atender»."
            if clave == "vencida":
                pista = ("La hora de la cita ya pasó. Si el paciente no llegó, marca «No se presentó»; "
                         "si sí, puedes atenderlo igual.")
        elif clave == "atendiendo":
            paso = 2 if activa else 1
            pista = ("Cuando termines, presiona «Cerrar/Evolucionar» para escribir tu nota de evolución."
                     if activa else "Esta atención quedó abierta. Presiona «Atender» para retomarla.")
        elif clave == "atendido":
            paso = len(vista.PASOS)
            pista = "Atención cerrada: tu nota de evolución quedó registrada."
        elif clave == "no_show":
            pista = "Quedó registrada como inasistencia del paciente."
        elif clave == "sin_fecha":
            pista = "Esta cita todavía no tiene fecha ni hora, así que no se puede atender."
        else:
            pista = "Caso sin cita: solo se puede probar, no queda registro."
        if self.is_admin and clave not in ("sin_cita", "sin_fecha") and not self._guardar_base:
            pista = "Modo prueba: no queda registro. " + pista
        nombre = f"{user.nombre} {user.apellido}".strip()
        cuando = f"{user.fecha} {user.hora}".strip() if user.fecha and user.hora else None
        datos = self._datos_paciente(user.rut, user.procedimiento, cuando)
        self.detalle.mostrar(nombre, datos, clave, pista, paso)

    def _detalle_practica_docente(self, key, it):
        intentos = int(it.get("intentos") or 0)
        alumnos = int(it.get("alumnos") or 0)
        if self._prueba_practica_activa(key):
            clave, paso = "practica_curso", 2
            pista = "Modo prueba: no queda registro. Presiona «Cerrar/Evolucionar» para terminar."
        else:
            clave, paso = ("practica_hecho" if intentos else "practica_nuevo"), 1
            pista = "Modo prueba: no queda registro. Presiona «Atender (prueba)» para abrirlo como lo ven tus alumnos."
        if intentos:
            pista += (f" Lo practicaron {_plural(alumnos, 'alumno', 'alumnos')}; "
                      f"el último intento cerrado es del {(it.get('ultimo') or '')[:10]}.")
        nombre = f"{it.get('nombre') or ''} {it.get('apellido') or ''}".strip()
        datos = self._datos_paciente(it.get("rut"), it.get("procedimiento"),
                                     " · ".join(p for p in (it.get("carpeta"), _plural(intentos, "intento", "intentos")) if p))
        self.detalle.mostrar(nombre, datos, clave, pista, paso)

    def _clave_caso_practica(self, it):
        """Fila de la agenda (oculta en la vista docente) con la que el
        docente abre en prueba un paciente de práctica: la del caso sin cita
        o, si ya hay citas del caso, cualquiera de ellas -- en prueba solo se
        lee el caso, no se escribe nada en la cita."""
        case_id = str(it.get("case_id") or "")
        rows = self.shedule.get("agenda_1", {})
        if f"case:{case_id}" in rows:
            return f"case:{case_id}"
        return next((k for k, v in rows.items() if v.case_id == case_id), None)

    def _prueba_practica_activa(self, key):
        it = self._practica.get(key)
        clave = self._clave_caso_practica(it) if it else None
        return clave is not None and self._prueba_atendiendo_key == clave and self._es_atencion_activa(clave)

    def _datos_paciente(self, rut, procedimiento, extra=None):
        edad = self._edad(rut) if rut else None
        partes = [f"RUT {rut}" if rut else None, f"{edad} años" if edad else None,
                  procedimiento or None, extra]
        return "  ·  ".join(p for p in partes if p)

    def _poner_anchos(self, llenando=False):
        """Columnas al ancho de su contenido, la última estirada.

        Mientras se llena la tabla van fijas: con ResizeToContents cada
        takeItem/setItem recalculaba el ancho mirando todas las filas, y
        rearmar la agenda era cuadrático (2026-10-28, docente con unas 300
        filas: 6,9 s de ventana congelada en terreno; 80 s en una prueba con
        300 filas ya puestas). Al terminar se vuelven a ajustar, una vez."""
        ancho = QHeaderView.ResizeMode
        cabecera = self.tableWidget.horizontalHeader()
        # Fijas en las dos vistas: el icono del estado; en práctica libre,
        # también el procedimiento (angosto) y los intentos. La última
        # visible se estira.
        fijas = {0: ANCHO_ESTADO}
        if self._modo_practica:
            fijas.update({1: ANCHO_PROCEDIMIENTO, 2: ANCHO_INTENTOS})
        ultima = COL_N_PRACTICA - 1 if self._modo_practica else cabecera.count() - 1
        for col in range(cabecera.count()):
            if col in fijas:
                cabecera.setSectionResizeMode(col, ancho.Interactive)
                cabecera.resizeSection(col, fijas[col])
            elif llenando:
                cabecera.setSectionResizeMode(col, ancho.Interactive)
            else:
                cabecera.setSectionResizeMode(col, ancho.Stretch if col == ultima else ancho.ResizeToContents)
        self.tableWidget.setColumnHidden(COL_N_PRACTICA, self._modo_practica)

    def _terminar_llenado(self):
        self._poner_anchos()
        self.tableWidget.setSortingEnabled(True)

    def _vaciar_tabla(self, filas):
        """Saca los items de la tabla antes de rearmarla y la deja en
        `filas` filas vacias.

        setItem sobre una celda ocupada hace que Qt borre el item viejo, y
        ese item lo creo Python: el 2026-10-22 (labsim3, sync de las 14:12)
        el borrado desde Qt reventó en shiboken (segfault en
        unregisterWrapper) con el alumno recién entrado a su atención. Con
        takeItem el item vuelve a Python y se libera de este lado, y Qt no
        borra nada. Hay que guardar lo devuelto hasta terminar de llenar."""
        tabla = self.tableWidget
        tabla.setSortingEnabled(False)
        self._poner_anchos(llenando=True)
        sueltos = [tabla.takeItem(f, c) for f in range(tabla.rowCount())
                   for c in range(tabla.columnCount())]
        tabla.setRowCount(filas)
        return sueltos

    def _populate_practica(self):
        """Llena la tabla con los pacientes de la carpeta elegida, en su orden
        (ver _on_toggle_practica). Al buscar, en todas las carpetas."""
        keys = list(self._practica.keys())
        if self._filtro_texto:
            texto = self._filtro_texto
            keys = [
                k for k in keys
                if texto in vista.texto_busqueda(
                    *(self._practica[k].get(c) for c in ("rut", "nombre", "apellido", "carpeta")),
                    procedimiento=self._practica[k].get("procedimiento") or "")
            ]
        else:
            keys = [k for k in keys if self._practica[k].get("folder_id") == self._carpeta]
        prev_key = self._selected_row_key

        self._loading = True
        sueltos = self._vaciar_tabla(len(keys))
        conteo = {}
        for row_idx, key in enumerate(keys):
            it = self._practica[key]
            intentos = int(it.get("intentos") or 0)
            ultimo = (it.get("ultimo") or "")[:10]
            abierto = self._prueba_practica_activa(key) if self.is_admin else bool(it.get("abierto"))
            clave = "practica_curso" if abierto else ("practica_hecho" if intentos else "practica_nuevo")
            conteo[clave] = conteo.get(clave, 0) + 1
            orden = it.get("orden")
            columnas = (it.get("procedimiento") or "", str(intentos), it.get("rut") or "", it.get("nombre") or "",
                        it.get("apellido") or "", it.get("fecha_nac") or "", int(orden) if orden else "")
            pista = [f"Carpeta: {it['carpeta']}" if it.get("carpeta") else "",
                     f"Último intento: {ultimo}" if ultimo else ""]
            self._poner_fila(row_idx, key, clave, columnas, " · ".join(p for p in pista if p))
        self._terminar_llenado()
        del sueltos
        self._loading = False
        self._actualizar_resumen(len(keys), conteo)

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
            self._actualizar_detalle()

    def _intento_abierto(self, key):
        """Key de agenda del intento que el alumno dejó abierto en este
        paciente de práctica, o None."""
        abierto = self._practica.get(key, {}).get("abierto")
        return str(abierto) if abierto else None

    def _on_practica_selected(self, key):
        it = self._practica[key]
        self._selected_row_key = key
        self._selected_key = None
        if self.is_admin:
            clave = self._clave_caso_practica(it)
            self.btn_atender.setText("Cerrar/Evolucionar" if self._prueba_practica_activa(key) else "Atender (prueba)")
            self.btn_atender.setEnabled(clave is not None)
            self.btn_ver_ficha.setEnabled(clave is not None)
            self.btn_ficha_estudio.setEnabled(bool(it.get("case_id")))
            self.btn_no_show.setEnabled(False)
            return
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
        if self.is_admin:
            self._atender_practica_docente(key, it)
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

    def _atender_practica_docente(self, key, it):
        """En prueba, como el "Atender" del docente en su agenda (ver
        atender_paciente): no crea un intento ni deja registro."""
        if self._prueba_practica_activa(key):
            self._cerrar_atencion_prueba()
            return
        clave = self._clave_caso_practica(it)
        if clave is None or not hasattr(self.main_window, "atender_paciente_prueba"):
            return
        self.main_window.atender_paciente_prueba(clave, practica=it)
        self._prueba_atendiendo_key = clave
        self._on_selection_changed()
        self.populate_shedule()

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
        key = self._selected_row_key or ""
        if self.is_admin:
            fila = self.shedule.get("agenda_1", {}).get(key)
            case_id = (self._practica.get(key) or {}).get("case_id") or (fila.case_id if fila else None)
            if case_id:
                abrir_ficha_estudio(self, case_id=case_id)
            return
        it = self._practica.get(key)
        if it and it.get("ultimo_cerrado"):
            abrir_ficha_estudio(self, it["ultimo_cerrado"])

    def _reset_atender_button(self):
        if self._modo_practica:
            self.btn_atender.setText("Atender (prueba)" if self.is_admin else "Practicar")
        else:
            self.btn_atender.setText("Atender")
        self.btn_atender.setEnabled(False)
        self.btn_ver_ficha.setEnabled(False)
        self.btn_no_show.setEnabled(False)
        self.btn_ficha_estudio.setEnabled(False)
        if self.is_admin:
            self.chk_guardar_base.setEnabled(True)

    def _on_selection_changed(self):
        self._on_selection_changed_impl()
        if not self._loading:
            self._actualizar_detalle()

    def _on_selection_changed_impl(self):
        if self._loading:
            # Tabla a medio rearmar (ver _vaciar_tabla): las celdas estan
            # vacias. populate recalcula el boton al terminar.
            return
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
        if self.is_admin:
            self.btn_ficha_estudio.setEnabled(tiene_caso)

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

        # En práctica libre la fila elegida es "practica:<id>", no la del caso
        user = self.shedule["agenda_1"][self._prueba_atendiendo_key or self._selected_row_key]
        nombre = f"{user.nombre} {user.apellido}".strip()

        def _guardar(nota):
            self._prueba_atendiendo_key = None
            self.main_window.cerrar_atencion_prueba(nota)
            self._on_selection_changed()
            if self._modo_practica:
                self.populate_shedule()
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
        item_practica = None
        if self._modo_practica and self.is_admin:
            item_practica = self._practica.get(appointment_key, {})
            appointment_key = self._clave_caso_practica(item_practica)
            if appointment_key is None:
                return
        elif self._modo_practica:
            appointment_key = self._intento_abierto(self._selected_row_key)
            if appointment_key is None or appointment_key not in self.shedule.get("agenda_1", {}):
                return
        row = self.shedule["agenda_1"][appointment_key]
        if item_practica:
            row = fila_de_practica(row, item_practica)
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
            cuando = f"{row.fecha} {row.hora}".strip() if row.fecha and row.hora else None
            self.main_window.abrir_ficha_con(
                html, lambda: self._abrir_chat_paciente(row, case_id, appointment_key),
                (f"{row.nombre} {row.apellido}".strip(), self._datos_paciente(row.rut, row.procedimiento, cuando)),
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
            self.main_window.abrir_chat_con(case_id, nombre or "el paciente", edad, procedimiento, appointment_id,
                                            audiometria_previa(row, {"id": case_id}) is not None)

