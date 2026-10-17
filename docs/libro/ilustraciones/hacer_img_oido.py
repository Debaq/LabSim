"""Imágenes reales de TC y RM de oído y hueso temporal (grupo OIDO, tanda B).

Baja las figuras de artículos de acceso abierto (licencias en
CREDITOS_IMG_OIDO.md), las recorta al panel útil y las deja en esta carpeta
como JPG (calidad 88, lado mayor <= 1600 px). No quema rótulos: los rótulos
van como globos del libro.

Uso:  python3 -I docs/libro/ilustraciones/hacer_img_oido.py [carpeta_descargas]

Las descargas son datos: solo se abren con Pillow.
"""
import sys
import urllib.request
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
DESCARGAS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/hacer_img_oido')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
SPR = 'https://media.springernature.com/full/springer-static/image/art%3A'
PMC = 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/'

# nombre local -> URL (la versión más grande que se encontró)
FUENTES = {
    'PMC8520521_f3.jpg': SPR + '10.1007%2Fs11547-021-01387-z/MediaObjects/11547_2021_1387_Fig3_HTML.jpg',
    'PMC11913933_f1.png': SPR + '10.1007%2Fs00330-024-11021-x/MediaObjects/330_2024_11021_Fig1_HTML.png',
    'PMC9324637_f4.jpg': PMC + 'df46/9324637/9e9a9f5d79e7/jcm-11-03966-g004.jpg',
    'PMC11790716_f5.jpg': SPR + '10.1007%2Fs10334-024-01213-3/MediaObjects/10334_2024_1213_Fig5_HTML.jpg',
    'PMC4661245_f2.jpg': PMC + '45be/4661245/69dfcffc3412/ceo-8-320-g002.jpg',
    'PMC6775179_f2.png': SPR + '10.1186%2Fs13244-019-0782-y/MediaObjects/13244_2019_782_Fig2_HTML.png',
    'PMC10684447_f2.png': SPR + '10.1186%2Fs13244-023-01562-y/MediaObjects/13244_2023_1562_Fig2_HTML.png',
    'PMC10366931_f31.jpg': PMC + '70cf/10366931/30c72df78ba5/tomography-09-00097-g031.jpg',
    'PMC3999364_f12.jpg': PMC + 'f7dc/3999364/3b9086b4a296/13244_2014_313_Fig12_HTML.jpg',
    'PMC3292638_f11.jpg': PMC + '16d9/3292638/000a7307c838/13244_2011_126_Fig11_HTML.jpg',
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
    # B1: TC axial normal, cortes b y c de Feraco y cols. (rótulos originales en inglés)
    f = bajar('PMC8520521_f3.jpg')
    guardar(lado_a_lado([f.crop((893, 0, 1770, 686)), f.crop((0, 704, 877, 1393))]), 'b1-tc-axial.jpg')

    # B1: TC coronal normal del oído derecho, panel A de Touska y Connor
    f = bajar('PMC11913933_f1.png')
    guardar(f.crop((86, 4, 537, 393)), 'b1-tc-coronal.jpg')

    # B1: RM sagital oblicua del CAI, oído normal (paneles a y b) de Johansson y cols.
    f = bajar('PMC9324637_f4.jpg')
    guardar(f.crop((0, 0, 741, 277)), 'b1-rm-cai.jpg', gris=False)

    # B1: plano de corte, esquema de los 4 nervios y corte real a 7 T (panel c)
    f = bajar('PMC11790716_f5.jpg')
    guardar(f.crop((355, 1570, 1725, 1885)), 'b1-rm-cai-plano.jpg')

    # cap. 1: oído normal, estenosis y atresia (Qin y cols.)
    guardar(bajar('PMC4661245_f2.jpg'), 'cap01-tc-atresia.jpg')

    # cap. 3: escudo sano frente a escudo erosionado (Gulati y cols.)
    guardar(bajar('PMC6775179_f2.png'), 'cap03-tc-colesteatoma.jpg', gris=False)

    # cap. 4: fissula enferma frente a sana (Xu y cols.)
    guardar(bajar('PMC10684447_f2.png'), 'cap04-tc-fissula.jpg')

    # cap. 4: Paget de la base del cráneo, con los CAI estrechados (Battal y Zamora)
    f = bajar('PMC10366931_f31.jpg')
    guardar(f.crop((60, 250, 680, 720)), 'cap04-tc-paget.jpg')

    # cap. 15: doble anillo de la otoesclerosis coclear (Purohit y cols.)
    # se tapa el texto del equipo ("Spin 0 / Tilt -59") quemado sobre el panel a
    # con un parche del fondo de al lado (solo fondo, sin hueso)
    f = bajar('PMC3999364_f12.jpg')
    f.paste(f.crop((204, 6, 252, 36)), (252, 6))
    guardar(f, 'cap15-tc-otoesclerosis-coclear.jpg')

    # cap. 7: fractura que respeta y fractura que cruza la cápsula ótica (Trojanowska y cols.)
    guardar(bajar('PMC3292638_f11.jpg'), 'cap07-tc-fractura.jpg', gris=False)


if __name__ == '__main__':
    main()
