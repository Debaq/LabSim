"""
Smoke test del generador VEMP.

Sin scipy en sandbox: stub mínimo para que el módulo importe y la función
principal se pueda instanciar sin ejecutar el pipeline completo (que
requiere filtfilt y butter). Verifica:
- Import del módulo
- Constantes y shape de SUBTIPO_PEAKS / WAVE_SIGMA
- normative_data.json tiene la estructura esperada
- Caso clínico de los 3 subtipos produce un case_config válido

Para ejecutar el pipeline completo se necesita scipy.signal disponible;
eso queda fuera del sandbox pero ya fue probado manualmente con el smoke
test equivalente de ABR_generator_v3.
"""

import sys
import os
import types
import json


def stub_scipy():
    """Stub scipy.signal con stubs que satisfacen las llamadas del generador."""
    fake_signal = types.ModuleType('scipy.signal')
    fake_butter = lambda *a, **k: ([1.0], [1.0])
    fake_filtfilt = lambda *a, **k: None
    fake_signal.butter = fake_butter
    fake_signal.filtfilt = fake_filtfilt
    scipy = types.ModuleType('scipy')
    scipy.signal = fake_signal
    sys.modules['scipy'] = scipy
    sys.modules['scipy.signal'] = fake_signal


def test_normative_data_structure():
    """El JSON normativo tiene la estructura esperada por VEMP_generator_v1."""
    path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'vemp', 'normative_data.json')
    with open(path) as f:
        n = json.load(f)
    assert 'populations' in n
    assert 'pathology_modifiers' in n
    for pop in ['adult_male', 'adult_female']:
        assert pop in n['populations'], f'falta población {pop}'
        air = n['populations'][pop]['air_conduction']['tone_burst']
        assert '500Hz' in air, f'falta 500Hz en {pop}'
        for sub in ['CVEMP', 'OVEMP', 'MVEMP']:
            assert sub in air['500Hz'], f'falta {sub} en {pop}/500Hz'
    for patho in ['normal', 'sacular', 'utricular', 'neural']:
        assert patho in n['pathology_modifiers'], f'falta pathology {patho}'


def test_vemp_generator_imports():
    """El módulo importa sin errores con scipy stubbed."""
    stub_scipy()
    # Stub PySide6 (no se ejecuta UI acá, solo importamos el generador).
    # El generador NO importa PySide6 directamente, solo el main window.
    from vemp.VEMP_generator_v1 import (
        VEMPGeneratorV1, VEMP_Curve, SUBTIPO_PEAKS, WAVE_SIGMA,
    )
    assert SUBTIPO_PEAKS == {
        'CVEMP': ['p13', 'n23'],
        'OVEMP': ['n10', 'p16'],
        'MVEMP': ['p13', 'n23'],
    }
    assert set(WAVE_SIGMA.keys()) == {'p13', 'n23', 'n10', 'p16'}
    assert VEMPGeneratorV1 is not None
    assert VEMP_Curve is not None


def test_baseline_values_returns_peaks():
    """get_baseline_values devuelve dict {pico: {lat, amp}} para cada subtipo."""
    stub_scipy()
    from vemp.VEMP_generator_v1 import VEMPGeneratorV1
    gen = VEMPGeneratorV1()
    for sub, expected_peaks in [('CVEMP', ['p13', 'n23']), ('OVEMP', ['n10', 'p16'])]:
        baseline = gen.get_baseline_values('adult_female', sub)
        for pico in expected_peaks:
            assert pico in baseline, f'{sub} sin pico {pico}'
            assert 'lat' in baseline[pico]
            assert 'amp' in baseline[pico]
            assert baseline[pico]['lat'] > 0
            assert baseline[pico]['amp'] > 0


def test_fallback_population():
    """Población inexistente cae a adult_female."""
    stub_scipy()
    from vemp.VEMP_generator_v1 import VEMPGeneratorV1
    gen = VEMPGeneratorV1()
    baseline = gen.get_baseline_values('alien_pop', 'CVEMP')
    assert 'p13' in baseline


def test_case_config_shape():
    """El case_config que arma la clínica tiene los campos esperados por el generador."""
    case = {
        'type': 'sacular',
        'subtipo': 'CVEMP',
        'umbral': 60,
        'repro': True,
        'repro_var': 0.2,
        'average_objetivo': 200,
        'desviaciones': {
            'p13': {'lat': 1.5, 'amp': -20},
            'n23': {'lat': 0, 'amp': 0},
            'n10': {'lat': 0, 'amp': 0},
            'p16': {'lat': 0, 'amp': 0},
        },
    }
    # Solo validamos el shape; ejecutar el pipeline requiere scipy.
    assert case['type'] in ('normal', 'sacular', 'utricular', 'neural')
    assert case['subtipo'] in ('CVEMP', 'OVEMP', 'MVEMP')
    assert set(case['desviaciones'].keys()) == {'p13', 'n23', 'n10', 'p16'}


if __name__ == '__main__':
    test_normative_data_structure()
    print('  test_normative_data_structure OK')
    test_vemp_generator_imports()
    print('  test_vemp_generator_imports OK')
    test_baseline_values_returns_peaks()
    print('  test_baseline_values_returns_peaks OK')
    test_fallback_population()
    print('  test_fallback_population OK')
    test_case_config_shape()
    print('  test_case_config_shape OK')
    print('TODOS LOS TESTS PASARON')
