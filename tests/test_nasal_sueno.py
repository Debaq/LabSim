"""Tests de la poligrafía y la polisomnografía (nasal/sueno.py,
nasal/PolisomnografiaWindow.py).

1. La noche es la del libro: con los perfiles del cap. 38, `resumen` da los
   mismos índices que libro-orl/material/ilustraciones/hacer_cap38.py (si el
   libro está a mano) y los del texto del capítulo.
2. Los índices con la puntuación del alumno: con los eventos verdaderos dan
   el IAH del libro; la regla de 4 % cuenta menos hipopneas; excluir un
   tramo saca sus eventos y sus horas.
3. La puntuación automática se equivoca como un programa: sin EEG no ve
   las hipopneas que solo dan despertar; donde la cánula se soltó ve apneas
   que no existen (y con el tramo excluido desaparecen).
4. El perfil personalizado da una noche con el IAH del orden pedido.
5. La ventana: sin SUENO no registra; montaje, noche, corregir (cambiar,
   borrar, agregar, excluir), índices e informe; al retomar vuelve igual;
   "lo que el equipo no sabe" solo para docente; cada acción a action_logs
   con prefijo psg_.
"""

import importlib.util
import os
import pathlib
import sys
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from nasal import sesion  # noqa: E402
from nasal import sueno as Z  # noqa: E402
from nasal.PolisomnografiaWindow import PolisomnografiaWindow  # noqa: E402

ADMIN = {'permission': 777}
ALUMNO = {'permission': 1}
LIBRO = pathlib.Path.home() / 'Escritorio/Proyectos/libro-orl/material/ilustraciones/hacer_cap38.py'


class ColaFalsa:
    def __init__(self):
        self.eventos = []

    def push(self, accion, payload=None):
        self.eventos.append((accion, payload or {}))

    def de(self, accion):
        return [p for a, p in self.eventos if a == accion]


LOGS = ColaFalsa()
sesion._cola = LOGS


def caso(sueno=None, edad=61, gender=1, id_=903):
    return {'id': id_, 'edad': edad, 'gender': gender, 'SUENO': sueno or {'perfil': 'grave'}}


def cerca(a, b, tol):
    assert abs(a - b) <= tol, (a, b, tol)


# --- 1 -----------------------------------------------------------------------

def test_noche_del_libro():
    # Las cifras del texto del cap. 38 (grave: PSG; dudosa: PSG con su PG previa).
    grave = Z.resumen(Z.noche(Z.normaliza({'perfil': 'grave'}), 'psg'), 'psg')
    cerca(grave['IAH'], 55.5, 0.05)
    dudosa = Z.resumen(Z.noche(Z.normaliza({'perfil': 'dudosa'}), 'psg'), 'psg')
    cerca(dudosa['IAH'], 20.8, 0.05)
    if not LIBRO.exists():
        print('    (sin libro-orl: no se compara con el script)')
        return
    spec = importlib.util.spec_from_file_location('hacer_cap38', LIBRO)
    libro = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(libro)
    for clave in ('roncador', 'moderado', 'grave', 'dudosa', 'dudosa_pg'):
        for modo in ('psg', 'pg'):
            a = libro.resumen(libro.simular(clave), modo)
            b = Z.resumen(Z.simular(clave), modo)
            assert a == b, (clave, modo)


# --- 2 -----------------------------------------------------------------------

def test_indices_con_la_puntuacion():
    S = Z.noche(Z.normaliza({'perfil': 'grave'}), 'psg')
    verdad = [dict(e) for e in S['ev']]
    r = Z.indices(S, verdad)
    R = Z.resumen(S, 'psg')
    cerca(r['IAH'], R['IAH'], 0.01)
    cerca(r['TST'], R['TST'], 0.01)
    assert Z.indices(S, verdad, regla='4')['IAH'] < r['IAH']
    # Excluir la primera mitad de la noche saca eventos y horas.
    mitad = S['N'] // 2
    rx = Z.indices(S, verdad, excluidos=[(0, mitad)])
    assert rx['horas'] < r['horas'] * 0.7
    assert sum(rx['n'].values()) < sum(r['n'].values())
    assert Z.gravedad_clave(r['IAH']) == 'grave' and Z.gravedad_clave(4.9) == 'normal'


# --- 3 -----------------------------------------------------------------------

