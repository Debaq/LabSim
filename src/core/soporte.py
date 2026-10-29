"""Reportar un problema: manda el registro de la app al servidor como ticket.

Pestaña de Configuración. Antes de mandar nada se muestra exactamente qué
sale del equipo (versión, nombre del equipo, sistema, el registro) y el
usuario tiene que aceptarlo; el servidor también exige esa aceptación (ver
labsim_backend/public/api/ticket.php). Al usuario no se le contesta: el
ticket es para que el equipo de LabSim abra un issue.
"""
import gzip

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout,
                               QLabel, QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from core import equipo, hilos, registro
from core.base import context
from core.helpers import Preferences
from core.ui_helpers import style_dialog

# Rótulos de detalle_sistema() para mostrar.
_ROTULOS = {"so_version": "Sistema operativo", "distribucion": "Distribución",
            "arquitectura": "Arquitectura", "python": "Python", "qt": "Qt",
            "pantalla": "Pantalla", "kiosko": "Equipo del laboratorio", "glibc": "glibc"}


def _enviar(descripcion, equipo_info, detalle, cierre_inesperado=False):
    """Manda el ticket con la cola del registro. Devuelve (ok, número de
    ticket o motivo). Corre con hilos.en_fondo: nada de widgets acá."""
    from backend.client import BackendClient
    try:
        log_gz = gzip.compress(registro.cola())
        client = BackendClient(Preferences().get("BACKEND_URL"),
                               context.get_resource("json/session.json"))
        if cierre_inesperado:
            respuesta = _enviar_cierre(client, (descripcion, equipo_info, detalle, log_gz or None))
        else:
            if not client.is_logged_in():
                raise RuntimeError("no hay sesión iniciada con el servidor")
            respuesta = client.send_ticket(descripcion, equipo_info, detalle, log_gz or None)
    except Exception as exc:  # noqa: BLE001 -- se le muestra al usuario
        print(f"soporte: no se pudo enviar el reporte: {exc}")
        return False, str(exc)
    print(f"soporte: reporte enviado, ticket #{respuesta.get('id')}")
    return True, str(respuesta.get("id", ""))


def _enviar_cierre(client, args):
    """Con la sesión que quedó de antes de la caída, si sigue valiendo
    (el ticket queda a nombre de ese usuario); si no, sin sesión."""
    import requests
    if client.is_logged_in():
        try:
            return client.send_ticket(*args, cierre_inesperado=True)
        except requests.HTTPError as exc:
            if getattr(exc.response, "status_code", None) != 401:
                raise
    return client.send_ticket(*args, cierre_inesperado=True, anonimo=True)


def _ruta_partible(ruta):
    """La ruta con puntos de corte invisibles después de cada carpeta: sin
    espacios no se parte y obliga a la ventana a su ancho."""
    return str(ruta).replace("/", "/\u200b").replace("\\", "\\\u200b")


def cabecera_dialogo(parent, icono, titulo, texto):
    """Encabezado de los diálogos (cierre inesperado, registro): el ícono, el
    título y una línea de explicación, en una tarjeta (tema.QSS_FORM)."""
    from core import iconos, tema
    marco = QFrame(parent)
    marco.setObjectName("cabeceraDialogo")
    fila = QHBoxLayout(marco)
    fila.setContentsMargins(14, 10, 14, 10)
    fila.setSpacing(12)
    marca = QLabel(marco)
    marca.setPixmap(iconos.pixmap(icono, tema.ACENTO, 30))
    textos = QVBoxLayout()
    textos.setSpacing(2)
    rotulo = QLabel(titulo, marco)
    rotulo.setProperty("role", "titulo")
    rotulo.setWordWrap(True)
    explicacion = QLabel(texto, marco)
    explicacion.setProperty("role", "hint")
    explicacion.setWordWrap(True)
    textos.addWidget(rotulo)
    textos.addWidget(explicacion)
    fila.addWidget(marca, 0, Qt.AlignmentFlag.AlignTop)
    fila.addLayout(textos, 1)
    return marco


