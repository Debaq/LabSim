"""
El paciente en el impedanciómetro: la cabeza (la de los electrodos, ver
core/cabeza_electrodos.py), el set de olivas, la sonda y el fono
contralateral (2026-11-13).

El orden es el de la práctica:

1. elegir el tamaño de la oliva y ponérsela a la sonda;
2. meter la sonda en el oído que se va a medir;
3. poner el fono contralateral en el otro: un fono de concha (supraaural)
   con cintillo, unilateral; del lado de la sonda el cintillo apoya en la
   sien con un soporte;
4. medir;
5. dar vuelta todo -- la sonda al otro oído, el fono al primero -- y medir
   el otro.

    MontajeZ       dónde está cada cosa y qué oliva lleva la sonda
    CabezaZ        la cabeza que gira, con la sonda y el fono dibujados
    PanelMontajeZ  la cabeza con las olivas, las herramientas y lo puesto

Lo que el equipo hace con eso está en Z.py (ZControl.montaje): sin la sonda
en el oído, o con una oliva que no sella, el equipo no presuriza (aviso
SONDA ABIERTA / FUGA en su pantalla); sin el fono contralateral en el otro
oído el estímulo CONTRA no llega a ninguna parte y el reflejo no aparece.
El oído medido es el de la sonda: al meterla, el equipo pasa a ese oído.
"""
import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)

from core import iconos, tema
from core.cabeza_electrodos import CabezaElectrodos, FonosInsercion, datos

# El set de olivas de la sonda, en mm de diámetro, cada una con su color
# (como vienen en la caja). Los colores no repiten el rojo/azul de OD/OI.
OLIVAS = (
    (7, "#F2C94C"),
    (9, "#F2994A"),
    (11, "#6FCF97"),
    (13, "#BDBDBD"),
    (15, "#9B51E0"),
    (17, "#A0785A"),
    (19, "#4F4F4F"),
)
COLOR_OLIVA = dict(OLIVAS)
OLIVAS_MM = tuple(mm for mm, _ in OLIVAS)
SONDA, CONTRA = "sonda", "contra"
NOMBRE = {SONDA: "La sonda", CONTRA: "El fono contralateral"}
OTRO = {"OD": "OI", "OI": "OD"}

VISTAS = (("Derecho", 90, 0), ("Frente", 0, 0), ("Izquierdo", 270, 0))
HERRAMIENTAS = (("girar", "Girar"), (SONDA, "Sonda"), (CONTRA, "Fono"))
PISTAS = {
    "girar": "Arrastra para girar la cabeza.",
    SONDA: "Clic en el conducto: ahí va la sonda.",
    CONTRA: "Clic en la oreja: ahí va el fono; el cintillo apoya en la otra sien.",
}
DONDE = {SONDA: "va en el conducto auditivo", CONTRA: "va sobre la oreja"}
OREJA_M = 0.040     # el fono de concha cubre la oreja: el clic cae a menos de 4 cm del conducto


def oreja_en(punto):
    """La oreja ('OD'/'OI') bajo un punto de la piel, o None."""
    d = datos()
    mejor = None
    for sitio, oido in (("cae_der", "OD"), ("cae_izq", "OI")):
        dist = float(np.linalg.norm(d["pos"][d["por_id"][sitio]] - np.asarray(punto)))
        if dist <= OREJA_M and (mejor is None or dist < mejor[1]):
            mejor = (oido, dist)
    return mejor[0] if mejor else None


