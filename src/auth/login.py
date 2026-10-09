# pylint: disable=no-name-in-module
from PySide6.QtCore import QRegularExpression, Qt, Signal
from PySide6.QtGui import QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)
from core import hilos

from auth.func_login import LoginConnect
from auth.login_busy_dialog import LoginBusyDialog
from auth import login_worker

# Largo del código de ingreso que entrega la actividad LabSim en la
# plataforma del curso (Moodle u otra con LTI; ver
# labsim_backend/public/lti/launch.php).
LARGO_CODIGO = 6


class MainLogin(QWidget):
    """Ventana de ingreso.

    Lo que abre es el ingreso del alumno: un solo campo para el código de 6
    dígitos que da la plataforma del curso (Moodle u otra, por LTI), que
    se envía apenas está completo (no hay que hacer
    clic en nada). Abajo, un link pasa al ingreso con usuario y contraseña
    (docentes y administración), y desde ahí otro vuelve al código.

    Cabe en el tamaño de la subventana LOGIN que fija el servidor (410x140,
    ver Layout.php): un cambio de alto ahí no llega a los equipos que
    todavía tienen el layout viejo en caché.

    Signal:
        data_login_signal(dict): datos del login, o {"user": False} al salir
    """

    data_login_signal = Signal(dict)

    PAGINA_CODIGO = 0
    PAGINA_USUARIO = 1

    def __init__(self) -> None:
        QWidget.__init__(self)
        self.setObjectName("Login")
        self.setMinimumSize(400, 90)
        self.login_func = LoginConnect()

        self.paginas = QStackedWidget(self)
        self.paginas.addWidget(self._pagina_codigo())
        self.paginas.addWidget(self._pagina_usuario())
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(10, 6, 10, 6)
        raiz.addWidget(self.paginas)

        # Login en curso (hilos.Tarea); None cuando no hay.
        self._login_thread = None
        self._busy = None

    # -----------------------------------------------------------------
    # Páginas
    # -----------------------------------------------------------------

    def _pagina_codigo(self):
        pagina = QWidget()
        col = QVBoxLayout(pagina)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        fila = QHBoxLayout()
        etiqueta = QLabel("Código de ingreso :")
        self.Le_codigo = QLineEdit()
        self.Le_codigo.setObjectName("Le_codigo")
        self.Le_codigo.setPlaceholderText("6 dígitos")
        self.Le_codigo.setMaxLength(LARGO_CODIGO)
        self.Le_codigo.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d{0,6}")))
        self.Le_codigo.setAlignment(Qt.AlignCenter)
        fuente = QFont(self.Le_codigo.font())
        fuente.setPointSizeF(fuente.pointSizeF() * 1.5)
        fuente.setLetterSpacing(QFont.AbsoluteSpacing, 4)
        self.Le_codigo.setFont(fuente)
        self.Le_codigo.textChanged.connect(self._codigo_cambio)
        self.Le_codigo.returnPressed.connect(self.get)
        fila.addWidget(etiqueta)
        fila.addWidget(self.Le_codigo, 1)
        col.addLayout(fila)

        ayuda = QLabel("Lo muestra la actividad LabSim de tu curso.")
        ayuda.setStyleSheet("color: #666;")
        col.addWidget(ayuda)
        col.addWidget(self._link("Ingresar con usuario y contraseña", self.PAGINA_USUARIO))
        return pagina

    def _pagina_usuario(self):
        pagina = QWidget()
        col = QVBoxLayout(pagina)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        fila = QHBoxLayout()
        campos = QVBoxLayout()
        self.Le_name = QLineEdit()
        self.Le_name.setObjectName("Le_name")
        self.Le_name.setPlaceholderText("Usuario")
        self.Le_passw = QLineEdit()
        self.Le_passw.setObjectName("Le_passw")
        self.Le_passw.setPlaceholderText("Contraseña")
        self.Le_passw.setEchoMode(QLineEdit.Password)
        # Enter en cualquiera de los dos campos envía (antes no hacía nada y
        # había que ir al botón con el mouse).
        self.Le_name.returnPressed.connect(self.get)
        self.Le_passw.returnPressed.connect(self.get)
        campos.addWidget(self.Le_name)
        campos.addWidget(self.Le_passw)
        self.btn_login = QPushButton("Ingresar")
        self.btn_login.setObjectName("btn_login")
        self.btn_login.clicked.connect(self.get)
        fila.addLayout(campos, 1)
        fila.addWidget(self.btn_login, 0, Qt.AlignBottom)
        col.addLayout(fila)
        col.addWidget(self._link("Ingresar con código de ingreso", self.PAGINA_CODIGO))
        self.setTabOrder(self.Le_name, self.Le_passw)
        return pagina

    def _link(self, texto, pagina):
        link = QLabel(f'<a href="#">{texto}</a>')
        link.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        link.linkActivated.connect(lambda _href: self.mostrar_pagina(pagina))
        return link

    def mostrar_pagina(self, pagina):
        self.paginas.setCurrentIndex(pagina)
        self._enfocar()

    def _enfocar(self):
        if self.paginas.currentIndex() == self.PAGINA_CODIGO:
            self.Le_codigo.setFocus()
        else:
            self.Le_name.setFocus()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._enfocar()

    # -----------------------------------------------------------------
    # Ingreso
    # -----------------------------------------------------------------

    def _codigo_cambio(self, texto):
        """El código completo se envía solo."""
        if len(texto) == LARGO_CODIGO and texto.isdigit():
            self.get()

    def _credenciales(self):
        """(usuario, contraseña) según la página: el alumno manda el código
        como contraseña y el usuario vacío (ver pair_exchange.php)."""
        if self.paginas.currentIndex() == self.PAGINA_USUARIO or self.Le_name.text().strip():
            return self.Le_name.text(), self.Le_passw.text()
        return "", self.Le_codigo.text()

    def get(self) -> None:
        """Valida lo escrito y arranca el login en segundo plano."""
        # Si ya hay un login en curso (doble Enter, código pegado), ignorar.
        if self._login_thread is not None:
            return
        name, passw = self._credenciales()
        if not self._verify_login(name, passw):
            mensaje = ("Escribe tu usuario y tu contraseña."
                       if self.paginas.currentIndex() == self.PAGINA_USUARIO
                       else f"El código tiene {LARGO_CODIGO} dígitos.")
            QMessageBox.warning(self, "Ingreso", mensaje)
            return
        self._start_login(name, passw)

    def _start_login(self, name: str, passw: str) -> None:
        """Corre el login con hilos.en_fondo para no congelar la UI.

        El HTTP a /api/admin_login.php (o /api/pair_exchange.php) puede
        tardar varios segundos con red lenta; con el overlay
        (LoginBusyDialog) el usuario ve que algo pasa y los campos quedan
        bloqueados para evitar un doble envío.

        Sin QThread ni worker de Qt: con QThread + LoginWorker hubo segfault
        (2026-09-07, deleteLater del worker en su propio hilo) y, con el
        mismo patrón en la agenda, los cierres del 2026-10-09. El resultado
        llega por `listo` ya en el hilo de la ventana, con la consulta
        terminada: el post-login (load_sub_windows) nunca corre en paralelo
        con él.
        """
        self._show_busy(True)
        self._login_thread = hilos.en_fondo(
            login_worker.intentar_login, name, passw, dueno=self,
            listo=self._on_login_finished, nombre="login")

    def _on_login_finished(self, result) -> None:
        """En el hilo de la GUI, con el login ya terminado."""
        self._login_thread = None
        self._show_busy(False)
        self._verify_result(result)

    def _campos(self):
        return (self.Le_codigo, self.Le_name, self.Le_passw, self.btn_login)

    def _show_busy(self, show: bool) -> None:
        """Muestra/oculta el spinner y deshabilita los campos."""
        for w in self._campos():
            w.setEnabled(not show)
        if show:
            self._busy = LoginBusyDialog(self)
            self._busy.show()
        elif self._busy is not None:
            self._busy.close_busy()
            self._busy = None

    def closeEvent(self, event) -> None:
        """Un login en curso al cerrar la ventana sigue solo y su resultado
        ya no le llega a nadie (ver hilos.Tarea.descartar)."""
        if self._login_thread is not None:
            self._login_thread.descartar()
            self._login_thread = None
        super().closeEvent(event)

    def _verify_result(self, result) -> None:
        """Con datos, avisa al main; si no, muestra el error del servidor y
        deja el campo listo para escribir de nuevo."""
        if result:
            self._disable_widgets()
            self.data_login_signal.emit(result)
            return
        QMessageBox.critical(self, "Ingreso",
                             getattr(result, "mensaje", None) or "No es posible ingresar")
        # Un código no sirve dos veces: se borra para escribir el nuevo.
        self.Le_codigo.clear()
        self._enfocar()

    def _verify_login(self, username: str, password: str) -> bool:
        """Hay algo que mandar: el código completo, o usuario y contraseña."""
        code = password.strip()
        if not username.strip() and code.isdigit() and len(code) == LARGO_CODIGO:
            return True  # login de alumno: código de 6 dígitos de Moodle, sin usuario
        return bool(username.strip() and password.strip())

    def _disable_widgets(self) -> None:
        """Con la sesión iniciada, la ventana no acepta otro ingreso."""
        for w in self._campos():
            w.setEnabled(False)

    def _enable_widgets(self) -> None:
        """Vuelve al ingreso limpio, en la página del código."""
        for w in self._campos():
            w.setEnabled(True)
        self.Le_codigo.blockSignals(True)
        self.Le_codigo.clear()
        self.Le_codigo.blockSignals(False)
        self.Le_name.clear()
        self.Le_passw.clear()
        self.mostrar_pagina(self.PAGINA_CODIGO)

    def logout(self):
        """función de logout"""
        self._enable_widgets()
        self.data_login_signal.emit({"user": False})
