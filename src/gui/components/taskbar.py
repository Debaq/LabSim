"""
taskbar.py - Barra de tareas inferior simulando Windows
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Componente de barra de tareas con botón de inicio, aplicaciones abiertas
y bandeja del sistema. Separado para mantener responsabilidades claras.
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
    QWidget, QMenu
)
from PySide6.QtCore import Qt, QTimer, QTime, Signal
from PySide6.QtGui import QAction


class StartButton(QPushButton):
    """Botón de Inicio en la barra de tareas."""
    
    # Señal para logout
    logout_requested = Signal()
    
    def __init__(self, username: str, parent=None):
        super().__init__("Inicio", parent)
        self.username = username
        self.setFixedSize(80, 30)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 60, 114, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(42, 82, 152, 0.9);
            }
            QPushButton:pressed {
                background-color: rgba(25, 50, 95, 1.0);
            }
        """)
        
        # Crear menú de inicio
        self.start_menu = QMenu(self)
        self.setupStartMenu()
        
    def setupStartMenu(self):
        """Configura el menú de inicio."""
        # Información del usuario en la parte superior
        user_action = QAction(f"👤 {self.username}", self)
        user_action.setEnabled(False)  # Solo informativo
        self.start_menu.addAction(user_action)
        
        self.start_menu.addSeparator()
        
        # Aplicaciones principales
        apps_menu = self.start_menu.addMenu("📁 Programas")
        
        apps = [
            ("🎧", "Audiometría"),
            ("📊", "Impedancia"), 
            ("📊", "OAE"),
            ("⚡", "ABR"),
            ("📋", "Casos Clínicos"),
            ("📝", "TextPro"),
            ("⚙️", "Configuración")
        ]
        
        for icon, name in apps:
            action = QAction(f"{icon} {name}", self)
            apps_menu.addAction(action)
        
        self.start_menu.addSeparator()
        
        # Opción de cerrar sesión
        logout_action = QAction("🚪 Cerrar Sesión", self)
        logout_action.triggered.connect(self.logout_requested.emit)
        self.start_menu.addAction(logout_action)
        
        self.start_menu.addSeparator()
        
        shutdown_action = QAction("⚡ Apagar", self)
        self.start_menu.addAction(shutdown_action)
        
        # Aplicar estilo al menú
        self.start_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 40, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                font-size: 12px;
                min-width: 200px;
            }
            QMenu::item {
                padding: 8px 16px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: rgba(70, 130, 200, 0.7);
            }
            QMenu::item:disabled {
                color: #86868b;
                background-color: rgba(255, 255, 255, 0.05);
                font-weight: bold;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.2);
                margin: 2px 0px;
            }
        """)
    
    def mousePressEvent(self, event):
        """Mostrar menú al hacer clic."""
        if event.button() == Qt.LeftButton:
            # Posicionar el menú arriba del botón
            pos = self.mapToGlobal(self.rect().topLeft())
            pos.setY(pos.y() - self.start_menu.sizeHint().height())
            self.start_menu.exec(pos)
        super().mousePressEvent(event)


class TaskbarButton(QPushButton):
    """Botón de aplicación en la barra de tareas."""
    
    def __init__(self, app_name: str, parent=None):
        super().__init__(app_name, parent)
        self.setMinimumWidth(120)
        self.setMaximumWidth(200)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                padding: 5px 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)


class SystemTrayArea(QWidget):
    """Área de bandeja del sistema en la barra de tareas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.setupTimer()
    
    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)
        
        # Indicadores de estado
        self.ai_status = QLabel("🤖 Local")
        self.ai_status.setStyleSheet("color: lightgreen; font-size: 12px;")
        
        self.cost_monitor = QLabel("💰 $0.00")
        self.cost_monitor.setStyleSheet("color: lightblue; font-size: 12px;")
        
        self.hardware_status = QLabel("🔧 OK")
        self.hardware_status.setStyleSheet("color: lightgreen; font-size: 12px;")
        
        # Reloj del sistema
        self.clock = QLabel()
        self.clock.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        
        # Agregar widgets al layout
        layout.addWidget(self.ai_status)
        layout.addWidget(self.cost_monitor)
        layout.addWidget(self.hardware_status)
        layout.addWidget(self.clock)
    
    def setupTimer(self):
        """Configura el timer para actualizar el reloj."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateClock)
        self.timer.start(1000)  # Actualizar cada segundo
        self.updateClock()
    
    def updateClock(self):
        """Actualiza la hora mostrada."""
        current_time = QTime.currentTime()
        self.clock.setText(current_time.toString("hh:mm:ss"))


class Taskbar(QFrame):
    """Barra de tareas inferior simulando Windows."""
    
    # Señal para logout
    logout_requested = Signal()
    
    def __init__(self, main_window, username: str, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.username = username
        self.open_apps = []  # Lista de aplicaciones abiertas
        self.setupUI()
    
    def update_user(self, username: str):
        """Actualiza el usuario en la taskbar."""
        self.username = username
        # Recrear el botón de inicio con el nuevo usuario
        self.start_button.deleteLater()
        self.start_button = StartButton(self.username)
        self.start_button.logout_requested.connect(self.logout_requested.emit)
        
        # Insertar en la primera posición
        layout = self.layout()
        layout.insertWidget(0, self.start_button)
    
    def setupUI(self):
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.8);
                border-top: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Botón de Inicio
        self.start_button = StartButton(self.username)
        self.start_button.logout_requested.connect(self.logout_requested.emit)
        layout.addWidget(self.start_button)
        
        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("color: rgba(255, 255, 255, 0.3);")
        layout.addWidget(separator)
        
        # Área de aplicaciones abiertas
        self.apps_area = QHBoxLayout()
        layout.addLayout(self.apps_area)
        
        # Spacer para empujar la bandeja del sistema a la derecha
        layout.addStretch()
        
        # Bandeja del sistema
        self.system_tray = SystemTrayArea()
        layout.addWidget(self.system_tray)
    
    def addOpenApp(self, app_name: str):
        """Agrega una aplicación a la barra de tareas."""
        if app_name not in self.open_apps:
            self.open_apps.append(app_name)
            button = TaskbarButton(app_name)
            self.apps_area.addWidget(button)
    
    def removeOpenApp(self, app_name: str):
        """Remueve una aplicación de la barra de tareas."""
        if app_name in self.open_apps:
            self.open_apps.remove(app_name)
            # Buscar y remover el botón correspondiente
            for i in range(self.apps_area.count()):
                widget = self.apps_area.itemAt(i).widget()
                if isinstance(widget, TaskbarButton) and widget.text() == app_name:
                    widget.deleteLater()
                    break