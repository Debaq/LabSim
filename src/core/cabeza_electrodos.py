"""
Cabeza giratoria para poner los electrodos de las pruebas electrofisiológicas.

La cabeza y los sitios 10-20 / 10-10 son los de labyrinthus3d, fotografiados
desde muchos ángulos (cada 2° de giro y cada 10° de inclinación): ver
scripts/cabeza_electrodos/. No es 3D en vivo -- el build no usa OpenGL, ver
LabSim.spec --, pero al arrastrar gira como si lo fuera. Cada cuadro trae
dónde cae cada sitio visible, así que los electrodos se dibujan encima y un
clic elige el sitio más cercano.

    CabezaElectrodos  la cabeza sola: gira, marca sitios, frota con el
                      algodón, avisa el clic
    Piel              cómo quedó la piel de cada sitio (alcohol, gel)
    Impedancias       cuánto da cada electrodo puesto, según esa piel
    MontajeElectrodos la cabeza con el panel: preparar la piel, poner activo,
                      referencia y tierra, medir impedancias (prototipo:
                      todavía no va conectado a los módulos)

El orden es el de la práctica: alcohol con algodón, gel exfoliante con
algodón (siempre en la misma dirección), electrodos, medir. Lo que se hace
mal no se avisa con mensajes: se ve en la piel (irritada) o en la impedancia,
y queda anotado en `Impedancias.errores` para la evaluación.
"""
import json
import math
import random
import time
from collections import OrderedDict

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QProgressBar, QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from core import iconos, tema
from core.base import context

# Colores de los cables: derecha roja e izquierda azul como OD/OI en todo
# LabSim; el activo blanco para no confundirse con la derecha (decidido por
# el autor, 2026-10-28). Con dos canales los cables son de lado (derecha e
# izquierda), no ipsi y contra: eso lo arma el equipo según el oído que se
# estimula.
BLANCO_BORDE = "#5E5360"
ROLES = (
    ("activo", "Activo (+)", "#FFFFFF"),
    ("referencia", "Referencia (−)", tema.OI),
    ("ref_der", "Ref. derecha (−)", tema.OD),
    ("ref_izq", "Ref. izquierda (−)", tema.OI),
    ("tierra", "Tierra", "#3AA655"),
)
COLOR_ROL = {clave: color for clave, _, color in ROLES}
NOMBRE_ROL = {clave: nombre for clave, nombre, _ in ROLES}
# Un canal: activo menos su referencia. Dos canales: el mismo activo contra
# la mastoides (o el lóbulo) de cada lado.
ROLES_POR_CANALES = {
    1: ("activo", "referencia", "tierra"),
    2: ("activo", "ref_der", "ref_izq", "tierra"),
}


def _borde(color):
    """El blanco necesita borde oscuro para verse sobre la piel y la tarjeta."""
    return BLANCO_BORDE if color.upper() == "#FFFFFF" else "white"


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


def corto_sitio(sitio_id):
    d = datos()
    i = d["por_id"].get(sitio_id)
    return d["sitios"][i]["corto"] if i is not None else sitio_id


# Impedancia de la piel sin preparar, en kΩ, según el sitio: el cuero
# cabelludo (con pelo y más grueso) da más que la frente o la mastoides. Se
# sortea por sitio: no hay un valor de fábrica que el alumno pueda aprenderse.
# Sin alcohol ni gel, ningún electrodo queda en norma.
RANGO_KOHM = {
    "frente": (8.0, 25.0), "lobulo": (8.0, 25.0), "mastoides": (8.0, 25.0),
    "mejilla": (8.0, 22.0), "infraorbital": (8.0, 22.0), "menton": (8.0, 22.0),
    "cae": (10.0, 30.0),
}
RANGO_CUERO_CABELLUDO = (15.0, 40.0)
PISO_KOHM = (0.8, 2.0)    # lo más bajo que llega esa piel, por bien preparada que esté
ESCALA_KOHM = 20.0       # tope de la barra

