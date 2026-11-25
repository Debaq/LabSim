"""El ABR en una estación OSCE (core/osce.py, paso 4 de docs/osce_plan.md).

- Configuración: el alumno encuentra el montaje hecho y TODOS los mandos al
  azar, nunca en el valor de rutina de la prueba.
- Marcaje: la app registra las curvas pedidas con el equipo de rutina; cada
  una lleva su verdad (latencias del generador) y el panel queda quieto.
- La entrega (sesión + panel + verdad) se puede mandar como JSON, y la
  verdad no entra en el informe normal (session_payload).
"""
import json
import os
import random
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim_datos_"))
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(RAIZ)

from test_abr_panel import _caso  # noqa: E402  (crea el QApplication)
from abr.AbrMainWindow import AbrMainWindow  # noqa: E402
from abr.protocols import standard_setup  # noqa: E402

ALUMNO = {'name': 'Estación OSCE', 'user': 'osce', 'permission': 444}


def _estacion(tipo, curvas=(), semilla=1):
    w = AbrMainWindow(dict(ALUMNO))
    w.la_super(_caso(), 'osce-T24-TFJ')
    w.osce_preparar(tipo, 'ABR', list(curvas), random.Random(semilla))
    return w


def test_configuracion_al_azar_y_nunca_de_rutina():
    control, tecnica = standard_setup('ABR')
    for semilla in range(12):
        w = _estacion('config_equipo', semilla=semilla)
        panel = w.control.get_data()
        assert panel['pol'] != control['pol'], panel
        assert panel['stim'] != control['stim'], panel
        assert panel['filter_passhigh'] != control['filter_passhigh'], panel
        assert panel['filter_down'] != control['filter_down'], panel
        assert panel['int'] != control['int'], panel
        assert abs(panel['rate'] - control['rate']) > 0.05, panel
        assert w.technical['transducer'] != 'insert_earphone'
        assert abs(w.technical['window_ms'] - tecnica['window_ms']) >= 0.5
        assert w.control.isEnabled(), "en configuración el panel se usa"
    # Y no siempre lo mismo: es un sorteo
    pols = {_estacion('config_equipo', semilla=s).control.get_data()['stim'] for s in range(8)}
    assert len(pols) > 1


def test_montaje_hecho_al_entrar():
    w = _estacion('config_equipo')
    colocados = w.montaje.colocados
    assert colocados.get('activo') is not None and colocados.get('tierra') is not None, colocados


def test_marcaje_registra_las_curvas_con_su_verdad():
    curvas = [('OD', 80), ('OD', 40), ('OD', 10), ('OI', 80)]
    w = _estacion('marcaje', curvas)
    assert w.curves_R == ['R1', 'R2', 'R3'] and w.curves_L == ['L1'], (w.curves_R, w.curves_L)
    assert set(w.memory) == {'R1', 'R2', 'R3', 'L1'}
    for nombre, (lado, nivel) in zip(['R1', 'R2', 'R3', 'L1'], curvas):
        assert w.memory[nombre]['side'] == lado and w.memory[nombre]['int'] == nivel
        assert w.memory[nombre]['rate'] == 21.1 and w.memory[nombre]['pol'] == 'Alternada'
    v80 = w.verdad_curvas['R1']
    assert v80['visible'] and {'I', 'III', 'V'} <= set(v80['waves']), v80
    assert 5.0 < v80['waves']['V']['lat'] < 6.5, v80
    # A 40 dB la V llega más tarde que a 80
    assert w.verdad_curvas['R2']['waves']['V']['lat'] > v80['waves']['V']['lat']
    assert not w.control.isEnabled(), "en marcaje no se registra"
    assert w.state_capture != 'record'


def test_entrega_serializable_y_verdad_solo_en_la_entrega():
    w = _estacion('marcaje', [('OD', 80), ('OI', 80)])
    entrega = w.osce_entrega()
    texto = json.dumps(entrega)
    vuelta = json.loads(texto)
    assert set(vuelta['verdad']) == {'R1', 'L1'}
    assert vuelta['panel']['side'] in ('OD', 'OI')
    assert 'R1' in vuelta['abr']['curvas']
    assert 'verdad' not in json.dumps(w.session_payload()), "la verdad no va en el informe"


def test_curvas_en_orden_con_marcas_y_tecnica():
    w = _estacion('marcaje', [('OD', 80), ('OI', 60)])
    v = w.verdad_curvas['R1']['waves']['V']['lat']
    w.update_memory_from_graph_mark({'R1': {'V': [v, 0.4]}})
    curvas = w.osce_entrega()['curvas']
    assert [(c['nombre'], c['side'], c['int']) for c in curvas] == [('R1', 'OD', 80), ('L1', 'OI', 60)]
    assert curvas[0]['marcas']['V'] == v and curvas[0]['marcas']['I'] is None
    assert curvas[0]['window_ms'] == 12.0 and curvas[0]['rate'] == 21.1
    assert curvas[0]['transducer'] == 'insert_earphone'


def test_protocolo_parte_al_azar_y_se_registra():
    w = _estacion('protocolo')
    assert w.control.isEnabled()
    assert w.control.get_data()['pol'] != 'Alternada'


def test_alumno_nuevo_borra_lo_del_anterior():
    w = _estacion('marcaje', [('OD', 80)])
    w.la_super(None, None)
    assert w.memory == {} and w.verdad_curvas == {}
    w.la_super(_caso(), 'osce-OTRO-111')
    w.osce_preparar('config_equipo', 'ABR', [], random.Random(3))
    assert w.memory == {} and w.control.isEnabled()


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK", flush=True)
    print("TODOS LOS TESTS PASARON", flush=True)
    sys.stdout.flush()
    os._exit(0)   # el apagado de Qt con pyqtgraph se cae (ver tests/conftest.py)
