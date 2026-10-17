#!/usr/bin/env python3
"""Imágenes reales (RM y TC) de los capítulos 21, 25, 35 y 36: grupo CENTRAL.

Nada aquí es de un paciente del libro ni está hecho con IA. Hay dos tipos:

1. Cortes propios de un dataset abierto. ISLES 2022 (Hernandez Petzsche y
   cols., 2022; Zenodo 7153326, CC BY 4.0), caso sub-strokecase0157: infarto
   cerebeloso hemisférico. Se baja solo lo que hace falta del zip remoto con
   herramientas/imagenologia/rzip3.py, se lleva a convención radiológica
   (derecha del paciente a la izquierda de la imagen, anterior arriba), se
   recorta a la fosa posterior y se ponen la difusión (DWI b=1000) y el mapa
   ADC lado a lado. Sin rótulos quemados: los rótulos van como globos del libro.

2. Figuras de artículos de PMC con licencia CC BY o CC BY-NC (verificada en
   el <license> del XML de Europe PMC; ver CREDITOS_IMG_CENTRAL.md). Solo se
   recortan al panel útil y, en dos casos, se ponen dos paneles lado a lado.

Uso (necesita numpy, nibabel y Pillow; los datos bajados se tratan como datos):

    python -I docs/libro/ilustraciones/hacer_img_central.py [carpeta_cache]

La carpeta de caché (por defecto ~/.cache/labsim_libro_img_central) guarda lo
bajado para no repetir la descarga.
"""
import os
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image

AQUI = pathlib.Path(__file__).resolve().parent
RZIP3 = AQUI.parent / 'herramientas' / 'imagenologia' / 'rzip3.py'
CACHE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                     os.path.expanduser('~/.cache/labsim_libro_img_central'))
CACHE.mkdir(parents=True, exist_ok=True)

LADO_MAX = 1600
CALIDAD = 88

ISLES_ZIP = 'https://zenodo.org/api/records/7153326/files/ISLES-2022.zip/content'

# figuras de PMC: archivo en caché -> URL de la figura (versión de PMC)
PMC = {
    'pmc5307938_f1.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/6410/5307938/7e714eb0a04e/jos-2016-00857f1.jpg',
    'pmc8055326_f5.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/baee/8055326/191f385c5a10/NEUROLOGY2020122101FF5.jpg',
    'pmc10380265_f2.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/4c52/10380265/106db05c5fba/jcm-12-04626-g002.jpg',
    'pmc9422510_f2.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7371/9422510/c59c27e17c2e/gr2.jpg',
    'pmc11505379_f1.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/22e7/11505379/ab6f18ce7c22/JAA-17-1027-g0001.jpg',
}


def bajar(nombre, url):
    destino = CACHE / nombre
    if not destino.exists():
        subprocess.run(['curl', '-sSL', '--retry', '3', '-A', 'Mozilla/5.0',
                        '-o', str(destino), url], check=True)
    return Image.open(destino).convert('RGB')


def guardar(img, nombre, escala=1.0):
    """Escala (Lanczos) y guarda en JPG, con el lado mayor <= LADO_MAX."""
    if escala != 1.0:
        img = img.resize((round(img.width * escala), round(img.height * escala)),
                         Image.LANCZOS)
    if max(img.size) > LADO_MAX:
        f = LADO_MAX / max(img.size)
        img = img.resize((round(img.width * f), round(img.height * f)), Image.LANCZOS)
    img.save(AQUI / nombre, quality=CALIDAD, optimize=True)
    print(nombre, img.size)


def lado_a_lado(a, b, sep=8, fondo=255):
    """Dos paneles a la misma altura, separados por una franja."""
    if a.mode != b.mode:
        a, b = a.convert('RGB'), b.convert('RGB')
    if a.mode == 'RGB':
        fondo = (fondo,) * 3
    h = max(a.height, b.height)
    a = a.resize((round(a.width * h / a.height), h), Image.LANCZOS)
    b = b.resize((round(b.width * h / b.height), h), Image.LANCZOS)
    out = Image.new(a.mode, (a.width + sep + b.width, h), fondo)
    out.paste(a, (0, 0))
    out.paste(b, (a.width + sep, 0))
    return out


