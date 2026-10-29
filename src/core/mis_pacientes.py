# -*- coding: utf-8 -*-
"""Historial de pacientes atendidos por el alumno (vista propia).

Botón "Mis pacientes" al lado de Agenda/Bandeja (ver
ui_helpers.ToolBar.chargeBtnsArea), visible solo para alumnos (el admin/
docente ya tiene su propia vista equivalente y más completa en el portal
web: admin/student.php + admin/chat_detail.php). Lista los pacientes que el
alumno ha atendido; al elegir uno, muestra en pestañas:
  - Resumen: stats de comportamiento de esa atención puntual, la evolución
    que registró y lo que el docente le comentó.
  - Conversación: el chat con el paciente simulado, con la retroalimentación
    que el docente haya dejado turno a turno (ver chat_comments).
  - Ficha clínica: misma ficha que agenda.Agenda muestra al atender (motor
    compartido, ver core.ficha), acá en modo solo-lectura histórico.
  - Exámenes: los informes de esa atención. El ABR se abre en el módulo para
    mirarlo (solo lectura: una atención cerrada no se actualiza más); el PDF
    de cualquier examen se ve en el portal web, no acá. En un intento de
    práctica deliberada, si el docente lo permite, también la ficha de
    estudio del caso (ver core.practica).

Vive como subventana única del MDI (ver main.py: self.subw["MIS_PACIENTES"]),
igual que Agenda o la Bandeja de entrada. Se arma igual que la bandeja
(core/inbox.py): lista a la izquierda, lo elegido a la derecha, y la red en
segundo plano (core/hilos.py) para que la ventana no se congele."""

from datetime import datetime
from types import SimpleNamespace

import shiboken6
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QScrollArea, QTabWidget,
                               QTextBrowser, QVBoxLayout, QWidget)

from agenda.ChatPaciente import QSS_CHAT, _burbuja, _ListaMensajes
from core import hilos, iconos, tema
from core.ficha import poner_html, render_ficha_html
from core.helpers import CasesOffline, Shedule, mi_conversacion, mis_atenciones, mis_informes
from core.inbox import fecha_corta, fecha_larga, _Elidida
from core.practica import abrir_ficha_estudio

BTN_OBJECT_NAME = "btn_mis_pacientes"

NOMBRE_EXAMEN = {
    "ABR": "PEATC (ABR)",
    "ELECTROCOCLEO": "Electrococleografía",
    "PEALM": "Potencial de latencia media (PEALM)",
    "CAEP": "Potencial cortical (P1-N1-P2)",
    "P300": "P300",
    "MMN": "Negatividad de disparidad (MMN)",
    "ASSR": "Potenciales de estado estable (ASSR)",
    "AABR": "Tamizaje automatizado (AABR)",
    "EOA": "Emisiones otoacústicas",
    "VEMP": "VEMP",
    "OTOSCOPIA": "Otoscopia",
}
ICONO_EXAMEN = {
    "ABR": "onda_abr", "ELECTROCOCLEO": "onda_abr", "PEALM": "onda_abr", "CAEP": "onda_abr",
    "P300": "onda_abr", "MMN": "onda_abr", "ASSR": "onda_abr", "AABR": "onda_check",
    "EOA": "coclea", "VEMP": "barras", "OTOSCOPIA": "otoscopio",
}
# Los que se pueden abrir en el módulo para mirarlos: guardan las curvas
# con su trazo y el ABR las vuelve a dibujar.
SE_ABREN_EN_EL_ABR = ("ABR", "ELECTROCOCLEO", "PEALM", "CAEP", "P300", "MMN", "ASSR")
AVISO_PDF = ("El informe en PDF de cada examen lo ves en la web: "
             "<i>Pacientes que has atendido → la atención → Tus informes</i>.")

