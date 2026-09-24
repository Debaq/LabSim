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
import math

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

# (clave, etiqueta, color, tipo) -- claves de FindingType de OtoReport.
#
# El tipo es cómo se dibuja la marca, y son dos cosas distintas:
#   "area": el hallazgo ocupa zona (una retracción, una efusión, una placa)
#           -- rellena el cuadrante.
#   "punto": el hallazgo es una lesión puntual dentro del cuadrante (una
#            perforación, un tubo) -- se dibuja como marcador encima.
# En un mismo cuadrante conviven varios: una perforación anteroinferior con
# timpanoesclerosis alrededor es un hallazgo corriente, y antes el segundo
# click pisaba al primero.
AREA = "area"
PUNTO = "punto"
HALLAZGOS = [
    ("retraction", "Retracción", "#f59e0b", AREA),
    ("perforation", "Perforación", "#ef4444", PUNTO),
    ("effusion", "Efusión", "#3b82f6", AREA),
    ("tympanosclerosis", "Timpanoesclerosis", "#8b5cf6", AREA),
    ("cholesteatoma", "Colesteatoma", "#f97316", AREA),
    ("inflammation", "Inflamación", "#dc2626", AREA),
    ("tube", "Tubo", "#10b981", PUNTO),
    ("myringitis", "Miringitis", "#ec4899", AREA),
]
COLOR_HALLAZGO = {clave: color for clave, _, color, _t in HALLAZGOS}
ETIQUETA_HALLAZGO = {clave: etiqueta for clave, etiqueta, _c, _t in HALLAZGOS}
TIPO_HALLAZGO = {clave: tipo for clave, _e, _c, tipo in HALLAZGOS}


def es_de_area(clave):
    """Los hallazgos desconocidos (informes de otra versión) se dibujan
    como área: es el relleno, lo que peor se puede perder de vista."""
    return TIPO_HALLAZGO.get(clave, AREA) == AREA