# ---------------------------------------------------------------- cap. 21 --
def isles_0157():
    import nibabel as nib
    d = CACHE / 'isles'
    d.mkdir(exist_ok=True)
    caso = 'sub-strokecase0157_ses-0001'
    if not all((d / f'{caso}_{k}.nii.gz').exists() for k in ('dwi', 'adc')):
        subprocess.run([sys.executable, '-I', str(RZIP3), ISLES_ZIP,
                        r'strokecase0157_ses-0001_(dwi|adc)\.nii\.gz$', str(d)], check=True)

    def vol(k):
        im = nib.as_closest_canonical(nib.load(d / f'{caso}_{k}.nii.gz'))  # RAS, 2 mm
        return np.asarray(im.dataobj).astype(np.float32)

    def corte(v, z):
        # filas: anterior arriba; columnas espejadas: convención radiológica
        return v[:, :, z].T[::-1, ::-1]

    dwi, adc = vol('dwi'), vol('adc')
    z = 12                       # corte con la lesión ancha y el IV ventrículo visible
    filas, cols = slice(61, 102), slice(20, 92)   # fosa posterior
    # ventanas: DWI 0-700 (parénquima ~250, lesión ~630); ADC 300-1500
    # (parénquima ~860, lesión ~500, LCR >2800 queda blanco)
    paneles = []
    for v, lo, hi in ((dwi, 0.0, 700.0), (adc, 300.0, 1500.0)):
        s = np.clip((corte(v, z)[filas, cols] - lo) / (hi - lo), 0, 1) * 255
        p = Image.fromarray(s.astype(np.uint8))
        paneles.append(p.resize((p.width * 9, p.height * 9), Image.LANCZOS))
    guardar(lado_a_lado(*paneles, sep=14, fondo=255), 'cap21-rm-infarto-cerebeloso.jpg')


def difusion_negativa():
    f = bajar('pmc5307938_f1.jpg', PMC['pmc5307938_f1.jpg'])
    # fila de arriba: A (difusión al día 1) y D (difusión 3 días después)
    a = f.crop((2, 2, 326, 141))
    dd = f.crop((358, 2, 683, 141))
    guardar(lado_a_lado(a, dd, sep=10), 'cap21-rm-difusion-negativa.jpg', escala=2.0)


# ---------------------------------------------------------------- cap. 25 --
def canvas():
    f = bajar('pmc8055326_f5.jpg', PMC['pmc8055326_f5.jpg'])
    guardar(f.crop((0, 308, 675, 519)), 'cap25-rm-canvas.jpg', escala=2.0)


def chiari():
    f = bajar('pmc10380265_f2.jpg', PMC['pmc10380265_f2.jpg'])
    guardar(f.crop((4, 4, 492, 505)), 'cap25-rm-chiari.jpg', escala=2.0)


# ---------------------------------------------------------------- cap. 35 --
def valvula():
    f = bajar('pmc9422510_f2.jpg', PMC['pmc9422510_f2.jpg'])
    ang = f.crop((0, 0, 361, 245))      # A: ángulo, antes de la cirugía
    area = f.crop((0, 258, 361, 505))   # C: área, antes de la cirugía
    guardar(lado_a_lado(ang, area, sep=10), 'cap35-tc-valvula.jpg', escala=1.6)


# ---------------------------------------------------------------- cap. 36 --
def polipos():
    f = bajar('pmc11505379_f1.jpg', PMC['pmc11505379_f1.jpg'])
    leve = f.crop((8, 262, 241, 527))       # A: coronal, opacificación leve
    total = f.crop((372, 1368, 731, 1651))  # C: coronal, opacificación total
    guardar(lado_a_lado(leve, total, sep=10), 'cap36-tc-polipos.jpg', escala=2.0)


if __name__ == '__main__':
    isles_0157()
    difusion_negativa()
    canvas()
    chiari()
    valvula()
    polipos()
