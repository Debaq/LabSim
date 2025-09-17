"""
desktop_area.py - Área del escritorio con iconos de aplicaciones
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Componente que maneja el área del escritorio con iconos de aplicaciones.
Separado de main_window para mantener responsabilidades claras.
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton
from PySide6.QtCore import Qt


class DesktopIcon(QPushButton):
    """Icono de aplicación en el escritorio."""
    
    def __init__(self, icon_text: str, app_name: str, main_window, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.main_window = main_window
        
        # Configuración visual del icono
        self.setFixedSize(80, 80)
        self.setText(f"{icon_text}\n{app_name}")
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 17px;
                text-align: center;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # NO conectar clicked, usar mouseDoubleClickEvent en su lugar
    
    def mouseDoubleClickEvent(self, event):
        """Lanzar la aplicación con doble clic."""
        if event.button() == Qt.LeftButton:
            self.launch_app()
        super().mouseDoubleClickEvent(event)
    
    def launch_app(self):
        """Lanzar la aplicación correspondiente."""
        self.main_window.open_module(self.app_name)


class DesktopArea(QWidget):
    """Área del escritorio con iconos de aplicaciones."""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setupUI()
    
    def setupUI(self):
        # Layout en grid para organizar los iconos
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Definir aplicaciones del escritorio
        desktop_apps = [
            ("🎧", "Audiometría"),
            ("📊", "Impedancia"),
            ("📊", "OAE"),
            ("⚡", "ABR"),
            ("📋", "Casos"),
            ("📝", "TextPro"),
            ("⚙️", "Config")
        ]
        
        # Crear iconos de escritorio
        row, col = 0, 0
        for icon_text, app_name in desktop_apps:
            icon = DesktopIcon(icon_text, app_name, self.main_window)
            layout.addWidget(icon, row, col)
            
            # Organizar en columnas de 2
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # Agregar stretch para que los iconos se mantengan arriba-izquierda
        layout.setRowStretch(row + 1, 1)
        layout.setColumnStretch(2, 1)