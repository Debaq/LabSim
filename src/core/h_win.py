from core.base import context
from PySide6.QtCore import Qt, QEvent, QTimer, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QMdiArea, QWidget
from core.UI.Ui_frameSubMdi import Ui_Form as UI_frameSubMdi


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
            new_pos = _event.globalPosition().toPoint() - self.move_position
            mdi_area = self.i.mdiArea()
            if mdi_area is not None:
                viewport = mdi_area.viewport()
                max_x = max(viewport.width() - self.i.width(), 0)
                max_y = max(viewport.height() - self.i.height(), 0)
                new_pos.setX(min(max(new_pos.x(), 0), max_x))
                new_pos.setY(min(max(new_pos.y(), 0), max_y))
            self.i.move(new_pos)
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
    # Se emite cuando la subventana se muestra/esconde (el hide() de la
    # QMdiSubWindow llega al widget como QHideEvent). La usa main.py para
    # mostrar los botones que solo aplican con cierto modulo abierto.
    visibility_changed = Signal(bool)

    def __init__(self, ui_ui):
        #super(FrameSubMdi, self).__init__()
        super().__init__()
        self.setupUi(self)
        # QWidget plano no pinta border/background de QSS sin esto (a
        # diferencia de QFrame, que lo hace solo) -- necesario para el
        # borde delgado que marca el límite de cada subventana MDI.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.obj = ui_ui
        self.layout_content.addWidget(self.obj)
        movewin = MoveWin(self)
        self.barra.mousePressEvent = movewin.press_window
        self.barra.mouseMoveEvent = movewin.move_window
        self.barra.mouseReleaseEvent = movewin.release_window
        self.btn_close.clicked.connect(self.hide_window)

    def hide_window(self):
        """Esconde la subventana (QMdiSubWindow) sin destruirla"""
        self.parent().hide()

    def showEvent(self, event):
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)



class MdiArea(QMdiArea):
    def __init__(self):
        super().__init__()
        self.setDocumentMode(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Al clickear un modulo full Qt lo trae al frente y taparia a los
        # modulos normales abiertos encima: se los vuelve a subir.
        self.subWindowActivated.connect(self._keep_full_below)

    def _keep_full_below(self, sub):
        if sub is None:
            return
        # Diferido: Qt sube la subventana activada despues de emitir la
        # señal, asi que reordenar aca mismo no sirve.
        QTimer.singleShot(0, self._restack_full)

    def _restack_full(self):
        """Deja los modulos full por debajo de todos los normales, sin
        alterar el orden entre estos (la activa queda al frente)."""
        from core.ui_helpers import is_full_window
        stack = [s for s in self.subWindowList(QMdiArea.WindowOrder.StackingOrder)
                 if not s.isHidden()]
        if not any(is_full_window(s) for s in stack):
            return
        normals = [s for s in stack if not is_full_window(s)]
        active = self.activeSubWindow()
        if active in normals:
            normals.remove(active)
            normals.append(active)
        for win in normals:
            win.raise_()

    def viewportEvent(self, event):
        result = super().viewportEvent(event)
        if event.type() == QEvent.Type.Paint:
            painter = QPainter(self.viewport())
            width = self.viewport().width()
            height = self.viewport().height()
            img = QPixmap(context.get_resource("img/LogoBN.png"))
            img_x = width/2 - 200/2
            img_y = height/2 - 200/2
            painter.drawPixmap(int(img_x), int(img_y), 200, 200, img)
            painter.end()
        return result

    def resizeEvent(self, event):
        """Reajusta los modulos a pantalla completa (ABR/VEMP/EOAS): su
        geometria se maneja a mano (ver ui_helpers.fit_full_window), asi
        que no siguen solos el resize del MDI."""
        super().resizeEvent(event)
        self._refit_full()

    def _refit_full(self):
        from core.ui_helpers import fit_full_window, is_full_window
        for sub in self.subWindowList():
            if is_full_window(sub) and not sub.isHidden():
                fit_full_window(sub)
