# pylint: disable=no-name-in-module
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from lib.main.func_login import LoginConnect
from UI.Ui_Login import Ui_Login



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

    def __init__(self, online) -> None:
        QWidget.__init__(self)
        self._flag_online = online
        # Inicialización de la ventana y propiedades
        self.setupUi(self)
        self.btn_login.clicked.connect(self.get)
        self.login_func = LoginConnect()

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
        else:
            result = self.login_func.login(name, passw, True) if self._flag_online else self.login_func.login(name, passw, False)
            print(result)
            self._verify_result(result)

    def _verify_result(self, result:any) -> None:
        """
        Verifica que retorno de func_login, si es 0  levanta un mensaje de error,
        si el login trae datos desativa el estado de los widgets y cambia la
        función del login, luego envia los datos al main para ser tratados
        Args:
            result (any): retorno de func_login
        """
        if result:
            self._disable_widgets()
            self.data_login_signal.emit(result)
        else:
            QMessageBox.critical(self, "Ingreso", "No es posible ingresar")

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
        #return True if username.strip() and password.strip() else False
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
        self.btn_login.setText(label)
        self.btn_login.clicked.disconnect()
        self.btn_login.clicked.connect(func)
