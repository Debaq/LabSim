"""
main_window.py - Ventana Principal con Escritorio Simulado tipo Windows
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Ventana principal que simula un escritorio Windows completo con:
- Área de escritorio con iconos de aplicaciones
- Barra de tareas inferior (sin botón inicio)
- Sistema de ventanas independientes para cada módulo
- Chat de paciente IA flotante
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QGridLayout, QSizePolicy, QMenu
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QFont, QPalette, QColor, QAction


class DesktopIcon(QPushButton):
    """Icono de aplicación en el escritorio."""
    
    def __init__(self, icon_text: str, app_name: str, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        
        # Configuración visual del icono
        self.setFixedSize(80, 80)
        self.setText(f"{icon_text}\n{app_name}")
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
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


class StartButton(QPushButton):
    """Botón de Inicio en la barra de tareas."""
    
    def __init__(self, parent=None):
        super().__init__("Inicio", parent)
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
        # Aplicaciones principales
        apps_menu = self.start_menu.addMenu("📁 Programas")
        
        apps = [
            ("🎧", "Audiometría"),
            ("📊", "Impedancia"), 
            ("🔊", "OAE"),
            ("⚡", "ABR"),
            ("📁", "Casos Clínicos"),
            ("📝", "TextPro"),
            ("⚙️", "Configuración")
        ]
        
        for icon, name in apps:
            action = QAction(f"{icon} {name}", self)
            apps_menu.addAction(action)
        
        self.start_menu.addSeparator()
        
        # Opciones del sistema
        system_action = QAction("👤 Cambiar Usuario", self)
        self.start_menu.addAction(system_action)
        
        logout_action = QAction("🚪 Cerrar Sesión", self)
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.open_apps = []  # Lista de aplicaciones abiertas
    
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
        self.start_button = StartButton()
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


class DesktopArea(QWidget):
    """Área del escritorio con iconos de aplicaciones."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
            ("🔊", "OAE"),
            ("⚡", "ABR"),
            ("📁", "Casos"),
            ("📝", "TextPro"),
            ("⚙️", "Config")
        ]
        
        # Crear iconos de escritorio
        row, col = 0, 0
        for icon_text, app_name in desktop_apps:
            icon = DesktopIcon(icon_text, app_name)
            layout.addWidget(icon, row, col)
            
            # Organizar en columnas de 2
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # Agregar stretch para que los iconos se mantengan arriba-izquierda
        layout.setRowStretch(row + 1, 1)
        layout.setColumnStretch(2, 1)


class MainWindow(QMainWindow):
    """Ventana principal con escritorio simulado tipo Windows."""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.setupWindow()
    
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
        self.desktop_area = DesktopArea()
        main_layout.addWidget(self.desktop_area, 1)  # Factor de stretch 1
        
        # Barra de tareas (altura fija en la parte inferior)
        self.taskbar = Taskbar()
        main_layout.addWidget(self.taskbar, 0)  # Sin stretch, altura fija
    
    def keyPressEvent(self, event):
        """Manejo de teclas especiales."""
        # ESC para salir de pantalla completa (temporal para desarrollo)
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())