"""
Iconos de línea de LabSim, dibujados con QPainter.

Son trazos sobre una grilla de 24x24 (el mismo estilo que Lucide/Feather:
línea de 1.8 px, puntas redondas, sin relleno). No se usa QtSvg ni se
cargan archivos: el build de la app solo lleva los módulos de Qt que
verificar_bundle.py conoce, y un icono dibujado aquí sale en cualquier
color y tamaño nítido sin sumar nada.

    icono("calendario", tema.ACENTO)        -> QIcon
    pixmap("reloj", tema.AVISO, 20)         -> QPixmap
"""

import re

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

# Cada icono es una lista de trazos sobre la grilla de 24:
#   ("c", cx, cy, r)            círculo
#   ("r", x, y, w, h, radio)    rectángulo redondeado
#   ("l", x1, y1, x2, y2)       línea
#   ("p", (x, y), (x, y), ...)  polilínea abierta
#   ("g", (x, y), (x, y), ...)  polígono cerrado
#   ("a", x, y, w, h, ini, ext) arco (grados, como QPainter.drawArc)
#   ("k", "M x y C x y x y x y L x y Z")  camino con M, L, C, Z (absolutos)
#   ("d", cx, cy)               punto relleno
_ICONOS = {
    "calendario": [("r", 3, 5, 18, 16, 3), ("l", 3, 10, 21, 10), ("l", 8, 3, 8, 7), ("l", 16, 3, 16, 7)],
    "calendario_vacio": [("r", 3, 5, 18, 16, 3), ("l", 3, 10, 21, 10), ("l", 8, 3, 8, 7),
                         ("l", 16, 3, 16, 7), ("l", 9, 15, 15, 15)],
    "reloj": [("c", 12, 12, 9), ("p", (12, 7), (12, 12), (15.5, 14))],
    "check": [("c", 12, 12, 9), ("p", (8, 12.5), (11, 15.5), (16, 9.5))],
    "x": [("c", 12, 12, 9), ("l", 9, 9, 15, 15), ("l", 15, 9, 9, 15)],
    "alerta": [("g", (12, 3.5), (21.5, 20), (2.5, 20)), ("l", 12, 10, 12, 14.5), ("d", 12, 17.3)],
    "persona": [("c", 12, 8, 4), ("k", "M4 21 C4 16 8 14 12 14 C16 14 20 16 20 21")],
    "buscar": [("c", 11, 11, 6.5), ("l", 16, 16, 21, 21)],
    "ficha": [("r", 5, 3, 14, 18, 2.5), ("l", 9, 8, 15, 8), ("l", 9, 12, 15, 12), ("l", 9, 16, 13, 16)],
    "atender": [("g", (7, 4.5), (19, 12), (7, 19.5))],
    "evolucion": [("k", "M4 20 L4.8 15.8 L16.5 4.1 C17.3 3.3 18.6 3.3 19.4 4.1 L19.9 4.6 "
                        "C20.7 5.4 20.7 6.7 19.9 7.5 L8.2 19.2 Z"), ("l", 14.5, 6.2, 17.8, 9.5)],
    "practica": [("a", 4, 4, 16, 16, 40 * 16, 250 * 16), ("p", (17.5, 2.5), (19.5, 6.5), (15.5, 7.5))],
    "libro": [("k", "M4 5 C4 4 5 3.5 6 3.5 L19 3.5 L19 18.5 L6 18.5 C5 18.5 4 19 4 20 Z"),
              ("k", "M4 20 C4 21 5 21.5 6 21.5 L19 21.5"), ("l", 8, 8, 15, 8)],
    "izquierda": [("p", (14.5, 6), (8.5, 12), (14.5, 18))],
    "derecha": [("p", (9.5, 6), (15.5, 12), (9.5, 18))],
    "lista": [("l", 9, 6.5, 20, 6.5), ("l", 9, 12, 20, 12), ("l", 9, 17.5, 20, 17.5),
              ("d", 4.8, 6.5), ("d", 4.8, 12), ("d", 4.8, 17.5)],
    "sin_cita": [("a", 3, 3, 18, 18, 0, 70 * 16), ("a", 3, 3, 18, 18, 90 * 16, 70 * 16),
                 ("a", 3, 3, 18, 18, 180 * 16, 70 * 16), ("a", 3, 3, 18, 18, 270 * 16, 70 * 16),
                 ("l", 12, 8.5, 12, 15.5), ("l", 8.5, 12, 15.5, 12)],
    "mensaje": [("k", "M4 5.5 C4 4.5 5 4 6 4 L18 4 C19 4 20 4.5 20 5.5 L20 14 C20 15 19 15.5 18 15.5 L10 15.5 L6 19.5 L6 15.5 C5 15 4 15 4 14 Z"),
                ("l", 8, 8.5, 16, 8.5), ("l", 8, 11.5, 13, 11.5)],
    "mas": [("l", 12, 5, 12, 19), ("l", 5, 12, 19, 12)],
    "info": [("c", 12, 12, 9), ("l", 12, 11, 12, 16.5), ("d", 12, 7.8)],
    "flecha": [("l", 5, 12, 19, 12), ("p", (13, 6), (19, 12), (13, 18))],
    "cerrar": [("l", 6, 6, 18, 18), ("l", 18, 6, 6, 18)],
}

