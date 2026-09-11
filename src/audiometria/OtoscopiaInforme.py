# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#              VER. 0.1 - Informe de otoscopia                  #
#               CREADOR : NICOLÁS QUEZADA QUEZADA               #
#                                                               #
#################################################################
"""Informe de otoscopia por cuadrantes: el alumno marca en el esquema de
la membrana timpánica qué vio y dónde, igual que en OtoReport (proyecto
aparte, ver src/components/otoscopy/ ahí). Las claves de cuadrantes y
hallazgos son las mismas de OtoReport a propósito -- así un informe de
LabSim se puede leer/importar con las mismas herramientas.

Lo marcado se sube como informe tipo 'OTOSCOPIA' (report_upload.php) para
que el docente lo revise desde admin/chat_detail.php.
"""
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# (clave, etiqueta, color) -- mismas claves que FindingType de OtoReport.
HALLAZGOS = [
    ("retraction", "Retracción", "#f59e0b"),
    ("perforation", "Perforación", "#ef4444"),
    ("effusion", "Efusión", "#3b82f6"),
    ("tympanosclerosis", "Timpanoesclerosis", "#8b5cf6"),
    ("cholesteatoma", "Colesteatoma", "#f97316"),
    ("inflammation", "Inflamación", "#dc2626"),
    ("tube", "Tubo", "#10b981"),
    ("myringitis", "Miringitis", "#ec4899"),
]
COLOR_HALLAZGO = {clave: color for clave, _, color in HALLAZGOS}
ETIQUETA_HALLAZGO = {clave: etiqueta for clave, etiqueta, _ in HALLAZGOS}

# Claves de QuadrantName (OtoReport). El orden es el de dibujo/lectura.
CUADRANTES = [
    ("anterior_superior", "AS"),
    ("anterior_inferior", "AI"),
    ("posterior_inferior", "PI"),
    ("posterior_superior", "PS"),
    ("pars_flaccida", "PF"),
]
ETIQUETA_CUADRANTE = {
    "anterior_superior": "Anterosuperior",
    "anterior_inferior": "Anteroinferior",
    "posterior_inferior": "Posteroinferior",
    "posterior_superior": "Posterosuperior",
    "pars_flaccida": "Pars flácida",
}

# Conducto auditivo externo: casillas, no cuadrantes (el hallazgo del CAE
# no tiene localización en el esquema de la membrana). Claves de
# DEFAULT_EAR_FINDINGS en OtoReport.
CAE_CHECKS = [
    ("cae_normal", "Normal"),
    ("cae_cerumen", "Cerumen"),
    ("cae_edema", "Edema"),
    ("cae_otorrhea", "Otorrea"),
    ("cae_exostosis", "Exostosis"),
]


