"""
login_widget.py - Widget de Login estilo macOS integrado en MDI
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Widget de login moderno estilo macOS que se integra directamente en el MDI.
No es una ventana modal, sino un widget que ocupa todo el espacio central.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush


class UserIconWidget(QWidget):
    """Widget que dibuja un icono de usuario grande."""
    
    def __init__(self, size=120, parent=None):
        super().__init__(parent)
        self.icon_size = size
        self.setFixedSize(size, size)
    
    def paintEvent(self, event):
        """Dibuja el icono de usuario."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            # Círculo de fondo
            center = self.rect().center()
            radius = self.icon_size // 2 - 10
            
            # Gradiente circular
            painter.setBrush(QBrush(QColor(70, 130, 200)))
            painter.setPen(QPen(QColor(255, 255, 255, 30), 2))
            painter.drawEllipse(center, radius, radius)
            
            # Dibujar icono de persona simplificado
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            
            # Cabeza (círculo pequeño arriba)
            head_radius = radius // 3
            head_center = center + QPoint(0, -radius // 4)  # Usar + en lugar de translated
            painter.drawEllipse(head_center, head_radius, head_radius)
            
            # Cuerpo (semicírculo abajo)
            body_width = radius // 1.5
            body_height = radius // 2
            body_rect = QRect(
                center.x() - body_width // 2,
                center.y(),
                body_width,
                body_height
            )
            painter.drawEllipse(body_rect)
            
        finally:
            painter.end()  # Asegurar que el painter se cierre


class LoginWidget(QWidget):
    """Widget de login estilo macOS integrado en MDI."""
    
    # Señal emitida cuando el login es exitoso
    login_successful = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        # Layout principal que ocupa toda la pantalla
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Widget contenedor centrado
        container = QFrame()
        container.setFixedSize(450, 600)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 0.8);
            }
        """)
        
        # Centrar el contenedor
        main_layout.addStretch()
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(container)
        center_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()
        
        # Layout del contenedor
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(50, 50, 50, 50)
        container_layout.setSpacing(25)
        
        # Icono de usuario grande
        self.user_icon = UserIconWidget(120)
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(self.user_icon)
        icon_layout.addStretch()
        container_layout.addLayout(icon_layout)
        
        # Título principal
        self.title_label = QLabel("LabSim 3.0")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("SF Pro Display", 36, QFont.Light))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                margin: 10px 0;
            }
        """)
        container_layout.addWidget(self.title_label)
        
        # Subtítulo
        self.subtitle_label = QLabel("Simulación Audiológica de Nueva Generación")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setFont(QFont("SF Pro Display", 15, QFont.Normal))
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #86868b;
                margin-bottom: 20px;
            }
        """)
        container_layout.addWidget(self.subtitle_label)
        
        # Espaciador
        container_layout.addStretch(1)
        
        # Campo de usuario
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        self.username_input.setText("user")
        self.username_input.setFont(QFont("SF Pro Display", 16))
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(248, 248, 248);
                border: 2px solid rgb(220, 220, 220);
                border-radius: 15px;
                padding: 18px 25px;
                font-size: 16px;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
                background-color: rgb(255, 255, 255);
            }
            QLineEdit::placeholder {
                color: #86868b;
            }
        """)
        container_layout.addWidget(self.username_input)
        
        # Campo de contraseña
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setText("pas123")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("SF Pro Display", 16))
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(248, 248, 248);
                border: 2px solid rgb(220, 220, 220);
                border-radius: 15px;
                padding: 18px 25px;
                font-size: 16px;
                color: #1d1d1f;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
                background-color: rgb(255, 255, 255);
            }
            QLineEdit::placeholder {
                color: #86868b;
            }
        """)
        container_layout.addWidget(self.password_input)
        
        # Espaciador
        container_layout.addStretch(1)
        
        # Botón de login
        self.login_button = QPushButton("Iniciar Sesión")
        self.login_button.setFont(QFont("SF Pro Display", 18, QFont.Medium))
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: 600;
                padding: 18px 40px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        self.login_button.clicked.connect(self.attempt_login)
        container_layout.addWidget(self.login_button)
        
        # Mensaje de error (inicialmente oculto)
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setFont(QFont("SF Pro Display", 14))
        self.error_label.setStyleSheet("""
            QLabel {
                color: #FF3B30;
                margin-top: 15px;
                background-color: rgba(255, 59, 48, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)
        
        # Conectar Enter para login
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
        
        # Focus inicial
        self.username_input.setFocus()
    
    def paintEvent(self, event):
        """Pinta el fondo con gradiente."""
        painter = QPainter(self)
        
        try:
            # Gradiente de fondo estilo macOS
            rect = self.rect()
            
            # Fondo principal
            painter.fillRect(rect, QColor(240, 242, 247))
            
            # Gradiente sutil
            gradient_height = rect.height() // 3
            for i in range(gradient_height):
                alpha = int(20 * (1 - i / gradient_height))
                color = QColor(180, 190, 210, alpha)
                painter.fillRect(0, i, rect.width(), 1, color)
                
        finally:
            painter.end()
            
        super().paintEvent(event)
    
    def attempt_login(self):
        """Intenta realizar el login."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Validación simple
        if username == "user" and password == "pas123":
            self.login_successful.emit(username)
        else:
            self.show_error("Usuario o contraseña incorrectos")
    
    def show_error(self, message: str):
        """Muestra un mensaje de error."""
        self.error_label.setText(message)
        self.error_label.show()
        
        # Animación de shake
        self.shake_animation()
    
    def shake_animation(self):
        """Animación de vibración para errores."""
        self.animation = QPropertyAnimation(self.username_input, b"geometry")
        self.animation.setDuration(100)
        
        start_geo = self.username_input.geometry()
        end_geo = QRect(start_geo.x() + 10, start_geo.y(), start_geo.width(), start_geo.height())
        
        self.animation.setStartValue(start_geo)
        self.animation.setEndValue(end_geo)
        self.animation.finished.connect(lambda: self.username_input.setGeometry(start_geo))
        self.animation.start()