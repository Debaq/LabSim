import weakref

from core.base import context
from core import tema, tiempos
from PySide6.QtCore import Qt, QEvent, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QMdiArea, QWidget
from core.UI.Ui_frameSubMdi import Ui_Form as UI_frameSubMdi


class MoveWin():
    """Arrastre de la subventana desde su barra.

    Guarda la ventana con weakref: la barra guarda estos métodos, y con una
    referencia fuerte quedaba el ciclo barra → MoveWin → FrameSubMdi →
    barra, que mantenía vivo todo el módulo (gráficos incluidos) hasta la
    próxima pasada del GC después de cerrarlo."""

    def __init__(self, window):
        self._window = weakref.ref(window)
        self.move_flag = False
        self.move_position = None

    def _sub(self):
        window = self._window()
        return None if window is None else window.parent()

    def press_window(self, _event):
        sub = self._sub()
        if sub is None:
            return
        if _event.buttons() == Qt.MouseButton.LeftButton:
            self.move_flag = True
            self.move_position = _event.globalPosition().toPoint() - sub.pos()
            self._window().setCursor(Qt.CursorShape.ClosedHandCursor)
            _event.accept()

    def move_window(self, _event):
        # Se mira el botón de verdad: si se perdió el release (un diálogo
        # modal en medio del arrastre), no se arrastra con otro botón.
        if not (self.move_flag and _event.buttons() & Qt.MouseButton.LeftButton):
            return
        sub = self._sub()
        if sub is None:
            return
        new_pos = _event.globalPosition().toPoint() - self.move_position
        mdi_area = sub.mdiArea()
        if mdi_area is not None:
            viewport = mdi_area.viewport()
            max_x = max(viewport.width() - sub.width(), 0)
            max_y = max(viewport.height() - sub.height(), 0)
            new_pos.setX(min(max(new_pos.x(), 0), max_x))
            new_pos.setY(min(max(new_pos.y(), 0), max_y))
        sub.move(new_pos)
        _event.accept()

    def release_window(self, _event):
        self.move_flag = False
        window = self._window()
        if window is not None:
            window.setCursor(Qt.CursorShape.ArrowCursor)




class FrameSubMdi(QWidget, UI_frameSubMdi):
    """Crea las subventanas dentro del mdi

    Args:
        QWidget ([type]): clase Qwidget
        UI_frameSubMdi ([type]): clase Ui del Mdi
    """
    # Se emite cuando la subventana se muestra/esconde (el hide() de la
    # QMdiSubWindow llega al widget como QHideEvent). La usan main.py, para
    # los botones que solo aplican con cierto modulo abierto, y MdiArea,
    # para avisar que cambiaron las ventanas.
    visibility_changed = Signal(bool)

    def __init__(self, ui_ui, expand=False):
        #super(FrameSubMdi, self).__init__()
        super().__init__()
        self.setupUi(self)
        # Un píxel libre a los lados y abajo para el borde del QSS
        # (FrameSubMdi en dark.qss): sin él el contenido lo tapaba y la
        # subventana quedaba sin línea inferior, fundida con el lienzo.
        self.verticalLayout_2.setContentsMargins(1, 0, 1, 1)
        if expand:
            # El spacer de abajo del .ui es Expanding y se reparte el alto
            # sobrante con el contenido: con stretch 1 el contenido se lo
            # lleva entero (texto que ocupa toda la subventana).
            self.verticalLayout_2.setStretchFactor(self.layout_content, 1)
            # El espaciador (40 px de mínimo) ya no hace falta y dejaba una
            # franja vacía abajo.
            self.verticalLayout_2.takeAt(self.verticalLayout_2.count() - 1)
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
        sub = self.parent()
        if sub is not None:
            sub.hide()

    def showEvent(self, event):
        tiempos.marca(f"mostrar {type(self.obj).__name__}")
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)



