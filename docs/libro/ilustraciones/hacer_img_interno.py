"""Imágenes reales de TC, RM y radiografía del oído interno (grupo INTERNO, tanda B).

Capítulos 10 (acueducto vestibular dilatado), 17 (CMV congénito y nervio
coclear), 26 (dehiscencia del conducto superior) y 29 (implante coclear e
implante de conducción ósea).

Baja las figuras de artículos de acceso abierto (licencias en
CREDITOS_IMG_INTERNO.md), las recorta al panel útil y las deja en esta carpeta
como JPG (calidad 88, lado mayor <= 1600 px). No quema rótulos: los rótulos
van como globos del libro.

Uso:  python3 -I docs/libro/ilustraciones/hacer_img_interno.py [carpeta_descargas]

Las descargas son datos: solo se abren con Pillow.
"""
import sys
import urllib.request
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
DESCARGAS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/hacer_img_interno')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
SPR = 'https://media.springernature.com/full/springer-static/image/art%3A'
PMC = 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/'
MDPI = 'https://mdpi-res.com/'

# nombre local -> URL (la versión más grande que se encontró)
FUENTES = {
    'PMC10066110_f4.png': SPR + '10.1007%2Fs00405-022-07681-4/MediaObjects/405_2022_7681_Fig4_HTML.png',
    'PMC12178317_f2.jpg': PMC + '86e2/12178317/42fe4250e1f8/cureus-0017-00000084477-i02.jpg',
    'PMC9406729_f7.png': MDPI + 'children/children-09-01210/article_deploy/html/images/children-09-01210-g007.png',
    'PMC9324637_f4.png': MDPI + 'jcm/jcm-11-03966/article_deploy/html/images/jcm-11-03966-g004.png',
    'PMC9443830_f3.jpg': PMC + '5551/9443830/62f753bf0e00/gr3.jpg',
    'PMC9420306_f2.jpg': PMC + 'b69a/9420306/591f42d14111/cureus-0014-00000027436-i02.jpg',
}


def bajar(nombre):
    destino = DESCARGAS / nombre
    if not destino.exists():
        DESCARGAS.mkdir(parents=True, exist_ok=True)
        pedido = urllib.request.Request(FUENTES[nombre], headers={'User-Agent': UA})
        with urllib.request.urlopen(pedido, timeout=60) as r:
            destino.write_bytes(r.read())
    return Image.open(destino).convert('RGB')


def lado_a_lado(paneles, sep=10):
    """Une paneles a la misma altura, separados por una franja blanca."""
    alto = min(p.height for p in paneles)
    paneles = [p.resize((round(p.width * alto / p.height), alto), Image.LANCZOS) for p in paneles]
    ancho = sum(p.width for p in paneles) + sep * (len(paneles) - 1)
    lienzo = Image.new('RGB', (ancho, alto), 'white')
    x = 0
    for p in paneles:
        lienzo.paste(p, (x, 0))
        x += p.width + sep
    return lienzo


def apilar(filas, sep=10):
    """Une filas al mismo ancho, una sobre otra."""
    ancho = min(f.width for f in filas)
    filas = [f.resize((ancho, round(f.height * ancho / f.width)), Image.LANCZOS) for f in filas]
    lienzo = Image.new('RGB', (ancho, sum(f.height for f in filas) + sep * (len(filas) - 1)), 'white')
    y = 0
    for f in filas:
        lienzo.paste(f, (0, y))
        y += f.height + sep
    return lienzo


def guardar(img, nombre, gris=True):
    if gris:
        img = img.convert('L')
    lado = max(img.size)
    if lado > 1600:
        f = 1600 / lado
        img = img.resize((round(img.width * f), round(img.height * f)), Image.LANCZOS)
    img.save(AQUI / nombre, quality=88, optimize=True)
    print(nombre, img.size)


def main():
    # Cap. 10: acueducto vestibular normal (a, b) frente a dilatado (g, h), Weiss y cols. 2023.
    # Se dejan en color las medidas originales (verde = punto medio, celeste = opérculo).
    f = bajar('PMC10066110_f4.png')
    control = [f.crop((84, 42, 560, 334)), f.crop((84, 340, 560, 632))]
    dilatado = [f.crop((1054, 42, 1530, 334)), f.crop((1054, 340, 1530, 632))]
    guardar(apilar([lado_a_lado([control[0], dilatado[0]]),
                    lado_a_lado([control[1], dilatado[1]])]), 'cap10-tc-acueducto.jpg', gris=False)

    # Cap. 26: dehiscencia del conducto superior derecho en Stenvers (B) y Pöschl (C)
    # frente al Pöschl izquierdo normal (D), Reddy y Pandey 2025. Flechas originales en amarillo.
    f = bajar('PMC12178317_f2.jpg')
    guardar(f.crop((0, 250, 750, 458)), 'cap26-tc-dehiscencia.jpg', gris=False)

    # Cap. 17: RM de un niño con CMV congénito y sordera posnatal, paneles E (FLAIR axial)
    # y F (T2 coronal), Lucignani y cols. 2022.
    f = bajar('PMC9406729_f7.png')
    guardar(lado_a_lado([f.crop((1200, 1200, 2356, 2416)), f.crop((2368, 1220, 4050, 2416))]),
            'cap17-rm-cmv.jpg')

    # Cap. 17: RM sagital oblicua del CAI del mismo lactante, oído que oye (b) y oído sordo
    # sin rama coclear (d), Johansson y cols. 2022. Recorte que deja fuera los rótulos en inglés.
    f = bajar('PMC9324637_f4.png')
    guardar(lado_a_lado([f.crop((2226, 300, 2796, 860)), f.crop((2316, 1580, 2886, 2140))]),
            'cap17-rm-nervio-coclear.jpg', gris=False)

    # Cap. 29: radiografía transorbitaria AP con el implante coclear, Molezini y cols. 2012.
    # Se corta la franja superior con la marca de la revista y se pasa a grises (el original es verdoso).
    f = bajar('PMC9443830_f3.jpg')
    guardar(f.crop((0, 24, 682, 588)), 'cap29-rx-implante-coclear.jpg')

    # Cap. 29: TC axial con el implante de una prótesis ósea anclada derecha, Mock y cols. 2022.
    f = bajar('PMC9420306_f2.jpg')
    guardar(f.crop((100, 60, 650, 680)), 'cap29-tc-baha.jpg')


if __name__ == '__main__':
    main()
