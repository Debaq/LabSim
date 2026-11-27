"""Agenda relativa al ingreso del alumno (core/agenda_relativa.py).

El docente pone el orden (hora) y la duración de cada paciente; el horario
del alumno parte en el múltiplo de 5 min siguiente a su primer ingreso del
día (nunca antes de la hora del primero) y suma duraciones. Cada paciente
llega al azar dentro de los 15 min previos a su turno, siempre igual para
el mismo alumno.
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from backend.shedule_sync import AgendaEntry, _appointment_fields, backend_state_to_shedule
from core import agenda_relativa as ar

HOY = "30-11-26"


def _agenda():
    # El caso del docente: 30, 45, 15 y 60 min, todos a "todo el curso".
    return {
        "11": AgendaEntry(fecha=HOY, hora="09:00", nombre="Samuel", duracion_min=30),
        "12": AgendaEntry(fecha=HOY, hora="09:30", nombre="Ana", duracion_min=45),
        "13": AgendaEntry(fecha=HOY, hora="10:15", nombre="Luis", duracion_min=15),
        "14": AgendaEntry(fecha=HOY, hora="10:30", nombre="Rosa", duracion_min=60),
        "20": AgendaEntry(fecha=HOY, hora="12:00", nombre="Fija"),
        "21": AgendaEntry(fecha="01-12-26", hora="09:00", nombre="Mañana", duracion_min=30),
    }


def test_turnos_desde_el_ingreso():
    ag = _agenda()
    ar.calcular(ag, "ana.rojas", datetime(2026, 11, 30, 11, 12, 40), HOY)
    turnos = [(ag[k].turno_inicio.strftime("%H:%M"), ag[k].turno_fin.strftime("%H:%M")) for k in "11 12 13 14".split()]
    assert turnos == [("11:15", "11:45"), ("11:45", "12:30"), ("12:30", "12:45"), ("12:45", "13:45")], turnos
    # Hora fija y otro día: sin turno calculado.
    assert ag["20"].turno_inicio is None and ag["21"].turno_inicio is None
    assert ar.hora_vista(ag["20"]) == "12:00" and ar.hora_vista(ag["12"]) == "11:45"


def test_multiplo_justo_pasa_al_siguiente():
    assert ar.primer_turno(datetime(2026, 11, 30, 11, 15, 0)) == datetime(2026, 11, 30, 11, 20)
    assert ar.primer_turno(datetime(2026, 11, 30, 11, 16, 59)) == datetime(2026, 11, 30, 11, 20)


def test_no_antes_de_la_hora_del_docente():
    ag = _agenda()
    ar.calcular(ag, "x", datetime(2026, 11, 30, 7, 50), HOY)
    assert ag["11"].turno_inicio == datetime(2026, 11, 30, 9, 0)
    assert ag["14"].turno_fin == datetime(2026, 11, 30, 11, 30)


def test_llegada_hasta_15_antes_y_estable():
    ag = _agenda()
    ar.calcular(ag, "ana.rojas", datetime(2026, 11, 30, 11, 12), HOY)
    otra = _agenda()
    ar.calcular(otra, "ana.rojas", datetime(2026, 11, 30, 11, 12), HOY)
    for k in "11 12 13 14".split():
        e = ag[k]
        assert e.turno_inicio - timedelta(minutes=15) <= e.llegada <= e.turno_inicio
        assert e.llegada == otra[k].llegada
    distinto = _agenda()
    ar.calcular(distinto, "otro.alumno", datetime(2026, 11, 30, 11, 12), HOY)
    assert any(distinto[k].llegada != ag[k].llegada for k in "11 12 13 14".split())
    e = ag["12"]
    assert ar.todavia_no_llega(e, e.llegada - timedelta(seconds=1))
    assert not ar.todavia_no_llega(e, e.llegada)


def test_ingreso_del_dia_es_el_primero_de_hoy_en_hora_local():
    ahora_local = datetime(2026, 11, 30, 11, 0)
    def utc(local):
        return local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ingresos = [utc(datetime(2026, 11, 29, 20, 0)), utc(datetime(2026, 11, 30, 10, 40)),
                utc(datetime(2026, 11, 30, 9, 5))]
    assert ar.ingreso_del_dia(ingresos, date(2026, 11, 30)) == datetime(2026, 11, 30, 9, 5)
    assert ar.ingreso_del_dia(ingresos[:1], ahora_local.date()) is None


def test_docente_no_recalcula():
    ag = _agenda()
    ar.aplicar(ag, {"role": "admin", "username": "profe"}, datetime(2026, 11, 30, 11, 0))
    assert all(e.turno_inicio is None for e in ag.values())


def test_turno_no_viaja_al_backend():
    ag = _agenda()
    ar.calcular(ag, "x", datetime(2026, 11, 30, 11, 0), HOY)
    campos = _appointment_fields(ag["11"])
    assert campos["hora"] == "09:00" and "turno_inicio" not in campos and "duracion_min" not in campos


def test_duracion_llega_del_sync():
    estado = {"appointments": [{"id": 5, "fecha": HOY, "hora": "09:00", "duracion_min": 30},
                               {"id": 6, "fecha": HOY, "hora": "09:30", "duracion_min": None}]}
    ag = backend_state_to_shedule(estado, 1, "x")["agenda_1"]
    assert ag["5"].duracion_min == 30 and ag["6"].duracion_min is None


def test_agenda_del_alumno_espera_la_llegada():
    """En la tabla: 'Aún no llega' con «Atender» apagado, 'En sala de espera'
    y 'Esperando, atrasado' con «Atender» prendido, sin «No se presentó»."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from core.base import context  # crea la QApplication
    import agenda.Agenda as mod
    app = context.app
    ahora = datetime.now().replace(microsecond=0)
    hoy = ahora.strftime("%d-%m-%y")

    def fila(nombre, llega_en, turno_en, hora):
        e = AgendaEntry(fecha=hoy, hora=hora, nombre=nombre, case_id="c" + nombre, duracion_min=30)
        e.llegada = ahora + timedelta(minutes=llega_en)
        e.turno_inicio = ahora + timedelta(minutes=turno_en)
        e.turno_fin = e.turno_inicio + timedelta(minutes=30)
        return e

    agenda = {"1": fila("Atrasado", -40, -20, "08:00"), "2": fila("Espera", -3, 10, "08:30"),
              "3": fila("Lejos", 30, 40, "09:00")}

    class _Shedule:
        def get(self):
            return {"agenda_1": agenda}

    class _Main:
        data_login = {"user": "alumno", "permission": 444}
        data_current_key = None

    mod.Shedule = _Shedule
    ag = mod.Agenda(444, _Main())
    tarea = ag._shedule_fetch
    if tarea is not None:
        assert tarea.esperar(5000)
        for _ in range(50):
            app.processEvents()
            if ag._shedule_fetch is None:
                break
    claves = dict(ag._claves_relativa())
    assert claves == {"1": "espera_atrasada", "2": "en_espera", "3": "aun_no_llega"}, claves
    keys = ag._visible_keys()
    for key, prendido in (("1", True), ("2", True), ("3", False)):
        ag.tableWidget.selectRow(keys.index(key))
        app.processEvents()
        assert ag.btn_atender.isEnabled() is prendido, key
        assert not ag.btn_no_show.isEnabled(), key
    # La hora que ve el alumno es su turno, no la del docente.
    col_hora = ag.tableWidget.item(keys.index("3"), 2).text()
    assert col_hora == agenda["3"].turno_inicio.strftime("%H:%M"), col_hora


