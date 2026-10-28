"""Junta los cuadros que dejó captura.html en un solo paquete para LabSim.

    resources/cabeza/cabeza.bin   los WebP, uno tras otro
    resources/cabeza/cabeza.json  sitios (con su punto 3D), ángulos, la
                                  cámara, dónde empieza cada cuadro en el .bin
                                  y dónde cae cada sitio en él
    resources/cabeza/malla.npz    la piel de cabeza.glb (vértices y caras), para
                                  saber qué punto de la piel hay bajo el mouse

Uso: python3 empaquetar.py <carpeta out/ de la captura> <commit de labyrinthus3d>
                           [<ruta de cabeza.glb>]
"""
import json
import pathlib
import struct
import sys

import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parents[2]


def malla_glb(ruta):
    """Vértices y caras de la primera malla de un .glb (sin dependencias)."""
    b = pathlib.Path(ruta).read_bytes()
    largo_json = struct.unpack("<I", b[12:16])[0]
    gltf = json.loads(b[20:20 + largo_json])
    binario = b[20 + largo_json + 8:]
    prim = gltf["meshes"][0]["primitives"][0]

    def leer(i_acc):
        acc = gltf["accessors"][i_acc]
        vista = gltf["bufferViews"][acc["bufferView"]]
        tipo = {5123: np.uint16, 5125: np.uint32, 5126: np.float32}[acc["componentType"]]
        n = {"SCALAR": 1, "VEC3": 3}[acc["type"]]
        ini = vista.get("byteOffset", 0) + acc.get("byteOffset", 0)
        return np.frombuffer(binario, tipo, acc["count"] * n, ini).reshape(-1, n) if n > 1 else \
            np.frombuffer(binario, tipo, acc["count"], ini)

    return leer(prim["attributes"]["POSITION"]).astype(np.float32), \
        leer(prim["indices"]).astype(np.int32).reshape(-1, 3)


def main(out, commit, glb=None):
    out = pathlib.Path(out)
    datos = json.loads((out / "sitios.json").read_text())
    geo = json.loads((out / "sitios3d.json").read_text())
    datos["camara"] = geo["camara"]
    por_id = {s["id"]: s for s in geo["sitios"]}
    for s in datos["sitios"]:
        s["pos"] = por_id[s["id"]]["pos"]
        s["normal"] = por_id[s["id"]]["normal"]
    destino = RAIZ / "resources" / "cabeza"
    destino.mkdir(parents=True, exist_ok=True)
    indice = {}
    with open(destino / "cabeza.bin", "wb") as binario:
        for p in datos["pitches"]:
            for y in datos["yaws"]:
                clave = f"{p}_{y}"
                bytes_ = (out / f"f_{clave}.webp").read_bytes()
                indice[clave] = [binario.tell(), len(bytes_)]
                binario.write(bytes_)
    datos["indice"] = indice
    datos["origen"] = f"labyrinthus3d {commit} (modelos/cabeza.glb, js/electrodos.js)"
    (destino / "cabeza.json").write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
    glb = glb or pathlib.Path.home() / "Escritorio/Proyectos/labyrinthus3d/modelos/cabeza.glb"
    vertices, caras = malla_glb(glb)
    np.savez_compressed(destino / "malla.npz", vertices=vertices, caras=caras)
    print(f"{len(indice)} cuadros, {(destino / 'cabeza.bin').stat().st_size / 1e6:.1f} MB; "
          f"malla {len(vertices)} vértices, {len(caras)} caras")


if __name__ == "__main__":
    main(*sys.argv[1:4])