QSS = f"""
QFrame#lista, QFrame#detalle {{
    background: {tema.TARJETA};
    border: 1px solid {tema.BORDE};
    border-radius: 10px;
}}
QWidget#filas, QWidget#pagina {{ background: transparent; }}
QFrame[fila="true"] {{
    background: transparent;
    border: none;
    border-bottom: 1px solid {tema.BORDE};
    border-left: 3px solid transparent;
}}
QFrame[fila="true"]:hover {{ background: {tema.TARJETA_ALT}; }}
QFrame[fila="true"][elegida="true"] {{
    background: {tema.ACENTO_SUAVE};
    border-left: 3px solid {tema.ACENTO};
}}
QLabel#iniciales {{
    background: {tema.ACENTO_SUAVE};
    color: {tema.ACENTO};
    border-radius: 17px;
    font-weight: 700;
}}
QLabel#inicialesGrande {{
    background: {tema.ACENTO_SUAVE};
    color: {tema.ACENTO};
    border-radius: 22px;
    font-size: 12pt;
    font-weight: 700;
}}
QLabel#nombre {{ font-weight: 700; color: {tema.TEXTO}; }}
QLabel#proc {{ color: {tema.TEXTO_SUAVE}; font-size: 8.5pt; }}
QLabel#fecha {{ color: {tema.TEXTO_TENUE}; font-size: 8pt; }}
QLabel#titulo {{ font-size: 13pt; font-weight: 600; color: {tema.TEXTO}; }}
QLabel#subtitulo {{ color: {tema.TEXTO_SUAVE}; }}
QLabel#paciente {{ font-size: 12pt; font-weight: 700; color: {tema.TEXTO}; }}
QLineEdit {{
    background: {tema.TARJETA};
    border: 1px solid {tema.BORDE_FUERTE};
    border-radius: 7px;
    padding: 5px 8px;
}}
QLineEdit:focus {{ border-color: {tema.ACENTO}; }}
QTabWidget::pane {{ border: none; background: transparent; top: 0px; }}
QTabBar::tab {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 6px 12px;
    margin-right: 2px;
    font-size: 9pt;
    font-weight: 600;
    color: {tema.TEXTO_TENUE};
}}
QTabBar::tab:selected {{ color: {tema.ACENTO}; border-bottom-color: {tema.ACENTO}; }}
QTabBar::tab:hover:!selected {{ color: {tema.TEXTO_SUAVE}; }}
QFrame[card="dato"] {{
    background: {tema.TARJETA_ALT};
    border: 1px solid {tema.BORDE};
    border-radius: 8px;
}}
QLabel[role="dato"][alerta="true"] {{ color: {tema.ALERTA}; }}
QFrame#evolucion {{
    background: {tema.TARJETA_ALT};
    border: 1px solid {tema.BORDE};
    border-radius: 8px;
}}
QFrame#notaDocente {{
    background: {tema.NOTA_DOCENTE};
    border: 1px solid {tema.NOTA_DOCENTE_BORDE};
    border-radius: 8px;
}}
QLabel#notaDe {{ color: {tema.NOTA_DOCENTE_TEXTO}; font-size: 8pt; font-weight: 700; }}
QFrame[examen="true"] {{
    background: {tema.TARJETA};
    border: 1px solid {tema.BORDE};
    border-radius: 8px;
}}
QTextBrowser {{ border: none; background: transparent; }}
""" + QSS_CHAT


def _nombre(it):
    return f"{it.get('nombre', '')} {it.get('apellido', '')}".strip() or "Paciente sin nombre"


def _iniciales(it):
    partes = [p for p in (it.get("nombre", ""), it.get("apellido", "")) if p]
    return "".join(p[0].upper() for p in partes[:2]) or "?"


def _cuando(it):
    """'Audiometría · 27 oct 2026, 14:00'."""
    fecha = it.get("fecha")
    cuando = fecha_larga(f"{fecha} {it.get('hora') or '00:00'}") if fecha else ""
    return " · ".join(x for x in (it.get("procedimiento") or "", cuando) if x)


