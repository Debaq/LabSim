#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H16 (prueba calórica):

    h16-conveccion.svg  convección de la endolinfa en el canal lateral vertical (tibia y fría)
    h16-mariposa.svg    las cuatro irrigaciones en el tiempo (velocidad de la fase lenta), A: oído sano; B: hidrops izquierdo

El segundo sale de los números de labyrinthus3d/js/provocadas.js corrido sin pantalla con node
(solo se lee el repositorio). Es un esquema docente: las cifras del simulador son órdenes de
magnitud, no valores normativos; en el texto del libro no se usa ninguna de ellas.
    python3 docs/libro/ilustraciones/hacer_h16.py [ruta a labyrinthus3d]"""
import json
import math
import pathlib
import subprocess
import sys
import tempfile

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
OD, OI, TIBIA, FRIA = '#c62f3a', '#2b5fa8', '#c0571c', '#21796c'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
AQUI = pathlib.Path(__file__).parent
SIM = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.home() / 'Escritorio/Proyectos/labyrinthus3d'

MJS = r"""
const R = process.argv[2];
const { CASO, efectivas, funciones, describeNistagmo } = await import(R + '/js/patologia.js');
const { postura } = await import(R + '/js/vppb.js');
const { AGUA, CALORICA, calorica } = await import(R + '/js/provocadas.js');
const q = postura({ atras: 60 });
const serie = (oido, agua, fe) => {
  const out = [];
  for (let t = 0; t <= CALORICA.dura; t += 1) {
    const l = calorica(oido, AGUA[agua], t, q, fe).lenta;
    const d = describeNistagmo(l);
    const v = Math.hypot(...l);
    const b = d?.partes?.[0];
    out.push([t, b === 'derecha' ? v : b === 'izquierda' ? -v : 0]);
  }
  return out;
};
const casos = { sano: efectivas(funciones()), hidrops: efectivas(funciones(CASO.meniere.canales)) };
const res = { irriga: CALORICA.irriga };
for (const [n, fe] of Object.entries(casos)) for (const o of ['der', 'izq']) for (const a of ['tibia', 'fria']) (res[n] ??= {})[o + '_' + a] = serie(o, a, fe);
console.log(JSON.stringify(res));
"""


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def t(self, x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
                        f'text-anchor="{anchor}" font-weight="{peso}">{esc(s)}</text>')

    def l(self, x1, y1, x2, y2, color=TINTA, w=1, dash=None, extra=''):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                        f'stroke-width="{w}"{d}{extra}/>')

    def poli(self, pts, color, w=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" '
                        f'stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def raw(self, s):
        self.out.append(s)

    def guardar(self, nombre, defs=''):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
               f'height="{self.h}"><defs>{defs}</defs><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.out) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre)


def punta(id_, color):
    return (f'<marker id="{id_}" markerWidth="8" markerHeight="8" refX="5" refY="4" markerUnits="userSpaceOnUse" '
            f'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="{color}"/></marker>')


def conveccion():
    c = Lienzo(720, 330)
    defs = punta('pt', TIBIA) + punta('pf', FRIA)
    for k, (cx, titulo, col, cal) in enumerate([(190, 'A · Agua tibia: el lado del oído se calienta', TIBIA, 1),
                                                (530, 'B · Agua fría: el lado del oído se enfría', FRIA, -1)]):
        cy, r = 175, 80
        c.t(cx, 24, titulo, 12, TINTA, 'middle', 700)
        c.raw(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f4f2ee" stroke="{FUERTE}" stroke-width="16"/>')
        # el lado de afuera (hacia el oído) a la derecha; la ampolla arriba
        c.raw(f'<circle cx="{cx + r * math.cos(-1.15)}" cy="{cy + r * math.sin(-1.15)}" r="13" fill="{FUERTE}"/>')
        c.t(cx + 5, cy - r - 24, 'ampolla', 10, TENUE, 'middle')
        c.t(cx, cy + 4, 'canal lateral', 11, TENUE, 'middle')
        c.t(cx, cy + 20, 'de pie, visto de costado', 10, TENUE, 'middle')
        # zona de cambio de temperatura, pegada al oído
        c.raw(f'<ellipse cx="{cx + r}" cy="{cy}" rx="22" ry="44" fill="{col}" fill-opacity=".22"/>')
        c.t(cx + r + 40, cy + 56, 'pared del' if cal else 'pared del', 10, TENUE, 'start')
        c.t(cx + r + 40, cy + 69, 'oído medio', 10, TENUE, 'start')
        # flecha de la endolinfa: caliente sube por afuera, frío baja por afuera
        sube = cal > 0
        for ang0, ang1, rr, sentido in [(-55, 55, r + 0, 1), (55, -55, r - 0, 1)]:
            pass
        a0, a1 = (50, -50) if sube else (-50, 50)
        pts = [(cx + (r + 24) * math.cos(math.radians(a)), cy + (r + 24) * math.sin(math.radians(a)))
               for a in [a0 + (a1 - a0) * i / 20 for i in range(21)]]
        c.poli(pts, col, 3)
        x, y = pts[-1]
        px, py = pts[-2]
        c.raw(f'<path d="M{x:.1f},{y:.1f}" />')
        ang = math.atan2(y - py, x - px)
        c.raw(f'<polygon points="{x + 9 * math.cos(ang):.1f},{y + 9 * math.sin(ang):.1f} '
              f'{x + 6 * math.cos(ang + 2.1):.1f},{y + 6 * math.sin(ang + 2.1):.1f} '
              f'{x + 6 * math.cos(ang - 2.1):.1f},{y + 6 * math.sin(ang - 2.1):.1f}" fill="{col}"/>')
        c.t(cx + r + 60, cy - 10, 'sube' if sube else 'baja', 12, col, 'start', 700)
        c.t(cx, 300, 'la endolinfa va hacia la ampolla (ampulípeta): excita' if sube
            else 'la endolinfa se aleja de la ampolla (ampulífuga): inhibe', 11, col, 'middle', 700)
        c.t(cx, 316, 'el nistagmo bate hacia el oído irrigado' if sube else 'el nistagmo bate hacia el otro oído', 11, TINTA, 'middle')
    c.guardar('h16-conveccion.svg', defs)


def mariposa():
    with tempfile.TemporaryDirectory() as d:
        js = pathlib.Path(d) / 'curvas.mjs'
        js.write_text(MJS)
        datos = json.loads(subprocess.run(['node', str(js), str(SIM)], capture_output=True, text=True, check=True).stdout)
    c = Lienzo(720, 580)
    T, ymax = 180, 36
    for k, (clave, titulo, y0) in enumerate([('sano', 'A · Un oído sano: las cuatro irrigaciones', 18),
                                             ('hidrops', 'B · Hipofunción del lado izquierdo: el izquierdo responde menos', 300)]):
        x0, x1, h = 70, 690, 190
        top = y0 + 26
        yc = top + h / 2
        sx = lambda t: x0 + (x1 - x0) * t / T
        sy = lambda v: yc - v * (h / 2) / ymax
        c.t(x0 - 54, y0 + 8, titulo, 12, TINTA, 'start', 700)
        c.raw(f'<rect x="{sx(0):.1f}" y="{top}" width="{sx(datos["irriga"]) - sx(0):.1f}" height="{h}" fill="#f0eee9"/>')
        c.t((sx(0) + sx(datos['irriga'])) / 2, top + h / 2 - 24, 'agua (simulada)', 10, TENUE)
        for v in range(-30, 31, 10):
            c.l(x0, sy(v), x1, sy(v), GRILLA if v else TINTA, 1 if v else 1.4)
            c.t(x0 - 8, sy(v) + 4, str(abs(v)), 10, TENUE, 'end')
        for t in range(0, T + 1, 30):
            c.l(sx(t), top + h, sx(t), top + h + 4, TENUE)
            c.t(sx(t), top + h + 16, str(t), 10, TENUE)
        c.t((x0 + x1) / 2, top + h + 30, 'segundos desde que se abre el agua', 10, TENUE)
        c.raw(f'<text transform="translate(16,{yc}) rotate(-90)" {F} font-size="10" fill="{TENUE}" text-anchor="middle">'
              f'velocidad de la fase lenta (°/s)</text>')
        c.t(x0 + 4, sy(ymax) + 14, 'bate a la derecha', 10, TENUE, 'start')
        c.t(x0 + 4, sy(-ymax) - 2, 'bate a la izquierda', 10, TENUE, 'start')
        estilos = [('der_tibia', OD, None, 'OD tibia'), ('der_fria', OD, '6 4', 'OD fría'),
                   ('izq_tibia', OI, None, 'OI tibia'), ('izq_fria', OI, '6 4', 'OI fría')]
        for nombre, col, dash, rot in estilos:
            s = datos[clave][nombre]
            c.poli([(sx(t), sy(v)) for t, v in s], col, 2.2, dash)
            pico = max(s, key=lambda p: abs(p[1]))
            if clave == 'sano':
                rot = {'OD tibia': 'OD tibia = OI fría', 'OI fría': None, 'OD fría': 'OD fría = OI tibia', 'OI tibia': None}[rot]
            if rot:
                c.t(sx(pico[0]) + 4, sy(pico[1]) + (-6 if pico[1] > 0 else 14), rot, 10, TINTA, 'start', 700)
    c.t(70, 566, 'Línea continua: agua tibia. Punteada: agua fría. Rojo: oído derecho. Azul: oído izquierdo.', 10, TENUE, 'start')
    c.guardar('h16-mariposa.svg')


if __name__ == '__main__':
    conveccion()
    mariposa()
