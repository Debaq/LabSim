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
except ImportError as exc:          # sin PySide6/pyqtgraph
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


def test_the_three_ecochg_electrodes_are_selectable():
    """El modelo distingue tres posiciones: el diálogo tiene que ofrecerlas.

    Cada una tiene su propio límite de razón PS/PA, y comparar el mismo oído
    medido desde el conducto y desde la membrana es medio ejercicio. Con una
    sola posición en el combo eso no se podía hacer.
    """
    if not HAS_UI:
        return
    from abr.AbrAdvanceSettings import MONTAGES
    for clave in ecochg.ELECTRODE_GAIN:
        assert clave in MONTAGES.values(), clave


def _boton(w, side, marca):
    tabla = w.table_ec_r if side == 0 else w.table_ec_l
    from abr import ecochg as _e
    for btn in tabla.botones:
        if btn.text() == _e.MARK_BUTTONS[marca]:
            return btn
    raise AssertionError(marca)


def test_the_buttons_mark_where_the_flag_is():
    """Como en el ABR: la bandera A en el punto y el botón. En clase se
    movía la bandera, se apretaba PA y no pasaba nada (el botón solo
    "armaba" la marca y había que hacer además un clic en la curva)."""
    if not HAS_UI:
        return
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    w = _ventana_visible()
    curva = _capturar(w)
    g = w.graph_r
    ap_lat = w.last_metadata['ecochg_ap_lat']
    for marca, lat in (('BL', 0.2), ('PS', ap_lat - 0.55),
                       ('PA', ap_lat + 0.15)):
        _arrastre(g, _pixel(g, g.inf_a.getXPos()), _pixel(g, lat))
        QTest.mouseClick(_boton(w, 0, marca), Qt.MouseButton.LeftButton)
        assert marca in g.marks.get(curva, {}), (marca, g.marks.get(curva))
        if marca != 'PA':
            assert abs(g.marks[curva][marca][0] - g.inf_a.getXPos()) < 0.05
    # El PA se pega al pico aunque la bandera haya quedado corrida.
    assert abs(g.marks[curva]['PA'][0] - ap_lat) < 0.1
    assert w.memory[curva]['ECochG'].get('sp_ap') is not None


def test_bl_ini_and_fin_are_colored_dots_not_arrows():
    """BL, Ini y Fin marcan un nivel o un límite, no un pico: van como
    punto de color (el del botón) y no tapan el trazo con una flecha."""
    if not HAS_UI:
        return
    w = _ventana()
    curva = _capturar(w)
    g = w.graph_r
    w.auto_ecochg_mark(0)
    for marca in ('BL', 'INI', 'FIN'):
        assert (curva, marca) in g.dot_items, marca
        assert g.mark_item(curva, marca) is None, marca
    for marca in ('PS', 'PA'):
        assert g.mark_item(curva, marca) is not None, marca
    g.active_curve(curva)
    g.delete_mark('FIN')
    assert (curva, 'FIN') not in g.dot_items
    w.reset()
    assert not g.dot_items


def test_the_flags_show_their_latency():
    """En ninguna parte de la pantalla se veía en qué latencia estaban las
    banderas (ABR y ECochG)."""
    if not HAS_UI:
        return
    w = _ventana()
    g = w.graph_r
    g.inf_a.setPos((1.35, 0))
    g.inf_b.setPos((5.5, 0))
    assert '1.35 ms' in g.inf_a.label.textItem.toPlainText()
    assert '5.50 ms' in g.inf_b.label.textItem.toPlainText()


def test_a_mark_that_cannot_be_placed_says_why():
    """Sin curva en ese oído, el botón avisa en la barra en vez de callar."""
    if not HAS_UI:
        return
    w = _ventana()
    _capturar(w)                         # solo OD
    w.mark_ecochg(1, 'BL')
    assert 'curva seleccionada' in w.lbl_info.text(), w.lbl_info.text()
    w.set_view_mode(True)
    w.mark_ecochg(0, 'BL')
    assert 'solo lectura' in w.lbl_info.text(), w.lbl_info.text()


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


