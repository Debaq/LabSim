"""
Tests de la electrococleografía (src/abr/ecochg.py + el enganche en
ABR_generator).

El ECochG comparte con el ABR el equipo entero --electrodos, rechazo de
artefacto, promediador, ruido, FSP-- y se separa en lo único que de verdad
cambia: qué se registra y cómo se mide. Estos tests cubren esa separación:

1. El trazo tiene los tres potenciales (MC, PS, PA) y no las ondas I-V.
2. La MC invierte con la polaridad y se cancela en alternada; el PS y el
   PA no la miran. Es lo que separa una desincronía de un hidrops.
3. La razón PS/PA que mide el alumno es la que el caso declara, en las
   tres posiciones de electrodo, y cada una contra su propio límite.
4. La razón de áreas se mueve más que la de amplitudes (el sumación del
   hidrops sube Y se prolonga).
5. Sin bloque de ECochG en el caso no hay registro: no se inventa un oído
   normal para que el equipo tenga algo que dibujar.
6. El PS necesita nivel: medir la razón a nivel bajo la da chica.
7. La ventana de análisis del FSP es la suya (el ECochG termina antes de
   que empiece la del ABR).
"""

import os
import statistics
import sys

import numpy as np

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from abr import ecochg as E
from abr.protocols import get_protocol

from abr.ABR_generator import default_settings
from abr.ECochG_generator import ECochG_Curve


CAPTURAS = ('R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8')


def _curva(sp_ap=0.25, montage='tympanic', pol='Alternada', inty=90,
           rate=11.1, umbral=20, capture='R1', stim='Click', extra=None,
           technical=None, avance=1.0, hp='10'):
    """Una captura de ECochG completa, como la pide AbrMainWindow."""
    tec = default_settings('ECochG')
    tec['montage'] = montage
    tec.update(technical or {})
    control = {'test': 'ECochG', 'stim': stim, 'pol': pol, 'int': inty,
               'mkg': 0, 'rate': rate, 'filter_down': '3000',
               'filter_passhigh': hp, 'average': 1500, 'side': 'OD',
               'atten': False, 'clamp': False}
    caso = {'umbral': umbral, 'type': 'normal', 'average_objetivo': 1500}
    if sp_ap is not None:
        caso['ecochg'] = dict({'sp_ap': sp_ap}, **(extra or {}))
    t, y, meta = ECochG_Curve(inty, control, caso, [avance, 1500],
                              done=avance >= 1.0,
                              patient={'edad': 35, 'gender': 1},
                              capture_id=capture, technical=tec)
    # Espejo del retorno de ABR_Curve, para que los tests no cambien de
    # forma: el ECochG no tiene canal contra ni jitter de repro.
    return t, y, None, None, 0, meta


def _marcas(t, y, ap_lat):
    """Las cuatro marcas bien puestas, como las pondría un alumno.

    La base sale del tramo pre-estímulo, el PA del pico y el PS del hombro
    a SP_SHOULDER_MS antes; el retorno es el primer cruce de la base
    después del PA.
    """
    base = float(np.mean(y[t < 0.25]))
    i_pa = int(np.argmin(np.abs(t - ap_lat)))
    cruces = np.where(y[i_pa:] >= base)[0]
    marcas = {'BL': (0.15, base),
              'PS': (ap_lat - E.SP_SHOULDER_MS, 0.0),
              'PA': (ap_lat, 0.0)}
    if len(cruces):
        marcas['FIN'] = (float(t[i_pa + cruces[0]]), 0.0)
    return marcas


def _medida(**kw):
    t, y, _, _, _, meta = _curva(**kw)
    return E.measure_complex(t, y, _marcas(t, y, meta['ecochg_ap_lat'])), meta


def _promedio(clave, **kw):
    valores = []
    for cap in CAPTURAS:
        medida, _ = _medida(capture=cap, **kw)
        if medida.get(clave) is not None:
            valores.append(medida[clave])
    return statistics.mean(valores) if valores else None


