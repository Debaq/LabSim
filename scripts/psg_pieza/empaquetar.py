"""Junta los cuadros que dejó gen_pieza.py (modo todo) en un paquete para LabSim.

    resources/psg_pieza/pieza.bin   los WebP, uno tras otro
    resources/psg_pieza/pieza.json  por grupo (cada punto de vista de la ventanilla y la cámara del
                                    techo): la imagen base entera, el rectángulo que cambia entre
                                    estados y el recorte de ese rectángulo en cada estado
                                    (pose_despierto_respiración); y el vano de la ventanilla en cada
                                    punto de vista, para el reflejo del vidrio.

La cámara del techo pasa a infrarrojo acá (gris, niveles fijos para todos los cuadros, viñeta).

Uso: python3 empaquetar.py <carpeta de gen_pieza.py todo>
"""
import io
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageOps

RAIZ = pathlib.Path(__file__).resolve().parents[2]
DESTINO = RAIZ / 'resources' / 'psg_pieza'
CALIDAD = 84
UMBRAL = 6        # diferencia (0-255) desde la que un píxel cuenta como cambiado
MARGEN = 8


def webp(im):
    b = io.BytesIO()
    im.save(b, 'WEBP', quality=CALIDAD, method=6)
    return b.getvalue()


def infrarrojo(im, niveles, vineta):
    g = np.asarray(im.convert('L'), dtype=np.float32)
    lo, hi = niveles
    g = np.clip((g - lo) / (hi - lo), 0, 1) * vineta
    g = np.clip(g * 255, 0, 255).astype(np.uint8)
    return ImageOps.colorize(Image.fromarray(g), '#050805', '#eef5ee')


def grupo(cuadros, binario, prep=None):
    """{clave: ruta png} -> base, rectángulo que cambia y recortes."""
    ims = {}
    for clave, ruta in cuadros.items():
        im = Image.open(ruta).convert('RGB')
        ims[clave] = prep(im) if prep else im
    claves = sorted(ims)
    base = ims[claves[0]]
    a = np.asarray(base, dtype=np.int16)
    cambio = np.zeros(a.shape[:2], bool)
    for c in claves[1:]:
        cambio |= (np.abs(np.asarray(ims[c], dtype=np.int16) - a).max(axis=2) > UMBRAL)
    ys, xs = np.nonzero(cambio)
    x0, y0 = max(0, xs.min() - MARGEN), max(0, ys.min() - MARGEN)
    x1, y1 = min(base.width, xs.max() + MARGEN + 1), min(base.height, ys.max() + MARGEN + 1)

    def guardar(b):
        ini = binario.tell()
        binario.write(b)
        return [ini, len(b)]

    return {'base': guardar(webp(base)), 'rect': [int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
            'cuadros': {c: guardar(webp(ims[c].crop((x0, y0, x1, y1)))) for c in claves}}


def main(carpeta):
    carpeta = pathlib.Path(carpeta)
    assert (carpeta / 'fin.txt').exists(), 'gen_pieza.py todo no terminó'
    info = json.loads((carpeta / 'vistas.json').read_text())
    claves = sorted(p.stem[3:] for p in carpeta.glob('v0_*.png'))
    DESTINO.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(['git', '-C', str(RAIZ), 'rev-parse', '--short', 'HEAD'],
                            capture_output=True, text=True).stdout.strip()
    datos = {'generado_con': f'scripts/psg_pieza (LabSim {commit})', 'respira': info['respira'],
             'claves': claves, 'ventanilla': {'tam': info['ventanilla'], 'vistas': []}}
    with open(DESTINO / 'pieza.bin', 'wb') as binario:
        for k, vano in enumerate(info['vano']):
            g = grupo({c: carpeta / f'v{k}_{c}.png' for c in claves}, binario)
            g['vano'] = vano
            datos['ventanilla']['vistas'].append(g)
        # Infrarrojo: niveles y viñeta fijos, sacados del primer cuadro.
        w, h = info['techo']
        muestra = np.asarray(Image.open(carpeta / f't_{claves[0]}.png').convert('L'), dtype=np.float32)
        niveles = (float(np.percentile(muestra, 1)), float(np.percentile(muestra, 99.5)))
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        vineta = np.clip(1.15 - 0.45 * r ** 2, 0, 1)
        datos['techo'] = {'tam': [w, h], **grupo({c: carpeta / f't_{c}.png' for c in claves}, binario,
                                                 lambda im: infrarrojo(im, niveles, vineta))}
    (DESTINO / 'pieza.json').write_text(json.dumps(datos, ensure_ascii=False, separators=(',', ':')))
    tam = (DESTINO / 'pieza.bin').stat().st_size / 1e6
    print(f'{len(claves)} estados x {len(info["vano"])} vistas + techo: {tam:.1f} MB')


if __name__ == '__main__':
    main(sys.argv[1])
