"""
Tests del panel del ECochG dentro de la ventana del ABR.

El ECochG no es otro módulo: es otra prueba del mismo equipo. Lo que estos
tests cubren es la costura, que es donde se rompe:

1. Elegir ECochG en el combo cambia el equipo (ventana, montaje) Y la
   tabla: la de ondas I-V se va, aparece la de razones.
2. Las marcas se ponen haciendo clic sobre la curva, no con los cursores.
   El PA se pega al pico; la base y el hombro del PS caen donde el alumno
   diga, que es la parte que se evalúa.
3. Con BL, PS y PA hay razón de amplitudes; el área y la duración del
   complejo esperan el retorno a la base.
4. El corrimiento por tasa aparece recién con dos curvas del mismo oído a
   distinta tasa.
5. Un caso sin bloque de ECochG no produce registro.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    import numpy as np
    from core.base import context  # noqa: F401  (crea el QApplication)
    from abr import ecochg
    from abr.AbrMainWindow import AbrMainWindow
    HAS_UI = True
except ImportError as exc:          # sin PySide6/pyqtgraph/scipy
    print(f"  (tests de panel salteados: {exc})")
    HAS_UI = False


def _caso(sp_ap=0.25, con_ecochg=True, umbral=20):
    oido = {'umbral': umbral, 'type': 'normal', 'repro': True,
            'repro_var': 0.3, 'desviaciones': {},
            'fsp_puntos': {'800': 2.3, '2000': 2.8},
            'average_objetivo': 1500}
    if con_ecochg:
        oido['ecochg'] = {'sp_ap': sp_ap}
    return {'edad': 34, 'gender': 1,
            'ABR': {'OD': dict(oido), 'OI': dict(oido)}}


def _ventana(caso=None, rate=11.1):
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(caso if caso is not None else _caso(), 42)
    w.control.cb_test.setCurrentText('ECochG')
    w.control.sb_prom.setValue(1500)
    w.control.sb_rate.setValue(rate)
    for combo, texto in ((w.control.cb_filter_up, '10'),
                         (w.control.cb_filter_down, '3000')):
        idx = combo.findText(texto)
        if idx >= 0:
            combo.setCurrentIndex(idx)
    idx = w.control.cb_pol.findText('Alternada')
    if idx >= 0:
        w.control.cb_pol.setCurrentIndex(idx)
    return w


def _capturar(w, intensidad=90, lado='OD'):
    idx = w.control.cb_side.findText(lado)
    if idx >= 0:
        w.control.cb_side.setCurrentIndex(idx)
    w.control.sb_intencity.setValue(intensidad)
    w.control.start_capture()
    for _ in range(500):
        w.capture()
        if w.state_capture != 'record':
            return w.current_capture_curve
    w.control.stop_capture()
    return w.current_capture_curve


def _marcar(w, curva, lado=0):
    """Pone las cuatro marcas bien puestas, como las pondría un alumno.

    Se hace por el mismo camino que el clic (graph.current_lat +
    create_marks), no escribiendo en memory: lo que se quiere probar es la
    costura entre el gráfico y la tabla.
    """
    grafico = w.graph_r if lado == 0 else w.graph_l
    x, y = grafico.data[curva]['ipsi_xy']
    ap_lat = w.last_metadata.get('ecochg_ap_lat')
    base = float(np.mean(y[x < 0.25]))
    i_pa = int(np.argmin(np.abs(x - ap_lat)))
    cruces = np.where(y[i_pa:] >= base)[0]
    puestas = [('BL', 0.15), ('PS', ap_lat - ecochg.SP_SHOULDER_MS),
               ('PA', ap_lat)]
    if len(cruces):
        puestas.append(('FIN', float(x[i_pa + cruces[0]])))
    for marca, lat in puestas:
        grafico.current_lat = lat
        grafico.create_marks(marca)
    return dict(puestas)


def _valor(tabla, clave):
    return (tabla.medidas or {}).get(clave)


# ----------------------------------------------------------------- tests

def test_choosing_ecochg_swaps_the_equipment_and_the_table():
    """El combo cambia la prueba entera, no solo un rótulo."""
    if not HAS_UI:
        return
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    assert w.table_r.isVisibleTo(w) and not w.table_ec_r.isVisibleTo(w)
    w.control.cb_test.setCurrentText('ECochG')
    assert w.technical['montage'] == 'tympanic'
    assert w.technical['window_ms'] == 10
    assert not w.table_r.isVisibleTo(w) and w.table_ec_r.isVisibleTo(w)
    # Y el gráfico pasa a marcar los cuatro puntos del ECochG.
    assert w.graph_r.mark_labels == ecochg.MARKS
    assert w.graph_r.snap_marks == ('PA',)
    w.control.cb_test.setCurrentText('ABR')
    assert w.table_r.isVisibleTo(w) and not w.table_ec_r.isVisibleTo(w)
    assert w.graph_r.mark_labels == ('I', 'II', 'III', 'IV', 'V')


def test_only_one_mark_is_armed_in_the_whole_window():
    """Con dos armadas, un clic en el otro oído pondría la que no se mira."""
    if not HAS_UI:
        return
    w = _ventana()
    w.arm_ecochg_mark(0, 'PA')
    assert w.graph_r.mark_mode == 'PA'
    w.arm_ecochg_mark(1, 'PS')
    assert w.graph_l.mark_mode == 'PS'
    assert w.graph_r.mark_mode is None


def test_the_action_potential_mark_snaps_to_the_peak():
    """Marcar el PA es decir dónde está, no acertarle al punto.

    La base y el hombro del PS NO se pegan a nada: ahí el alumno decide, y
    de esa decisión sale la razón que informa.
    """
    if not HAS_UI:
        return
    w = _ventana()
    curva = _capturar(w)
    ap_lat = w.last_metadata['ecochg_ap_lat']
    pegado = w.graph_r.snap_to_peak(ap_lat + 0.2)
    assert abs(pegado - ap_lat) < abs(ap_lat + 0.2 - ap_lat)
    x, y = w.graph_r.data[curva]['ipsi_xy']
    cerca = np.where(np.abs(x - ap_lat) <= w.graph_r.SNAP_MS)[0]
    assert abs(pegado - float(x[cerca[int(np.argmin(y[cerca]))]])) < 1e-9


def test_the_marks_fill_the_ecochg_table():
    """Las cuatro marcas y la tabla queda completa."""
    if not HAS_UI:
        return
    w = _ventana(_caso(sp_ap=0.25))
    curva = _capturar(w)
    _marcar(w, curva)
    tabla = w.table_ec_r
    assert abs(_valor(tabla, 'sp_ap') - 0.25) < 0.06
    assert _valor(tabla, 'ap_amp') > 1.0          # electrodo timpánico: µV
    assert _valor(tabla, 'area_ratio') is not None
    assert _valor(tabla, 'ancho_pa') is not None
    # Y la medida queda guardada en la curva, para el informe.
    assert w.memory[curva]['ECochG']['sp_ap'] == _valor(tabla, 'sp_ap')


def test_without_the_return_mark_there_is_no_area():
    """El área se integra hasta el retorno a la base: sin esa marca no hay."""
    if not HAS_UI:
        return
    w = _ventana()
    curva = _capturar(w)
    grafico = w.graph_r
    ap_lat = w.last_metadata['ecochg_ap_lat']
    x, y = grafico.data[curva]['ipsi_xy']
    for marca, lat in (('BL', 0.15), ('PS', ap_lat - ecochg.SP_SHOULDER_MS),
                       ('PA', ap_lat)):
        grafico.current_lat = lat
        grafico.create_marks(marca)
    tabla = w.table_ec_r
    assert _valor(tabla, 'sp_ap') is not None
    assert _valor(tabla, 'area_ratio') is None
    assert tabla.medidas['faltan'] == ['FIN']


def test_a_hydrops_ear_crosses_its_limit_and_the_table_says_so():
    """El fondo rojo sale del límite del electrodo que se está usando."""
    if not HAS_UI:
        return
    for sp_ap, fuera in ((0.20, False), (0.60, True)):
        w = _ventana(_caso(sp_ap=sp_ap))
        curva = _capturar(w)
        _marcar(w, curva)
        tabla = w.table_ec_r
        fila = [f[1] for f in __import__('abr.EcochgTable', fromlist=['FILAS']).FILAS].index('sp_ap')
        item = tabla.tabla.item(fila, 0)
        assert item.toolTip().startswith('Fuera') is fuera, (sp_ap, item.text())


def test_the_rate_shift_needs_two_curves_of_the_same_ear():
    """Es una comparación entre registros, no una medida de una curva."""
    if not HAS_UI:
        return
    w = _ventana(rate=11.1)
    curva = _capturar(w, 90)
    _marcar(w, curva)
    assert _valor(w.table_ec_r, 'd_lat') is None
    w.control.sb_rate.setValue(91.0)
    otra = _capturar(w, 90)
    _marcar(w, otra)
    assert _valor(w.table_ec_r, 'd_lat') is not None
    # El PA se adapta: llega más tarde y más chico.
    assert _valor(w.table_ec_r, 'd_lat') > 0
    assert _valor(w.table_ec_r, 'd_amp_pct') < 0


def test_a_case_without_ecochg_records_nothing():
    """Sin dato del backend no se inventa un oído normal."""
    if not HAS_UI:
        return
    w = _ventana(_caso(con_ecochg=False))
    _capturar(w)
    assert w.last_metadata['ecochg_sin_datos'] is True
    assert w.last_metadata['recording'] is False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
