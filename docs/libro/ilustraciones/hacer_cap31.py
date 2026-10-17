#!/usr/bin/env python3
"""Dibuja las ilustraciones del cap. 31 (compensar una neuritis):

    cap31-seguimiento-martin.svg, cap31-seguimiento-lucia.svg, cap31-seguimiento-ignacio.svg
        la "hoja de seguimiento" de cada caso: el impulso cefálico hacia el lado enfermo en tres
        visitas, con la ganancia y la sacada, y debajo la batería funcional y el DHI de cada visita
    cap31-trayectorias.svg   DHI y ganancia del vHIT de los tres casos, semana a semana
    cap31-balanceo-simulador.svg  balanceo lateral de pie, ojos cerrados sobre espuma, a 1, 7, 30 y 90 días
                                  de una pérdida unilateral (modelo de labyrinthus3d; hacer_cap31.mjs)

Las cifras de las fichas y de las trayectorias son las de los pacientes INVENTADOS del capítulo: no son
normas ni datos de pacientes reales. Las trazas del impulso salen del mismo generador sintético de
hacer_h17.py (cabeza gaussiana de 200 °/s, ojo = ganancia x cabeza + sacada). El balanceo sale del
simulador labyrinthus3d (del autor, solo lectura): sus constantes son órdenes de magnitud para enseñar.
Uso:  python3 hacer_cap31.py"""
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from hacer_h17 import (AVISO, CABEZA, FUERTE, GRILLA, OJO, OK, TENUE, TINTA, Ejes,  # noqa: E402
                       Lienzo, cabeza, ojo)

AQUI = pathlib.Path(__file__).parent
MORADO = '#6b4a9e'

# visita: (rótulo, ganancia del lado enfermo, sacada, batería)
CASOS = {
    'martin': dict(nombre='Martín', lado='derecho', color=CABEZA, visitas=[
        ('Semana 2', 0.45, 'manifiesta', dict(dhi=58, dva=3, mono='8 s', tug='10 s', dgi='9/12')),
        ('Semana 6', 0.62, 'encubierta', dict(dhi=30, dva=1, mono='24 s', tug='8 s', dgi='11/12')),
        ('Mes 3', 0.74, 'encubierta', dict(dhi=12, dva=0, mono='30 s', tug='7 s', dgi='12/12'))]),
    'lucia': dict(nombre='Lucía', lado='izquierdo', color=OJO, visitas=[
        ('Semana 5', 0.30, 'manifiesta', dict(dhi=74, dva=4, mono='2 s', tug='17 s', dgi='5/12')),
        ('Semana 9', 0.42, 'manifiesta', dict(dhi=52, dva=3, mono='6 s', tug='13 s', dgi='8/12')),
        ('Semana 17', 0.55, 'encubierta', dict(dhi=24, dva=1, mono='14 s', tug='10 s', dgi='10/12'))]),
    'ignacio': dict(nombre='Ignacio', lado='derecho', color=MORADO, visitas=[
        ('Semana 2', 0.50, 'manifiesta', dict(dhi=60, dva=3, mono='10 s', tug='10 s', dgi='9/12')),
        ('Semana 6', 0.78, 'encubierta', dict(dhi=46, dva=1, mono='30 s', tug='7 s', dgi='12/12')),
        ('Semana 10', 0.90, None, dict(dhi=52, dva=0, mono='30 s', tug='7 s', dgi='12/12'))]),
}
NOTA_SAC = {'manifiesta': 'sacada manifiesta', 'encubierta': 'sacada encubierta', None: 'sin sacadas'}


def coma(x):
    return f'{x:.2f}'.replace('.', ',')


def seguimiento(clave):
    d = CASOS[clave]
    c = Lienzo(740, 372)
    c.t(16, 20, f'{d["nombre"]} · impulso cefálico hacia el lado {d["lado"]} (el enfermo), en tres visitas', 10, TINTA, 'start', 700)
    c.t(16, 33, 'cabeza (azul) y ojo invertido (naranja), °/s; si el reflejo compensa, se superponen', 8, TENUE, 'start')
    for k, (rot, g, sac, b) in enumerate(d['visitas']):
        x = 22 + k * 240
        e = Ejes(c, x + 26, 70, 170, 96, 0, 400, 0, 420)
        e.marco([0, 200, 400], [0, 200, 400], 'ms' if k == 1 else '', None)
        e.curva(cabeza, CABEZA, 1.8, 400)
        e.curva(lambda t, g=g, s=sac: ojo(t, g, s), OJO, 1.8, 800)
        c.t(x + 26, 52, rot, 9.5, TINTA, 'start', 700)
        malo = g < 0.8
        c.t(x + 26, 63, f'ganancia {coma(g)}', 8.5, AVISO if malo else OK, 'start', 700)
        c.t(x + 26 + 170, 63, NOTA_SAC[sac], 8, AVISO if sac else OK, 'end', 700)
        # batería debajo
        y = 212
        filas = [('DHI', f'{b["dhi"]}'), ('DVA, líneas perdidas', f'{b["dva"]}'), ('Apoyo en un pie', b['mono']),
                 ('TUG', b['tug']), ('DGI de 4 ítems', b['dgi'])]
        c.out.append(f'<rect x="{x + 10}" y="{y - 14}" width="206" height="{len(filas) * 20 + 16}" rx="6" fill="#fff" stroke="{FUERTE}"/>')
        for i, (lab, val) in enumerate(filas):
            yy = y + 8 + i * 20
            c.t(x + 20, yy, lab, 8.5, TENUE, 'start')
            c.t(x + 206, yy, val, 9, TINTA, 'end', 700)
            if i < len(filas) - 1:
                c.l(x + 18, yy + 7, x + 208, yy + 7, GRILLA, 1)
    c.t(16, 360, 'Cifras de un paciente inventado para el libro. Trazas con el generador sintético de H17; la batería es la de H19.',
        7.5, TENUE, 'start')
    c.guardar(f'cap31-seguimiento-{clave}.svg')


