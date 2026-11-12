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


def test_muchas_preguntas_no_borran_dos_pitos():
    """Tickets 53/55: tras 12 preguntas seguidas "Dos pitos" salía de la
    historia y "¿En qué oído?" se contestaba como en umbrales."""
    r = _respuesta()
    r.rol_player('colocar_fonos')
    r.rol_player('dos_pitos')
    for _ in range(40):
        r.rol_player('sonidos_iguales')
        r.rol_player('en_qué_oído')
    assert r._instruccion() == 'dos_pitos'
    assert len(r.history_command) <= 12
    r.rol_player('mano_levantada')        # una instrucción nueva sí la reemplaza
    assert r._instruccion() == 'mano_levantada'


def test_el_reproductor_avisa_cuando_termina():
    p = Player(3)
    terminados = []
    p.termino.connect(terminados.append)
    p.check_end_of_media(p.players[2], QMediaPlayer.MediaStatus.EndOfMedia)
    p.check_end_of_media(p.players[2], QMediaPlayer.MediaStatus.InvalidMedia)
    p.check_end_of_media(p.players[2], QMediaPlayer.MediaStatus.LoadedMedia)
    assert terminados == [2, 2]


def _dice(diplacusia, n, int_od, int_oi):
    """Lo que contesta fowler_q con OD 5 / OI 25 y reclutamiento completo."""
    from audiometria.Fowler import FOWLER_PATTERNS
    r = ResponseAudiometry(_Audio())
    o = r.other_response
    dichas = []
    o.create_voice_ = dichas.append
    o.set_fowler_data(5, 25, FOWLER_PATTERNS['complete'], diplacusia)
    o.fowler_q(n, {'audio': {'output': [0, 1], 'int': [int_od, int_oi]}})
    return dichas


def test_mismo_volumen_solo_sonoridad():
    """¿Los escucha al mismo volumen?: la diploacusia no lo cambia."""
    for diplacusia in (False, True):
        assert _dice(diplacusia, 1, 65, 65) == ['si']
        assert _dice(diplacusia, 1, 65, 50) == ['no']
        assert _dice(diplacusia, 2, 65, 50) == ['elderecho']


def test_diferentes_en_forma_es_la_diploacusia():
    """¿Los dos sonidos eran diferentes en forma?, en cualquier nivel en que
    oiga los dos tonos (OD 5 / OI 25)."""
    for od, oi in ((5, 25), (45, 55), (90, 90)):
        assert _dice(True, 3, od, oi) == ['si']
        assert _dice(False, 3, od, oi) == ['no']
    assert _dice(True, 3, 40, 20) == ['nose']    # el OI bajo su umbral
    assert _dice(False, 3, 0, 0) == ['nose']


def test_diploacusia_por_frecuencia():
    from audiometria.Fowler import diploacusia
    fowler = {'patterns': {'3': 'complete', '4': 'none'}, 'diplacusia': {'3': True, '4': False}}
    assert diploacusia(fowler, 3) and not diploacusia(fowler, 4)
    assert diploacusia({'diplacusia': True}, 5)          # caso viejo: todo el caso
    assert not diploacusia({'diplacusia': []}, 3)
    assert not diploacusia({}, 3) and not diploacusia(None, 3)


def test_diferentes_en_forma_va_al_fowler():
    r = _respuesta()
    r.rol_player('colocar_fonos')         # ya no está "Dos pitos": igual contesta
    r.rol_player('sonidos_distintos')
    r.talkback_termino()
    QTest.qWait(ResponseAudiometry.PAUSA_RESPUESTA_MS[1] + 100)
    assert r.contestadas == [3]


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