# ------------------------------------------------------------- protocolo

def test_the_protocol_is_implemented_and_brings_its_own_equipment():
    """El combo deja elegir ECochG porque hay generador detrás."""
    p = get_protocol('ECochG')
    assert p.implemented
    assert p.montage == 'tympanic'
    # Pasa-alto bajo: el potencial de sumación es un desplazamiento DC y un
    # pasa-alto de ABR (100 Hz) se lo lleva puesto.
    assert p.filter_high <= 10
    # Ventana corta pero suficiente para que el complejo vuelva a la base.
    assert 5 < p.window_ms <= 15
    # Tasa lenta: el PA se adapta y el examen se hace con el PA entero.
    assert p.rate <= 21.1


def test_without_an_ecochg_block_the_case_gives_nothing():
    """Sin dato del backend no se inventa un oído normal."""
    assert E.case_params(None) is None
    assert E.case_params({}) is None
    completo = E.case_params({'sp_ap': 0.5})
    assert completo['sp_ap'] == 0.5
    # Lo que el caso no declara cae en el default, no desaparece.
    assert completo['mc'] == 'normal'
    assert completo['tasa'] == 1.0


def test_the_electrode_moves_the_ratio_and_its_limit_together():
    """El mismo oído no cambia de diagnóstico al cambiar de electrodo."""
    for declarado in (0.20, 0.35, 0.55):
        veredictos = set()
        for montaje in E.ELECTRODE_GAIN:
            razon = E.sp_ap_for_electrode(declarado, montaje)
            veredictos.add(razon > E.SP_AP_LIMIT[montaje])
        assert len(veredictos) == 1, declarado


# ----------------------------------------------------------- el registro

def test_no_ecochg_data_means_no_recording():
    """Elegir ECochG sobre un caso que no lo trae no dibuja un ABR de 10 ms."""
    t, y, _, _, _, meta = _curva(sp_ap=None)
    assert meta['ecochg_sin_datos'] is True
    assert meta['recording'] is False
    assert meta['ecochg'] is False


def test_the_measured_ratio_is_the_one_the_case_declares():
    """Lo que el alumno mide bien es lo que el docente configuró.

    Es la condición para que el caso se pueda poner en el borde del límite
    a propósito: si el trazo devolviera otra cosa, un oído declarado en
    0.38 se informaría como hidrops.

    La tolerancia es del tamaño del error de medición de una captura
    sola (~±0.08, que es lo que reporta la bibliografía para el
    test-retest de esta razón): lo que se exige acá es que no haya SESGO,
    no que el ruido no exista.
    """
    for declarado in (0.20, 0.30, 0.40, 0.55):
        medido = _promedio('sp_ap', sp_ap=declarado)
        assert abs(medido - declarado) < 0.07, (declarado, medido)


def test_the_ratio_is_read_against_the_limit_of_its_own_electrode():
    """Cada posición de electrodo mide su propio número."""
    for montaje in ('extratympanic', 'tympanic', 'transtympanic'):
        sano = _promedio('sp_ap', sp_ap=0.20, montage=montaje)
        hidrops = _promedio('sp_ap', sp_ap=0.55, montage=montaje)
        limite = E.SP_AP_LIMIT[montaje]
        assert sano < limite < hidrops, (montaje, sano, hidrops)


def test_the_closer_electrode_gets_a_bigger_response():
    """Meterse hasta la membrana no es capricho: el PA crece."""
    amps = [_promedio('ap_amp', montage=m)
            for m in ('extratympanic', 'tympanic', 'transtympanic')]
    assert amps[0] < amps[1] < amps[2]
    # Y con el electrodo timpánico el PA está en el rango real (uV, no
    # decimas de uV como una onda I de superficie).
    assert 1.5 < amps[1] < 6.0


