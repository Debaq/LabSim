"""
Cabeza giratoria para preparar la piel y poner los electrodos de las pruebas
electrofisiológicas.

La cabeza y los sitios 10-20 / 10-10 son los de labyrinthus3d, fotografiados
desde muchos ángulos (cada 2° de giro y cada 10° de inclinación): ver
scripts/cabeza_electrodos/. No es 3D en vivo -- el build no usa OpenGL, ver
LabSim.spec --, pero junto con las fotos viene la piel (`malla.npz`) y la
cámara exacta con que se tomaron. Con eso cada punto del mouse cae en un
punto de la piel 3D (`Geometria.rayo`) y cada punto de la piel se dibuja en
cualquier foto (`Geometria.proyectar`): la limpieza queda pintada donde se
frotó y gira con la cabeza, y los electrodos van donde el alumno los pone,
no a un punto de la norma. Así se ve si los pone en su lugar y sobre lo que
limpió.

    Geometria         la piel y la cámara: del mouse a la piel y de vuelta
    Piel              las pasadas de algodón (alcohol, gel) y lo que dejan en
                      cada punto: impedancia, irritación
    Impedancias       cuánto da cada electrodo puesto, según la piel donde quedó
    CabezaElectrodos  la cabeza: gira, frota, pone, dibuja
    MontajeElectrodos la cabeza con el panel (prototipo: todavía no va
                      conectado a los módulos)

El orden es el de la práctica: alcohol con algodón, gel exfoliante con
algodón (siempre en la misma dirección), electrodos, medir. Lo que se hace
mal no se avisa con mensajes: se ve en la piel (irritada) o en la impedancia,
y queda anotado en `Piel.errores` para la evaluación.
"""
import json
import math
import random
import time
from collections import OrderedDict

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
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
CUADROS_EN_MEMORIA = 80

# --- La piel -----------------------------------------------------------
# Impedancia sin preparar, en kΩ, según la zona: el cuero cabelludo (con
# pelo y más grueso) da más que la frente o la mastoides. Se sortea por
# sitio de la norma y vale para la piel que lo rodea: no hay un valor de
# fábrica que el alumno pueda aprenderse. Sin alcohol ni gel, ningún
# electrodo queda en norma.
RANGO_KOHM = {
    "frente": (8.0, 25.0), "lobulo": (8.0, 25.0), "mastoides": (8.0, 25.0),
    "mejilla": (8.0, 22.0), "infraorbital": (8.0, 22.0), "menton": (8.0, 22.0),
    "cae": (10.0, 30.0),
}
RANGO_CUERO_CABELLUDO = (15.0, 40.0)
PISO_KOHM = (0.8, 2.0)    # lo más bajo que llega esa piel, por bien preparada que esté
ESCALA_KOHM = 20.0        # tope de la barra

# Preparación. Son criterio de trabajo para que el ejercicio funcione, no
# cifras de una norma: ajustarlas acá.
PINCEL_M = 0.008                      # radio de lo que limpia el algodón: 8 mm
ALCOHOL_FACTOR = {1: 0.85, 2: 0.70}   # pasadas de alcohol -> lo que queda (2 o más: 0.70)
GEL_POR_PASADA = 0.78                 # cada pasada de gel en la misma dirección
GEL_SIN_ALCOHOL = 0.90                # con la grasa todavía ahí rinde menos
GEL_MAX_PASADAS = 10                  # sobre esto la piel se irrita y ya no baja
IDA_Y_VUELTA_PARA_IRRITAR = 3         # pasadas de ida y vuelta que irritan
PASADA_MIN_PX = 25                    # un arrastre más corto no es una pasada
IDA_Y_VUELTA = 1.6                    # recorrido / desplazamiento neto sobre esto
BRILLO_S = 3.0                        # cuánto se ve húmedo el alcohol
PASO_TRAZO_M = 0.002                  # los trazos se guardan con un punto cada 2 mm
UN_ELECTRODO_M = 0.010                # dos electrodos a menos de 1 cm: el nuevo saca al otro

_datos = None
_geometria = None


def datos():
    """El paquete de la cabeza (resources/cabeza): se lee una vez."""
    global _datos
    if _datos is None:
        with open(context.get_resource("cabeza/cabeza.json"), encoding="utf-8") as f:
            info = json.load(f)
        with open(context.get_resource("cabeza/cabeza.bin"), "rb") as f:
            info["bin"] = f.read()
        info["por_id"] = {s["id"]: i for i, s in enumerate(info["sitios"])}
        info["pos"] = np.array([s["pos"] for s in info["sitios"]], dtype=float)
        info["normales"] = np.array([s["normal"] for s in info["sitios"]], dtype=float)
        _datos = info
    return _datos


