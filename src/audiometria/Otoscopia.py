# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Otoscopia                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from audiometria.OtoscopiaInforme import InformeOtoscopia
from backend.client import BackendClient
from core.base import context
from core.helpers import Preferences, foto_otoscopia
from PySide6.QtCore import QRect, Qt, QThread, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QRegion
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

SIN_IMAGEN_TEXTO = "Otoscopio sin batería"

# Qué fase de otoscopia le corresponde ver a cada alumno según su propio
# avance (derivación + aprobación docente) con este paciente todavía no
# está implementado -- ver TODO.md. Por ahora se muestra siempre la fase 1
# (índice 0), la misma para todos.
FASE_FIJA = 0


class _OtoscopiaFetchThread(QThread):
    """Trae las imágenes OD/OI del caso fuera del hilo de UI -- mismo
    patrón que _AvatarFetchThread en agenda/ChatPaciente.py. Emite None por
    lado si no hay imagen subida o no hay conexión (no es una falla)."""
    listo = Signal(object, object)

    def __init__(self, case_id, parent=None):
        super().__init__(parent)
        self._case_id = case_id

    def run(self):
        od = foto_otoscopia(self._case_id, "od", FASE_FIJA)
        oi = foto_otoscopia(self._case_id, "oi", FASE_FIJA)
        self.listo.emit(od, oi)