def _con_turnos(ingreso=datetime(2026, 11, 30, 11, 12)):
    ag = _agenda()
    ar.calcular(ag, "ana.rojas", ingreso, HOY)
    return ag


def test_karime_umbrales():
    from core import secretaria as sec
    assert sec._umbral("atrasado", 4.9) is None
    assert [sec._umbral("atrasado", m) for m in (5, 14, 15, 29, 30, 46)] == [5, 5, 15, 15, 30, 45]
    assert [sec._umbral("pasado", m) for m in (-1, 0, 9, 10, 25)] == [None, 0, 0, 10, 20]


def test_karime_minutos_por_curso():
    from core import secretaria as sec
    curso = {"umbrales": {"atrasado": {"primero": 10, "segundo": 0, "cada": 0},
                          "pasado": {"primero": 5, "cada": 5}, "box": {"cada": "roto"}}}
    u = sec.config_minutos(curso)
    assert u["atrasado"] == ((10.0,), 0.0)          # segundo menor = sin segundo
    assert u["pasado"] == ((5.0,), 5.0)
    assert u["box"] == ((0.0,), 10.0)               # valor roto = el de la app
    # cada 0: después del último no se repite (misma clave, no se vuelve a decir)
    assert [sec._umbral("atrasado", m, u) for m in (9, 10, 50, 300)] == [None, 10, 10, 10]
    # Con el primer aviso de atención pasada a los 5 min, la pregunta va ahí.
    from core.base import context  # crea la QApplication
    from PySide6.QtWidgets import QMdiArea, QPushButton
    ag = _con_turnos()
    ag["11"].atencion["ana.rojas"] = {"estado": "atendiendo"}
    area = QMdiArea()
    s = sec.Secretaria(area)
    original = sec.app_config_store.get
    sec.app_config_store.get = lambda clave: curso if clave == sec.CONFIG_MINUTOS_KEY else original(clave)
    try:
        _pregunta_al_primer_aviso(sec, s, ag)
    finally:
        sec.app_config_store.get = original
        s.detener()


