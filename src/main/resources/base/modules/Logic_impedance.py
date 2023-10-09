from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile


class Funccion(QWidget):
    def __init__(self, ui_file_path):
        super().__init__()
        loader = QUiLoader()
        file = QFile(ui_file_path)
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file, self)
        file.close()
        
        #se crea un Layout para agregar el widget
        
        central_layout = QVBoxLayout(self)
        central_layout.addWidget(self.ui)
        
        # Aquí puedes hacer tus modificaciones o extensiones
        self.ui.btn_stim_ch0.clicked.connect(self.mi_funcion)
    
    def mi_funcion(self):
        print("estimulo")