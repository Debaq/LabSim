"""Tests de la rinoscopía (nasal/rinoscopia.py y nasal/RinoscopiaWindow.py).

1. El dibujo: imagen del tamaño pedido, la misma cada vez, y la fosa
   izquierda es la derecha en espejo cuando las dos fosas son iguales.
2. Lo que hay sale de la nariz del caso: desviación, espolón, cornete
   congestionado que el vasoconstrictor achica, pólipos, perforación, y el
   aspecto de la mucosa del bloque `rinoscopia`.
3. El módulo: sin NASAL no mira; con NASAL dibuja (fuera de la ventana),
   anota en qué orden y posiciones miró el alumno, y el informe lleva lo
   marcado y la técnica. Retomar devuelve lo informado.
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


def test_hallazgos_del_caso():
    def h(cuadro, lado='D', estado=None, nasal=None):
        p = modelo.paciente(cuadro)
        return rinoscopia.hallazgos(p, nasal, lado, estado or {'minuto': 0})
    assert h('normal')['tabique'] == 'centrado'
    assert h('desviacion_derecha')['tabique'] == 'desviado'
    assert h('desviacion_derecha', 'I')['tabique'] == 'centrado'
    p = modelo.paciente('desviacion_derecha')
    p['lados']['D']['desviacion']['ancho'] = 0.3
    assert rinoscopia.hallazgos(p, None, 'D', {})['tabique'] == 'espolon'
    assert h('cornetes')['cornete_inferior'] in ('hipertrofico', 'contacta')
    assert h('cornetes', estado={'vc': True})['cornete_inferior'] == 'normal'
    assert h('polipos')['polipos'] and not h('normal')['polipos']
    assert h('perforacion')['perforacion']
    nasal = {'rinoscopia': {'D': {'mucosa': 'palida', 'secrecion': 'acuosa'}, 'I': {'mucosa': 'verde'}}}
    assert h('normal', nasal=nasal)['mucosa'] == 'palida'
    assert h('normal', 'I', nasal=nasal)['mucosa'] == 'rosada'


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
    assert not w.btn_lado['D'].isEnabled()
    assert w.report_job() is None


def test_modulo_mira_e_informa():
    sesion._actual = None
    data = caso('desviacion_derecha')
    w = RW.RinoscopiaWindow(data_login=ADMIN)
    w.la_super(data, '42')
    esperar(w)
    assert ('D', 0, False) in w.imagenes and ('I', 60, False) in w.imagenes
    assert w.report_job() is None          # todavía no miró nada
    w._elegir(grados=30)
    w._elegir(grados=60)
    w._elegir(lado='I', grados=0)
    esperar(w)
    w.paneles['D'].combos['tabique'].setCurrentIndex(w.paneles['D'].combos['tabique'].findData('desviado'))
    w.paneles['D'].chk_perforacion.setChecked(False)
    w.txt_conclusion.setPlainText('Desviación septal derecha.')
    job = w.report_job()
    assert job['tipo'] == 'RINOSCOPIA' and job['appointment_id'] == 42
    d = job['data']
    assert d['D']['tabique'] == 'desviado'
    t = d['tecnica']
    assert t['primera_fosa'] == 'D'
    assert t['posiciones'] == {'D': [30, 60], 'I': [0]}   # la recta de entrada no la eligió él
    assert not t['tres_posiciones']['D']
    w._elegir(lado='D', grados=0)
    assert w.tecnica()['tres_posiciones']['D']
    assert 'Desviado' in w.lbl_verdad.text()

    sesion._actual = None
    otra = RW.RinoscopiaWindow(data_login=ADMIN)
    otra.la_super(data, '42')
    assert otra.restore_report(w.report_job()['data'])
    assert otra.paneles['D'].combos['tabique'].currentData() == 'desviado'
    assert otra.tecnica() == w.tecnica()
    assert not otra.restore_report(d)    # ya tiene algo: no pisa
    esperar(otra)


def test_cache_en_el_equipo():
    sesion._actual = None
    w = RW.RinoscopiaWindow(data_login=ADMIN)
    w.la_super(caso('mixta'), '7')
    esperar(w)
    antes = len(os.listdir(_cache))
    assert antes >= 6
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