# Preparación de la piel. Son criterio de trabajo para que el ejercicio
# funcione, no cifras de una norma: ajustarlas acá.
ALCOHOL_FACTOR = {1: 0.85, 2: 0.70}   # pasadas de alcohol -> lo que queda (2 o más: 0.70)
GEL_POR_PASADA = 0.78                 # cada pasada de gel en la misma dirección
GEL_SIN_ALCOHOL = 0.90                # con la grasa todavía ahí rinde menos
GEL_MAX_PASADAS = 10                  # sobre esto la piel se irrita y ya no baja
IDA_Y_VUELTA_PARA_IRRITAR = 3         # pasadas de ida y vuelta que irritan
PASADA_MIN_PX = 25                    # un arrastre más corto no es una pasada
# Recorrido / desplazamiento neto sobre esto: frotó de ida y vuelta.
IDA_Y_VUELTA = 1.6
BRILLO_S = 3.0                        # cuánto se ve húmedo el alcohol


def limites():
    """Los límites clínicos del generador del ABR: cada electrodo y el desbalance."""
    from abr.ABR_generator import IMPEDANCE_BALANCE_LIMIT_KOHM, IMPEDANCE_LIMIT_KOHM
    return IMPEDANCE_LIMIT_KOHM, IMPEDANCE_BALANCE_LIMIT_KOHM


