#!/usr/bin/env python3
"""Dibuja las ilustraciones del cap. 30 (Oír y no entender):

    cap30-que-mide-el-puntaje.svg  lo que se suma en el puntaje de una prueba central (esquema)
    cap30-perfil-nino.svg          perfil de rendimiento del caso 30.1 (z contra la norma de cada versión)
    cap30-perfil-mayor.svg         perfil de rendimiento del caso 30.2

Esquemas propios, no IA. Los resultados de los perfiles son INVENTADOS para el libro:
el z supone una norma de la versión de cada prueba, que aquí no se da."""
import pathlib

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

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{w}"{d}/>')

    def r(self, x, y, w, h, fill, stroke='none', sw=1, rx=4):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def c(self, x, y, rad, fill, stroke='none'):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def que_mide():
    c = Lienzo(700, 250)
    c.t(14, 20, 'Lo que se suma en el puntaje de una prueba de procesamiento central', 10.5, TINTA, 'start', 700)
    cajas = [('Audición periférica', 'umbral, oído medio', COCLEAR),
             ('Atención', 'sostenida y selectiva', RETRO),
             ('Memoria de trabajo', 'retener y repetir', RETRO),
             ('Lenguaje', 'léxico, instrucción', RETRO),
             ('Procesamiento auditivo', 'lo que se quiere medir', AVISO)]
    x0, w, g = 24, 112, 10
    y0 = 52
    for i, (tit, sub, col) in enumerate(cajas):
        x = x0 + i * (w + g)
        c.r(x, y0, w, 74, '#fff', col, 2)
        c.t(x + w / 2, y0 + 30, tit, 8.5, col, 'middle', 700)
        c.t(x + w / 2, y0 + 50, sub, 7.5, TENUE)
        c.l(x + w / 2, y0 + 74, x + w / 2, y0 + 96, col, 1.5)
        c.t(x + w / 2, y0 + 92, '', 7)
    xs = x0
    xe = x0 + 5 * w + 4 * g
    c.l(x0 + w / 2, y0 + 96, x0 + 4 * (w + g) + w / 2, y0 + 96, FUERTE, 1.5)
    c.l((xs + xe) / 2, y0 + 96, (xs + xe) / 2, y0 + 118, TINTA, 1.5)
    c.r((xs + xe) / 2 - 130, y0 + 118, 260, 40, '#f6f4ef', TINTA, 1.5)
    c.t((xs + xe) / 2, y0 + 143, 'Puntaje de la prueba (un solo número)', 9.5, TINTA, 'middle', 700)
    c.t(14, 236, 'Un puntaje bajo no dice cuál de las cinco cajas falló. Por eso se cierra lo periférico, se mide lo demás y se describe un perfil.',
        8, TENUE, 'start')
    c.guardar('cap30-que-mide-el-puntaje.svg')


def perfil(nombre, titulo, filas):
    """filas: (etiqueta, z, color) ; z en desviaciones estándar contra la norma de la versión y la edad."""
    alto = 110 + 30 * len(filas)
    c = Lienzo(700, alto)
    c.t(14, 20, titulo, 10.5, TINTA, 'start', 700)
    xl, xr = 230, 660              # eje z de -4 a +2
    z2x = lambda z: xl + (z + 4) / 6 * (xr - xl)
    ytop, ybot = 40, 52 + 30 * len(filas)
    c.r(z2x(-4), ytop, z2x(-2) - z2x(-4), ybot - ytop, '#fbe9e6', rx=0)
    for z in range(-4, 3):
        c.l(z2x(z), ytop, z2x(z), ybot, GRILLA if z not in (0, -2) else FUERTE, 1, '4 3' if z == -2 else None)
        c.t(z2x(z), ybot + 16, f'{z:+d}'.replace('+0', '0').replace('-', '−'), 8.5, TENUE)
    c.t(z2x(-3), ytop + 12, 'bajo −2 DE', 8, AVISO, 'middle', 700)
    for i, (et, z, col) in enumerate(filas):
        y = ytop + 28 + 30 * i
        c.t(220, y + 3, et, 8.5, TINTA, 'end')
        c.l(z2x(0), y, z2x(z), y, col, 2)
        c.c(z2x(z), y, 6, col, '#fff')
    c.t((xl + xr) / 2, ybot + 32, 'desviaciones estándar respecto de la norma de la versión y de la edad', 8.5, TENUE)
    c.t(14, alto - 6, 'Datos inventados para el libro. El z supone una norma de cada versión que aquí no se da.', 7.5, TENUE, 'start')
    c.guardar(nombre)


if __name__ == '__main__':
    que_mide()
    perfil('cap30-perfil-nino.svg', 'Alejandro, 9 años · perfil de rendimiento', [
        ('Dígitos dicóticos · OD', -0.4, RETRO),
        ('Dígitos dicóticos · OI', -2.8, AVISO),
        ('Patrón de frecuencia (nombrado)', -2.4, AVISO),
        ('Patrón de duración (nombrado)', -1.1, RETRO),
        ('GIN (promedio de los dos oídos)', -1.6, RETRO),
        ('Matrix en ruido (SNR)', -0.6, RETRO)])
    perfil('cap30-perfil-mayor.svg', 'Daniela, 71 años · perfil de rendimiento', [
        ('Dígitos dicóticos · OD', -0.9, RETRO),
        ('Dígitos dicóticos · OI', -2.3, AVISO),
        ('GIN (promedio de los dos oídos)', -1.2, RETRO),
        ('Patrón de duración (nombrado)', -1.4, RETRO),
        ('Frases en ruido (SNR)', -2.6, AVISO)])
