"""Tests de la olfatometría (nasal/olfatometria.py, nasal/OlfatometriaWindow.py).

1. La escalera de la hoja sigue la regla de H28 (hacer_h28): cuenta las
   inversiones como cambios de dirección y promedia las últimas cuatro.
2. Un alumno que sigue la regla obtiene en promedio el T del caso (±0,6;
   la escalera aprieta un poco hacia el medio); D e I dan en promedio los
   aciertos del caso, y un anósmico saca el azar (~5 y 4 de 16).
3. Lo que el alumno hace mal cambia la respuesta: sin venda acierta lo que
   no huele; presentando seguido se adapta; sin preparar huele menos; el
   que exagera saca bajo el azar.
4. Normas: categoría por los cortes y percentil 10 por edad.
5. La ventana: sin OLFATO no mide; el «no huelo nada» pide elección
   forzada; la hoja cuenta; el informe sube y vuelve igual al retomar;
   "lo que el equipo no sabe" solo para docente; cada acción a
   action_logs con prefijo olf_.
"""

import os
import random
import statistics
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from nasal import olfatometria as O  # noqa: E402
from nasal import sesion  # noqa: E402
from nasal.OlfatometriaWindow import OlfatometriaWindow  # noqa: E402

ADMIN = {'permission': 777}
ALUMNO = {'permission': 1}


def bloque(T=8, D=12, I=13, TI=None, conducta='buena', preparacion='ok'):
    izq = {'T': T if TI is None else TI, 'D': D, 'I': I}
    return {'lados': {'D': {'T': T, 'D': D, 'I': I}, 'I': izq},
            'conducta': conducta, 'preparacion': preparacion}


class ColaFalsa:
    def __init__(self):
        self.eventos = []

    def push(self, accion, payload=None):
        self.eventos.append((accion, payload or {}))

    def de(self, accion):
        return [p for a, p in self.eventos if a == accion]


LOGS = ColaFalsa()
sesion._cola = LOGS


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def caso(olfato=None, edad=34, gender=1, id_=901):
    return {'id': id_, 'edad': edad, 'gender': gender, 'OLFATO': olfato or bloque()}


def escalera_alumno(olf, semilla, narina='ambas', **kw):
    """Un alumno que sigue la regla hasta la séptima inversión."""
    ens = []
    while not O.terminada(ens) and len(ens) < 80:
        paso = O.escalera(ens)['siguiente']
        c = random.Random(f'{semilla}/{len(ens)}/c').randrange(3)
        r = O.responder(olf, 'T', narina, paso=paso, correcta=c, n_opciones=3,
                        semilla=f'{semilla}/{len(ens)}', **kw)
        ens.append((paso, r['eleccion'] == c))
    return ens


# --- 1 -----------------------------------------------------------------------

def test_escalera_de_la_figura():
    # La regla de la hoja aplicada a una secuencia escrita a mano: sube
    # desde 16 con errores, dos aciertos en 5 (inversión), etc.
    ens = [(p, False) for p in range(16, 5, -1)] + [(5, True), (5, True), (6, False),
                                                     (5, True), (5, True), (6, True), (6, True),
                                                     (7, False), (6, False), (5, True), (5, True),
                                                     (6, False), (5, False), (4, True), (4, True)]
    info = O.escalera(ens)
    pasos_inv = [ens[i][0] for i in info['inversiones']]
    # Dos aciertos en 6 después de diluir no son inversión; un error en 6
    # mientras se sigue concentrando, tampoco.
    assert pasos_inv == [5, 6, 5, 7, 5, 6, 4], pasos_inv
    assert O.umbral_regla(ens) == (7 + 5 + 6 + 4) / 4
    assert O.terminada(ens)
    assert O.umbral_regla(ens[:12]) is None


# --- 2 -----------------------------------------------------------------------

def test_escalera_bien_hecha_da_el_T_del_caso():
    for T, tol in ((6, 0.8), (8, 0.6), (12, 0.6), (15, 0.7)):
        olf = O.normaliza(bloque(T=T))
        ts = [O.umbral_regla(escalera_alumno(olf, f's{T}/{s}')) for s in range(300)]
        assert abs(statistics.mean(ts) - T) <= tol, (T, statistics.mean(ts))