class _OtoscopioVisor(QWidget):
    """Simula el ocular de un otoscopio real: la foto queda tapada por una
    máscara negra excepto un círculo que sigue al mouse -- a diferencia de
    un QLabel con la foto entera visible, el alumno solo ve de a un
    fragmento circular por vez, como al mirar por el instrumento real."""

    RADIO_PEDIATRICO = 42  # px del círculo "visible" alrededor del cursor
    RADIO_ADULTO = RADIO_PEDIATRICO * 2  # cono adulto: el doble de diámetro

    def __init__(self, parent=None):
        super().__init__(parent)
        self._radio = self.RADIO_PEDIATRICO
        self._pixmap = None
        self._texto = SIN_IMAGEN_TEXTO
        self._scaled = None
        self._scaled_size = None
        self._mouse_pos = None
        self.setMinimumSize(220, 220)
        self.setMouseTracking(True)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self._texto = None
        self._scaled = None
        self.update()

    def setRadio(self, radio):
        """Cambia el diámetro del campo visible (tamaño del cono)."""
        if radio == self._radio:
            return
        self._radio = radio
        self.update()

    def setText(self, texto):
        self._pixmap = None
        self._texto = texto
        self.update()

    def mouseMoveEvent(self, event):
        self._mouse_pos = event.position().toPoint()
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._mouse_pos = None
        self.update()
        super().leaveEvent(event)

    def _pixmap_escalado(self):
        # Cachea el escalado -- si no, cada mouseMoveEvent reescalaría la
        # imagen entera (SmoothTransformation no es gratis).
        size = self.size()
        if self._scaled is None or self._scaled_size != size:
            self._scaled = self._pixmap.scaled(
                size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
            )
            self._scaled_size = size
        return self._scaled

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        if self._pixmap is None:
            painter.fillRect(rect, QColor("#fafafa"))
            painter.setPen(QPen(QColor("#cccccc")))
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
            painter.setPen(QColor("#888888"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self._texto or "")
            painter.end()
            return

        # Fondo negro (no el gris claro del estado vacío) -- así las franjas
        # de letterbox (imagen con proporción distinta al widget) quedan del
        # mismo negro que la máscara, en vez de un marco claro alrededor.
        painter.fillRect(rect, QColor(0, 0, 0))
        painter.setPen(QPen(QColor("#444444")))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        scaled = self._pixmap_escalado()
        img_rect = QRect(0, 0, scaled.width(), scaled.height())
        img_rect.moveCenter(rect.center())
        painter.drawPixmap(img_rect.topLeft(), scaled)

        # Máscara: negro en todo salvo el círculo alrededor del mouse (si el
        # mouse no está encima, queda completamente tapado).
        mascara = QRegion(rect)
        if self._mouse_pos is not None:
            r = self._radio
            circulo = QRect(self._mouse_pos.x() - r, self._mouse_pos.y() - r, r * 2, r * 2)
            mascara -= QRegion(circulo, QRegion.RegionType.Ellipse)
        painter.setClipRegion(mascara)
        painter.fillRect(rect, QColor(0, 0, 0))
        painter.end()


class Otoscopia(QWidget):
    """Otoscopia: muestra la imagen de otoscopia de OD y OI del caso, una
    al lado de la otra (ver OtoscopiaPhoto.php / ficha Otoscopia en
    case_create.php). Sin imagen subida, o mientras no hay caso cargado,
    cada lado queda con el aviso "Otoscopio sin batería"."""

    def __init__(self, thr=None):
        super().__init__()
        self.data = None
        self.appointment_id = None
        self._fetch_thread = None
        self._case_id_pedido = None

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab_otoscopio(), "Otoscopio")
        self.informe = InformeOtoscopia()
        self.informe.guardar_pedido.connect(self._guardar_informe)
        self.tabs.addTab(self.informe, "Informe")
        layout.addWidget(self.tabs)

        self.la_super(thr)

    def _build_tab_otoscopio(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        fila_visores = QHBoxLayout()
        self.lbl_od = self._build_slot()
        self.lbl_oi = self._build_slot()
        fila_visores.addLayout(self._build_columna("Oído derecho (OD)", self.lbl_od))
        fila_visores.addLayout(self._build_columna("Oído izquierdo (OI)", self.lbl_oi))
        layout.addLayout(fila_visores)
        layout.addLayout(self._build_conos())
        return tab

    def _build_conos(self):
        """Elección del espéculo: el pediátrico deja el campo visible chico
        (lo de siempre) y el de adulto lo duplica en diámetro."""
        fila = QHBoxLayout()
        self.grupo_conos = QButtonGroup(self)
        self.grupo_conos.setExclusive(True)
        self.btn_cono_pediatrico = QPushButton("Cono pediátrico")
        self.btn_cono_adulto = QPushButton("Cono adulto")
        for btn, radio in (
            (self.btn_cono_pediatrico, _OtoscopioVisor.RADIO_PEDIATRICO),
            (self.btn_cono_adulto, _OtoscopioVisor.RADIO_ADULTO),
        ):
            btn.setCheckable(True)
            self.grupo_conos.addButton(btn)
            btn.clicked.connect(lambda _checked=False, r=radio: self._set_cono(r))
        self.btn_cono_pediatrico.setChecked(True)
        fila.addStretch(1)
        fila.addWidget(self.btn_cono_pediatrico)
        fila.addWidget(self.btn_cono_adulto)
        fila.addStretch(1)
        return fila

    def _set_cono(self, radio):
        self.lbl_od.setRadio(radio)
        self.lbl_oi.setRadio(radio)

    def _build_columna(self, titulo, label):
        col = QVBoxLayout()
        titulo_lbl = QLabel(f"<b>{titulo}</b>")
        titulo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(titulo_lbl)
        col.addWidget(label)
        return col

    def _build_slot(self):
        return _OtoscopioVisor()

    def la_super(self, data, appointment_id=None):
        """Hidrata (o deshidrata, data=None) el módulo con el caso actual --
        mismo patrón que Acumetria.la_super(), llamado por
        MainWindow._hydrate_modules() cada vez que cambia el caso activo."""
        self.data = data
        self.appointment_id = appointment_id
        # El informe es de ESTE paciente: al cambiar de caso (o al
        # deshidratar) se limpia, si no el alumno arranca el siguiente con
        # los cuadrantes del anterior marcados.
        self.informe.limpiar()
        self.lbl_od.setText(SIN_IMAGEN_TEXTO)
        self.lbl_oi.setText(SIN_IMAGEN_TEXTO)

        case_id = data.get("id") if data else None
        self._case_id_pedido = str(case_id) if case_id is not None else None
        if self._case_id_pedido is None:
            return

        self._fetch_thread = _OtoscopiaFetchThread(self._case_id_pedido, parent=self)
        self._fetch_thread.listo.connect(
            lambda od, oi, cid=self._case_id_pedido: self._on_fotos_listas(cid, od, oi)
        )
        self._fetch_thread.start()

    def _on_fotos_listas(self, case_id_solicitado, od_bytes, oi_bytes):
        if case_id_solicitado != self._case_id_pedido:
            return  # el alumno ya cambió de paciente (o se deshidrató) mientras se pedía
        for lbl, data in ((self.lbl_od, od_bytes), (self.lbl_oi, oi_bytes)):
            if data:
                pix = QPixmap()
                pix.loadFromData(data)
                lbl.setPixmap(pix)
            else:
                lbl.setText(SIN_IMAGEN_TEXTO)

    def _guardar_informe(self):
        """Botón "Guardar informe": misma subida que al cerrar la atención,
        pero acá el alumno ve qué pasó (el cierre es best-effort silencioso)."""
        if self.appointment_id is None:
            self.informe.set_estado("Sin una atención abierta no hay dónde guardar el informe.")
            return
        ok, detalle = self._subir_informe()
        self.informe.set_estado("Informe guardado." if ok else f"No se pudo guardar: {detalle}")

    def submit_report(self):
        """Sube el informe al cerrar la atención -- lo llama main.py::
        _cerrar_atencion_real ANTES de deshidratar (mismo patrón que
        AbrMainWindow.submit_report). Best-effort: sin conexión falla en
        silencio, el cierre de la atención no se rompe por esto."""
        if self.appointment_id is None or not self.informe.tiene_algo():
            return
        ok, detalle = self._subir_informe()
        if not ok:
            print(f"Otoscopia: no se pudo subir el informe: {detalle}")

    def _subir_informe(self):
        """(ok, detalle). Sube el informe tipo 'OTOSCOPIA' -- sin imágenes:
        lo que el alumno informa son las marcas por cuadrante, la foto del
        caso ya la tiene el backend (ver OtoscopiaPhoto.php)."""
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return False, "la cita no tiene un id válido"
        client = BackendClient(
            Preferences().get("BACKEND_URL"), context.get_resource("json/session.json")
        )
        if not client.is_logged_in():
            return False, "no hay sesión iniciada con el servidor"
        try:
            client.upload_report(appointment_id, "OTOSCOPIA", self.informe.to_dict(), {})
        except Exception as exc:
            return False, str(exc)
        return True, ""
