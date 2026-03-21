"""
impedance_window.py - Ventana de Impedanciometría
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Ventana completa de impedanciometría que incluye timpanograma y reflejos acústicos.
Interfaz visual completa sin funcionalidad de procesamiento por ahora.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGridLayout, QGroupBox, QComboBox, QSpinBox,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPen, QBrush, QColor, QPainter


class TympanogramWidget(QGraphicsView):
    """Widget para mostrar el timpanograma."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setupScene()
        self.setupGrid()
    
    def setupScene(self):
        """Configura la escena del gráfico."""
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configurar vista sin RenderHint problemático
        self.setRenderHints(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
    
    def setupGrid(self):
        """Dibuja la grilla del timpanograma."""
        # Limpiar escena
        self.scene.clear()
        
        # Dimensiones del gráfico
        width, height = 380, 280
        margin = 20
        
        # Establecer límites de la escena
        self.scene.setSceneRect(0, 0, width, height)
        
        # Dibujar ejes principales
        pen_axis = QPen(QColor(0, 0, 0), 2)
        
        # Eje X (presión: -400 a +200 daPa)
        self.scene.addLine(margin, height - margin, width - margin, height - margin, pen_axis)
        
        # Eje Y (compliance: 0 a 2.5 ml)
        self.scene.addLine(margin, margin, margin, height - margin, pen_axis)
        
        # Grilla secundaria
        pen_grid = QPen(QColor(200, 200, 200), 1)
        
        # Líneas verticales (presión)
        for i in range(1, 7):  # -400 a +200, cada 100 daPa
            x = margin + (i * (width - 2 * margin) / 6)
            self.scene.addLine(x, margin, x, height - margin, pen_grid)
        
        # Líneas horizontales (compliance)
        for i in range(1, 6):  # 0 a 2.5, cada 0.5 ml
            y = margin + (i * (height - 2 * margin) / 5)
            self.scene.addLine(margin, y, width - margin, y, pen_grid)
        
        # Etiquetas de los ejes
        font = QFont("Arial", 8)
        
        # Etiquetas eje X (presión)
        pressures = ["-400", "-300", "-200", "-100", "0", "+100", "+200"]
        for i, pressure in enumerate(pressures):
            x = margin + (i * (width - 2 * margin) / 6)
            text = self.scene.addText(pressure, font)
            text.setPos(x - 15, height - margin + 5)
        
        # Etiquetas eje Y (compliance)
        compliances = ["2.5", "2.0", "1.5", "1.0", "0.5", "0.0"]
        for i, compliance in enumerate(compliances):
            y = margin + (i * (height - 2 * margin) / 5)
            text = self.scene.addText(compliance, font)
            text.setPos(5, y - 10)
        
        # Títulos de los ejes
        title_font = QFont("Arial", 10, QFont.Bold)
        
        # Título eje X
        x_title = self.scene.addText("Presión (daPa)", title_font)
        x_title.setPos(width/2 - 40, height - 5)
        
        # Título eje Y
        y_title = self.scene.addText("Compliance (ml)", title_font)
        y_title.setPos(-5, 5)
        y_title.setRotation(-90)


class ReflexThresholdWidget(QFrame):
    """Widget para mostrar umbrales de reflejos."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(200, 250)
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Umbrales de Reflejos")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grid para frecuencias
        grid_layout = QGridLayout()
        
        # Headers
        grid_layout.addWidget(QLabel("Frecuencia"), 0, 0)
        grid_layout.addWidget(QLabel("IPSI"), 0, 1)
        grid_layout.addWidget(QLabel("CONTRA"), 0, 2)
        
        # Frecuencias y campos de resultado
        frequencies = ["500 Hz", "1000 Hz", "2000 Hz", "4000 Hz", "NBN"]
        
        for i, freq in enumerate(frequencies, 1):
            # Frecuencia
            freq_label = QLabel(freq)
            grid_layout.addWidget(freq_label, i, 0)
            
            # Campo IPSI
            ipsi_label = QLabel("---")
            ipsi_label.setFrameStyle(QFrame.Box)
            ipsi_label.setAlignment(Qt.AlignCenter)
            ipsi_label.setMinimumHeight(25)
            grid_layout.addWidget(ipsi_label, i, 1)
            
            # Campo CONTRA
            contra_label = QLabel("---")
            contra_label.setFrameStyle(QFrame.Box)
            contra_label.setAlignment(Qt.AlignCenter)
            contra_label.setMinimumHeight(25)
            grid_layout.addWidget(contra_label, i, 2)
        
        layout.addLayout(grid_layout)
        layout.addStretch()


class TympanometryResultsWidget(QFrame):
    """Widget para mostrar resultados de timpanometría."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(200, 150)
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Resultados")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grid para resultados
        grid_layout = QGridLayout()
        
        # Compliance
        grid_layout.addWidget(QLabel("Compliance:"), 0, 0)
        self.compliance_label = QLabel("--- ml")
        self.compliance_label.setFrameStyle(QFrame.Box)
        self.compliance_label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(self.compliance_label, 0, 1)
        
        # Presión
        grid_layout.addWidget(QLabel("Presión:"), 1, 0)
        self.pressure_label = QLabel("--- daPa")
        self.pressure_label.setFrameStyle(QFrame.Box)
        self.pressure_label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(self.pressure_label, 1, 1)
        
        # Volumen
        grid_layout.addWidget(QLabel("Volumen:"), 2, 0)
        self.volume_label = QLabel("--- ml")
        self.volume_label.setFrameStyle(QFrame.Box)
        self.volume_label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(self.volume_label, 2, 1)
        
        # Gradiente
        grid_layout.addWidget(QLabel("Gradiente:"), 3, 0)
        self.gradient_label = QLabel("--- daPa")
        self.gradient_label.setFrameStyle(QFrame.Box)
        self.gradient_label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(self.gradient_label, 3, 1)
        
        layout.addLayout(grid_layout)
        layout.addStretch()


class ImpedanceWindow(QWidget):
    """Ventana principal de impedanciometría."""
    
    # Señal para notificar cuando la ventana se cierra
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupWindow()
        self.setupUI()
    
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle("Impedanciómetro - LabSim 3.0")
        self.setGeometry(100, 100, 1000, 700)
        
        # Estilo de ventana independiente
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
                font-family: 'Arial', sans-serif;
                font-size: 10pt;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #888888;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 3px;
                min-width: 100px;
            }
            QSpinBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 3px;
                min-width: 80px;
            }
        """)
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header con información del paciente y oído
        self.setupHeader(main_layout)
        
        # Área principal dividida en tres secciones
        content_layout = QHBoxLayout()
        
        # Sección izquierda: Controles
        self.setupControlsSection(content_layout)
        
        # Sección central: Gráficos
        self.setupGraphicsSection(content_layout)
        
        # Sección derecha: Resultados
        self.setupResultsSection(content_layout)
        
        main_layout.addLayout(content_layout)
        
        # Footer con controles de navegación
        self.setupFooter(main_layout)
    
    def setupHeader(self, parent_layout):
        """Configura el header con información del paciente."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_frame.setMaximumHeight(60)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Información del paciente
        patient_info = QLabel("Paciente: [Caso Clínico] - Edad: [XX] años")
        patient_info.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(patient_info)
        
        header_layout.addStretch()
        
        # Selector de oído
        ear_label = QLabel("Oído:")
        header_layout.addWidget(ear_label)
        
        self.ear_selector = QComboBox()
        self.ear_selector.addItems(["Oído Derecho (OD)", "Oído Izquierdo (OI)"])
        header_layout.addWidget(self.ear_selector)
        
        # Fecha/hora
        datetime_label = QLabel("26/07/2021 - 14:30:25")
        datetime_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(datetime_label)
        
        parent_layout.addWidget(header_frame)
    
    def setupControlsSection(self, parent_layout):
        """Configura la sección de controles."""
        controls_group = QGroupBox("Controles")
        controls_group.setMaximumWidth(200)
        controls_layout = QVBoxLayout(controls_group)
        
        # Modo de prueba
        mode_label = QLabel("Modo de Prueba:")
        controls_layout.addWidget(mode_label)
        
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Timpanometría", "Reflejos Acústicos"])
        controls_layout.addWidget(self.mode_selector)
        
        controls_layout.addWidget(QLabel(""))  # Spacer
        
        # Controles de timpanometría
        tymp_label = QLabel("Timpanometría:")
        tymp_label.setFont(QFont("Arial", 10, QFont.Bold))
        controls_layout.addWidget(tymp_label)
        
        self.start_tymp_btn = QPushButton("Iniciar")
        controls_layout.addWidget(self.start_tymp_btn)
        
        self.stop_tymp_btn = QPushButton("Detener")
        self.stop_tymp_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_tymp_btn)
        
        controls_layout.addWidget(QLabel(""))  # Spacer
        
        # Controles de reflejos
        reflex_label = QLabel("Reflejos Acústicos:")
        reflex_label.setFont(QFont("Arial", 10, QFont.Bold))
        controls_layout.addWidget(reflex_label)
        
        # Frecuencia
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Freq:"))
        self.freq_selector = QComboBox()
        self.freq_selector.addItems(["500 Hz", "1000 Hz", "2000 Hz", "4000 Hz", "NBN"])
        freq_layout.addWidget(self.freq_selector)
        controls_layout.addLayout(freq_layout)
        
        # Intensidad
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Nivel:"))
        self.intensity_spinbox = QSpinBox()
        self.intensity_spinbox.setRange(70, 120)
        self.intensity_spinbox.setValue(85)
        self.intensity_spinbox.setSuffix(" dB")
        intensity_layout.addWidget(self.intensity_spinbox)
        controls_layout.addLayout(intensity_layout)
        
        # Tipo de reflejo
        reflex_type_layout = QHBoxLayout()
        reflex_type_layout.addWidget(QLabel("Tipo:"))
        self.reflex_type = QComboBox()
        self.reflex_type.addItems(["IPSI", "CONTRA"])
        reflex_type_layout.addWidget(self.reflex_type)
        controls_layout.addLayout(reflex_type_layout)
        
        self.test_reflex_btn = QPushButton("Probar")
        controls_layout.addWidget(self.test_reflex_btn)
        
        controls_layout.addStretch()
        
        # Botones de acción
        self.clear_btn = QPushButton("Limpiar")
        controls_layout.addWidget(self.clear_btn)
        
        self.print_btn = QPushButton("Imprimir")
        controls_layout.addWidget(self.print_btn)
        
        parent_layout.addWidget(controls_group)
    
    def setupGraphicsSection(self, parent_layout):
        """Configura la sección de gráficos."""
        graphics_group = QGroupBox("Timpanograma")
        graphics_layout = QVBoxLayout(graphics_group)
        
        # Widget del timpanograma
        self.tympanogram = TympanogramWidget()
        graphics_layout.addWidget(self.tympanogram)
        
        # Controles de navegación del gráfico
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(QLabel("Navegar:"))
        
        self.left_btn = QPushButton("←")
        self.left_btn.setMaximumWidth(40)
        nav_layout.addWidget(self.left_btn)
        
        self.right_btn = QPushButton("→")
        self.right_btn.setMaximumWidth(40)
        nav_layout.addWidget(self.right_btn)
        
        nav_layout.addStretch()
        
        # Indicador de presión actual
        nav_layout.addWidget(QLabel("Presión:"))
        self.current_pressure = QLabel("0 daPa")
        self.current_pressure.setFrameStyle(QFrame.Box)
        self.current_pressure.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.current_pressure)
        
        graphics_layout.addLayout(nav_layout)
        
        parent_layout.addWidget(graphics_group)
    
    def setupResultsSection(self, parent_layout):
        """Configura la sección de resultados."""
        results_layout = QVBoxLayout()
        
        # Resultados de timpanometría
        self.tymp_results = TympanometryResultsWidget()
        results_layout.addWidget(self.tymp_results)
        
        # Umbrales de reflejos
        self.reflex_thresholds = ReflexThresholdWidget()
        results_layout.addWidget(self.reflex_thresholds)
        
        results_layout.addStretch()
        
        parent_layout.addLayout(results_layout)
    
    def setupFooter(self, parent_layout):
        """Configura el footer con controles adicionales."""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.Box)
        footer_frame.setMaximumHeight(40)
        
        footer_layout = QHBoxLayout(footer_frame)
        
        # Estado del sistema
        status_label = QLabel("Estado: Listo")
        footer_layout.addWidget(status_label)
        
        footer_layout.addStretch()
        
        # Botón de calibración
        self.calibrate_btn = QPushButton("Calibrar")
        footer_layout.addWidget(self.calibrate_btn)
        
        # Botón de configuración
        self.config_btn = QPushButton("Configuración")
        footer_layout.addWidget(self.config_btn)
        
        parent_layout.addWidget(footer_frame)
    
    def closeEvent(self, event):
        """Evento al cerrar la ventana."""
        self.finished.emit()
        event.accept()