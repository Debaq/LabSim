#!/usr/bin/env python3
"""Dibuja las ilustraciones de la herramienta H16 (examen vestibular y VNG):

    h16-vor-pushpull.svg     el reflejo vestíbulo-ocular en empuje-tracción y por qué una pérdida
                             unilateral produce un nistagmo que bate hacia el lado sano (esquema)
    h16-nistagmo-trazas.svg  nistagmo espontáneo de una neuritis aguda: sin fijación (lentes / VNG
                             sin luz) y con fijación, y cómo se mide la velocidad de la fase lenta
    h16-mirada.svg           ley de Alexander (periférico) y nistagmo evocado por la mirada (central)
    h16-oculomotor.svg       sacadas, seguimiento y optocinético: normal y lesiones
    h16-calibracion.svg      calibración de la VNG: por qué una mala ganancia falsea la velocidad (esquema)

Las trazas salen del modelo de labyrinthus3d (software propio del autor, Apache-2.0) corrido sin
pantalla por hacer_h15.mjs: su constantes son órdenes de magnitud docentes, no valores normativos.
Los esquemas no son datos de pacientes.  Uso:  python3 hacer_h15.py"""
import json
import math
import pathlib
import subprocess

TINTA, TENUE, GRILLA, FUERTE = '#24101a', '#8a8a90', '#e7e5e0', '#cfccc5'
COCLEAR, RETRO, AVISO, AZUL = '#c0571c', '#21796c', '#c62f3a', '#3b6fa8'
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

    def r(self, x, y, w, h, fill, stroke='none', sw=1, extra=''):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{sw}"{extra}/>')

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


