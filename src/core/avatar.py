# -*- coding: utf-8 -*-
"""Avatares circulares para el chat con el paciente: foto real si existe
(ver PatientPhoto.php en labsim_backend), si no un círculo de color sólido
con las iniciales del nombre -- mismo criterio visual que Slack/Gmail/etc.
para cuando alguien no tiene foto de perfil."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont

_PALETTE = [
    QColor("#5B8DEF"), QColor("#E0679B"), QColor("#4CAF93"), QColor("#F0A24B"),
    QColor("#9B7CE0"), QColor("#4BA3C7"), QColor("#D9704D"), QColor("#6EB05B"),
]


def _iniciales(nombre):
    partes = [p for p in (nombre or "").split() if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def _color_por(nombre):
    # Determinístico: el mismo nombre siempre cae en el mismo color, así el
    # paciente/alumno no cambia de color de un chat a otro.
    idx = sum(ord(c) for c in (nombre or "")) % len(_PALETTE)
    return _PALETTE[idx]


def avatar_iniciales(nombre, size=32):
    """Círculo de color con las iniciales del nombre -- fallback cuando no
    hay foto (o mientras se está pidiendo al backend)."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(_color_por(nombre))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    painter.setPen(QColor("#ffffff"))
    font = QFont()
    font.setPixelSize(max(8, int(size * 0.42)))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, _iniciales(nombre))
    painter.end()
    return pixmap


def avatar_circular_desde_bytes(data, size=32):
    """Recorta a círculo + ajusta al tamaño pedido una imagen ya cargada
    (bytes PNG/JPG). El avatar que sirve PatientPhoto.php ya viene circular
    con alfa, así que esto en la práctica solo la reescala -- pero recortar
    de nuevo no hace daño y deja la función a prueba de que llegue algo
    cuadrado. None si los bytes no son una imagen válida."""
    src = QPixmap()
    if not data or not src.loadFromData(data):
        return None
    src = src.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    x = (size - src.width()) // 2
    y = (size - src.height()) // 2
    painter.drawPixmap(x, y, src)
    painter.end()
    return pixmap