def glifo_hallazgo(clave):
    """Símbolo con que se dibuja el hallazgo en el esquema, para poder
    repetirlo en el botón: el botón de la paleta es la leyenda, y con solo
    el color no se sabe si el hallazgo sale como relleno, como disco o como
    anillo. Tiene que seguir a _DiagramaTimpanico._dibujar_marcador."""
    if es_de_area(clave):
        return "■"
    return "○" if clave == "tube" else "●"

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
    """Esquema clickeable de la membrana: 4 cuadrantes + pars flácida.

    Cada cuadrante guarda VARIOS hallazgos, no uno: en una misma zona se
    encuentra más de una cosa a la vez (perforación con timpanoesclerosis
    alrededor, retracción con placa). Los de área se reparten el cuadrante
    en franjas y los puntuales se dibujan como marcadores encima, así
    ninguno tapa al otro. Marcar dos veces el mismo hallazgo lo saca.
    """

    cuadrante_click = Signal(str)

    def __init__(self, lado, parent=None):
        super().__init__(parent)
        self._es_derecho = lado == "od"
        self.marcas = {}  # cuadrante -> [claves de hallazgo, en orden de marcado]
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)  # para el tooltip con lo marcado

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

    def mouseMoveEvent(self, event):
        """Tooltip con lo marcado en el cuadrante de abajo del mouse: con
        varios hallazgos en la misma zona, el dibujo solo no siempre deja
        claro cuáles son."""
        cuadrante = self._cuadrante_en(event.position().toPoint())
        if cuadrante is None:
            self.setToolTip("")
        else:
            claves = self.marcas.get(cuadrante, [])
            etiquetas = ", ".join(ETIQUETA_HALLAZGO.get(c, c) for c in claves) or "sin hallazgos"
            self.setToolTip(f"{ETIQUETA_CUADRANTE.get(cuadrante, cuadrante)}: {etiquetas}")
        super().mouseMoveEvent(event)

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

        # Relleno de los cuadrantes marcados: los 90° del cuadrante se
        # reparten en tantas franjas como hallazgos de área tenga. Con uno
        # solo queda igual que antes (el pie entero).
        for cuadrante, angulo in self._angulos_cuadrantes().items():
            de_area = [c for c in self.marcas.get(cuadrante, []) if es_de_area(c)]
            if not de_area:
                continue
            painter.setPen(Qt.PenStyle.NoPen)
            franja = 90.0 / len(de_area)
            for i, clave in enumerate(de_area):
                color = QColor(COLOR_HALLAZGO.get(clave, "#888888"))
                color.setAlpha(150)
                painter.setBrush(color)
                painter.drawPie(
                    rect_de(r), int((angulo + i * franja) * 16), int(franja * 16)
                )

        # Divisiones
        painter.setPen(QPen(QColor("#92400e"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(int(centro.x() - r), centro.y(), int(centro.x() + r), centro.y())
        painter.drawLine(centro.x(), int(centro.y() - r), centro.x(), int(centro.y() + r))

        # Pars flácida: mismo criterio, pero repartida en bandas
        # verticales (es un óvalo chico, un pie ahí no se leería).
        pf = self._rect_pars_flaccida()
        area_pf = [c for c in self.marcas.get("pars_flaccida", []) if es_de_area(c)]
        if area_pf:
            painter.save()
            painter.setClipRect(pf)
            painter.setPen(Qt.PenStyle.NoPen)
            ancho = pf.width() / len(area_pf)
            for i, clave in enumerate(area_pf):
                color = QColor(COLOR_HALLAZGO.get(clave, "#888888"))
                color.setAlpha(150)
                painter.fillRect(
                    QRect(int(pf.left() + i * ancho), pf.top(),
                          int(ancho) + 1, pf.height()),
                    color,
                )
            painter.restore()
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

        # Hallazgos puntuales (perforación, tubo): marcadores encima del
        # relleno, no un color de fondo -- una perforación es una lesión en
        # un punto del cuadrante, no el cuadrante entero, y así se ve junto
        # con el área que la rodea. Van al final para que ninguna
        # referencia anatómica los tape.
        for cuadrante, angulo in self._angulos_cuadrantes().items():
            puntos = [c for c in self.marcas.get(cuadrante, []) if not es_de_area(c)]
            if not puntos:
                continue
            centro_ang = angulo + 45.0
            # 0.78r y no el centro del cuadrante: ahí van las siglas
            # (AS/AI/PS/PI, a ~0.6r) y el marcador quedaba encima del texto.
            radio = r * 0.78
            for i, clave in enumerate(puntos):
                # Se abren en abanico dentro del cuadrante: dos
                # perforaciones marcadas seguidas no se superponen.
                ang = math.radians(centro_ang + (i - (len(puntos) - 1) / 2) * 16.0)
                self._dibujar_marcador(
                    painter, clave,
                    QPoint(int(centro.x() + radio * math.cos(ang)),
                           int(centro.y() - radio * math.sin(ang))),
                    lado,
                )

        puntos_pf = [c for c in self.marcas.get("pars_flaccida", []) if not es_de_area(c)]
        for i, clave in enumerate(puntos_pf):
            paso = pf.width() / (len(puntos_pf) + 1)
            self._dibujar_marcador(
                painter, clave,
                QPoint(int(pf.left() + paso * (i + 1)), pf.center().y()),
                lado,
            )

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

    def _dibujar_marcador(self, painter, clave, punto, lado):
        """Marcador de un hallazgo puntual. El tubo va como anillo y el
        resto (perforación) como disco: con dos marcadores del mismo tamaño
        y solo el color distinto, en el esquema chico no se distinguen."""
        color = QColor(COLOR_HALLAZGO.get(clave, "#888888"))
        radio = max(3, int(lado * 0.028))
        if clave == "tube":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(color, max(2, int(lado * 0.012))))
        else:
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.drawEllipse(punto, radio, radio)

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

        # Esquema y paleta lado a lado (como en OtoReport): apilados, el
        # panel medía casi 700 px de alto y no entraba en la subventana
        # del MDI junto con la pestaña del otoscopio.
        fila = QHBoxLayout()
        self.diagrama = _DiagramaTimpanico(lado)
        self.diagrama.cuadrante_click.connect(self._marcar_cuadrante)
        fila.addWidget(self.diagrama, 1)

        columna = QVBoxLayout()
        columna.addWidget(QLabel("Hallazgo a marcar:"))
        self.diagrama.setToolTip(
            "Cada click suma el hallazgo elegido al cuadrante. Volver a "
            "marcarlo lo saca; sin hallazgo elegido, el click vacía el "
            "cuadrante."
        )
        columna.addLayout(self._build_paleta())
        self.btn_limpiar = QPushButton("Limpiar marcas")
        self.btn_limpiar.clicked.connect(self.limpiar_marcas)
        columna.addWidget(self.btn_limpiar)
        columna.addStretch(1)
        fila.addLayout(columna)
        raiz.addLayout(fila, 1)

        raiz.addWidget(QLabel("<b>Conducto auditivo externo</b>"))
        raiz.addLayout(self._build_cae())

        raiz.addWidget(QLabel("Observaciones:"))
        self.txt_observaciones = QTextEdit()
        self.txt_observaciones.setPlaceholderText("Observaciones")
        self.txt_observaciones.setMaximumHeight(64)
        raiz.addWidget(self.txt_observaciones)

    def _build_paleta(self):
        # Sin QButtonGroup exclusivo: destildar el hallazgo activo deja el
        # modo "borrador" (click en un cuadrante marcado lo borra, ver
        # _marcar_cuadrante), y un grupo exclusivo no permite quedar sin
        # ninguno tildado.
        grid = QGridLayout()
        self.botones_hallazgo = {}
        for i, (clave, etiqueta, color, _tipo) in enumerate(HALLAZGOS):
            btn = QPushButton(f"{glifo_hallazgo(clave)} {etiqueta}")
            btn.setCheckable(True)
            btn.setStyleSheet(
                # 3 px: con 1 px el color del hallazgo casi no se veía en
                # el botón, que es la única leyenda de qué color es cada uno.
                f"QPushButton {{ border: 3px solid {color}; border-radius: 4px; padding: 3px; }}"
                f"QPushButton:checked {{ background-color: {color}; color: white; }}"
            )
            btn.setToolTip(
                "Rellena el cuadrante" if es_de_area(clave)
                else "Marca puntual dentro del cuadrante"
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
            grid.addWidget(chk, i // 3, i % 3)
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
        """Suma el hallazgo activo a ese cuadrante (no lo reemplaza: en una
        zona se ve más de una cosa). Click con el mismo hallazgo ya marcado
        lo saca; click sin hallazgo activo vacía el cuadrante entero."""
        marcas = self.diagrama.marcas
        del_cuadrante = marcas.setdefault(cuadrante, [])
        if self._hallazgo_activo is None:
            del_cuadrante.clear()
        elif self._hallazgo_activo in del_cuadrante:
            del_cuadrante.remove(self._hallazgo_activo)
        else:
            del_cuadrante.append(self._hallazgo_activo)
        if not del_cuadrante:
            marcas.pop(cuadrante)
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
            # cuadrante -> lista de hallazgos (antes era un solo string;
            # el PDF del backend lee las dos formas, ver ReportPdfBuilder).
            "cuadrantes": {c: list(h) for c, h in self.diagrama.marcas.items()},
            "cae": sorted(clave for clave, chk in self.checks_cae.items() if chk.isChecked()),
            "observaciones": self.txt_observaciones.toPlainText().strip(),
        }

    def tiene_algo(self):
        d = self.to_dict()
        return bool(d["cuadrantes"] or d["cae"] or d["observaciones"])

    def from_dict(self, d):
        """Lo contrario de to_dict (acepta el formato viejo de un hallazgo
        por cuadrante)."""
        self.limpiar()
        for cuadrante, hallazgos in (d.get("cuadrantes") or {}).items():
            lista = [hallazgos] if isinstance(hallazgos, str) else list(hallazgos or [])
            if lista:
                self.diagrama.marcas[cuadrante] = lista
        for clave in d.get("cae") or []:
            if clave in self.checks_cae:
                self.checks_cae[clave].setChecked(True)
        self.txt_observaciones.setPlainText(d.get("observaciones") or "")
        self.diagrama.update()


class InformeOtoscopia(QWidget):
    """Pestaña "Informe" de la ventana de otoscopia: lo que el alumno dice
    haber visto, por cuadrante y oído (varios hallazgos por cuadrante). No se compara con nada acá -- lo
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

    def from_dict(self, d):
        self.panel_od.from_dict(d.get("od") or {})
        self.panel_oi.from_dict(d.get("oi") or {})

    def set_estado(self, texto):
        self.lbl_estado.setText(texto)