def test_alternating_polarity_cancels_the_cochlear_microphonic():
    """La MC entra con signo y el promedio de las dos polaridades la borra.

    No es un caso aparte con factores propios: la alternada se calcula
    promediando rarefacción y condensación, que es lo que el equipo hace
    barrido a barrido. Por eso una desincronía auditiva se busca con las
    dos polaridades por separado.
    """
    t, y_alt, _, _, _, meta = _curva(pol='Alternada', extra={'mc': 'amplificada'})
    _, y_rar, _, _, _, _ = _curva(pol='Rarefacción', extra={'mc': 'amplificada'})
    _, y_con, _, _, _, _ = _curva(pol='Condensación', extra={'mc': 'amplificada'})
    # La microfónica vive en la diferencia entre polaridades...
    mc = (y_rar - y_con) / 2.0
    ventana = (t > 0.2) & (t < meta['ecochg_ap_lat'])
    assert np.abs(mc[ventana]).max() > 0.5
    # ...y NO en la alternada, donde queda el PS y el PA solos.
    promedio = (y_rar + y_con) / 2.0
    assert np.abs(promedio - y_alt).max() < np.abs(mc[ventana]).max() / 3


def test_an_amplified_microphonic_does_not_change_the_sp_ap_ratio():
    """La MC es otro hallazgo, no una razón PS/PA más alta.

    El mismo registro contesta dos preguntas distintas --hidrops en la
    alternada, desincronía en la resta de polaridades-- y una no puede
    contaminar a la otra.
    """
    normal = _promedio('sp_ap', sp_ap=0.30)
    amplificada = _promedio('sp_ap', sp_ap=0.30, extra={'mc': 'amplificada'})
    assert abs(normal - amplificada) < 0.05


def test_the_summating_potential_needs_level():
    """El ECochG se hace a 90 dB, no en una serie descendente.

    El PA existe hasta el umbral, pero el PS solo se hace medible con la
    cóclea bien empujada: medir la razón a nivel bajo la da CHICA aunque el
    oído tenga hidrops, y el equipo no avisa.
    """
    assert E.sp_level_factor(80) == 1.0
    assert E.sp_level_factor(20) == 0.0
    assert 0 < E.sp_level_factor(50) < 1
    alto = _promedio('sp_ap', sp_ap=0.55, inty=90, umbral=20)
    bajo = _promedio('sp_ap', sp_ap=0.55, inty=50, umbral=20)
    assert bajo < alto / 2


# -------------------------------------------------------------- medidas

def test_the_automatic_marking_reads_the_trace_and_nothing_else():
    """El marcado automático es el del equipo, no la respuesta del caso.

    Encuentra el PA como el PRIMER mínimo hondo del rango fisiológico (no
    el más hondo: con un sumación grande el N2 llega a medir casi lo
    mismo), la base en el tramo previo y el retorno en el cruce. El hombro
    del PS va por convención, a SP_SHOULDER_MS del PA -- ver TODO.md.
    """
    for montaje in ('tympanic', 'transtympanic'):
        for declarado in (0.25, 0.40, 0.55):
            razones = []
            for cap in CAPTURAS:
                t, y, _, _, _, meta = _curva(sp_ap=declarado, montage=montaje,
                                             capture=cap)
                auto = E.auto_marks(t, y)
                assert set(auto) == set(E.MARKS) | set(E.AREA_MARKS), (montaje, declarado, auto)
                assert abs(auto['PA'] - meta['ecochg_ap_lat']) < 0.15
                medida = E.measure_complex(
                    t, y, {k: (v, 0.0) for k, v in auto.items()})
                razones.append(medida['sp_ap'])
            esperado = E.sp_ap_for_electrode(declarado, montaje)
            assert abs(statistics.mean(razones) - esperado) < 0.06, \
                (montaje, declarado, statistics.mean(razones), esperado)


