"""Imágenes reales de RM para los caps. 9, 11, 12 y 23 (grupo RETRO).

Hace dos cosas:

1. Cortes propios de datasets abiertos (CC BY 4.0), sin rótulos ni contornos
   quemados: escala de grises, orientación radiológica (la derecha del
   paciente a la izquierda de la imagen), recortados a la región.
   - TCIA Vestibular-Schwannoma-SEG: VS-SEG-141 (schwannoma intracanalicular
     pequeño, CAI izquierdo) y VS-SEG-010 (grande, quístico, del ángulo
     derecho); T1 con gadolinio y T2 de alta resolución (CISS).
   - MSLesSeg, paciente P57 (test): placas de esclerosis múltiple en la
     protuberancia y periventriculares, FLAIR.
2. Figuras de artículos de PMC (CC BY / CC BY-NC), bajadas en alta y
   recortadas cuando hace falta.

Los datos se bajan a IMG_DATOS (por defecto ~/.cache/labsim-libro/imagenologia)
solo si faltan. Se tratan como datos: correr con el intérprete aislado y un
venv con numpy, pillow, pydicom y nibabel:

    IMG_DATOS=/ruta/datos /ruta/venv/bin/python -I docs/libro/ilustraciones/hacer_img_retro.py

Créditos y licencias en CREDITOS_IMG_RETRO.md (misma carpeta).
"""
import glob
import io
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import nibabel as nib
import numpy as np
import pydicom
from PIL import Image

AQUI = Path(__file__).resolve().parent
RZIP3 = AQUI.parent / 'herramientas' / 'imagenologia' / 'rzip3.py'
DATOS = Path(os.environ.get('IMG_DATOS', Path.home() / '.cache' / 'labsim-libro' / 'imagenologia'))
UA = {'User-Agent': 'Mozilla/5.0'}
CALIDAD = 88
BLANCO = 255
SEP = 8            # separación entre paneles, en píxeles

# ---------------------------------------------------------------- descargas

TCIA = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getImage?SeriesInstanceUID='
SERIES = {   # carpeta -> SeriesInstanceUID (Vestibular-Schwannoma-SEG, doi:10.7937/TCIA.9YTJ-5Q73)
    'VS-SEG-141_t1': '1.3.6.1.4.1.14519.5.2.1.310614644524521594494051190574955327182',
    'VS-SEG-141_t2': '1.3.6.1.4.1.14519.5.2.1.15051876378477273432527967382885690193',
    'VS-SEG-010_t1': '1.3.6.1.4.1.14519.5.2.1.280726347369327948783198395882782662228',
    'VS-SEG-010_t2': '1.3.6.1.4.1.14519.5.2.1.47368711747357463116341094276606315239',
}
MSLESSEG = 'https://ndownloader.figshare.com/files/52771814'   # MSLesSeg Dataset.zip (figshare 27919209)
PMC = {
    'hidrops_11098000_f2.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/7033/11098000/43b73b2b8631/10.1177_19160216241250350-fig2.jpg',
    'hidrops_9909016_f2.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/85c2/9909016/b84b7d83bcac/fneur-14-1105461-g0002.jpg',
    'epidermoide_3467374_f1.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/8153/3467374/f17705bb782b/jkns-52-148-g001.jpg',
    'aica_6417406_f2.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/43eb/6417406/73b973620dde/peerj-07-6582-g002.jpg',
    'infarto_11390645_f1.jpg': 'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/5496/11390645/f3696309f8d7/fneur-15-1448989-g001.jpg',
}


def bajar(url, destino):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        return r.read() if destino is None else Path(destino).write_bytes(r.read())


def serie_tcia(nombre):
    carpeta = DATOS / 'tcia' / nombre
    if not glob.glob(str(carpeta / '*.dcm')):
        carpeta.mkdir(parents=True, exist_ok=True)
        print('bajando', nombre)
        z = zipfile.ZipFile(io.BytesIO(bajar(TCIA + SERIES[nombre], None)))
        for i in z.infolist():
            if i.filename.lower().endswith('.dcm'):        # solo los DICOM, sin rutas
                (carpeta / Path(i.filename).name).write_bytes(z.read(i))
    return carpeta


