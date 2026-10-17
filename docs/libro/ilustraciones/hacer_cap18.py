#!/usr/bin/env python3
"""Ilustraciones del capítulo 18 (El ABR que engaña). Los trazos NO son de un paciente real:
salen del generador de LabSim (src/abr/ABR_generator.py, importado SOLO PARA LEER) con el
equipo mal puesto o con un artefacto activado, y se dibujan acá en SVG propio.

    cap18-promedio.svg    el mismo oído a 20 dB nHL con 250 a 4.000 barridos
    cap18-raiz.svg        el ruido residual cae con 1/raíz(N): teoría, no simulador
    cap18-estimulo.svg    artefacto de estímulo con fono supraaural; alternar y pinzar el tubo
    cap18-pam.svg         respuesta postauricular: onda tardía que no migra con la intensidad
    cap18-falsa-v.svg     falsa onda V: está en un subpromedio y no en el otro
    cap18-filtros.svg     filtros mal elegidos
    cap18-polaridad.svg   polaridad y ventana de registro

Los números rotulados (FSP, ruido residual) son del simulador y solo ilustran; los criterios
de la literatura se dicen en el texto del capítulo."""
import json
import pathlib
import sys

import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
import os
os.chdir(RAIZ)
sys.path.insert(0, str(RAIZ / 'src'))
from abr.ABR_generator import ABR_Curve  # noqa: E402

DEMO = json.loads((RAIZ / 'docs/manual/capturas/casos_demo.json').read_text(encoding='utf-8'))
TINTA, TENUE, GRILLA = '#24101a', '#8a8a90', '#e7e5e0'
AZUL, ROJO, VERDE = '#2a5d9f', '#c62f3a', '#21796c'
F = "font-family=\"'Plus Jakarta Sans', sans-serif\""
BASE_CS = {'stim': 'Click', 'pol': 'Alternada', 'rate': 21.1, 'filter_down': 3000,
           'filter_passhigh': 100, 'side': 'OD'}


def traza(caso, lado, nivel, n, cs=None, tech=None, pref=None, cap='R1', contra=False):
    """Una curva del generador. pref: cambios sobre el bloque ABR del caso."""
    p = json.loads(json.dumps(DEMO[str(caso)]['ABR'][lado]))
    p.update(pref or {})
    c = dict(BASE_CS, side=lado)
    c.update(cs or {})
    pac = {'edad': DEMO[str(caso)]['edad'], 'gender': DEMO[str(caso)]['gender']}
    t, y, _, _, _, m = ABR_Curve(nivel, c, p, 0, [0, n], True, patient=pac, technical=tech or {},
                                 capture_id=cap)
    return dict(t=np.asarray(t), y=np.asarray(y), a=np.asarray(m['sub_a']), b=np.asarray(m['sub_b']),
                fsp=m['fsp'], ruido=m['residual_noise_nv'], n=n)


def coma(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


class Lienzo:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, []

    def t(self, x, y, s, size=11, color=TINTA, anchor='middle', peso=400):
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" {F} font-size="{size}" fill="{color}" '
                      f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')

    def l(self, x1, y1, x2, y2, color=GRILLA, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                      f'stroke-width="{w}"{d}/>')

    def p(self, pts, color, w=2, op=1.0):
        s = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        self.o.append(f'<polyline points="{s}" fill="none" stroke="{color}" stroke-width="{w}" '
                      f'stroke-linejoin="round" stroke-linecap="round" opacity="{op}"/>')

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}"><rect width="{self.w}" height="{self.h}" fill="#fff"/>'
               + ''.join(self.o) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')