def _pregunta_al_primer_aviso(sec, s, ag):
    from PySide6.QtWidgets import QPushButton
    r = sec.Recepcion(s, lambda: ag, lambda: "ana.rojas", lambda: "11", lambda: 33 * 60, citar=lambda: None)
    r._timer.stop()
    ahora = ag["11"].turno_inicio + timedelta(minutes=33)
    for _ in range(10):
        r.tic(ahora)
    assert not any(a.findChildren(QPushButton) for a in s._avisos)    # 33 min = 3 pasado: todavía no
    r._fuentes = (lambda: ag, lambda: "ana.rojas", lambda: "11", lambda: 36 * 60)
    for _ in range(10):
        r.tic(ahora)
    assert sum(1 for a in s._avisos if a.findChildren(QPushButton)) == 1


def test_karime_eventos_en_orden():
    from core import secretaria as sec
    ag = _con_turnos()
    samuel, ana = ag["11"], ag["12"]
    # Antes de que llegue nadie: nada.
    assert sec.eventos_agenda(ag, "ana.rojas", samuel.llegada - timedelta(minutes=1)) == []
    # Samuel llegó: se anuncia.
    ev = sec.eventos_agenda(ag, "ana.rojas", samuel.llegada)
    assert [e[1] for e in ev] == ["llegada"] and ev[0][2]["nombre"] == "Samuel"
    # 20 min pasado su turno sin atenderlo: llegada + atrasado (umbral 15).
    ev = sec.eventos_agenda(ag, "ana.rojas", samuel.turno_inicio + timedelta(minutes=20))
    claves = [e[0] for e in ev]
    assert ("atrasado", "11", 15) in claves and claves[0] == ("llegada", "11")
    # Atendiendo a Samuel 35 min (duración 30): se pasó; Ana espera y se anuncia.
    samuel.atencion["ana.rojas"] = {"estado": "atendiendo"}
    ahora = samuel.turno_inicio + timedelta(minutes=35)
    ev = sec.eventos_agenda(ag, "ana.rojas", ahora, key_activa="11", segundos_atencion=35 * 60)
    tipos = [e[1] for e in ev]
    assert "pasado" in tipos and tipos.index("llegada") < tipos.index("pasado")
    assert not any(e[0][:2] == ("atrasado", "11") for e in ev)
    # Pasado el bloque con Rosa sin atender: el box.
    fin = ag["14"].turno_fin
    ev = sec.eventos_agenda(ag, "ana.rojas", fin + timedelta(minutes=12))
    assert (("box", 10), "box", {"hora": fin.strftime("%H:%M")}) in ev


