#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H20 (prueba de audífonos):

    h20-rango-dinamico.svg  el rango dinamico del oido normal, con perdida coclear, con ganancia lineal y con compresion
    h20-ventilacion.svg     molde cerrado y ventilado: que pasa con los graves

SVG propios, no IA: son esquemas. Son esquemas: no llevan cifras clínicas, solo la forma."""
import math
import pathlib
import random

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO = '#c0571c', '#21796c', '#c62f3a'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
ESCALA = 1.2


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=9, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size * ESCALA:.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}{extra}/>')

    def poli(self, pts, color, w=2, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}{extra}/>')

    def guardar(self, nombre, defs=''):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><defs>{defs}</defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def punta(id_, color):
    return (f'<marker id="{id_}" markerWidth="6" markerHeight="6" refX="4" refY="3.5" '
            f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" '
            f'transform="scale(.8)" fill="{color}"/></marker>')


def rango():
    c = Lienzo(720, 335)
    top, bot = 50, 270          # nivel: arriba fuerte, abajo suave
    def y(n):                   # n en 0..100 (esquema), 100 = muy fuerte
        return bot - (bot - top) * n / 100
    cols = [(110, 'A · Oído normal'), (290, 'B · Pérdida coclear,\nsin audífono'),
            (470, 'C · Ganancia lineal\n(todo sube igual)'), (640, 'D · Compresión\n(sube más lo suave)')]
    for x, tit in cols:
        for k, linea in enumerate(tit.split('\n')):
            c.t(x, 18 + 13 * k, linea, 9.5, TINTA, 'middle', 700)
        c.l(x, top, x, bot, FUERTE, 1)
    w = 52
    def rect(x, a, b, color, op, nombre=None):
        c.out.append(f'<rect x="{x - w / 2:.1f}" y="{y(b):.1f}" width="{w}" height="{y(a) - y(b):.1f}" '
                     f'fill="{color}" fill-opacity="{op}" stroke="{color}" stroke-width="1"/>')
    # rangos audibles: entre el umbral (abajo) y la molestia (arriba)
    rect(110, 5, 95, COCLEAR, .13)
    rect(290, 55, 95, COCLEAR, .13)
    rect(470, 25, 95, COCLEAR, .13)
    rect(640, 25, 95, COCLEAR, .13)
    # el habla: del suave al fuerte
    rect(110, 30, 60, RETRO, .45)
    rect(290, 30, 60, RETRO, .45)
    rect(470, 55, 85, RETRO, .45)
    rect(640, 28, 52, RETRO, .45)
    # molestia
    for x in (110, 290, 470, 640):
        c.l(x - w / 2 - 8, y(95), x + w / 2 + 8, y(95), AVISO, 1.6)
    c.t(110, y(95) - 6, 'molestia', 8, AVISO)
    for x, n in ((110, 5), (290, 55), (470, 25), (640, 25)):
        c.l(x - w / 2 - 8, y(n), x + w / 2 + 8, y(n), TINTA, 1.6)
    c.t(110, y(5) + 13, 'umbral', 8, TINTA)
    c.t(290, y(55) - 6, 'umbral', 8, TINTA)
    c.t(470, y(25) + 13, 'umbral con audífono', 8, TINTA)
    c.t(640, y(25) + 13, 'umbral con audífono', 8, TINTA)
    # el habla bajo el umbral en B
    c.t(290, y(45) + 3, 'habla', 8, '#fff', 'middle', 700)
    c.t(110, y(45) + 3, 'habla', 8, '#fff', 'middle', 700)
    c.t(470, y(70) + 3, 'habla', 8, '#fff', 'middle', 700)
    c.t(640, y(40) + 3, 'habla', 8, '#fff', 'middle', 700)
    c.t(290, bot + 28, 'casi toda bajo el umbral: no se oye', 8, AVISO)
    c.t(470, bot + 28, 'el habla fuerte pasa la molestia', 8, AVISO)
    c.t(640, bot + 28, 'cabe entera en el rango', 8, RETRO, 'middle', 700)
    c.t(30, top - 4, 'fuerte', 8, TENUE, 'middle')
    c.t(30, bot + 10, 'suave', 8, TENUE, 'middle')
    c.l(30, top + 4, 30, bot - 4, TENUE, 1, extra=' marker-end="url(#p-r)"')
    c.t(360, 322, 'Un oído y una frecuencia. El rango entre el umbral y la molestia se achica; el habla no.', 8.5, TENUE)
    c.guardar('h20-rango-dinamico.svg', punta('p-r', TENUE))


def ventilacion():
    c = Lienzo(720, 332)
    c.t(14, 20, 'Lo que pasa con los graves según el molde', 10.5, TINTA, 'start', 700)
    for k, (x0, tit, cerrado) in enumerate(((50, 'A · Molde cerrado', True), (390, 'B · Molde con ventilación', False))):
        # conducto
        c.t(x0 + 120, 46, tit, 9.5, TINTA, 'middle', 700)
        cy = 85
        c.out.append(f'<rect x="{x0}" y="{cy - 14}" width="240" height="28" rx="14" fill="#f3e3d4" stroke="{FUERTE}"/>')
        c.out.append(f'<rect x="{x0 + 70}" y="{cy - 11}" width="80" height="22" rx="7" fill="{COCLEAR}" fill-opacity=".55" stroke="{COCLEAR}"/>')
        c.t(x0 + 110, cy + 3, 'molde', 8, '#fff', 'middle', 700)
        c.t(x0 + 225, cy + 3, 'tímpano', 7.5, TENUE, 'end')
        c.t(x0 + 10, cy + 3, 'afuera', 7.5, TENUE, 'start')
        if not cerrado:
            c.l(x0 + 72, cy - 3, x0 + 148, cy - 3, '#fff', 3)
            c.t(x0 + 110, cy + 26, 'ventilación', 8, RETRO, 'middle', 700)
        # curvas de graves
        gx, gy, gw, gh = x0 + 20, 140, 200, 110
        c.l(gx, gy + gh, gx + gw, gy + gh, TENUE, 1)
        c.l(gx, gy, gx, gy + gh, TENUE, 1)
        c.t(gx + gw / 2, gy + gh + 18, 'frecuencia (graves → agudos)', 8, TENUE)
        c.t(gx - 6, gy + 4, 'nivel', 8, TENUE, 'end')
        pts_ampl, pts_oclu = [], []
        n = 40
        for i in range(n + 1):
            u = i / n
            amp = 0.55 + 0.25 * u if cerrado else (0.18 + 0.7 * (1 - math.exp(-6 * u)) * (0.9))
            pts_ampl.append((gx + u * gw, gy + gh - gh * amp))
        c.poli(pts_ampl, COCLEAR, 2.2)
        c.t(gx + gw - 4, pts_ampl[-1][1] - 6, 'ganancia', 8, COCLEAR, 'end', 700)
        if cerrado:
            c.t(gx + 4, gy + gh + 32, 'los graves quedan atrapados:', 8, AVISO, 'start', 700)
            c.t(gx + 4, gy + gh + 44, 'refuerzo de graves y oclusión', 8, AVISO, 'start', 700)
        else:
            c.t(gx + 4, gy + gh + 32, 'parte de los graves se escapa:', 8, RETRO, 'start', 700)
            c.t(gx + 4, gy + gh + 44, 'menos ganancia grave, menos oclusión', 8, RETRO, 'start', 700)
    c.t(360, 322, 'El efecto depende del largo y el diámetro de la ventilación y del conducto.', 8.5, TENUE)
    c.guardar('h20-ventilacion.svg')


if __name__ == '__main__':
    rango()
    ventilacion()
