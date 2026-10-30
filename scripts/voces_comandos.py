"""Instrucciones del talkback (lo que dice el examinador), generadas con edge-tts.

Deja resources/audio/comandos/<clave>.mp3 para cada clave de COMANDOS, que
son las de src/audiometria/comandos_voz.py (también el nombre del audio y lo
que lee ResponseAudiometry.history_command: no se cambian). Rehace todas:
para cambiar una frase se edita su texto acá y se corre de nuevo, o se pasan
las claves a rehacer.

    python -m venv /tmp/venv_edge && /tmp/venv_edge/bin/pip install edge-tts
    /tmp/venv_edge/bin/python scripts/voces_comandos.py                  # todas
    /tmp/venv_edge/bin/python scripts/voces_comandos.py dos_pitos escucha

Los textos salen de las grabaciones anteriores (transcritas, con la redacción
del autor); ruido_blanco_contralateral y rosemberg_bilateral no tenían
grabación. Necesita ffmpeg. Ver docs/roadmap_voces.md.
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import unicodedata

import edge_tts

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "resources", "audio", "comandos")

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


def archivo(clave):
    """Como h_audio.normalize: sin tildes (en_qué_oído -> en_que_oido)."""
    plano = unicodedata.normalize("NFKD", clave).encode("ascii", "ignore").decode()
    return os.path.join(SALIDA, f"{plano}.mp3")


async def generar(clave):
    texto = COMANDOS[clave]
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        crudo = tmp.name
    try:
        await edge_tts.Communicate(texto, VOZ, pitch=TONO, rate=VELOCIDAD).save(crudo)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", crudo, "-af", FILTRO,
                        "-ac", "1", "-ar", "48000", "-b:a", "64k", archivo(clave)], check=True)
    finally:
        os.unlink(crudo)
    print(f"  {os.path.relpath(archivo(clave), RAIZ)}")


async def main(claves):
    for clave in claves:
        await generar(clave)


if __name__ == "__main__":
    pedidas = sys.argv[1:] or list(COMANDOS)
    desconocidas = [c for c in pedidas if c not in COMANDOS]
    if desconocidas:
        sys.exit(f"Claves desconocidas: {', '.join(desconocidas)}")
    asyncio.run(main(pedidas))