def datos():
    r = subprocess.run(['node', str(AQUI / 'hacer_h15.mjs')], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


class Eje:
    """Un recuadro de ejes: tiempo (t0..t1) en x, valor (v0..v1) en y."""

    def __init__(self, c, x, y, w, h, t0, t1, v0, v1):
        self.c, self.x, self.y, self.w, self.h = c, x, y, w, h
        self.t0, self.t1, self.v0, self.v1 = t0, t1, v0, v1

    def X(self, t):
        return self.x + (t - self.t0) / (self.t1 - self.t0) * self.w

    def Y(self, v):
        return self.y + self.h - (v - self.v0) / (self.v1 - self.v0) * self.h

    def marco(self, cero=True, dv=None, etiqueta_v=True, dt=None, etiqueta_t=True, fmt='{:g}'):
        c = self.c
        c.l(self.x, self.y + self.h, self.x + self.w, self.y + self.h, FUERTE, 1)
        c.l(self.x, self.y, self.x, self.y + self.h, FUERTE, 1)
        if cero and self.v0 < 0 < self.v1:
            c.l(self.x, self.Y(0), self.x + self.w, self.Y(0), GRILLA, 1, '4 3')
        if dv:
            v = math.ceil(self.v0 / dv) * dv
            while v <= self.v1 + 1e-9:
                c.l(self.x - 3, self.Y(v), self.x, self.Y(v), FUERTE, 1)
                if etiqueta_v:
                    c.t(self.x - 6, self.Y(v) + 3, fmt.format(v), 7.5, TENUE, 'end')
                v += dv
        if dt:
            t = math.ceil(self.t0 / dt) * dt
            while t <= self.t1 + 1e-9:
                c.l(self.X(t), self.y + self.h, self.X(t), self.y + self.h + 3, FUERTE, 1)
                if etiqueta_t:
                    c.t(self.X(t), self.y + self.h + 13, fmt.format(t - self.t0 if False else t), 7.5, TENUE)
                t += dt

    def traza(self, pts, color, w=1.4, dash=None, t0=None, t1=None):
        a = self.t0 if t0 is None else t0
        b = self.t1 if t1 is None else t1
        seg = [(self.X(p[0]), self.Y(max(self.v0, min(self.v1, p[1])))) for p in pts if a <= p[0] <= b]
        self.c.poli(seg, color, w, dash)


# ---------------------------------------------------------------- 1. VOR ---

def vor():
    c = Lienzo(700, 330)
    c.t(14, 20, 'El reflejo vestíbulo-ocular compara dos lados: lo que importa es la diferencia', 10.5, TINTA, 'start', 700)
    paneles = [
        ('A · Cabeza quieta, sano', 'iguales: los ojos no se mueven', 1.0, 1.0, None),
        ('B · Cabeza gira a la derecha', 'el derecho sube, el izquierdo baja', 1.5, 0.5, 'izq'),
        ('C · Pérdida del lado izquierdo', 'el izquierdo cae a cero: la misma diferencia', 1.0, 0.0, 'izq'),
    ]
    ancho = 215
    reposo = 1.0
    for i, (tit, sub, d, iz, _) in enumerate(paneles):
        x0 = 20 + i * (ancho + 12)
        y0, alto = 62, 120
        c.t(x0, 46, tit, 9.5, TINTA, 'start', 700)
        c.l(x0, y0 + alto, x0 + ancho, y0 + alto, FUERTE, 1)
        yr = y0 + alto - reposo * 52
        c.l(x0, yr, x0 + ancho, yr, TENUE, 1, '4 3')
        c.t(x0 + ancho, yr - 4, 'reposo', 7.5, TENUE, 'end')
        for j, (lado, val, col) in enumerate((('Izquierdo', iz, AZUL), ('Derecho', d, COCLEAR))):
            bx = x0 + 28 + j * 98
            hh = val * 52
            if hh > 0.5:
                c.r(bx, y0 + alto - hh, 60, hh, col)
            c.t(bx + 30, y0 + alto + 13, lado, 8.5, TINTA, 'middle', 600)
        c.t(x0 + ancho / 2, y0 + alto + 28, 'canal horizontal: frecuencia de descarga', 7.5, TENUE)
        c.t(x0 + ancho / 2, y0 + alto + 46, sub, 8.5, TINTA, 'middle', 600)
    # efectos
    efectos = [('sin diferencia', 'el ojo se queda quieto', TENUE),
               ('diferencia a favor del derecho', 'el ojo se va a la izquierda (fase lenta)', COCLEAR),
               ('diferencia a favor del derecho', 'el mismo ojo a la izquierda, sin que la cabeza se mueva', AVISO)]
    for i, (a, b, col) in enumerate(efectos):
        x0 = 20 + i * (ancho + 12)
        c.l(x0 + ancho / 2, 250, x0 + ancho / 2, 266, col, 1.6, extra=' marker-end="url(#p-vor)"')
        c.t(x0 + ancho / 2, 281, a, 8.5, col, 'middle', 700)
    c.t(20 + (ancho + 12) * 2 + ancho / 2, 293, '→ lenta a la izquierda, rápida a la derecha', 8.5, AVISO, 'middle', 700)
    c.t(20 + (ancho + 12) + ancho / 2, 293, '(el ojo compensa el giro que cree sentir)', 8, TENUE, 'middle')
    c.t(20 + ancho / 2, 293, '(sin movimiento ocular)', 8, TENUE, 'middle')
    c.t(14, 322, 'En el reposo cada lado descarga y la diferencia entre los dos es nula.', 8, TENUE, 'start')
    c.guardar('h16-vor-pushpull.svg', punta('p-vor', AVISO))


# --------------------------------------------------------- 2. trazas ---

def pendiente_lenta(pts, a, b, tope=30):
    """Velocidad media de la fase lenta (°/s) en [a, b), sin las fases rápidas."""
    seg = [p for p in pts if a <= p[0] < b]
    v = [(seg[i][1] - seg[i - 1][1]) / (seg[i][0] - seg[i - 1][0]) for i in range(1, len(seg))]
    lentas = [x for x in v if abs(x) < tope]
    return sum(lentas) / len(lentas) if lentas else 0.0


def trazas(d):
    c = Lienzo(700, 430)
    c.t(14, 20, 'Nistagmo espontáneo de una neuritis del lado izquierdo (aguda): posición horizontal del ojo', 10.5, TINTA, 'start', 700)
    t0, t1 = 1.0, 6.0
    paneles = [('A · Sin fijación (lentes de Frenzel, VNG sin luz)', d['frenzel']['muestras'], COCLEAR, 40),
               ('B · Con fijación (con luz, mirando un punto)', d['fijando']['muestras'], RETRO, 225)]
    spv = {}
    ejes = {}
    for tit, pts, col, y0 in paneles:
        e = Eje(c, 70, y0 + 16, 540, 100, t0, t1, -2.5, 2.5)
        ejes[tit[0]] = e
        c.t(14, y0 + 6, tit, 9.5, TINTA, 'start', 700)
        e.marco(dv=2, dt=1)
        c.t(e.x + e.w / 2, e.y + e.h + 28, 'tiempo (s)', 8, TENUE)
        c.t(e.x - 34, e.y + e.h / 2, 'grados', 8, TENUE)
        e.traza(pts, col, 1.6)
        spv[tit[0]] = pendiente_lenta(pts, t0, t1)
    e = ejes['A']
    # fase rápida: sube en t ~ 1.3; fase lenta: baja entre 1.4 y 1.8
    c.l(e.X(1.55), e.Y(2.0), e.X(1.33), e.Y(0.6), AVISO, 1, extra=' marker-end="url(#p-nis)"')
    c.t(e.X(1.6), e.Y(2.0) + 3, 'fase rápida: hacia el lado sano (derecha)', 8.5, AVISO, 'start', 700)
    c.l(e.X(3.35), e.Y(-2.0), e.X(3.0), e.Y(-0.55), TINTA, 1, extra=' marker-end="url(#p-nis2)"')
    c.t(e.X(3.4), e.Y(-2.0) + 3, 'fase lenta: hacia el lado enfermo (izquierda); su pendiente es la VFL', 8.5, TINTA, 'start', 700)
    c.t(14, 206, f'En este trazo: {abs(spv["A"]):.1f} °/s sin fijar y {abs(spv["B"]):.1f} °/s fijando. Con la misma lesión, la fijación frena la fase lenta.', 8.5, TINTA, 'start', 600)
    c.t(14, 378, 'La velocidad de la fase lenta (VFL, °/s) es la pendiente de los tramos lentos, sin contar las fases rápidas.', 8.5, TINTA, 'start', 600)
    c.t(14, 393, 'En las lentes de Frenzel se estima a ojo; en la VNG, el programa la calcula tramo por tramo.', 8.5, TINTA, 'start')
    c.t(14, 418, 'Positivo = derecha del paciente.', 8, TENUE, 'start')
    c.guardar('h16-nistagmo-trazas.svg', punta('p-nis', AVISO) + punta('p-nis2', TINTA))
    return spv


# ---------------------------------------------------------- 3. mirada ---

def mirada(d):
    c = Lienzo(700, 470)
    c.t(14, 20, 'Qué hace el nistagmo al mirar a los lados: desviación del ojo respecto de la posición pedida', 10.5, TINTA, 'start', 700)
    ventanas = [('Mirada a la izquierda 20°', 17.0, 21.0, -20), ('Mirada al frente', 1.0, 5.0, 0), ('Mirada a la derecha 20°', 7.0, 11.0, 20)]
    filas = [('A · Periférico (neuritis izquierda): bate siempre a la derecha', 'alexander', COCLEAR),
             ('B · Central (integrador de la mirada): bate hacia donde se mira', 'evocado', AVISO)]
    ancho, gap, vmax = 196, 20, 6
    y = 40
    for tit, clave, col in filas:
        c.t(14, y + 6, tit, 9.5, TINTA, 'start', 700)
        for i, (nom, a, b, objetivo) in enumerate(ventanas):
            x0 = 62 + i * (ancho + gap)
            e = Eje(c, x0, y + 26, ancho - 26, 110, a, b, -vmax, vmax)
            c.t(x0 + (ancho - 26) / 2, y + 20, nom, 8.5, TINTA, 'middle', 600)
            e.marco(dv=3 if i == 0 else None, etiqueta_v=(i == 0), dt=2, etiqueta_t=False)
            pts = [(t, h - objetivo) for t, h, _ in d[clave]['muestras']]
            e.traza(pts, col, 1.5)
            c.t(e.x + e.w / 2, e.y + e.h + 13, '4 s', 7.5, TENUE)
        c.t(14, y + 85, 'grados', 8, TENUE, 'start')
        y += 175
    c.t(14, 395, 'Cómo se lee', 9.5, TINTA, 'start', 700)
    c.t(14, 412, 'A · el nistagmo periférico mantiene su dirección en las tres posiciones y se ve más mirando hacia su fase rápida (ley de Alexander).', 8.5, TINTA, 'start')
    c.t(14, 427, 'B · el central evocado por la mirada cambia de dirección: a la derecha el ojo vuelve a la izquierda y bate a la derecha; a la izquierda, al revés.', 8.5, TINTA, 'start')
    c.t(14, 442, 'Al frente no hay nistagmo. Positivo = derecha del paciente.', 8.5, TENUE, 'start')
    c.t(14, 460, 'Sin fijación.', 8, TENUE, 'start')
    c.guardar('h16-mirada.svg')


# -------------------------------------------------------- 4. oculomotor ---

def oculomotor(d):
    c = Lienzo(700, 470)
    c.t(14, 20, 'Pruebas oculomotoras: blanco (gris) y ojo derecho (color)', 10.5, TINTA, 'start', 700)
    # fila 1: sacadas
    c.t(14, 42, 'A · Sacadas: el blanco salta 20° cada segundo', 9.5, TINTA, 'start', 700)
    casos = [('sano', 'Normal', RETRO), ('vermis', 'Vermis dorsal', COCLEAR),
             ('fastigio', 'Núcleo fastigio izquierdo', COCLEAR), ('fef', 'Campo frontal y colículo izq.', COCLEAR)]
    ancho = 152
    for i, (k, nom, col) in enumerate(casos):
        x0 = 54 + i * (ancho + 10)
        e = Eje(c, x0, 66, ancho - 6, 96, 0.0, 4.2, -14, 14)
        c.t(x0 + (ancho - 6) / 2, 58, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=10, etiqueta_v=(i == 0), dt=1, etiqueta_t=True)
        sub = d['sacadas'][k]['sub']
        e.traza([(t, b) for t, b, _, _ in sub], FUERTE, 1.3)
        e.traza([(t, der) for t, _, der, _ in sub], col, 1.6)
        m = d['sacadas'][k]['saltos']['der']
        # texto de la medición
        if k == 'sano':
            tx = f"latencia {m['mas']['latencia']:.0f} ms · precisión {m['mas']['precision']:.2f}"
        elif k == 'vermis':
            tx = f"precisión {m['mas']['precision']:.2f} (corta a los dos lados)"
        elif k == 'fastigio':
            tx = f"izq. {m['menos']['precision']:.2f} · der. {m['mas']['precision']:.2f}"
        else:
            tx = f"a la derecha: latencia {m['mas']['latencia']:.0f} ms"
        c.t(x0 + (ancho - 6) / 2, 186, tx, 7.5, TINTA, 'middle')
    c.t(14, 98, 'grados', 8, TENUE, 'start')
    # fila 2: seguimiento y OKN
    c.t(14, 222, 'B · Seguimiento: el blanco va y viene a 0,4 Hz', 9.5, TINTA, 'start', 700)
    for i, (k, nom, col) in enumerate((('sano', 'Normal', RETRO), ('floculos', 'Los dos flóculos', COCLEAR))):
        x0 = 54 + i * 215
        e = Eje(c, x0, 258, 185, 100, 2.0, 7.0, -12, 12)
        c.t(x0 + 92, 250, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=10, etiqueta_v=(i == 0), dt=1, etiqueta_t=True)
        sub = d['seguimiento'][k]['sub']
        e.traza([(t, b) for t, b, _, _ in sub], FUERTE, 1.4)
        e.traza([(t, der) for t, _, der, _ in sub], col, 1.5)
        g = d['seguimiento'][k]['seg']['der']
        c.t(x0 + 92, 385, f"ganancia {g['mas']['ganancia']:.2f} · alcance {g['sacadas']:.1f}/s", 7.5, TINTA, 'middle')
    c.t(14, 290, 'grados', 8, TENUE, 'start')
    c.t(484, 222, 'C · Optocinético', 9.5, TINTA, 'start', 700)
    c.t(556, 250, 'barras a 40°/s', 8.5, TINTA, 'middle', 600)
    e = Eje(c, 484, 258, 170, 100, 2.0, 8.0, -30, 30)
    e.marco(dv=20, etiqueta_v=False, dt=2, etiqueta_t=True)
    okn = d['optocinetico']
    e.traza([(t, h) for t, h, _ in okn], RETRO, 1.4)
    c.t(569, 385, 'lenta con las barras, rápida contra', 7.5, TINTA, 'middle')
    c.t(14, 420, 'Sacada: latencia y precisión. Seguimiento: ganancia y sacadas de alcance. Optocinético: la fase lenta sigue a las barras.', 8.5, TINTA, 'start')
    c.t(14, 436, 'Medidas tomadas sobre cada traza.', 8.5, TENUE, 'start')
    c.guardar('h16-oculomotor.svg')


# --------------------------------------------------------- 5. calibración ---

def calibracion():
    c = Lienzo(700, 330)
    c.t(14, 20, 'Calibración: el ojo se convierte en grados con la ganancia que se mide, y esa ganancia escala todo lo demás', 10.5, TINTA, 'start', 700)
    blanco = []
    for k in range(0, 100):
        t = k * 0.1
        blanco.append((t, (10, 0, -10, 0)[int(t // 2.5) % 4]))
    def ojo(g):
        out, v = [], 0.0
        for t, b in blanco:
            v += (g * b - v) * 0.5
            out.append((t, v))
        return out
    for i, (nom, g, col, nota) in enumerate((('A · Bien calibrado', 1.0, RETRO, 'el ojo llega a donde está el blanco'),
                                              ('B · Ganancia de 0,7', 0.7, AVISO, 'todo se registra 30 % más chico'))):
        x0 = 56 + i * 330
        e = Eje(c, x0, 66, 270, 110, 0, 10, -14, 14)
        c.t(x0 - 42, 52, nom, 9.5, TINTA, 'start', 700)
        e.marco(dv=10, etiqueta_v=(i == 0), dt=2, etiqueta_t=True)
        e.traza(blanco, FUERTE, 2)
        e.traza(ojo(g), col, 1.6)
        c.t(x0 + 135, 210, nota, 8.5, col, 'middle', 700)
    c.t(14, 98, 'grados', 8, TENUE, 'start')
    c.t(14, 245, 'Para qué sirve este paso:', 9.5, TINTA, 'start', 700)
    for j, s in enumerate(('1. El paciente mira puntos de posición conocida y el programa asigna grados a lo que ve la cámara.',
                           '2. Si la ganancia sale baja, la velocidad de la fase lenta (°/s) sale baja en la misma proporción: un nistagmo puede quedar bajo el límite.',
                           '3. Se rehace si el paciente movió la cabeza, el párpado tapa la pupila o las gafas se corrieron.')):
        c.t(14, 262 + j * 15, s, 8.5, TINTA, 'start')
    c.t(14, 322, 'Blanco que salta 10° a cada lado.', 8, TENUE, 'start')
    c.guardar('h16-calibracion.svg')


if __name__ == '__main__':
    d = datos()
    vor()
    print(trazas(d))
    mirada(d)
    oculomotor(d)
    calibracion()
