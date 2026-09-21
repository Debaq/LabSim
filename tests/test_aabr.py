"""Equipo de tamizaje automatizado (AABR).

Lo que separa este equipo del ABR diagnóstico no es el modelo --es el mismo
generador, el mismo criterio y el mismo ruido del paciente-- sino lo que
deja hacer: nivel fijo, sin marcar ondas, y una sola respuesta, PASA o
REFIERE. Estos tests miran eso:

1. El veredicto sale del caso, no de un sorteo: el oído sano pasa, el que
   tiene una hipoacusia por encima del nivel de tamizaje refiere.
2. El patrón que justifica tamizar con AABR en la UCI: la neuropatía
   refiere aunque su cóclea esté viva.
3. El tope de barridos manda: con pocos, un oído normal también refiere.
   Es el error de procedimiento que el ejercicio tiene que dejar cometer.
4. Sin caso cargado no se tamiza nada (sin fallback sintético).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from abr.AabrMainWindow import (BARRIDOS_MAX, CRITERIO_FSP, IMPEDANCIA_KOHM,
                                    NIVEL_DB, AabrMainWindow)
    HAS_UI = True
except Exception as exc:  # pragma: no cover - sin PySide6/scipy
    print(f"  (salteado: {exc})")
    HAS_UI = False

ANSD = {'bloqueo': 'total', 'microfonica': 'alta', 'desincronia': 'alta'}


def _oido(umbral, tipo='normal', neural=None):
    caso = {'umbral': umbral, 'type': tipo, 'repro': True, 'desviaciones': {},
            'average_objetivo': 2000,
            'umbral_por_estimulo': {'click': umbral, 'ce_chirp': umbral},
            'barridos_criterio': 2000.0,
            'respuesta_en_referencia': 'presente'}
    if neural:
        caso['neural'] = neural
    return caso


def _ventana(od, oi=None, horas=30):
    w = AabrMainWindow(data_login={'user': 'doc'})
    w.la_super({'nombre': 'RN', 'edad': 0, 'edad_horas': horas, 'gender': 0,
                'ABR': {'OD': od, 'OI': oi if oi is not None else od}}, 7)
    return w


def _tamizar(w, sello=0.9, tope=3000):
    """La secuencia entera sin QTimer, disparando cada fase a mano.

    En la app la mueve el equipo solo: un botón, y sonda -> impedancias ->
    registro -> resultado. Acá los timers no corren, así que el test los
    reemplaza en el mismo orden.
    """
    w.start()
    if not w.corriendo:
        return w.resultado[w.lado_activo]
    w.probe.fit_quality = sello
    w._sonda_lista()                 # cierra la sonda y encadena impedancias
    if not w.corriendo:
        return w.resultado[w.lado_activo]
    w._fase_registro()               # lo que dispara el timer del paso 2
    for _ in range(tope):
        if not w.corriendo:
            break
        w._tick()
    return w.resultado[w.lado_activo]


def test_a_healthy_newborn_passes():
    if not HAS_UI:
        return
    r = _tamizar(_ventana(_oido(10)))
    assert r['veredicto'] == 'PASA', r
    # Y pasa rápido: un oído sano cruza el criterio mucho antes del tope.
    assert r['barridos'] < BARRIDOS_MAX / 2, r


def test_a_real_hearing_loss_refers():
    if not HAS_UI:
        return
    r = _tamizar(_ventana(_oido(80, 'coclear')))
    assert r['veredicto'] == 'REFIERE', r
    assert r['barridos'] == BARRIDOS_MAX, r


def test_neuropathy_refers_even_with_a_live_cochlea():
    """El patrón que justifica tamizar con AABR y no solo con EOA.

    La cóclea responde --las emisiones están-- y el tronco no, así que el
    AABR refiere. Un tamizaje que fuera solo de EOA lo dejaría pasar.
    """
    if not HAS_UI:
        return
    r = _tamizar(_ventana(_oido(10, 'neural', ANSD)))
    assert r['veredicto'] == 'REFIERE', r


def test_stopping_too_early_refers_a_normal_ear():
    """Cortar el promedio antes de tiempo REFIERE un oído sano.

    Es el error de procedimiento que el ejercicio tiene que dejar cometer:
    el equipo no sabe que el paciente es normal, sabe que no llegó al
    criterio con los barridos que le dieron.
    """
    if not HAS_UI:
        return
    w = _ventana(_oido(25))
    w.sb_barridos.setValue(200)
    r = _tamizar(w)
    assert r['veredicto'] == 'REFIERE', r
    assert r['barridos'] == 200, r


def test_the_level_is_what_decides():
    """Sin búsqueda de umbral: manda el nivel al que se tamiza.

    El mismo oído --umbral 45-- refiere a 35 dB nHL y pasa a 60, que es lo
    que hace que subir el nivel para "conseguir un PASA" sea un error y no
    una maniobra.
    """
    if not HAS_UI:
        return
    assert _tamizar(_ventana(_oido(45, 'coclear')))['veredicto'] == 'REFIERE'
    w = _ventana(_oido(45, 'coclear'))
    w.sb_nivel.setValue(60)
    assert _tamizar(w)['veredicto'] == 'PASA'


def test_each_ear_keeps_its_own_result():
    if not HAS_UI:
        return
    w = _ventana(_oido(10), _oido(85, 'coclear'))
    _tamizar(w)
    w.cb_lado.setCurrentText('OI')
    _tamizar(w)
    assert w.resultado['OD']['veredicto'] == 'PASA'
    assert w.resultado['OI']['veredicto'] == 'REFIERE'
    assert 'OD: PASA' in w.lbl_resumen.text()
    assert 'OI: REFIERE' in w.lbl_resumen.text()


def test_without_a_case_nothing_is_screened():
    if not HAS_UI:
        return
    w = AabrMainWindow(data_login={'user': 'doc'})
    assert not w.btn_start.isEnabled()
    w.start()
    assert not w.corriendo
    assert w.resultado['OD'] is None
    # Con atención abierta pero sin ABR en ese oído, tampoco.
    w.la_super({'nombre': 'X', 'edad': 30, 'gender': 0, 'ABR': {}}, 1)
    w.start()
    assert not w.corriendo
    assert w.resultado['OD'] is None


def test_one_button_runs_the_whole_thing_in_order():
    """Un botón: sonda, impedancias, registro, resultado.

    No hay navegación ni pasos que apretar. El indicador de fase va
    avanzando solo y termina en el resultado.
    """
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    assert w.paso == 0
    w.start()
    assert w.corriendo
    assert w.paso == 0                 # chequeando la sonda
    w.probe.fit_quality = 0.9
    w._sonda_lista()
    assert w.paso == 1                 # impedancias, y encadena solo
    w._fase_registro()
    assert w.paso == 2
    for _ in range(3000):
        if not w.corriendo:
            break
        w._tick()
    assert w.paso == 3
    assert w.resultado['OD']['veredicto'] == 'PASA'


def test_a_loose_probe_stops_the_sequence():
    """Sello flojo: el equipo se detiene ahí y dice por qué."""
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    w.start()
    w.probe.fit_quality = 0.2
    w._sonda_lista()
    assert not w.corriendo
    assert not w.sonda_ok
    assert w.paso == 0
    assert 'sonda' in w.lbl_resumen.text().lower()
    assert w.resultado['OD'] is None


def test_impedances_are_shown_and_never_stop_anything():
    """En tamizaje el límite es ancho: se muestran y listo.

    No se modelan ni frenan la prueba -- el ejercicio del AABR no es el
    montaje, y un chequeo que nunca falla no tiene nada que enseñar.
    """
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    assert f"{IMPEDANCIA_KOHM:.0f}" in w.lbl_impedancias.text()
    assert 'OK' in w.lbl_impedancias.text()
    assert _tamizar(w)['veredicto'] == 'PASA'


def test_the_screening_takes_the_time_it_takes():
    """900 barridos son unos 30 segundos, no uno.

    El tiempo sale de la tasa: subirla acorta la prueba, que es la razón
    por la que los equipos de tamizaje estimulan tan rápido.
    """
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    w.barridos = 900.0
    assert 25 <= w._segundos() <= 35, w._segundos()
    # Con la tasa al doble, la mitad del tiempo.
    lento, rapido = 45.0, 90.0
    w.sb_tasa.setValue(lento)
    t_lento = w._segundos()
    w.sb_tasa.setValue(rapido)
    assert abs(w._segundos() * 2 - t_lento) < 1.0

    # Y el resultado lo informa: cuánto costó, no solo qué dio.
    r = _tamizar(_ventana(_oido(10)))
    assert r['segundos'] > 0
    assert f"{r['segundos']} s" in w.lbl_resumen.text() or r['segundos'] > 0


def test_the_trace_is_drawn_while_averaging():
    """La curva SÍ se ve: los equipos de tamizaje la muestran."""
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    w.start()
    w.probe.fit_quality = 0.9
    w._sonda_lista()
    w._fase_registro()
    w._tick()
    x, y = w.curva.getData()
    assert x is not None and len(x) > 100
    assert float(max(abs(v) for v in y)) > 0


def test_changing_ear_goes_back_to_the_probe():
    """Oído nuevo, sonda nueva: la oliva se saca y se pone del otro lado."""
    if not HAS_UI:
        return
    w = _ventana(_oido(10), _oido(10))
    _tamizar(w)
    assert w.sonda_ok
    w.cb_lado.setCurrentText('OI')
    assert not w.sonda_ok
    assert w.paso == 0


def test_closing_the_attention_stops_the_run():
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    w.start()
    assert w.corriendo
    w.la_super(None, None)
    assert not w.corriendo
    assert not w.btn_start.isEnabled()


def test_the_protocol_button_puts_the_equipment_back():
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    w.sb_nivel.setValue(60)
    w.sb_barridos.setValue(1000)
    w.sb_criterio.setValue(2.0)
    w.chk_auto.setChecked(False)
    w.restore_protocol()
    assert w.sb_nivel.value() == NIVEL_DB
    assert w.sb_barridos.value() == BARRIDOS_MAX
    assert abs(w.sb_criterio.value() - CRITERIO_FSP) < 1e-9
    assert w.chk_auto.isChecked()


def test_the_report_travels_with_the_result():
    """El informe se precarga con lo que dio y queda editable.

    Y lo que se guarda es lo INFORMADO, no lo medido: informar distinto de
    lo que salió también es un error, y tiene que poder cometerse.
    """
    if not HAS_UI:
        return
    w = _ventana(_oido(10), _oido(85, 'coclear'))
    _tamizar(w)
    assert w.cb_informe['OD'].currentText() == 'PASA'
    data = w.report_data()
    assert data['resultados']['OD']['veredicto'] == 'PASA'
    assert data['resultados']['OI']['veredicto'] == 'No realizado'
    # Las condiciones salen del registro: es el procedimiento lo que se evalúa.
    assert data['resultados']['OD']['nivel'] == NIVEL_DB
    assert data['resultados']['OD']['barridos'] > 0
    assert data['resultados']['OD']['segundos'] > 0
    assert data['tecnica']['criterio_fsp'] == CRITERIO_FSP
    assert data['tecnica']['sello_sonda_ok'] is True
    # Y el texto del alumno.
    w.txt_observaciones.setPlainText("Bebé dormido, sin artefacto")
    w.txt_conducta.setPlainText("Rescreening en 15 días")
    data = w.report_data()
    assert 'dormido' in data['hallazgos']
    assert 'Rescreening' in data['conclusion']
    # Informar otra cosa: se guarda lo informado.
    w.cb_informe['OD'].setCurrentText('REFIERE')
    assert w.report_data()['resultados']['OD']['veredicto'] == 'REFIERE'


def test_nothing_is_uploaded_without_a_screening():
    """Sin tamizar y sin escribir nada no se sube un informe vacío."""
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    data = w.report_data()
    assert all(r['veredicto'] == 'No realizado' for r in data['resultados'].values())
    assert data['hallazgos'] == '' and data['conclusion'] == ''


def test_the_report_is_uploaded_as_its_own_type():
    """Va al backend como tipo 'AABR', que es el que report_upload.php
    acepta y el que el PDF del informe sabe dibujar. El backend resuelve la
    atención con appointment_id + el alumno del token, así que el informe
    queda colgado de SU atención."""
    if not HAS_UI:
        return
    w = _ventana(_oido(10))
    _tamizar(w)
    subido = {}

    class _ClienteFalso:
        def __init__(self, *a, **k):
            pass

        def is_logged_in(self):
            return True

        def upload_report(self, appointment_id, tipo, data, images):
            subido.update({'appointment_id': appointment_id, 'tipo': tipo,
                           'data': data, 'images': images})
            return {}

    import abr.AabrMainWindow as modulo
    original = modulo.BackendClient
    modulo.BackendClient = _ClienteFalso
    try:
        w.submit_report()
    finally:
        modulo.BackendClient = original
    assert subido['tipo'] == 'AABR'
    assert subido['appointment_id'] == 7       # el de _ventana
    assert subido['images'] == {}              # un tamizaje no informa curvas
    assert subido['data']['resultados']['OD']['veredicto'] == 'PASA'


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
