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
from core import hilos
from core import iconos, tema
from core.helpers import Preferences, foto_otoscopia
from core.report_autosave import subir_ahora
from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

SIN_IMAGEN_TEXTO = "Otoscopio sin batería"

# Lo que el visor pinta fuera de la foto y como máscara: negro con un dejo
# del tinte de la app, para que no sea un agujero en la tarjeta.
NEGRO_VISOR = QColor("#0E0A0D")
RADIO_VISOR = 8

# Reglas propias de la ventana (el resto sale de core/tema.py).
EXTRA_QSS = f"""
QTabWidget::pane {{ border: none; background: transparent; top: 0px; }}
QTabBar::tab {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 16px;
    margin-right: 4px;
    font-size: 9pt;
    font-weight: 600;
    color: {tema.TEXTO_TENUE};
}}
QTabBar::tab:selected {{ color: {tema.ACENTO}; border-bottom-color: {tema.ACENTO}; }}
QTabBar::tab:hover:!selected {{ color: {tema.TEXTO_SUAVE}; }}
QCheckBox {{ spacing: 6px; color: {tema.TEXTO}; }}
"""

# Qué fase de otoscopia le corresponde ver a cada alumno según su propio
# avance (derivación + aprobación docente) con este paciente todavía no
# está implementado -- ver TODO.md. Por ahora se muestra siempre la fase 1
# (índice 0), la misma para todos.
FASE_FIJA = 0


def _traer_fotos(case_id):
    """Imágenes OD/OI del caso (bytes o None por lado: sin imagen subida o
    sin conexión no es una falla). Corre con hilos.en_fondo."""
    return foto_otoscopia(case_id, "od", FASE_FIJA), foto_otoscopia(case_id, "oi", FASE_FIJA)


