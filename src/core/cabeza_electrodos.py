"""
Cabeza giratoria para poner los electrodos de las pruebas electrofisiológicas.

La cabeza y los sitios 10-20 / 10-10 son los de labyrinthus3d, fotografiados
desde muchos ángulos (cada 2° de giro y cada 10° de inclinación): ver
scripts/cabeza_electrodos/. No es 3D en vivo -- el build no usa OpenGL, ver
LabSim.spec --, pero al arrastrar gira como si lo fuera. Cada cuadro trae
dónde cae cada sitio visible, así que los electrodos se dibujan encima y un
clic elige el sitio más cercano.

    CabezaElectrodos  la cabeza sola: gira, marca sitios, avisa el clic
    MontajeElectrodos la cabeza con el panel para poner activo, referencia y
                      tierra (prototipo: todavía no va conectado a los módulos)
"""
import json
import math
from collections import OrderedDict

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from core import iconos, tema
from core.base import context

# Colores de los cables, como en el equipo y en labyrinthus3d (COLOR_ROL):
# no son los de los oídos aunque se parezcan.
ROLES = (
    ("activo", "Activo (+)", "#E0302A"),
    ("referencia", "Referencia (−)", "#2F7FE0"),
    ("tierra", "Tierra", "#3AA655"),
)
COLOR_ROL = {clave: color for clave, _, color in ROLES}
NOMBRE_ROL = {clave: nombre for clave, nombre, _ in ROLES}

# Vistas rápidas: (giro, inclinación). Con giro 90 se ve el lado derecho del
# paciente (la cabeza gira hacia su izquierda).
VISTAS = (
    ("Frente", 0, 0),
    ("Derecha", 90, 0),
    ("Izquierda", 270, 0),
    ("Arriba", 0, 60),
    ("Atrás", 180, 20),
)
GRADOS_POR_PIXEL = 0.6
RADIO_CLIC = 14          # px de pantalla para tomar el sitio más cercano
CUADROS_EN_MEMORIA = 80

_datos = None


def datos():
    """El paquete de la cabeza (resources/cabeza): se lee una vez."""
    global _datos
    if _datos is None:
        with open(context.get_resource("cabeza/cabeza.json"), encoding="utf-8") as f:
            info = json.load(f)
        with open(context.get_resource("cabeza/cabeza.bin"), "rb") as f:
            info["bin"] = f.read()
        info["por_id"] = {s["id"]: i for i, s in enumerate(info["sitios"])}
        _datos = info
    return _datos


def nombre_sitio(sitio_id):
    d = datos()
    i = d["por_id"].get(sitio_id)
    return d["sitios"][i]["nombre"] if i is not None else sitio_id


