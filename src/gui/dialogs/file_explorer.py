"""
file_explorer.py - Explorador y diálogos estilo sistema tradicional
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Explorador y diálogos que imitan el estilo tradicional del sistema operativo
pero simplificado para una sola carpeta de documentos JSON.
"""

import os
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QMessageBox, QInputDialog,
    QDialogButtonBox, QGroupBox, QGridLayout, QSplitter, QFrame, QToolBar,
    QComboBox, QHeaderView, QTreeWidget, QTreeWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QAction


class FileListWidget(QListWidget):
    """Lista de archivos estilo explorador tradicional."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_dir = None
        self.setupList()
    
    def setupList(self):
        """Configura la lista con estilo tradicional."""
        self.setIconSize(QSize(32, 32))
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Estilo similar a explorador de archivos
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #d0d0d0;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e5f3ff;
            }
        """)
    
    def setUserDirectory(self, user_name):
        """Establece el directorio del usuario."""
        self.user_dir = Path.home() / "labsim" / "data" / user_name
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.refreshFiles()
    
    def refreshFiles(self):
        """Actualiza la lista de archivos."""
        if not self.user_dir:
            return
            
        self.clear()
        
        # Buscar archivos JSON
        json_files = list(self.user_dir.glob("*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                item = QListWidgetItem()
                
                # Nombre del archivo visible
                title = metadata.get('title', file_path.stem)
                item.setText(title)
                
                # Guardar metadata
                item.setData(Qt.UserRole, {
                    'file_path': str(file_path),
                    'metadata': metadata
                })
                
                # Tooltip con información
                try:
                    date_obj = datetime.fromisoformat(metadata.get('modified_at', '').replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%d/%m/%Y %H:%M')
                except:
                    date_str = 'Fecha desconocida'
                
                tooltip = f"""Archivo: {file_path.name}
Título: {title}
Modificado: {date_str}
Tamaño: {file_path.stat().st_size} bytes
Páginas: {metadata.get('page_count', 0)}
Palabras: {metadata.get('word_count', 0)}"""
                item.setToolTip(tooltip)
                
                self.addItem(item)
                
            except Exception as e:
                # Archivo JSON corrupto, mostrar como archivo sin metadatos
                item = QListWidgetItem()
                item.setText(f"{file_path.stem} (corrupto)")
                item.setData(Qt.UserRole, {
                    'file_path': str(file_path),
                    'metadata': {}
                })
                self.addItem(item)
    
    def getSelectedFile(self):
        """Retorna el archivo seleccionado."""
        current = self.currentItem()
        if current:
            data = current.data(Qt.UserRole)
            return data.get('file_path') if data else None
        return None
    
    def getSelectedMetadata(self):
        """Retorna los metadatos del archivo seleccionado."""
        current = self.currentItem()
        if current:
            data = current.data(Qt.UserRole)
            return data.get('metadata', {}) if data else {}
        return {}


class FileInfoPanel(QFrame):
    """Panel de información del archivo estilo explorador."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMaximumWidth(250)
        self.setupUI()
    
    def setupUI(self):
        """Configura la interfaz del panel."""
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Propiedades")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Información del archivo
        self.info_layout = QVBoxLayout()
        layout.addLayout(self.info_layout)
        
        # Labels de información
        self.name_label = QLabel()
        self.size_label = QLabel()
        self.date_label = QLabel()
        self.author_label = QLabel()
        self.pages_label = QLabel()
        self.words_label = QLabel()
        
        # Vista previa
        layout.addWidget(QLabel("Vista previa:"))
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        layout.addStretch()
        
        self.clearInfo()
    
    def showFileInfo(self, file_path, metadata):
        """Muestra información del archivo."""
        self.clearInfo()
        
        if not file_path or not os.path.exists(file_path):
            return
        
        path = Path(file_path)
        
        # Información básica del archivo
        info_items = [
            ("Nombre:", metadata.get('title', path.stem)),
            ("Archivo:", path.name),
            ("Tamaño:", f"{path.stat().st_size} bytes"),
            ("Autor:", metadata.get('author', 'Desconocido')),
            ("Páginas:", str(metadata.get('page_count', 0))),
            ("Palabras:", str(metadata.get('word_count', 0)))
        ]
        
        # Fecha de modificación
        try:
            date_obj = datetime.fromisoformat(metadata.get('modified_at', '').replace('Z', '+00:00'))
            date_str = date_obj.strftime('%d/%m/%Y %H:%M')
        except:
            date_str = 'Desconocida'
        info_items.insert(3, ("Modificado:", date_str))
        
        # Mostrar información
        for label, value in info_items:
            item_widget = QFrame()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(2)
            
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 8, QFont.Bold))
            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            
            item_layout.addWidget(label_widget)
            item_layout.addWidget(value_widget)
            
            self.info_layout.addWidget(item_widget)
        
        # Vista previa del contenido
        plain_text = metadata.get('plain_text', '')
        if plain_text:
            preview = plain_text[:150] + ("..." if len(plain_text) > 150 else "")
            self.preview_text.setPlainText(preview)
    
    def clearInfo(self):
        """Limpia la información mostrada."""
        # Limpiar layout de información
        while self.info_layout.count():
            child = self.info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Limpiar vista previa
        self.preview_text.clear()


class DocumentOpenDialog(QDialog):
    """Diálogo de abrir estilo explorador tradicional."""
    
    def __init__(self, user_name, parent=None):
        super().__init__(parent)
        self.user_name = user_name
        self.selected_file = None
        self.setupDialog()
    
    def setupDialog(self):
        """Configura el diálogo estilo tradicional."""
        self.setWindowTitle("Abrir Documento")
        self.setModal(True)
        self.resize(800, 500)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Barra de ubicación
        location_frame = QFrame()
        location_frame.setFrameStyle(QFrame.StyledPanel)
        location_layout = QHBoxLayout(location_frame)
        
        location_layout.addWidget(QLabel("Ubicación:"))
        location_path = QLabel(f"labsim/data/{self.user_name}")
        location_path.setStyleSheet("background-color: white; padding: 4px; border: 1px solid #d0d0d0;")
        location_layout.addWidget(location_path, 1)
        
        layout.addWidget(location_frame)
        
        # Área principal con splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Lista de archivos
        self.file_list = FileListWidget()
        self.file_list.setUserDirectory(self.user_name)
        self.file_list.currentItemChanged.connect(self.onFileSelected)
        self.file_list.itemDoubleClicked.connect(self.onFileDoubleClicked)
        splitter.addWidget(self.file_list)
        
        # Panel de información
        self.info_panel = FileInfoPanel()
        splitter.addWidget(self.info_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([550, 250])
        layout.addWidget(splitter)
        
        # Área inferior estilo diálogo tradicional
        bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(bottom_frame)
        
        # Campo de nombre de archivo
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("Nombre del archivo:"))
        self.filename_edit = QLineEdit()
        self.filename_edit.setReadOnly(True)
        filename_layout.addWidget(self.filename_edit)
        bottom_layout.addLayout(filename_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.open_button = QPushButton("Abrir")
        self.open_button.setEnabled(False)
        self.open_button.setDefault(True)
        self.open_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.open_button)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        bottom_layout.addLayout(buttons_layout)
        layout.addWidget(bottom_frame)
    
    def onFileSelected(self, current, previous):
        """Se ejecuta cuando se selecciona un archivo."""
        if current:
            data = current.data(Qt.UserRole)
            if data:
                file_path = data.get('file_path')
                metadata = data.get('metadata', {})
                
                # Actualizar campo de nombre
                if file_path:
                    self.filename_edit.setText(Path(file_path).name)
                    self.selected_file = file_path
                
                # Mostrar información
                self.info_panel.showFileInfo(file_path, metadata)
                
                # Habilitar botón
                self.open_button.setEnabled(True)
        else:
            self.filename_edit.clear()
            self.info_panel.clearInfo()
            self.open_button.setEnabled(False)
            self.selected_file = None
    
    def onFileDoubleClicked(self, item):
        """Se ejecuta al hacer doble clic en un archivo."""
        self.accept()
    
    def getSelectedFile(self):
        """Retorna el archivo seleccionado."""
        return self.selected_file


class DocumentSaveDialog(QDialog):
    """Diálogo de guardar estilo explorador tradicional."""
    
    def __init__(self, user_name, current_title="", parent=None):
        super().__init__(parent)
        self.user_name = user_name
        self.current_title = current_title
        self.document_title = ""
        self.setupDialog()
    
    def setupDialog(self):
        """Configura el diálogo estilo tradicional."""
        self.setWindowTitle("Guardar Documento")
        self.setModal(True)
        self.resize(800, 500)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Barra de ubicación
        location_frame = QFrame()
        location_frame.setFrameStyle(QFrame.StyledPanel)
        location_layout = QHBoxLayout(location_frame)
        
        location_layout.addWidget(QLabel("Guardar en:"))
        location_path = QLabel(f"labsim/data/{self.user_name}")
        location_path.setStyleSheet("background-color: white; padding: 4px; border: 1px solid #d0d0d0;")
        location_layout.addWidget(location_path, 1)
        
        layout.addWidget(location_frame)
        
        # Área principal con splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Lista de archivos existentes
        self.file_list = FileListWidget()
        self.file_list.setUserDirectory(self.user_name)
        self.file_list.currentItemChanged.connect(self.onFileSelected)
        splitter.addWidget(self.file_list)
        
        # Panel de información
        self.info_panel = FileInfoPanel()
        splitter.addWidget(self.info_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([550, 250])
        layout.addWidget(splitter)
        
        # Área inferior estilo diálogo tradicional
        bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(bottom_frame)
        
        # Campo de nombre de archivo
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("Título del documento:"))
        self.filename_edit = QLineEdit(self.current_title)
        self.filename_edit.textChanged.connect(self.onTitleChanged)
        filename_layout.addWidget(self.filename_edit)
        bottom_layout.addLayout(filename_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.save_button = QPushButton("Guardar")
        self.save_button.setEnabled(bool(self.current_title))
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        bottom_layout.addLayout(buttons_layout)
        layout.addWidget(bottom_frame)
        
        # Focus y selección
        self.filename_edit.setFocus()
        if self.current_title:
            self.filename_edit.selectAll()
    
    def onFileSelected(self, current, previous):
        """Se ejecuta cuando se selecciona un archivo existente."""
        if current:
            data = current.data(Qt.UserRole)
            if data:
                metadata = data.get('metadata', {})
                title = metadata.get('title', '')
                
                # Mostrar información
                self.info_panel.showFileInfo(data.get('file_path'), metadata)
                
                # Opcional: completar título si está vacío
                if not self.filename_edit.text() and title:
                    self.filename_edit.setText(title)
        else:
            self.info_panel.clearInfo()
    
    def onTitleChanged(self, text):
        """Se ejecuta cuando cambia el título."""
        self.save_button.setEnabled(bool(text.strip()))
    
    def accept(self):
        """Acepta el diálogo."""
        self.document_title = self.filename_edit.text().strip()
        if self.document_title:
            super().accept()
    
    def getDocumentTitle(self):
        """Retorna el título del documento."""
        return self.document_title


class FileExplorerWindow(QWidget):
    """Ventana del explorador de archivos completo estilo tradicional."""
    
    finished = Signal()
    
    def __init__(self, user_name, parent=None):
        super().__init__(parent)
        self.user_name = user_name
        self.setupWindow()
        self.setupUI()
    
    def setupWindow(self):
        """Configuración básica de la ventana."""
        self.setWindowTitle(f"Explorador de Documentos - {self.user_name}")
        self.setGeometry(100, 100, 900, 600)
        self.setWindowFlags(Qt.Window)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: black;
            }
            QToolBar {
                background-color: white;
                border: 1px solid #d0d0d0;
                spacing: 2px;
                padding: 4px;
            }
            QPushButton {
                background-color: #e1e1e1;
                border: 1px solid #adadad;
                border-radius: 3px;
                padding: 6px 12px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #888888;
                border: 1px solid #d0d0d0;
            }
        """)
    
    def setupUI(self):
        """Configuración de la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Barra de herramientas estilo explorador
        self.toolbar = QToolBar()
        
        # Botones principales
        open_action = QAction("Abrir", self)
        open_action.triggered.connect(self.openDocument)
        self.toolbar.addAction(open_action)
        
        self.toolbar.addSeparator()
        
        rename_action = QAction("Renombrar", self)
        rename_action.triggered.connect(self.renameDocument)
        self.toolbar.addAction(rename_action)
        
        delete_action = QAction("Eliminar", self)
        delete_action.triggered.connect(self.deleteDocument)
        self.toolbar.addAction(delete_action)
        
        self.toolbar.addSeparator()
        
        refresh_action = QAction("Actualizar", self)
        refresh_action.triggered.connect(self.refreshFiles)
        self.toolbar.addAction(refresh_action)
        
        layout.addWidget(self.toolbar)
        
        # Barra de ubicación
        location_frame = QFrame()
        location_frame.setFrameStyle(QFrame.StyledPanel)
        location_layout = QHBoxLayout(location_frame)
        
        location_layout.addWidget(QLabel("Ubicación:"))
        location_path = QLabel(f"labsim/data/{self.user_name}")
        location_path.setStyleSheet("background-color: white; padding: 4px; border: 1px solid #d0d0d0;")
        location_layout.addWidget(location_path, 1)
        
        layout.addWidget(location_frame)
        
        # Área principal con splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Lista de archivos
        self.file_list = FileListWidget()
        self.file_list.setUserDirectory(self.user_name)
        self.file_list.currentItemChanged.connect(self.onFileSelected)
        self.file_list.itemDoubleClicked.connect(self.openDocument)
        splitter.addWidget(self.file_list)
        
        # Panel de información
        self.info_panel = FileInfoPanel()
        splitter.addWidget(self.info_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([650, 250])
        layout.addWidget(splitter)
        
        # Barra de estado
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("Listo")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.count_label = QLabel()
        status_layout.addWidget(self.count_label)
        
        layout.addWidget(status_frame)
        
        # Actualizar contador inicial
        self.updateFileCount()
    
    def onFileSelected(self, current, previous):
        """Se ejecuta cuando se selecciona un archivo."""
        if current:
            data = current.data(Qt.UserRole)
            if data:
                file_path = data.get('file_path')
                metadata = data.get('metadata', {})
                
                # Mostrar información
                self.info_panel.showFileInfo(file_path, metadata)
                
                # Actualizar estado
                filename = Path(file_path).name if file_path else ""
                self.status_label.setText(f"Seleccionado: {filename}")
        else:
            self.info_panel.clearInfo()
            self.status_label.setText("Listo")
    
    def openDocument(self):
        """Abre el documento seleccionado."""
        file_path = self.file_list.getSelectedFile()
        if file_path:
            # Aquí se podría integrar con TextPro
            QMessageBox.information(self, "Abrir", f"Abriría el documento:\n{Path(file_path).name}")
    
    def renameDocument(self):
        """Renombra el documento seleccionado."""
        current = self.file_list.currentItem()
        if not current:
            QMessageBox.information(self, "Renombrar", "Seleccione un documento para renombrar.")
            return
        
        data = current.data(Qt.UserRole)
        if not data:
            return
            
        file_path = data.get('file_path')
        metadata = data.get('metadata', {})
        old_title = metadata.get('title', Path(file_path).stem)
        
        new_title, ok = QInputDialog.getText(
            self,
            "Renombrar Documento",
            "Nuevo título:",
            text=old_title
        )
        
        if ok and new_title and new_title != old_title:
            try:
                # Leer archivo actual
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Actualizar título y fecha
                data['title'] = new_title
                data['modified_at'] = datetime.now().isoformat()
                
                # Guardar cambios
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.refreshFiles()
                self.status_label.setText("Documento renombrado exitosamente")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo renombrar el documento:\n{str(e)}")
    
    def deleteDocument(self):
        """Elimina el documento seleccionado."""
        current = self.file_list.currentItem()
        if not current:
            QMessageBox.information(self, "Eliminar", "Seleccione un documento para eliminar.")
            return
        
        data = current.data(Qt.UserRole)
        if not data:
            return
            
        file_path = data.get('file_path')
        metadata = data.get('metadata', {})
        title = metadata.get('title', Path(file_path).stem)
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar '{title}'?\n\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                self.refreshFiles()
                self.status_label.setText("Documento eliminado exitosamente")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el documento:\n{str(e)}")
    
    def refreshFiles(self):
        """Actualiza la lista de archivos."""
        self.file_list.refreshFiles()
        self.updateFileCount()
        self.status_label.setText("Lista actualizada")
    
    def updateFileCount(self):
        """Actualiza el contador de archivos."""
        count = self.file_list.count()
        self.count_label.setText(f"{count} elemento{'s' if count != 1 else ''}")
    
    def closeEvent(self, event):
        """Evento al cerrar la ventana."""
        self.finished.emit()
        event.accept()