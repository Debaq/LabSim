"""La noche del PSG que llega sola al final enciende la luz (ticket #65).

_tic dejaba t_actual en el final antes de llamar a _manana, y _manana (que
solo actúa con la noche en vivo) salía sin hacer nada: sin puntuación
automática, sin resultados y con "La noche corre…" en pantalla.
"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
RAIZ = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(RAIZ, 'src'))
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(RAIZ)

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from nasal import sueno as Z  # noqa: E402
import test_nasal_sueno as T  # noqa: E402


def _noche_corriendo():
    w = T.ventana(T.caso({'perfil': 'moderado'}, edad=52, gender=0))
    w.cmb_estudio.setCurrentIndex(w.cmb_estudio.findData('psg'))
    for k in Z.sensores_del_estudio('psg'):
        w.chk_sensor[k].click()
    w._registrar()
    T.esperar(lambda: w.S is not None)
    assert w._en_vivo() and w.corriendo
    return w


def test_la_noche_que_termina_sola_trae_la_puntuacion():
    w = _noche_corriendo()
    w.timer.stop()
    logs = []
    w._log = lambda accion, **p: logs.append((accion, p))
    w.t_actual = w.S['N'] - 0.1   # al último tic (aun en tiempo real)
    w._tic()
    assert w._de_dia() and not w.corriendo and not w.timer.isActive()
    assert w.eventos, 'sin puntuación automática al encender la luz'
    assert w.panel_puntuacion.isEnabled()
    assert w.tabla_informe.rowCount() > 0
    assert 'corriendo' not in w.lbl_avisos.text()
    manana = [p for a, p in logs if a == 'manana']
    assert len(manana) == 1 and manana[0]['adelantada'] is False


def test_hasta_la_manana_sigue_marcando_adelantada():
    w = _noche_corriendo()
    w.timer.stop()
    logs = []
    w._log = lambda accion, **p: logs.append((accion, p))
    w.btn_manana.click()
    assert w._de_dia() and w.eventos
    assert [p['adelantada'] for a, p in logs if a == 'manana'] == [True]


if __name__ == '__main__':
    for nombre, fn in list(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            fn()
            print(f'  {nombre} OK', flush=True)
    print('TODOS LOS TESTS PASARON', flush=True)
    os._exit(0)
