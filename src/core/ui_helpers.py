"""
ui_helpers.py
show_hide(obj:any, pos:int): muestra o esconde la subventana que
                            se encuentre en obj segpun su indice
_flags(obj:any): banderas para la sub-ventana
togle_max_min(obj:object, minimum:tuple=(800,600)): maximisa la
                 ventana y restringue su tamaño
MoveWindow(parent:object): mueve la ventana a la
                            posicion que se le pasa
"""
# pylint: disable=no-name-in-module

from PySide6.QtCore import Qt,QSize,QRectF
from PySide6.QtGui import QMouseEvent, QIcon, QPixmap, QPainter, QPen, QColor
from PySide6.QtWidgets import QPushButton, QLayout, QFrame
from PySide6.QtWidgets import QMdiSubWindow
from core.h_win import FrameSubMdi, MdiArea
from core import inbox

def titlebar_icon(kind: str, size: int = 14, color: str = "#ffffff") -> QIcon:
    """
    Dibuja un icono vectorial simple (min/max/restore/close) para los
    botones de la barra de título, en vez de usar los iconos nativos del
    estilo del sistema (quedan con el color y forma del tema del SO, no
    calzan con la barra oscura de LabSim).

    Args:
        kind: "min", "max", "restore" o "close"
        size: lado del icono en px
        color: color del trazo
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.3)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    margin = size * 0.28

    if kind == "min":
        y = size - margin
        painter.drawLine(int(margin), int(y), int(size - margin), int(y))
    elif kind == "max":
        painter.drawRect(QRectF(margin, margin, size - 2 * margin, size - 2 * margin))
    elif kind == "restore":
        offset = size * 0.18
        front = size - 2 * margin - offset
        # cuadro de adelante (completo)
        painter.drawRect(QRectF(margin, margin + offset, front, front))
        # cuadro de atrás: solo el borde superior y derecho, para no
        # dibujar encima del cuadro de adelante
        bx, by = margin + offset, margin
        painter.drawLine(int(bx), int(by), int(bx + front), int(by))
        painter.drawLine(int(bx + front), int(by), int(bx + front), int(by + front))
    elif kind == "close":
        painter.drawLine(int(margin), int(margin), int(size - margin), int(size - margin))
        painter.drawLine(int(size - margin), int(margin), int(margin), int(size - margin))
    painter.end()
    return QIcon(pixmap)

def show_hide(obj:any, pos:int):
    """
    Muestra o esconde la subventana que se encuentre en obj según su indice

    Args:
        pos(int): indice de la subventana
    """
    if obj.get(pos).isHidden():
        obj.get(pos).show()
    else:
        obj.get(pos).hide()

def _flags(obj:any) -> None:
    """
    Banderas para la sub-ventana
    Args:
        var(QMdiSubWindow): sub-ventana
    """
    obj.setWindowFlags(Qt.WindowType.Window |
                        Qt.WindowType.CustomizeWindowHint |
                        Qt.WindowType.WindowTitleHint |
                        Qt.WindowType.FramelessWindowHint|
                        Qt.WindowType.WindowCloseButtonHint |
                        Qt.WindowType.WindowStaysOnTopHint)

def toggle_max_min(obj:object, minimum:tuple=(800,600)) -> None:
    """Permite Maximisar o minimizar la ventana"""
    if obj.isMaximized():
        obj.showNormal()
        obj.resize(minimum[0], minimum[1])
    else:
        obj.showMaximized()

class MoveWindow():
    """
    Clase para el movimiento de la ventana"""

    def __init__(self, parent) -> None:
        self.parent = parent

    def set_movewindow(self) -> None:
        """Permite obtener el evento de movimiento de la ventana
        y llama a la funcion press_window"""
        self.parent.showMaximized()
        self.parent.barra.mousePressEvent = self.press_window

    def press_window(self, event : QMouseEvent) -> None:
        """Delega el arrastre de la ventana al window manager: este se
        encarga de restaurar (si estaba maximizada) y seguir el cursor,
        igual que una barra de titulo nativa"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            window = self.parent.windowHandle()
            if window is not None:
                window.startSystemMove()
            event.accept()

    def toggle_max_min(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.parent.resize(800,600)
        else:
            self.parent.showMaximized()

class SubWindow():
    """
    Clase para la sub-ventana"""
    def __init__(self, app, modules, mdi_area) -> None:
        self.app = app
        self.modules = modules
        self.mdi_area = mdi_area

    def activate_subwindow(self, size:QSize, app:str, submdi: FrameSubMdi) -> None:
        """
        Activa la subventana que se le pasa por parametro según una lista
        previa en json que contiene la información basica de la ventana

        Json:
        {name:[active(bool), nombre(str), pos_z(int), fix(tuple), size(tuple), position(tuple)]}

        Args:
            app(str): nombre de la aplicacion
            submdi(FrameSubMdi): objeto de la subventana
        """
        width = size().width()
        height = size().height()
        _, name, pos_z, fix, size, _ = self.app[app]
        width = width/2
        height = height/2
        w_submdi=size[0]/2
        h_submdi=size[1]/2
        pos = [width-w_submdi, height-h_submdi]
        self.create_sub_window(submdi, name, pos_z=pos_z,
                               fix=fix, size=size,position=pos)

    def create_sub_window(self,widg:FrameSubMdi, name:str, pos_z:int,
                          fix:tuple=(True, True),size:tuple=(740,560),
                          position:tuple=(0,0)) -> None:
        """
        Crea una subventana y la agrega a la memoria self.modules

        Args:
            widg(FrameSubMdi): objeto de la subventana
            name(str): nombre de la subventana
            pos_z(int): posicion de la subventana en la ventana
            fix(tuple): indica si la subventana se puede mover o no
            size(tuple): tamaño de la subventana
            position(tuple): posicion de la subventana
        """
        if self.modules.is_full(pos_z):
            show_hide(self.modules, pos_z)
        else:
            open_count = len(self.mdi_area.subWindowList())
            sub = QMdiSubWindow()
            sub.setWidget(widg)
            widg.lbl_title.setText(name)
            self.mdi_area.addSubWindow(sub)
            if position != [0,0]:
                pos_x,pos_y = int(position[0]), int(position[1])
                if open_count > 0:
                    step = 40
                    viewport = self.mdi_area.viewport().size()
                    max_x = max(viewport.width() - size[0], 0)
                    max_y = max(viewport.height() - size[1], 0)
                    offset = (open_count * step) % (max(max_x, max_y, step) + step)
                    pos_x = min(pos_x + offset, max_x)
                    pos_y = min(pos_y + offset, max_y + 220)
                sub.move(pos_x,pos_y-220)
            _flags(sub)
            if fix[0]:
                sub.setMaximumSize(size[0], size[1])
            if fix[1]:
                sub.setMinimumSize(size[0], size[1])
                sub.resize(size[0], size[1])
            sub.show()
            list_wi = self.mdi_area.subWindowList()
            self.modules.set(pos_z, list_wi[-1])



class ToolBar(SubWindow):
    """
    Clase para la barra de herramientas"""
    tuple_qlayout = (QLayout, QLayout)
    def __init__(self, sender, box:dict, apps:dict,
                 layout:tuple_qlayout, frame:QFrame,
                 modules:dict, mdi_area:MdiArea, size:QSize,
                 subw) -> None:
        """Inicia toolbar
        Args:        
            box (dict): diccionario con la informacion de la barra de herramientas
            layout (QLayout): layout de la barra de herramientas
            frame (QFrame): frame de la barra de herramientas
        """
        SubWindow.__init__(self, apps, modules, mdi_area)

        self.sender = sender
        self.boxs = box
        self.layouts = layout
        self.frame = frame
        self.apps = apps
        self.size = size
        self.subw = subw

     ## Funciones para el toolbar
    def _clear_layout(self, layout):
        """Elimina todos los widgets contenidos en un layout"""
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def btns_seccion(self):
        self._clear_layout(self.layouts[0])
        self._clear_layout(self.layouts[1])
        active = str()
        for iter_btn, i in enumerate(self.boxs):
            if self.boxs[i][0]:
                btn = QPushButton()
                btn.setObjectName(i)
                btn.setText(self.boxs[i][2])
                btn.clicked.connect(self.changeArea)
                btn.setMinimumHeight(30)
                btn.setCheckable(True)
                btn.setAutoExclusive(True)
                self.layouts[0].addWidget(btn)
                if iter_btn == 0:
                    active = i
        btn_selec = self.frame.findChild(QPushButton,active)
        btn_selec.setChecked(True)
        self.chargeBtnsArea(active)
        #self.parent.btns_actions()

    def changeArea(self):
        for i in reversed(range( self.layouts[1].count())):
            self.layouts[1].itemAt(i).widget().deleteLater()
        # el botón de bandeja se destruye arriba junto al resto de la
        # sección y solo se recrea si la nueva sección tiene "AGENDA" (ver
        # chargeBtnsArea) -- invalidar la ref ahora evita que
        # inbox.actualizar_badge() la use ya destruida en el próximo sync.
        self.btn_bandeja_oirs = None
        widget = self.sender()
        obj_name = widget.objectName()
        self.chargeBtnsArea(obj_name)

    def chargeBtnsArea(self, area):
        for i in self.boxs[area][1]:
            btn = QPushButton(f'{i}')
            btn.setObjectName(f"btn_{i}")
            btn.clicked.connect(self.activate_soft)
            tooltip = self.apps[i][1]
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            self.layouts[1].addWidget(btn)
            state = self.apps[i][5] == "development"
            btn.setDisabled(state)
            btn.setMaximumHeight(25)
            btn.setMinimumWidth(btn.sizeHint().width())

        # Bandeja de entrada: al lado del botón de Agenda (misma sección,
        # "Sala de Espera"), no dentro de la propia Agenda -- visible para
        # cualquier rol logueado (alumno o docente/admin, este último para
        # poder probarla sin necesitar un usuario alumno aparte). Se recrea
        # cada vez que chargeBtnsArea corre (cambio de sección) -- ver
        # core.inbox.crear_boton().
        if "AGENDA" in self.boxs[area][1] and self.data_login:
            inbox.crear_boton(self, self.layouts[1])

    def activate_soft(self) -> None:
        """activa la ventana con el mismo nombre del boton que envia la señal"""
        widget = self.sender()
        btn_name = widget.objectName()
        _, obj_name = btn_name.split("_")
        obj_name = obj_name.upper()
        self.activate_subwindow(self.size, obj_name, self.subw[obj_name])
    
    def activate_soft_(self, name) -> None:
        """activa la ventana con el mismo nombre del boton que envia la señal"""
        
        if name is not None:
            #widget = self.sender()
            #btn_name = widget.objectName()
            #_, obj_name = btn_name.split("_")
            #obj_name = obj_name.upper()
            obj_name = name
            self.activate_subwindow(self.size, obj_name, self.subw[obj_name])
        
    def activate_auto(self, name) -> None:
        obj_name = name
        self.activate_subwindow(self.size, obj_name, self.subw[obj_name])

    def close_sub_window(self, name) -> None:
        """Oculta la subventana con el nombre indicado sin destruir su contenido interior"""
        _, _, pos_z, *_ = self.apps[name]
        if self.modules.is_full(pos_z):
            self.modules.get(pos_z).hide()


    def changeStateBtnAreas(self, frame:QFrame, b):
        box = self.boxs[b]
        for area in box[1]:
            for i in self.frameAction.findChildren(QPushButton):
                if i.objectName() == area and self.apps[area][5] != "development":
                    i.setDisabled(False)