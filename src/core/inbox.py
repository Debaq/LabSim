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
Agenda o el chat con el paciente, en vez de un diálogo emergente.

Se lee como un correo: la lista a la izquierda con un adelanto de cada
mensaje y el abierto a la derecha. Al abrir la bandeja se muestra el primer
no leído, las flechas pasan de uno a otro y "Marcar todo como leído" evita
tener que abrirlos uno por uno. La red va en segundo plano (core/hilos.py):
la ventana no se congela esperando al servidor."""

import html as html_lib
from datetime import date, datetime, timedelta

import shiboken6
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget)

from core import hilos, iconos, tema
from core.helpers import inbox_list, inbox_marcar_leido

BTN_OBJECT_NAME = "btn_bandeja_oirs"
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")

QSS = f"""
QFrame#lista {{
    background: {tema.TARJETA};
    border: 1px solid {tema.BORDE};
    border-radius: 10px;
}}
QWidget#filas {{ background: transparent; }}
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
QLabel#remitente {{ color: {tema.TEXTO_SUAVE}; font-size: 8.5pt; }}
QLabel#remitente[nuevo="true"] {{ color: {tema.TEXTO}; font-weight: 700; }}
QLabel#asunto {{ color: {tema.TEXTO}; }}
QLabel#asunto[nuevo="true"] {{ font-weight: 700; }}
QLabel#adelanto {{ color: {tema.TEXTO_TENUE}; font-size: 8pt; }}
QLabel#fecha {{ color: {tema.TEXTO_TENUE}; font-size: 8pt; }}
QLabel#fecha[nuevo="true"] {{ color: {tema.ACENTO}; font-weight: 600; }}
QFrame#lectura {{
    background: {tema.TARJETA};
    border: 1px solid {tema.BORDE};
    border-radius: 10px;
}}
QLabel#titulo {{ font-size: 13pt; font-weight: 600; color: {tema.TEXTO}; }}
QLabel#subtitulo {{ color: {tema.TEXTO_SUAVE}; }}
QLabel#lecturaAsunto {{ font-size: 12pt; font-weight: 700; color: {tema.TEXTO}; }}
QLabel#lecturaDe {{ color: {tema.TEXTO_SUAVE}; }}
QFrame#aviso {{
    background: {tema.OI_SUAVE};
    border: 1px solid #C9D8F5;
    border-radius: 8px;
}}
QLabel#avisoTexto {{ color: #34507A; font-size: 8.5pt; }}
QTextBrowser {{ border: none; background: transparent; font-size: 10pt; }}
QPushButton[filtro="true"] {{ padding: 4px 12px; }}
"""


def fecha_corta(texto, hoy=None):
    """'2026-10-27 14:32:05' -> '14:32' si es de hoy, 'ayer', '12 oct', o
    '12 oct 2025' si es de otro año."""
    try:
        cuando = datetime.strptime(str(texto)[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        return str(texto or "")
    hoy = hoy or date.today()
    if cuando.date() == hoy:
        return cuando.strftime("%H:%M")
    if cuando.date() == hoy - timedelta(days=1):
        return "ayer"
    corta = f"{cuando.day} {MESES[cuando.month - 1]}"
    return corta if cuando.year == hoy.year else f"{corta} {cuando.year}"


def fecha_larga(texto):
    try:
        cuando = datetime.strptime(str(texto)[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        return str(texto or "")
    return f"{cuando.day} {MESES[cuando.month - 1]} {cuando.year}, {cuando:%H:%M}"


class _Elidida(QLabel):
    """Una línea que se corta con "…" al ancho que tenga."""

    def __init__(self, texto=""):
        super().__init__()
        self._completo = " ".join(str(texto).split())
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setText(self._completo)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.setText(self.fontMetrics().elidedText(self._completo, Qt.TextElideMode.ElideRight,
                                                   max(0, self.width())))


class _Fila(QFrame):
    """Un mensaje en la lista: remitente y fecha, asunto y el comienzo del texto."""
    elegida = Signal(object)

    def __init__(self, it):
        super().__init__()
        self.it = it
        self.setProperty("fila", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        col = QVBoxLayout(self)
        col.setContentsMargins(10, 7, 10, 8)
        col.setSpacing(1)
        arriba = QHBoxLayout()
        arriba.setSpacing(6)
        self.punto = QLabel()
        self.punto.setFixedSize(8, 8)
        self.remitente = _Elidida(it.get("remitente") or "Sistema")
        self.remitente.setObjectName("remitente")
        self.fecha = QLabel(fecha_corta(it.get("created_at")))
        self.fecha.setObjectName("fecha")
        arriba.addWidget(self.punto)
        arriba.addWidget(self.remitente, 1)
        arriba.addWidget(self.fecha)
        col.addLayout(arriba)
        self.asunto = _Elidida(it.get("asunto", ""))
        self.asunto.setObjectName("asunto")
        self.adelanto = _Elidida(it.get("cuerpo", ""))
        self.adelanto.setObjectName("adelanto")
        col.addWidget(self.asunto)
        col.addWidget(self.adelanto)
        self.pintar(False)

    def pintar(self, elegida):
        nuevo = "false" if self.it.get("leido") else "true"
        self.setProperty("elegida", "true" if elegida else "false")
        for w in (self.remitente, self.asunto, self.fecha):
            w.setProperty("nuevo", nuevo)
            tema.repintar(w)
        self.punto.setStyleSheet(
            f"background: {tema.ACENTO if nuevo == 'true' else 'transparent'}; border-radius: 4px;")
        tema.repintar(self)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.elegida.emit(self)
        super().mousePressEvent(ev)


class InboxWidget(QWidget):
    """Lista de mensajes a la izquierda y el elegido a la derecha. refresh()
    recarga contra el backend -- se llama cada vez que se abre la
    subventana, no solo al crearla."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._items = []
        self._filas = []
        self._actual = None
        self._solo_nuevos = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        tema.aplicar_estilo(self, QSS)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(8)
        raiz.addLayout(self._cabecera())

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(10)
        cuerpo.addWidget(self._lista())
        cuerpo.addWidget(self._lectura(), 1)
        raiz.addLayout(cuerpo, 1)
        self._pintar_vacio("Cargando mensajes…")

    # ------------------------------------------------------------ armado
    def _cabecera(self):
        fila = QHBoxLayout()
        fila.setSpacing(8)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        titulo = QLabel("Bandeja de entrada")
        titulo.setObjectName("titulo")
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setObjectName("subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(self.lbl_resumen)
        fila.addLayout(textos, 1)

        grupo = QButtonGroup(self)
        for texto, solo in (("Todos", False), ("Sin leer", True)):
            btn = QPushButton(texto)
            btn.setCheckable(True)
            btn.setProperty("filtro", "true")
            btn.setChecked(not solo)
            btn.clicked.connect(lambda _=False, s=solo: self._filtrar(s))
            grupo.addButton(btn)
            fila.addWidget(btn)
        self.btn_sin_leer = grupo.buttons()[1]

        self.btn_todo_leido = QPushButton(" Marcar todo como leído")
        self.btn_todo_leido.setIcon(iconos.icono_boton("check", tema.TEXTO_SUAVE, tam=15))
        self.btn_todo_leido.clicked.connect(self.marcar_todo_leido)
        fila.addSpacing(6)
        fila.addWidget(self.btn_todo_leido)
        return fila

    def _lista(self):
        marco = QFrame()
        marco.setObjectName("lista")
        marco.setFixedWidth(270)
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

    def _lectura(self):
        marco = QFrame()
        marco.setObjectName("lectura")
        col = QVBoxLayout(marco)
        col.setContentsMargins(18, 14, 18, 14)
        col.setSpacing(6)

        self.lbl_tipo = QLabel()
        self.lbl_tipo.setProperty("pill", "acento")
        self.lbl_tipo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.lbl_asunto = QLabel()
        self.lbl_asunto.setObjectName("lecturaAsunto")
        self.lbl_asunto.setWordWrap(True)
        self.lbl_de = QLabel()
        self.lbl_de.setObjectName("lecturaDe")
        self.lbl_de.setWordWrap(True)
        col.addWidget(self.lbl_tipo)
        col.addWidget(self.lbl_asunto)
        col.addWidget(self.lbl_de)

        # Los de la OIRS simulada traen `aviso` (ver Oirs.php en el backend):
        # va antes del texto, para que nadie lea una sugerencia del paciente
        # virtual como una queja real.
        self.caja_aviso = QFrame()
        self.caja_aviso.setObjectName("aviso")
        fila = QHBoxLayout(self.caja_aviso)
        fila.setContentsMargins(10, 8, 10, 8)
        fila.setSpacing(8)
        ico = QLabel()
        ico.setPixmap(iconos.pixmap("info", "#34507A", 18))
        ico.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lbl_aviso = QLabel()
        self.lbl_aviso.setObjectName("avisoTexto")
        self.lbl_aviso.setWordWrap(True)
        fila.addWidget(ico)
        fila.addWidget(self.lbl_aviso, 1)
        col.addWidget(self.caja_aviso)

        self.txt_cuerpo = QTextBrowser()
        self.txt_cuerpo.setOpenExternalLinks(False)
        col.addWidget(self.txt_cuerpo, 1)

        # Sin mensaje elegido (o sin mensajes): icono y una línea.
        self.vacio = QWidget()
        vcol = QVBoxLayout(self.vacio)
        vcol.addStretch(1)
        ico_vacio = QLabel()
        ico_vacio.setPixmap(iconos.pixmap("bandeja", tema.TEXTO_TENUE, 40))
        ico_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio = QLabel()
        self.lbl_vacio.setProperty("role", "hint")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vcol.addWidget(ico_vacio)
        vcol.addWidget(self.lbl_vacio)
        vcol.addStretch(2)
        col.addWidget(self.vacio, 1)
        return marco

    # ------------------------------------------------------------ datos
    def refresh(self):
        """Recarga los mensajes desde el backend, sin congelar la ventana."""
        if not self._items:
            self._pintar_vacio("Cargando mensajes…")
        hilos.en_fondo(inbox_list, dueno=self, nombre="bandeja", listo=self._cargar)

    def _cargar(self, items):
        actual_id = self._actual.it.get("id") if self._actual is not None else None
        self._items = list(items or [])
        self._armar_filas()
        # Se vuelve al que estaba abierto; si no, al primero sin leer.
        destino = next((f for f in self._filas if f.it.get("id") == actual_id), None)
        if destino is None:
            destino = next((f for f in self._filas if not f.it.get("leido")), None)
        if destino is None and self._filas:
            destino = self._filas[0]
        if destino is not None:
            self._abrir(destino)
        self._pintar_resumen()

    def _armar_filas(self):
        for f in self._filas:
            f.setParent(None)
            f.deleteLater()
        self._filas = []
        self._actual = None
        for it in self._items:
            if self._solo_nuevos and it.get("leido"):
                continue
            fila = _Fila(it)
            fila.elegida.connect(self._abrir)
            self.col_filas.insertWidget(self.col_filas.count() - 1, fila)
            self._filas.append(fila)
        if not self._filas:
            self._pintar_vacio("Sin mensajes sin leer." if self._solo_nuevos and self._items
                               else "Sin mensajes todavía.")

    def _abrir(self, fila):
        if self._actual is not None and shiboken6.isValid(self._actual):
            self._actual.pintar(False)
        self._actual = fila
        it = fila.it
        self.vacio.hide()
        for w in (self.lbl_asunto, self.lbl_de, self.txt_cuerpo):
            w.show()
        self.lbl_tipo.setVisible(bool(it.get("tipo_label")))
        self.lbl_tipo.setText(it.get("tipo_label") or "")
        self.lbl_asunto.setText(it.get("asunto") or "(sin asunto)")
        de = f"De {it.get('remitente') or 'Sistema'} · {fecha_larga(it.get('created_at'))}"
        if it.get("procedimiento") or it.get("fecha"):
            cuando = fecha_larga(f"{it.get('fecha')} {it.get('hora') or '00:00'}") if it.get("fecha") else ""
            cita = " · ".join(str(x) for x in (it.get("procedimiento"), cuando) if x)
            de += f"\nAtención: {cita}"
        self.lbl_de.setText(de)
        self.caja_aviso.setVisible(bool(it.get("aviso")))
        self.lbl_aviso.setText(it.get("aviso") or "")
        self.txt_cuerpo.setHtml(cuerpo_html(it))
        fila.pintar(True)
        self.scroll.ensureWidgetVisible(fila)
        if not it.get("leido"):
            it["leido"] = 1
            fila.pintar(True)
            hilos.en_fondo(inbox_marcar_leido, int(it["id"]), dueno=self, nombre="bandeja_leido")
            self._pintar_resumen()

    def _filtrar(self, solo_nuevos):
        self._solo_nuevos = solo_nuevos
        actual_id = self._actual.it.get("id") if self._actual is not None else None
        self._armar_filas()
        destino = next((f for f in self._filas if f.it.get("id") == actual_id), None)
        if destino is None and self._filas:
            destino = self._filas[0]
        if destino is not None:
            self._abrir(destino)

    def marcar_todo_leido(self):
        nuevos = [it for it in self._items if not it.get("leido")]
        for it in nuevos:
            it["leido"] = 1
        ids = [int(it["id"]) for it in nuevos]
        for f in self._filas:
            f.pintar(f is self._actual)
        self._pintar_resumen()
        if ids:
            hilos.en_fondo(lambda: [inbox_marcar_leido(i) for i in ids],
                           dueno=self, nombre="bandeja_leido")

    def _no_leidos(self):
        return sum(1 for it in self._items if not it.get("leido"))

    def _pintar_resumen(self):
        n = self._no_leidos()
        total = len(self._items)
        if not total:
            texto = "Avisos sobre tus atenciones y mensajes de tus docentes."
        elif n:
            texto = f"{n} sin leer de {total}"
        else:
            texto = f"{total} mensaje{'s' if total != 1 else ''}, todos leídos"
        self.lbl_resumen.setText(texto)
        self.btn_todo_leido.setEnabled(n > 0)
        self.btn_sin_leer.setText(f"Sin leer ({n})" if n else "Sin leer")
        if self._main_window is not None:
            actualizar_badge(self._main_window, no_leidos=n)

    def _pintar_vacio(self, texto):
        for w in (self.lbl_tipo, self.lbl_asunto, self.lbl_de, self.caja_aviso, self.txt_cuerpo):
            w.hide()
        self.lbl_vacio.setText(texto)
        self.vacio.show()
        self._pintar_resumen()

    def keyPressEvent(self, ev):
        """↑ / ↓ pasan al mensaje anterior / siguiente."""
        paso = {Qt.Key.Key_Up: -1, Qt.Key.Key_Down: 1}.get(ev.key())
        if paso is None or not self._filas:
            super().keyPressEvent(ev)
            return
        i = self._filas.index(self._actual) if self._actual in self._filas else -1
        i = max(0, min(len(self._filas) - 1, i + paso))
        self._abrir(self._filas[i])


def cuerpo_html(it):
    """El texto del mensaje, con sus saltos de línea."""
    texto = html_lib.escape(it.get("cuerpo", "")).replace(chr(10), "<br>")
    return f'<div style="color:{tema.TEXTO}; line-height:140%;">{texto}</div>'


def crear_boton(main_window, layout):
    """Crea el botón y lo agrega a `layout` -- se llama cada vez que
    ui_helpers.chargeBtnsArea reconstruye la sección "Sala de Espera" (cambia
    de sección = destruye y recrea los botones), por eso guarda la
    referencia en main_window para poder refrescar el contador después."""
    btn = QPushButton("Bandeja de entrada")
    btn.setObjectName(BTN_OBJECT_NAME)
    btn.setToolTip("Bandeja de entrada")
    btn.setIcon(iconos.icono_boton("bandeja", tema.TEXTO_SUAVE, tema.ACENTO, 18))
    btn.setMaximumHeight(25)
    btn.clicked.connect(lambda: abrir(main_window))
    layout.addWidget(btn)
    main_window.btn_bandeja_oirs = btn
    btn.setMinimumWidth(btn.sizeHint().width())
    # Lo último que se supo; si nunca se preguntó, se pregunta sin esperar.
    conocido = getattr(main_window, "_inbox_no_leidos", None)
    if conocido is None:
        hilos.en_fondo(inbox_list, dueno=btn, nombre="bandeja",
                       listo=lambda items: actualizar_badge(main_window, items))
    else:
        actualizar_badge(main_window, no_leidos=conocido)
    return btn


def actualizar_badge(main_window, items=None, no_leidos=None):
    """Refresca el contador de no leídos en el botón y lo resalta con color
    si hay algo nuevo -- llamar en cada ciclo de sync y al leer mensajes.
    `no_leidos`: lo que trae el sync (inbox_no_leidos) o la bandeja abierta;
    `items`: la bandeja ya consultada. No consulta la red: quien llama ya
    tiene el dato."""
    if no_leidos is None:
        if items is None:
            return
        no_leidos = sum(1 for it in items if not it.get("leido"))
    main_window._inbox_no_leidos = no_leidos
    btn = getattr(main_window, "btn_bandeja_oirs", None)
    if btn is None or not shiboken6.isValid(btn):
        return
    if no_leidos:
        btn.setText(f"Bandeja de entrada ({no_leidos})")
        btn.setStyleSheet(
            f"QPushButton {{ background-color:{tema.AVISO}; color:white; font-weight:600; "
            "border-radius:4px; padding:2px 8px; }"
            "QPushButton:hover { background-color:#C06F1A; }"
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
