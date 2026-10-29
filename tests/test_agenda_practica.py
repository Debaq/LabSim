"""
Práctica libre en la agenda del alumno (agenda/Agenda.py, ver
labsim_backend/src/Practica.php): la lista de práctica se ve aparte de la
agenda, los intentos no aparecen como citas, y el botón sigue el ciclo
Practicar -> (intento abierto) -> Cerrar/Evolucionar, o Retomar si la app se
cerró con el intento abierto.

Sin red: Shedule y la API de práctica se reemplazan por dobles.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import Qt

from core.base import context  # crea la QApplication
from backend.shedule_sync import AgendaEntry
import agenda.Agenda as mod

APP = context.app


def _agenda_estado():
    hoy = mod.QDate.currentDate().toString("dd-MM-yy")
    return {"agenda_1": {
        "10": AgendaEntry(fecha=hoy, hora="09:00", nombre="Cita", apellido="Normal", case_id="c1"),
        "11": AgendaEntry(fecha=hoy, hora="21:00", nombre="Intento", apellido="Viejo", case_id="c2",
                          practice_id=1, atencion={"alumno": {"estado": "atendido"}}),
    }}


class _SheduleFalso:
    def get(self):
        return _agenda_estado()


class _Main:
    def __init__(self):
        self.data_login = {"user": "alumno", "permission": 444}
        self.data_current_key = None
        self.atendidos = []
        self.evoluciones = []

    def atender_paciente(self, key):
        self.atendidos.append(key)
        self.data_current_key = key

    def abrir_evolucion(self, nombre, guardar, key=None):
        self.evoluciones.append((nombre, key))


ITEMS = [{"id": 1, "case_id": "c2", "procedimiento": "Audiometría", "show_study_sheet": True,
          "curso": "C1", "nombre": "Ana", "apellido": "Paz", "rut": "1-9", "fecha_nac": "",
          "intentos": 1, "ultimo": "2026-10-08 20:00:00", "ultimo_cerrado": 11, "abierto": None}]


def _primera_carga(ag):
    """La agenda se baja en segundo plano al crearla (ver Agenda.__init__)."""
    tarea = ag._shedule_fetch
    if tarea is not None:
        assert tarea.esperar(5000)
        for _ in range(50):
            APP.processEvents()
            if ag._shedule_fetch is None:
                break


def _armar(monkey_iniciar):
    mod.Shedule = _SheduleFalso
    mod.lista_practica = lambda: [dict(it) for it in ITEMS]
    mod.iniciar_practica = monkey_iniciar
    main = _Main()
    ag = mod.Agenda(444, main)
    _primera_carga(ag)
    # Sin hilo: se entrega la lista como lo haría _pedir_practica (hilos.en_fondo).
    ag._pedir_practica = lambda: ag._on_practica_fetched(mod.lista_practica())
    ag.refresh_async = ag._pedir_practica
    return ag, main


def _filas(ag):
    return [ag.tableWidget.item(r, 4).text() for r in range(ag.tableWidget.rowCount())]


def test_los_intentos_no_aparecen_en_la_agenda():
    ag, _ = _armar(lambda pid: {})
    assert _filas(ag) == ["Cita"], _filas(ag)


def test_practicar_abre_un_intento_y_despues_se_cierra():
    abiertos = []

    def iniciar(pid):
        abiertos.append(pid)
        return {"id": 42}

    ag, main = _armar(iniciar)
    ag.btn_practica.setChecked(True)
    assert _filas(ag) == ["Ana"], _filas(ag)
    ag.tableWidget.selectRow(0)
    assert ag.btn_atender.text() == "Practicar"
    assert ag.btn_ficha_estudio.isEnabled()
    assert not ag.btn_ver_ficha.isEnabled()

    ag.btn_atender.click()
    assert abiertos == [1] and main.atendidos == ["42"]
    assert ag.btn_atender.text() == "Cerrar/Evolucionar", ag.btn_atender.text()

    ag.btn_atender.click()
    assert main.evoluciones == [("Ana Paz", "42")]

    ag.btn_vista_agenda.setChecked(True)
    assert _filas(ag) == ["Cita"]


def test_intento_abierto_de_otra_vez_se_retoma():
    ag, main = _armar(lambda pid: (_ for _ in ()).throw(AssertionError("no debe crear otro")))
    ITEMS[0]["abierto"] = 77
    try:
        ag.btn_practica.setChecked(True)
        ag.tableWidget.selectRow(0)
        assert ag.btn_atender.text() == "Retomar"
        ag.btn_atender.click()
        assert main.atendidos == ["77"]
    finally:
        ITEMS[0]["abierto"] = None



def test_rearmar_la_agenda_muchas_veces_no_deja_items_colgados():
    """El sync rearma la tabla cada minuto. El 2026-10-22 (labsim3) se
    cerró la app en setItem: Qt borraba el item viejo, creado en Python.
    Ahora los items se sacan con takeItem antes de rearmar."""
    import gc
    ag, _ = _armar(lambda pid: {})
    hoy = mod.QDate.currentDate().toString("dd-MM-yy")
    for vuelta in range(60):
        n = 1 + (vuelta * 7) % 9
        ag.shedule = {"agenda_1": {
            str(100 + i): AgendaEntry(fecha=hoy, hora=f"{8 + i:02d}:00", nombre=f"P{i}",
                                      apellido="X", case_id="c1")
            for i in range(n)}}
        if vuelta % 3 == 0 and ag.tableWidget.rowCount():
            ag.tableWidget.selectRow(0)
        if vuelta % 5 == 0:
            ag.tableWidget.sortItems(3, Qt.DescendingOrder)
        ag.populate_shedule()
        gc.collect()
        APP.processEvents()
        assert ag.tableWidget.rowCount() == n
        assert sorted(_filas(ag)) == sorted(f"P{i}" for i in range(n))
    ag.btn_practica.setChecked(True)
    ag.btn_vista_agenda.setChecked(True)
    gc.collect()
    assert ag.tableWidget.rowCount() >= 1

# -- Docente: la misma lista aparte, en modo prueba --------------------------

ITEMS_DOCENTE = [
    {"id": 1, "case_id": "c2", "procedimiento": "Audiometría", "show_study_sheet": True, "folder_id": 7, "carpeta": "Cap. 3", "orden": 1,
     "nombre": "Zoe", "apellido": "Paz", "rut": "1-9", "fecha_nac": "", "intentos": 3, "alumnos": 2,
     "ultimo": "2026-10-08 20:00:00", "ultimo_cerrado": None, "abierto": None},
    {"id": 2, "case_id": "c3", "procedimiento": "Impedanciometría", "show_study_sheet": False, "folder_id": 7, "carpeta": "Cap. 3", "orden": 2,
     "nombre": "Ana", "apellido": "Abarca", "rut": "2-7", "fecha_nac": "", "intentos": 0, "alumnos": 0,
     "ultimo": None, "ultimo_cerrado": None, "abierto": None},
]


class _MainDocente(_Main):
    def __init__(self):
        super().__init__()
        self.data_login = {"user": "profe", "permission": 555}
        self.pruebas = []

    def atender_paciente_prueba(self, key):
        self.pruebas.append(key)
        self.data_current_key = key


def _agenda_docente():
    hoy = mod.QDate.currentDate().toString("dd-MM-yy")
    return {"agenda_1": {
        "10": AgendaEntry(fecha=hoy, hora="09:00", nombre="Cita", apellido="Normal", case_id="c1"),
        "11": AgendaEntry(fecha=hoy, hora="21:00", nombre="Intento", apellido="Alumno", case_id="c2",
                          practice_id=1, atencion={"alumno": {"estado": "atendido"}}),
        "case:c3": AgendaEntry(nombre="Ana", apellido="Abarca", case_id="c3", sin_cita=True),
        "case:c4": AgendaEntry(nombre="Otro", apellido="Caso", case_id="c4", sin_cita=True),
    }}


def _armar_docente():
    class _Falso:
        def get(self):
            return _agenda_docente()
    mod.Shedule = _Falso
    mod.lista_practica = lambda: [dict(it) for it in ITEMS_DOCENTE]
    mod.iniciar_practica = lambda pid: (_ for _ in ()).throw(AssertionError("el docente no crea intentos"))
    main = _MainDocente()
    ag = mod.Agenda(555, main)
    _primera_carga(ag)
    ag._pedir_practica = lambda: ag._on_practica_fetched(mod.lista_practica())
    ag.refresh_async = ag._pedir_practica
    ag._pedir_practica()
    return ag, main


def test_docente_tiene_practica_libre_y_su_agenda_no_la_mezcla():
    ag, _ = _armar_docente()
    assert not ag.btn_practica.isHidden()
    # Ni el intento del alumno ni el caso sin cita que es de práctica
    assert sorted(_filas(ag)) == ["Cita", "Otro"], _filas(ag)
    ag.btn_practica.setChecked(True)
    # El orden de la carpeta, no el de la columna Estado
    assert _filas(ag) == ["Zoe", "Ana"], _filas(ag)
    assert ag.tableWidget.item(0, 1).text() == "1"
    assert ag.tableWidget.horizontalHeaderItem(1).text() == "N°"
    assert ag.chk_guardar_base.isHidden()
    # El docente ve siempre la ficha de estudio del caso, en las dos vistas
    assert not ag.btn_ficha_estudio.isHidden()
    ag.tableWidget.selectRow(0)
    assert ag.btn_ficha_estudio.isEnabled()
    pedidas = []
    mod.abrir_ficha_estudio = lambda parent, appointment_id=None, case_id=None: pedidas.append(case_id)
    ag.btn_ficha_estudio.click()
    assert pedidas == ["c2"], pedidas
    ag.btn_vista_agenda.setChecked(True)
    assert sorted(_filas(ag)) == ["Cita", "Otro"]
    assert not ag.chk_guardar_base.isHidden() and not ag.btn_ficha_estudio.isHidden()


def test_docente_abre_la_practica_en_prueba():
    ag, main = _armar_docente()
    ag.btn_practica.setChecked(True)
    ag.tableWidget.selectRow(1)                 # Ana: caso sin cita
    assert ag.btn_atender.text() == "Atender (prueba)"
    assert ag.btn_ver_ficha.isEnabled()
    ag.btn_atender.click()
    assert main.pruebas == ["case:c3"], main.pruebas
    assert ag.btn_atender.text() == "Cerrar/Evolucionar", ag.btn_atender.text()
    ag.btn_atender.click()
    assert main.evoluciones == [("Ana Abarca", None)], main.evoluciones

    ag.tableWidget.selectRow(0)                 # Zoe: solo tiene intentos de alumnos
    assert ag.btn_atender.text() == "Atender (prueba)"
    ag._prueba_atendiendo_key = None
    main.data_current_key = None
    ag.btn_atender.click()
    assert main.pruebas[-1] == "11", main.pruebas


def _item(i, carpeta, fid, orden, nombre):
    return {"id": i, "case_id": f"c{i}", "procedimiento": "Audiometría", "show_study_sheet": False,
            "folder_id": fid, "carpeta": carpeta, "orden": orden, "nombre": nombre, "apellido": "X",
            "rut": f"{i}-9", "fecha_nac": "", "intentos": 0, "ultimo": None, "ultimo_cerrado": None,
            "abierto": None}


def test_carpetas_en_su_orden_y_buscar_en_todas():
    """Cap. 6 viene antes que Cap. 3 porque así las ordenó el admin: la app
    respeta el orden del backend, en las carpetas y adentro de cada una."""
    ag, _ = _armar(lambda pid: {})
    items = [_item(1, "Cap. 6", 60, 1, "Zoe"), _item(2, "Cap. 6", 60, 2, "Ana")]
    items += [_item(10 + n, "Cap. 3", 30, n, f"P{n}") for n in range(1, 12)]
    mod.lista_practica = lambda: [dict(it) for it in items]
    ag.btn_practica.setChecked(True)
    lista = ag.lista_carpetas
    assert not lista.isHidden()
    assert [lista.item(i).text() for i in range(lista.count())] == ["Cap. 6  (2)", "Cap. 3  (11)"]
    assert _filas(ag) == ["Zoe", "Ana"]
    lista.setCurrentRow(1)
    assert _filas(ag) == [f"P{n}" for n in range(1, 12)]
    # N° es número: ordenar por esa columna no pone el 10 antes que el 2
    ag.tableWidget.sortItems(1, Qt.AscendingOrder)
    assert _filas(ag) == [f"P{n}" for n in range(1, 12)]
    ag.led_buscar.setText("ana")
    assert _filas(ag) == ["Ana"]
    # Por examen, aunque el procedimiento no lo nombre: ASSR va con el PEATC
    items[0]["procedimiento"] = "EOA + PEATC"
    ag._on_practica_fetched([dict(x) for x in items])
    ag.led_buscar.setText("ASSR")
    assert _filas(ag) == ["Zoe"], _filas(ag)
    ag.led_buscar.setText("audiometria")      # sin tilde también
    assert len(_filas(ag)) == len(items) - 1
    ag.led_buscar.setText("")
    ag.btn_vista_agenda.setChecked(True)
    assert lista.isHidden()


def test_la_agenda_no_se_baja_en_el_hilo_de_la_ventana():
    """Al iniciar sesión la ventana quedaba congelada mientras llegaba el
    estado completo. Ahora se crea vacía, avisa que carga y, al llegar,
    main retoma la atención abierta (agenda_cargada)."""
    import threading
    hilos_que_bajan = []

    class _Lento:
        def get(self):
            hilos_que_bajan.append(threading.current_thread().name)
            return _agenda_estado()
    mod.Shedule = _Lento
    mod.lista_practica = lambda: []
    main = _Main()
    cargadas = []
    main.agenda_cargada = lambda: cargadas.append(1)
    ag = mod.Agenda(444, main)
    assert ag.lbl_vacio.text() == "Cargando la agenda…", ag.lbl_vacio.text()
    _primera_carga(ag)
    assert hilos_que_bajan and hilos_que_bajan[0] != threading.current_thread().name
    assert _filas(ag) == ["Cita"] and cargadas == [1]
    ag.refresh_async()
    _primera_carga(ag)
    assert cargadas == [1]          # solo la primera vez


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
