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

--ac y --ot hacen las de los diapasones (COMANDOS_AC, resources/audio/
comandos_ac/) y del otoscopio (COMANDOS_OT, resources/audio/comandos_ot/).

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
SALIDA_AC = os.path.join(RAIZ, "resources", "audio", "comandos_ac")
SALIDA_OT = os.path.join(RAIZ, "resources", "audio", "comandos_ot")

# La de las grabaciones era femenina (~240 Hz): Catalina, un poco más lenta
# para un paciente que oye mal.
VOZ, TONO, VELOCIDAD = "es-CL-CatalinaNeural", "+0Hz", "-8%"
# Igual que las grabadas: -21 LUFS de mediana, sin pasar de -1.5 dBTP, para
# que el vúmetro y el nivel del talkback no cambien. Mono 48 kHz, 64 kbit/s.
# El final se recorta suave (-60 dB, dejando 150 ms) y se le agrega medio
# segundo de silencio: con el corte a -45 dB pegado a la voz se perdía la
# última sílaba (la "s" de "caso"), y el reproductor corta apenas termina el
# archivo, así que el colchón va en el audio (pedido del equipo, 2026-11-13).
COLA_S = 0.5
FILTRO = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.15,areverse,"
          f"loudnorm=I=-21:TP=-1.5:LRA=11,apad=pad_dur={COLA_S}")

