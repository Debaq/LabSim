"""Ficha de umbrales del ASSR: lo que va en la pestaña donde el ABR tiene la
Latencia/Intensidad (que en el ASSR no existe: no hay latencias).

Dos paneles, como en el libro (fig_assr.py):

- Detección por oído, portadora y nivel: cada nivel probado es una celda
  (verde: respuesta clara, con su p; gris: ausente; naranja: no
  concluyente) y el umbral lleva borde.
- Umbral del ASSR (dB nHL, cuadrado vacío) y audiograma estimado (dB eHL,
  cuadrado lleno y línea), un gráfico por oído. Sin la audiometría del caso:
  eso es lo que el alumno tiene que estimar.

Se dibuja con QPainter desde el registro del panel (vivo o guardado), así
que sirve igual al registrar, al retomar y al mirar una sesión anterior.
"""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from abr import assr
from core import tema

VERDE, GRIS, NARANJA = "#1E9C8B", "#5B6475", "#E8A33D"
MARCO, TENUE, TINTA, GRILLA = "#16202C", "#6B7280", "#1F2933", "#E5E8EC"
COLOR = {"OD": tema.OD, "OI": tema.OI}
NOMBRE = {"OD": "Oído derecho", "OI": "Oído izquierdo"}
ROTULO_F = {500: "500", 1000: "1.000", 2000: "2.000", 4000: "4.000"}
CORTO_F = {500: "500", 1000: "1k", 2000: "2k", 4000: "4k"}


def _p(p):
    if p is None:
        return ""
    return "p < 0,001" if p < 0.001 else f"p = {p:.3f}".replace(".", ",")


def datos(rec, correccion):
    """Lo que dibuja la ficha, sacado del registro: por oído, la grilla
    {(portadora, nivel): (detectada, concluyente, p)} y por portadora el
    umbral (nHL), el estimado (eHL) y si terminó sin respuesta."""
    out = {}
    if rec is None:
        return out
    for side in assr.SIDES:
        if not rec.has_ear(side):
            continue
        grilla, umbral, ehl, sin_resp = {}, {}, {}, {}
        for f in assr.CARRIERS:
            canal = (side, f)
            tramos = list(rec.history.get(canal) or [])
            st = rec.stats(canal)
            if st.get("n", 0) >= assr.MIN_EPOCHS:
                tramos.append({"level": rec.levels[canal], "detected": st["detected"],
                               "conclusive": st["conclusive"], "p": st.get("p")})
            for t in tramos:
                clave = (f, int(t["level"]))
                det, conc, p = grilla.get(clave, (False, False, None))
                tp = t.get("p")
                grilla[clave] = (det or bool(t.get("detected")), conc or bool(t.get("conclusive")),
                                 tp if p is None else (p if tp is None else min(p, tp)))
            umbral[f] = rec.threshold_hl(canal)
            ehl[f] = rec.threshold_ehl(canal, correccion)
            sin_resp[f] = umbral[f] is None and any(
                c and not d for (ff, _), (d, c, _) in grilla.items() if ff == f)
        out[side] = {"grilla": grilla, "umbral": umbral, "ehl": ehl, "sin_resp": sin_resp}
    return out


