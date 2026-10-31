"""Voces del paciente, generadas con edge-tts.

Por cada voz deja:
  - resources/audio/logo/respuestas/<voz>/<palabra>.mp3: el paciente repite
    cada palabra de las listas (PALABRAS de src/audiometria/ListWords.py), y
    none1-3.mp3 cuando no la entendió.
  - resources/audio/paciente/<voz>/<frase>.mp3: lo que contesta en las otras
    pruebas (FRASES: sí/no del SISI y del Fowler, "molesta" de la LDL...).

Las que ya existen no se rehacen: para rehacer una, se borra su mp3 y se
corre de nuevo.

    python -m venv /tmp/venv_edge && /tmp/venv_edge/bin/pip install edge-tts
    /tmp/venv_edge/bin/python scripts/voces_edge.py                # todo
    /tmp/venv_edge/bin/python scripts/voces_edge.py nina1          # una voz
    /tmp/venv_edge/bin/python scripts/voces_edge.py nina1 pelota   # una palabra o frase

La voz de cada caso la elige audiometria/h_audio.voz_del_paciente (edad y
sexo). edge-tts usa la lectura en voz alta de Edge: gratis y sin clave, pero
no es una API oficial. Necesita ffmpeg. Ver docs/roadmap_voces.md.
"""
import ast
import asyncio
import os
import subprocess
import sys

import edge_tts

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(RAIZ, "resources", "audio")

# voz de la app -> (voz de Edge, tono, velocidad). Edge no tiene voces
# infantiles en español: son las chilenas adultas con el tono subido. La
# mujer adulta no es Catalina, que es la del examinador (talkback).
VOCES = {
    "nino1": ("es-CL-LorenzoNeural", "+45Hz", "-45%"),
    "nina1": ("es-CL-CatalinaNeural", "+40Hz", "-45%"),
    "feme1": ("es-PE-CamilaNeural", "+0Hz", "-10%"),
    "male1": ("es-CL-LorenzoNeural", "+0Hz", "-10%"),
}
# Cuando no entendió la palabra (ListWords elige una al azar).
NO_ENTENDIO = {"none1": "No entendí.", "none2": "¿Qué dijo?", "none3": "No sé."}
# Respuestas en las otras pruebas (create_voice). Las claves son las que
# pide el motor (response.py, response_A.py); los textos, los de las
# grabaciones que había.
FRASES = {
    "si": "¡Sí!",
    "no": "No.",
    "molesta": "Molesta.",
    "elderecho": "El derecho.",
    "elizquierdo": "El izquierdo.",
    "dejaescucharse": "Dejó de escucharse.",
    "seescuchamasbajito": "Se escucha más bajito.",
    "cansado1": "¡Me quiero ir!",
    "cansado2": "Estoy que me desmayo.",
    "cansado3": "¿Falta mucho?",
    "cansado4": "¿Cuánto dura esta atención?",
    "cansado5": "Disculpe, pero tengo calor.",
}
# Recorta el silencio del principio y del final, y deja todas las voces al
# mismo volumen (el de las de niño, que ya estaban).
FILTRO = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "loudnorm=I=-17:TP=-1.5:LRA=11")


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


def trabajos():
    """(archivo final, texto) de todo lo que dice el paciente, por voz."""
    for clave in VOCES:
        logo = os.path.join(AUDIO, "logo", "respuestas", clave)
        for palabra in palabras_de_las_listas():
            yield clave, palabra, os.path.join(logo, normalize(palabra.lower()) + ".mp3"), f"{palabra}."
        for nombre, texto in NO_ENTENDIO.items():
            yield clave, nombre, os.path.join(logo, nombre + ".mp3"), texto
        for nombre, texto in FRASES.items():
            yield clave, nombre, os.path.join(AUDIO, "paciente", clave, nombre + ".mp3"), texto


async def generar(final, texto, voz, tono, velocidad):
    if os.path.exists(final):
        return
    os.makedirs(os.path.dirname(final), exist_ok=True)
    crudo = final + ".crudo.mp3"
    for _ in range(4):
        try:
            await edge_tts.Communicate(texto, voz, rate=velocidad, pitch=tono).save(crudo)
            break
        except Exception as e:
            print("reintento", final, e)
            await asyncio.sleep(2)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", crudo, "-af", FILTRO,
                    "-ac", "1", "-ar", "24000", "-b:a", "96k", final], check=True)
    os.remove(crudo)
    print(os.path.relpath(final, RAIZ))


async def main(args):
    pedidos = [(final, texto, VOCES[clave]) for clave, nombre, final, texto in trabajos()
               if (not args or clave == args[0]) and (len(args) < 2 or nombre == args[1])]
    sem = asyncio.Semaphore(4)

    async def tarea(final, texto, cfg):
        async with sem:
            await generar(final, texto, *cfg)

    await asyncio.gather(*(tarea(*p) for p in pedidos))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
