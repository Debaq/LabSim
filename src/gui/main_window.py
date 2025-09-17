"""
main_window.py - Ventana Principal con Escritorio Simulado tipo Windows
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Ventana principal que coordina el escritorio simulado y gestiona módulos.
Refactorizada para seguir la estructura modular propuesta.
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

from .components.desktop_area import DesktopArea
from .components.taskbar import Taskbar
from .registry.module_registry import ModuleRegistry


class MainWindow(QMainWindow):
    """Ventana principal con escritorio simulado tipo Windows."""
    
    # Señal para solicitar logout
    logout_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_user = None  # Se establecerá después del login
        self.module_registry = ModuleRegistry(self)
        self.open_windows = {}  # Diccionario para gestionar ventanas abiertas
        self.setupWindow()
        self.setupUI()
    
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle("LabSim 3.0 - Simulación Audiológica")
        self.showFullScreen()  # Ventana en pantalla completa
        
        # Aplicar tema oscuro de escritorio
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1e3c72, stop: 1 #2a5298);
            }
        """)
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        # Widget central que contiene todo el escritorio
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Área del escritorio (ocupa la mayor parte del espacio)
        self.desktop_area = DesktopArea(self)
        main_layout.addWidget(self.desktop_area, 1)  # Factor de stretch 1
        
        # Barra de tareas (altura fija en la parte inferior)
        # Inicialmente sin usuario, se actualizará después del login
        self.taskbar = Taskbar(self, "")
        main_layout.addWidget(self.taskbar, 0)  # Sin stretch, altura fija
        
        # Conectar señal de logout de la taskbar
        self.taskbar.logout_requested.connect(self.logout_requested.emit)
    
    def set_current_user(self, username: str):
        """Establece el usuario actual después del login."""
        self.current_user = username
        
        # Actualizar la taskbar con el nuevo usuario
        self.taskbar.update_user(username)
    
    def open_module(self, module_name: str):
        """Abre un módulo específico usando el registry."""
        # Solo permitir abrir módulos si hay usuario logueado
        if not self.current_user:
            return
            
        # Verificar si ya hay una instancia abierta
        if module_name in self.open_windows and self.open_windows[module_name].isVisible():
            # Si ya está abierta, traerla al frente
            self.open_windows[module_name].raise_()
            self.open_windows[module_name].activateWindow()
        else:
            # Crear nueva ventana usando el registry
            window = self.module_registry.create_module(module_name)
            if window:
                window.show()
                
                # Registrar la ventana
                self.open_windows[module_name] = window
                
                # Agregar a la barra de tareas
                self.taskbar.addOpenApp(module_name)
                
                # Conectar señal de cierre correctamente
                window.finished.connect(lambda: self.on_window_closed(module_name))
    
    def on_window_closed(self, module_name: str):
        """Se ejecuta cuando se cierra una ventana."""
        if module_name in self.open_windows:
            del self.open_windows[module_name]
        self.taskbar.removeOpenApp(module_name)
    
    def keyPressEvent(self, event):
        """Manejo de teclas especiales."""
        # ESC para salir de pantalla completa (temporal para desarrollo)
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)