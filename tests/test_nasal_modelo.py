"""Tests del paciente de RinoSim (src/nasal/modelo.py): geometría por
parámetros, ciclo nasal, vasoconstrictor y semillas.

1. El vasoconstrictor retira la mucosa y no toca lo estructural.
2. Apaga el ciclo nasal; sin él las dos fosas van en contrafase.
3. Las áreas son positivas y el perfil cubre la rejilla.
4. La misma semilla da el mismo paciente; otra, otro.
5. Un paciente en JSON se completa con el normal y rechaza lo que no es número.
"""

import os
import sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from nasal.modelo import (  # noqa: E402
    CUADROS, LADOS, REJILLA, congestion, normaliza, paciente, perfil, piezas)


def test_vasoconstrictor_retira_mucosa_no_lo_estructural():
    for cuadro in CUADROS:
        p = paciente(cuadro)
        for lado in LADOS:
            s = p['lados'][lado]
            c_reposo = congestion(p, lado, {'minuto': 40})
            c_vc = congestion(p, lado, {'vc': True})
            assert c_vc <= c_reposo, f'{cuadro} {lado}: la congestión no baja'
            for x in (0.5, 1.3, 2, 3.2, 4.5, 6):
                a = piezas(s, x, c_reposo)
                b = piezas(s, x, c_vc)
                assert b['estructural'] == a['estructural'], f'{cuadro} {lado} x={x}: cambió lo estructural'
                assert b['base'] == a['base']
                assert b['mucoso'] <= a['mucoso']


def test_vasoconstrictor_apaga_el_ciclo_nasal():
    p = paciente('normal')
    sin_vc = {f"{congestion(p, 'D', {'minuto': t}):.3f}" for t in (0, 40, 80, 120)}
    con_vc = {f"{congestion(p, 'D', {'minuto': t, 'vc': True}):.3f}" for t in (0, 40, 80, 120)}
    assert len(sin_vc) > 1
    assert len(con_vc) == 1


def test_ciclo_nasal_contrafase():
    p = paciente('normal')
    t = p['ciclo']['periodo'] / 4
    d = congestion(p, 'D', {'minuto': t}) - p['lados']['D']['congestion']
    i = congestion(p, 'I', {'minuto': t}) - p['lados']['I']['congestion']
    assert d > 0.2 and i < -0.2, f'{d} {i}'


def test_areas_positivas_y_perfil_cubre_la_rejilla():
    import math
    for cuadro in CUADROS:
        A = perfil(paciente(cuadro), 'D', {})
        assert len(A) == len(REJILLA)
        assert all(a > 0 and math.isfinite(a) for a in A)


def test_misma_semilla_mismo_paciente():
    a = paciente('cornetes', 7)
    b = paciente('cornetes', 7)
    c = paciente('cornetes', 8)
    assert a == b
    assert a['lados'] != c['lados']
    # Sin semilla, el cuadro tal cual.
    assert paciente('normal')['lados'] == paciente('normal', None)['lados']


def test_paciente_en_json_se_completa_y_rechaza_no_numeros():
    p = normaliza({'lados': {'I': {'polipos': 1.2}}})
    assert p['lados']['I']['polipos'] == 1.2
    assert p['lados']['D'] == paciente('normal')['lados']['D']
    try:
        normaliza({'lados': {'D': {'valvula': {'area': 'chica'}}}})
    except ValueError:
        pass
    else:
        raise AssertionError('tenía que rechazar un valor que no es número')


def test_cuadro_desconocido_falla():
    try:
        paciente('inexistente')
    except ValueError:
        pass
    else:
        raise AssertionError('tenía que fallar con un cuadro desconocido')


def test_el_paciente_es_json():
    import json
    for cuadro in CUADROS:
        p = paciente(cuadro, 3)
        assert json.loads(json.dumps(p)) == p


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