class _OtoscopioVisor(QWidget):
    """Simula el ocular de un otoscopio real: la foto queda tapada por una
    máscara negra excepto un círculo que sigue al mouse -- a diferencia de
    un QLabel con la foto entera visible, el alumno solo ve de a un
    fragmento circular por vez, como al mirar por el instrumento real."""

    # Fracción del lado menor del visor que abarca el círculo "visible"
    # alrededor del cursor -- no un radio en px: con el visor estirado a
    # toda la ventana, 42 px fijos (lo que medía sobre el visor de 220 px
    # de antes) dejaban ver una porción cada vez más chica de la foto
    # cuanto más grande la ventana. 0.19 mantiene esa misma proporción.
    CONO_PEDIATRICO = 0.19
    CONO_ADULTO = CONO_PEDIATRICO * 2  # el doble de diámetro

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cono = self.CONO_PEDIATRICO
        self._pixmap = None
        self._texto = SIN_IMAGEN_TEXTO
        self._scaled = None
        self._scaled_size = None
        self._mouse_pos = None
        self.setMinimumSize(260, 260)
        # Expanding: el visor tiene que repartirse todo el alto/ancho libre
        # de la pestaña -- con el tamaño Preferred de un QWidget pelado las
        # fotos quedaban chicas aunque sobrara ventana.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self._texto = None
        self._scaled = None
        self.update()

    def setCono(self, fraccion):
        """Cambia el diámetro del campo visible (tamaño del cono)."""
        if fraccion == self._cono:
            return
        self._cono = fraccion
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

        borde = QPainterPath()
        borde.addRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), RADIO_VISOR, RADIO_VISOR)

        if self._pixmap is None:
            painter.fillPath(borde, QColor(tema.TARJETA_ALT))
            painter.setPen(QPen(QColor(tema.BORDE), 1))
            painter.drawPath(borde)
            icono = iconos.pixmap("otoscopio", tema.TEXTO_TENUE, 44)
            ancho_icono = icono.width() / icono.devicePixelRatio()
            alto_icono = icono.height() / icono.devicePixelRatio()
            painter.drawPixmap(int(rect.center().x() - ancho_icono / 2),
                               int(rect.center().y() - alto_icono - 4), icono)
            painter.setPen(QColor(tema.TEXTO_TENUE))
            painter.drawText(rect.adjusted(12, int(rect.height() / 2 + 6), -12, 0),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                             self._texto or "")
            painter.end()
            return

        # Todo lo que sigue recortado a las esquinas redondeadas. Fondo
        # oscuro (no el claro del estado vacío) -- así las franjas de
        # letterbox (imagen con proporción distinta al widget) quedan del
        # mismo color que la máscara, en vez de un marco claro alrededor.
        painter.setClipPath(borde)
        painter.fillRect(rect, NEGRO_VISOR)

        scaled = self._pixmap_escalado()
        img_rect = QRect(0, 0, scaled.width(), scaled.height())
        img_rect.moveCenter(rect.center())
        painter.drawPixmap(img_rect.topLeft(), scaled)

        # Luz del otoscopio: sin mouse encima queda todo tapado; con él, un
        # círculo de luz cálida cuyo borde se difumina hacia el negro (la luz
        # real no corta en seco).
        if self._mouse_pos is None:
            painter.fillRect(rect, NEGRO_VISOR)
        else:
            # 1.15: el borde difuso se come parte del radio; así lo nítido queda como antes.
            r = min(rect.width(), rect.height()) * self._cono * 1.15
            centro = QPointF(self._mouse_pos)
            tinte = QRadialGradient(centro, r)
            tinte.setColorAt(0.0, QColor(255, 214, 120, 80))
            tinte.setColorAt(0.8, QColor(255, 190, 80, 45))
            tinte.setColorAt(1.0, QColor(255, 190, 80, 0))
            painter.fillRect(rect, tinte)
            mascara = QRadialGradient(centro, r)
            negro = NEGRO_VISOR
            mascara.setColorAt(0.0, QColor(negro.red(), negro.green(), negro.blue(), 0))
            mascara.setColorAt(0.55, QColor(negro.red(), negro.green(), negro.blue(), 0))
            mascara.setColorAt(0.8, QColor(negro.red(), negro.green(), negro.blue(), 150))
            mascara.setColorAt(1.0, QColor(negro.red(), negro.green(), negro.blue(), 255))
            painter.fillRect(rect, mascara)
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

        tema.aplicar_estilo(self, EXTRA_QSS)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab_otoscopio(), iconos.icono("otoscopio", tema.TEXTO_TENUE, 16), "Otoscopio")
        self.informe = InformeOtoscopia()
        # Lo actualiza el autoguardado (core/report_autosave.py).
        self.estado_informe = self.informe.estado
        self.tabs.addTab(self.informe, iconos.icono("evolucion", tema.TEXTO_TENUE, 16), "Informe")
        self.tabs.currentChanged.connect(self._iconos_pestanas)
        self._iconos_pestanas(0)
        layout.addWidget(self.tabs)

        self.la_super(thr)

    def _iconos_pestanas(self, activa):
        """El icono de la pestaña elegida va en el acento, el resto tenue."""
        for i, nombre in enumerate(("otoscopio", "evolucion")):
            color = tema.ACENTO if i == activa else tema.TEXTO_TENUE
            self.tabs.setTabIcon(i, iconos.icono(nombre, color, 16))

    def _build_tab_otoscopio(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        fila_visores = QHBoxLayout()
        fila_visores.setSpacing(10)
        self.lbl_od = self._build_slot()
        self.lbl_oi = self._build_slot()
        fila_visores.addWidget(self._build_tarjeta("OD", "Oído derecho", self.lbl_od), 1)
        fila_visores.addWidget(self._build_tarjeta("OI", "Oído izquierdo", self.lbl_oi), 1)
        layout.addLayout(fila_visores, 1)
        layout.addLayout(self._build_conos())
        return tab

    def _build_conos(self):
        """Elección del espéculo: el pediátrico deja el campo visible chico
        (lo de siempre) y el de adulto lo duplica en diámetro."""
        fila = QHBoxLayout()
        fila.setSpacing(6)
        self.grupo_conos = QButtonGroup(self)
        self.grupo_conos.setExclusive(True)
        self.btn_cono_pediatrico = QPushButton("Cono pediátrico")
        self.btn_cono_adulto = QPushButton("Cono adulto")
        pista = QLabel("Mueve el mouse sobre la imagen: el espéculo deja ver un círculo a la vez.")
        pista.setProperty("role", "hint")
        pista.setWordWrap(True)
        lbl_cono = QLabel("ESPÉCULO")
        lbl_cono.setProperty("role", "seccion")
        for btn, fraccion in (
            (self.btn_cono_pediatrico, _OtoscopioVisor.CONO_PEDIATRICO),
            (self.btn_cono_adulto, _OtoscopioVisor.CONO_ADULTO),
        ):
            btn.setCheckable(True)
            self.grupo_conos.addButton(btn)
            btn.clicked.connect(lambda _checked=False, f=fraccion: self._set_cono(f))
        self.btn_cono_pediatrico.setChecked(True)
        fila.addWidget(pista, 1)
        fila.addWidget(lbl_cono)
        fila.addWidget(self.btn_cono_pediatrico)
        fila.addWidget(self.btn_cono_adulto)
        return fila

    def _set_cono(self, fraccion):
        self.lbl_od.setCono(fraccion)
        self.lbl_oi.setCono(fraccion)

    def _build_tarjeta(self, lado, titulo, visor):
        """Tarjeta de un oído: píldora OD/OI + título y el visor."""
        tarjeta = QFrame()
        tarjeta.setProperty("card", "true")
        col = QVBoxLayout(tarjeta)
        col.setContentsMargins(12, 10, 12, 12)
        col.setSpacing(8)
        cabecera = QHBoxLayout()
        pastilla = QLabel(lado)
        tema.pastilla_lado(pastilla, lado)
        titulo_lbl = QLabel(titulo)
        titulo_lbl.setProperty("role", "titulo")
        cabecera.addWidget(pastilla)
        cabecera.addWidget(titulo_lbl)
        cabecera.addStretch(1)
        col.addLayout(cabecera)
        col.addWidget(visor, 1)
        return tarjeta

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

        self._fetch_thread = hilos.en_fondo(
            _traer_fotos, self._case_id_pedido, dueno=self, nombre="otoscopia",
            listo=lambda fotos, cid=self._case_id_pedido: self._on_fotos_listas(cid, *fotos))

    def _on_fotos_listas(self, case_id_solicitado, od_bytes, oi_bytes):
        if case_id_solicitado != self._case_id_pedido:
            return  # el alumno ya cambió de paciente (o se deshidrató) mientras se pedía
        for lbl, data in ((self.lbl_od, od_bytes), (self.lbl_oi, oi_bytes)):
            pix = QPixmap()
            if data and pix.loadFromData(data):
                lbl.setPixmap(pix)
            else:
                if data:
                    # Llegó la foto pero Qt no la sabe leer (p. ej. WebP sin
                    # el plugin qwebp en el build, ver LabSim.spec).
                    print(f"Otoscopia: no se pudo decodificar la imagen ({len(data)} bytes, {data[:12]!r})")
                lbl.setText(SIN_IMAGEN_TEXTO)

    def submit_report(self):
        """Sube el informe al cerrar la atención -- lo llama main.py::
        _cerrar_atencion_real ANTES de deshidratar (mismo patrón que
        AbrMainWindow.submit_report). Best-effort: sin conexión falla en
        silencio, el cierre de la atención no se rompe por esto."""
        if self.report_job() is None:
            return True
        ok, detalle = self._subir_informe()
        if not ok:
            print(f"Otoscopia: no se pudo subir el informe: {detalle}")
        return ok

    def report_job(self):
        """El informe tal como se sube (ver core/report_autosave.py), o None.
        Sin imágenes: la foto del caso ya la tiene el backend."""
        if self.appointment_id is None or not self.informe.tiene_algo():
            return None
        try:
            appointment_id = int(self.appointment_id)
        except (TypeError, ValueError):
            return None
        return {"appointment_id": appointment_id, "tipo": "OTOSCOPIA",
                "data": self.informe.to_dict(), "images": None}

    def restore_report(self, data):
        """Retomar la atención: vuelve el informe ya guardado (ver
        core/report_autosave.py), si todavía no se marcó nada."""
        if self.appointment_id is None or self.informe.tiene_algo():
            return False
        self.informe.from_dict(data or {})
        return self.informe.tiene_algo()

    def _subir_informe(self):
        """(ok, detalle). Sube el informe tipo 'OTOSCOPIA' -- sin imágenes:
        lo que el alumno informa son las marcas por cuadrante, la foto del
        caso ya la tiene el backend (ver OtoscopiaPhoto.php)."""
        job = self.report_job()
        if job is None:
            return False, "la cita no tiene un id válido"
        client = BackendClient(
            Preferences().get("BACKEND_URL"), context.get_resource("json/session.json")
        )
        # Por subir_ahora, como los demás: queda respaldado en el equipo
        # aunque no haya red (ver core/respaldo_informes.py).
        return subir_ahora(job, client)
