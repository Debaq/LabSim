"""Placeholder minimo para modulos habilitables por curso que todavia no
tienen implementacion real (ver Layout::APPS en el backend, state 'pre'
sin funcionalidad -- ej. VEMP/EOAS). Sin esto, activar el modulo desde
el checklist de courses.php pero sin una entrada en self.subw de main.py
revienta con KeyError al hacer clic (ver ToolBar.activate_subwindow)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ModulePlaceholder(QWidget):
    def __init__(self, titulo: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(f"{titulo}\n\nMódulo en construcción -- todavía no disponible.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
