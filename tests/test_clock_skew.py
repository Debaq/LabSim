"""
Comparación del reloj de la máquina contra el del servidor
(BackendClient.clock_skew, api/clock.php).

Lo que se compara es el EPOCH UTC, que es lo único que no depende de zonas
horarias. Y se compara para AVISAR, no para reinterpretar fechas: las horas
de una cita son las del curso y no las del computador que las lee -- si se
mostraran en la zona de cada máquina, dos alumnos de la misma clase con los
relojes distintos verían horarios distintos para la misma cita.
"""

import os
import sys
import time

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backend.client import CLOCK_SKEW_TOLERANCE_S, BackendClient


def _cliente(respuesta):
    c = BackendClient('http://ejemplo', '/tmp/labsim-test-no-existe.json')
    if isinstance(respuesta, Exception):
        def falla():
            raise respuesta
        c.get_clock = falla
    else:
        c.get_clock = lambda: respuesta
    return c


def test_sin_respuesta_no_se_inventa_un_desfase():
    """Sin conexión no se sabe, y no saber no es "está en hora"."""
    import requests
    assert _cliente(requests.RequestException('sin red')).clock_skew() is None
    # Un servidor que contesta pero sin epoch tampoco sirve.
    assert _cliente({}).clock_skew() is None
    assert _cliente({'zona': 'America/Santiago'}).clock_skew() is None


def test_un_reloj_en_hora_no_molesta():
    """La tolerancia existe: latencia y deriva normal no son un problema."""
    skew = _cliente({'epoch': int(time.time()), 'zona': 'America/Santiago'}).clock_skew()
    assert skew['en_hora'] is True
    assert abs(skew['segundos']) < 5
    assert skew['zona_servidor'] == 'America/Santiago'
    # Y la zona de esta máquina viaja en el resultado, para poder mostrarla.
    assert skew['zona_local']


def test_un_reloj_corrido_se_avisa_con_signo():
    """Adelantado y atrasado son problemas distintos: el signo importa."""
    ahora = time.time()
    adelantado = _cliente({'epoch': int(ahora - 600),
                           'zona': 'America/Santiago'}).clock_skew()
    atrasado = _cliente({'epoch': int(ahora + 600),
                         'zona': 'America/Santiago'}).clock_skew()
    assert adelantado['en_hora'] is False
    assert atrasado['en_hora'] is False
    assert adelantado['segundos'] > 0    # la máquina va adelante
    assert atrasado['segundos'] < 0


def test_la_tolerancia_es_de_minutos_y_no_de_horas():
    """Una hora de diferencia mueve una cita entera: no puede pasar.

    Y unos segundos no pueden dar aviso, o el aviso se vuelve ruido y nadie
    lo mira.
    """
    assert 30 <= CLOCK_SKEW_TOLERANCE_S <= 300
    ahora = time.time()
    justo = _cliente({'epoch': int(ahora - CLOCK_SKEW_TOLERANCE_S + 10),
                      'zona': 'America/Santiago'}).clock_skew()
    pasado = _cliente({'epoch': int(ahora - CLOCK_SKEW_TOLERANCE_S - 10),
                       'zona': 'America/Santiago'}).clock_skew()
    assert justo['en_hora'] is True
    assert pasado['en_hora'] is False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