def test_puntuacion_automatica():
    S = Z.noche(Z.normaliza({'perfil': 'dudosa'}), 'psg')
    con = Z.auto_puntuar(S, Z.sensores_del_estudio('psg'), 's')
    sin_eeg = Z.auto_puntuar(S, [k for k in Z.sensores_del_estudio('psg') if k != 'eeg'], 's')
    assert len(sin_eeg) < 0.5 * len(con)          # 38.4: casi todas son hipopneas con despertar
    assert not Z.auto_puntuar(S, ['torax', 'abd', 'spo2'], 's')
    # La cánula suelta en la casa: apneas falsas que se van al excluir.
    b = Z.normaliza({'perfil': 'roncador', 'canula_suelta': {'desde': 120, 'hasta': 240}})
    S = Z.noche(b, 'pg')
    auto = Z.auto_puntuar(S, Z.sensores_del_estudio('pg'), 's')
    falsos = [e for e in auto if e.get('falso')]
    assert len(falsos) > 50
    r = Z.indices(S, auto)
    rx = Z.indices(S, auto, excluidos=[(120 * 60, 240 * 60)])
    assert r['IAH'] > 15 > rx['IAH'] and rx['min validos'] == r['min registro'] - 120
    # En el laboratorio no se suelta.
    assert Z.noche(b, 'psg')['canula_suelta'] is None


def test_normaliza():
    for malo in ({}, {'perfil': 'otro'}, {'perfil': 'personalizado', 'params': {'tasa': 500}},
                 {'perfil': 'grave', 'canula_suelta': {'desde': 100, 'hasta': 50}}):
        try:
            Z.normaliza(malo)
        except ValueError:
            continue
        raise AssertionError(malo)
    assert Z.desde_caso({'SUENO': {'perfil': 'x'}}) == Z.desde_caso({})


# --- 4 -----------------------------------------------------------------------

def test_perfil_personalizado():
    for tasa, lo, hi in ((3, 0, 8), (25, 15, 45), (70, 45, 120)):
        b = Z.normaliza({'perfil': 'personalizado', 'params': {'tasa': tasa, 'semilla': 7}})
        R = Z.resumen(Z.noche(b, 'psg'), 'psg')
        assert lo <= R['IAH'] <= hi, (tasa, R['IAH'])


# --- 5 -----------------------------------------------------------------------

def ventana(data=None, login=ADMIN, cita=4545):
    w = PolisomnografiaWindow(data_login=login)
    w.la_super(data if data is not None else caso(), cita)
    return w


def esperar(cond, limite=20):
    from PySide6.QtWidgets import QApplication
    fin = time.time() + limite
    while time.time() < fin:
        QApplication.processEvents()
        if cond():
            return
        time.sleep(0.02)
    raise AssertionError('no terminó a tiempo')


def montar(w, estudio='psg', sin=()):
    w.cmb_estudio.setCurrentIndex(w.cmb_estudio.findData(estudio))
    for k in Z.sensores_del_estudio(estudio):
        if k not in sin:
            w.chk_sensor[k].click()
    w._registrar()
    esperar(lambda: w.S is not None)
    if estudio == 'psg':
        # La noche corre en el laboratorio: se adelanta hasta la mañana.
        assert w._en_vivo() and w.eventos == []
        w._manana()
    assert w._de_dia()


def test_ventana_sin_sueno_es_normal():
    w = ventana({'id': 1, 'edad': 30, 'gender': 0})
    assert w.btn_registrar.isEnabled() and 'SUENO' not in w.lbl_mensaje.text()


def test_ventana_sueno_mal_escrito_es_normal():
    w = ventana({'id': 1, 'edad': 30, 'gender': 0, 'SUENO': {'perfil': 'x'}})
    assert w.btn_registrar.isEnabled() and 'SUENO' not in w.lbl_mensaje.text()