def mslesseg(paciente):
    carpeta = DATOS / 'mslesseg'
    carpeta.mkdir(parents=True, exist_ok=True)
    if not (carpeta / f'{paciente}_FLAIR.nii.gz').exists():
        print('bajando MSLesSeg', paciente)
        subprocess.run([sys.executable, '-I', str(RZIP3), MSLESSEG,
                        rf'test/{paciente}/{paciente}_(FLAIR|MASK)\.nii\.gz$', str(carpeta)], check=True)
    return carpeta


def figura_pmc(nombre):
    archivo = DATOS / 'pmc' / nombre
    if not archivo.exists():
        archivo.parent.mkdir(parents=True, exist_ok=True)
        print('bajando', nombre)
        bajar(PMC[nombre], archivo)
    return Image.open(archivo).convert('RGB')


# ---------------------------------------------------------------- cortes

def ventana(a, bajo=0.5, alto=99.7, gamma=1.0):
    lo, hi = np.percentile(a[a > 0] if (a > 0).any() else a, [bajo, alto])
    a = np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1) ** gamma
    return Image.fromarray((a * 255).round().astype(np.uint8))


def corte_dcm(carpeta, z_mm, caja, mm_px=0.2, **vent):
    """Corte axial más cercano a z_mm (LPS), recortado a caja = (x0, x1, y0, y1)
    en mm LPS. Las columnas DICOM van de derecha a izquierda del paciente y las
    filas de adelante hacia atrás: ya es la orientación radiológica."""
    ds = [pydicom.dcmread(f) for f in glob.glob(str(carpeta / '*.dcm'))]
    d = min(ds, key=lambda d: abs(float(d.ImagePositionPatient[2]) - z_mm))
    o = np.array(d.ImagePositionPatient, float)
    ps = float(d.PixelSpacing[0])
    x0, x1, y0, y1 = caja
    c0, c1 = round((x0 - o[0]) / ps), round((x1 - o[0]) / ps)
    f0, f1 = round((y0 - o[1]) / ps), round((y1 - o[1]) / ps)
    sub = d.pixel_array.astype(np.float32)[f0:f1, c0:c1]
    tam = (round((x1 - x0) / mm_px), round((y1 - y0) / mm_px))
    sub = np.asarray(Image.fromarray(sub, 'F').resize(tam, Image.LANCZOS))
    return ventana(sub, **vent)


def corte_nii(archivo, z, caja=None, escala=4, **vent):
    """Corte axial z (vóxeles, tras pasar a RAS) en orientación radiológica:
    adelante arriba y la derecha del paciente a la izquierda de la imagen.
    caja = (c0, c1, f0, f1) en vóxeles de esa imagen ya orientada."""
    v = np.asarray(nib.as_closest_canonical(nib.load(str(archivo))).dataobj).astype(np.float32)
    sl = v[:, :, z].T[::-1, ::-1]
    if caja:
        c0, c1, f0, f1 = caja
        sl = sl[f0:f1, c0:c1]
    sl = np.ascontiguousarray(sl)
    tam = (sl.shape[1] * escala, sl.shape[0] * escala)
    sl = np.clip(np.asarray(Image.fromarray(sl, 'F').resize(tam, Image.LANCZOS)), 0, None)
    return ventana(sl, **vent)


def lamina(filas, sep=SEP):
    """filas = [[img, img], [img, img]]: cada fila se iguala en alto y la
    lámina se iguala en ancho (se escala la fila entera)."""
    hechas = []
    for fila in filas:
        h = max(im.height for im in fila)
        fila = [im.resize((round(im.width * h / im.height), h), Image.LANCZOS) for im in fila]
        ancho = sum(im.width for im in fila) + sep * (len(fila) - 1)
        lienzo = Image.new('L', (ancho, h), BLANCO)
        x = 0
        for im in fila:
            lienzo.paste(im.convert('L'), (x, 0))
            x += im.width + sep
        hechas.append(lienzo)
    w = max(f.width for f in hechas)
    hechas = [f.resize((w, round(f.height * w / f.width)), Image.LANCZOS) for f in hechas]
    total = Image.new('L', (w, sum(f.height for f in hechas) + sep * (len(hechas) - 1)), BLANCO)
    y = 0
    for f in hechas:
        total.paste(f, (0, y))
        y += f.height + sep
    return total


