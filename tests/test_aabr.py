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
    from abr.AabrMainWindow import (BARRIDOS_MAX, CRITERIO_FSP, NIVEL_DB,
                                    AabrMainWindow)
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


def _tamizar(w, tope=400):
    """Corre la prueba entera sin QTimer, tick a tick."""
    w.start()
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


def test_screening_does_not_upload_a_report():
    """El tamizaje no produce informe: produce PASA o REFIERE."""
    if not HAS_UI:
        return
    assert _ventana(_oido(10)).submit_report() is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
