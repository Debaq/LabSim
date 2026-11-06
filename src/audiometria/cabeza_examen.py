"""La cabeza del paciente para examinar con herramientas: diapasón y otoscopio.

La misma cabeza de los electrodos (core/cabeza_electrodos.py: fotos de
labyrinthus3d cada 2° y la piel 3D, cada clic cae en un punto real), con
otras herramientas:

- girar: arrastrar gira la cabeza (también fuera de la piel, y con las
  flechas del teclado);
- diapason / otoscopio: el clic en la piel emite `apoyado(punto, normal)`;
  quien la usa decide qué es (zona());
- traccion: arrastrar desde la oreja tira del pabellón; al soltar emite
  `traccionado(oido, arriba, atras)` con el tirón en centímetros hacia
  arriba (+) o abajo (-) y hacia atrás (+) o adelante (-), en el marco de
  la cabeza, por mucho que esté girada.

Ejes de la cabeza (cabeza.json): x hacia la izquierda del paciente, y hacia
arriba, z hacia adelante.
"""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainterPath, QPen

from core import iconos, tema
from core.cabeza_electrodos import CabezaElectrodos, datos

# Vistas rápidas (giro, inclinación): como VISTAS de los electrodos.
VISTA_OIDO = {"od": (90, 0), "oi": (270, 0)}
VISTA_FRENTE = (0, 0)
VISTA_ARRIBA = (0, 60)

MASTOIDES = {"M2": "od", "M1": "oi"}
PABELLON = {"cae_der": "od", "cae_izq": "oi", "A2": "od", "A1": "oi"}
LINEA_MEDIA = {"Nz": "frente", "Fpz": "frente", "AFz": "frente", "Fz": "frente",
               "FCz": "vertice", "Cz": "vertice", "CPz": "vertice"}
CERCA_MASTOIDES_M = 0.025
CERCA_PABELLON_M = 0.030
CERCA_LINEA_MEDIA_M = 0.030
FUERA_DE_LA_LINEA_M = 0.012   # más que esto a un lado de la línea media
DESDE_LA_OREJA_M = 0.045      # el tirón empieza en la oreja (o muy cerca)
CERCA_CONDUCTO_M = 0.022      # el otoscopio entra por el conducto


def _pos(sitio):
    d = datos()
    return d["pos"][d["por_id"][sitio]]


def _mas_cercano(punto, sitios):
    mejor = None
    for sitio in sitios:
        dist = float(np.linalg.norm(_pos(sitio) - punto))
        if mejor is None or dist < mejor[1]:
            mejor = (sitio, dist)
    return mejor


def zona(punto):
    """Dónde quedó el diapasón: (zona, oído o parte, sitio, distancia en m).

    zona: 'mastoides' (oído 'od'/'oi'), 'pabellon' (frente a la oreja, por
    aire), 'linea_media' ('frente'/'vertice'), 'fuera_de_linea' (frente o
    vértex, pero a un lado) u 'otro'."""
    punto = np.asarray(punto, dtype=float)
    sitio, dist = _mas_cercano(punto, PABELLON)
    if dist <= CERCA_PABELLON_M:
        return "pabellon", PABELLON[sitio], sitio, dist
    sitio, dist = _mas_cercano(punto, MASTOIDES)
    if dist <= CERCA_MASTOIDES_M:
        return "mastoides", MASTOIDES[sitio], sitio, dist
    sitio, dist = _mas_cercano(punto, LINEA_MEDIA)
    if dist <= CERCA_LINEA_MEDIA_M:
        if abs(punto[0]) > FUERA_DE_LA_LINEA_M:
            return "fuera_de_linea", "od" if punto[0] < 0 else "oi", sitio, dist
        return "linea_media", LINEA_MEDIA[sitio], sitio, dist
    from core.cabeza_electrodos import sitio_cercano
    sitio, dist = sitio_cercano(punto)
    return "otro", None, sitio, dist


def conducto(punto):
    """El conducto ('od'/'oi') bajo un punto, o None."""
    sitio, dist = _mas_cercano(np.asarray(punto, dtype=float), ("cae_der", "cae_izq"))
    return PABELLON[sitio] if dist <= CERCA_CONDUCTO_M else None


