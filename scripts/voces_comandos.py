"""Instrucciones del talkback (lo que dice el examinador), generadas con edge-tts.

Deja resources/audio/comandos/<clave>.mp3 para cada clave de COMANDOS, que
son las de src/audiometria/comandos_voz.py (también el nombre del audio y lo
que lee ResponseAudiometry.history_command: no se cambian). Rehace todas:
para cambiar una frase se edita su texto acá y se corre de nuevo, o se pasan
las claves a rehacer.

    python -m venv /tmp/venv_edge && /tmp/venv_edge/bin/pip install edge-tts
    /tmp/venv_edge/bin/python scripts/voces_comandos.py                  # todas
    /tmp/venv_edge/bin/python scripts/voces_comandos.py dos_pitos escucha
    /tmp/venv_edge/bin/python scripts/voces_comandos.py --estimulos      # palabras sin audio

--z hace las instrucciones del impedanciómetro (COMANDOS_Z, las claves de
src/impedanciometria/instrucciones.py) en resources/audio/comandos_z/:

    /tmp/venv_edge/bin/python scripts/voces_comandos.py --z              # todas
    /tmp/venv_edge/bin/python scripts/voces_comandos.py --z trague_una_vez

--estimulos hace, con la misma voz, las palabras de las listas
(ListWords.PALABRAS) que todavía no tienen su logo/estimulos/<palabra>.mp3;
no toca las que ya existen (las grabadas).

Los textos salen de las grabaciones anteriores (transcritas, con la redacción
del autor); ruido_blanco_contralateral y rosemberg_bilateral no tenían
grabación. Necesita ffmpeg. Ver docs/roadmap_voces.md.
"""
import ast
import asyncio
import os
import subprocess
import sys
import tempfile
import unicodedata

import edge_tts

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "resources", "audio", "comandos")
SALIDA_Z = os.path.join(RAIZ, "resources", "audio", "comandos_z")

# La de las grabaciones era femenina (~240 Hz): Catalina, un poco más lenta
# para un paciente que oye mal.
VOZ, TONO, VELOCIDAD = "es-CL-CatalinaNeural", "+0Hz", "-8%"
# Igual que las grabadas: -21 LUFS de mediana, sin pasar de -1.5 dBTP, para
# que el vúmetro y el nivel del talkback no cambien. Mono 48 kHz, 64 kbit/s.
FILTRO = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "loudnorm=I=-21:TP=-1.5:LRA=11")

COMANDOS = {
    # PREPARAR
    "colocar_fonos": "Le voy a colocar estos fonos. Por estos fonos va a escuchar unos pitos. "
                     "Cada pito que escuche, necesito que levante la mano. Aunque suenen muy "
                     "pequeños, me avisa todos los pitos que escuche.",
    "colocar_vibrador": "Le voy a colocar este aparato detrás de su oreja. Necesito que me avise "
                        "los pitos igual que al comienzo del examen, aunque suenen muy bajitos.",
    "aerea_+_ruido": "Ahora va a escuchar un ruido por la otra orejita. Necesito que no le haga "
                     "caso a ese ruido, y que me siga avisando los pitos de esta orejita.",
    "vibrador_+_ruido": "Le voy a colocar este aparato detrás de su oreja. Necesito que me avise "
                        "los pitos, aunque suenen muy bajitos. Por la otra oreja va un ruido: a "
                        "ese ruido no le haga caso, y me sigue avisando los pitos que escuche.",
    # INSTRUCCIONES
    "mano_levantada": "Va a escuchar un pito continuo. Necesito que mantenga la mano levantada "
                      "todo el tiempo que escuche el pito. Si lo deja de escuchar, baja la mano. "
                      "Si lo escucha más despacio, mantenga la mano levantada.",
    "mano_levantada_en_ruido": "Va a escuchar un ruido fuerte por la otra orejita, y un pito por "
                               "esta. A ese ruido no le haga caso. Necesito que mantenga la mano "
                               "levantada todo el tiempo que escuche el pito. Solo si deja de "
                               "escuchar el pito, baja la mano. Si lo escucha más bajito, "
                               "mantenga la mano levantada.",
    "escuche_mi_voz": "Apenas escuche mi voz, levante la mano.",
    "dictar_palabras": "Ahora le voy a dictar unas palabras. Necesito que las repita en voz alta, "
                       "y repita solo lo que entienda.",
    "pitos_fuertes": "Ahora le voy a colocar unos pitos fuertes. Van a ser todos fuertes, y se "
                     "irán aumentando en volumen: serán cada vez más fuertes. Necesito que me "
                     "avise si alguno de esos pitos fuertes a usted le molesta.",
    "solo_si_molesta": "Solo si le molesta el pito fuerte, levante la mano.",
    "dos_pitos": "Va a escuchar dos pitos de forma alternada: un oído primero y el otro después. "
                 "Necesito que me diga si los escucha iguales en volumen, o si escucha uno más "
                 "fuerte que el otro.",
    "cambie_de_volumen": "Va a escuchar un pito de forma continua. Necesito que me avise cuando "
                         "ese pito cambie de volumen, levantando la mano cada vez que ocurra.",
    "ruido_blanco_contralateral": "Va a escuchar un pito fuerte y continuo en esta orejita, y un "
                                  "ruido por la otra. A ese ruido no le haga caso. Necesito que "
                                  "mantenga la mano levantada todo el tiempo que escuche el "
                                  "pito. Si lo deja de escuchar, baja la mano.",
    "rosemberg_bilateral": "Va a escuchar un pito continuo, primero en una orejita y después "
                           "en la otra. Necesito que mantenga la mano levantada todo el tiempo "
                           "que escuche el pito. Si lo deja de escuchar, baja la mano, y la "
                           "vuelve a levantar cuando lo escuche de nuevo.",
    "pa_pa_pa": "Hola, hola, hola, hola, hola, hola. Pa, pa, pa, pa, pa.",
    # PREGUNTAS
    "escucha": "¿Me escucha?",
    "dejo_de_escuchar": "¿Lo dejó de escuchar?",
    "en_qué_oído": "¿En qué oído lo escuchó más fuerte?",
    "sonidos_iguales": "¿Los escuchó iguales?",
    "no_entiende": "¿Escucha, pero no entiende?",
    "molesta": "¿Le molesta cuando le hablo?",
    "molesto_o": "¿Ese sonido le molestó, o solo lo escuchó fuerte?",
    "muy_fuerte": "¿Está muy fuerte mi voz?",
}

