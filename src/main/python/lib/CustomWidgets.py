from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QMdiArea, QMenu, QWidget
from PySide6.QtCore import Qt, QCoreApplication, QTranslator
from UI.UI_frameSubMdi import UI_frameSubMdi
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

from fbs_runtime.application_context.PySide6 import ApplicationContext



class MoveWin():
    """Clase para gestionar el movimiento de una ventana al arrastrar con el ratón."""
    
    def __init__(self, window):
        self.window = window
        self.move_flag = False
        self.move_position = None

    def press_window(self, _event):
        if _event.buttons() == Qt.MouseButton.LQWidgeteftButton:
            self.move_flag = True
            self.move_position = _event.globalPosition().toPoint() - self.window.parent().pos()
            self.window.setCursor(Qt.CursorShape.ClosedHandCursor)
            _event.accept()

    def move_window(self, _event):
        if Qt.MouseButton.LeftButton and self.move_flag:
            self.window.parent().move(_event.globalPosition().toPoint() - self.move_position)
            _event.accept()

    def release_window(self, _event):
        self.move_flag = False
        self.window.setCursor(Qt.CursorShape.ArrowCursor)




class CustomMdiSubWindow(QWidget, UI_frameSubMdi):
    """Crea las subventanas dentro del mdi."""
    
    def __init__(self, ui_input):
        super().__init__()
        self.setupUi(self)
        
        # Verificar si el input es una ruta de archivo (string) o un widget
        if isinstance(ui_input, str):
            # Suponemos que es una ruta de archivo .ui
            loader = QUiLoader()
            file = QFile(ui_input)
            file.open(QFile.ReadOnly)
            self.ui_ui = loader.load(file, self)
            file.close()
        else:
            # Suponemos que es un widget
            self.ui_ui = ui_input
            # Verificar si setupUi está presente y llamarlo si es necesario
            if hasattr(self.ui_ui, 'setupUi'):
                self.ui_ui.setupUi()

        self.layout_content.addWidget(self.ui_ui)
        self.movewin = MoveWin(self)
        self.barra.mousePressEvent = self.movewin.press_window
        self.barra.mouseMoveEvent = self.movewin.move_window
        self.barra.mouseReleaseEvent = self.movewin.release_window


class CustomMdiArea(QMdiArea):
    """
    Clase MdiArea que extiende QMdiArea para proporcionar funcionalidades personalizadas.
    
    Métodos:
        paintEvent: Dibuja el logo en el centro si no hay subventanas activas.
        move_window: Muestra un menú contextual para gestionar las subventanas.
        closeAll: Cierra todas las subventanas.
    """
    
    def __init__(self, logo = None):
        super().__init__()
        self.logo = logo
        self.documentMode = True
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.img = QPixmap(logo)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.currentSubWindow() is None:
            painter = QPainter(self.viewport())
            width = event.rect().width()
            height = event.rect().height()
            img_x = width/2 - 200/2
            img_y = height/2 - 200/2
            painter.drawPixmap(int(img_x), int(img_y), 200, 200, self.img)
            painter.end()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.MouseButton.RightButton:
            context_menu = QMenu(self)
            ordenar = context_menu.addMenu(QCoreApplication.translate("MdiArea", "Ordenar"))
            ordenar.addAction(QCoreApplication.translate("MdiArea", "Cascada"), self.cascadeSubWindows)
            ordenar.addAction(QCoreApplication.translate("MdiArea", "Azulejos"), self.tileSubWindows)
            ordenar.addAction(QCoreApplication.translate("MdiArea", "Cerrar todo"), self.closeAll)
            context_menu.exec(self.mapToGlobal(event.pos()))

    def closeAll(self):
        parent_widget = self.parent()
        try:
            for j in parent_widget.Modules.length(True):
                if parent_widget.Modules.get(j) is not None:
                    parent_widget.Modules.get(j).hide()
        except AttributeError:
            print(QCoreApplication.translate("MdiArea", "No existen módulos"))

# Estrategia de traducción:
# 1. Utilizar QTranslator para cargar archivos de traducción (.qm) generados por Qt Linguist.
# 2. Usar QCoreApplication.translate() para traducir cadenas en tiempo de ejecución.
# 3. Cambiar el idioma en tiempo de ejecución actualizando el QTranslator y llamando a QCoreApplication::installTranslator().
