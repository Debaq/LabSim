# pylint: disable=no-name-in-module
"""Overlay "Conectando con el servidor..." mostrado sobre la ventana de
login mientras LoginWorker corre el HTTP en background.

Diseño: QDialog frameless translúcido con un spinner Unicode que rota
vía QTimer (sin assets). Se ve más cuidado que un QProgressDialog genérico
y combina con el estilo oscuro de la app.

Implementación segura:
- Padre Qt real (MainLogin), no None. Así cuando el widget de login se
  destruye, el overlay se limpia solo -- sin riesgo de C++ deleted.
- Sin setModal(True) ni accept(): no estamos en un exec_() loop. Los
  inputs del padre se deshabilitan manualmente, no necesitamos modal.
- close_busy usa close() + deleteLater(), no accept() (que es para
  loops modales y al usarlo sin contexto ha dado segfault en X11)."""
# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QVBoxLayout


_SPINNER_FRAMES = ("⏳", "◐", "◓", "◑", "◒", "◓", "◑", "◒")
_SPINNER_INTERVAL_MS = 90


class LoginBusyDialog(QDialog):
    """Mini diálogo frameless con spinner Unicode. Padre = MainLogin."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Sin modal: los inputs del padre se bloquean por setEnabled(False),
        # no necesitamos un event loop modal -- y accept() sin exec_() es
        # una fuente típica de segfault en X11/Wayland.

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

        # Tamaño cómodo del diálogo independiente del tamaño del parent
        # (MainLogin es 400x90 fijo; el diálogo se posiciona manual encima).
        self.resize(260, 110)
        if parent is not None:
            target = parent.mapToGlobal(parent.rect().center())
            self.move(target - self.rect().center())

    def _tick(self) -> None:
        self._idx = (self._idx + 1) % len(_SPINNER_FRAMES)
        self._spinner.setText(_SPINNER_FRAMES[self._idx])

    def close_busy(self) -> None:
        """Para el timer, cierra el diálogo y libera. NO usar close() directo."""
        self._timer.stop()
        self.close()
        self.deleteLater()
