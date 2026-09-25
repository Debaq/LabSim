"""
Sesiones anteriores del ABR: al mismo paciente se le puede hacer más de un
ABR, y el alumno abre uno anterior para verlo o terminarlo (marcas y
conclusiones, nunca curvas nuevas). Todo vive en el backend: acá se lo
reemplaza por un cliente falso que guarda lo que se le sube.

Necesita PySide6 + pyqtgraph (ver test_abr_panel.py).
"""

import json
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
TESTS = os.path.dirname(__file__)
if TESTS not in sys.path:
    sys.path.insert(0, TESTS)

try:
    import numpy as np
    import test_abr_panel as panel
    import abr.AbrMainWindow as modulo
    HAS_UI = panel.HAS_UI
except ImportError as exc:
    print(f"  (tests de sesiones salteados: {exc})")
    HAS_UI = False


class ClienteFalso:
    """Lo que el módulo usa de BackendClient, sin red."""
    subidas = []
    informes = []
    actuales = []   # lo ya guardado de la cita en curso (my_report.php)

    def __init__(self, *args, **kwargs):
        pass

    def is_logged_in(self):
        return True

    def get_patient_reports(self, appointment_id):
        return self.informes

    def get_my_report(self, appointment_id, tipos=None):
        return self.actuales

    def upload_report(self, appointment_id, tipo, data, images):
        # Lo que viaja de verdad: JSON. Si algo no se serializa, revienta acá.
        ClienteFalso.subidas.append((appointment_id, tipo, json.loads(json.dumps(data))))
        return {'ok': True}


def _preparar():
    ClienteFalso.subidas = []
    ClienteFalso.informes = []
    ClienteFalso.actuales = []
    modulo.BackendClient = ClienteFalso


def _sesion_guardada():
    """Una sesión de otra atención, tal como la devuelve el backend."""
    w = panel._ventana()
    panel._capturar(w, intensidad=80)
    panel._capturar(w, intensidad=60)
    w.report.text_edit_2.setPlainText('Conclusión de la primera')
    data = json.loads(json.dumps(w.session_payload()))
    return {'id': 5, 'tipo': 'ABR', 'appointment_id': 7, 'fecha': '2026-09-10',
            'hora': '10:30:00', 'estado': 'atendido', 'data': data}


def _con_anterior():
    anterior = _sesion_guardada()
    w = panel._ventana()
    w.fill_sessions([anterior])
    return w, anterior


def test_the_payload_carries_the_traces_and_marks():
    if not HAS_UI:
        return
    _preparar()
    w = panel._ventana()
    panel._capturar(w, intensidad=80)
    w.graph_r.act_curve = 'R1'
    w.graph_r.current_lat = 5.6
    w.graph_r.create_marks('V')
    data = w.session_payload()
    curva = data['curvas']['R1']
    assert len(curva['traza']['t']) == len(curva['traza']['ipsi']) == 500
    assert curva['traza']['contra'] is not None
    assert 'V' in curva['marcas_graf']
    assert data['prueba'] == 'ABR'
    json.dumps(data)


def test_a_previous_session_is_drawn_as_it_was():
    if not HAS_UI:
        return
    _preparar()
    w, anterior = _con_anterior()
    w.select_session(0)
    assert w.curves_R == ['R1', 'R2']
    assert w.graph_r.curve_int == {'R1': 80, 'R2': 60}
    guardado = anterior['data']['curvas']['R1']['traza']
    assert np.allclose(w.graph_r.data['R1']['ipsi_xy'][1], guardado['ipsi'])
    assert w.report.text_edit_2.toPlainText() == 'Conclusión de la primera'
    assert w.cb_session.currentIndex() == 1


def test_a_previous_session_does_not_record_or_lose_curves():
    if not HAS_UI:
        return
    _preparar()
    w, _ = _con_anterior()
    w.select_session(0)
    assert not w.control.isEnabled()
    w.capture_state('record')          # aunque llegara la señal
    assert w.state_capture == 'stopped'
    w.graph_r.act_curve = 'R1'
    w.graph_r.delete_curve()
    assert 'R1' in w.graph_r.data and 'R1' in w.memory


