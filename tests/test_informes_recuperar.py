"""Retomar la atención: cada módulo de examen recupera lo que ya se había
guardado solo (core/report_autosave.py).

Antes, cerrar la app con la atención abierta perdía todo. Ahora el informe
se guarda solo en el servidor, y al retomar la atención vuelve a cada
módulo. Acá se prueba la ida y vuelta de cada uno: lo que sube
report_job() tiene que alcanzar para rearmarlo con restore_report().

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np  # noqa: E402

from core.base import context  # noqa: E402

try:
    import pyqtgraph  # noqa: F401
    HAS_UI = True
except ImportError:
    HAS_UI = False

APP = context.app
LOGIN = {'name': 'Alumno', 'user': 'al', 'permission': 'user'}


def _viaje(data):
    """Lo que pasa por el backend es JSON."""
    return json.loads(json.dumps(data))


# ------------------------------------------------------------ Otoscopia

def test_otoscopia_vuelve_igual():
    from audiometria.OtoscopiaInforme import InformeOtoscopia
    a = InformeOtoscopia()
    a.panel_od.diagrama.marcas['aps'] = ['perforation', 'tympanosclerosis']
    a.panel_od.checks_cae['cae_cerumen'].setChecked(True)
    a.panel_oi.txt_observaciones.setPlainText('Membrana opaca')
    guardado = _viaje(a.to_dict())
    b = InformeOtoscopia()
    b.from_dict(guardado)
    assert b.to_dict() == guardado


def test_otoscopia_lee_el_formato_viejo():
    from audiometria.OtoscopiaInforme import InformeOtoscopia
    b = InformeOtoscopia()
    b.from_dict({'od': {'cuadrantes': {'aps': 'perforation'}}, 'oi': {}})
    assert b.panel_od.diagrama.marcas == {'aps': ['perforation']}


# ------------------------------------------------------------ AABR

def test_aabr_vuelve_con_su_resultado_y_texto():
    if not HAS_UI:
        return
    import test_aabr as t
    w = t._ventana(t._oido(10), t._oido(85, 'coclear'))
    t._tamizar(w)
    w.txt_conducta.setPlainText('Rescreening en 15 días')
    guardado = _viaje(w.report_data())
    w2 = t._ventana(t._oido(10), t._oido(85, 'coclear'))
    assert w2.restore_report(guardado)
    assert w2.cb_informe['OD'].currentText() == 'PASA'
    assert w2.resultado['OD']['veredicto'] == 'PASA'
    assert w2.resultado['OI'] is None
    assert w2.txt_conducta.toPlainText() == 'Rescreening en 15 días'
    assert _viaje(w2.report_data())['resultados'] == guardado['resultados']


def test_aabr_no_pisa_un_tamizaje_nuevo():
    if not HAS_UI:
        return
    import test_aabr as t
    w = t._ventana(t._oido(10))
    t._tamizar(w)
    antes = w.report_data()
    assert not w.restore_report({'resultados': {'OD': {'veredicto': 'REFIERE', 'barridos': 9,
                                                       'fsp': 1.0}}})
    assert w.report_data()['resultados'] == antes['resultados']


def test_aabr_volver_a_un_oido_ya_tamizado():
    """_reset_lectura le pasaba el dict del resultado a _pintar_veredicto:
    unhashable, reventaba al volver a un oído ya tamizado."""
    if not HAS_UI:
        return
    import test_aabr as t
    w = t._ventana(t._oido(10), t._oido(10))
    t._tamizar(w)
    w.cb_lado.setCurrentText('OI')
    w.cb_lado.setCurrentText('OD')
    assert w.lbl_veredicto.text() == 'PASA'


# ------------------------------------------------------------ VEMP

def _vemp_con_curva():
    import test_vemp as tv
    from vemp.VempMainWindow import VempMainWindow
    w = VempMainWindow(data_login=LOGIN)
    w.la_super(tv.caso(), 42)
    aju = w.control.ajustes()
    registro = w.sesion.nuevo(aju, w.motor.eje(aju.subtipo))
    registro.acumular(w.motor.lote(aju, 60.0, 200))
    registro.terminado = True
    registro.marcar('p13', 13.2, 3.1)
    registro.marcar('n23', 22.8, -2.9)
    w.trazas[registro.lado].agregar(registro)
    w.informe.txt_conclusion.setPlainText('Asimetría dentro de norma')
    return w, registro


def test_vemp_vuelve_con_su_trazo_y_sus_marcas():
    if not HAS_UI:
        return
    import test_vemp as tv
    from vemp.VempMainWindow import VempMainWindow
    w, registro = _vemp_con_curva()
    guardado = _viaje(w.report_job()['data'])
    w2 = VempMainWindow(data_login=LOGIN)
    w2.la_super(tv.caso(), 42)
    assert w2.restore_report(guardado)
    r2 = w2.sesion.get(registro.nombre)
    assert np.allclose(r2.y, registro.y, atol=1e-4)
    assert r2.marcas == registro.marcas
    assert r2.aceptados == registro.aceptados
    assert abs(r2.emg_medio - registro.emg_medio) < 1e-3
    assert registro.nombre in w2.trazas[registro.lado].trazas
    assert w2.informe.conclusion() == 'Asimetría dentro de norma'
    # Y lo que volvería a subir es lo mismo.
    assert _viaje(w2.report_job()['data'])['curvas'] == guardado['curvas']


def test_vemp_sin_trazo_no_inventa_una_curva():
    from vemp.session import Registro
    assert Registro.desde_dict('c-OD-1', {'side': 'OD', 'LatAmp': {}}) is None


# ------------------------------------------------------------ EOA

def test_eoa_recupera_los_resultados_y_no_pisa_lo_nuevo():
    if not HAS_UI:
        return
    from oae.OaeMainWindow import OaeMainWindow
    w = OaeMainWindow(data_login=LOGIN)
    w.teoae_panel._report['OI'] = {'pasa': True, 'nuevo': True}
    guardado = {'pruebas': {'teoae': {'OD': {'pasa': False}, 'OI': {'pasa': False}},
                            'dpoae': {'OD': {'puntos': 5}}},
                'hallazgos': 'TEOAE ausentes en OD', 'conclusion': ''}
    assert w.restore_report(guardado)
    assert w.teoae_panel._report == {'OI': {'pasa': True, 'nuevo': True},
                                     'OD': {'pasa': False}}
    assert w.dpoae_panel._report == {'OD': {'puntos': 5}}
    assert w.report.text_edit_1.toPlainText() == 'TEOAE ausentes en OD'


# ------------------------------------------------------------ reparto

def test_el_reparto_le_da_a_cada_modulo_lo_suyo():
    from core import report_autosave as ra

    class Cliente:
        def is_logged_in(self):
            return True

        def get_my_report(self, cita, tipos):
            return [{'tipo': 'VEMP', 'data': {'n': 2}},     # el más nuevo
                    {'tipo': 'VEMP', 'data': {'n': 1}},
                    {'tipo': 'OTOSCOPIA', 'data': {'od': {}}},
                    {'tipo': 'EOA', 'data': {'x': 1}}]

    class Modulo:
        def __init__(self):
            self.recibido = []

        def restore_report(self, data):
            self.recibido.append(data)

    original = ra._client
    ra._client = Cliente
    try:
        vemp, oto = Modulo(), Modulo()
        auto = ra.ReportAutosave(lambda: [])
        hilo = auto.recuperar(42, {'VEMP': vemp, 'OTOSCOPIA': oto}, lambda cita: cita == 42)
        hilo.wait(5000)
        for _ in range(5):
            APP.processEvents()
        assert vemp.recibido == [{'n': 2}]
        assert oto.recibido == [{'od': {}}]

        tarde = Modulo()
        hilo = auto.recuperar(42, {'VEMP': tarde}, lambda cita: False)
        hilo.wait(5000)
        for _ in range(5):
            APP.processEvents()
        assert tarde.recibido == []   # el alumno ya cambió de atención
    finally:
        ra._client = original


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  {nombre} OK")
            except AssertionError as exc:
                fallas += 1
                print(f"  FAIL {nombre}: {exc!r}")
    print("FALLARON" if fallas else "TODOS LOS TESTS PASARON")
    sys.exit(1 if fallas else 0)
