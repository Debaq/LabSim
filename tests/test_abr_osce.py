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


def test_en_la_estacion_la_curva_sale_al_instante():
    """Iniciar no anima el promediado: la curva queda entera y el equipo
    vuelve a "Iniciar" en la misma llamada."""
    w = _estacion('protocolo')
    control, _ = standard_setup('ABR')
    w.control.set_data(dict(control, side='OD', int=80))
    w.control.start_capture()
    assert w.state_capture != 'record' and not w.capture_timer.isActive()
    assert list(w.memory) == ['R1'] and w.graph_r.data['R1']['done']
    assert w.memory['R1']['average'] == 2000
    assert w.verdad_curvas['R1']['visible']


def _caso_completo():
    """Caso con ECochG y bloque Central: sirve para todas las pruebas del ABR."""
    oido = {'umbral': 15, 'type': 'normal', 'repro': True, 'repro_var': 0.3, 'desviaciones': {},
            'fsp_puntos': {'800': 2.3, '2000': 2.8}, 'average_objetivo': 1500, 'ecochg': {'sp_ap': 0.45}}
    return {'edad': 30, 'gender': 1, 'ABR': {'OD': dict(oido), 'OI': dict(oido)},
            'Central': {'estado': 'despierto'}}


def _marcaje(prueba, curvas):
    w = AbrMainWindow(dict(ALUMNO))
    w.la_super(_caso_completo(), 'osce-X')
    w.osce_preparar('marcaje', prueba, list(curvas), random.Random(1))
    return w


def test_marcaje_ecochg_trae_ps_y_pa():
    w = _marcaje('ECochG', [('OD', 90)])
    v = w.verdad_curvas['R1']
    assert v['visible'] and set(v['waves']) == {'PS', 'PA'}, v
    assert v['waves']['PS']['lat'] < v['waves']['PA']['lat'] < 3.0, v
    w.ecochg_mark_changed({'R1': {'PA': [v['waves']['PA']['lat'], -1.0]}})
    c = w.osce_entrega()['curvas'][0]
    assert c['test'] == 'ECochG' and abs(c['marcas']['PA'] - v['waves']['PA']['lat']) < 1e-6, c


def test_marcaje_corticales_traen_sus_componentes():
    esperado = {'MLR': ('Cz', {'Na', 'Pa'}), 'CAEP': ('Cz', {'P1', 'N1', 'P2'}),
                'P300': ('Pz', {'P3'}), 'MMN': ('Fz', {'MMN'})}
    for prueba, (canal, comps) in esperado.items():
        w = _marcaje(prueba, [('OD', 70)])
        v = w.verdad_curvas.get(f'R1.{canal}')
        assert v is not None and v['visible'], (prueba, w.verdad_curvas.keys())
        assert comps <= set(v['waves']), (prueba, v['waves'].keys())
        if prueba == 'MLR':
            assert v['waves']['Na']['amp'] < 0 and abs(v['waves']['Na']['amp']) < 0.5, v['waves']['Na']
        curvas = {c['nombre']: c for c in w.osce_entrega()['curvas']}
        assert curvas[f'R1.{canal}']['canal'] == canal and curvas[f'R1.{canal}']['test'] == prueba


def test_configuracion_p300_sortea_el_oddball():
    for semilla in range(4):
        w = AbrMainWindow(dict(ALUMNO))
        w.la_super(_caso_completo(), 'osce-X')
        w.osce_preparar('config_equipo', 'P300', [], random.Random(semilla))
        e = w.osce_entrega()
        assert e['panel']['test'] == 'P300' and e['panel'].get('tarea') not in (None, 'contar'), e['panel']
        assert e['equipo']['oddball_rare'] != 'Burst 2 kHz' and e['equipo']['oddball_pct'] != 20.0, e['equipo']


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