class MdiArea(QMdiArea):
    # Se abrió, cerró o cambió de foco alguna subventana. La usa main.py
    # para el nombre de la ventana activa y su ✕ en la barra de arriba.
    ventanas_cambiaron = Signal()

    # Logo de marca de agua, en px.
    _LADO_MARCA = 200

    def __init__(self):
        super().__init__()
        self._aviso_pendiente = False
        self.setDocumentMode(True)
        self.setBackground(QColor(tema.LIENZO_APP))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Se carga y escala una vez: el viewport se pinta en cada arrastre.
        self._marca = QPixmap(context.get_resource("img/LogoBN.png"))
        if not self._marca.isNull():
            self._marca = self._marca.scaled(
                self._LADO_MARCA, self._LADO_MARCA,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
        # Al clickear un modulo full Qt lo trae al frente y taparia a los
        # modulos normales abiertos encima: se los vuelve a subir.
        self.subWindowActivated.connect(self._keep_full_below)
        self.subWindowActivated.connect(self._avisar_cambio)
        # Esconder una que no es la activa no pasa por subWindowActivated:
        # se escucha la señal visibility_changed del FrameSubMdi (su
        # showEvent/hideEvent). NINGÚN eventFilter en Python: ni sobrescrito
        # en QMdiArea (b7aabcaf, tickets 35, 36, 43 del 2026-11-05) ni como
        # filtro aparte sobre las subventanas (ab6c94dc). Cada evento de la
        # subventana pasaba por Python, y si se destruía sin deleteLater
        # (al salir, al borrar el MDI) PySide volvía a armar envolturas de
        # objetos a medio borrar.

    def addSubWindow(self, sub, *args):
        sub = super().addSubWindow(sub, *args)
        frame = sub.widget() if sub is not None else None
        if isinstance(frame, FrameSubMdi) and not getattr(frame, "_avisa_al_mdi", False):
            # El receptor es el MDI: Qt corta la conexión si muere
            # cualquiera de los dos.
            frame.visibility_changed.connect(self._avisar_cambio)
            frame._avisa_al_mdi = True
        return sub

    def removeSubWindow(self, widget):
        super().removeSubWindow(widget)
        self._avisar_cambio()

    def _avisar_cambio(self, *_):
        """Un solo aviso por vuelta del loop: abrir un módulo full esconde
        al otro y activa el nuevo, todo de una."""
        if self._aviso_pendiente:
            return
        self._aviso_pendiente = True

        def avisar():
            self._aviso_pendiente = False
            self.ventanas_cambiaron.emit()
        # Con el MDI de contexto: si muere antes, Qt no llama.
        QTimer.singleShot(0, self, avisar)

    def _keep_full_below(self, sub):
        if sub is None:
            return
        # Diferido: Qt sube la subventana activada despues de emitir la
        # señal, asi que reordenar aca mismo no sirve.
        QTimer.singleShot(0, self, self._restack_full)

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
        if event.type() == QEvent.Type.Paint and not self._marca.isNull():
            painter = QPainter(self.viewport())
            # Marca de agua: sobre el lienzo claro, el logo pleno pesa demasiado.
            painter.setOpacity(0.18)
            x = (self.viewport().width() - self._marca.width()) // 2
            y = (self.viewport().height() - self._marca.height()) // 2
            painter.drawPixmap(x, y, self._marca)
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
            if sub.isHidden():
                continue
            if is_full_window(sub):
                fit_full_window(sub)
            else:
                self.keep_inside(sub)

    def keep_inside(self, sub):
        """Deja la subventana entera dentro del viewport: si es más grande
        la achica (el contenido se recorta, pero la barra con la ✕ queda a
        la vista) y si quedó corrida la vuelve a meter. Sin esto, en
        pantallas chicas o al achicar la ventana principal había módulos
        que quedaban con la barra afuera y no se podían cerrar ni mover.

        Lo que se achicó vuelve a su tamaño (y a su mínimo) cuando el MDI
        crece lo suficiente, salvo que el usuario la haya redimensionado
        entretanto."""
        viewport = self.viewport().size()
        vw, vh = viewport.width(), viewport.height()
        if vw <= 0 or vh <= 0:
            return
        self._restaurar_tamano(sub, vw, vh)
        w, h = sub.width(), sub.height()
        if w > vw or h > vh:
            pedido = getattr(sub, "_tam_pedido", None)
            if pedido is None:
                pedido = (sub.minimumSize(), sub.size())
            w, h = min(w, vw), min(h, vh)
            sub.setMinimumSize(min(sub.minimumWidth(), w), min(sub.minimumHeight(), h))
            sub.resize(w, h)
            sub._tam_pedido = (pedido[0], pedido[1], sub.size())
        # max(…, 0) al final: si no logró achicarse, que quede a la vista
        # la esquina de arriba a la izquierda, donde está la barra.
        x = max(min(sub.x(), vw - sub.width()), 0)
        y = max(min(sub.y(), vh - sub.height()), 0)
        if (x, y) != (sub.x(), sub.y()):
            sub.move(x, y)

    @staticmethod
    def _restaurar_tamano(sub, vw, vh):
        pedido = getattr(sub, "_tam_pedido", None)
        if pedido is None:
            return
        minimo, tam, achicado = pedido
        if sub.size() != achicado:
            # La redimensionó el usuario: se respeta, solo vuelve el mínimo
            # hasta donde lo permite su tamaño actual.
            sub.setMinimumSize(min(minimo.width(), sub.width()),
                               min(minimo.height(), sub.height()))
            del sub._tam_pedido
            return
        if tam.width() <= vw and tam.height() <= vh:
            sub.setMinimumSize(minimo)
            sub.resize(tam)
            del sub._tam_pedido
