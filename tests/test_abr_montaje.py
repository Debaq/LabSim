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


def test_paciente_nuevo_piel_nueva():
    w = _ventana(_de_libro)
    w.la_super(_caso(), 43)
    assert w.montaje.colocados == {} and w.montaje.impedancias.piel.trazos == []
    # La misma atención no borra lo hecho.
    w.montaje.de_libro(1)
    w.la_super(_caso(), 43)
    assert w.montaje.colocados


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