def test_the_automatic_marking_does_not_invent_a_complex():
    """Sin deflexión donde debería estar el PA, no marca nada."""
    t = np.linspace(0, 10, 400)
    assert E.auto_marks(t, np.zeros_like(t)) == {}
    # Una curva que solo sube tampoco tiene PA: el PA es una deflexión
    # NEGATIVA respecto de la base (el electrodo activo es el del oído).
    assert E.auto_marks(t, t * 0.1) == {}


def test_the_measurement_says_which_marks_are_missing():
    """Sin las marcas no hay medida, y se dice cuál falta."""
    t = np.linspace(0, 10, 400)
    y = np.zeros_like(t)
    assert set(E.measure_complex(t, y, {})['faltan']) == {'BL', 'PS', 'PA'}
    medida = E.measure_complex(t, y, {'BL': (0.1, 0.0), 'PS': (1.0, 0.0),
                                      'PA': (1.5, 0.0)})
    # Con las tres primeras ya hay razón de amplitudes; el área necesita el
    # retorno a la base.
    assert medida['faltan'] == ['FIN']
    assert 'area_ratio' not in medida


def test_the_area_ratio_moves_more_than_the_amplitude_one():
    """El sumación del hidrops sube Y se prolonga.

    Si solo cambiara de altura, las dos razones dirían exactamente lo mismo
    y la de áreas no agregaría nada. Con el método publicado la de áreas
    parte de 1 (el complejo entero contra el PA), así que se compara cuánto
    pasa cada una SU límite: el área lo pasa por más.
    """
    limites = E.normative('tympanic')
    lim_amp, lim_area = limites['sp_ap'][1], limites['area_ratio'][1]
    amp_mal = _promedio('sp_ap', sp_ap=0.50)
    area_sano = _promedio('area_ratio', sp_ap=0.25)
    area_mal = _promedio('area_ratio', sp_ap=0.50)
    assert area_mal / lim_area > amp_mal / lim_amp, (area_mal, amp_mal)
    assert area_sano < lim_area < area_mal
    # Y el oído sano cae donde los controles publicados (1.34 ± 0.30).
    assert 1.04 < area_sano < 1.64, area_sano


def test_the_action_potential_widens_in_hydrops():
    """El PA no solo queda chico contra el PS: se desincroniza."""
    sano = _promedio('ancho_pa', sp_ap=0.25)
    mal = _promedio('ancho_pa', sp_ap=0.60)
    assert mal > sano
    assert sano < E.normative('tympanic')['ancho_pa'][1] < mal


def test_the_rate_shift_needs_two_captures():
    """El corrimiento por tasa es una comparación, no un número por curva."""
    assert E.rate_shift([]) is None
    assert E.rate_shift([{'rate': 11.1, 'ap_lat': 1.5, 'ap_amp': 3.0}]) is None
    fuera = E.rate_shift([{'rate': 11.1, 'ap_lat': 1.5, 'ap_amp': 3.0},
                          {'rate': 91.0, 'ap_lat': 1.9, 'ap_amp': 1.5}])
    assert abs(fuera['d_lat'] - 0.4) < 1e-9
    assert round(fuera['d_amp_pct']) == -50


def test_raising_the_rate_delays_and_shrinks_the_action_potential():
    """El PA se adapta: es el mismo modelo de tasa que la onda I del ABR."""
    lento, _ = _medida(rate=11.1, sp_ap=0.25)
    rapido, _ = _medida(rate=91.0, sp_ap=0.25)
    fuera = E.rate_shift([
        {'rate': 11.1, 'ap_lat': lento['ap_lat'], 'ap_amp': lento['ap_amp']},
        {'rate': 91.0, 'ap_lat': rapido['ap_lat'], 'ap_amp': rapido['ap_amp']},
    ])
    assert fuera['d_lat'] > 0
    assert fuera['d_amp_pct'] < 0