def test_karime_dice_una_vez_y_no_al_docente():
    from core.base import context  # crea la QApplication
    from PySide6.QtWidgets import QMdiArea
    from core import secretaria as sec
    ag = _con_turnos()
    area = QMdiArea()
    area.resize(800, 600)
    s = sec.Secretaria(area)
    usuario = {"u": "ana.rojas"}
    r = sec.Recepcion(s, lambda: ag, lambda: usuario["u"], lambda: None, lambda: 0)
    r._timer.stop()
    ahora = ag["12"].llegada + timedelta(seconds=1)   # llegaron Samuel y Ana
    dichos = []
    while (texto := r.tic(ahora)) is not None:
        dichos.append(texto)
    assert "Samuel" in dichos[0] and "Ana" in dichos[1], dichos
    # Lo que queda (el turno de Samuel atrasado) se dice una vez y se acaba.
    assert len(dichos) == len(sec.eventos_agenda(ag, "ana.rojas", ahora)), dichos
    usuario["u"] = None
    r.reiniciar()
    assert r.tic(ahora) is None
    # Una cita con duración no programa los avisos por minutos.
    s.iniciar(None, relativa=True)
    assert s._timers == []
    s.detener()


def test_pendientes_en_horario_libre_y_plazo():
    ag = _agenda()   # práctico el 30-11 y otro el 01-12
    ag["30"] = AgendaEntry(fecha="05-12-26", hora="09:00", nombre="Otro práctico", duracion_min=30)
    cont = AgendaEntry(fecha=HOY, hora="12:40", nombre="Samuel", continua_de=11)
    ag["40"] = cont
    hoy = date(2026, 11, 30)
    # La continuación es pendiente desde que nace; plazo: el práctico del 01-12.
    assert ar.es_pendiente_libre(cont, "ana", hoy)
    assert ar.plazo(cont, ag) == date(2026, 12, 1)
    assert not ar.pendiente_vencido(cont, ag, hoy)
    assert ar.pendiente_vencido(cont, ag, date(2026, 12, 1))
    # Un paciente con duración sin atender pasa a pendiente al día siguiente.
    rosa = ag["14"]
    assert not ar.es_pendiente_libre(rosa, "ana", hoy)
    assert ar.es_pendiente_libre(rosa, "ana", date(2026, 12, 1))
    assert ar.plazo(rosa, ag) == date(2026, 12, 1)
    rosa.atencion["ana"] = {"estado": "atendido"}
    assert not ar.es_pendiente_libre(rosa, "ana", date(2026, 12, 1))
    # Una cita fija vieja no es pendiente (sigue siendo "hora pasada").
    assert not ar.es_pendiente_libre(ag["20"], "ana", date(2026, 12, 1))
    # Sin próximo práctico agendado: plazo por confirmar.
    assert ar.plazo(AgendaEntry(fecha="06-12-26", hora="10:00", continua_de=1), ag) is None


def test_cierre_con_continuar_viaja_por_la_cola():
    import tempfile
    from core import acciones_pendientes as ap
    with tempfile.TemporaryDirectory() as tmp:
        ap._carpeta = lambda: __import__("pathlib").Path(tmp)

        class _Cliente:
            user = {"id": 7, "username": "ana"}
            token = "t"
            def __init__(self):
                self.enviados = []
            def post_attendance_action(self, cita, accion, nota=None, continuar=False):
                self.enviados.append((cita, accion, continuar))

        c = _Cliente()
        ap.subir_informes_de = lambda cliente, cita: []
        ap._cliente_para = lambda item, actual: c
        ap.encolar(c, 99, "atendido", "falta la impedancia", continuar=True)
        ap.encolar(c, 98, "atendido", "completa")
        assert ap.vaciar() == 0
        assert c.enviados == [(99, "atendido", True), (98, "atendido", False)], c.enviados


