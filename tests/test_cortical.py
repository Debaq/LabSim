"""
Tests del motor de latencia media y tardía (abr/cortical.py) y de su
generador (abr/Cortical_generator.py).

Los casos clínicos son los de la clase 10-11 de Electrofisiología:
1. ACV de la cerebral media derecha: efecto electrodo en C4 con los dos oídos.
2. Niña con implante a los 5 años: P1 tardía para la edad.
3. Mujer de 72 años con olvidos: P300 prolongada con exógenos normales.

Y lo técnico que la clase pide reconocer: el filtro pasa-alto que se come
la Pa, la tasa que habitúa la N1, el PAM con referencia en mastoides, el
sueño del niño, la MMN que necesita desviantes y el oddball sin desviación.
"""

import os
import sys

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
# El generador del ABR lee su normativa con ruta relativa a la raíz.
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np

from abr import cortical
from abr.Cortical_generator import Cortical_Curve
from abr.protocols import PROTOCOLS, STANDARD_SETUP, get_protocol


OIDO = {'umbral': 10, 'type': 'normal'}


def _tarea_estandar(test):
    return STANDARD_SETUP[test]['control'].get('tarea')


def _ctx(test, rate=None, sl=60, stim='Burst 1 kHz', rare='Burst 2 kHz',
         fraccion=0.2, sueno=0.5, tarea=None):
    rate = rate or get_protocol(test).rate
    return {'rate': rate, 'refractory': cortical.refractory_factor(test, rate),
            'sl': cortical.sl_factor(test, sl),
            'stim_lat': cortical.stim_latency(stim),
            'deviance': cortical.deviance(stim, rare),
            'rare_fraction': fraccion, 'sleep_draw': sueno,
            'tarea': tarea or _tarea_estandar(test) or 'ninguna'}


def _t(test):
    ventana = get_protocol(test).window_ms
    return np.linspace(0, ventana, int(ventana * cortical.SAMPLES_PER_MS[test]) + 1)


def _napa(t, y):
    """Na-Pa de una curva objetivo: valle 12-24 ms contra pico 24-40."""
    na = y[(t > 12) & (t < 24)].min()
    pa = y[(t > 24) & (t < 40)].max()
    return pa - na


def _captura(test, central, edad=30, avg=None, rate=None, hp=None, lp=None,
             stim=None, tecnica='estandar', capture='c1', lado='OD',
             fraccion=1.0, oido=None, tarea=None):
    proto = get_protocol(test)
    tec = (dict(STANDARD_SETUP[test]['technical']) if tecnica == 'estandar'
           else dict(tecnica or {}))
    control = {'stim': stim or STANDARD_SETUP[test]['control']['stim'],
               'pol': 'Alternada', 'rate': rate or proto.rate,
               'filter_down': lp or proto.filter_low,
               'filter_passhigh': hp or proto.filter_high,
               'side': lado, 'clamp': False, 'mkg': 0,
               'tarea': tarea or _tarea_estandar(test)}
    return Cortical_Curve(test, 70, control, oido or OIDO, central,
                          [fraccion, avg or proto.averages], fraccion >= 1,
                          patient={'edad': edad, 'gender': 0},
                          capture_id=capture, technical=tec)


# ------------------------------------------------------------------ caso

def test_the_four_tests_are_implemented():
    for test in cortical.TESTS:
        assert PROTOCOLS[test].implemented, test
        assert test in STANDARD_SETUP, test


def test_no_central_block_means_no_recording():
    """Sin bloque `Central` no se inventa una corteza normal."""
    assert cortical.case_params(None) is None
    assert cortical.case_params({}) is None
    for test in cortical.TESTS:
        t, y, meta = _captura(test, None)
        assert meta['cortical_sin_datos'], test
        assert not meta['waves_visible'], test


