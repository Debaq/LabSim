#!/usr/bin/env python3
"""Dibuja los esquemas propios del capítulo 32 (volver a caminar sin miedo):

    cap32-sustitucion.svg       qué pasa con el peso de cada sentido cuando falla uno, dos y se apaga la luz
    cap32-factores.svg          los dominios de una evaluación multifactorial y quién se ocupa de cada uno
    cap32-riesgo.svg            la estratificación del riesgo de caída de las Guías Mundiales 2022
    cap32-ortostatismo.svg      presión arterial acostado y de pie del caso 32.2 (cifras inventadas)
    cap32-mctsib-perfiles.svg   balanceo en las 4 condiciones del mCTSIB con cuatro perfiles (modelo de labyrinthus3d)

Son esquemas docentes, no datos de pacientes. Las trazas salen del modelo postural de labyrinthus3d
(hacer_cap32.mjs, solo lectura): sus constantes son órdenes de magnitud para enseñar, no valores
normativos, y por eso los ejes de balanceo no llevan cifras. La estratificación sale de Montero-Odasso
y cols. (2022); la presión de pie, de los criterios de Freeman y cols. (2011). Imprime en la salida
estándar las posiciones (en %) que se usan para los globos.
    python3 docs/libro/ilustraciones/hacer_cap32.py"""
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
        s = s.replace('&', '&amp;')
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
        self.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circ(self, x, y, r, fill='none', stroke=TINTA, sw=1.2):
        self.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def guardar(self, nombre):
        defs = ''.join(f'<marker id="{i}" markerWidth="8" markerHeight="8" refX="6" refY="4" markerUnits="userSpaceOnUse" orient="auto">'
                       f'<path d="M0,0 L8,4 L0,8 z" fill="{c}"/></marker>' for i, c in (('pr', ROJO), ('pa', AZUL), ('pt', TINTA), ('pv', VERDE), ('pg', TENUE)))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}"><defs>{defs}</defs>'
               + ''.join(self.o) + '</svg>')
        (AQUI / nombre).write_text(svg, encoding='utf-8')
        print(nombre, f'({self.w}x{self.h})')


def lineas(g, x, y, textos, size=9, color=TINTA, paso=12, anchor='middle', peso=400):
    for k, s in enumerate(textos):
        g.t(x, y + k * paso, s, size, color, anchor, peso)


# ------------------------------------------------------------------ sustitución --
def sustitucion():
    W, H = 760, 330
    g = Dib(W, H)
    g.t(14, 22, 'Cuando un sentido falla, el cerebro carga los otros', 12.5, TINTA, 'start', 700)
    g.t(14, 38, 'La altura de cada barra es cuánto se apoya el equilibrio en ese sentido.', 8.5, TENUE, 'start')
    sentidos = [('Vista', AZUL), ('Pies y piernas', VERDE), ('Vestíbulo', NARANJA)]
    paneles = [
        ('Todo funciona', [0.55, 1.0, 0.6], [True, True, True], 'De pie en terreno firme, con luz:', 'los pies mandan y los demás confirman.', VERDE),
        ('Falla uno (neuropatía)', [0.95, 0.12, 0.95], [True, False, True], 'Los otros dos suben su peso:', 'se compensa, con menos margen.', NARANJA),
        ('Fallan dos (y neuropatía)', [1.0, 0.12, 0.12], [True, False, False], 'Queda solo la vista:', 'si cierra los ojos o falta luz, no hay otro.', NARANJA),
        ('Y se apaga la luz', [0.12, 0.12, 0.12], [False, False, False], 'No queda ningún sentido confiable:', 'el baño de noche, el pasto, la espuma.', ROJO),
    ]
    cw, gap, x0, y0, ph = 168, 16, 14, 64, 150
    for k, (tit, alt, ok, l1, l2, col) in enumerate(paneles):
        x = x0 + k * (cw + gap)
        g.rect(x, y0, cw, ph + 78, '#faf9f6', GRILLA)
        g.t(x + cw / 2, y0 + 16, tit, 10, col, 'middle', 700)
        base = y0 + ph + 4
        g.linea(x + 14, base, x + cw - 14, base, TENUE, 1)
        for j, ((nom, c), a, v) in enumerate(zip(sentidos, alt, ok)):
            bx = x + 26 + j * 46
            h = a * (ph - 52)
            g.rect(bx, base - h, 30, h, c if v else '#d8d6d0', 'none', 0, 2)
            if not v:
                g.linea(bx - 3, base - h - 14, bx + 33, base - h - 2, ROJO, 2)
                g.linea(bx - 3, base - h - 2, bx + 33, base - h - 14, ROJO, 2)
        for j, (nom, c) in enumerate(sentidos):
            bx = x + 26 + j * 46 + 15
            for m, s in enumerate(nom.split(' y ') if ' y ' in nom else [nom]):
                g.t(bx, base + 12 + 10 * m, s if m == 0 and ' y ' not in nom else (s + ' y' if m == 0 else s), 7.5, TINTA)
        lineas(g, x + cw / 2, y0 + ph + 52, [l1, l2], 8.3, TINTA, 11)
    g.t(W / 2, H - 10, 'Cómo se reparte el peso de cada entrada se explica en H20 (→ Fundamento); la anatomía de cada vía, en las Bases.', 8.5, TENUE)
    g.guardar('cap32-sustitucion.svg')


