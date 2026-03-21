"""
textpro_advanced.py - Editor de Texto Avanzado con Páginas A4
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Editor de texto avanzado que simula páginas A4, guarda en JSON con metadatos
y incluye funcionalidades típicas de procesador de textos.
"""

import os
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QMenuBar, QToolBar,
    QFileDialog, QMessageBox, QApplication, QScrollArea, QFrame,
    QFontComboBox, QSpinBox, QComboBox, QPushButton, QColorDialog,
    QDialog, QGridLayout, QLabel, QLineEdit, QDialogButtonBox,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QAction, QFont, QTextCursor, QTextCharFormat, QColor,
    QTextTableFormat, QTextBlockFormat, QTextListFormat,
    QPageSize, QPainter, QTextDocument, QPixmap
)
from PySide6.QtPrintSupport import QPrinter


class PageWidget(QTextEdit):
    """Widget que representa una página A4."""
    
    def __init__(self, page_number=1, parent=None):
        super().__init__(parent)
        self.page_number = page_number
        self.setupPage()
    
    def setupPage(self):
        """Configura la página con dimensiones A4."""
        # Dimensiones A4 en píxeles (210x297mm a 96 DPI)
        self.setFixedSize(595, 842)  # Ancho x Alto A4
        
        # Márgenes
        doc = self.document()
        doc.setDocumentMargin(50)  # 50px de margen
        
        # Estilo de página
        self.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                margin: 10px;
            }
        """)
        
        # Font por defecto
        self.setFont(QFont("Times New Roman", 12))


class TableDialog(QDialog):
    """Diálogo para insertar tablas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insertar Tabla")
        self.setFixedSize(300, 150)
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # Filas
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Filas:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setMinimum(1)
        self.rows_spin.setMaximum(20)
        self.rows_spin.setValue(3)
        row_layout.addWidget(self.rows_spin)
        layout.addLayout(row_layout)
        
        # Columnas
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("Columnas:"))
        self.cols_spin = QSpinBox()
        self.cols_spin.setMinimum(1)
        self.cols_spin.setMaximum(10)
        self.cols_spin.setValue(3)
        col_layout.addWidget(self.cols_spin)
        layout.addLayout(col_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def getTableSize(self):
        return self.rows_spin.value(), self.cols_spin.value()


class FindReplaceDialog(QDialog):
    """Diálogo para buscar y reemplazar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar y Reemplazar")
        self.setFixedSize(400, 200)
        self.text_edit = None
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # Buscar
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Buscar:"))
        self.find_line = QLineEdit()
        find_layout.addWidget(self.find_line)
        layout.addLayout(find_layout)
        
        # Reemplazar
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Reemplazar:"))
        self.replace_line = QLineEdit()
        replace_layout.addWidget(self.replace_line)
        layout.addLayout(replace_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.find_btn = QPushButton("Buscar")
        self.find_btn.clicked.connect(self.find_text)
        buttons_layout.addWidget(self.find_btn)
        
        self.replace_btn = QPushButton("Reemplazar")
        self.replace_btn.clicked.connect(self.replace_text)
        buttons_layout.addWidget(self.replace_btn)
        
        self.replace_all_btn = QPushButton("Reemplazar Todo")
        self.replace_all_btn.clicked.connect(self.replace_all)
        buttons_layout.addWidget(self.replace_all_btn)
        
        layout.addLayout(buttons_layout)
        
        # Cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def set_text_edit(self, text_edit):
        self.text_edit = text_edit
    
    def find_text(self):
        if not self.text_edit:
            return
        text = self.find_line.text()
        if text:
            self.text_edit.find(text)
    
    def replace_text(self):
        if not self.text_edit:
            return
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_line.text())
    
    def replace_all(self):
        if not self.text_edit:
            return
        find_text = self.find_line.text()
        replace_text = self.replace_line.text()
        if find_text:
            content = self.text_edit.toPlainText()
            new_content = content.replace(find_text, replace_text)
            self.text_edit.setPlainText(new_content)


class TextProWindow(QWidget):
    """Editor de texto avanzado con páginas A4."""
    
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.is_modified = False
        self.current_user = getattr(parent, 'current_user', 'usuario') if parent else 'usuario'
        self.pages = []
        self.current_page_index = 0
        self.find_dialog = None
        
        self.setupWindow()
        self.setupUI()
        self.setupMenus()
        self.setupToolbar()
        self.addNewPage()
        
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle("TextPro - Nuevo Documento")
        self.setGeometry(100, 50, 900, 700)
        self.setWindowFlags(Qt.Window)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                color: black;
            }
            QMenuBar {
                background-color: white;
                border-bottom: 1px solid #d0d0d0;
                padding: 2px;
            }
            QToolBar {
                background-color: white;
                border-bottom: 1px solid #d0d0d0;
                spacing: 3px;
                padding: 5px;
            }
            QScrollArea {
                background-color: #e0e0e0;
                border: none;
            }
        """)
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Barra de menú
        self.menu_bar = QMenuBar()
        layout.addWidget(self.menu_bar)
        
        # Barra de herramientas
        self.toolbar = QToolBar()
        layout.addWidget(self.toolbar)
        
        # Área de scroll para las páginas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        # Widget contenedor de páginas
        self.pages_container = QWidget()
        self.pages_layout = QVBoxLayout(self.pages_container)
        self.pages_layout.setAlignment(Qt.AlignCenter)
        self.pages_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.pages_container)
        layout.addWidget(self.scroll_area)
    
    def setupMenus(self):
        """Configuración de los menús."""
        # Menú Archivo
        file_menu = self.menu_bar.addMenu("Archivo")
        
        new_action = QAction("Nuevo", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("Abrir...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Guardar", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Guardar Como...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Editar
        edit_menu = self.menu_bar.addMenu("Editar")
        
        undo_action = QAction("Deshacer", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Rehacer", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cortar", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Copiar", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Pegar", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction("Buscar y Reemplazar...", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(find_action)
        
        # Menú Insertar
        insert_menu = self.menu_bar.addMenu("Insertar")
        
        date_action = QAction("Fecha y Hora", self)
        date_action.triggered.connect(self.insert_datetime)
        insert_menu.addAction(date_action)
        
        table_action = QAction("Tabla...", self)
        table_action.triggered.connect(self.insert_table)
        insert_menu.addAction(table_action)
        
        # Menú Formato
        format_menu = self.menu_bar.addMenu("Formato")
        
        bold_action = QAction("Negrita", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(self.toggle_bold)
        format_menu.addAction(bold_action)
        
        italic_action = QAction("Cursiva", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(self.toggle_italic)
        format_menu.addAction(italic_action)
        
        underline_action = QAction("Subrayado", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(self.toggle_underline)
        format_menu.addAction(underline_action)
        
        format_menu.addSeparator()
        
        align_left_action = QAction("Alinear Izquierda", self)
        align_left_action.triggered.connect(lambda: self.set_alignment(Qt.AlignLeft))
        format_menu.addAction(align_left_action)
        
        align_center_action = QAction("Centrar", self)
        align_center_action.triggered.connect(lambda: self.set_alignment(Qt.AlignCenter))
        format_menu.addAction(align_center_action)
        
        align_right_action = QAction("Alinear Derecha", self)
        align_right_action.triggered.connect(lambda: self.set_alignment(Qt.AlignRight))
        format_menu.addAction(align_right_action)
        
        justify_action = QAction("Justificar", self)
        justify_action.triggered.connect(lambda: self.set_alignment(Qt.AlignJustify))
        format_menu.addAction(justify_action)
    
    def setupToolbar(self):
        """Configuración de la barra de herramientas."""
        # Fuente
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.change_font)
        self.toolbar.addWidget(QLabel("Fuente:"))
        self.toolbar.addWidget(self.font_combo)
        
        # Tamaño de fuente
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(12)
        self.size_spin.valueChanged.connect(self.change_font_size)
        self.toolbar.addWidget(QLabel("Tamaño:"))
        self.toolbar.addWidget(self.size_spin)
        
        self.toolbar.addSeparator()
        
        # Formato
        bold_btn = QPushButton("B")
        bold_btn.setCheckable(True)
        bold_btn.setFont(QFont("Arial", 10, QFont.Bold))
        bold_btn.clicked.connect(self.toggle_bold)
        self.toolbar.addWidget(bold_btn)
        
        italic_btn = QPushButton("I")
        italic_btn.setCheckable(True)
        font = QFont("Arial", 10)
        font.setItalic(True)
        italic_btn.setFont(font)
        italic_btn.clicked.connect(self.toggle_italic)
        self.toolbar.addWidget(italic_btn)
        
        underline_btn = QPushButton("U")
        underline_btn.setCheckable(True)
        underline_btn.clicked.connect(self.toggle_underline)
        self.toolbar.addWidget(underline_btn)
        
        self.toolbar.addSeparator()
        
        # Color de texto
        color_btn = QPushButton("Color")
        color_btn.clicked.connect(self.change_text_color)
        self.toolbar.addWidget(color_btn)
        
        self.toolbar.addSeparator()
        
        # Alineación
        align_left_btn = QPushButton("←")
        align_left_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignLeft))
        self.toolbar.addWidget(align_left_btn)
        
        align_center_btn = QPushButton("↕")
        align_center_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignCenter))
        self.toolbar.addWidget(align_center_btn)
        
        align_right_btn = QPushButton("→")
        align_right_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignRight))
        self.toolbar.addWidget(align_right_btn)
        
        justify_btn = QPushButton("≡")
        justify_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignJustify))
        self.toolbar.addWidget(justify_btn)
        
        self.toolbar.addSeparator()
        
        # Listas
        bullet_btn = QPushButton("• Lista")
        bullet_btn.clicked.connect(self.insert_bullet_list)
        self.toolbar.addWidget(bullet_btn)
        
        number_btn = QPushButton("1. Lista")
        number_btn.clicked.connect(self.insert_number_list)
        self.toolbar.addWidget(number_btn)
    
    def addNewPage(self):
        """Agrega una nueva página."""
        page = PageWidget(len(self.pages) + 1)
        page.textChanged.connect(self.on_text_changed)
        page.textChanged.connect(self.check_page_overflow)
        
        self.pages.append(page)
        self.pages_layout.addWidget(page)
        
        # Conectar páginas para navegación fluida
        if len(self.pages) > 1:
            # Conectar con página anterior
            prev_page = self.pages[-2]
            page.keyPressEvent = lambda event, p=page: self.handle_page_navigation(event, p)
        
        page.setFocus()
        return page
    
    def check_page_overflow(self):
        """Verifica si necesita crear una nueva página."""
        current_page = self.sender()
        if current_page and current_page in self.pages:
            # Verificar si el texto se desborda (simplificado)
            doc = current_page.document()
            if doc.size().height() > current_page.height() - 100:  # Margen de seguridad
                if current_page == self.pages[-1]:  # Solo si es la última página
                    self.addNewPage()
    
    def handle_page_navigation(self, event, page):
        """Maneja la navegación entre páginas."""
        # Implementación básica para navegación entre páginas
        PageWidget.keyPressEvent(page, event)
    
    def get_current_page(self):
        """Obtiene la página actualmente activa."""
        for page in self.pages:
            if page.hasFocus():
                return page
        return self.pages[0] if self.pages else None
    
    def new_file(self):
        """Crear nuevo archivo."""
        if self.check_unsaved_changes():
            # Limpiar todas las páginas
            for page in self.pages:
                page.deleteLater()
            self.pages.clear()
            
            # Crear nueva página
            self.addNewPage()
            
            self.current_file = None
            self.is_modified = False
            self.update_title()
    
    def open_file(self):
        """Abrir archivo JSON."""
        if self.check_unsaved_changes():
            from .file_explorer import DocumentOpenDialog
            
            dialog = DocumentOpenDialog(self.current_user, self)
            if dialog.exec() == QDialog.Accepted:
                file_path = dialog.getSelectedFile()
                if file_path:
                    self.load_from_json(file_path)
    
    def load_from_json(self, file_path):
        """Carga un documento desde JSON."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Limpiar páginas actuales
            for page in self.pages:
                page.deleteLater()
            self.pages.clear()
            
            # Cargar contenido
            content = data.get('content', '')
            
            # Crear primera página y cargar contenido
            page = self.addNewPage()
            page.setHtml(content)  # Usar setHtml para mantener formato
            
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{str(e)}")
    
    def save_file(self):
        """Guardar archivo actual."""
        if self.current_file:
            self.save_to_json(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Guardar archivo con nuevo nombre."""
        from .file_explorer import DocumentSaveDialog
        
        current_title = ""
        if self.current_file:
            try:
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    current_title = data.get('title', '')
            except:
                pass
        
        dialog = DocumentSaveDialog(self.current_user, current_title, self)
        if dialog.exec() == QDialog.Accepted:
            title = dialog.getDocumentTitle()
            if title:
                user_dir = Path.home() / "labsim" / "data" / self.current_user
                user_dir.mkdir(parents=True, exist_ok=True)
                
                # Crear nombre de archivo seguro
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"{safe_title}.json"
                file_path = user_dir / filename
                
                self.save_to_json(str(file_path), title)
    
    def save_to_json(self, file_path, title=None):
        """Guarda el contenido en formato JSON."""
        try:
            # Combinar contenido de todas las páginas
            combined_content = ""
            for i, page in enumerate(self.pages):
                if i > 0:
                    combined_content += "<br><div style='page-break-before: always;'></div><br>"
                combined_content += page.toHtml()
            
            # Calcular estadísticas
            plain_text = ""
            for page in self.pages:
                plain_text += page.toPlainText()
            
            word_count = len(plain_text.split())
            char_count = len(plain_text)
            
            # Crear estructura JSON
            data = {
                "title": title or (Path(file_path).stem if self.current_file else "Documento sin título"),
                "content": combined_content,
                "plain_text": plain_text,
                "created_at": datetime.now().isoformat() if not self.current_file else self.get_creation_time(file_path),
                "modified_at": datetime.now().isoformat(),
                "author": self.current_user,
                "word_count": word_count,
                "char_count": char_count,
                "page_count": len(self.pages)
            }
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{str(e)}")
    
    def get_creation_time(self, file_path):
        """Obtiene la fecha de creación del archivo actual."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    return data.get('created_at', datetime.now().isoformat())
            except:
                pass
        return datetime.now().isoformat()
    
    # Funciones de edición
    def undo(self):
        current_page = self.get_current_page()
        if current_page:
            current_page.undo()
    
    def redo(self):
        current_page = self.get_current_page()
        if current_page:
            current_page.redo()
    
    def cut(self):
        current_page = self.get_current_page()
        if current_page:
            current_page.cut()
    
    def copy(self):
        current_page = self.get_current_page()
        if current_page:
            current_page.copy()
    
    def paste(self):
        current_page = self.get_current_page()
        if current_page:
            current_page.paste()
    
    # Funciones de formato
    def toggle_bold(self):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            format = cursor.charFormat()
            format.setFontWeight(QFont.Normal if format.fontWeight() == QFont.Bold else QFont.Bold)
            cursor.setCharFormat(format)
    
    def toggle_italic(self):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            format = cursor.charFormat()
            format.setFontItalic(not format.fontItalic())
            cursor.setCharFormat(format)
    
    def toggle_underline(self):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            format = cursor.charFormat()
            format.setFontUnderline(not format.fontUnderline())
            cursor.setCharFormat(format)
    
    def change_font(self, font):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            format = cursor.charFormat()
            format.setFontFamily(font.family())
            cursor.setCharFormat(format)
    
    def change_font_size(self, size):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            format = cursor.charFormat()
            format.setFontPointSize(size)
            cursor.setCharFormat(format)
    
    def change_text_color(self):
        color = QColorDialog.getColor(Qt.black, self)
        if color.isValid():
            current_page = self.get_current_page()
            if current_page:
                cursor = current_page.textCursor()
                format = cursor.charFormat()
                format.setForeground(color)
                cursor.setCharFormat(format)
    
    def set_alignment(self, alignment):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            block_format = cursor.blockFormat()
            block_format.setAlignment(alignment)
            cursor.setBlockFormat(block_format)
    
    def insert_bullet_list(self):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.ListDisc)
            cursor.insertList(list_format)
    
    def insert_number_list(self):
        current_page = self.get_current_page()
        if current_page:
            cursor = current_page.textCursor()
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.ListDecimal)
            cursor.insertList(list_format)
    
    def insert_datetime(self):
        current_page = self.get_current_page()
        if current_page:
            now = datetime.now()
            datetime_str = now.strftime("%d/%m/%Y %H:%M")
            current_page.insertPlainText(datetime_str)
    
    def insert_table(self):
        dialog = TableDialog(self)
        if dialog.exec() == QDialog.Accepted:
            rows, cols = dialog.getTableSize()
            current_page = self.get_current_page()
            if current_page:
                cursor = current_page.textCursor()
                
                table_format = QTextTableFormat()
                table_format.setCellPadding(5)
                table_format.setCellSpacing(0)
                table_format.setBorder(1)
                
                cursor.insertTable(rows, cols, table_format)
    
    def show_find_replace(self):
        if not self.find_dialog:
            self.find_dialog = FindReplaceDialog(self)
        
        current_page = self.get_current_page()
        if current_page:
            self.find_dialog.set_text_edit(current_page)
            self.find_dialog.show()
    
    def on_text_changed(self):
        """Se ejecuta cuando el texto cambia."""
        if not self.is_modified:
            self.is_modified = True
            self.update_title()
    
    def update_title(self):
        """Actualiza el título de la ventana."""
        if self.current_file:
            filename = Path(self.current_file).stem
        else:
            filename = "Nuevo Documento"
        
        if self.is_modified:
            self.setWindowTitle(f"TextPro - {filename}*")
        else:
            self.setWindowTitle(f"TextPro - {filename}")
    
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
            self.finished.emit()
            event.accept()
        else:
            event.ignore()