class _DiagramaTimpanico(QWidget):
    """Esquema clickeable de la membrana: 4 cuadrantes + pars flácida. Un
    hallazgo por cuadrante (marcar otro lo reemplaza, marcar el mismo lo
    borra) -- mismo comportamiento que TympanicDiagram de OtoReport."""

    cuadrante_click = Signal(str)

    def __init__(self, lado, parent=None):
        super().__init__(parent)
        self._es_derecho = lado == "od"
        self.marcas = {}  # cuadrante -> clave de hallazgo
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # -- geometría (todo derivado del lado menor: el esquema es cuadrado) --
    def _metricas(self):
        lado = min(self.width(), self.height())
        centro = QPoint(self.width() // 2, self.height() // 2)
        return lado, centro, lado * 0.38, lado * 0.46  # r_membrana, r_cae

    def _rect_pars_flaccida(self):
        lado, centro, r, _ = self._metricas()
        rx, ry = lado * 0.09, lado * 0.05
        cy = centro.y() - r + lado * 0.04
        return QRect(int(centro.x() - rx), int(cy - ry), int(rx * 2), int(ry * 2))

    def _cuadrante_en(self, pos):
        """Cuadrante bajo el punto, o None si el click cayó fuera de la
        membrana. Anterior queda a la derecha en OD y a la izquierda en OI
        (el alumno mira al paciente de frente)."""
        if self._rect_pars_flaccida().contains(pos):
            return "pars_flaccida"
        _, centro, r, _ = self._metricas()
        dx = pos.x() - centro.x()
        dy = pos.y() - centro.y()
        if dx * dx + dy * dy > r * r:
            return None
        es_anterior = (dx > 0) if self._es_derecho else (dx < 0)
        es_superior = dy < 0
        if es_anterior:
            return "anterior_superior" if es_superior else "anterior_inferior"
        return "posterior_superior" if es_superior else "posterior_inferior"

    def mousePressEvent(self, event):
        cuadrante = self._cuadrante_en(event.position().toPoint())
        if cuadrante:
            self.cuadrante_click.emit(cuadrante)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        lado, centro, r, r_cae = self._metricas()

        def rect_de(radio):
            return QRect(
                int(centro.x() - radio), int(centro.y() - radio), int(radio * 2), int(radio * 2)
            )

        # CAE y annulus (los mismos ocres de OtoReport, para que el alumno
        # reconozca el esquema entre las dos herramientas).
        painter.setPen(QPen(QColor("#d97706"), 1.5))
        painter.setBrush(QColor("#fef3c7"))
        painter.drawEllipse(rect_de(r_cae))
        painter.setPen(QPen(QColor("#92400e"), 2))
        painter.setBrush(QColor("#fde68a"))
        painter.drawEllipse(rect_de(r))

        # Relleno de los cuadrantes marcados (pie de 90° cada uno).
        for cuadrante, angulo in self._angulos_cuadrantes().items():
            clave = self.marcas.get(cuadrante)
            if not clave:
                continue
            color = QColor(COLOR_HALLAZGO.get(clave, "#888888"))
            color.setAlpha(150)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(rect_de(r), angulo * 16, 90 * 16)

        # Divisiones
        painter.setPen(QPen(QColor("#92400e"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(int(centro.x() - r), centro.y(), int(centro.x() + r), centro.y())
        painter.drawLine(centro.x(), int(centro.y() - r), centro.x(), int(centro.y() + r))

        # Pars flácida
        pf = self._rect_pars_flaccida()
        clave_pf = self.marcas.get("pars_flaccida")
        if clave_pf:
            color = QColor(COLOR_HALLAZGO.get(clave_pf, "#888888"))
            color.setAlpha(150)
            painter.setBrush(color)
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#92400e"), 1))
        painter.drawEllipse(pf)

        # Mango del martillo, umbo y cono luminoso (referencias anatómicas:
        # sin ellas el alumno no sabe para qué lado está mirando).
        painter.setPen(QPen(QColor("#78350f"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        y_umbo = int(centro.y() + lado * 0.05)
        painter.drawLine(centro.x(), int(centro.y() - r + lado * 0.075), centro.x(), y_umbo)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#78350f"))
        painter.drawEllipse(QPoint(centro.x(), y_umbo), int(lado * 0.015), int(lado * 0.015))
        signo = 1 if self._es_derecho else -1
        cono = [
            QPoint(int(centro.x() + signo * lado * 0.015), int(y_umbo + lado * 0.015)),
            QPoint(int(centro.x() + signo * lado * 0.175), int(y_umbo + lado * 0.175)),
            QPoint(int(centro.x() + signo * lado * 0.10), int(y_umbo + lado * 0.20)),
        ]
        painter.setPen(QPen(QColor("#eab308"), 1))
        painter.setBrush(QColor(254, 240, 138, 130))
        painter.drawPolygon(cono)

        # Siglas
        painter.setPen(QColor("#78350f"))
        signo_ant = 1 if self._es_derecho else -1
        dx = int(lado * 0.18)
        dy = int(lado * 0.14)
        for texto, x, y in (
            ("AS", centro.x() + signo_ant * dx, centro.y() - dy),
            ("AI", centro.x() + signo_ant * dx, centro.y() + dy),
            ("PS", centro.x() - signo_ant * dx, centro.y() - dy),
            ("PI", centro.x() - signo_ant * dx, centro.y() + dy),
            ("PF", centro.x(), int(centro.y() - r - lado * 0.02)),
        ):
            painter.drawText(QRect(x - 15, y - 8, 30, 16), Qt.AlignmentFlag.AlignCenter, texto)
        painter.end()

    def _angulos_cuadrantes(self):
        """Ángulo inicial (grados, antihorario desde las 3 en punto, como
        QPainter.drawPie) de cada cuadrante de la pars tensa."""
        if self._es_derecho:
            return {
                "anterior_superior": 0,
                "posterior_superior": 90,
                "posterior_inferior": 180,
                "anterior_inferior": 270,
            }
        return {
            "posterior_superior": 0,
            "anterior_superior": 90,
            "anterior_inferior": 180,
            "posterior_inferior": 270,
        }


class _PanelOido(QWidget):
    """Un oído del informe: esquema + paleta de hallazgos + CAE + notas."""

    def __init__(self, lado, titulo, parent=None):
        super().__init__(parent)
        self.lado = lado
        self._hallazgo_activo = None

        raiz = QVBoxLayout(self)
        lbl_titulo = QLabel(f"<b>{titulo}</b>")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        raiz.addWidget(lbl_titulo)

        self.diagrama = _DiagramaTimpanico(lado)
        self.diagrama.cuadrante_click.connect(self._marcar_cuadrante)
        raiz.addWidget(self.diagrama)

        raiz.addWidget(QLabel("Hallazgo a marcar en el cuadrante:"))
        raiz.addLayout(self._build_paleta())

        self.btn_limpiar = QPushButton("Limpiar marcas")
        self.btn_limpiar.clicked.connect(self.limpiar_marcas)
        raiz.addWidget(self.btn_limpiar)

        raiz.addWidget(QLabel("<b>Conducto auditivo externo</b>"))
        raiz.addLayout(self._build_cae())

        raiz.addWidget(QLabel("Observaciones:"))
        self.txt_observaciones = QTextEdit()
        self.txt_observaciones.setPlaceholderText("Lo que no entra en el esquema")
        self.txt_observaciones.setMaximumHeight(70)
        raiz.addWidget(self.txt_observaciones)

    def _build_paleta(self):
        # Sin QButtonGroup exclusivo: destildar el hallazgo activo deja el
        # modo "borrador" (click en un cuadrante marcado lo borra, ver
        # _marcar_cuadrante), y un grupo exclusivo no permite quedar sin
        # ninguno tildado.
        grid = QGridLayout()
        self.botones_hallazgo = {}
        for i, (clave, etiqueta, color) in enumerate(HALLAZGOS):
            btn = QPushButton(etiqueta)
            btn.setCheckable(True)
            btn.setStyleSheet(
                f"QPushButton {{ border: 1px solid {color}; padding: 3px; }}"
                f"QPushButton:checked {{ background-color: {color}; color: white; }}"
            )
            btn.clicked.connect(lambda checked, c=clave: self._set_hallazgo(c if checked else None))
            self.botones_hallazgo[clave] = btn
            grid.addWidget(btn, i // 2, i % 2)
        return grid

    def _build_cae(self):
        grid = QGridLayout()
        self.checks_cae = {}
        for i, (clave, etiqueta) in enumerate(CAE_CHECKS):
            chk = QCheckBox(etiqueta)
            chk.stateChanged.connect(lambda _estado, c=clave: self._cae_cambiado(c))
            self.checks_cae[clave] = chk
            grid.addWidget(chk, i // 2, i % 2)
        return grid

    def _cae_cambiado(self, clave):
        """'Normal' y cualquier hallazgo son excluyentes -- un CAE con
        cerumen no es un CAE normal."""
        if not self.checks_cae[clave].isChecked():
            return
        if clave == "cae_normal":
            for otra, chk in self.checks_cae.items():
                if otra != "cae_normal":
                    chk.setChecked(False)
        else:
            self.checks_cae["cae_normal"].setChecked(False)

    def _set_hallazgo(self, clave):
        self._hallazgo_activo = clave
        for otra, btn in self.botones_hallazgo.items():
            btn.setChecked(otra == clave)

    def _marcar_cuadrante(self, cuadrante):
        marcas = self.diagrama.marcas
        if self._hallazgo_activo is None:
            marcas.pop(cuadrante, None)
        elif marcas.get(cuadrante) == self._hallazgo_activo:
            marcas.pop(cuadrante)  # segundo click con el mismo hallazgo = borrar
        else:
            marcas[cuadrante] = self._hallazgo_activo
        self.diagrama.update()

    def limpiar_marcas(self):
        self.diagrama.marcas.clear()
        self.diagrama.update()

    def limpiar(self):
        self.limpiar_marcas()
        self._set_hallazgo(None)
        for chk in self.checks_cae.values():
            chk.setChecked(False)
        self.txt_observaciones.clear()

    def to_dict(self):
        return {
            "cuadrantes": dict(self.diagrama.marcas),
            "cae": sorted(clave for clave, chk in self.checks_cae.items() if chk.isChecked()),
            "observaciones": self.txt_observaciones.toPlainText().strip(),
        }

    def tiene_algo(self):
        d = self.to_dict()
        return bool(d["cuadrantes"] or d["cae"] or d["observaciones"])


class InformeOtoscopia(QWidget):
    """Pestaña "Informe" de la ventana de otoscopia: lo que el alumno dice
    haber visto, por cuadrante y oído. No se compara con nada acá -- lo
    evalúa el docente contra la foto del caso (admin/chat_detail.php)."""

    guardar_pedido = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        raiz = QVBoxLayout(self)

        oidos = QHBoxLayout()
        self.panel_od = _PanelOido("od", "Oído derecho (OD)")
        self.panel_oi = _PanelOido("oi", "Oído izquierdo (OI)")
        oidos.addWidget(self.panel_od)
        oidos.addWidget(self.panel_oi)
        raiz.addLayout(oidos)

        barra = QHBoxLayout()
        self.lbl_estado = QLabel("")
        self.btn_guardar = QPushButton("Guardar informe")
        self.btn_guardar.clicked.connect(self.guardar_pedido.emit)
        barra.addWidget(self.lbl_estado, 1)
        barra.addWidget(self.btn_guardar)
        raiz.addLayout(barra)

    def limpiar(self):
        self.panel_od.limpiar()
        self.panel_oi.limpiar()
        self.lbl_estado.setText("")

    def to_dict(self):
        return {"od": self.panel_od.to_dict(), "oi": self.panel_oi.to_dict()}

    def tiene_algo(self):
        return self.panel_od.tiene_algo() or self.panel_oi.tiene_algo()

    def set_estado(self, texto):
        self.lbl_estado.setText(texto)
