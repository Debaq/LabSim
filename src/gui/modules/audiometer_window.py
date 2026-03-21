"""
audiometer_window.py - Ventana de Audiómetro Refactorizada
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Ventana del audiómetro con código refactorizado usando componentes reutilizables.
Mantiene la disposición exacta del archivo original pero elimina duplicación.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QDial, QFrame, QProgressBar, QGroupBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor


class ChannelDisplay:
    """Componente reutilizable para el display de un canal."""
    
    def __init__(self, side: str, output_text: str, stim_text: str):
        self.side = side
        self.output_text = output_text
        self.stim_text = stim_text
        
        # Labels que serán creados
        self.lbl_intensity = None
        self.lbl_trans = None
        self.lbl_step = None
        self.lbl_output = None
        self.lbl_stim = None
        self.lbl_contin = None
        self.lbl_rev = None
        self.lbl_warning = None
    
    def create_layout(self):
        """Crea el layout del display del canal."""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        
        # Intensidad
        self.lbl_intensity = QLabel("20 dB HL")
        self.lbl_intensity.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_intensity.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_intensity)
        
        # Transductor y Step
        trans_step_layout = QHBoxLayout()
        
        self.lbl_trans = QLabel("Aerea")
        self.lbl_trans.setAlignment(Qt.AlignCenter)
        trans_step_layout.addWidget(self.lbl_trans)
        
        self.lbl_step = QLabel("Pasos : 5 dB")
        self.lbl_step.setAlignment(Qt.AlignCenter)
        trans_step_layout.addWidget(self.lbl_step)
        
        layout.addLayout(trans_step_layout)
        
        # Output
        self.lbl_output = QLabel(self.output_text)
        self.lbl_output.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_output)
        
        # Línea separadora
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)
        
        # Estímulo, Continuo, Reverso
        stim_layout = QHBoxLayout()
        
        self.lbl_stim = QLabel(self.stim_text)
        self.lbl_stim.setFont(QFont("Arial", 8))
        self.lbl_stim.setAlignment(Qt.AlignCenter)
        stim_layout.addWidget(self.lbl_stim)
        
        line_v1 = QFrame()
        line_v1.setFrameShape(QFrame.VLine)
        line_v1.setFrameShadow(QFrame.Sunken)
        stim_layout.addWidget(line_v1)
        
        self.lbl_contin = QLabel("Continuo")
        self.lbl_contin.setFont(QFont("Arial", 8))
        self.lbl_contin.setAlignment(Qt.AlignCenter)
        stim_layout.addWidget(self.lbl_contin)
        
        line_v2 = QFrame()
        line_v2.setFrameShape(QFrame.VLine)
        line_v2.setFrameShadow(QFrame.Sunken)
        stim_layout.addWidget(line_v2)
        
        self.lbl_rev = QLabel("Normal")
        self.lbl_rev.setFont(QFont("Arial", 8))
        self.lbl_rev.setAlignment(Qt.AlignCenter)
        stim_layout.addWidget(self.lbl_rev)
        
        layout.addLayout(stim_layout)
        
        # Línea separadora
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # Warning
        self.lbl_warning = QLabel("")
        layout.addWidget(self.lbl_warning)
        
        return layout


class VUMeter:
    """Componente reutilizable para VU meters."""
    
    def __init__(self, side: str):
        self.side = side
        self.vmeter = None
    
    def create_widget(self):
        """Crea el widget del VU meter."""
        meter_frame = QFrame()
        meter_frame.setMinimumSize(18, 0)
        meter_frame.setMaximumSize(18, 16777215)
        
        layout = QHBoxLayout(meter_frame)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress bar
        self.vmeter = QProgressBar()
        self.vmeter.setMinimumSize(7, 0)
        self.vmeter.setMaximumSize(7, 16777215)
        self.vmeter.setStyleSheet("QProgressBar::chunk { background-color: #55ff7f; }")
        self.vmeter.setValue(0)
        self.vmeter.setOrientation(Qt.Vertical)
        
        # Líneas decorativas
        lines_frame = QFrame()
        lines_frame.setMinimumSize(7, 0)
        lines_frame.setMaximumSize(7, 16777215)
        
        lines_layout = QVBoxLayout(lines_frame)
        lines_layout.setSpacing(0)
        lines_layout.setContentsMargins(0, 0, 0, 0)
        
        for _ in range(3):
            line = QFrame()
            line.setMinimumSize(5, 0)
            line.setMaximumSize(5, 16777215)
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            lines_layout.addWidget(line)
        
        # Orden según el lado
        if self.side == "der":
            layout.addWidget(self.vmeter)
            layout.addWidget(lines_frame)
        else:
            layout.addWidget(lines_frame)
            layout.addWidget(self.vmeter)
        
        return meter_frame


class ChannelControls:
    """Componente reutilizable para controles de canal."""
    
    def __init__(self, side: str):
        self.side = side
        self.buttons = {}
    
    def create_upper_controls(self):
        """Crea los controles superiores del canal."""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, -1, -1, -1)
        
        # Salida
        output_layout = QVBoxLayout()
        output_label = QLabel("Salida")
        output_label.setFont(QFont("Arial", 9))
        output_label.setAlignment(Qt.AlignCenter)
        output_layout.addWidget(output_label)
        
        for text in ["Derecha", "Izquierda", "Simultáneo"]:
            btn = QPushButton(text)
            btn.setMaximumSize(16777215, 25)
            btn.setFont(QFont("Arial", 9))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.buttons[f"output_{text.lower()}"] = btn
            output_layout.addWidget(btn)
        
        output_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(output_layout)
        
        # Estímulo
        stim_layout = QVBoxLayout()
        stim_layout.setContentsMargins(-1, -1, -1, 0)
        
        stim_label = QLabel("Estímulo")
        stim_label.setFont(QFont("Arial", 9))
        stim_label.setAlignment(Qt.AlignCenter)
        stim_layout.addWidget(stim_label)
        
        # Botones principales de estímulo
        for text in ["Tono", "FM", "Habla"]:
            btn = QPushButton(text)
            btn.setMaximumSize(16777215, 25)
            btn.setFont(QFont("Arial", 9))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.buttons[f"stim_{text.lower()}"] = btn
            stim_layout.addWidget(btn)
        
        # Ruidos en dos filas
        noise_layout1 = QHBoxLayout()
        noise_layout1.setSpacing(0)
        for text in ["WN", "NBN"]:
            btn = QPushButton(text)
            btn.setMaximumSize(35, 25)
            btn.setFont(QFont("Arial", 8))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.buttons[f"stim_{text.lower()}"] = btn
            noise_layout1.addWidget(btn)
        stim_layout.addLayout(noise_layout1)
        
        noise_layout2 = QHBoxLayout()
        noise_layout2.setSpacing(0)
        for text in ["PN", "SN"]:
            btn = QPushButton(text)
            btn.setMaximumSize(35, 25)
            btn.setFont(QFont("Arial", 8))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.buttons[f"stim_{text.lower()}"] = btn
            noise_layout2.addWidget(btn)
        stim_layout.addLayout(noise_layout2)
        
        stim_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(stim_layout)
        
        # Transductor
        trans_layout = QVBoxLayout()
        trans_label = QLabel("Transductor")
        trans_label.setFont(QFont("Arial", 9))
        trans_label.setAlignment(Qt.AlignCenter)
        trans_layout.addWidget(trans_label)
        
        for text in ["Aéreo", "Ósea", "C. libre"]:
            btn = QPushButton(text)
            btn.setMaximumSize(16777215, 25)
            btn.setFont(QFont("Arial", 9))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.buttons[f"trans_{text.lower().replace(' ', '_').replace('ó', 'o')}"] = btn
            trans_layout.addWidget(btn)
        
        trans_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(trans_layout)
        
        return layout
    
    def create_lower_controls(self):
        """Crea los controles inferiores del canal (dial + botones)."""
        layout = QHBoxLayout()
        
        # Crear dial
        dial = QDial()
        dial.setCursor(QCursor(Qt.OpenHandCursor))
        dial.setMinimum(1)
        dial.setMaximum(20)
        dial.setValue(10)
        dial.setWrapping(True)
        dial.setNotchesVisible(False)
        self.buttons["dial"] = dial
        
        dial_layout = QVBoxLayout()
        dial_layout.addWidget(dial)
        
        # Crear botones de control
        controls_layout = QVBoxLayout()
        
        btn_puls = QPushButton("Pulsado")
        btn_puls.setFont(QFont("Arial", 9))
        self.buttons["pulsado"] = btn_puls
        controls_layout.addWidget(btn_puls)
        
        btn_rever = QPushButton("Invertir")
        btn_rever.setFont(QFont("Arial", 9))
        btn_rever.setCursor(QCursor(Qt.PointingHandCursor))
        self.buttons["invertir"] = btn_rever
        controls_layout.addWidget(btn_rever)
        
        controls_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        btn_stim = QPushButton("Estímulo")
        btn_stim.setFont(QFont("Arial", 9))
        btn_stim.setCursor(QCursor(Qt.PointingHandCursor))
        self.buttons["estimulo"] = btn_stim
        controls_layout.addWidget(btn_stim)
        
        controls_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Orden según el lado (reflejo)
        if self.side == "der":
            layout.addLayout(dial_layout)
            layout.addLayout(controls_layout)
        else:
            layout.addLayout(controls_layout)
            layout.addLayout(dial_layout)
        
        return layout


class AudiometerWindow(QWidget):
    """Ventana del audiómetro con componentes refactorizados."""
    
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupWindow()
        self.setupUI()
    
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle("Audiómetro - LabSim 3.0")
        self.setGeometry(100, 100, 740, 504)
        self.setMinimumSize(740, 500)
        self.setMaximumSize(830, 504)
        self.setWindowFlags(Qt.Window)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: black;
            }
            QPushButton {
                background-color: #e8e8e8;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #d8d8d8;
            }
            QPushButton:pressed {
                background-color: #c8c8c8;
            }
            QFrame[frameShape="4"], QFrame[frameShape="5"] {
                color: #a0a0a0;
            }
            QLabel {
                background-color: transparent;
            }
            QDial {
                background-color: #e8e8e8;
            }
            QProgressBar {
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                background-color: #f8f8f8;
            }
            QProgressBar::chunk {
                background-color: #55ff7f;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                margin-top: 0.5em;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Layout vertical principal
        vertical_layout = QVBoxLayout()
        vertical_layout.setSpacing(4)
        
        # === DISPLAY SUPERIOR ===
        self.create_display_section(vertical_layout)
        
        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        vertical_layout.addWidget(line)
        
        # === CONTROLES ===
        self.create_controls_section(vertical_layout)
        
        main_layout.addLayout(vertical_layout)
    
    def create_display_section(self, parent_layout):
        """Crea la sección del display superior usando componentes."""
        display = QFrame()
        display.setMinimumSize(0, 120)
        display.setMaximumSize(16777215, 120)
        display.setStyleSheet("background-color: white; border: 1px solid #c0c0c0;")
        display.setFrameShape(QFrame.Box)
        
        display_layout = QHBoxLayout(display)
        display_layout.setSpacing(2)
        display_layout.setContentsMargins(0, 0, 0, 0)
        
        # Canal Derecho
        channel_der = ChannelDisplay("der", "Derecha", "Tono")
        display_layout.addLayout(channel_der.create_layout())
        
        # Separador + VU Meter Derecho
        self.add_vertical_separator(display_layout)
        vu_der = VUMeter("der")
        display_layout.addWidget(vu_der.create_widget())
        
        # Separador + Display Central
        self.add_vertical_separator(display_layout)
        self.create_central_display(display_layout)
        
        # Separador + VU Meter Izquierdo
        self.add_vertical_separator(display_layout)
        vu_izq = VUMeter("izq")
        display_layout.addWidget(vu_izq.create_widget())
        
        # Canal Izquierdo
        channel_izq = ChannelDisplay("izq", "Izquierda", "Narrow Band Noise")
        display_layout.addLayout(channel_izq.create_layout())
        
        parent_layout.addWidget(display)
    
    def create_central_display(self, parent_layout):
        """Crea el display central."""
        central = QFrame()
        central.setMinimumSize(270, 0)
        central.setMaximumSize(270, 16777215)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Frecuencia
        self.lbl_freq = QLabel("1000 Hz")
        self.lbl_freq.setMinimumSize(0, 60)
        self.lbl_freq.setMaximumSize(16777215, 60)
        self.lbl_freq.setFont(QFont("Arial", 20, QFont.Bold))
        self.lbl_freq.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_freq)
        
        # Otras labels centrales
        for text in ["Umbrales", "0:0", ""]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            if text == "":
                lbl.setFont(QFont("Arial", 8, QFont.Bold))
            layout.addWidget(lbl)
        
        # Extensiones
        ext_layout = QHBoxLayout()
        ext_layout.setSpacing(0)
        
        for align in [Qt.AlignLeft, Qt.AlignCenter, Qt.AlignRight]:
            ext_lbl = QLabel("")
            ext_lbl.setMinimumSize(90, 0)
            ext_lbl.setMaximumSize(90, 15)
            ext_lbl.setFont(QFont("Arial", 9))
            ext_lbl.setAlignment(align)
            ext_layout.addWidget(ext_lbl)
        
        layout.addLayout(ext_layout)
        parent_layout.addWidget(central)
    
    def create_controls_section(self, parent_layout):
        """Crea la sección de controles usando componentes."""
        control_layout = QVBoxLayout()
        control_layout.setSpacing(4)
        
        # === CONTROLES SUPERIORES ===
        upper_controls = QHBoxLayout()
        upper_controls.setSpacing(10)
        
        # Monitor
        self.create_monitor_section(upper_controls)
        self.add_vertical_separator(upper_controls)
        
        # Canal Derecho
        channel_der_controls = ChannelControls("der")
        upper_controls.addLayout(channel_der_controls.create_upper_controls())
        self.add_vertical_separator(upper_controls)
        
        # Controles Centrales
        self.create_central_controls(upper_controls)
        self.add_vertical_separator(upper_controls)
        
        # Canal Izquierdo
        channel_izq_controls = ChannelControls("izq")
        upper_controls.addLayout(channel_izq_controls.create_upper_controls())
        self.add_vertical_separator(upper_controls)
        
        # Talkback
        self.create_talkback_section(upper_controls)
        
        control_layout.addLayout(upper_controls)
        
        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        control_layout.addWidget(line)
        
        # === CONTROLES INFERIORES ===
        lower_controls = QHBoxLayout()
        lower_controls.setSpacing(4)
        
        # Dial y controles derecho
        channel_der_lower = ChannelControls("der")
        lower_controls.addLayout(channel_der_lower.create_lower_controls())
        self.add_vertical_separator(lower_controls)
        
        # Controles centrales inferiores
        self.create_lower_central_controls(lower_controls)
        self.add_vertical_separator(lower_controls)
        
        # Dial y controles izquierdo
        channel_izq_lower = ChannelControls("izq")
        lower_controls.addLayout(channel_izq_lower.create_lower_controls())
        
        control_layout.addLayout(lower_controls)
        parent_layout.addLayout(control_layout)
    
    def create_monitor_section(self, parent_layout):
        """Crea la sección de monitor."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, -1, -1, -1)
        
        # Label
        monitor_label = QLabel("Monitor")
        monitor_label.setFont(QFont("Arial", 8))
        monitor_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(monitor_label)
        
        # Diales y labels
        for ch_num in [1, 2]:
            dial = QDial()
            dial.setMinimumSize(45, 45)
            dial.setMaximumSize(45, 45)
            dial.setMaximum(20)
            dial.setValue(2)
            dial.setNotchesVisible(True)
            layout.addWidget(dial)
            
            ch_label = QLabel(f"ch{ch_num}")
            ch_label.setFont(QFont("Arial", 7))
            ch_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(ch_label)
        
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        parent_layout.addLayout(layout)
    
    def create_central_controls(self, parent_layout):
        """Crea los controles centrales."""
        central_frame = QFrame()
        central_frame.setMaximumSize(90, 16777215)
        
        layout = QVBoxLayout(central_frame)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Alta frecuencia
        btn_alta_frec = QPushButton("Alta frec.")
        btn_alta_frec.setMaximumSize(85, 25)
        btn_alta_frec.setFont(QFont("Arial", 9))
        layout.addWidget(btn_alta_frec)
        
        # Línea
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # GroupBox Pasos
        step_group = QGroupBox("Pasos")
        step_group.setFont(QFont("Arial", 8))
        step_group.setAlignment(Qt.AlignCenter)
        
        step_layout = QHBoxLayout(step_group)
        step_layout.setContentsMargins(1, 0, 1, 0)
        
        for text in ["1", "3", "5"]:
            btn = QPushButton(text)
            btn.setMaximumSize(16777215, 25)
            btn.setFont(QFont("Arial", 8))
            step_layout.addWidget(btn)
        
        layout.addWidget(step_group)
        
        # Línea
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # Ext. Rango
        btn_ext_range = QPushButton("Ext. Rango")
        btn_ext_range.setMaximumSize(85, 25)
        btn_ext_range.setFont(QFont("Arial", 9))
        layout.addWidget(btn_ext_range)
        
        parent_layout.addWidget(central_frame)
    
    def create_talkback_section(self, parent_layout):
        """Crea la sección de talkback."""
        layout = QVBoxLayout()
        
        talkback_label = QLabel("Talkback")
        talkback_label.setFont(QFont("Arial", 8))
        layout.addWidget(talkback_label)
        
        dial_talkback = QDial()
        dial_talkback.setMinimumSize(45, 45)
        dial_talkback.setMaximumSize(45, 45)
        dial_talkback.setMaximum(100)
        dial_talkback.setValue(5)
        dial_talkback.setNotchesVisible(True)
        layout.addWidget(dial_talkback)
        
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        parent_layout.addLayout(layout)
    
    def create_lower_central_controls(self, parent_layout):
        """Crea los controles centrales inferiores."""
        layout = QVBoxLayout()
        layout.setContentsMargins(-1, 0, -1, -1)
        
        # Botones de tiempo
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(-1, 0, -1, -1)
        for text in ["Iniciar", "Detener", "Borrar"]:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 9))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            time_layout.addWidget(btn)
        layout.addLayout(time_layout)
        
        # Botones de respuesta
        response_layout = QHBoxLayout()
        response_layout.setContentsMargins(-1, 0, -1, -1)
        for text in ["+1", "Limpiar", "-1"]:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 9))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            response_layout.addWidget(btn)
        layout.addLayout(response_layout)
        
        # Talkback y Alternado
        talk_alt_layout = QHBoxLayout()
        for text in ["Talkback", "Alternado"]:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 9))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            talk_alt_layout.addWidget(btn)
        layout.addLayout(talk_alt_layout)
        
        # Frecuencia
        freq_layout = QHBoxLayout()
        freq_layout.setContentsMargins(-1, 0, -1, -1)
        
        btn_freq_minus = QPushButton("<")
        btn_freq_minus.setFont(QFont("Arial", 9))
        btn_freq_minus.setCursor(QCursor(Qt.PointingHandCursor))
        freq_layout.addWidget(btn_freq_minus)
        
        freq_label = QLabel("Frecuencia")
        freq_label.setFont(QFont("Arial", 9))
        freq_label.setAlignment(Qt.AlignCenter)
        freq_layout.addWidget(freq_label)
        
        btn_freq_plus = QPushButton(">")
        btn_freq_plus.setFont(QFont("Arial", 9))
        btn_freq_plus.setCursor(QCursor(Qt.PointingHandCursor))
        freq_layout.addWidget(btn_freq_plus)
        
        layout.addLayout(freq_layout)
        parent_layout.addLayout(layout)
    
    def add_vertical_separator(self, parent_layout):
        """Agrega un separador vertical."""
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        parent_layout.addWidget(line)
    
    def closeEvent(self, event):
        """Evento al cerrar la ventana."""
        self.finished.emit()
        event.accept()