def ofrecer_envio_por_cierre(parent, hora_arranque):
    """La vez anterior LabSim se cerró sin terminar bien (ver
    registro.marcar_inicio): se ofrece mandar el registro, mostrando qué
    sale del equipo. Mandarlo es tocar "Enviar"; no se insiste."""
    from agenda.vista import BotonAccion
    info_equipo = equipo.identidad()
    detalle = registro.detalle_sistema()
    dlg = QDialog(parent)
    dlg.setWindowTitle("LabSim se cerró de forma inesperada")
    dlg.resize(600, 560)
    caja = QVBoxLayout(dlg)
    caja.setContentsMargins(14, 14, 14, 12)
    caja.setSpacing(10)
    cuando = f" (abierto a las {hora_arranque[11:16]})" if len(hora_arranque) >= 16 else ""
    caja.addWidget(cabecera_dialogo(
        dlg, "alerta", "LabSim se cerró de forma inesperada",
        f"La última vez que se usó en este equipo{cuando} no terminó bien. ¿Enviar el registro al "
        "equipo de LabSim? Sirve para encontrar la causa. No se envía nada de lo que hiciste en los "
        "exámenes."))
    descripcion = QPlainTextEdit(dlg)
    descripcion.setPlaceholderText("¿Qué estabas haciendo? (opcional)")
    descripcion.setMaximumHeight(70)
    caja.addWidget(descripcion)
    # Lo que se envía es largo: con scroll, para que quepa en 768 px de alto
    scroll = QScrollArea(dlg)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(_caja_que_se_envia(None, info_equipo, detalle, dlg))
    caja.addWidget(scroll, 1)
    pie = QHBoxLayout()
    pie.addStretch(1)
    btn_no = BotonAccion("No enviar", "x", parent=dlg)
    btn_no.clicked.connect(dlg.reject)
    btn_enviar = BotonAccion("Enviar registro", "enviar", principal=True, parent=dlg)
    btn_enviar.clicked.connect(dlg.accept)
    btn_enviar.setDefault(True)
    pie.addWidget(btn_no)
    pie.addWidget(btn_enviar)
    caja.addLayout(pie)
    style_dialog(dlg)
    respuesta = dlg.exec()
    registro.cierre_atendido()
    if respuesta != QDialog.DialogCode.Accepted:
        print("soporte: no se envió el registro del cierre inesperado")
        return None
    # No hay ventana que espere la respuesta: el resultado queda en el registro.
    return hilos.en_fondo(_enviar, descripcion.toPlainText().strip(), info_equipo, detalle,
                          cierre_inesperado=True, nombre="soporte")


def _caja_que_se_envia(parent, info_equipo, detalle, ventana=None):
    """`ventana`: de quién cuelga el visor del registro, si `parent` todavía
    no tiene dueño (la caja va a un scroll)."""
    box = QGroupBox("Qué se envía", parent)
    form = QFormLayout(box)
    e = info_equipo or {}
    form.addRow("Versión de LabSim:", QLabel(e.get("version") or equipo.version or "?", box))
    form.addRow("Nombre del equipo:", QLabel(e.get("nombre", "?"), box))
    for clave, valor in detalle.items():
        if isinstance(valor, bool):
            valor = "sí" if valor else "no"
        etiqueta = QLabel(str(valor), box)
        etiqueta.setWordWrap(True)
        form.addRow(f"{_ROTULOS.get(clave, clave)}:", etiqueta)
    kb = len(registro.cola()) // 1024
    btn_ver = QPushButton(f"Ver el registro ({kb} KB)", box)
    btn_ver.clicked.connect(lambda: _ver_registro(ventana or parent))
    form.addRow("Registro de la app:", btn_ver)
    donde = QLabel(f"Se guarda en: {_ruta_partible(registro.archivo())}", box)
    donde.setWordWrap(True)
    form.addRow("", donde)
    return box


def _ver_registro(parent):
    from agenda.vista import BotonAccion
    dlg = QDialog(parent)
    dlg.setWindowTitle("Registro de LabSim")
    dlg.resize(760, 540)
    caja = QVBoxLayout(dlg)
    caja.setContentsMargins(14, 14, 14, 12)
    caja.setSpacing(10)
    caja.addWidget(cabecera_dialogo(
        dlg, "lista", "Registro de LabSim",
        f"Lo último que anotó la app en este equipo. Se guarda en {_ruta_partible(registro.archivo())}."))
    texto = QPlainTextEdit(dlg)
    texto.setReadOnly(True)
    texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    texto.setStyleSheet('QPlainTextEdit { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; }')
    texto.setPlainText(registro.cola().decode("utf-8", errors="replace")
                       or "(el registro está vacío)")
    texto.moveCursor(texto.textCursor().MoveOperation.End)
    caja.addWidget(texto, 1)
    pie = QHBoxLayout()
    pie.addStretch(1)
    cerrar = BotonAccion("Cerrar", "x", parent=dlg)
    cerrar.clicked.connect(dlg.reject)
    pie.addWidget(cerrar)
    caja.addLayout(pie)
    style_dialog(dlg)
    dlg.exec()