def oliva_que_sella(caso=None):
    """El tamaño de oliva que sella el conducto de este paciente. Por ahora
    siempre la mediana del set (pedido del autor, 2026-11-13); cuando el
    caso traiga el tamaño del conducto, sale de ahí."""
    return OLIVAS_MM[len(OLIVAS_MM) // 2]


class MontajeZ:
    """Dónde quedó la sonda ('OD'/'OI' o None, en la mesa), qué oliva lleva
    (mm o None) y dónde el fono contralateral. En cada conducto entra una
    sola cosa: lo que se mete donde había otra la devuelve a la mesa."""

    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.oliva = None
        self.sonda = None
        self.contra = None

    def elegir_oliva(self, mm):
        """Se cambia con la sonda en la mano, no metida. True si la cambió."""
        if self.sonda is not None or mm not in OLIVAS_MM:
            return False
        self.oliva = mm
        return True

    def poner(self, que, oido):
        """Mete la sonda o el fono en ese oído. Devuelve lo que había ahí y
        volvió a la mesa (SONDA/CONTRA) o None."""
        sacado = None
        if que == SONDA:
            if self.contra == oido:
                self.contra, sacado = None, CONTRA
            self.sonda = oido
        else:
            if self.sonda == oido:
                self.sonda, sacado = None, SONDA
            self.contra = oido
        return sacado

    def sacar(self, que):
        """Lo vuelve a la mesa; devuelve el oído donde estaba (o None)."""
        oido = getattr(self, que)
        setattr(self, que, None)
        return oido

    def sella(self, caso=None):
        """La sonda en un oído y con la oliva que sella."""
        return self.sonda is not None and self.oliva == oliva_que_sella(caso)

    def contra_en_el_otro(self):
        """El fono contralateral en el oído opuesto al de la sonda."""
        return self.sonda is not None and self.contra == OTRO[self.sonda]

    def estado(self):
        return {"oliva": self.oliva, "sonda": self.sonda, "contra": self.contra}


class CabezaZ(CabezaElectrodos):
    """La cabeza con la sonda y el fono. Con Sonda o Fono contra, el clic
    en la piel emite `punto_elegido` (quien la usa ve si cayó en un
    conducto)."""

    def __init__(self, montaje, parent=None):
        super().__init__(parent)
        self.montaje = montaje
        self.setMinimumSize(150, 150)
        self.mirar(90, 0)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.herramienta in (SONDA, CONTRA) \
                and self._apretado is not None and not self._arrastrando:
            self._apretado = None
            tocado = self.tocar(ev.position())
            if tocado is not None:
                self.punto_elegido.emit(tocado[0], tocado[1])
            return
        super().mouseReleaseEvent(ev)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        _, escala = self._marco()
        px_por_m = self.geo.foco * self.geo.tam / 2 / self.geo.ojo[2] * escala
        if self.montaje.contra is not None:
            self._dibujar_contra(p, self.montaje.contra, px_por_m)
        if self.montaje.sonda is not None:
            self._dibujar_sonda(p, self.montaje.sonda, self.montaje.oliva, px_por_m)
        p.end()

    @staticmethod
    def _conducto(oido):
        d = datos()
        c = d["pos"][d["por_id"]["cae_der" if oido == "OD" else "cae_izq"]]
        return c, np.array([1.0 if c[0] > 0 else -1.0, 0.0, 0.0])

    def _proyectar(self, puntos, lat):
        inc, giro = self._angulos()
        px, vis = self.geo.proyectar(np.array(puntos), [lat] * len(puntos), inc, giro, umbral=-0.3)
        return [self._a_pantalla(xy) for xy in px], vis

    def _dibujar_sonda(self, p, oido, oliva, px_por_m):
        """La oliva en el conducto, el cuerpo de la sonda asomando y el cable
        que baja por detrás de la oreja. Una oliva más grande que la que
        sella queda afuera, en la concha."""
        c, lat = self._conducto(oido)
        afuera = 0.002 if oliva is None or oliva <= oliva_que_sella() else 0.006
        pant, vis = self._proyectar([
            c + lat * afuera,                                     # oliva
            c + lat * (afuera + 0.020),                           # punta de atrás de la sonda
            [c[0] + lat[0] * 0.020, c[1] - 0.035, c[2] - 0.015],  # detrás del lóbulo
            [c[0] + lat[0] * 0.016, -0.110, c[2] - 0.010],
            [c[0] * 0.8, -0.170, c[2] + 0.010],                   # hacia el equipo
        ], lat)
        if not vis[0]:
            return
        cable = QPainterPath(pant[1])
        cable.cubicTo(pant[2], pant[3], pant[4])
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(70, 74, 82, 230), max(2.0, 0.0022 * px_por_m)))
        p.drawPath(cable)
        cuerpo = QPen(QColor("#2F3238"), max(7.0, 0.011 * px_por_m))
        cuerpo.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(cuerpo)
        p.drawLine(pant[0], pant[1])
        if oliva is not None:
            radio = max(4.5, oliva / 2000 * px_por_m)
            p.setPen(QPen(QColor("#2F3238"), 1.5))
            p.setBrush(QColor(COLOR_OLIVA[oliva]))
            p.drawEllipse(pant[0], radio, radio)

    def _dibujar_contra(self, p, oido, px_por_m):
        """Fono de concha (supraaural) unilateral: la concha sobre la oreja,
        el cintillo por encima de la cabeza y, del otro lado, el soporte
        apoyado en la sien. Cada parte se ve mientras mire a la cámara."""
        c, lat = self._conducto(oido)
        inc, giro = self._angulos()
        # La concha: un disco en el plano de la oreja, con el auricular
        # (más chico) por fuera.
        centro = c + lat * 0.020 + np.array([0.0, 0.004, -0.008])
        ang = np.linspace(0, 2 * np.pi, 28, endpoint=False)
        def disco(cen, radio):
            return cen + radio * (np.outer(np.cos(ang), [0, 1, 0]) + np.outer(np.sin(ang), [0, 0, 1]))
        _, vis = self.geo.proyectar(centro, lat, inc, giro, umbral=-0.3)
        # El cintillo: de lo alto de la concha, por sobre el vértex, al
        # soporte en la sien del otro lado.
        s = lat[0]
        sien = np.array([-s * 0.078, 0.038, 0.026])
        t = np.linspace(0.0, np.pi - 0.35, 24)
        arco = np.stack([s * 0.100 * np.cos(t), 0.030 + 0.118 * np.sin(t),
                         0.002 + 0.022 * t / np.pi], axis=1)
        arco = np.vstack([arco, sien + np.array([-s * 0.006, 0.0, 0.0])])
        normales = arco - np.array([0.0, 0.030, 0.0])
        normales /= np.linalg.norm(normales, axis=1, keepdims=True)
        px, vis_arco = self.geo.proyectar(arco, normales, inc, giro, umbral=-0.25)
        pant = [self._a_pantalla(xy) for xy in px]
        banda = QPen(QColor("#3B3F46"), max(3.0, 0.005 * px_por_m))
        banda.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(banda)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for k in range(len(pant) - 1):
            if vis_arco[k] and vis_arco[k + 1]:
                p.drawLine(pant[k], pant[k + 1])
        # El soporte de la sien.
        px, vis_sien = self.geo.proyectar(sien, -lat, inc, giro, umbral=-0.3)
        if vis_sien[0]:
            r = max(4.0, 0.009 * px_por_m)
            p.setPen(QPen(QColor("#2F3238"), 1.5))
            p.setBrush(QColor("#5A5F68"))
            p.drawEllipse(self._a_pantalla(px[0]), r * 0.7, r)
        if not vis[0]:
            return
        # El cable baja desde el auricular.
        afuera = centro + lat * 0.014
        px, _ = self.geo.proyectar(np.array([
            afuera - np.array([0.0, 0.018, 0.0]),
            afuera + np.array([0.0, -0.060, -0.010]),
            [afuera[0] * 0.95, -0.120, afuera[2] - 0.010],
            [afuera[0] * 0.85, -0.170, afuera[2] + 0.010],
        ]), [lat] * 4, inc, giro, umbral=-1.0)
        q = [self._a_pantalla(xy) for xy in px]
        cable = QPainterPath(q[0])
        cable.cubicTo(q[1], q[2], q[3])
        p.setPen(QPen(QColor(70, 74, 82, 230), max(2.0, 0.0022 * px_por_m)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(cable)
        for cen, radio, relleno in ((centro, 0.028, "#2B2D31"),
                                    (centro + lat * 0.012, 0.021, "#4A4F57")):
            px, _ = self.geo.proyectar(disco(cen, radio), [lat] * len(ang), inc, giro, umbral=-1.0)
            poli = QPainterPath(self._a_pantalla(px[0]))
            for xy in px[1:]:
                poli.lineTo(self._a_pantalla(xy))
            poli.closeSubpath()
            p.setPen(QPen(QColor("#1E1F22"), 1.5))
            p.setBrush(QColor(relleno))
            p.drawPath(poli)


def _chip(color, texto, tam=26):
    """El ícono de una oliva: el círculo de su color con los mm encima."""
    pm = QPixmap(tam * 2, tam * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#2F3238"), 2))
    p.setBrush(QColor(color))
    p.drawEllipse(QRectF(2, 2, tam * 2 - 4, tam * 2 - 4))
    oscuro = QColor(color).lightness() < 140
    p.setPen(QColor("white" if oscuro else "#2A2229"))
    f = QFont()
    f.setPixelSize(int(tam * 0.9))
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(0, 0, tam * 2, tam * 2), Qt.AlignmentFlag.AlignCenter, texto)
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


EXTRA_QSS = f"""
QPushButton[segmento="true"] {{ padding: 3px 0px; }}
QPushButton[herramienta="true"] {{ padding: 4px 0px; font-weight: 600; }}
QPushButton[herramienta="true"]:checked {{ background: {tema.ACENTO}; border-color: {tema.ACENTO}; color: white; }}
QPushButton[oliva="true"] {{ padding: 2px; }}
QPushButton[oliva="true"]:checked {{ background: {tema.ACENTO_SUAVE}; border: 2px solid {tema.ACENTO}; }}
QLabel#puesto {{ color: {tema.TEXTO}; font-weight: 600; }}
QLabel#puesto[vacio="true"] {{ color: {tema.TEXTO_TENUE}; font-weight: 400; }}
"""


class PanelMontajeZ(QFrame):
    """La columna derecha del impedanciómetro: arriba la cabeza, abajo el set
    de olivas, la sonda y el fono contralateral.

    `puesto(que, oido)` y `sacado(que, oido)` avisan al equipo (Z.py); cada
    acción va además al registro por `log(accion, **payload)`."""
    puesto = Signal(str, str)
    sacado = Signal(str, str)

    def __init__(self, log=None, parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")
        tema.aplicar_estilo(self, EXTRA_QSS)
        self.log = log or (lambda accion, **payload: None)
        self.montaje = MontajeZ()

        col = QVBoxLayout(self)
        col.setContentsMargins(8, 8, 8, 8)
        col.setSpacing(5)
        self.cabeza = CabezaZ(self.montaje)
        self.cabeza.punto_elegido.connect(self._en_la_piel)
        col.addWidget(self.cabeza, 1)

        vistas = QHBoxLayout()
        vistas.setSpacing(3)
        for nombre, giro, incl in VISTAS:
            b = QPushButton(nombre)
            b.setProperty("segmento", "true")
            b.clicked.connect(lambda _=False, g=giro, i=incl: self.cabeza.mirar(g, i))
            vistas.addWidget(b, 1)
        col.addLayout(vistas)

        herramientas = QHBoxLayout()
        herramientas.setSpacing(3)
        grupo = QButtonGroup(self)
        self.botones_herramienta = {}
        for clave, nombre in HERRAMIENTAS:
            b = QPushButton(nombre)
            b.setCheckable(True)
            b.setProperty("herramienta", "true")
            b.clicked.connect(lambda _=False, c=clave: self.elegir_herramienta(c))
            grupo.addButton(b)
            herramientas.addWidget(b, 1)
            self.botones_herramienta[clave] = b
        col.addLayout(herramientas)

        self.pista = QLabel()
        self.pista.setProperty("role", "hint")
        self.pista.setWordWrap(True)
        self.pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.pista)

        col.addWidget(self._seccion("OLIVAS DE LA SONDA"))
        grilla = QGridLayout()
        grilla.setSpacing(3)
        self.grupo_oliva = QButtonGroup(self)
        self.grupo_oliva.setExclusive(False)   # se maneja a mano: puede no haber ninguna
        self.botones_oliva = {}
        por_fila = 4
        for i, (mm, color) in enumerate(OLIVAS):
            b = QPushButton()
            b.setIcon(_chip(color, str(mm)))
            b.setIconSize(b.iconSize() * 1.6)
            b.setCheckable(True)
            b.setProperty("oliva", "true")
            b.setToolTip(f"Oliva de {mm} mm")
            b.clicked.connect(lambda _=False, m=mm: self._elegir_oliva(m))
            self.grupo_oliva.addButton(b)
            grilla.addWidget(b, i // por_fila, i % por_fila)
            self.botones_oliva[mm] = b
        col.addLayout(grilla)

        col.addWidget(self._seccion("PUESTO"))
        puestos = QGridLayout()
        puestos.setHorizontalSpacing(4)
        puestos.setVerticalSpacing(3)
        puestos.setColumnStretch(1, 1)
        self.lbl_puesto = {}
        for fila, (que, nombre) in enumerate(((SONDA, "Sonda"), (CONTRA, "Fono contra"))):
            puestos.addWidget(QLabel(nombre), fila, 0)
            lbl = QLabel()
            lbl.setObjectName("puesto")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            puestos.addWidget(lbl, fila, 1)
            quitar = QPushButton()
            quitar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_TENUE, tam=12))
            quitar.setToolTip("Sacar")
            quitar.setFixedSize(24, 22)
            quitar.clicked.connect(lambda _=False, q=que: self.sacar(q))
            puestos.addWidget(quitar, fila, 2)
            self.lbl_puesto[que] = lbl
        col.addLayout(puestos)

        self.elegir_herramienta("girar")
        self._pintar()

    @staticmethod
    def _seccion(texto):
        lbl = QLabel(texto)
        lbl.setProperty("role", "seccion")
        return lbl

    # ------------------------------------------------------------ acciones
    def reiniciar(self):
        """Paciente nuevo: todo a la mesa y la sonda sin oliva."""
        self.montaje.reiniciar()
        self.cabeza.mirar(90, 0)
        self.elegir_herramienta("girar")
        self._pintar()

    def elegir_herramienta(self, clave):
        self.cabeza.poner_herramienta(clave)
        self.botones_herramienta[clave].setChecked(True)
        self.pista.setText(PISTAS[clave])

    def _elegir_oliva(self, mm):
        if self.montaje.sonda is not None:
            self.pista.setText("Saca la sonda del oído para cambiarle la oliva.")
        elif self.montaje.oliva != mm and self.montaje.elegir_oliva(mm):
            self.log("z_oliva", oliva_mm=mm)
            self.elegir_herramienta(SONDA)
        self._pintar()

    def _en_la_piel(self, punto, _normal):
        que = self.cabeza.herramienta
        oido = FonosInsercion.oido_en(punto) if que == SONDA else oreja_en(punto)
        if oido is None:
            self.pista.setText(f"{NOMBRE[que]} {DONDE[que]}.")
            return
        self.poner(que, oido)

    def poner(self, que, oido):
        if que == SONDA and self.montaje.oliva is None:
            self.log("z_sonda_sin_oliva", oido=oido)
            self.pista.setText("La sonda no entra sin oliva: elige una del set.")
            return
        if getattr(self.montaje, que) == oido:
            return
        antes = getattr(self.montaje, que)
        if antes is not None:
            self._sacar(que)
        desplazado = self.montaje.poner(que, oido)
        if desplazado is not None:
            # Lo que estaba en ese oído vuelve a la mesa.
            self.log(f"z_{desplazado}_sacar", oido=oido)
            self.sacado.emit(desplazado, oido)
        payload = {"oido": oido}
        if que == SONDA:
            payload["oliva_mm"] = self.montaje.oliva
        self.log(f"z_{que}_poner", **payload)
        self.puesto.emit(que, oido)
        self.pista.setText(PISTAS[self.cabeza.herramienta])
        self._pintar()

    def sacar(self, que):
        if getattr(self.montaje, que) is None:
            return
        self._sacar(que)
        self._pintar()

    def _sacar(self, que):
        oido = self.montaje.sacar(que)
        self.log(f"z_{que}_sacar", oido=oido)
        self.sacado.emit(que, oido)

    # ------------------------------------------------------------ dibujo
    def _pintar(self):
        for mm, b in self.botones_oliva.items():
            b.setChecked(mm == self.montaje.oliva)
        for que, lbl in self.lbl_puesto.items():
            oido = getattr(self.montaje, que)
            texto = "en la mesa" if oido is None else oido
            if que == SONDA and self.montaje.oliva is not None:
                texto += f" · {self.montaje.oliva} mm"
            lbl.setText(texto)
            lbl.setProperty("vacio", "true" if oido is None else "false")
            if oido is not None:
                lbl.setStyleSheet(f"color: {tema.color_lado(oido)};")
            else:
                lbl.setStyleSheet("")
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)
        self.cabeza.update()
