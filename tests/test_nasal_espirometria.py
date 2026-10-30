"""Tests de la espirometría (nasal/espirometria.py, nasal/EspirometriaWindow.py).

1. GLI-2012 da los ejemplos publicados del manual SER 2024 (los mismos con
   que se valida el libro, hacer_cap37.py).
2. Una maniobra bien conducida mide la FVC, el FEV1 y el PEF del caso (pre y
   con el broncodilatador pleno), con BEV bajo el límite, meseta y CVIF ≈ FVC.
3. Lo que hace el alumno se ve en la maniobra: sin «siga» el paciente deja
   de soplar antes (sin meseta, FVC utilizable); sin «tome aire rápido» no
   hay CVIF; soplar sin llenar los pulmones deja la CVIF sobre la FVC.
4. Los errores simulados dejan su huella y el equipo los califica con la
   tabla de H30: inicio lento (BEV), tos marcada (FEV1 ninguna), fuga.
5. La obstrucción fija de la vía aérea superior aplana el PEF y lleva
   FEF50/FIF50 cerca de 1 y FEV1/PEF sobre 8.
6. Grados A-F y respuesta broncodilatadora sobre el teórico (ejemplo del
   manual: 13,3 %).
7. La receta rehace la maniobra idéntica.
8. La ventana: sin ESPIRO no mide; pide boquilla y talla; las maniobras
   entran a la tabla y al informe; el broncodilatador tiene espera; el
   informe sube y al retomar vuelven idénticas; "lo que el equipo no sabe"
   solo para docente; cada acción a action_logs con prefijo esp_.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from nasal import espirometria as E  # noqa: E402
from nasal import sesion  # noqa: E402
from nasal.EspirometriaWindow import EspirometriaWindow  # noqa: E402

ADMIN = {'permission': 777}
ALUMNO = {'permission': 1}

ASMA = {'talla': 176, 'peso': 74, 'pre': {'fvc': 4.90, 'fev1': 3.20, 'pef': 7.4},
        'bd': {'fvc': 5.10, 'fev1': 3.80, 'pef': 8.8}}
ESTENOSIS = {'talla': 160, 'peso': 68, 'pre': {'fvc': 3.25, 'fev1': 2.80, 'pef': 7.4},
             'tope_e': 3.2, 'tope_i': 3.0}


class ColaFalsa:
    def __init__(self):
        self.eventos = []

    def push(self, accion, payload=None):
        self.eventos.append((accion, payload or {}))

    def de(self, accion):
        return [p for a, p in self.eventos if a == accion]


LOGS = ColaFalsa()
sesion._cola = LOGS


def caso(espiro=ASMA, edad=27, gender=0, id_=900):
    return {'id': id_, 'edad': edad, 'gender': gender, 'ESPIRO': espiro}


def conducir(reg, siga=True, inspire=True, aire=True):
    """Una maniobra como se hace: 3-4 respiraciones tranquilas, «tome todo el
    aire», «¡sople!» al llegar a TLC, «siga» cada 2 s mientras sopla y
    «tome aire rápido» cuando se queda sin aire."""
    return _conducir(reg, reg.avanzar, reg.indicar, siga, inspire, aire)


def _conducir(reg, avanzar, indicar, siga, inspire, aire):
    avanzar(13 * E.HZ)
    if aire:
        indicar('aire')
        while reg.estado != 'tlc' and reg.i < 40 * E.HZ:
            avanzar(5)
        avanzar(50)
    indicar('sople')
    avanzar(60)
    ultimo = reg.i
    while reg.estado == 'espira':
        if siga and reg.i - ultimo >= 2 * E.HZ:
            indicar('siga')
            ultimo = reg.i
        avanzar(5)
    if inspire:
        indicar('inspire')
    while not reg.terminada and reg.i < 80 * E.HZ:
        avanzar(10)
    return E.analizar(reg.flujos)


def registro(espiro=ASMA, semilla='t', **receta):
    pulmon = E.Pulmon(E.normaliza(espiro))
    return E.Registro(pulmon, {'semilla': semilla, **receta})


def cerca(a, b, tol):
    assert abs(a - b) <= tol, (a, b, tol)


# --- 1 -----------------------------------------------------------------------

def test_gli_ejemplos_del_manual():
    cerca(E.previsto('M', 'FEV1', 54, 160), 3.00, 0.02)
    for par, teor, lin in (('FVC', 3.67, 2.91), ('FEV1', 2.97, 2.35), ('FEV1FVC', 0.8142, 0.7046)):
        cerca(E.previsto('F', par, 44, 164), teor, 0.006)
        cerca(E.lin('F', par, 44, 164), lin, 0.006)
    # El z del LIN es −1,645 y la gravedad sigue la tabla de 2022.
    cerca(E.zscore('M', 'FVC', E.lin('M', 'FVC', 55, 172), 55, 172), -1.645, 1e-9)
    assert [E.gravedad(z) for z in (-1, -2, -3, -5)] == ['normal', 'leve', 'moderada', 'grave']
    # "otros" da previstos más bajos que "caucásico" (H30).
    assert E.previsto('M', 'FVC', 27, 176, 'otros') < E.previsto('M', 'FVC', 27, 176)


# --- 2 -----------------------------------------------------------------------

def test_maniobra_bien_hecha_mide_el_caso():
    for semilla in 'abc':
        r = conducir(registro(semilla=semilla))
        cerca(r['fvc'], 4.90, 0.15)
        cerca(r['fev1'], 3.20, 0.12)
        cerca(r['pef'], 7.4, 0.5)
        assert r['bev'] < r['bev_limite'] and r['meseta'] and r['corrientes'] >= 3
        cerca(r['cvif'], r['fvc'], 0.1)
        assert E.aceptabilidad(r) == ('aceptable', 'aceptable', [])
    post = conducir(registro(semilla='a', frac_bd=1.0))
    cerca(post['fvc'], 5.10, 0.15)
    cerca(post['fev1'], 3.80, 0.12)


# --- 3 -----------------------------------------------------------------------

def test_sin_siga_deja_de_soplar():
    reg = registro(semilla='a')
    r = conducir(reg, siga=False)
    assert not r['meseta'] and r['tef'] < 15
    assert 'dejó de soplar' in reg.verdad['fin']
    fev1, fvc, motivos = E.aceptabilidad(r)
    assert (fev1, fvc) == ('aceptable', 'utilizable') and motivos
    # Con otra maniobra de FVC parecida, el criterio de fin se cumple por repetibilidad.
    assert E.aceptabilidad(r, [r['fvc'] + 0.1])[1] == 'aceptable'


def test_sin_inspiracion_final_no_hay_cvif():
    reg = registro(semilla='a')
    r = conducir(reg, inspire=False)
    assert r['cvif'] is None or r['cvif'] < 0.7 * r['fvc']
    assert not reg.verdad['cvif_forzada']


def test_sople_sin_llenar_los_pulmones():
    reg = registro(semilla='a')
    r = conducir(reg, aire=False)
    assert not reg.verdad['parto_tlc']
    # Desde la FRC el flujo de este asma ni llega al gatillo; si llega, la
    # CVIF lo delata.
    if r is not None:
        assert r['cvif'] - r['fvc'] > max(0.1, 0.05 * r['fvc'])
        assert E.aceptabilidad(r)[:2] == ('utilizable', 'utilizable')
    r = conducir(registro(semilla='a', frac_bd=1.0), aire=False)
    assert r is not None and E.aceptabilidad(r)[:2] == ('utilizable', 'utilizable')


# --- 4 -----------------------------------------------------------------------

def test_errores_simulados():
    lento = conducir(registro(semilla='a', errores=['lento']))
    assert lento['bev'] > lento['bev_limite']
    assert E.aceptabilidad(lento)[:2] == ('no', 'no')
    no_tlc = conducir(registro(semilla='a', errores=['no_tlc']))
    assert E.aceptabilidad(no_tlc)[:2] == ('utilizable', 'utilizable')
    bien = conducir(registro(semilla='a'))
    fuga = conducir(registro(semilla='a', errores=['fuga']))
    assert fuga['fvc'] < 0.9 * bien['fvc']
    # El equipo no ve la tos: la marca el alumno, y con ella el FEV1 no sirve.
    reg = registro(semilla='a', errores=['tos'])
    tos = conducir(reg)
    assert reg.verdad['t_tos']
    assert E.aceptabilidad(tos, marca='tos1')[:2] == ('no', 'aceptable')
    # Cero corrido: la línea de base se mueve y no hay meseta.
    cero = conducir(registro(semilla='a', cero=0.05))
    assert abs(cero['deriva']) > 0.08 and not cero['meseta']
    # Descalibrado: todo un 6 % más.
    desc = conducir(registro(semilla='a', calibracion=1.06))
    cerca(desc['fvc'] / bien['fvc'], 1.06, 0.01)


def test_verificacion_con_jeringa():
    ok, bien = E.verificar(1.0, 'x')
    assert bien and len(ok) == 3
    _r, mal = E.verificar(1.06, 'x')
    assert not mal


# --- 5 -----------------------------------------------------------------------

def test_estenosis_fija():
    r = conducir(registro(ESTENOSIS, semilla='a'))
    cerca(r['pef'], 3.2, 0.1)
    cerca(r['fef50'] / r['fif50'], 1.0, 0.15)
    assert r['fev1'] * 1000 / (r['pef'] * 60) > 8
    # La normal, en cambio, tiene FEV1/PEF bajo 8.
    asma = conducir(registro(semilla='a'))
    assert asma['fev1'] * 1000 / (asma['pef'] * 60) < 8


# --- 6 -----------------------------------------------------------------------

def test_grados_y_respuesta():
    assert E.grado([3.0, 2.95, 2.9], False) == 'A'
    assert E.grado([3.0, 2.9], False) == 'B'
    assert E.grado([3.0, 2.82], False) == 'C'
    assert E.grado([3.0, 2.76], False) == 'D'
    assert E.grado([3.0, 2.7], False) == 'E'
    assert E.grado([3.0], False) == 'E'
    assert E.grado([], True) == 'U'
    assert E.grado([], False) == 'F'
    # H30, pregunta 3: 2,60; 2,50; 2,41 -> diferencia de las dos mayores 0,10: A.
    assert E.grado([2.60, 2.50, 2.41], False) == 'A'
    litros, pct = E.respuesta_bd(2.0, 2.4, 3.0)
    cerca(litros, 0.4, 1e-9)
    cerca(pct, 13.33, 0.01)


def test_resumen_informa_lo_mayor_de_las_aceptables():
    ms = [{'r': conducir(registro(semilla=s))} for s in 'abc']
    res = E.resumen_fase(ms)
    assert res['grado_fev1'] in 'AB' and res['n_fev1'] == 3
    assert res['fev1'] == max(m['r']['fev1'] for m in ms)
    assert res['fvc'] == max(m['r']['fvc'] for m in ms)
    # Descartar una deja dos.
    ms[0]['marca'] = 'descartar'
    assert E.resumen_fase(ms)['n_fvc'] == 2


# --- 7 -----------------------------------------------------------------------

def test_receta_rehace_identico():
    reg = registro(semilla='z', errores=['tos'])
    conducir(reg)
    reg.receta['muestras'] = reg.i
    otro = E.rehace(reg.pulmon, reg.receta)
    assert otro.flujos == reg.flujos


# --- 8 -----------------------------------------------------------------------

class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def ventana(data=None, login=ADMIN, cita=4242):
    reloj = Reloj()
    w = EspirometriaWindow(data_login=login, reloj=reloj)
    w.la_super(data if data is not None else caso(), cita)
    return w, reloj


def preparar(w):
    w._pinza()
    w._boquilla()
    w._medir_talla()
    w._verificar()


def maniobra_en_ventana(w, reloj, **kw):
    w._iniciar()
    reg = w.registro
    assert reg is not None

    def avanzar(n):
        # Como el reloj de verdad: un tic cada 50 ms.
        for _ in range(0, n, 5):
            reloj.t += min(5, n) * E.DT
            w._tic()

    _conducir(reg, avanzar, w._indicar, kw.get('siga', True), True, True)
    while w.registro is not None and reloj.t < 1e6:
        avanzar(10)


def test_ventana_sin_espiro_no_mide():
    w, _r = ventana({'id': 1, 'edad': 30, 'gender': 0})
    assert not w.btn_iniciar.isEnabled() and not w.panel_paciente.isEnabled()
    assert 'ESPIRO' in w.lbl_mensaje.text()


def test_ventana_pide_boquilla_y_talla():
    w, _r = ventana()
    w._iniciar()
    assert w.registro is None and 'boquilla' in w.lbl_mensaje.text()
    w._boquilla()
    w._iniciar()
    assert w.registro is None and 'talla' in w.lbl_mensaje.text()


def test_ventana_maniobras_bd_e_informe():
    LOGS.eventos.clear()
    w, reloj = ventana()
    preparar(w)
    for _ in range(3):
        maniobra_en_ventana(w, reloj)
    assert len(w.maniobras) == 3 and w.tabla.rowCount() == 3
    assert 'VEF1 A' in w.lbl_calidad.text() or 'VEF1 B' in w.lbl_calidad.text()
    # Broncodilatador: espera de 15 min; antes de eso el efecto es parcial.
    w._dar_bd()
    assert w.sesion.fase() == 'post' and w.sesion.falta_bd() == 15 * 60
    reloj.t += 5 * 60
    assert 0.5 < w.sesion.frac_bd() < 0.7
    w._saltar_espera()
    assert w.sesion.falta_bd() == 0
    for _ in range(3):
        maniobra_en_ventana(w, reloj)
    contenido = w.tabla_informe.contenido
    assert contenido['cabeceras'][2] == 'Pre' and contenido['filas'][0][0] == 'CVF (L)'
    cambio = float(contenido['filas'][1][10].replace(',', '.'))
    assert cambio > 10          # el asma del caso responde
    job = w.report_job()
    assert job['tipo'] == 'ESPIROMETRIA' and len(job['data']['maniobras']) == 6
    assert job['data']['broncodilatador']['clave'] == 'salbutamol'
    assert job['data']['verificacion']['ok']
    imagenes = job['images']()
    assert set(imagenes) == {'esp_fv', 'esp_vt'} and all(os.path.isfile(p) for p in imagenes.values())
    # Al retomar, las maniobras vuelven idénticas.
    w2, _r = ventana()
    assert w2.restore_report(job['data'])
    from PySide6.QtWidgets import QApplication
    for _ in range(200):
        QApplication.processEvents()
        if w2.maniobras:
            break
        import time
        time.sleep(0.02)
    assert [m['flujos'] for m in w2.maniobras] == [m['flujos'] for m in w.maniobras]
    assert w2.tabla_informe.contenido == contenido
    # Los logs.
    acciones = {a for a, _p in LOGS.eventos}
    for a in ('esp_pinza', 'esp_boquilla', 'esp_medir', 'esp_verificar', 'esp_iniciar',
              'esp_indicacion', 'esp_maniobra', 'esp_broncodilatador', 'esp_saltar_espera'):
        assert a in acciones, a
    m = LOGS.de('esp_maniobra')[0]
    assert 'verdad' in m and 'esfuerzo' in m['verdad'] and m['case_id'] == 900


def test_marca_del_alumno_cambia_la_calidad():
    w, reloj = ventana()
    preparar(w)
    maniobra_en_ventana(w, reloj)
    assert w.tabla.item(0, 9).text() == 'aceptable'
    w._marcar(0, 'tos1')
    assert w.tabla.item(0, 9).text() == 'ninguna' and w.tabla.item(0, 10).text() == 'aceptable'
    assert LOGS.de('esp_marca')[-1]['marca'] == 'tos1'


def test_verdad_solo_docente():
    w, _r = ventana(login=ALUMNO)
    assert w.verdad is None and w.tabs.count() == 2
    w, _r = ventana()
    assert w.verdad is not None and 'talla real' in w.verdad.text()


if __name__ == '__main__':
    for nombre, f in list(globals().items()):
        if nombre.startswith('test_') and callable(f):
            f()
            print(f'  {nombre} OK')
    print('TODOS LOS TESTS PASARON')
