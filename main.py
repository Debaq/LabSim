"""
main.py - Entry point único para LabSim 3.0 con Login
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Punto de entrada único que muestra el escritorio simulado y luego el login encima.
"""

import sys
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.gui.dialogs.login_window import LoginWindow


def main():
    """Función principal de la aplicación."""
    app = QApplication(sys.argv)
    
    # Configurar estilo global de la aplicación
    app.setStyle('Fusion')  # Estilo moderno multiplataforma
    
    # Crear y mostrar ventana principal primero (escritorio simulado)
    main_window = MainWindow()
    main_window.show()
    
    # Crear login encima del escritorio simulado
    login_window = LoginWindow(main_window)
    
    def on_login_success(username):
        """Callback cuando el login es exitoso."""
        # Actualizar usuario en la ventana principal
        main_window.set_current_user(username)
        main_window.setEnabled(True)  # Reactivar interacción
        
        # Cerrar login
        login_window.close()
    
    def show_login_again():
        """Muestra el login nuevamente al cerrar sesión."""
        # Deshabilitar interacción con el escritorio
        main_window.setEnabled(False)
        
        # Crear nuevo login encima
        new_login = LoginWindow(main_window)
        
        def on_new_login_success(username):
            main_window.set_current_user(username)
            main_window.setEnabled(True)
            new_login.close()
        
        new_login.login_successful.connect(on_new_login_success)
        new_login.show()
        new_login.raise_()  # Asegurar que esté al frente
        new_login.activateWindow()
    
    # Conectar señales
    login_window.login_successful.connect(on_login_success)
    main_window.logout_requested.connect(show_login_again)
    
    # Deshabilitar interacción inicial con el escritorio
    main_window.setEnabled(False)
    
    # Mostrar login encima del escritorio
    login_window.show()
    login_window.raise_()  # Forzar al frente
    login_window.activateWindow()  # Activar para recibir input
    
    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()