class Piel:
    """La piel de cada sitio: su impedancia sin preparar (sorteada por zona),
    su piso, y las pasadas de alcohol y de gel que lleva."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.base, self.piso = {}, {}
        self.alcohol, self.gel, self.ida_vuelta = {}, {}, {}
        self.irritada = set()
        self.brillo = {}          # sitio -> cuándo se le pasó alcohol (monotonic)
        self.errores = []         # lo que estuvo mal hecho, para la evaluación

    def _sortear(self, sitio):
        if sitio in self.base:
            return
        d = datos()
        zona = d["sitios"][d["por_id"][sitio]]["zona"]
        self.base[sitio] = self.rng.uniform(*RANGO_KOHM.get(zona, RANGO_CUERO_CABELLUDO))
        self.piso[sitio] = self.rng.uniform(*PISO_KOHM)

    def pasada(self, sitio, herramienta, misma_direccion=True):
        """Una pasada de algodón con alcohol o con gel exfoliante."""
        self._sortear(sitio)
        if herramienta == "alcohol":
            self.alcohol[sitio] = self.alcohol.get(sitio, 0) + 1
            self.brillo[sitio] = time.monotonic()
            return
        if not self.alcohol.get(sitio) and not self.gel.get(sitio):
            self.errores.append(("gel_sin_alcohol", sitio))
        if misma_direccion:
            self.gel[sitio] = self.gel.get(sitio, 0) + 1.0
        else:
            # De ida y vuelta saca menos y lastima más.
            self.gel[sitio] = self.gel.get(sitio, 0) + 0.5
            self.ida_vuelta[sitio] = self.ida_vuelta.get(sitio, 0) + 1
            self.errores.append(("ida_y_vuelta", sitio))
        if sitio not in self.irritada and (self.gel[sitio] > GEL_MAX_PASADAS or
                                           self.ida_vuelta.get(sitio, 0) >= IDA_Y_VUELTA_PARA_IRRITAR):
            self.irritada.add(sitio)
            self.errores.append(("piel_irritada", sitio))

    def preparada(self, sitio):
        return bool(self.alcohol.get(sitio) or self.gel.get(sitio))

    def impedancia(self, sitio):
        """Lo que daría un electrodo puesto ahora en ese sitio, en kΩ."""
        self._sortear(sitio)
        z = self.base[sitio]
        alcohol = self.alcohol.get(sitio, 0)
        if alcohol:
            z *= ALCOHOL_FACTOR[min(alcohol, 2)]
        gel = min(self.gel.get(sitio, 0), GEL_MAX_PASADAS)
        if gel:
            z *= (GEL_POR_PASADA if alcohol else GEL_SIN_ALCOHOL) ** gel
        return max(self.piso[sitio], z)

    def resumen(self, sitio):
        if sitio in self.irritada:
            return "piel irritada"
        partes = []
        if self.alcohol.get(sitio):
            partes.append("alcohol ✓")
        if self.gel.get(sitio):
            g = self.gel[sitio]
            partes.append(f"gel {g:g}")
        return " · ".join(partes) or "sin preparar"


class Impedancias:
    """La impedancia de cada electrodo puesto: la de la piel de su sitio en
    el momento de ponerlo. Se ve solo después de medir, como en el equipo:
    lo que cambió desde la última medición queda sin medir."""

    def __init__(self, rng=None):
        self.piel = Piel(rng)
        self.z = {}           # rol -> kΩ
        self.medido = {}      # rol -> kΩ de la última medición (o falta)

    @property
    def errores(self):
        return self.piel.errores

    def poner(self, rol, sitio):
        if not self.piel.preparada(sitio):
            self.piel.errores.append(("electrodo_sin_preparar", sitio))
        self.z[rol] = self.piel.impedancia(sitio)
        self.medido.pop(rol, None)

    def quitar(self, rol):
        for dic in (self.z, self.medido):
            dic.pop(rol, None)

    def renombrar(self, viejo, nuevo):
        """El mismo electrodo cambia de papel (al pasar de 1 a 2 canales)."""
        for dic in (self.z, self.medido):
            if viejo in dic:
                dic[nuevo] = dic.pop(viejo)

    def medir(self):
        self.medido = dict(self.z)
        return self.medido

    def informe(self):
        """(peor, desbalance, dentro_de_norma) de lo medido, o None."""
        if not self.medido or len(self.medido) < len(self.z):
            return None
        limite, balance = limites()
        valores = list(self.medido.values())
        peor, desbalance = max(valores), max(valores) - min(valores)
        return peor, desbalance, peor <= limite and desbalance <= balance

    def estado(self, rol):
        """'ok', 'aviso' o 'alerta' de lo medido de un electrodo, o None."""
        z = self.medido.get(rol)
        if z is None:
            return None
        limite, _ = limites()
        return "ok" if z <= limite else ("aviso" if z <= 2 * limite else "alerta")


COLOR_ESTADO = {"ok": tema.OK, "aviso": tema.AVISO, "alerta": tema.ALERTA}


HERRAMIENTAS = (
    ("girar", "Girar"),
    ("alcohol", "Alcohol"),
    ("gel", "Gel exfoliante"),
    ("electrodo", "Electrodo"),
)


class CabezaElectrodos(QWidget):
    """La cabeza. Arrastrar fuera de un sitio la gira. Con alcohol o gel,
    arrastrar sobre un sitio es una pasada de algodón (`pasada`); con el
    electrodo, el clic en un sitio emite `sitio_elegido`."""
    sitio_elegido = Signal(str)
    pasada = Signal(str, str, bool)     # sitio, herramienta, misma dirección

    def __init__(self, parent=None):
        super().__init__(parent)
        self.d = datos()
        self.yaws = self.d["yaws"]
        self.pitches = self.d["pitches"]
        self.giro = 0.0           # grados, continuo; se ajusta al cuadro más cercano
        self.inclinacion = 0.0
        self.sistema = "10-20"
        self.colocados = {}       # rol -> sitio
        self.estados = {}         # rol -> 'ok'/'aviso'/'alerta' de la impedancia medida
        self.herramienta = "girar"
        self.piel = None          # Piel, para dibujar cómo quedó cada sitio
        self._sobre = None        # sitio bajo el mouse
        self._apretado = None
        self._arrastrando = False
        self._trazo = None        # la pasada en curso: sitio y recorrido
        self._dir_previa = {}     # sitio -> dirección de su última pasada
        self._brillo = QTimer(self)
        self._brillo.setInterval(80)
        self._brillo.timeout.connect(self._mientras_brilla)
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

    def poner_herramienta(self, herramienta):
        self.herramienta = herramienta
        self.update()

    def _mientras_brilla(self):
        if not self.piel or not any(time.monotonic() - t < BRILLO_S for t in self.piel.brillo.values()):
            self._brillo.stop()
        self.update()

    def poner(self, colocados, estados=None):
        self.colocados = dict(colocados)
        self.estados = dict(estados or {})
        self.update()

    # ------------------------------------------------------------ dibujo
    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        marco, _escala = self._marco()
        p.drawPixmap(marco, self._pixmap(self._clave()), QRectF(0, 0, self.d["tam"], self.d["tam"]))

        rol_de = {sitio: rol for rol, sitio in self.colocados.items()}
        self._dibujar_piel(p)
        fuente = QFont(self.font())
        fuente.setPointSizeF(7.5)
        fuente.setBold(True)
        p.setFont(fuente)
        for s, pt in self._visibles():
            rol = rol_de.get(s["id"])
            sobre = s["id"] == self._sobre
            if rol:
                estado = self.estados.get(rol)
                if estado:
                    # Anillo con lo que dio la impedancia, como la luz del equipo.
                    p.setPen(QPen(QColor(COLOR_ESTADO[estado]), 3))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawEllipse(pt, 11, 11)
                p.setPen(QPen(QColor(_borde(COLOR_ROL[rol])), 2))
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
                texto_color = BLANCO_BORDE if rol and _borde(COLOR_ROL[rol]) == BLANCO_BORDE \
                    else (COLOR_ROL[rol] if rol else tema.ACENTO)
                p.setPen(QColor(texto_color))
                p.drawText(caja, Qt.AlignmentFlag.AlignCenter, texto)
        if self._trazo is not None and self._trazo["puntos"]:
            # El algodón bajo el dedo.
            ultimo = self._trazo["puntos"][-1]
            p.setPen(QPen(QColor("#C9C2C8"), 1))
            p.setBrush(QColor(255, 255, 255, 235))
            p.drawEllipse(ultimo, 9, 9)
        p.end()

    def _dibujar_piel(self, p):
        """Cómo quedó la piel: húmeda del alcohol unos segundos, rosada con
        el gel (más con cada pasada), roja si se irritó."""
        if self.piel is None:
            return
        ahora = time.monotonic()
        p.setPen(Qt.PenStyle.NoPen)
        for s, pt in self._visibles():
            sitio = s["id"]
            if sitio in self.piel.irritada:
                p.setBrush(QColor(205, 30, 30, 165))
                p.drawEllipse(pt, 13, 13)
            elif self.piel.gel.get(sitio):
                alfa = int(min(30 + 10 * self.piel.gel[sitio], 120))
                p.setBrush(QColor(240, 150, 150, alfa))
                p.drawEllipse(pt, 12, 12)
            t = self.piel.brillo.get(sitio)
            if t is not None and ahora - t < BRILLO_S:
                alfa = int(170 * (1 - (ahora - t) / BRILLO_S))
                p.setBrush(QColor(235, 245, 255, alfa))
                p.drawEllipse(pt, 12, 12)

    # ------------------------------------------------------------ mouse
    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        if self.herramienta in ("alcohol", "gel"):
            sitio = self._sitio_en(ev.position())
            if sitio:
                self._trazo = {"sitio": sitio, "puntos": [ev.position()]}
                self.update()
                return
        self._apretado = (ev.position(), self.giro, self.inclinacion)
        self._arrastrando = False

    def mouseMoveEvent(self, ev):
        if self._trazo is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            self._trazo["puntos"].append(ev.position())
            self.update()
            return
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
            if sobre and self.herramienta in ("alcohol", "gel"):
                cursor = Qt.CursorShape.CrossCursor
            elif sobre and self.herramienta == "electrodo":
                cursor = Qt.CursorShape.PointingHandCursor
            else:
                cursor = Qt.CursorShape.OpenHandCursor
            self.setCursor(cursor)
            texto = nombre_sitio(sobre) if sobre else ""
            if sobre and self.piel is not None:
                texto += f" — {self.piel.resumen(sobre)}"
            self.setToolTip(texto)
            self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self._trazo is not None:
            trazo, self._trazo = self._trazo, None
            trazo["puntos"].append(ev.position())
            self._terminar_pasada(trazo["sitio"], trazo["puntos"])
            self.update()
            return
        if ev.button() != Qt.MouseButton.LeftButton or self._apretado is None:
            return
        arrastro = self._arrastrando
        self._apretado = None
        self._arrastrando = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if not arrastro and self.herramienta == "electrodo":
            sitio = self._sitio_en(ev.position())
            if sitio:
                self.sitio_elegido.emit(sitio)

    def _terminar_pasada(self, sitio, puntos):
        """Una pasada si recorrió lo suficiente. Es "en la misma dirección" si
        no fue y volvió dentro del arrastre y si va para el mismo lado que la
        pasada anterior en ese sitio."""
        recorrido = sum(math.hypot(b.x() - a.x(), b.y() - a.y()) for a, b in zip(puntos, puntos[1:]))
        if recorrido < PASADA_MIN_PX:
            return
        dx, dy = puntos[-1].x() - puntos[0].x(), puntos[-1].y() - puntos[0].y()
        neto = math.hypot(dx, dy)
        misma = recorrido <= IDA_Y_VUELTA * neto
        if neto > 0:
            direccion = (dx / neto, dy / neto)
            previa = self._dir_previa.get(sitio)
            if previa is not None and previa[0] * direccion[0] + previa[1] * direccion[1] < 0:
                misma = False
            self._dir_previa[sitio] = direccion
        self.pasada.emit(sitio, self.herramienta, misma)
        if self.herramienta == "alcohol":
            self._brillo.start()

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
QPushButton[herramienta="true"] {{ padding: 5px 0px; font-weight: 600; }}
QPushButton[herramienta="true"]:checked {{ background: {tema.ACENTO}; border-color: {tema.ACENTO}; color: white; }}
QLabel#puesto {{ color: {tema.TEXTO}; font-weight: 600; }}
QLabel#puesto[vacio="true"] {{ color: {tema.TEXTO_TENUE}; font-weight: 400; }}
QLabel#kohm {{ font-weight: 700; color: {tema.TEXTO_TENUE}; }}
QLabel#kohm[estado="ok"] {{ color: {tema.OK}; }}
QLabel#kohm[estado="aviso"] {{ color: {tema.AVISO}; }}
QLabel#kohm[estado="alerta"] {{ color: {tema.ALERTA}; }}
QProgressBar {{
    background: {tema.GRILLA}; border: none; border-radius: 3px;
    min-height: 6px; max-height: 6px;
}}
QProgressBar::chunk {{ border-radius: 3px; background: {tema.TEXTO_TENUE}; }}
QProgressBar[estado="ok"]::chunk {{ background: {tema.OK}; }}
QProgressBar[estado="aviso"]::chunk {{ background: {tema.AVISO}; }}
QProgressBar[estado="alerta"]::chunk {{ background: {tema.ALERTA}; }}
QPushButton[chico="true"] {{ padding: 2px 8px; font-size: 8pt; }}
QPushButton[primario="true"] {{
    background: {tema.ACENTO}; border-color: {tema.ACENTO}; color: white; font-weight: 600;
}}
QPushButton[primario="true"]:hover {{ background: {tema.ACENTO_CLARO}; color: white; }}
QPushButton[primario="true"]:disabled {{
    background: {tema.TARJETA_ALT}; border-color: {tema.BORDE}; color: {tema.TEXTO_TENUE};
}}
"""