def test_case_params_clip_and_fall_back():
    p = cortical.case_params({'estado': 'hipnotizado', 'mlr_reduccion': 3,
                              'p1_retardo_ms': 'mucho'})
    assert p['estado'] == 'despierto'
    assert p['mlr_reduccion'] == 1.0
    assert p['p1_retardo_ms'] == 0.0


# ------------------------------------------------------------------ PEALM

def test_case_1_right_hemisphere_gives_an_electrode_effect():
    """ACV derecho: C4 baja con CUALQUIER oído (efecto electrodo)."""
    central = cortical.case_params({'mlr_hemisferio': 'derecho',
                                    'mlr_reduccion': 0.6})
    t = _t('MLR')
    napa = {}
    for lado in ('OD', 'OI'):
        tr = cortical.build_traces('MLR', t, 58, central, lado,
                                   _ctx('MLR', stim='Click'))
        for canal, y in tr['main'].items():
            napa[(lado, canal)] = _napa(t, y)
        assert napa[(lado, 'C4')] < 0.65 * napa[(lado, 'C3')], napa
    dif, hemi = cortical.electrode_effect(napa)
    assert hemi == 'derecho' and dif >= cortical.ELECTRODE_EFFECT_LIMIT, (dif, hemi)
    # Sin efecto oído: los dos oídos dan lo mismo en promedio.
    dif_o, _ = cortical.ear_effect(napa)
    assert dif_o < 0.15, dif_o


def test_ear_effect_lowers_every_electrode():
    central = cortical.case_params({'mlr_oido': 'OI',
                                    'mlr_oido_reduccion': 0.6})
    t = _t('MLR')
    napa = {}
    for lado in ('OD', 'OI'):
        tr = cortical.build_traces('MLR', t, 40, central, lado,
                                   _ctx('MLR', stim='Click'))
        for canal, y in tr['main'].items():
            napa[(lado, canal)] = _napa(t, y)
    for canal in cortical.CHANNELS['MLR']:
        assert napa[('OI', canal)] < 0.7 * napa[('OD', canal)], napa
    dif_e, _ = cortical.electrode_effect(napa)
    dif_o, oido = cortical.ear_effect(napa)
    assert oido == 'OI' and dif_o >= cortical.EAR_EFFECT_LIMIT
    assert dif_e < 0.2, dif_e


def test_a_sleeping_child_can_lose_pa_but_an_adult_does_not():
    t = _t('MLR')
    dormido = cortical.case_params({'estado': 'dormido'})
    despierto = cortical.case_params({'estado': 'despierto'})

    def napa(edad, central, sueno):
        """La Pa sola (el Na es subcortical y no depende del sueño)."""
        tr = cortical.build_traces('MLR', t, edad, central, 'OD',
                                   _ctx('MLR', stim='Click', sueno=sueno))
        return tr['main']['Cz'][(t > 24) & (t < 45)].max()
    # Niño de 3 años: según la etapa del sueño Pa está o no está.
    assert napa(3, dormido, 0.05) < 0.5 * napa(3, dormido, 0.95)
    # Adulto: Pa estable dormido.
    assert napa(30, dormido, 0.05) > 0.85 * napa(30, despierto, 0.05)


def test_a_high_pass_of_30_hz_eats_pa():
    """Pregunta de la clase: por qué no 30 Hz de pasa-alto en el MLR.

    El filtrado es de fase cero (como en el ABR, ver docs/decisiones.md):
    achica la Pa pero no le corre la latencia. Con el pasa-alto del ABR
    (100 Hz), que es el error de dejar el equipo como venía, no queda Pa.
    """
    from abr.ABR_generator import _get_generator
    abr = _get_generator()
    t = _t('MLR')
    fs = (len(t) - 1) / (t[-1] / 1000.0)
    y = cortical.build_traces('MLR', t, 30, cortical.case_params({'estado': 'despierto'}),
                              'OD', _ctx('MLR', stim='Click'))['main']['Cz']
    tramo = (t > 24) & (t < 40)

    def pa(hp):
        return abr.apply_filters(y, 300, hp, fs)[tramo].max()
    assert pa(30) < 0.8 * pa(10), (pa(10), pa(30))
    assert _napa(t, abr.apply_filters(y, 300, 100, fs)) < 0.2 * _napa(
        t, abr.apply_filters(y, 300, 10, fs))


