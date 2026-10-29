"""Tests de la rinomanometría (src/nasal/rinomanometria.py): de la geometría
a la resistencia, la técnica y sus errores. Portados de rinosim/test.

1. Angostar cualquier pieza sube la resistencia (monotonía).
2. Rohrer: la resistencia sube con la presión; flujo y presión son inversas.
3. Resistencias en paralelo: los ejercicios de H26.
4. El vasoconstrictor baja la obstrucción mucosa y no la estructural.
5. La tabla de H26 sobre los ejercicios 3 y 4 y sobre los cuadros.
6. Una nariz normal del modelo queda bajo la referencia del libro.
7. Colapso valvular, perforación septal, errores de técnica, nariz amplia.
8. La misma semilla da la misma medición.
"""

import os
import sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from nasal.modelo import LADOS, paciente  # noqa: E402
from nasal.referencias import REFERENCIA_UNILATERAL_150  # noqa: E402
from nasal.rinomanometria import (  # noqa: E402
    examen, flujo, fosa, lectura_vasoconstrictor, mide_fosa, presion,
    resistencia_fosa, resistencia_total)

REF_150 = REFERENCIA_UNILATERAL_150['valor']


def r150(p, lado='D', estado=None):
    return resistencia_fosa(fosa(p, lado, estado or {}), 150)


def crece(valores, mensaje):
    for i in range(1, len(valores)):
        assert valores[i] > valores[i - 1], f"{mensaje}: {' '.join(f'{v:.3f}' for v in valores)}"


def test_geometria_resistencia_monotona():
    def con(cambia):
        def f(v):
            p = paciente('normal')
            cambia(p['lados']['D'], v)
            return r150(p)
        return f

    def pone(s, ruta, v):
        ks = ruta.split('.')
        for k in ks[:-1]:
            s = s[k]
        s[ks[-1]] = v

    for ruta, vals, nombre in (
            ('valvula.area', [0.9, 0.7, 0.5, 0.35, 0.25], 'válvula'),
            ('desviacion.area', [0, 0.2, 0.4, 0.6], 'desviación'),
            ('cornete.oseo', [0, 0.4, 0.8, 1.2], 'cornete óseo'),
            ('polipos', [0, 1, 2, 2.5], 'pólipos'),
            ('congestion', [0, 0.3, 0.6, 0.9], 'congestión'),
            ('valvula.colapso', [0, 0.3, 0.6], 'colapso de la válvula')):
        crece([con(lambda s, v, r=ruta: pone(s, r, v))(v) for v in vals], nombre)


def test_rohrer_flujo_presion_inversas():
    f = fosa(paciente('normal'), 'D', {})
    assert resistencia_fosa(f, 150) > resistencia_fosa(f, 75)
    for k1, k2, dP in ((0.04, 5e-4, 150), (0.2, 2e-3, -80)):
        assert abs(presion(k1, k2, flujo(k1, k2, dP)) - dP) < 1e-9


def test_resistencias_en_paralelo_h26():
    assert abs(resistencia_total(0.6, 0.3) - 0.2) < 1e-12  # ejercicio 2
    assert abs(resistencia_total(0.375, 0.3) - 1 / 6) < 1e-12  # ejercicio 3
    assert resistencia_total(float('inf'), 0.25) == 0.25  # pregunta 5: una fosa tapada
    assert resistencia_total(0.6, 0.3) < min(0.6, 0.3)
    assert resistencia_total(None, 0.3) is None
    # Y el examen la calcula así con lo que midió.
    e = examen(paciente('mixta'), {}, {'semilla': 3})
    rD = e['fosas']['D']['lecturas'][150]['insp']['R']
    rI = e['fosas']['I']['lecturas'][150]['insp']['R']
    assert abs(e['total'][150] - 1 / (1 / rD + 1 / rI)) < 1e-12


def test_vasoconstrictor_baja_lo_mucoso_no_lo_estructural():
    corn = paciente('cornetes')
    assert r150(corn) > REF_150
    assert r150(corn, 'D', {'vc': True}) <= REF_150
    # Una fosa sin mucosa: el vasoconstrictor no cambia nada.
    hueso = paciente('desviacion_derecha')
    hueso['lados']['D']['cornete']['mucosa'] = 0
    assert r150(hueso, 'D', {}) == r150(hueso, 'D', {'vc': True})