def test_the_case_can_declare_a_worse_adaptation():
    """El corrimiento por tasa separa un oído sano de uno con hidrops.

    No hay un modelo de tasa aparte: se agrega sobre la misma pendiente que
    usa la onda I del ABR, con `tasa` diciendo cuánto MÁS se adapta este
    oído que uno sano.
    """
    def corrimiento(tasa):
        lento, _ = _medida(rate=11.1, sp_ap=0.25, extra={'tasa': tasa})
        rapido, _ = _medida(rate=91.0, sp_ap=0.25, extra={'tasa': tasa})
        return E.rate_shift([
            {'rate': 11.1, 'ap_lat': lento['ap_lat'], 'ap_amp': lento['ap_amp']},
            {'rate': 91.0, 'ap_lat': rapido['ap_lat'], 'ap_amp': rapido['ap_amp']},
        ])
    sano = corrimiento(1.0)
    malo = corrimiento(2.5)
    limite = E.normative('tympanic')['d_lat'][1]
    assert sano['d_lat'] < limite < malo['d_lat']
    assert malo['d_amp_pct'] < sano['d_amp_pct']


def test_the_case_can_widen_the_rarefaction_condensation_gap():
    """La separación entre polaridades es del oído, no una constante.

    En un oído sano el PA de condensación llega 0.1 ms después (es el
    efecto de polaridad de la onda I); con la membrana desplazada la
    separación crece, y se mide comparando las dos curvas.
    """
    def separacion(ms):
        _, _, _, _, _, rar = _curva(pol='Rarefacción', extra={'rar_cond_ms': ms})
        _, _, _, _, _, con = _curva(pol='Condensación', extra={'rar_cond_ms': ms})
        return con['ecochg_ap_lat'] - rar['ecochg_ap_lat']
    assert separacion(0.6) > separacion(0.1) + 0.2


# ------------------------------------------------------- equipo compartido

def test_the_fsp_uses_the_ecochg_window():
    """Con la ventana del ABR el FSP daba 1.0 siempre.

    El ECochG entero termina antes de que empiece la ventana de la onda V:
    analizándolo ahí, el equipo nunca declaraba respuesta presente por
    mucho que se promediara.
    """
    _, _, _, _, _, meta = _curva()
    assert meta['fsp'] > 3.0
    assert meta['fsp_a_rms'] > 0


def test_the_trace_settles_while_it_averages():
    """La promediación tiene que verse, no solo correr.

    El ruido que trae el paciente es el MISMO corra la prueba que corra: si
    se lo despeja con la curva del ECochG al nivel de referencia --donde el
    potencial de sumación vale cero-- sale ~0, y el complejo aparece entero
    en el primer bloque de barridos. El contador avanza y en pantalla no
    pasa nada.
    """
    residuales = []
    for avance in (0.05, 0.2, 1.0):
        tec = default_settings('ECochG')
        control = {'test': 'ECochG', 'stim': 'Click', 'pol': 'Alternada',
                   'int': 90, 'mkg': 0, 'rate': 11.1, 'filter_down': '3000',
                   'filter_passhigh': '10', 'average': 1500, 'side': 'OD',
                   'atten': False, 'clamp': False}
        caso = {'umbral': 20, 'type': 'normal', 'average_objetivo': 1500,
                'ecochg': {'sp_ap': 0.25}}
        _, _, meta = ECochG_Curve(
            90, control, caso, [avance, 1500], done=False,
            patient={'edad': 35, 'gender': 1}, capture_id='R1', technical=tec)
        residuales.append(meta['residual_noise_nv'])
    assert residuales[0] > residuales[1] > residuales[2], residuales
    # Y al principio hay ruido de verdad: no es un trazo limpio al que le
    # baja un decimal.
    assert residuales[0] > 2 * residuales[-1], residuales


