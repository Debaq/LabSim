"""Voces del paciente (audiometria/h_audio.py): la del caso sale de su edad y
sexo, y cada voz tiene todo lo que el motor le hace decir."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from audiometria.h_audio import VOCES_PACIENTE, normalize, voz_del_paciente  # noqa: E402
from audiometria.ListWords import PALABRAS  # noqa: E402

AUDIO = os.path.join(RAIZ, "resources", "audio")
# Lo que piden response.py y response_A.py con create_voice.
FRASES_DEL_MOTOR = {"si", "no", "molesta", "elderecho", "elizquierdo"}


def test_la_voz_sale_de_la_edad_y_el_sexo():
    assert voz_del_paciente({"gender": 0, "edad": 45}) == ("feme", 1)
    assert voz_del_paciente({"gender": 1, "edad": 45}) == ("male", 1)
    assert voz_del_paciente({"gender": 0, "edad": 7}) == ("nina", 1)
    assert voz_del_paciente({"gender": 1, "edad": 12}) == ("nino", 1)
    assert voz_del_paciente({"gender": 1, "edad": 13}) == ("male", 1)
    assert voz_del_paciente({"gender": 1}) == ("male", 1)       # sin edad: adulto
    assert voz_del_paciente({"edad": ""}) == ("feme", 1)


def test_cada_voz_tiene_las_palabras_el_no_entendi_y_las_frases():
    palabras = {p for lista in PALABRAS.values() for p in lista}
    for voz in VOCES_PACIENTE:
        logo = os.path.join(AUDIO, "logo", "respuestas", voz)
        for p in palabras:
            assert os.path.exists(os.path.join(logo, normalize(p.lower()) + ".mp3")), (voz, p)
        for n in ("none1", "none2", "none3"):
            assert os.path.exists(os.path.join(logo, n + ".mp3")), (voz, n)
        for f in FRASES_DEL_MOTOR:
            assert os.path.exists(os.path.join(AUDIO, "paciente", voz, f + ".mp3")), (voz, f)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