def trayectorias():
    c = Lienzo(740, 330)
    c.t(16, 20, 'Los tres casos, semana a semana: lo que dice el paciente y lo que mide el vHIT', 10, TINTA, 'start', 700)
    semanas = (0, 18)

    def panel(px, py, w, h, titulo, y0, y1, yt, clave):
        e = Ejes(c, px, py, w, h, semanas[0], semanas[1], y0, y1)
        c.t(px, py - 12, titulo, 9.5, TINTA, 'start', 700)
        e.marco([0, 2, 6, 12, 18], yt, 'semanas desde el inicio del cuadro')
        for nom, d in CASOS.items():
            pts = []
            for (rot, g, sac, b) in d['visitas']:
                sem = int(rot.split()[-1]) if rot.startswith('Semana') else 13   # "Mes 3" = semana 13
                pts.append((e.X(sem), e.Y(b['dhi'] if clave == 'dhi' else g)))
            c.poli(pts, d['color'], 2)
            for (x, y) in pts:
                c.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{d["color"]}"/>')
            x, y = pts[-1]
            c.t(x + 6, y + 3, d['nombre'], 8.5, d['color'], 'start', 700)
        return e
    e = panel(48, 56, 300, 200, 'A · Discapacidad por mareo (DHI, 0 a 100)', 0, 100, [0, 30, 60, 100], 'dhi')
    for v, t in ((30, 'leve | moderado'), (60, 'moderado | grave')):
        c.l(e.px, e.Y(v), e.px + e.w, e.Y(v), FUERTE, 1, '4 3')
    e2 = panel(404, 56, 300, 200, 'B · Ganancia del vHIT, lado enfermo (0 a 1)', 0, 1, [0, 0.5, 1], 'gain')
    c.l(e2.px, e2.Y(1), e2.px + e2.w, e2.Y(1), FUERTE, 1, '4 3')
    c.t(e2.px + 4, e2.Y(1) + 11, 'reflejo normal: cerca de 1', 7.5, TENUE, 'start')
    c.t(16, 318, 'Cifras inventadas para el libro. Ignacio: la ganancia sigue subiendo y el DHI no.', 7.5, TENUE, 'start')
    c.guardar('cap31-trayectorias.svg')


def balanceo():
    r = subprocess.run(['node', str(AQUI / 'hacer_cap31.mjs')], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    c = Lienzo(740, 250)
    c.t(16, 20, 'Balanceo lateral de pie, ojos cerrados sobre espuma, tras perder un laberinto (modelo del simulador)', 10, TINTA, 'start', 700)
    c.t(16, 33, '20 s por cuadro, misma escala; el eje va de un lado al otro. Esquema de enseñanza: los días del simulador no son tiempos de un paciente.',
        7.5, TENUE, 'start')
    ph, cw, gap, x0, y0 = 150, 160, 12, 50, 62
    for k, (dia, rot) in enumerate((('1', '1 día'), ('7', '1 semana'), ('30', '1 mes'), ('90', '3 meses'))):
        x = x0 + k * (cw + gap)
        tr = d[dia]['espuma_cerrados']
        c.out.append(f'<rect x="{x}" y="{y0}" width="{cw}" height="{ph}" fill="#faf9f6" stroke="{GRILLA}"/>')
        c.l(x, y0 + ph / 2, x + cw, y0 + ph / 2, GRILLA, 1, '3 3')
        c.t(x + cw / 2, y0 - 8, rot, 9.5, TINTA, 'middle', 700)
        pts = []
        for t, lat, ap in tr['serie']:
            if tr['cayo'] is not None and t > tr['cayo'] + 0.3:
                break
            pts.append((x + t / 20 * cw, y0 + ph / 2 - max(-8, min(8, lat)) * ph / 16))
        c.poli(pts, AVISO if tr['cayo'] is not None else OK, 1.5)
        if tr['cayo'] is not None:
            xe, ye = pts[-1]
            c.t(xe + 5, ye + (14 if ye < y0 + ph - 24 else -6), 'se cae', 9, AVISO, 'start', 700)
        else:
            c.t(x + cw / 2, y0 + ph + 14, 'se sostiene', 9, OK, 'middle', 700)
    c.t(x0 - 6, y0 + 10, 'a un lado', 8, TENUE, 'end')
    c.t(x0 - 6, y0 + ph - 2, 'al otro', 8, TENUE, 'end')
    c.t(16, 238, 'Modelo de labyrinthus3d (software libre del autor): pérdida unilateral, sin otro déficit.', 7.5, TENUE, 'start')
    c.guardar('cap31-balanceo-simulador.svg')


if __name__ == '__main__':
    for k in CASOS:
        seguimiento(k)
    trayectorias()
    balanceo()
