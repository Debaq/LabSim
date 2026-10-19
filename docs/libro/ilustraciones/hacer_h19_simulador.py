#!/usr/bin/env python3
"""Limpia los montajes de maniobras de H19 hechos con labyrinthus3d:

    h19-dix-hallpike.png, h19-lateral.png, h19-epley.png, h19-semont.png

Los montajes (hacer_h18_capturas.py + hacer_h18_montajes.py) ya recortan solo la escena, el canal
en 2D y el ojo, pero arrastraban dos rótulos de la interfaz del simulador: la etiqueta oscura con
el nombre del caso sobre el canal («canalitiasis del canal …») y la de «OJO DERECHO» sobre el ojo.
Este paso los borra: cada etiqueta se ubica por su color (gris oscuro #4a4a4c, en el canal) o por su
lugar (la del ojo, que es semitransparente) y se rellena fila por fila interpolando entre los
píxeles que la rodean; el halo claro de la etiqueta pasa al gris del fondo. Es idempotente: si ya no hay etiqueta, no cambia nada.

    python3 docs/libro/ilustraciones/hacer_h18_simulador.py

Si se rehacen las capturas con hacer_h18_montajes.py, hay que volver a correr este paso."""
import collections
import pathlib

import numpy as np
from PIL import Image

AQUI = pathlib.Path(__file__).parent
ETIQUETA = (74, 74, 76)
# La etiqueta «OJO DERECHO» en h19-dix-hallpike.png, relativa a la etiqueta del canal del mismo recuadro.
OJO_REL = (-5, 275, -166, 284)


def etiquetas(a):
    """Cajas (x0, y0, x1, y1) de las etiquetas grises del canal."""
    m = np.all(np.abs(a[..., :3] - np.array(ETIQUETA)) <= 3, axis=-1)
    alto, ancho = m.shape
    visto = np.zeros_like(m)
    cajas = []
    for y, x in zip(*np.nonzero(m)):
        if visto[y, x]:
            continue
        cola = collections.deque([(y, x)])
        visto[y, x] = True
        y0 = y1 = y
        x0 = x1 = x
        while cola:
            cy, cx = cola.popleft()
            y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < alto and 0 <= nx < ancho and m[ny, nx] and not visto[ny, nx]:
                        visto[ny, nx] = True
                        cola.append((ny, nx))
        if x1 - x0 > 80 and 10 <= y1 - y0 <= 30:
            cajas.append((int(x0), int(y0), int(x1), int(y1)))
    return cajas


def rellena(a, x0, y0, x1, y1, margen=4):
    """Rellena la caja interpolando, en cada fila, entre el píxel de la izquierda y el de la derecha."""
    x0, y0, x1, y1 = x0 - margen, y0 - margen, x1 + margen, y1 + margen
    izq, der = a[y0:y1 + 1, x0 - 1].astype(float), a[y0:y1 + 1, x1 + 1].astype(float)
    k = np.linspace(0, 1, x1 - x0 + 1)[None, :, None]
    a[y0:y1 + 1, x0:x1 + 1] = (izq[:, None, :] * (1 - k) + der[:, None, :] * k).round().astype(a.dtype)


def sombra(a, x0, y0, x1, y1, margen=9):
    """La etiqueta tiene un halo claro: los grises claros alrededor pasan al color del fondo del panel.
    No toca lo que tiene color (el canal) ni el texto oscuro (los rótulos del dibujo)."""
    x0, y0, x1, y1 = x0 - margen, max(0, y0 - margen), x1 + margen, y1 + margen
    zona = a[y0:y1 + 1, x0:x1 + 1].astype(int)
    croma = zona.max(-1) - zona.min(-1)
    claro = (croma < 6) & (zona.min(-1) >= 200) & (zona.max(-1) <= 250)
    valores, cuentas = np.unique(zona[claro].reshape(-1, 3), axis=0, return_counts=True)
    if len(valores):
        zona[claro] = valores[cuentas.argmax()]
        a[y0:y1 + 1, x0:x1 + 1] = zona.astype(a.dtype)


def limpia(nombre, con_ojo=False):
    ruta = AQUI / nombre
    a = np.array(Image.open(ruta).convert('RGB'))
    cajas = etiquetas(a)
    for x0, y0, x1, y1 in cajas:
        if con_ojo:
            dx0, dy0, dx1, dy1 = OJO_REL
            # el primer recuadro (sentado) no tiene ojo
            if x0 > 600:
                rellena(a, x0 + dx0, y0 + dy0, x1 + dx1, y1 + dy1, margen=0)
        rellena(a, x0, y0, x1, y1)
        sombra(a, x0, y0, x1, y1)
    Image.fromarray(a).save(ruta, optimize=True)
    print(nombre, len(cajas), 'etiquetas')


if __name__ == '__main__':
    limpia('h19-dix-hallpike.png', con_ojo=True)
    for n in ('h19-lateral.png', 'h19-epley.png', 'h19-semont.png'):
        limpia(n)