def geometria():
    global _geometria
    if _geometria is None:
        _geometria = Geometria()
    return _geometria


def nombre_sitio(sitio_id):
    d = datos()
    i = d["por_id"].get(sitio_id)
    return d["sitios"][i]["nombre"] if i is not None else sitio_id


def corto_sitio(sitio_id):
    d = datos()
    i = d["por_id"].get(sitio_id)
    return d["sitios"][i]["corto"] if i is not None else sitio_id


def sitio_cercano(punto):
    """(id del sitio de la norma más cercano, distancia en m)."""
    d = datos()
    dist = np.linalg.norm(d["pos"] - punto, axis=1)
    i = int(np.argmin(dist))
    return d["sitios"][i]["id"], float(dist[i])


def limites():
    """Los límites clínicos del generador del ABR: cada electrodo y el desbalance."""
    from abr.ABR_generator import IMPEDANCE_BALANCE_LIMIT_KOHM, IMPEDANCE_LIMIT_KOHM
    return IMPEDANCE_LIMIT_KOHM, IMPEDANCE_BALANCE_LIMIT_KOHM


class Geometria:
    """La piel de cabeza.glb y la cámara de las fotos (la misma de
    scripts/cabeza_electrodos/captura.html: la cabeza gira con Euler XYZ de
    three.js y la cámara queda fija)."""

    def __init__(self):
        d = datos()
        cam = d["camara"]
        malla = np.load(context.get_resource("cabeza/malla.npz"))
        v, c = malla["vertices"].astype(np.float64), malla["caras"]
        self.v0 = v[c[:, 0]]
        self.e1 = v[c[:, 1]] - self.v0
        self.e2 = v[c[:, 2]] - self.v0
        n = np.cross(self.e1, self.e2)
        self.normales = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        # Para descartar rápido las caras lejos del rayo: su centro y lo más
        # que un vértice se aleja de él.
        self.centros = self.v0 + (self.e1 + self.e2) / 3
        self.radio = float(np.max(np.linalg.norm(np.stack([
            self.v0, self.v0 + self.e1, self.v0 + self.e2]) - self.centros, axis=2))) + 1e-4
        self.tam = cam["tam"]
        self.ojo = np.array(cam["posicion"], dtype=float)
        atras = self.ojo - np.array(cam["mira"], dtype=float)
        atras /= np.linalg.norm(atras)
        derecha = np.cross([0.0, 1.0, 0.0], atras)
        derecha /= np.linalg.norm(derecha)
        arriba = np.cross(atras, derecha)
        self.vista = np.stack([derecha, arriba, atras])
        self.foco = 1.0 / math.tan(math.radians(cam["fov"]) / 2)

    @staticmethod
    def rotacion(inclinacion, giro):
        a, b = math.radians(inclinacion), math.radians(giro)
        rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
        return rx @ ry

    def proyectar(self, puntos, normales, inclinacion, giro):
        """Puntos de la piel (marco de la cabeza) -> (px de la foto, a la vista)."""
        r = self.rotacion(inclinacion, giro)
        mundo = np.atleast_2d(puntos) @ r.T
        nm = np.atleast_2d(normales) @ r.T
        cam = (mundo - self.ojo) @ self.vista.T
        x = self.foco * cam[:, 0] / -cam[:, 2]
        y = self.foco * cam[:, 1] / -cam[:, 2]
        px = np.stack([(x + 1) / 2 * self.tam, (1 - y) / 2 * self.tam], axis=1)
        # De frente a la cámara: la normal apunta hacia ella.
        visible = np.einsum("ij,ij->i", nm, self.ojo - mundo) > 0
        return px, visible

    def rayo(self, x, y, inclinacion, giro):
        """El punto de la piel bajo el pixel (x, y) de la foto, con su
        normal, en el marco de la cabeza; None si ahí no hay cabeza."""
        r = self.rotacion(inclinacion, giro)
        nx, ny = 2 * x / self.tam - 1, 1 - 2 * y / self.tam
        direccion = self.vista.T @ np.array([nx / self.foco, ny / self.foco, -1.0])
        origen = r.T @ self.ojo
        d = r.T @ (direccion / np.linalg.norm(direccion))
        # Solo las caras cuyo centro queda cerca de la recta del rayo (las
        # demás no la pueden cortar), y contra esas Möller-Trumbore a la vez.
        rel = self.centros - origen
        cerca = np.flatnonzero(np.einsum("ij,ij->i", rel, rel) - (rel @ d) ** 2 <= self.radio ** 2)
        if not len(cerca):
            return None
        v0, e1, e2 = self.v0[cerca], self.e1[cerca], self.e2[cerca]
        p = np.cross(d, e2)
        det = np.einsum("ij,ij->i", e1, p)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        t0 = origen - v0
        u = np.einsum("ij,ij->i", t0, p) * inv
        q = np.cross(t0, e1)
        v = (q @ d) * inv
        t = np.einsum("ij,ij->i", e2, q) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        if not hit.any():
            return None
        j = np.flatnonzero(hit)[np.argmin(t[hit])]
        normal = self.normales[cerca[j]]
        if normal @ d > 0:
            normal = -normal
        return origen + t[j] * d, normal


