"""
textpro_window.py - Editor de Texto Básico TextPro
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Editor de texto básico que funciona como ventana independiente sobre el escritorio.
Movido a src/gui/dialogs según la estructura propuesta.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QMenuBar, QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont


class TextProWindow(QWidget):
    """Ventana del editor de texto TextPro."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.is_modified = False
        self.setupUI()
        self.setupMenus()
        self.setupWindow()
    
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle("TextPro - Nuevo Documento")
        self.setGeometry(200, 100, 800, 600)
        
        # Estilo de ventana independiente
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
            }
            QMenuBar {
                background-color: #f0f0f0;
                border-bottom: 1px solid #d0d0d0;
                padding: 2px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QTextEdit {
                border: 1px solid #d0d0d0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                background-color: white;
            }
        """)
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Barra de menú
        self.menu_bar = QMenuBar()
        layout.addWidget(self.menu_bar)
        
        # Área de texto principal
        self.text_area = QTextEdit()
        self.text_area.setFont(QFont("Consolas", 12))
        self.text_area.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_area)
        
        # Focus en el área de texto
        self.text_area.setFocus()
    
    def setupMenus(self):
        """Configuración de los menús."""
        # Menú Archivo
        file_menu = self.menu_bar.addMenu("Archivo")
        
        # Acción Nuevo
        new_action = QAction("Nuevo", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        # Acción Abrir
        open_action = QAction("Abrir...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Acción Guardar
        save_action = QAction("Guardar", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # Acción Guardar Como
        save_as_action = QAction("Guardar Como...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Acción Salir
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Editar
        edit_menu = self.menu_bar.addMenu("Editar")
        
        # Acción Deshacer
        undo_action = QAction("Deshacer", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.text_area.undo)
        edit_menu.addAction(undo_action)
        
        # Acción Rehacer
        redo_action = QAction("Rehacer", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.text_area.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Acción Cortar
        cut_action = QAction("Cortar", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.text_area.cut)
        edit_menu.addAction(cut_action)
        
        # Acción Copiar
        copy_action = QAction("Copiar", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.text_area.copy)
        edit_menu.addAction(copy_action)
        
        # Acción Pegar
        paste_action = QAction("Pegar", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.text_area.paste)
        edit_menu.addAction(paste_action)
    
    def on_text_changed(self):
        """Se ejecuta cuando el texto cambia."""
        if not self.is_modified:
            self.is_modified = True
            self.update_title()
    
    def update_title(self):
        """Actualiza el título de la ventana."""
        if self.current_file:
            filename = self.current_file.split('/')[-1]
        else:
            filename = "Nuevo Documento"
        
        if self.is_modified:
            self.setWindowTitle(f"TextPro - {filename}*")
        else:
            self.setWindowTitle(f"TextPro - {filename}")
    
    def new_file(self):
        """Crear nuevo archivo."""
        if self.check_unsaved_changes():
            self.text_area.clear()
            self.current_file = None
            self.is_modified = False
            self.update_title()
    
    def open_file(self):
        """Abrir archivo existente."""
        if self.check_unsaved_changes():
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Abrir Archivo", 
                "", 
                "Archivos de Texto (*.txt);;Todos los Archivos (*)"
            )
            
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        self.text_area.setPlainText(content)
                        self.current_file = file_path
                        self.is_modified = False
                        self.update_title()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{str(e)}")
    
    def save_file(self):
        """Guardar archivo actual."""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Guardar archivo con nuevo nombre."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Archivo",
            "",
            "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )
        
        if file_path:
            self.save_to_file(file_path)
    
    def save_to_file(self, file_path):
        """Guardar contenido en archivo específico."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.text_area.toPlainText())
                self.current_file = file_path
                self.is_modified = False
                self.update_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{str(e)}")
    
    def check_unsaved_changes(self):
        """Verificar si hay cambios sin guardar."""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Cambios sin Guardar",
                "El documento tiene cambios sin guardar.\n¿Desea guardarlos antes de continuar?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_file()
                return not self.is_modified  # Solo continuar si se guardó exitosamente
            elif reply == QMessageBox.Cancel:
                return False
        
        return True
    
    def closeEvent(self, event):
        """Evento al cerrar la ventana."""
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()