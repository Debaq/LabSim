# pylint: disable=no-name-in-module
"""Overlay "Conectando con el servidor..." mostrado sobre la ventana de
login mientras LoginWorker corre el HTTP en background.

Usa QProgressDialog en estado indeterminate (min=max=0) en lugar de un
QDialog custom. Razón: QProgressDialog ya maneja internamente la animación
de busy, el top-level modal y el repintado correcto en X11/Wayland, y no
necesita flags raros (WA_TranslucentBackground + FramelessWindowHint +
Dialog sin parent) que en Linux han producido segfaults intermitentes
con versiones de Qt/PySide6.
"""
# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressDialog


class LoginBusyDialog(QProgressDialog):
    """Mini diálogo de progreso indeterminate. Mostrar con show()/ocultar
    con close_busy() (compatible con el código que ya espera esa API)."""

    def __init__(self, parent=None):
        # min=max=0 → indeterminate: Qt anima la barra solita.
        super().__init__("Conectando con el servidor...", None, 0, 0, parent)
        # Sin botón cancelar: el login no es cancelable a mitad de camino.
        self.setCancelButton(None)
        # Window modal: bloquea input en el parent mientras está abierto.
        self.setWindowModality(Qt.WindowModality.WindowModal)
        # Se mantiene encima para que el usuario lo vea aunque el parent
        # quede detrás de otras ventanas durante la request.
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setMinimumDuration(0)
        self.setAutoClose(False)
        self.setAutoReset(False)
        # Tamaño cómodo. QProgressDialog respeta sizeHint de Qt.
        self.resize(320, 110)
        # Centrar sobre el parent en coords de pantalla.
        if parent is not None:
            target = parent.mapToGlobal(parent.rect().center())
            self.move(target - self.rect().center())

    def close_busy(self) -> None:
        """Cierra y libera el diálogo. Llamar siempre, no close() directo."""
        self.reset()
        self.deleteLater()