# --------------------------------------------------------------------- factores --
def factores():
    W, H = 760, 470
    g = Dib(W, H)
    g.t(14, 22, 'Una caída casi nunca tiene una sola causa', 12.5, TINTA, 'start', 700)
    g.t(14, 38, 'Dominios de la evaluación multifactorial (Guías Mundiales 2022). En azul, lo que mide quien evalúa la audición y el equilibrio; '
        'en naranja, lo que se pregunta, se mide a pie de cama o se deriva.', 8.2, TENUE, 'start')
    izq = [('Audición', 'audiograma, discriminación (→ cap. 5)', AZUL),
           ('Vestíbulo', 'VPPB, hipofunción (→ cap. 22, 24)', AZUL),
           ('Equilibrio y marcha', 'TUG, DGI, mCTSIB (→ H20)', AZUL),
           ('Miedo a caer', 'ABC o FES-I', AZUL),
           ('Presión de pie', 'acostado y de pie; se deriva', NARANJA),
           ('Fármacos', 'revisión por quien receta', NARANJA)]
    der = [('Vista', 'agudeza, anteojos, cataratas', NARANJA),
           ('Nervios y pies', 'neuropatía, calzado, dolor', NARANJA),
           ('Músculo y fragilidad', 'fuerza, peso, levantarse', NARANJA),
           ('Cognición y ánimo', 'atención, depresión, delirio', NARANJA),
           ('Casa y calle', 'luz, alfombras, escaleras', NARANJA)]
    cx, cy = W / 2, 262
    g.rect(cx - 62, cy - 42, 124, 84, '#fff', TINTA, 1.6, 10)
    lineas(g, cx, cy - 8, ['La caída', 'y el mareo'], 12.5, TINTA, 18, 'middle', 700)
    bw, bh = 238, 52
    for lado, items, x in (('izq', izq, 14), ('der', der, W - 14 - bw)):
        n = len(items)
        for k, (tit, sub, col) in enumerate(items):
            y = 62 + k * (bh + 10) + (0 if lado == 'izq' else 28)
            g.rect(x, y, bw, bh, '#faf9f6', col, 1.6, 8)
            g.rect(x, y, 6, bh, col, 'none', 0, 3)
            g.t(x + 18, y + 22, tit, 11, col, 'start', 700)
            g.t(x + 18, y + 40, sub, 9, TINTA, 'start')
            xa = x + bw if lado == 'izq' else x
            xb = cx - 62 if lado == 'izq' else cx + 62
            g.linea(xa, y + bh / 2, xb, cy + (y + bh / 2 - cy) * 0.18, col, 1.2, dash='4 3')
    g.t(W / 2, H - 12, 'Ningún dominio basta solo: se miran todos, se tratan los que se pueden tratar y se avisa a quien corresponde.', 9, TENUE)
    g.guardar('cap32-factores.svg')


