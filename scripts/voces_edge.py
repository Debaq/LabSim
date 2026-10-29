"""Voces del paciente para las listas de palabras, generadas con edge-tts.

Lee las palabras de src/audiometria/ListWords.py (PALABRAS) y deja en
resources/audio/logo/respuestas/<voz>/<palabra>.mp3 una por voz. Las que ya
existen no se rehacen: para rehacer una, se borra su mp3 y se corre de nuevo.

    python -m venv /tmp/venv_edge && /tmp/venv_edge/bin/pip install edge-tts
    /tmp/venv_edge/bin/python scripts/voces_edge.py                # todas las voces
    /tmp/venv_edge/bin/python scripts/voces_edge.py nina1 pelota   # solo esa

edge-tts usa la lectura en voz alta de Edge: gratis y sin clave, pero no es
una API oficial. Necesita ffmpeg. Ver docs/roadmap_voces.md.
"""
import ast
import asyncio
import os
import subprocess
import sys

import edge_tts

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "resources", "audio", "logo", "respuestas")

# voz de la app -> (voz de Edge, tono, velocidad). Edge no tiene voces
# infantiles en español: son las chilenas adultas con el tono subido.
VOCES = {
    "nino1": ("es-CL-LorenzoNeural", "+45Hz", "-45%"),
    "nina1": ("es-CL-CatalinaNeural", "+40Hz", "-45%"),
}
# Recorta el silencio del principio y del final (igual que las grabadas)
FILTRO = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse")


def palabras_de_las_listas():
    arbol = ast.parse(open(os.path.join(RAIZ, "src", "audiometria", "ListWords.py")).read())
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and getattr(nodo.targets[0], "id", "") == "PALABRAS":
            listas = ast.literal_eval(nodo.value)
            return sorted({p for lista in listas.values() for p in lista})
    sys.exit("No se encontró PALABRAS en ListWords.py")


def normalize(s):
    # La misma de audiometria/h_audio.py, sin importar Qt
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        s = s.replace(a, b).replace(a.upper(), b.upper())
    return s


async def generar(palabra, clave, voz, tono, velocidad):
    final = os.path.join(SALIDA, clave, normalize(palabra.lower()) + ".mp3")
    if os.path.exists(final):
        return
    os.makedirs(os.path.dirname(final), exist_ok=True)
    crudo = final + ".crudo.mp3"
    for _ in range(4):
        try:
            await edge_tts.Communicate(f"{palabra}.", voz, rate=velocidad, pitch=tono).save(crudo)
            break
        except Exception as e:
            print("reintento", clave, palabra, e)
            await asyncio.sleep(2)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", crudo, "-af", FILTRO,
                    "-b:a", "96k", final], check=True)
    os.remove(crudo)
    print(clave, palabra)


async def main(args):
    voces = {k: v for k, v in VOCES.items() if not args or k == args[0]}
    palabras = [args[1]] if len(args) > 1 else palabras_de_las_listas()
    sem = asyncio.Semaphore(4)

    async def tarea(p, clave, cfg):
        async with sem:
            await generar(p, clave, *cfg)

    await asyncio.gather(*(tarea(p, c, cfg) for p in palabras for c, cfg in voces.items()))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
