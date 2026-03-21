"""
main_window.py - Ventana Principal con Login Integrado en MDI
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Ventana principal que alterna entre widget de login y escritorio simulado.
El login está integrado en el MDI, no como ventana modal separada.
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

from .components.desktop_area import DesktopArea
from .components.taskbar import Taskbar
from .components.login_widget import LoginWidget
from .registry.module_registry import ModuleRegistry


class MainWindow(QMainWindow):
    """Ventana principal con login integrado y escritorio simulado."""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.module_registry = None
        self.open_windows = {}
        self.desktop_widget = None
        self.setupWindow()
        self.setupUI()
        
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle("LabSim 3.0 - Simulación Audiológica")
        self.showFullScreen()
        
        # Fondo base
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
        """)
    
    def setupUI(self):
        """Configuración inicial - solo muestra login."""
        # Widget central con stack para alternar login/escritorio
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Mostrar login inicialmente
        self.show_login()
    
    def show_login(self):
        """Muestra el widget de login."""
        # Limpiar stack
        while self.stacked_widget.count() > 0:
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Crear y mostrar login widget
        self.login_widget = LoginWidget()
        self.login_widget.login_successful.connect(self.on_login_success)
        self.stacked_widget.addWidget(self.login_widget)
        
        # Limpiar variables del escritorio
        self.current_user = None
        self.module_registry = None
        self.open_windows = {}
        self.desktop_widget = None
    
    def on_login_success(self, username: str):
        """Callback cuando el login es exitoso."""
        self.current_user = username
        self.show_desktop()
    
    def show_desktop(self):
        """Construye y muestra el escritorio."""
        # Limpiar stack
        while self.stacked_widget.count() > 0:
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Crear widget del escritorio
        self.desktop_widget = QWidget()
        
        # Layout principal del escritorio
        desktop_layout = QVBoxLayout(self.desktop_widget)
        desktop_layout.setContentsMargins(0, 0, 0, 0)
        desktop_layout.setSpacing(0)
        
        # Aplicar tema del escritorio
        self.desktop_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1e3c72, stop: 1 #2a5298);
            }
        """)
        
        # Inicializar registry y componentes
        self.module_registry = ModuleRegistry(self)
        
        # Área del escritorio
        self.desktop_area = DesktopArea(self)
        desktop_layout.addWidget(self.desktop_area, 1)
        
        # Barra de tareas
        self.taskbar = Taskbar(self, self.current_user)
        self.taskbar.logout_requested.connect(self.logout)
        desktop_layout.addWidget(self.taskbar, 0)
        
        # Agregar al stack y mostrar
        self.stacked_widget.addWidget(self.desktop_widget)
    
    def logout(self):
        """Cierra sesión y vuelve al login."""
        # Cerrar todas las ventanas abiertas
        for window in list(self.open_windows.values()):
            if window and window.isVisible():
                window.close()
        
        # Volver al login
        self.show_login()
    
    def open_module(self, module_name: str):
        """Abre un módulo específico usando el registry."""
        if not self.current_user or not self.module_registry:
            return
            
        # Verificar si ya hay una instancia abierta
        if module_name in self.open_windows and self.open_windows[module_name].isVisible():
            self.open_windows[module_name].raise_()
            self.open_windows[module_name].activateWindow()
        else:
            # Crear nueva ventana
            window = self.module_registry.create_module(module_name)
            if window:
                window.show()
                self.open_windows[module_name] = window
                self.taskbar.addOpenApp(module_name)
                window.finished.connect(lambda: self.on_window_closed(module_name))
    
    def on_window_closed(self, module_name: str):
        """Se ejecuta cuando se cierra una ventana."""
        if module_name in self.open_windows:
            del self.open_windows[module_name]
        if self.taskbar:
            self.taskbar.removeOpenApp(module_name)
    
    def keyPressEvent(self, event):
        """Manejo de teclas especiales."""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)