# ----------------------------------------------------------------------- riesgo --
def caja(g, x, y, w, h, titulo, lineas_, col, fondo='#faf9f6'):
    g.rect(x, y, w, h, fondo, col, 1.6, 8)
    g.rect(x, y, w, 24, col, 'none', 0, 8)
    g.rect(x, y + 14, w, 10, col, 'none', 0, 0)
    g.t(x + w / 2, y + 17, titulo, 10.5, '#fff', 'middle', 700)
    for k, s in enumerate(lineas_):
        g.t(x + 10, y + 42 + k * 13, s, 8.6, TINTA, 'start')


def riesgo():
    W, H = 760, 440
    g = Dib(W, H)
    g.t(14, 22, 'Del relato al riesgo: cuándo hace falta una evaluación multifactorial', 12.5, TINTA, 'start', 700)
    g.t(14, 38, 'Resumen de la estratificación de las Guías Mundiales de Caídas (Montero-Odasso y cols., 2022). Es una guía de decisión, no un puntaje.',
        8.5, TENUE, 'start')
    # entrada
    g.rect(14, 56, 732, 74, '#fff', TINTA, 1.4, 8)
    g.t(24, 74, 'Se pregunta a todo mayor:', 9.5, TINTA, 'start', 700)
    g.t(24, 90, '¿Se cayó en el último año?  ¿Tiene mareo, pérdida del conocimiento o dificultad para caminar o mantener el equilibrio?', 8.8, TINTA, 'start')
    g.t(24, 104, 'Si hay más tiempo: ¿el miedo a caer le hace dejar actividades?  Si responde que sí a algo, se mide la marcha:', 8.8, TINTA, 'start')
    g.t(24, 118, 'velocidad de marcha (corte: menos de 0,8 m/s) o, como alternativa, el TUG (corte: más de 15 s).', 8.8, TINTA, 'start')
    bw, y = 236, 156
    caja(g, 14, y, bw, 168, 'Riesgo bajo', ['Sin caídas, o una sola caída', 'no grave, y sin problema de', 'marcha ni de equilibrio.', '',
                                              'Prevención: actividad física y', 'consejo. Se revisa cada año.'], VERDE)
    caja(g, 14 + bw + 12, y, bw, 168, 'Riesgo intermedio', ['Una sola caída no grave, pero', 'con problema de marcha o de', 'equilibrio.', '',
                                                               'Ejercicio de fuerza y de equilibrio', '(→ Otago, Tai Chi).'], NARANJA)
    caja(g, 14 + 2 * (bw + 12), y, bw, 168, 'Riesgo alto', ['Una caída y además alguna de estas:', '- lesión que requirió atención',
                                                              '- dos o más caídas en 12 meses', '- fragilidad conocida',
                                                              '- no poder levantarse en una hora', '- sospecha de pérdida del conocimiento'], ROJO)
    for k in range(2):
        xa = 14 + k * (bw + 12) + bw
        g.linea(xa + 1, y + 84, xa + 11, y + 84, TENUE, 1.4, 'pg')
    g.rect(14 + 2 * (bw + 12), y + 182, bw, 62, '#fff', ROJO, 1.4, 8)
    lineas(g, 14 + 2 * (bw + 12) + bw / 2, y + 202, ['Evaluación multifactorial', 'y plan con varios frentes', '(si hubo síncope, se estudia aparte)'], 9, ROJO, 13, 'middle', 700)
    g.linea(14 + 2 * (bw + 12) + bw / 2, y + 168, 14 + 2 * (bw + 12) + bw / 2, y + 182, ROJO, 1.6, 'pr')
    g.t(14, y + 204, 'Eva, Hugo e Isabel (casos 32.1 a 32.3)', 9.5, TINTA, 'start', 700)
    lineas(g, 14, y + 220, ['cumplen una o más de las condiciones de la caja roja:', 'por eso no basta con "entrenar el equilibrio".'], 9, TINTA, 13, 'start')
    g.t(W / 2, H - 10, 'La estratificación decide cuánto estudiar; el ejercicio de equilibrio le sirve a todos.', 9, TENUE)
    g.guardar('cap32-riesgo.svg')


