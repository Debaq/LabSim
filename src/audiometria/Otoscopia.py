# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                       VER. 0.1 - Otoscopia                    #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
import math

from audiometria.OtoscopiaInforme import InformeOtoscopia
from audiometria.cabeza_examen import CabezaOtoscopia
from audiometria.comandos_voz import SILENCIO
from audiometria.frases_habladas import FrasesHabladas
from backend.log_queue import get_log_queue
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
LADO_TEXTO = {"od": "derecho", "oi": "izquierdo"}
TIRON_MIN_CM = 0.5          # menos que esto no es un tirón
EDAD_TIRON_ABAJO = 3        # años: menor que esto, el pabellón va abajo y atrás
EDAD_ESPECULO_ADULTO = 6    # años: menor que esto el espéculo de adulto no entra
CAMPO_SIN_TRACCION = 0.5    # sin enderezar el conducto se ve la mitad del campo
# Las herramientas de la cabeza, como las de los electrodos
HERRAMIENTAS = (("girar", "Girar"), ("traccion", "Traccionar"), ("otoscopia", "Otoscopio"))
PISTAS = {
    "girar": "Arrastra para girar la cabeza.",
    "traccion": "Arrastra desde la oreja hacia donde quieras tirar del pabellón.",
    "otoscopia": "Lleva el mouse al conducto: lo que se ve aparece ahí. Muévelo un poco para recorrer.",
}

