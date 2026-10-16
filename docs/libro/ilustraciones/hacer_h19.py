#!/usr/bin/env python3
"""Dibuja los esquemas propios de H19 (rehabilitación vestibular):

    h19-mctsib.svg        balanceo adelante-atrás en las 4 condiciones del mCTSIB (sano / sin vestíbulo)
    h19-compensacion.svg  recuperación en el tiempo: reposo (estática) y movimiento (dinámica)
    h19-vor-ejercicios.svg  deslizamiento retiniano y los ejercicios x1, x2 y de sustitución

Son esquemas docentes, no datos de un paciente. Las trazas y las curvas del
tiempo salen del modelo de labyrinthus3d (hacer_h19.mjs, solo lectura): sus
constantes son órdenes de magnitud para enseñar, no valores normativos, y por
eso ningún eje lleva cifras."""
import json
import math
import pathlib
import subprocess

TINTA, TENUE, GRILLA = '#24101a', '#8a8a90', '#e7e5e0'
ROJO, AZUL, VERDE, NARANJA = '#c62f3a', '#2b5fa8', '#21796c', '#b8741a'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent


class Dib:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, [f'<rect width="{w}" height="{h}" fill="#fff"/>']

    def t(self, x, y, s, size=10, color=TINTA, anchor='middle', peso=400):
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def linea(self, x1, y1, x2, y2, color=TINTA, w=1.2, flecha=None, dash=None):
        m = f' marker-end="url(#{flecha})"' if flecha else ''
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d}{m}/>')

    def poli(self, pts, color, w=1.6, fill='none', dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.o.append(f'<polyline points="{p}" fill="{fill}" stroke="{color}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def rect(self, x, y, w, h, fill='none', stroke=GRILLA, sw=1, rx=0):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circ(self, x, y, r, fill='none', stroke=TINTA, sw=1.2):
        self.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def guardar(self, nombre):
        defs = ''.join(f'<marker id="{i}" markerWidth="8" markerHeight="8" refX="6" refY="4" markerUnits="userSpaceOnUse" orient="auto">'
                       f'<path d="M0,0 L8,4 L0,8 z" fill="{c}"/></marker>' for i, c in (('pr', ROJO), ('pa', AZUL), ('pt', TINTA), ('pv', VERDE)))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}"><defs>{defs}</defs>'
               + ''.join(self.o) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def datos():
    r = subprocess.run(['node', str(AQUI / 'hacer_h19.mjs')], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def mctsib(d):
    W, H = 760, 420
    g = Dib(W, H)
    g.t(14, 22, 'Balanceo adelante-atrás en las cuatro condiciones del mCTSIB', 12.5, TINTA, 'start', 700)
    g.t(14, 38, 'Misma escala en todos los cuadros (20 s cada uno). Arriba, un laberinto sano; abajo, sin función vestibular en los dos oídos. Esquema del simulador, no un paciente.', 8.5, TENUE, 'start')
    conds = [('firme_abiertos', 'Firme, ojos abiertos'), ('firme_cerrados', 'Firme, ojos cerrados'),
             ('espuma_abiertos', 'Espuma, ojos abiertos'), ('espuma_cerrados', 'Espuma, ojos cerrados')]
    filas = [('sano', 'Vestíbulo sano', AZUL), ('bilateral', 'Sin vestíbulo (bilateral)', ROJO)]
    x0, cw, gap = 56, 160, 12
    ph, y0 = 135, 86
    escala = ph / 2 / 8.0  # ±8° en el alto del cuadro
    for fi, (clave, titulo, color) in enumerate(filas):
        y = y0 + fi * (ph + 38)
        g.t(x0, y - 24, titulo, 10.5, color, 'start', 700)
        for ci, (cond, rot) in enumerate(conds):
            x = x0 + ci * (cw + gap)
            g.rect(x, y, cw, ph, '#faf9f6')
            g.linea(x, y + ph / 2, x + cw, y + ph / 2, GRILLA, 1, dash='3 3')
            if fi == 0:
                g.t(x + cw / 2, y - 8, rot, 9.5, TINTA, 'middle', 600)
            tr = d[clave][cond]
            pts = []
            for t, ap in tr['serie']:
                if tr['cayo'] is not None and t > tr['cayo'] + 0.3:
                    break
                yy = y + ph / 2 - max(-8, min(8, ap)) * escala
                pts.append((x + t / 20 * cw, yy))
            g.poli(pts, color, 1.4)
            if tr['cayo'] is not None:
                xc, yc = pts[-1]
                g.t(xc + 6, yc + (14 if yc < y + ph - 24 else -6), 'se cae', 9, ROJO, 'start', 700)
    g.t(x0 - 6, y0 + 12, 'adelante', 8, TENUE, 'end')
    g.t(x0 - 6, y0 + ph - 4, 'atrás', 8, TENUE, 'end')
    g.t(x0 - 6, y0 + ph / 2 + 3, '0', 8, TENUE, 'end')
    g.t(x0 + 2 * (cw + gap) + cw / 2 + (cw + gap) / 2 - 6, H - 10, 'tiempo (20 s por cuadro)', 8.5, TENUE)
    g.guardar('h19-mctsib.svg')


def compensacion(d):
    W, H = 760, 310
    g = Dib(W, H)
    g.t(14, 22, 'Compensación después de perder un laberinto: lo estático y lo dinámico', 12.5, TINTA, 'start', 700)
    g.t(14, 38, 'Esquema con las curvas del simulador; los tiempos reales varían de un paciente a otro y los ejercicios los adelantan. Sin cifras a propósito.', 8.5, TENUE, 'start')
    x0, y0, w, h = 70, 60, 520, 220
    g.rect(x0, y0, w, h, '#faf9f6')
    marcas = [(1, '1 día'), (7, '1 semana'), (30, '1 mes'), (90, '3 meses')]
    tmin, tmax = 0.25, 120.0
    X = lambda t: x0 + (math.log(t) - math.log(tmin)) / (math.log(tmax) - math.log(tmin)) * w
    Y = lambda v: y0 + h - v * h
    for t, rot in marcas:
        g.linea(X(t), y0, X(t), y0 + h, GRILLA, 1)
        g.t(X(t), y0 + h + 14, rot, 9, TENUE)
    g.t(x0 + w / 2, y0 + h + 30, 'tiempo desde la lesión (escala logarítmica)', 9, TENUE)
    g.t(x0 - 8, y0 + 4, 'recuperado', 8.5, TENUE, 'end')
    g.t(x0 - 8, y0 + h, 'nada', 8.5, TENUE, 'end')
    series = [(1, VERDE, 2.4), (2, AZUL, 2.4), (3, ROJO, 2.4)]
    for col, color, w_ in series:
        g.poli([(X(r[0]), Y(r[col])) for r in d['comp']], color, w_)
    xl = x0 + w + 14
    g.t(xl, Y(0.97) + 4, 'Reposo', 10, VERDE, 'start', 700)
    g.t(xl, Y(0.97) + 17, 'se equilibra la actividad', 8.5, TENUE, 'start')
    g.t(xl, Y(0.97) + 29, 'de los dos núcleos: se apaga', 8.5, TENUE, 'start')
    g.t(xl, Y(0.97) + 41, 'el nistagmo y el vértigo', 8.5, TENUE, 'start')
    g.t(xl, Y(0.62), 'Función con el movimiento', 10, AZUL, 'start', 700)
    g.t(xl, Y(0.62) + 13, 'tarda más y pide práctica:', 8.5, TENUE, 'start')
    g.t(xl, Y(0.62) + 25, 'estrategias, sustitución,', 8.5, TENUE, 'start')
    g.t(xl, Y(0.62) + 37, 'ganancia del reflejo', 8.5, TENUE, 'start')
    g.t(xl, Y(0.18) - 14, 'Reflejo vestíbulo-ocular', 10, ROJO, 'start', 700)
    g.t(xl, Y(0.18) - 1, 'recupera solo una parte', 8.5, TENUE, 'start')
    g.t(xl, Y(0.18) + 11, 'de lo perdido', 8.5, TENUE, 'start')
    g.guardar('h19-compensacion.svg')


def vor_ejercicios():
    W, H = 760, 460
    g = Dib(W, H)
    g.t(14, 22, 'Por qué el movimiento de la cabeza enseña al reflejo', 12.5, TINTA, 'start', 700)
    # A: velocidades
    g.t(14, 46, 'A. Un giro de la cabeza (velocidad) y la respuesta del ojo', 10.5, TINTA, 'start', 700)
    paneles = [('Reflejo normal: el ojo compensa', 1.0), ('Reflejo disminuido: el ojo se queda corto', 0.5)]
    px, pw, ph, py = 30, 330, 120, 66
    for i, (tit, gan) in enumerate(paneles):
        x = px + i * (pw + 40)
        g.rect(x, py, pw, ph, '#faf9f6')
        g.linea(x, py + ph / 2, x + pw, py + ph / 2, GRILLA, 1, dash='3 3')
        g.t(x + pw / 2, py - 6, tit, 9.5, TINTA, 'middle', 600)
        n = 120
        cab = [(x + 10 + k / n * (pw - 20), py + ph / 2 + 40 * math.sin(2 * math.pi * 1.5 * k / n)) for k in range(n + 1)]
        ojo = [(x + 10 + k / n * (pw - 20), py + ph / 2 + 40 * gan * math.sin(2 * math.pi * 1.5 * k / n)) for k in range(n + 1)]
        if gan < 1:
            # el deslizamiento: la diferencia entre lo que giró la cabeza y lo que compensó el ojo
            g.o.append('<polygon points="' + ' '.join(f'{a:.1f},{b:.1f}' for a, b in cab + [(x2, y2) for x2, y2 in ojo[::-1]]) + '" fill="#c62f3a" fill-opacity="0.13" stroke="none"/>')
        g.poli(cab, TENUE, 1.6, dash='4 3')
        g.poli(ojo, AZUL, 2.2)
        if gan < 1:
            g.t(x + pw / 2, py + ph + 16, 'el área roja es el deslizamiento de la imagen en la retina', 8.5, ROJO)
        else:
            g.t(x + pw / 2, py + ph + 16, 'sin deslizamiento: la imagen queda quieta en la retina', 8.5, VERDE)
    g.t(px + 6, py + ph - 6, '- - lo que haría falta (contra la cabeza)', 8, TENUE, 'start')
    g.t(px + pw - 6, py + ph - 6, '— ojo', 8, AZUL, 'end')
    g.t(14, py + ph + 40, 'El deslizamiento es la señal de error que el cerebelo usa para recalibrar la ganancia del reflejo. Sin mover la cabeza no hay error, y sin error no hay adaptación.', 9, TENUE, 'start')
    # B: ejercicios vistos desde arriba
    yb = 250
    g.t(14, yb - 6, 'B. Los tres ejercicios, vistos desde arriba', 10.5, TINTA, 'start', 700)
    cols = [('x1', 'Blanco quieto, cabeza gira', 'el ojo debe ir contra la cabeza', 0),
            ('x2', 'Blanco y cabeza se mueven en sentido contrario', 'la imagen resbala el doble de rápido', 1),
            ('Sustitución', 'El ojo salta al blanco antes que la cabeza', 'no repara el reflejo: lo reemplaza', 2)]
    cw = 232
    for ci, (nom, l1, l2, tipo) in enumerate(cols):
        cx = 24 + ci * (cw + 10) + cw / 2
        cy = yb + 70
        g.rect(cx - cw / 2 + 4, yb + 6, cw - 8, 190, '#faf9f6')
        g.t(cx, yb + 26, nom, 11.5, ROJO if tipo != 2 else VERDE, 'middle', 700)
        # cabeza vista desde arriba: círculo con nariz hacia arriba
        g.circ(cx, cy + 40, 26, '#f3e6d8', TINTA, 1.4)
        g.poli([(cx - 5, cy + 16), (cx, cy + 8), (cx + 5, cy + 16)], TINTA, 1.4)
        # blanco
        by = cy - 28
        bx = cx
        if tipo == 0:
            g.circ(bx, by, 6, TINTA, TINTA)
            g.linea(cx - 40, cy + 18, cx + 40, cy + 18, 'none', 0)
            g.o.append(f'<path d="M{cx - 34},{cy + 4} A34,34 0 0 1 {cx + 34},{cy + 4}" fill="none" stroke="{AZUL}" stroke-width="1.8" marker-end="url(#pa)"/>')
            g.t(cx, cy - 4, 'cabeza', 8.5, AZUL)
        elif tipo == 1:
            g.circ(bx + 30, by, 6, TINTA, TINTA)
            g.linea(bx + 30, by + 10, bx + 52, by + 10, TINTA, 1.6, 'pt')
            g.t(bx + 62, by + 14, 'blanco', 8.5, TINTA, 'start')
            g.o.append(f'<path d="M{cx - 34},{cy + 4} A34,34 0 0 1 {cx + 34},{cy + 4}" fill="none" stroke="{AZUL}" stroke-width="1.8" marker-start="url(#pa)"/>')
            g.t(cx - 36, cy - 4, 'cabeza', 8.5, AZUL, 'end')
        else:
            g.circ(bx - 40, by, 6, TINTA, TINTA)
            g.circ(bx + 40, by, 6, TINTA, TINTA)
            g.linea(cx, cy + 40, bx - 40, by + 6, VERDE, 1.6, 'pv', dash='3 3')
            g.t(cx, cy - 4, 'primero el ojo, después la cabeza', 8.5, VERDE)
        g.t(cx, yb + 138 + 40, l1, 9, TINTA, 'middle', 600)
        g.t(cx, yb + 152 + 40, l2, 8.5, TENUE)
    g.guardar('h19-vor-ejercicios.svg')


if __name__ == '__main__':
    d = datos()
    mctsib(d)
    compensacion(d)
    vor_ejercicios()