def test_40_per_second_builds_the_40_hz_response():
    """A 40/s las respuestas se superponen y el trazo se vuelve periódico."""
    t = _t('MLR')
    central = cortical.case_params({'estado': 'despierto'})
    y = cortical.build_traces('MLR', t, 30, central, 'OD',
                              _ctx('MLR', rate=40.0, stim='Click'))['main']['Cz']
    paso = int(round(25.0 * cortical.SAMPLES_PER_MS['MLR']))
    tramo = y[int(30 * cortical.SAMPLES_PER_MS['MLR']):]
    r = np.corrcoef(tramo[:-paso], tramo[paso:])[0, 1]
    assert r > 0.9, r


def test_pam_is_bigger_with_the_mastoid_reference():
    central = {'estado': 'despierto', 'tension_cervical': 0.8}

    def pico_pam(montaje):
        tec = dict(STANDARD_SETUP['MLR']['technical'], montage=montaje)
        t, y, _ = _captura('MLR', central, tecnica=tec, avg=4000)
        tramo = (t > 11) & (t < 16)
        return np.abs(y['Cz'][tramo]).max()
    assert pico_pam('vertex_mastoid') > 2.0 * pico_pam('vertex_earlobe')


# ------------------------------------------------------------------ PEALT

def test_case_2_p1_is_late_for_a_six_year_old_with_late_implant():
    # Sharma 2002: latencia = 155.6 - 32.746 ln(edad).
    media, limite = cortical.p1_norm(6)
    assert abs(media - (155.6 - 32.746 * np.log(6))) < 1e-9
    assert limite < 130
    # Fuera del tramo de la regresión no se extrapola.
    assert cortical.p1_norm(60) == cortical.p1_norm(20)
    t = _t('CAEP')
    central = cortical.case_params({'p1_retardo_ms': 100})
    y = cortical.build_traces('CAEP', t, 6, central, 'OD', _ctx('CAEP'))['main']['Cz']
    p1 = t[(t > 60) & (t < 400)][np.argmax(y[(t > 60) & (t < 400)])]
    assert p1 > limite, (p1, limite)


def test_n1_appears_only_after_eight_to_ten_years():
    t = _t('CAEP')
    central = cortical.case_params({'estado': 'despierto'})

    def n1(edad):
        y = cortical.build_traces('CAEP', t, edad, central, 'OD',
                                  _ctx('CAEP'))['main']['Cz']
        return -y[(t > 80) & (t < 130)].min()
    assert n1(5) < 0.3 * n1(25)


def test_a_fast_rate_habituates_the_cortical_response():
    """Por qué el PEALT se estimula a 1/s y no a 7/s."""
    assert cortical.refractory_factor('CAEP', 7.1) < 0.3
    assert cortical.refractory_factor('MLR', 7.1) > 0.95


def test_case_3_p300_is_late_for_72_with_normal_exogenous():
    media, de = cortical.p300_norm(72)
    assert 320 <= media - 2 * de and media + 2 * de <= 410, (media, de)
    t = _t('P300')
    central = cortical.case_params({'p300_retardo_ms': 60})
    tr = cortical.build_traces('P300', t, 72, central, 'OD', _ctx('P300'))
    y = tr['main']['Pz']
    tramo = (t > 250) & (t < 600)
    p3 = t[tramo][np.argmax(y[tramo])]
    assert p3 > media + 2 * de, (p3, media, de)
    # El frecuente no tiene P3.
    frec = tr['overlays']['frecuente']['Pz']
    assert frec[tramo].max() < 0.3 * y[tramo].max()


