"""Todos los audios que la app puede pedir existen en resources/audio.

Si falta un mp3, la app no avisa: la palabra o la frase simplemente no suena
(ListWords corta el timer con InvalidMedia, FrasesHabladas se la salta).
Este test lee las listas y las frases desde el código, así que una palabra o
instrucción nueva sin su audio lo hace fallar. Para generar lo que falte:
scripts/voces_edge.py (paciente) y scripts/voces_comandos.py (examinador).
Ver docs/roadmap_voces.md.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from audiometria.h_audio import VOCES_PACIENTE, normalize  # noqa: E402
from audiometria.ListWords import MITADES, PALABRAS  # noqa: E402
from audiometria import comandos_voz, Acumetria, Otoscopia  # noqa: E402
from impedanciometria import instrucciones  # noqa: E402

AUDIO = os.path.join(RAIZ, "resources", "audio")
# Cuando no entendió la palabra (ListWords.response elige una al azar).
NO_ENTENDIO = ("none1", "none2", "none3")
# Lo que dice el paciente fuera de las listas (create_voice): response.py y
# response_A.py (LDL, SISI, Fowler, preguntas del talkback).
FRASES_PACIENTE = ("si", "no", "molesta", "elderecho", "elizquierdo")


def _faltan(rutas):
    return sorted(os.path.relpath(r, AUDIO) for r in rutas if not os.path.exists(r))


def _palabras():
    return {p for lista in PALABRAS.values() for p in lista}


def _mitades():
    return {m for par in MITADES.values() for m in par}


def _archivo(nombre):
    # Igual que create_word / create_word_response: minúsculas y sin tildes ni ñ
    return normalize(nombre.lower()) + ".mp3"


def _claves(grupos):
    return [clave for _titulo, frases in grupos for _rotulo, clave in frases]


def test_cada_palabra_tiene_su_estimulo():
    rutas = [os.path.join(AUDIO, "logo", "estimulos", _archivo(p)) for p in _palabras()]
    assert not _faltan(rutas), _faltan(rutas)


def test_cada_compuesta_del_srt_tiene_sus_mitades():
    for palabra, mitades in MITADES.items():
        assert len(mitades) == 2, palabra
    srt = set(PALABRAS[("s", "")])
    assert srt == set(MITADES), srt ^ set(MITADES)


def test_cada_voz_repite_cada_palabra():
    nombres = _palabras() | _mitades() | set(NO_ENTENDIO)
    rutas = [os.path.join(AUDIO, "logo", "respuestas", voz, _archivo(n))
             for voz in VOCES_PACIENTE for n in nombres]
    assert not _faltan(rutas), _faltan(rutas)


def test_cada_voz_tiene_sus_frases():
    rutas = [os.path.join(AUDIO, "paciente", voz, f"{frase}.mp3")
             for voz in VOCES_PACIENTE for frase in FRASES_PACIENTE]
    assert not _faltan(rutas), _faltan(rutas)


def test_cada_instruccion_del_audiometro_tiene_su_audio():
    rutas = [os.path.join(AUDIO, "comandos", normalize(f"{c}.mp3"))
             for c in _claves(comandos_voz.GRUPOS)]
    assert not _faltan(rutas), _faltan(rutas)


def test_cada_instruccion_de_los_otros_equipos_tiene_su_audio():
    # FrasesHabladas busca <carpeta>/<clave>.mp3 tal cual, sin normalizar
    equipos = (("comandos_ac", Acumetria.GRUPOS), ("comandos_ot", Otoscopia.GRUPOS),
               ("comandos_z", instrucciones.GRUPOS))
    rutas = [os.path.join(AUDIO, carpeta, f"{c}.mp3")
             for carpeta, grupos in equipos for c in _claves(grupos)]
    assert not _faltan(rutas), _faltan(rutas)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