def test_getting_closer_to_the_cochlea_buys_signal_to_noise():
    """Meterse hasta la membrana mejora la relación señal/ruido.

    El ruido es del paciente y del amplificador, no de la cóclea: el mismo
    registro con un electrodo más cerca trae más respuesta sobre el mismo
    piso de ruido. Esa es la razón de meterse hasta la membrana, y se tiene
    que poder leer en el FSP y en cuánto salta la razón medida entre dos
    capturas iguales.
    """
    fsps, ruidos, saltos = [], [], []
    for montaje in ('extratympanic', 'tympanic', 'transtympanic'):
        medidas, propios, ruido = [], [], []
        for cap in CAPTURAS:
            _, _, _, _, _, meta = _curva(montage=montaje, capture=cap)
            propios.append(meta['fsp'])
            ruido.append(meta['residual_noise_nv'])
            medida, _ = _medida(montage=montaje, capture=cap)
            if medida.get('sp_ap') is not None:
                medidas.append(medida['sp_ap'])
        fsps.append(statistics.mean(propios))
        ruidos.append(statistics.mean(ruido))
        saltos.append(statistics.pstdev(medidas))
    assert fsps[0] < fsps[1] < fsps[2], fsps
    # El piso de ruido es el mismo: lo que cambia es cuánta respuesta llega.
    # Se compara el promedio de varias capturas porque el residual de UNA
    # tiene mucha varianza (la ondulación lenta que deja entrar el
    # pasa-alto bajo tiene pocos grados de libertad en una ventana corta).
    assert max(ruidos) / min(ruidos) < 1.5, ruidos
    # Y la medida se vuelve más reproducible al acercarse.
    assert saltos[0] > saltos[1] > saltos[2], saltos


def test_the_band_does_not_charge_high_frequency_noise_for_low_cuts():
    """Lo que deja entrar un pasa-alto bajo es ruido LENTO.

    En una ventana de diez milisegundos no entra ni un ciclo de 10 Hz: ese
    ruido se ve como una línea de base que se va para arriba o para abajo
    en cada barrido, no como un trazo peludo. Importa porque la banda de
    10 Hz es la OBLIGATORIA del ECochG --no es un error del alumno-- y
    cobrándola como ruido parejo la razón PS/PA quedaba con 40% de
    dispersión y no se podía separar un oído normal de uno con hidrops.

    Una medida de base a pico se come casi todo ese error, porque las dos
    marcas están a menos de un milisegundo y la ondulación las mueve
    juntas. Eso es lo que este test mide.
    """
    from abr.ABR_generator import ABRGenerator
    gen = ABRGenerator()
    rng = np.random.default_rng(11)
    n = 416
    ancho = gen.sweep_noise(n, 200, rng, band_factor=3.16)
    # El RMS total es el que declara la banda: el ruido residual que
    # muestra el equipo no cambia.
    assert abs(float(np.mean(np.std(ancho, axis=1))) - 3.16) < 0.4
    # Pero la diferencia entre dos puntos cercanos --que es como se mide
    # una amplitud-- crece mucho menos que el RMS.
    angosto = gen.sweep_noise(n, 200, rng, band_factor=1.0)
    salto = 25                       # ~0.6 ms en una ventana de 10 ms
    def cercanos(m):
        return float(np.mean(np.std(m[:, salto:] - m[:, :-salto], axis=1)))
    assert cercanos(ancho) < 2.0 * cercanos(angosto), \
        (cercanos(ancho), cercanos(angosto))


def test_the_ecochg_has_no_shadow_curve_and_no_contra_channel():
    """Un electrodo timpánico está pegado a ESTA cóclea.

    La curva sombra es de campo lejano; lo que el timpánico capta del otro
    oído queda muy por debajo de su propia respuesta. Por eso el ECochG no
    es la prueba con la que se enseña enmascaramiento.
    """
    _, _, dx, dy, _, meta = _curva()
    assert dy is None and dx is None
    assert meta['contra'] is None
    assert meta['shadow'] is False


