"""
main.py - Entry point simplificado para LabSim 3.0
Autor: LabSim 3.0
Licencia: MIT

Descripción
-----------
Punto de entrada simplificado. El login ahora está integrado en el MDI.
"""

import sys
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main():
    """Función principal de la aplicación."""
    app = QApplication(sys.argv)
    
    # Configurar estilo global
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal (inicia con login integrado)
    main_window = MainWindow()
    main_window.show()
    
    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()