# pylint: disable=no-name-in-module
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox, QWidget
from core import hilos

from auth.func_login import LoginConnect
from auth.login_busy_dialog import LoginBusyDialog
from auth import login_worker
from auth.UI.Ui_Login import Ui_Login



class MainLogin(QWidget, Ui_Login):
    """trata a la ventana Gui de login y la conecta a las funciones LoginConnect

    Args:
        QWidget: clase Qwidget
        Ui_Login: clase Ui_Login
    Return:
        data_login(dict): datos del login y el caso
    Signal:
        data_login_signal(dict): datos del login y el caso

    """

    data_login_signal = Signal(dict)

    def __init__(self) -> None:
        QWidget.__init__(self)

        # Inicialización de la ventana y propiedades
        self.setupUi(self)
        self.Le_name.setPlaceholderText("Usuario admin (vacío si vienes de Moodle)")
        self.Le_passw.setPlaceholderText("Contraseña, o código de 6 dígitos de Moodle")
        self.btn_login.clicked.connect(self.get)
        self.login_func = LoginConnect()
        self.setTabOrder(self.Le_name, self.Le_passw)
        self.Le_name.setFocus()

        # Login en curso (hilos.Tarea); None cuando no hay.
        self._login_thread = None
        self._busy = None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.Le_name.setFocus()

    def get(self) -> None:
        """
        envia los datos del login a _verify_login para verificar
        y luego a func_login para logear quien devuelve el data del caso
        o 0 para indicar error de conexion
        """
        name = self.Le_name.text()
        passw = self.Le_passw.text()
        if not self._verify_login(name, passw):
            QMessageBox.critical(self, "Ingreso", "Error de Login")
            return
        # Si ya hay un login en curso (doble click, Enter repetido), ignorar.
        if self._login_thread is not None:
            return
        self._start_login(name, passw)

    def _start_login(self, name: str, passw: str) -> None:
        """Corre el login con hilos.en_fondo para no congelar la UI.

        El HTTP a /api/admin_login.php (o /api/pair_exchange.php) puede
        tardar varios segundos con red lenta; antes esto se ejecutaba
        sincrónico y la ventana quedaba pegada. Con el overlay
        (LoginBusyDialog), el usuario ve feedback de progreso y los inputs
        quedan bloqueados para evitar doble submit.

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

    def _show_busy(self, show: bool) -> None:
        """Muestra/oculta el spinner y deshabilita los inputs."""
        widgets = (self.Le_name, self.Le_passw, self.btn_login)
        if show:
            for w in widgets:
                w.setEnabled(False)
            self._busy = LoginBusyDialog(self)
            self._busy.show()
        else:
            for w in widgets:
                w.setEnabled(True)
            if self._busy is not None:
                self._busy.close_busy()
                self._busy = None

    def closeEvent(self, event) -> None:
        """Un login en curso al cerrar la ventana sigue solo y su resultado
        ya no le llega a nadie (ver hilos.Tarea.descartar)."""
        if self._login_thread is not None:
            self._login_thread.descartar()
            self._login_thread = None
        super().closeEvent(event)

    def _verify_result(self, result:any) -> None:
        """
        Verifica que retorno de func_login, si es 0  levanta un mensaje de error,
        si el login trae datos desactiva el estado de los widgets y cambia la
        función del login, luego envia los datos al main para ser tratados
        Args:
            result (any): retorno de func_login
        """
        if result:
            self._disable_widgets()
            self.data_login_signal.emit(result)
        else:
            QMessageBox.critical(self, "Ingreso",
                                 getattr(result, "mensaje", None) or "No es posible ingresar")

    def _verify_login(self, username:str, password:str) -> bool:
        """
        Verifica si hay usuario y contraseña
        ni no se a agregado devuelve una ventana de advertencia
        Args:
            username (str): nombre de usuario
            password (str): contraseña
        Return:
            bool: True si hay usuario y contraseña
        """
        code = password.strip()
        if not username.strip() and code.isdigit() and len(code) == 6:
            return True  # login de alumno: código de 6 dígitos de Moodle, sin usuario
        return bool(username.strip() and password.strip())

    def _disable_widgets(self) -> None:
        """Desactiva los widget y cambia la función de btn_login a logout"""
        self._change_state_window(False, "Salir", self.logout)

    def _enable_widgets(self) -> None:
        """Activa los widget y cambia la función de btn_login a login"""
        self._change_state_window(True, "Ingresar", self.get)


    def logout(self):
        """función de logout"""
        self._enable_widgets()
        self.data_login_signal.emit({"user":False})



    def _change_state_window(self, state:bool, label:str, func:callable) -> None:
        """
        helper para cambiar el estado de los widgets
        Args:
            state (bool): estado de los widgets
            label (str): texto del boton
            func (callable): función del boton
        """
        self.Le_name.setEnabled(state)
        self.Le_passw.setEnabled(state)
        if state:
            self.Le_name.setText("")
            self.Le_passw.setText("")
            self.Le_name.setFocus()
        self.btn_login.setText(label)
        self.btn_login.clicked.disconnect()
        self.btn_login.clicked.connect(func)
