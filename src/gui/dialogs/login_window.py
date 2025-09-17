"""
login_window.py - Ventana de Login estilo macOS
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Ventana de login moderna estilo macOS para autenticación de usuarios.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QWidget, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor


class LoginWindow(QDialog):
    """Ventana de login estilo macOS."""
    
    # Señal emitida cuando el login es exitoso
    login_successful = Signal(str)  # Emite el nombre de usuario
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.setupWindow()
        self.setupUI()
        self.setupAnimations()
    
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle("LabSim 3.0 - Iniciar Sesión")
        
        # Pantalla completa sin bordes, siempre encima
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.showFullScreen()  # Pantalla completa como macOS
        
        # Hacer que la ventana sea modal y esté siempre al frente
        self.setModal(True)
        self.raise_()
        self.activateWindow()
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        # Layout principal que ocupa toda la pantalla
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Widget que centra el contenido
        center_widget = QWidget()
        center_widget.setFixedSize(400, 500)
        center_widget.setStyleSheet("background-color: transparent;")
        
        # Centrar el widget en la pantalla
        main_layout.addStretch()
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(center_widget)
        center_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()
        
        # Container principal con bordes redondeados (dentro del widget centrado)
        container_layout = QVBoxLayout(center_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_container = QFrame()
        self.main_container.setStyleSheet("""
            QFrame {
                background-color: rgb(255, 255, 255);
                border-radius: 20px;
                border: 1px solid rgb(200, 200, 200);
            }
        """)
        
        # Quitar efecto de sombra que puede causar problemas de opacidad
        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(50)
        # shadow.setColor(QColor(0, 0, 0, 100))
        # shadow.setOffset(0, 20)
        # self.main_container.setGraphicsEffect(shadow)
        
        container_layout.addWidget(self.main_container)
        
        # Layout del container
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(30)
        
        # Logo/Título
        self.title_label = QLabel("LabSim 3.0")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("SF Pro Display", 32, QFont.Light))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                margin-bottom: 10px;
            }
        """)
        container_layout.addWidget(self.title_label)
        
        # Subtítulo
        self.subtitle_label = QLabel("Simulación Audiológica")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setFont(QFont("SF Pro Display", 14, QFont.Normal))
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
        self.username_input.setText("user")  # Valor por defecto
        self.username_input.setFont(QFont("SF Pro Display", 16))
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(248, 248, 248);
                border: 2px solid rgb(220, 220, 220);
                border-radius: 12px;
                padding: 15px 20px;
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
        self.password_input.setText("pas123")  # Valor por defecto
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("SF Pro Display", 16))
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(248, 248, 248);
                border: 2px solid rgb(220, 220, 220);
                border-radius: 12px;
                padding: 15px 20px;
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
        self.login_button.setFont(QFont("SF Pro Display", 16, QFont.Medium))
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                padding: 15px 30px;
                font-size: 16px;
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
        self.error_label.setFont(QFont("SF Pro Display", 12))
        self.error_label.setStyleSheet("""
            QLabel {
                color: #FF3B30;
                margin-top: 10px;
            }
        """)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)
        
        # Conectar Enter para login
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
        
        # Focus inicial en usuario
        self.username_input.setFocus()
    
    def setupAnimations(self):
        """Configuración de animaciones - simplificado sin opacidad."""
        # Quitar animaciones de opacidad que causan problemas
        pass
    
    def attempt_login(self):
        """Intenta realizar el login."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Validación simple (expandible en el futuro)
        if username == "user" and password == "pas123":
            self.current_user = username
            self.show_success()
        else:
            self.show_error("Usuario o contraseña incorrectos")
    
    def show_error(self, message: str):
        """Muestra un mensaje de error."""
        self.error_label.setText(message)
        self.error_label.show()
        
        # Animación de vibración en los campos
        self.shake_animation()
    
    def show_success(self):
        """Muestra éxito y emite señal."""
        self.error_label.hide()
        
        # Directamente emitir éxito sin animación de opacidad
        self.emit_success()
    
    def emit_success(self):
        """Emite la señal de login exitoso."""
        self.login_successful.emit(self.current_user)
        self.accept()
    
    def shake_animation(self):
        """Animación de vibración para errores."""
        # Animación simple de movimiento horizontal
        original_pos = self.pos()
        
        self.shake_animation_obj = QPropertyAnimation(self, b"pos")
        self.shake_animation_obj.setDuration(100)
        self.shake_animation_obj.setStartValue(original_pos)
        self.shake_animation_obj.setEndValue(original_pos.translated(10, 0))
        self.shake_animation_obj.finished.connect(
            lambda: self.move(original_pos)
        )
        self.shake_animation_obj.start()
    
    def paintEvent(self, event):
        """Pinta el fondo sólido sin transparencia."""
        painter = QPainter(self)
        
        # Fondo sólido oscuro simple
        background_color = QColor(45, 45, 45)  # Gris oscuro sólido
        painter.fillRect(self.rect(), background_color)
        
        painter.end()
        
        super().paintEvent(event)