def guardar(im, nombre, lado_max=1600):
    if max(im.size) > lado_max:
        k = lado_max / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    im.convert('RGB' if im.mode not in ('L', 'RGB') else im.mode).save(AQUI / nombre, quality=CALIDAD, optimize=True)
    print(nombre, im.size)


# ---------------------------------------------------------------- figuras

def cap11_schwannoma():
    """Lámina 2 × 2: arriba el intracanalicular pequeño (VS-SEG-141, CAI
    izquierdo, con el CAI derecho sano en el mismo corte); abajo el grande
    del ángulo derecho (VS-SEG-010). Izquierda T1 con gadolinio, derecha
    CISS, al mismo nivel (z en mm)."""
    caja141 = (-40, 58, -45, -12)        # x (der → izq), y (adelante → atrás), mm LPS
    caja010 = (-55, 45, -45, 20)
    fila1 = [corte_dcm(serie_tcia('VS-SEG-141_t1'), -24.2, caja141),
             corte_dcm(serie_tcia('VS-SEG-141_t2'), -24.2, caja141)]
    fila2 = [corte_dcm(serie_tcia('VS-SEG-010_t1'), -24.6, caja010),
             corte_dcm(serie_tcia('VS-SEG-010_t2'), -24.8, caja010)]
    guardar(lamina([fila1, fila2]), 'cap11-rm-schwannoma.jpg')


def cap11_epidermoide():
    """PMC3467374 Fig. 1: T2 (A), T1 con gadolinio (B) y difusión (C) en una
    fila; se quita la histología (D)."""
    f = figura_pmc('epidermoide_3467374_f1.jpg')
    w, h = f.size                                        # 631 × 624, 2 × 2
    a = f.crop((0, 0, w // 2 - 2, h // 2 - 2))
    b = f.crop((w // 2 + 2, 0, w, h // 2 - 2))
    c = f.crop((0, h // 2 + 2, w // 2 - 2, h))
    guardar(lamina([[a, b, c]]), 'cap11-rm-epidermoide.jpg')


def cap11_asa_aica():
    """PMC6417406 Fig. 2 (clasificación de Gorrie), entera."""
    guardar(figura_pmc('aica_6417406_f2.jpg'), 'cap11-rm-asa-aica.jpg')


def cap09_hidrops():
    """PMC11098000 Fig. 2: oído con hidrops y oído control, entera."""
    guardar(figura_pmc('hidrops_11098000_f2.jpg'), 'cap09-rm-hidrops.jpg')


def cap23_hidrops_grados():
    """PMC9909016 Fig. 2: grados 0, I y II con su esquema, entera."""
    guardar(figura_pmc('hidrops_9909016_f2.jpg'), 'cap23-rm-hidrops-grados.jpg')


def cap12_infarto_aica():
    """PMC11390645 Fig. 1: vHIT, audiometría y difusión del mismo paciente."""
    guardar(figura_pmc('infarto_11390645_f1.jpg'), 'cap12-rm-infarto-aica.jpg')


def cap12_esclerosis():
    """MSLesSeg P57, FLAIR: la protuberancia (recortada) y un corte alto con
    las placas alrededor de los ventrículos, de la misma persona."""
    d = mslesseg('P57')
    tronco = corte_nii(d / 'P57_FLAIR.nii.gz', 44, caja=(41, 141, 72, 162), escala=4)
    alto = corte_nii(d / 'P57_FLAIR.nii.gz', 96, caja=(18, 164, 14, 200), escala=3)
    guardar(lamina([[tronco, alto]]), 'cap12-rm-esclerosis-multiple.jpg')


if __name__ == '__main__':
    for fn in (cap11_schwannoma, cap11_epidermoide, cap11_asa_aica, cap09_hidrops,
               cap23_hidrops_grados, cap12_infarto_aica, cap12_esclerosis):
        if len(sys.argv) == 1 or fn.__name__ in sys.argv[1:]:
            fn()