def _remuestrear(puntos, paso=PASO_TRAZO_M):
    """Un punto cada `paso` metros a lo largo del trazo."""
    puntos = np.asarray(puntos, dtype=float)
    if len(puntos) < 2:
        return puntos
    seg = np.linalg.norm(np.diff(puntos, axis=0), axis=1)
    largo = np.concatenate([[0.0], np.cumsum(seg)])
    if largo[-1] < paso:
        return puntos[[0, -1]]
    s = np.arange(0.0, largo[-1] + 1e-9, paso)
    return np.stack([np.interp(s, largo, puntos[:, k]) for k in range(3)], axis=1)


class Trazo:
    def __init__(self, herramienta, puntos, normales, misma):
        puntos = np.asarray(puntos, dtype=float)
        self.herramienta = herramienta
        self.puntos = _remuestrear(puntos)
        # Cada punto remuestreado toma la normal del original más cercano.
        cerca = np.argmin(np.linalg.norm(self.puntos[:, None, :] - puntos[None], axis=2), axis=1)
        self.normales = np.asarray(normales, dtype=float)[cerca]
        self.misma = misma
        neto = self.puntos[-1] - self.puntos[0]
        self.direccion = neto / max(np.linalg.norm(neto), 1e-9)
        self.cuando = time.monotonic()

    def cubre(self, punto):
        return bool(np.min(np.linalg.norm(self.puntos - punto, axis=1)) <= PINCEL_M)


