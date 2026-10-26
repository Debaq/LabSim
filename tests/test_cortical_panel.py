"""
Tests del panel de latencia media y tardía dentro de la ventana del ABR.

Como el ECochG, MLR, CAEP, P300 y MMN no son otro módulo sino otras
pruebas del mismo equipo. Lo que se cubre es la costura:

1. Elegir la prueba cambia la tabla, las marcas y la ventana; el docente
   encuentra el equipo en el estándar y el alumno no.
2. Cada captura deja una curva por canal ('R1.C3', 'R1.Cz', 'R1.C4'), y el
   oddball su trazo frecuente superpuesto.
3. Se marca como en el ABR (bandera A + botón) y la marca se pega al pico
   o al valle según el componente, con el mouse de verdad.
4. El efecto electrodo del caso 1 de la clase aparece en la tabla.
5. La sesión se guarda y vuelve con canales, superpuestos y marcas, con su
   propio tipo de informe.
6. Sin bloque `Central` no hay registro.
7. La tarea del paciente (P300 y MMN) se elige en el panel, viaja con la
   captura y la tabla muestra la respuesta del paciente.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('LABSIM_DATA_DIR', __import__('tempfile').mkdtemp(prefix='labsim_datos_'))

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

try:
    import numpy as np
    from core.base import context  # noqa: F401  (crea el QApplication)
    from abr import cortical
    from abr.AbrMainWindow import AbrMainWindow
    HAS_UI = True
except ImportError as exc:          # sin PySide6/pyqtgraph
    print(f"  (tests de panel salteados: {exc})")
    HAS_UI = False

DOCENTE = {'name': 'Docente', 'user': 'doc', 'permission': 777}
ALUMNO = {'name': 'Alumno', 'user': 'alu', 'permission': 1}


def _caso(central=None, edad=58):
    oido = {'umbral': 10, 'type': 'normal', 'repro': True,
            'desviaciones': {}, 'average_objetivo': 1500}
    caso = {'edad': edad, 'gender': 0,
            'ABR': {'OD': dict(oido), 'OI': dict(oido)}}
    if central is not False:
        caso['Central'] = central or {'estado': 'despierto'}
    return caso


def _ventana(test='MLR', caso=None, login=DOCENTE):
    w = AbrMainWindow(login)
    w.la_super(caso if caso is not None else _caso(), 42)
    w.control.cb_test.setCurrentText(test)
    return w


def _capturar(w, lado='OD'):
    w.control.cb_side.setCurrentText(lado)
    w.control.start_capture()
    for _ in range(600):
        w.capture()
        if w.state_capture != 'record':
            break
    else:
        w.control.stop_capture()
    return w.current_capture_curve


def _marcar(w, lado, canal, marca, lat):
    grafico = w.graph_r if lado == 0 else w.graph_l
    curva = [c for c in grafico.data if c.endswith('.' + canal)][-1]
    grafico.active_curve(curva)
    grafico.inf_a.setPos((lat, 0))
    w.mark_ecochg(lado, marca)
    return curva


def test_choosing_mlr_swaps_table_marks_and_window():
    if not HAS_UI:
        return
    w = _ventana('MLR')
    assert not w.table_cx_r.isHidden() and w.table_r.isHidden()
    assert w.table_ec_r.isHidden()
    assert w.graph_r.mark_labels == cortical.MARKS['MLR']
    assert w.graph_r.snap_sign['Pa'] == 1 and w.graph_r.snap_sign['Na'] == -1
    assert w.graph_r.window_ms == 100
    assert w.graph_r.x_tick() == 10.0
    w.control.cb_test.setCurrentText('P300')
    assert w.graph_r.window_ms == 800 and w.graph_r.x_tick() == 50.0
    assert w.table_cx_r.tabla.columnCount() == 3
    w.control.cb_test.setCurrentText('ABR')
    assert not w.table_r.isHidden() and w.table_cx_r.isHidden()


def test_the_teacher_gets_the_standard_and_the_student_does_not():
    if not HAS_UI:
        return
    w = _ventana('MLR')
    assert w.technical['montage'] == 'vertex_earlobe'
    assert w.control.cb_filter_up.currentText() == '10'
    assert w.control.cb_filter_down.currentText() == '300'
    assert abs(w.control.sb_rate.value() - 7.1) < 1e-6
    w = _ventana('P300')
    assert w.control.cb_filter_up.currentText() == '0.5'
    assert w.technical['oddball_rare'] == 'Burst 2 kHz'
    alumno = _ventana('MLR', login=ALUMNO)
    # El equipo llega del ABR: mastoides y la ganancia de siempre.
    assert alumno.technical['montage'] == 'vertex_mastoid'
    assert alumno.technical['gain'] == 100000.0


def test_each_capture_leaves_one_curve_per_channel():
    if not HAS_UI:
        return
    w = _ventana('MLR')
    grupo = _capturar(w)
    assert grupo == 'R1'
    assert sorted(w.graph_r.data) == ['R1.C3', 'R1.C4', 'R1.Cz']
    assert {w.memory[c]['canal'] for c in w.graph_r.data} == {'C3', 'Cz', 'C4'}
    assert 'Cz' in w.graph_r.label_html('R1.Cz', '#fff')
    w = _ventana('P300')
    _capturar(w)
    assert 'frecuente' in w.graph_r.data['R1.Pz']['overlays']
    assert 'ov_frecuente' in w.graph_r.traces['R1.Pz']


def test_marks_snap_to_peaks_and_troughs():
    if not HAS_UI:
        return
    w = _ventana('MLR')
    _capturar(w)
    curva = _marcar(w, 0, 'Cz', 'Pa', 27.0)
    x, y = w.graph_r.data[curva]['ipsi_xy']
    lat, amp = w.graph_r.marks[curva]['Pa']
    cerca = np.abs(x - 27.0) <= cortical.SNAP_MS['MLR']
    assert abs(amp - y[cerca].max()) < 1e-9
    _marcar(w, 0, 'Cz', 'Na', 18.0)
    _, amp_na = w.graph_r.marks[curva]['Na']
    cerca = np.abs(x - 18.0) <= cortical.SNAP_MS['MLR']
    assert abs(amp_na - y[cerca].min()) < 1e-9
    medidas = w.table_cx_r.medidas['Cz']
    assert abs(medidas['amp']['Na-Pa'] - (amp - amp_na)) < 1e-9


def test_marking_with_the_real_mouse():
    """Bandera arrastrada con el mouse + botón de la tabla, como en clase."""
    if not HAS_UI:
        return
    from PySide6.QtCore import QPointF
    from PySide6.QtWidgets import QApplication
    from test_ecochg_panel import _arrastre, _pixel
    w = _ventana('CAEP')
    w.resize(1400, 900)
    w.show()
    QApplication.processEvents()
    _capturar(w)
    g = w.graph_r
    curva = 'R1.Cz'
    g.active_curve(curva)
    QApplication.processEvents()
    g.inf_a.setPos((40.0, 0))
    _arrastre(g, _pixel(g, 40.0), _pixel(g, 95.0))
    assert abs(g.inf_a.getXPos() - 95.0) < 8.0, g.inf_a.getXPos()
    boton = [b for b in w.table_cx_r.botones if b.text() == 'N1'][0]
    boton.click()
    QApplication.processEvents()
    assert 'N1' in g.marks[curva]
    assert w.table_cx_r.medidas['Cz']['lat']['N1'] == g.marks[curva]['N1'][0]


def test_clicking_a_trace_selects_it_and_brings_flag_a():
    """Clic sobre el trazo de Cz: esa curva se marca, no la última creada
    (Pz). Y las banderas no quedan amontonadas al venir del ABR."""
    if not HAS_UI:
        return
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from test_ecochg_panel import _pixel
    w = _ventana('CAEP')
    w.resize(1400, 900)
    w.show()
    QApplication.processEvents()
    g = w.graph_r
    # A' venía de los 12 ms del ABR y quedaba pegada a A, contra el eje.
    assert g.inf_b.getXPos() > 0.9 * g.window_ms, g.inf_b.getXPos()
    _capturar(w)
    # La captura queda en el canal donde se lee el CAEP, no en el último.
    assert g.act_curve == 'R1.Cz', g.act_curve
    QApplication.processEvents()
    QTest.mouseClick(g.viewport(), Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, _pixel(g, 100.0, 'R1.Pz'))
    QApplication.processEvents()
    assert g.act_curve == 'R1.Pz', g.act_curve
    assert abs(g.inf_a.getXPos() - 100.0) < 8.0, g.inf_a.getXPos()
    boton = [b for b in w.table_cx_r.botones if b.text() == 'N1'][0]
    boton.click()
    QApplication.processEvents()
    assert 'N1' in g.marks['R1.Pz'] and 'N1' not in g.marks['R1.Cz']
    # El N1 busca cerca: la marca queda a menos de 10 ms del clic.
    assert abs(g.marks['R1.Pz']['N1'][0] - g.inf_a.getXPos()) <= 10.0 + 1e-9
    w.control.cb_test.setCurrentText('MMN')
    _capturar(w)
    assert g.act_curve == 'R1.Fz', g.act_curve


def test_normal_latency_guides_follow_the_selected_curve():
    """Cajas de latencia normal sobre la curva activa, solo en los
    corticales; el botón N las apaga y no van al informe."""
    if not HAS_UI:
        return
    w = _ventana('P300')
    _capturar(w)
    g = w.graph_r
    assert w.btn_norm_guides.isVisibleTo(w)
    assert sorted(g.norm_lat) == sorted(cortical.MARKS['P300'])
    lo, hi = g.norm_lat['P3']
    assert lo < 350 < hi
    assert len(g.norm_items) == 2 * len(g.norm_lat)
    # La caja sigue a la curva seleccionada.
    g.active_curve('R1.Fz')
    caja = g.norm_items[0]
    assert abs(caja.rect().top() - g.data['R1.Fz']['gap']) < g.scale_uv * 0.2
    w.btn_norm_guides.setChecked(False)
    assert not g.norm_items
    w.btn_norm_guides.setChecked(True)
    assert g.norm_items
    # La grilla no escribe 6.66667 a 40 uV.
    assert g.y_tick() == 5.0
    w.control.cb_test.setCurrentText('ABR')
    assert not g.norm_items and not w.btn_norm_guides.isVisibleTo(w)


def test_case_1_shows_an_electrode_effect_in_the_table():
    if not HAS_UI:
        return
    caso = _caso({'estado': 'despierto', 'mlr_hemisferio': 'derecho',
                  'mlr_reduccion': 0.6})
    w = _ventana('MLR', caso)
    for lado, nombre in ((0, 'OD'), (1, 'OI')):
        _capturar(w, nombre)
        for canal in ('C3', 'C4'):
            _marcar(w, lado, canal, 'Na', 18.0)
            _marcar(w, lado, canal, 'Pa', 30.0)
    # Declarado -60 %; medido pico a pico sobre un trazo con ruido sale
    # algo menos (el ruido infla más al electrodo chico), como en clínica.
    (dif, hemi), _ = w.cortical_effects()
    assert hemi == 'derecho' and dif > 0.3, (dif, hemi)
    assert 'Efecto electrodo' in w.table_cx_r.lbl_extra.text()
    assert w.session_payload()['efectos']['hemisferio'] == 'derecho'


def test_session_comes_back_with_channels_overlays_and_marks():
    if not HAS_UI:
        return
    w = _ventana('P300')
    _capturar(w)
    _marcar(w, 0, 'Pz', 'P3', 310.0)
    assert w.report_tipo() == 'P300'
    data = w.session_payload()
    assert data['curvas']['R1.Pz']['traza']['overlays']['frecuente']
    otra = _ventana('ABR')
    otra.draw_session(data)
    assert otra.test_actual == 'P300'
    assert sorted(otra.graph_r.data) == ['R1.Cz', 'R1.Fz', 'R1.Pz']
    assert 'P3' in otra.graph_r.marks['R1.Pz']
    assert 'frecuente' in otra.graph_r.data['R1.Pz']['overlays']
    assert otra.curves_R == ['R1']
    assert otra.table_cx_r.medidas['Pz']['lat']['P3'] == w.graph_r.marks['R1.Pz']['P3'][0]


def test_changing_test_keeps_each_session():
    if not HAS_UI:
        return
    w = _ventana('MLR')
    _capturar(w)
    w.control.cb_test.setCurrentText('CAEP')
    assert not w.graph_r.data
    _capturar(w)
    tipos = sorted(j['tipo'] for j in w.report_jobs())
    assert tipos == ['CAEP', 'PEALM'], tipos
    w.control.cb_test.setCurrentText('MLR')
    assert sorted(w.graph_r.data) == ['R1.C3', 'R1.C4', 'R1.Cz']


def test_the_task_selector_shows_only_in_the_oddball():
    if not HAS_UI:
        return
    w = _ventana('MLR')
    assert not w.control.cb_tarea.isVisibleTo(w)
    assert 'tarea' not in w.control.get_data()
    w.control.cb_test.setCurrentText('P300')
    assert w.control.cb_tarea.isVisibleTo(w)
    # El docente la recibe en el estándar; el alumno, sin instrucción.
    assert w.control.cb_tarea.currentData() == 'contar'
    w.control.cb_test.setCurrentText('MMN')
    assert w.control.cb_tarea.currentData() == 'pasiva'
    alumno = _ventana('P300', login=ALUMNO)
    assert alumno.control.cb_tarea.currentData() == 'ninguna'


def test_the_task_travels_with_the_capture_and_the_answer_is_shown():
    if not HAS_UI:
        return
    w = _ventana('P300', login=ALUMNO)
    _capturar(w)
    _marcar(w, 0, 'Pz', 'P3', 310.0)
    assert w.memory['R1.Pz']['tarea'] == 'ninguna'
    texto = w.table_cx_r.lbl_extra.text()
    assert 'Sin instrucción' in texto and 'no informó raros' in texto, texto
    w.control.cb_tarea.setCurrentIndex(w.control.cb_tarea.findData('boton'))
    _capturar(w)
    _marcar(w, 0, 'Pz', 'P3', 310.0)
    texto = w.table_cx_r.lbl_extra.text()
    assert 'Apretar botón' in texto and 'aciertos de' in texto, texto
    data = w.session_payload()
    assert data['curvas']['R2.Pz']['tarea'] == 'boton'
    assert data['conteo']['OD']['tarea'] == 'boton'


def test_without_central_block_there_is_no_recording():
    if not HAS_UI:
        return
    w = _ventana('CAEP', _caso(central=False))
    _capturar(w)
    assert 'vía central' in w.lbl_info.text()
    assert not w.last_metadata['waves_visible']


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for prueba in pruebas:
        prueba()
        print(f"  ok  {prueba.__name__}")
    print("TODOS LOS TESTS PASARON")
