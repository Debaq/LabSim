"""
Tests del ASSR (potenciales de estado estable) dentro de la ventana del ABR.

Modelo (abr/assr.py):
1. Una línea con respuesta se detecta y fuera del umbral no; el ruido baja
   como 1/raíz(N).
2. Las líneas caen en bins distintos y el cambio de nivel reinicia SOLO esa
   portadora.
3. Un oído sordo no responde, pero el cruce de sonido a 65 dB de
   atenuación hace aparecer la línea del oído estimulado.
4. Sin datos del oído no se registra ese oído.
5. El umbral y su corrección a eHL; la estrategia automática termina.

Panel:
6. Elegir ASSR cambia los gráficos por el panel y el registro corre con el
   tick de captura; el alumno no ve el audiograma real, el docente sí.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('LABSIM_DATA_DIR', __import__('tempfile').mkdtemp(prefix='labsim_datos_'))

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np

from abr import assr

try:
    from core.base import context  # noqa: F401  (crea el QApplication)
    from abr.AbrMainWindow import AbrMainWindow
    HAS_UI = True
except ImportError as exc:          # sin PySide6/pyqtgraph
    print(f"  (tests de panel salteados: {exc})")
    HAS_UI = False

DOCENTE = {'name': 'Docente', 'user': 'doc', 'permission': 777}
ALUMNO = {'name': 'Alumno', 'user': 'alu', 'permission': 1}


def _oido(umbrales):
    return {'umbral_por_estimulo': {
        f'tone_burst_{f}Hz': umbrales[i]
        for i, f in enumerate(assr.CARRIERS)}}


NORMAL = _oido([25, 25, 20, 20])
SORDO = _oido([None] * 4)


def _registro(od=NORMAL, oi=NORMAL, nivel=60, n=300, **kw):
    rec = assr.Recording({'OD': od, 'OI': oi}, **kw)
    for c in assr.channels():
        rec.set_level(c, nivel)
    rec.step(n)
    return rec


def test_response_is_detected_above_threshold_and_not_below():
    rec = _registro(nivel=70)
    for c in assr.channels():
        assert rec.stats(c)['detected'], c
    rec = _registro(nivel=0)
    assert not any(rec.stats(c)['detected'] for c in assr.channels())


def test_noise_drops_as_one_over_root_n():
    rec = _registro(od=SORDO, oi=SORDO, nivel=40, n=1000)
    c = ('OD', 1000)
    ruido = []
    for n in (60, 240, 960):
        rec.start[c] = 0
        rec.n = n
        ruido.append(rec.stats(c)['noise_nv'])
    # 4x las épocas = la mitad del ruido (con holgura estadística).
    assert 1.4 < ruido[0] / ruido[1] < 2.9, ruido
    assert 1.4 < ruido[1] / ruido[2] < 2.9, ruido


def test_lines_fall_on_different_bins_and_level_change_resets_only_one():
    bins = [b for s in assr.SIDES for b in assr.FM_BIN[s]]
    assert len(set(bins)) == 8
    assert all(abs(a - b) >= 2 for a in bins for b in bins if a != b)
    rec = _registro(n=60)
    antes = rec.stats(('OI', 500))['n']
    rec.set_level(('OD', 500), 40)
    assert rec.stats(('OD', 500))['n'] == 0
    assert rec.stats(('OI', 500))['n'] == antes
    assert rec.history[('OD', 500)][0]['level'] == 60


def test_dead_ear_does_not_respond_but_crossover_shows_at_high_level():
    rec = _registro(od=SORDO, oi=NORMAL, nivel=50, n=300)
    assert not rec.stats(('OD', 1000))['detected']
    rec = _registro(od=SORDO, oi=NORMAL, nivel=105, n=300)
    # 105 - 65 de atenuación = 40 dB en el oído sano: responde a la
    # modulación del oído sordo.
    assert rec.stats(('OD', 1000))['detected']


def test_ear_without_data_is_not_recorded():
    rec = assr.Recording({'OD': NORMAL, 'OI': None})
    assert rec.has_ear('OD') and not rec.has_ear('OI')
    rec.step(50)
    assert rec.stats(('OI', 1000))['estado'] == 'sin datos'
    assert not rec.active(('OI', 1000))


def test_threshold_and_ehl_correction():
    rec = assr.Recording({'OD': NORMAL, 'OI': NORMAL})
    for nivel in (60, 50, 40, 30, 20, 10):
        for c in assr.channels():
            rec.set_level(c, nivel)
        rec.step(500)
    c = ('OD', 1000)
    thr = rec.threshold_hl(c)
    assert thr is not None and 10 <= thr <= 50, thr
    ehl = rec.threshold_ehl(c)
    assert ehl == thr - assr.DEFAULT_EHL_CORRECTION[1000]
    assert rec.threshold_ehl(c, {1000: 0.0, 500: 0, 2000: 0, 4000: 0}) == thr


def test_auto_strategy_finishes_with_threshold_and_no_response():
    rec = assr.Recording({'OD': NORMAL, 'OI': SORDO})
    for _ in range(400):
        rec.step(15)
        rec.auto_step()
        if rec.all_done():
            break
    od = [rec.threshold_hl(('OD', f)) for f in assr.CARRIERS]
    assert all(t is not None for t in od), od
    assert rec.threshold_hl(('OI', 1000)) is None


def test_same_patient_same_recording():
    a = _registro(n=40, patient={'edad': 30})
    b = _registro(n=40, patient={'edad': 30})
    assert np.allclose(a.rows[:40], b.rows[:40])


def test_artifact_epochs_are_rejected_with_a_tight_window():
    rec = assr.Recording({'OD': NORMAL, 'OI': NORMAL}, inquietud=1.0,
                         reject_uv=25.0)
    rec.step(400)
    assert rec.rejected > 40
    flojo = assr.Recording({'OD': NORMAL, 'OI': NORMAL}, inquietud=1.0,
                           reject_uv=500.0)
    flojo.step(400)
    assert flojo.rejected == 0


def _caso():
    return {'edad': 30, 'gender': 0,
            'ABR': {'OD': dict(NORMAL), 'OI': dict(NORMAL)}}


def _ventana(login=DOCENTE):
    w = AbrMainWindow(login)
    w.la_super(_caso(), 7)
    w.control.cb_test.setCurrentText('ASSR')
    return w


def test_panel_replaces_the_graphs_and_runs_with_the_capture_tick():
    if not HAS_UI:
        return
    w = _ventana()
    assert w.assr_panel.isVisibleTo(w)
    assert not w.graph_r.isVisibleTo(w) and w.table_r.isHidden()
    w.control.start_capture()
    for _ in range(40):
        w.capture()
    assert w.assr_panel.rec.n > 60
    assert 'épocas' in w.lbl_info.text()
    w.control.stop_capture()
    w.control.cb_test.setCurrentText('ABR')
    assert w.graph_r.isVisibleTo(w) and not w.assr_panel.isVisibleTo(w)


def test_panel_students_do_not_see_the_real_audiogram():
    if not HAS_UI:
        return
    for login, espera in ((DOCENTE, True), (ALUMNO, False)):
        w = _ventana(login)
        w.assr_panel.rec.set_level(('OD', 1000), 70)
        w.assr_panel.tick(60)
        assert w.assr_panel.docente is espera
        w.assr_panel.dibujar_audiograma()


def test_panel_without_abr_in_the_case_says_no_recording():
    if not HAS_UI:
        return
    w = AbrMainWindow(DOCENTE)
    w.la_super({'edad': 30, 'gender': 0}, 7)
    w.control.cb_test.setCurrentText('ASSR')
    assert w.assr_panel.rec is None
    assert 'SIN REGISTRO' in w.assr_panel.lbl_estado.text()


def _registrar(w, ticks=40):
    w.control.start_capture()
    for _ in range(ticks):
        w.capture()
    w.control.stop_capture()


def test_the_assr_is_saved_as_its_own_report_with_images():
    if not HAS_UI:
        return
    w = _ventana()
    assert w.report_job() is None, 'sin registrar no hay nada que subir'
    w.appointment_id = 7
    _registrar(w)
    job = w.report_job()
    assert job is not None and job['tipo'] == 'ASSR'
    assert job['data']['prueba'] == 'ASSR'
    snap = job['data']['assr']
    assert snap['n'] > 60 and len(snap['canales']) == 8
    c = snap['canales']['OD:1000']
    assert len(c['espectro']) == assr.N_BINS and c['stats']['n'] > 0
    import json
    json.dumps(job['data'])            # viaja como JSON al backend
    imagenes = job['images']()
    assert set(imagenes) == {'assr_rastro', 'assr_fft', 'assr_polar', 'assr_audio'}
    assert all(os.path.getsize(r) > 1000 for r in imagenes.values())
    assert 'barridos_presentados' not in job['data']['tecnica']


def test_the_saved_assr_comes_back_as_it_was():
    if not HAS_UI:
        return
    w = _ventana()
    w.appointment_id = 7
    _registrar(w)
    antes = w.assr_panel.snapshot()
    data = w.session_payload()
    w2 = AbrMainWindow(DOCENTE)
    w2.la_super(_caso(), 7)
    w2.apply_restored([{'tipo': 'ASSR', 'data': data}], 'u', 7)
    assert w2.test_actual == 'ASSR' and w2.assr_panel.isVisibleTo(w2)
    rec = w2.assr_panel.rec
    assert getattr(rec, 'guardado', False) and rec.n == antes['n']
    c = ('OD', 1000)
    assert abs(rec.stats(c)['amp_nv'] - w.assr_panel.rec.stats(c)['amp_nv']) < 1e-6
    assert rec.threshold_hl(c) == w.assr_panel.rec.threshold_hl(c)
    esp, n = rec.mean_spectrum(c)
    assert n == w.assr_panel.rec.stats(c)['n'] and np.abs(esp).max() > 0
    w2.assr_panel.refrescar()
    assert 'solo lectura' in w2.assr_panel.lbl_estado.text()
    # El informe del registro vuelto a abrir no cambia al guardarlo otra vez.
    assert w2.assr_panel.snapshot()['n'] == antes['n']


def test_leaving_and_returning_keeps_the_live_assr():
    if not HAS_UI:
        return
    w = _ventana()
    w.appointment_id = 7
    _registrar(w)
    n = w.assr_panel.rec.n
    w.control.cb_test.setCurrentText('ABR')
    assert 'ASSR' in w.otras_pruebas
    w.control.cb_test.setCurrentText('ASSR')
    assert w.assr_panel.en_vivo() and w.assr_panel.rec.n == n
    assert w.assr_panel.isVisibleTo(w)


def test_looking_at_a_past_session_does_not_lose_the_live_recording():
    if not HAS_UI:
        return
    w = _ventana()
    w.appointment_id = 7
    _registrar(w)
    n = w.assr_panel.rec.n
    pasada = w.session_payload()
    w.sessions = [{'data': pasada}]
    w.select_session(0)
    assert getattr(w.assr_panel.rec, 'guardado', False)
    assert not w.assr_panel.btn_reiniciar.isEnabled()
    w.select_session(None)
    assert w.assr_panel.en_vivo() and w.assr_panel.rec.n == n


def test_report_type_maps_to_assr_and_back():
    from abr.AbrSessions import report_tipo, test_of_report
    assert report_tipo('ASSR') == 'ASSR' and test_of_report('ASSR') == 'ASSR'

if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for prueba in pruebas:
        prueba()
        print(f"  ok  {prueba.__name__}")
    print("TODOS LOS TESTS PASARON")
