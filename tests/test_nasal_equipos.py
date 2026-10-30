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
10. La rinomanometría se registra como en el equipo: adaptador en una
    narina, máscara, presión y flujo en el tiempo; las indicaciones al
    paciente cambian los ciclos siguientes y la receta los rehace iguales.
6. La misma atención y los mismos pasos dan la misma medición (semillas
   estables, no hash()).
7. La pestaña "Lo que el equipo no sabe" es solo para docente/admin.
8. El minuto del ciclo corre con el reloj de la sesión.
9. El informe: sin mediciones o sin atención real no hay nada que subir;
   con mediciones sube la tabla que se ve, cómo se tomó cada medición y las
   imágenes, y al retomar la atención las mediciones vuelven idénticas.
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
    """La medición corre en otro hilo (hilos.en_fondo): se espera el aviso.
    En la rinomanometría es un registro de seis ciclos."""
    if isinstance(w, RinomanometriaWindow):
        registrar(w, lado)
        return
    w._medir(lado)
    while w.midiendo:
        context.app.processEvents()
        if w.tarea is not None:
            w.tarea.esperar(20)
    context.app.processEvents()
ALUMNO = {'permission': 1}


def reloj(w):
    """Un reloj de mentira para la ventana (las curvas corren con él)."""
    if not hasattr(w, '_t_falso'):
        w._t_falso = [0.0]
        w._reloj = lambda: w._t_falso[0]
    return w._t_falso


def esperar_vivo(w):
    while w.mon is None or w._mon_nuevo is not None:
        context.app.processEvents()
        if w.tarea is not None:
            w.tarea.esperar(20)
    context.app.processEvents()


def preparar(w, lado):
    """Adaptador en la narina contraria y máscara puesta: en vivo."""
    reloj(w)
    if w.mascara:
        w._mascara()
    if w.sonda != ('I' if lado == 'D' else 'D'):
        w._poner_sonda('I' if lado == 'D' else 'D')
    w._mascara()
    esperar_vivo(w)


def correr(w, segundos):
    """El tiempo pasa de a 0,1 s."""
    t = reloj(w)
    for _ in range(int(round(segundos * 10))):
        t[0] += 0.1
        w._tic()
        # Lo que se calcula en el fondo tarda menos que una respiración.
        if w.tarea is not None:
            w.tarea.esperar(3000)
        context.app.processEvents()


def registrar(w, lado, segundos=20):
    if not (w.sesion and w.sesion.hay_paciente):
        w._registro()
        return
    preparar(w, lado)
    w.cmb_tiempo.setCurrentIndex(w.TIEMPOS.index(segundos))
    w._registro()
    correr(w, segundos + 0.2)
    assert w.rec is None


def poner_vc(w, lados='Las dos'):
    """Fuera máscara y adaptador, vasoconstrictor y sin esperar los 15 min."""
    if w.mascara:
        w._mascara()
    if w.sonda:
        w._poner_sonda(w.sonda)
    w.cmb_fosa_vc.setCurrentText(lados)
    w._vasoconstrictor()
    w.sesion.saltar_espera()


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
    poner_vc(w)
    medir(w, 'D')
    assert w.res['vc']['D'] and w.res['vc']['D']['estado']['vc']
    assert w.tabla.columnCount() == columnas + 2
    assert not w.btn_vc.isEnabled()      # las dos fosas ya tienen


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
    poner_vc(rm, 'Derecha')
    ra._calibrar()
    medir(ra, 'D')
    assert ra.res['vc']['D'] is not None and ra.res['reposo']['D'] is None
    ra.la_super(data, 'otra-atencion')
    assert not ra.sesion.vc


def test_mide_en_segundo_plano():
    w = RinometriaWindow(data_login=ADMIN)
    w.la_super(caso(), 'fondo')
    w._calibrar()
    w._medir('D')
    assert w.midiendo and not w.btn_d.isEnabled() and not w.btn_vc.isEnabled()
    while w.midiendo:
        context.app.processEvents()
        w.tarea.esperar(20)
    assert w.res['reposo']['D'] is not None and w.btn_d.isEnabled()


