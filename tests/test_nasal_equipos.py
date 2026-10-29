"""Tests de los equipos nasales en LabSim (nasal/equipos.py, nasal/sesion.py).

1. Sin bloque NASAL en el caso el equipo no mide: los paneles quedan
   apagados y el mensaje lo dice (no hay nariz normal de relleno).
2. La rinomanometría mide las dos fosas, la tabla trae la fila total y
   con vasoconstrictor suma las columnas del cambio.
3. La rinometría no mide sin calibrar; calibrada, tres registros por fosa.
4. Los dos equipos comparten la nariz: el vasoconstrictor puesto en uno vale
   para el otro en la misma atención, y una atención nueva empieza en reposo.
5. La medición corre fuera de la ventana y deja los botones apagados
   mientras tanto.
6. La misma atención y los mismos pasos dan la misma medición (semillas
   estables, no hash()).
7. La pestaña "Lo que el equipo no sabe" es solo para docente/admin.
8. El minuto del ciclo corre con el reloj de la sesión.
"""

import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
SRC = os.path.join(os.path.dirname(__file__), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.base import context  # noqa: E402,F401  (crea la QApplication)
from nasal import modelo, sesion  # noqa: E402
from nasal.equipos import RinometriaWindow, RinomanometriaWindow  # noqa: E402

ADMIN = {'permission': 777}


def medir(w, lado):
    """La medición corre en otro hilo (hilos.en_fondo): se espera el aviso."""
    w._medir(lado)
    while w.midiendo:
        context.app.processEvents()
        if w.tarea is not None:
            w.tarea.esperar(20)
    context.app.processEvents()
ALUMNO = {'permission': 1}


def caso(cuadro='mixta'):
    return {'NASAL': modelo.paciente(cuadro), 'edad': 40,
            'paciente_snapshot': {'nombre': 'Ana', 'apellido': 'Pérez'}}


def test_sin_nariz_no_mide():
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super({'edad': 30}, 'sin-nariz')
    assert not w.panel_examen.isEnabled()
    assert 'no tiene la nariz' in w.lbl_mensaje.text()
    medir(w, 'D')
    assert w.res['reposo']['D'] is None
    w.la_super(None, None)
    assert 'Abre una atención' in w.lbl_mensaje.text()


def test_rinomanometria_mide_y_tabula():
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super(caso(), 'rm-1')
    medir(w, 'D')
    medir(w, 'I')
    assert w.res['reposo']['D'] and w.res['reposo']['I']
    assert w.tabla.rowCount() == 3 and w.tabla.item(2, 0).text() == 'Total'
    columnas = w.tabla.columnCount()
    w._vasoconstrictor()
    medir(w, 'D')
    assert w.res['vc']['D'] and w.res['vc']['D']['estado']['vc']
    assert w.tabla.columnCount() == columnas + 2
    assert not w.btn_vc.isEnabled()


def test_rinometria_pide_calibrar():
    w = RinometriaWindow(data_login=ADMIN)
    w.la_super(caso(), 'ra-1')
    medir(w, 'D')
    assert w.res['reposo']['D'] is None
    assert 'calibra' in w.lbl_mensaje.text().lower()
    w._calibrar()
    medir(w, 'D')
    assert len(w.res['reposo']['D']['registros']) == 3


def test_vasoconstrictor_compartido():
    rm = RinomanometriaWindow(data_login=ADMIN)
    ra = RinometriaWindow(data_login=ADMIN)
    data = caso()
    rm.la_super(data, 'compartida')
    ra.la_super(data, 'compartida')
    assert rm.sesion is ra.sesion
    rm._vasoconstrictor()
    ra._calibrar()
    medir(ra, 'D')
    assert ra.res['vc']['D'] is not None and ra.res['reposo']['D'] is None
    ra.la_super(data, 'otra-atencion')
    assert not ra.sesion.vc


def test_mide_en_segundo_plano():
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super(caso(), 'fondo')
    w._medir('D')
    assert w.midiendo and not w.btn_d.isEnabled() and not w.btn_vc.isEnabled()
    while w.midiendo:
        context.app.processEvents()
        w.tarea.esperar(20)
    assert w.res['reposo']['D'] is not None and w.btn_d.isEnabled()


def test_misma_atencion_misma_medicion():
    def una():
        sesion._actual = None
        w = RinomanometriaWindow(data_login=ADMIN)
        w.la_super(caso('cornetes'), 'repetible')
        medir(w, 'D')
        return w.res['reposo']['D']['lecturas'][150]['insp']
    assert una() == una()


def test_verdad_solo_docente():
    assert RinomanometriaWindow(data_login=ADMIN).verdad is not None
    assert RinomanometriaWindow(data_login={'permission': 555}).verdad is not None
    alumno = RinometriaWindow(data_login=ALUMNO)
    assert alumno.verdad is None and alumno.chk_verdad is None
    assert alumno.tabs.count() == 1


def test_minuto_corre_con_el_reloj():
    t = [1000.0]
    s = sesion.SesionNasal(caso(), 'reloj', reloj=lambda: t[0])
    m0 = s.minuto()
    t[0] += 30 * 60
    assert s.minuto() == m0 + 30
    assert 0 <= s.minuto_llegada < 150


if __name__ == '__main__':
    fallas = 0
    for nombre, fn in list(globals().items()):
        if nombre.startswith('test_') and callable(fn):
            try:
                fn()
                print(f'  {nombre} OK')
            except Exception as exc:  # noqa: BLE001
                fallas += 1
                print(f'  {nombre} FALLA: {exc!r}')
    print('TODOS LOS TESTS PASARON' if not fallas else f'{fallas} FALLARON')
    sys.stdout.flush()
    os._exit(1 if fallas else 0)
