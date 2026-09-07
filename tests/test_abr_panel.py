"""
Tests del panel de detalle y de los gráficos del módulo ABR.

Lo que se verifica acá es lo que antes no existía o no llegaba a pantalla:

1. Monitor de EEG crudo (src/abr/EEG.py): era un cascarón con ejes y las
   letras R/L, sin un solo método de update y sin nadie que le pasara
   datos. Ahora corre por timer y muestra impedancias, tierra y rechazo
   ANTES de promediar.
2. FSP (src/abr/FSP.py): dos viewboxes linkeados sin una sola curva. Ahora
   grafica FSP y ruido residual contra promediaciones, con la línea del
   criterio y la marca del cruce.
3. Rechazos y estado de captura: el generador los calculaba y ABR_Curve no
   los devolvía, así que lbl_info/lbl_time y todo el bloque lbl_info_* del
   .ui quedaban en blanco para siempre.
4. Gráfico principal: apilado de curvas siguiendo la escala (antes todas
   nacían en el mismo 1.8 µV fijo y se pisaban), canal contralateral
   dibujado y subpromedios A/B superpuestos.
5. Tabla con normativa: antes solo pintaba el fondo según el oído, sin
   marcar latencias, interpicos ni V/I fuera de rango.
6. Informe: las condiciones de registro suben junto con las curvas.

Necesita PySide6 + pyqtgraph + scipy. Sin entorno gráfico se corre igual
con QT_QPA_PLATFORM=offscreen, que se fija acá abajo.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    import numpy as np
    # core.base crea el QApplication al importarse: va antes de los widgets.
    from core.base import context  # noqa: F401
    from abr.ABR_generator import DISCONNECTED, normative_limits
    from abr.AbrMainWindow import AbrMainWindow
    HAS_UI = True
except ImportError as exc:          # sin PySide6/pyqtgraph/scipy
    print(f"  (tests de panel salteados: {exc})")
    HAS_UI = False


def _caso(edad=34, gender=1, umbral=20, tipo='normal', repro=True):
    oido = {'umbral': umbral, 'type': tipo, 'repro': repro, 'repro_var': 0.3,
            'desviaciones': {}, 'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'average_objetivo': 2000}
    return {'edad': edad, 'gender': gender,
            'ABR': {'OD': dict(oido), 'OI': dict(oido)}}


def _ventana(caso=None, average=2000):
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(caso if caso is not None else _caso(), 42)
    w.control.sb_prom.setValue(average)
    w.control.sb_rate.setValue(21.1)
    return w


def _capturar(w, intensidad=80, lado='OD'):
    """Una captura completa, tick a tick, sin depender del QTimer."""
    idx = w.control.cb_side.findText(lado)
    if idx >= 0:
        w.control.cb_side.setCurrentIndex(idx)
    w.control.sb_intencity.setValue(intensidad)
    w.control.start_capture()
    for _ in range(500):
        w.capture()
        if w.state_capture != 'record':
            return
    raise AssertionError('la captura no terminó nunca')


# ------------------------------------------------------- monitor de EEG

def test_eeg_monitor_draws_both_channels():
    """El EEG crudo llega a pantalla: antes el widget no tenía update."""
    if not HAS_UI:
        return
    w = _ventana()
    w.refresh_eeg()
    for canal in ('R', 'L'):
        x, y = w.eeg.curves[canal].getData()
        assert len(y) == w.eeg.n
        assert y.std() > 1.0, canal          # hay trazo, no una línea plana


def test_eeg_monitor_shows_a_disconnected_electrode():
    """Electrodo desconectado = canal plano y rotulado, no un EEG limpio."""
    if not HAS_UI:
        return
    w = _ventana()
    w.technical['electrodes'] = dict(w.technical['electrodes'],
                                     right=DISCONNECTED)
    w.refresh_eeg()
    _, y = w.eeg.curves['R'].getData()
    assert np.allclose(y, w.eeg.offsets['R'])
    assert 'sin electrodo' in w.eeg.state_text['R'].toPlainText()


def test_eeg_reject_bars_follow_the_equipment():
    """Las barras de rechazo son las del equipo, y se mueven con él."""
    if not HAS_UI:
        return
    w = _ventana()
    w.eeg.set_reject(25.0)
    arriba, abajo = w.eeg.reject_lines['R']
    assert arriba.isVisible()
    assert abs(arriba.value() - (w.eeg.offsets['R'] + 25.0)) < 1e-6
    assert abs(abajo.value() - (w.eeg.offsets['R'] - 25.0)) < 1e-6
    w.eeg.set_reject(0.0)                     # rechazo desactivado
    assert not arriba.isVisible()


# -------------------------------------------------------------- FSP

def test_fsp_graphs_the_capture():
    """Un punto de FSP y de ruido residual por tick de promediación."""
    if not HAS_UI:
        return
    w = _ventana()
    _capturar(w)
    x, y = w.fmp.curve_fsp.getData()
    assert len(y) > 5
    assert list(x) == sorted(x)               # contra promediaciones acumuladas
    assert y[-1] > y[0]                       # el FSP sube con los barridos
    _, ruido = w.fmp.curve_noise.getData()
    assert ruido[-1] < ruido[0]               # y el ruido residual baja


def test_fsp_marks_the_criterion_crossing():
    """El criterio de Parámetros Avanzados se dibuja y se marca el cruce."""
    if not HAS_UI:
        return
    w = _ventana()
    w.technical['fsp_criterion'] = 2.0
    _capturar(w)
    assert w.fmp.line_criterion.isVisible()
    assert abs(w.fmp.line_criterion.value() - 2.0) < 1e-6
    assert w.fmp.crossed_at is not None
    assert 'barridos' in w.fmp.lbl_cross.toPlainText()


def test_fsp_does_not_cross_an_unreachable_criterion():
    """Con un criterio que el caso no alcanza no hay marca de cruce."""
    if not HAS_UI:
        return
    w = _ventana()
    w.technical['fsp_criterion'] = 4.0        # el caso llega a 2.8
    _capturar(w)
    assert w.fmp.crossed_at is None


# ------------------------------------------------ rechazos y estado visible

def test_capture_state_reaches_the_labels():
    """lbl_info/lbl_time estaban en el .ui y nadie les escribía nunca."""
    if not HAS_UI:
        return
    w = _ventana()
    _capturar(w)
    info = w.lbl_info.text()
    for texto in ('barridos', 'aceptados', 'FSP', 'repro', 'nV'):
        assert texto in info, info
    assert w.lbl_time.text() == '01:34'       # 2000 barridos a 21.1/s


def test_artifact_rejection_is_visible():
    """El rechazo se ve: barridos aceptados < presentados, y el aviso."""
    if not HAS_UI:
        return
    w = _ventana()
    w.technical['artifact_reject_uv'] = 10.0
    _capturar(w)
    assert w.last_metadata['accepted_sweeps'] < w.last_metadata['current_avg']
    assert 'RECHAZO' in w.lbl_info.text(), w.lbl_info.text()


def test_detail_panel_describes_the_capture():
    """El bloque lbl_info_* del panel de detalle refleja la curva."""
    if not HAS_UI:
        return
    w = _ventana()
    _capturar(w, intensidad=70)
    assert w.detail.lbl_info_int.text() == '70 dBnHL'
    assert w.detail.lbl_info_side.text() == 'OD'
    assert w.detail.lbl_info_estim.text() == w.control.cb_stim.currentText()
    assert w.detail.lbl_info_aver.text() == '2000'
    # Y al seleccionar otra curva, muestra la de ESA curva.
    _capturar(w, intensidad=40)
    w.curve_selected('R1')
    assert w.detail.lbl_info_int.text() == '70 dBnHL'


# ----------------------------------------------------- gráfico principal

def test_curves_stack_instead_of_piling_up():
    """Cada curva nueva baja una ranura: antes todas nacían en 1.8 µV.

    Hacia abajo, que es como se lee un ABR: la intensidad más alta arriba y
    las siguientes descendiendo hacia el umbral.
    """
    if not HAS_UI:
        return
    w = _ventana()
    for db in (80, 60, 40):
        _capturar(w, intensidad=db)
    gaps = [w.graph_r.data[c]['gap'] for c in ('R1', 'R2', 'R3')]
    assert gaps == sorted(gaps, reverse=True) and len(set(gaps)) == 3, gaps
    # Y el rango visible alcanza para todas.
    lo, hi = w.graph_r.pw.viewRange()[1]
    assert lo < min(gaps)


def test_stacking_follows_the_scale():
    """Al cambiar la escala, el apilado la sigue en la misma proporción."""
    if not HAS_UI:
        return
    w = _ventana()
    for db in (80, 60):
        _capturar(w, intensidad=db)
    antes = w.graph_r.data['R2']['gap']
    escala_antes = w.graph_r.get_scale()
    w.btn_scale_plus.click()
    factor = w.graph_r.get_scale() / escala_antes
    assert abs(w.graph_r.data['R2']['gap'] - antes * factor) < 1e-9
    assert w.lbl_scale.text() == f"{int(round(w.graph_r.get_scale()))}µV"


def test_every_curve_draws_its_four_traces():
    """Promedio, contralateral y los dos subpromedios A/B."""
    if not HAS_UI:
        return
    w = _ventana()
    _capturar(w)
    trazos = w.graph_r.traces['R1']
    assert set(trazos) == {'main', 'contra', 'sub_a', 'sub_b'}
    for clave in ('main', 'contra', 'sub_a', 'sub_b'):
        _, y = trazos[clave].getData()
        assert y is not None and len(y) > 0, clave
    # El contra no es una copia del ipsi (antes dy = y.copy()).
    _, principal = trazos['main'].getData()
    _, contra = trazos['contra'].getData()
    assert not np.array_equal(principal, contra)


def test_no_contra_trace_without_the_electrode():
    """Sin el electrodo del otro mastoides, ese trazo queda vacío."""
    if not HAS_UI:
        return
    w = _ventana()
    w.technical['electrodes'] = dict(w.technical['electrodes'],
                                     left=DISCONNECTED)
    _capturar(w, lado='OD')
    _, contra = w.graph_r.traces['R1']['contra'].getData()
    assert contra is None or len(contra) == 0


# ------------------------------------------------------- tabla con normativa

def test_table_flags_a_late_wave_v():
    """Una onda V tardía se marca; una normal no."""
    if not HAS_UI:
        return
    w = _ventana()
    w.table_r.set_norms(normative_limits(_caso(), 80))
    normal = {'LatAmp': {'I': [1.6, 0.2], 'II': [None, None],
                         'III': [3.7, 0.3], 'IV': [None, None],
                         'V': [5.5, 0.5]}}
    w.table_r.update_latamp_table(normal)
    assert w.table_r.tw_latamp.item(4, 0).toolTip() == ''
    tardia = {'LatAmp': dict(normal['LatAmp'], V=[7.2, 0.5])}
    w.table_r.update_latamp_table(tardia)
    assert 'Fuera de rango' in w.table_r.tw_latamp.item(4, 0).toolTip()


def test_table_flags_a_prolonged_interpeak():
    """El interpico I-V prolongado es el hallazgo retrococlear clásico."""
    if not HAS_UI:
        return
    w = _ventana()
    w.table_r.set_norms(normative_limits(_caso(), 80))
    w.table_r.update_latamp_table({'LatAmp': {
        'I': [1.6, 0.2], 'II': [None, None], 'III': [4.2, 0.2],
        'IV': [None, None], 'V': [6.4, 0.2]}})
    assert 'Fuera de rango' in w.table_r.tw_inter.item(0, 0).toolTip()   # I-V


def test_table_flags_a_low_v_over_i_ratio():
    """Razón V/I caída: la onda V no crece respecto de la I."""
    if not HAS_UI:
        return
    w = _ventana()
    w.table_r.set_norms(normative_limits(_caso(), 80))
    w.table_r.update_latamp_table({'LatAmp': {
        'I': [1.6, 0.6], 'II': [None, None], 'III': [3.7, 0.3],
        'IV': [None, None], 'V': [5.5, 0.2]}})
    assert 'Fuera de rango' in w.table_r.tw_inter.item(3, 0).toolTip()


def test_table_norms_follow_the_curve_intensity():
    """Los rangos se recalculan para la intensidad de la curva elegida."""
    if not HAS_UI:
        return
    w = _ventana()
    _capturar(w, intensidad=80)
    _capturar(w, intensidad=40)
    w.curve_selected('R2')
    limite_40 = w.table_r.norms['lat']['V'][1]
    w.curve_selected('R1')
    limite_80 = w.table_r.norms['lat']['V'][1]
    assert limite_40 > limite_80


# ------------------------------------------------- banda latencia-intensidad

def test_lat_int_band_follows_the_patient():
    """La banda normativa sigue a la edad: un neonato no está fuera de norma."""
    if not HAS_UI:
        return
    w = _ventana()
    _, adulto = w.graph_lat_int.curve_top.getData()
    w.la_super(_caso(edad=0.1), 43)
    _, neonato = w.graph_lat_int.curve_top.getData()
    assert all(n > a for n, a in zip(neonato, adulto))
    assert 'años' in w.graph_lat_int.lbl_band.toPlainText()


# ------------------------------------------------------------------ informe

def test_report_carries_the_recording_conditions():
    """El informe sube CÓMO se registró, no solo qué dio.

    Sin esto el docente evalúa el resultado pero no el procedimiento: no
    puede distinguir un registro bien hecho de uno con los electrodos a
    8 kOhm o sin tierra.
    """
    if not HAS_UI:
        return
    w = _ventana()
    w.technical['impedance'] = dict(w.technical['impedance'], vertex=8.0)
    _capturar(w)
    tec = w.recording_conditions()
    for clave in ('transductor', 'montaje', 'ventana_ms', 'electrodos',
                  'impedancias_kohm', 'rechazo_artefacto_uv', 'criterio_fsp',
                  'barridos_presentados', 'barridos_aceptados', 'fsp',
                  'ruido_residual_nv', 'replicabilidad'):
        assert clave in tec, clave
    assert tec['impedancia_max_kohm'] == 8.0
    assert tec['impedancia_en_norma'] is False
    # Y cada curva se lleva las suyas: el equipo se puede cambiar a mitad
    # del examen.
    assert w.memory['R1']['tecnica']['impedancia_max_kohm'] == 8.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
