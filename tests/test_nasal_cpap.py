"""Tests de la titulación de CPAP (nasal/cpap.py, nasal/CpapWindow.py).

1. Con la presión eficaz los eventos se van, y cada tipo tiene su umbral:
   primero las apneas, después las hipopneas y al final el ronquido (H32).
2. Una titulación bien hecha (sube 1 cmH2O cada 10 min si se cumple el
   criterio) llega a una presión con grado óptimo o bueno; quedarse en 4
   cmH2O es inaceptable.
3. La interfaz y la fuga: talla equivocada o boca abierta con mascarilla
   nasal suben la fuga y bajan la presión real; la oronasal la resuelve.
4. La misma secuencia de cambios rehace la misma noche.
5. La ventana: sin SUENO no titula; empezar, avanzar, subir, terminar,
   informe; al retomar vuelve igual; verdad solo docente; logs cpap_.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from nasal import cpap as C  # noqa: E402
from nasal import sesion  # noqa: E402
from nasal import sueno as Z  # noqa: E402
from nasal.CpapWindow import TIC_MS, CpapWindow  # noqa: E402

ADMIN = {'permission': 777}
ALUMNO = {'permission': 1}


class ColaFalsa:
    def __init__(self):
        self.eventos = []

    def push(self, accion, payload=None):
        self.eventos.append((accion, payload or {}))

    def de(self, accion):
        return [p for a, p in self.eventos if a == accion]


LOGS = ColaFalsa()
sesion._cola = LOGS


def caso(sueno=None, id_=904):
    return {'id': id_, 'edad': 61, 'gender': 1, 'SUENO': sueno or {'perfil': 'grave'}}


def titular(T, cada=600):
    """Lo que hace un técnico: cada 10 min, si hubo criterio, sube 1."""
    ult = 0
    while not T.terminada:
        T.avanzar(60)
        if T.t - ult >= cada and T.cumple_criterio(ult) and T.presion < C.P_MAX:
            T.cambiar(T.presion + 1)
            ult = T.t
    return T


# --- 1 -----------------------------------------------------------------------

def test_umbrales_por_tipo():
    pe = 10
    assert C.factor('ao', 8, pe) == 0 and C.factor('h', 8, pe) > 0 and C.factor('ron', 9, pe) > 0
    assert C.factor('h', 9, pe) == 0 and C.factor('ron', 10, pe) == 0
    assert C.factor('ao', 4, pe) > C.factor('ao', 6, pe) > 0


# --- 2 -----------------------------------------------------------------------

def test_titulacion_bien_hecha():
    b = Z.normaliza({'perfil': 'grave'})
    T = titular(C.Titulacion(b, 'a'))
    assert T.presion >= 12
    assert T.grado(T.presion) in ('optima', 'buena')
    filas = T.por_presion()
    assert filas[0]['presion'] == 4 and filas[0]['IDR'] > 20
    quieta = C.Titulacion(b, 'b')
    quieta.avanzar(quieta.N)
    assert quieta.grado(4) == 'inaceptable'


# --- 3 -----------------------------------------------------------------------

def test_interfaz_y_fuga():
    cp = C.parametros(Z.normaliza({'perfil': 'moderado'}))
    assert cp['boca'] and cp['p_eficaz'] == 10
    nasal = C.fuga(10, 'nasal', cp['talla'], cp)
    oro = C.fuga(10, 'oronasal', cp['talla'], cp)
    mala = C.fuga(10, 'oronasal', 'S', cp)
    assert nasal > 24 > oro and mala > oro
    assert C.presion_real(10, nasal) < 10 == C.presion_real(10, oro)
    # Con nasal y boca abierta, a la presión eficaz siguen los eventos.
    b = Z.normaliza({'perfil': 'moderado'})
    con_boca = C.Titulacion(b, 'c', 'nasal', 'M', 12)
    con_boca.avanzar(con_boca.N)
    bien = C.Titulacion(b, 'c', 'oronasal', 'M', 12)
    bien.avanzar(bien.N)
    assert len(con_boca.eventos) > len(bien.eventos)


# --- 4 -----------------------------------------------------------------------

def test_misma_secuencia_misma_noche():
    b = Z.normaliza({'perfil': 'grave'})
    A = titular(C.Titulacion(b, 'd'))
    B = C.Titulacion(b, 'd')
    for t, p in A.cambios[1:]:
        B.avanzar(t - B.t)
        B.cambiar(p)
    B.avanzar(B.N)
    assert [(x['t'], x['tipo']) for x in A.eventos] == [(x['t'], x['tipo']) for x in B.eventos]


def test_parametros_del_caso():
    b = Z.normaliza({'perfil': 'grave', 'cpap': {'p_eficaz': 15, 'talla': 'L'}})
    cp = C.parametros(b)
    assert cp['p_eficaz'] == 15 and cp['talla'] == 'L' and not cp['boca']
    try:
        C.parametros(Z.normaliza({'perfil': 'grave', 'cpap': {'p_eficaz': 30}}))
    except ValueError:
        pass
    else:
        raise AssertionError('p_eficaz fuera de rango')


# --- 5 -----------------------------------------------------------------------

def ventana(data=None, login=ADMIN, cita=4646):
    w = CpapWindow(data_login=login)
    w.la_super(data if data is not None else caso(), cita)
    return w


def test_ventana_sin_sueno():
    w = ventana({'id': 1, 'edad': 30, 'gender': 0})
    assert not w.panel_interfaz.isEnabled() and 'SUENO' in w.lbl_mensaje.text()


def test_ventana_titulacion():
    LOGS.eventos.clear()
    w = ventana()
    w._empezar()
    w.timer.stop()
    assert w.T is not None and w.T.presion == 4
    # A mano: 10 min de noche por vez, sube si hubo criterio.
    while not w.T.terminada:
        w.T.avanzar(600)
        if w.T.cumple_criterio(w.ultimo_cambio):
            w._cambiar(1)
    w._terminar()
    assert w._terminado() and not w.panel_presion.isEnabled()
    contenido = w.tabla_informe.contenido
    assert contenido['cabeceras'][0] == 'cmH₂O' and len(contenido['filas']) >= 5
    w.spin_indicada.setValue(w.T.presion)
    w.cmb_grado.setCurrentIndex(w.cmb_grado.findData(w.T.grado(w.T.presion)))
    job = w.report_job()
    assert job['tipo'] == 'CPAP' and job['data']['terminada'] and job['data']['presion_indicada'] == w.T.presion
    imagenes = job['images']()
    assert set(imagenes) == {'cpap_noche'} and os.path.isfile(imagenes['cpap_noche'])
    w2 = ventana()
    assert w2.restore_report(job['data'])
    assert w2.tabla_informe.contenido == contenido and w2._terminado()
    acciones = {a for a, _p in LOGS.eventos}
    for a in ('cpap_empezar', 'cpap_presion', 'cpap_terminar', 'cpap_indicar'):
        assert a in acciones, a
    p = LOGS.de('cpap_presion')[0]
    assert p['criterio'] and p['case_id'] == 904 and 'p_eficaz_ahora' in p


def test_ventana_tic_avanza_y_pausa():
    w = ventana()
    w._empezar()
    w.timer.stop()
    w._tic()
    # ×60 por defecto: cada tic de 200 ms son 12 s de noche.
    assert w.T.t == 60 * TIC_MS // 1000
    w._pausa()
    t = w.T.t
    w._tic()
    assert w.T.t == t


def test_verdad_solo_docente():
    w = ventana(login=ALUMNO)
    assert w.verdad is None and w.tabs.count() == 2
    w = ventana()
    assert 'Presión eficaz' in w.verdad.text()



def test_mismas_presiones_que_el_backend():
    """La tarjeta Sueño (CaseForm.php) propone las mismas presiones por perfil."""
    import re
    php = open(os.path.join(os.path.dirname(__file__), '..', 'labsim_backend', 'src', 'CaseForm.php'),
               encoding='utf-8').read()
    cuerpo = re.search(r'SUENO_CPAP_PERFIL = \[(.*?)\];', php, re.S).group(1)
    assert {k: int(v) for k, v in re.findall(r"'(\w+)' => (\d+)", cuerpo)} == C.PRESION_PERFIL


if __name__ == '__main__':
    for nombre, f in list(globals().items()):
        if nombre.startswith('test_') and callable(f):
            f()
            print(f'  {nombre} OK')
    print('TODOS LOS TESTS PASARON')
