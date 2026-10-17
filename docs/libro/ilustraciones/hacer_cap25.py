#!/usr/bin/env python3
"""Dibuja las ilustraciones del capítulo 25 (Lo que viene de arriba):

    cap25-nistagmos-centrales.svg   downbeat, upbeat, evocado por la mirada con rebote, periódico alternante
                                    y pendular: la forma de cada uno
    cap25-caso1-canvas.svg          caso 25.1: mirada excéntrica con y sin luz, seguimiento
    cap25-caso2-ino.svg             caso 25.2: sacada a la derecha en los dos ojos (oftalmoplejía internuclear)
    cap25-caso3-chiari.svg          caso 25.3: canal vertical y canal horizontal de la misma VNG
    cap25-caso4-farmaco.svg         caso 25.4: mirada excéntrica, seguimiento y sacadas

Las trazas salen del modelo de labyrinthus3d (software propio del autor, Apache-2.0) corrido sin
pantalla por hacer_cap25.mjs: sus constantes son órdenes de magnitud docentes, no valores
normativos. Los números de las notas (ganancias, precisión, sacadas por segundo) son medidas
tomadas sobre esas mismas trazas; los de la ficha del paciente están en el texto del capítulo.
Uso:  python3 hacer_cap25.py"""
import json
import pathlib
import subprocess

from hacer_h15 import Eje, Lienzo, punta, pendiente_lenta, TINTA, TENUE, GRILLA, FUERTE, COCLEAR, RETRO, AVISO, AZUL  # noqa: F401

AQUI = pathlib.Path(__file__).parent


class Hoja(Lienzo):
    """Lienzo con párrafos que se parten solos al ancho de la hoja."""

    def par(self, x, y, texto, size=8.5, color=TINTA, peso=400):
        import textwrap
        for linea in textwrap.wrap(texto, int(980 / size)):
            self.t(x, y, linea, size, color, 'start', peso)
            y += size * 1.2 * 1.25
        return y


