"""El paciente contesta las preguntas del Fowler (¿Los escuchó iguales?, ¿En
qué oído?) cuando el talkback termina de decirlas, no encima: antes el "sí"
salía al mismo tiempo que la pregunta."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtMultimedia import QMediaPlayer  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from audiometria.audio_player import Player  # noqa: E402
from audiometria.response import ResponseAudiometry  # noqa: E402


class _Label:
    def setStyleSheet(self, value):
        pass


class _Audio:
    lbl_response = _Label()


def _respuesta():
    r = ResponseAudiometry(_Audio())
    r.contestadas = []
    r.other_response.fowler_q = lambda n, data: r.contestadas.append(n)
    return r


def test_contesta_despues_de_la_pregunta():
    r = _respuesta()
    r.rol_player('sonidos_iguales')
    QTest.qWait(1000)
    assert r.contestadas == []            # mientras suena la pregunta, nada
    r.talkback_termino()
    assert r.contestadas == []            # una pausa antes de contestar
    QTest.qWait(ResponseAudiometry.PAUSA_RESPUESTA_MS[1] + 100)
    assert r.contestadas == [1]
    r.talkback_termino()                  # otra instrucción que termina: no repite
    QTest.qWait(ResponseAudiometry.PAUSA_RESPUESTA_MS[1] + 100)
    assert r.contestadas == [1]


def test_en_que_oido_y_otra_instruccion_la_reemplaza():
    r = _respuesta()
    r.rol_player('en_qué_oído')
    r.rol_player('dos_pitos')             # se cambió antes de terminar
    r.talkback_termino()
    QTest.qWait(ResponseAudiometry.PAUSA_RESPUESTA_MS[1] + 100)
    assert r.contestadas == []
    r.rol_player('en_qué_oído')
    r.talkback_termino()
    QTest.qWait(ResponseAudiometry.PAUSA_RESPUESTA_MS[1] + 100)
    assert r.contestadas == [2]


def test_el_reproductor_avisa_cuando_termina():
    p = Player(3)
    terminados = []
    p.termino.connect(terminados.append)
    p.check_end_of_media(p.players[2], QMediaPlayer.MediaStatus.EndOfMedia)
    p.check_end_of_media(p.players[2], QMediaPlayer.MediaStatus.InvalidMedia)
    p.check_end_of_media(p.players[2], QMediaPlayer.MediaStatus.LoadedMedia)
    assert terminados == [2, 2]


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
