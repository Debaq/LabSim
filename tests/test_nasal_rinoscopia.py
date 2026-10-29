"""Tests de la rinoscopía (nasal/rinoscopia.py y nasal/RinoscopiaWindow.py).

1. El dibujo: imagen del tamaño pedido, la misma cada vez, y la fosa
   izquierda es la derecha en espejo cuando las dos fosas son iguales.
2. La fosa sale de la nariz del caso: desviación (y la concavidad del otro
   lado), cornete congestionado que el vasoconstrictor achica, pólipos,
   perforación, y el aspecto de la mucosa del bloque `rinoscopia`.
3. El módulo: sin NASAL no mira; con NASAL dibuja (fuera de la ventana);
   "reclinar" mueve la cabeza de a 2° entre 0° y 60° y el interior usa el
   cálculo más cercano; una posición cuenta como mirada cuando el espéculo
   (el mouse) pasa por la narina; el mouse sobre cada narina elige su fosa;
   el informe lleva lo marcado y la técnica. Retomar devuelve lo informado.
"""

import os
import shutil
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import numpy as np  # noqa: E402
from PySide6.QtCore import QPointF  # noqa: E402

from core.base import context  # noqa: E402
from nasal import RinoscopiaWindow as RW  # noqa: E402
from nasal import modelo, rinoscopia, sesion  # noqa: E402

ADMIN = {'permission': 777}
RW.TAM = 72   # chico: las pruebas no necesitan ver
_cache = tempfile.mkdtemp(prefix='rinoscopia_')
RW._carpeta_cache = lambda: _cache


def caso(cuadro='normal', **extra):
    nasal = dict(modelo.paciente(cuadro), **extra)
    return {'NASAL': nasal, 'edad': 40, 'paciente_snapshot': {'nombre': 'Ana', 'apellido': 'Pérez'}}


def esperar(w):
    for _ in range(4000):
        context.app.processEvents()
        if w.calculando is None and not w.cola:
            break
        if w.tarea is not None:
            w.tarea.esperar(10)
    context.app.processEvents()


def test_dibujo():
    p = modelo.paciente('normal')
    f = rinoscopia.Fosa(p, 'D', {'minuto': 0})
    a = rinoscopia.render(f, 0, 64)
    assert a.shape == (64, 64, 3) and a.dtype == np.uint8
    assert np.array_equal(a, rinoscopia.render(f, 0, 64))
    assert np.array_equal(rinoscopia.render(f, 0, 64, espejo=True), a[:, ::-1])
    assert not np.array_equal(a, rinoscopia.render(f, 60, 64))   # la cabeza cambia la vista


def test_la_fosa_sale_del_caso():
    p = modelo.paciente('desviacion_derecha')
    d = rinoscopia.Fosa(p, 'D', {})
    i = rinoscopia.Fosa(p, 'I', {})
    assert d.dev['B'] > 0 and i.dev['B'] == 0          # el tabique se va a la derecha
    assert i.concavo['B'] > 0                           # y del otro lado queda cóncavo
    assert rinoscopia.Fosa(modelo.paciente('polipos'), 'D', {}).pol
    assert rinoscopia.Fosa(modelo.paciente('perforacion'), 'D', {}).perf is not None
    nasal = {'rinoscopia': {'D': {'mucosa': 'palida', 'secrecion': 'acuosa'}, 'I': {'mucosa': 'verde'}}}
    assert rinoscopia.aspecto(nasal, 'D') == {'mucosa': 'palida', 'secrecion': 'acuosa'}
    assert rinoscopia.aspecto(nasal, 'I')['mucosa'] == 'rosada'
    assert rinoscopia.aspecto(None, 'D') == rinoscopia.ASPECTO_NORMAL