def test_anosmico_saca_el_azar():
    olf = O.normaliza(bloque(T=1, D=0, I=0))
    d = [sum(O.responder(olf, 'D', 'ambas', correcta=i % 3, n_opciones=3, semilla=f'd{s}/{i}')['eleccion'] == i % 3
             for i in range(16)) for s in range(300)]
    i_ = [sum(O.responder(olf, 'I', 'ambas', correcta=i % 4, n_opciones=4, semilla=f'i{s}/{i}')['eleccion'] == i % 4
              for i in range(16)) for s in range(300)]
    assert 4.7 < statistics.mean(d) < 6.0 and 3.4 < statistics.mean(i_) < 4.6
    ts = [O.umbral_regla(escalera_alumno(olf, f'a{s}')) for s in range(150)]
    assert statistics.mean(ts) < 5        # "un puntaje bajo no es cero"


def test_D_e_I_dan_los_aciertos_del_caso():
    olf = O.normaliza(bloque(D=12, I=10))
    for prueba, n_op, esperado in (('D', 3, 12), ('I', 4, 10)):
        xs = [sum(O.responder(olf, prueba, 'ambas', correcta=i % n_op, n_opciones=n_op,
                              semilla=f'{prueba}{s}/{i}')['eleccion'] == i % n_op for i in range(16))
              for s in range(300)]
        assert abs(statistics.mean(xs) - esperado) < 0.5


def test_con_las_dos_narinas_huele_el_mejor_lado():
    olf = O.normaliza({'lados': {'D': {'T': 4, 'D': 9, 'I': 13}, 'I': {'T': 9, 'D': 12, 'I': 8}}})
    assert O.verdad_binasal(olf) == {'T': 9, 'D': 12, 'I': 13}
    assert O.capacidad(olf, 'D')['T'] == 4


# --- 3 -----------------------------------------------------------------------

def test_errores_del_alumno():
    olf = O.normaliza(bloque(T=3, D=6))
    # Sin venda en la discriminación ve el bolígrafo distinto.
    con = sum(O.responder(olf, 'D', 'ambas', correcta=1, n_opciones=3, semilla=f'v{s}')['eleccion'] == 1
              for s in range(400)) / 400
    sin = sum(O.responder(olf, 'D', 'ambas', correcta=1, n_opciones=3, semilla=f'v{s}', venda=False)['eleccion'] == 1
              for s in range(400)) / 400
    assert sin > 0.9 > 0.6 > con
    # Presentando seguido se adapta; sin preparar huele menos.
    p = O.responder(olf, 'T', 'ambas', paso=3, correcta=0, n_opciones=3, semilla='x')['p']
    p_seguido = O.responder(olf, 'T', 'ambas', paso=3, correcta=0, n_opciones=3, semilla='x', dt=3)['p']
    p_fumo = O.responder(olf, 'T', 'ambas', paso=3, correcta=0, n_opciones=3, semilla='x', preparado=False)['p']
    assert p_seguido < p and p_fumo < p
    # El que exagera saca bajo el azar en la identificación.
    exag = O.normaliza(bloque(I=15, conducta='exagera'))
    xs = [sum(O.responder(exag, 'I', 'ambas', correcta=i % 4, n_opciones=4, semilla=f'e{s}/{i}')['eleccion'] == i % 4
              for i in range(16)) for s in range(200)]
    assert statistics.mean(xs) < 4


# --- 4 -----------------------------------------------------------------------

def test_normas_y_categorias():
    assert O.categoria(16) == 'anosmia' and O.categoria(16.25) == 'hiposmia'
    assert O.categoria(30.5) == 'hiposmia' and O.categoria(30.75) == 'normosmia'
    assert O.categoria(41.5) == 'superior'
    assert O.p10(34) == 30.5 and O.p10(78) == 19.2 and O.p10(90) == 13.0 and O.p10(4) is None


def test_normaliza_rechaza_lo_que_no_sirve():
    for malo in ({}, {'lados': {'D': {'T': 0, 'D': 1, 'I': 1}, 'I': {'T': 5, 'D': 1, 'I': 1}}},
                 {'lados': {'D': {'T': 5, 'D': 17, 'I': 1}, 'I': {'T': 5, 'D': 1, 'I': 1}}}):
        try:
            O.normaliza(malo)
        except ValueError:
            continue
        raise AssertionError(malo)
    assert O.desde_caso({'edad': 30, 'OLFATO': {'lados': 'x'}}) is None


# --- 5 -----------------------------------------------------------------------

def ventana(data=None, login=ADMIN, cita=4343):
    reloj = Reloj()
    w = OlfatometriaWindow(data_login=login, reloj=reloj)
    w.la_super(data if data is not None else caso(), cita)
    return w, reloj


def presentar(w, reloj, paso=None):
    reloj.t += 25
    if paso is not None:
        w.spin_paso.setValue(paso)
    w._presentar()
    if w.pendiente is not None:
        w._elegir_igual()
    return w.ensayos[-1]