def test_going_back_restores_the_current_session():
    if not HAS_UI:
        return
    _preparar()
    w, _ = _con_anterior()
    panel._capturar(w, intensidad=70)
    w.report.text_edit_1.setPlainText('hallazgos de hoy')
    actual = np.asarray(w.graph_r.data['R1']['ipsi_xy'][1]).copy()
    w.select_session(0)
    w.select_session(None)
    assert w.curves_R == ['R1']
    assert w.graph_r.curve_int == {'R1': 70}
    assert np.allclose(w.graph_r.data['R1']['ipsi_xy'][1], actual, atol=1e-3)
    assert w.report.text_edit_1.toPlainText() == 'hallazgos de hoy'
    assert w.control.isEnabled()
    panel._capturar(w, intensidad=50)
    assert w.curves_R == ['R1', 'R2']


def test_a_previous_session_is_read_only():
    """Una atención cerrada no se actualiza más: ni marcas, ni borrar
    marcas, ni texto del informe, y nada se sube."""
    if not HAS_UI:
        return
    _preparar()
    w, anterior = _con_anterior()
    w.select_session(0)
    antes = dict(w.graph_r.marks.get('R1', {}))
    w.graph_r.act_curve = 'R1'
    w.graph_r.current_lat = 5.7
    w.graph_r.create_marks('V')
    w.graph_r.delete_all_marks()
    assert w.graph_r.marks.get('R1', {}) == antes
    w.measure_action({'0': {'V_L': None}})     # marcar desde la tabla
    assert w.memory['R1'] == {k: v for k, v in anterior['data']['curvas']['R1'].items()
                              if k not in ('traza', 'marcas_graf')}
    assert w.report.text_edit_2.isReadOnly()
    assert not hasattr(w, 'btn_save_session')
    w.select_session(None)
    assert not w.report.text_edit_2.isReadOnly()
    assert not w.graph_r.read_only
    assert ClienteFalso.subidas == []


def test_a_past_attention_opens_to_look_only():
    """Desde "Mis pacientes": sin atención en curso, el ABR de una
    atención cerrada se abre para mirar."""
    if not HAS_UI:
        return
    _preparar()
    guardado = _sesion_guardada()['data']
    w = panel._ventana()
    assert not w.open_past(guardado, 'x')      # con atención abierta, no
    w.la_super(None)
    assert w.open_past(guardado, 'Atención del 10/09: solo lectura')
    assert w.curves_R == ['R1', 'R2']
    assert w.view_only and w.graph_r.read_only
    assert not w.control.isEnabled()
    assert w.report_job() is None
    w.la_super(panel._caso(), 42)              # llega una atención nueva
    assert not w.view_only and w.graph_r.data == {}


def test_closing_the_attendance_uploads_the_current_session():
    """Si al cerrar se estaba mirando una anterior, sube la de hoy."""
    if not HAS_UI:
        return
    _preparar()
    w, _ = _con_anterior()
    w.data_login = {'name': 'Alumno', 'user': 'al', 'permission': 'user'}
    panel._capturar(w, intensidad=70)
    w.select_session(0)
    w.export_images = lambda: {}
    w.submit_report()
    cita, tipo, data = ClienteFalso.subidas[-1]
    assert cita == 42
    assert list(data['curvas']) == ['R1']
    assert data['curvas']['R1']['int'] == 70


def test_the_list_comes_from_the_backend():
    if not HAS_UI:
        return
    _preparar()
    ClienteFalso.informes = [_sesion_guardada()]
    w = panel._ventana()
    assert not w.cb_session.isVisibleTo(w)
    w.fetch_sessions()
    assert w.cb_session.count() == 2
    assert w.cb_session.itemText(1) == '10/09/2026 10:30 · ABR'
    assert w.cb_session.isVisibleTo(w)