def _hora(texto):
    """Solo la hora de un 'YYYY-MM-DD HH:MM:SS' (los turnos del chat)."""
    try:
        return datetime.strptime(str(texto)[:16], "%Y-%m-%d %H:%M").strftime("%H:%M")
    except ValueError:
        return str(texto or "")


def _fmt_duracion(segundos):
    segundos = int(segundos or 0)
    minutos, seg = divmod(segundos, 60)
    return f"{minutos} min {seg} s" if minutos else f"{seg} s"


def _seccion(texto):
    lbl = QLabel(texto)
    lbl.setProperty("role", "seccion")
    return lbl


def _nota_docente(comentario):
    """Un comentario del docente: nota amarilla con quién y cuándo."""
    marco = QFrame()
    marco.setObjectName("notaDocente")
    col = QVBoxLayout(marco)
    col.setContentsMargins(10, 6, 10, 8)
    col.setSpacing(2)
    de = QLabel(f"{comentario.get('teacher_name') or 'Docente'} (docente) · "
                f"{fecha_larga(comentario.get('created_at'))}")
    de.setObjectName("notaDe")
    texto = QLabel(comentario.get("comment", ""))
    texto.setTextFormat(Qt.TextFormat.PlainText)
    texto.setWordWrap(True)
    texto.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    col.addWidget(de)
    col.addWidget(texto)
    return marco