def test_ventana_sin_olfato_no_mide():
    w, _r = ventana({'id': 1, 'edad': 30, 'gender': 0})
    assert not w.btn_presentar.isEnabled() and not w.panel_paciente.isEnabled()
    assert 'OLFATO' in w.lbl_mensaje.text()


def test_ventana_bateria_completa_e_informe():
    LOGS.eventos.clear()
    w, reloj = ventana()
    w._preguntar()
    w._venda()
    # Umbral siguiendo la regla.
    while not O.terminada(w._escalera_de('ambas')):
        presentar(w, reloj, O.escalera(w._escalera_de('ambas'))['siguiente'])
    t_regla = O.umbral_regla(w._escalera_de('ambas'))
    # Discriminación y, sin venda, identificación.
    w.cmb_prueba.setCurrentIndex(1)
    for _ in range(16):
        presentar(w, reloj)
    w._venda()
    w.cmb_prueba.setCurrentIndex(2)
    for _ in range(16):
        presentar(w, reloj)
    w._presentar()          # el 17.º no existe
    assert sum(e['prueba'] == 'I' for e in w.ensayos) == 16
    w.spin_t['ambas'].setValue(t_regla)
    p = w._puntajes()['ambas']
    assert p['T'] == t_regla and p['D'] is not None and p['I'] is not None
    assert p['TDI'] == p['T'] + p['D'] + p['I']
    w.cmb_categoria.setCurrentIndex(w.cmb_categoria.findData(O.categoria(p['TDI'])))
    contenido = w.tabla_informe.contenido
    assert contenido['filas'][0][0] == 'Ambas narinas'
    job = w.report_job()
    assert job['tipo'] == 'OLFATOMETRIA' and len(job['data']['ensayos']) == len(w.ensayos)
    assert job['data']['p10'] == 30.5 and job['data']['grupo_edad'] == '31–40'
    assert job['data']['preparacion']['pregunto']
    assert all('verdad' not in e for e in job['data']['ensayos'])
    imagenes = job['images']()
    assert set(imagenes) == {'olf_umbral'} and os.path.isfile(imagenes['olf_umbral'])
    # Al retomar vuelve igual.
    w2, _r = ventana()
    assert w2.restore_report(job['data'])
    assert w2.tabla_informe.contenido == contenido
    assert w2._puntajes() == w._puntajes() and w2.cmb_categoria.currentData() == O.categoria(p['TDI'])
    acciones = {a for a, _p in LOGS.eventos}
    for a in ('olf_preguntar_preparacion', 'olf_venda', 'olf_presentar', 'olf_prueba',
              'olf_puntaje', 'olf_categoria'):
        assert a in acciones, a
    pres = LOGS.de('olf_presentar')[0]
    assert pres['case_id'] == 901 and 'detecto' in pres and pres['paso_regla'] == 16


def test_no_huelo_nada_pide_eleccion_forzada():
    LOGS.eventos.clear()
    w, reloj = ventana(caso(bloque(T=1, D=0, I=0)))
    w._venda()
    vistos = 0
    for _ in range(20):
        reloj.t += 25
        w._presentar()
        if w.pendiente is not None:
            vistos += 1
            assert w.btn_elegir.isVisible() or not w.isVisible()
            assert not w.btn_presentar.isEnabled()
            w._anotar_error()
            assert w.ensayos[-1]['anotado_error'] and not w.ensayos[-1]['ok']
    assert vistos > 5 and LOGS.de('olf_anotar_sin_eleccion')


def test_identificacion_con_venda_no_lee():
    w, reloj = ventana()
    w.cmb_prueba.setCurrentIndex(2)
    w._venda()
    reloj.t += 25
    w._presentar()
    assert not w.ensayos and 'venda' in w.lbl_paciente.text()


def test_preparacion_y_espera():
    w, reloj = ventana(caso(bloque(preparacion='fumo')))
    w._preguntar()
    assert 'cigarro' in w.lbl_paciente.text()
    assert not w.sesion.preparado()
    w._esperar()
    reloj.t += 30 * 60
    assert not w.sesion.preparado()
    w._saltar_espera()
    assert w.sesion.preparado()


def test_verdad_solo_docente():
    w, _r = ventana(login=ALUMNO)
    assert w.verdad is None and w.tabs.count() == 2
    w, _r = ventana()
    assert w.verdad is not None and 'de verdad' in w.verdad.text()


if __name__ == '__main__':
    for nombre, f in list(globals().items()):
        if nombre.startswith('test_') and callable(f):
            f()
            print(f'  {nombre} OK')
    print('TODOS LOS TESTS PASARON')