def test_the_p300_is_highest_at_pz():
    t = _t('P300')
    tr = cortical.build_traces('P300', t, 25, cortical.case_params({'estado': 'despierto'}),
                               'OD', _ctx('P300'))
    tramo = (t > 250) & (t < 450)
    picos = {c: tr['main'][c][tramo].max() for c in ('Fz', 'Cz', 'Pz')}
    assert picos['Pz'] > picos['Cz'] > picos['Fz'], picos


def test_without_deviance_there_is_no_p300_and_no_mmn():
    t = _t('P300')
    central = cortical.case_params({'estado': 'despierto'})
    ctx = _ctx('P300', stim='Burst 1 kHz', rare='Burst 1 kHz')
    tr = cortical.build_traces('P300', t, 25, central, 'OD', ctx)
    tramo = (t > 250) & (t < 450)
    assert tr['main']['Pz'][tramo].max() - tr['overlays']['frecuente']['Pz'][tramo].max() < 0.5
    t = _t('MMN')
    tr = cortical.build_traces('MMN', t, 25, central, 'OD',
                               _ctx('MMN', stim='Burst 1 kHz', rare='Burst 1 kHz'))
    assert np.abs(tr['main']['Fz']).max() < 1e-9


def test_asleep_there_is_no_p300_and_no_count():
    central = {'estado': 'dormido'}
    _, _, meta = _captura('P300', central)
    assert meta['conteo'] is None
    t = _t('P300')
    tr = cortical.build_traces('P300', t, 25, cortical.case_params(central),
                               'OD', _ctx('P300'))
    tramo = (t > 250) & (t < 450)
    assert tr['main']['Pz'][tramo].max() - tr['overlays']['frecuente']['Pz'][tramo].max() < 0.5


def _p3(tr, t):
    """Lo que el raro tiene de más que el frecuente en Pz (250-500 ms)."""
    tramo = (t > 250) & (t < 500)
    return float((tr['main']['Pz'] - tr['overlays']['frecuente']['Pz'])[tramo].max())


def test_without_the_instruction_there_is_no_p3b_and_no_count():
    """La P3b es endógena: sin pedirle que cuente o apriete, no sale."""
    t = _t('P300')
    central = cortical.case_params({'estado': 'despierto'})
    contar = _p3(cortical.build_traces('P300', t, 25, central, 'OD',
                                       _ctx('P300', tarea='contar')), t)
    boton = _p3(cortical.build_traces('P300', t, 25, central, 'OD',
                                      _ctx('P300', tarea='boton')), t)
    for tarea in ('ninguna', 'pasiva'):
        sin = _p3(cortical.build_traces('P300', t, 25, central, 'OD',
                                        _ctx('P300', tarea=tarea)), t)
        assert sin < 0.25 * contar, (tarea, sin, contar)
        _, _, meta = _captura('P300', {'estado': 'despierto'}, tarea=tarea)
        assert meta['conteo'] is None and meta['tarea'] == tarea
    assert abs(boton - contar) < 1e-9


def test_a_big_deviance_leaves_a_small_passive_p3a():
    """Sin tarea, 1 kHz contra 4 kHz igual orienta: P3a chica y frontal."""
    t = _t('P300')
    central = cortical.case_params({'estado': 'despierto'})
    tr = cortical.build_traces('P300', t, 25, central, 'OD',
                               _ctx('P300', rare='Burst 4 kHz', tarea='ninguna'))
    tramo = (t > 200) & (t < 350)
    extra = {c: (tr['main'][c] - tr['overlays']['frecuente'][c])[tramo].max()
             for c in ('Fz', 'Pz')}
    assert 0.5 < extra['Fz'] < 3.0 and extra['Fz'] > extra['Pz'], extra


def test_the_count_and_the_button_answer_the_task():
    _, _, meta = _captura('P300', {'estado': 'despierto'}, tarea='contar')
    assert meta['conteo']['tarea'] == 'contar' and meta['conteo']['dice'] == meta['conteo']['reales']
    _, _, meta = _captura('P300', {'estado': 'despierto', 'conteo_error': 0.2},
                          tarea='boton')
    c = meta['conteo']
    assert c['tarea'] == 'boton' and c['aciertos'] <= c['reales'] and c['falsas'] >= 0


