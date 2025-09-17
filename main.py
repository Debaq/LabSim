"""
main.py - Entry point único para LabSim 3.0
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Punto de entrada único que inicializa la aplicación con la nueva estructura modular.
"""

import sys
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main():
    """Función principal de la aplicación."""
    app = QApplication(sys.argv)
    
    # Configurar estilo global de la aplicación si es necesario
    app.setStyle('Fusion')  # Estilo moderno multiplataforma
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()