def test_ventana_flujo_completo():
    LOGS.eventos.clear()
    w = ventana()
    montar(w)
    assert w.S['estudio'] == 'psg' and len(w.eventos) > 100
    iah0 = w._indices()['IAH']
    # Cambiar el tipo de un evento, borrar otro y agregar uno con la selección.
    e = w.eventos[0]
    w._ir_a(e['t'])
    w._clic_detalle(e['t'] + 1)
    assert w.elegido is e
    w._poner_tipo('ac')
    assert e['tipo'] == 'ac' and not e['auto']
    w._clic_detalle(w.eventos[1]['t'] + 1)
    w._borrar()
    assert w._indices()['IAH'] < iah0
    w.elegido = None
    t = w.S['N'] - 600
    w._ir_a(t)
    w.detalle.seleccion.setRegion((w.t0 + 20, w.t0 + 35))
    n_antes = len(w.eventos)
    w._poner_tipo('h')
    assert len(w.eventos) == n_antes + 1 and w.elegido['dur'] == 15
    # Excluir un tramo con la selección de la noche.
    w.chk_sel_noche.setChecked(True)
    w.noche.seleccion.setRegion((1.0, 1.5))
    w._excluir()
    assert w.excluidos == [(3600, 5400)]
    w.cmb_gravedad.setCurrentIndex(w.cmb_gravedad.findData('grave'))
    contenido = w.tabla_informe.contenido
    assert any(f[0].startswith('IAH') for f in contenido['filas'])
    job = w.report_job()
    assert job['tipo'] == 'POLISOMNOGRAFIA' and job['data']['estudio'] == 'psg'
    assert len(job['data']['eventos']) == len(w.eventos) and job['data']['excluidos'] == [[3600, 5400]]
    imagenes = job['images']()
    assert set(imagenes) == {'psg_noche'} and os.path.isfile(imagenes['psg_noche'])
    w2 = ventana()
    assert w2.restore_report(job['data'])
    assert w2.tabla_informe.contenido == contenido and w2.cmb_gravedad.currentData() == 'grave'
    acciones = {a for a, _p in LOGS.eventos}
    for a in ('psg_sensor', 'psg_registrar', 'psg_cambiar', 'psg_borrar', 'psg_agregar', 'psg_excluir',
              'psg_gravedad'):
        assert a in acciones, a
    assert LOGS.de('psg_registrar')[0]['case_id'] == 903
    assert 'IAH' in LOGS.de('psg_registrar')[0]['verdad']


def test_poligrafia_sin_eeg_ni_estadios():
    w = ventana(caso({'perfil': 'moderado'}, edad=52, gender=0))
    montar(w, 'pg')
    assert 'eeg' not in w.montaje and w.S['estudio'] == 'pg'
    assert 'REI' in ' '.join(f[0] for f in w.tabla_informe.contenido['filas'])


def test_montaje_incompleto_se_avisa():
    w = ventana()
    montar(w, sin=('torax', 'abd'))
    assert 'Sin' in w.lbl_avisos.text() and 'banda' in w.lbl_avisos.text().lower()
    w = ventana()
    montar(w, sin=('ron', 'spo2'))
    valores = dict(w.tabla_informe.contenido['filas'])
    assert valores['Ronquido'] == 'sin micrófono' and valores['Tiempo con SpO₂ < 90 %'] == 'sin oxímetro'


def test_verdad_solo_docente():
    w = ventana(login=ALUMNO)
    assert w.verdad is None and w.tabs.count() == 2
    w = ventana()
    montar(w)
    assert 'La noche de verdad' in w.verdad.text()



def test_mismas_listas_que_el_backend():
    """La ficha del caso (CaseForm.php) valida con los mismos perfiles y rangos."""
    import re
    php = open(os.path.join(os.path.dirname(__file__), '..', 'labsim_backend', 'src', 'CaseForm.php'),
               encoding='utf-8').read()
    cuerpo = re.search(r'SUENO_PARAMETROS = \[(.*?)\];', php, re.S).group(1)
    params = {k: tuple(float(x) for x in v.split(','))
              for k, v in re.findall(r"'(\w+)' => \[([\d., ]+)\]", cuerpo)}
    assert params == {k: (float(lo), float(hi), float(d)) for k, lo, hi, d in Z.PARAMETROS}
    cuerpo = re.search(r'SUENO_PERFILES = \[(.*?)\];', php, re.S).group(1)
    perfiles = dict(re.findall(r"'(\w+)' => '([^']*)'", cuerpo))
    assert perfiles == {**dict(Z.PERFILES_LIBRO), 'personalizado': 'Personalizado'}


if __name__ == '__main__':
    for nombre, f in list(globals().items()):
        if nombre.startswith('test_') and callable(f):
            f()
            print(f'  {nombre} OK')
    print('TODOS LOS TESTS PASARON')


# --- El técnico acomoda al paciente (2026-11-16) ------------------------------

def test_sin_acomodos_la_noche_es_la_de_siempre():
    # La pauta del práctico (fichas 159-162) depende de esto.
    for perfil in ('roncador', 'moderado', 'grave', 'dudosa'):
        S = Z.noche(Z.normaliza({'perfil': perfil}), 'psg', [])
        L = Z.simular(perfil)
        assert S['ev'] == L['ev'] and S['seg'] == L['seg'] and S['sp'] == L['sp'] and S['pos'] == L['pos']