def test_rm_en_vivo_con_adaptador_o_mascara():
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super(caso(), 'vivo')
    reloj(w)
    w._registro()
    assert w.rec is None and 'adaptador' in w.lbl_mensaje.text()
    w._poner_sonda('I')                     # solo adaptador: presión, sin flujo
    esperar_vivo(w)
    assert w.mon.lado == 'D' and w.timer.isActive()
    correr(w, 4)
    assert max(map(abs, w._P)) > 30 and max(map(abs, w._V)) < 30
    w._registro()
    assert w.rec is None and 'máscara' in w.lbl_mensaje.text()
    w._poner_sonda('I')                     # fuera el adaptador
    assert w.mon is None and not w.timer.isActive()
    w._mascara()                            # solo máscara: flujo por las dos fosas, sin presión
    esperar_vivo(w)
    assert w.mon.abierta
    correr(w, 4)
    assert max(map(abs, w._V)) > 100 and max(map(abs, w._P[-60:])) < 30
    w._poner_sonda('D')                     # con la máscara puesta no se cambia
    assert w.sonda is None and 'Saca la máscara' in w.lbl_mensaje.text()


def test_rm_graba_por_tiempo_y_descarta_lo_anterior():
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super(caso(), 'tiempo')
    preparar(w, 'D')
    correr(w, 9)
    assert w._t[-1] > 8
    w.cmb_tiempo.setCurrentIndex(w.TIEMPOS.index(10))
    w._registro()
    assert w.rec is not None and w._t == [] and not w.btn_vc.isEnabled()
    w._mascara()                            # no se saca grabando
    assert w.mascara
    correr(w, 10.2)
    # 10 s a 3,2 s por ciclo: tres completos.
    assert w.rec is None and len(w.res['reposo']['D']['ciclos']) == 3
    assert w.mediciones[-1]['opciones']['desde'] == 0 and w.timer.isActive()   # sigue en vivo
    w._registro()
    correr(w, 2)
    w._registro()                           # cancelar
    assert w.rec is None and 'cancelada' in w.lbl_mensaje.text()


def test_rm_indicaciones_tardan_y_se_rehacen():
    data = caso('cornetes')
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super(data, '55')
    w.chk_err['boca'].setChecked(True)
    preparar(w, 'D')
    assert w.vista_paciente.boca
    w._indicar('boca')
    assert w.chk_err['boca'].isChecked()    # todavía no: espera a que se regule
    correr(w, 2 * w.DURACION[False] + 0.2)
    assert not w.chk_err['boca'].isChecked() and not w.vista_paciente.boca
    w.chk_err['irregular'].setChecked(True)
    w._registro()
    correr(w, 4)
    w._indicar('parejo')
    while w.tarea is not None and not w.tarea.esperar(20):
        context.app.processEvents()
    context.app.processEvents()
    correr(w, 16.2)
    conds = w.mediciones[-1]['opciones']['registro']
    assert conds[0]['errores'] == {'irregular': True} and conds[-1]['errores'] == {}

    sesion._actual = None
    otra = RinomanometriaWindow(data_login=ADMIN)
    otra.la_super(data, '55')
    assert otra.restore_report(w.report_job()['data'])
    esperar(otra)
    assert otra.res['reposo']['D']['lecturas'] == w.res['reposo']['D']['lecturas']