def filas(nombre, rows, ventana=12.0, escala_uv=1.0, alto=74, ancho=760, subs=True, titulo_pie=''):
    """rows: lista de dicts con la traza (t,y,a,b) + 'rot' (rótulo izq.), 'nota' (rótulo der.),
    'marcas' [(ms, texto, color)]. Todas con la misma escala de µV."""
    X0, X1 = 150, ancho - 150
    top = 30
    H = top + alto * len(rows) + 46
    L = Lienzo(ancho, H)
    px = lambda ms: X0 + ms / ventana * (X1 - X0)
    for ms in range(0, int(ventana) + 1, 2 if ventana <= 14 else 5):
        L.l(px(ms), top - 6, px(ms), H - 40)
        L.t(px(ms), H - 24, f'{ms}', 10, TENUE)
    L.t((X0 + X1) / 2, H - 8, 'Tiempo desde el estímulo (ms)', 10.5, TENUE)
    k = alto / (2.2 * escala_uv)          # px por µV
    for i, r in enumerate(rows):
        cy = top + alto * i + alto * 0.55
        L.l(X0, cy, X1, cy, '#d8d5cf', 0.8)
        m = r['t'] <= ventana + 1e-9
        t = r['t'][m]
        if subs and r.get('a') is not None and len(r['a']) == len(r['t']):
            L.p([(px(a), cy - v * k) for a, v in zip(t, r['a'][m])], AZUL, 1.0, 0.8)
            L.p([(px(a), cy - v * k) for a, v in zip(t, r['b'][m])], ROJO, 1.0, 0.8)
        L.p([(px(a), cy - v * k) for a, v in zip(t, r['y'][m])], TINTA, 2.0)
        L.t(X0 - 10, cy - 4, r['rot'], 11, TINTA, 'end', 600)
        if r.get('rot2'):
            L.t(X0 - 10, cy + 10, r['rot2'], 9.5, TENUE, 'end')
        L.t(X1 + 10, cy - 4, r.get('nota', ''), 10, TINTA, 'start', 600)
        if r.get('nota2'):
            L.t(X1 + 10, cy + 10, r['nota2'], 9.5, TENUE, 'start')
        for ms, tx, col in r.get('marcas', []):
            L.l(px(ms), cy - alto * 0.45, px(ms), cy + alto * 0.3, col, 1.2, '3 3')
            L.t(px(ms), cy - alto * 0.47, tx, 10, col, 'middle', 700)
    # escala de amplitud
    yb = H - 40
    L.l(30, yb, 30, yb - escala_uv * k, TINTA, 2)
    L.t(37, yb - escala_uv * k / 2 + 3, f'{coma(escala_uv)} µV', 10, TENUE, 'start')
    if subs:
        L.l(X0, 12, X0 + 22, 12, TINTA, 2)
        L.t(X0 + 28, 16, 'promedio', 10, TENUE, 'start')
        L.l(X0 + 90, 12, X0 + 112, 12, AZUL, 1.2)
        L.t(X0 + 118, 16, 'mitad A', 10, TENUE, 'start')
        L.l(X0 + 175, 12, X0 + 197, 12, ROJO, 1.2)
        L.t(X0 + 203, 16, 'mitad B', 10, TENUE, 'start')
    L.guardar(nombre)


def promedio():
    rows = []
    for n in (250, 500, 1000, 2000, 4000):
        r = traza(33, 'OD', 20, n)
        r.update(rot=f'{n:,}'.replace(',', '.') + ' barridos', rot2='20 dB nHL',
                 nota=f'FSP {coma(r["fsp"])}', nota2=f'ruido {r["ruido"]:.0f} nV')
        rows.append(r)
    return rows


def raiz():
    L = Lienzo(640, 330)
    X0, X1, Y0, Y1 = 70, 600, 270, 40
    px = lambda n: X0 + np.log2(n / 250) / np.log2(16) * (X1 - X0)
    py = lambda v: Y0 - v * (Y0 - Y1)
    for n in (250, 500, 1000, 2000, 4000):
        L.l(px(n), Y0, px(n), Y1)
        L.t(px(n), Y0 + 16, f'{n:,}'.replace(',', '.'), 10, TENUE)
    for v in (0, .25, .5, .75, 1):
        L.l(X0, py(v), X1, py(v))
        L.t(X0 - 8, py(v) + 4, f'{int(v * 100)} %', 10, TENUE, 'end')
    L.t((X0 + X1) / 2, Y0 + 36, 'Barridos promediados', 11, TENUE)
    L.o.append(f'<text transform="translate(18 {(Y0 + Y1) / 2}) rotate(-90)" {F} font-size="11" '
               f'fill="{TENUE}" text-anchor="middle">Ruido residual (% del de 250 barridos)</text>')
    ns = np.geomspace(250, 4000, 80)
    L.p([(px(n), py(np.sqrt(250 / n))) for n in ns], ROJO, 2.4)
    for n in (250, 1000, 4000):
        v = np.sqrt(250 / n)
        L.o.append(f'<circle cx="{px(n):.1f}" cy="{py(v):.1f}" r="4" fill="#fff" stroke="{ROJO}" stroke-width="2"/>')
        L.t(px(n) + (14 if n == 250 else 0), py(v) - 10, f'{int(round(v * 100))} %', 10, ROJO, 'middle', 600)
    L.t(px(1000) + 70, py(.5) + 4, '4 veces más barridos', 10.5, AZUL, 'start', 600)
    L.t(px(1000) + 70, py(.5) + 18, 'para la mitad del ruido', 10.5, AZUL, 'start', 600)
    L.guardar('cap18-raiz.svg')