def test_the_polarity_shift_needs_a_rarefaction_and_a_condensation():
    """Una curva de cada polaridad al mismo nivel, y la fila se llena; el
    informe la lleva aparte, por oído."""
    if not HAS_UI:
        return
    caso = _caso()
    for oido in caso['ABR'].values():
        oido['ecochg']['rar_cond_ms'] = 0.5
    w = _ventana(caso)
    for pol in ('Rarefacción', 'Condensación'):
        w.control.cb_pol.setCurrentIndex(w.control.cb_pol.findText(pol))
        curva = _capturar(w, 90)
        _marcar(w, curva)
        if pol == 'Rarefacción':
            assert _valor(w.table_ec_r, 'd_rc') is None
    d_rc = _valor(w.table_ec_r, 'd_rc')
    assert d_rc is not None and abs(d_rc - 0.5) < 0.12, d_rc
    fila = [f[1] for f in __import__('abr.EcochgTable', fromlist=['FILAS']).FILAS].index('d_rc')
    assert w.table_ec_r.tabla.item(fila, 0).toolTip().startswith('Fuera')
    polaridad = w.session_payload().get('polaridad')
    assert polaridad and polaridad[0]['oido'] == 'OD', polaridad


def _ventana_con_permiso(permiso):
    w = AbrMainWindow({'name': 'X', 'user': 'x', 'permission': permiso})
    w.la_super(_caso(), 42)
    w.control.cb_test.setCurrentText('ECochG')
    return w


def test_the_teacher_gets_the_standard_ecochg_setup():
    """El docente encuentra el ECochG listo para tomar."""
    if not HAS_UI:
        return
    w = _ventana_con_permiso(777)
    c = w.control.get_data()
    assert c['stim'] == 'Click' and c['pol'] == 'Alternada', c
    assert c['int'] == 90 and c['average'] == 1500, c
    assert abs(c['rate'] - 11.1) < 1e-6, c
    assert (c['filter_passhigh'], c['filter_down']) == ('5', '3000'), c
    assert w.technical['window_ms'] == 10.0
    assert w.technical['montage'] == 'tympanic'
    assert w.technical['gain'] == 100000.0
    # Con burst: envolvente 1-10-1 ms y una ventana que contenga la meseta.
    w.control.cb_stim.setCurrentText('Burst 1 kHz')
    assert w.technical['burst_envelope'] == 'ms-1-10-1'
    assert w.technical['window_ms'] == 20.0
    # Y de vuelta al click, la ventana del click.
    w.control.cb_stim.setCurrentText('Click')
    assert w.technical['window_ms'] == 10.0


def test_a_window_set_by_hand_survives_a_stimulus_change():
    """Si el docente cambió la ventana a mano, cambiar de estímulo no se
    la devuelve a la del preset (ni la envolvente)."""
    if not HAS_UI:
        return
    w = _ventana_con_permiso(777)
    w.technical['window_ms'] = 15.0             # Parámetros avanzados
    w.control.cb_stim.setCurrentText('Burst 1 kHz')
    assert w.technical['window_ms'] == 15.0
    assert w.technical['burst_envelope'] == 'ms-1-10-1'
    w.technical['burst_envelope'] = '2-1-2'
    w.control.cb_stim.setCurrentText('Burst 2 kHz')
    assert w.technical['burst_envelope'] == '2-1-2'
    w.control.cb_stim.setCurrentText('Click')
    assert w.technical['window_ms'] == 15.0


def test_the_student_does_not_get_the_standard_setup():
    """El alumno arranca con el protocolo y lo demás al azar."""
    if not HAS_UI:
        return
    w = _ventana_con_permiso(1)
    assert w.control.get_data()['filter_passhigh'] != '5'
    assert w.technical['window_ms'] == 10
    w.control.cb_stim.setCurrentText('Burst 1 kHz')
    assert w.technical['burst_envelope'] == '2-1-2'


def test_the_baseline_is_drawn_from_bl_to_fin():
    """BL deja una línea de base a la vista; con FIN termina ahí."""
    if not HAS_UI:
        return
    w = _ventana()
    curva = _capturar(w)
    g = w.graph_r
    g.current_lat = 0.15
    g.create_marks('BL')
    xs, ys = g.base_lines[curva].getData()
    assert abs(xs[0] - 0.15) < 0.05 and abs(xs[1] - g.window_ms) < 1e-9
    assert ys[0] == ys[1]
    puestas = _marcar(w, curva)
    xs, _ = g.base_lines[curva].getData()
    assert abs(xs[1] - puestas['FIN']) < 0.05, (xs, puestas)
    g.delete_mark('BL')
    assert curva not in g.base_lines


def _pixel(g, lat, curva=None):
    from PySide6.QtCore import QPointF
    y = 0.0
    if curva is not None:
        xs, ys = g.data[curva]['ipsi_xy']
        y = float(np.interp(lat, xs, ys)) + g.data[curva].get('gap', 0.0)
    return g.mapFromScene(g.pw.vb.mapViewToScene(QPointF(lat, y)))


