"""Tests de la rinometría acústica (src/nasal/rinometria.py): dónde caen los
mínimos y dónde se equivoca la curva. Portados de rinosim/test.

1. MCA1 cae en la válvula y MCA2 en la cabeza del cornete.
2. MCA1 es el área de la válvula; el vasoconstrictor abre MCA2 más que MCA1.
3. Los errores del método: estrechamiento marcado, senos, perforación.
4. Criterio de repetición del libro; fuga y adaptador que aprieta.
5. Volúmenes y medidas de una curva conocida; misma semilla, mismos registros.
"""

import os
import sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import math  # noqa: E402

from nasal.modelo import REJILLA, paciente, perfil  # noqa: E402
from nasal.rinometria import (  # noqa: E402
    CRITERIO_REPETICION, curva_del_equipo, medidas, mide_fosa, volumen)


def en_x(x):
    return next(i for i, v in enumerate(REJILLA) if v >= x)


def test_mca1_en_la_valvula_y_mca2_en_el_cornete():
    for pos in (1.0, 1.3, 1.7):
        p = paciente('normal')
        p['lados']['D']['valvula']['pos'] = pos
        r = mide_fosa(p, 'D', {}, {'semilla': 1})
        assert abs(r['promedio']['dist1'] - pos) < 0.15, f"válvula en {pos}, MCA1 en {r['promedio']['dist1']}"
        cpos = p['lados']['D']['cornete']['pos']
        assert abs(r['promedio']['dist2'] - cpos) < 0.3, f"cornete en {cpos}, MCA2 en {r['promedio']['dist2']}"


def test_mca1_es_el_area_de_la_valvula():
    p = paciente('normal')
    for area in (0.4, 0.65, 0.9):
        p['lados']['D']['valvula']['area'] = area
        r = mide_fosa(p, 'D', {'vc': True}, {'semilla': 1})
        assert abs(r['verdad']['medidas']['mca1'] - area) < 0.05, f"{area} -> {r['verdad']['medidas']['mca1']}"
        assert abs(r['promedio']['mca1'] - r['verdad']['medidas']['mca1']) < 0.08


def test_vasoconstrictor_abre_el_cornete_mas_que_la_valvula():
    p = paciente('cornetes')
    a = mide_fosa(p, 'D', {}, {'semilla': 1})['promedio']
    b = mide_fosa(p, 'D', {'vc': True}, {'semilla': 1})['promedio']
    assert b['mca2'] > 3 * a['mca2']
    assert b['mca2'] / a['mca2'] > 2 * (b['mca1'] / a['mca1']), \
        f"MCA1 x{b['mca1'] / a['mca1']:.2f}, MCA2 x{b['mca2'] / a['mca2']:.2f}"
    # Una desviación (esqueleto) casi no se mueve.
    d0 = mide_fosa(paciente('desviacion_derecha'), 'D', {}, {'semilla': 1})['promedio']['mca1']
    d1 = mide_fosa(paciente('desviacion_derecha'), 'D', {'vc': True}, {'semilla': 1})['promedio']['mca1']
    assert abs(d1 - d0) / d0 < 0.15


def test_detras_de_un_estrechamiento_marcado_se_subestima():
    p = paciente('normal')
    p['lados']['D']['valvula']['area'] = 0.15
    verdad = perfil(p, 'D', {})
    visto = curva_del_equipo(p, 'D', {})
    i = en_x(3.2)
    assert visto[i] < 0.8 * verdad[i], f'{visto[i]} vs {verdad[i]}'


def test_pasados_5_cm_suma_senos_y_rinofaringe():
    p = paciente('normal')
    i = en_x(6.5)
    reposo = curva_del_equipo(p, 'D', {})[i] - perfil(p, 'D', {})[i]
    vc = curva_del_equipo(p, 'D', {'vc': True})[i] - perfil(p, 'D', {'vc': True})[i]
    assert reposo > 0.3
    assert vc > reposo
    # Y en la zona de la válvula no.
    j = en_x(1.3)
    assert abs(curva_del_equipo(p, 'D', {})[j] - perfil(p, 'D', {})[j]) < 0.1


def test_perforacion_detras_suma_la_otra_fosa():
    r = mide_fosa(paciente('perforacion'), 'D', {}, {'semilla': 1})
    assert r['promedio']['mca2'] > 1.2 * r['verdad']['medidas']['mca2']


def test_criterio_de_repeticion_del_libro():
    for cuadro in ('normal', 'cornetes', 'desviacion_derecha', 'mixta'):
        r = mide_fosa(paciente(cuadro), 'D', {}, {'semilla': 5})
        assert r['repetible'], f"{cuadro}: {r['rango']['mca1']} {r['rango']['mca2']}"
    malo = mide_fosa(paciente('normal'), 'D', {}, {'semilla': 5, 'errores': {'fuga': True}})
    assert not malo['repetible']
    assert malo['promedio']['vol05'] > mide_fosa(paciente('normal'), 'D', {}, {'semilla': 5})['promedio']['vol05'], \
        'la fuga sobreestima'
    assert CRITERIO_REPETICION == 0.03


def test_adaptador_que_aprieta_achica_la_entrada():
    bien = mide_fosa(paciente('normal'), 'D', {}, {'semilla': 1})['promedio']['mca1']
    mal = mide_fosa(paciente('normal'), 'D', {}, {'semilla': 1, 'errores': {'aprieta': True}})['promedio']['mca1']
    assert mal < 0.9 * bien


def test_volumenes_y_medidas_de_una_curva_conocida():
    x = [i * 0.025 for i in range(401)]
    A = [2 for _ in x]
    assert abs(volumen(x, A, 0, 5) - 10) < 1e-9
    assert abs(volumen(x, A, 0, 2) + volumen(x, A, 2, 5) - volumen(x, A, 0, 5)) < 1e-9
    B = [2 - 1.4 * math.exp(-0.5 * ((v - 1.5) / 0.3) ** 2) - math.exp(-0.5 * ((v - 3.5) / 0.4) ** 2) for v in x]
    m = medidas(x, B)
    assert abs(m['dist1'] - 1.5) < 0.03 and abs(m['dist2'] - 3.5) < 0.03
    assert abs(m['mca1'] - 0.6) < 0.01 and abs(m['mca2'] - 1.0) < 0.01


def test_misma_semilla_mismos_registros():
    p = paciente('polipos', 3)
    assert mide_fosa(p, 'I', {}, {'semilla': 9}) == mide_fosa(p, 'I', {}, {'semilla': 9})


def _correr():
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            try:
                fn()
                print(f'  {nombre} OK')
            except AssertionError as exc:
                fallos += 1
                print(f'  {nombre} FALLÓ: {exc}')
    print('TODOS LOS TESTS PASARON' if not fallos else f'{fallos} FALLARON')
    return fallos


if __name__ == '__main__':
    sys.exit(1 if _correr() else 0)