def _punto(color, tam=12):
    pm = QPixmap(tam * 2, tam * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(_borde(color)), 3))
    p.setBrush(QColor(color))
    p.drawEllipse(QRectF(2, 2, tam * 2 - 4, tam * 2 - 4))
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


class MontajeElectrodos(QWidget):
    """Prototipo: la cabeza y un panel para poner activo, referencia y tierra
    y medir sus impedancias."""
    montaje_cambio = Signal(dict)

    def __init__(self, parent=None, rng=None):
        super().__init__(parent)
        self.impedancias = Impedancias(rng)
        tema.aplicar_estilo(self, EXTRA_QSS)
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(12, 10, 12, 12)
        raiz.setSpacing(10)

        lienzo = QFrame()
        lienzo.setProperty("card", "true")
        col = QVBoxLayout(lienzo)
        col.setContentsMargins(8, 8, 8, 8)
        self.cabeza = CabezaElectrodos()
        self.cabeza.piel = self.impedancias.piel
        self.cabeza.sitio_elegido.connect(self._poner)
        self.cabeza.pasada.connect(self._pasada)
        col.addWidget(self.cabeza, 1)
        herramientas = QHBoxLayout()
        herramientas.setSpacing(4)
        grupo_her = QButtonGroup(self)
        self.botones_herramienta = {}
        for clave, nombre in HERRAMIENTAS:
            b = QPushButton(nombre)
            b.setCheckable(True)
            b.setProperty("herramienta", "true")
            b.clicked.connect(lambda _=False, c=clave: self.elegir_herramienta(c))
            grupo_her.addButton(b)
            herramientas.addWidget(b, 1)
            self.botones_herramienta[clave] = b
        col.addLayout(herramientas)
        vistas = QHBoxLayout()
        vistas.setSpacing(4)
        for nombre, giro, incl in VISTAS:
            b = QPushButton(nombre)
            b.setProperty("segmento", "true")
            b.clicked.connect(lambda _=False, g=giro, i=incl: self.cabeza.mirar(g, i))
            vistas.addWidget(b, 1)
        col.addLayout(vistas)
        self.pista = QLabel()
        self.pista.setProperty("role", "hint")
        self.pista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.pista)
        raiz.addWidget(lienzo, 1)

        panel = QFrame()
        panel.setProperty("card", "true")
        panel.setFixedWidth(262)
        pcol = QVBoxLayout(panel)
        pcol.setContentsMargins(12, 10, 12, 12)
        pcol.setSpacing(6)
        seccion = QLabel("CANALES")
        seccion.setProperty("role", "seccion")
        pcol.addWidget(seccion)
        fila = QHBoxLayout()
        fila.setSpacing(4)
        grupo_can = QButtonGroup(self)
        self.botones_canales = {}
        for n, texto in ((1, "1 canal"), (2, "2 canales")):
            b = QPushButton(texto)
            b.setCheckable(True)
            b.setChecked(n == 1)
            b.setProperty("segmento", "true")
            b.clicked.connect(lambda _=False, c=n: self.poner_canales(c))
            grupo_can.addButton(b)
            fila.addWidget(b, 1)
            self.botones_canales[n] = b
        pcol.addLayout(fila)
        pcol.addSpacing(4)
        seccion = QLabel("ELECTRODO")
        seccion.setProperty("role", "seccion")
        pcol.addWidget(seccion)
        self.grupo = QButtonGroup(self)
        self.botones_rol = {}
        self.lbl_puesto = {}
        self.widgets_rol = {}     # rol -> widgets de su fila (se esconden según los canales)
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(4)
        grilla.setVerticalSpacing(4)
        grilla.setColumnStretch(0, 1)
        for i, (clave, nombre, color) in enumerate(ROLES):
            b = QPushButton(" " + nombre)
            b.setIcon(_punto(color))
            b.setCheckable(True)
            b.setProperty("rol", clave)
            b.clicked.connect(lambda _=False, c=clave: self._elegir_rol(c, herramienta=True))
            self.grupo.addButton(b)
            self.botones_rol[clave] = b
            puesto = QLabel()
            puesto.setObjectName("puesto")
            self.lbl_puesto[clave] = puesto
            puesto.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grilla.addWidget(b, i, 0)
            grilla.addWidget(puesto, i, 1)
            quitar = QPushButton()
            quitar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_TENUE, tam=12))
            quitar.setToolTip("Quitar este electrodo")
            quitar.setFixedSize(24, 22)
            quitar.clicked.connect(lambda _=False, c=clave: self._quitar(c))
            grilla.addWidget(quitar, i, 2)
            self.widgets_rol[clave] = [b, puesto, quitar]
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

        pcol.addSpacing(6)
        pcol.addLayout(self._seccion_impedancias())
        pcol.addStretch(1)
        self.btn_limpiar = QPushButton(" Sacar todos")
        self.btn_limpiar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_SUAVE, tam=14))
        self.btn_limpiar.clicked.connect(self.limpiar)
        pcol.addWidget(self.btn_limpiar)
        raiz.addWidget(panel)

        self.colocados = {}
        self.canales = 1
        self._mostrar_roles()
        self._elegir_rol("activo")
        self.elegir_herramienta("girar")
        self._pintar()

    PISTAS = {
        "girar": "Arrastra para girar la cabeza.",
        "alcohol": "Pasa el algodón con alcohol: arrastra sobre el sitio.",
        "gel": "Pasa el algodón con gel exfoliante: arrastra sobre el sitio.",
        "electrodo": "Clic en un sitio pone el electrodo elegido.",
    }

    def elegir_herramienta(self, clave):
        self.botones_herramienta[clave].setChecked(True)
        self.cabeza.poner_herramienta(clave)
        self.pista.setText(self.PISTAS[clave] + " Fuera de los sitios, arrastrar gira la cabeza."
                           if clave != "girar" else self.PISTAS[clave])

    def _pasada(self, sitio, herramienta, misma):
        if sitio in self.colocados.values():
            # Con el electrodo puesto no se puede frotar esa piel.
            self.pista.setText("Ese sitio tiene un electrodo: sácalo para volver a preparar la piel.")
            return
        self.impedancias.piel.pasada(sitio, herramienta, misma)
        self._pintar()

    def roles(self):
        return ROLES_POR_CANALES[self.canales]

    def poner_canales(self, n):
        """1 o 2 canales. Al pasar a dos, la referencia ya puesta queda como
        la del lado donde está (derecha si está en la línea media); al volver
        a uno, queda la derecha (o la izquierda si es la única) y la otra se
        saca."""
        if n == self.canales:
            return
        if n == 2 and "referencia" in self.colocados:
            d = datos()
            lado = d["sitios"][d["por_id"][self.colocados["referencia"]]].get("lado")
            nuevo = "ref_izq" if lado == "izq" else "ref_der"
            self.colocados[nuevo] = self.colocados.pop("referencia")
            self.impedancias.renombrar("referencia", nuevo)
        elif n == 1:
            viejo = "ref_der" if "ref_der" in self.colocados else "ref_izq"
            if viejo in self.colocados:
                self.colocados["referencia"] = self.colocados.pop(viejo)
                self.impedancias.renombrar(viejo, "referencia")
        for rol in list(self.colocados):
            if rol not in ROLES_POR_CANALES[n]:
                self.colocados.pop(rol)
                self.impedancias.quitar(rol)
        self.canales = n
        self.botones_canales[n].setChecked(True)
        self._mostrar_roles()
        falta = next((c for c in self.roles() if c not in self.colocados), self.roles()[0])
        self._elegir_rol(falta)
        self._pintar()

    def _mostrar_roles(self):
        for rol, widgets in self.widgets_rol.items():
            for w in widgets + list(self.filas_imp[rol]) + [self.puntos_imp[rol]]:
                w.setVisible(rol in self.roles())

    def _seccion_impedancias(self):
        col = QVBoxLayout()
        col.setSpacing(4)
        cab = QHBoxLayout()
        seccion = QLabel("IMPEDANCIAS")
        seccion.setProperty("role", "seccion")
        cab.addWidget(seccion, 1)
        self.btn_medir = QPushButton("Medir")
        self.btn_medir.setProperty("primario", "true")
        self.btn_medir.setProperty("chico", "true")
        self.btn_medir.clicked.connect(self.medir)
        cab.addWidget(self.btn_medir)
        col.addLayout(cab)
        self.filas_imp = {}
        self.puntos_imp = {}
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(6)
        grilla.setVerticalSpacing(2)
        for i, (clave, nombre, color) in enumerate(ROLES):
            punto = QLabel()
            punto.setPixmap(_punto(color, 10))
            valor = QLabel("—")
            valor.setObjectName("kohm")
            valor.setMinimumWidth(56)
            barra = QProgressBar()
            barra.setRange(0, int(ESCALA_KOHM * 10))
            barra.setTextVisible(False)
            piel = QLabel()
            piel.setProperty("role", "hint")
            sacar = QPushButton("Sacar")
            sacar.setProperty("chico", "true")
            sacar.setToolTip("Sacar el electrodo para volver a preparar la piel")
            sacar.clicked.connect(lambda _=False, c=clave: self._quitar(c))
            grilla.addWidget(punto, i * 2, 0)
            grilla.addWidget(valor, i * 2, 1)
            grilla.addWidget(piel, i * 2, 2)
            grilla.addWidget(sacar, i * 2, 3)
            grilla.addWidget(barra, i * 2 + 1, 0, 1, 4)
            self.filas_imp[clave] = (valor, barra, sacar, piel)
            self.puntos_imp[clave] = punto
        grilla.setColumnStretch(1, 1)
        col.addLayout(grilla)
        self.lbl_desbalance = QLabel()
        self.lbl_desbalance.setWordWrap(True)
        self.lbl_desbalance.setProperty("role", "hint")
        col.addWidget(self.lbl_desbalance)
        return col

    def medir(self):
        self.impedancias.medir()
        self._pintar()

    def _pintar_impedancias(self):
        limite, balance = limites()
        for clave, (valor, barra, sacar, piel) in self.filas_imp.items():
            puesto = clave in self.colocados
            z = self.impedancias.medido.get(clave)
            estado = self.impedancias.estado(clave)
            if not puesto:
                valor.setText("—")
            elif z is None:
                valor.setText("sin medir")
            else:
                valor.setText(f"{z:.1f} kΩ")
            barra.setValue(int(min(z or 0, ESCALA_KOHM) * 10))
            for w in (valor, barra):
                w.setProperty("estado", estado or "")
                tema.repintar(w)
            sacar.setEnabled(puesto)
            sitio = self.colocados.get(clave)
            piel.setText(self.impedancias.piel.resumen(sitio) if sitio else "")
        self.btn_medir.setEnabled(bool(self.colocados))
        informe = self.impedancias.informe()
        if informe is None:
            texto = (f"Cada electrodo bajo {limite:.0f} kΩ y entre ellos menos de "
                     f"{balance:.0f} kΩ de diferencia.")
            estado = ""
        else:
            peor, desbalance, ok = informe
            texto = (f"Diferencia entre electrodos: {desbalance:.1f} kΩ. " +
                     ("Listo para registrar." if ok else
                      "Fuera de norma."))
            estado = "ok" if ok else "alerta"
        self.lbl_desbalance.setText(texto)
        self.lbl_desbalance.setProperty("estado", estado)
        tema.repintar(self.lbl_desbalance)

    def _elegir_rol(self, clave, herramienta=False):
        self.rol_actual = clave
        self.botones_rol[clave].setChecked(True)
        if herramienta:
            self.elegir_herramienta("electrodo")

    def _poner(self, sitio):
        # Un sitio lleva un solo electrodo: si había otro ahí, se saca.
        for rol, s in list(self.colocados.items()):
            if s == sitio:
                del self.colocados[rol]
                self.impedancias.quitar(rol)
        self.colocados[self.rol_actual] = sitio
        self.impedancias.poner(self.rol_actual, sitio)
        # Pasa solo al siguiente que falta, como quien va poniendo los tres.
        falta = next((c for c in self.roles() if c not in self.colocados), None)
        if falta:
            self._elegir_rol(falta)
        self._pintar()

    def _quitar(self, clave):
        self.colocados.pop(clave, None)
        self.impedancias.quitar(clave)
        self._elegir_rol(clave)
        self._pintar()

    @property
    def errores(self):
        """Lo mal hecho en la preparación, para la evaluación (no se muestra)."""
        return list(self.impedancias.errores)

    def limpiar(self):
        """Sacar todos los electrodos. La piel queda como estaba."""
        self.colocados = {}
        self.impedancias.z.clear()
        self.impedancias.medido.clear()
        self._elegir_rol("activo")
        self._pintar()

    def _pintar(self):
        for clave, lbl in self.lbl_puesto.items():
            sitio = self.colocados.get(clave)
            lbl.setText(corto_sitio(sitio) if sitio else "—")
            lbl.setToolTip(nombre_sitio(sitio) if sitio else "Sin poner")
            lbl.setProperty("vacio", "false" if sitio else "true")
            tema.repintar(lbl)
        estados = {rol: self.impedancias.estado(rol) for rol in self.colocados
                   if self.impedancias.estado(rol)}
        self.cabeza.poner(self.colocados, estados)
        self._pintar_impedancias()
        self.montaje_cambio.emit(dict(self.colocados))