def test_an_ecochg_session_comes_back_with_its_marks_and_table():
    """Un ECochG anterior: la prueba, el equipo y la tabla PS/PA vuelven."""
    if not HAS_UI:
        return
    import test_ecochg_panel as ec
    _preparar()
    w = ec._ventana()
    ec._capturar(w)
    ec._marcar(w, 'R1')
    medidas = dict(w.memory['R1']['ECochG'])
    anterior = {'id': 6, 'tipo': 'ELECTROCOCLEO', 'appointment_id': 8,
                'fecha': '2026-09-11', 'hora': '09:00:00', 'estado': 'atendido',
                'data': json.loads(json.dumps(w.session_payload()))}

    w2 = panel._ventana()                 # hoy se esta haciendo un ABR
    w2.fill_sessions([anterior])
    w2.select_session(0)
    assert w2.control.cb_test.currentText() == 'ECochG'
    assert w2.es_ecochg() and w2.table_ec_r.isVisibleTo(w2)
    assert set(w2.graph_r.marks['R1']) == set(w.graph_r.marks['R1'])
    for clave in ('ap_lat', 'sp_ap_ratio'):
        if medidas.get(clave) is not None:
            assert abs(w2.memory['R1']['ECochG'][clave] - medidas[clave]) < 1e-2, clave
    w2.select_session(None)
    assert w2.control.cb_test.currentText() == 'ABR'
    assert not w2.es_ecochg()
    assert w2.graph_r.data == {}


def test_resuming_brings_back_what_was_saved():
    """Se cerró la app con la atención abierta: el informe se había guardado
    solo (core/report_autosave.py) y al retomar vuelve tal como estaba."""
    if not HAS_UI:
        return
    _preparar()
    guardado = _sesion_guardada()
    guardado['data']['curvas']['R1']['marcas_graf'] = {'V': [5.6, 0.3]}
    ClienteFalso.actuales = [{'tipo': 'ABR', 'data': guardado['data']}]
    w = panel._ventana()
    w.fetch_sessions()
    assert w.curves_R == ['R1', 'R2']
    assert set(w.memory) == {'R1', 'R2'}
    assert 'V' in w.graph_r.marks['R1']
    assert w.report.text_edit_2.toPlainText() == 'Conclusión de la primera'
    assert w.session_idx is None            # es la sesión en curso, no una anterior
    w.data_login = {'name': 'Alumno', 'user': 'al', 'permission': 'user'}
    job = w.report_job()
    assert job['appointment_id'] == 42 and set(job['data']['curvas']) == {'R1', 'R2'}


def test_resuming_does_not_overwrite_new_work():
    if not HAS_UI:
        return
    _preparar()
    ClienteFalso.actuales = [{'tipo': 'ABR', 'data': _sesion_guardada()['data']}]
    w = panel._ventana()
    panel._capturar(w, intensidad=70)
    w.fetch_sessions()
    assert list(w.memory) == ['R1']
    assert w.memory['R1']['int'] == 70


def test_nothing_is_autosaved_while_looking_at_another_session():
    if not HAS_UI:
        return
    _preparar()
    w, _ = _con_anterior()
    w.data_login = {'name': 'Alumno', 'user': 'al', 'permission': 'user'}
    panel._capturar(w, intensidad=70)
    assert w.report_job() is not None
    w.select_session(0)
    assert w.report_job() is None


def test_the_report_goes_up_even_without_the_temp_folder():
    """En la app instalada no existe local_cache/abr/temp (local_cache no va
    en el build). El JPEG no se escribía, sin error, y la subida reventaba al
    abrir un archivo inexistente: el ABR no llegaba nunca al backend."""
    if not HAS_UI:
        return
    import tempfile
    _preparar()
    w = panel._ventana()
    w.data_login = {'name': 'Alumno', 'user': 'al', 'permission': 'user'}
    panel._capturar(w, intensidad=80)
    base = os.path.join(tempfile.mkdtemp(), 'no', 'existe')
    original = modulo.context.get_resource
    modulo.context.get_resource = lambda ruta: (os.path.join(base, ruta) if ruta.startswith('local_cache')
                                                else original(ruta))
    try:
        imagenes = w.export_images()
        w.submit_report()
    finally:
        modulo.context.get_resource = original
    assert set(imagenes) == {'0', '1', 'lat_int'}
    assert all(os.path.isfile(r) for r in imagenes.values())
    assert ClienteFalso.subidas and ClienteFalso.subidas[-1][1] == 'ABR'


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  {name} OK")
    print("TODOS LOS TESTS PASARON")
