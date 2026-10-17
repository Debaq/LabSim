"""Fotos clínicas reales de malformaciones del oído externo (grupo MALFORMACIONES, tanda B).

Baja las figuras de acceso abierto (licencias en CREDITOS_IMG_MALFORMACIONES.md),
las recorta a la parte útil y las deja en esta carpeta como JPG (calidad 88,
lado mayor <= 1600 px). No quema rótulos: los rótulos van como globos del libro.

Uso:  python3 -I docs/libro/ilustraciones/hacer_img_malformaciones.py [carpeta_descargas]

Las descargas son datos: solo se abren con Pillow.
"""
import shutil
import sys
import urllib.request
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
DESCARGAS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/hacer_img_malformaciones')
UA = 'LabSimLibro/1.0 (libro de casos; contacto en el repositorio)'
PMC = 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/'

FUENTES = {
    # Truong MT et al. (2022), Front Surg, PMC9831057, CC BY 4.0
    'truong_f1.jpg': PMC + 'b86a/9831057/045866b0d9b0/fsurg-09-944223-g001.jpg',
    'truong_f2.jpg': PMC + 'b86a/9831057/14b860939bd4/fsurg-09-944223-g002.jpg',
    # CDC / Dr. James W. Hanson, dominio público (Wikimedia Commons, File:Ear-VACTERL.jpg)
    'ear_vacterl.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/5a/Ear-VACTERL.jpg',
}


def bajar(nombre):
    destino = DESCARGAS / nombre
    if not destino.exists():
        DESCARGAS.mkdir(parents=True, exist_ok=True)
        pedido = urllib.request.Request(FUENTES[nombre], headers={'User-Agent': UA})
        with urllib.request.urlopen(pedido, timeout=60) as r:
            destino.write_bytes(r.read())
    return destino


def guardar(im, nombre, lado=1600):
    if max(im.size) > lado:
        im.thumbnail((lado, lado), Image.LANCZOS)
    im.save(AQUI / nombre, 'JPEG', quality=88)
    print(nombre, im.size)


def lado_a_lado(paneles, sep=10):
    alto = min(p.height for p in paneles)
    paneles = [p.resize((round(p.width * alto / p.height), alto), Image.LANCZOS) for p in paneles]
    lienzo = Image.new('RGB', (sum(p.width for p in paneles) + sep * (len(paneles) - 1), alto), 'white')
    x = 0
    for p in paneles:
        lienzo.paste(p, (x, 0))
        x += p.width + sep
    return lienzo


def main():
    # B1: clasificación de la microtia, sin modificar (se copia tal cual).
    shutil.copyfile(bajar('truong_f1.jpg'), AQUI / 'b1-microtia-grados.jpg')
    print('b1-microtia-grados.jpg (copia sin modificar)')

    # Cap. 1: las dos fotos de la Fig. 2 (estenosis | atresia con microtia), sin las TC
    # ni las letras A/B del panel.
    f2 = Image.open(bajar('truong_f2.jpg')).convert('RGB')
    a = f2.crop((21, 0, 391, 310))
    b = f2.crop((21, 352, 391, 662))
    guardar(lado_a_lado([a, b]), 'cap01-foto-estenosis-atresia.jpg')

    # Cap. 1, caso de Ramón: recién nacido con microtia y atresia derechas, recortado a la oreja.
    rn = Image.open(bajar('ear_vacterl.jpg')).convert('RGB')
    guardar(rn.crop((320, 540, 1890, 2050)), 'cap01-foto-atresia-rn.jpg', lado=1200)


if __name__ == '__main__':
    main()