class PaginaSoporte(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._equipo = equipo.identidad()
        self._detalle = registro.detalle_sistema()
        self._envio = None

        caja = QVBoxLayout(self)
        intro = QLabel(
            "Si LabSim se cerró solo, se colgó o algo no funcionó, cuéntanos qué pasó y envía "
            "el registro de este equipo. Se crea un ticket para el equipo de LabSim. No vas a "
            "recibir respuesta, pero nos sirve para encontrar y corregir el problema.", self)
        intro.setWordWrap(True)
        caja.addWidget(intro)

        caja.addWidget(QLabel("¿Qué estabas haciendo y qué pasó? (opcional)", self))
        self.txt_descripcion = QPlainTextEdit(self)
        self.txt_descripcion.setPlaceholderText(
            "Ej.: estaba en el ABR, se cortó internet y la ventana se cerró.")
        self.txt_descripcion.setMaximumHeight(90)
        caja.addWidget(self.txt_descripcion)

        caja.addWidget(self._caja_que_se_envia())

        # La casilla sin texto y el texto aparte: un QCheckBox no parte su
        # texto en líneas y obligaba a la ventana a medir 670 px de ancho.
        # Un clic en el texto también la marca.
        fila_acepto = QHBoxLayout()
        self.chk_acepto = QCheckBox(self)
        self.chk_acepto.toggled.connect(self._actualizar_boton)
        texto_acepto = QLabel(
            "Acepto enviar al servidor de LabSim la información de este equipo que aparece "
            "arriba y el registro de la aplicación.", self)
        texto_acepto.setWordWrap(True)
        texto_acepto.mousePressEvent = lambda _e: self.chk_acepto.toggle()
        fila_acepto.addWidget(self.chk_acepto, 0, Qt.AlignmentFlag.AlignTop)
        fila_acepto.addWidget(texto_acepto, 1)
        caja.addLayout(fila_acepto)

        self.btn_enviar = QPushButton("Enviar reporte", self)
        self.btn_enviar.clicked.connect(self._enviar)
        caja.addWidget(self.btn_enviar)

        self.lbl_estado = QLabel(self)
        self.lbl_estado.setWordWrap(True)
        caja.addWidget(self.lbl_estado)
        caja.addStretch(1)
        self._actualizar_boton()

    def _caja_que_se_envia(self):
        return _caja_que_se_envia(self, self._equipo, self._detalle)

    def _ver_registro(self):
        _ver_registro(self)

    def _actualizar_boton(self, *_):
        enviando = self._envio is not None
        self.btn_enviar.setEnabled(self.chk_acepto.isChecked() and not enviando)

    def _enviar(self):
        if not self.chk_acepto.isChecked() or self._envio is not None:
            return
        self.lbl_estado.setStyleSheet("color:#666666;")
        self.lbl_estado.setText("Enviando…")
        # Si se cierra Configuración mientras sube, sigue solo y el
        # resultado ya no le llega a nadie (dueno).
        self._envio = hilos.en_fondo(_enviar, self.txt_descripcion.toPlainText().strip(),
                                     self._equipo, self._detalle, dueno=self,
                                     listo=lambda r: self._enviado(*r), nombre="soporte")
        self._actualizar_boton()

    def _enviado(self, ok, detalle):
        self._envio = None
        if ok:
            self.lbl_estado.setStyleSheet("color:#27ae60;")
            self.lbl_estado.setText(f"Reporte enviado. Ticket #{detalle}. ¡Gracias!")
            self.txt_descripcion.clear()
            self.chk_acepto.setChecked(False)
        else:
            self.lbl_estado.setStyleSheet("color:#c0392b;")
            self.lbl_estado.setText(
                "No se pudo enviar el reporte. Revisa la conexión e inténtalo de nuevo; "
                f"el registro sigue guardado en este equipo.\n({detalle[:160]})")
        self._actualizar_boton()