def _arrastre(g, desde, hasta, pasos=8):
    """Apretar, mover y soltar con el mouse, como en clase."""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    QTest.mousePress(g.viewport(), Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, desde)
    for k in range(1, pasos + 1):
        QTest.mouseMove(g.viewport(), QPoint(
            int(desde.x() + (hasta.x() - desde.x()) * k / pasos),
            int(desde.y() + (hasta.y() - desde.y()) * k / pasos)))
        QApplication.processEvents()
    QTest.mouseRelease(g.viewport(), Qt.MouseButton.LeftButton,
                       Qt.KeyboardModifier.NoModifier, hasta)
    QApplication.processEvents()


def _ventana_visible():
    from PySide6.QtWidgets import QApplication
    w = _ventana()
    w.resize(1400, 900)
    w.show()
    QApplication.processEvents()
    return w


def test_cursor_a_can_be_dragged_before_any_mark():
    """Las banderas se arrastran con el mouse aunque no haya marcas."""
    if not HAS_UI:
        return
    w = _ventana_visible()
    _capturar(w)
    g = w.graph_r
    g.inf_a.setPos((1.0, 0))              # fuera del borde del eje
    x0 = g.inf_a.getXPos()
    _arrastre(g, _pixel(g, x0), _pixel(g, 2.0))
    assert abs(g.inf_a.getXPos() - 2.0) < 0.3, g.inf_a.getXPos()
    # A' se agarra por la parte de abajo de la línea: a la altura de la
    # curva, en el borde derecho, está su etiqueta de intensidad, y arriba
    # su bandera.
    from PySide6.QtCore import QPointF
    arriba = -g.scale_uv * 0.3
    _arrastre(g, g.mapFromScene(g.pw.vb.mapViewToScene(
                  QPointF(g.inf_b.getXPos(), arriba))),
              g.mapFromScene(g.pw.vb.mapViewToScene(QPointF(4.0, arriba))))
    assert abs(g.inf_b.getXPos() - 4.0) < 0.3, g.inf_b.getXPos()
    # Y arrastrando la bandera (el rótulo de arriba) la línea sigue al
    # mouse, no una fracción de su movimiento.
    class _Arrastre:
        def __init__(self, x, fin=False):
            self._p = g.pw.vb.mapViewToScene(QPointF(x, 0))
            self._fin = fin
        def button(self):
            return __import__('PySide6.QtCore', fromlist=['Qt']).Qt.MouseButton.LeftButton
        def accept(self):
            pass
        def ignore(self):
            pass
        def scenePos(self):
            return self._p
        def isFinish(self):
            return self._fin
    for x in (2.5, 3.0):
        g.inf_a.label.mouseDragEvent(_Arrastre(x, fin=(x == 3.0)))
    assert abs(g.inf_a.getXPos() - 3.0) < 0.05, g.inf_a.getXPos()


def test_the_auto_mark_respects_read_only_sessions():
    """Una sesión cerrada solo se mira: tampoco con el botón Auto."""
    if not HAS_UI:
        return
    w = _ventana()
    curva = _capturar(w)
    w.set_view_mode(True)
    w.auto_ecochg_mark(0)
    assert not w.graph_r.marks.get(curva)


def test_dragging_the_label_of_a_deleted_curve_does_not_crash():
    """Arrastrar la etiqueta de una curva que ya no está no revienta."""
    if not HAS_UI:
        return
    w = _ventana()
    curva = _capturar(w)
    g = w.graph_r
    g.active_curve(curva)
    g.delete_curve()
    g.drag_curve({'pos': (10.0, -1.0), 'name': curva})
    assert curva not in g.data


def test_the_y_axis_can_be_inverted():
    """El botón da vuelta el eje de los dos oídos."""
    if not HAS_UI:
        return
    w = _ventana()
    # El botón dice dónde quedó el negativo.
    assert w.btn_invert_y.text() == "−↓"
    assert 'abajo' in w.btn_invert_y.toolTip()
    w.btn_invert_y.setChecked(True)
    assert w.graph_r.pw.getViewBox().yInverted()
    assert w.graph_l.pw.getViewBox().yInverted()
    assert w.btn_invert_y.text() == "−↑"
    assert 'arriba' in w.btn_invert_y.toolTip()
    w.btn_invert_y.setChecked(False)
    assert not w.graph_r.pw.getViewBox().yInverted()
    assert w.btn_invert_y.text() == "−↓"


