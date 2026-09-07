# pylint: disable=no-name-in-module
"""Overlay pequeño "Conectando con el servidor..." mostrado sobre la ventana
de login mientras LoginWorker corre el HTTP en background.

- QDialog sin marco, fondo translúcido.
- Sin assets: el "spinner" es un caracter Unicode que rota vía QTimer
  ciclando entre ⏳◐◓◑◒ -- se ve animado en cualquier tema sin depender
  de transforms CSS de Qt (frágiles entre versiones).
- Se centra sobre el parent (MainLogin) pero NO es child: si fuera child
  heredaría el setMaximumSize(400, 90) del widget de login y no entraría.
"""
# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QVBoxLayout


_SPINNER_FRAMES = ("⏳", "◐", "◓", "◑", "◒", "◓", "◑", "◒")
_SPINNER_INTERVAL_MS = 90


class LoginBusyDialog(QDialog):
    """Mini diálogo modal con spinner. Mostrar/ocultar con show()/close_busy()."""

    def __init__(self, parent=None):
        # Dialog independiente: si heredara el parent del widget de login,
        # el setMaximumSize(400,90) de Ui_Login lo aplastaría.
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        # No se cierra con ESC ni con click fuera -- es un feedback de
        # progreso, no una decisión del usuario.
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        frame = QFrame(self)
        frame.setObjectName("loginBusyFrame")
        frame.setStyleSheet(
            "#loginBusyFrame {"
            "  background-color: palette(window);"
            "  border: 1px solid palette(mid);"
            "  border-radius: 8px;"
            "}"
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(8)

        self._spinner = QLabel(_SPINNER_FRAMES[0], frame)
        spinner_font = QFont()
        spinner_font.setPointSize(22)
        spinner_font.setBold(True)
        self._spinner.setFont(spinner_font)
        self._spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._spinner)

        msg = QLabel("Conectando con el servidor...", frame)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self._idx = 0
        self._timer = QTimer(self)
        self._timer.setInterval(_SPINNER_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        # Tamaño cómodo y consistente.
        self.resize(260, 110)

        # Centrar sobre el parent (en coords de pantalla).
        if parent is not None:
            target = parent.mapToGlobal(parent.rect().center())
            self.move(target - self.rect().center())

    def _tick(self) -> None:
        self._idx = (self._idx + 1) % len(_SPINNER_FRAMES)
        self._spinner.setText(_SPINNER_FRAMES[self._idx])

    def close_busy(self) -> None:
        """Para el timer y libera el diálogo. Llamar siempre, no close() directo."""
        self._timer.stop()
        self.accept()
        self.deleteLater()