def test_the_shading_is_exactly_what_is_integrated():
    """Lo achurado en el gráfico da el mismo número que la tabla, y el
    lóbulo del PA termina en el P1 aunque haya hidrops (el N2 no entra)."""
    for sp_ap in (0.25, 0.55):
        t, y, _, _, _, _ = _curva(sp_ap=sp_ap)
        marcas = {k: (v, float(np.interp(v, t, y)))
                  for k, v in E.auto_marks(t, y).items()}
        medida = E.measure_complex(t, y, marks=marcas)
        zonas = E.area_shading(t, y, marcas)
        for clave, area in (('ps', 'area_ps'), ('pa', 'area_pa')):
            x, arriba, abajo = zonas[clave]
            achurado = float(np.trapezoid(arriba - abajo, x))
            assert abs(achurado - medida[area]) < 1e-6 * max(1.0, medida[area])
        x_pa = zonas['pa'][0]
        assert x_pa[-1] < medida['ap_lat'] + E.N2_MS - 0.2, (sp_ap, x_pa[-1])


# ------------------------------------------------------------- tone burst

BURST_LARGO = {'window_ms': 20, 'burst_envelope': 'ms-1-10-1'}


def test_the_burst_envelope_is_read_in_cycles_or_in_ms():
    """'2-1-2' va en ciclos del tono; 'ms-1-10-1' en milisegundos."""
    assert E.burst_timing('2-1-2', 1000) == (2.0, 1.0, 2.0)
    assert E.burst_timing('2-1-2', 4000) == (0.5, 0.25, 0.5)
    assert E.burst_timing('ms-1-10-1', 1000) == (1.0, 10.0, 1.0)
    assert E.burst_timing('ms-1-10-1', 4000) == (1.0, 10.0, 1.0)
    # Una clave rota no tira la captura: cae en la de rutina.
    assert E.burst_timing('basura', 1000) == E.burst_timing(None, 1000)


def test_with_a_long_burst_the_sp_lasts_as_long_as_the_stimulus():
    """Con 1-10-1 ms el sumación es una meseta de ~12 ms, no un hombro.

    Se mira en alternada (sin MC) y con el pasa-alto bajo, que es como se
    registra: con 10 Hz la meseta se cae sola en 10 ms.
    """
    t = None
    mitad, despues = [], []
    for cap in CAPTURAS:
        t, y, _, _, _, _ = _curva(sp_ap=0.55, stim='Burst 1 kHz', hp='3.3',
                                  technical=BURST_LARGO, capture=cap)
        base = float(np.mean(y[t < 0.3]))
        mitad.append(base - float(np.mean(y[(t > 5) & (t < 9)])))
        despues.append(base - float(np.mean(y[(t > 16) & (t < 19)])))
    assert statistics.mean(mitad) > 1.0, mitad
    assert statistics.mean(mitad) > 3 * abs(statistics.mean(despues)), \
        (mitad, despues)


def test_with_a_burst_the_hydrops_deepens_the_plateau():
    """Mismo burst, mismo nivel: el hidrops deja la meseta más honda."""
    def meseta(sp_ap):
        valores = []
        for cap in CAPTURAS:
            t, y, _, _, _, _ = _curva(sp_ap=sp_ap, stim='Burst 1 kHz',
                                      hp='3.3', technical=BURST_LARGO,
                                      capture=cap)
            base = float(np.mean(y[t < 0.3]))
            valores.append(base - float(np.mean(y[(t > 5) & (t < 9)])))
        return statistics.mean(valores)
    sano, hidrops = meseta(0.25), meseta(0.55)
    assert hidrops > 1.6 * sano, (sano, hidrops)


def test_with_a_short_burst_the_plateau_ends_early():
    """El 2-1-2 de rutina a 1 kHz dura 5 ms: a los 8 ms ya no hay meseta."""
    corto = {'window_ms': 20, 'burst_envelope': '2-1-2'}
    valores = []
    for cap in CAPTURAS:
        t, y, _, _, _, _ = _curva(sp_ap=0.55, stim='Burst 1 kHz', hp='3.3',
                                  technical=corto, capture=cap)
        base = float(np.mean(y[t < 0.3]))
        valores.append(base - float(np.mean(y[(t > 8) & (t < 11)])))
    assert statistics.mean(valores) < 0.5, valores


