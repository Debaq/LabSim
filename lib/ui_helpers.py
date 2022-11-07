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

from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QPushButton, QLayout, QFrame
from PySide6.QtWidgets import QMdiSubWindow
from lib.h_win import FrameSubMdi, MdiArea

def show_hide(obj:any, pos:int):
    """
    Muestra o esconde la subventana que se encuentre en obj segpun su indice

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
        y llama a la funcion move_window"""
        self.parent.showMaximized()
        self.parent.setMouseTracking(True)
        self.parent.barra.mouseMoveEvent = self.move_window

    def move_window(self, event : QMouseEvent) -> None:
        """permite mover la ventana con la barra de titulo"""
        move = False
        if self.parent.isMaximized(): #Not maximized
            self.parent.toggle_max_min()
            move=True
        if not self.parent.isMaximized(): #Not maximized
            move = True
        if move and event.buttons() == Qt.MouseButton.LeftButton:
            #Move window
            g_xy = event.globalPosition().toPoint()
            self.parent.move(g_xy)
            event.accept()

class SubWindow():
    """
    Clase para la sub-ventana"""
    def __init__(self, app, modules, mdi_area) -> None:
        self.app = app
        self.modules = modules
        self.mdi_area = mdi_area

    def activate_subwindow(self, size:QSize, app: str, submdi: FrameSubMdi) -> None:
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
            sub = QMdiSubWindow()
            sub.setWidget(widg)
            widg.lbl_title.setText(name)
            self.mdi_area.addSubWindow(sub)
            if position != [0,0]:
                pos_x,pos_y = int(position[0]), int(position[1])
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
    def btns_seccion(self):
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
                if iter_btn == 1:
                    active = i
        btn_selec = self.frame.findChild(QPushButton,active)
        btn_selec.setChecked(True)
        self.chargeBtnsArea(active)
        #self.parent.btns_actions()

    def changeArea(self):
        for i in reversed(range( self.layouts[1].count())):
            self.layouts[1].itemAt(i).widget().deleteLater()
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
            btn.setMaximumWidth(40)

    def activate_soft(self) -> None:
        """activa la ventana con el mismo nombre del boton que envia la señal"""
        widget = self.sender()
        btn_name = widget.objectName()
        _, obj_name = btn_name.split("_")
        obj_name = obj_name.upper()
        self.activate_subwindow(self.size, obj_name, self.subw[obj_name])
    
    def activate_auto(self, name) -> None:
        obj_name = name
        self.activate_subwindow(self.size, obj_name, self.subw[obj_name])
              

    def changeStateBtnAreas(self, frame:QFrame, b):
        box = self.boxs[b]
        for area in box[1]:
            for i in self.frameAction.findChildren(QPushButton):
                if i.objectName() == area and self.apps[area][5] != "development":
                    i.setDisabled(False)