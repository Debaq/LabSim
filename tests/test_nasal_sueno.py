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
    assert Z.desde_caso({'SUENO': {'perfil': 'x'}}) is None


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


def test_ventana_sin_sueno_no_registra():
    w = ventana({'id': 1, 'edad': 30, 'gender': 0})
    assert not w.btn_registrar.isEnabled() and 'SUENO' in w.lbl_mensaje.text()


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