# Lo que el evaluador le dice al paciente (audiometria/frases_habladas.py;
# audio en resources/audio/comandos_ot/, scripts/voces_comandos.py --ot).
# Sin preguntas por ahora: el caso no dice si duele o molesta (solo trae
# las fotos), y el paciente no contesta lo que el caso no sabe.
GRUPOS = (
    ("PREPARAR", (
        ("Explicar el examen", "explicar_otoscopia"),
    )),
    ("INSTRUCCIONES", (
        ("Quédese quieto", "quedese_quieto"),
        ("Incline la cabeza", "incline_cabeza"),
        ("Avíseme si le molesta", "avise_si_molesta"),
    )),
)

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
QPushButton[segmento="true"] {{ padding: 4px 0px; }}
QPushButton[herramienta="true"] {{ padding: 5px 0px; font-weight: 600; }}
QPushButton[herramienta="true"]:checked {{ background: {tema.ACENTO}; border-color: {tema.ACENTO}; color: white; }}
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
        self.log_queue = get_log_queue()
        self._fotos = {"od": None, "oi": None}   # QPixmap por oído
        self._tiron = None     # el pabellón traccionado: {'oido', 'arriba', 'atras', 'correcto'}
        self._dentro = None    # 'od'/'oi': el otoscopio metido en ese conducto

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
        """Por áreas, como el posicionamiento de electrodos: las frases a la
        izquierda; al centro la cabeza (el mouse es el otoscopio,
        cabeza_examen.CabezaOtoscopia) con sus herramientas, sus vistas y la
        pista; a la derecha el panel con el espéculo y el pabellón."""
        tab = QWidget()
        fila = QHBoxLayout(tab)
        fila.setContentsMargins(0, 10, 0, 0)
        fila.setSpacing(10)
        self.frases = FrasesHabladas(GRUPOS, {}, "comandos_ot")
        self.frases.setFixedWidth(250)
        self.frases.btn_checked.connect(self._frase)
        fila.addWidget(self.frases)

        lienzo = QFrame()
        lienzo.setProperty("card", "true")
        col = QVBoxLayout(lienzo)
        col.setContentsMargins(8, 8, 8, 8)
        self.cabeza = CabezaOtoscopia(self.vista)
        self.cabeza.miro.connect(self._miro)
        self.cabeza.salio.connect(self._salio)
        self.cabeza.traccionado.connect(self._traccionar)
        col.addWidget(self.cabeza, 1)
        herramientas = QHBoxLayout()
        herramientas.setSpacing(4)
        grupo = QButtonGroup(self)
        self.botones_herramienta = {}
        for clave, nombre in HERRAMIENTAS:
            b = QPushButton(nombre)
            b.setCheckable(True)
            b.setProperty("herramienta", "true")
            b.clicked.connect(lambda _c=False, k=clave: self._elegir_herramienta(k))
            grupo.addButton(b)
            herramientas.addWidget(b, 1)
            self.botones_herramienta[clave] = b
        col.addLayout(herramientas)
        vistas = QHBoxLayout()
        vistas.setSpacing(4)
        for nombre, accion in (("Frente", lambda: self.cabeza.mirar(0, 0)),
                               ("Oído derecho", lambda: self.cabeza.mirar_oido("od")),
                               ("Oído izquierdo", lambda: self.cabeza.mirar_oido("oi"))):
            b = QPushButton(nombre)
            b.setProperty("segmento", "true")
            b.clicked.connect(accion)
            vistas.addWidget(b, 1)
        col.addLayout(vistas)
        self.pista = QLabel()
        self.pista.setProperty("role", "hint")
        self.pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.pista)
        fila.addWidget(lienzo, 1)

        panel = QFrame()
        panel.setProperty("card", "true")
        panel.setFixedWidth(262)
        pcol = QVBoxLayout(panel)
        pcol.setContentsMargins(12, 10, 12, 12)
        pcol.setSpacing(6)
        pcol.addWidget(self._seccion("ESPÉCULO"))
        pcol.addLayout(self._build_conos())
        pcol.addSpacing(4)
        pcol.addWidget(self._seccion("PABELLÓN"))
        self.lbl_pabellon = QLabel("Suelto.")
        self.lbl_pabellon.setWordWrap(True)
        pcol.addWidget(self.lbl_pabellon)
        self.btn_soltar = QPushButton(" Soltar el pabellón")
        self.btn_soltar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_SUAVE, tam=14))
        self.btn_soltar.clicked.connect(self._soltar_pabellon)
        pcol.addWidget(self.btn_soltar)
        pcol.addSpacing(4)
        pcol.addWidget(self._seccion("OTOSCOPIO"))
        self.lbl_otoscopio = QLabel("Fuera del oído.")
        self.lbl_otoscopio.setWordWrap(True)
        pcol.addWidget(self.lbl_otoscopio)
        pcol.addStretch(1)
        fila.addWidget(panel)
        self._elegir_herramienta("girar")
        return tab

    @staticmethod
    def _seccion(texto):
        lbl = QLabel(texto)
        lbl.setProperty("role", "seccion")
        return lbl

    def _build_conos(self):
        """El espéculo: el pediátrico deja ver la mitad del disco y el de
        adulto el disco entero (en un niño chico no entra)."""
        fila = QHBoxLayout()
        fila.setSpacing(4)
        self.grupo_conos = QButtonGroup(self)
        self.grupo_conos.setExclusive(True)
        self.btn_cono_pediatrico = QPushButton("Pediátrico")
        self.btn_cono_adulto = QPushButton("Adulto")
        for btn, clave in ((self.btn_cono_pediatrico, "pediatrico"), (self.btn_cono_adulto, "adulto")):
            btn.setCheckable(True)
            btn.setProperty("segmento", "true")
            self.grupo_conos.addButton(btn)
            btn.clicked.connect(lambda _checked=False, k=clave: self._cambiar_especulo(k))
            fila.addWidget(btn, 1)
        self.btn_cono_pediatrico.setChecked(True)
        return fila

    def _elegir_herramienta(self, clave):
        self.botones_herramienta[clave].setChecked(True)
        self.cabeza.poner_herramienta(clave)
        self.pista.setText(PISTAS[clave])

    # ------------------------------------------------------------ técnica
    def _edad(self):
        try:
            return float((self.data or {}).get("edad") or 0)
        except (TypeError, ValueError):
            return 0.0

    def _especulo(self):
        return "adulto" if self.btn_cono_adulto.isChecked() else "pediatrico"

    def _tiron_correcto(self, arriba, atras):
        """Adulto y niño grande: arriba y atrás. Menor de 3 años: abajo y
        atrás (el conducto todavía es casi todo cartilaginoso)."""
        if atras < TIRON_MIN_CM:
            return False
        if self._edad() < EDAD_TIRON_ABAJO:
            return arriba <= -TIRON_MIN_CM
        return arriba >= TIRON_MIN_CM

    def _traccionar(self, oido, arriba, atras):
        if math.hypot(arriba, atras) < TIRON_MIN_CM:
            return   # fue un clic en la oreja, no un tirón
        correcto = self._tiron_correcto(arriba, atras)
        self._tiron = {"oido": oido, "arriba": arriba, "atras": atras, "correcto": correcto}
        self.cabeza.poner_tiron((oido, arriba, atras))
        self._log("ot_traccion", oido=oido, arriba_cm=arriba, atras_cm=atras, correcto=correcto,
                  edad=self._edad())
        self._pintar_estado()

    def _soltar_pabellon(self):
        if self._tiron is None:
            return
        self._log("ot_soltar", oido=self._tiron["oido"])
        self._tiron = None
        self.cabeza.poner_tiron(None)
        self._pintar_estado()

    def _pintar_estado(self):
        """Lo que se está haciendo, en el panel (sin decir si está bien)."""
        if self._tiron is None:
            self.lbl_pabellon.setText("Suelto.")
        else:
            t = self._tiron
            hacia = ("arriba" if t["arriba"] > 0 else "abajo") + (" y atrás" if t["atras"] > 0 else " y adelante")
            self.lbl_pabellon.setText(f"Tirando del pabellón {LADO_TEXTO[t['oido']]} hacia {hacia}.")
        self.btn_soltar.setEnabled(self._tiron is not None)
        self.lbl_otoscopio.setText("Fuera del oído." if self._dentro is None
                                   else f"En el conducto {LADO_TEXTO[self._dentro]}.")

    def _cambiar_especulo(self, clave):
        self._log("ot_especulo", especulo=clave)
        self.cabeza.update()

    def _no_entra(self):
        return self._especulo() == "adulto" and self._edad() < EDAD_ESPECULO_ADULTO

    def vista(self, oido):
        """Lo que se ve por el otoscopio en ese conducto (lo dibuja
        CabezaOtoscopia): la foto del caso con el campo del espéculo; sin el
        pabellón bien traccionado el conducto no se endereza y la pared tapa
        casi todo. Sin foto, el otoscopio está sin batería."""
        if self._no_entra():
            return {"texto": "El espéculo de adulto no entra en este conducto."}
        foto = self._fotos.get(oido)
        if foto is None:
            return {"texto": SIN_IMAGEN_TEXTO}
        cono = _OtoscopioVisor.CONO_ADULTO if self._especulo() == "adulto" else _OtoscopioVisor.CONO_PEDIATRICO
        tiron = self._tiron if self._tiron and self._tiron["oido"] == oido else None
        return {"foto": foto, "cono": cono, "adulto": self._especulo() == "adulto",
                "tapado": not (tiron and tiron["correcto"])}

    def _miro(self, oido):
        """El otoscopio entró al conducto (el mouse pasó por él)."""
        self._dentro = oido
        self._pintar_estado()
        tiron = self._tiron if self._tiron and self._tiron["oido"] == oido else None
        if self._no_entra():
            self._log("ot_especulo_grande", oido=oido, edad=self._edad())
            return
        self._log("ot_otoscopio", oido=oido, especulo=self._especulo(), traccion=bool(tiron),
                  traccion_correcta=bool(tiron and tiron["correcto"]), edad=self._edad(),
                  hay_foto=self._fotos.get(oido) is not None)

    def _salio(self):
        self._dentro = None
        self._pintar_estado()

    def _build_slot(self):
        return _OtoscopioVisor()

    def _log(self, action, **payload):
        """Encola una acción del alumno con el otoscopio (prefijo ot_, ver
        backend/log_queue.py), como Acumetria._log."""
        case_id = self.data.get("id") if self.data else None
        if case_id is not None:
            payload.setdefault("case_id", case_id)
        payload.setdefault("appointment_id", self.appointment_id)
        payload.setdefault("con_paciente", case_id is not None)
        self.log_queue.push(action, payload)

    def _frase(self, clave):
        if clave != SILENCIO:
            self._log("ot_instruccion", clave=clave)

    def callar(self):
        self.frases.callar()

    def la_super(self, data, appointment_id=None):
        """Hidrata (o deshidrata, data=None) el módulo con el caso actual --
        mismo patrón que Acumetria.la_super(), llamado por
        MainWindow._hydrate_modules() cada vez que cambia el caso activo."""
        self.data = data
        self.appointment_id = appointment_id
        self.frases.callar()
        self.frases.silencio()
        # El informe es de ESTE paciente: al cambiar de caso (o al
        # deshidratar) se limpia, si no el alumno arranca el siguiente con
        # los cuadrantes del anterior marcados.
        self.informe.limpiar()
        self._fotos = {"od": None, "oi": None}
        self._tiron = None
        self._dentro = None
        self.cabeza.poner_tiron(None)
        self.cabeza.mirar_oido("od")
        self._pintar_estado()

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
        for oido, data in (("od", od_bytes), ("oi", oi_bytes)):
            pix = QPixmap()
            if data and pix.loadFromData(data):
                self._fotos[oido] = pix
            else:
                if data:
                    # Llegó la foto pero Qt no la sabe leer (p. ej. WebP sin
                    # el plugin qwebp en el build, ver LabSim.spec).
                    print(f"Otoscopia: no se pudo decodificar la imagen ({len(data)} bytes, {data[:12]!r})")
                self._fotos[oido] = None
        self.cabeza.update()

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