_cache = {}


def _camino(spec):
    ruta = QPainterPath()
    t = re.findall(r"[MLCZ]|-?[\d.]+", spec)
    i = 0
    while i < len(t):
        cmd = t[i]
        if cmd == "M":
            ruta.moveTo(float(t[i + 1]), float(t[i + 2]))
            i += 3
        elif cmd == "L":
            ruta.lineTo(float(t[i + 1]), float(t[i + 2]))
            i += 3
        elif cmd == "C":
            v = [float(x) for x in t[i + 1:i + 7]]
            ruta.cubicTo(v[0], v[1], v[2], v[3], v[4], v[5])
            i += 7
        elif cmd == "Z":
            ruta.closeSubpath()
            i += 1
        else:
            i += 1
    return ruta


def _dibujar(p, trazos):
    for t in trazos:
        tipo = t[0]
        if tipo == "c":
            p.drawEllipse(QPointF(t[1], t[2]), t[3], t[3])
        elif tipo == "r":
            p.drawRoundedRect(QRectF(t[1], t[2], t[3], t[4]), t[5], t[5])
        elif tipo == "l":
            p.drawLine(QPointF(t[1], t[2]), QPointF(t[3], t[4]))
        elif tipo == "p":
            p.drawPolyline(QPolygonF([QPointF(x, y) for x, y in t[1:]]))
        elif tipo == "g":
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in t[1:]]))
        elif tipo == "a":
            p.drawArc(QRectF(t[1], t[2], t[3], t[4]), int(t[5]), int(t[6]))
        elif tipo == "k":
            p.drawPath(_camino(t[1]))


def pixmap(nombre, color="#5D1049", tam=20):
    """El icono `nombre` como QPixmap de `tam` px lógicos (dibujado al doble
    para que se vea nítido en pantallas de alta densidad)."""
    clave = (nombre, str(color), tam)
    if clave in _cache:
        return _cache[clave]
    escala = 2
    lado = tam * escala
    img = QImage(lado, lado, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(lado / 24.0, lado / 24.0)
    pen = QPen(QColor(color), 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Los puntos rellenos usan el color del trazo.
    for t in _ICONOS[nombre]:
        if t[0] == "d":
            p.save()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(color))
            p.drawEllipse(QPointF(t[1], t[2]), 1.3, 1.3)
            p.restore()
        else:
            _dibujar(p, [t])
    p.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(escala)
    _cache[clave] = pm
    return pm


def icono(nombre, color="#5D1049", tam=20):
    """El icono `nombre` como QIcon. Deshabilitado, Qt lo atenúa solo."""
    return QIcon(pixmap(nombre, color, tam))
