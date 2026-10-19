#!/usr/bin/env python3
"""Arma los montajes de maniobras de H19 a partir de capturas de labyrinthus3d.

Las capturas (1400x900, vista VPPB) las saca `hacer_h18_capturas.py` con
chromium sin cabeza. Uso:

    python3 hacer_h18_montajes.py <carpeta-de-capturas>

Cada recuadro: el paciente en la camilla (recorte de la escena), el canal
afectado en 2D con sus partículas y la flecha de "abajo" (recorte del panel de
arriba a la derecha) y, si se pide, el ojo con sus trazas."""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

AQUI = pathlib.Path(__file__).parent
CAJA_CANAL = (752, 62, 1012, 290)
CAJA_OJO = (10, 102, 290, 398)
TEXTO = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', 21)
FUENTE = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans-Bold.ttf', 26) if pathlib.Path('/usr/share/fonts/TTF/DejaVuSans-Bold.ttf').exists() else ImageFont.load_default()


def recuadro(captura, caja_cuerpo, numero, titulo, con_ojo=False, alto=330, dy=0):
    im = Image.open(captura).convert('RGB')
    cuerpo = im.crop(caja_cuerpo)
    k = alto / cuerpo.height
    cuerpo = cuerpo.resize((round(cuerpo.width * k), alto), Image.LANCZOS)
    cuerpo0 = cuerpo
    CW, CH = 312, 274
    ancho = cuerpo.width + CW + 10
    if con_ojo:
        alto = max(alto, CH + 4 + round(CW * 275 / 260))
        cuerpo = cuerpo.resize((round(cuerpo.width * alto / cuerpo.height), alto), Image.LANCZOS)
        ancho = cuerpo.width + CW + 10
    franja = 70
    t = Image.new('RGB', (ancho, alto + franja), (255, 255, 255))
    t.paste(cuerpo, (0, 0))
    canal = im.crop((CAJA_CANAL[0], CAJA_CANAL[1] + dy, CAJA_CANAL[2], CAJA_CANAL[3] + dy)).resize((CW, CH), Image.LANCZOS)
    t.paste(canal, (cuerpo.width + 10, 0))
    if con_ojo:
        t.paste(im.crop((CAJA_OJO[0], CAJA_OJO[1] + dy, CAJA_OJO[2], CAJA_OJO[3] + dy)).resize((CW, round(CW * 275 / 260)), Image.LANCZOS), (cuerpo.width + 10, canal.height + 4))
    d = ImageDraw.Draw(t)
    d.ellipse((6, 6, 44, 44), fill=(36, 16, 26))
    d.text((25, 25), str(numero), fill=(255, 255, 255), font=FUENTE, anchor='mm')
    # pie con el nombre de la postura, en dos líneas como mucho
    palabras, lineas, actual = titulo.split(), [], ''
    for p in palabras:
        prueba = (actual + ' ' + p).strip()
        if d.textlength(prueba, font=TEXTO) > ancho - 16 and actual:
            lineas.append(actual)
            actual = p
        else:
            actual = prueba
    lineas.append(actual)
    for i, l in enumerate(lineas[:2]):
        d.text((8, alto + 8 + i * 27), l, fill=(36, 16, 26), font=TEXTO)
    d.rectangle((0, 0, ancho - 1, alto + franja - 1), outline=(207, 204, 197))
    return t


def montaje(tiles, columnas, salida):
    w = max(t.width for t in tiles)
    h = max(t.height for t in tiles)
    filas = (len(tiles) + columnas - 1) // columnas
    m = Image.new('RGB', (columnas * w + (columnas - 1) * 8, filas * h + (filas - 1) * 8), (255, 255, 255))
    for i, t in enumerate(tiles):
        celda = Image.new('RGB', (w, h), (255, 255, 255))
        celda.paste(t, (0, 0))
        ImageDraw.Draw(celda).rectangle((0, 0, w - 1, h - 1), outline=(207, 204, 197))
        m.paste(celda, ((i % columnas) * (w + 8), (i // columnas) * (h + 8)))
    m.save(AQUI / salida, optimize=True)
    print(salida, m.size)


if __name__ == '__main__':
    carpeta = pathlib.Path(sys.argv[1])
    CUERPO = (320, 90, 740, 876)
    # Epley: los 6 pasos de la maniobra
    ep = ['Sentado, con la cabeza girada 45° hacia el lado afectado.',
          'Dix-Hallpike: acostado, cabeza colgando. Las partículas caen por el canal.',
          'La cabeza gira 90° hacia el lado contrario, siempre colgando.',
          'Otros 90°: de costado, con la cara hacia el suelo.',
          'Sentado, con la cabeza todavía girada.',
          'De frente: las partículas están en el utrículo.']
    montaje([recuadro(carpeta / f'ep_{i}_desde_la_cabecera.png', CUERPO, i + 1, ep[i]) for i in range(6)], 3, 'h19-epley.png')
    sm = ['Sentado, con la cabeza girada 45° hacia el lado sano.',
          'Rápido a decúbito lateral del lado afectado, cara hacia arriba.',
          'De golpe al decúbito del otro lado, con la cara hacia el suelo.',
          'Sentado, despacio.',
          'De frente: las partículas están en el utrículo.']
    montaje([recuadro(carpeta / f'sm_{i}_desde_la_cabecera.png', (300, 120, 750, 876), i + 1, sm[i]) for i in range(5)], 3, 'h19-semont.png')
    # Giro supino (canal lateral derecho, geotrópico) y Gufoni: la cabeza gira o el cuerpo se tumba
    la = [('rl', 1, 'desde_arriba', (590, 345, 840, 610), 38, 'Giro supino, visto desde arriba: cabeza girada 90° hacia el lado enfermo (derecho).'),
          ('rl', 3, 'desde_arriba', (590, 345, 840, 610), 38, 'Giro supino: cabeza girada 90° hacia el otro lado (izquierdo, sano).'),
          ('gf', 0, 'desde_la_cabecera', (296, 90, 740, 876), 0, 'Gufoni: sentado en el borde de la camilla.'),
          ('gf', 1, 'desde_la_cabecera', (296, 90, 740, 876), 0, 'Gufoni: de golpe de costado sobre el lado sano.'),
          ('gf', 2, 'desde_la_cabecera', (296, 90, 740, 876), 0, 'Gufoni: la cabeza gira 45° hacia el suelo.'),
          ('gf', 3, 'desde_la_cabecera', (296, 90, 740, 876), 0, 'Se sienta. Las partículas salieron del canal.')]
    montaje([recuadro(carpeta / f'{p}_{i}_{v}.png', c, k + 1, t, dy=dy) for k, (p, i, v, c, dy, t) in enumerate(la)], 2, 'h19-lateral.png')
    # Dix-Hallpike: sentado, en el pico del nistagmo (con el ojo y sus trazas) y al sentarse otra vez
    dh = [('dr_2.png', 'Sentado, con la cabeza girada 45° hacia el lado que se examina.', False),
          ('dp_1.png', 'Acostado y colgando, unos segundos después: el nistagmo está en su máximo.', True),
          ('dr_0.png', 'De nuevo sentado: el nistagmo se invierte y es más débil.', True)]
    montaje([recuadro(carpeta / f, (320, 130, 740, 876), k + 1, t, con_ojo=o, alto=420, dy=38) for k, (f, t, o) in enumerate(dh)], 3, 'h19-dix-hallpike.png')
