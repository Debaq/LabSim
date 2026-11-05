"""El montaje de la pestaña Electrodos manda en las curvas del ABR.

Lo que el alumno hace sobre la cabeza (core/cabeza_electrodos.py) --dónde
pone cada electrodo, si preparó la piel, cuántos canales-- entra al equipo
(technical_config) y de ahí a la curva:

- sin electrodos no hay registro;
- bien hecho (Cz, mastoides, Fpz, piel preparada) hay respuesta;
- con la piel sin preparar la impedancia tapa la respuesta;
- activo y referencia cambiados dan la curva al revés;
- la única referencia del lado no estimulado da el canal contralateral
  (sin onda I);
- sin tierra entra la red;
- Parámetros avanzados ya no toca los electrodos.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim_datos_"))
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(RAIZ)

from test_abr_panel import _banda, _capturar, _caso  # noqa: E402  (crea el QApplication)
import numpy as np  # noqa: E402
from abr.ABR_generator import ABRGenerator  # noqa: E402
from abr.AbrMainWindow import AbrMainWindow  # noqa: E402
from core import cabeza_electrodos as ce  # noqa: E402


def _ventana(montar):
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(_caso(), 42)
    assert w.tabWidget.currentWidget() is w.montaje      # paciente nuevo: a los electrodos
    w.control.sb_prom.setValue(2000)
    w.control.sb_rate.setValue(21.1)
    _banda(w, '100', '3000')
    montar(w.montaje)
    w.tabWidget.setCurrentWidget(w.abr)
    _capturar(w, 80, 'OD')
    return w


def _de_libro(m):
    m.de_libro(1)


def test_sin_electrodos_no_hay_registro():
    w = _ventana(lambda m: None)
    assert set(w.technical['electrodes'].values()) == {'No Conectado'}
    assert w.last_metadata['fsp'] < 1.5
    # Entradas abiertas: el rechazo descarta todo y no hay trazo, ni de ruido.
    assert w.last_metadata['accepted_sweeps'] == 0
    _x, y = w.graph_r.data[list(w.graph_r.data)[-1]]['ipsi_xy']
    assert np.allclose(y, 0)


def test_sin_electrodos_el_assr_no_registra():
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(_caso(), 42)
    w.control.cb_test.setCurrentText('ASSR')
    w.assr_panel.actualizar_equipo(w.technical)
    assert w.assr_panel.rec is not None
    w.assr_panel.tick()
    assert w.assr_panel.rec.n == 0
    assert 'SIN ELECTRODOS' in w.assr_panel.lbl_estado.text()
    w.montaje.de_libro(1)
    w.assr_panel.actualizar_equipo(w.technical)
    w.assr_panel.tick()
    assert w.assr_panel.rec.n > 0


def test_bien_hecho_hay_respuesta():
    w = _ventana(_de_libro)
    assert w.technical['electrodes'] == {'vertex': 'Cz', 'right': 'M2',
                                         'left': 'No Conectado', 'ground': 'Fpz'}
    assert max(w.technical['impedance'][k] for k in ('vertex', 'right')) < 5.0
    assert w.last_metadata['fsp'] > 3.0


def test_sin_preparar_la_impedancia_tapa_la_respuesta():
    def sin_preparar(m):
        for sitio in ('Cz', 'M2', 'Fpz'):
            m.poner_en_sitio(sitio)
    w = _ventana(sin_preparar)
    assert w.technical['impedance']['vertex'] > 5.0
    assert w.last_metadata['fsp'] < _ventana(_de_libro).last_metadata['fsp'] / 2
    assert ('electrodo_sin_preparar', 'Cz') in w.montaje.errores


def test_al_reves_la_curva_se_invierte():
    def al_reves(m):
        m.de_libro(1)
        m.sacar_todos()
        for sitio in ('M2', 'Cz', 'Fpz'):           # activo en la mastoides
            m.poner_en_sitio(sitio)
    w = _ventana(al_reves)
    assert w.technical['electrode_gain'] < 0


def test_referencia_del_otro_lado_es_el_canal_contra():
    def contra(m):
        m.de_libro(2)
        m._quitar('ref_der')                        # queda M1, estimulando OD
        m.poner_canales(1)
    w = _ventana(contra)
    assert w.technical['electrodes']['right'] == 'No Conectado'
    assert ABRGenerator.solo_referencia_contra(w.technical, 'OD')


def test_sin_tierra_entra_la_red():
    def sin_tierra(m):
        m.de_libro(1)
        m._quitar('tierra')
    w = _ventana(sin_tierra)
    assert w.technical['electrodes']['ground'] == 'No Conectado'
    assert w.last_metadata['fsp'] < _ventana(_de_libro).last_metadata['fsp'] / 2


def test_parametros_avanzados_no_pisa_los_electrodos():
    w = _ventana(_de_libro)
    antes = dict(w.technical['electrodes'])
    from abr.AbrAdvanceSettings import AbrAdvanceSettings
    w.technical = AbrAdvanceSettings(w.technical, 'ABR').get_data()
    w._con_montaje()                                 # lo que hace al aceptar
    assert w.technical['electrodes'] == antes


def test_el_informe_lleva_el_montaje():
    w = _ventana(_de_libro)
    data = w.session_payload()
    assert data['electrodos']['activo']['sitio'] == 'Cz'
    assert data['tecnica']['montaje'] == 'Cz - M2'
    assert data['preparacion_errores'] == []


def test_el_eeg_se_ve_bajo_la_cabeza():
    """En la pestaña Electrodos el monitor de EEG va bajo la cabeza (se ve el
    trazo limpiarse al corregir un electrodo) y vuelve a su lugar al salir."""
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(_caso(), 42)
    assert w.montaje.ranura_eeg.indexOf(w.eeg) >= 0
    w.tabWidget.setCurrentWidget(w.abr)
    assert w.montaje.ranura_eeg.indexOf(w.eeg) < 0
    assert w.detail.layout_tab1_secction1.indexOf(w.eeg) >= 0
    w.tabWidget.setCurrentWidget(w.montaje)
    assert w.montaje.ranura_eeg.indexOf(w.eeg) >= 0


def test_aunque_algo_pise_el_equipo_manda_la_cabeza():
    """Sesiones anteriores o informes guardados antes de la pestaña
    Electrodos traen los electrodos de fábrica (Cz, A1, A2, Fpz): el EEG y la
    captura igual usan lo que está puesto en la cabeza."""
    from abr.AbrAdvanceSettings import default_settings
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(_caso(), 42)
    w.technical = default_settings('ABR')            # electrodos de fábrica
    w.refresh_eeg()
    assert w.technical['electrodes']['vertex'] == 'No Conectado'
    w.technical = default_settings('ABR')
    w.tabWidget.setCurrentWidget(w.abr)
    _capturar(w, 80, 'OD')
    assert w.last_metadata['accepted_sweeps'] == 0


def test_otro_paciente_abre_en_abr_y_lo_suyo_si_se_recupera():
    """Si el paciente anterior quedó en ASSR, el siguiente abría en ASSR y
    parecía una sesión ajena (lo vio el autor, 2026-10-28). Paciente nuevo:
    prueba ABR. Retomar SU atención sí trae lo que se guardó de ella."""
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(_caso(), 16)
    w.montaje.de_libro(1)
    w.control.cb_test.setCurrentText('ASSR')
    w.assr_panel.actualizar_equipo(w.technical)
    for _ in range(5):
        w.assr_panel.tick()
    guardado = w.session_payload()
    assert guardado['prueba'] == 'ASSR'

    w.la_super(_caso(edad=50), 99)                    # otro paciente
    assert w.test_actual == 'ABR' and w.control.cb_test.currentText() == 'ABR'
    assert w.otras_pruebas == {}

    w.la_super(_caso(), 16)                           # vuelve el primero
    w.apply_restored([{'tipo': 'ASSR', 'data': guardado}], 'u', 16)
    assert w.test_actual == 'ASSR'


def test_paciente_nuevo_piel_nueva():
    w = _ventana(_de_libro)
    w.la_super(_caso(), 43)
    assert w.montaje.colocados == {} and w.montaje.impedancias.piel.trazos == []
    # La misma atención no borra lo hecho.
    w.montaje.de_libro(1)
    w.la_super(_caso(), 43)
    assert w.montaje.colocados



def test_sin_fonos_no_llega_el_estimulo():
    def sin_fonos(m):
        m.de_libro(1)
        for canal in ('OD', 'OI'):
            m._sacar_fono(canal)
    w = _ventana(sin_fonos)
    assert w.technical['fonos']['OD']['oido'] is None
    assert w.last_metadata['fsp'] < _ventana(_de_libro).last_metadata['fsp'] / 2


def test_fonos_cruzados_registran_el_otro_oido():
    caso = _caso()
    caso['ABR']['OI']['umbral'] = 100          # oído izquierdo sin respuesta
    def cruzados(m):
        m.de_libro(1)
        for canal, oido in (('OD', 'OI'), ('OI', 'OD')):
            m.fonos.apretar(canal, ahora=0.0)
            m.fonos.soltar(canal, ahora=2.0)
            m.fonos.poner(canal, oido, ahora=2.0)
        m._pintar()
    w = AbrMainWindow({'name': 'Docente', 'user': 'doc', 'permission': 'admin'})
    w.la_super(caso, 42)
    w.control.sb_prom.setValue(2000)
    w.control.sb_rate.setValue(21.1)
    _banda(w, '100', '3000')
    cruzados(w.montaje)
    w.tabWidget.setCurrentWidget(w.abr)
    _capturar(w, 80, 'OD')
    assert w.last_metadata['fsp'] < _ventana(_de_libro).last_metadata['fsp'] / 2
    assert ('fono_cruzado', 'OD') in w.montaje.errores


def test_el_ruido_sale_por_el_otro_fono():
    w = _ventana(_de_libro)
    setting = dict(w.current_setting, mkg=60)
    real, s, _t = w._por_los_fonos('OD', setting)
    assert real == 'OD' and s['mkg'] == 60
    w.montaje._sacar_fono('OI')
    _real, s, t = w._por_los_fonos('OD', setting)
    assert s['mkg'] == 0 and t['masking_offset_db'] == 0.0
    # A medio meter el estímulo llega con menos nivel.
    w.montaje.fonos.poner('OI', 'OI', ahora=0.0)     # sin enrollar
    w.montaje._pintar()
    _real, s, _t = w._por_los_fonos('OI', dict(setting, int=80))
    assert s['int'] == 80 - ce.PERDIDA_SUPERFICIAL_DB


def test_el_informe_lleva_los_fonos():
    w = _ventana(_de_libro)
    assert w.session_payload()['fonos']['OD'] == {'oido': 'OD', 'profunda': True, 'oliva': 'adulto'}



def test_al_admin_no_le_toca_preparar_la_cabeza():
    """El docente/admin encuentra el montaje hecho y el equipo en el
    estándar: puede tomar el ASSR o el ECochG sin limpiar la piel."""
    w = AbrMainWindow({'name': 'Admin', 'user': 'adm', 'permission': 777})
    w.la_super(_caso(), 42)
    assert w.tabWidget.currentWidget() is w.abr
    assert w.technical['electrodes']['vertex'] == 'Cz'
    assert {c: v['oido'] for c, v in w.technical['fonos'].items()} == {'OD': 'OD', 'OI': 'OI'}
    assert w.control.get_data()['filter_passhigh'] == '100'
    w.control.cb_test.setCurrentText('ASSR')
    w.capture_state('record')
    for _ in range(3):
        w.capture()
    assert w.assr_panel.rec.n > 0
    w.capture_state('stopped')
    w.control.cb_test.setCurrentText('ECochG')
    assert w.montaje.montaje()['activo']['sitio'] == 'cae_der'
    # El alumno sigue empezando de cero.
    a = AbrMainWindow({'name': 'Alumno', 'user': 'al', 'permission': 444})
    a.la_super(_caso(), 42)
    assert a.tabWidget.currentWidget() is a.montaje and a.montaje.colocados == {}



def test_el_docente_reinicia_el_montaje_desde_el_panel():
    """attendances.montaje_reinicio llega con el sync: la app empieza de cero
    una vez por pedido, y no lo repite al reabrir la atención."""
    from core import helpers

    class Cliente:
        user = {"id": 34, "username": "dana", "role": "student"}
    viejo_estado, viejo_cliente = helpers._estado_agenda, helpers._backend_client
    try:
        helpers._backend_client = Cliente()
        helpers._estado_agenda = {"students": [], "appointments": {}, "cases": {},
                                  "attendances": {1: {"id": 1, "appointment_id": 42, "student_id": 34,
                                                      "montaje_reinicio": 0}}}
        assert helpers.reinicio_montaje(42) == 0 and helpers.reinicio_montaje(99) == 0
        w = _ventana(_de_libro)
        assert not w.reinicio_docente(helpers.reinicio_montaje(42))
        helpers._estado_agenda["attendances"][1]["montaje_reinicio"] = 1
        assert w.reinicio_docente(helpers.reinicio_montaje(42))
        assert w.montaje.colocados == {} and w.montaje.reinicios == ["docente"]
        assert w.tabWidget.currentWidget() is w.montaje
        w._aviso_reinicio.close()
        assert not w.reinicio_docente(1)                  # el mismo pedido no se repite
        guardado = w.montaje.estado()
        w.la_super(_caso(), 43)                           # otro paciente y vuelve
        w.la_super(_caso(), 42)
        w.montaje.restaurar(guardado)
        assert not w.reinicio_docente(1) and w.montaje.reinicio_docente == 1
    finally:
        helpers._estado_agenda, helpers._backend_client = viejo_estado, viejo_cliente
    # Al docente no: su montaje se pone solo.
    a = AbrMainWindow({'name': 'Admin', 'user': 'adm', 'permission': 777})
    a.la_super(_caso(), 42)
    assert not a.reinicio_docente(5)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