def test_karime_pregunta_si_se_pasa_o_cita():
    from core.base import context  # crea la QApplication
    from PySide6.QtWidgets import QMdiArea, QPushButton
    from core import secretaria as sec
    ag = _con_turnos()
    samuel = ag["11"]
    samuel.atencion["ana.rojas"] = {"estado": "atendiendo"}
    area = QMdiArea()
    area.resize(800, 600)
    s = sec.Secretaria(area)
    citados = []
    r = sec.Recepcion(s, lambda: ag, lambda: "ana.rojas", lambda: "11", lambda: 31 * 60,
                      citar=lambda: citados.append(True))
    r._timer.stop()
    ahora = samuel.turno_inicio + timedelta(minutes=31)
    for _ in range(10):
        r.tic(ahora)
    con_botones = [a for a in s._avisos if a.findChildren(QPushButton)]
    assert len(con_botones) == 1
    botones = {b.text(): b for b in con_botones[0].findChildren(QPushButton)}
    assert set(botones) == {"Me paso", "Citar para terminar"}
    botones["Citar para terminar"].click()
    assert citados == [True]
    s.detener()


def test_evolucion_muestra_y_manda_citar_para_terminar():
    from core.base import context  # crea la QApplication
    import agenda.Agenda as mod
    ev = mod.EvolucionWidget()
    recibido = []
    ev.set_contexto("Samuel", lambda nota: recibido.append(nota) or True, None, continuar=None)
    assert ev.chk_continuar.isHidden()
    ev.set_contexto("Samuel", lambda nota: recibido.append(nota) or True, None, continuar=True)
    assert not ev.chk_continuar.isHidden() and ev.chk_continuar.isChecked()
    ev.texto.setPlainText("Audiometría hecha; falta impedanciometría.")
    ev._on_guardar_clicked()
    assert recibido == ["Audiometría hecha; falta impedanciometría."]
    assert not ev.chk_continuar.isChecked()   # la próxima nota parte sin marcar


def test_agenda_muestra_lo_pendiente_cualquier_dia():
    from core.base import context  # crea la QApplication
    import agenda.Agenda as mod
    app = context.app
    hoy = datetime.now().date()
    ayer = (hoy - timedelta(days=1)).strftime("%d-%m-%y")
    manana = (hoy + timedelta(days=1)).strftime("%d-%m-%y")
    agenda = {
        "50": AgendaEntry(fecha=ayer, hora="09:00", nombre="Rosa", case_id="c1", duracion_min=60),
        "51": AgendaEntry(fecha=ayer, hora="12:10", nombre="Samuel", case_id="c2", continua_de=7),
        "52": AgendaEntry(fecha=ayer, hora="10:00", nombre="Fija vieja", case_id="c3"),
        "53": AgendaEntry(fecha=manana, hora="09:00", nombre="Próximo", case_id="c4", duracion_min=30),
    }

    class _Shedule:
        def get(self):
            return {"agenda_1": agenda}

    class _Main:
        data_login = {"user": "alumno", "permission": 444}
        data_current_key = None

    mod.Shedule = _Shedule
    ag = mod.Agenda(444, _Main())
    tarea = ag._shedule_fetch
    if tarea is not None:
        assert tarea.esperar(5000)
        for _ in range(50):
            app.processEvents()
            if ag._shedule_fetch is None:
                break
    keys = ag._visible_keys()
    assert set(keys) == {"50", "51"}, keys      # hoy: solo lo pendiente
    for key in keys:
        estado = ag._clave_estado(agenda[key], None)
        assert estado == "pendiente", (key, estado)
        ag.tableWidget.selectRow(keys.index(key))
        app.processEvents()
        assert ag.btn_atender.isEnabled() and not ag.btn_no_show.isEnabled()
        assert ag.tableWidget.item(keys.index(key), 2).text() == "libre"
    assert manana in ag._texto_plazo(agenda["51"])