class CabezaElectrodos(QWidget):
    """La cabeza: arrastrar gira, clic en un sitio emite `sitio_elegido`."""
    sitio_elegido = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.d = datos()
        self.yaws = self.d["yaws"]
        self.pitches = self.d["pitches"]
        self.giro = 0.0           # grados, continuo; se ajusta al cuadro más cercano
        self.inclinacion = 0.0
        self.sistema = "10-20"
        self.colocados = {}       # rol -> sitio
        self.rol_actual = None    # el que se pone con el próximo clic (para el cursor)
        self._sobre = None        # sitio bajo el mouse
        self._apretado = None
        self._arrastrando = False
        self._cache = OrderedDict()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(260, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    # ------------------------------------------------------------ cuadros
    def _clave(self):
        paso = self.yaws[1] - self.yaws[0]
        y = self.yaws[int(round((self.giro % 360) / paso)) % len(self.yaws)]
        p = min(self.pitches, key=lambda v: abs(v - self.inclinacion))
        return f"{p}_{y}"

    def _pixmap(self, clave):
        pm = self._cache.get(clave)
        if pm is None:
            ini, largo = self.d["indice"][clave]
            img = QImage.fromData(self.d["bin"][ini:ini + largo], "WEBP")
            pm = QPixmap.fromImage(img)
            self._cache[clave] = pm
            if len(self._cache) > CUADROS_EN_MEMORIA:
                self._cache.popitem(last=False)
        else:
            self._cache.move_to_end(clave)
        return pm

    def _marco(self):
        """Dónde se dibuja el cuadro (cuadrado, centrado) y su escala."""
        lado = min(self.width(), self.height())
        x0 = (self.width() - lado) / 2
        y0 = (self.height() - lado) / 2
        return QRectF(x0, y0, lado, lado), lado / self.d["tam"]

    def _visibles(self):
        """[(sitio, punto en pantalla)] de los sitios a la vista en este cuadro."""
        marco, escala = self._marco()
        fila = self.d["cuadros"][self._clave()]
        puestos = set(self.colocados.values())
        out = []
        for s, xy in zip(self.d["sitios"], fila):
            if xy is None:
                continue
            if self.sistema == "10-20" and s["craneo"] and s["sistema"] != "10-20" \
                    and s["id"] not in puestos:
                continue
            out.append((s, QPointF(marco.x() + xy[0] * escala, marco.y() + xy[1] * escala)))
        return out

    def _sitio_en(self, pos):
        mejor, dist = None, RADIO_CLIC
        for s, p in self._visibles():
            dd = math.hypot(p.x() - pos.x(), p.y() - pos.y())
            if dd < dist:
                mejor, dist = s["id"], dd
        return mejor

    # ------------------------------------------------------------ API
    def mirar(self, giro, inclinacion):
        self.giro, self.inclinacion = float(giro), float(inclinacion)
        self.update()

    def poner_sistema(self, sistema):
        self.sistema = sistema
        self.update()

    def poner(self, colocados):
        self.colocados = dict(colocados)
        self.update()

    # ------------------------------------------------------------ dibujo
    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        marco, _escala = self._marco()
        p.drawPixmap(marco, self._pixmap(self._clave()), QRectF(0, 0, self.d["tam"], self.d["tam"]))

        rol_de = {sitio: rol for rol, sitio in self.colocados.items()}
        fuente = QFont(self.font())
        fuente.setPointSizeF(7.5)
        fuente.setBold(True)
        p.setFont(fuente)
        for s, pt in self._visibles():
            rol = rol_de.get(s["id"])
            sobre = s["id"] == self._sobre
            if rol:
                p.setPen(QPen(QColor("white"), 2))
                p.setBrush(QColor(COLOR_ROL[rol]))
                p.drawEllipse(pt, 7.5, 7.5)
            else:
                r = 4.5 if sobre else 2.6
                p.setPen(QPen(QColor(tema.ACENTO if sobre else "#5E5360"), 1.2))
                p.setBrush(QColor("white"))
                p.drawEllipse(pt, r, r)
            if rol or sobre:
                texto = s["corto"]
                ancho = p.fontMetrics().horizontalAdvance(texto) + 8
                caja = QRectF(pt.x() + 9, pt.y() - 9, ancho, 17)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, 255, 255, 225))
                p.drawRoundedRect(caja, 4, 4)
                p.setPen(QColor(COLOR_ROL[rol]) if rol else QColor(tema.ACENTO))
                p.drawText(caja, Qt.AlignmentFlag.AlignCenter, texto)
        p.end()

    # ------------------------------------------------------------ mouse
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._apretado = (ev.position(), self.giro, self.inclinacion)
            self._arrastrando = False

    def mouseMoveEvent(self, ev):
        if self._apretado is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            inicio, giro0, incl0 = self._apretado
            dx = ev.position().x() - inicio.x()
            dy = ev.position().y() - inicio.y()
            if not self._arrastrando and math.hypot(dx, dy) > 4:
                self._arrastrando = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            if self._arrastrando:
                # Arrastrar a la derecha gira la cara hacia la derecha de la
                # pantalla; hacia abajo, se ve más la coronilla.
                self.giro = giro0 + dx * GRADOS_POR_PIXEL
                self.inclinacion = max(self.pitches[0], min(self.pitches[-1], incl0 + dy * GRADOS_POR_PIXEL))
                self._sobre = None
                self.update()
            return
        sobre = self._sitio_en(ev.position())
        if sobre != self._sobre:
            self._sobre = sobre
            self.setCursor(Qt.CursorShape.PointingHandCursor if sobre else Qt.CursorShape.OpenHandCursor)
            self.setToolTip(nombre_sitio(sobre) if sobre else "")
            self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton or self._apretado is None:
            return
        arrastro = self._arrastrando
        self._apretado = None
        self._arrastrando = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if not arrastro:
            sitio = self._sitio_en(ev.position())
            if sitio:
                self.sitio_elegido.emit(sitio)

    def leaveEvent(self, _ev):
        if self._sobre:
            self._sobre = None
            self.update()

    def keyPressEvent(self, ev):
        paso = {Qt.Key.Key_Left: (-6, 0), Qt.Key.Key_Right: (6, 0),
                Qt.Key.Key_Up: (0, -10), Qt.Key.Key_Down: (0, 10)}.get(ev.key())
        if paso is None:
            super().keyPressEvent(ev)
            return
        self.mirar(self.giro + paso[0],
                   max(self.pitches[0], min(self.pitches[-1], self.inclinacion + paso[1])))


EXTRA_QSS = f"""
QPushButton[rol] {{ text-align: left; padding: 6px 10px; }}
QPushButton[rol]:checked {{ background: {tema.ACENTO_SUAVE}; border-color: {tema.ACENTO}; color: {tema.ACENTO}; font-weight: 600; }}
QPushButton[segmento="true"] {{ padding: 4px 0px; }}
QLabel#puesto {{ color: {tema.TEXTO}; font-weight: 600; }}
QLabel#puesto[vacio="true"] {{ color: {tema.TEXTO_TENUE}; font-weight: 400; }}
"""


def _punto(color, tam=12):
    pm = QPixmap(tam * 2, tam * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("white"), 3))
    p.setBrush(QColor(color))
    p.drawEllipse(QRectF(2, 2, tam * 2 - 4, tam * 2 - 4))
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


