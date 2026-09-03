# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Otoscopia                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.helpers import foto_otoscopia

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

        layout = QHBoxLayout(self)
        self.lbl_od = self._build_slot()
        self.lbl_oi = self._build_slot()
        layout.addLayout(self._build_columna("Oído derecho (OD)", self.lbl_od))
        layout.addLayout(self._build_columna("Oído izquierdo (OI)", self.lbl_oi))

        self.la_super(thr)

    def _build_columna(self, titulo, label):
        col = QVBoxLayout()
        titulo_lbl = QLabel(f"<b>{titulo}</b>")
        titulo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(titulo_lbl)
        col.addWidget(label)
        return col

    def _build_slot(self):
        lbl = QLabel(SIN_IMAGEN_TEXTO)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setMinimumSize(220, 220)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("border: 1px solid #ccc; border-radius: 6px; color: #888; background: #fafafa;")
        return lbl

    def la_super(self, data, appointment_id=None):
        """Hidrata (o deshidrata, data=None) el módulo con el caso actual --
        mismo patrón que Acumetria.la_super(), llamado por
        MainWindow._hydrate_modules() cada vez que cambia el caso activo."""
        self.data = data
        self.appointment_id = appointment_id
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
                lbl.setPixmap(pix.scaled(
                    lbl.width() or 220, lbl.height() or 220,
                    Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
                ))
            else:
                lbl.setText(SIN_IMAGEN_TEXTO)