def estimulo():
    pref = {}
    sup = {'transducer': 'TDH39_headphone'}
    rows = []
    for rot, rot2, cs, tech, nota in (
            ('Inserción', 'alternada', {}, {}, 'limpio'),
            ('Supraaural', 'condensación', {'pol': 'Condensación'}, sup, 'artefacto'),
            ('Supraaural', 'alternada', {}, sup, 'se cancela'),
            ('Inserción', 'cond. + tubo pinzado', {'pol': 'Condensación', 'clamp': True}, {}, 'sin respuesta')):
        r = traza(37, 'OD', 100, 2000, cs, tech, pref)
        r.update(rot=rot, rot2=rot2, nota=nota)
        rows.append(r)
    return rows


def pam():
    rows = []
    for nivel in (100, 90, 80, 70, 60):
        r = traza(36, 'OD', nivel, 2000, tech={'window_ms': 25.0}, pref={'pam': 0.4})
        r.update(rot=f'{nivel} dB nHL')
        rows.append(r)
    rows[0]['marcas'] = [(13.0, '13 ms', ROJO)]
    rows[1]['marcas'] = [(5.9, 'V', VERDE), (13.0, '13 ms', ROJO)]
    return rows


def falsa_v():
    fv = {'amp': 0.25, 'lat': 5.6, 'int_min': 0, 'int_max': 75, 'mitad': 'a'}
    rows = []
    for nivel in (70, 60, 50, 40):
        r = traza(42, 'OD', nivel, 2000, pref={'falsa_v': fv})
        r.update(rot=f'{nivel} dB nHL', nota=f'FSP {coma(r["fsp"])}', nota2=f'ruido {r["ruido"]:.0f} nV',
                 marcas=[(5.6, '5,6 ms', ROJO)])
        rows.append(r)
    return rows


def _fila(rot, rot2, nivel=80, cs=None, tech=None):
    r = traza(38, 'OI', nivel, 2000, cs, tech)
    r.update(rot=rot, rot2=rot2)
    return r


def filtros():
    return [_fila('Rutina', '100-3.000 Hz'),
            _fila('Pasa alto 300 Hz', '300-3.000 Hz', cs={'filter_passhigh': 300}),
            _fila('Pasa alto 30 Hz', '30-3.000 Hz', cs={'filter_passhigh': 30}),
            _fila('Pasa bajo 1.000 Hz', '100-1.000 Hz', cs={'filter_down': 1000})]


def polaridad():
    filas_ = [_fila('Alternada', '80 dB nHL'),
            _fila('Rarefacción', '80 dB nHL', cs={'pol': 'Rarefacción'}),
            _fila('Condensación', '80 dB nHL', cs={'pol': 'Condensación'}),
            _fila('Ventana de 12 ms', '50 dB nHL', nivel=50),
            _fila('Ventana de 6 ms', '50 dB nHL', nivel=50, tech={'window_ms': 6.0})]
    filas_[3]['marcas'] = [(6.7, 'V', VERDE)]
    return filas_


if __name__ == '__main__':
    filas('cap18-promedio.svg', promedio(), escala_uv=0.5)
    raiz()
    filas('cap18-estimulo.svg', estimulo(), escala_uv=1.0)
    filas('cap18-pam.svg', pam(), ventana=25.0, escala_uv=1.0)
    filas('cap18-falsa-v.svg', falsa_v(), escala_uv=0.5)
    filas('cap18-filtros.svg', filtros(), escala_uv=1.0)
    filas('cap18-polaridad.svg', polaridad(), escala_uv=1.0)
