#!/usr/bin/env python3
"""cap27-sot-sano-pppd.svg (cap. 27, mareo que no se va): la posturografía de seis condiciones de un
paciente simulado sano y de uno con el vestíbulo sano y la dependencia visual marcada.

Los números salen del modelo postural de labyrinthus3d, corrido sin pantalla por
hacer_cap27_simulador.mjs (semilla fija, el promedio de tres intentos por condición). Se dibuja aquí,
sin nada de la interfaz del simulador. Las constantes del modelo (y sus límites normales) son órdenes de
magnitud docentes, no valores normativos.

    python3 docs/libro/ilustraciones/hacer_cap27_simulador.py"""
import json
import pathlib
import subprocess

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
ROJO, AZUL = '#c62f3a', '#2b5fa8'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent

# las seis condiciones: ojos abiertos, plataforma referida, entorno referido
SOT = [(True, False, False), (False, False, False), (True, False, True),
       (True, True, False), (False, True, False), (True, True, True)]


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{esc(s)}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                        f'stroke-width="{w}"{d}/>')

    def r(self, x, y, w, h, fill, op=1, stroke='none', sw=1, dash=None, rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                        f'fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def c(self, x, y, r, fill, stroke='none', w=1):
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>' + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def monito(c, x, y, ojos, plataforma, entorno):
    """La condición en dibujo: la caja del entorno, la persona y la plataforma (discontinuo = sigue el balanceo)."""
    c.r(x - 20, y, 40, 46, 'none', 1, TINTA, 1.3, '3 2.5' if entorno else None)
    c.c(x, y + 10, 4.5, '#fff', TINTA, 1.2)
    if ojos:
        c.c(x - 1.6, y + 9.5, 0.9, TINTA)
        c.c(x + 1.6, y + 9.5, 0.9, TINTA)
    else:
        c.l(x - 4.5, y + 9.5, x + 4.5, y + 9.5, TINTA, 2.2)
    c.l(x, y + 14.5, x, y + 30, TINTA, 1.2)
    c.l(x - 7, y + 20, x + 7, y + 20, TINTA, 1.2)
    c.l(x, y + 30, x - 5, y + 41, TINTA, 1.2)
    c.l(x, y + 30, x + 5, y + 41, TINTA, 1.2)
    c.l(x - 14, y + 43, x + 14, y + 43, TINTA, 3, '3 2.5' if plataforma else None)


def panel(c, x0, titulo, d, normal, an_normal):
    c.t(x0 + 180, 24, titulo, 12.5, TINTA, 'middle', 700)
    paso, ancho = 58, 34
    base, alto = 300, 170
    for i, (ojos, plat, ent) in enumerate(SOT):
        cx = x0 + 35 + paso * i
        monito(c, cx, 40, ojos, plat, ent)
        c.t(cx, 106, str(i + 1), 11, TINTA, 'middle', 700)
        c.r(cx - ancho / 2, base - alto, ancho, alto, '#fff', 1, FUERTE)
        v, cae = d['puntajes'][i], d['caidas'][i]
        bajo = v < normal[i]
        if cae:
            c.t(cx, base - 8, 'cae', 10.5, ROJO, 'middle', 700)
        else:
            h = alto * v / 100
            c.r(cx - ancho / 2, base - h, ancho, h, ROJO if bajo else AZUL, 0.9)
            c.t(cx, base - h - 5, str(v), 10.5, ROJO if bajo else TINTA, 'middle', 700 if bajo else 400)
        yl = base - alto * normal[i] / 100
        c.l(cx - ancho / 2 - 4, yl, cx + ancho / 2 + 4, yl, ROJO, 1.3, '4 2.5')
    # el análisis sensorial
    c.t(x0 + 5, 330, 'Análisis sensorial', 11.5, TINTA, 'start', 700)
    filas = [('soma', 'somatosensorial (2/1)'), ('vista', 'visual (4/1)'), ('vest', 'vestibular (5/1)'),
             ('pref', 'preferencia visual (3+6)/(2+5)')]
    bx, bw = x0 + 165, 150
    for k, (clave, nombre) in enumerate(filas):
        y = 346 + 21 * k
        v = d['analisis'][clave]
        bajo = v < an_normal[clave]
        c.t(x0 + 5, y + 10, nombre, 10, TINTA, 'start')
        c.r(bx, y, bw, 13, '#fff', 1, FUERTE)
        c.r(bx, y, bw * min(v, 1.0), 13, ROJO if bajo else AZUL, 0.9)
        xl = bx + bw * an_normal[clave]
        c.l(xl, y - 3, xl, y + 16, ROJO, 1.6)
        c.t(bx + bw + 6, y + 10.5, f'{v:.2f}'.replace('.', ','), 10, ROJO if bajo else TINTA, 'start', 700 if bajo else 400)
    c.t(x0 + 5, 448, f'Puntaje compuesto: {d["compuesto"]}', 11, TINTA, 'start', 700)


def main():
    datos = json.loads(subprocess.check_output(['node', str(AQUI / 'hacer_cap27_simulador.mjs')], text=True))
    c = Lienzo(760, 500)
    panel(c, 15, 'Paciente simulado sano', datos['sano'], datos['normal'], datos['analisis_normal'])
    c.l(385, 14, 385, 455, GRILLA, 1)
    panel(c, 400, 'Vestíbulo sano, dependencia visual marcada', datos['pppd'], datos['normal'], datos['analisis_normal'])
    c.t(15, 476, 'Barras: puntaje de equilibrio (100: quieto; 0: se cae). Rayado rojo: límite inferior del modelo.',
        10, TENUE, 'start')
    c.t(15, 492, 'Línea discontinua en el dibujo: el entorno visual o la plataforma siguen el balanceo del paciente.',
        10, TENUE, 'start')
    c.guardar('cap27-sot-sano-pppd.svg')


if __name__ == '__main__':
    main()