def test_acomodar_cambia_desde_ahi_hasta_que_se_da_vuelta_solo():
    bloque = Z.normaliza({'perfil': 'moderado'})
    S = Z.noche(bloque, 'psg')
    t = 150 * 60                       # moderado: de lado derecho de 140 a 210 min
    A = Z.noche(bloque, 'psg', [(t, 'supino')])
    assert S['pos'][t] == 'derecha' and A['pos'][t] == 'supino' and A['pos'][t - 1] == 'derecha'
    assert A['pos'][340 * 60] == 'izquierda'          # su próximo cambio propio sigue igual
    assert A['etapa'][t] == 'W' and A['etapa'][t + Z.VIGILIA_ACOMODO - 1] == 'W'
    assert [x for x in S['ev'] if x['t'] < t] == [x for x in A['ev'] if x['t'] < t]
    ideal = lambda X: [{'t': x['t'], 'dur': x['dur'], 'tipo': x['tipo']} for x in X['ev']]
    assert Z.indices(A, ideal(A))['min supino'] > Z.indices(S, ideal(S))['min supino'] + 40
    assert A['seg'][0] == S['seg'][0] and sum(b - a for _e, a, b in A['seg']) == A['N']
    assert Z.tramos_posicion(A)[1] == (140 * 60, t, 'derecha')
    # En la casa no hay técnico.
    assert Z.noche(bloque, 'pg', [(t, 'supino')])['pos'] == Z.noche(bloque, 'pg')['pos']


def test_ventana_acomodar_en_vivo_y_retomar():
    LOGS.eventos.clear()
    w = ventana(caso({'perfil': 'moderado'}, edad=52, gender=0), login={'permission': 444, 'name': 'a'})
    w.cmb_estudio.setCurrentIndex(w.cmb_estudio.findData('psg'))
    for k in Z.sensores_del_estudio('psg'):
        w.chk_sensor[k].click()
    w._registrar()
    esperar(lambda: w.S is not None)
    assert w._en_vivo() and not w.panel_puntuacion.isEnabled() and w.panel_sala.isVisibleTo(w)
    w._pausa()
    w.t_actual = 150 * 60
    w._ir_a(200 * 60)                                   # el futuro no se mira
    assert w.t0 + w._dur() <= w.t_actual
    w._acomodar('derecha')                              # ya está de lado derecho: nada
    assert not w.S['acomodos']
    w._acomodar('supino')
    esperar(lambda: not w.recalculando)
    assert w.S['acomodos'] == [(150 * 60, 'supino')] and w.S['pos'][150 * 60] == 'supino'
    assert LOGS.de('psg_acomodar')[0]['de'] == 'derecha'
    job = w.report_job()
    assert job['data']['acomodos'] == [[9000, 'supino']] and job['data']['t_actual'] == 9000
    # Retomar a medio correr: en pausa donde iba.
    w2 = ventana(caso({'perfil': 'moderado'}, edad=52, gender=0), login={'permission': 444, 'name': 'a'})
    assert w2.restore_report(job['data']) and w2._en_vivo() and not w2.corriendo
    assert w2.S['pos'] == w.S['pos']
    w._manana()
    assert w._de_dia() and w.eventos and w.panel_puntuacion.isEnabled()
    assert LOGS.de('psg_manana')[0]['acomodos'] == [[9000, 'supino']]
    job = w.report_job()
    assert job['data']['t_actual'] is None
    w3 = ventana(caso({'perfil': 'moderado'}, edad=52, gender=0), login={'permission': 444, 'name': 'a'})
    assert w3.restore_report(job['data']) and w3._de_dia() and w3.S['ev'] == w.S['ev']
    assert w3._indices()['IAH'] == w._indices()['IAH']



def test_la_noche_entera_en_15_minutos():
    from nasal.PolisomnografiaWindow import NOCHE_EN_MIN, TIC_MS
    w = ventana(caso({'perfil': 'moderado'}, edad=52, gender=0))
    w.cmb_estudio.setCurrentIndex(w.cmb_estudio.findData('psg'))
    for k in Z.sensores_del_estudio('psg'):
        w.chk_sensor[k].click()
    w._registrar()
    esperar(lambda: w.S is not None)
    w.timer.stop()
    assert w.cmb_velocidad.currentData() == 0
    tics = NOCHE_EN_MIN * 60 * 1000 / TIC_MS
    cerca(w._velocidad() * TIC_MS / 1000 * tics, w.S['N'], 1)