class MontajeElectrodos(QWidget):
    """Prototipo: la cabeza y un panel para poner activo, referencia y tierra."""
    montaje_cambio = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        tema.aplicar_estilo(self, EXTRA_QSS)
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(10)

        lienzo = QFrame()
        lienzo.setProperty("card", "true")
        col = QVBoxLayout(lienzo)
        col.setContentsMargins(8, 8, 8, 8)
        self.cabeza = CabezaElectrodos()
        self.cabeza.sitio_elegido.connect(self._poner)
        col.addWidget(self.cabeza, 1)
        vistas = QHBoxLayout()
        vistas.setSpacing(4)
        for nombre, giro, incl in VISTAS:
            b = QPushButton(nombre)
            b.setProperty("segmento", "true")
            b.clicked.connect(lambda _=False, g=giro, i=incl: self.cabeza.mirar(g, i))
            vistas.addWidget(b, 1)
        col.addLayout(vistas)
        pista = QLabel("Arrastra para girar la cabeza. Clic en un sitio pone el electrodo elegido.")
        pista.setProperty("role", "hint")
        pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(pista)
        raiz.addWidget(lienzo, 1)

        panel = QFrame()
        panel.setProperty("card", "true")
        panel.setFixedWidth(240)
        pcol = QVBoxLayout(panel)
        pcol.setContentsMargins(12, 10, 12, 12)
        pcol.setSpacing(6)
        seccion = QLabel("ELECTRODO")
        seccion.setProperty("role", "seccion")
        pcol.addWidget(seccion)
        self.grupo = QButtonGroup(self)
        self.botones_rol = {}
        self.lbl_puesto = {}
        grilla = QGridLayout()
        grilla.setVerticalSpacing(4)
        for i, (clave, nombre, color) in enumerate(ROLES):
            b = QPushButton(" " + nombre)
            b.setIcon(_punto(color))
            b.setCheckable(True)
            b.setProperty("rol", clave)
            b.clicked.connect(lambda _=False, c=clave: self._elegir_rol(c))
            self.grupo.addButton(b)
            self.botones_rol[clave] = b
            puesto = QLabel()
            puesto.setObjectName("puesto")
            self.lbl_puesto[clave] = puesto
            grilla.addWidget(b, i * 2, 0, 1, 2)
            grilla.addWidget(puesto, i * 2 + 1, 0)
            quitar = QPushButton()
            quitar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_TENUE, tam=12))
            quitar.setToolTip("Quitar este electrodo")
            quitar.setFixedSize(24, 22)
            quitar.clicked.connect(lambda _=False, c=clave: self._quitar(c))
            grilla.addWidget(quitar, i * 2 + 1, 1)
        pcol.addLayout(grilla)

        pcol.addSpacing(6)
        seccion = QLabel("SITIOS")
        seccion.setProperty("role", "seccion")
        pcol.addWidget(seccion)
        fila = QHBoxLayout()
        fila.setSpacing(4)
        grupo_sis = QButtonGroup(self)
        for nombre in ("10-20", "10-10"):
            b = QPushButton(nombre)
            b.setCheckable(True)
            b.setChecked(nombre == "10-20")
            b.setProperty("segmento", "true")
            b.clicked.connect(lambda _=False, n=nombre: self.cabeza.poner_sistema(n))
            grupo_sis.addButton(b)
            fila.addWidget(b, 1)
        pcol.addLayout(fila)
        pcol.addStretch(1)
        self.btn_limpiar = QPushButton(" Sacar todos")
        self.btn_limpiar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_SUAVE, tam=14))
        self.btn_limpiar.clicked.connect(self.limpiar)
        pcol.addWidget(self.btn_limpiar)
        raiz.addWidget(panel)

        self.colocados = {}
        self._elegir_rol("activo")
        self._pintar()

    def _elegir_rol(self, clave):
        self.rol_actual = clave
        self.botones_rol[clave].setChecked(True)

    def _poner(self, sitio):
        # Un sitio lleva un solo electrodo: si había otro ahí, se saca.
        for rol, s in list(self.colocados.items()):
            if s == sitio:
                del self.colocados[rol]
        self.colocados[self.rol_actual] = sitio
        # Pasa solo al siguiente que falta, como quien va poniendo los tres.
        falta = next((c for c, _, _ in ROLES if c not in self.colocados), None)
        if falta:
            self._elegir_rol(falta)
        self._pintar()

    def _quitar(self, clave):
        self.colocados.pop(clave, None)
        self._elegir_rol(clave)
        self._pintar()

    def limpiar(self):
        self.colocados = {}
        self._elegir_rol("activo")
        self._pintar()

    def _pintar(self):
        for clave, lbl in self.lbl_puesto.items():
            sitio = self.colocados.get(clave)
            lbl.setText(nombre_sitio(sitio) if sitio else "sin poner")
            lbl.setProperty("vacio", "false" if sitio else "true")
            tema.repintar(lbl)
        self.cabeza.poner(self.colocados)
        self.montaje_cambio.emit(dict(self.colocados))
