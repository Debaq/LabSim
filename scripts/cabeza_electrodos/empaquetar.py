"""Junta los cuadros que dejó captura.html en un solo paquete para LabSim.

    resources/cabeza/cabeza.bin   los WebP, uno tras otro
    resources/cabeza/cabeza.json  sitios, ángulos, dónde empieza cada cuadro
                                  en el .bin y dónde cae cada sitio en él

Uso: python3 empaquetar.py <carpeta out/ de la captura> <commit de labyrinthus3d>
"""
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[2]


def main(out, commit):
    out = pathlib.Path(out)
    datos = json.loads((out / "sitios.json").read_text())
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
    print(f"{len(indice)} cuadros, {(destino / 'cabeza.bin').stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main(*sys.argv[1:3])
