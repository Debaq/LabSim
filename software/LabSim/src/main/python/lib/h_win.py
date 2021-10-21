from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from UI.Ui_frameSubMdi import Ui_Form as UI_frameSubMdi

class MoveWin():
    def __init__(self, window):
        self.window = window
        self.move_flag = False
        self.i = None
        self.move_flag = None
        self.move_position = None

    def press_window(self, _event):
        self.i = self.window.parent()
        if _event.buttons() == Qt.MouseButton.LeftButton:
            self.move_flag = True
            self.move_position = _event.globalPosition().toPoint() - self.i.pos()
            self.window.setCursor(Qt.CursorShape.ClosedHandCursor)
            _event.accept()

    def move_window(self, _event):
        if Qt.MouseButton.LeftButton and self.move_flag:
            self.i.move(_event.globalPosition().toPoint() - self.move_position)
            _event.accept()

    def release_window(self, _event):
        self.move_flag = False
        self.window.setCursor(Qt.CursorShape.ArrowCursor)




class FrameSubMdi(QWidget, UI_frameSubMdi):
    """Crea las subventanas dentro del mdi

    Args:
        QWidget ([type]): clase Qwidget
        UI_frameSubMdi ([type]): clase Ui del Mdi
    """
    def __init__(self, ui_ui):
        #super(FrameSubMdi, self).__init__()
        super().__init__()
        self.setupUi(self)
        self.ui_ui = ui_ui
        self.layout_content.addWidget(self.ui_ui)
        movewin = MoveWin(self)
        self.barra.mousePressEvent = movewin.press_window
        self.barra.mouseMoveEvent = movewin.move_window
        self.barra.mouseReleaseEvent = movewin.release_window
