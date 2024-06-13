import sys
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Signal, Slot

class ExtendedLabel(QLabel):
    textChanged = Signal(object)

    def setText(self, text):
        super().setText(text)
        self.textChanged.emit(self)