def datos():
    r = subprocess.run(['node', str(AQUI / 'hacer_cap25.mjs')], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def co(x, n=2):
    """Número con coma decimal."""
    return f'{x:.{n}f}'.replace('.', ',')


def ventana(pts, a, b, col=1, base=0.0):
    """Muestras (t, valor de la columna col) entre a y b, con t desde a."""
    return [(p[0] - base, p[col]) for p in pts if a <= p[0] <= b]


def panel(c, x, y, w, h, t0, t1, v0, v1, titulo, trazas, dv=None, dt=1, etiqueta_v=True, etiqueta_t=True, tlabel=None):
    e = Eje(c, x, y, w, h, t0, t1, v0, v1)
    c.t(x + w / 2, y - 7, titulo, 8.5, TINTA, 'middle', 600)
    e.marco(dv=dv, etiqueta_v=etiqueta_v, dt=dt, etiqueta_t=etiqueta_t)
    for pts, col, ancho, dash in trazas:
        e.traza(pts, col, ancho, dash)
    if tlabel:
        c.t(x + w / 2, y + h + 25, tlabel, 7.5, TENUE)
    return e


# ------------------------------------------------------------- 1. catálogo ---

def catalogo(d):
    c = Hoja(700, 592)
    c.t(14, 20, 'Cómo se ven los nistagmos centrales: posición del ojo en el tiempo', 10.5, TINTA, 'start', 700)
    # fila 1: vertical
    y = 58
    h = 100
    w = 250
    e = panel(c, 70, y, w, h, 0, 5, -6, 6, 'A · Hacia abajo (downbeat), mirando al frente',
              [(ventana(d['dbn']['con']['muestras'], 1, 6, 2, 1), FUERTE, 2.4, None),
               (ventana(d['dbn']['sin']['muestras'], 1, 6, 2, 1), AVISO, 1.4, None)], dv=5, dt=1)
    c.t(70 + w / 2, y + h + 25, 'segundos · arriba = el ojo sube', 7.5, TENUE)
    c.t(70 + w / 2, y + h + 38, 'la fase lenta sube, la rápida baja; con luz (gris ancho) casi no cambia', 7.5, AVISO, 'middle', 600)
    e = panel(c, 395, y, w, h, 0, 5, -6, 6, 'B · Hacia arriba (upbeat), mirando al frente',
              [(ventana(d['ubn']['con']['muestras'], 1, 6, 2, 1), FUERTE, 2.4, None),
               (ventana(d['ubn']['sin']['muestras'], 1, 6, 2, 1), AVISO, 1.4, None)], dv=5, dt=1, etiqueta_v=False)
    c.t(395 + w / 2, y + h + 25, 'segundos', 7.5, TENUE)
    c.t(395 + w / 2, y + h + 38, 'la fase lenta baja, la rápida sube', 7.5, AVISO, 'middle', 600)
    c.t(14, y + 48, 'grados', 8, TENUE, 'start')
    # fila 2: evocado por la mirada y rebote (la misma traza, dos tramos)
    y = 232
    g = d['gen_floculos']['muestras']
    panel(c, 70, y, w, h, 0, 5, 14, 24, 'C · Mirada 20° a la derecha: el ojo no se queda',
          [(ventana(g, 7, 12, 1, 7), AVISO, 1.5, None), ([(0, 20), (5, 20)], FUERTE, 1.2, '4 3')], dv=5, dt=1)
    c.t(70 + w / 2, y + h + 25, 'segundos desde que llegó · gris punteado: dónde se pidió', 7.5, TENUE)
    c.t(70 + w / 2, y + h + 38, 'se va hacia el centro y vuelve de un salto: bate hacia donde mira', 7.5, AVISO, 'middle', 600)
    panel(c, 395, y, w, h, 0, 8, -4, 4, 'D · Al volver al centro: rebote',
          [(ventana(g, 30.5, 38.5, 1, 30.5), AVISO, 1.5, None)], dv=2, dt=2)
    c.t(395 + w / 2, y + h + 25, 'segundos desde que volvió al centro', 7.5, TENUE)
    c.t(395 + w / 2, y + h + 38, 'bate hacia el lado contrario al que miraba, y se apaga solo', 7.5, AVISO, 'middle', 600)
    c.t(14, y + 48, 'grados', 8, TENUE, 'start')
    # fila 3: PAN y pendular
    y = 408
    pan = [(p[0] / 60.0, p[1]) for p in d['pan']]
    panel(c, 70, y, 340, h, 0, 7, -15, 15, 'E · Periódico alternante: velocidad de la fase lenta', [(pan, AVISO, 1.8, None)], dv=10, dt=1)
    c.t(70 + 170, y + h + 25, 'minutos · arriba = fase lenta hacia la derecha (°/s)', 7.5, TENUE)
    c.t(70 + 170, y + h + 38, 'invierte la dirección cada par de minutos, con luz y a oscuras', 7.5, AVISO, 'middle', 600)
    pen = [(p[0], p[1]) for p in d['pendular'] if p[0] <= 1.5]
    panel(c, 470, y, 180, h, 0, 1.5, -6, 6, 'F · Pendular adquirido (grados)', [(pen, AVISO, 1.5, None)], dv=5, dt=0.5, etiqueta_v=True)
    c.t(470 + 90, y + h + 25, 'segundos · sin fase rápida: va y viene', 7.5, TENUE)
    c.t(14, y + 48, '°/s', 8, TENUE, 'start')
    c.par(14, 572, 'Trazas del modelo de labyrinthus3d, sin luz salvo donde se indica (órdenes de magnitud docentes, no valores de referencia).', 8, TENUE)
    c.guardar('cap25-nistagmos-centrales.svg')


# ------------------------------------------------------------ 2. caso 25.1 ---

def caso_canvas(d):
    c = Hoja(700, 494)
    c.t(14, 20, 'Caso 25.1 · VNG: mirada excéntrica y seguimiento', 10.5, TINTA, 'start', 700)
    c.t(14, 42, 'A · Mirada excéntrica: cuánto se desvía el ojo de donde se pidió (a oscuras en rojo; con luz, gris ancho)', 9, TINTA, 'start', 700)
    m, ml = d['canvas']['mirada']['muestras'], d['canvas']['miradaLuz']['muestras']
    ven = [('Mirada 20° a la izquierda', 29.5, 33.5, -20), ('Mirada al frente', 1.0, 5.0, 0), ('Mirada 20° a la derecha', 8.0, 12.0, 20)]
    ancho = 196
    for i, (nom, a, b, obj) in enumerate(ven):
        x0 = 62 + i * (ancho + 20)
        e = Eje(c, x0, 66, ancho - 26, 100, 0, 4, -3, 3)
        c.t(x0 + (ancho - 26) / 2, 58, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=2 if i == 0 else None, etiqueta_v=(i == 0), dt=2, etiqueta_t=False)
        e.traza([(p[0] - a, p[1] - obj) for p in ml if a <= p[0] <= b], FUERTE, 2.6)
        e.traza([(p[0] - a, p[1] - obj) for p in m if a <= p[0] <= b], AVISO, 1.5)
        c.t(e.x + e.w / 2, e.y + e.h + 13, '4 s', 7.5, TENUE)
    c.t(14, 118, 'grados', 8, TENUE, 'start')
    # seguimiento
    c.t(14, 212, 'B · Seguimiento: el blanco (gris) va y viene a 0,4 Hz; el ojo derecho en color', 9, TINTA, 'start', 700)
    for i, (k, nom, col) in enumerate((('sano', 'Sin lesión', RETRO), ('canvas', 'Este paciente', AVISO))):
        x0 = 62 + i * 330
        e = Eje(c, x0, 248, 285, 110, 2.0, 7.0, -24, 24)
        c.t(x0 + 142, 240, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=20, etiqueta_v=(i == 0), dt=1, etiqueta_t=True)
        sub = d[k]['seguimiento']['sub']
        e.traza([(t, b) for t, b, _, _ in sub], FUERTE, 1.4)
        e.traza([(t, der) for t, _, der, _ in sub], col, 1.5)
        g = d[k]['seguimiento']['seg']['der']
        c.t(x0 + 142, 384, f"ganancia {co(g['mas']['ganancia'])} · sacadas de alcance {co(g['sacadas'], 1)} por segundo", 8, TINTA, 'middle')
    c.t(14, 300, 'grados', 8, TENUE, 'start')
    y = c.par(14, 418, 'En la mirada excéntrica la fase lenta se va hacia el centro y la rápida vuelve: es el nistagmo evocado por la mirada. Con luz sigue ahí. El seguimiento que no alcanza al blanco se arregla con sacadas pequeñas: seguimiento sacádico.')
    y = c.par(14, y + 8, 'Trazas del modelo de labyrinthus3d con los dos flóculos a medias y los dos laberintos perdidos (órdenes de magnitud docentes). El «sin lesión» que se dibuja no es una norma: cada equipo trae la suya.', 8, TENUE)
    c.guardar('cap25-caso1-canvas.svg')


# ------------------------------------------------------------ 3. caso 25.2 ---

def caso_ino(d):
    c = Hoja(700, 410)
    c.t(14, 20, 'Caso 25.2 · VNG: sacadas horizontales de 20° registradas en cada ojo', 10.5, TINTA, 'start', 700)
    sub = d['ino']['sacadas']['sub']
    m = d['ino']['sacadas']['saltos']
    for i, (nom, col, k, j) in enumerate((('A · Ojo derecho (el que registran muchos equipos)', AVISO, 'der', 2),
                                          ('B · Ojo izquierdo', AZUL, 'izq', 3))):
        x0 = 62 + i * 330
        e = Eje(c, x0, 66, 285, 130, 0.9, 5.9, -14, 14)
        c.t(x0 + 142, 56, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=10, etiqueta_v=(i == 0), dt=1, etiqueta_t=True)
        e.traza([(p[0], p[1]) for p in sub], FUERTE, 2.4)
        e.traza([(p[0], p[j]) for p in sub], col, 1.6)
        mas, menos = m[k]['mas'], m[k]['menos']
        c.t(x0 + 142, 222, 'segundos', 7.5, TENUE)
        c.t(x0 + 142, 238, f"hacia la derecha: precisión {co(mas['precision'])} · hacia la izquierda: {co(menos['precision'])}", 8, TINTA, 'middle')
    c.t(14, 130, 'grados', 8, TENUE, 'start')
    y = c.par(14, 285, 'El blanco (gris ancho) salta cada segundo entre 10° a la derecha y 10° a la izquierda. Hacia la derecha el ojo izquierdo es el que aduce: sale a tiempo (la misma latencia que el derecho) pero se queda a la mitad del camino. Hacia la izquierda, los dos llegan.')
    y = c.par(14, y, 'Si el equipo solo registra el ojo derecho, el examen sale normal.', 8.5, AVISO, 700)
    y = c.par(14, y + 12, 'Trazas del modelo de labyrinthus3d con el fascículo longitudinal medial izquierdo perdido (órdenes de magnitud docentes). El simulador deja corta la aducción, pero no la enlentece ni agrega el nistagmo del ojo que abduce, dos rasgos de la oftalmoplejía internuclear real.', 8, TENUE)
    c.guardar('cap25-caso2-ino.svg')


# ------------------------------------------------------------ 4. caso 25.3 ---

def caso_chiari(d):
    c = Hoja(700, 494)
    c.t(14, 20, 'Caso 25.3 · La misma VNG, dos canales: horizontal y vertical', 10.5, TINTA, 'start', 700)
    ch = d['chiari']
    # fila 1: horizontal y vertical al frente
    c.t(14, 40, 'A · Mirando al frente, a oscuras (en gris ancho, con luz)', 9, TINTA, 'start', 700)
    for i, (nom, col, k) in enumerate((('Canal horizontal', AZUL, 1), ('Canal vertical', AVISO, 2))):
        x0 = 62 + i * 330
        e = Eje(c, x0, 66, 285, 90, 0, 5, -5, 5)
        c.t(x0 + 142, 58, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=5, etiqueta_v=(i == 0), dt=1, etiqueta_t=True)
        e.traza(ventana(ch['fijando']['muestras'], 1, 6, k, 1), FUERTE, 2.6)
        e.traza(ventana(ch['primaria']['muestras'], 1, 6, k, 1), col, 1.5)
    spv0 = abs(pendiente_lenta([(p[0], p[2]) for p in ch['primaria']['muestras']], 1, 6))
    c.t(62 + 142, 190, 'sin nistagmo horizontal', 8, TINTA, 'middle')
    c.t(62 + 330 + 142, 190, f"fase lenta hacia arriba: {co(spv0, 1)} °/s", 8, TINTA, 'middle')
    c.t(14, 118, 'grados', 8, TENUE, 'start')
    # fila 2: vertical al mirar abajo y a la derecha
    c.t(14, 222, 'B · El canal vertical al mirar a otro lado: desviación del ojo respecto de donde se pidió', 9, TINTA, 'start', 700)
    for i, (nom, k, obj, col) in enumerate((('Mirada 20° abajo', 'abajo', -20, AVISO), ('Mirada 20° a la derecha', 'lado', 0, AVISO))):
        x0 = 62 + i * 330
        e = Eje(c, x0, 248, 285, 100, 0, 5, -6, 6)
        c.t(x0 + 142, 240, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=5, etiqueta_v=(i == 0), dt=1, etiqueta_t=True)
        pts = [(p[0] - 1, p[2] - obj) for p in ch[k]['muestras'] if 1 <= p[0] <= 6]
        e.traza(pts, col, 1.5)
        spv = abs(pendiente_lenta([(p[0], p[2]) for p in ch[k]['muestras']], 1, 6))
        c.t(x0 + 142, 374, f"fase lenta hacia arriba: {co(spv, 1)} °/s", 8, TINTA, 'middle')
    c.t(14, 300, 'grados', 8, TENUE, 'start')
    y = c.par(14, 408, 'Mirando al frente el canal horizontal está plano y el vertical bate hacia abajo. El nistagmo crece al mirar abajo y a un lado, y la luz casi no lo cambia.')
    y = c.par(14, y, 'Con un registro solo horizontal el paciente sale «sin nistagmo».', 8.5, AVISO, 700)
    y = c.par(14, y + 8, 'Trazas del modelo de labyrinthus3d con los dos flóculos a medias (órdenes de magnitud docentes). Las velocidades son medidas sobre estas trazas.', 8, TENUE)
    c.guardar('cap25-caso3-chiari.svg')


# ------------------------------------------------------------ 5. caso 25.4 ---

def caso_farmaco(d):
    c = Hoja(700, 494)
    c.t(14, 20, 'Caso 25.4 · VNG: mirada excéntrica, seguimiento y sacadas', 10.5, TINTA, 'start', 700)
    c.t(14, 42, 'A · Mirada excéntrica: cuánto se desvía el ojo de donde se pidió (a oscuras en rojo; con luz, gris ancho)', 9, TINTA, 'start', 700)
    m, ml = d['farmaco']['mirada']['muestras'], d['farmaco']['miradaLuz']['muestras']
    ven = [('Mirada 20° a la izquierda', 29.5, 33.5, -20), ('Mirada al frente', 1.0, 5.0, 0), ('Mirada 20° a la derecha', 8.0, 12.0, 20)]
    ancho = 196
    for i, (nom, a, b, obj) in enumerate(ven):
        x0 = 62 + i * (ancho + 20)
        e = Eje(c, x0, 66, ancho - 26, 100, 0, 4, -4, 4)
        c.t(x0 + (ancho - 26) / 2, 58, nom, 8.5, TINTA, 'middle', 600)
        e.marco(dv=2 if i == 0 else None, etiqueta_v=(i == 0), dt=2, etiqueta_t=False)
        e.traza([(p[0] - a, p[1] - obj) for p in ml if a <= p[0] <= b], FUERTE, 2.6)
        e.traza([(p[0] - a, p[1] - obj) for p in m if a <= p[0] <= b], AVISO, 1.5)
        c.t(e.x + e.w / 2, e.y + e.h + 13, '4 s', 7.5, TENUE)
    c.t(14, 118, 'grados', 8, TENUE, 'start')
    c.t(14, 212, 'B · Seguimiento a 0,4 Hz', 9, TINTA, 'start', 700)
    e = Eje(c, 62, 248, 285, 100, 2.0, 7.0, -24, 24)
    e.marco(dv=20, etiqueta_v=True, dt=1, etiqueta_t=True)
    sub = d['farmaco']['seguimiento']['sub']
    e.traza([(t, b) for t, b, _, _ in sub], FUERTE, 1.4)
    e.traza([(t, der) for t, _, der, _ in sub], AVISO, 1.5)
    g = d['farmaco']['seguimiento']['seg']['der']
    c.t(62 + 142, 384, f"ganancia {co(g['mas']['ganancia'])} · sacadas de alcance {co(g['sacadas'], 1)} por segundo", 8, TINTA, 'middle')
    c.t(14, 300, 'grados', 8, TENUE, 'start')
    c.t(392, 212, 'C · Sacadas de 20°', 9, TINTA, 'start', 700)
    e = Eje(c, 392, 248, 260, 100, 0.9, 4.9, -14, 14)
    e.marco(dv=10, etiqueta_v=False, dt=1, etiqueta_t=True)
    sub = d['farmaco']['sacadas']['sub']
    e.traza([(p[0], p[1]) for p in sub], FUERTE, 2.4)
    e.traza([(p[0], p[2]) for p in sub], AVISO, 1.5)
    s = d['farmaco']['sacadas']['saltos']['der']
    c.t(392 + 130, 384, f"latencia {s['mas']['latencia']:.0f} ms · precisión {co(s['mas']['precision'])}", 8, TINTA, 'middle')
    y = c.par(14, 418, 'La fase lenta vuelve hacia el centro a los dos lados y la rápida lo devuelve; con luz sigue. Seguimiento y sacadas salen casi sin cambios.')
    y = c.par(14, y + 8, 'Trazas del modelo de labyrinthus3d con el integrador de la mirada a medias, como con anticonvulsivantes o alcohol (órdenes de magnitud docentes). En fármacos reales el seguimiento y las sacadas también suelen alterarse (Remler y cols., 1990): el simulador solo modela el mantenimiento de la mirada.', 8, TENUE)
    c.guardar('cap25-caso4-farmaco.svg')


if __name__ == '__main__':
    d = datos()
    catalogo(d)
    caso_canvas(d)
    caso_ino(d)
    caso_chiari(d)
    caso_farmaco(d)
