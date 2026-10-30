"""Tests del prick test (nasal/prick.py, nasal/PrickWindow.py).

1. El curso de la pápula: la histamina llega antes (8-10 min), los
   alérgenos a los 15-20, a la hora casi no queda nada.
2. El antihistamínico sin suspender achica todo (la histamina queda bajo
   3 mm: prueba no válida); suspendido a tiempo, nada.
3. Los errores de H29 ensucian: punciones a menos de 2 cm (reflejo
   axónico), lanceta reusada, secar arrastrando; el dermografismo da pápula
   en el negativo.
4. El criterio: 3 mm o más, y 3 mm sobre el negativo si este reacciona.
5. La ventana: sin PRICK no se hace; marcar, puncionar con lanceta nueva,
   esperar, medir con la regla y anotar; el informe sube y vuelve al
   retomar; "lo que el equipo no sabe" solo para docente; cada acción a
   action_logs con prefijo prick_.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from nasal import prick as P  # noqa: E402
from nasal import sesion  # noqa: E402
from nasal.PrickWindow import PrickWindow  # noqa: E402

ADMIN = {'permission': 777}
ALUMNO = {'permission': 1}

# El ejemplo de la hoja de H29.
LIBRO = {'histamina': 6, 'alergenos': {'dpte': 8, 'dfar': 6, 'gato': 3, 'perro': 2, 'pastos': 5}}


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
        self.t = 100000.0

    def __call__(self):
        return self.t


def caso(prick=None, edad=27, gender=0, id_=902):
    return {'id': id_, 'edad': edad, 'gender': gender, 'PRICK': prick or LIBRO}


def sitio(extracto, x, y, puncion=0.0, lanceta=None, arrastre=False):
    return {'extracto': extracto, 'x': x, 'y': y, 'puncion': puncion,
            'lanceta': lanceta if lanceta is not None else hash((extracto, x, y)), 'arrastre': arrastre}


def mayor(piel, sitios, i, minuto):
    return P.papula(piel, sitios, i, minuto, f's{i}')['mayor']


# --- 1 -----------------------------------------------------------------------

def test_curso_de_la_papula():
    piel = P.normaliza(LIBRO)
    s = [sitio('his', 0, 60), sitio('dpte', 0, 100)]
    his = [mayor(piel, s, 0, m) for m in (5, 10, 20, 60)]
    dp = [mayor(piel, s, 1, m) for m in (5, 10, 17, 60)]
    assert his[1] > his[0] and his[1] > his[2] > his[3]
    assert dp[2] > dp[1] > dp[0] and dp[3] < 0.15 * dp[2]
    assert 6.0 < dp[2] < 10.0          # ~8 mm con la variación del sitio
    assert P.curso(P.PICO_ALERGENO, P.PICO_ALERGENO) == 1


# --- 2 -----------------------------------------------------------------------

def test_antihistaminico():
    s = [sitio('his', 0, 60), sitio('dpte', 0, 100)]
    sin = P.normaliza(LIBRO)
    ayer = P.normaliza({**LIBRO, 'farmaco': {'clave': 'cetirizina', 'horas': 24}})
    hace_10_dias = P.normaliza({**LIBRO, 'farmaco': {'clave': 'cetirizina', 'horas': 240}})
    nasal = P.normaliza({**LIBRO, 'farmaco': {'clave': 'budesonida', 'horas': 2}})
    assert mayor(ayer, s, 0, 12) < 3 <= mayor(sin, s, 0, 12)
    assert mayor(hace_10_dias, s, 1, 17) == mayor(sin, s, 1, 17) == mayor(nasal, s, 1, 17)
    assert P.supresion(None) == 0 and P.supresion(ayer['farmaco']) > 0.9


# --- 3 -----------------------------------------------------------------------

def test_errores_ensucian():
    piel = P.normaliza(LIBRO)
    # Perro (2 mm, negativo) a 1 cm de D. pteronyssinus: el reflejo axónico.
    lejos = [sitio('dpte', 0, 100), sitio('perro', 0, 125)]
    cerca = [sitio('dpte', 0, 100), sitio('perro', 0, 110)]
    assert mayor(piel, cerca, 1, 17) > mayor(piel, lejos, 1, 17)
    assert P.avisos_sitio(cerca, 1) == ['cerca'] and P.avisos_sitio(lejos, 1) == []
    assert P.avisos_sitio([sitio('neg', 0, 10)], 0) == ['pliegue']
    # Lanceta reusada: el negativo después de D. pteronyssinus hace pápula.
    reusada = [sitio('dpte', 0, 100, puncion=0, lanceta=1), sitio('neg', 0, 140, puncion=0.5, lanceta=1)]
    assert mayor(piel, reusada, 1, 17) >= 3
    assert P.contaminantes(reusada, 1) == [('dpte', 0.6, 'lanceta')]
    # Secar arrastrando la gota del vecino.
    arrastre = [sitio('dpte', 0, 100, arrastre=True), sitio('neg', 0, 122)]
    assert mayor(piel, arrastre, 1, 17) > 2
    # Dermografismo: el negativo reacciona.
    dermo = P.normaliza({**LIBRO, 'dermografismo': 4})
    assert mayor(dermo, [sitio('neg', 0, 100)], 0, 10) >= 3


# --- 4 -----------------------------------------------------------------------

def test_criterio():
    s = [sitio('neg', 0, 40), sitio('his', 0, 70), sitio('gato', 0, 100), sitio('perro', 0, 130)]
    assert P.resultado_correcto(s, [0, 6, 3, 2]) == {0: 'valido', 1: 'valido', 2: 'positivo', 3: 'negativo'}
    # Negativo de 2 mm: el gato necesita 5.
    assert P.resultado_correcto(s, [2, 6, 4, 5])[2] == 'negativo'
    assert P.resultado_correcto(s, [2, 6, 4, 5])[3] == 'positivo'
    assert P.resultado_correcto(s, [0, 2, 3, 0])[1] == 'no_valido'


def test_normaliza():
    b = P.normaliza({'histamina': 6, 'alergenos': {'gato': 3, 'inventado': 9}})
    assert b['alergenos']['gato'] == 3 and 'inventado' not in b['alergenos'] and b['farmaco'] is None
    for malo in ({'histamina': 20}, {'histamina': 6, 'alergenos': {'gato': 30}}, []):
        try:
            P.normaliza(malo)
        except ValueError:
            continue
        raise AssertionError(malo)


# --- 5 -----------------------------------------------------------------------

def ventana(data=None, login=ADMIN, cita=4444):
    reloj = Reloj()
    w = PrickWindow(data_login=login, reloj=reloj)
    w.la_super(data if data is not None else caso(), cita)
    return w, reloj


def elegir(w, clave):
    for i in range(w.lista.count()):
        if w.lista.item(i).data(0x0100) == clave:
            w.lista.setCurrentRow(i)
            return
    raise KeyError(clave)


def test_ventana_sin_prick_no_se_hace():
    w, _r = ventana({'id': 1, 'edad': 30, 'gender': 0})
    assert not w.panel_extractos.isEnabled() and not w.brazo.activo
    assert 'PRICK' in w.lbl_mensaje.text()


def test_ventana_prueba_completa():
    LOGS.eventos.clear()
    w, reloj = ventana()
    w._preguntar()
    assert 'Para la alergia no tomo nada' in w.lbl_paciente.text()
    orden = ['neg', 'dpte', 'dfar', 'gato', 'perro', 'pastos', 'alternaria', 'his']
    # Dos columnas de cuatro, a 2,5 cm entre sí, como la figura de H29.
    lugar = [(-14 if k < 4 else 14, 60 + (k % 4) * 25) for k in range(len(orden))]
    for k, clave in enumerate(orden):
        elegir(w, clave)
        w._clic_brazo(*lugar[k])
    assert [s['extracto'] for s in w.sitios] == orden
    assert all(P.avisos_sitio(w.sitios, i) == [] for i in range(len(orden)))
    w.btn_modo['puncionar'].setChecked(True)
    for k in range(len(orden)):
        w._lanceta_nueva()
        reloj.t += 5
        w._clic_brazo(*lugar[k])
    assert all(s['puncion'] is not None for s in w.sitios)
    assert len({s['lanceta'] for s in w.sitios}) == len(orden)
    w._secar()
    reloj.t += 16 * 60
    # Medir y anotar cada sitio con su pápula verdadera (como lo haría la regla).
    for i, s in enumerate(w.sitios):
        w._seleccionar(i)
        v = w.papula(i)
        if v['mayor'] == 0:
            w._anotar('sin')
        else:
            w.lupa.ultima = round(v['mayor'] * 2) / 2
            w._anotar('mayor')
            w.lupa.ultima = round(v['menor'] * 2) / 2
            w._anotar('perpendicular')
    correctos = w._correctos()
    assert correctos[0] == 'valido' and correctos[len(orden) - 1] == 'valido'
    assert correctos[1] == 'positivo' and correctos[6] == 'negativo'
    for i in range(len(orden)):
        combo = w.tabla.cellWidget(i, 5)
        combo.setCurrentIndex(combo.findData(correctos[i]))
    assert w.sitios[1]['resultado'] == 'positivo'
    w.txt_farmacos.setText('Sin antihistamínicos.')
    job = w.report_job()
    assert job['tipo'] == 'PRICK' and len(job['data']['sitios']) == len(orden)
    assert 15 <= job['data']['lectura_min'] <= 17
    assert job['data']['sitios'][0]['puncion_min'] == 0
    assert job['data']['pregunto_farmacos']
    imagenes = job['images']()
    assert set(imagenes) == {'prick_brazo'} and os.path.isfile(imagenes['prick_brazo'])
    # Al retomar vuelven los sitios, las lecturas y los resultados.
    w2, _r = ventana()
    assert w2.restore_report(job['data'])
    assert [s['extracto'] for s in w2.sitios] == orden
    assert [s['lectura'] for s in w2.sitios] == [s['lectura'] for s in w.sitios]
    assert [s['resultado'] for s in w2.sitios] == [s['resultado'] for s in w.sitios]
    assert w2.papula(1)['mayor'] > 3      # a los 20 minutos de la última
    acciones = {a for a, _p in LOGS.eventos}
    for a in ('prick_preguntar_farmacos', 'prick_marcar', 'prick_lanceta', 'prick_puncionar',
              'prick_secar', 'prick_medir', 'prick_resultado'):
        assert a in acciones, a
    assert LOGS.de('prick_marcar')[0]['case_id'] == 902


def test_ventana_lanceta_reusada_y_quitar():
    LOGS.eventos.clear()
    w, reloj = ventana()
    elegir(w, 'dpte')
    w._clic_brazo(0, 60)
    elegir(w, 'neg')
    w._clic_brazo(0, 90)
    w._clic_brazo(0, 120)        # el siguiente de la lista
    w.btn_modo['quitar'].setChecked(True)
    w._clic_brazo(0, 120)
    assert len(w.sitios) == 2
    w.btn_modo['puncionar'].setChecked(True)
    w._clic_brazo(0, 60)
    reloj.t += 3
    w._clic_brazo(0, 90)          # sin cambiar la lanceta
    assert LOGS.de('prick_puncionar')[-1]['reusada']
    assert LOGS.de('prick_puncionar')[-1]['contaminantes'] == ['dpte']
    reloj.t += 17 * 60
    assert w.papula(1)['mayor'] >= 3
    w.btn_modo['quitar'].setChecked(True)
    w._clic_brazo(0, 60)
    assert len(w.sitios) == 2 and 'puncionado' in w.lbl_mensaje.text()


def test_saltar_espera():
    w, reloj = ventana()
    elegir(w, 'his')
    w._clic_brazo(0, 80)
    w.btn_modo['puncionar'].setChecked(True)
    w._clic_brazo(0, 80)
    w._saltar_espera()
    assert abs(w.sesion.minuto() - w.sitios[0]['puncion'] - 15) < 1e-6


def test_verdad_solo_docente():
    w, _r = ventana(login=ALUMNO)
    assert w.verdad is None and w.tabs.count() == 2
    w, _r = ventana()
    assert w.verdad is not None and 'Sensibilizado a' in w.verdad.text()



def test_mismas_listas_que_el_backend():
    """La ficha del caso (CaseForm.php) valida con las mismas claves."""
    import re
    php = open(os.path.join(os.path.dirname(__file__), '..', 'labsim_backend', 'src', 'CaseForm.php'),
               encoding='utf-8').read()

    def claves(const):
        cuerpo = re.search(const + r' = \[(.*?)\];', php, re.S).group(1)
        return dict(re.findall(r"'(\w+)' => '([^']*)'", cuerpo))

    assert claves('PRICK_ALERGENOS') == {k: n for k, n, _a in P.ALERGENOS}
    assert claves('PRICK_FARMACOS') == P.NOMBRE_FARMACO
    from nasal import olfatometria as O
    builder = open(os.path.join(os.path.dirname(__file__), '..', 'labsim_backend', 'src', 'CaseBuilder.php'),
                   encoding='utf-8').read()
    grupos = re.search(r"'grupos' => \[(.*?)\]\],", builder, re.S).group(1)
    filas = [tuple(float(x) for x in f.split(',')) for f in re.findall(r'\[([\d., ]+)\]', grupos + ']')]
    assert filas == [tuple(float(x) for x in f) for f in O.NORMAS]


if __name__ == '__main__':
    for nombre, f in list(globals().items()):
        if nombre.startswith('test_') and callable(f):
            f()
            print(f'  {nombre} OK')
    print('TODOS LOS TESTS PASARON')