# ------------------------------------------------------------------ ortostatismo --
def ortostatismo():
    W, H = 600, 300
    g = Dib(W, H)
    g.t(14, 22, 'Presión arterial acostado y de pie', 12, TINTA, 'start', 700)
    g.t(14, 37, 'Hugo, caso 32.2. Los cortes son los del consenso de hipotensión ortostática: baja de 20 en la sistólica o de 10 en la diastólica.', 8.3, TENUE, 'start')
    x0, y0, w, h = 70, 60, 440, 200
    g.rect(x0, y0, w, h, '#faf9f6', GRILLA)
    vmin, vmax = 50, 160
    Y = lambda v: y0 + h - (v - vmin) / (vmax - vmin) * h
    for v in range(60, 160, 20):
        g.linea(x0, Y(v), x0 + w, Y(v), GRILLA, 1)
        g.t(x0 - 8, Y(v) + 3, str(v), 8.5, TENUE, 'end')
    g.t(x0 - 40, y0 + h / 2, 'mmHg', 8.5, TENUE, 'middle')
    xs = [x0 + 60, x0 + 200, x0 + 380]
    nom = ['Acostado', 'De pie, 1 min', 'De pie, 3 min']
    sis = [142, 118, 112]
    dia = [84, 70, 68]
    for x, n in zip(xs, nom):
        g.t(x, y0 + h + 16, n, 9, TINTA)
        g.linea(x, y0 + h, x, y0 + h + 4, TENUE, 1)
    # umbrales respecto de la basal
    g.linea(xs[0], Y(sis[0] - 20), x0 + w - 20, Y(sis[0] - 20), ROJO, 1.1, dash='5 4')
    g.t(x0 + w - 22, Y(sis[0] - 20) - 4, 'corte sistólica (−20)', 8, ROJO, 'end')
    g.linea(xs[0], Y(dia[0] - 10), x0 + w - 20, Y(dia[0] - 10), AZUL, 1.1, dash='5 4')
    g.t(x0 + w - 22, Y(dia[0] - 10) - 4, 'corte diastólica (−10)', 8, AZUL, 'end')
    g.poli([(x, Y(v)) for x, v in zip(xs, sis)], ROJO, 2.2)
    g.poli([(x, Y(v)) for x, v in zip(xs, dia)], AZUL, 2.2)
    for x, a, b in zip(xs, sis, dia):
        g.circ(x, Y(a), 4, ROJO, ROJO)
        g.circ(x, Y(b), 4, AZUL, AZUL)
        g.t(x + 10, Y(a) - 7, str(a), 9.5, ROJO, 'start', 700)
        g.t(x + 10, Y(b) + 14, str(b), 9.5, AZUL, 'start', 700)
    g.t(x0 + 6, Y(150), 'sistólica', 9, ROJO, 'start', 700)
    g.t(x0 + 6, Y(61), 'diastólica', 9, AZUL, 'start', 700)
    g.t(W / 2, H - 8, 'Se mide acostado tras unos minutos de reposo y de pie al minuto y a los 3 minutos (→ Fisiología).', 8.3, TENUE)
    g.guardar('cap32-ortostatismo.svg')
    # posiciones de los globos (en % de la imagen)
    for x, a, n in zip(xs, sis, nom):
        print(f'  sis {n}: @{(x - 18) / W * 100:.1f},{Y(a) / H * 100:.1f}')
    print(f'  dia 3 min: @{(xs[2] - 18) / W * 100:.1f},{Y(dia[2]) / H * 100:.1f}')


