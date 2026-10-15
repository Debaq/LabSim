"""Lienzo SVG mínimo: lo justo para las figuras del libro, sin dependencias."""
import json
from xml.sax.saxutils import escape

from . import estilo as E


def _n(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


class Svg:
    def __init__(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.partes = []
        # Anclas: dónde quedó cada cosa dibujada ("OD 4000", "OD 80 V"...),
        # para que el libro ponga globos encima sin rehacer las cuentas.
        self.anclas = {}

    def ancla(self, clave, x, y):
        self.anclas[clave] = [round(x, 2), round(y, 2)]

    def crudo(self, s):
        self.partes.append(s)

    def linea(self, x1, y1, x2, y2, color=E.GRILLA, ancho=1.0, extra=''):
        self.crudo(f'<line x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" '
                   f'stroke="{color}" stroke-width="{ancho}" {extra}/>')

    def rect(self, x, y, w, h, relleno, borde='none', ancho=0, extra=''):
        self.crudo(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" '
                   f'fill="{relleno}" stroke="{borde}" stroke-width="{ancho}" {extra}/>')

    def texto(self, x, y, s, tam=E.T_EJE, color=E.TINTA_2, ancla='middle', peso=400, extra=''):
        self.crudo(f'<text x="{_n(x)}" y="{_n(y)}" font-size="{tam}" fill="{color}" '
                   f'text-anchor="{ancla}" font-weight="{peso}" {extra}>{escape(str(s))}</text>')

    def trazo(self, puntos, color, ancho=E.LINEA, opacidad=1.0, guiones=None):
        if len(puntos) < 2:
            return
        d = 'M' + ' L'.join(f'{_n(x)},{_n(y)}' for x, y in puntos)
        g = f' stroke-dasharray="{guiones}"' if guiones else ''
        self.crudo(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{ancho}" '
                   f'stroke-opacity="{opacidad}" stroke-linejoin="round" stroke-linecap="round"{g}/>')

    def camino(self, d, color, ancho=E.LINEA, relleno='none'):
        self.crudo(f'<path d="{d}" fill="{relleno}" stroke="{color}" stroke-width="{ancho}" '
                   f'stroke-linejoin="round" stroke-linecap="round"/>')

    def circulo(self, x, y, r, borde, relleno=E.PAPEL, ancho=E.LINEA):
        self.crudo(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="{relleno}" '
                   f'stroke="{borde}" stroke-width="{ancho}"/>')

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_n(self.ancho)} {_n(self.alto)}" '
                f'width="{_n(self.ancho)}" height="{_n(self.alto)}" font-family="{E.FUENTE}">'
                f'<rect width="100%" height="100%" fill="{E.PAPEL}"/>' + ''.join(self.partes)
                + (f'<metadata id="anclas">{json.dumps(self.anclas, ensure_ascii=False)}</metadata>' if self.anclas else '')
                + '</svg>')
