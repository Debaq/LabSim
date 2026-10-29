"""La cara del paciente de frente, reclinándose, para la rinoscopía
(nasal/RinoscopiaWindow.py). Mismo método que la cabeza de los electrodos
(scripts/cabeza_electrodos/LEEME.md): la cabeza de labyrinthus3d
fotografiada con captura.html, aquí solo de frente y de 0° a 60° de
extensión cada 2°:

    ... (servidor y enlaces como en el LEEME)
    chromium --headless=new --no-sandbox --use-angle=swiftshader \\
        --enable-unsafe-swiftshader --user-data-dir=$S/perfil \\
        "http://127.0.0.1:8731/captura.html?yaw=360&tam=600&pitch=0,-2,-4,...,-60"
    python3 scripts/nasal/cara_rinoscopia.py $S/out <commit de labyrinthus3d>

Deja resources/rinoscopia/cara.bin (los WebP) y cara.json: los ángulos,
dónde empieza cada cuadro, dónde cae cada narina en cada cuadro y dónde
asoma el corte del cuello (el modelo termina ahí: el visor lo tapa con la
bata). Las narinas y el cuello se proyectan con la malla y la cámara de
resources/cabeza (core/cabeza_electrodos.Geometria), la misma cámara de la
captura.
"""
import json
import pathlib
import sys

import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'src'))
from core.base import context  # noqa: E402,F401
from core import cabeza_electrodos as ce  # noqa: E402

TAM = 600
# Las narinas en el cuadro recto (px de 600): la derecha del paciente queda
# a la izquierda de la imagen.
NARINAS = {'D': (286, 322), 'I': (312, 322)}


def main(out, commit):
    out = pathlib.Path(out)
    datos = json.loads((out / 'sitios.json').read_text())
    pitches = sorted(datos['pitches'], reverse=True)          # 0, -2, ..., -60
    g = ce.geometria()
    k = g.tam / TAM
    narinas = {}
    for lado, (x, y) in NARINAS.items():
        hit = g.rayo(x * k, y * k, 0, 0)
        if hit is None:
            raise SystemExit(f'no hay piel bajo la narina {lado}')
        narinas[lado] = hit
    # El borde del cuello: los vértices más bajos de la malla.
    malla = np.load(context.get_resource('cabeza/malla.npz'))
    v = malla['vertices'].astype(float)
    anillo = v[v[:, 1] < v[:, 1].min() + 0.004]
    destino = RAIZ / 'resources' / 'rinoscopia'
    destino.mkdir(parents=True, exist_ok=True)
    indice, por_cuadro = {}, {}
    with open(destino / 'cara.bin', 'wb') as binario:
        for p in pitches:
            clave = str(-p)                  # grados de extensión: 0 ... 60
            bytes_ = (out / f'f_{p}_0.webp').read_bytes()
            indice[clave] = [binario.tell(), len(bytes_)]
            binario.write(bytes_)
            fila = {}
            for lado, (punto, normal) in narinas.items():
                px, _ = g.proyectar(punto, normal, p, 0)
                fila[lado] = [round(float(px[0][0] / k), 1), round(float(px[0][1] / k), 1)]
            px, _ = g.proyectar(anillo, np.zeros_like(anillo), p, 0)
            px = px / k
            fila['cuello'] = [round(float(px[:, 0].min()), 1), round(float(px[:, 0].max()), 1),
                              round(float(px[:, 1].min()), 1)]
            por_cuadro[clave] = fila
    info = {'tam': TAM, 'grados': [-p for p in pitches], 'indice': indice, 'cuadros': por_cuadro,
            'origen': f'labyrinthus3d {commit} (modelos/cabeza.glb), scripts/nasal/cara_rinoscopia.py'}
    (destino / 'cara.json').write_text(json.dumps(info, ensure_ascii=False, separators=(',', ':')))
    print(f"{len(indice)} cuadros, {(destino / 'cara.bin').stat().st_size / 1e6:.1f} MB")


if __name__ == '__main__':
    main(*sys.argv[1:3])
