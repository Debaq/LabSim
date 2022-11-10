from base import context
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QMdiArea, QWidget, QMenu
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



class MdiArea(QMdiArea):
    def __init__(self):
        super().__init__()
        self.mousePressEvent = self.move_window
        self.documentMode = True
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.currentSubWindow() is None:

            painter = QPainter(self.viewport())
            width = event.rect().width()
            height = event.rect().height()
            img = QPixmap(context.get_resource("img/LogoBN.png"))
            img_x = width/2 - 200/2
            img_y = height/2 - 200/2
            painter.drawPixmap(int(img_x), int(img_y), 200, 200, img)
            painter.end()

    def move_window(self, event):
        if event.buttons() == Qt.MouseButton.RightButton:
            context_menu = QMenu(self)
            ordenar = context_menu.addMenu("Ordenar")
            ordenar.addAction("Cascada", self.cascadeSubWindows)
            ordenar.addAction("Azulejos", self.tileSubWindows)
            ordenar.addAction("Cerrar todo", self.closeAll)
            context_menu.exec(self.mapToGlobal(event.pos()))

    def closeAll(self):
        i = self.parent().parent().parent()
        try:
            for j in i.Modules.length(True):
                if i.Modules.get(j) != None:
                    i.Modules.get(j).hide()
        except AttributeError:
            print("No existe modulos")