def test_rm_vasoconstrictor_espera_su_tiempo():
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super(caso('cornetes'), 'vc')
    t = reloj(w)
    w.sesion._reloj = w._reloj
    preparar(w, 'D')
    w._vasoconstrictor()                    # con máscara y adaptador no
    assert not w.sesion.vc and 'Saca la máscara' in w.lbl_mensaje.text()
    w._mascara()
    w._poner_sonda('I')
    w.cmb_fosa_vc.setCurrentText('Derecha')
    w.cmb_farmaco.setCurrentIndex(1)
    w._vasoconstrictor()
    assert w.sesion.fase('D') == 'vc' and w.sesion.fase('I') == 'reposo'
    assert not w.sesion.vc_activo('D') and 'faltan 15:00' in w.pill_estado.text()
    registrar(w, 'D')                       # antes de tiempo: rotulado con VC, sin efecto
    assert w.res['vc']['D'] and not w.res['vc']['D']['estado']['vc']
    t[0] += 15 * 60
    w._cada_segundo()
    assert w.sesion.vc_activo('D') and 'en acción' in w.pill_estado.text()
    correr(w, 4)                            # el paciente en vivo pasa a tener VC
    esperar_vivo(w)
    assert w.mon.estado['vc']
    assert w.sesion.vc_informe()['farmaco']['D'].startswith('Xilometazolina')
    assert 'HR' in w.pill_ambiente.text()


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
    assert [alumno.tabs.tabText(i) for i in range(alumno.tabs.count())] == ['Registro', 'Informe']


def test_minuto_corre_con_el_reloj():
    t = [1000.0]
    s = sesion.SesionNasal(caso(), 'reloj', reloj=lambda: t[0])
    m0 = s.minuto()
    t[0] += 30 * 60
    assert s.minuto() == m0 + 30
    assert 0 <= s.minuto_llegada < 150


def esperar(w):
    while w.midiendo:
        context.app.processEvents()
        w.tarea.esperar(20)
    context.app.processEvents()


def test_informe_y_retomar():
    data = caso('cornetes')
    w = RinomanometriaWindow(data_login=ADMIN)
    w.la_super(data, '123')
    assert w.report_job() is None
    medir(w, 'D')
    medir(w, 'I')
    poner_vc(w, 'Derecha')
    medir(w, 'D')
    w.txt_conclusion.setPlainText('Obstrucción derecha que mejora con VC.')
    job = w.report_job()
    assert job['tipo'] == 'RINOMANOMETRIA' and job['appointment_id'] == 123
    d = job['data']
    assert d['vasoconstrictor']['lados'] == ['D'] and len(d['mediciones']) == 3
    assert d['ambiente']['temperatura'] > 15 and d['segundos'] == 20
    assert d['tabla']['filas'][-1][0] == 'Total'
    imagenes = job['images']()
    assert set(imagenes) == {'rm_curva', 'rm_resistencia'}
    assert all(os.path.getsize(r) > 1000 for r in imagenes.values())

    # Otra vuelta de la misma atención (la app se cerró): vuelve todo igual.
    sesion._actual = None
    otra = RinomanometriaWindow(data_login=ADMIN)
    otra.la_super(data, '123')
    assert otra.restore_report(d)
    esperar(otra)
    for fase, lado in (('reposo', 'D'), ('reposo', 'I'), ('vc', 'D')):
        assert otra.res[fase][lado]['lecturas'] == w.res[fase][lado]['lecturas'], (fase, lado)
    assert otra.sesion.vc and otra.txt_conclusion.toPlainText().startswith('Obstrucción')
    assert not otra.restore_report(d)   # ya tiene mediciones: no pisa

    # Prueba del docente (sin cita): no sube nada.
    prueba = RinomanometriaWindow(data_login=ADMIN)
    prueba.la_super(data, None)
    medir(prueba, 'D')
    assert prueba.report_job() is None


def test_informe_rinometria():
    data = caso('mixta')
    w = RinometriaWindow(data_login=ADMIN)
    w.la_super(data, '77')
    w._calibrar()
    medir(w, 'D')
    w._vasoconstrictor()
    medir(w, 'D')
    d = w.report_job()['data']
    assert d['calibrado'] and any(a.startswith('Cambio con vasoconstrictor FND') for a in d['avisos'])
    assert set(w.report_job()['images']()) == {'ra_curva'}
    sesion._actual = None
    otra = RinometriaWindow(data_login=ADMIN)
    otra.la_super(data, '77')
    otra.restore_report(d)
    esperar(otra)
    assert otra.calibrado
    assert otra.res['vc']['D']['promedio'] == w.res['vc']['D']['promedio']


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
