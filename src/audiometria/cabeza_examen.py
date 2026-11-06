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
                self._icono(p, pos, "diapason", 34 * max(escala, 0.6))
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
LUPA = 0.20                 # radio del disco del otoscopio, como fracción del lado de la cabeza
RECORRIDO_PX = 12.0         # px de la foto de la cabeza: con eso se recorre todo el tímpano
ZOOM_TIMPANO = 0.5          # el disco muestra esta fracción de la foto; el resto se recorre
METAL = "#8E9098"
NEGRO_VISOR = "#0E0A0D"
PARED_CONDUCTO = "#B9786A"


class CabezaOtoscopia(CabezaExamen):
    """La otoscopía como la rinoscopía (nasal/RinoscopiaWindow.Cara): el
    mouse es el otoscopio. Sobre un conducto aparece el otoscopio y al lado
    se abre la lupa con lo que se ve; moverlo dentro del conducto recorre el
    tímpano. Arrastrar desde la oreja tira del pabellón (queda tirado, con
    su flecha, hasta soltarlo); arrastrar fuera de la oreja gira la cabeza.

    `vista(oido)` dice qué se ve por ese conducto: {'foto': QPixmap o None,
    'cono': fracción del ancho de la foto que deja ver el espéculo,
    'tapado': sin el conducto enderezado se ve la pared, 'texto': lo que se
    lee en la lupa en lugar de la foto, o None}."""
    miro = Signal(str)       # el otoscopio entró a ese conducto
    salio = Signal()

    def __init__(self, vista, parent=None):
        super().__init__(parent)
        self.vista = vista
        self.herramienta = "otoscopia"
        self._mouse = None
        self._conducto = None   # el conducto donde está el otoscopio

    def _centro_conducto(self, oido):
        sitio = "cae_der" if oido == "od" else "cae_izq"
        normal = np.array([-1.0 if oido == "od" else 1.0, 0.0, 0.0])
        return self.en_pantalla(_pos(sitio), normal)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            tocado = self.tocar(ev.position())
            lado = oreja(tocado[0]) if tocado is not None else None
            if lado is not None:
                self._tirando = (lado, ev.position(), ev.position())
                self._salir()
                self.update()
                return
        CabezaElectrodos.mousePressEvent(self, ev)

    def mouseMoveEvent(self, ev):
        if self._tirando is not None or self._apretado is not None:
            super().mouseMoveEvent(ev)
            return
        self._mouse = ev.position()
        tocado = self.tocar(ev.position())
        oido = conducto(tocado[0]) if tocado is not None else None
        if self._conducto is not None:
            # Dentro del conducto se puede mover un poco sin salir
            c = self._centro_conducto(self._conducto)
            _, escala = self._marco()
            if c is not None and math.hypot(c.x() - self._mouse.x(), c.y() - self._mouse.y()) \
                    <= RECORRIDO_PX * escala * 1.4:
                oido = self._conducto
        if oido != self._conducto:
            self._conducto = oido
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
            self.salio.emit()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self._tirando is not None:
            super().mouseReleaseEvent(ev)
            return
        CabezaElectrodos.mouseReleaseEvent(self, ev)

    # ------------------------------------------------------------ dibujo
    def paintEvent(self, ev):
        CabezaElectrodos.paintEvent(self, ev)
        from PySide6.QtGui import QPainter
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.tiron is not None:
            self._flecha_tiron(p)
        if self._tirando is not None:
            _lado, inicio, fin = self._tirando
            self._flecha(p, inicio, fin)
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
        m = self._mouse - centro
        dx = max(-1.0, min(1.0, m.x() / recorrido))
        dy = max(-1.0, min(1.0, m.y() / recorrido))
        # El disco sigue un poco al mouse, sin salirse de la cabeza a la vista
        c = QPointF(centro.x() + dx * recorrido, centro.y() + dy * recorrido)
        c.setX(max(r + 6, min(self.width() - r - 6, c.x())))
        c.setY(max(r + 6, min(self.height() - r * 2.2, c.y())))
        self._pintar_mango(p, c, r, self._hacia_la_nuca(oido, centro))
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
            # La mitad del tímpano llena el disco; el mouse recorre el resto
            lado = min(foto.width(), foto.height()) * ZOOM_TIMPANO
            libre_x = (foto.width() - lado) / 2
            libre_y = (foto.height() - lado) / 2
            fuente = QRectF(libre_x + dx * libre_x, libre_y + dy * libre_y, lado, lado)
            hueco = QPainterPath()
            hueco.addEllipse(c, claro, claro)
            p.save()
            p.setClipPath(hueco)
            p.drawPixmap(caja, foto, fuente)
            if v.get("tapado"):
                # Sin enderezar el conducto, la pared tapa casi todo
                pared = QPainterPath()
                pared.addEllipse(c, claro, claro)
                ventana = QPainterPath()
                ventana.addEllipse(QPointF(c.x() + claro * 0.3, c.y() + claro * 0.2), claro * 0.42, claro * 0.42)
                p.fillPath(pared.subtracted(ventana), QColor(PARED_CONDUCTO))
            from PySide6.QtGui import QRadialGradient
            luz = QRadialGradient(c, claro)
            luz.setColorAt(0.0, QColor(255, 220, 150, 30))
            luz.setColorAt(0.8, QColor(0, 0, 0, 0))
            luz.setColorAt(1.0, QColor(14, 10, 13, 220))
            p.fillRect(caja, luz)
            p.restore()
        p.restore()
        aro = max(6.0, r * 0.07)
        p.setPen(QPen(QColor("#2B2B30"), aro))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(c, r + aro / 2, r + aro / 2)
        p.setPen(QPen(QColor(255, 255, 255, 90), aro * 0.3))
        p.drawArc(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), 40 * 16, 70 * 16)

    @staticmethod
    def _pintar_mango(p, c, r, hacia):
        """El mango del otoscopio, desde el disco hacia abajo y hacia la
        nuca: el cuello y el mango moleteado."""
        import math as _m
        ang = _m.radians(90 + hacia * -25)          # hacia abajo, inclinado a la nuca
        u = QPointF(_m.cos(ang), _m.sin(ang))
        n = QPointF(-u.y(), u.x())
        base = c + u * (r * 0.92)
        cuello = [base + n * (r * 0.16), base + u * (r * 0.32) + n * (r * 0.11),
                  base + u * (r * 0.32) - n * (r * 0.11), base - n * (r * 0.16)]
        mango = [base + u * (r * 0.32) + n * (r * 0.17), base + u * (r * 1.45) + n * (r * 0.19),
                 base + u * (r * 1.45) - n * (r * 0.19), base + u * (r * 0.32) - n * (r * 0.17)]
        from PySide6.QtGui import QPolygonF
        p.setPen(QPen(QColor("#1E1E22"), 1.5))
        p.setBrush(QColor("#3A3A40"))
        p.drawPolygon(QPolygonF(cuello))
        p.setBrush(QColor("#2C2C31"))
        p.drawPolygon(QPolygonF(mango))
        p.setPen(QPen(QColor(255, 255, 255, 40), 1.2))
        for k in range(1, 9):
            a = base + u * (r * (0.32 + 0.13 * k))
            p.drawLine(a + n * (r * 0.17), a - n * (r * 0.17))