def test_vasoconstrictor_achica_el_cornete():
    p = modelo.paciente('cornetes')
    con = rinoscopia.Fosa(p, 'D', {'minuto': 0})
    sin = rinoscopia.Fosa(p, 'D', {'vc': True})
    assert sin.r_ci < con.r_ci
    # Más fondo oscuro (pasillo libre) con el cornete retraído.
    fondo = (np.clip(rinoscopia.FONDO, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
    oscuro = lambda a: int((a == fondo).all(-1).sum())
    assert oscuro(rinoscopia.render(sin, 0, 80)) > oscuro(rinoscopia.render(con, 0, 80))


def test_modulo_sin_nariz():
    sesion._actual = None
    w = RW.RinoscopiaWindow(data_login=ADMIN)
    w.la_super({'edad': 30}, '1')
    assert not w.btn_atras.isEnabled() and not w.cara.activa
    assert w.report_job() is None


def test_modulo_mira_e_informa():
    sesion._actual = None
    data = caso('desviacion_derecha')
    w = RW.RinoscopiaWindow(data_login=ADMIN)
    w.la_super(data, '42')
    esperar(w)
    assert ('D', 0, False) in w.imagenes and ('I', 60, False) in w.imagenes and ('D', 10, False) in w.imagenes
    assert w.report_job() is None          # todavía no miró nada
    for _ in range(15):          # mantener apretado "reclinar": de a 2°
        w._reclinar(+2)
    assert w.grados == 30 and w.cara.grados == 30 and w.angulo() == 30
    w._miro('D')
    for _ in range(20):
        w._reclinar(+2)
    assert w.grados == 60            # no pasa de 60
    w._miro('D')
    w._reclinar(-2)
    assert w.angulo() == 60          # 58° muestra el cálculo de 60°
    for _ in range(40):
        w._reclinar(-2)
    assert w.grados == 0
    w._miro('I')
    esperar(w)
    assert w.cara.interior['D'] is not None
    w.paneles['D'].combos['tabique'].setCurrentIndex(w.paneles['D'].combos['tabique'].findData('desviado'))
    w.txt_conclusion.setPlainText('Desviación septal derecha.')
    job = w.report_job()
    assert job['tipo'] == 'RINOSCOPIA' and job['appointment_id'] == 42
    d = job['data']
    assert d['D']['tabique'] == 'desviado'
    t = d['tecnica']
    assert t['primera_fosa'] == 'D'
    assert t['posiciones'] == {'D': [30, 60], 'I': [0]}
    assert not t['tres_posiciones']['D']
    w._miro('D')
    assert w.tecnica()['tres_posiciones']['D']

    sesion._actual = None
    otra = RW.RinoscopiaWindow(data_login=ADMIN)
    otra.la_super(data, '42')
    assert otra.restore_report(w.report_job()['data'])
    assert otra.paneles['D'].combos['tabique'].currentData() == 'desviado'
    assert otra.tecnica() == w.tecnica()
    assert not otra.restore_report(d)    # ya tiene algo: no pisa
    esperar(otra)


def test_narinas_eligen_la_fosa():
    sesion._actual = None
    w = RW.RinoscopiaWindow(data_login=ADMIN)
    w.resize(900, 700)
    w.la_super(caso('normal'), '3')
    for grados in (0, 30, 60):
        w.grados = grados
        w.cara.set_grados(grados)
        narinas, k = w.cara._narinas()
        assert w.cara.fosa_bajo(narinas['D']) == 'D'
        assert w.cara.fosa_bajo(narinas['I']) == 'I'
        assert narinas['D'].x() < narinas['I'].x()      # la derecha del paciente, a mi izquierda
        lejos = narinas['D'] + QPointF(0, 60 * k)
        assert w.cara.fosa_bajo(lejos) is None
    esperar(w)


def test_cache_en_el_equipo():
    sesion._actual = None
    w = RW.RinoscopiaWindow(data_login=ADMIN)
    w.la_super(caso('mixta'), '7')
    esperar(w)
    antes = len(os.listdir(_cache))
    assert antes >= 14
    sesion._actual = None
    w2 = RW.RinoscopiaWindow(data_login=ADMIN)
    w2.la_super(caso('mixta'), '7')
    esperar(w2)
    assert len(os.listdir(_cache)) == antes   # no recalculó: las leyó


if __name__ == '__main__':
    fallas = 0
    try:
        for nombre, fn in list(globals().items()):
            if nombre.startswith('test_') and callable(fn):
                try:
                    fn()
                    print(f'  {nombre} OK')
                except Exception as exc:  # noqa: BLE001
                    fallas += 1
                    print(f'  {nombre} FALLA: {exc!r}')
    finally:
        shutil.rmtree(_cache, ignore_errors=True)
    print('TODOS LOS TESTS PASARON' if not fallas else f'{fallas} FALLARON')
    sys.stdout.flush()
    os._exit(1 if fallas else 0)