def test_automatic_marking_with_a_burst_reads_the_sp_mid_plateau():
    """El equipo sabe qué burst mandó: el PS va a la mitad de la meseta y
    el retorno, después de que el estímulo terminó."""
    from abr.ECochG_generator import burst_ps_ms
    ps_at = burst_ps_ms('Burst 1 kHz', BURST_LARGO)
    assert 5.5 <= ps_at <= 7.5, ps_at
    assert burst_ps_ms('Click', BURST_LARGO) is None
    t, y, _, _, _, _ = _curva(sp_ap=0.55, stim='Burst 1 kHz', hp='3.3',
                              technical=BURST_LARGO)
    auto = E.auto_marks(t, y, ps_at=ps_at)
    assert auto['PS'] == ps_at
    assert auto['PA'] < 4.0, auto
    assert auto.get('FIN', 0) > 11.0, auto


def test_with_a_burst_the_click_limits_are_not_painted():
    """Las razones con burst se miden pero no se comparan contra los
    límites del click: un oído sano saldría pintado de hidrops."""
    click = E.normative('tympanic')
    burst = E.normative('tympanic', burst=True)
    assert click['sp_ap'] == (None, 0.40)
    assert click['area_ratio'] == (None, 1.94)
    assert 'sp_ap' not in burst and 'area_ratio' not in burst
    assert burst['d_rc'] == click['d_rc'] == (None, E.RAR_COND_LIMIT_MS)


def test_the_limits_per_electrode():
    """Promontorio 0.35, tímpano 0.40, conducto 0.50; áreas 1.94 en los
    tres (con el método publicado el electrodo mueve las dos áreas juntas)."""
    assert E.SP_AP_LIMIT == {'transtympanic': 0.35, 'tympanic': 0.40,
                             'extratympanic': 0.50}
    assert set(E.AREA_RATIO_LIMIT.values()) == {1.94}
    assert E.RAR_COND_LIMIT_MS == 0.38


# ------------------------------------------------- rarefacción/condensación

def test_the_polarity_shift_needs_a_pair_at_the_same_level():
    """Una de cada polaridad, mismo estímulo y nivel."""
    assert E.polarity_shift([]) is None
    solo = [{'pol': 'Rarefacción', 'stim': 'Click', 'int': 90, 'ap_lat': 1.4}]
    assert E.polarity_shift(solo) is None
    distinto_nivel = solo + [{'pol': 'Condensación', 'stim': 'Click',
                              'int': 70, 'ap_lat': 1.9}]
    assert E.polarity_shift(distinto_nivel) is None
    par = distinto_nivel + [{'pol': 'Condensación', 'stim': 'Click',
                             'int': 90, 'ap_lat': 1.85}]
    shift = E.polarity_shift(par)
    assert shift['int'] == 90.0
    assert abs(shift['d_rc'] - 0.45) < 1e-9
    # Sin el PA marcado no hay comparación.
    sin_marca = solo + [{'pol': 'Condensación', 'stim': 'Click', 'int': 90,
                         'ap_lat': None}]
    assert E.polarity_shift(sin_marca) is None


def test_the_measured_polarity_shift_follows_the_case():
    """Lo que el caso declara en rar_cond_ms es lo que separa los PA."""
    for declarado in (0.1, 0.5):
        difs = []
        for cap in CAPTURAS:
            lat = {}
            for pol in ('Rarefacción', 'Condensación'):
                t, y, _, _, _, _ = _curva(
                    sp_ap=0.25, pol=pol, capture=cap,
                    extra={'rar_cond_ms': declarado})
                lat[pol] = E.auto_marks(t, y)['PA']
            difs.append(lat['Condensación'] - lat['Rarefacción'])
        assert abs(statistics.mean(difs) - declarado) < 0.1, (declarado, difs)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