class AssrResumen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(500, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("AssrResumen { background: white; }")
        self.d = {}
        self.correccion = dict(assr.DEFAULT_EHL_CORRECTION)

    def set_registro(self, rec, correccion=None):
        self.correccion = dict(correccion or assr.DEFAULT_EHL_CORRECTION)
        self.d = datos(rec, self.correccion)
        self.update()

    # ------------------------------------------------------------ dibujo
    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("white"))
        if not self.d:
            p.setPen(QColor(TENUE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin registro del ASSR todavía.")
            p.end()
            return
        W, H = self.width(), self.height()
        # Lado a lado si hay ancho; si no, la grilla arriba y el audiograma abajo.
        if W >= 1.9 * H:
            izq, der = QRectF(0, 0, W * 0.5, H), QRectF(W * 0.5, 0, W * 0.5, H)
        else:
            izq, der = QRectF(0, 0, W, H * 0.5), QRectF(0, H * 0.5, W, H * 0.5)
        self._grillas(p, izq.adjusted(12, 8, -12, -8))
        self._audiogramas(p, der.adjusted(12, 8, -12, -8))
        p.end()

    def _texto(self, p, x, y, texto, tam=8.5, color=TENUE, peso=QFont.Weight.Normal,
               ancla=Qt.AlignmentFlag.AlignLeft, ancho=400):
        f = QFont(self.font())
        f.setPointSizeF(tam)
        f.setWeight(peso)
        p.save()
        p.setFont(f)
        p.setPen(QColor(color))
        r = QRectF(x - ancho if ancla & Qt.AlignmentFlag.AlignRight else
                   x - ancho / 2 if ancla & Qt.AlignmentFlag.AlignHCenter else x, y - 12, ancho, 16)
        p.drawText(r, ancla | Qt.AlignmentFlag.AlignVCenter,
                   p.fontMetrics().elidedText(texto, Qt.TextElideMode.ElideRight, int(ancho)))
        p.restore()

    def _grillas(self, p, r):
        self._texto(p, r.left(), r.top() + 8,
                    "Detección por oído, portadora y nivel · verde: respuesta clara · "
                    "gris: ausente · naranja: no concluyente · borde: umbral", ancho=r.width())
        niveles = sorted({n for d in self.d.values() for (_, n) in d["grilla"]}, reverse=True)
        lados = list(self.d)
        if not niveles:
            return
        ml, top, sep, mb = 34, r.top() + 44, 22, 34
        ancho = (r.width() - ml * len(lados) - sep * (len(lados) - 1)) / len(lados)
        celda_w = ancho / len(assr.CARRIERS)
        celda_h = min(30.0, (r.bottom() - mb - top) / len(niveles))
        for j, side in enumerate(lados):
            x0 = r.left() + j * (ancho + ml + sep) + ml
            d = self.d[side]
            self._texto(p, x0, top - 12, NOMBRE[side], 10, COLOR[side], QFont.Weight.Bold)
            for k, nivel in enumerate(niveles):
                y = top + k * celda_h
                self._texto(p, x0 - 6, y + celda_h / 2, str(nivel), 8, TENUE,
                            ancla=Qt.AlignmentFlag.AlignRight)
                for i, f in enumerate(assr.CARRIERS):
                    if (f, nivel) not in d["grilla"]:
                        continue
                    det, conc, pv = d["grilla"][(f, nivel)]
                    color = VERDE if det else (GRIS if conc else NARANJA)
                    caja = QRectF(x0 + i * celda_w, y, celda_w, celda_h).adjusted(1, 1, -1, -1)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(color))
                    p.drawRect(caja)
                    txt = _p(pv) if det else ("ausente" if conc else "no concl.")
                    self._texto(p, caja.center().x(), caja.center().y(), txt, 7.5, "white",
                                QFont.Weight.Bold, Qt.AlignmentFlag.AlignHCenter)
                    if det and d["umbral"].get(f) == nivel:
                        p.setPen(QPen(QColor(MARCO), 2.5))
                        p.setBrush(Qt.BrushStyle.NoBrush)
                        p.drawRect(caja.adjusted(1, 1, -1, -1))
            y_pie = top + len(niveles) * celda_h
            for i, f in enumerate(assr.CARRIERS):
                self._texto(p, x0 + (i + 0.5) * celda_w, y_pie + 10, ROTULO_F[f], 8, TENUE,
                            ancla=Qt.AlignmentFlag.AlignHCenter)
            self._texto(p, x0 + 2 * celda_w, y_pie + 24, "Portadora (Hz)", 8, TENUE,
                        ancla=Qt.AlignmentFlag.AlignHCenter)
            if j == 0:
                p.save()
                p.translate(r.left() + 6, top + len(niveles) * celda_h / 2)
                p.rotate(-90)
                self._texto(p, 0, 0, "Nivel (dB nHL)", 8, TENUE, ancla=Qt.AlignmentFlag.AlignHCenter)
                p.restore()

    def _audiogramas(self, p, r):
        corr = " / ".join(f"{self.correccion[f]:g}" for f in assr.CARRIERS)
        self._texto(p, r.left(), r.top() + 8,
                    f"Umbral del ASSR y audiograma estimado · corrección {corr} dB "
                    "en 500 / 1.000 / 2.000 / 4.000 Hz", ancho=r.width())
        lados = list(self.d)
        ml, sep, top, mb = 40, 26, r.top() + 44, 34
        ancho = (r.width() - ml * len(lados) - sep * (len(lados) - 1)) / len(lados)
        # Proporción de audiograma, no todo el alto disponible.
        alto = min(r.bottom() - mb - top, ancho * 0.85)
        for j, side in enumerate(lados):
            x0 = r.left() + j * (ancho + ml + sep) + ml
            d, color = self.d[side], QColor(COLOR[side])
            self._texto(p, x0, top - 12, NOMBRE[side], 10, COLOR[side], QFont.Weight.Bold)

            def X(i):
                return x0 + (i + 0.5) / len(assr.CARRIERS) * ancho

            def Y(db):
                return top + (max(-10.0, min(120.0, db)) + 10) / 130 * alto

            p.setPen(QPen(QColor(GRILLA), 1))
            for db in range(0, 121, 20):
                p.drawLine(QPointF(x0, Y(db)), QPointF(x0 + ancho, Y(db)))
                self._texto(p, x0 - 6, Y(db), str(db), 8, TENUE, ancla=Qt.AlignmentFlag.AlignRight)
            for i, f in enumerate(assr.CARRIERS):
                p.setPen(QPen(QColor(GRILLA), 1))
                p.drawLine(QPointF(X(i), top), QPointF(X(i), top + alto))
                self._texto(p, X(i), top + alto + 10, CORTO_F[f], 8, TENUE,
                            ancla=Qt.AlignmentFlag.AlignHCenter)
            self._texto(p, x0 + ancho / 2, top + alto + 24, "Hz", 8, TENUE,
                        ancla=Qt.AlignmentFlag.AlignHCenter)
            p.setPen(QPen(QColor(TENUE), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(QRectF(x0, top, ancho, alto))
            if j == 0:
                p.save()
                p.translate(r.left() + 8, top + alto / 2)
                p.rotate(-90)
                self._texto(p, 0, 0, "dB", 8, TENUE, ancla=Qt.AlignmentFlag.AlignHCenter)
                p.restore()
            # estimado (eHL): línea y cuadrado lleno
            pts = [(X(i), Y(d["ehl"][f])) for i, f in enumerate(assr.CARRIERS) if d["ehl"].get(f) is not None]
            p.setPen(QPen(color, 2))
            for a, b in zip(pts, pts[1:]):
                p.drawLine(QPointF(*a), QPointF(*b))
            lado = 8
            for x, y in pts:
                p.setBrush(color)
                p.drawRect(QRectF(x - lado / 2, y - lado / 2, lado, lado))
            # umbral del ASSR (nHL): cuadrado vacío
            p.setBrush(QColor("white"))
            p.setPen(QPen(color, 1.6))
            for i, f in enumerate(assr.CARRIERS):
                u = d["umbral"].get(f)
                if u is not None:
                    p.drawRect(QRectF(X(i) - lado / 2, Y(u) - lado / 2, lado, lado))
                elif d["sin_resp"].get(f):
                    self._texto(p, X(i), Y(108), "sin", 7.5, COLOR[side], ancla=Qt.AlignmentFlag.AlignHCenter)
                    self._texto(p, X(i), Y(116), "respuesta", 7.5, COLOR[side],
                                ancla=Qt.AlignmentFlag.AlignHCenter)
            if j == 0:
                self._leyenda(p, x0 + 8, top + alto - 32, color)

    def _leyenda(self, p, x, y, color):
        p.setPen(QPen(color, 1.6))
        p.setBrush(QColor("white"))
        p.drawRect(QRectF(x, y - 4, 8, 8))
        self._texto(p, x + 14, y, "umbral ASSR (dB nHL)", 7.5, TINTA)
        p.setPen(QPen(color, 2))
        p.drawLine(QPointF(x - 4, y + 16), QPointF(x + 12, y + 16))
        p.setBrush(color)
        p.drawRect(QRectF(x, y + 12, 8, 8))
        self._texto(p, x + 18, y + 16, "estimado (dB eHL)", 7.5, TINTA)