def test_the_auto_mark_button_fills_the_table():
    """El equipo marca solo, y de ahí salen las medidas.

    Es lo que hace cualquier equipo real: pone las cuatro marcas y el
    clínico corrige. No es la respuesta -- detecta sobre el trazo.
    """
    if not HAS_UI:
        return
    w = _ventana(_caso(sp_ap=0.25))
    curva = _capturar(w)
    assert w.table_ec_r.medidas == {}
    w.table_ec_r.btn_auto.click()
    medidas = w.table_ec_r.medidas
    assert medidas.get('faltan') == []
    assert abs(medidas['sp_ap'] - 0.25) < 0.08
    # Las marcas quedan puestas como cualquier otra: se pueden corregir.
    assert set(w.graph_r.marks[curva]) == set(ecochg.AUTO_MARKS)


def test_the_auto_mark_is_not_the_answer():
    """Marcando bien sobre un registro mal hecho, la medida sale mal.

    El potencial de sumación es un desplazamiento DC y el pasa-alto se lo
    come: con la constante de tiempo de un corte en 200 Hz (0.8 ms) el PS
    pierde un tercio de sus µV.
    El marcado automático no lo sabe -- pone las marcas igual. Si en vez de
    medir el trazo devolviera lo que el caso declara, el examen no
    existiría.
    """
    if not HAS_UI:
        return
    medidas = {}
    for pasa_alto in ('10', '200'):
        w = _ventana(_caso(sp_ap=0.55))
        idx = w.control.cb_filter_up.findText(pasa_alto)
        assert idx >= 0
        w.control.cb_filter_up.setCurrentIndex(idx)
        leidas = []
        # Tres curvas del mismo oído al mismo nivel: la razón de UNA
        # captura tiene su ruido, y lo que se compara acá es la banda.
        razones = []
        for _ in range(3):
            curva = _capturar(w, 90)
            w.graph_r.active_curve(curva)
            w.table_ec_r.btn_auto.click()
            valor = w.table_ec_r.medidas.get('sp_amp')
            if valor is not None:
                leidas.append(valor)
                razones.append(w.table_ec_r.medidas.get('sp_ap'))
        medidas[pasa_alto] = sum(leidas) / len(leidas)
        if pasa_alto == '10':
            assert abs(sum(razones) / len(razones) - 0.55) < 0.10, razones
    # Con la banda del ABR el pasa-alto se come el PS (es un desplazamiento
    # DC): la misma cóclea informa bastante menos µV de sumación, y el
    # equipo no avisa. La RAZÓN se mueve poco, porque la meseta también es
    # parte de la profundidad del PA (ver docs/decisiones.md).
    assert medidas['200'] < 0.8 * medidas['10'], medidas


def test_switching_test_with_curves_asks_first():
    """Cambiar de prueba empieza un registro nuevo, y avisa.

    El ABR y el ECochG no se apilan en el mismo gráfico --ventanas
    distintas, y el ECochG tiene el PA hacia abajo-- y el informe se sube
    con UN tipo. Pero el combo está a un clic, así que no puede borrar sin
    preguntar.
    """
    if not HAS_UI:
        return
    w = _ventana()
    curva = _capturar(w)
    assert curva in w.memory

    preguntas = []
    w.confirm_test_change = lambda test: (preguntas.append(test), False)[1]
    w.control.cb_test.setCurrentText('ABR')
    assert preguntas == ['ABR']
    assert w.control.cb_test.currentText() == 'ECochG'
    assert curva in w.memory            # no se borró nada

    w.confirm_test_change = lambda test: True
    w.control.cb_test.setCurrentText('ABR')
    assert w.control.cb_test.currentText() == 'ABR'
    assert w.memory == {}


def test_the_report_goes_up_as_an_ecochg():
    """La tabla `reports` ya distingue ELECTROCOCLEO de ABR."""
    if not HAS_UI:
        return
    w = _ventana()
    subidos = []

    class _Cliente:
        def __init__(self, *a, **k):
            pass

        def is_logged_in(self):
            return True

        def upload_report(self, appointment_id, tipo, data, images):
            subidos.append(tipo)

    import abr.AbrMainWindow as modulo
    original = modulo.BackendClient
    modulo.BackendClient = _Cliente
    try:
        _capturar(w)
        w.submit_report()
    finally:
        modulo.BackendClient = original
    assert subidos == ['ELECTROCOCLEO']


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