def oreja(punto):
    """La oreja ('od'/'oi') de la que se puede tirar desde ese punto, o None."""
    sitio, dist = _mas_cercano(np.asarray(punto, dtype=float), PABELLON)
    return PABELLON[sitio] if dist <= DESDE_LA_OREJA_M else None


class CabezaExamen(CabezaElectrodos):
    apoyado = Signal(object, object)            # punto, normal
    traccionado = Signal(str, float, float)     # oído, cm arriba, cm atrás

    def __init__(self, parent=None):
        super().__init__(parent)
        self.diapason = None      # (punto, normal) donde está apoyado
        self.otoscopio = None     # 'od'/'oi': metido en ese conducto
        self.tiron = None         # ('od'/'oi', cm arriba, cm atrás) que se mantiene
        self._tirando = None      # el arrastre en curso: (oído, pantalla inicio, pantalla ahora)

    # ------------------------------------------------------------ API
    def mirar_oido(self, oido):
        self.mirar(*VISTA_OIDO[oido])

    def poner_diapason(self, punto=None, normal=None):
        self.diapason = None if punto is None else (np.asarray(punto), np.asarray(normal))
        self.update()

    def poner_otoscopio(self, oido):
        self.otoscopio = oido
        self.update()

    def poner_tiron(self, tiron):
        self.tiron = tiron
        self.update()

    # ------------------------------------------------------------ mouse
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.herramienta == "traccion":
            tocado = self.tocar(ev.position())
            lado = oreja(tocado[0]) if tocado is not None else None
            if lado is not None:
                self._tirando = (lado, ev.position(), ev.position())
                self.update()
                return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._tirando is not None:
            lado, inicio, _ = self._tirando
            self._tirando = (lado, inicio, ev.position())
            self.update()
            return
        if self.herramienta in ("diapason", "otoscopio", "traccion") and self._apretado is None:
            sobre = self.tocar(ev.position())
            self.setCursor(Qt.CursorShape.CrossCursor if sobre is not None else Qt.CursorShape.OpenHandCursor)
            return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self._tirando is not None:
            lado, inicio, fin = self._tirando
            self._tirando = None
            arriba, atras = self._tiron_en_la_cabeza(lado, fin - inicio)
            self.update()
            self.traccionado.emit(lado, arriba, atras)
            return
        if ev.button() == Qt.MouseButton.LeftButton and self.herramienta in ("diapason", "otoscopio") \
                and self._apretado is not None and not self._arrastrando:
            self._apretado = None
            tocado = self.tocar(ev.position())
            if tocado is not None:
                self.apoyado.emit(tocado[0], tocado[1])
            return
        super().mouseReleaseEvent(ev)

    def _tiron_en_la_cabeza(self, lado, delta):
        """El arrastre en pantalla, en cm hacia arriba y hacia atrás de la
        cabeza: se proyectan esas dos direcciones desde la oreja y se
        descompone el arrastre en ellas."""
        c = _pos("cae_der" if lado == "od" else "cae_izq")
        lat = np.array([-1.0 if lado == "od" else 1.0, 0.0, 0.0])
        paso = 0.02
        puntos = np.array([c, c + [0, paso, 0], c + [0, 0, -paso]])
        inc, giro = self._angulos()
        px, _vis = self.geo.proyectar(puntos, [lat] * 3, inc, giro, umbral=-1.0)
        o, a, b = (self._a_pantalla(xy) for xy in px)
        arriba = np.array([a.x() - o.x(), a.y() - o.y()])
        atras = np.array([b.x() - o.x(), b.y() - o.y()])
        base = np.column_stack([arriba, atras])
        if abs(np.linalg.det(base)) < 1e-6:
            return 0.0, 0.0   # de frente no se ve hacia dónde tira
        cu, ca = np.linalg.solve(base, np.array([delta.x(), delta.y()]))
        return round(float(cu * paso * 100), 2), round(float(ca * paso * 100), 2)

    # ------------------------------------------------------------ dibujo
    def paintEvent(self, ev):
        super().paintEvent(ev)
        from PySide6.QtGui import QPainter
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        _, escala = self._marco()
        if self.diapason is not None:
            pos = self.en_pantalla(*self.diapason)
            if pos is not None:
                self._dibujar_diapason(p, pos, max(escala, 0.6))
        if self.otoscopio is not None:
            sitio = "cae_der" if self.otoscopio == "od" else "cae_izq"
            normal = np.array([-1.0 if self.otoscopio == "od" else 1.0, 0.0, 0.0])
            pos = self.en_pantalla(_pos(sitio), normal)
            if pos is not None:
                self._icono(p, pos, "otoscopio", 40 * max(escala, 0.6))
        if self._tirando is not None:
            _lado, inicio, fin = self._tirando
            self._flecha(p, inicio, fin)
        p.end()

    @staticmethod
    def _dibujar_diapason(p, punto, escala):
        """El diapasón apoyado: un punto chico donde toca la piel (para que
        se vea exactamente dónde quedó) y el diapasón saliendo de ahí,
        mango y dos ramas, en metal."""
        import math as _m
        largo_mango = 30 * escala
        largo_ramas = 34 * escala
        abre = 5 * escala
        ang = _m.radians(-60)                       # hacia arriba y a la derecha
        u = QPointF(_m.cos(ang), _m.sin(ang))
        n = QPointF(-u.y(), u.x())
        horqueta = punto + u * largo_mango
        metal = QColor("#7C808A")
        p.setPen(QPen(QColor(255, 255, 255, 200), 5.5 * escala, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(punto, horqueta)
        p.setPen(QPen(metal, 3.2 * escala, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(punto, horqueta)
        # La U de las ramas
        izq0, der0 = horqueta + n * abre, horqueta - n * abre
        camino = QPainterPath(izq0 + u * largo_ramas)
        camino.lineTo(izq0)
        camino.quadTo(horqueta - u * (abre * 1.2), der0)
        camino.lineTo(der0 + u * largo_ramas)
        p.setPen(QPen(QColor(255, 255, 255, 200), 5 * escala, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(camino)
        p.setPen(QPen(metal, 2.8 * escala, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(camino)
        # Donde toca la piel
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        p.setBrush(QColor(tema.ACENTO))
        p.drawEllipse(punto, 4.2 * escala, 4.2 * escala)

    @staticmethod
    def _icono(p, pos, nombre, tam):
        tam = int(tam)
        p.setPen(QPen(QColor(tema.ACENTO), 2))
        p.setBrush(QColor(255, 255, 255, 220))
        p.drawEllipse(pos, tam * 0.62, tam * 0.62)
        p.drawPixmap(QPointF(pos.x() - tam / 2, pos.y() - tam / 2), iconos.pixmap(nombre, tema.ACENTO, tam))

    @staticmethod
    def _flecha(p, inicio, fin):
        largo = math.hypot(fin.x() - inicio.x(), fin.y() - inicio.y())
        if largo < 3:
            return
        p.setPen(QPen(QColor(tema.ACENTO), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(inicio, fin)
        ang = math.atan2(fin.y() - inicio.y(), fin.x() - inicio.x())
        punta = QPainterPath(fin)
        for d in (2.6, -2.6):
            punta.lineTo(QPointF(fin.x() - 12 * math.cos(ang + d / 6), fin.y() - 12 * math.sin(ang + d / 6)))
            punta.moveTo(fin)
        p.drawPath(punta)


# ---------------------------------------------------------------- otoscopía
LUPA = 0.16                 # radio de la ventana del otoscopio, fracción del lado de la cabeza (80 % de 0.20, él)
RECORRIDO_PX = 30.0         # px de la foto de la cabeza, desde donde entró: de borde a borde del tímpano
ZOOM_TIMPANO = 0.5          # el disco muestra esta fracción de la foto; el resto se recorre
ALCANCE = 0.85              # hasta dónde llega el centro de la vista (fracción del radio de la foto)
METAL = "#8E9098"
PARED_CLARA = "#C98E80"     # la piel del conducto cerca de la membrana
PARED_OSCURA = "#6E3A31"    # y más afuera, en sombra
NEGRO_VISOR = "#0E0A0D"


class CabezaOtoscopia(CabezaExamen):
    """La otoscopía como la rinoscopía (nasal/RinoscopiaWindow.Cara): el
    mouse es el otoscopio. Sobre un conducto aparece el otoscopio y al lado
    se abre la lupa con lo que se ve; moverlo dentro del conducto recorre el
    tímpano. Arrastrar desde la oreja tira del pabellón (queda tirado, con
    su flecha, hasta soltarlo); arrastrar fuera de la oreja gira la cabeza.

    `vista(oido)` dice qué se ve por ese conducto: {'foto': QPixmap o None,
    'adulto': el espéculo de adulto (disco claro entero; el pediátrico, la
    mitad), 'pared': fracción del radio que tapa la pared del conducto (0
    con buena tracción), 'texto': lo que se lee en lugar de la foto, o
    None}."""
    miro = Signal(str)       # el otoscopio entró a ese conducto
    salio = Signal()

    def __init__(self, vista=None, parent=None):
        super().__init__(parent)
        self.vista = vista or (lambda _oido: {"texto": "Otoscopio sin batería"})
        self.herramienta = "otoscopia"
        self._mouse = None
        self._conducto = None   # el conducto donde está el otoscopio
        self._ancla = None      # dónde entró el mouse al conducto: ahí la vista está centrada

    def _centro_conducto(self, oido):
        sitio = "cae_der" if oido == "od" else "cae_izq"
        normal = np.array([-1.0 if oido == "od" else 1.0, 0.0, 0.0])
        return self.en_pantalla(_pos(sitio), normal)

    def poner_herramienta(self, herramienta):
        """girar, traccion u otoscopia (como las herramientas de los
        electrodos: cada una hace lo suyo con el mouse)."""
        if herramienta != "otoscopia":
            self._salir()
        super().poner_herramienta(herramienta)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.herramienta == "traccion":
            tocado = self.tocar(ev.position())
            lado = oreja(tocado[0]) if tocado is not None else None
            if lado is not None:
                self._tirando = (lado, ev.position(), ev.position())
                self.update()
                return
        CabezaElectrodos.mousePressEvent(self, ev)

    def mouseMoveEvent(self, ev):
        if self._tirando is not None or self._apretado is not None or self.herramienta != "otoscopia":
            super().mouseMoveEvent(ev)
            return
        self._mouse = ev.position()
        tocado = self.tocar(ev.position())
        oido = conducto(tocado[0]) if tocado is not None else None
        if self._conducto is not None and self._ancla is not None:
            # Una vez dentro, moverse para recorrer la membrana no saca el
            # otoscopio: se sale alejándose más que el recorrido
            _, escala = self._marco()
            if math.hypot(self._ancla.x() - self._mouse.x(), self._ancla.y() - self._mouse.y()) \
                    <= RECORRIDO_PX * escala * 1.5:
                oido = self._conducto
        if oido != self._conducto:
            self._conducto = oido
            self._ancla = QPointF(self._mouse) if oido is not None else None
            if oido is None:
                self.salio.emit()
            else:
                self.miro.emit(oido)
        self.setCursor(Qt.CursorShape.BlankCursor if oido else Qt.CursorShape.OpenHandCursor)
        self.update()

    def leaveEvent(self, ev):
        self._salir()
        self.update()
        super().leaveEvent(ev)

    def _salir(self):
        if self._conducto is not None:
            self._conducto = None
            self._ancla = None
            self.salio.emit()

    # El soltar lo resuelve CabezaExamen: el tirón, y el clic con el diapasón

    # ------------------------------------------------------------ dibujo
    def paintEvent(self, ev):
        # La cabeza, el diapasón apoyado y el tirón en curso (CabezaExamen)
        super().paintEvent(ev)
        from PySide6.QtGui import QPainter
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.tiron is not None:
            self._flecha_tiron(p)
        if self._conducto is not None and self._mouse is not None:
            self._pintar_otoscopio(p)
        p.end()

    def _hacia_la_nuca(self, oido, centro):
        """+1 si la nuca queda a la derecha de la oreja en pantalla, -1 si a
        la izquierda."""
        c = _pos("cae_der" if oido == "od" else "cae_izq")
        lat = np.array([-1.0 if oido == "od" else 1.0, 0.0, 0.0])
        inc, giro = self._angulos()
        px, _vis = self.geo.proyectar(np.array([c, c + [0, 0, -0.05]]), [lat, lat], inc, giro, umbral=-1.0)
        return 1 if px[1][0] >= px[0][0] else -1

    def _flecha_tiron(self, p):
        """El pabellón que se mantiene tirado: la flecha desde la oreja."""
        oido, arriba, atras = self.tiron
        c = _pos("cae_der" if oido == "od" else "cae_izq")
        lat = np.array([-1.0 if oido == "od" else 1.0, 0.0, 0.0])
        fin = c + np.array([0.0, arriba / 100.0, -atras / 100.0]) * 3.0
        inc, giro = self._angulos()
        px, vis = self.geo.proyectar(np.array([c, fin]), [lat, lat], inc, giro, umbral=-0.3)
        if vis[0]:
            self._flecha(p, self._a_pantalla(px[0]), self._a_pantalla(px[1]))

    def _pintar_otoscopio(self, p):
        """El otoscopio en la oreja: lo que se ve se levanta ahí mismo, en un
        disco que es la cabeza del otoscopio, y de él sale el mango. Mover
        el mouse un poco dentro del conducto recorre todo el tímpano. El
        disco claro es entero con el espéculo de adulto y de la mitad del
        diámetro con el pediátrico."""
        oido = self._conducto
        centro = self._centro_conducto(oido)
        if centro is None:
            return
        marco, escala = self._marco()
        r = marco.width() * LUPA
        recorrido = RECORRIDO_PX * escala
        # Desde donde entró el mouse: ahí la vista está centrada, y el
        # recorrido lleva de borde a borde de la foto
        m = self._mouse - (self._ancla or centro)
        dx = max(-1.0, min(1.0, m.x() / recorrido))
        dy = max(-1.0, min(1.0, m.y() / recorrido))
        # El disco queda fijo en la oreja (sin salirse de la vista)
        c = QPointF(centro)
        c.setX(max(r + 6, min(self.width() - r - 6, c.x())))
        c.setY(max(r + 6, min(self.height() - r * 2.2, c.y())))
        self._pintar_mango(p, c, r, self._hacia_la_nuca(oido, centro))
        self._pintar_cabezal(p, c, r)
        caja = QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r)
        circulo = QPainterPath()
        circulo.addEllipse(c, r, r)
        p.save()
        p.setClipPath(circulo)
        p.fillRect(caja, QColor(NEGRO_VISOR))
        v = self.vista(oido) or {}
        foto = v.get("foto")
        if v.get("texto") or foto is None:
            p.setPen(QColor(tema.TEXTO_TENUE))
            p.drawText(caja.adjusted(r * 0.2, 0, -r * 0.2, 0),
                       Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                       v.get("texto") or "Otoscopio sin batería")
        else:
            claro = r * (1.0 if v.get("adulto") else 0.5)
            # La foto ampliada (ZOOM_TIMPANO de ella llena el disco). El centro
            # de la vista va de borde a borde de la membrana con el
            # recorrido del mouse; lo que cae fuera de la foto se ve oscuro
            lado = min(foto.width(), foto.height()) * ZOOM_TIMPANO
            px = foto.width() / 2 + dx * foto.width() / 2 * ALCANCE
            py = foto.height() / 2 + dy * foto.height() / 2 * ALCANCE
            fuente = QRectF(px - lado / 2, py - lado / 2, lado, lado)
            dentro = fuente.intersected(QRectF(0, 0, foto.width(), foto.height()))
            k = 2 * r / lado
            destino = QRectF(caja.x() + (dentro.x() - fuente.x()) * k, caja.y() + (dentro.y() - fuente.y()) * k,
                             dentro.width() * k, dentro.height() * k)
            hueco = QPainterPath()
            hueco.addEllipse(c, claro, claro)
            p.save()
            p.setClipPath(hueco)
            if not dentro.isEmpty():
                p.drawPixmap(destino, foto, dentro)
            pared = v.get("pared") or 0.0
            if pared > 0:
                # La pared del conducto sin enderezar: un anillo concéntrico
                # que tapa el borde de la membrana (más, cuanto peor la
                # tracción); más oscuro hacia afuera, como un túnel
                from PySide6.QtGui import QRadialGradient as _Rad
                hueco_r = claro * (1.0 - pared)
                anillo = QPainterPath()
                anillo.addEllipse(c, claro, claro)
                centro_libre = QPainterPath()
                centro_libre.addEllipse(c, hueco_r, hueco_r)
                tunel = _Rad(c, claro)
                tunel.setColorAt(0.0, QColor(PARED_CLARA))
                tunel.setColorAt(max(0.0, 1.0 - pared), QColor(PARED_CLARA))
                tunel.setColorAt(1.0, QColor(PARED_OSCURA))
                p.fillPath(anillo.subtracted(centro_libre), tunel)
            from PySide6.QtGui import QRadialGradient
            luz = QRadialGradient(c, claro)
            luz.setColorAt(0.0, QColor(255, 220, 150, 30))
            luz.setColorAt(0.8, QColor(0, 0, 0, 0))
            luz.setColorAt(1.0, QColor(14, 10, 13, 220))
            p.fillRect(caja, luz)
            p.restore()
        p.restore()
        # El borde de la ventana, encajado en el cabezal (sin brillo de vidrio:
        # se mira a través del otoscopio, no de una lupa)
        p.setPen(QPen(QColor("#0B0B0E"), max(3.0, r * 0.04)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(c, r, r)

    @staticmethod
    def _pintar_cabezal(p, c, r):
        """El cabezal del otoscopio: una caja oscura de esquinas redondeadas
        con la ventana de visión al centro, como se ve desde el lado del
        examinador."""
        from PySide6.QtGui import QLinearGradient
        lado = r * 2.36
        caja = QRectF(c.x() - lado / 2, c.y() - lado / 2, lado, lado)
        cuerpo = QLinearGradient(caja.topLeft(), caja.bottomRight())
        cuerpo.setColorAt(0.0, QColor("#3A3B41"))
        cuerpo.setColorAt(1.0, QColor("#17181C"))
        p.setPen(QPen(QColor("#0B0B0E"), 1.5))
        p.setBrush(cuerpo)
        p.drawRoundedRect(caja, r * 0.42, r * 0.42)
        # La lengüeta de la luz, arriba
        lengueta = QRectF(c.x() - r * 0.22, caja.top() - r * 0.12, r * 0.44, r * 0.16)
        p.setBrush(QColor("#2A2B30"))
        p.drawRoundedRect(lengueta, r * 0.05, r * 0.05)

    @staticmethod
    def _pintar_mango(p, c, r, hacia):
        """El mango bajo el cabezal, apenas inclinado hacia la nuca: el
        cuello, el anillo del reóstato, el mango moleteado y la tapa."""
        import math as _m
        from PySide6.QtGui import QPolygonF
        ang = _m.radians(90 + hacia * -12)
        u = QPointF(_m.cos(ang), _m.sin(ang))
        n = QPointF(-u.y(), u.x())
        base = c + u * (r * 1.12)

        def tramo(desde, hasta, ancho_a, ancho_b, color):
            a, b = base + u * desde, base + u * hasta
            p.setBrush(QColor(color))
            p.drawPolygon(QPolygonF([a + n * ancho_a, b + n * ancho_b, b - n * ancho_b, a - n * ancho_a]))

        p.setPen(QPen(QColor("#0B0B0E"), 1.2))
        tramo(0, r * 0.28, r * 0.15, r * 0.12, "#26272C")                 # cuello
        tramo(r * 0.28, r * 0.50, r * 0.22, r * 0.22, "#5B5E66")          # reóstato
        p.setPen(QPen(QColor(255, 255, 255, 70), 1))
        for k in range(1, 6):
            x = base + u * (r * (0.28 + 0.037 * k))
            p.drawLine(x + n * (r * 0.22), x - n * (r * 0.22))
        p.setPen(QPen(QColor("#0B0B0E"), 1.2))
        tramo(r * 0.50, r * 1.75, r * 0.20, r * 0.21, "#2A2B30")          # mango
        p.setPen(QPen(QColor(255, 255, 255, 35), 1))
        for k in range(1, 16):
            x = base + u * (r * (0.50 + 0.078 * k))
            p.drawLine(x + n * (r * 0.20), x - n * (r * 0.20))
        p.setPen(QPen(QColor("#0B0B0E"), 1.2))
        tramo(r * 1.75, r * 1.86, r * 0.21, r * 0.18, "#1C1D21")          # tapa