def test_tabla_h26_ejercicios_y_cuadros():
    assert lectura_vasoconstrictor(0.6, 0.375)['tipo'] == 'vasomotora'
    assert lectura_vasoconstrictor(0.6, 0.45)['tipo'] == 'mixta'
    assert lectura_vasoconstrictor(0.6, 0.59)['tipo'] == 'mecanica'

    def lee(cuadro, lado):
        p = paciente(cuadro)
        a = mide_fosa(p, lado, {}, {'semilla': 1})['lecturas'][150]['insp']['R']
        b = mide_fosa(p, lado, {'vc': True}, {'semilla': 1})['lecturas'][150]['insp']['R']
        return lectura_vasoconstrictor(a, b)['tipo']

    assert lee('cornetes', 'D') == 'vasomotora'
    assert lee('desviacion_derecha', 'D') == 'mecanica'
    assert lee('mixta', 'D') == 'mixta'
    assert lee('colapso_valvular', 'I') == 'mecanica'


def test_nariz_normal_bajo_la_referencia_de_trabajo():
    for lado in LADOS:
        r = mide_fosa(paciente('normal'), lado, {}, {'semilla': 2})
        assert r['lecturas'][150]['insp']['R'] <= REF_150
        assert abs(r['lecturas'][150]['insp']['R'] - r['verdad'][150]) / r['verdad'][150] < 0.05, \
            'sin errores, el equipo mide la verdad'


def test_colapso_valvular_peor_al_inspirar_y_meseta_forzada():
    p = paciente('colapso_valvular')
    r = mide_fosa(p, 'D', {}, {'semilla': 1})
    assert r['lecturas'][150]['insp']['R'] > 1.3 * r['lecturas'][150]['esp']['R']
    fz = mide_fosa(p, 'D', {}, {'semilla': 1, 'forzada': True})
    assert fz['pico']['insp'] > 2 * r['pico']['insp']

    # Meseta: de 450 a 850 Pa el flujo casi no crece.
    def v(P):
        return next(q for q in fz['media']['insp'] if q[0] >= P)[1]

    assert v(850) / v(450) < 1.25, f'{v(450)} -> {v(850)}'


def test_perforacion_septal_mide_mal():
    r = mide_fosa(paciente('perforacion'), 'D', {}, {'semilla': 1})
    lec = r['lecturas'][75]['insp']
    medida = lec['R'] if lec else None
    assert medida is None or medida < 0.8 * r['verdad'][75], f"medida {medida}, verdad {r['verdad'][75]}"


def test_errores_de_tecnica_tuercen_como_dice_h26():
    p = paciente('normal')

    def mide(errores):
        return mide_fosa(p, 'D', {}, {'semilla': 4, 'errores': errores})

    bien = mide({})['lecturas'][150]['insp']['R']
    assert mide({'mascara': True})['lecturas'][150]['insp']['R'] > 1.2 * bien, 'fuga en la máscara: R alta'
    sello = mide({'adaptador': True})
    lec = sello['lecturas'][75]['insp']
    assert (lec['R'] if lec else 0) < 0.8 * mide({})['lecturas'][75]['insp']['R'], 'adaptador sin sellar: R baja'
    assert mide({'boca': True})['lecturas'][150]['insp'] is None, 'por la boca no llega a 150 Pa'
    irr = mide({'irregular': True})
    assert irr['cv_entre_ciclos'] > mide({})['cv_entre_ciclos']
    assert any('reproducibles' in a for a in irr['avisos'])


def test_nariz_muy_amplia_no_llega_a_150_y_avisa():
    p = paciente('normal')
    for lado in LADOS:
        p['lados'][lado]['valvula']['area'] = 1.2
        p['lados'][lado]['cornete']['mucosa'] = 0
        p['lados'][lado]['narina'] = 1.5
    r = mide_fosa(p, 'D', {}, {'semilla': 1})
    assert r['lecturas'][150]['insp'] is None
    assert '150 Pa' in r['avisos'][0]


def test_misma_semilla_misma_medicion():
    p = paciente('mixta', 12)
    a = mide_fosa(p, 'I', {'minuto': 30}, {'semilla': 'x'})
    b = mide_fosa(p, 'I', {'minuto': 30}, {'semilla': 'x'})
    assert a == b
    assert mide_fosa(p, 'I', {}, {'semilla': 'x'})['ciclos'] != mide_fosa(p, 'I', {}, {'semilla': 'y'})['ciclos']


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