# Impedanciómetro: se le habla al paciente en el box, sin talkback.
COMANDOS_Z = {
    # PREPARAR
    "explicar_examen": "Le voy a hacer un examen para ver cómo está su oído por dentro. No "
                       "duele. Va a sentir un poco de presión en el oído, y va a escuchar "
                       "algunos sonidos. Usted no tiene que hacer nada.",
    "colocar_sonda": "Le voy a poner esta gomita en la entrada del oído. Puede que sienta un "
                     "poco de presión. Si le molesta, me avisa levantando la mano.",
    "colocar_fono_contra": "En la otra oreja le voy a poner este fono. Por ahí va a escuchar "
                           "unos sonidos fuertes.",
    # INSTRUCCIONES
    "no_hablar_ni_tragar": "Ahora necesito que no se mueva, que no hable y que no trague "
                           "saliva, hasta que yo le avise. Respire normal.",
    "sonidos_fuertes": "Ahora va a escuchar unos sonidos fuertes. No tiene que hacer nada: "
                       "solo no se mueva, no hable y no trague.",
    "sonido_largo": "Ahora va a escuchar un sonido fuerte y largo. No se mueva, no hable y "
                    "no trague hasta que se termine.",
    "trague_tres_veces": "Ahora trague saliva tres veces seguidas, sin apurarse.",
    "trague_una_vez": "Ahora trague saliva una vez.",
    # PREGUNTAS
    "le_molesta_presion": "¿Le molesta la presión?",
    "trago": "¿Tragó saliva recién?",
    "esta_bien": "¿Está bien? ¿Puedo seguir?",
}


def archivo(clave, salida=SALIDA):
    """Como h_audio.normalize: sin tildes (en_qué_oído -> en_que_oido)."""
    plano = unicodedata.normalize("NFKD", clave).encode("ascii", "ignore").decode()
    return os.path.join(salida, f"{plano}.mp3")


async def generar(clave, textos=COMANDOS, salida=SALIDA):
    texto = textos[clave]
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        crudo = tmp.name
    try:
        await edge_tts.Communicate(texto, VOZ, pitch=TONO, rate=VELOCIDAD).save(crudo)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", crudo, "-af", FILTRO,
                        "-ac", "1", "-ar", "48000", "-b:a", "64k", archivo(clave, salida)],
                       check=True)
    finally:
        os.unlink(crudo)
    print(f"  {os.path.relpath(archivo(clave, salida), RAIZ)}")


# Las palabras de las listas, al nivel de las grabadas (-18 LUFS, mono
# 44,1 kHz): el vúmetro está calibrado con ellas.
FILTRO_ESTIMULO = FILTRO.replace("loudnorm=I=-21:TP=-1.5", "loudnorm=I=-18:TP=-1")
ESTIMULOS = os.path.join(RAIZ, "resources", "audio", "logo", "estimulos")


def palabras_de_las_listas():
    arbol = ast.parse(open(os.path.join(RAIZ, "src", "audiometria", "ListWords.py")).read())
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and getattr(nodo.targets[0], "id", "") == "PALABRAS":
            return sorted({p for lista in ast.literal_eval(nodo.value).values() for p in lista})
    sys.exit("No se encontró PALABRAS en ListWords.py")


async def estimulos():
    for palabra in palabras_de_las_listas():
        plano = unicodedata.normalize("NFKD", palabra.lower()).encode("ascii", "ignore").decode()
        final = os.path.join(ESTIMULOS, f"{plano}.mp3")
        if os.path.exists(final):
            continue
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            crudo = tmp.name
        try:
            await edge_tts.Communicate(f"{palabra}.", VOZ, pitch=TONO, rate=VELOCIDAD).save(crudo)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", crudo, "-af", FILTRO_ESTIMULO,
                            "-ac", "1", "-ar", "44100", "-b:a", "64k", final], check=True)
        finally:
            os.unlink(crudo)
        print(f"  {os.path.relpath(final, RAIZ)}")


async def main(claves, textos=COMANDOS, salida=SALIDA):
    os.makedirs(salida, exist_ok=True)
    for clave in claves:
        await generar(clave, textos, salida)


if __name__ == "__main__":
    if sys.argv[1:] == ["--estimulos"]:
        asyncio.run(estimulos())
        sys.exit()
    args = sys.argv[1:]
    textos, salida = COMANDOS, SALIDA
    if args[:1] == ["--z"]:
        args, textos, salida = args[1:], COMANDOS_Z, SALIDA_Z
    pedidas = args or list(textos)
    desconocidas = [c for c in pedidas if c not in textos]
    if desconocidas:
        sys.exit(f"Claves desconocidas: {', '.join(desconocidas)}")
    asyncio.run(main(pedidas, textos, salida))