def test_turnos_se_registran_una_vez_al_dia():
    ag = _agenda()
    registros = []
    ar._ingresos_utc = []
    ar._ingreso_local.clear()
    ar._registrados.clear()
    ahora = datetime(2026, 11, 30, 11, 12)
    usuario = {"role": "student", "username": "ana.rojas"}
    ar.aplicar(ag, usuario, ahora, registrar=lambda a, p: registros.append((a, p)))
    ar.aplicar(ag, usuario, ahora + timedelta(minutes=5), registrar=lambda a, p: registros.append((a, p)))
    assert len(registros) == 1 and registros[0][0] == "agenda_turnos"
    p = registros[0][1]
    assert p["fecha"] == HOY and p["ingreso"] == "2026-11-30 11:12:00"
    assert [(t["appointment_id"], t["inicio"], t["fin"], t["duracion_min"]) for t in p["turnos"]] == [
        (11, "11:15", "11:45", 30), (12, "11:45", "12:30", 45), (13, "12:30", "12:45", 15), (14, "12:45", "13:45", 60)]


def test_ir_a_buscar_al_paciente_recien_despedido():
    """Cerrar es despedirlo; durante 5 min «Ir a buscarlo» reabre la atención."""
    from core.base import context  # crea la QApplication
    import main as app_main
    import agenda.Agenda as mod
    app = context.app

    class _Yo:
        VENTANA_BUSCAR_MIN = app_main.MainWindow.VENTANA_BUSCAR_MIN
        plazo_ir_a_buscar = app_main.MainWindow.plazo_ir_a_buscar

    yo = _Yo()
    yo._despedidos = {"60": (datetime.now() - timedelta(minutes=2), "nota"),
                      "61": (datetime.now() - timedelta(minutes=6), "nota")}
    assert yo.plazo_ir_a_buscar("60") is not None
    assert yo.plazo_ir_a_buscar("61") is None and yo.plazo_ir_a_buscar("62") is None

    hoy = datetime.now().strftime("%d-%m-%y")
    agenda = {"60": AgendaEntry(fecha=hoy, hora="09:00", nombre="Samuel", case_id="c1",
                                atencion={"alumno": {"estado": "atendido", "nota": "x"}}),
              "61": AgendaEntry(fecha=hoy, hora="10:00", nombre="Rosa", case_id="c2",
                                atencion={"alumno": {"estado": "atendido", "nota": "x"}})}

    class _Shedule:
        def get(self):
            return {"agenda_1": agenda}

    buscados = []

    class _Main:
        data_login = {"user": "alumno", "permission": 444}
        data_current_key = None
        plazo_ir_a_buscar = yo.plazo_ir_a_buscar
        def ir_a_buscar(self, key):
            buscados.append(key)

    mod.Shedule = _Shedule
    ag = mod.Agenda(444, _Main())
    tarea = ag._shedule_fetch
    if tarea is not None:
        assert tarea.esperar(5000)
        for _ in range(50):
            app.processEvents()
            if ag._shedule_fetch is None:
                break
    keys = ag._visible_keys()
    ag.tableWidget.selectRow(keys.index("60"))
    app.processEvents()
    assert ag.btn_atender.text() == "Ir a buscarlo" and ag.btn_atender.isEnabled()
    ag.atender_paciente()
    assert buscados == ["60"]
    ag.tableWidget.selectRow(keys.index("61"))
    app.processEvents()
    assert ag.btn_atender.text() == "Atender" and not ag.btn_atender.isEnabled()


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print("ok", nombre)