COMANDOS = {
    # PREPARAR
    "colocar_fonos": "Le voy a colocar estos fonos. Por estos fonos va a escuchar unos pitos. "
                     "Cada pito que escuche, necesito que levante la mano. Aunque suenen muy "
                     "pequeños, me avisa todos los pitos que escuche.",
    "colocar_vibrador": "Le voy a colocar este aparato detrás de su oreja. Necesito que me avise "
                        "los pitos igual que al comienzo del examen, aunque suenen muy bajitos.",
    # Aviso de enmascaramiento: va además de la instrucción de la prueba.
    "ruido_otro_oido": "Ahora le voy a poner un ruido en el otro oído. A ese ruido no le "
                       "haga caso.",
    # INSTRUCCIONES
    # Carhart y Rosemberg: la misma consigna (el motor deduce cuál por el
    # nivel en que parte, ver response.ROSEMBERG_DESDE_SL).
    "mano_levantada": "Va a escuchar un pitito. Mantenga la mano levantada todo el tiempo que "
                      "escuche el pitito. Si lo escucha más despacio, mantenga la mano "
                      "levantada; si lo deja de escuchar, baje la mano.",
    "escuche_mi_voz": "Apenas escuche mi voz, levante la mano.",
    "dictar_palabras": "Ahora le voy a dictar unas palabras. Necesito que las repita en voz alta, "
                       "y repita solo lo que entienda.",
    "dictar_compuestas": "Ahora le voy a dictar unas palabras compuestas, como sacapuntas. "
                         "Necesito que las repita en voz alta. Si entiende solo una parte de la "
                         "palabra, repita esa parte, y si no está seguro, adivine.",
    "pitos_fuertes": "Ahora le voy a colocar unos pitos fuertes. Van a ser todos fuertes, y se "
                     "irán aumentando en volumen: serán cada vez más fuertes. Necesito que me "
                     "avise si alguno de esos pitos fuertes a usted le molesta.",
    "solo_si_molesta": "Solo si le molesta el pito fuerte, levante la mano.",
    "dos_pitos": "Va a escuchar dos pititos alternados, uno en cada oído: primero en uno y "
                 "después en el otro. Cada tanto le voy a preguntar en qué oído lo escucha "
                 "más fuerte, o si los escucha iguales.",
    "cambie_de_volumen": "Va a escuchar un pito de forma continua. Necesito que me avise cuando "
                         "ese pito cambie de volumen, levantando la mano cada vez que ocurra.",
    "ruido_blanco_contralateral": "Va a escuchar un pito fuerte y continuo en esta orejita, y un "
                                  "ruido por la otra. A ese ruido no le haga caso. Necesito que "
                                  "mantenga la mano levantada todo el tiempo que escuche el "
                                  "pito. Si lo deja de escuchar, baja la mano.",
    # No es una instrucción: la voz en vivo del SDT, en el panel de las
    # listas (ListWords). Suena en bucle por el canal con Habla.
    "pa_pa_pa": "Hola, hola, hola, hola, hola, hola. Pa, pa, pa, pa, pa.",
    # Tinnitumetría (T03): tono, intensidad, NME e inhibición residual.
    "acufeno_cual_se_parece": "Le voy a presentar algunos sonidos, uno después del otro. Fíjese "
                              "en lo agudo o lo grave de cada uno. Después le voy a preguntar "
                              "cuál se parece más a su ruido.",
    "acufeno_igual_fuerte": "Ahora va a escuchar un sonido que irá subiendo de a poco. Levante "
                            "la mano cuando lo escuche igual de fuerte que su ruido.",
    "acufeno_deje_de_escuchar": "Ahora va a escuchar un ruido que irá subiendo de a poco. "
                                "Levante la mano cuando ya no escuche su propio ruido.",
    "acufeno_solo_el_mio": "Escuche mi pitido. Avíseme cuando solo escuche el mío y no el suyo.",
    "acufeno_un_minuto": "Ahora va a escuchar un sonido durante un minuto. No tiene que hacer "
                         "nada. Cuando se apague, le voy a preguntar cómo está su ruido.",
    # PREGUNTAS
    "escucha": "¿Me escucha?",
    "dejo_de_escuchar": "¿Lo dejó de escuchar?",
    "en_qué_oído": "¿En qué oído lo escuchó más fuerte?",
    "sonidos_distintos": "¿Los dos sonidos eran diferentes en forma?",
    "no_entiende": "¿Escucha, pero no entiende?",
    "molesto_o": "¿Ese sonido le molestó, o solo lo escuchó fuerte?",
    "muy_fuerte": "¿Está muy fuerte mi voz?",
    "acufeno_cual": "¿Cuál se parece más a su ruido: el primero, el segundo o el tercero?",
    "acufeno_como_esta": "¿Cómo está su ruido ahora?",
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

# Diapasones (src/audiometria/Acumetria.py, GRUPOS): en el box, sin talkback.
COMANDOS_AC = {
    # PREPARAR
    "explicar_diapasones": "Le voy a hacer una prueba con este diapasón, que vibra y suena. Se lo "
                           "voy a poner detrás de la oreja, frente a la oreja y en la frente. No "
                           "duele.",
    # INSTRUCCIONES
    "avise_si_escucha": "Cada vez que le ponga el diapasón, dígame si lo escucha.",
    "avise_cuando_deje": "Le voy a poner el diapasón. Avíseme justo cuando deje de "
                         "escucharlo.",
    "compare_sonidos": "Le voy a poner el diapasón detrás de la oreja y después frente a la "
                       "oreja. Dígame dónde lo escucha más fuerte.",
    "diga_donde": "Le voy a poner el diapasón en la frente. Dígame dónde lo escucha: en el oído "
                  "derecho, en el izquierdo o al medio.",
    # PREGUNTAS
    "lo_escucha": "¿Lo escucha?",
    "sigue_escuchando": "¿Lo sigue escuchando?",
    "escucha_o_vibra": "¿Lo escucha, o solo lo siente vibrar?",
    "donde_mas_fuerte": "¿Dónde lo escuchó más fuerte?",
    "igual_ambos": "¿Lo escucha igual en los dos oídos?",
}

# Otoscopía (src/audiometria/Otoscopia.py, GRUPOS).
COMANDOS_OT = {
    # PREPARAR
    "explicar_otoscopia": "Le voy a revisar el oído con esta luz. No duele. Voy a tirar un "
                          "poquito de su oreja para ver mejor.",
    # INSTRUCCIONES
    "quedese_quieto": "Quédese quieto, por favor, sin mover la cabeza.",
    "incline_cabeza": "Incline un poco la cabeza hacia el otro lado.",
    "avise_si_molesta": "Si le molesta o le duele, me avisa.",
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
# Sin el colchón del final: son estímulos de la lista, no instrucciones.
FILTRO_ESTIMULO = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                   "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                   "loudnorm=I=-18:TP=-1:LRA=11")
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
    elif args[:1] == ["--ac"]:
        args, textos, salida = args[1:], COMANDOS_AC, SALIDA_AC
    elif args[:1] == ["--ot"]:
        args, textos, salida = args[1:], COMANDOS_OT, SALIDA_OT
    pedidas = args or list(textos)
    desconocidas = [c for c in pedidas if c not in textos]
    if desconocidas:
        sys.exit(f"Claves desconocidas: {', '.join(desconocidas)}")
    asyncio.run(main(pedidas, textos, salida))