def test_attending_the_deviants_contaminates_the_mmn():
    """Contar los raros suma N2b y P3b: la diferencia ya no es solo MMN."""
    t = _t('MMN')
    central = cortical.case_params({'estado': 'despierto'})
    pasiva = cortical.build_traces('MMN', t, 25, central, 'OD',
                                   _ctx('MMN', tarea='pasiva'))['main']
    contando = cortical.build_traces('MMN', t, 25, central, 'OD',
                                     _ctx('MMN', tarea='contar'))['main']
    tardio = (t > 280) & (t < 450)
    # Pasiva queda solo la cola del N1-P2 del raro (menos de 1.5 uV).
    assert pasiva['Pz'][tardio].max() < 1.5, pasiva['Pz'][tardio].max()
    assert contando['Pz'][tardio].max() > 5.0 * pasiva['Pz'][tardio].max()
    # La MMN misma sigue ahí (Fz, 150-250 ms).
    mmn = (t > 140) & (t < 230)
    assert pasiva['Fz'][mmn].min() < -1.0


def test_the_mmn_needs_many_deviants():
    """Con 200 barridos (40 desviantes) la diferencia es puro ruido."""
    central = {'estado': 'despierto'}
    _, _, pocos = _captura('MMN', central, avg=200)
    _, _, muchos = _captura('MMN', central, avg=1500)
    assert pocos['residual_noise_nv'] > 2.0 * muchos['residual_noise_nv']
    assert muchos['rare_sweeps'] >= 150 > pocos['rare_sweeps']


# ------------------------------------------------------------------ equipo

def test_noise_drops_as_the_square_root_of_the_sweeps():
    central = {'estado': 'despierto'}
    _, _, a = _captura('CAEP', central, avg=100, capture='n1')
    _, _, b = _captura('CAEP', central, avg=1600, capture='n1')
    razon = a['residual_noise_nv'] / b['residual_noise_nv']
    assert 2.5 < razon < 6.5, razon


def test_gain_and_rejection_decide_what_enters():
    """Con la ganancia del ABR (x100.000) el amplificador satura a 50 uV
    y el EEG cortical se rechaza más; con el rechazo apagado entran los
    parpadeos."""
    central = {'estado': 'despierto'}
    base = dict(STANDARD_SETUP['P300']['technical'])
    _, _, bien = _captura('P300', central, tecnica=base)
    _, _, saturado = _captura('P300', central,
                              tecnica=dict(base, gain=100000.0))
    _, _, sin_rechazo = _captura('P300', central,
                                 tecnica=dict(base, artifact_reject_uv=0.0))
    assert saturado['artifact_acceptance'] < bien['artifact_acceptance']
    assert sin_rechazo['blinks_in_average'] and not bien['blinks_in_average']


def test_same_capture_same_trace():
    central = {'estado': 'despierto'}
    _, a, _ = _captura('MLR', central, capture='x', fraccion=0.5)
    _, b, _ = _captura('MLR', central, capture='x', fraccion=0.5)
    assert np.array_equal(a['Cz'], b['Cz'])


def test_measure_reads_the_marks():
    t = np.linspace(0, 100, 501)
    y = np.zeros_like(t)
    m = cortical.measure('MLR', t, y, {'Na': [18.0, -0.5], 'Pa': [30.0, 0.8]})
    assert m['lat'] == {'Na': 18.0, 'Pa': 30.0}
    assert abs(m['amp']['Na-Pa'] - 1.3) < 1e-9
    m = cortical.measure('MMN', t, y, {'MMN': [180.0, -2.0]})
    assert abs(m['amp']['MMN'] - 2.0) < 1e-9


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for prueba in pruebas:
        prueba()
        print(f"  ok  {prueba.__name__}")
    print("TODOS LOS TESTS PASARON")