class Piel:
    """Las pasadas de algodón y lo que dejan en cada punto de la piel."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.trazos = []
        self.base, self.piso = {}, {}     # por sitio de la norma: vale para su zona
        self.errores = []                 # lo mal hecho, para la evaluación
        self._irritados = set()           # sitios ya anotados como irritados
        self._puntos_irritados = None     # caché para dibujar; se rehace con cada pasada

    def _zona(self, punto):
        sitio, _ = sitio_cercano(punto)
        if sitio not in self.base:
            d = datos()
            zona = d["sitios"][d["por_id"][sitio]]["zona"]
            self.base[sitio] = self.rng.uniform(*RANGO_KOHM.get(zona, RANGO_CUERO_CABELLUDO))
            self.piso[sitio] = self.rng.uniform(*PISO_KOHM)
        return sitio

    def pasadas(self, punto):
        """(alcohol, gel efectivo, ida y vuelta) que cubrieron ese punto."""
        alcohol = gel = ida = 0
        for t in self.trazos:
            if not t.cubre(punto):
                continue
            if t.herramienta == "alcohol":
                alcohol += 1
            elif t.misma:
                gel += 1.0
            else:
                gel += 0.5
                ida += 1
        return alcohol, gel, ida

    def irritada(self, punto):
        _alcohol, gel, ida = self.pasadas(punto)
        return gel > GEL_MAX_PASADAS or ida >= IDA_Y_VUELTA_PARA_IRRITAR

    def pasada(self, herramienta, puntos, normales, misma_direccion=True):
        """Una pasada de algodón: los puntos de la piel por donde pasó."""
        puntos = np.asarray(puntos, dtype=float)
        if herramienta == "gel":
            neto = puntos[-1] - puntos[0]
            direccion = neto / max(np.linalg.norm(neto), 1e-9)
            # Al revés que una pasada anterior de gel sobre la misma piel:
            # también es ida y vuelta, aunque cada arrastre vaya derecho.
            for t in self.trazos:
                if t.herramienta == "gel" and t.direccion @ direccion < 0 and \
                        np.min(np.linalg.norm(t.puntos[:, None] - puntos[None], axis=2)) <= PINCEL_M:
                    misma_direccion = False
                    break
            if self.pasadas(puntos[0])[0] == 0:
                self.errores.append(("gel_sin_alcohol", self._zona(puntos[0])))
            if not misma_direccion:
                self.errores.append(("ida_y_vuelta", self._zona(puntos[0])))
        trazo = Trazo(herramienta, puntos, normales, misma_direccion)
        self.trazos.append(trazo)
        self._puntos_irritados = None
        if herramienta == "gel":
            for p in trazo.puntos[::3]:
                if self.irritada(p):
                    sitio = self._zona(p)
                    if sitio not in self._irritados:
                        self._irritados.add(sitio)
                        self.errores.append(("piel_irritada", sitio))
        return trazo

    def puntos_irritados(self):
        """(puntos, normales) de la piel irritada, para dibujarla."""
        if self._puntos_irritados is None:
            pares = [(pt, n) for t in self.trazos if t.herramienta == "gel"
                     for pt, n in zip(t.puntos[::2], t.normales[::2]) if self.irritada(pt)]
            self._puntos_irritados = (np.array([a for a, _ in pares]), np.array([b for _, b in pares]))
        return self._puntos_irritados

    def preparada(self, punto):
        alcohol, gel, _ = self.pasadas(punto)
        return bool(alcohol or gel)

    def impedancia(self, punto):
        """Lo que daría un electrodo puesto ahora en ese punto, en kΩ."""
        sitio = self._zona(punto)
        alcohol, gel, _ = self.pasadas(punto)
        z = self.base[sitio]
        if alcohol:
            z *= ALCOHOL_FACTOR[min(alcohol, 2)]
        gel = min(gel, GEL_MAX_PASADAS)
        if gel:
            z *= (GEL_POR_PASADA if alcohol else GEL_SIN_ALCOHOL) ** gel
        return max(self.piso[sitio], z)

    def resumen(self, punto):
        if self.irritada(punto):
            return "piel irritada"
        alcohol, gel, _ = self.pasadas(punto)
        partes = []
        if alcohol:
            partes.append("alcohol ✓")
        if gel:
            partes.append(f"gel {gel:g}")
        return " · ".join(partes) or "sin preparar"


class Electrodo:
    def __init__(self, punto, normal):
        self.punto = np.asarray(punto, dtype=float)
        self.normal = np.asarray(normal, dtype=float)

    def cercano(self):
        return sitio_cercano(self.punto)

    def lado(self):
        """'izq' o 'der' del paciente (+x del marco es su izquierda)."""
        return "izq" if self.punto[0] > 0.01 else "der"


class Impedancias:
    """La impedancia de cada electrodo: la de la piel donde quedó, en el
    momento de ponerlo. Se ve solo después de medir, como en el equipo: lo
    que cambió desde la última medición queda sin medir."""

    def __init__(self, rng=None):
        self.piel = Piel(rng)
        self.z = {}           # rol -> kΩ
        self.medido = {}      # rol -> kΩ de la última medición (o falta)

    @property
    def errores(self):
        return self.piel.errores

    def poner(self, rol, electrodo):
        if not self.piel.preparada(electrodo.punto):
            self.piel.errores.append(("electrodo_sin_preparar", electrodo.cercano()[0]))
        self.z[rol] = self.piel.impedancia(electrodo.punto)
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
    """La cabeza. Arrastrar con Girar, o fuera de la cabeza, la gira. Con
    alcohol o gel, arrastrar sobre la piel es una pasada (`pasada`); con el
    electrodo, el clic en la piel emite `punto_elegido`."""
    punto_elegido = Signal(object, object)          # punto, normal (marco de la cabeza)
    pasada = Signal(str, object, object, bool)      # herramienta, puntos, normales, misma dirección

    def __init__(self, parent=None):
        super().__init__(parent)
        self.d = datos()
        self.geo = geometria()
        self.yaws = self.d["yaws"]
        self.pitches = self.d["pitches"]
        self.giro = 0.0           # grados, continuo; se ajusta al cuadro más cercano
        self.inclinacion = 0.0
        self.sistema = "10-20"
        self.ver_puntos = False
        self.herramienta = "girar"
        self.piel = None          # Piel, para dibujar lo limpiado
        self.colocados = {}       # rol -> Electrodo
        self.estados = {}         # rol -> 'ok'/'aviso'/'alerta' de la impedancia medida
        self._apretado = None
        self._arrastrando = False
        self._trazo = None        # la pasada en curso
        self._cache = OrderedDict()
        self._brillo = QTimer(self)
        self._brillo.setInterval(80)
        self._brillo.timeout.connect(self._mientras_brilla)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(260, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    # ------------------------------------------------------------ cuadros
    def _angulos(self):
        """(inclinación, giro) del cuadro que se muestra."""
        paso = self.yaws[1] - self.yaws[0]
        y = self.yaws[int(round((self.giro % 360) / paso)) % len(self.yaws)]
        p = min(self.pitches, key=lambda v: abs(v - self.inclinacion))
        return p, y

    def _clave(self):
        p, y = self._angulos()
        return f"{p}_{y}"

    def _pixmap(self, clave):
        pm = self._cache.get(clave)
        if pm is None:
            ini, largo = self.d["indice"][clave]
            pm = QPixmap.fromImage(QImage.fromData(self.d["bin"][ini:ini + largo], "WEBP"))
            self._cache[clave] = pm
            if len(self._cache) > CUADROS_EN_MEMORIA:
                self._cache.popitem(last=False)
        else:
            self._cache.move_to_end(clave)
        return pm

    def _marco(self):
        """Dónde se dibuja el cuadro (cuadrado, centrado) y su escala."""
        lado = min(self.width(), self.height())
        return QRectF((self.width() - lado) / 2, (self.height() - lado) / 2, lado, lado), \
            lado / self.d["tam"]

    def _a_pantalla(self, px):
        marco, escala = self._marco()
        return QPointF(marco.x() + px[0] * escala, marco.y() + px[1] * escala)

    def _a_foto(self, pos):
        marco, escala = self._marco()
        return (pos.x() - marco.x()) / escala, (pos.y() - marco.y()) / escala

    def tocar(self, pos):
        """El punto de la piel bajo una posición del widget, o None."""
        x, y = self._a_foto(pos)
        p, g = self._angulos()
        return self.geo.rayo(x, y, p, g)

    def en_pantalla(self, punto, normal):
        """Dónde se ve un punto de la piel en el widget, o None si está detrás."""
        p, g = self._angulos()
        px, vis = self.geo.proyectar(punto, normal, p, g)
        return self._a_pantalla(px[0]) if vis[0] else None

    def _sitios_visibles(self):
        fila = self.d["cuadros"][self._clave()]
        for s, xy in zip(self.d["sitios"], fila):
            if xy is None:
                continue
            if self.sistema == "10-20" and s["craneo"] and s["sistema"] != "10-20":
                continue
            yield s, self._a_pantalla(xy)

    # ------------------------------------------------------------ API
    def mirar(self, giro, inclinacion):
        self.giro, self.inclinacion = float(giro), float(inclinacion)
        self.update()

    def poner_sistema(self, sistema):
        self.sistema = sistema
        self.update()

    def poner_ver_puntos(self, ver):
        self.ver_puntos = bool(ver)
        self.update()

    def poner_herramienta(self, herramienta):
        self.herramienta = herramienta
        self.update()

    def poner(self, colocados, estados=None):
        self.colocados = dict(colocados)
        self.estados = dict(estados or {})
        self.update()

    def _mientras_brilla(self):
        if not self.piel or not any(time.monotonic() - t.cuando < BRILLO_S
                                    for t in self.piel.trazos if t.herramienta == "alcohol"):
            self._brillo.stop()
        self.update()

    # ------------------------------------------------------------ dibujo
    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        marco, escala = self._marco()
        p.drawPixmap(marco, self._pixmap(self._clave()), QRectF(0, 0, self.d["tam"], self.d["tam"]))
        self._dibujar_piel(p, escala)
        if self.ver_puntos:
            self._dibujar_sitios(p)
        self._dibujar_electrodos(p)
        if self._trazo is not None and self._trazo["pantalla"]:
            # El algodón bajo el dedo.
            p.setPen(QPen(QColor("#C9C2C8"), 1))
            p.setBrush(QColor(255, 255, 255, 235))
            p.drawEllipse(self._trazo["pantalla"][-1], 9, 9)
        p.end()

    def _dibujar_piel(self, p, escala):
        """Lo frotado: húmedo del alcohol unos segundos, rosado con el gel
        (más intenso donde se pasó más veces), rojo donde se irritó."""
        if self.piel is None or not self.piel.trazos:
            return
        inc, giro = self._angulos()
        # Ancho del algodón en pantalla: 8 mm de radio a la distancia de la cabeza.
        ancho = 2 * PINCEL_M * self.geo.foco * self.geo.tam / 2 / self.geo.ojo[2] * escala
        ahora = time.monotonic()
        for t in self.piel.trazos:
            if t.herramienta == "alcohol":
                edad = ahora - t.cuando
                if edad >= BRILLO_S:
                    continue
                color = QColor(235, 245, 255, int(150 * (1 - edad / BRILLO_S)))
            else:
                color = QColor(240, 140, 140, 45)
            px, vis = self.geo.proyectar(t.puntos, t.normales, inc, giro)
            pen = QPen(color, ancho)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            camino, abierto = QPainterPath(), False
            for xy, v in zip(px, vis):
                q = self._a_pantalla(xy)
                if v and abierto:
                    camino.lineTo(q)
                elif v:
                    camino.moveTo(q)
                    camino.lineTo(q)
                abierto = bool(v)
            p.drawPath(camino)
        # Lo irritado, encima.
        puntos, normales = self.piel.puntos_irritados()
        if len(puntos):
            px, vis = self.geo.proyectar(puntos, normales, inc, giro)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(205, 30, 30, 70))
            for xy, v in zip(px, vis):
                if v:
                    p.drawEllipse(self._a_pantalla(xy), ancho / 2, ancho / 2)

    def _dibujar_sitios(self, p):
        fuente = QFont(self.font())
        fuente.setPointSizeF(7)
        p.setFont(fuente)
        for s, pt in self._sitios_visibles():
            p.setPen(QPen(QColor(BLANCO_BORDE), 1.1))
            p.setBrush(QColor("white"))
            p.drawEllipse(pt, 2.6, 2.6)
            if s["sistema"] == "10-20" or not s["craneo"]:
                p.setPen(QColor(BLANCO_BORDE))
                p.drawText(pt + QPointF(4, 3), s["corto"])

    def _dibujar_electrodos(self, p):
        for rol, e in self.colocados.items():
            pt = self.en_pantalla(e.punto, e.normal)
            if pt is None:
                continue
            estado = self.estados.get(rol)
            if estado:
                # Anillo con lo que dio la impedancia, como la luz del equipo.
                p.setPen(QPen(QColor(COLOR_ESTADO[estado]), 3))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(pt, 11, 11)
            p.setPen(QPen(QColor(_borde(COLOR_ROL[rol])), 2))
            p.setBrush(QColor(COLOR_ROL[rol]))
            p.drawEllipse(pt, 7.5, 7.5)

    # ------------------------------------------------------------ mouse
    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        if self.herramienta in ("alcohol", "gel"):
            tocado = self.tocar(ev.position())
            if tocado is not None:
                self._trazo = {"puntos": [tocado[0]], "normales": [tocado[1]],
                               "pantalla": [ev.position()]}
                self.update()
                return
        self._apretado = (ev.position(), self.giro, self.inclinacion)
        self._arrastrando = False

    def mouseMoveEvent(self, ev):
        if self._trazo is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            self._trazo["pantalla"].append(ev.position())
            tocado = self.tocar(ev.position())
            if tocado is not None:
                self._trazo["puntos"].append(tocado[0])
                self._trazo["normales"].append(tocado[1])
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
                self.update()
            return
        if self.herramienta != "girar":
            sobre = self.tocar(ev.position())
            self.setCursor(Qt.CursorShape.CrossCursor if sobre is not None else Qt.CursorShape.OpenHandCursor)
            if sobre is not None and self.piel is not None and self.herramienta != "electrodo":
                self.setToolTip(self.piel.resumen(sobre[0]))
            else:
                self.setToolTip("")

    def mouseReleaseEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        if self._trazo is not None:
            trazo, self._trazo = self._trazo, None
            self._terminar_pasada(trazo)
            self.update()
            return
        if self._apretado is None:
            return
        arrastro = self._arrastrando
        self._apretado = None
        self._arrastrando = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if not arrastro and self.herramienta == "electrodo":
            tocado = self.tocar(ev.position())
            if tocado is not None:
                self.punto_elegido.emit(tocado[0], tocado[1])

    def _terminar_pasada(self, trazo):
        """Una pasada si recorrió lo suficiente en pantalla y tocó la piel.
        Es "en la misma dirección" si no fue y volvió dentro del arrastre
        (Piel.pasada mira además si va al revés que la anterior)."""
        pantalla = trazo["pantalla"]
        recorrido = sum(math.hypot(b.x() - a.x(), b.y() - a.y()) for a, b in zip(pantalla, pantalla[1:]))
        if recorrido < PASADA_MIN_PX or len(trazo["puntos"]) < 2:
            return
        neto = math.hypot(pantalla[-1].x() - pantalla[0].x(), pantalla[-1].y() - pantalla[0].y())
        misma = recorrido <= IDA_Y_VUELTA * neto
        self.pasada.emit(self.herramienta, np.array(trazo["puntos"]), np.array(trazo["normales"]), misma)
        if self.herramienta == "alcohol":
            self._brillo.start()

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
    """Prototipo: la cabeza y un panel para preparar la piel, poner activo,
    referencia(s) y tierra donde el alumno quiera y medir sus impedancias."""
    montaje_cambio = Signal(dict)

    PISTAS = {
        "girar": "Arrastra para girar la cabeza.",
        "alcohol": "Pasa el algodón con alcohol: arrastra sobre la piel.",
        "gel": "Pasa el algodón con gel exfoliante: arrastra sobre la piel.",
        "electrodo": "Clic en la piel pone el electrodo elegido.",
    }

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
        self.cabeza.punto_elegido.connect(self._poner_en)
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

        pcol.addWidget(self._seccion("CANALES"))
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
        pcol.addWidget(self._seccion("ELECTRODO"))
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
            puesto.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.lbl_puesto[clave] = puesto
            quitar = QPushButton()
            quitar.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_TENUE, tam=12))
            quitar.setToolTip("Sacar este electrodo")
            quitar.setFixedSize(24, 22)
            quitar.clicked.connect(lambda _=False, c=clave: self._quitar(c))
            grilla.addWidget(b, i, 0)
            grilla.addWidget(puesto, i, 1)
            grilla.addWidget(quitar, i, 2)
            self.widgets_rol[clave] = [b, puesto, quitar]
        pcol.addLayout(grilla)

        pcol.addSpacing(4)
        pcol.addWidget(self._seccion("NORMA"))
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
        # Los puntos de la norma son una ayuda: se ven solo si se piden.
        self.btn_ver_puntos = QPushButton("Ver puntos")
        self.btn_ver_puntos.setCheckable(True)
        self.btn_ver_puntos.setProperty("segmento", "true")
        self.btn_ver_puntos.toggled.connect(self._ver_puntos)
        fila.addWidget(self.btn_ver_puntos, 1)
        pcol.addLayout(fila)

        pcol.addSpacing(4)
        pcol.addLayout(self._seccion_impedancias())
        pcol.addStretch(1)
        self.btn_sacar_todos = QPushButton(" Sacar todos")
        self.btn_sacar_todos.setIcon(iconos.icono_boton("cerrar", tema.TEXTO_SUAVE, tam=14))
        self.btn_sacar_todos.clicked.connect(self.sacar_todos)
        pcol.addWidget(self.btn_sacar_todos)
        raiz.addWidget(panel)

        self.colocados = {}       # rol -> Electrodo
        self.canales = 1
        self._mostrar_roles()
        self._elegir_rol("activo")
        self.elegir_herramienta("girar")
        self._pintar()

    @staticmethod
    def _seccion(texto):
        lbl = QLabel(texto)
        lbl.setProperty("role", "seccion")
        return lbl

    def _seccion_impedancias(self):
        col = QVBoxLayout()
        col.setSpacing(4)
        cab = QHBoxLayout()
        cab.addWidget(self._seccion("IMPEDANCIAS"), 1)
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
        for i, (clave, _nombre, color) in enumerate(ROLES):
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

    # ------------------------------------------------------------ estado
    def roles(self):
        return ROLES_POR_CANALES[self.canales]

    def elegir_herramienta(self, clave):
        self.botones_herramienta[clave].setChecked(True)
        self.cabeza.poner_herramienta(clave)
        self.pista.setText(self.PISTAS[clave] + " Fuera de la cabeza, arrastrar la gira."
                           if clave != "girar" else self.PISTAS[clave])

    def _ver_puntos(self, ver):
        self.cabeza.poner_ver_puntos(ver)
        self._pintar()

    def _elegir_rol(self, clave, herramienta=False):
        self.rol_actual = clave
        self.botones_rol[clave].setChecked(True)
        if herramienta:
            self.elegir_herramienta("electrodo")

    def poner_canales(self, n):
        """1 o 2 canales. Al pasar a dos, la referencia ya puesta queda como
        la del lado donde está; al volver a uno, queda la derecha (o la
        izquierda si es la única) y la otra se saca."""
        if n == self.canales:
            return
        if n == 2 and "referencia" in self.colocados:
            nuevo = "ref_izq" if self.colocados["referencia"].lado() == "izq" else "ref_der"
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

    def _pasada(self, herramienta, puntos, normales, misma):
        for e in self.colocados.values():
            if np.min(np.linalg.norm(puntos - e.punto, axis=1)) <= PINCEL_M:
                # Con el electrodo puesto no se frota esa piel: no pasa nada.
                self.pista.setText("Ahí hay un electrodo: sácalo para volver a preparar esa piel.")
                return
        self.impedancias.piel.pasada(herramienta, puntos, normales, misma)
        self._pintar()

    def _poner_en(self, punto, normal):
        e = Electrodo(punto, normal)
        # Dos electrodos en la misma piel no caben: el nuevo saca al otro.
        for rol, otro in list(self.colocados.items()):
            if np.linalg.norm(otro.punto - e.punto) < UN_ELECTRODO_M:
                del self.colocados[rol]
                self.impedancias.quitar(rol)
        self.colocados[self.rol_actual] = e
        self.impedancias.poner(self.rol_actual, e)
        # Pasa solo al siguiente que falta, como quien va poniendo los tres.
        falta = next((c for c in self.roles() if c not in self.colocados), None)
        if falta:
            self._elegir_rol(falta)
        self._pintar()

    def poner_en_sitio(self, sitio_id):
        """Pone el electrodo elegido justo en un sitio de la norma (pruebas y
        montajes de ejemplo del docente)."""
        d = datos()
        i = d["por_id"][sitio_id]
        self._poner_en(d["pos"][i], d["normales"][i])

    def _quitar(self, clave):
        self.colocados.pop(clave, None)
        self.impedancias.quitar(clave)
        self._elegir_rol(clave)
        self._pintar()

    def sacar_todos(self):
        """Saca todos los electrodos. La piel queda como estaba."""
        self.colocados = {}
        self.impedancias.z.clear()
        self.impedancias.medido.clear()
        self._elegir_rol("activo")
        self._pintar()

    def medir(self):
        self.impedancias.medir()
        self._pintar()

    @property
    def errores(self):
        """Lo mal hecho en la preparación, para la evaluación (no se muestra)."""
        return list(self.impedancias.errores)

    def montaje(self):
        """Dónde quedó cada electrodo, para la evaluación y el registro: el
        sitio de la norma más cercano y a cuántos mm, y su impedancia."""
        out = {}
        for rol, e in self.colocados.items():
            sitio, dist = e.cercano()
            out[rol] = {"sitio": sitio, "distancia_mm": round(dist * 1000, 1),
                        "lado": e.lado(), "kohm": self.impedancias.z.get(rol),
                        "punto": [round(float(v), 5) for v in e.punto]}
        return out

    # ------------------------------------------------------------ pintado
    def _pintar(self):
        for clave, lbl in self.lbl_puesto.items():
            e = self.colocados.get(clave)
            if e is None:
                lbl.setText("—")
                lbl.setToolTip("Sin poner")
            elif self.cabeza.ver_puntos:
                sitio, dist = e.cercano()
                lbl.setText(f"{corto_sitio(sitio)} · {dist * 1000:.0f} mm")
                lbl.setToolTip(f"A {dist * 1000:.0f} mm de {nombre_sitio(sitio)}")
            else:
                lbl.setText("puesto")
                lbl.setToolTip("")
            lbl.setProperty("vacio", "false" if e else "true")
            tema.repintar(lbl)
        estados = {rol: self.impedancias.estado(rol) for rol in self.colocados
                   if self.impedancias.estado(rol)}
        self.cabeza.poner(self.colocados, estados)
        self._pintar_impedancias()
        self.montaje_cambio.emit(self.montaje())

    def _pintar_impedancias(self):
        limite, balance = limites()
        for clave, (valor, barra, sacar, piel) in self.filas_imp.items():
            e = self.colocados.get(clave)
            z = self.impedancias.medido.get(clave)
            estado = self.impedancias.estado(clave)
            if e is None:
                valor.setText("—")
            elif z is None:
                valor.setText("sin medir")
            else:
                valor.setText(f"{z:.1f} kΩ")
            barra.setValue(int(min(z or 0, ESCALA_KOHM) * 10))
            for w in (valor, barra):
                w.setProperty("estado", estado or "")
                tema.repintar(w)
            sacar.setEnabled(e is not None)
            piel.setText(self.impedancias.piel.resumen(e.punto) if e is not None else "")
        self.btn_medir.setEnabled(bool(self.colocados))
        informe = self.impedancias.informe()
        if informe is None:
            texto = (f"Cada electrodo bajo {limite:.0f} kΩ y entre ellos menos de "
                     f"{balance:.0f} kΩ de diferencia.")
            estado = ""
        else:
            _peor, desbalance, ok = informe
            texto = (f"Diferencia entre electrodos: {desbalance:.1f} kΩ. " +
                     ("Listo para registrar." if ok else "Fuera de norma."))
            estado = "ok" if ok else "alerta"
        self.lbl_desbalance.setText(texto)
        self.lbl_desbalance.setProperty("estado", estado)
        tema.repintar(self.lbl_desbalance)