def _vaciar(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget() is not None:
            # Escondido ya: deleteLater lo borra después y mientras tanto
            # quedaba dibujado encima de lo nuevo.
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout() is not None:
            _vaciar(item.layout())


class _Fila(QFrame):
    """Una atención en la lista: iniciales, paciente, procedimiento y fecha."""
    elegida = Signal(object)

    def __init__(self, it):
        super().__init__()
        self.it = it
        self.setProperty("fila", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        fila = QHBoxLayout(self)
        fila.setContentsMargins(10, 7, 10, 7)
        fila.setSpacing(9)
        ini = QLabel(_iniciales(it))
        ini.setObjectName("iniciales")
        ini.setFixedSize(34, 34)
        ini.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila.addWidget(ini)
        col = QVBoxLayout()
        col.setSpacing(0)
        arriba = QHBoxLayout()
        arriba.setSpacing(6)
        nombre = _Elidida(_nombre(it))
        nombre.setObjectName("nombre")
        fecha = QLabel(fecha_corta(f"{it.get('fecha') or ''} {it.get('hora') or '00:00'}"))
        fecha.setObjectName("fecha")
        arriba.addWidget(nombre, 1)
        arriba.addWidget(fecha)
        col.addLayout(arriba)
        abajo = QHBoxLayout()
        abajo.setSpacing(6)
        proc = _Elidida(it.get("procedimiento") or "—")
        proc.setObjectName("proc")
        abajo.addWidget(proc, 1)
        if it.get("practica"):
            # Intento de práctica deliberada: se rotula, no se esconde.
            pill = QLabel("práctica")
            pill.setProperty("pill", "acento")
            abajo.addWidget(pill)
        col.addLayout(abajo)
        fila.addLayout(col, 1)
        self.pintar(False)

    def pintar(self, elegida):
        self.setProperty("elegida", "true" if elegida else "false")
        tema.repintar(self)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.elegida.emit(self)
        super().mousePressEvent(ev)


class MisPacientesWidget(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._items = []
        self._filas = []
        self._actual = None
        self._shedule = {}
        self._cases = {}
        self._examenes = []
        self._atencion = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        tema.aplicar_estilo(self, QSS)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(8)
        raiz.addLayout(self._cabecera())
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(10)
        cuerpo.addWidget(self._lista())
        cuerpo.addWidget(self._detalle(), 1)
        raiz.addLayout(cuerpo, 1)
        self._mostrar_vacio("Cargando tus atenciones…")

    # ------------------------------------------------------------ armado
    def _cabecera(self):
        fila = QHBoxLayout()
        fila.setSpacing(8)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        titulo = QLabel("Mis pacientes")
        titulo.setObjectName("titulo")
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setObjectName("subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(self.lbl_resumen)
        fila.addLayout(textos, 1)
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar paciente o procedimiento…")
        self.buscar.addAction(iconos.icono("buscar", tema.TEXTO_TENUE, 16),
                              QLineEdit.ActionPosition.LeadingPosition)
        self.buscar.setClearButtonEnabled(True)
        self.buscar.setFixedWidth(260)
        self.buscar.textChanged.connect(self._filtrar)
        fila.addWidget(self.buscar)
        return fila

    def _lista(self):
        marco = QFrame()
        marco.setObjectName("lista")
        marco.setFixedWidth(280)
        col = QVBoxLayout(marco)
        col.setContentsMargins(1, 1, 1, 1)
        self.filas = QWidget()
        self.filas.setObjectName("filas")
        self.col_filas = QVBoxLayout(self.filas)
        self.col_filas.setContentsMargins(0, 0, 0, 0)
        self.col_filas.setSpacing(0)
        self.col_filas.addStretch(1)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.filas)
        col.addWidget(self.scroll)
        return marco

    def _detalle(self):
        marco = QFrame()
        marco.setObjectName("detalle")
        col = QVBoxLayout(marco)
        col.setContentsMargins(14, 12, 14, 10)
        col.setSpacing(6)

        self.cabeza = QWidget()
        cab = QHBoxLayout(self.cabeza)
        cab.setContentsMargins(0, 0, 0, 0)
        cab.setSpacing(10)
        self.lbl_ini = QLabel()
        self.lbl_ini.setObjectName("inicialesGrande")
        self.lbl_ini.setFixedSize(44, 44)
        self.lbl_ini.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cab.addWidget(self.lbl_ini)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.lbl_paciente = QLabel()
        self.lbl_paciente.setObjectName("paciente")
        self.lbl_cuando = QLabel()
        self.lbl_cuando.setObjectName("subtitulo")
        textos.addWidget(self.lbl_paciente)
        textos.addWidget(self.lbl_cuando)
        cab.addLayout(textos, 1)
        self.lbl_practica = QLabel("Práctica deliberada")
        self.lbl_practica.setProperty("pill", "acento")
        cab.addWidget(self.lbl_practica, 0, Qt.AlignmentFlag.AlignTop)
        col.addWidget(self.cabeza)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._pagina_resumen(), iconos.icono("lista", tema.TEXTO_SUAVE, 16), "Resumen")
        self.tabs.addTab(self._pagina_conversacion(), iconos.icono("mensaje", tema.TEXTO_SUAVE, 16), "Conversación")
        self.texto_ficha = QTextBrowser()
        self.tabs.addTab(self.texto_ficha, iconos.icono("ficha", tema.TEXTO_SUAVE, 16), "Ficha clínica")
        self.tabs.addTab(self._pagina_examenes(), iconos.icono("onda_abr", tema.TEXTO_SUAVE, 16), "Exámenes")
        col.addWidget(self.tabs, 1)

        self.vacio = QWidget()
        vcol = QVBoxLayout(self.vacio)
        vcol.addStretch(1)
        ico = QLabel()
        ico.setPixmap(iconos.pixmap("persona", tema.TEXTO_TENUE, 40))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio = QLabel()
        self.lbl_vacio.setProperty("role", "hint")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.setWordWrap(True)
        vcol.addWidget(ico)
        vcol.addWidget(self.lbl_vacio)
        vcol.addStretch(2)
        col.addWidget(self.vacio, 1)
        return marco

    @staticmethod
    def _pagina_con_scroll():
        pagina = QWidget()
        pagina.setObjectName("pagina")
        col = QVBoxLayout(pagina)
        col.setContentsMargins(2, 10, 8, 4)
        col.setSpacing(8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(pagina)
        return scroll, col

    def _pagina_resumen(self):
        scroll, self.col_resumen = self._pagina_con_scroll()
        return scroll

    def _pagina_conversacion(self):
        self.lista_chat = _ListaMensajes()
        # "vacioChat": _ListaMensajes.vaciar() lo deja, solo se esconde.
        self.aviso_chat = QLabel()
        self.aviso_chat.setObjectName("vacioChat")
        self.aviso_chat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso_chat.setWordWrap(True)
        self.lista_chat.agregar(self.aviso_chat)
        return self.lista_chat

    def _pagina_examenes(self):
        scroll, col = self._pagina_con_scroll()
        self.col_examenes = QVBoxLayout()
        self.col_examenes.setSpacing(6)
        col.addLayout(self.col_examenes)
        self.btn_ficha_estudio = QPushButton(" Ficha de estudio (PDF)")
        self.btn_ficha_estudio.setIcon(iconos.icono_boton("ficha", tema.TEXTO_SUAVE, tam=15))
        self.btn_ficha_estudio.setToolTip("Los resultados del caso, para comparar con lo que obtuviste")
        self.btn_ficha_estudio.setVisible(False)
        self.btn_ficha_estudio.clicked.connect(self._ver_ficha_estudio)
        col.addWidget(self.btn_ficha_estudio, 0, Qt.AlignmentFlag.AlignLeft)
        self.lbl_examenes = QLabel(AVISO_PDF)
        self.lbl_examenes.setWordWrap(True)
        self.lbl_examenes.setProperty("role", "hint")
        col.addWidget(self.lbl_examenes)
        col.addStretch(1)
        return scroll

    # ------------------------------------------------------------ lista
    def refresh(self):
        """Recarga las atenciones y el estado local (agenda/casos) que la
        ficha clínica necesita, sin congelar la ventana."""
        if not self._items:
            self._mostrar_vacio("Cargando tus atenciones…")
        hilos.en_fondo(self._leer_todo, dueno=self, nombre="mis_pacientes", listo=self._cargar)

    @staticmethod
    def _leer_todo():
        items = mis_atenciones()
        try:
            shedule = Shedule().get()
        except Exception:
            shedule = {}
        try:
            cases = CasesOffline().get_cases()
        except Exception:
            cases = {}
        return items, shedule, cases

    def _cargar(self, resultado):
        items, self._shedule, self._cases = resultado
        actual = self._actual.it.get("appointment_id") if self._actual is not None else None
        self._items = list(items or [])
        self._armar_filas()
        destino = next((f for f in self._filas if f.it.get("appointment_id") == actual), None)
        if destino is None and self._filas:
            destino = self._filas[0]
        if destino is not None:
            self._abrir(destino)
        n = len(self._items)
        practica = sum(1 for it in self._items if it.get("practica"))
        self.lbl_resumen.setText(
            "Todavía no has cerrado ninguna atención." if not n else
            f"{n} atenci{'ones' if n != 1 else 'ón'}" + (f" · {practica} de práctica" if practica else ""))

    def _armar_filas(self):
        for f in self._filas:
            f.setParent(None)
            f.deleteLater()
        self._filas = []
        self._actual = None
        for it in self._items:
            fila = _Fila(it)
            fila.elegida.connect(self._abrir)
            self.col_filas.insertWidget(self.col_filas.count() - 1, fila)
            self._filas.append(fila)
        if not self._filas:
            self._mostrar_vacio("Cuando cierres una atención, aquí verás el paciente, la "
                                "conversación, la ficha y los exámenes que guardaste.")
        self._filtrar(self.buscar.text())

    def _filtrar(self, texto):
        buscado = _plano(texto)
        for f in self._filas:
            f.setVisible(buscado in _plano(f"{_nombre(f.it)} {f.it.get('procedimiento') or ''}"))
        # Si lo abierto quedó fuera de la búsqueda, se abre el primero que sí.
        visibles = [f for f in self._filas if not f.isHidden()]
        if self._actual is not None and self._actual.isHidden() and visibles:
            self._abrir(visibles[0])

    def keyPressEvent(self, ev):
        """↑ / ↓ pasan a la atención anterior / siguiente."""
        paso = {Qt.Key.Key_Up: -1, Qt.Key.Key_Down: 1}.get(ev.key())
        visibles = [f for f in self._filas if not f.isHidden()]
        if paso is None or not visibles:
            super().keyPressEvent(ev)
            return
        i = visibles.index(self._actual) if self._actual in visibles else -1
        self._abrir(visibles[max(0, min(len(visibles) - 1, i + paso))])

    # ------------------------------------------------------------ detalle
    def _mostrar_vacio(self, texto):
        self.cabeza.hide()
        self.tabs.hide()
        self.lbl_vacio.setText(texto)
        self.vacio.show()

    def _abrir(self, fila):
        if self._actual is not None and shiboken6.isValid(self._actual):
            self._actual.pintar(False)
        self._actual = fila
        fila.pintar(True)
        self.scroll.ensureWidgetVisible(fila)
        it = fila.it
        self.vacio.hide()
        self.cabeza.show()
        self.tabs.show()
        self.lbl_ini.setText(_iniciales(it))
        self.lbl_paciente.setText(_nombre(it))
        self.lbl_cuando.setText(_cuando(it))
        self.lbl_practica.setVisible(bool(it.get("practica")))
        self._mostrar_resumen(it)
        self._mostrar_ficha(it)
        self._pedir_conversacion(it)
        self._pedir_examenes(it)

    def _mostrar_resumen(self, it):
        _vaciar(self.col_resumen)
        col = self.col_resumen
        stats = it.get("stats") or {}

        horas = QLabel(" · ".join(
            f"{rotulo} {valor}" for rotulo, valor in (
                ("Cita", it.get("hora")), ("inicio real", it.get("hora_real")),
                ("cerrada", fecha_larga(it.get("updated_at")) if it.get("updated_at") else None))
            if valor))
        horas.setProperty("role", "hint")
        col.addWidget(horas)

        col.addWidget(_seccion("DURANTE LA ATENCIÓN"))
        grilla = QGridLayout()
        grilla.setSpacing(6)
        delta = stats.get("avg_delta_s")
        datos = (
            ("Duración total", _fmt_duracion(stats.get("total_duration_s")), False),
            ("Bloques de actividad", stats.get("n_sessions", 0), False),
            ("Mensajes con el paciente", it.get("n_chat_messages", 0), False),
            ("Pausas largas (≥ 30 s)", stats.get("long_pauses", 0), bool(stats.get("long_pauses"))),
            ("Acciones sin pausa", stats.get("no_pause_actions", 0), False),
            ("Tiempo entre acciones", f"{delta} s" if delta is not None else "—", False),
        )
        for i, (rotulo, valor, alerta) in enumerate(datos):
            tarjeta = QFrame()
            tarjeta.setProperty("card", "dato")
            t = QVBoxLayout(tarjeta)
            t.setContentsMargins(10, 6, 10, 7)
            t.setSpacing(0)
            lbl_valor = QLabel(str(valor))
            lbl_valor.setProperty("role", "dato")
            lbl_valor.setProperty("alerta", "true" if alerta else "false")
            lbl_rotulo = QLabel(rotulo)
            lbl_rotulo.setProperty("role", "hint")
            t.addWidget(lbl_valor)
            t.addWidget(lbl_rotulo)
            grilla.addWidget(tarjeta, i // 3, i % 3)
        col.addLayout(grilla)

        if it.get("nota"):
            col.addWidget(_seccion("TU EVOLUCIÓN"))
            marco = QFrame()
            marco.setObjectName("evolucion")
            m = QVBoxLayout(marco)
            m.setContentsMargins(10, 8, 10, 8)
            nota = QLabel(it["nota"])
            nota.setTextFormat(Qt.TextFormat.PlainText)
            nota.setWordWrap(True)
            nota.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            m.addWidget(nota)
            col.addWidget(marco)
        for clave, sobre in (("evolucion_comments", "TU EVOLUCIÓN"),
                             ("procedimiento_comments", "EL PROCEDIMIENTO")):
            comentarios = it.get(clave) or []
            if comentarios:
                col.addWidget(_seccion(f"TU DOCENTE SOBRE {sobre}"))
                for c in comentarios:
                    col.addWidget(_nota_docente(c))
        col.addStretch(1)

    def _pedir_conversacion(self, it):
        self.lista_chat.vaciar()
        appointment_id = it.get("appointment_id")
        self._aviso_chat("Cargando la conversación…")
        if not appointment_id:
            self._aviso_chat("Sin conversación registrada para esta atención.")
            return
        hilos.en_fondo(mi_conversacion, appointment_id, dueno=self, nombre="mis_pacientes_chat",
                       listo=lambda turnos, a=appointment_id: self._mostrar_conversacion(a, turnos))

    def _aviso_chat(self, texto):
        self.lista_chat.vaciar()
        self.aviso_chat.setText(texto)
        self.aviso_chat.show()

    def _mostrar_conversacion(self, appointment_id, turnos):
        if self._atencion_actual() != appointment_id:
            return      # llegó tarde: ya se eligió otra atención
        if not turnos:
            self._aviso_chat("Sin conversación registrada para esta atención.")
            return
        self.lista_chat.vaciar()
        self.aviso_chat.hide()
        for turno in turnos:
            propia = turno.get("role") == "user"
            etiqueta = f"{'Tú' if propia else 'Paciente'} · {_hora(turno.get('created_at'))}"
            burbuja = _burbuja(turno.get("content", ""), propia, etiqueta,
                               tema.ACENTO if propia else tema.TEXTO_SUAVE)
            fila = QHBoxLayout()
            contenedor = QWidget()
            contenedor.setLayout(fila)
            fila.setContentsMargins(0, 0, 0, 0)
            if propia:
                fila.addStretch(1)
            fila.addWidget(burbuja)
            if not propia:
                fila.addStretch(1)
            self.lista_chat.agregar(contenedor, burbuja)
            for c in turno.get("comments", []):
                nota = _nota_docente(c)
                nota.setMaximumWidth(460)
                envoltura = QWidget()
                h = QHBoxLayout(envoltura)
                h.setContentsMargins(0, 0, 0, 0)
                h.addStretch(1)
                h.addWidget(nota, 4)
                h.addStretch(1)
                self.lista_chat.agregar(envoltura)
        self.lista_chat._pegado = False
        self.lista_chat.verticalScrollBar().setValue(0)

    def _mostrar_ficha(self, it):
        case_id = it.get("case_id")
        appointment_id = it.get("appointment_id")
        if not case_id:
            self.texto_ficha.setHtml(
                f"<p style='color:{tema.TEXTO_TENUE};'>Este registro no tiene un caso clínico asociado.</p>")
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
                practice_id=1 if it.get("practica") else None,
            )
        caso = self._cases.get(case_id, {})
        username = (self._main_window.data_login.get("user")
                    if self._main_window and getattr(self._main_window, "data_login", None) else None)
        # Una atención ya hecha: lo que trajo el paciente se ve entero
        poner_html(self.texto_ficha, render_ficha_html(row, caso, self._shedule, username, False, todos=True))

    # ------------------------------------------------------------ exámenes
    def _atencion_actual(self):
        return self._actual.it.get("appointment_id") if self._actual is not None else None

    def _pedir_examenes(self, it):
        self._atencion = it
        self._examenes = []
        _vaciar(self.col_examenes)
        self.btn_ficha_estudio.setVisible(bool(it.get("ficha_estudio")))
        appointment_id = it.get("appointment_id")
        if not appointment_id:
            self._mostrar_examenes(it, [])
            return
        self.lbl_examenes.setText("Cargando los exámenes…")
        hilos.en_fondo(mis_informes, appointment_id, dueno=self, nombre="mis_pacientes_examenes",
                       listo=lambda informes, i=it: self._mostrar_examenes(i, informes))

    def _mostrar_examenes(self, it, informes):
        if it is not self._atencion:
            return      # llegó tarde: ya se eligió otra atención
        self._examenes = list(informes or [])
        _vaciar(self.col_examenes)
        self.botones_abr = []
        for informe in self._examenes:
            tipo = informe.get("tipo", "")
            marco = QFrame()
            marco.setProperty("examen", "true")
            fila = QHBoxLayout(marco)
            fila.setContentsMargins(10, 7, 8, 7)
            fila.setSpacing(10)
            ico = QLabel()
            ico.setPixmap(iconos.pixmap(ICONO_EXAMEN.get(tipo, "ficha"), tema.ACENTO, 20))
            fila.addWidget(ico)
            textos = QVBoxLayout()
            textos.setSpacing(0)
            nombre = QLabel(NOMBRE_EXAMEN.get(tipo, tipo))
            nombre.setStyleSheet("font-weight: 600;")
            guardado = QLabel(f"Guardado {fecha_larga(informe.get('updated_at'))}"
                              if informe.get("updated_at") else "Guardado")
            guardado.setProperty("role", "hint")
            textos.addWidget(nombre)
            textos.addWidget(guardado)
            fila.addLayout(textos, 1)
            if tipo in SE_ABREN_EN_EL_ABR:
                btn = QPushButton(" Ver en el ABR")
                btn.setIcon(iconos.icono_boton("onda_abr", tema.TEXTO_SUAVE, tam=15))
                btn.setToolTip("Abre las curvas en el módulo ABR, solo para mirarlas")
                btn.clicked.connect(lambda _=False, inf=informe: self._ver_en_abr(inf))
                fila.addWidget(btn)
                self.botones_abr.append(btn)
            self.col_examenes.addWidget(marco)
        self.lbl_examenes.setText(
            AVISO_PDF if self._examenes else "Esta atención no tiene exámenes guardados.")

    def _ver_en_abr(self, informe):
        if informe is None or informe.get("tipo") not in SE_ABREN_EN_EL_ABR:
            return
        it = self._atencion or {}
        aviso = f"{_nombre(it) if it.get('nombre') or it.get('apellido') else 'el paciente'}" \
                f" · atención del {it.get('fecha') or '—'}: solo lectura"
        if self._main_window is not None and hasattr(self._main_window, "abrir_abr_consulta"):
            self._main_window.abrir_abr_consulta(informe.get("data") or {}, aviso)

    def _ver_ficha_estudio(self):
        it = self._atencion or {}
        if it.get("ficha_estudio") and it.get("appointment_id"):
            abrir_ficha_estudio(self, it["appointment_id"])


def _plano(texto):
    tabla = str.maketrans("áéíóúüñ", "aeiouun")
    return str(texto).lower().translate(tabla).strip()


def crear_boton(main_window, layout):
    """Crea el botón y lo agrega a `layout` -- se llama cada vez que
    ui_helpers.chargeBtnsArea reconstruye la sección "Sala de Espera" (cambia
    de sección = destruye y recrea los botones)."""
    btn = QPushButton("Mis pacientes")
    btn.setObjectName(BTN_OBJECT_NAME)
    btn.setToolTip("Pacientes que has atendido")
    btn.setIcon(iconos.icono_boton("persona", tema.TEXTO_SUAVE, tema.ACENTO, 18))
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