# ------------------------------------------------------------------------ mCTSIB --
def mctsib():
    r = subprocess.run(['node', str(AQUI / 'hacer_cap32.mjs')], capture_output=True, text=True, check=True, env={**__import__('os').environ, 'SEMILLA': '3'})
    d = json.loads(r.stdout)
    W, H = 760, 686
    g = Dib(W, H)
    g.t(14, 22, 'Balanceo adelante-atrás en las cuatro condiciones del mCTSIB, con cuatro perfiles', 12.5, TINTA, 'start', 700)
    g.t(14, 38, 'Misma escala en todos los cuadros (20 s cada uno). Los sentidos que se quitan se suman hacia abajo.',
        8.5, TENUE, 'start')
    conds = [('firme_abiertos', 'Firme, ojos abiertos'), ('firme_cerrados', 'Firme, ojos cerrados'),
             ('espuma_abiertos', 'Espuma, ojos abiertos'), ('espuma_cerrados', 'Espuma, ojos cerrados')]
    filas = [('sano', 'Sin déficit (referencia)', AZUL),
             ('neuropatia', 'Neuropatía en las piernas', VERDE),
             ('vest_neuro', 'Neuropatía y pérdida vestibular bilateral (Isabel, caso 32.3)', NARANJA),
             ('multi', 'Lo anterior y además mala vista', ROJO)]
    x0, cw, gap, ph = 56, 160, 12, 104
    y0 = 96
    escala = ph / 2 / 8.0
    pos = {}
    for fi, (clave, titulo, color) in enumerate(filas):
        y = y0 + fi * (ph + 40)
        g.t(x0, y - 22, titulo, 10.5, color, 'start', 700)
        for ci, (cond, rot) in enumerate(conds):
            x = x0 + ci * (cw + gap)
            g.rect(x, y, cw, ph, '#faf9f6')
            g.linea(x, y + ph / 2, x + cw, y + ph / 2, GRILLA, 1, dash='3 3')
            if fi == 0:
                g.t(x + cw / 2, y - 8 - 0, rot, 9.5, TINTA, 'middle', 600)
            tr = d[clave][cond]
            pts = []
            for t, ap in tr['serie']:
                if tr['cayo'] is not None and t > tr['cayo'] + 0.3:
                    break
                pts.append((x + t / 20 * cw, y + ph / 2 - max(-8, min(8, ap)) * escala))
            g.poli(pts, color, 1.4)
            if tr['cayo'] is not None:
                xc, yc = pts[-1]
                g.t(xc + 6, yc + (14 if yc < y + ph - 24 else -6), 'se cae', 9, ROJO, 'start', 700)
            pos[(clave, cond)] = ((x + cw / 2) / W * 100, (y + ph / 2) / H * 100, bool(tr['cayo']))
        g.t(x0 - 6, y + 12, 'adelante', 8, TENUE, 'end')
        g.t(x0 - 6, y + ph - 4, 'atrás', 8, TENUE, 'end')
    g.t(W / 2 + 26, H - 10, 'tiempo (20 s por cuadro)', 8.5, TENUE)
    g.guardar('cap32-mctsib-perfiles.svg')
    for k, v in pos.items():
        if k[1] in ('espuma_cerrados', 'espuma_abiertos'):
            print(f'  {k[0]} {k[1]}: @{v[0]:.1f},{v[1]:.1f} {"CAE" if v[2] else ""}')


if __name__ == '__main__':
    sustitucion()
    factores()
    riesgo()
    ortostatismo()
    mctsib()
